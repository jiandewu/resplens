# Hospital Respiratory Data Reporting: New Resources and FAQs

National Center for Emerging and Zoonotic Infectious Diseases
NHSN Hospital Respiratory Data
New Resources and FAQs
CDC Division of Healthcare Quality Promotion (DHQP)
September 2024
1

Webinar Summary
• Resource Overview
• Frequently Asked Questions
• Import File Specifications and “Front End” Requirements for Successful Submission
• Data Element Definitions and Additional Reporting Scenarios
• Q&A
- Please submit all questions to the Q&A option in the Zoom taskbar
• Replay webinar scheduled
- Friday, September 20, 2024, @ 1-2pm ET

3
Resource Overview

• Protocol
• Hospital Respiratory Data Form
and Tables of Instructions –
Weekly Reporting option
• Hospital Respiratory Data Form
and Tables of Instructions – Daily
Reporting option
• CSV Templates
• Training Registration and Slides

Hospital Respiratory Data Webpage
4
https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html

• Background for reporting
requirements
• Key information
• What is changing
• What is new
• Data elements
• Reporting cadence
• Data submission overview
Hospital Respiratory Data – Previous Training
5
https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html

Hospital Respiratory Data Reporting Resources
6
• NEW: Hospital Respiratory
Data Reporting Protocol
- Summary of Data Elements
- Reporting Requirements,
Cadence, and Pathways
• Calendar examples
- Guidance for reporting specific
data elements
• Scenario examples

Hospital Respiratory Data
Webpage Tour
7

Frequently Asked Questions
8

• For both the daily data submission pathway and the weekly data
submission pathway, data submission for reporting week of Sunday –
Saturday is due by the following Tuesday at 11:59pm Pacific Time
Reporting Cadence
9

Reporting Cadence – Daily Reporting
10
See p. 18 in protocol for full reporting cycle example

• Example: Reporting week of Sunday, November 3 – Saturday, November 9
• Required:
- Bed capacity, occupancy, and hospitalization fields required for Wednesday,
November 6
- New admissions fields required for each day of the reporting week Sunday,
November 3 – Saturday, November 9
• All above reporting due by Tuesday, November 12
Reporting Cadence – Daily Reporting
11

Reporting Cadence – Weekly Reporting
12
See p. 19 in protocol for full reporting cycle example

• Example: Reporting week of Sunday, November 3 – Saturday, November 9
• Required:
- Bed capacity, occupancy, and hospitalization fields required for Wednesday,
November 6
- New admissions fields required as a summed weekly total for reporting week
Sunday, November 3 – Saturday, November 9
• All above reporting due by Tuesday, November 12
Reporting Cadence – Weekly Reporting
13

• In the Hospital Respiratory Data module, you will see tab options for the Daily
Reporting Pathway and the Weekly Reporting Pathway.
How do I indicate which reporting pathway my facility will use (daily
versus weekly)?
14
- Submit data under the tab for the reporting
pathway your facility has selected.
- You will submit data using that pathway for the
entirety of the 28-day reporting cycle.
- The weekly reporting pathway OR the daily
reporting pathway will satisfy requirements for
submission of Hospital Respiratory Data for
CMS Conditions of Participation.
- If submitting via CSV upload or API, ensure you
are using the correct (daily, weekly) template.

• Please see page 8 of the protocol:
https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting.html
What are the definitions of laboratory-confirmed COVID-19,
influenza, and RSV ?
15

• The option to submit via API will be available.
• Hospital Respiratory Data instructions for setting up API submission are
being finalized.
- Instructions will be very similar to the set up for the COVID-19 reporting:
https://www.cdc.gov/nhsn/pdfs/covid19/COVID19-hospital-data-submission-API-
instructions-508.pdf
- The individual responsible for the API submission will need a SAMS account –
please reach out via the contact options at the end of the presentation to request
an invitation.
Hospital Respiratory Data API Submission
16

