import json
import math
import random

import pytest

from resplens.forecast import analyze, llm, persistence, score, vintage
from resplens.forecast.persistence import LEVELS


def pinball_wis(quantiles, y):
    """WIS as the weighted sum of quantile losses (Bracher et al. 2021, eq. 4), as an independent check."""
    losses = [2 * ((y < q) - tau) * (q - y) for tau, q in zip(LEVELS, quantiles)]
    return sum(losses) / 2 / (len(score.PAIRS) + 0.5)


def test_wis_of_a_point_forecast_is_its_absolute_error():
    assert score.wis([10.0] * len(LEVELS), 13) == pytest.approx(3.0)


def test_wis_matches_the_quantile_loss_form():
    rng = random.Random(0)
    for _ in range(20):
        quantiles = sorted(rng.uniform(0, 100) for _ in LEVELS)
        y = rng.uniform(-10, 110)
        assert score.wis(quantiles, y) == pytest.approx(pinball_wis(quantiles, y))


def test_coverage_and_relative_scores():
    quantiles = list(range(len(LEVELS)))  # value = index: 0.25 -> 6, 0.75 -> 16; 0.025 -> 1, 0.975 -> 21
    assert score.covered(quantiles, 6, 0.5) and not score.covered(quantiles, 17, 0.5)
    assert score.covered(quantiles, 21, 0.95) and not score.covered(quantiles, 0.5, 0.95)
    rows = [{"date": d, "system": s, "wis": w} for d, s, w in
            [("a", "x", 1), ("a", "p", 2), ("b", "x", 3), ("b", "p", 4)]]
    result = score.relative(rows, "wis", "x", "p")
    assert result["ratio"] == pytest.approx(4 / 6, abs=1e-3) and result["ci95"][0] <= 0.667 <= result["ci95"][1]


def test_persistence_median_is_the_last_value_and_uses_the_gap():
    series = [(f"2025-01-{d:02d}", v) for d, v in [(4, 10), (11, 20), (18, 15), (25, None)]]
    out = persistence.forecast(series, ["2025-02-01", "2025-02-15"])
    for quantiles in out.values():
        assert quantiles[LEVELS.index(0.5)] == pytest.approx(15) and quantiles == sorted(quantiles)
    # the last observed week is 2025-01-18, so the first target is 2 weeks ahead; the only 2-week change is
    # d = log(16/11), used with -d, and numpy's linear interpolation puts the 0.99 quantile at 0.98 d
    assert max(out["2025-02-01"]) == pytest.approx(16 * math.exp(0.98 * math.log(16 / 11)) - 1)
    flat = persistence.forecast([("2025-01-04", 7), ("2025-01-11", 7)], ["2025-01-18"])
    assert flat["2025-01-18"] == pytest.approx([7.0] * len(LEVELS))


def test_vintage_series_real_time_and_revised(ds):
    assert vintage.real_time(ds, "ZZ", "covid", "2026-10-08") == [("2026-09-26", 88), ("2026-10-03", 55)]
    assert vintage.real_time(ds, "ZZ", "covid", "2026-10-15")[-1] == ("2026-10-03", 60)
    assert vintage.revised(ds, "ZZ", "covid", "2026-10-03") == [
        ("2026-09-05", 40), ("2026-09-12", 44), ("2026-09-19", None), ("2026-09-26", 90), ("2026-10-03", 60)]
    assert vintage.truth(ds, "ZZ", "covid", ["2026-10-10", "2026-09-19"]) == {"2026-10-10": 65, "2026-09-19": None}
    assert vintage.targets("2025-04-04") == ["2025-04-05", "2025-04-12", "2025-04-19", "2025-04-26"]
    assert vintage.standard_last_week("2025-04-04") == "2025-03-29"


def reply(content, done_reason="stop"):
    return {"message": {"role": "assistant", "content": content}, "done_reason": done_reason,
            "prompt_eval_count": 1, "eval_count": 1, "wall_seconds": 0.0}


def answer(**overrides):
    values = {key: list(range(len(LEVELS))) for key in llm.KEYS}
    return json.dumps({**values, **overrides})


