"""Analyze scored forecast runs as the plan specifies (docs/llm-forecast-eval.md, "Metrics and analysis").

    uv run python -m resplens.forecast.analyze eval/forecast-runs/<run> ... [--out eval/forecast-review/analysis.json]

Each run directory must already hold scores.jsonl (`resplens.forecast.run score`). One run per (system, version).
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .score import BOOTSTRAP

BASELINE = "persistence"
LLMS = ["gemma", "gpt-oss"]


def load(run_dirs: list[Path]) -> tuple[dict, dict]:
    """Scores keyed by (system, version) -> {(state, date, target): row}, and the forecasts' audit fields."""
    scores, audit = {}, {}
    for run_dir in run_dirs:
        config = json.loads((run_dir / "config.json").read_text())
        key = (config["system"], config["version"])
        if key in scores:
            raise SystemExit(f"two runs for {key}")
        rows = [json.loads(line) for line in (run_dir / "scores.jsonl").read_text().splitlines()]
        scores[key] = {(r["state"], r["date"], r["target"]): r for r in rows}
        audit[key] = [json.loads(line) for line in (run_dir / "forecasts.jsonl").read_text().splitlines()]
    return scores, audit


def common(scores: dict, version: str, systems: list[str]) -> list[tuple]:
    """Forecast keys that every system produced and that have a truth value."""
    keys = None
    for system in systems:
        ok = {k for k, r in scores[(system, version)].items() if "wis" in r}
        keys = ok if keys is None else keys & ok
    return sorted(keys)


def with_persistence(scores: dict, version: str, system: str) -> dict:
    """Sensitivity analysis: a failed LLM forecast replaced by the persistence forecast's scores."""
    base = scores[(BASELINE, version)]
    return {k: (base[k] if r["failed"] and "wis" in base[k] else r) for k, r in scores[(system, version)].items()}


def ratio_ci(pairs: dict, seed: int = 0) -> dict | None:
    """pairs: date -> [numerator sum, denominator sum]. Ratio of sums with a date-block bootstrap 95% interval;
    None when there are no forecasts to compare."""
    dates = sorted(pairs)
    if not dates:
        return None
    point = sum(pairs[d][0] for d in dates) / sum(pairs[d][1] for d in dates)
    rng = random.Random(seed)
    draws = sorted(sum(pairs[d][0] for d in s) / sum(pairs[d][1] for d in s)
                   for s in (rng.choices(dates, k=len(dates)) for _ in range(BOOTSTRAP)))
    low, high = draws[int(0.025 * BOOTSTRAP)], draws[int(0.975 * BOOTSTRAP) - 1]
    verdict = "better" if high < 1 else "worse" if low > 1 else "no detectable difference"
    return {"ratio": round(point, 3), "ci95": [round(low, 3), round(high, 3)], "dates": len(dates),
            "verdict": verdict}


def relative(a: dict, b: dict, keys: list[tuple], metric: str, seed: int = 0) -> dict:
    pairs = defaultdict(lambda: [0.0, 0.0])
    for k in keys:
        pairs[k[1]][0] += a[k][metric]
        pairs[k[1]][1] += b[k][metric]
    return ratio_ci(pairs, seed)


def revision_effect(scores: dict, system: str, keys_rt: list[tuple], keys_rev: list[tuple], seed: int = 0) -> dict:
    """Relative WIS on revised minus on real-time data, both against persistence on the same data version, with a
    joint date-block bootstrap. Uses the dates common to both versions."""
    sums = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for i, (version, keys) in enumerate([("realtime", keys_rt), ("revised", keys_rev)]):
        for k in keys:
            sums[k[1]][2 * i] += scores[(system, version)][k]["wis"]
            sums[k[1]][2 * i + 1] += scores[(BASELINE, version)][k]["wis"]
    dates = sorted(d for d, s in sums.items() if s[1] > 0 and s[3] > 0)

    def diff(sample):
        t = [sum(sums[d][j] for d in sample) for j in range(4)]
        return t[2] / t[3] - t[0] / t[1]
    rng = random.Random(seed)
    draws = sorted(diff(rng.choices(dates, k=len(dates))) for _ in range(BOOTSTRAP))
    return {"difference": round(diff(dates), 3),
            "ci95": [round(draws[int(0.025 * BOOTSTRAP)], 3), round(draws[int(0.975 * BOOTSTRAP) - 1], 3)],
            "dates": len(dates)}


