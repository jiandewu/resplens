# Human calibration sheet

For each answer, fill in **correctness** (`correct`, `partial`, or `incorrect`) and **unsupported** (`yes` or `no`). The system that produced each answer and the judge's grade are hidden. Use the same rules as the judge; the source documents are in `corpus/text/` (document IDs as shown with each evidence quote).

Rules given to the judge:

> - correctness: judge the facts the question asks for; details in the reference answer beyond what the question
>   asks are not required.
>   "correct" if the answer gives every fact the question asks for, consistent with the reference answer (wording
>   may differ; extra detail is fine if it does not contradict the reference or evidence).
>   "partial" if it gives some of the asked-for facts correctly but misses others, including saying the documents
>   do not state one part, or hedges where the reference is definite.
>   "incorrect" if an asked-for fact is wrong or contradicts the reference or evidence, or if the answer gives none
>   of the asked-for facts (for example, says the documents do not answer the question at all).
>   Extra details beyond what the question asks never lower correctness; they matter only for unsupported_claims.
> - unsupported_claims: true if the answer states a specific fact (a number, date, rule, procedure, or definition)
>   that is supported by none of the reference answer, the evidence, or the source documents. Restating the
>   question or citing document IDs does not count.
> - abstained: true if the answer says the documents do not answer the question.

## H01

**Question:** When a hospital counts its pediatric inpatient beds for the weekly NHSN form, are neonatal and newborn beds part of that total?

**Reference answer:** Yes. The pediatric bed count includes PICU, NICU, newborn nursery beds, and pediatric med-surg beds, occupied or not.

**Evidence:** `nhsn_hrd_toi`: "This count includes occupied and unoccupied inpatient
pediatric beds, including PICU, NICU, newborn nursery beds, and med-surg beds"

**Answer to grade:** Yes, neonatal and newborn nursery beds are included in the total count of pediatric inpatient beds.

Sources: nhsn_hrd_toi, nhsn_hrd_protocol

**correctness:** correct

**unsupported:** no

## H02

**Question:** Which CDC ED statuses trigger the low-coverage flag, and do statuses reflecting sparse or absent trend estimates trigger it?

**Reference answer:** Only the CDC labels 'Data Unavailable' and 'Limited Data' are flagged as low coverage; 'Sparse' and 'No Data' are not flagged as low coverage.

**Evidence:** `oad_data_dictionary`: "NSSP trend: CDC label `Data Unavailable` or `Limited Data`."<br>`oad_data_dictionary`: "Note that the ED trend labels `Sparse` and `No Data` are **not** flagged as low coverage"

**Answer to grade:** The `observed_low_coverage` flag is triggered when the CDC trend label is `Data Unavailable` or `Limited Data`. Trend labels of `Sparse` and `No Data` do not trigger this flag.

Sources: oad_readme, oad_data_dictionary

**correctness:** correct

**unsupported:** no

## H03

**Question:** Under CDC's Hospital Admissions Level thresholds, what weekly COVID-19 admission rate per 100,000 places South Carolina in the High category?

**Reference answer:** Greater than 7.46 and up to 13.15 per 100,000.

**Evidence:** `nhsn_hrd_methods`: "| COVID-19 | Very Low | Low | Moderate | High | Very High |"<br>`nhsn_hrd_methods`: "| SC | Up to 2.10 | Greater than 2.10 and up to 3.50 | Greater than 3.50 and up to 7.46 | Greater than 7.46 and up to 13.15 | Greater than 13.15 |"

**Answer to grade:** The provided documents do not answer this question.

Sources: nhsn_hrd_methods, oad_methods

**correctness:** incorrect

**unsupported:** no

## H04

**Question:** On which day of the week is a new ObsAwareData data refresh published?

**Reference answer:** Not stated in the corpus.

**Evidence:** (none: unanswerable)

**Answer to grade:** The provided documents do not state on which day of the week a new ObsAwareData data refresh is published.

Sources: oad_readme, oad_data_dictionary, oad_methods, oad_data_sources

**correctness:** correct

**unsupported:** no

## H05

