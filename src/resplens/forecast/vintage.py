"""Weekly series as published on a forecast date (real time) or from the pinned release (revised), and the targets.

A series is a list of (week, value) for every week from the first to the last, with None where a week is missing.
"""

from __future__ import annotations

from datetime import date, timedelta

from .. import tools
from ..data import Dataset


MEASURE = "hospital_admission_count"
MAX_WEEKS = 520
TARGET_DAYS = (1, 8, 15, 22)  # targets are the weeks ending 1, 8, 15 and 22 days after a Friday forecast date
REPORTING_LAG_DAYS = 6  # a standard release usually ends with the week that ended 6 days earlier

Series = list[tuple[str, int | float | None]]


def weekly(rows: list[dict]) -> Series:
    """Every week from the first to the last row, with None for weeks that are missing or absent."""
    values = {row["week"]: row["value"] for row in rows}
    if not values:
        return []
    week, last = date.fromisoformat(min(values)), date.fromisoformat(max(values))
    series = []
    while week <= last:
        series.append((week.isoformat(), values.get(week.isoformat())))
        week += timedelta(days=7)
    return series


def real_time(ds: Dataset, state: str, pathogen: str, forecast_date: str) -> Series:
    """The series as published on the forecast date: the newest release on or before it, standard over preliminary."""
    return weekly(tools.get_as_of(ds, state, MEASURE, pathogen, forecast_date, max_weeks=MAX_WEEKS)["weeks"])


def revised(ds: Dataset, state: str, pathogen: str, last_week: str) -> Series:
    """The series from the pinned release, cut at last_week."""
    return weekly(tools.get_series(ds, state, MEASURE, pathogen, end=last_week, max_weeks=MAX_WEEKS)["weeks"])


def targets(forecast_date: str) -> list[str]:
    day = date.fromisoformat(forecast_date)
    return [(day + timedelta(days=days)).isoformat() for days in TARGET_DAYS]


def standard_last_week(forecast_date: str) -> str:
    """The last week a release on the forecast date would usually contain (used on dev, where no history exists)."""
    return (date.fromisoformat(forecast_date) - timedelta(days=REPORTING_LAG_DAYS)).isoformat()


def last_observed(series: Series) -> tuple[str, int | float]:
    for week, value in reversed(series):
        if value is not None:
            return week, value
    raise ValueError("the series has no observed values")


def truth(ds: Dataset, state: str, pathogen: str, weeks: list[str]) -> dict[str, int | float | None]:
    """Values in the pinned release for the given weeks (None if missing)."""
    rows = tools.get_series(ds, state, MEASURE, pathogen, start=min(weeks), end=max(weeks), max_weeks=MAX_WEEKS)
    values = {row["week"]: row["value"] for row in rows["weeks"]}
    return {week: values.get(week) for week in weeks}


def fridays(first: str, last: str) -> list[str]:
    day, end = date.fromisoformat(first), date.fromisoformat(last)
    out = []
    while day <= end:
        out.append(day.isoformat())
        day += timedelta(days=7)
    return out
