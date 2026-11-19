"""Full B1 benchmark runs (plan: docs/forecast-eval.md): run a model over a split, score runs, choose settings on dev.

    uv run --extra forecast python -m resplens.forecast.bench run --split dev --model arima --settings '{"context": 104}'
    uv run --extra forecast python -m resplens.forecast.bench run --split test --model arima --version realtime
    uv run --extra forecast python -m resplens.forecast.bench run --resume eval/forecast-b1/runs/<run>
    uv run --extra forecast python -m resplens.forecast.bench score eval/forecast-b1/runs/<run> ...
    uv run --extra forecast python -m resplens.forecast.bench select eval/forecast-b1/runs/*-dev-*
    uv run --extra forecast python -m resplens.forecast.bench ensemble --version realtime

Inputs come from the cache built by `resplens.forecast.inputs`. On test, every model uses the settings chosen on dev
(models.CHOSEN), per pathogen; a test run refuses to start while they are missing.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime
from importlib import metadata
from pathlib import Path

import numpy as np

from ..data import DATA_TAG, Dataset
from ..retrieval.evaluate import ROOT, _git_commit
from . import inputs, models, persistence, vintage
from .models.tabular import REFIT_EVERY
from .score import score

RUNS = ROOT / "eval" / "forecast-b1" / "runs"
RUN_INPUTS = ["src", "pyproject.toml", "uv.lock"]
TRUTH_CUTOFF = "2026-08-15"
FALLBACK_WINDOW = persistence.WINDOW  # persistence window for fallbacks on dev; test uses the dev choice
PACKAGES = ("statsforecast", "lightgbm", "chronos-forecasting", "tabpfn", "torch", "numpy")


def versions() -> dict:
    out = {}
    for name in PACKAGES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def settings_for(model: str, split: str, settings: dict | None) -> dict[str, dict]:
    """Settings per pathogen: the given settings on dev, the dev choice on test."""
    if split == "dev":
        if settings is None:
            raise ValueError("dev runs need --settings (one point of the model's grid)")
        return {p: settings for p in inputs.PATHOGENS}
    source = models.UNTUNED.get(model, model)
    chosen = models.CHOSEN.get(source)
    if not chosen or set(chosen) != set(inputs.PATHOGENS):
        raise ValueError(f"no settings chosen on dev for {source}; record them in models.CHOSEN and the plan first")
    return chosen


def fallback_settings(split: str) -> dict[str, dict]:
    """Persistence settings per pathogen for rows a model cannot forecast."""
    if split == "dev":
        return {p: {"window": FALLBACK_WINDOW} for p in inputs.PATHOGENS}
    return settings_for("persistence", split, None)


def model_record(model: str) -> dict:
    if model.startswith("chronos2"):
        from .models.foundation import REPOS
        repo, revision = REPOS[model == "chronos2_synth"]
        return {"repo": repo, "revision": revision}
    if model == "tabpfn":
        from .models import tabular
        return {"repo": tabular.TABPFN_REPO, "revision": tabular.TABPFN_REVISION, "file": tabular.TABPFN_FILE,
                "sha256": tabular.TABPFN_SHA256, "n_estimators": tabular.TABPFN_ESTIMATORS}
    if model.startswith("lightgbm"):
        from .models import tabular
        return {"trees": tabular.TREES, "min_leaf": tabular.MIN_LEAF, "refit_every": tabular.REFIT_EVERY}
    return {}


def dates_for(model: str, split: str) -> list[str]:
    dates = inputs.DATES[split]
    return [d for d in dates if d >= inputs.ED_FROM] if model == "lightgbm_ed" else dates


def run(split: str | None = None, model: str | None = None, version: str = "revised", settings: dict | None = None,
        resume: Path | None = None, source: Path | None = None, dates: list[str] | None = None,
        out_dir: Path | None = None) -> Path:
    if resume:
        run_dir = resume
        config = json.loads((run_dir / "config.json").read_text())
    else:
        per_pathogen = settings_for(model, split, settings)
        name = models.config_name(settings) if split == "dev" else "chosen"
        run_dir = (out_dir or RUNS) / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-{model}-{name}-{version}"
        run_dir.mkdir(parents=True)
        config = {"split": split, "model": model, "version": version, "settings": per_pathogen,
                  "dates": dates or dates_for(model, split), "pathogens": list(inputs.PATHOGENS),
                  "data_release": DATA_TAG, "levels": list(persistence.LEVELS),
                  "min_history": {"observed": inputs.MIN_OBSERVED, "of_last_weeks": inputs.HISTORY_WEEKS},
                  "fallback": fallback_settings(split), "model_record": model_record(model), "packages": versions(),
                  "git_commit": _git_commit(inputs=RUN_INPUTS), "started": datetime.now().isoformat(timespec="seconds")}
        (run_dir / "config.json").write_text(json.dumps(config, indent=1))
    groups, removed = inputs.load(config["split"], config["version"], source)
    instances = {p: models.get(config["model"], s) for p, s in config["settings"].items()}
    fallback = config.get("fallback") or {p: {"window": config["fallback_window"]} for p in config["pathogens"]}
    fallback_models = {p: models.get("persistence", s) for p, s in fallback.items()}
    out = run_dir / "forecasts.jsonl"
    done = {(r["date"], r["pathogen"]) for r in map(json.loads, out.read_text().splitlines())} if out.exists() \
        else set()
    run_dates = config["dates"]
    with out.open("a") as handle:
        for i, day in enumerate(run_dates):
            targets = vintage.targets(day)
            for pathogen in config["pathogens"]:
                items = groups.get((day, pathogen), [])
                if (day, pathogen) in done or not items:
                    continue
                refit = run_dates[i - i % REFIT_EVERY]  # LightGBM refits on every 4th date of the run
                context = {"refit_key": f"{pathogen}:{refit}", "train_items": groups.get((refit, pathogen), items)}
                started = time.time()
                try:
                    forecasts = instances[pathogen].predict(items, targets, context)
                except Exception as exc:  # noqa: BLE001  (the whole group falls back; counted)
                    print(f"{config['model']} {day} {pathogen}: {type(exc).__name__}: {exc}", flush=True)
                    forecasts = [None] * len(items)
                seconds = time.time() - started
                backup = fallback_models[pathogen].predict(items, targets) if any(f is None for f in forecasts) \
                    else None
                for j, (item, forecast) in enumerate(zip(items, forecasts)):
                    handle.write(json.dumps({
                        "date": day, "pathogen": pathogen, "state": item.state, "last_week": item.last_week,
                        "targets": targets, "k": [item.k(t) for t in targets],
                        "quantiles": forecast if forecast is not None else backup[j],
                        "fallback": forecast is None, "group_seconds": round(seconds, 2)}) + "\n")
                handle.flush()
                fallbacks = sum(f is None for f in forecasts)
                print(f"{config['model']} {day} {pathogen} {len(items)} items {seconds:.1f}s"
                      + (f" fallbacks={fallbacks}" if fallbacks else ""), flush=True)
    (run_dir / "removed.json").write_text(json.dumps(removed))
    return run_dir


_TRUTH = {}


def truth(ds: Dataset, state: str, pathogen: str) -> dict[str, float]:
    if (state, pathogen) not in _TRUTH:
        _TRUTH[(state, pathogen)] = {w: v for w, v in vintage.revised(ds, state, pathogen, TRUTH_CUTOFF)
                                     if v is not None}
    return _TRUTH[(state, pathogen)]


def history_max(split: str, version: str, source: Path | None = None) -> dict[tuple, float]:
    """(date, pathogen, state) -> the largest value of the series the models saw."""
    groups, _ = inputs.load(split, version, source)
    return {(day, pathogen, item.state): max(item.values)
            for (day, pathogen), items in groups.items() for item in items}


def score_run(run_dir: Path, ds: Dataset | None = None, source: Path | None = None) -> list[dict]:
    """One row per forecast and target week (horizon 1-4 by calendar), against the pinned release; targets after
    TRUTH_CUTOFF or without a value are left out. Scores use the capped quantiles (models.cap); `wis_uncapped` keeps
    the score of the raw forecast."""
    ds = ds or Dataset()
    config = json.loads((run_dir / "config.json").read_text())
    maxima = history_max(config["split"], config["version"], source)
    rows = []
    for f in map(json.loads, (run_dir / "forecasts.jsonl").read_text().splitlines()):
        values = truth(ds, f["state"], f["pathogen"])
        top = maxima[(f["date"], f["pathogen"], f["state"])]
        for horizon, (week, k) in enumerate(zip(f["targets"], f["k"]), 1):
            if week > TRUTH_CUTOFF or week not in values:
                continue
            raw = f["quantiles"][week]
            capped = models.cap(raw, top)
            rows.append({"date": f["date"], "pathogen": f["pathogen"], "state": f["state"], "target": week,
                         "horizon": horizon, "k": k, "model": config["model"], "version": config["version"],
                         "truth": values[week], "fallback": f["fallback"], "history_max": top,
                         "capped": capped != raw, **score(capped, values[week]),
                         "wis_uncapped": score(raw, values[week])["wis"]})
    (run_dir / "scores.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return rows


ENSEMBLE = ("seasonal_naive", "arima", "ets", "lightgbm", "chronos2", "tabpfn")


def find_run(split: str, model: str, version: str, runs: Path | None = None) -> Path:
    found = sorted((runs or RUNS).glob(f"*-{split}-{model}-{'chosen' if split == 'test' else '*'}-{version}"))
    if len(found) != 1:
        raise SystemExit(f"expected one {split} run for {model}/{version}, found {[p.name for p in found]}")
    return found[0]


def ensemble(split: str, version: str, runs: Path | None = None, source: Path | None = None) -> Path:
    """The median ensemble (plan, Models): quantile-wise median of the members' capped quantiles. A row counts as a
    fallback when any member's row was one, so the primary analysis removes it as it removes the member's."""
    members = {m: find_run(split, m, version, runs) for m in ENSEMBLE}
    forecasts = {m: {(f["date"], f["pathogen"], f["state"]): f
                     for f in map(json.loads, (d / "forecasts.jsonl").read_text().splitlines())}
                 for m, d in members.items()}
    keys = set.intersection(*(set(f) for f in forecasts.values()))
    if any(set(f) != keys for f in forecasts.values()):
        raise SystemExit("ensemble members forecast different rows")
    maxima = history_max(split, version, source)
    run_dir = (runs or RUNS) / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-ensemble-chosen-{version}"
    run_dir.mkdir(parents=True)
    config = {"split": split, "model": "ensemble", "version": version, "members": {m: d.name for m, d in members.items()},
              "combination": "quantile-wise median of capped member quantiles", "cap": models.CAP,
              "data_release": DATA_TAG, "levels": list(persistence.LEVELS),
              "git_commit": _git_commit(inputs=RUN_INPUTS), "started": datetime.now().isoformat(timespec="seconds")}
    (run_dir / "config.json").write_text(json.dumps(config, indent=1))
    with (run_dir / "forecasts.jsonl").open("w") as handle:
        for key in sorted(keys):
            rows = [forecasts[m][key] for m in ENSEMBLE]
            first, top = rows[0], maxima[key]
            quantiles = {t: [float(v) for v in np.median([models.cap(r["quantiles"][t], top) for r in rows], axis=0)]
                         for t in first["targets"]}
            handle.write(json.dumps({"date": first["date"], "pathogen": first["pathogen"], "state": first["state"],
                                     "last_week": first["last_week"], "targets": first["targets"], "k": first["k"],
                                     "quantiles": quantiles, "fallback": any(r["fallback"] for r in rows),
                                     "fallback_members": [m for m, r in zip(ENSEMBLE, rows) if r["fallback"]]}) + "\n")
    removed = json.loads((members[ENSEMBLE[0]] / "removed.json").read_text())
    (run_dir / "removed.json").write_text(json.dumps(removed))
    return run_dir


def select(run_dirs: list[Path]) -> dict:
    """For each model and pathogen, the dev configuration with the lowest mean WIS over the rows that every
    configuration of that model forecast without a fallback. Ties go to the earlier (simpler) grid entry."""
    by_model = defaultdict(dict)
    for run_dir in run_dirs:
        config = json.loads((run_dir / "config.json").read_text())
        if config["split"] != "dev":
            continue
        settings = config["settings"][inputs.PATHOGENS[0]]
        rows = [json.loads(line) for line in (run_dir / "scores.jsonl").read_text().splitlines()]
        by_model[config["model"]][models.config_name(settings)] = (settings, rows)
    result = {}
    for model, configs in sorted(by_model.items()):
        order = [models.config_name(s) for s in models.GRID[model]]
        missing = [name for name in order if name not in configs]
        result[model] = {"missing": missing}
        for pathogen in inputs.PATHOGENS:
            keys, bad = None, set()
            for _, rows in configs.values():
                these = {(r["date"], r["state"], r["target"]) for r in rows if r["pathogen"] == pathogen}
                bad |= {(r["date"], r["state"], r["target"]) for r in rows
                        if r["pathogen"] == pathogen and r["fallback"]}
                keys = these if keys is None else keys & these
            keys -= bad
            scores = {}
            for name in order:
                if name in configs:
                    wis = [r["wis"] for r in configs[name][1]
                           if r["pathogen"] == pathogen and (r["date"], r["state"], r["target"]) in keys]
                    scores[name] = sum(wis) / len(wis)
            best = min(scores, key=lambda n: (round(scores[n], 9), order.index(n)))
            result[model][pathogen] = {"chosen": configs[best][0], "chosen_name": best, "rows": len(keys),
                                       "excluded_fallback_rows": len(bad),
                                       "mean_wis": {n: round(v, 3) for n, v in scores.items()}}
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run")
    runner.add_argument("--split", choices=sorted(inputs.DATES))
    runner.add_argument("--model", choices=sorted([*models.GRID, *models.UNTUNED]))
    runner.add_argument("--version", choices=["realtime", "revised"], default="revised")
    runner.add_argument("--settings", type=json.loads, help="JSON, one point of the model's grid (dev only)")
    runner.add_argument("--resume", type=Path)
    scorer = commands.add_parser("score")
    scorer.add_argument("run_dirs", nargs="+", type=Path)
    combiner = commands.add_parser("ensemble")
    combiner.add_argument("--split", choices=sorted(inputs.DATES), default="test")
    combiner.add_argument("--version", choices=["realtime", "revised"], required=True)
    selector = commands.add_parser("select")
    selector.add_argument("run_dirs", nargs="+", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        if not args.resume:
            if not args.split or not args.model:
                parser.error("--split and --model are required unless --resume")
            if args.split == "dev" and args.version != "revised":
                parser.error("dev has no release history; use --version revised")
            if args.split == "dev" and args.model in models.UNTUNED:
                parser.error(f"{args.model} is not tuned on dev; it uses {models.UNTUNED[args.model]}'s choice")
            if args.split == "dev" and args.settings not in models.GRID[args.model]:
                parser.error(f"--settings must be one of {models.GRID[args.model]}")
            if args.split == "test" and args.settings:
                parser.error("test uses the settings chosen on dev (models.CHOSEN)")
        print(run(args.split, args.model, args.version, args.settings, args.resume))
    elif args.command == "score":
        for run_dir in args.run_dirs:
            rows = score_run(run_dir)
            print(run_dir.name, f"scored {len(rows)}", f"mean WIS {sum(r['wis'] for r in rows) / max(1, len(rows)):.2f}",
                  f"fallback rows {sum(r['fallback'] for r in rows)}")
    elif args.command == "ensemble":
        print(ensemble(args.split, args.version))
    else:
        result = select(args.run_dirs)
        out = ROOT / "eval" / "forecast-b1" / "dev-selection.json"
        out.write_text(json.dumps(result, indent=1))
        print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