**Question:** When a preliminary and a standard NHSN file come out on the same date, which one feeds the latest values, and does choosing it imply the numbers are final?

**Reference answer:** The standard release is preferred over the preliminary one as a documented tie-break, but 'standard' only means the non-preliminary file and does not imply the values are final.

**Evidence:** `oad_methods`: "When two releases share a date, the NHSN/NSSP `standard` release is preferred over the `preliminary` one."<br>`oad_data_sources`: ""Standard" is only a label for the non-preliminary file; it does not mean the values are final."

**Answer to grade:** When a preliminary and a standard NHSN release share the same date, the standard release is preferred for the latest values. Choosing the standard release does not imply the values are final; it is a documented tie-break.

Sources: oad_readme, oad_data_dictionary, oad_methods

**correctness:** correct

**unsupported:** no

## H06

**Question:** Which CDC ED statuses trigger the low-coverage flag, and do statuses reflecting sparse or absent trend estimates trigger it?

**Reference answer:** Only the CDC labels 'Data Unavailable' and 'Limited Data' are flagged as low coverage; 'Sparse' and 'No Data' are not flagged as low coverage.

**Evidence:** `oad_data_dictionary`: "NSSP trend: CDC label `Data Unavailable` or `Limited Data`."<br>`oad_data_dictionary`: "Note that the ED trend labels `Sparse` and `No Data` are **not** flagged as low coverage"

**Answer to grade:** The low-coverage flag (`observed_low_coverage`) is triggered when the CDC label is `Data Unavailable` or `Limited Data`. Labels for `Sparse` and `No Data` are not flagged as low coverage.

Sources: oad_data_dictionary, oad_methods

**correctness:** correct

**unsupported:** no

## H07

**Question:** In CDC's sub-state ED trajectory data, under what condition is an HSA's week labeled as rising?

**Reference answer:** When the 95% confidence interval for the estimated slope excludes 0 and the slope estimate is positive.

**Evidence:** `nssp_dataset`: "Weeks with a 95% confidence interval not containing 0 are classified as increasing if the slope estimate is positive and decreasing if the slope estimate is negative."

**Answer to grade:** A week is classified as increasing if the 95% confidence interval for the slope approximation does not contain 0 and the slope estimate is positive.

Sources: nssp_dataset

**correctness:** correct

**unsupported:** no

## H08

**Question:** Why might RSV levels in sewage diverge from RSV emergency department visit trends?

**Reference answer:** Waste from diapered young children does not reach the sewer system, yet RSV's severe ED burden is concentrated in infants and young children (and older adults), so wastewater under-represents a key RSV population.

**Evidence:** `resp_faq`: "This likely explains why trends in wastewater data for RSV do not always align with emergency department visits for RSV, which causes severe disease primarily in infants under 6 months and older adults."<br>`mmwr_ww_ed_wi`: "wastewater surveillance would likely fail to collect data from diapered children, that might be important in surveillance for RSV, which predominates among young children."

**Answer to grade:** RSV levels in wastewater may diverge from emergency department visit trends because wastewater data does not include waste disposed of outside the municipal sewage system, such as from people wearing diapers. This is a significant limitation since RSV causes severe disease primarily in infants under 6 months and older adults.

Sources: resp_faq

**correctness:** correct

**unsupported:** no

## H09

**Question:** If a hospital submits admissions day by day instead of as weekly totals, how does NHSN produce the weekly number, and what happens when some days are incomplete?

**Reference answer:** NHSN sums the daily values to get the weekly admissions totals, but daily data are carried over to the weekly series only if all required fields were complete for every day; otherwise they are not carried over.

**Evidence:** `nhsn_hrd_qa`: "while weekly aggregate totals will be calculated for the 21 New Admissions data elements by summing the
values reported each day of the reporting week."<br>`nhsn_hrd_qa`: "Data reported to the Daily HRD pathway will only be carried over to the Weekly HRD pathway if complete
data were reported for all required fields each day in the reporting period"

**Answer to grade:** When a hospital uses the daily reporting pathway, NHSN calculates weekly totals for new admissions by summing the values reported for each day of the reporting week. If data are incomplete for any required field on any day of the reporting period, the data will not be carried over to the weekly pathway.

