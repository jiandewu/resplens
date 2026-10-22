# Methods

This document describes how the published tables were built from the public source files, how each reliability flag is assigned, and the known limitations. Column definitions are in [DATA_DICTIONARY.md](DATA_DICTIONARY.md) and source details in [DATA_SOURCES.md](DATA_SOURCES.md).

## 1. Processing overview

1. **Register every source release.** Each downloaded nationwide file (<!-- auto:releases_nhsn -->118<!-- /auto:releases_nhsn --> NHSN, <!-- auto:releases_nssp -->54<!-- /auto:releases_nssp --> NSSP, <!-- auto:releases_nwss -->11<!-- /auto:releases_nwss --> NWSS releases, plus the Census extracts) is kept unmodified and registered with its release date and SHA-256 hash. Earlier releases are never overwritten by later ones.
2. **Filter to the state.** Each state's rows are selected from the nationwide files. National, regional, and territory records are excluded.
3. **Standardize to one long schema.** Every value becomes one row: source, release, week, region, pathogen, measure, value, unit, reliability flag, definition status. Only the fields listed in [DATA_SOURCES.md](DATA_SOURCES.md) are kept.
4. **Build the revision history and the latest view.**
   - The revision history (published for every state as GitHub Release assets: a full file, then weekly increments) keeps one row per key per release.
   - The latest view (`<st>_long_latest_<year>.csv`, one file per year of `observation_week`) keeps, for each key, the row from the release with the latest `as_of_date`. When two releases share a date, the NHSN/NSSP `standard` release is preferred over the `preliminary` one. This is a documented tie-break, not a claim that the standard release is final. Each row cites (`source_snapshot_id`, `as_of_date`) the earliest release since which every release carrying the key has published the same value and flags, so a row of the latest view changes only when its content does.
5. **Assign reliability flags** (section 3).
6. **Reshape to wide tables.**
   - `<st>_nhsn_wide.csv`, `<st>_nssp_wide.csv`, `<st>_nwss_wide.csv`: one row per region and week.
   - `<st>_all_sources_wide.csv`: one row per week. The state-level NHSN and NSSP columns, each HSA's NSSP columns, each wastewater site's columns, and the state Census variables are placed side by side.
   - No values are aggregated, averaged, interpolated, or imputed.
7. **Join Census context** at the state level only.
8. **Check and package.** Each state's quality report confirms:
   - Unique keys
   - Cell-by-cell agreement between every wide table and the long table
   - A complete weekly sequence
   - Agreement between the latest view and the revision history

## 2. Geography

- **State:** identified by its two-digit FIPS code.
- **Health service area (HSA):** the sub-state unit in which CDC publishes NSSP data. It is a multi-county region, and every member county shares one value, so HSA values are not independent county measurements. Some HSAs appear in the source with no ED values at any time.
- **Wastewater site:** the unit in which CDC publishes wastewater data. A site can serve several counties, and a few serve counties in two states; a site is listed under the state given by the source. Sites are not split, weighted, or reassigned to counties or HSAs in these tables.
- **Census:** state level only. No official correspondence exists between HSAs or wastewater service areas and Census geographies, so no population weighting to those units is attempted.

## 3. Reliability flag rules

Rules are applied per state, in the order below. A later rule only replaces `observed_valid`. It never overrides a more specific flag already assigned.

### 3.1 Base flag (all numeric measures)

| Condition | Flag |
|---|---|
| Value missing | `incidental_missing` |
| Value equals 0 | `observed_zero` |
| Otherwise | `observed_valid` |

### 3.2 NHSN hospital admissions

- **Structural absence.** RSV rows for weeks up to and including 2024-08-03 are `structural_absent` for all three NHSN measures. Hospitals were not required to report RSV before then.
- **Coverage.** `coverage_status` is set as follows:
  - `reduced_participation` (flag `observed_low_coverage`) when `hospital_reporting_count` is below the state threshold.
  - `full_participation` (flag `observed_valid`) otherwise.
  - Blank (flag `incidental_missing`) when the reporting count is missing.
- **Anomaly.** `hospital_admission_count` is flagged `flagged_anomalous` when its absolute relative change from the closest preceding non-missing week (same pathogen) is at least the state threshold. Comparisons against a preceding value of 0 are skipped, since the relative change is undefined.

### 3.3 NSSP emergency department visits

- **Trend label coverage.** `ed_trend_category` is `observed_low_coverage` when CDC's label is `Data Unavailable` or `Limited Data`. Other labels are `observed_valid`.
- **Anomaly.** `ed_visit_percent_smoothed` is flagged `flagged_anomalous` with the same relative-change rule as NHSN, applied within each region and pathogen, using the state's NSSP threshold. The raw (unsmoothed) percent is not anomaly-flagged.
- **Participation.** NSSP publishes no visit-count denominator, so coverage is approximated with CDC's county facility-participation map of 2026-08-06.
  - An HSA is `reduced_participation` (flag `observed_low_coverage`) if at least one member county does not have "recent data in NSSP": either a mix of contributing and non-contributing counties, or no contributing county at all.
  - It is `full_participation` otherwise.
  - This is a single point-in-time assessment, applied to every week.

