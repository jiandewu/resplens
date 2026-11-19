"""A forecast tool for the agent, from the B1 benchmark's best model (an addition to the evaluated A3 agent).

    uv run --extra forecast python -m resplens.forecast.tool forecast SC influenza
    uv run --extra forecast --extra models python -m resplens.forecast.tool ask --system gemma "<question>"

forecast_admissions gives 1- to 4-week-ahead quantile forecasts of weekly NHSN hospital admissions for one state and
pathogen. The model is LightGBM with the settings chosen on dev in B1 (docs/forecast-eval.md), trained on every
state's series for the pathogen in the pinned release and fitted once per pathogen in the process. The forecast
starts from the latest weeks in the release, which are first reports. Quantiles are capped at models.CAP times the
series' largest value, the rule used when B1 was scored.

The agent gets the tool through ForecastToolbox and FORECAST_PROMPT; the A3 toolbox, system prompt, runner and
service are unchanged, so the evaluated configurations are not affected.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, timedelta
from functools import partial
from pathlib import Path

from .. import tools
from ..data import DATA_TAG, DataError, Dataset
from . import inputs, models, vintage
from .persistence import LEVELS

PATHOGENS = inputs.PATHOGENS
MODEL = "lightgbm"
# B1 test results for this model (docs/forecast-results.md): real-time data, all states and pathogens, horizons 1-4.
# Coverage in percent, the form answers use (dev runs 2026-11-17: 0.475 was reported as 47.5%).
BACKTEST = {"forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)", "data": "as published on each date",
            "relative_wis_vs_persistence": 0.712, "relative_wis_ci95": [0.666, 0.755],
            "coverage_50_interval_percent": 47.5, "coverage_95_interval_percent": 90.2}
NOTES = ["The forecast starts from the latest reported weeks, which are first reports and are often revised.",
         "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."]

SCHEMA = {
    "name": "forecast_admissions",
    "description": "Forecast weekly hospital admissions (NHSN) for one state and pathogen 1 to 4 weeks after the "
                   "latest reported week: median and 50% and 95% intervals, with the model's backtest accuracy.",
    "parameters": {"type": "object", "properties": {
        "state": {"type": "string", "description": 'Two-letter postal code, e.g. "SC" or "DC".'},
        "pathogen": {"type": "string", "enum": list(PATHOGENS), "description": "Pathogen."}},
        "required": ["state", "pathogen"]},
}


def _index(level: float) -> int:
    return LEVELS.index(level)


class Forecaster:
    """Builds every state's series for a pathogen from the pinned release, fits the model once per pathogen and
    forecasts one state. `load` replaces the series source in tests: pathogen -> list of inputs.Item."""

    def __init__(self, ds: Dataset | None = None, load=None):
        self._ds, self._load = ds, load
        self._items: dict[str, list[inputs.Item]] = {}
        self._models: dict[str, object] = {}

    def items(self, pathogen: str) -> list[inputs.Item]:
        if pathogen not in self._items:
            self._items[pathogen] = self._load(pathogen) if self._load else self._build(pathogen)
        return self._items[pathogen]

    def _build(self, pathogen: str) -> list[inputs.Item]:
        ds = self._ds = self._ds or Dataset()
        out = []
        for state in sorted(ds.coverage):
            try:
                rows = tools.get_series(ds, state, vintage.MEASURE, pathogen, max_weeks=vintage.MAX_WEEKS)["weeks"]
            except DataError:
                continue
            series = vintage.weekly(rows)
            if inputs.enough_history(series):
                first, values = inputs.fill(series)
                out.append(inputs.Item(state, pathogen, "", first, values))
        return out

    def forecast(self, state: str, pathogen: str) -> dict:
        state = state.strip().upper()
        if pathogen not in PATHOGENS:
            raise DataError(f"pathogen must be one of {', '.join(PATHOGENS)}")
        items = self.items(pathogen)
        item = next((i for i in items if i.state == state), None)
        if item is None:
            raise DataError(f"No forecast for {state} {pathogen}: unknown state, or fewer than {inputs.MIN_OBSERVED} "
                            f"reported weeks among the last {inputs.HISTORY_WEEKS}.")
        latest = max(i.last_week for i in items)
        forecast_date = (date.fromisoformat(latest) + timedelta(days=vintage.REPORTING_LAG_DAYS)).isoformat()
        targets = vintage.targets(forecast_date)
        settings = models.CHOSEN[MODEL][pathogen]
        model = self._models.setdefault(pathogen, models.get(MODEL, settings))
        context = {"refit_key": f"{pathogen}:{forecast_date}", "train_items": items}
        quantiles = model.predict([item], targets, context)[0]
        if quantiles is None:
            raise DataError(f"The model could not forecast {state} {pathogen}.")
        top = max(item.values)
        rows = []
        for target in targets:
            q = models.cap(quantiles[target], top)
            rows.append({"week": target, "weeks_after_last_reported": item.k(target),
                         "median": round(q[_index(0.5)]),
                         "interval_50": [round(q[_index(0.25)]), round(q[_index(0.75)])],
                         "interval_95": [round(q[_index(0.025)]), round(q[_index(0.975)])]})
        return {"state": state, "pathogen": pathogen, "measure": vintage.MEASURE, "data_release": DATA_TAG,
                "last_reported_week": item.last_week, "last_reported_value": round(item.values[-1]),
                "forecasts": rows, "model": "LightGBM quantile regression ("
                                            + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in settings.items())
                                            + "), chosen on dev in the B1 benchmark",
                "backtest": BACKTEST, "notes": NOTES}


def _agent_parts():
    """The agent modules, imported only for the agent (they need the retrieval and MCP dependencies)."""
    from ..agent import loop
    return loop


def make_toolbox_class():
    loop = _agent_parts()

    class ForecastToolbox(loop.Toolbox):
        """The A3 toolbox plus forecast_admissions, run in-process."""

        forecaster: Forecaster | None = None

        def __init__(self, client, data_schemas, search=None):
            super().__init__(client, data_schemas, search)
            self.schemas.append(SCHEMA)
            self.names.add(SCHEMA["name"])
            self.forecaster = self.forecaster or Forecaster()

        async def call(self, name: str, args: dict) -> tuple[str, bool]:
            if name != SCHEMA["name"]:
                return await super().call(name, args)
            if not isinstance(args, dict) or not isinstance(args.get("state"), str) \
                    or not isinstance(args.get("pathogen"), str):
                return "forecast_admissions needs a state code and a pathogen (covid, influenza or rsv).", True
            try:
                output = await asyncio.to_thread(self.forecaster.forecast, args["state"], args["pathogen"])
            except DataError as exc:
                return str(exc), True
            injection = self.injection  # evaluation only, as in the A3 toolbox
            if injection and injection["target"]["tool"] == SCHEMA["name"]:
                loop._set_path(output, injection["target"]["field"], lambda text: f"{text} {injection['payload']}")
            return json.dumps(output, indent=2), False

    return ForecastToolbox


FORECAST_RULES = {
    "v1": """- forecast_admissions forecasts weekly hospital admissions 1 to 4 weeks ahead. Use it only for questions \
