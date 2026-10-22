# ObsAwareData: observation-aware weekly respiratory surveillance data for the 50 US states and DC

Weekly COVID-19, influenza, and RSV surveillance data for all 50 states and the District of Columbia, harmonized from three CDC surveillance systems plus US Census context. It is built for forecasting and nowcasting research, so every value carries a **reliability flag** (`observation_state`) and a pointer back to the exact public source release it came from.

| Source | What it measures | Geography | Weeks covered |
|---|---|---|---|
| NHSN Hospital Respiratory Data | New hospital admissions and number of reporting hospitals | State | <!-- auto:weeks_nhsn -->2020-08-08 to 2026-10-10<!-- /auto:weeks_nhsn --> |
| NSSP Emergency Department Visit Trajectories | Percent of ED visits for each pathogen, CDC trend label | State and CDC health service areas (multi-county regions) | <!-- auto:weeks_nssp -->2022-10-01 to 2026-10-10<!-- /auto:weeks_nssp --> |
| NWSS Wastewater Viral Activity Level | Wastewater viral activity index and category | Individual wastewater sampling sites | <!-- auto:weeks_nwss -->2022-01-01 to 2026-10-10<!-- /auto:weeks_nwss --> |
| Census ACS 5-year 2022 and Population Estimates 2022 | Population and socioeconomic context | State | Static |

Weeks end on Saturday (MMWR week ending date). The latest values reflect the CDC releases available on <!-- auto:latest_releases -->2026-10-16 (NHSN, NWSS) and 2026-10-14 (NSSP)<!-- /auto:latest_releases -->. Details and links for each source are in [DATA_SOURCES.md](DATA_SOURCES.md).

## What makes this dataset different

