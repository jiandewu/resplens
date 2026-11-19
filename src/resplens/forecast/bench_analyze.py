"""Analysis of the full B1 test runs as the plan specifies (docs/forecast-eval.md, "Metrics", "Analysis",
"Comparisons", and the changes after freezing).

    uv run --extra forecast python -m resplens.forecast.bench_analyze [--out eval/forecast-b1/analysis.json]

Uses the one scored test run per (model, version) in eval/forecast-b1/runs/. A forecast row is identified by
(pathogen, state, forecast date, target week). Primary: relative WIS against persistence on real-time data, pooled over
pathogens, on the rows every compared system forecast without a fallback, with a date-block bootstrap 95% interval.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from .analyze import ratio_ci
from .bench import RUNS, find_run
from .inputs import PATHOGENS
from .score import BOOTSTRAP

BASELINE = "persistence"
SYSTEMS = ["seasonal_naive", "arima", "ets", "lightgbm", "chronos2", "chronos2_synth", "tabpfn", "ensemble"]
VERSIONS = ["realtime", "revised"]
DATE = 2  # index of the forecast date in a row key


def load(runs: Path | None = None) -> dict:
    scores = {}
    for model in [BASELINE, *SYSTEMS, "lightgbm_ed"]:
        for version in VERSIONS:
            run_dir = find_run("test", model, version, runs)
            rows = map(json.loads, (run_dir / "scores.jsonl").read_text().splitlines())
            scores[(model, version)] = {(r["pathogen"], r["state"], r["date"], r["target"]): r for r in rows}
    return scores


def common(scores: dict, version: str, systems: list[str], keep_fallback: bool = False) -> list[tuple]:
    """Rows every system scored; without keep_fallback, also none of them a fallback (plan: removed for all)."""
    keys = set.intersection(*(set(scores[(s, version)]) for s in systems))
    if not keep_fallback:
        keys = {k for k in keys if not any(scores[(s, version)][k]["fallback"] for s in systems)}
    return sorted(keys)


def relative(a: dict, b: dict, keys: list[tuple], metric: str = "wis", seed: int = 0) -> dict | None:
    pairs = defaultdict(lambda: [0.0, 0.0])
    for k in keys:
        pairs[k[DATE]][0] += a[k][metric]
        pairs[k[DATE]][1] += b[k][metric]
    return ratio_ci(pairs, seed)


def by_state(a: dict, b: dict, keys: list[tuple]) -> dict[str, float]:
    """Each location's WIS sum divided by its persistence WIS sum (point estimates, no interval)."""
    sums = defaultdict(lambda: [0.0, 0.0])
    for k in keys:
        sums[k[1]][0] += a[k]["wis"]
        sums[k[1]][1] += b[k]["wis"]
    return {st: round(s[0] / s[1], 3) for st, s in sorted(sums.items()) if s[1] > 0}


def normalized(a: dict, b: dict, keys: list[tuple]) -> float:
    """Plan, Metrics: each location's WIS divided by its persistence WIS, then averaged over locations."""
    return round(statistics.fmean(by_state(a, b, keys).values()), 3)


def revision_effect(scores: dict, system: str, keys: dict, seed: int = 0) -> dict:
    """Relative WIS on revised minus on real-time data, each against persistence on the same version, with a joint
    date-block bootstrap."""
    sums = defaultdict(lambda: [0.0] * 4)
    for i, version in enumerate(VERSIONS):
        for k in keys[version]:
            sums[k[DATE]][2 * i] += scores[(system, version)][k]["wis"]
            sums[k[DATE]][2 * i + 1] += scores[(BASELINE, version)][k]["wis"]
    dates = sorted(d for d, s in sums.items() if s[1] > 0 and s[3] > 0)

    def diff(sample):
        t = [sum(sums[d][j] for d in sample) for j in range(4)]
        return t[2] / t[3] - t[0] / t[1]
    rng = random.Random(seed)
    draws = sorted(diff(rng.choices(dates, k=len(dates))) for _ in range(BOOTSTRAP))
    low, high = draws[int(0.025 * BOOTSTRAP)], draws[int(0.975 * BOOTSTRAP) - 1]
    return {"difference": round(diff(dates), 3), "ci95": [round(low, 3), round(high, 3)], "dates": len(dates),
            "verdict": "revised better" if high < 0 else "revised worse" if low > 0 else "no detectable difference"}


