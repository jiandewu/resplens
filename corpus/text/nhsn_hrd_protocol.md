# Hospital Respiratory Data Reporting Protocol

January 2026  Hospital Respiratory Data

1

NHSN Hospital Respiratory Data (HRD) Reporting
Updated: January 1, 2026
Implementation date: October 9, 2024
Note: For ease of navigation, all changes reflected in this updated protocol have been highlighted in
orange. The updates reflect 2026 reporting information for annual reporters.

Introduction
The COVID-19 pandemic underscored the public health threat of respiratory pathogens and highlighted
the need for comprehensive, real-time surveillance data on U.S. healthcare system stress, capacity,
capability, and patient safety for prevention and response purposes. As such, from September 2, 2020 –
April 30, 2024, all U.S. acute care and critical access hospitals were required to report COVID-19 and other
respiratory pathogen, bed capacity, and supply data to the U.S. Government, specifically the Department
of Health and Human Services (HHS) and the Centers for Disease Control and Prevention (CDC), under the
Centers for Medicare & Medicaid (CMS) Conditions of Participation (CoP).1

Due to the ongoing need for situational awareness of the impacts of respiratory disease, CMS proposed a
new requirement for all U.S. hospitals to electronically report information about COVID-19, influenza,
respiratory syncytial virus (RSV), and hospital bed capacity to CDC’s National Healthcare Safety Network
(NHSN) in a standardized format and frequency specified by the HHS Secretary to provide situational
awareness of the impact of these respiratory diseases on patients and healthcare systems in the United
States. In August 2024, CMS finalized the FY 2025 IPPS rule. Beginning on November 1, 2024, CMS
specified the required reporting to include the following to NHSN on a weekly basis:2

1. Hospital bed capacity and occupancy information, overall and by bed type (inpatient, ICU) and
designation (adult, pediatric)
2. Number of patients hospitalized with laboratory-confirmed COVID-19, influenza, and RSV, by age
group
3. Number of new hospital admissions of patients with laboratory-confirmed COVID-19, influenza,
and RSV, by age group

Additionally, hospital personal protective equipment (PPE) and supply data are available for voluntary
reporting to NHSN in conjunction with the required data.




1 For information on previous reporting guidance, requirements, and specifications through April 30, 2024, please
visit the NHSN Hospital Respiratory Data page.
2 FY 2025 Hospital Inpatient Prospective Payment System (IPPS) and Long -Term Care Hospital Prospective Payment
System (LTCH PPS) Final Rule, pgs. 898-905.

January 2026  Hospital Respiratory Data

2

Facility Types Required to Report3
Weekly Reporters
The following facility types are required to report Hospital Respiratory Data to NHSN on a weekly cadence
(e.g., report data by Tuesday 11:59pm PT for the previous reporting week of Sunday – Saturday):
• Short-term Acute Care Hospitals (including Medicaid-Only Short-term Acute Care Hospitals)
• Long-term Care Hospitals (LTCHs)
• Critical Access Hospitals (CAHs)
• Oncology Hospitals (including PPS Exempt Cancer Hospitals)
• Children’s Hospitals (including Medicaid-Only Children’s Hospitals)
• Indian Health Services Hospitals (also Tribal Hospitals, Medicare-participating)

Veteran’s Health Administration (VHA) and Defense Health Agency (DHA) facilities are also encouraged to
report following a weekly cadence.

Annual Reporters
The following facility types are required to report Hospital Respiratory Data to NHSN annually, beginning
January 2025:
• Freestanding inpatient rehabilitation facilities (including Medicaid-Only Rehabilitation
Hospitals)
• Freestanding inpatient psychiatric facilities (including Medicaid-Only Psychiatric Hospitals)
• CMS-certified inpatient rehabilitation facility units (IRF within a hospital; distinct part units)
• CMS-certified inpatient psychiatric facility units (IPF within a hospital; distinct part units)

See Appendix A for specific guidance on reporting for CMS-certified IRF and IPF units.

Facilities are responsible for reporting the information directly to the Federal government using NHSN’s
Patient Safety Component (PSC) Hospital Respiratory Data (HRD) Module. Facilities should report at the
individual hospital level, even if hospitals share a CMS Certification Number (CCN).

Reporting capabilities for the NHSN application webform, CSV upload, and API are available.
• Facilities can report individually directly into the NHSN application via the webform, CSV upload,
or API.
• Jurisdictions can submit data on behalf of facilities within their area, hospital systems can submit
data at an enterprise level, and third-party providers can submit data on behalf of facilities and
jurisdictions via CSV upload or API.

3 Updates to the Condition of Participation (CoP) Requirements for Hospitals and Critical Access Hospitals (CAHs) To
Report Acute Respiratory Illnesses

January 2026  Hospital Respiratory Data

