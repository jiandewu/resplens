# Question set review

Drafted by an LLM from `corpus/text/`; every quote was checked to appear verbatim. For each question, mark **Verdict** as `ok`, `edit: <change>`, or `drop`.
Check that: the answer is correct and complete per the evidence; the question is natural and does not give the answer away; unanswerable questions are truly not answered by the corpus.

## q01 · test · definition

**Q:** Some early RSV hospital admission weeks are marked as absent by design rather than missing. What does that label mean and which weeks does it cover?

**A:** It means the value was not collected in that period by design; currently it applies only to RSV hospital data for weeks up to 2024-08-03, before RSV reporting was required.

**Evidence:** `oad_data_dictionary`: "Not collected in this period by design. Currently only RSV hospital data up to 2024-08-03, before RSV reporting was required."

**Verdict:** edit: Rephrase Q as "How should structural_absent be interpreted, and where is it currently used?"; the current wording gives away the definition.

## q02 · dev · definition

**Q:** In the long tables, what does it mean when a measure's definition status is marked as uncertain instead of confirmed?

**A:** The measure is usable, but either the source documentation leaves part of its definition open or the field is derived by ObsAwareData itself.

**Evidence:** `oad_data_dictionary`: "`observed_definition_uncertain`: usable, but either the source documentation leaves part of the definition open or the field is derived by this dataset."

**Verdict:** ok

## q03 · dev · definition

**Q:** What exactly does the NHSN hospital reporting count measure represent?

**A:** It is the number of hospitals that reported in that week for that pathogen, i.e. the denominator behind the admission count.

**Evidence:** `oad_data_dictionary`: "Number of hospitals that reported that week for that pathogen: the denominator behind the admission count."

**Verdict:** ok

## q04 · test · number_or_date

**Q:** Why does the wastewater anomaly rule require a jump of three category tiers rather than two, in terms of how many site-weeks get flagged?

**A:** A two-tier rule would flag about 14% of all site-weeks, mostly ordinary swings and real season onsets, whereas three tiers flags about 5%.

**Evidence:** `oad_methods`: "A two-tier threshold would flag about 14% of all site-weeks, mostly ordinary swings around a category boundary and real rises at the start of a season; three tiers flags about 5%."

