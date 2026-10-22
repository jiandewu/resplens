# HRD Data Processing and Quality Assurance Reference Guide

May 2025

     1
NHSN Hospital Respiratory Data (HRD) Data Processing and
Quality Assurance Reference Guide
Version 1
Updated: May 30, 2025

This guide provides detailed information regarding the processing, deduplication, data quality
assurance, and aggregation steps applied to data submitted to NHSN’s Hospital Respiratory Data (HRD)
Module prior to inclusion in downstream internal and external products, including publication to CDC’s
public-facing webpages and dashboards.
HRD Data Submission Pathways
As of November 1, 2024, all U.S. acute care and critical access hospitals are required to electronically
report weekly information about COVID-19, influenza, respiratory syncytial virus (RSV), and hospital bed
capacity to CDC’s National Healthcare Safety Network (NHSN) in a standardized format and frequency
specified by the HHS Secretary under the Centers for Medicare & Medicaid (CMS) Conditions of
Participation (CoP). These data are submitted to CDC via NHSN Hospital Respiratory Data (HRD) module,
located in the Patient Safety Component (PSC), through either the HRD Daily or the HRD Weekly Pathway.
Users may choose which pathway they would like to use to submit their facility’s data. Additionally, users
may choose to report their facility’s data using either the web form entry, CSV upload, or API direct
upload.
Front-End Specifications & Business Rules
Each reporting pathway and submission method requires certain NHSN front-end specifications be met
when submitting and saving data, including specified data element formats, valid value ranges and
response options, and business rules. Business rules are specified checks applied upon submission that
flag and/or reject illogical data (e.g., reporting a greater number of adult inpatient beds than total
inpatient beds) from being saved. The table below provides the list of data elements for which business
rules are applied.

Business Rules
Data Element
Column Name
ID Business Rule(s)
numInPtBeds 2a Must be >= 2b. numInPtBedsAdult + 2c. numInPtBedsPed Must be >= 3a. numInPtBedsOcc
numInPtBedsAdult 2b Must be <= 2a. numInPtBeds Must be >= 3b. numInPtBedsOccAdult
numInPtBedsPed 2c Must be >= 5a. numICUBedsOcc (where 5a. numICUBedsOcc does not equal 9999) AND Must be >= (3b. numInPtBedsOccAdult + 3c. numInPtBedsOccPed)
numInPtBedsOcc 3a Must be >= 5a. numICUBedsOcc (where 5a. numICUBedsOcc does not equal 9999) AND
Must be >= (3b. numInPtBedsOccAdult + 3c. numInPtBedsOccPed)

May 2025

     2
numInPtBedsOccAdult 3b Must be <= 3a. numInPtBedsOcc AND
Must be >= 5b. numICUBedsOccAdult (where 5b. numICUBedsOccAdult does not equal
9999)
numInPtBedsOccPed 3c Must be <= 3a. numInPtBedsOcc AND
Must be >= 5c. numICUBedsOccPed (where 5c. numICUBedsOccPed does not equal
9999)
numICUBeds 4a If not equal to 9999:
Must be <= 2a. numInPtBeds AND
Must be >= 4b. numICUBedsAdult (where 4b. numICUBedsAdult does NOT equal 9999) +
4c. numICUBedsPed (where 4c. numICUBedsPed does NOT equal 9999)]) AND
Must be >= 5a. numICUBedsOcc
numICUBedsAdult 4b Must be 9999 if 4a. numICUBeds equals 9999
If not equal to 9999:
Must be <= 4a. numICUBeds AND
Must be >= 5b. numICUBedsOccAdult
numICUBedsPed 4c Must be 9999 if 4a. numICUBeds equals 9999
If not equal to 9999:
Must be <= 4a. numICUBeds AND
Must be >= 5c. numICUBedsOccPed
numICUBedsOcc 5a Must be 9999 if 4a. numICUBeds equals 9999
If not equal to 9999:
Must be <= 3a. numInPtBedsOcc AND
Must be >= 5b. numICUBedsOccAdult (where 5b. numICUBedsOccAdult does NOT equal
9999) + 5c. numICUBedsOccPed (where 5c. numICUBedsOccPed does NOT equal 9999)
numICUBedsOccAdult 5b Must be 9999 if 4a. numICUBeds equals 9999 OR if 4b. numICUBedsAdult equals 9999
If not equal to 9999:
Must be <= 5a. numICUBedsOcc
numICUBedsOccPed 5c Must be 9999 if 4a. numICUBeds equals 9999 OR if 4c. numICUBedsPed equals 9999
If not equal to 9999:
Must be <= 5a. numICUBedsOcc
numConfC19ICUPatsAdult 9a Must be <= 6a. numConfC19HospPatsAdult
numConfC19ICUPatsPed 9b Must be <= 6b. numConfC19HospPatsPed
numConfFluICUPatsAdult 10a Must be <= 7a. numConfFluHospPatsAdult
numConfFluICUPatsPed 10b Must be <= 7b. numConfFluHospPatsPed
numConfRSVICUPatsAdult 11a Must be <= 8a. numConfRSVHospPatsAdult
numConfRSVICUPatsPed 11b Must be <= 8b. numConfRSVHospPatsPed

