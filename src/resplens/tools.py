"""Query tools over ObsAwareData, shaped for LLM tool calling.

Every value is returned with its reliability flag; nothing here averages or fills in
values. Measure and flag definitions follow the ObsAwareData DATA_DICTIONARY.md.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from .data import DataError, Dataset


# feature_name -> (stream, allowed pathogens, allowed region types, unit kind)
MEASURES = {
    "hospital_admission_count": ("nhsn", ("covid", "influenza", "rsv"), ("state",), "number"),
    "hospital_reporting_count": ("nhsn", ("covid", "influenza", "rsv"), ("state",), "number"),
    "coverage_status": ("nhsn", ("covid", "influenza", "rsv"), ("state",), "label"),
    "ed_visit_percent": ("nssp", ("covid", "influenza", "rsv", "combined"), ("state", "sub_state_hsa"), "number"),
    "ed_visit_percent_smoothed": ("nssp", ("covid", "influenza", "rsv", "combined"), ("state", "sub_state_hsa"),
                                  "number"),
    "ed_trend_category": ("nssp", ("covid", "influenza", "rsv"), ("state", "sub_state_hsa"), "label"),
    "wastewater_activity_level": ("nwss", ("covid", "influenza", "rsv"), ("sampling_site",), "number"),
    "wastewater_activity_category": ("nwss", ("covid", "influenza", "rsv"), ("sampling_site",), "label"),
    # participation_status exists in two sources; the pathogen tells them apart.
    "participation_status": (None, ("not_applicable", "covid", "influenza", "rsv"), ("sub_state_hsa", "sampling_site"),
                             "label"),
}

MEASURE_NOTES = {
    "hospital_admission_count": "New hospital admissions with a laboratory-confirmed diagnosis, all ages (NHSN).",
    "hospital_reporting_count": "Hospitals that reported that week: the denominator behind the admission count (NHSN).",
    "coverage_status": "Derived: full_participation or reduced_participation (fewer reporting hospitals than the "
                       "state threshold).",
    "ed_visit_percent": "Percent of all ED visits matching the pathogen's syndrome definition (NSSP).",
    "ed_visit_percent_smoothed": "CDC's smoothed version of ed_visit_percent (NSSP).",
    "ed_trend_category": "CDC trend label: Increasing, Decreasing, No Change, or a data-availability note.",
    "wastewater_activity_level": "Site-level Wastewater Viral Activity Level (NWSS). Not comparable across pathogens; "
                                 "use caution across sites.",
    "wastewater_activity_category": "Very Low < Low < Moderate < High < Very High (NWSS); recommended for cross-site "
                                    "comparison.",
    "participation_status": "Derived. NSSP HSA rows (pathogen not_applicable): a member county lacked recent facility "
                            "data. NWSS sites: share of weeks with data below the state threshold.",
}

FLAGS = {
    "observed_valid": "A normal reported value.",
    "observed_zero": "A reported value of exactly zero; a real zero, not a gap.",
    "observed_low_coverage": "Reported, but based on reduced coverage (few reporting hospitals or facilities).",
    "flagged_anomalous": "Reported, but an unusually large week-over-week change, or blended wastewater sources. "
                         "Check before use.",
    "incidental_missing": "No value reported for a week within an otherwise active series.",
    "structural_absent": "Not collected in this period by design (RSV hospital data before 2024-08-03).",
}
USABLE_FLAGS = ("observed_valid", "observed_zero")
WW_CATEGORIES = ("Very Low", "Low", "Moderate", "High", "Very High")


def _iso(value: str | None, name: str) -> str | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise DataError(f"{name} must be a date in YYYY-MM-DD form, got {value!r}") from None


def _stream(measure: str, pathogen: str) -> str:
    stream = MEASURES[measure][0]
    if stream is None:
        return "nssp" if pathogen == "not_applicable" else "nwss"
    return stream


def _check_measure(measure: str, pathogen: str, region_type: str) -> tuple[str, str]:
    if measure not in MEASURES:
        raise DataError(f"unknown measure {measure!r}; choose one of {', '.join(MEASURES)}")
    _, pathogens, region_types, kind = MEASURES[measure]
    if pathogen not in pathogens:
        raise DataError(f"{measure} is published for pathogens {', '.join(pathogens)}, not {pathogen!r}")
    if measure == "participation_status":
        region_types = ("sub_state_hsa",) if pathogen == "not_applicable" else ("sampling_site",)
    if region_type not in region_types:
        raise DataError(f"{measure} is published for region types {', '.join(region_types)}, not {region_type!r}")
    return _stream(measure, pathogen), kind


def _value(raw: str, kind: str):
    if raw in (None, ""):
        return None
    if kind == "number":
        number = float(raw)
        return int(number) if number.is_integer() else number
    return raw


def _region_id(ds: Dataset, state: str, region_type: str, region_id: str | None) -> str:
    if region_type == "state":
        return ds.coverage[state]["state_fips"]
    if not region_id:
        raise DataError(f"region_id is required for {region_type}; call describe_state to list the regions")
    return region_id.strip()


def describe_state(ds: Dataset, state: str) -> dict:
    """Coverage, thresholds, and region lists for one state."""
    state = ds.state(state)
    view = ds.latest(state)
    coverage = ds.coverage[state]
    hsas = ds.query(f"SELECT DISTINCT analysis_region_id AS id, analysis_region AS name, raw_geography_id AS counties "
                    f"FROM {view} WHERE analysis_region_type = 'sub_state_hsa' ORDER BY TRY_CAST(id AS INTEGER), id")
    sites = ds.query(f"SELECT analysis_region_id AS id, list(DISTINCT pathogen ORDER BY pathogen) AS pathogens, "
                     f"max(observation_week) AS last_week FROM {view} "
                     f"WHERE analysis_region_type = 'sampling_site' GROUP BY 1 ORDER BY 1")
    return {
        "state": state,
        "name": coverage["state_name"],
        "fips": coverage["state_fips"],
        "dataset_release": ds.tag,
        "weeks": {stream: {"first": coverage[f"{stream}_first_week"], "last": coverage[f"{stream}_last_week"]}
                  for stream in ("nhsn", "nssp", "nwss")},
        "thresholds": {key: value for key, value in ds.thresholds[state].items() if key != "state"},
        "ed_regions": hsas,
        "wastewater_sites": [{**site, "pathogens": list(site["pathogens"])} for site in sites],
    }


def get_series(ds: Dataset, state: str, measure: str, pathogen: str, region_type: str = "state",
               region_id: str | None = None, start: str | None = None, end: str | None = None,
               max_weeks: int = 104) -> dict:
    """Weekly values with their reliability flags, newest weeks kept when the range is longer than max_weeks."""
    state = ds.state(state)
    stream, kind = _check_measure(measure, pathogen, region_type)
    region = _region_id(ds, state, region_type, region_id)
    start, end = _iso(start, "start"), _iso(end, "end")
    max_weeks = max(1, min(int(max_weeks), 520))
    rows = ds.query(
        f"SELECT observation_week, weekly_feature, observation_state, as_of_date, feature_unit, definition_status, "
        f"analysis_region FROM {ds.latest(state)} WHERE stream_id = ? AND feature_name = ? AND pathogen = ? "
        f"AND analysis_region_type = ? AND analysis_region_id = ? "
        f"AND (? IS NULL OR observation_week >= ?) AND (? IS NULL OR observation_week <= ?) "
        f"ORDER BY observation_week",
        [stream, measure, pathogen, region_type, region, start, start, end, end])
    if not rows:
        raise DataError(f"no {measure} {pathogen} data for {state} {region_type} {region!r} in that range")
    truncated = len(rows) > max_weeks
    rows = rows[-max_weeks:]
    return {
        "state": state,
        "measure": measure,
        "pathogen": pathogen,
        "source": stream,
        "region": {"type": region_type, "id": region, "name": rows[-1]["analysis_region"]},
        "unit": rows[-1]["feature_unit"],
        "definition_status": rows[-1]["definition_status"],
        "truncated_to_latest_weeks": max_weeks if truncated else None,
        "flag_counts": dict(Counter(row["observation_state"] for row in rows)),
        "weeks": [{"week": row["observation_week"], "value": _value(row["weekly_feature"], kind),
                   "flag": row["observation_state"], "as_of": row["as_of_date"]} for row in rows],
    }


def _window(ds: Dataset, view: str, weeks: int, end: str | None) -> tuple[str, str]:
    if end is None:
        end = ds.query(f"SELECT max(observation_week) AS week FROM {view} WHERE stream_id = 'nhsn'")[0]["week"]
    start = (date.fromisoformat(end) - timedelta(weeks=weeks - 1)).isoformat()
    return start, end


def check_reliability(ds: Dataset, state: str, pathogen: str, weeks: int = 8, end: str | None = None) -> dict:
    """Rule-based summary of how far the recent data for one pathogen can be trusted.

    Looks at the last ``weeks`` weeks ending at ``end`` (default: the latest NHSN week) and
    returns per-source flag counts plus plain-language caveats derived from them.
    """
    state = ds.state(state)
    if pathogen not in ("covid", "influenza", "rsv"):
        raise DataError("pathogen must be covid, influenza, or rsv")
    weeks = max(1, min(int(weeks), 52))
    view = ds.latest(state)
    start, end = _window(ds, view, weeks, _iso(end, "end"))
    threshold = int(ds.thresholds[state]["nhsn_min_reporting_hospitals"])
    caveats: list[str] = []

    def series(stream, measure, region_type="state"):
        return ds.query(
            f"SELECT observation_week AS week, analysis_region_id AS region, weekly_feature AS value, "
            f"observation_state AS flag FROM {view} WHERE stream_id = ? AND feature_name = ? AND pathogen = ? "
            f"AND analysis_region_type = ? AND observation_week BETWEEN ? AND ? ORDER BY week",
            [stream, measure, pathogen, region_type, start, end])

    def flagged(rows, *flags):
        return [row["week"] for row in rows if row["flag"] in flags]

    # Hospital admissions (NHSN)
    admissions = series("nhsn", "hospital_admission_count")
    reporting = series("nhsn", "hospital_reporting_count")
    low_reporting = flagged(series("nhsn", "coverage_status"), "observed_low_coverage")
    nhsn = {
        "weeks_with_data": len(admissions),
        "last_week": admissions[-1]["week"] if admissions else None,
        "flag_counts": dict(Counter(row["flag"] for row in admissions)),
        "reporting_hospitals_latest": _value(reporting[-1]["value"], "number") if reporting else None,
        "reporting_threshold": threshold,
        "weeks_reduced_participation": low_reporting,
    }
    if not admissions:
        caveats.append("No hospital admission data in this window.")
    if structural := flagged(admissions, "structural_absent"):
        caveats.append(f"Hospital {pathogen} admissions were not collected by design for {len(structural)} week(s).")
    if anomalous := flagged(admissions, "flagged_anomalous"):
        caveats.append(f"Hospital admissions had an unusually large week-over-week change in: {', '.join(anomalous)}.")
    if missing := flagged(admissions, "incidental_missing"):
        caveats.append(f"Hospital admissions are missing for: {', '.join(missing)}.")
    if low_reporting:
        caveats.append(f"Fewer than {threshold} hospitals reported in: {', '.join(low_reporting)}; admission counts "
                       f"in those weeks undercount.")

    # Statewide ED visits (NSSP)
    ed = series("nssp", "ed_visit_percent_smoothed")
    trend = series("nssp", "ed_trend_category")
    nssp = {
        "weeks_with_data": len(ed),
        "last_week": ed[-1]["week"] if ed else None,
        "flag_counts": dict(Counter(row["flag"] for row in ed)),
        "latest_trend": trend[-1]["value"] if trend else None,
    }
    if not ed:
        caveats.append("No statewide ED visit data in this window.")
    if anomalous := flagged(ed, "flagged_anomalous"):
        caveats.append(f"Smoothed ED percent had an unusually large change in: {', '.join(anomalous)}.")
    if missing := flagged(ed, "incidental_missing"):
        caveats.append(f"Statewide ED percent is missing for: {', '.join(missing)}.")
    if limited := flagged(trend, "observed_low_coverage"):
        caveats.append(f"CDC marked the ED trend as unavailable or limited in: {', '.join(limited)}.")

    # Wastewater sites (NWSS)
    categories = series("nwss", "wastewater_activity_category", "sampling_site")
    participation = series("nwss", "participation_status", "sampling_site")
    last_ww = max((row["week"] for row in categories), default=None)
    latest_categories = Counter(row["value"] for row in categories if row["week"] == last_ww and row["value"])
    reduced_sites = sorted({row["region"] for row in participation if row["flag"] == "observed_low_coverage"})
    sites = sorted({row["region"] for row in categories})
    nwss = {
        "sites_with_data": len(sites),
        "last_week": last_ww,
        "latest_week_categories": {name: latest_categories[name] for name in WW_CATEGORIES if latest_categories[name]},
        "sites_reduced_participation": len(reduced_sites),
        "anomalous_site_weeks": len(flagged(categories, "flagged_anomalous")),
    }
    if not sites:
        caveats.append("No wastewater sites reported in this window.")
    elif len(reduced_sites) * 2 >= len(sites):
        caveats.append(f"{len(reduced_sites)} of {len(sites)} wastewater sites report irregularly "
                       f"(reduced participation).")
    if pathogen == "influenza" and sites:
        caveats.append("Wastewater influenza covers influenza A only.")

    for name, last in (("hospital", nhsn["last_week"]), ("ED", nssp["last_week"]), ("wastewater", last_ww)):
        if last and last < end:
            caveats.append(f"The latest {name} week is {last}, earlier than the window end {end}.")

    return {"state": state, "pathogen": pathogen, "window": {"start": start, "end": end},
            "hospital_admissions": nhsn, "ed_visits": nssp, "wastewater": nwss, "caveats": caveats}


def _versions_sql(view: str) -> str:
    # Release channel from source_snapshot_id: <stream>_<YYYYMMDD>[_<channel>]_<hash12>
    return (f"SELECT *, CASE WHEN split_part(source_snapshot_id, '_', 3) = 'standard' THEN 1 ELSE 0 END AS standard "
            f"FROM {view} WHERE stream_id = ? AND feature_name = ? AND pathogen = ? "
            f"AND analysis_region_type = ? AND analysis_region_id = ?")


def get_revisions(ds: Dataset, state: str, measure: str, pathogen: str, week: str, region_type: str = "state",
                  region_id: str | None = None) -> dict:
    """Every published version of one week's value, oldest release first."""
    state = ds.state(state)
    stream, kind = _check_measure(measure, pathogen, region_type)
    region = _region_id(ds, state, region_type, region_id)
    week = _iso(week, "week")
    rows = ds.query(f"{_versions_sql(ds.versions(state))} AND observation_week = ? ORDER BY as_of_date, standard",
                    [stream, measure, pathogen, region_type, region, week])
    if not rows:
        raise DataError(f"no published versions of {measure} {pathogen} for {state} week {week}; the revision "
                        f"history starts in 2025 (NHSN), 2025-08 (NSSP), or 2026-08 (NWSS)")
    versions = [{"as_of": row["as_of_date"], "release": row["source_snapshot_id"],
                 "value": _value(row["weekly_feature"], kind), "flag": row["observation_state"]} for row in rows]
    # Most releases republish the same value; keep only the first release and each change.
    distinct = [current for previous, current in zip([None, *versions], versions)
                if previous is None or (previous["value"], previous["flag"]) != (current["value"], current["flag"])]
    changes = len(distinct) - 1
    first, last = versions[0]["value"], versions[-1]["value"]
    relative = None
    if kind == "number" and isinstance(first, (int, float)) and isinstance(last, (int, float)) and first:
        relative = round((last - first) / abs(first) * 100, 1)
    return {"state": state, "measure": measure, "pathogen": pathogen, "week": week,
            "region": {"type": region_type, "id": region}, "releases": len(versions), "changes": changes,
            "first_value": first, "latest_value": last, "latest_release": versions[-1]["release"],
            "percent_change_first_to_latest": relative, "change_points": distinct}


