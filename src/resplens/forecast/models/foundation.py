"""Chronos-2 and Chronos-2-Synth, zero-shot, univariate, on raw values (the model scales internally)."""

from __future__ import annotations

import numpy as np

from . import finish, interpolate

REPOS = {False: ("amazon/chronos-2", "29ec3766d36d6f73f0696f85560a422f50e8498c"),
         True: ("autogluon/chronos-2-synth", "3607918a9fd027d5c465d8213e46b98e2c041cea")}
_PIPELINES = {}


def pipeline(synth: bool):
    if synth not in _PIPELINES:
        from chronos import Chronos2Pipeline
        repo, revision = REPOS[synth]
        _PIPELINES[synth] = Chronos2Pipeline.from_pretrained(repo, revision=revision, device_map="cuda")
    return _PIPELINES[synth]


class Chronos2:
    def __init__(self, context: int | None, synth: bool = False):
        self.context, self.synth = context, synth

    def predict(self, items, targets, context=None):
        model = pipeline(self.synth)
        native = list(model.quantiles)
        inputs = [np.asarray(item.values if self.context is None else item.values[-self.context:], dtype=np.float32)
                  for item in items]
        ks = [[item.k(t) for t in targets] for item in items]
        quantiles, _ = model.predict_quantiles(inputs, prediction_length=max(max(k) for k in ks),
                                               quantile_levels=native)
        out = []
        for q, item_ks in zip(quantiles, ks):
            q = q[0].float().cpu().numpy()  # (prediction_length, levels) for the single target variable
            forecast = {t: finish(interpolate(native, q[k - 1])) for t, k in zip(targets, item_ks)}
            out.append(None if any(v is None for v in forecast.values()) else forecast)
        return out