When a user attempts to submit a record that fails one or more of these business rules, the submission
will be rejected, and the user will receive a notification of the error. When submitting data via the web
form, this notification will appear as a pop-up message with errors listed. When submitting data via CSV
upload, this notification will appear as both a pop-up message and notification of errors will be sent to the
email address associated with the submitting user’s NHSN account. When submitting data via API upload,
notification of errors will be sent to the email address associated with the System Account in SAMS. All
errors must be fixed before the record can be successfully submitted and saved. Examples of these error
notifications are provided below.

May 2025

     3
Web Form


 CSV Upload


CSV Upload and API Submission – Email Notification

May 2025

     4
For a full list of data upload and reporting specifications, please review the HRD Daily and Weekly
Reporting Tables of Instructions and Import File Specifications documentation found here, under Data
Collection Forms and Instructions: https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html,
along with the full HRD Protocol.
As such, the sections that follow in this reference guide outline
additional data processing steps that are performed and applied after
data are successfully submitted to the HRD Daily or Weekly
Pathways, meaning all reporting specifications and business rules
have been met.
Deduplication of Records
While NHSN users can upload more than one record for a single facility for a specific date (HRD Daily
Pathway) or reporting week (HRD Weekly Pathway), our downstream timeseries datasets used for
reporting and analytics only include one record per facility per reporting week (or date).
Therefore, our data processing includes a de-deduplication step within each reporting pathway where a
single record is chosen based on the completeness of the record for CMS enforcement purposes. If more
than one record is considered equal based on these criteria, then the record submitted most recently will
be retained.
Logic Checks
Suppression is applied to the deduplicated data in both the Daily and Weekly data pipelines for values
that fail specified logic checks for priority data elements. While many of these checks are addressed at
submission through the applied business rules described above, this step ensures any  logically
implausible data are removed from final aggregate metrics used for reporting, analytics, and public
dissemination. The tables below provide the list of logic checks applied to both the Daily and Weekly data
pipelines:

Daily Pathway Logic Checks
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
Inpatient
Beds
numInPtBeds
numInPtBedsAdult
numInPtBedsPed
numInPtBedsOcc
numInPtBedsOccAdult
numInPtBedsOccPed
numConfFluHospPatsAdult
numConfFluHospPatsPed
(numInPtBedsAdult + numInPtBedsPed) > numInPtBeds
(numInPtBedsOccAdult + numInPtBedsOccPed) > numInPtBedsOcc
(numConfC19HospPatsAdult + numConfC19HospPatsPed) > numInPtBedsOcc
(numConfFluHospPatsAdult + numConfFluHospPatsPed) > numInPtBedsOcc
(numConfRSVHospPatsAdult + numConfRSVHospPatsPed) > numInPtBedsOcc
numInPtBeds is > 20 AND
(numInPtBedsOcc/numInPtBeds) > 1.1
numInPtBeds <= 20 AND