3

Summary of Data Elements
The NHSN HRD module collects 58 data elements, 48 of which are required to be reported and 10 of
which are optional.
Table 1: Summary of Data Elements required for reporting to NHSN as of Nov 1, 2024
Status Category
Number of
data
elements
Data
element
IDs
Required  Facility information and datetime fields 3 1a – 1c
Hospital bed capacity and occupancy,
overall and by bed type and designation  12 2a – 5c
Prevalent hospitalizations (COVID-19,
influenza, RSV), by age group 12 6a – 11b
New hospital admissions (COVID-19,
influenza, RSV), by age group 21 12a – 14g
Optional Days-on-hand supplies 5 15a – 15e
Able to maintain supplies 5 16a – 16e

Complete lists of the required and optional data elements and data element definitions can be found in
the data collection forms and tables of instructions, available on the NHSN Hospital Respiratory Data
page.


Reporting Requirements, Cadence, and Pathways
As of November 1, 2024, all hospitals listed under “Facility Types Required to Report – Weekly Reporters”
are required to report the requested information weekly to NHSN.

All required data for a reporting week of Sunday through Saturday are due by the following Tuesday,
11:59pm PT. For Tuesday deadlines falling on federal holidays, the reporting deadline will shift to
Wednesday of the same week.


The data included in the submission depends on the selected reporting form and associated pathway in
the NHSN application (either the HRD Daily or HRD Weekly Form/Pathway) but both options will capture
the data needed to meet the CMS CoP:

January 2026  Hospital Respiratory Data

4

1. Single-day snapshot data elements: the 24 data elements within the reporting form sections for
Bed Capacity and Occupancy and Prevalent Hospitalizations are required to be reported as single
day snapshots (specifically, Wednesday) of the reporting week.

2. Weekly total data elements: the 21 data elements within the reporting form sections for New
Admissions are required to be reported to account for aggregated data for the entire reporting
week (specifically, Sunday-Saturday).

Table 2: NHSN HRD Reporting Pathway Options
 Daily data pathway Weekly data pathway
24 single-day
snapshot fields
(required)
Required: Report for the Wednesday of
the reporting week
(CAN report for other days in the week
voluntarily)
Required: Report for the Wednesday of the
reporting week
(CANNOT report for other days in the week
voluntarily)
21 weekly total new
hospital admissions
fields
(required)
Required: Report values for every day in
the reporting week separately; NHSN
application determines completeness of
reporting and calculates weekly totals
Required:  Reporters calculate and provide
the weekly total values for the reporting
week directly into the NHSN application
10 supply/PPE fields
(optional)
Recommended: Report for the
Wednesday in the reporting week
(Can report for other days in the week
voluntarily)
Recommended: Report for the Wednesday
in the reporting week
(CANNOT report for other days in the week
voluntarily)

The HRD module provides reporters the choice to submit data using either a weekly reporting pathway
OR a daily reporting pathway. The NHSN reporter must select one pathway (weekly or daily) and submit
data using that pathway for the entirety of a given reporting cycle (see information in next section). A user
may change the pathway when a new reporting cycle begins.

Either the weekly reporting pathway OR the daily reporting pathway will satisfy requirements for
submission of Hospital Respiratory Data for CMS CoP; reporters do NOT need to provide data into both
pathways to meet the CoP.

January 2026  Hospital Respiratory Data

5

Example Reporting Week: Sunday, November 3 – Saturday, November 9
Using HRD daily data pathway:
• Data for bed capacity and occupancy and prevalent COVID-19, influenza, and RSV hospitalizations
(24 total data elements; fields 2a – 11b on the reporting form) must be reported as a single-day
snapshot for Wednesday, November 6.
o Data for these fields can be voluntarily reported for all other days during the reporting
week.
• Data for COVID-19, influenza, and RSV new hospital admissions (21 total data elements; fields 12a
– 14g on the reporting form) must be reported for each day separately during the reporting week
of Sunday, November 3 – Saturday, November 9.
• Supply/PPE data (10 total data elements; fields 15a – 16b on the reporting form) can be
voluntarily reported for all days during the reporting week but are recommended to be reported
for Wednesdays to maintain consistency with previous reporting requirements for these fields
and with other single-day snapshot fields required under the CoP.

Using HRD weekly data pathway:
• Data for bed capacity and occupancy and prevalent COVID-19, influenza, and RSV hospitalizations
(24 total data elements; fields 2a – 11b on the reporting form) must be reported as a single-day
snapshot for Wednesday, November 6.
o Data for these fields CANNOT be voluntarily reported for all other days during the
reporting week in the weekly pathway/form.
• Data for COVID-19, influenza, and RSV new hospital admissions (21 total data elements; fields 12a
– 14g on the reporting form) must be reported as weekly totals directly for the reporting week of
Sunday, November 3 – Saturday, November 9.
• Supply/PPE data (10 total data elements; fields 15a – 16b on the reporting form) are available for
optional reporting on the weekly pathway/form, with data for Wednesday recommended to
maintain consistency with previous reporting requirements for these fields and with other single-
day snapshot fields required under the CoP.

