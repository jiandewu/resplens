# Data sources

All inputs are public data published by the US Centers for Disease Control and Prevention (CDC) and the US Census Bureau. They were downloaded as the full nationwide files; each state's tables are a filter of those files, not separately obtained data. Every release used is kept unmodified in the public [archive of CDC releases](https://github.com/jiandewu/ObsAwareData-pipeline), with its release date and SHA-256 checksum.

## 1. Hospital admissions: NHSN Hospital Respiratory Data (HRD)

- **Dataset:** Weekly Hospital Respiratory Data (HRD) Metrics by Jurisdiction, National Healthcare Safety Network (NHSN).
- **Publisher:** CDC, National Healthcare Safety Network.
- **Links:**
  - [Main dataset (ua7e-t2fy)](https://data.cdc.gov/Public-Health-Surveillance/Weekly-Hospital-Respiratory-Data-HRD-Metrics-by-Ju/ua7e-t2fy)
  - [Preliminary release (mpgq-jmmr)](https://data.cdc.gov/Public-Health-Surveillance/Weekly-Hospital-Respiratory-Data-HRD-Metrics-by-Ju/mpgq-jmmr)
- **Releases used:** <!-- auto:releases_nhsn -->118<!-- /auto:releases_nhsn --> dated downloads of the full file, the latest dated <!-- auto:newest_nhsn -->2026-10-16<!-- /auto:newest_nhsn -->. Some are the preliminary release and some the main release. `source_snapshot_id` records which release each row came from (`..._preliminary_...` or `..._standard_...`). "Standard" is only a label for the non-preliminary file; it does not mean the values are final. Releases from 2026-10-07 on are the API's CSV export, which rounds the few NHSN values that end in .5 half to even; earlier files rounded them half up, so those values can differ by 1 between the two (no other difference).
- **Fields used:** total new admissions with a confirmed diagnosis (COVID-19, influenza, RSV), and the number of hospitals reporting those admissions. All other HRD fields are excluded: bed occupancy, ICU counts, age breakdowns, rates, and change measures.
- **Geography:** State (jurisdiction). DC is included; territories and national or regional aggregates are excluded.
- **Note:** Hospitals were not required to report RSV admissions before August 2024. RSV hospital data for weeks up to 2024-08-03 are therefore marked `structural_absent`, not missing.

## 2. Emergency department visits: NSSP

- **Dataset:** NSSP Emergency Department Visit Trajectories by State and Sub State Regions - COVID-19, Flu, RSV, Combined.
- **Publisher:** CDC, National Syndromic Surveillance Program (NSSP).
- **Link:** [rdmq-nq56](https://data.cdc.gov/Public-Health-Surveillance/NSSP-Emergency-Department-Visit-Trajectories-by-St/rdmq-nq56)
- **Releases used:** <!-- auto:releases_nssp -->54<!-- /auto:releases_nssp --> dated downloads of the full file, the latest dated <!-- auto:newest_nssp -->2026-10-14<!-- /auto:newest_nssp -->.
- **Fields used:** percent of ED visits (raw and smoothed) for COVID-19, influenza, RSV, and all three combined, plus CDC's trend label for each pathogen.
- **Geography:** State, and CDC health service areas (HSAs) within the state. HSAs are identified by their NCI HSA code. An HSA is a multi-county region; every member county carries the same value. The national row is excluded.
- **Supplementary coverage file:** CDC's NSSP county facility-participation map ([coverage-map.csv](https://www.cdc.gov/nssp/documents/coverage-map.csv)), downloaded on 2026-08-06. It is used only to derive the ED `participation_status` field (see [METHODS.md](METHODS.md)). It is a single point-in-time snapshot, not a weekly history.

## 3. Wastewater: NWSS

- **Dataset:** CDC Wastewater Viral Activity Level for SARS-CoV-2, Influenza A and RSV.
- **Publisher:** CDC, National Wastewater Surveillance System (NWSS).
- **Link:** [atcp-73re](https://data.cdc.gov/Public-Health-Surveillance/CDC-Wastewater-Viral-Activity-Level-for-SARS-CoV-2/atcp-73re)
- **Releases used:** <!-- auto:releases_nwss -->11<!-- /auto:releases_nwss --> dated downloads, the latest dated <!-- auto:newest_nwss -->2026-10-16<!-- /auto:newest_nwss -->.
- **Fields used:**
  - Site-level Wastewater Viral Activity Level (WVAL) and its category
  - The date each site was included in WVAL reporting
  - The reported data source, used only for a quality flag
- **Geography:** Individual wastewater sampling site. The anonymous CDC site identifier is kept as-is (e.g. `ID:113`). A site is assigned to a state by the source's `State/Territory` field. Sites are not reassigned to counties or HSAs in these tables.
- **Note:** North Dakota has no influenza A or RSV wastewater data in the source. Its COVID-19 wastewater series ends on 2023-09-16.

## 4. Census context

- **Datasets:**
  - American Community Survey (ACS) 5-year estimates, 2022 vintage. Data Profile and Subject Table variables, retrieved from the [Census Data API](https://www.census.gov/data/developers/data-sets/acs-5year.html).
  - Population Estimates Program, 2022 state totals ([NST-EST2022-ALLDATA](https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/state/totals/NST-EST2022-ALLDATA.csv)).
- **Publisher:** US Census Bureau.
- **Geography:** State only. No sub-state Census join is made: HSAs have no official Census correspondence, and wastewater service areas are not Census geographies.
- **Variables:** 23 ACS variables (estimates and margins of error), listed with their ACS codes in [DATA_DICTIONARY.md](DATA_DICTIONARY.md#census-variables), plus `POPESTIMATE2022`.

## Terms of use

The CDC and Census source data are public-domain US government works. This derived dataset is released under CC BY 4.0 (see [LICENSE](LICENSE)). When using it, please also acknowledge CDC (NHSN, NSSP, NWSS) and the US Census Bureau as the original data sources. The originating agencies have not reviewed or endorsed this dataset.
