"""Global models on lag features: LightGBM (quantile loss), LightGBM + NSSP ED visits, TabPFN v2.

A row is one origin week t of one location's series z = log1p(values) and one horizon k. Target: z[t+k] - z[t].
Features: z[t-0..t-7], z[t]-z[t-1], z[t]-z[t-4], week of year of t (sine, cosine), mean of z over the last 52 weeks
(at least 26 present, otherwise over what there is); with ED visits also log1p(ED percent) at weeks t-0..t-3 (NaN when
missing, which LightGBM handles).
"""

from __future__ import annotations

import hashlib
import os
from datetime import date
from pathlib import Path

import numpy as np

from . import LEVELS, finish
from ..inputs import week_at

LAGS, ED_LAGS, MIN_ORIGIN = 8, 4, 7
TREES, MIN_LEAF = 300, 20
REFIT_EVERY = 4  # forecast dates of a run; bench.run passes the refit date in the context
TABPFN_REPO, TABPFN_REVISION = "Prior-Labs/TabPFN-v2-reg", "02a44705ff7790b50cded404bc59adb94da456a1"
TABPFN_FILE = "tabpfn-v2-regressor.ckpt"
TABPFN_SHA256 = "2ab5a07d5c41dfe6db9aa7ae106fc6de898326c2765be66505a07e2868c10736"
TABPFN_ESTIMATORS = 8


def features(item, t: int, z: np.ndarray, with_ed: bool) -> list[float]:
    week = date.fromisoformat(week_at(item.first_week, t))
    angle = 2 * np.pi * week.timetuple().tm_yday / 365.25
    row = [*z[t - LAGS + 1:t + 1][::-1], z[t] - z[t - 1], z[t] - z[t - 4], np.sin(angle), np.cos(angle),
           z[max(0, t - 51):t + 1].mean()]
    if with_ed:
        for lag in range(ED_LAGS):
            value = item.ed.get(week_at(item.first_week, t - lag))
            row.append(np.log1p(value) if value is not None else np.nan)
    return row


def training_rows(items, k: int, with_ed: bool, window: int | None = None):
    """Rows from every item's history: origins t with t+k observed; with a window, only targets in the last
    `window` weeks of each series."""
    X, y = [], []
    for item in items:
        z = np.log1p(np.asarray(item.values, dtype=float))
        first = MIN_ORIGIN if window is None else max(MIN_ORIGIN, len(z) - window - k)
        for t in range(first, len(z) - k):
            X.append(features(item, t, z, with_ed))
            y.append(z[t + k] - z[t])
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def origin_rows(items, with_ed: bool):
    zs = [np.log1p(np.asarray(item.values, dtype=float)) for item in items]
    X = [features(item, len(z) - 1, z, with_ed) for item, z in zip(items, zs)]
    return np.asarray(X, dtype=float), np.asarray([z[-1] for z in zs])


def _assemble(items, targets, by_k, last):
    """by_k: k -> array (items x levels) of predicted changes. Returns forecasts on the count scale."""
    out = []
    for i, item in enumerate(items):
        forecast = {}
        for target in targets:
            k = item.k(target)
            forecast[target] = finish(np.expm1(last[i] + np.sort(by_k[k][i])))
        out.append(None if any(q is None for q in forecast.values()) else forecast)
    return out


class LightGBM:
    """One model per (pathogen, k, level), refit every REFIT_EVERY forecast dates on the series as they stood on the
    refit date. context: {"refit_key": str, "train_items": items as of the refit date}."""

    def __init__(self, leaves: int, learning_rate: float, with_ed: bool = False):
        self.leaves, self.learning_rate, self.with_ed = leaves, learning_rate, with_ed
        self.fitted = {}

    def _models(self, key, train_items, k):
        if (key, k) not in self.fitted:
            import lightgbm as lgb
            X, y = training_rows(train_items, k, self.with_ed)
            self.fitted[(key, k)] = [
                lgb.LGBMRegressor(objective="quantile", alpha=level, n_estimators=TREES, num_leaves=self.leaves,
                                  learning_rate=self.learning_rate, min_child_samples=MIN_LEAF, random_state=0,
                                  deterministic=True, force_row_wise=True, n_jobs=N_THREADS, verbose=-1).fit(X, y)
                for level in LEVELS]
            self.fitted = {key_k: m for key_k, m in self.fitted.items() if key_k[0] == key}  # keep one refit
        return self.fitted[(key, k)]

    def predict(self, items, targets, context):
        X, last = origin_rows(items, self.with_ed)
        by_k = {}
        for k in sorted({item.k(t) for item in items for t in targets}):
            models = self._models(context["refit_key"], context["train_items"], k)
            by_k[k] = np.column_stack([m.predict(X) for m in models])
        return _assemble(items, targets, by_k, last)


def tabpfn_checkpoint() -> Path:
    from huggingface_hub import hf_hub_download
    path = Path(hf_hub_download(TABPFN_REPO, TABPFN_FILE, revision=TABPFN_REVISION))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != TABPFN_SHA256:
        raise RuntimeError(f"TabPFN checkpoint SHA-256 {digest} != {TABPFN_SHA256}")
    return path


class TabPFN:
    """TabPFN v2 regressor, refit (in context) on every forecast date with all locations' rows whose target falls in
    the last `window` weeks."""

    def __init__(self, window: int):
        self.window = window
        self.path = None

    def predict(self, items, targets, context=None):
        from tabpfn import TabPFNRegressor
        self.path = self.path or tabpfn_checkpoint()
        X, last = origin_rows(items, False)
        by_k = {}
        for k in sorted({item.k(t) for item in items for t in targets}):
            X_train, y_train = training_rows(items, k, False, window=self.window)
            model = TabPFNRegressor(model_path=self.path, device="cuda", random_state=0,
                                    n_estimators=TABPFN_ESTIMATORS)
            model.fit(X_train, y_train)
            by_k[k] = np.column_stack(model.predict(X, output_type="quantiles", quantiles=list(LEVELS)))
        return _assemble(items, targets, by_k, last)


N_THREADS = int(os.environ.get("RESPLENS_THREADS", "16"))
MODELS = {"lightgbm": LightGBM, "lightgbm_ed": lambda **s: LightGBM(with_ed=True, **s), "tabpfn": TabPFN}