The above data for example reporting week of Sunday, November 3 – Saturday, November 9 must be
entered into the NHSN application by Tuesday, November 12, 11:59pm PT. Please see Appendix B for
additional examples.

Annual Reporters
As of November 1, 2024, all hospitals listed under “Facility Types Required to Report – Annual Reporters”
are required to report the requested information to NHSN once annually, beginning January 2025.

To meet the annual reporting requirement, annual reporters should report data using either the HRD
daily data pathway or HRD weekly data pathway for one of the following full weeks in January 2025:
• Sunday, January 4, 2026 – Saturday January 10, 2026 (due by Tuesday January 13, 2026)
• Sunday, January 11, 2026 – Saturday January 17, 2026 (due by Tuesday January 20, 2026)
• Sunday, January 18, 2026 – Saturday January 24, 2026 (due by Tuesday January 27, 2026)
• Sunday, January 25, 2026 – Saturday, January 31, 2026 (due by Tuesday, February 3, 2026)

January 2026  Hospital Respiratory Data

6


All required data as outlined above in Table 2 for a reporting week of Sunday through Saturday are due
by the following Tuesday, 11:59pm PT.

Note: Annual reporters are also able to voluntarily report HRD to NHSN throughout the year, outside of
the required reporting week selected in January 2026. Data reported outside of the required reporting
week selected will not meet the annual requirement.

Reporting Completeness Evaluation
A full evaluation period for CMS CoP will span 28 days, or four total reporting weeks, of Sunday-Saturday.
NHSN will evaluate the completeness and timeliness of required reporting on a weekly basis, with final
evaluation reports generated in the days immediately following the final Tuesday submission deadline for
the fourth week in the evaluation period.

January 2026  Hospital Respiratory Data

7

Additional guidance for reporting specific data elements
Table 3. Pathogen-specific new hospital admissions and prevalent hospitalization data elements.
Template Data Element Column Name Data Field ID Data Field Name – Daily Reporting
numConfC19HospPatsAdult 6a All hospitalized adult patients with laboratory-confirmed COVID-19
numConfC19HospPatsPed 6b All hospitalized pediatric patients with laboratory-confirmed COVID-19
numConfC19ICUPatsAdult 9a Adult ICU patients with laboratory-confirmed COVID-19
numConfC19ICUPatsPed 9b Pediatric ICU patients with laboratory-confirmed COVID-19
numConfFluHospPatsAdult 7a All hospitalized adult patients with laboratory-confirmed influenza
numConfFluHospPatsPed 7b All hospitalized pediatric patients with laboratory-confirmed influenza
numConfFluICUPatsAdult 10a Adult ICU patients with laboratory-confirmed influenza
numConfFluICUPatsPed 10b Pediatric ICU patients with laboratory-confirmed influenza
numConfRSVHospPatsAdult 8a All hospitalized adult patients with laboratory-confirmed RSV
numConfRSVHospPatsPed 8b All hospitalized pediatric patients with laboratory-confirmed RSV
numConfRSVICUPatsAdult 11a Adult ICU patients with laboratory-confirmed RSV
numConfRSVICUPatsPed 11b Pediatric ICU patients with laboratory-confirmed RSV
numConfC19NewAdmPed0to4 12a Number of new admissions of patients with laboratory-confirmed COVID-19, 0-4 years of age
numConfC19NewAdmPed5to17 12b Number of new admissions of patients with laboratory-confirmed COVID-19, 5-17 years of age
numConfC19NewAdmAdult18to49 12c Number of new admissions of patients with laboratory-confirmed COVID-19, 18-49 years of age
numConfC19NewAdmAdult50to64 12d Number of new admissions of patients with laboratory-confirmed COVID-19, 50-64 years of age
numConfC19NewAdmAdult65to74 12e Number of new admissions of patients with laboratory-confirmed COVID-19, 65-74 years of age
numConfC19NewAdmAdult75plus 12f Number of new admissions of patients with laboratory-confirmed COVID-19, 75+ years of age
numConfC19NewAdmUnk 12g Number of new admissions of patients with laboratory-confirmed COVID-19, unknown age
numConfFluNewAdmPed0to4 13a Number of new admissions of patients with laboratory-confirmed influenza, 0-4 years of age
numConfFluNewAdmPed5to17 13b Number of new admissions of patients with laboratory-confirmed influenza, 5-17 years of age
numConfFluNewAdmAdult18to49 13c Number of new admissions of patients with laboratory-confirmed influenza, 18-49 years of age
numConfFluNewAdmAdult50to64 13d Number of new admissions of patients with laboratory-confirmed influenza, 50-64 years of age
numConfFluNewAdmAdult65to74 13e Number of new admissions of patients with laboratory-confirmed influenza, 65-74 years of age
numConfFluNewAdmAdult75plus 13f Number of new admissions of patients with laboratory-confirmed influenza, 75+ years of age
numConfFluNewAdmUnk 13g Number of new admissions of patients with laboratory-confirmed influenza, unknown age
numConfRSVNewAdmPed0to4 14a Number of new admissions of patients with laboratory-confirmed RSV, 0-4 years of age
numConfRSVNewAdmPed5to17 14b Number of new admissions of patients with laboratory-confirmed RSV, 5-17 years of age
numConfRSVNewAdmAdult18to49 14c Number of new admissions of patients with laboratory-confirmed RSV, 18-49 years of age
numConfRSVNewAdmAdult50to64 14d Number of new admissions of patients with laboratory-confirmed RSV, 50-64 years of age
numConfRSVNewAdmAdult65to74 14e Number of new admissions of patients with laboratory-confirmed RSV, 65-74 years of age
numConfRSVNewAdmAdult75plus 14f Number of new admissions of patients with laboratory-confirmed RSV, 75+ years of age
numConfRSVNewAdmUnk 14g Number of new admissions of patients with laboratory-confirmed RSV, unknown age

