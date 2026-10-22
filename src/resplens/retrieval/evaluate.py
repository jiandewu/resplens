"""Retrieval evaluation: rank chunks for each question and score them against evidence quotes.

    uv run python -m resplens.retrieval.evaluate --split dev --retriever bm25 --chunk-tokens 400
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from . import corpus
from .bm25 import BM25
from .chunking import Chunk, chunk_document
from .dense import OllamaEmbedder, SentenceTransformerEmbedder, dense_search, hybrid_search, rerank_search
from .metrics import bootstrap_ci, first_hit_rank, mrr, normalize, recall_at


ROOT = Path(__file__).resolve().parents[3]
QUESTIONS = ROOT / "eval" / "questions.jsonl"
KS = (1, 3, 5, 10)


def load_questions(path: Path = QUESTIONS, split: str | None = None) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [row for row in rows if split in (None, "all", row["split"])]


def check_questions(questions: list[dict], documents: list[corpus.Document]) -> list[str]:
    """Problems with the question set: quotes not found verbatim, or spanning a paragraph break."""
    texts = {doc.id: doc.text for doc in documents}
    problems = []
    for question in questions:
        for evidence in question["evidence"]:
            text = texts.get(evidence["doc"])
            if text is None:
                problems.append(f"{question['id']}: unknown document {evidence['doc']}")
            elif normalize(evidence["quote"]) not in normalize(text):
                problems.append(f"{question['id']}: quote not found in {evidence['doc']}")
            elif not any(normalize(evidence["quote"]) in normalize(part) for part in text.split("\n\n")):
                problems.append(f"{question['id']}: quote spans a paragraph break in {evidence['doc']}")
    return problems


def build_chunks(documents: list[corpus.Document], chunk_tokens: int) -> list[Chunk]:
    """Chunks sized in the embedding tokenizer's tokens, shared by every retriever."""
    from .tokens import count_tokens
    return [chunk for doc in documents
            for chunk in chunk_document(doc.id, doc.text, max_tokens=chunk_tokens, count=count_tokens)]


def evaluate(questions: list[dict], chunks: list[Chunk], search, k: int = max(KS)) -> tuple[list[dict], dict]:
    """Per-question results and a summary; ``search(query, k)`` returns chunk indices, best first."""
    answerable = [question for question in questions if question["evidence"]]
    results, latencies = [], []
    for question in answerable:
        start = time.perf_counter()
        ranked = search(question["question"], k)
        latencies.append(time.perf_counter() - start)
        texts = [chunks[index].text for index in ranked]
        rank = first_hit_rank(texts, [evidence["quote"] for evidence in question["evidence"]])
        results.append({"id": question["id"], "type": question["type"], "rank": rank,
                        "retrieved": [chunks[index].id for index in ranked]})
    ranks = [result["rank"] for result in results]
    summary = {"questions": len(results), "mrr": round(mrr(ranks), 3)}
    for k_value in KS:
        hits = [1.0 if rank is not None and rank <= k_value else 0.0 for rank in ranks]
        low, high = bootstrap_ci(hits)
        summary[f"recall@{k_value}"] = round(recall_at(ranks, k_value), 3)
        summary[f"recall@{k_value}_ci95"] = [round(low, 3), round(high, 3)]
    latencies.sort()
    summary["latency_ms_p50"] = round(1000 * latencies[len(latencies) // 2], 2) if latencies else None
    summary["latency_ms_p95"] = round(1000 * latencies[int(0.95 * (len(latencies) - 1))], 2) if latencies else None
    return results, summary


def bm25_search(chunks: list[Chunk], with_headings: bool = True):
    index = BM25([chunk.indexed_text(with_headings) for chunk in chunks])
    return lambda query, k: [position for position, _ in index.search(query, k)]


def _git_commit() -> str:
    """Short commit of the code that produced a run, with "-dirty" if tracked files had uncommitted changes."""
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                                check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return f"{commit}-dirty" if dirty else commit


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    parser.add_argument("--retriever", default="bm25", choices=["bm25", "dense", "hybrid"])
    parser.add_argument("--embed-model", default="nomic-embed-text-v2-moe",
                        help="Ollama model name, or a Hugging Face ID such as BAAI/bge-m3 (run locally)")
    parser.add_argument("--rerank", action="store_true", help="rerank the top 30 with BAAI/bge-reranker-v2-m3")
    parser.add_argument("--query-prefix", default="", help='e.g. "search_query: " for nomic models')
    parser.add_argument("--doc-prefix", default="", help='e.g. "search_document: " for nomic models')
    parser.add_argument("--chunk-tokens", type=int, default=400)
    parser.add_argument("--no-headings", action="store_true", help="index chunk text without its heading path")
    parser.add_argument("--save", action="store_true", help="write results under eval/runs/")
    args = parser.parse_args(argv)

    documents = corpus.load()
    questions = load_questions(split=args.split)
    if problems := check_questions(questions, documents):
        raise SystemExit("question set problems:\n" + "\n".join(problems))
    chunks = build_chunks(documents, args.chunk_tokens)
    texts = [chunk.indexed_text(not args.no_headings) for chunk in chunks]
    searches = []
    if args.retriever in ("bm25", "hybrid"):
        searches.append(bm25_search(chunks, with_headings=not args.no_headings))
    if args.retriever in ("dense", "hybrid"):
        backend = SentenceTransformerEmbedder if "/" in args.embed_model else OllamaEmbedder
        embedder = backend(args.embed_model, args.query_prefix, args.doc_prefix)
        searches.append(dense_search(embedder, texts))
    search = searches[0] if len(searches) == 1 else hybrid_search(searches)
    if args.rerank:
        search = rerank_search(search, texts)
    results, summary = evaluate(questions, chunks, search)
    config = {"split": args.split, "retriever": args.retriever, "chunk_tokens": args.chunk_tokens,
              "embed_model": args.embed_model if args.retriever != "bm25" else None,
              "query_prefix": args.query_prefix, "doc_prefix": args.doc_prefix,
              "rerank": "BAAI/bge-reranker-v2-m3" if args.rerank else None,
              "headings": not args.no_headings, "chunks": len(chunks), "git_commit": _git_commit(),
              "corpus_manifest_sha256": hashlib.sha256((corpus.ROOT / "manifest.csv").read_bytes()).hexdigest()[:16]}
    print(json.dumps({"config": config, "summary": summary}, indent=1))
    if args.save:
        run_dir = ROOT / "eval" / "runs" / datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir.mkdir(parents=True)
        (run_dir / "summary.json").write_text(json.dumps({"config": config, "summary": summary}, indent=1))
        (run_dir / "results.jsonl").write_text("".join(json.dumps(row) + "\n" for row in results))
        print(f"saved to {run_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