def test_parse_reports_usable_errors():
    assert llm.parse(reply("", "length"))[1].startswith("the answer was cut off")
    assert llm.parse(reply("not json"))[1] == "the answer is not valid JSON"
    assert llm.parse(reply(answer(week_2=[1] * 22)))[1] == "week_2 has 22 values; return exactly 23"
    assert "not a finite number" in llm.parse(reply(answer(week_3=["x"] * 23)))[1]
    assert llm.parse(reply(answer()))[1] is None


def scripted(*contents):
    replies = iter(contents)
    seen = []

    def chat(model, messages, think, seed=0):
        seen.append([m["content"] for m in messages])
        return reply(next(replies))
    chat.seen = seen
    return chat


def test_forecast_repairs_once_then_fails():
    targets = ["2025-04-05", "2025-04-12", "2025-04-19", "2025-04-26"]
    chat = scripted(answer(week_1=[1] * 22), answer(week_4=[5, 3, *range(21)]))
    out = llm.forecast("m", False, "prompt", targets, chat_fn=chat)
    assert out["repaired"] and out["sorted"] and not out["clipped"] and out["quantiles"]["2025-04-26"][:3] == [0, 1, 2]
    assert "week_1 has 22 values" in chat.seen[1][-1]
    failed = llm.forecast("m", False, "prompt", targets, chat_fn=scripted("bad", "bad"))
    assert failed["quantiles"] is None and len(failed["turns"]) == 2


def test_prompt_lists_the_series_and_last_year():
    series = [(f"2024-{m:02d}-01", 1) for m in range(1, 13)] + [("2025-01-04", None)]
    text = llm.prompt("Zedland", "ZZ", "influenza", "2025-01-10", series, ["2025-01-11"] * 4, "h26_last_year")
    assert "2025-01-04: missing" in text and "The same weeks one year earlier:" in text
    assert "week_1 = week ending 2025-01-11" in text and "exactly 23 numbers" in text
    assert "one year earlier" not in llm.prompt("Zedland", "ZZ", "influenza", "2025-01-10", series,
                                                ["2025-01-11"] * 4, "h26")


def _scores(values, failed=()):
    """(state, date, target) -> row for one system, from {date: wis}."""
    return {("ZZ", d, d): {"state": "ZZ", "date": d, "target": d, "horizon": 1, "truth": 1.0, "failed": d in failed,
                           **({} if d in failed else {"wis": w, "ae": w, "cover50": True, "cover95": True})}
            for d, w in values.items()}


def test_analysis_uses_common_forecasts_and_the_failure_sensitivity():
    dates = ["a", "b", "c"]
    scores = {("persistence", "realtime"): _scores({d: 2.0 for d in dates}),
              ("gemma", "realtime"): _scores({"a": 1.0, "b": 1.0, "c": 9.0}, failed={"c"}),
              ("gpt-oss", "realtime"): _scores({d: 3.0 for d in dates})}
    keys = analyze.common(scores, "realtime", ["persistence", "gemma", "gpt-oss"])
    assert [k[1] for k in keys] == ["a", "b"]  # c failed for gemma, so it is dropped for every system
    result = analyze.analyze(scores, {})["versions"]["realtime"]
    assert result["gemma"]["relative_wis"]["ratio"] == 0.5 and result["gpt-oss"]["relative_wis"]["ratio"] == 1.5
    assert result["gpt-oss"]["relative_wis"]["verdict"] == "worse"
    # failed forecasts replaced by persistence: (1 + 1 + 2) / 6
    assert result["gemma"]["sensitivity_failures_as_persistence"]["ratio"] == pytest.approx(0.667, abs=1e-3)


def test_revision_effect_is_revised_minus_real_time():
    dates = {"a": 1.0, "b": 1.0}
    scores = {("persistence", "realtime"): _scores({d: 2.0 for d in dates}),
              ("persistence", "revised"): _scores({d: 2.0 for d in dates}),
              ("gemma", "realtime"): _scores({d: 1.0 for d in dates}),
              ("gemma", "revised"): _scores({d: 1.5 for d in dates})}
    keys = analyze.common(scores, "realtime", ["persistence", "gemma"])
    effect = analyze.revision_effect(scores, "gemma", keys, keys)
    assert effect["difference"] == 0.25 and effect["ci95"] == [0.25, 0.25]
