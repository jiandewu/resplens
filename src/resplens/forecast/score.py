"""Scores for quantile forecasts: WIS, interval coverage, absolute error of the median, and a date-block bootstrap."""

from __future__ import annotations

import random
from collections import defaultdict

from .persistence import LEVELS


MEDIAN = LEVELS.index(0.5)
PAIRS = [(i, len(LEVELS) - 1 - i) for i in range(MEDIAN)]  # (0.01, 0.99), (0.025, 0.975), ..., (0.45, 0.55)
BOOTSTRAP = 10_000


def wis(quantiles: list[float], y: float) -> float:
    """Weighted interval score (Bracher et al. 2021) over the 11 central intervals and the median."""
    total = 0.5 * abs(y - quantiles[MEDIAN])
    for low, high in PAIRS:
        alpha = 2 * LEVELS[low]
        lower, upper = quantiles[low], quantiles[high]
        interval = (upper - lower) + 2 / alpha * max(lower - y, 0) + 2 / alpha * max(y - upper, 0)
        total += alpha / 2 * interval
    return total / (len(PAIRS) + 0.5)


def covered(quantiles: list[float], y: float, coverage: float) -> bool:
    low = LEVELS.index(round((1 - coverage) / 2, 3))
    return quantiles[low] <= y <= quantiles[len(LEVELS) - 1 - low]


def score(quantiles: list[float], y: float) -> dict:
    return {"wis": wis(quantiles, y), "ae": abs(y - quantiles[MEDIAN]),
            "cover50": covered(quantiles, y, 0.5), "cover95": covered(quantiles, y, 0.95)}


def relative(rows: list[dict], metric: str, system: str, baseline: str, seed: int = 0) -> dict:
    """Sum of metric for system over the sum for baseline, on the same forecasts, with a 95% bootstrap interval that
    resamples forecast dates (all states and targets of a date together).

    rows: one per (forecast, system), with keys date, system, and metric.
    """
    by_date = defaultdict(lambda: [0.0, 0.0])
    for row in rows:
        if row["system"] == system:
            by_date[row["date"]][0] += row[metric]
        elif row["system"] == baseline:
            by_date[row["date"]][1] += row[metric]
    dates = sorted(by_date)
    ratio = sum(by_date[d][0] for d in dates) / sum(by_date[d][1] for d in dates)
    rng = random.Random(seed)
    draws = []
    for _ in range(BOOTSTRAP):
        sample = rng.choices(dates, k=len(dates))
        draws.append(sum(by_date[d][0] for d in sample) / sum(by_date[d][1] for d in sample))
    draws.sort()
    return {"ratio": round(ratio, 3), "ci95": [round(draws[int(0.025 * BOOTSTRAP)], 3),
                                              round(draws[int(0.975 * BOOTSTRAP) - 1], 3)], "dates": len(dates)}
