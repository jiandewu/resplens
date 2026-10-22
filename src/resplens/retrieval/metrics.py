"""Retrieval metrics matched on evidence quotes, so different chunkings stay comparable."""

from __future__ import annotations

import random
import re


def normalize(text: str) -> str:
    """Lowercase, Markdown emphasis and code marks removed, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"[*`_]", "", text.lower())).strip()


def contains(chunk_text: str, quote: str) -> bool:
    return normalize(quote) in normalize(chunk_text)


def first_hit_rank(ranked_texts: list[str], quotes: list[str]) -> int | None:
    """1-based rank at which every quote has appeared in some retrieved chunk; None if never."""
    remaining = {normalize(quote) for quote in quotes}
    for rank, text in enumerate(ranked_texts, start=1):
        normalized = normalize(text)
        remaining = {quote for quote in remaining if quote not in normalized}
        if not remaining:
            return rank
    return None


def recall_at(ranks: list[int | None], k: int) -> float:
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks) if ranks else 0.0


def mrr(ranks: list[int | None]) -> float:
    return sum(1 / rank for rank in ranks if rank) / len(ranks) if ranks else 0.0


def bootstrap_ci(values: list[float], iterations: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap interval of the mean over questions."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=len(values))) / len(values) for _ in range(iterations))
    return means[int(0.025 * iterations)], means[int(0.975 * iterations) - 1]
