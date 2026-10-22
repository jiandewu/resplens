# CDC Wastewater Viral Activity Level for SARS-CoV-2, Influenza A and RSV

This dataset provides a complete time history of weekly SARS-CoV-2, Influenza A, and RSV wastewater viral activity level (WVAL) values from US sampling locations.

Learn more at: https://www.cdc.gov/wastewater
This dataset is updated weekly on Fridays.

## Columns

### State/Territory (`state_territory`)

State, DC, US territory, or Freely Associated State jurisdiction name (2-letter abbreviation) in which the wastewater treatment plant is located

### Counties_Served (`counties_served`)

The county and county-equivalent names served by this sampling site. Note that most jurisdictions are covered by counties, but some are covered by county equivalents, such as independent cities, parishes, or census areas.

### Site (`site`)

A unique identifier for wastewater treatment plants. This is an arbitrary integer used to provide a unique, but anonymous identifier for a wastewater treatment plant. This identifier is consistent over time, such that the same plant retains the same ID regardless of the addition or subtraction of other plants from the data set.

### Population_Served (`population_served`)

Estimated number of persons served by this sampling site (i.e., served by this wastewater treatment plant or, if 'sample_location' is "upstream", then by this upstream location)

### Source (`source`)

The source of the data collected and reported to CDC's Wastewater Surveillance Program, including public health departments (State_Territory), CDC's national wastewater testing contract (CDC_Verily, or formerly, CDC_Biobot) and an academic partner group WastewaterSCAN (WastewaterSCAN). For additional information see: https://www.cdc.gov/wastewater/about/index.html

### Site_WVAL (`site_wval`)

The calculated site wastewater viral activity level (WVAL) for the CDC/MMWR reporting week.

### Site_WVAL_Category (`site_wval_category`)

Category for the calculated site WVAL for the CDC/MMWR reporting week. Categories are ordinal based on pathogen specific cut-offs of WVAL values: very low, low, moderate, high, very high; and includes a 'limited/no data' category when there is insufficient data to calculate a WVAL.

### Date_Included_In_WVAL (`date_included_in_wval`)

Date site first submitted samples for inclusion in WVAL calculation

### Week_End (`week_end`)

Last date in one week time period for CDC/MMWR reporting week (always a Saturday)

### Pathogen_Target (`pathogen_target`)

Pathogen for which wastewater viral activity levels calculated.

### date_updated (`date_updated`)

Timestamp of processing run used in posted data. "As of " stamp.