January 2026  Hospital Respiratory Data

8

Laboratory-confirmed definitions
The information listed below applies to the data elements listed in Table 3.

• Laboratory-confirmed COVID-19
o Laboratory confirmation includes detection of SARS-CoV-2 infection through molecular
tests (e.g., polymerase chain reaction, nucleic acid amplification), antigen detection tests,
immunofluorescence tests, OR viral culture. A positive result in the prior 14 days (≤14
days), whether completed as an inpatient or outpatient, can be used as the laboratory
confirmation.

• Laboratory-confirmed influenza
o Laboratory confirmation includes detection of influenza virus infection through molecular
tests (e.g., polymerase chain reaction, nucleic acid amplification), antigen detection tests,
immunofluorescence tests, OR viral culture. For hospital reporting, laboratory-confirmed
influenza is defined as Influenza A and B (this includes their subtypes and lineages [e.g.,
A(H1N1), A(H3N2), B/Victoria, B/Yamagata)]. Parainfluenza and Haemophilus influenzae
infections should not be reported. A positive result in the prior 14 days (≤14 days),
whether completed as an inpatient or outpatient, can be used as the laboratory
confirmation.

• Laboratory-confirmed RSV
o Laboratory confirmation includes detection of RSV infection through molecular tests (e.g.,
polymerase chain reaction, nucleic acid amplification), antigen detection tests,
immunofluorescence tests, OR viral culture. A positive result in the prior 14 days (≤14
days), whether completed as an inpatient or outpatient, can be used as the laboratory
confirmation.

Additional clarifications on laboratory-confirmed new hospital admissions and prevalent
hospitalizations for COVID-19, influenza, and RSV
The information listed below also applies to the data elements listed in Table 3.

• Patients should be counted in fields 12a-14g (new hospital admissions of COVID-19, influenza,
RSV) only once, using the date that corresponds to their hospital admission if a positive laboratory
confirmation is also present on the day of admission. If laboratory confirmation is not available at
the time of admission but becomes available at a later date, the previous count for admissions do
not need to be updated.
• Patients should be counted in fields 6a through 11b listed in Table 3 (prevalent COVID-19,
influenza, RSV hospitalizations) for the entirety of their hospitalization, even if they are still
hospitalized following negative laboratory testing. These counts also include patients with a re-
infection or co-infection.

January 2026  Hospital Respiratory Data

9

o In circumstances where patients have an exceptionally long length of stay (for example, in
a behavioral health unit) NHSN will defer to the facility to determine when to remove the
patient from inclusion in fields 6a through 11b.
• The number of new hospital admissions and the total patients hospitalized should generally not
be the same value.
o Laboratory-confirmed new hospitals admissions are the number of new patients who
were admitted to an inpatient bed with lab-confirmed COVID-19, influenza, or RSV.
 This is a measure of incidence, or new patients coming into the hospital.
o Total patients hospitalized with laboratory-confirmed COVID-19, influenza, or RSV are the
current number of patients with lab-confirmed COVID-19, influenza, or RSV occupying an
inpatient bed.
 This is a measure of prevalence, or current patients occupying a hospital bed.