May 2025

     5
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
numConfC19HospPatsAdult
numConfC19HospPatsPed
numConfRSVHospPatsAdult
numConfRSVHospPatsPed
numInPtBedsOcc – numInPtBeds > 2
(numConfC19HospPatsAdult is null AND numConfC19HospPatsPed is null) OR
(numConfFluHospPatsAdult is null AND numConfFluHospPatsPed is null) OR
(numConfRSVHospPatsAdult is null AND numConfRSVHospPatsPed is null) OR
numInPtBeds is null OR
numInPtBedsOcc is null
ICU Beds numICUBeds
numICUBedsAdult
numICUBedsPed
numICUBedsOcc
numICUBedsOccAdult
numICUBedsOccPed
numConfC19ICUPatsAdult
numConfC19ICUPatsPed
numConfFluICUPatsAdult
numConfFluICUPatsPed
numConfRSVICUPatsAdult
numConfRSVICUPatsPed
(numICUBedsAdult + numICUBedsPed) > numICUBeds
(numICUBedsOccAdult + numICUBedsOccPed) > numICUBedsOcc
(numConfC19ICUPatsAdult + numConfC19ICUPatsPed) > numICUBedsOcc
(numConfFluICUPatsAdult + numConfFluICUPatsPed) > numICUBedsOcc
(numConfRSVICUPatsAdult + numConfRSVICUPatsPed) > numICUBedsOcc
numICUBeds is > 20 AND
(numICUBedsOcc/numICUBeds) > 1.1
numICUBeds <= 20 AND
numICUBedsOcc – numICUBeds > 2
(numConfC19ICUPatsAdult is null AND numConfC19ICUPatsPed is null) OR
(numConfFluICUPatsAdult is null AND numConfFluICUPatsPed is null) OR
(numConfRSVICUPatsAdult is null AND numConfRSVICUPatsPed is null) OR
numICUBeds is null OR
numICUBedsOcc is null
COVID-19
Pediatric
Admissions
and
Hospitalized
Patients
numConfC19HospPatsPed
numConfC19NewAdmPed0to4
numConfC19NewAdmPed5to17

