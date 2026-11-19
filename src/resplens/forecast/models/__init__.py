"""Models for the full B1 benchmark (plan: docs/forecast-eval.md, "Implementation details").

Every model has the same interface: `predict(items, targets, context) -> list[dict[target, quantiles] | None]`, one
entry per item, with the 23 quantile levels of `LEVELS` on the count scale. None means the model could not forecast
that item; the run then uses persistence for it and counts a fallback.
"""

from __future__ import annotations

import math

import numpy as np

from ..persistence import LEVELS

GRID = {  # tuned on dev, per pathogen (plan table)
    "persistence": [{"window": 52}, {"window": 104}, {"window": 156}],
    "seasonal_naive": [{"window": 52}, {"window": 104}],
    "arima": [{"context": 104}, {"context": 208}],
    "ets": [{"context": 104}, {"context": 208}],
    "lightgbm": [{"leaves": leaves, "learning_rate": rate} for leaves in (15, 31) for rate in (0.03, 0.1)],
    "chronos2": [{"context": 104}, {"context": 208}, {"context": None}],
    "tabpfn": [{"window": 52}, {"window": 104}],
}
UNTUNED = {"lightgbm_ed": "lightgbm", "chronos2_synth": "chronos2"}  # use the named model's chosen settings
# model -> pathogen -> settings; chosen on dev (capped scores) and recorded in the plan on 2026-11-10, before any test
# forecast (eval/forecast-b1/dev-selection.json)
CHOSEN: dict[str, dict[str, dict]] = {
    "persistence": {"covid": {"window": 156}, "influenza": {"window": 104}, "rsv": {"window": 104}},
    "seasonal_naive": {"covid": {"window": 104}, "influenza": {"window": 104}, "rsv": {"window": 52}},
    "arima": {"covid": {"context": 208}, "influenza": {"context": 104}, "rsv": {"context": 104}},
    "ets": {"covid": {"context": 208}, "influenza": {"context": 208}, "rsv": {"context": 104}},
    "lightgbm": {p: {"leaves": 15, "learning_rate": 0.03} for p in ("covid", "influenza", "rsv")},
    "chronos2": {"covid": {"context": None}, "influenza": {"context": None}, "rsv": {"context": 104}},
    "tabpfn": {p: {"window": 104} for p in ("covid", "influenza", "rsv")},
}
CAP = 5  # plan, change of 2026-11-10: every quantile is capped at CAP x the series' observed maximum when scored


def cap(quantiles: list[float], history_max: float) -> list[float]:
    """Quantiles capped at CAP x the largest value of the input series (applied to every model at scoring time; the
    raw forecasts are kept, so uncapped scores remain available)."""
    return [min(q, CAP * history_max) for q in quantiles]


def config_name(settings: dict) -> str:
    return "-".join(f"{k}{'all' if v is None else v}" for k, v in settings.items())


def interpolate(native: list[float], values: list[float]) -> list[float]:
    """Quantiles at LEVELS from quantiles at other levels: linear in the level between neighbouring native levels
    (levels outside the native range take the nearest native value)."""
    return list(np.interp(LEVELS, native, values))


def finish(quantiles) -> list[float] | None:
    """Sorted, clipped at 0; None if any value is not finite."""
    values = [float(q) for q in quantiles]
    if len(values) != len(LEVELS) or not all(math.isfinite(v) for v in values):
        return None
    return sorted(max(0.0, v) for v in values)


def get(name: str, settings: dict):
    """A model instance by name (imports heavy libraries only when needed)."""
    if name in ("persistence", "seasonal_naive", "arima", "ets"):
        from . import local
        return local.MODELS[name](**settings)
    if name in ("lightgbm", "lightgbm_ed", "tabpfn"):
        from . import tabular
        return tabular.MODELS[name](**settings)
    if name in ("chronos2", "chronos2_synth"):
        from . import foundation
        return foundation.Chronos2(synth=name == "chronos2_synth", **settings)
    raise KeyError(name)