def get_as_of(ds: Dataset, state: str, measure: str, pathogen: str, as_of: str, region_type: str = "state",
              region_id: str | None = None, start: str | None = None, max_weeks: int = 104) -> dict:
    """The series as it was published on ``as_of``: for each week, the newest release on or before that date.

    When two releases share a date the standard release wins over the preliminary one,
    matching ObsAwareData's latest-value rule.
    """
    state = ds.state(state)
    stream, kind = _check_measure(measure, pathogen, region_type)
    region = _region_id(ds, state, region_type, region_id)
    as_of, start = _iso(as_of, "as_of"), _iso(start, "start")
    max_weeks = max(1, min(int(max_weeks), 520))
    view = ds.versions(state)
    first_release = ds.query(f"SELECT min(as_of_date) AS first FROM {view} WHERE stream_id = ?", [stream])[0]["first"]
    if first_release is None or as_of < first_release:
        raise DataError(f"the {stream} revision history starts on {first_release}; choose as_of on or after it")
    rows = ds.query(
        f"SELECT observation_week, weekly_feature, observation_state, as_of_date, source_snapshot_id FROM "
        f"({_versions_sql(view)} AND as_of_date <= ? AND (? IS NULL OR observation_week >= ?)) "
        f"QUALIFY row_number() OVER (PARTITION BY observation_week ORDER BY as_of_date DESC, standard DESC) = 1 "
        f"ORDER BY observation_week",
        [stream, measure, pathogen, region_type, region, as_of, start, start])
    if not rows:
        raise DataError(f"no {measure} {pathogen} data for {state} published by {as_of}")
    truncated = len(rows) > max_weeks
    rows = rows[-max_weeks:]
    return {"state": state, "measure": measure, "pathogen": pathogen, "as_of": as_of,
            "region": {"type": region_type, "id": region},
            "truncated_to_latest_weeks": max_weeks if truncated else None,
            "weeks": [{"week": row["observation_week"], "value": _value(row["weekly_feature"], kind),
                       "flag": row["observation_state"], "release": row["source_snapshot_id"]} for row in rows]}


def describe_measures() -> dict:
    """Measures, the pathogens and region types each is published for, and the reliability flag codes."""
    measures = []
    for name, (stream, pathogens, region_types, _) in MEASURES.items():
        measures.append({"measure": name, "source": stream or "nssp (not_applicable) / nwss",
                         "pathogens": list(pathogens), "region_types": list(region_types),
                         "meaning": MEASURE_NOTES[name]})
    return {"measures": measures, "flags": FLAGS, "usable_flags": list(USABLE_FLAGS),
            "source": "ObsAwareData DATA_DICTIONARY.md (CC BY 4.0)"}