(If numConfC19NewAdmPed0to4 OR
numConfC19NewAdmPed5to17 is not null) AND
(numConfC19HospPatsPed is not null)
AND
(numConfC19HospPatsPed > 20 AND
(numConfC19NewAdmPed0to4 + numConfC19NewAdmPed5to17)
/numConfC19HospPatsPed >1.1)
(If numConfC19NewAdmPed0to4 OR numConfC19NewAdmPed5to17 is not
null) AND (numConfC19HospPatsPed is not null)
AND
(numConfC19HospPatsPed <= 20 AND
(numConfC19NewAdmPed0to4 + numConfC19NewAdmPed5to17) -
numConfC19HospPatsPed > 2)
COVID-19
Adult
Admissions
and
Hospitalized
Patients
numConfC19HospPatsAdult
numConfC19NewAdmAdult18to49
numConfC19NewAdmAdult50to64
numConfC19NewAdmAdult65to74
numConfC19NewAdmAdult75plus
(IF numConfC19NewAdmAdult18to49 OR
numConfC19NewAdmAdult50to64 OR
numConfC19NewAdmAdult65to74 OR
numConfC19NewAdmAdult75plus is not null) AND
(numConfC19HospPatsAdult is not null)
AND
(numConfC19HospPatsAdult > 20 AND
(numConfC19NewAdmAdult18to49 +numConfC19NewAdmAdult50to64 +
numConfC19NewAdmAdult65to74 + numConfC19NewAdmAdult75plus)
/numConfC19HospPatsAdult >1.1)
(IF numConfC19NewAdmAdult18to49 is not null OR
numConfC19NewAdmAdult50to64 is not null OR
numConfC19NewAdmAdult65to74 is not null OR

May 2025

     6
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
numConfC19NewAdmAdult75plus is not null) AND
numConfC19HospPatsAdult is not null)
AND
(numConfC19HospPatsAdult <= 20 AND
(numConfC19NewAdmAdult18to49 +numConfC19NewAdmAdult50to64 +
numConfC19NewAdmAdult65to74 +numConfC19NewAdmAdult75plus) -
numConfC19HospPatsAdult > 2)
Flu Pediatric
Admissions
and
Hospitalized
Patients
numConfFluHospPatsPed
numConfFluNewAdmPed0to4
numConfFluNewAdmPed5to17
(IF numConfFluNewAdmPed0to4 is not null OR
numConfFluNewAdmPed5to17 is not null) AND
(numConfFluHospPatsPed is not null)
AND
(numConfFluHospPatsPed > 20 and
(numConfFluNewAdmPed0to4 + numConfFluNewAdmPed5to17)
/numConfFluHospPatsPed >1.1)
(IF numConfFluNewAdmPed0to4 is not null OR
numConfFluNewAdmPed5to17 is not null) AND
(numConfFluHospPatsPed is not null)
AND
(numConfFluHospPatsPed <= 20 AND
(numConfFluNewAdmPed0to4 + numConfFluNewAdmPed5to17) -
numConfFluHospPatsPed > 2)
Flu Adult
Admissions
and
Hospitalized
Patients
numConfFluHospPatsAdult
numConfFluNewAdmAdult18to49
numConfFluNewAdmAdult50to64
numConfFluNewAdmAdult65to74
numConfFluNewAdmAdult75plus
(IF numConfFluNewAdmAdult18to49 is not null OR
numConfFluNewAdmAdult50to64 is not null OR
numConfFluNewAdmAdult65to74 is not null OR
numConfFluNewAdmAdult75plus is not null) AND
(numConfFluHospPatsAdult is not null)

AND

(numConfFluHospPatsAdult > 20 AND
(numConfFluNewAdmAdult18to49 + numConfFluNewAdmAdult50to64 +
numConfFluNewAdmAdult65to74 +  numConfFluNewAdmAdult75plus)
/numConfFluHospPatsAdult >1.1)
(IF numConfFluNewAdmAdult18to49  is not null OR
numConfFluNewAdmAdult50to64 is not null  OR
numConfFluNewAdmAdult65to74 is not null OR
numConfFluNewAdmAdult75plus is not null) AND
(numConfFluHospPatsAdult is not null)
AND
(numConfFluHospPatsAdult <= 20 AND
(numConfFluNewAdmAdult18to49 + numConfFluNewAdmAdult50to64 +
numConfFluNewAdmAdult65to74 + numConfFluNewAdmAdult75plus) -
numConfFluHospPatsAdult > 2)
RSV Pediatric
Admissions
and
numConfRSVHospPatsPed
numConfRSVNewAdmPed0to4
numConfRSVNewAdmPed5to17
(IF numConfRSVNewAdmPed0to4 is not null OR
numConfRSVNewAdmPed5to17 is not null) AND
(numConfRSVHospPatsPed is not null)