Import File Specifications and “Front End”
Requirements for Successful Submission
17

• Posted 9/17/2024:
- NHSN Hospital Respiratory Data Protocol
• Forthcoming:
- File Import and Data Upload Specifications (Daily and Weekly versions)
• ‘Front end’ requirements for successful file submission and data upload; applicable
to all reporting modalities (webform, CSV, API)
- Data Quality Reference Guide
- Guide for mapping columns between “old” COVID-19 templates and new HRD
Daily and Weekly templates
- NHSN Analysis Reports and Reference Guides
- SAMS and API Reference Guide
New and Forthcoming Resources for HRD Reporting
18

• Fields required for successful file import and data upload:
- Always required:
• NHSN OrgID: Organization Identification Number
– Note: will auto populate in the webform for submission, but needs to be
included on the CSV and API uploads
• Context: needed for ‘facility-within-facility’ or location-specific reporting, including
that for CMS-certified inpatient psychiatric (IPUs) or rehabilitation units (IRUs).
– Required to be included on CSV and API uploads, or, if using webform,
selected on the webform.
– See appendix A in Protocol for more details and guidance for IPU and IRU
reporting requirements.
File Import and Data Upload Specifications –
Required Fields
19

• Fields required for successful file import and data upload:
- Always required:
• Reporting for date (daily) or weekending date (weekly): date for which the counts
and/or responses in the selected pathway apply.
– Daily: reporting the number of new hospital admissions of patients with laboratory-
confirmed COVID-19 age 0-4 years for Monday 10/7/2024 of the reporting week.
Monday 10/7/2024 should be entered as the reportingDate, or selected on the calendar
view as the day for which counts are being reported in the HRD Daily Pathway.
– Weekly: reporting the number of new hospital admissions of patients with laboratory-
confirmed COVID-19 age 0-4 years for weekending Saturday, 10/12/2024, which should
be entered as the weekending date or selected on the calendar view as the week for
which counts are reported in the HRD weekly pathway.
» IMPORTANT: if using HRD Weekly pathway, data for the reporting week Sun-Sat
CANNOT be entered until reporting week has ended.
File Import and Data Upload Specifications –
Required Fields
20

• Fields required for successful file
import and data upload:
- Always required:
• New hospital admissions:
– Daily: report admissions counts
for each day separately in
reporting week
– Weekly: report total admission
counts for the entire reporting
week
File Import and Data Upload Specifications –
Required Fields
21
COVID-19 (7 total)
New hospital admissions, 0-4 years of age
New hospital admissions, 5-17 years of age
New hospital admissions, 18-49 years of age
New hospital admissions, 50-64 years of age
New hospital admissions, 65-74 years of age
New hospital admissions, 75+ years of age
New hospital admissions, unknown age
Influenza (7 total)
New hospital admissions, 0-4 years of age
New hospital admissions, 5-17 years of age
New hospital admissions, 18-49 years of age
New hospital admissions, 50-64 years of age
New hospital admissions, 65-74 years of age
New hospital admissions, 75+ years of age
New hospital admissions, unknown age
RSV (7 total)
New hospital admissions, 0-4 years of age
New hospital admissions, 5-17 years of age
New hospital admissions, 18-49 years of age
New hospital admissions, 50-64 years of age
New hospital admissions, 65-74 years of age
New hospital admissions, 75+ years of age
New hospital admissions, unknown age

