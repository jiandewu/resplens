"""Okapi BM25 over a few thousand chunks; small enough to need no external index."""

from __future__ import annotations

import math
import re
from collections import Counter


TOKEN = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")
STOPWORDS = frozenset("a an and are as at be by for from has in is it its of on or that the this to was were "
                      "which with what when how does do".split())


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens; identifiers such as hospital_admission_count stay whole."""
    return [token for token in TOKEN.findall(text.lower()) if token not in STOPWORDS]


class BM25:
    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(text)) for text in documents]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.avg_length = sum(self.lengths) / max(1, len(self.lengths))
        frequency = Counter(term for doc in self.docs for term in doc)
        n = len(self.docs)
        self.idf = {term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in frequency.items()}

    def scores(self, query: str) -> list[float]:
        terms = [term for term in tokenize(query) if term in self.idf]
        result = []
        for doc, length in zip(self.docs, self.lengths):
            norm = self.k1 * (1 - self.b + self.b * length / self.avg_length)
            result.append(sum(self.idf[t] * doc[t] * (self.k1 + 1) / (doc[t] + norm) for t in terms if t in doc))
        return result

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        """(document index, score) of the top k documents with a positive score."""
        ranked = sorted(enumerate(self.scores(query)), key=lambda item: -item[1])
        return [(index, score) for index, score in ranked[:k] if score > 0]
