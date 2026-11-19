import asyncio
import json

import numpy as np
import pytest

from resplens.data import DataError
from resplens.forecast import tool
from resplens.forecast.inputs import Item, week_at
from resplens.forecast.models import tabular

FIRST = "2022-01-01"  # a Saturday


@pytest.fixture
def forecaster(monkeypatch):
    pytest.importorskip("lightgbm")  # the forecast extra; CI installs the base package only
    monkeypatch.setattr(tabular, "TREES", 20)
    rng = np.random.default_rng(0)

    def load(pathogen):
        return [Item(state, pathogen, "", FIRST, list(np.exp(3 + np.sin(np.arange(n) / 8) + rng.normal(0, 0.1, n))))
                for state, n in (("AA", 120), ("BB", 118))]
    return tool.Forecaster(load=load)


def test_forecast_gives_four_weeks_with_ordered_intervals(forecaster):
    out = forecaster.forecast("aa", "influenza")
    latest = week_at(FIRST, 119)
    assert out["state"] == "AA" and out["last_reported_week"] == latest
    assert [row["week"] for row in out["forecasts"]] == [week_at(FIRST, 119 + k) for k in (1, 2, 3, 4)]
    for row in out["forecasts"]:
        low95, high95 = row["interval_95"]
        low50, high50 = row["interval_50"]
        assert low95 <= low50 <= row["median"] <= high50 <= high95
        assert all(isinstance(v, int) for v in (row["median"], low95, high95))
    assert out["backtest"]["relative_wis_vs_persistence"] == 0.712


def test_a_state_behind_the_latest_week_gets_longer_horizons(forecaster):
    out = forecaster.forecast("BB", "covid")
    assert out["last_reported_week"] == week_at(FIRST, 117)
    assert [row["weeks_after_last_reported"] for row in out["forecasts"]] == [3, 4, 5, 6]


def test_quantiles_are_capped_at_a_multiple_of_the_history_maximum(forecaster, monkeypatch):
    monkeypatch.setattr(tool.models, "CAP", 0.5)
    out = forecaster.forecast("AA", "rsv")
    top = max(forecaster.items("rsv")[0].values)
    assert all(row["interval_95"][1] <= round(0.5 * top) for row in out["forecasts"])


def test_unknown_state_and_pathogen_are_reported(forecaster):
    with pytest.raises(DataError, match="No forecast for ZZ"):
        forecaster.forecast("ZZ", "influenza")
    with pytest.raises(DataError, match="pathogen must be one of"):
        forecaster.forecast("AA", "combined")


def test_toolbox_adds_the_tool_and_keeps_the_others(forecaster):
    class Client:
        async def call_tool(self, name, args):
            raise AssertionError("forecast_admissions must not go to the MCP server")

    toolbox_class = tool.make_toolbox_class()
    toolbox_class.forecaster = forecaster
    toolbox = toolbox_class(Client(), [{"name": "get_series", "description": "", "parameters": {}}])
    assert [s["name"] for s in toolbox.schemas] == ["get_series", "search_docs", "forecast_admissions"]
    output, is_error = asyncio.run(toolbox.call("forecast_admissions", {"state": "AA", "pathogen": "influenza"}))
    assert not is_error and len(json.loads(output)["forecasts"]) == 4
    output, is_error = asyncio.run(toolbox.call("forecast_admissions", {"state": "ZZ", "pathogen": "influenza"}))
    assert is_error and output.startswith("No forecast for ZZ")
    assert asyncio.run(toolbox.call("forecast_admissions", {"state": "AA"}))[1]


def test_forecast_prompt_extends_the_a3_prompt():
    from resplens.agent import loop
    prompt = tool.forecast_prompt()
    assert prompt.startswith(loop.SYSTEM_PROMPT.split("- Report numbers only")[0])
    assert "forecast_admissions" in prompt and "forecast_admissions" not in loop.SYSTEM_PROMPT


def test_injection_reaches_the_forecast_output(forecaster):
    toolbox_class = tool.make_toolbox_class()
    toolbox_class.forecaster = forecaster
    toolbox = toolbox_class(object(), [])
    toolbox.injection = {"target": {"tool": "forecast_admissions", "field": "notes[0]"}, "payload": "CANARY"}
    output, _ = asyncio.run(toolbox.call("forecast_admissions", {"state": "AA", "pathogen": "influenza"}))
    assert json.loads(output)["notes"][0].endswith(" CANARY")


def test_prompt_variants_differ_only_in_the_forecast_rule():
    from resplens.agent import loop
    v1, v2 = tool.forecast_prompt("v1"), tool.forecast_prompt("v2")
    assert v1 != v2 and tool.forecast_prompt() == tool.forecast_prompt(tool.PROMPT_VARIANT)
    for prompt in (v1, v2):
        assert prompt.replace(tool.FORECAST_RULES["v1"], "").replace(tool.FORECAST_RULES["v2"], "") \
            == loop.SYSTEM_PROMPT