• Fields required for successful file
import and data upload:
- Conditionally required: required only for
Wednesday of the reporting week
• Hospitalizations:
– Daily: report hospitalization
counts for report date =
Wednesday in reporting week
– Weekly: report hospitalization
counts for the Wednesday of
the reporting week
File Import and Data Upload Specifications –
Required Fields
22
Prevalent hospitalizations 6 elements total
COVID-19
All hospitalized adult patients with laboratory-
confirmed COVID-19
All hospitalized pediatric patients with laboratory-
confirmed COVID-19
Flu
All hospitalized adult patients with laboratory-
confirmed influenza
All hospitalized pediatric patients with laboratory-
confirmed influenza
RSV
All hospitalized adult patients with laboratory-
confirmed RSV
All hospitalized pediatric patients with laboratory-
confirmed RSV
ICU hospitalizations 6 elements total
COVID-19
Adult ICU patients with laboratory-confirmed
COVID-19
Pediatric ICU patients with laboratory-confirmed
COVID-19
Flu
Adult ICU patients with laboratory-confirmed
influenza
Pediatric ICU patients with laboratory-confirmed
influenza
RSV
Adult ICU patients with laboratory-confirmed RSV
Pediatric ICU patients with laboratory-confirmed
RSV

• Fields required for successful file
import and data upload:
- Conditionally required: required only for
Wednesday of the reporting week, and if
not actively participating in the NHSN
Connectivity Initiative: Hospital Bed
Capacity collection*
• Bed capacity and occupancy:
– Daily: report hospitalization
counts for report date =
Wednesday in reporting week
– Weekly: report hospitalization
counts for the Wednesday of
the reporting week
File Import and Data Upload Specifications –
Required Fields
23
Bed capacity and
occupancy 12 elements total
Inpatient beds
All hospital inpatient beds
All adult inpatient beds
All pediatric inpatient beds
Inpatient bed occupancy
All hospital inpatient occupancy
All adult inpatient occupancy
All pediatric inpatient occupancy
ICU beds
All ICU beds
Adult ICU beds
Pediatric ICU beds
ICU bed occupancy
All ICU bed occupancy
Adult ICU occupancy
Pediatric ICU occupancy
*Information on the NHSN Connectivity Initiative: Hospital Bed Capacity Project can
be found online: https://www.cdc.gov/nhsn/bed-capacity/index.html.

• No longer on NHSN import template, but still very important:
- CMS certification number (CCN)
- Hospital name
- Hospital location information (street address, county, zip code, etc.)
- Note: these additional columns CAN be added to your template and part of your
submission, but not required.
File Import and Data Upload Specifications –
Additional Guidance for Identifiers and Facility Information
24

• Column formats
- Counts (admissions, hospitalizations, bed capacity/occupancy): whole numbers
- Categorical (supplies): Y , N, N/A
- Date time fields (reporting date, weekending date): MMDDYYYY
• Valid values
File Import and Data Upload Specifications –
Column Formats and Valid Values
25
Template Data Element
Column Name ID Column Name Status Format Valid Values Business Rules
numConfC19NewAdmPed0to4 12a Number of new admissions of patients with laboratory-confirmed COVID-19, 0-4 years of age Required Integer (whole number) 0 to 100 Required for all reporting dates
numConfC19NewAdmPed5to17 12b Number of new admissions of patients with laboratory-confirmed COVID-19, 5-17 years of age Required Integer (whole number) 0 to 100 Required for all reporting dates
numConfC19NewAdmAdult18to49 12c Number of new admissions of patients with laboratory-confirmed COVID-19, 18-49 years of age Required Integer (whole number) 0 to 100 Required for all reporting dates
numConfC19NewAdmAdult50to64 12d Number of new admissions of patients with laboratory-confirmed COVID-19, 50-64 years of age Required Integer (whole number) 0 to 100 Required for all reporting dates
numConfC19NewAdmAdult65to74 12e Number of new admissions of patients with laboratory-confirmed COVID-19, 65-74 years of age Required Integer (whole number) 0 to 100 Required for all reporting dates
numConfC19NewAdmAdult75plus 12f Number of new admissions of patients with laboratory-confirmed COVID-19, 75+ years of age Required Integer (whole number) 0 to 100 Required for all reporting dates