o If the values are reported such that the number of patients currently hospitalized are
incorrectly reported as the number of new admissions, this can cause the new admissions
rate for the facility, county, and state to appear overinflated. Accuracy of these fields is
important, as they are frequently included reports, dashboards, and datasets that are
widely used by the public and the U.S. government.

See below scenarios for examples of how to report patients with laboratory-confirmed COVID-19,
influenza, or RSV.

January 2026  Hospital Respiratory Data

10

Scenario 1:
Patient aged 65 is admitted to hospital on Sunday of reporting week, with laboratory-confirmed COVID-19. Patient does NOT require ICU hospitalization during course of illness.

Using HRD Daily Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is admitted with
laboratory-confirmed COVID-
19.
Patient is hospitalized,
repeat test positive.
Patient is hospitalized,
repeat test negative.
Patient is discharged.
Action for reporting date of
Sunday:

Patient is included in:
REQUIRED 12e: Number of
new admissions of patients
with laboratory-confirmed
COVID-19, 65-74 years of age.
OPTIONAL 6a: All hospitalized
adult patients with laboratory-
confirmed COVID-19.
Action for reporting
date of Monday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
Action for reporting
date of Tuesday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
Action for reporting
date of Wednesday:

Patient is included in:
REQUIRED 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19 if
the census is captured
prior to discharge.

Action for reporting
date of Thursday:
NONE

Action for reporting
date of Friday:
NONE
Action for reporting
date of Saturday:
NONE


Using HRD Weekly Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is admitted with
laboratory-confirmed COVID-
19.
Patient is hospitalized,
repeat test positive.
Patient is hospitalized,
repeat test negative.
Patient is discharged.


Action for week ending Saturday:

Patient is included in:
REQUIRED 12e: Number of new admissions of patients with laboratory-confirmed COVID-19, 65-74 years of age (weekly total).
REQUIRED 6a: All hospitalized adult patients with laboratory- confirmed COVID-19 (Wednesday snapshot) if the census is captured prior to discharge.

January 2026  Hospital Respiratory Data

11

Scenario 2: Patient aged 55 is admitted to hospital on Sunday of reporting week, with laboratory-confirmed COVID-19 and laboratory-confirmed influenza (co-infection). Patient
does require ICU hospitalization initially in course of illness.
Using HRD Daily Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is newly admitted
and requires ICU
hospitalization, with
laboratory-confirmed COVID-
19 and laboratory-confirmed
influenza.
Patient is hospitalized in
ICU, repeat COVID test
positive, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
positive, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
negative.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
negative.
Patient is discharged.
Action for reporting date of
Sunday:

Patient is included in:
REQUIRED 12d: Number of
new admissions of patients
with laboratory-confirmed
COVID-19, 50-64 years of
age.
REQUIRED 13d: Number of
new admissions of patients
with laboratory-confirmed
influenza, 50-64 years of age.
OPTIONAL 6a: All
hospitalized adult patients
with laboratory- confirmed
COVID-19.
OPTIONAL 7a: All
hospitalized adult patients
with laboratory- confirmed
influenza.
OPTIONAL 9a: All
hospitalized adult ICU
patients with laboratory-
confirmed COVID-19.
OPTIONAL 10a: All
hospitalized adult ICU
patients with laboratory-
confirmed influenza.
Action for reporting
date of Monday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
OPTIONAL 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza.
OPTIONAL 9a: All
hospitalized adult ICU
patients with laboratory-
confirmed COVID-19.
OPTIONAL 10a: All
hospitalized adult ICU
patients with laboratory-
confirmed influenza.
Action for reporting
date of Tuesday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
OPTIONAL 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza.

Action for reporting
date of Wednesday:

Patient is included in:
REQUIRED 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
REQUIRED 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza.

Action for reporting
date of Thursday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
OPTIONAL 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza.

Action for reporting
date of Friday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19.
OPTIONAL 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza.

Action for reporting
date of Saturday:

Patient is included in:
OPTIONAL 6a: All
hospitalized adult
patients with laboratory-
confirmed COVID-19 if
the census is captured
prior to discharge.
OPTIONAL 7a: All
hospitalized adult
patients with laboratory-
confirmed influenza if
the census is captured
prior to discharge.

January 2026  Hospital Respiratory Data

12

Using HRD Weekly Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is newly admitted
and requires ICU
hospitalization, with
laboratory-confirmed COVID-
19 and laboratory-confirmed
influenza.
Patient is hospitalized in
ICU, repeat COVID test
positive, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
positive, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
positive.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
negative.
Patient is hospitalized
but no longer requires
ICU, repeat COVID test
negative, repeat flu test
negative.
Patient is discharged.