def summary(rows: dict, keys: list[tuple]) -> dict:
    return {"mean_wis": round(statistics.fmean(rows[k]["wis"] for k in keys), 3),
            "mean_wis_uncapped": round(statistics.fmean(rows[k]["wis_uncapped"] for k in keys), 3),
            "cover50": round(statistics.fmean(rows[k]["cover50"] for k in keys), 3),
            "cover95": round(statistics.fmean(rows[k]["cover95"] for k in keys), 3),
            "capped_rows": sum(rows[k]["capped"] for k in keys)}


def compare(scores: dict, version: str, system: str, keys: list[tuple], keys_kept: list[tuple]) -> dict:
    rows, base = scores[(system, version)], scores[(BASELINE, version)]
    return {
        "relative_wis": relative(rows, base, keys),
        "relative_mae": relative(rows, base, keys, "ae"),
        "relative_wis_by_pathogen": {p: relative(rows, base, [k for k in keys if k[0] == p]) for p in PATHOGENS},
        "relative_wis_by_horizon": {h: relative(rows, base, [k for k in keys if rows[k]["horizon"] == h])
                                    for h in range(1, 5)},
        "relative_wis_by_state": by_state(rows, base, keys),
        "location_normalized_relative_wis": normalized(rows, base, keys),
        "sensitivity_uncapped": relative(rows, base, keys, "wis_uncapped"),
        "sensitivity_fallbacks_kept": relative(rows, base, keys_kept),
    }


def analyze(scores: dict) -> dict:
    systems = [BASELINE, *SYSTEMS]
    out = {"systems": systems, "versions": {}}
    keys_by_version = {}
    for version in VERSIONS:
        keys = common(scores, version, systems)
        kept = common(scores, version, systems, keep_fallback=True)
        keys_by_version[version] = keys
        result = {"rows": len(keys), "rows_with_fallbacks_kept": len(kept),
                  "removed_for_fallbacks": {s: sum(scores[(s, version)][k]["fallback"] for k in kept)
                                            for s in systems},
                  "summary": {s: summary(scores[(s, version)], keys) for s in systems}}
        ranking = sorted(systems, key=lambda s: result["summary"][s]["mean_wis"])
        result["rank_by_mean_wis"] = ranking
        for system in SYSTEMS:
            result[system] = compare(scores, version, system, keys, kept)
        result["chronos2_synth_vs_chronos2"] = relative(scores[("chronos2_synth", version)],
                                                        scores[("chronos2", version)], keys)
        ed_systems = [BASELINE, "lightgbm", "lightgbm_ed"]
        ed_keys = common(scores, version, ed_systems)
        ed, lgb, base = (scores[(s, version)] for s in ("lightgbm_ed", "lightgbm", BASELINE))
        result["lightgbm_ed"] = {"rows": len(ed_keys), "first_date": ed_keys[0][DATE] if ed_keys else None,
                                 "summary": {s: summary(scores[(s, version)], ed_keys) for s in ed_systems},
                                 "relative_wis_vs_persistence": relative(ed, base, ed_keys),
                                 "relative_wis_vs_lightgbm": relative(ed, lgb, ed_keys),
                                 "lightgbm_relative_wis_vs_persistence_same_rows": relative(lgb, base, ed_keys)}
        out["versions"][version] = result
    out["revision_effect"] = {s: revision_effect(scores, s, keys_by_version) for s in SYSTEMS}
    out["rank_change"] = {v: out["versions"][v]["rank_by_mean_wis"] for v in VERSIONS}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=RUNS.parent / "analysis.json")
    args = parser.parse_args(argv)
    result = analyze(load())
    args.out.write_text(json.dumps(result, indent=1) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