May 2025

     7
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
Hospitalized
Patients
AND
(numConfRSVHospPatsPed > 20 AND
(numConfRSVNewAdmPed0to4 + numConfRSVNewAdmPed5to17)
/numConfRSVHospPatsPed >1.1)
(IF numConfRSVNewAdmPed0to4 is not null OR
numConfRSVNewAdmPed5to17 is not null) AND
(numConfRSVHospPatsPed is not null)
AND
(numConfRSVHospPatsPed <= 20 AND
(numConfRSVNewAdmPed0to4 + numConfRSVNewAdmPed5to17) -
numConfRSVHospPatsPed > 2)
RSV Adult
Admissions
and
Hospitalized
Patients
numConfRSVHospPatsAdult
numConfRSVNewAdmAdult18to49
numConfRSVNewAdmAdult50to64
numConfRSVNewAdmAdult65to74
numConfRSVNewAdmAdult75plus
(IF numConfRSVNewAdmAdult18to49 is not null  OR
numConfRSVNewAdmAdult50to64 is not null OR
numConfRSVNewAdmAdult65to74 is not null OR
numConfRSVNewAdmAdult75plus is not null) AND
(numConfRSVHospPatsAdult is not null)
AND
(numConfRSVHospPatsAdult > 20 and
(numConfRSVNewAdmAdult18to49 + numConfRSVNewAdmAdult50to64 +
numConfRSVNewAdmAdult65to74 + numConfRSVNewAdmAdult75plus)
/numConfRSVHospPatsAdult >1.1)
(IF numConfRSVNewAdmAdult18to49 is not null OR
numConfRSVNewAdmAdult50to64 is not null OR
numConfRSVNewAdmAdult65to74 is not null OR
numConfRSVNewAdmAdult75plus is not null) AND
(numConfRSVHospPatsAdult is not null)
AND
(numConfRSVHospPatsAdult <= 20 AND
(numConfRSVNewAdmAdult18to49 +numConfRSVNewAdmAdult50to64 +
numConfRSVNewAdmAdult65to74 +numConfRSVNewAdmAdult75plus) -
numConfRSVHospPatsAdult > 2)


Weekly Pathway Logic Checks
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
Inpatient
Beds
numInPtBeds
numInPtBedsAdult
numInPtBedsPed
numInPtBedsOcc
numInPtBedsOccAdult
numInPtBedsOccPed
numConfFluHospPatsAdult
numConfFluHospPatsPed
(numInPtBedsAdult + numInPtBedsPed) > numInPtBeds
(numInPtBedsOccAdult + numInPtBedsOccPed) > numInPtBedsOcc
(numConfC19HospPatsAdult + numConfC19HospPatsPed) > numInPtBedsOcc
(numConfFluHospPatsAdult + numConfFluHospPatsPed) > numInPtBedsOcc
(numConfRSVHospPatsAdult + numConfRSVHospPatsPed) > numInPtBedsOcc
numInPtBeds is > 20 AND
(numInPtBedsOcc/numInPtBeds) > 1.1
numInPtBeds <= 20 AND

May 2025

     8
Logic
Check
Type
Impacted Fields
(The fields listed will be converted to null if
ANY of the logic check conditions in the
column on the right are met) Data Quality Checks
numConfC19HospPatsAdult
numConfC19HospPatsPed
numConfRSVHospPatsAdult
numConfRSVHospPatsPed
numInPtBedsOcc – numInPtBeds > 2
(numConfC19HospPatsAdult is null AND numConfC19HospPatsPed is null) OR
(numConfFluHospPatsAdult is null AND numConfFluHospPatsPed is null) OR
(numConfRSVHospPatsAdult is null AND numConfRSVHospPatsPed is null) OR
numInPtBeds is null OR
numInPtBedsOcc is null
ICU Beds numICUBeds
numICUBedsAdult
numICUBedsPed
numICUBedsOcc
numICUBedsOccAdult
numICUBedsOccPed
numConfC19ICUPatsAdult
numConfC19ICUPatsPed
numConfFluICUPatsAdult
numConfFluICUPatsPed
numConfRSVICUPatsAdult
numConfRSVICUPatsPed
(numICUBedsAdult + numICUBedsPed) > numICUBeds
(numICUBedsOccAdult + numICUBedsOccPed) > numICUBedsOcc
(numConfC19ICUPatsAdult + numConfC19ICUPatsPed) > numICUBedsOcc
(numConfFluICUPatsAdult + numConfFluICUPatsPed) > numICUBedsOcc
(numConfRSVICUPatsAdult + numConfRSVICUPatsPed) > numICUBedsOcc
numICUBeds is > 20 AND
(numICUBedsOcc/numICUBeds) > 1.1
numICUBeds <= 20 AND
numICUBedsOcc – numICUBeds > 2
(numConfC19ICUPatsAdult is null AND numConfC19ICUPatsPed is null) OR
(numConfFluICUPatsAdult is null AND numConfFluICUPatsPed is null) OR
(numConfRSVICUPatsAdult is null AND numConfRSVICUPatsPed is null) OR
numICUBeds is null OR
numICUBedsOcc is null