### 3.4 NWSS wastewater

- **Participation.** For each site and pathogen:
  - coverage ratio = (number of weeks with data on or after the site's WVAL inclusion date) / (number of weeks in the state's data from that inclusion date onward). Both counts cover the same window, so the ratio is at most 1. It is computed within each source release, from that release's data only, so a published release's flags never change.
  - Below the state's pathogen-specific threshold, `participation_status` is `reduced_participation` (flag `observed_low_coverage`); otherwise `full_participation`.
  - Within each source release, one value per site and pathogen, repeated on each of the site's weeks.
- **Category jump.** When `wastewater_activity_category` moves three or more tiers (on the scale Very Low < Low < Moderate < High < Very High; for example Very Low to High) from the site's previous reported week in the same source release, that week's category and activity level are both `flagged_anomalous`. A two-tier threshold would flag about 14% of all site-weeks, mostly ordinary swings around a category boundary and real rises at the start of a season; three tiers flags about 5%.
- **Blended source.** Weeks where the source release reports a blended data source for the site are `flagged_anomalous` for both category and level. These are typically one-off laboratory or pipeline transitions.

## 4. How the thresholds were set

The thresholds are data-derived starting points. They are **not clinically validated**.

1. **South Carolina (reference state).** Fixed values were chosen from South Carolina's own data during the initial single-state build, partly from evidence of how quickly hospitals began reporting RSV and partly by team judgment:
   - fewer than 50 reporting hospitals
   - 100% week-over-week admission change
   - 35% smoothed ED percent change
   - wastewater coverage ratio below 0.75 (COVID-19), 0.76 (influenza), 0.76 (RSV); see below

   The wastewater cutoffs differ by pathogen so that each flags a similar share (about 19-23%) of South Carolina's site-pathogen pairs.
2. **All other states.** Reusing South Carolina's absolute numbers would not work nationwide: a 50-hospital cutoff means something very different in Wyoming and in California. Instead, each rule flags the same **share** of each state's own data that South Carolina's value flags in South Carolina:

   | Rule | South Carolina tail share |
   |---|---|
   | NHSN reporting-hospital count | 10.1% of pathogen-weeks |
   | NHSN admission change | 6.14% of pathogen-weeks |
   | NSSP smoothed change | 10.75% of region-pathogen-weeks |
   | NWSS coverage ratio | 22.6% (COVID-19), 21.4% (influenza), 19.2% (RSV) of site-pathogen pairs |

   Each state's threshold is the value that cuts off that share of its own distribution, computed from the latest release. Applying the method to South Carolina itself gives values close to its fixed ones for hospital admissions and ED visits: 58 vs. 50 hospitals, 99% vs. 100%, and 35%.

   **Wastewater.** The wastewater target shares (22.6%, 21.4%, 19.2%) are the shares originally intended for South Carolina. South Carolina's own wastewater cutoffs are derived with the same percentile method as every other state, which gives 0.75, 0.76, and 0.76.

   **Ties.** Many sites share the same coverage ratio (for example, sites that joined on the same date and missed the same weeks). A site is flagged only when its ratio is strictly below the threshold, so sites tied at the threshold are not flagged. The share actually flagged can therefore fall below the target. In South Carolina, 22.6% of COVID-19, 14.3% of influenza, and 11.5% of RSV site-pathogen pairs are flagged.

The values applied to each state are in `metadata/observation_state_thresholds.csv` and in each state's quality report.

## 5. Known limitations

1. **The flag thresholds are provisional.** They are data-derived and have not been externally or clinically validated. Treat the flags as screening aids, not ground truth.
2. **Coverage flags are static for ED and wastewater.** The NSSP participation status reflects a single August 2026 facility map. The NWSS participation status is one summary per site and pathogen in each source release. Neither describes how coverage changed over time.
3. **Some region IDs repeat across region types.** `analysis_region_id` is unique only together with `analysis_region_type`. In Pennsylvania, the HSA with code `42` and the state FIPS code `42` coexist.
4. **Source coverage varies by state and period.**
   - NSSP data begin in October 2022.
   - The NSSP `combined` series ends in September 2024 in most states.
   - NHSN influenza reporting in most states begins in October 2020.
   - North Dakota has no influenza A or RSV wastewater data. Its COVID-19 wastewater data (2 sites) end on 2023-09-16.
5. **Wastewater activity levels are pathogen-specific indices.** Values are not comparable across pathogens; use the category for comparisons.
6. **Snapshot of source data.** The latest values reflect CDC releases through <!-- auto:latest_releases -->2026-10-16 (NHSN, NWSS) and 2026-10-14 (NSSP)<!-- /auto:latest_releases -->. Later CDC revisions are not included.
