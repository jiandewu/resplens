# Data dictionary

This document describes every file type in `data/<ST>/` and `metadata/`, every column, the rules for building column names, and every code value that appears in the data.

Conventions used throughout:

- `<ST>` is the two-letter postal code in upper case (folder names). `<st>` is the same code in lower case (file-name prefix).
- All files are UTF-8 CSV with a header row. Missing values are empty cells (no `NA` or `null` strings).
- `observation_week` is the Saturday that ends the reporting week (`YYYY-MM-DD`).
- `pathogen` is one of `covid` (SARS-CoV-2 / COVID-19), `influenza` (influenza; influenza A only for wastewater), `rsv` (respiratory syncytial virus), `combined` (ED visits for any of the three), or `not_applicable` (measures with no pathogen dimension).

## Contents

1. [Files per state](#1-files-per-state)
2. [Long tables](#2-long-tables)
3. [Single-source wide tables](#3-single-source-wide-tables)
4. [All-sources wide table and its column-naming rules](#4-all-sources-wide-table)
5. [Measures](#5-measures)
6. [Reliability flags (`observation_state`)](#6-reliability-flags)
7. [Census variables](#census-variables)
8. [Quality report and metadata files](#8-quality-report-and-metadata-files)

## 1. Files per state

| File | Format | One row per | Contents |
|---|---|---|---|
| `<st>_long_latest_<year>.csv` | long | source x week x region x pathogen x measure | Latest published value of every measure, with provenance; one file per year of `observation_week` (see [section 2](#2-long-tables)) |
| `<st>_nhsn_wide.csv` | wide | week | Hospital admissions (state level) |
| `<st>_nssp_wide.csv` | wide | region x week | ED visits (state row plus one row per HSA) |
| `<st>_nwss_wide.csv` | wide | site x week | Wastewater, one row per sampling site |
| `<st>_all_sources_wide.csv` | wide | week | Everything above plus Census, side by side |
| `<st>_census_context.csv` | long | Census variable | State Census context |
| `<st>_quality_report.md` | text | - | Coverage, flag counts, consistency checks |
| `<st>_long_all_versions.csv.gz` | long, gzip | source x week x region x pathogen x measure x source release | Every published version of every value. **Distributed as GitHub Release assets**: one full file per state, then one increment per later release (`<st>_long_all_versions_added_<as-of date>.csv.gz`); all listed in `metadata/release_assets.csv`. |

All wide tables are reshaped from the `<st>_long_latest_<year>.csv` files and contain exactly the same values and flags (verified in each quality report). They hold the latest values only, with no revision history.

## 2. Long tables

The latest-value table is split into one file per year: `<st>_long_latest_<year>.csv` holds the weeks whose `observation_week` falls in `<year>` (for example, `tx_long_latest_2025.csv`). The files have the same columns; concatenate a state's files to get the complete table. A new file appears when the first week of a new year is published.

`<st>_long_all_versions.csv.gz` has the 16 columns below; `<st>_long_latest_<year>.csv` has the same columns without `extract_timestamp` (15 columns):

| Column | Type | Description |
|---|---|---|
| `stream_id` | text | Source system: `nhsn` (hospital admissions), `nssp` (ED visits), `nwss` (wastewater). |
| `source_snapshot_id` | text | The CDC release this value came from: `<stream>_<YYYYMMDD>[_<channel>]_<hash12>`. `<YYYYMMDD>` is the release date, `<channel>` (NHSN and NSSP) is `standard` or `preliminary`, and `<hash12>` is the first 12 hex digits of the raw file's SHA-256. The full SHA-256 and a download link for the archived raw file are in [`metadata/source_snapshots.csv`](#8-quality-report-and-metadata-files). In the latest-value files it is the earliest release since which every release carrying the row has published this same value and flags; the value is also the newest release's. A latest-value row therefore changes only when its content does. |
| `as_of_date` | date | Release date of that source file. |
| `extract_timestamp` | date | Revision history only: the as-of date of the ObsAwareData release that first published the row's source release, so a published row never changes. |
| `observation_week` | date | Week-ending Saturday the value describes (not when it was published). |
| `analysis_region` | text | Human-readable region name, e.g. `California`, `Butte (Chico), CA - Tehama, CA`, or a site ID. |
| `analysis_region_type` | text | `state`, `sub_state_hsa` (CDC health service area), or `sampling_site` (wastewater site). |
| `analysis_region_id` | text | Region identifier. State: two-digit FIPS code (e.g. `06`). HSA: NCI HSA code (e.g. `690`). Site: CDC's anonymous site ID (e.g. `ID:113`). **Unique only together with `analysis_region_type`**: in Pennsylvania, HSA `42` and state FIPS `42` coexist. |
| `raw_geography_type` | text | How the source labeled the geography: `state_abbreviation` (NHSN), `state_fips_placeholder` (NSSP state row), `hsa_member_counties` (NSSP HSA row), `state_territory` (NWSS). |
| `raw_geography_id` | text | The source's own geography label: postal code (NHSN), the source's state `fips` field exactly as published (e.g. `6,000` for California), the HSA's member counties (e.g. `Colusa, Sutter, Yuba`), or the full state name (NWSS). Kept for traceability only. |
| `pathogen` | text | See conventions above. |
| `feature_name` | text | The measure; see [section 5](#5-measures). |
| `weekly_feature` | number or text | The value. Numeric for counts, percents, and indices; a label for categorical measures. Empty when the source had no value. |
| `feature_unit` | text | `count`, `percent_ed_visits`, `wval_index_not_cross_pathogen_comparable`, `ordinal_category`, `categorical_trend`, or `categorical_coverage_status`. |
| `observation_state` | text | Reliability flag for this value; see [section 6](#6-reliability-flags). |
| `definition_status` | text | `confirmed`: the measure is fully defined by the source documentation. `observed_definition_uncertain`: usable, but either the source documentation leaves part of the definition open or the field is derived by this dataset. See section 5 for which measures are which. |

**Unique key:**

- `<st>_long_latest_<year>.csv` (all years together): (`stream_id`, `observation_week`, `analysis_region_type`, `analysis_region_id`, `pathogen`, `feature_name`).
- `<st>_long_all_versions.csv.gz`: the same columns plus `source_snapshot_id`.

**Latest vs. all versions.** The latest-value table keeps, for each key, the value from the most recent release that contains it, and cites the earliest release since which that value and its flags have been published unchanged. When two releases share an `as_of_date`, the `standard` release is preferred over `preliminary`. Because values are revised after first publication, filtering `<st>_long_all_versions.csv.gz` to releases with `as_of_date <= D` and keeping the latest per key reconstructs the data as it was available on date `D`. This works for any `D` covered by the retained releases: NHSN from <!-- auto:first_nhsn -->2025-04-04<!-- /auto:first_nhsn -->, NSSP from <!-- auto:first_nssp -->2025-08-15<!-- /auto:first_nssp -->, NWSS from <!-- auto:first_nwss -->2026-08-07<!-- /auto:first_nwss -->.

**Reading tip:** read all columns as text first (`dtype=str, keep_default_na=False` in pandas). Otherwise leading zeros in FIPS codes are lost, and categorical labels mix with numbers in `weekly_feature`.

## 3. Single-source wide tables

`<st>_nhsn_wide.csv`, `<st>_nssp_wide.csv`, and `<st>_nwss_wide.csv` each start with six key columns:

`analysis_region`, `analysis_region_type`, `analysis_region_id`, `raw_geography_type`, `raw_geography_id`, `observation_week`

These are followed by a pair of columns for every measure and pathogen the source publishes:

| Column name | Holds |
|---|---|
| `<measure>_<pathogen>` | the value (`weekly_feature` in the long table) |
| `<measure>_<pathogen>_flag` | its reliability flag (`observation_state` in the long table) |

Examples: `hospital_admission_count_covid` and `hospital_admission_count_covid_flag`, `ed_visit_percent_smoothed_rsv`, `wastewater_activity_category_influenza`. The ED `participation_status` has no pathogen dimension, so its columns are `participation_status_not_applicable` and `participation_status_not_applicable_flag`.

Rows exist only for (region, week) combinations the source reports. Within a row, a blank value **with** a flag is a reported gap (for example `incidental_missing`). A blank value **and** a blank flag means the source has no record for that pathogen in that region and week.

## 4. All-sources wide table

`<st>_all_sources_wide.csv` has one row per week, spanning every week in any source (<!-- auto:weeks_all_sources -->2020-08-08 to 2026-10-10<!-- /auto:weeks_all_sources -->), and one column per region, site, measure, and pathogen. Nothing is aggregated or averaged: each ED region and each wastewater site keeps its own columns. Column counts range from about 100 to 3,200 depending on how many regions and sites a state has.

**Column-naming rule:** `[<prefix>]<measure>_<pathogen>[_flag]`. The prefix identifies where the value comes from:

| Prefix | Source and geography | Example |
|---|---|---|
| none | NHSN state-level hospital admissions | `hospital_admission_count_influenza` |
| none | NSSP statewide ED values (published separately by CDC, not an average of the HSAs) | `ed_visit_percent_covid` |
| `HSA<code>_` | NSSP value for one health service area; `<code>` is its `analysis_region_id` | `HSA690_ed_visit_percent_covid` |
| `ID<n>_` | NWSS value for one wastewater site; `<n>` is the site ID without the colon (`ID:113` becomes `ID113`) | `ID113_wastewater_activity_level_covid` |
| `census_` | State Census variable, repeated unchanged on every row | `census_median_age` |

The measure names never overlap between NHSN and NSSP, so the unprefixed state-level columns are unambiguous. Every value column except `census_*` has a matching `_flag` column.

Blank cells:

- A blank flag means the source has no record for that region and week, for example weeks before a site started reporting, or weeks after a source's last published week. <!-- auto:source_end_dates -->All three sources end on 2026-10-10.<!-- /auto:source_end_dates -->
- A blank value with a non-blank flag is a reported gap.

Every wastewater site in the state appears here, including the few that serve counties in more than one ED region or more than one state.

`observation_week` is the first column. To map an `HSA<code>` back to its name and member counties, look up that `analysis_region_id` in `<st>_nssp_wide.csv`.

## 5. Measures

| `feature_name` | Source | Pathogens | Unit | `definition_status` | Meaning |
|---|---|---|---|---|---|
| `hospital_admission_count` | NHSN | covid, influenza, rsv | `count` | confirmed | New hospital admissions in the week with a laboratory-confirmed diagnosis, all ages. |
| `hospital_reporting_count` | NHSN | covid, influenza, rsv | `count` | confirmed | Number of hospitals that reported that week for that pathogen: the denominator behind the admission count. |
| `coverage_status` | NHSN (derived) | covid, influenza, rsv | `categorical_coverage_status` | uncertain | `full_participation` or `reduced_participation` (fewer reporting hospitals than the state's threshold; see [METHODS.md](METHODS.md)). Blank when `structural_absent`. |
| `ed_visit_percent` | NSSP | covid, influenza, rsv, combined | `percent_ed_visits` | confirmed | Percent of all ED visits in the region and week that match the pathogen's syndrome definition. |
| `ed_visit_percent_smoothed` | NSSP | covid, influenza, rsv, combined | `percent_ed_visits` | confirmed | CDC's smoothed version of the same percent. |
| `ed_trend_category` | NSSP | covid, influenza, rsv | `categorical_trend` | uncertain | CDC's trend label: `Increasing`, `Decreasing`, `No Change`, or a data-availability note: `Data Unavailable`, `Limited Data`, `Sparse`, `No Data`. |
| `participation_status` | NSSP (derived) | not_applicable | `categorical_coverage_status` | uncertain | HSA rows only. `reduced_participation` if at least one member county had no facility with recent data in CDC's 2026-08-06 facility map. The same value is applied to every week. |
| `wastewater_activity_level` | NWSS | covid, influenza, rsv | `wval_index_not_cross_pathogen_comparable` | uncertain | CDC's site-level Wastewater Viral Activity Level. **Not comparable across pathogens**, and use caution comparing across sites. |
| `wastewater_activity_category` | NWSS | covid, influenza, rsv | `ordinal_category` | confirmed | CDC's category for the same measurement: `Very Low` < `Low` < `Moderate` < `High` < `Very High`. The recommended field for cross-site or cross-pathogen comparison. |
| `participation_status` | NWSS (derived) | covid, influenza, rsv | `categorical_coverage_status` | uncertain | `reduced_participation` if the site's share of weeks with data is below the state's threshold for that pathogen (see [METHODS.md](METHODS.md)). Within each source release, one value per site and pathogen, repeated on every week and computed from that release alone. |

"Derived" measures are computed in this dataset from the source data. They are not published by CDC.

Coverage notes:

- In these releases, the NSSP `combined` series ends on 2024-09-28 in most states.
- Some HSAs have rows but no ED values at any time.
- NHSN influenza reporting starts in October 2020 for most states.
- Each state's own date ranges are in its quality report and in `metadata/coverage_summary.csv`.

## 6. Reliability flags

Each value in the long table carries one `observation_state`, and each value column in the wide tables has a `_flag` column with the same code.

| Code | Meaning | Where it occurs |
|---|---|---|
| `observed_valid` | A normal reported value. | all measures |
| `observed_zero` | A reported value of exactly zero. This is a real zero, not a gap. | hospital admission and reporting counts, both ED percents, wastewater level (rare) |
| `observed_low_coverage` | Reported, but based on reduced coverage. NHSN: fewer reporting hospitals than the state threshold. NSSP trend: CDC label `Data Unavailable` or `Limited Data`. Participation measures: `reduced_participation`. | `coverage_status`, `ed_trend_category`, both `participation_status` measures |
| `flagged_anomalous` | Reported, but an unusually large change from the previous week, or (wastewater) a week where CDC blended data from more than one source. Worth checking before use. | `hospital_admission_count`, `ed_visit_percent_smoothed`, wastewater level and category |
| `incidental_missing` | No value reported for a week within an otherwise active series. The value cell is blank. | `hospital_admission_count`, both ED percents |
| `structural_absent` | Not collected in this period by design. Currently only RSV hospital data up to 2024-08-03, before RSV reporting was required. | NHSN RSV measures |

Rules and per-state thresholds are in [METHODS.md](METHODS.md) and `metadata/observation_state_thresholds.csv`. Note that the ED trend labels `Sparse` and `No Data` are **not** flagged as low coverage; the flag follows CDC's own "unavailable/limited" labels only.

## Census variables

`<st>_census_context.csv` has one row per variable, with these columns: `analysis_region` (state name), `analysis_region_type` (`state`), `analysis_region_id` (FIPS), `product` (`acs_5yr_2022` or `population_estimates_2022`), `variable`, `value`. The same values appear as `census_<variable>` columns in `<st>_all_sources_wide.csv`.

| `variable` | Source code | Description |
|---|---|---|
| `total_population` / `_moe` | ACS DP05_0001E / M | Total population (estimate / margin of error) |
| `median_age` / `_moe` | ACS DP05_0018E / M | Median age, years |
| `percent_male` | ACS DP05_0002PE | Percent of population male |
| `population_under_18` / `_moe` | ACS DP05_0019E / M | Population under 18 years |
| `population_65_plus` / `_moe` | ACS DP05_0024E / M | Population 65 years and over |
| `percent_white_alone` | ACS DP05_0037PE | Percent White alone |
| `percent_black_alone` | ACS DP05_0038PE | Percent Black or African American alone |
| `percent_asian_alone` | ACS DP05_0044PE | Percent Asian alone |
| `percent_hispanic_or_latino` | ACS DP05_0073PE | Percent Hispanic or Latino (of any race) |
| `median_household_income` / `_moe` | ACS DP03_0062E / M | Median household income, 2022 inflation-adjusted dollars |
| `percent_below_poverty_all_people` | ACS DP03_0128PE | Percent of all people below the poverty level |
| `percent_bachelor_or_higher_25plus` | ACS DP02_0068PE | Percent of population 25+ with a bachelor's degree or higher |
| `unemployment_rate` | ACS DP03_0009PE | Unemployment rate, civilian labor force |
| `percent_no_health_insurance` | ACS DP03_0099PE | Percent of civilian noninstitutionalized population with no health insurance |
| `percent_no_vehicle_available` | ACS DP04_0058PE | Percent of occupied housing units with no vehicle available |
| `percent_broadband_internet_subscription` | ACS DP02_0154PE | Percent of households with a broadband internet subscription |
| `percent_occupants_per_room_1_01_to_1_50` | ACS S2501_C02_007E | Percent of occupied housing units with 1.01-1.50 occupants per room |
| `percent_occupants_per_room_1_51_plus` | ACS S2501_C02_008E | Percent of occupied housing units with 1.51 or more occupants per room |
| `POPESTIMATE2022` | PEP NST-EST2022 | Census Bureau population estimate, July 1, 2022 |

**Placeholder codes:** the Census Bureau uses large negative numbers such as `-555555555` in margin-of-error fields to mean "not applicable" (for example, `total_population_moe` for states, whose total population is controlled). They are kept unchanged from the source. Treat them as missing before doing arithmetic. Each quality report lists the affected variables.

## 8. Quality report and metadata files

**`<st>_quality_report.md`**, generated from the published files, contains:

- The number of ED regions and wastewater sites
- Source release dates
- Rows, columns, and size of each file
- First and last week with data by source and pathogen
- Counts of each reliability flag by measure
- The thresholds used for this state
- Census placeholder variables
- A list of consistency checks and their results. The checks cover: each latest-value file holding only its year's weeks, key uniqueness, every wide table cell matching the long table, weekly continuity, and agreement between the latest and all-versions tables. The report also summarizes the state's revision history: rows, releases per source, and how many values were revised after first publication.

**`metadata/coverage_summary.csv`**, one row per state:

| Column | Description |
|---|---|
| `state`, `state_name`, `state_fips` | Identifiers |
| `n_ed_regions` | Number of NSSP health service areas in the state |
| `n_wastewater_sites`, `n_wastewater_sites_<pathogen>` | Number of wastewater sites, in total and with data for each pathogen |
| `nhsn_first_week`, `nhsn_last_week`, `nssp_first_week`, `nssp_last_week`, `nwss_first_week`, `nwss_last_week` | First and last week with a value for the source's primary measure |
| `long_latest_rows`, `all_sources_wide_columns` | Table sizes |
| `all_checks_passed` | Whether every consistency check in the quality report passed |

**`metadata/observation_state_thresholds.csv`**, one row per state, gives the thresholds actually applied:

| Column | Description |
|---|---|
| `nhsn_min_reporting_hospitals` | `coverage_status` is `reduced_participation` below this many reporting hospitals |
| `nhsn_admission_change_pct` | `hospital_admission_count` is `flagged_anomalous` at or above this absolute week-over-week percent change |
| `nssp_smoothed_change_pct` | Same rule for `ed_visit_percent_smoothed` |
| `nwss_min_coverage_ratio_<pathogen>` | Wastewater `participation_status` is `reduced_participation` below this coverage ratio. Blank if the state has no sites for that pathogen. |

**`metadata/source_snapshots.csv`** lists every CDC source release used in the long tables and the revision history, one row each: `source_snapshot_id`, `stream_id`, `release_channel` (`standard` or `preliminary` for NHSN and NSSP; blank for NWSS), `as_of_date`, `source_file_hash` (full SHA-256 of the raw file, upper case), and `archive_url` (the raw file, unmodified and compressed with xz, in the [archive of CDC releases](https://github.com/jiandewu/ObsAwareData-pipeline); after decompressing, its SHA-256 matches `source_file_hash`). Join it to a long table on `source_snapshot_id`.

**`metadata/manifest.csv`** lists `path`, `bytes`, and `sha256` for every file under `data/`.

**`metadata/release_assets.csv`** lists every revision-history file of every state, in order: `tag` (the release the file is attached to), `version` (build rules), `state`, `file`, `kind` (`full` or `increment`), `as_of` (as-of date of that release), `snapshots` and `rows` (source releases and rows in the file), `bytes`, `sha256`, and `url` (direct download link). A state's files, concatenated in this order, form its complete revision history. Check each downloaded file against its `sha256`.
