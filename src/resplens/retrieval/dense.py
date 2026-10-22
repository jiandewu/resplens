"""Dense retrieval with embeddings from a local Ollama server, plus rank fusion with BM25."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
CACHE = Path(__file__).resolve().parents[3] / ".cache" / "embeddings"


class EmbeddingError(RuntimeError):
    pass


class OllamaEmbedder:
    """Embeddings via Ollama's /api/embed, cached on disk by model, prefix, and text.

    Inputs longer than the model's context raise EmbeddingError instead of being truncated,
    so an oversized chunk can never be indexed with its tail silently missing.
    """

    def __init__(self, model: str, query_prefix: str = "", document_prefix: str = "", batch_size: int = 32):
        self.model, self.query_prefix, self.document_prefix = model, query_prefix, document_prefix
        self.batch_size = batch_size

    def _request(self, inputs: list[str]) -> list[list[float]]:
        body = json.dumps({"model": self.model, "input": inputs, "truncate": False}).encode()
        request = urllib.request.Request(f"{OLLAMA_URL}/api/embed", body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.load(response)["embeddings"]
        except urllib.error.HTTPError as exc:
            raise EmbeddingError(f"{self.model}: {exc.read().decode('utf-8', 'replace')[:300]}") from None

    def _cache_path(self, texts: list[str]) -> Path:
        digest = hashlib.sha256("\x00".join([self.model, *texts]).encode()).hexdigest()[:24]
        return CACHE / f"{self.model.replace(':', '_').replace('/', '_')}-{digest}.npy"

    def embed(self, texts: list[str], prefix: str = "", cache: bool = True) -> np.ndarray:
        """Unit-length embeddings, one row per text; ``cache`` reuses earlier results from disk."""
        texts = [prefix + text for text in texts]
        path = self._cache_path(texts)
        if cache and path.exists():
            return np.load(path)
        rows = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]
            try:
                rows += self._request(batch)
            except EmbeddingError:
                # find which input is too long, for a useful message
                for text in batch:
                    try:
                        self._request([text])
                    except EmbeddingError as exc:
                        raise EmbeddingError(f"{exc} (input starts: {text[:80]!r})") from None
                raise
        matrix = np.asarray(rows, dtype=np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        if cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, matrix)
        return matrix

    def documents(self, texts: list[str]) -> np.ndarray:
        return self.embed(texts, self.document_prefix)

    def query(self, text: str) -> np.ndarray:
        # never cached: query encoding is part of the measured search latency
        return self.embed([text], self.query_prefix, cache=False)[0]


# Hugging Face models run with sentence-transformers, pinned to a commit for reproducibility.
HF_REVISIONS = {
    "BAAI/bge-m3": "5617a9f61b028005a4858fdac845db406aefb181",
    "BAAI/bge-reranker-v2-m3": "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
}


class SentenceTransformerEmbedder:
    """Reference implementation of an embedding model (used for bge-m3: Ollama's build returned
    NaN for some inputs). Same interface and on-disk cache as OllamaEmbedder."""

    def __init__(self, model: str, query_prefix: str = "", document_prefix: str = "", batch_size: int = 32):
        from sentence_transformers import SentenceTransformer

        self.model, self.query_prefix, self.document_prefix = model, query_prefix, document_prefix
        self.batch_size = batch_size
        self._model = SentenceTransformer(model, revision=HF_REVISIONS.get(model))

    _cache_path = OllamaEmbedder._cache_path

    def embed(self, texts: list[str], prefix: str = "", cache: bool = True) -> np.ndarray:
        texts = [prefix + text for text in texts]
        path = self._cache_path(texts)
        if cache and path.exists():
            return np.load(path)
        matrix = self._model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                    convert_to_numpy=True).astype(np.float32)
        if not np.isfinite(matrix).all():
            raise EmbeddingError(f"{self.model}: non-finite embedding values")
        if cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            np.save(path, matrix)
        return matrix

    documents = OllamaEmbedder.documents
    query = OllamaEmbedder.query


def rerank_search(first_stage, texts: list[str], model: str = "BAAI/bge-reranker-v2-m3", depth: int = 30):
    """Rerank the first stage's top ``depth`` results with a cross-encoder."""
    from sentence_transformers import CrossEncoder

    encoder = CrossEncoder(model, revision=HF_REVISIONS.get(model))

    def search(query: str, k: int) -> list[int]:
        candidates = first_stage(query, depth)
        scores = encoder.predict([(query, texts[index]) for index in candidates])
        order = np.argsort(-np.asarray(scores))
        return [candidates[position] for position in order[:k]]
    return search


def dense_search(embedder, documents: list[str]):
    """search(query, k) -> document indices by cosine similarity."""
    matrix = embedder.documents(documents)

    def search(query: str, k: int) -> list[int]:
        scores = matrix @ embedder.query(query)
        return [int(index) for index in np.argsort(-scores)[:k]]
    return search


def rrf(rankings: list[list[int]], k: int, constant: int = 60) -> list[int]:
    """Reciprocal rank fusion: score(d) = sum over rankings of 1 / (constant + rank)."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (constant + rank)
    return [index for index, _ in sorted(scores.items(), key=lambda item: -item[1])[:k]]


def hybrid_search(searches, depth: int = 50):
    """Fuse several search functions, each asked for its top ``depth`` results."""
    def search(query: str, k: int) -> list[int]:
        return rrf([run(query, depth) for run in searches], k)
    return search