• Comparing values across 2 or more columns to ensure logical consistency
and validity of reported data
Rationale for 3a. numInPtBedsOcc business rules:
• Field 5a (numICUBedsOcc) is a subset of 3a (numInPtBedsOcc)
• Field 3a represents at least the sum for 3b
(numInPtBedsOccAdult) and 3c (numInPtBedsOccPed)
File Import and Data Upload Specifications –
Logical Relationships
26
Template Data Element Column
Name ID Column Name Status Format Valid Values Business Rules
numInPtBeds 2a All hospital inpatient beds Conditional* Integer (whole number) 0 to 1500
numInPtBedsAdult 2b All adult inpatient beds Conditional* Integer (whole number) 0 to 1500 Must be <= 2a. numInPtBeds
numInPtBedsPed 2c All pediatric inpatient beds Conditional* Integer (whole number) 0 to 1500 Must be <= 2a. numInPtBeds
numInPtBedsOcc 3a All hospital inpatient occupancy Conditional* Integer (whole number) 0 to 1500 Must be >= 5a. numICUBedsOcc (where 5a. numICUBedsOcc does not equal 9999) ANDMust be >= (3b. numInPtBedsOccAdult + 3c. numInPtBedsOccPed)

• The value of 9999 should be reported in ICU fields to represent “not applicable.”
• Hierarchy:
- If 4a. numICUBeds = 9999, then values for all ICU fields listed = 9999
- If 4b. numICUBedsAdult = 9999, then value for 5b. numICUBedsOccAdult = 9999
- If 4c. numICUBedsPed = 9999, then value for 5c. numICUBedsOccPed = 9999
• If the ICU bed type is available but no ICU beds occupied or (zero really means zero) – report a zero.
• Null values will lead to file/record rejection – all fields should either have a zero, nonzero, or 9999 value
captured
File Import and Data Upload Specifications –
Differentiating zero bed counts from not applicable
27
Template Data Element Column Name Data Field ID Data Field Name
numICUBeds 4a All ICU beds
numICUBedsAdult 4b Adult ICU beds
numICUBedsPed 4c Pediatric ICU beds
numICUBedsOcc 5a All ICU bed occupancy
numICUBedsOccAdult 5b Adult ICU bed occupancy
numICUBedsOccPed 5c Pediatric ICU bed occupancy

• Scenario 1: Hospital A does not have an ICU, or any beds that can be designated as
ICU beds for adult or pediatric patients.
File Import and Data Upload Specifications –
Differentiating zero bed counts from not applicable
28
Template Data Element Column Name Data Field ID Data Field Name Value Reported to NHSN
numICUBeds 4a All ICU beds 9999
numICUBedsAdult 4b Adult ICU beds 9999
numICUBedsPed 4c Pediatric ICU beds 9999
numICUBedsOcc 5a All ICU bed occupancy 9999
numICUBedsOccAdult 5b Adult ICU bed occupancy 9999
numICUBedsOccPed 5c Pediatric ICU bed occupancy 9999

• Scenario 2: Hospital B does have an ICU with 10 beds (2 of which are occupied),
but only designates ICU beds as adult ICU beds, and does not have any pediatric-
designated ICU beds.
File Import and Data Upload Specifications –
Differentiating zero bed counts from not applicable
29
Template Data Element Column Name Data Field ID Data Field Name Value reported to NHSN
numICUBeds 4a All ICU beds 10
numICUBedsAdult 4b Adult ICU beds 10
numICUBedsPed 4c Pediatric ICU beds 9999
numICUBedsOcc 5a All ICU bed occupancy 2
numICUBedsOccAdult 5b Adult ICU bed occupancy 2
numICUBedsOccPed 5c Pediatric ICU bed occupancy 9999

• Scenario 3: Hospital C does have an ICU with 12 beds, of which 10 are designed for
adult patients (5 of which are occupied), and 2 are designated for pediatric
patients (1 of which is occupied).
File Import and Data Upload Specifications –
Differentiating zero bed counts from not applicable
30
Template Data Element Column Name Data Field ID Data Field Name Value reported to NHSN
numICUBeds 4a All ICU beds 12
numICUBedsAdult 4b Adult ICU beds 10
numICUBedsPed 4c Pediatric ICU beds 2
numICUBedsOcc 5a All ICU bed occupancy 6
numICUBedsOccAdult 5b Adult ICU bed occupancy 5
numICUBedsOccPed 5c Pediatric ICU bed occupancy 1