Scenario 3: Patient aged 4 years is admitted to hospital on Sunday of reporting week, with laboratory-confirmed RSV. Patient does require ICU hospitalization during course of
illness.
Using HRD Daily Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is newly admitted
and requires ICU
hospitalization, with
laboratory-confirmed RSV.
Patient is hospitalized in
ICU, repeat RSV test
positive.
Patient is hospitalized in
ICU, repeat RSV test
positive.
Patient is hospitalized in
ICU, no repeat test
performed.
Patient is hospitalized in
ICU, no repeat test
performed.
Patient is hospitalized
but no longer requires
ICU, repeat RSV test
negative.
Patient is discharged.
Action for reporting date of
Sunday:

Patient is included in:
REQUIRED 14a: Number of
new admissions of patients
with laboratory-confirmed
RSV, 0-4 years of age.
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV
OPTIONAL 11b. Pediatric ICU
patients with laboratory-
confirmed RSV
Action for reporting
date of Monday:

Patient is included in:
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV
OPTIONAL 11b. Pediatric
ICU patients with
laboratory-confirmed
RSV
Action for reporting
date of Tuesday:

Patient is included in:
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV
OPTIONAL 11b. Pediatric
ICU patients with
laboratory-confirmed
RSV
Action for reporting
date of Wednesday:

Patient is included in:
REQUIRED 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV
REQUIRED 11b. Pediatric
ICU patients with
laboratory-confirmed
RSV
Action for reporting
date of Thursday:

Patient is included in:
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV
OPTIONAL 11b. Pediatric
ICU patients with
laboratory-confirmed
RSV
Action for reporting
date of Friday:

Patient is included in:
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV

Action for reporting
date of Saturday:

Patient is included in:
OPTIONAL 8b: All
hospitalized pediatric
patients with laboratory-
confirmed RSV if the
census is captured prior
to discharge.



Action for week ending Saturday:
REQUIRED 12d: Number of new admissions of patients with laboratory-confirmed COVID-19, 50-64 years of age (weekly total).
REQUIRED 13d: Number of new admissions of patients with laboratory-confirmed influenza, 50-64 years of age (weekly total).
REQUIRED 6a: All hospitalized adult patients with laboratory-confirmed COVID-19.
REQUIRED 7a: All hospitalized adult patients with laboratory-confirmed influenza.

January 2026  Hospital Respiratory Data

13

Using HRD Weekly Reporting Pathway:
Sunday Monday Tuesday Wednesday Thursday Friday Saturday
Patient is newly admitted
and requires ICU
hospitalization, with
laboratory-confirmed RSV.
Patient is hospitalized in
ICU, repeat RSV test
positive.
Patient is hospitalized in
ICU, repeat RSV test
positive.
Patient is hospitalized in
ICU, no repeat test
performed.
Patient is hospitalized in
ICU, no repeat test
performed.
Patient is hospitalized
but no longer requires
ICU, repeat RSV test
negative.
Patient is discharged.

Reporting bed-level vs. unit- or location-level counts
Table 4. Inpatient bed capacity and occupancy data elements
Template Data Element Column Name Data Field ID Data Field Name – Daily Reporting
numInPtBeds 2a All hospital inpatient beds
numInPtBedsAdult 2b All adult inpatient beds
numInPtBedsPed 2c All pediatric inpatient beds
numInPtBedsOcc 3a All hospital inpatient occupancy
numInPtBedsOccAdult 3b All adult inpatient occupancy
numInPtBedsOccPed 3c All pediatric inpatient occupancy

The information listed below applies to the data elements listed in Table 4.

• Inpatient bed counts are not location-specific unless your facility has a CMS-certified inpatient rehabilitation or inpatient psychiatric unit.
All inpatient beds (which also include ICU beds), regardless of location, that are designated as pediatric or adult should be counted as
such. For additional clarification please see Specific guidance for CMS-certified psychiatric and rehabilitation units (Appendix A).




Action for week ending Saturday:
REQUIRED 14a: Number of new admissions of patients with laboratory-confirmed RSV, 0-4 years of age.
REQUIRED 8b: All hospitalized pediatric patients with laboratory-confirmed RSV.
REQUIRED 11b. Pediatric ICU patients with laboratory-confirmed RSV.

January 2026  Hospital Respiratory Data

14


Reporting inpatient pediatric bed counts for facilities that do not designate inpatient beds for adult or pediatric patients
The information listed below also applies to the data elements listed in Table 4.

• For facilities with staffed inpatient beds that are not designated specifically for adult or pediatric patients, it is acceptable to report
pediatric capacity as zero up until the point when there is a pediatric patient occupying a staffed inpatient bed, in which case numbers for
fields 2c, 3c, 4c, and 5c are asked to be reflective of hospitalized pediatric patients.

Reporting swing beds
The information listed below also applies to the data elements listed in Table 4.