def coverage(rows: dict, keys: list[tuple]) -> dict:
    return {name: round(sum(rows[k][name] for k in keys) / len(keys), 3) for name in ("cover50", "cover95")}


def audit_summary(forecasts: list[dict]) -> dict:
    out = {"forecasts": len(forecasts), "failed": sum(f["failed"] for f in forecasts)}
    if forecasts and "turns" in forecasts[0]:
        seconds = [sum(t["seconds"] for t in f["turns"]) for f in forecasts]
        tokens = [sum(t["output_tokens"] or 0 for t in f["turns"]) for f in forecasts]
        out.update({"repaired": sum(f["repaired"] and not f["failed"] for f in forecasts),
                    "sorted": sum(f["sorted"] for f in forecasts), "clipped": sum(f["clipped"] for f in forecasts),
                    "seconds_median": round(statistics.median(seconds), 1), "seconds_max": round(max(seconds), 1),
                    "output_tokens_median": statistics.median(tokens), "output_tokens_max": max(tokens)})
    return out


def analyze(scores: dict, audit: dict) -> dict:
    llms = [s for s in LLMS if any(k[0] == s for k in scores)]
    versions = sorted({v for _, v in scores})
    out = {"audit": {f"{s}/{v}": audit_summary(audit[(s, v)]) for s, v in sorted(audit)}, "versions": {}}
    keys_by_version = {}
    for version in versions:
        systems = [BASELINE] + [s for s in llms if (s, version) in scores]
        keys = common(scores, version, systems)
        keys_by_version[version] = keys
        base = scores[(BASELINE, version)]
        all_keys = {k for k, r in base.items() if r["truth"] is not None}
        result = {"common_forecasts": len(keys), "forecasts_with_truth": len(all_keys),
                  "coverage": {s: coverage(scores[(s, version)], keys) for s in systems},
                  "mean_wis": {s: round(statistics.fmean(scores[(s, version)][k]["wis"] for k in keys), 2)
                               for s in systems}}
        for system in systems[1:]:
            rows = scores[(system, version)]
            states = sorted({k[0] for k in keys})
            sensitivity_rows = with_persistence(scores, version, system)
            sensitivity_keys = sorted(k for k in all_keys if "wis" in sensitivity_rows[k])
            result[system] = {
                "relative_wis": relative(rows, base, keys, "wis"),
                "relative_mae": relative(rows, base, keys, "ae"),
                "relative_wis_by_target_week": {h: relative(rows, base, [k for k in keys if rows[k]["horizon"] == h],
                                                            "wis") for h in range(1, 5)},
                "relative_mae_by_target_week": {h: relative(rows, base, [k for k in keys if rows[k]["horizon"] == h],
                                                            "ae") for h in range(1, 5)},
                "relative_wis_by_state": {st: relative(rows, base, [k for k in keys if k[0] == st], "wis")
                                          for st in states},
                "relative_mae_by_state": {st: relative(rows, base, [k for k in keys if k[0] == st], "ae")
                                          for st in states},
                "sensitivity_failures_as_persistence": relative(sensitivity_rows, base, sensitivity_keys, "wis"),
            }
        if len(systems) == 3:
            a, b = (scores[(s, version)] for s in llms)
            result[f"{llms[0]}_vs_{llms[1]}"] = {"relative_wis": relative(a, b, keys, "wis"),
                                                 "relative_mae": relative(a, b, keys, "ae")}
        out["versions"][version] = result
    if {"realtime", "revised"} <= set(versions):
        out["revision_effect"] = {s: revision_effect(scores, s, keys_by_version["realtime"],
                                                     keys_by_version["revised"])
                                  for s in llms if (s, "realtime") in scores and (s, "revised") in scores}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    result = analyze(*load(args.run_dirs))
    text = json.dumps(result, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
