"""Persistence baseline: the last observed value, with quantiles from the series' own past changes."""

from __future__ import annotations

import math
from datetime import date

import numpy as np

from .vintage import Series, last_observed


LEVELS = (0.01, 0.025, *[round(0.05 * i, 2) for i in range(1, 20)], 0.975, 0.99)
WINDOW = 104  # weeks of past changes


def weeks_between(first: str, second: str) -> int:
    return (date.fromisoformat(second) - date.fromisoformat(first)).days // 7


def forecast(series: Series, targets: list[str], window: int = WINDOW) -> dict[str, list[float]]:
    """For a target k weeks after the last observed week: log1p(last) plus the quantiles of past k-week changes of
    log1p(value) over the last `window` weeks, transformed back. The changes are used together with their negatives,
    so the median is exactly the last observed value, as the plan specifies."""
    last_week, last = last_observed(series)
    values = [value for week, value in series if week <= last_week]
    logs = [None if value is None else math.log1p(value) for value in values]
    out = {}
    for target in targets:
        k = weeks_between(last_week, target)
        start = max(k, len(logs) - window)
        changes = [logs[t] - logs[t - k] for t in range(start, len(logs))
                   if logs[t] is not None and logs[t - k] is not None]
        changes = changes + [-change for change in changes] if changes else [0.0]
        quantiles = np.quantile(changes, LEVELS)
        out[target] = [max(0.0, math.expm1(math.log1p(last) + q)) for q in quantiles]
    return out
