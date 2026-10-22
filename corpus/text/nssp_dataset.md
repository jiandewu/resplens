# NSSP Emergency Department Visit Trajectories by State and Sub-State Regions

NSSP Emergency Department (ED) Visit Trajectories by State and Sub-State Regions- COVID-19, Flu, RSV, Combined. This dataset provides the percentage of emergency department patient visits for the specified pathogen of all ED patient visits for the specified geographic part of the country that were observed for the given week from data submitted to the National Syndromic Surveillance Program (NSSP). In addition, the trend over time is characterized as increasing, decreasing or no change, with exceptions for when there are no data available, the data are too sparse, or there are not enough data to compute a trend. These data are to provide awareness of how the weekly trend is changing for the given geographic region.

Note that the reported sub-state trends are from Health Service Areas (HSA) and the data reported from the health care facilities located within the given HSA. Health Service Areas are regions of one or more counties that align to patterns of care seeking. The HSA level data are reported for each county in the HSA.

More information on HSAs is available here.

For the emergency department time series, trajectory classifications reported on for sub-state (HSA) emergency department time series, trajectory classifications are based on approximations of the first derivative (slope) of trends that are smoothed using generalized additive models (GAMs). To determine time intervals in which the slope is sufficiently changing (i.e., rate of change distinguishable from 0), 95% confidence intervals for the slope approximations are calculated and assessed. Weeks with a 95% confidence interval not containing 0 are classified as increasing if the slope estimate is positive and decreasing if the slope estimate is negative. Weeks with a 95% confidence interval containing 0 are classified as stable. In the scenario that an HSA's time series is determined to be too sparse (i.e., many weeks with percentages of 0%), a model is not fit, and the HSA is classified as “sparse”.

For additional information, please see: Companion Guide: NSSP Emergency Department Data on Respiratory Illness

Updated once per week on Fridays.

## Columns

### week_end (`week_end`)

No description provided.

### geography (`geography`)

No description provided.

### county (`county`)

No description provided.

### percent_visits_combined (`percent_visits_combined`)

No description provided.

### percent_visits_covid (`percent_visits_covid`)

No description provided.

### percent_visits_influenza (`percent_visits_influenza`)

No description provided.

### percent_visits_rsv (`percent_visits_rsv`)

No description provided.

### percent_visits_smoothed_combined (`percent_visits_smoothed`)

No description provided.

### percent_visits_smoothed_covid (`percent_visits_smoothed_covid`)

No description provided.

### percent_visits_smoothed_influenza (`percent_visits_smoothed_1`)

No description provided.

### percent_visits_smoothed_rsv (`percent_visits_smoothed_rsv`)

No description provided.

### ed_trends_covid (`ed_trends_covid`)

No description provided.

### ed_trends_influenza (`ed_trends_influenza`)

No description provided.

### ed_trends_rsv (`ed_trends_rsv`)

No description provided.

### hsa (`hsa`)

No description provided.

### hsa_counties (`hsa_counties`)

No description provided.

### hsa_nci_id (`hsa_nci_id`)

No description provided.

### fips (`fips`)

No description provided.

### trend_source (`trend_source`)

No description provided.

### BuildNumber (`buildnumber`)

No description provided.