May 2025

     9
Reconciliation of Valid/Complete Data to Weekly Pathway
NHSN users may choose to submit data via either a weekly reporting pathway OR a daily reporting
pathway to satisfy requirements for submission of Hospital Respiratory Data for CMS CoP. Data submitted
to the weekly pathway represent two types of information:
1. Single-day snapshot data elements: the 24 data elements within the reporting form sections for
Bed Capacity and Occupancy and Prevalent Hospitalizations are required to be reported as single
day snapshots (specifically, Wednesday) of the reporting week.
2. Weekly total data elements: the 21 data elements within the reporting form sections for New
Admissions are required to be reported to account for aggregated data for the entire reporting
week (specifically, Sunday-Saturday).
Complete daily data (meaning non-null values reported for all 45 required data elements) submitted for a
given reporting week (Sunday – Saturday) to the Daily HRD pathway will be reconciled with data
submitted via the Weekly HRD pathway. Values reported for the Wednesday during the reporting period
will be retained for the 24 Bed Capacity and Occupancy and Prevalent Hospitalizations data elements,
while weekly aggregate totals will be calculated for the 21 New Admissions data elements by summing the
values reported each day of the reporting week.
Data reported to the Daily HRD pathway will only be carried over to the Weekly HRD pathway if complete
data were reported for all required fields each day in the reporting period (for New Admissions) and on
Wednesday (for Bed Capacity and Occupancy and Prevalent Hospitalizations).
Note: This data reconciliation step occurs AFTER deduplication of the Daily HRD data and application of
the logic checks outlined above to the Daily HRD data. Therefore, invalid daily data that fail the data
quality logic checks will be treated as missing in this step and, thus, will not be carried over to the Weekly
HRD pathway.
Aggregate Data Pipeline
Reconciled, de-duplicated weekly hospital respiratory data with logic checks applied are ingested into the
1 CDC Data Platform (1CDP), a Palantir Foundry platform, for further transformation and aggregation prior
to analytics, reporting, and public release.
Weekly hospital level data are first aggregated to the NHSN Facility ID level, aggregating data reported
across multiple contexts for a single hospital. Exclusion criteria are then applied to remove hospitals that
do not meet the following criteria:
• facType (NHSN Facility Type) = {HOSP-GEN, HOSP-CAH, HOSP-LTAC, HOSP-SURG, HOSP-CHLD,
HOSP-ORTHO, HOSP-ONC, HOSP-WOM, HOSP-WOMCHILD, HOSP-VA, HOSP-MIL}
o Note: These facility types represent hospitals that are required to report weekly hospital
respiratory under the CMS CoP as well as federal hospitals
• facStatus (NHSN Facility Status) = ‘A’

May 2025

     10
o Note: A facility status of ‘A’ indicates that the hospital currently has an Active registration
with NHSN
After exclusion criteria are applied, the weekly hospital data are then aggregated to various geographic
levels (nation, HHS region, state/territory) allowing for calculation of aggregate metrics, including hospital
admission rates and inpatient and ICU occupancy percentages. These aggregate data are published to
data.cdc.gov and CDC’s NHSN HRD website every Friday afternoon.
Additional Resources
• CDC’S NHSN Hospital Respiratory Data
• Hospital Respiratory Data Weekly Reporting Form
• Hospital Respiratory Data Table of Instructions
• Hospital Respiratory Data Daily Reporting Form
• Hospital Respiratory Data Table of Instructions
