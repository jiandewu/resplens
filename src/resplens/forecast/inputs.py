"""Inputs for the full B1 benchmark (plan: docs/forecast-eval.md): every series a model sees, built once and cached.

    uv run python -m resplens.forecast.inputs --split dev --version revised     # resumable
    uv run python -m resplens.forecast.inputs --split test --version realtime
    uv run python -m resplens.forecast.inputs --split test --version revised

Each row is one (forecast date, pathogen, state): the series as the model would see it (real time: the newest release
on or before the date; revised: the pinned release cut at the same last week; dev: the pinned release cut where a
standard release would usually end), the NSSP ED percent series for the same pathogen on the same terms (test dates
from ED_FROM only), and whether the row passes the minimum-history rule.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .. import tools
from ..data import DATA_TAG, DataError, Dataset
from ..retrieval.evaluate import ROOT
from . import vintage

PATHOGENS = ("covid", "influenza", "rsv")
DATES = {"dev": vintage.fridays("2022-10-07", "2025-03-07"), "test": vintage.fridays("2025-04-04", "2026-07-24")}
MIN_OBSERVED, HISTORY_WEEKS = 26, 52  # at least 26 observed weeks among the last 52
ED_MEASURE = "ed_visit_percent"
ED_FROM = "2025-08-15"  # first NSSP release in the history
CACHE = ROOT / "cache" / "forecast-b1"


@dataclass
class Item:
    """One location-pathogen series on one forecast date, with interior gaps filled (see fill)."""

    state: str
    pathogen: str
    date: str
    first_week: str  # week of values[0]
    values: list[float]  # ends at the last observed week
    eligible: bool = True
    ed: dict[str, float] = field(default_factory=dict)  # NSSP week -> percent, empty if not used

    @property
    def last_week(self) -> str:
        return week_at(self.first_week, len(self.values) - 1)

    def k(self, target: str) -> int:
        return (date.fromisoformat(target) - date.fromisoformat(self.last_week)).days // 7

    def series(self) -> vintage.Series:
        return [(week_at(self.first_week, i), v) for i, v in enumerate(self.values)]


def week_at(first_week: str, i: int) -> str:
    return (date.fromisoformat(first_week) + timedelta(days=7 * i)).isoformat()


def enough_history(series: vintage.Series) -> bool:
    if not any(v is not None for _, v in series):
        return False
    last = vintage.last_observed(series)[0]
    recent = [v for w, v in series if w <= last][-HISTORY_WEEKS:]
    return sum(v is not None for v in recent) >= MIN_OBSERVED


def fill(series: vintage.Series) -> tuple[str, list[float]]:
    """Drop weeks before the first and after the last observed value, and fill missing weeks in between by linear
    interpolation of log1p(value). Returns the first week and the values."""
    observed = [i for i, (_, v) in enumerate(series) if v is not None]
    first, last = observed[0], observed[-1]
    values = [series[i][1] for i in range(first, last + 1)]
    known = [i for i, v in enumerate(values) if v is not None]
    out = []
    for i, v in enumerate(values):
        if v is not None:
            out.append(float(v))
            continue
        before = max(j for j in known if j < i)
        after = min(j for j in known if j > i)
        a, b = math.log1p(values[before]), math.log1p(values[after])
        out.append(math.expm1(a + (b - a) * (i - before) / (after - before)))
    return series[first][0], out


def nhsn(ds: Dataset, split: str, version: str, state: str, pathogen: str, day: str) -> vintage.Series:
    if split == "dev":
        return vintage.revised(ds, state, pathogen, vintage.standard_last_week(day))
    real = vintage.real_time(ds, state, pathogen, day)
    if version == "realtime" or not real:
        return real
    return vintage.revised(ds, state, pathogen, real[-1][0])


def ed(ds: Dataset, split: str, version: str, state: str, pathogen: str, day: str) -> dict[str, float]:
    if split == "dev" or day < ED_FROM:
        return {}
    try:
        real = tools.get_as_of(ds, state, ED_MEASURE, pathogen, day, max_weeks=vintage.MAX_WEEKS)["weeks"]
    except DataError:  # a state's NSSP history can start later (MO: 2026-06-12): no ED series before it
        return {}
    if version == "revised" and real:
        real = tools.get_series(ds, state, ED_MEASURE, pathogen, end=real[-1]["week"],
                                max_weeks=vintage.MAX_WEEKS)["weeks"]
    return {row["week"]: row["value"] for row in real if row["value"] is not None}


def path(split: str, version: str) -> Path:
    return CACHE / f"inputs-{split}-{version}.jsonl.gz"


def build(split: str, version: str, ds: Dataset | None = None, states: list[str] | None = None,
          dates: list[str] | None = None, out: Path | None = None) -> Path:
    ds = ds or Dataset()
    out = out or path(split, version)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with gzip.open(out, "rt") as handle:
            done = {(r["date"], r["pathogen"], r["state"]) for r in map(json.loads, handle)}
    states = states or sorted(ds.coverage)
    with gzip.open(out, "at") as handle:
        for day in dates or DATES[split]:
            for pathogen in PATHOGENS:
                for state in states:
                    if (day, pathogen, state) in done:
                        continue
                    series = nhsn(ds, split, version, state, pathogen, day)
                    row = {"date": day, "pathogen": pathogen, "state": state, "data_release": DATA_TAG,
                           "first_week": series[0][0] if series else None, "raw": [v for _, v in series],
                           "ed": ed(ds, split, version, state, pathogen, day) if series else {}}
                    handle.write(json.dumps(row) + "\n")
            handle.flush()
            print(split, version, day, flush=True)
    return out


def load(split: str, version: str, source: Path | None = None) -> tuple[dict[tuple[str, str], list[Item]], dict]:
    """(date, pathogen) -> eligible items sorted by state, and counts of rows removed by the minimum-history rule.
    The cache holds the raw series; filling and the eligibility rule are applied here."""
    groups, removed = defaultdict(list), defaultdict(int)
    with gzip.open(source or path(split, version), "rt") as handle:
        for row in map(json.loads, handle):
            series = [(week_at(row["first_week"], i), v) for i, v in enumerate(row["raw"])] if row["raw"] else []
            if not enough_history(series):
                removed[row["pathogen"]] += 1
                continue
            first, values = fill(series)
            groups[(row["date"], row["pathogen"])].append(
                Item(row["state"], row["pathogen"], row["date"], first, values, True, row["ed"]))
    return {key: sorted(items, key=lambda i: i.state) for key, items in groups.items()}, dict(removed)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--split", choices=sorted(DATES), required=True)
    parser.add_argument("--version", choices=["realtime", "revised"], required=True)
    args = parser.parse_args(argv)
    if args.split == "dev" and args.version != "revised":
        parser.error("dev has no release history; use --version revised")
    print(build(args.split, args.version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
