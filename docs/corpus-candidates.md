# A2 corpus candidates (for review)

Compiled 2026-10-22. Word counts are estimates from fetched pages (PDF counts from extracted text). Nothing has been downloaded into the repository yet.

## Reuse terms

- **cdc.gov** ([Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html)): "Most of the information on the CDC and ATSDR websites is not subject to copyright, is in the public domain, and may be freely used or reproduced without obtaining copyright permission." Exceptions: material by contractors, grantees, or third parties, and works of state and local governments. Conditions: attribute the material to CDC, state that the use does not imply CDC endorsement, and do not change its substantive content. Logos may not be used.
- **MMWR** ([About the MMWR Series](https://www.cdc.gov/mmwr/about.html)): "All material in the MMWR Series is in the public domain and may be used and reprinted without special permission; citation as to source, however, is appreciated."
- **data.cdc.gov** dataset metadata: "Public Domain U.S. Government".
- **CDCgov/NWSS** on GitHub: public domain in the US, CC0 worldwide.

How resplens complies: raw files are stored unchanged with their source URL and retrieval date; extracted text is labeled as derived from the source; the README credits CDC and states that the project is not endorsed by CDC.

## Recommended: include (24 documents, about 57,000 words)

| ID | Title | System | Words | Explains |
|---|---|---|---|---|
| nhsn_hrd_dataset | Weekly HRD Metrics by Jurisdiction: description and column dictionary ([ua7e-t2fy](https://data.cdc.gov/Public-Health-Surveillance/Weekly-Hospital-Respiratory-Data-HRD-Metrics-by-Ju/ua7e-t2fy), via metadata API) | NHSN | 11,400 | mandate periods, metric definitions, coverage columns |
| nhsn_hrd_prelim_dataset | Weekly HRD Metrics, preliminary release ([mpgq-jmmr](https://data.cdc.gov/Public-Health-Surveillance/Weekly-Hospital-Respiratory-Data-HRD-Metrics-by-Ju/mpgq-jmmr)) | NHSN | 1,350 | Wednesday preliminary release, revisions |
| nhsn_hrd_hub | [Hospital Respiratory Data](https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html) | NHSN | 600 | reporting requirement |
| nhsn_hrd_methods | [HRD Methodology](https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting/data-methods.html) | NHSN | 5,000 | admission levels, thresholds, validation |
| nhsn_hrd_protocol | [HRD Reporting Protocol](https://www.cdc.gov/nhsn/pdfs/pscmanual/HRD-Protocol-Final.pdf) (PDF, Jan 2026) | NHSN | 6,000 | requirements, definitions, data elements |
| nhsn_hrd_toi | [Table of Instructions, Weekly Reporting 57.101](https://www.cdc.gov/nhsn/pdfs/pscmanual/TOI-HRD-Weekly-Reporting-57.101.pdf) (PDF, Oct 2024) | NHSN | 4,100 | field-by-field definitions |
| nhsn_hrd_qa | [HRD Data Processing and QA Reference Guide](https://www.cdc.gov/nhsn/pdfs/HRD-Data-Processing-QA.pdf) (PDF, May 2025) | NHSN | 2,600 | deduplication, QA, aggregation |
| nhsn_hrd_faq | [HRD Resources and FAQs](https://www.cdc.gov/nhsn/psc/Hospital-Respiratory-Data_Reporting-Resources-and-FAQs.pdf) (slides, Sept 2024) | NHSN | 2,900 | reporting scenarios |
| cms_qso_25_05 | [CMS QSO-25-05](https://www.cms.gov/files/document/qso-25-05-hospitals-cahs.pdf) (PDF, Oct 2024) | NHSN | 2,500 | legal reporting requirement from 2024-11-01 |
| nssp_dataset | NSSP ED Visit Trajectories: description ([rdmq-nq56](https://data.cdc.gov/Public-Health-Surveillance/NSSP-Emergency-Department-Visit-Trajectories-by-St/rdmq-nq56)) | NSSP | 340 | percent of visits, trend classes, "sparse" |
| nssp_companion_guide | [Companion Guide: NSSP ED Data on Respiratory Illness](https://www.cdc.gov/nssp/php/onboarding-resources/companion-guide-ed-data-respiratory-illness.html) (Jan 2026) | NSSP | 800 | inclusion, diagnosis codes, caveats |
| nssp_about | [About NSSP](https://www.cdc.gov/nssp/php/about/index.html) | NSSP | 650 | coverage, data flow |
| seer_hsa | [Health Service Areas](https://seer.cancer.gov/seerstat/variables/countyattribs/hsa.html) (NCI) | NSSP | 290 | HSA definition |
| nwss_wval | [Using the Wastewater Viral Activity Level](https://www.cdc.gov/wastewater/about/wval.html) (Aug 2026) | NWSS | 1,400 | WVAL calculation, Aug 2026 method update |
| nwss_methods | [Wastewater Monitoring Data Methodology](https://www.cdc.gov/wastewater/about/data-methods.html) | NWSS | 800 | data quality, display rules |
| nwss_about_data | [About Wastewater Data](https://www.cdc.gov/wastewater/about-data/index.html) | NWSS | 700 | value and limitations |
| nwss_national | [National Wastewater Data for Respiratory Viruses](https://www.cdc.gov/wastewater/respiratory-viruses/national.html) | NWSS | 600 | aggregation, coverage notes, revisions |
| nwss_dataset | CDC WVAL dataset: description and columns ([atcp-73re](https://data.cdc.gov/Public-Health-Surveillance/CDC-Wastewater-Viral-Activity-Level-for-SARS-CoV-2/atcp-73re)) | NWSS | 400 | column definitions |
| nwss_github | [CDCgov/NWSS README](https://github.com/CDCgov/NWSS) | NWSS | 600 | public datasets, WVAL script |
| mmwr_ww_ed_wi | [MMWR 72(37): wastewater and ED visits, Wisconsin 2022–23](https://www.cdc.gov/mmwr/volumes/72/wr/mm7237a2.htm) | NWSS, NSSP | 1,800 | wastewater lead time over ED visits |
| mmwr_nwss_coe | [MMWR 72(48): NWSS Centers of Excellence](https://www.cdc.gov/mmwr/volumes/72/wr/mm7248a4.htm) | NWSS | 800 | how jurisdictions used wastewater data |
| resp_faq | [Release Notes and FAQs, Respiratory Illnesses Data Channel](https://www.cdc.gov/respiratory-viruses/data/faqs.html) (Oct 2026) | all | 7,000 | change log 2024–2026, cross-system FAQs |
| resp_activity_levels | [Illness Levels Over Time](https://www.cdc.gov/respiratory-viruses/data/activity-levels.html) | NSSP, NWSS | 2,000 | ED activity levels, HSA suppression rules |
| resp_severity | [Hospitalizations and Deaths](https://www.cdc.gov/respiratory-viruses/data/illness-severity.html) | NHSN | 1,900 | rates per 100k, under-80% reporting flag |

Plus Tier 1, the ObsAwareData documentation (about 5,300 words, CC BY 4.0).

## Recommended: exclude

| Document | Reason |
|---|---|
| CSTE-hosted ARI syndrome technical brief | Non-federal host, no visible license |
| EID article on NWSS progress, 2020–2024 | No public-domain statement found on the page; include only after verification |
| Archived NSSP companion guide (2023) | Superseded by the 2026 guide; page shows processing errors |
| MMWR 73(37): influenza A and H5 in wastewater, 2024 | Uses wastewater level categories that predate WVAL; would contradict current documents |
| HRD weekly reporting form 57.101 | OMB approval expired 2026-03-31; covered by the protocol and instructions |
| Respiratory data channel index, NHSN dashboard page, RESP-NET dashboard page | Mostly navigation |
| Further NHSN PDFs (daily instructions, import specs, API FAQs, influenza and RSV guidance, submission slides) | Not fetched yet; add later if questions need them |