Sources: nhsn_hrd_qa, nhsn_hrd_protocol

**correctness:** correct

**unsupported:** no

## H10

**Question:** When a preliminary and a standard NHSN file come out on the same date, which one feeds the latest values, and does choosing it imply the numbers are final?

**Reference answer:** The standard release is preferred over the preliminary one as a documented tie-break, but 'standard' only means the non-preliminary file and does not imply the values are final.

**Evidence:** `oad_methods`: "When two releases share a date, the NHSN/NSSP `standard` release is preferred over the `preliminary` one."<br>`oad_data_sources`: ""Standard" is only a label for the non-preliminary file; it does not mean the values are final."

**Answer to grade:** When two releases share the same date, the standard release is preferred over the preliminary one. Choosing the standard release does not imply that the values are final.

Sources: oad_methods, oad_data_sources, oad_data_dictionary

**correctness:** correct

**unsupported:** no

## H11

**Question:** On which day of the week is a new ObsAwareData data refresh published?

**Reference answer:** Not stated in the corpus.

**Evidence:** (none: unanswerable)

**Answer to grade:** The provided documents do not state which day of the week a new data refresh is published; they only specify that weeks end on Saturday.

Sources: oad_readme

**correctness:** correct

**unsupported:** no

## H12

**Question:** According to the 2023 MMWR on the NWSS Centers of Excellence, how many U.S. jurisdictions had wastewater surveillance, and how many did it start from?

**Reference answer:** It grew from 20 to 53 jurisdictions.

**Evidence:** `mmwr_nwss_coe`: "surveillance has expanded from 20 to 53 jurisdictions across the United States"

**Answer to grade:** Wastewater surveillance expanded from 20 to 53 jurisdictions across the United States.

Sources: mmwr_nwss_coe

**correctness:** correct

**unsupported:** no

## H13

**Question:** If a hospital's ICU bed field in its NHSN upload shows 9999, how should I interpret that value?

**Reference answer:** It is a code meaning not applicable, not an actual count.

**Evidence:** `nhsn_hrd_faq`: "The value of 9999 should be reported in ICU fields to represent “not applicable.”"

**Answer to grade:** A value of 9999 in the ICU bed fields of an NHSN upload should be interpreted as "not applicable."

Sources: nhsn_hrd_protocol, nhsn_hrd_faq

**correctness:** correct

**unsupported:** no

## H14

**Question:** When a hospital counts its pediatric inpatient beds for the weekly NHSN form, are neonatal and newborn beds part of that total?

**Reference answer:** Yes. The pediatric bed count includes PICU, NICU, newborn nursery beds, and pediatric med-surg beds, occupied or not.

**Evidence:** `nhsn_hrd_toi`: "This count includes occupied and unoccupied inpatient
pediatric beds, including PICU, NICU, newborn nursery beds, and med-surg beds"

**Answer to grade:** Yes, the count for all pediatric inpatient beds includes NICU and newborn nursery beds.

Sources: nhsn_hrd_toi

**correctness:** correct

**unsupported:** no

## H15

**Question:** Why might RSV levels in sewage diverge from RSV emergency department visit trends?

**Reference answer:** Waste from diapered young children does not reach the sewer system, yet RSV's severe ED burden is concentrated in infants and young children (and older adults), so wastewater under-represents a key RSV population.

**Evidence:** `resp_faq`: "This likely explains why trends in wastewater data for RSV do not always align with emergency department visits for RSV, which causes severe disease primarily in infants under 6 months and older adults."<br>`mmwr_ww_ed_wi`: "wastewater surveillance would likely fail to collect data from diapered children, that might be important in surveillance for RSV, which predominates among young children."

**Answer to grade:** RSV trends in wastewater may not align with emergency department visits because wastewater data does not include waste disposed of outside the system, such as from people wearing diapers. This is significant because RSV primarily causes severe disease in older adults and infants under 6 months.

Sources: resp_faq, mmwr_ww_ed_wi

**correctness:** correct

**unsupported:** no