**Note:** Question may name terms that also appear in the evidence (drafting agent's concern).

**Verdict:** edit: Rephrase Q as "Why was the stricter cutoff chosen for the wastewater sudden-change flag?" to avoid copying the distinctive two-tier/three-tier evidence wording.

## q05 · dev · number_or_date

**Q:** Starting from which NHSN release date did the rounding of half-integer values change, and how?

**A:** From the 2026-10-07 release on, the API CSV export rounds values ending in .5 half to even; earlier files rounded them half up.

**Evidence:** `oad_data_sources`: "Releases from 2026-10-07 on are the API's CSV export, which rounds the few NHSN values that end in .5 half to even; earlier files rounded them half up"

**Verdict:** ok

## q06 · dev · multi_passage

**Q:** For a real-time backtest, how do I get the revision history files and rebuild the data as it looked on a past date?

**A:** The full version history is distributed as GitHub Release assets (one full file per state plus later increments); filter it to releases with as_of_date on or before the target date and keep the latest row per key.

**Evidence:** `oad_data_dictionary`: "**Distributed as GitHub Release assets**: one full file per state, then one increment per later release"<br>`oad_data_dictionary`: "filtering `<st>_long_all_versions.csv.gz` to releases with `as_of_date <= D` and keeping the latest per key reconstructs the data as it was available on date `D`."

**Verdict:** ok

## q07 · test · multi_passage

**Q:** Which CDC ED trend labels get the low-coverage flag, and are weeks labeled 'Sparse' or 'No Data' treated the same way?

**A:** Only the CDC labels 'Data Unavailable' and 'Limited Data' are flagged as low coverage; 'Sparse' and 'No Data' are not flagged as low coverage.

**Evidence:** `oad_data_dictionary`: "NSSP trend: CDC label `Data Unavailable` or `Limited Data`."<br>`oad_data_dictionary`: "Note that the ED trend labels `Sparse` and `No Data` are **not** flagged as low coverage"

**Note:** Question may name terms that also appear in the evidence (drafting agent's concern).

**Verdict:** edit: Rephrase Q as "Which CDC ED statuses trigger the low-coverage flag, and do statuses reflecting sparse or absent trend estimates trigger it?" to avoid naming two evidence labels verbatim.

## q08 · test · cross_document

**Q:** When a preliminary and a standard NHSN file come out on the same date, which one feeds the latest values, and does choosing it imply the numbers are final?

**A:** The standard release is preferred over the preliminary one as a documented tie-break, but 'standard' only means the non-preliminary file and does not imply the values are final.

**Evidence:** `oad_methods`: "When two releases share a date, the NHSN/NSSP `standard` release is preferred over the `preliminary` one."<br>`oad_data_sources`: ""Standard" is only a label for the non-preliminary file; it does not mean the values are final."

**Verdict:** ok

## q09 · test · unanswerable

**Q:** Is there a DOI (for example via Zenodo) I can use to cite ObsAwareData in a paper?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok

## q10 · test · unanswerable

**Q:** On which day of the week is a new ObsAwareData data refresh published?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok

## q11 · test · definition

**Q:** In the NHSN weekly jurisdiction dataset, how is the respiratory season field bounded in terms of MMWR weeks?

**A:** A season runs from week 40 of one year through week 39 of the following year.

**Evidence:** `nhsn_hrd_dataset`: "Respiratory virus seasons are defined as the 40th week of a given year to the 39th week of the following year"

**Verdict:** ok

## q12 · test · definition

**Q:** Which influenza viruses count toward the lab-confirmed flu fields that hospitals report to NHSN?

**A:** Influenza A and B, including their subtypes and lineages (e.g., A(H1N1), A(H3N2), B/Victoria, B/Yamagata).

**Evidence:** `nhsn_hrd_protocol`: "For hospital reporting, laboratory-confirmed
influenza is defined as Influenza A and B (this includes their subtypes and lineages [e.g.,
A(H1N1), A(H3N2), B/Victoria, B/Yamagata)]."

**Verdict:** ok

## q13 · test · definition

**Q:** If a hospital's ICU bed field in its NHSN upload shows 9999, how should I interpret that value?

**A:** It is a code meaning 'not applicable' (e.g., the hospital has no ICU beds of that type), not an actual count.

**Evidence:** `nhsn_hrd_faq`: "The value of 9999 should be reported in ICU fields to represent “not applicable.”"

**Verdict:** edit: Remove the unsupported example from A; use "It is a code meaning not applicable, not an actual count."

## q14 · test · definition

**Q:** When a hospital counts its pediatric inpatient beds for the weekly NHSN form, are neonatal and newborn beds part of that total?

**A:** Yes. The pediatric bed count includes PICU, NICU, newborn nursery beds, and pediatric med-surg beds, occupied or not.

**Evidence:** `nhsn_hrd_toi`: "This count includes occupied and unoccupied inpatient
pediatric beds, including PICU, NICU, newborn nursery beds, and med-surg beds"

**Verdict:** ok

## q15 · test · number_or_date

**Q:** Under CDC's Hospital Admissions Level thresholds, what weekly COVID-19 admission rate per 100,000 places South Carolina in the High category?

**A:** Greater than 7.46 and up to 13.15 per 100,000.

**Evidence:** `nhsn_hrd_methods`: "| SC | Up to 2.10 | Greater than 2.10 and up to 3.50 | Greater than 3.50 and up to 7.46 | Greater than 7.46 and up to 13.15 | Greater than 13.15 |"

**Verdict:** edit: Add the table header to Evidence; the isolated SC row does not establish which range is the High column.

## q16 · dev · number_or_date

**Q:** After a hospital receives a CMS letter saying its respiratory data reporting was incomplete, how long does it have to send CDC proof that it actually reported?

**A:** 5 business days.

**Evidence:** `cms_qso_25_05`: "A provider may submit evidence
to CDC within 5 business days of receiving an incomplete reporting notification letter."

**Verdict:** ok

## q17 · dev · number_or_date

**Q:** How many data elements does the NHSN hospital respiratory module collect in total, and how many of them are mandatory?

**A:** 58 data elements, of which 48 are required and 10 are optional.

**Evidence:** `nhsn_hrd_protocol`: "The NHSN HRD module collects 58 data elements, 48 of which are required to be reported and 10 of
which are optional."

**Verdict:** ok

## q18 · test · multi_passage

**Q:** If a hospital submits admissions day by day instead of as weekly totals, how does NHSN produce the weekly number, and what happens when some days are incomplete?

**A:** NHSN sums the daily values over the Sunday-Saturday week to get the weekly admissions totals, but daily data are carried over to the weekly series only if all required fields were complete for every day; otherwise they are not carried over.

**Evidence:** `nhsn_hrd_qa`: "while weekly aggregate totals will be calculated for the 21 New Admissions data elements by summing the
values reported each day of the reporting week."<br>`nhsn_hrd_qa`: "Data reported to the Daily HRD pathway will only be carried over to the Weekly HRD pathway if complete
data were reported for all required fields each day in the reporting period"

**Verdict:** edit: Remove "over the Sunday-Saturday week" from A because the cited evidence only says "reporting week."

## q19 · test · multi_passage

**Q:** What post-submission check does NHSN use to catch hospitals reporting more occupied inpatient beds than they have, and is the rule different for small hospitals?

**A:** For hospitals with more than 20 inpatient beds, data fail if occupied beds divided by total beds exceeds 1.1; for hospitals with 20 or fewer beds, they fail if occupied beds exceed total beds by more than 2.

**Evidence:** `nhsn_hrd_qa`: "numInPtBeds is > 20 AND
(numInPtBedsOcc/numInPtBeds) > 1.1
numInPtBeds <= 20 AND"<br>`nhsn_hrd_qa`: "numInPtBedsOcc – numInPtBeds > 2"

**Note:** Evidence is formula text from a PDF table; reads unnaturally.

**Verdict:** ok

## q20 · test · multi_passage

**Q:** On CDC's chart of NHSN hospitalization rates, what does a hollow marker signal, and which hospitals form the denominator of the reporting percentage behind it?

**A:** An open circle means fewer than 80% of hospitals in that area reported; the percentage is computed against all hospitals that have reported to NHSN Hospital Respiratory Data since it began in November 2024 (excluding the excluded hospital types).

**Evidence:** `resp_severity`: "Open circles indicate fewer than 80% of hospitals in that area have reported illness numbers."<br>`resp_severity`: "out of all hospitals that have reported to the system since the implementation of NHSN Hospital Respiratory Data in November 2024 (excluding the types listed above)"

**Verdict:** ok

## q21 · dev · cross_document

**Q:** Which day of the week does the preliminary state-level NHSN hospital respiratory file refresh, and when are the finalized aggregate numbers published?

**A:** The preliminary dataset updates on Wednesdays; the final aggregate data are published every Friday afternoon.

**Evidence:** `nhsn_hrd_prelim_dataset`: "This dataset updates weekly on Wednesdays with preliminary data reported to NHSN for the previous reporting week (Sunday – Saturday)."<br>`nhsn_hrd_qa`: "These aggregate data are published to
data.cdc.gov and CDC’s NHSN HRD website every Friday afternoon."

**Verdict:** edit: Add the nhsn_hrd_prelim_dataset sentence stating that the Friday data are considered final; the current second quote establishes publication timing but not finality.

## q22 · test · cross_document

**Q:** Psychiatric and rehab hospitals are left out of CDC's NHSN admission rate calculations. Do they still have to report respiratory data, and how often?

**A:** They are excluded from the rate calculations, but they still must report once a year, in January, covering a single week.

**Evidence:** `resp_severity`: "Psychiatric, rehabilitation, and religious non-medical hospital types are excluded from calculations."<br>`cms_qso_25_05`: "Rehabilitation Hospital Distinct Part Units will report once, annually, in January and only include the
data for the previous week."

**Note:** Same sentence also appears in nhsn_hrd_dataset and nhsn_hrd_prelim_dataset; any of them counts.

**Verdict:** edit: Replace the second Evidence quote with the full sentence covering Psychiatric Hospitals, Rehabilitation Hospitals, and both distinct-part-unit types; the current quote supports only rehabilitation DPUs.

## q23 · dev · unanswerable

**Q:** How many hospitals received CMS's initial warning letter for incomplete NHSN respiratory reporting after the first 28-day period in November 2024?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok

## q24 · test · unanswerable

**Q:** On average, by how much do state-level weekly flu admission counts change between the preliminary NHSN release and the final release?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok

## q25 · test · definition

**Q:** In CDC's sub-state ED trajectory data, under what condition is an HSA's week labeled as rising?

**A:** When the 95% confidence interval for the estimated slope excludes 0 and the slope estimate is positive.

**Evidence:** `nssp_dataset`: "Weeks with a 95% confidence interval not containing 0 are classified as increasing if the slope estimate is positive and decreasing if the slope estimate is negative."

**Verdict:** ok

## q26 · test · definition

**Q:** How does the NCI-modified Health Service Area variable in SEER differ from the original HSA definitions?

**A:** HSAs that crossed state or SEER registry boundaries were split, so every HSA's counties lie within a single state and/or SEER registry.

**Evidence:** `seer_hsa`: "It was modified so that any HSAs that crossed state or SEER Registry boundaries were split so that all counties from one HSA were in one state and/or SEER Registry."

**Verdict:** ok

## q27 · dev · definition

**Q:** How is a wastewater site's WVAL computed from its current viral concentration?

**A:** Current virus level minus the site's baseline (typical low level), divided by the standard deviation.

**Evidence:** `nwss_wval`: "To calculate the WVAL, determine the difference between the current amount of virus and the baseline level, then divide that value by the standard deviation."

**Verdict:** edit: Remove the unsupported parenthetical "typical low level" from A; the cited sentence only says "baseline level."

## q28 · test · definition

**Q:** What does the site field in the NWSS WVAL dataset actually encode?

**A:** An arbitrary, anonymous integer ID that uniquely identifies a wastewater treatment plant.

**Evidence:** `nwss_dataset`: "This is an arbitrary integer used to provide a unique, but anonymous identifier for a wastewater treatment plant."

**Verdict:** ok

## q29 · dev · definition

**Q:** For the NSSP pathogen-specific ED percentages, what is used as the denominator?

**A:** All emergency department visits in the same age group.

**Evidence:** `nssp_companion_guide`: "each respiratory illness is presented as a percent of all emergency department visits by age group."

**Verdict:** ok

## q30 · test · number_or_date

**Q:** Roughly what share of U.S. emergency departments contribute data to NSSP?

**A:** 85%.

**Evidence:** `nssp_about`: "85% of U.S. emergency departments send data to NSSP, often within 24 hours."

**Verdict:** ok

## q31 · test · number_or_date

**Q:** What is the smallest sewershed population for which CDC will publicly display wastewater data without local jurisdiction approval?

**A:** 3,000 people; data from sewersheds serving fewer than 3,000 people are not publicly displayed unless the jurisdiction approves.

**Evidence:** `nwss_methods`: "Data from sewersheds that serve fewer than 3,000 people"

**Verdict:** edit: Expand Evidence to the complete sentence stating that such data are not publicly displayed unless approved locally; the current fragment alone does not support the answer.

## q32 · test · number_or_date

**Q:** According to the 2023 MMWR on the NWSS Centers of Excellence, how many U.S. jurisdictions had wastewater surveillance, and how many did it start from?

**A:** It grew from 20 to 53 jurisdictions.

**Evidence:** `mmwr_nwss_coe`: "surveillance has expanded from 20 to 53 jurisdictions across the United States"

**Verdict:** ok

## q33 · dev · multi_passage

**Q:** Under the current CDC method, the national WVAL is the median of what, and what was it the median of before the change?

**A:** Since August 2026 it is the median of jurisdictional (state/territory) WVALs; previously it was the median of regional WVALs.

**Evidence:** `nwss_wval`: "Previously, the national WVAL was calculated as the median of the regional WVALs."<br>`nwss_wval`: "As of August 2026, the national WVAL is calculated as the median of the jurisdictional WVALs."

**Note:** nwss_national.md states an older rule; checks that retrieval prefers the Aug 2026 method update.

**Verdict:** ok

## q34 · dev · multi_passage

**Q:** For a brand-new wastewater site testing for COVID-19, what baseline is used at first, and when do its values start counting toward state or national medians?

**A:** For the first 182 days it uses a baseline and standard deviation computed from all data at its testing laboratory; it enters aggregate medians once at least 8 weeks of samples have been reported.

**Evidence:** `nwss_wval`: "As of August 2026, new sites use a baseline and standard deviation calculated from all data at their testing laboratory for the first 182 days (COVID-19) or 365 days (influenza A and RSV)."<br>`nwss_wval`: "included in national, regional, state, or territorial median values once there are at least 8 weeks of samples reported for that location."

**Verdict:** ok

## q35 · test · multi_passage

**Q:** In the Wisconsin 2022-23 study, how long did influenza and RSV wastewater signals outlast the drop in ED visits, and how did the authors explain it?

**A:** Up to about 3 months; they attributed it to asymptomatic and mild infections outside the peak and possibly prolonged viral shedding.

**Evidence:** `mmwr_ww_ed_wi`: "persisted beyond declines in associated ED visits for up to 3 months."<br>`mmwr_ww_ed_wi`: "likely reflects asymptomatic and mild illness outside the outbreak’s peak, as well as possible prolonged viral shedding"

**Verdict:** ok

## q36 · test · cross_document

**Q:** Why might RSV levels in sewage diverge from RSV emergency department visit trends?

**A:** Waste from diapered young children does not reach the sewer system, yet RSV's severe ED burden is concentrated in infants and young children (and older adults), so wastewater under-represents a key RSV population.

**Evidence:** `resp_faq`: "This likely explains why trends in wastewater data for RSV do not always align with emergency department visits for RSV, which causes severe disease primarily in infants under 6 months and older adults."<br>`mmwr_ww_ed_wi`: "wastewater surveillance would likely fail to collect data from diapered children, that might be important in surveillance for RSV, which predominates among young children."

**Verdict:** ok

## q37 · dev · cross_document

**Q:** What geographic unit underlies NSSP's sub-state ED trends, and how many of these units exist nationally?

**A:** Health Service Areas (one or more counties grouped by care-seeking patterns); there are 949 HSAs.

**Evidence:** `nssp_dataset`: "Health Service Areas are regions of one or more counties that align to patterns of care seeking."<br>`resp_activity_levels`: "There are 949 HSAs."

**Verdict:** ok

## q38 · dev · cross_document

**Q:** On which weekday are the NSSP ED trajectory dataset and the NWSS WVAL dataset refreshed?

**A:** Both are updated weekly on Fridays.

**Evidence:** `nssp_dataset`: "Updated once per week on Fridays."<br>`nwss_dataset`: "This dataset is updated weekly on Fridays."

**Verdict:** ok

## q39 · dev · unanswerable

**Q:** Before computing WVAL, does CDC normalize wastewater viral concentrations by flow rate or by a fecal marker such as PMMoV?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok

## q40 · test · unanswerable

**Q:** What minimum percentage of ED records with a discharge diagnosis must a state reach for NSSP to publish its jurisdiction-level data?

**A:** Not stated in the corpus.

**Evidence:** (none)

**Verdict:** ok
