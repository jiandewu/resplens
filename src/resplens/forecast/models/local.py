"""One series at a time: persistence, seasonal naive, ARIMA and ETS (statsforecast)."""

from __future__ import annotations

import math

import numpy as np

from .. import persistence
from . import LEVELS, finish

SEASON = 52
N_JOBS = 16


class Persistence:
    def __init__(self, window: int):
        self.window = window

    def predict(self, items, targets, context=None):
        return [{t: finish(q) for t, q in persistence.forecast(item.series(), targets, self.window).items()}
                for item in items]


class SeasonalNaive:
    """Median: log1p of the value 52 weeks before the target plus (mean log1p of the last 4 weeks minus the mean of the
    same 4 weeks a year earlier). Quantiles: the same rule's errors at past origins whose target falls in the window."""

    def __init__(self, window: int):
        self.window = window

    @staticmethod
    def point(z: np.ndarray, t: int, k: int) -> float | None:
        if t - 55 < 0 or t + k - SEASON < 0:
            return None
        return z[t + k - SEASON] + z[t - 3:t + 1].mean() - z[t - 55:t - 51].mean()

    def predict(self, items, targets, context=None):
        out = []
        for item in items:
            z = np.log1p(np.asarray(item.values, dtype=float))
            n, forecast = len(z), {}
            for target in targets:
                k = item.k(target)
                median = self.point(z, n - 1, k)
                errors = [z[t + k] - self.point(z, t, k) for t in range(max(55, n - self.window - k), n - k)]
                if median is None or len(errors) < 10:
                    forecast = None
                    break
                forecast[target] = finish(np.expm1(median + np.quantile(errors, LEVELS)))
            out.append(forecast)
        return out


def _columns(alias: str) -> list[str]:
    """statsforecast column for each level: lo-98 for 0.01, ..., the mean for 0.5, ..., hi-98 for 0.99."""
    columns = []
    for level in LEVELS:
        width = round(abs(1 - 2 * level) * 100)
        columns.append(alias if width == 0 else f"{alias}-{'lo' if level < 0.5 else 'hi'}-{width}")
    return columns


class StatsModel:
    """AutoARIMA or AutoETS on log1p of the last `context` weeks, non-seasonal, Gaussian prediction intervals."""

    def __init__(self, kind: str, context: int):
        self.kind, self.context = kind, context

    def _model(self):
        from statsforecast.models import AutoARIMA, AutoETS
        return AutoARIMA(season_length=1) if self.kind == "arima" else AutoETS(season_length=1)

    def _fit(self, items, targets, n_jobs):
        import pandas as pd
        from statsforecast import StatsForecast
        frames, ks = [], {}
        for item in items:
            z = np.log1p(np.asarray(item.values[-self.context:], dtype=float))
            frames.append(pd.DataFrame({"unique_id": item.state, "ds": np.arange(len(z)), "y": z}))
            ks[item.state] = [item.k(t) for t in targets]
        model = self._model()
        levels = sorted({round(abs(1 - 2 * q) * 100) for q in LEVELS} - {0})
        h = max(max(k) for k in ks.values())
        fc = StatsForecast(models=[model], freq=1, n_jobs=n_jobs).forecast(df=pd.concat(frames), h=h, level=levels)
        columns = _columns(repr(model))
        out = {}
        for state, rows in fc.groupby("unique_id"):
            rows = rows.sort_values("ds")
            forecast = {t: finish(np.expm1(rows.iloc[k - 1][columns].to_numpy(dtype=float)))
                        for t, k in zip(targets, ks[state])}
            out[state] = None if any(q is None for q in forecast.values()) else forecast
        return [out.get(item.state) for item in items]

    def predict(self, items, targets, context=None):
        try:
            return self._fit(items, targets, n_jobs=N_JOBS)
        except Exception as exc:  # noqa: BLE001  (then one series at a time, so one failure costs one fallback)
            print(f"{self.kind} batch {items[0].date}: {exc}; retrying one series at a time", flush=True)
        out = []
        for item in items:
            try:
                out.extend(self._fit([item], targets, n_jobs=1))
            except Exception as exc:  # noqa: BLE001
                print(f"{self.kind} {item.state} {item.date}: {exc}", flush=True)
                out.append(None)
        return out


MODELS = {"persistence": Persistence, "seasonal_naive": SeasonalNaive,
          "arima": lambda context: StatsModel("arima", context), "ets": lambda context: StatsModel("ets", context)}
