import os

import pytest

from resplens import tools
from resplens.data import DataError, Dataset


def test_describe_state_lists_regions(ds):
    state = tools.describe_state(ds, "zz")
    assert state["state"] == "ZZ" and state["fips"] == "99"
    assert state["ed_regions"] == [{"id": "7", "name": "North, ZZ - South, ZZ", "counties": "North, South"}]
    assert state["wastewater_sites"][0]["id"] == "ID:5"


def test_unknown_state_is_rejected(ds):
    with pytest.raises(DataError, match="unknown state"):
        tools.describe_state(ds, "XX")


def test_get_series_keeps_flags_and_gaps(ds):
    series = tools.get_series(ds, "ZZ", "hospital_admission_count", "covid")
    weeks = {week["week"]: week for week in series["weeks"]}
    assert weeks["2026-09-19"] == {"week": "2026-09-19", "value": None, "flag": "incidental_missing",
                                   "as_of": "2026-10-16"}
    assert weeks["2026-09-26"]["flag"] == "flagged_anomalous"
    assert series["flag_counts"]["observed_valid"] == 4
    assert isinstance(weeks["2026-10-10"]["value"], int)


def test_get_series_range_and_truncation(ds):
    series = tools.get_series(ds, "ZZ", "hospital_admission_count", "covid", start="2026-09-12", max_weeks=2)
    assert [week["week"] for week in series["weeks"]] == ["2026-10-03", "2026-10-10"]
    assert series["truncated_to_latest_weeks"] == 2


def test_get_series_hsa_requires_region_id(ds):
    with pytest.raises(DataError, match="region_id is required"):
        tools.get_series(ds, "ZZ", "ed_visit_percent_smoothed", "covid", region_type="sub_state_hsa")
    series = tools.get_series(ds, "ZZ", "ed_visit_percent_smoothed", "covid", "sub_state_hsa", "7")
    assert series["region"]["name"] == "North, ZZ - South, ZZ"
    assert series["weeks"][-1]["value"] == 1.5


@pytest.mark.parametrize("measure, pathogen, region_type, message", [
    ("hospital_admission_count", "combined", "state", "published for pathogens"),
    ("wastewater_activity_category", "covid", "state", "published for region types"),
    ("participation_status", "not_applicable", "sampling_site", "published for region types"),
    ("hospital_beds", "covid", "state", "unknown measure"),
])
def test_invalid_requests_explain_the_fix(ds, measure, pathogen, region_type, message):
    with pytest.raises(DataError, match=message):
        tools.get_series(ds, "ZZ", measure, pathogen, region_type, "ID:5")


def test_bad_date_is_rejected(ds):
    with pytest.raises(DataError, match="YYYY-MM-DD"):
        tools.get_series(ds, "ZZ", "hospital_admission_count", "covid", start="10/03/2026")


def test_check_reliability_reports_caveats(ds):
    report = tools.check_reliability(ds, "ZZ", "covid", weeks=6)
    assert report["window"] == {"start": "2026-09-05", "end": "2026-10-10"}
    assert report["hospital_admissions"]["weeks_reduced_participation"] == ["2026-09-26"]
    assert report["ed_visits"]["latest_trend"] == "Limited Data"
    assert report["wastewater"]["latest_week_categories"] == {"High": 1}
    caveats = " ".join(report["caveats"])
    assert "2026-09-26" in caveats and "missing for: 2026-09-19" in caveats
    assert "unavailable or limited in: 2026-10-10" in caveats
    assert "1 of 1 wastewater sites" in caveats


def test_check_reliability_window_end(ds):
    report = tools.check_reliability(ds, "ZZ", "covid", weeks=2, end="2026-09-12")
    assert report["window"] == {"start": "2026-09-05", "end": "2026-09-12"}
    assert report["caveats"] == ["1 of 1 wastewater sites report irregularly (reduced participation)."]


def test_get_revisions_keeps_change_points(ds):
    revisions = tools.get_revisions(ds, "ZZ", "hospital_admission_count", "covid", "2026-10-03")
    assert revisions["releases"] == 3 and revisions["changes"] == 2
    assert (revisions["first_value"], revisions["latest_value"]) == (50, 60)
    assert revisions["percent_change_first_to_latest"] == 20.0


def test_get_as_of_prefers_standard_release_on_the_same_day(ds):
    series = tools.get_as_of(ds, "ZZ", "hospital_admission_count", "covid", "2026-10-07")
    assert [(week["week"], week["value"]) for week in series["weeks"]] == [("2026-09-26", 88), ("2026-10-03", 55)]
    later = tools.get_as_of(ds, "ZZ", "hospital_admission_count", "covid", "2026-10-20")
    assert later["weeks"][-1]["value"] == 60


def test_get_as_of_before_history_starts(ds):
    with pytest.raises(DataError, match="revision history starts on 2026-10-07"):
        tools.get_as_of(ds, "ZZ", "hospital_admission_count", "covid", "2026-01-01")


def test_checksum_mismatch_is_detected(mirror, tmp_path):
    import shutil
    copy = tmp_path / "mirror"
    shutil.copytree(mirror, copy)
    with (copy / "data" / "ZZ" / "zz_long_latest_2026.csv").open("a") as handle:
        handle.write("tampered\n")
    with pytest.raises(DataError, match="checksum mismatch"):
        Dataset(mirror=copy).latest("ZZ")


def test_describe_measures_covers_every_measure():
    described = tools.describe_measures()
    assert {item["measure"] for item in described["measures"]} == set(tools.MEASURES)
    assert set(described["usable_flags"]) <= set(described["flags"])


@pytest.mark.skipif(not os.environ.get("RESPLENS_NETWORK_TESTS"), reason="set RESPLENS_NETWORK_TESTS=1")
def test_real_release_south_carolina():
    real = Dataset()
    revisions = tools.get_revisions(real, "SC", "hospital_admission_count", "covid", "2026-01-03")
    latest = tools.get_series(real, "SC", "hospital_admission_count", "covid", start="2026-01-03", end="2026-01-03")
    assert revisions["latest_value"] == latest["weeks"][0]["value"]