- **Reliability flags on every value.** Each value is labeled `observed_valid`, `observed_zero`, `observed_low_coverage`, `flagged_anomalous`, `incidental_missing`, or `structural_absent`, so a missing or questionable week is never silently treated as a real zero or a normal reading.
- **Traceable to the source release.** Each row in the long tables records a CDC release that published it (`source_snapshot_id`, `as_of_date`; in the latest-value files, the release that first published its current value); [`metadata/source_snapshots.csv`](metadata/source_snapshots.csv) gives each release's SHA-256 and a link to an unmodified copy of the raw file.
- **Full revision history for every state.** Every published version of every value across <!-- auto:releases_nhsn -->118<!-- /auto:releases_nhsn --> NHSN, <!-- auto:releases_nssp -->54<!-- /auto:releases_nssp --> NSSP, and <!-- auto:releases_nwss -->11<!-- /auto:releases_nwss --> NWSS releases is available for all 50 states and DC. These releases are dated <!-- auto:release_windows -->April 2025 to October 2026 (NHSN), August 2025 to October 2026 (NSSP), and August to October 2026 (NWSS)<!-- /auto:release_windows -->, so you can reconstruct what was known on any date in those windows. In South Carolina, for example, about a quarter of all values were revised after first publication. The revision-history files are large, so they are distributed as [GitHub Release assets](https://github.com/DMA-PRIME/ObsAwareData/releases) rather than in the repository; see [Revision history downloads](#revision-history-downloads).
- **No invented aggregation.** Sub-state regions and wastewater sites keep their own columns; nothing is averaged, weighted, or reallocated across geographies.

## Repository layout

```text
ObsAwareData/
├── README.md                 this file
├── DATA_SOURCES.md           where each input comes from
├── DATA_DICTIONARY.md        every file, column, naming rule, and code value
├── METHODS.md                how the tables were built, flag rules, known limitations
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE                   CC BY 4.0
├── metadata/
│   ├── coverage_summary.csv            one row per state: regions, sites, date ranges
│   ├── observation_state_thresholds.csv  per-state thresholds behind the reliability flags
│   ├── manifest.csv                    SHA-256 checksum of every file under data/
│   ├── source_snapshots.csv            every CDC source release used: SHA-256 and archived copy
│   └── release_assets.csv              download link and SHA-256 of every revision-history file
└── data/
    └── <ST>/                 one folder per state, two-letter postal code (AK ... WY, DC)
        ├── <st>_long_latest_<year>.csv   all sources, long format, latest value per week; one file per year
        ├── <st>_nhsn_wide.csv            hospital admissions, wide format
        ├── <st>_nssp_wide.csv            ED visits, wide format
        ├── <st>_nwss_wide.csv            wastewater, wide format
        ├── <st>_all_sources_wide.csv     one row per week, every source and region side by side
        ├── <st>_census_context.csv       state Census context
        └── <st>_quality_report.md        coverage, flag counts, consistency checks
```

Revision-history files for all 51 jurisdictions are attached to the GitHub Releases: for each state one full file (`<st>_long_all_versions.csv.gz`, up to about 75 MB, about 1 GB for all states) and then, in each later release, a small file with only the newly published source releases; see [Revision history downloads](#revision-history-downloads).

## Which file should I use?

- **To model or plot one state week by week:** `<st>_all_sources_wide.csv`. One row per week, one column per measure and region, with a `_flag` column next to each value.
- **To work with one source:** `<st>_nhsn_wide.csv`, `<st>_nssp_wide.csv`, or `<st>_nwss_wide.csv`. One row per region (or site) and week.
- **To filter, join, or stack states programmatically:** `<st>_long_latest_<year>.csv`, one file per year of `observation_week`. One row per measurement, with full provenance. All states and years share the same columns, so the files can be concatenated directly.
- **To study data revisions or run a real-time backtest:** the revision history, downloaded from the releases (see below).

## Quick start

Python:

```python
import pandas as pd

wide = pd.read_csv("data/SC/sc_all_sources_wide.csv", parse_dates=["observation_week"])
usable = wide["hospital_admission_count_covid_flag"].isin(["observed_valid", "observed_zero"])
covid_admissions = wide.loc[usable, ["observation_week", "hospital_admission_count_covid"]]

# the long table: one file per year
import glob
long = pd.concat((pd.read_csv(p, dtype=str, keep_default_na=False)
                  for p in sorted(glob.glob("data/SC/sc_long_latest_*.csv"))), ignore_index=True)
```

R:

```r
library(readr)
wide <- read_csv("data/SC/sc_all_sources_wide.csv")
long <- read_csv(Sys.glob("data/SC/sc_long_latest_*.csv"), col_types = cols(.default = col_character()))
```

## Revision history downloads

A state's revision history is split across releases: one full file (`kind` = `full`, `<st>_long_all_versions.csv.gz`) followed by one increment per later release (`kind` = `increment`, `<st>_long_all_versions_added_<as-of date>.csv.gz`) holding only the source releases first published in it. `metadata/release_assets.csv` lists every file of every state in order, with its download link, size, and SHA-256. Concatenating a state's files in that order gives the complete table; each source release appears in exactly one file.

In Python:

```python
import hashlib, urllib.request
import pandas as pd

assets = pd.read_csv("metadata/release_assets.csv")
parts = []
for a in assets[assets.state == "TX"].itertuples():  # in order: the full file, then increments
    urllib.request.urlretrieve(a.url, a.file)
    assert hashlib.sha256(open(a.file, "rb").read()).hexdigest() == a.sha256
    # keep_default_na=False keeps category labels as text
    parts.append(pd.read_csv(a.file, dtype=str, keep_default_na=False))
history = pd.concat(parts, ignore_index=True)
```

With the [GitHub CLI](https://cli.github.com/), download each listed file from its release, for example `gh release download "<tag>" --repo DMA-PRIME/ObsAwareData --pattern "tx_long_all_versions*"` for each `tag` of the state's rows.

The larger files expand to several GB in memory when read as text. Read them in chunks (`chunksize=` in pandas), or keep only the columns you need (`usecols=`).

## Before any numeric calculation

Two things to handle:

1. **Filter on the flag, not only on the value.** Filter each value on its `_flag` column (or `observation_state` in the long tables). A blank value with `incidental_missing` is a gap, not a zero.
2. **Drop the Census placeholder code.** A few Census margin-of-error columns hold `-555555555`, the Census Bureau's placeholder for "not applicable". Exclude it from numeric calculations.

## Important caveats

- **Wide tables have no revision history.** They hold only the latest value for each week.
- **ED "regions" are CDC health service areas (HSAs).** These are multi-county units: every county in an HSA shares one reported number.
- **Sites are the only valid geography for wastewater.** A wastewater site can serve several counties, and some serve counties in more than one state.
- **Wastewater activity levels can't be compared across pathogens.** Use `wastewater_activity_category` to compare.
- **The flag thresholds are data-derived, not clinically validated.** See [METHODS.md](METHODS.md) for how they were set, and for the known limitations.

## Versioning

Releases are tagged `v<version>+<data date>`, for example `v1.0.0+2026-10-16`:

- **`<version>`** follows [Semantic Versioning](https://semver.org/) and changes only when the rules for building the data change (structure, processing, or flag rules).
- **`<data date>`** is the release date of the most recent CDC source file used. A data refresh under the same rules keeps the version and changes only the date.

To reproduce an analysis, cite or check out the full tag. [CHANGELOG.md](CHANGELOG.md) lists what changed in each release and each source's release date.

## License and citation

The data are released under the [Creative Commons Attribution 4.0 International License](LICENSE) (CC BY 4.0). The underlying CDC and Census data are public; please also acknowledge the original sources listed in [DATA_SOURCES.md](DATA_SOURCES.md). How to cite this dataset: see [CITATION.cff](CITATION.cff).

This dataset contains only aggregated public surveillance data. It contains no individual-level or protected health information.