• Swing beds are included in reporting fields 2a-3c UNLESS the beds part of a CMS-licensed SNF unit (SNF unit has a unique CCN with ‘U’,
‘W’, or ‘Y’ in the third position of the CCN). Swing beds in CMS-licensed SNF units within a facility are not included.
• See further information about swing beds on the Locations FAQs page.

Neonatal Intensive Care Unit (NICU) and nursery bed inclusion
The information listed below applies to the data elements listed in both Table 4 and Table 5.
Table 5. ICU bed capacity and occupancy data elements.
Template Data Element Column
Name
Data
Field ID Data Field Name
numICUBeds 4a All ICU beds
numICUBedsAdult 4b Adult ICU beds
numICUBedsPed 4c Pediatric ICU beds
numICUBedsOcc 5a All ICU bed occupancy
numICUBedsOccAdult 5b Adult ICU bed occupancy
numICUBedsOccPed 5c Pediatric ICU bed occupancy

• NICU and nursery beds should be included in the counts of inpatient and ICU beds.

January 2026  Hospital Respiratory Data

15

Reporting ICU bed counts for facilities that do not have ICUs, or ICU beds designated for adult or pediatric patients
The information listed below also applies to the data elements listed in Table 5.

• The value of 9999 should be reported in ICU fields to represent “not applicable.”
• The following scenarios ensure ICU bed counts for fields listed in Table 5 can be reported to differentiate between “not applicable”
scenarios, for facilities that do not have an ICU or ICU beds designated for adult or pediatric patients versus facilities that do have ICU
beds that might be reported as true zero or non-zero counts.


Scenario 1: Hospital A does not have an ICU, or any beds that can be designated as ICU beds for adult or pediatric patients.
Template Data Element Column
Name
Data
Field ID Data Field Name  Value Reported to NHSN
numICUBeds 4a All ICU beds 9999
numICUBedsAdult 4b Adult ICU beds 9999
numICUBedsPed 4c Pediatric ICU beds 9999
numICUBedsOcc 5a All ICU bed occupancy 9999
numICUBedsOccAdult 5b Adult ICU bed occupancy 9999
numICUBedsOccPed 5c Pediatric ICU bed occupancy 9999


Scenario 2: Hospital B does have an ICU with 10 beds (2 of which are occupied), but only designates ICU beds as adult ICU beds, and does not have
any pediatric-designated ICU beds.
Template Data Element Column
Name
Data
Field ID Data Field Name  Value reported to NHSN
numICUBeds 4a All ICU beds 10
numICUBedsAdult 4b Adult ICU beds 10
numICUBedsPed 4c Pediatric ICU beds 9999
numICUBedsOcc 5a All ICU bed occupancy 2
numICUBedsOccAdult 5b Adult ICU bed occupancy 2
numICUBedsOccPed 5c Pediatric ICU bed occupancy 9999

January 2026  Hospital Respiratory Data

16

Scenario 3: Hospital C does have an ICU with 12 beds, of which 10 are designed for adult patients (5 of which are occupied), and 2 are designated
for pediatric patients (1 of which is occupied).
Template Data Element Column
Name
Data
Field ID Data Field Name  Value reported to NHSN
numICUBeds 4a All ICU beds 12
numICUBedsAdult 4b Adult ICU beds 10
numICUBedsPed 4c Pediatric ICU beds 2
numICUBedsOcc 5a All ICU bed occupancy 6
numICUBedsOccAdult 5b Adult ICU bed occupancy 5
numICUBedsOccPed 5c Pediatric ICU bed occupancy 1

January 2026  Hospital Respiratory Data

17

Appendix A. Specific guidance for CMS-certified psychiatric and rehabilitation units
Some acute care, critical access, or long-term acute care facilities have a CMS-certified inpatient
rehabilitation facility (IRF) unit and/or a CMS-certified inpatient psychiatric facility (IPF) unit located within
the facility. These units share the facility’s NHSN OrgID but have a unique CCN (even if different by only
one letter or number).

Example:
Facility CCN: 000000
CMS-certified psychiatric unit CCN: 00S000

Tip: your facility’s billing/administrative department can confirm if the rehabilitation or psychiatric unit is
CMS-certified and has a different CCN from the facility.

Data for CMS-certified IRF units and/or CMS-certified IPF units should be reported separately from the
larger parent facility for Hospital Respiratory Data reporting.

Separate reporting of CMS-certified IRF unit and/or CMS-certified IPF unit data for Hospital Reporting
should be done under the same OrgID as the parent hospital, using the Context field in the data
collection.

For facilities WITH a CMS-certified IRF unit and/or CMS-certified IPF unit:
EXCLUDE CMS-certified IRF unit and/or CMS-certified IPF unit beds from the overall counts reported
under the HOSP context.
Report the CMS-certified IRF unit and/or CMS-certified IPF unit counts separately for the facility under the
IRF and/or IPF context.

