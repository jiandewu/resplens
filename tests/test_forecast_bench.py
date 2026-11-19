import gzip
import json
import math

import numpy as np
import pytest

from resplens.forecast import bench, inputs, models
from resplens.forecast.inputs import Item, week_at
from resplens.forecast.models import local, tabular
from resplens.forecast.persistence import LEVELS

FIRST = "2022-01-01"  # a Saturday


def item(values, state="ZZ", pathogen="influenza", day=None, ed=None):
    last = week_at(FIRST, len(values) - 1)
    from datetime import date, timedelta
    day = day or (date.fromisoformat(last) + timedelta(days=6)).isoformat()  # the Friday after the last week
    return Item(state, pathogen, day, FIRST, [float(v) for v in values], True, ed or {})


def test_fill_drops_edges_and_interpolates_log1p():
    series = [("w0", None), ("w1", 3.0), ("w2", None), ("w3", 15.0), ("w4", None)]
    first, values = inputs.fill(series)
    assert first == "w1" and len(values) == 3
    assert values[1] == pytest.approx(math.expm1((math.log1p(3) + math.log1p(15)) / 2))


def test_minimum_history_counts_observed_weeks_in_the_last_52():
    weeks = [(week_at(FIRST, i), None if i < 30 else 5) for i in range(60)]
    assert inputs.enough_history(weeks)  # 30 observed of the last 52
    sparse = [(w, v if i % 3 == 0 else None) for i, (w, v) in enumerate(weeks)]
    assert not inputs.enough_history(sparse)


def test_interpolate_levels_and_finish():
    native = [0.01, 0.05, 0.5, 0.95, 0.99]
    q = models.interpolate(native, [0, 4, 10, 16, 20])
    assert q[LEVELS.index(0.025)] == pytest.approx(1.5) and q[LEVELS.index(0.5)] == pytest.approx(10)
    assert models.finish([-1.0] + [1.0] * 22)[0] == 0.0
    assert models.finish([float("nan")] * 23) is None


def test_cap_limits_quantiles_at_a_multiple_of_the_history_maximum():
    assert models.cap([1.0, 40.0, 1e14], history_max=10.0) == [1.0, 40.0, models.CAP * 10.0]


def test_persistence_median_is_the_last_value_for_every_window():
    it = item([10, 12, 9, 14, 11] * 40)
    targets = ["2025-01-04"]
    for window in (52, 104, 156):
        q = local.Persistence(window).predict([it], [week_at(FIRST, 200)])[0]
        assert list(q.values())[0][LEVELS.index(0.5)] == pytest.approx(11)


def test_seasonal_naive_repeats_last_year_on_a_periodic_series_and_falls_back_when_short():
    pattern = [10 + 50 * (1 + math.sin(2 * math.pi * i / 52)) for i in range(52)]
    it = item(pattern * 4)
    target = week_at(FIRST, len(it.values) + 1)  # k = 2
    q = local.SeasonalNaive(104).predict([it], [target])[0][target]
    assert q[LEVELS.index(0.5)] == pytest.approx(pattern[(len(it.values) + 1) % 52], rel=1e-6)
    assert q[0] == pytest.approx(q[-1], rel=1e-6)  # the rule is exact here, so the interval has no width
    assert local.SeasonalNaive(104).predict([item(pattern)], [target])[0] is None


def test_statsforecast_columns_match_the_levels():
    columns = local._columns("AutoARIMA")
    assert columns[0] == "AutoARIMA-lo-98" and columns[1] == "AutoARIMA-lo-95"
    assert columns[LEVELS.index(0.5)] == "AutoARIMA" and columns[-1] == "AutoARIMA-hi-98"


def test_tabular_rows_use_only_the_series_history():
    it = item(range(1, 41))
    X, y = tabular.training_rows([it], k=2, with_ed=False)
    z = np.log1p(np.arange(1, 41, dtype=float))
    assert len(y) == 40 - 2 - tabular.MIN_ORIGIN and y[0] == pytest.approx(z[9] - z[7])
    assert X[0][0] == pytest.approx(z[7]) and X[0][7] == pytest.approx(z[0])
    Xw, _ = tabular.training_rows([it], k=2, with_ed=False, window=10)
    assert len(Xw) == 10
    ed = item(range(1, 41), ed={week_at(FIRST, 7): 2.0})
    row = tabular.features(ed, 7, z, with_ed=True)
    assert row[-4] == pytest.approx(math.log1p(2.0)) and math.isnan(row[-3])


def test_lightgbm_returns_sorted_quantiles(monkeypatch):
    pytest.importorskip("lightgbm")  # the forecast extra; CI installs the base package only
    monkeypatch.setattr(tabular, "TREES", 20)
    rng = np.random.default_rng(0)
    items = [item(np.exp(3 + np.sin(np.arange(120) / 8) + rng.normal(0, 0.1, 120)), state=s) for s in ("AA", "BB")]
    target = week_at(FIRST, 121)
    model = tabular.LightGBM(leaves=15, learning_rate=0.1)
    out = model.predict(items, [target], {"refit_key": "x", "train_items": items})
    q = out[0][target]
    assert q == sorted(q) and len(q) == len(LEVELS) and q[0] < q[-1]


