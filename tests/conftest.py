"""A tiny ObsAwareData mirror for one made-up state (ZZ), laid out like the real repository."""

from __future__ import annotations

import csv
import gzip
import hashlib
from pathlib import Path

import pytest

from resplens.data import Dataset


LONG_COLUMNS = ["stream_id", "source_snapshot_id", "as_of_date", "observation_week", "analysis_region",
                "analysis_region_type", "analysis_region_id", "raw_geography_type", "raw_geography_id", "pathogen",
                "feature_name", "weekly_feature", "feature_unit", "observation_state", "definition_status"]
WEEKS = ["2026-09-05", "2026-09-12", "2026-09-19", "2026-09-26", "2026-10-03", "2026-10-10"]
STATE = ("Zedland", "state", "99", "state_abbreviation", "ZZ")
HSA = ("North, ZZ - South, ZZ", "sub_state_hsa", "7", "hsa_member_counties", "North, South")
SITE = ("ID:5", "sampling_site", "ID:5", "state_territory", "Zedland")


def row(stream, snapshot, as_of, week, region, pathogen, feature, value, unit, flag, status="confirmed"):
    return [stream, snapshot, as_of, week, *region, pathogen, feature, value, unit, flag, status]


def latest_rows() -> list[list[str]]:
    rows = []
    admissions = ["40", "44", "", "90", "60", "65"]
    admission_flags = ["observed_valid", "observed_valid", "incidental_missing", "flagged_anomalous",
                       "observed_valid", "observed_valid"]
    reporting = ["30", "31", "30", "12", "30", "30"]
    for week, value, flag, hospitals in zip(WEEKS, admissions, admission_flags, reporting):
        snap = "nhsn_20261016_standard_aaaaaaaaaaaa"
        rows.append(row("nhsn", snap, "2026-10-16", week, STATE, "covid", "hospital_admission_count", value, "count",
                        flag))
        rows.append(row("nhsn", snap, "2026-10-16", week, STATE, "covid", "hospital_reporting_count", hospitals,
                        "count", "observed_valid"))
        low = int(hospitals) < 20
        rows.append(row("nhsn", snap, "2026-10-16", week, STATE, "covid", "coverage_status",
                        "reduced_participation" if low else "full_participation", "categorical_coverage_status",
                        "observed_low_coverage" if low else "observed_valid", "observed_definition_uncertain"))
    for index, week in enumerate(WEEKS):
        snap = "nssp_20261014_standard_bbbbbbbbbbbb"
        for region in (STATE, HSA):
            rows.append(row("nssp", snap, "2026-10-14", week, region, "covid", "ed_visit_percent_smoothed",
                            f"{1.0 + index / 10:.2f}", "percent_ed_visits", "observed_valid"))
            rows.append(row("nssp", snap, "2026-10-14", week, region, "covid", "ed_trend_category",
                            "Increasing" if index < 5 else "Limited Data", "categorical_trend",
                            "observed_valid" if index < 5 else "observed_low_coverage",
                            "observed_definition_uncertain"))
        rows.append(row("nssp", snap, "2026-10-14", week, HSA, "not_applicable", "participation_status",
                        "full_participation", "categorical_coverage_status", "observed_valid",
                        "observed_definition_uncertain"))
        snap = "nwss_20261016_cccccccccccc"
        rows.append(row("nwss", snap, "2026-10-16", week, SITE, "covid", "wastewater_activity_category", "High",
                        "ordinal_category", "observed_valid"))
        rows.append(row("nwss", snap, "2026-10-16", week, SITE, "covid", "participation_status",
                        "reduced_participation", "categorical_coverage_status", "observed_low_coverage",
                        "observed_definition_uncertain"))
    return rows


def version_rows() -> list[list[str]]:
    """Week 2026-10-03 admissions: preliminary 50, standard 55 the same day, revised to 60 a week later."""
    week = "2026-10-03"
    rows = [
        row("nhsn", "nhsn_20261007_preliminary_111111111111", "2026-10-07", week, STATE, "covid",
            "hospital_admission_count", "50", "count", "observed_valid"),
        row("nhsn", "nhsn_20261007_standard_222222222222", "2026-10-07", week, STATE, "covid",
            "hospital_admission_count", "55", "count", "observed_valid"),
        row("nhsn", "nhsn_20261014_standard_333333333333", "2026-10-14", week, STATE, "covid",
            "hospital_admission_count", "60", "count", "observed_valid"),
        row("nhsn", "nhsn_20261007_standard_222222222222", "2026-10-07", "2026-09-26", STATE, "covid",
            "hospital_admission_count", "88", "count", "flagged_anomalous"),
    ]
    return [[*values, "2026-10-16"] for values in rows]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture(scope="session")
def mirror(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("obsawaredata")
    latest = root / "data" / "ZZ" / "zz_long_latest_2026.csv"
    write_csv(latest, LONG_COLUMNS, latest_rows())
    write_csv(root / "metadata" / "manifest.csv", ["path", "bytes", "sha256"],
              [["data/ZZ/zz_long_latest_2026.csv", str(latest.stat().st_size), sha256(latest)]])
    write_csv(root / "metadata" / "coverage_summary.csv",
              ["state", "state_name", "state_fips", "nhsn_first_week", "nhsn_last_week", "nssp_first_week",
               "nssp_last_week", "nwss_first_week", "nwss_last_week"],
              [["ZZ", "Zedland", "99", *([WEEKS[0], WEEKS[-1]] * 3)]])
    write_csv(root / "metadata" / "observation_state_thresholds.csv",
              ["state", "nhsn_min_reporting_hospitals", "nhsn_admission_change_pct"], [["ZZ", "20", "100"]])
    history = root / "releases" / "zz_long_all_versions.csv.gz"
    history.parent.mkdir(parents=True)
    with gzip.open(history, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([*LONG_COLUMNS, "extract_timestamp"])
        writer.writerows(version_rows())
    write_csv(root / "metadata" / "release_assets.csv", ["state", "file", "kind", "sha256", "url"],
              [["ZZ", history.name, "full", sha256(history), ""]])
    return root


@pytest.fixture()
def ds(mirror) -> Dataset:
    return Dataset(mirror=mirror)
