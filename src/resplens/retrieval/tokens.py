"""Exact token counts for chunk budgets, using the embedding model's own tokenizer.

Word-based estimates were off by up to 5.8x on this corpus (URLs, identifiers, tables),
which overflowed the embedding model's 512-token input. nomic-embed-text-v2-moe and bge-m3
share the XLM-RoBERTa tokenizer; its counts matched Ollama's exactly on a 196-chunk sample.
"""

from __future__ import annotations

import hashlib
import urllib.request
from functools import lru_cache
from pathlib import Path

from tokenizers import Tokenizer


TOKENIZER_URL = ("https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe/resolve/"
                 "1066b6599d099fbb93dfcb64f9c37a7c9e503e85/tokenizer.json")
TOKENIZER_SHA256 = "3a56def25aa40facc030ea8b0b87f3688e4b3c39eb8b45d5702b3a1300fe2a20"  # gitleaks:allow (checksum of a public file)
CACHE = Path(__file__).resolve().parents[3] / ".cache" / "tokenizers" / "nomic-v2-moe-tokenizer.json"


@lru_cache(maxsize=1)
def _tokenizer() -> Tokenizer:
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(TOKENIZER_URL, timeout=120) as response:
            CACHE.write_bytes(response.read())
    if hashlib.sha256(CACHE.read_bytes()).hexdigest() != TOKENIZER_SHA256:
        raise RuntimeError(f"{CACHE} does not match the pinned tokenizer; delete it and retry")
    return Tokenizer.from_file(str(CACHE))


@lru_cache(maxsize=200_000)
def count_tokens(text: str) -> int:
    """Tokens the embedding model sees for ``text``, including its special tokens."""
    return len(_tokenizer().encode(text).ids)
