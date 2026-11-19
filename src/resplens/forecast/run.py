"""Run a forecasting system over the dev or test dates, and score saved runs (plan: docs/llm-forecast-eval.md).

    uv run python -m resplens.forecast.run run --split dev --system gemma --version revised --variant h26
    uv run python -m resplens.forecast.run run --split test --system persistence --version realtime
    uv run python -m resplens.forecast.run score eval/forecast-runs/<run>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from ..agent.run import SYSTEMS as LLM_SYSTEMS, model_info
from ..data import DATA_TAG, Dataset
from ..retrieval.dense import CPU_THREADS
from ..retrieval.evaluate import ROOT, _git_commit
from . import llm, persistence, vintage
from .score import score


PATHOGEN = "influenza"
STATES = ["CT", "DE", "FL", "GA", "MT", "NC", "PA", "RI", "SC", "TX"]  # random.Random(20261105).sample(sorted(51), 10)
DATES = {"dev": vintage.fridays("2024-10-04", "2025-03-28"), "test": vintage.fridays("2025-04-04", "2026-07-24")}
TRUTH_CUTOFF = "2026-08-15"
PROMPT_VARIANT = "h52"  # chosen on dev 2026-11-06, recorded in docs/llm-forecast-eval.md before any test forecast
RUN_INPUTS = ["src", "pyproject.toml", "uv.lock"]
SYSTEMS = ["persistence", *LLM_SYSTEMS]


def series_for(ds: Dataset, split: str, version: str, state: str, forecast_date: str) -> vintage.Series:
    if split == "dev":  # no release history before 2025-04-04: revised data cut where a release would usually end
        return vintage.revised(ds, state, PATHOGEN, vintage.standard_last_week(forecast_date))
    real = vintage.real_time(ds, state, PATHOGEN, forecast_date)
    return real if version == "realtime" else vintage.revised(ds, state, PATHOGEN, real[-1][0])


def run(split: str, system: str, version: str, variant: str | None, states: list[str], dates: list[str],
        resume: Path | None = None, chat_fn=llm.chat, ds: Dataset | None = None) -> Path:
    ds = ds or Dataset()
    if resume:
        run_dir = resume
        config = json.loads((run_dir / "config.json").read_text())
        split, system, version, variant = config["split"], config["system"], config["version"], config["variant"]
        states, dates = config["states"], config["dates"]
    else:
        run_dir = ROOT / "eval" / "forecast-runs" / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-{system}-{version}"
        run_dir.mkdir(parents=True)
        config = {"split": split, "system": system, "version": version, "variant": variant, "pathogen": PATHOGEN,
                  "states": states, "dates": dates, "data_release": DATA_TAG, "levels": list(persistence.LEVELS),
                  "git_commit": _git_commit(inputs=RUN_INPUTS), "started": datetime.now().isoformat(timespec="seconds")}
        if system == "persistence":
            config["window_weeks"] = persistence.WINDOW
        else:
            config.update(model_info(LLM_SYSTEMS[system]["model"]))
            config.update({"think": LLM_SYSTEMS[system]["think"], "temperature": 0, "seed": 0, "num_ctx": llm.NUM_CTX,
                           "max_output": llm.MAX_OUTPUT, "num_thread": CPU_THREADS,
                           "system_prompt": llm.SYSTEM_PROMPT, "schema": llm.SCHEMA})
        (run_dir / "config.json").write_text(json.dumps(config, indent=1))
    out = run_dir / "forecasts.jsonl"
    done = {(r["state"], r["date"]) for r in map(json.loads, out.read_text().splitlines())} if out.exists() else set()
    with out.open("a") as handle:
        for state in states:
            name = ds.coverage[state]["state_name"]
            for forecast_date in dates:
                if (state, forecast_date) in done:
                    continue
                series = series_for(ds, split, version, state, forecast_date)
                weeks = vintage.targets(forecast_date)
                row = {"state": state, "date": forecast_date, "last_week": series[-1][0],
                       "last_observed": vintage.last_observed(series)[0], "targets": weeks}
                if system == "persistence":
                    row.update({"quantiles": persistence.forecast(series, weeks), "failed": False})
                else:
                    text = llm.prompt(name, state, PATHOGEN, forecast_date, series, weeks, variant)
                    result = llm.forecast(LLM_SYSTEMS[system]["model"], LLM_SYSTEMS[system]["think"], text, weeks,
                                          chat_fn=chat_fn)
                    row.update({"prompt": text, **result, "failed": result["quantiles"] is None})
                handle.write(json.dumps(row) + "\n")
                handle.flush()
                print(state, forecast_date, "failed" if row["failed"] else "ok")
    print(f"saved to {run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir}")
    return run_dir


def score_run(run_dir: Path, ds: Dataset | None = None) -> list[dict]:
    """One row per forecast and target week, against the pinned release; failed forecasts are kept with failed=True."""
    ds = ds or Dataset()
    config = json.loads((run_dir / "config.json").read_text())
    rows = []
    for forecast in map(json.loads, (run_dir / "forecasts.jsonl").read_text().splitlines()):
        truth = vintage.truth(ds, forecast["state"], config["pathogen"], forecast["targets"])
        for horizon, week in enumerate(forecast["targets"], 1):
            row = {"state": forecast["state"], "date": forecast["date"], "target": week, "horizon": horizon,
                   "system": config["system"], "version": config["version"], "truth": truth[week],
                   "failed": forecast["failed"]}
            if not forecast["failed"] and truth[week] is not None:
                row.update(score(forecast["quantiles"][week], truth[week]))
            rows.append(row)
    (run_dir / "scores.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run")
    runner.add_argument("--split", choices=sorted(DATES), required=True)
    runner.add_argument("--system", choices=SYSTEMS, required=True)
    runner.add_argument("--version", choices=["realtime", "revised"], required=True)
    runner.add_argument("--variant", choices=sorted(llm.VARIANTS), help="prompt variant (dev only)")
    runner.add_argument("--states", help="comma-separated subset (default: all 10)")
    runner.add_argument("--dates", help="comma-separated subset of the split's dates")
    runner.add_argument("--resume", type=Path)
    scorer = commands.add_parser("score")
    scorer.add_argument("run_dirs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.split == "dev" and args.version != "revised":
            parser.error("dev has no release history; use --version revised")
        if args.split == "test":
            if args.variant:
                parser.error("test uses the variant chosen on dev (PROMPT_VARIANT); --variant is for dev only")
            if args.system != "persistence" and PROMPT_VARIANT is None:
                parser.error("choose PROMPT_VARIANT on dev and record it in the plan before any test forecast")
        variant = args.variant if args.split == "dev" else PROMPT_VARIANT
        if args.system != "persistence" and variant is None:
            parser.error("LLM runs on dev need --variant")
        states = args.states.split(",") if args.states else STATES
        dates = args.dates.split(",") if args.dates else DATES[args.split]
        run(args.split, args.system, args.version, variant, states, dates, args.resume)
    else:
        for run_dir in args.run_dirs:
            rows = score_run(run_dir)
            scored = [r for r in rows if "wis" in r]
            print(run_dir.name, f"scored {len(scored)}/{len(rows)}",
                  f"mean WIS {sum(r['wis'] for r in scored) / max(1, len(scored)):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