• File naming convention
- No required naming convention in place
• Column headers
- Columns can be included in any order, only requirement is to make sure they are
spelled correctly (including upper/lowercase) and values formatted correctly
- Be wary of additional characters (like an extra space) in your column header
names!
Additional Specifications for CSV and API Uploads
31

File Import and Data Upload Specifications –
Error Messages via CSV / API
32

File Import and Data Upload Specifications –
Error Messages in UI
33

File Import and Data Upload Specifications –
Reference Guides are on the Way!
34

Data Element Definitions and Additional Reporting
Scenarios
35

• Patients should be counted in fields 12a through 14g (new hospital admissions of
COVID-19, influenza, RSV) only once, for the date that corresponds to their hospital
admission if a positive laboratory confirmation is also present on the day of
admission.
• Patients should be counted in fields 6a through 11b (prevalent COVID-19,
influenza, RSV hospitalizations) for the entirety of their hospitalization, even if
they are still hospitalized following negative laboratory testing.
• These counts also include patients with a re-infection or co-infection.
Data Elements - Clarifications on new hospital admissions vs
hospitalizations for COVID-19, influenza, and RSV
36

• The number of new hospital admissions and the total patients
hospitalized should generally not be the same value.
- Laboratory-confirmed new hospitals admissions are the number of new patients
who were admitted to an inpatient bed with lab-confirmed COVID-19, influenza,
or RSV.
 This is a measure of incidence, or new patients coming into the hospital.
- Total patients hospitalized with laboratory-confirmed COVID-19, influenza, or
RSV are the current number of patients with lab-confirmed COVID-19, influenza,
or RSV occupying an inpatient bed.
 This is a measure of prevalence, or current patients occupying a hospital bed.
Data Elements - Clarifications on new hospital admissions vs
prevalent hospitalizations for COVID-19, influenza, and RSV
37

• Using HRD Daily pathway:
Scenario 1: Patient aged 65 is admitted to hospital on Sunday of reporting week,
with laboratory-confirmed COVID-19. Patient does NOT require ICU hospitalization
during course of illness. Patient is discharged on Wednesday of the reporting week.
38

• Using HRD Weekly pathway:
From Protocol:
Scenario 1: Patient aged 65 is admitted to hospital on Sunday of reporting week,
with laboratory-confirmed COVID-19. Patient does NOT require ICU hospitalization
during course of illness. Patient is discharged on Wednesday of the reporting week.
39

• Using HRD Daily Pathway:
40
From Protocol:
Scenario 3: Patient aged 4 years is admitted to hospital on Sunday of reporting week,
with laboratory-confirmed RSV. Patient does require ICU hospitalization during
course of illness and discharged on Saturday of the reporting week.

• Using HRD Weekly Pathway:
41
From Protocol:
Scenario 3: Patient aged 4 years is admitted to hospital on Sunday of reporting week,
with laboratory-confirmed RSV. Patient does require ICU hospitalization during
course of illness and discharged on Saturday of the reporting week.

For more information, contact CDC
1-800-CDC-INFO (232-4636)
TTY:  1-888-232-6348    www.cdc.gov
The findings and conclusions in this report are those of the authors and do not necessarily represent the official
position of the Centers for Disease Control and Prevention.
Contact the NHSN Helpdesk
• NHSN-ServiceNow to submit questions to the NHSN Help Desk.
• Access the portal at https://ServiceDesk.cdc.gov/NHSNcsp.
• If you do not have a SAMS login, or are unable to access ServiceNow,
you can still email the NHSN Help Desk at NHSN@cdc.gov.