about future weeks. Report the median and the 95% interval with the weeks they refer to, say that it is a model \
forecast, and give the backtest accuracy and notes it returns. Also call check_reliability for the same state and \
pathogen, because the forecast starts from the latest reported weeks.
""",
    # Tried on dev 2026-11-17 (author's decision): base and fine-tuned E4B skipped check_reliability with v1.
    "v2": """- forecast_admissions forecasts weekly hospital admissions 1 to 4 weeks ahead. Use it only for questions \
about future weeks. Whenever you report a forecast: give the median and the 95% interval for each week it returns, \
with the week dates; say that it is a model forecast and give the backtest accuracy it returns; and always call \
check_reliability for the same state and pathogen and state the hospital-data caveats it returns, or say that none \
were flagged, because the forecast starts from the latest reported weeks.
""",
}
PROMPT_VARIANT = "v2"  # chosen on dev 2026-11-17 by the pre-set rule (23 against 22 successes, docs/forecast-tool-eval.md)


def forecast_prompt(variant: str | None = None) -> str:
    loop = _agent_parts()
    anchor = "- Report numbers only as returned by the tools"
    assert loop.SYSTEM_PROMPT.count(anchor) == 1
    return loop.SYSTEM_PROMPT.replace(anchor, FORECAST_RULES[variant or PROMPT_VARIANT] + anchor)


async def ask(question: str, system: str, url: str | None = None, forecaster: Forecaster | None = None) -> dict:
    from mcp import Client

    from .. import server
    from ..agent import checks
    from ..agent.run import SYSTEMS
    loop = _agent_parts()
    spec = SYSTEMS[system]
    chat_fn = partial(loop.openai_chat, url=url) if spec.get("backend") == "vllm" else loop.chat
    toolbox_class = make_toolbox_class()
    toolbox_class.forecaster = forecaster
    async with Client(server.mcp) as client:
        toolbox = await toolbox_class.create(client)
        trace = await loop.run_task({"id": "forecast-tool", "question": question}, toolbox, spec["model"],
                                    spec["think"], 0, forecast_prompt(), chat_fn=chat_fn)
    result = trace.to_dict()
    result["system"], result["system_prompt"] = system, forecast_prompt()
    result["grounding"] = checks.grounding(result["answer"], question, [c["output"] for c in trace.calls()])
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("forecast")
    one.add_argument("state")
    one.add_argument("pathogen", choices=PATHOGENS)
    agent = commands.add_parser("ask")
    agent.add_argument("question")
    agent.add_argument("--system", default="gemma")
    agent.add_argument("--url", help="vLLM server for the b2 systems")
    agent.add_argument("--out", type=Path, help="append the trace as one JSON line")
    args = parser.parse_args(argv)
    if args.command == "forecast":
        print(json.dumps(Forecaster().forecast(args.state, args.pathogen), indent=1))
        return 0
    result = asyncio.run(ask(args.question, args.system, args.url))
    for turn in result["turns"]:
        for call in turn["tool_calls"]:
            print(f"tool {call['name']} {json.dumps(call['args'])}{' ERROR' if call['is_error'] else ''}")
    print(f"\n{result['answer']}\n\nstop {result['stop']}, {result['seconds']:.1f} s, numbers found "
          f"{len(result['grounding']['direct'])}, not found {result['grounding']['unmatched']}")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("a") as handle:
            handle.write(json.dumps(result) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