For facilities WITHOUT a CMS-certified inpatient rehabilitation unit and/or CMS-certified inpatient
psychiatric unit:
INCLUDE any inpatient rehabilitation and psychiatric beds in your hospital in the bed count for this field,
using the HOSP context.

Scenario:

Acute Care Facility with NHSN OrgID 00000 has a CMS-certified IRF and IPF.

If using the Hospital Respiratory Data webform, the facility will report HOSP, IRF, and IPF values separately
by submitting a form with data completed for each of the contexts:

January 2026  Hospital Respiratory Data

18



Complete reporting view for Wednesday of the reporting week:


If using the Hospital Respiratory Data CSV template upload, the facility will report HOSP, IRF, and IPF
values on separate rows under the “context” header in the file:



Note: CMS-certified inpatient rehabilitation facility units (IRF within a hospital; distinct part units) and
CMS-certified inpatient psychiatric facility units (IPF within a hospital; distinct part units), in addition to
freestanding inpatient rehabilitation and inpatient freestanding psychiatric facilities are required to report
HRD to NHSN once annually.

January 2026  Hospital Respiratory Data

19

Appendix B. Reporting cadence calendar examples
Daily Data Reporting Cadence
Note: Data for each week are due by the following Tuesday, 11:59 p.m. PT.
 Sunday Monday Tuesday Wednesday Thursday Friday Saturday
WEEK 1
Day 1 Day 2 Day 3 Day 4 Day 5 Day 6 Day 7
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions,
hospitalizations, bed
capacity/occupancy
OPTIONAL: supplies
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New
admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
START OF EVALUATION
PERIOD
WEEK 2
Day 8 Day 9 Day 10 Day 11 Day 12 Day 13 Day 14
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions,
hospitalizations, bed
capacity/occupancy
OPTIONAL: supplies
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New
admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
Submission deadline (Week 1,
days 1-7)
WEEK 3
Day 15 Day 16 Day 17 Day 18 Day 19 Day 20 Day 21
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions,
hospitalizations, bed
capacity/occupancy
OPTIONAL: supplies
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New
admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
Submission deadline (Week 2,
days 8-14)
WEEK 4
Day 22 Day 23 Day 24 Day 25 Day 26 Day 27 Day 28
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions,
hospitalizations, bed
capacity/occupancy
OPTIONAL: supplies
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New
admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
Submission deadline (Week 3,
days 15-21)
END OF EVALUATION PERIOD
WEEK 1
Day 1 Day 2  Day 3 Day 4  Day 5 Day 6 Day 7
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions,
hospitalizations, bed
capacity/occupancy
OPTIONAL: supplies
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New
admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
REQUIRED: New admissions
OPTIONAL: supplies,
hospitalizations, bed
capacity/occupancy
START OF NEW EVALUATION
PERIOD
Submission deadline (Week 4,
days 22-28)
Completeness report
generated, weeks 1 - 4

January 2026                                                                                                                    Hospital Respiratory Data


20

Weekly Data Reporting Cadence
Note: Data for each week are due by the following Tuesday, 11:59 p.m. PT.
 Sunday Monday Tuesday Wednesday Thursday Friday Saturday
WEEK 1
Day 1 Day 2 Day 3 Day 4 Day 5 Day 6 Day 7
REQUIRED: weekly total new admissions
   REQUIRED: hospitalizations,
bed capacity/occupancy
OPTIONAL: supplies

START OF EVALUATION
PERIOD
WEEK 2
Day 8 Day 9 Day 10 Day 11 Day 12 Day 13 Day 14
REQUIRED: weekly total new admissions
  Submission deadline
(Week 1)
REQUIRED: hospitalizations,
bed capacity/occupancy
OPTIONAL: supplies

WEEK 3
Day 15 Day 16 Day 17 Day 18 Day 19 Day 20 Day 21
REQUIRED: weekly total new admissions
  Submission deadline
(Week 2)
REQUIRED: hospitalizations,
bed capacity/occupancy
OPTIONAL: supplies

WEEK 4
Day 22 Day 23 Day 24 Day 25 Day 26 Day 27 Day 28
REQUIRED: weekly total new admissions
  Submission deadline
(Week 3)
REQUIRED: hospitalizations,
bed capacity/occupancy
OPTIONAL: supplies

END OF EVALUATION
PERIOD
WEEK 1
Day 1 Day 2  Day 3 Day 4  Day 5 Day 6 Day 7
REQUIRED: weekly total new admissions
  Submission deadline
(Week 4)
REQUIRED: hospitalizations,
bed capacity/occupancy
OPTIONAL: supplies

Completeness report
generated, weeks 1 - 4

START OF NEW
EVALUATION PERIOD