def write_cache(path, rows):
    with gzip.open(path, "wt") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_run_score_and_select_on_a_tiny_cache(tmp_path, monkeypatch):
    pattern = [20 + 10 * math.sin(2 * math.pi * i / 52) for i in range(160)]
    days = [(lambda d: d)(week_at(FIRST, n - 1)) for n in (150, 151)]
    from datetime import date, timedelta
    fridays = [(date.fromisoformat(d) + timedelta(days=6)).isoformat() for d in days]
    rows = []
    for n, day in zip((150, 151), fridays):
        for pathogen in inputs.PATHOGENS:
            rows.append({"date": day, "pathogen": pathogen, "state": "ZZ", "first_week": FIRST,
                         "raw": pattern[:n], "ed": {}})
    rows.append({"date": fridays[0], "pathogen": "rsv", "state": "YY", "first_week": FIRST,
                 "raw": [None] * 40 + [3] * 10, "ed": {}})  # too little history: removed
    cache = tmp_path / "inputs.jsonl.gz"
    write_cache(cache, rows)
    truth = {week_at(FIRST, i): v for i, v in enumerate(pattern)}
    monkeypatch.setattr(bench, "truth", lambda ds, state, pathogen: truth)
    monkeypatch.setattr(bench, "_git_commit", lambda inputs: "test")
    runs = []
    for settings in models.GRID["persistence"]:
        run_dir = bench.run("dev", "persistence", "revised", settings, source=cache, dates=fridays,
                            out_dir=tmp_path / "runs")
        scored = bench.score_run(run_dir, ds=object(), source=cache)
        assert all(r["history_max"] == pytest.approx(max(pattern[:150 if r["date"] == fridays[0] else 151]))
                   for r in scored)
        runs.append(run_dir)
    forecasts = [json.loads(line) for line in (runs[0] / "forecasts.jsonl").read_text().splitlines()]
    assert len(forecasts) == 6 and not any(f["fallback"] for f in forecasts)
    assert json.loads((runs[0] / "removed.json").read_text()) == {"rsv": 1}
    result = bench.select(runs)
    assert set(result["persistence"]["influenza"]["mean_wis"]) == {"window52", "window104", "window156"}
    assert result["persistence"]["influenza"]["chosen"] in models.GRID["persistence"]


def test_test_runs_need_settings_chosen_on_dev(monkeypatch):
    monkeypatch.setattr(models, "CHOSEN", {})
    with pytest.raises(ValueError, match="no settings chosen"):
        bench.settings_for("chronos2_synth", "test", None)
    monkeypatch.setattr(models, "CHOSEN", {"chronos2": {p: {"context": 104} for p in inputs.PATHOGENS}})
    assert bench.settings_for("chronos2_synth", "test", None)["rsv"] == {"context": 104}


def test_ensemble_is_the_median_of_capped_members_and_flags_fallbacks(tmp_path, monkeypatch):
    target = "2025-04-05"
    for i, model in enumerate(bench.ENSEMBLE):
        run_dir = tmp_path / f"20250101-00000{i}-test-{model}-chosen-realtime"
        run_dir.mkdir()
        high = 1e9 if model == "tabpfn" else 10.0 * (i + 1)  # tabpfn's upper value is capped at 5 x 10 = 50
        row = {"date": "2025-04-04", "pathogen": "influenza", "state": "ZZ", "last_week": "2025-03-29",
               "targets": [target], "k": [1], "quantiles": {target: [float(i)] * 22 + [high]},
               "fallback": model == "ets"}
        (run_dir / "forecasts.jsonl").write_text(json.dumps(row) + "\n")
        (run_dir / "removed.json").write_text("{}")
    monkeypatch.setattr(bench, "history_max", lambda *a, **k: {("2025-04-04", "influenza", "ZZ"): 10.0})
    monkeypatch.setattr(bench, "_git_commit", lambda inputs: "test")
    out = bench.ensemble("test", "realtime", runs=tmp_path)
    row = json.loads((out / "forecasts.jsonl").read_text())
    q = row["quantiles"][target]
    assert q[0] == pytest.approx(2.5)  # median of 0..5
    assert q[-1] == pytest.approx(np.median([10, 20, 30, 40, 50, 50]))
    assert row["fallback"] and row["fallback_members"] == ["ets"]


def test_analysis_removes_fallback_rows_for_every_system():
    from resplens.forecast import bench_analyze as ba
    row = {"wis": 1.0, "fallback": False}
    scores = {("persistence", "realtime"): {("p", "S", "d1", "t"): row, ("p", "S", "d2", "t"): row},
              ("arima", "realtime"): {("p", "S", "d1", "t"): {**row, "fallback": True}, ("p", "S", "d2", "t"): row}}
    assert ba.common(scores, "realtime", ["persistence", "arima"]) == [("p", "S", "d2", "t")]
    assert len(ba.common(scores, "realtime", ["persistence", "arima"], keep_fallback=True)) == 2
