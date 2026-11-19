# Unmatched numbers (blind)

Each number below did not appear in the question or a tool output. Label it `derived` if its inputs and operation are stated and correct (rounding to the precision shown is fine), otherwise `unsupported`. One row per occurrence; identical answers from different runs appear once.

## N01

**Question:** Forecast influenza hospital admissions in Alaska for the next four weeks.

**Numbers to review:** 48.0, 90.0

**Answer:**

**Influenza hospital-admission forecast for Alaska (next 4 weeks)**  

| Week ending (Saturday) | Median forecast | 50 % interval (Q25-Q75) | 95 % interval (Q2.5-Q97.5) |
|------------------------|----------------|------------------------|----------------------------|
| 2026-10-17 | 17 | 12 - 21 | 4 - 34 |
| 2026-10-24 | 20 | 13 - 24 | 4 - 49 |
| 2026-10-31 | 14 | 11 - 27 | 2 - 100 |
| 2026-11-07 | 24 | 11 - 34 | 3 - 145 |

*Model*: LightGBM quantile-regression (15 leaves, learning-rate 0.03).  
*Back-test performance* (forecast dates 2025-04-04 to 2026-07-24, 69 Fridays):  

- Relative weighted interval score vs. persistence = 0.712 (95 % CI 0.666 - 0.755).  
- 50 % interval coverage ≈ 48 %; 95 % interval coverage ≈ 90 %.

**Reliability caveats (recent data)**  

- Hospital-admission counts for the most recent weeks (2026-10-03 and 2026-10-10) were reported by only **14 hospitals**, below the state threshold of **17**. Those weeks likely **under-count** admissions.  
- No other flags (e.g., data quality issues) were raised for the latest weeks.  
- Wastewater influenza data (influenza A only) are available, but do not affect the hospital-admission forecast.

Because the forecast starts from the latest reported week (2026-10-10), the above hospital-participation caveats apply to the baseline from which the model projects forward.

**Sources**: forecast_admissions, check_reliability

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "AK", "weeks": 4})</summary>

```
{
  "state": "AK",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 14,
    "reporting_threshold": 17,
    "weeks_reduced_participation": [
      "2026-10-03",
      "2026-10-10"
    ]
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "latest_trend": "No Change"
  },
  "wastewater": {
    "sites_with_data": 4,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 2,
      "Low": 1,
      "Moderate": 1
    },
    "sites_reduced_participation": 0,
    "anomalous_site_weeks": 5
  },
  "caveats": [
    "Fewer than 17 hospitals reported in: 2026-10-03, 2026-10-10; admission counts in those weeks undercount.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "AK"})</summary>

```
{
  "state": "AK",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 13,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 17,
      "interval_50": [
        12,
        21
      ],
      "interval_95": [
        4,
        34
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 20,
      "interval_50": [
        13,
        24
      ],
      "interval_95": [
        4,
        49
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 14,
      "interval_50": [
        11,
        27
      ],
      "interval_95": [
        2,
        100
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 24,
      "interval_50": [
        11,
        34
      ],
      "interval_95": [
        3,
        145
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N02

**Question:** Where are COVID-19 hospital admissions in Georgia headed over the next month?

**Numbers to review:** 70.0

**Answer:**

**COVID-19 Hospital Admissions Forecast for Georgia (next ≈ 4 weeks)**  

| Week ending (Saturday) | Median forecast | 50 % interval (low-high) | 95 % interval (low-high) |
|------------------------|----------------|--------------------------|--------------------------|
| 2026-10-17 | 76 | 67 - 88 | 51 - 119 |
| 2026-10-24 | 72 | 60 - 86 | 44 - 140 |
| 2026-10-31 | 72 | 55 - 89 | 30 - 161 |
| 2026-11-07 | 69 | 55 - 93 | 32 - 190 |

*The latest reported week (2026-10-10) had 84 admissions.*

**Model & Back-test performance**  
- LightGBM quantile-regression model (15 leaves, learning-rate 0.03).  
- Back-test (2025-04-04 → 2026-07-24, 69 forecast dates):  
  * Relative Weighted Interval Score vs. persistence: **0.712** (95 % CI 0.666 - 0.755).  
  * 50 % interval coverage: **47.5 %** (slightly low).  
  * 95 % interval coverage: **90.2 %** (close to nominal).  

**Data reliability for the recent period (2026-09-19 → 2026-10-10)**  
- Hospital admissions: 4 weeks of data, all flagged **observed_valid**.  
- Reporting hospitals = 113, exceeding the required threshold of 91 (no reduced participation weeks).  
- No additional caveats were flagged for hospital data.  

**Interpretation**  
The model suggests a modest decline from the most recent 84 admissions to a median of about 70-76 admissions over the next month, with fairly wide uncertainty-especially at the 95 % level-reflecting typical variability in weekly counts. The underlying hospital data for the recent weeks meet reporting thresholds and show no flagged reliability issues, giving confidence that the forecast is based on a solid recent data foundation.

*Sources: forecast_admissions (COVID-19, GA), check_reliability (GA, COVID-19).*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "covid", "state": "GA", "weeks": 4})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 113,
    "reporting_threshold": 91,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "latest_trend": "Decreasing"
  },
  "wastewater": {
    "sites_with_data": 25,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 3,
      "Low": 3,
      "Moderate": 3,
      "High": 4,
      "Very High": 7
    },
    "sites_reduced_participation": 2,
    "anomalous_site_weeks": 10
  },
  "caveats": []
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "COVID-19", "state": "GA"})</summary>

```
pathogen must be one of covid, influenza, rsv
```

</details>

<details><summary>forecast_admissions({"pathogen": "covid", "state": "GA"})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 84,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 76,
      "interval_50": [
        67,
        88
      ],
      "interval_95": [
        51,
        119
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 72,
      "interval_50": [
        60,
        86
      ],
      "interval_95": [
        44,
        140
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 72,
      "interval_50": [
        55,
        89
      ],
      "interval_95": [
        30,
        161
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 69,
      "interval_50": [
        55,
        93
      ],
      "interval_95": [
        32,
        190
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N03

**Question:** Forecast influenza hospital admissions for the Greenville area of South Carolina over the next four weeks.

**Numbers to review:** 2025.0, 2026.0, 0.71, 0.67, 0.76, 90.0, 48.0

**Answer:**

**Influenza hospital-admission forecast (state-level, South Carolina)**  

The CDC forecasting model provides weekly forecasts for the *state* total of influenza hospital admissions. A sub-state (e.g., Greenville HSA) forecast is not available, so the state-level numbers are the best proxy for the Greenville area.

| Week ending (Saturday) | Median forecast | 95 % prediction interval |
|------------------------|----------------|--------------------------|
| 2026-10-17 | 60 admissions | 23 - 117 |
| 2026-10-24 | 75 admissions | 21 - 188 |
| 2026-10-31 | 64 admissions | 14 - 420 |
| 2026-11-07 | 102 admissions | 16 - 609 |

*The most recent reported week (2026-10-10) had 51 influenza admissions.*

**Model performance** - Back-test (April 2025 → July 2026) shows a relative weighted interval score of **0.71** versus a persistence baseline (95 % CI 0.67 - 0.76). The 95 % intervals captured the observed value in **90 %** of back-test weeks, while the 50 % intervals covered the observed value in **48 %** of weeks.

**Data-quality caveats for South Carolina (influenza)**  

- **Hospital admissions**: All 4 recent weeks have the “observed_valid” flag; 70 hospitals reported, exceeding the required threshold of 50. No weeks with reduced participation.  
- **ED visits**: 3 of the last 4 weeks are flagged “anomalous” (large changes in smoothed percent), only 1 week is “observed_valid”. This suggests the ED trend may be unstable.  
- **Wastewater**: 24 sites report; 20 are in the “Very Low” category, 3 in “Very High”. Two sites showed reduced participation, and three weeks were flagged anomalous. Wastewater data cover influenza A only.

**Interpretation for Greenville**  
Because the forecast is at the state level, it reflects the overall trend for South Carolina. Greenville’s hospitals are part of the state reporting network, and the hospital-admission data are considered reliable (no flag, reporting above threshold). However, the ED and wastewater signals show recent anomalies, which could affect the precision of the forecast for any single locality.

**Bottom line** - Expect roughly 60-102 influenza hospital admissions per week in South Carolina over the next four weeks, with wide uncertainty especially later in the horizon. Greenville’s experience is likely to follow this state trend, but local variation cannot be quantified with the current sub-state forecast.

**Sources**: forecast_admissions (SC influenza), check_reliability (SC influenza)

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "SC", "weeks": 4})</summary>

```
{
  "state": "SC",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 70,
    "reporting_threshold": 50,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 3,
      "observed_valid": 1
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 24,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 20,
      "Very High": 3
    },
    "sites_reduced_participation": 2,
    "anomalous_site_weeks": 3
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26, 2026-10-03.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "SC"})</summary>

```
{
  "state": "SC",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 51,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 60,
      "interval_50": [
        50,
        67
      ],
      "interval_95": [
        23,
        117
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 75,
      "interval_50": [
        54,
        87
      ],
      "interval_95": [
        21,
        188
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 64,
      "interval_50": [
        43,
        129
      ],
      "interval_95": [
        14,
        420
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 102,
      "interval_50": [
        65,
        152
      ],
      "interval_95": [
        16,
        609
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N04

**Question:** Forecast weekly influenza hospital admissions in Florida through 2026-11-07.

**Numbers to review:** 950.0

**Answer:**

**Influenza Hospital Admissions Forecast - Florida (through 2026-11-07)**  

| Week ending (Saturday) | Weeks after last reported (2026-10-10) | Median forecast | 50 % interval (lower - upper) | 95 % interval (lower - upper) |
|------------------------|----------------------------------------|----------------|------------------------------|------------------------------|
| 2026-10-17 | 1 | 714 | 639 - 787 | 420 - 965 |
| 2026-10-24 | 2 | 814 | 662 - 904 | 342 - 1 295 |
| 2026-10-31 | 3 | 678 | 556 - 1 121 | 194 - 2 250 |
| 2026-11-07 | 4 | 953 | 733 - 1 339 | 213 - 2 875 |

**Model & performance**  
* LightGBM quantile-regression (15 leaves, learning-rate 0.03).  
* Back-test (2025-04-04 → 2026-07-24, 69 forecast dates):  
  * Relative weighted interval score vs. persistence = 0.712 (95 % CI 0.666 - 0.755).  
  * 50 % interval covered the observed value 47.5 % of the time.  
  * 95 % interval coverage = 90.2 %.  

**Data reliability (Florida, influenza)** - from the most recent 4 weeks (2026-09-19 → 2026-10-10):  

* **Hospital admissions** - 4 weeks of data; 225 hospitals reported (threshold = 164). One week (2026-09-19) flagged as anomalous due to an unusually large change; the other three weeks are valid.  
* **ED visits** - all 4 weeks flagged anomalous (large week-over-week changes).  
* **Wastewater** - 10 sites reported; 4 Low, 6 Moderate categories; no reduced participation or anomalous weeks.  
* **Caveats** - The anomalous hospital week (2026-09-19) may affect the baseline used for the forecast; ED percent changes were also unusually large in the same period. Wastewater data cover only influenza A.

**Interpretation**  
The forecast suggests a modest rise in influenza hospital admissions over the next month, with the highest median (≈ 950) expected for the week ending 2026-11-07. The 95 % intervals are wide, reflecting uncertainty especially in later weeks, and the recent anomalous hospital week should be kept in mind when interpreting the numbers.

*Sources: forecast_admissions, check_reliability*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "FL", "weeks": 4})</summary>

```
{
  "state": "FL",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 1,
      "observed_valid": 3
    },
    "reporting_hospitals_latest": 225,
    "reporting_threshold": 164,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 4
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 10,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Low": 4,
      "Moderate": 6
    },
    "sites_reduced_participation": 0,
    "anomalous_site_weeks": 0
  },
  "caveats": [
    "Hospital admissions had an unusually large week-over-week change in: 2026-09-19.",
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26, 2026-10-03, 2026-10-10.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "FL"})</summary>

```
{
  "state": "FL",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 634,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 714,
      "interval_50": [
        639,
        787
      ],
      "interval_95": [
        420,
        965
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 814,
      "interval_50": [
        662,
        904
      ],
      "interval_95": [
        342,
        1295
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 678,
      "interval_50": [
        556,
        1121
      ],
      "interval_95": [
        194,
        2250
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 953,
      "interval_50": [
        733,
        1339
      ],
      "interval_95": [
        213,
        2875
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N05

**Question:** What are influenza hospital admissions in Utah expected to be over the next four weeks, and how much can I trust that?

**Numbers to review:** 2025.0, 2026.0

**Answer:**

Based on a model forecast, influenza hospital admissions in Utah are expected to be as follows for the next four weeks:

*   **2026-10-17:** Median of **33** (95% interval: 10-65)
*   **2026-10-24:** Median of **38** (95% interval: 10-97)
*   **2026-10-31:** Median of **32** (95% interval: 7-234)
*   **2026-11-07:** Median of **52** (95% interval: 8-341)

### Reliability and Trustworthiness
To determine how much you can trust these numbers, consider the following:

**1. Model Accuracy**
This is a model forecast using LightGBM quantile regression. In backtests conducted from April 2025 to July 2026, the 95% intervals contained the actual reported value **90.2%** of the time.

**2. Data Quality (Hospital Data)**
The forecast is based on the most recent reported data, which are often subject to later revisions. However, the current hospital data for Utah appears reliable:
*   **Participation:** For the week ending 2026-10-10, 55 hospitals reported, which is above the state's minimum threshold of 40.
*   **Consistency:** There were no weeks with reduced participation flagged in the recent window (2026-08-22 to 2026-10-10).

**3. Other Caveats**
While hospital data is stable, other surveillance sources show some volatility:
*   **ED Visits:** There were three weeks (Sept 12, 19, and 26) with unusually large changes in smoothed ED percentages.
*   **Wastewater:** Wastewater data for influenza in Utah only covers influenza A.

Sources: forecast_admissions, check_reliability

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "window": {
    "start": "2026-08-22",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 8
    },
    "reporting_hospitals_latest": 55,
    "reporting_threshold": 40,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 5,
      "flagged_anomalous": 3
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 33,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 29,
      "Low": 3,
      "High": 1
    },
    "sites_reduced_participation": 5,
    "anomalous_site_weeks": 20
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-12, 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 30,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 33,
      "interval_50": [
        26,
        38
      ],
      "interval_95": [
        10,
        65
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 38,
      "interval_50": [
        27,
        49
      ],
      "interval_95": [
        10,
        97
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 32,
      "interval_50": [
        22,
        67
      ],
      "interval_95": [
        7,
        234
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 52,
      "interval_50": [
        26,
        81
      ],
      "interval_95": [
        8,
        341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N06

**Question:** How are influenza hospital admissions in Nebraska expected to change over the next month?

**Numbers to review:** 2025.0, 2026.0

**Answer:**

**Influenza hospital admissions forecast for Nebraska (next ≈ 4 weeks)**  

| Week ending (Saturday) | Median forecast | 50 % interval (low-high) | 95 % interval (low-high) |
|------------------------|----------------|--------------------------|--------------------------|
| 2026-10-17 | 17 | 9 - 20 | 4 - 39 |
| 2026-10-24 | 18 | 11 - 25 | 3 - 57 |
| 2026-10-31 | 15 | 11 - 32 | 3 - 133 |
| 2026-11-07 | 24 | 12 - 42 | 3 - 189 |

*The model (LightGBM quantile regression) was trained on historic CDC data and selected via the B1 benchmark. In back-testing (April 2025 - July 2026) the forecast’s weighted interval score was 0.712 ×  that of a simple persistence model (95 % CI 0.666-0.755). The 95 % prediction intervals captured the observed value in 90.2 % of back-test weeks.*

**Reliability caveats for the most recent data (the 4 weeks that the forecast builds on, 2026-09-19 to 2026-10-10):**  

* Hospital admissions met the reporting-hospital threshold (77 hospitals) each week, but two weeks (2026-09-19 and 2026-10-03) were flagged as **anomalous** due to unusually large week-over-week changes.  
* Emergency-department (ED) visit data also show two anomalous weeks (2026-10-03 and 2026-10-10).  
* Wastewater surveillance (16 sites) includes 2 “Very Low” and 1 “Low” category sites; 4 sites had reduced participation and 9 site-weeks were flagged anomalous.  
* Influenza wastewater data cover influenza A only.

Overall, the recent hospital data are complete but contain a few anomalous weeks, which adds some uncertainty to the forecast.  

**Takeaway:** The model suggests modestly increasing influenza hospital admissions over the next month, with a median of about 17-24 weekly admissions and wide uncertainty bounds, especially for the later weeks.

*Sources: forecast_admissions, check_reliability*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "NE", "weeks": 4})</summary>

```
{
  "state": "NE",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 2,
      "observed_valid": 2
    },
    "reporting_hospitals_latest": 77,
    "reporting_threshold": 77,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 2,
      "flagged_anomalous": 2
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 16,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 2,
      "Low": 1
    },
    "sites_reduced_participation": 4,
    "anomalous_site_weeks": 9
  },
  "caveats": [
    "Hospital admissions had an unusually large week-over-week change in: 2026-09-19, 2026-10-03.",
    "Smoothed ED percent had an unusually large change in: 2026-10-03, 2026-10-10.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "NE"})</summary>

```
{
  "state": "NE",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 14,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 17,
      "interval_50": [
        9,
        20
      ],
      "interval_95": [
        4,
        39
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 18,
      "interval_50": [
        11,
        25
      ],
      "interval_95": [
        3,
        57
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 15,
      "interval_50": [
        11,
        32
      ],
      "interval_95": [
        3,
        133
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 24,
      "interval_50": [
        12,
        42
      ],
      "interval_95": [
        3,
        189
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N07

**Question:** What are influenza hospital admissions in Utah expected to be over the next four weeks, and how much can I trust that?

**Numbers to review:** 2025.0, 2026.0

**Answer:**

Based on a model forecast, influenza hospital admissions in Utah are expected to be as follows for the next four weeks:

*   **2026-10-17:** Median of **33** (95% interval: 10-65)
*   **2026-10-24:** Median of **38** (95% interval: 10-97)
*   **2026-10-31:** Median of **32** (95% interval: 7-234)
*   **2026-11-07:** Median of **52** (95% interval: 8-341)

### Reliability and Trustworthiness
To determine how much you can trust these numbers, consider the following:

**1. Model Accuracy**
This is a model forecast using LightGBM quantile regression. In backtests conducted from April 2025 to July 2026, the 95% intervals contained the actual reported value **90.2%** of the time.

**2. Data Quality (Hospital Data)**
The forecast is based on the most recent reported data, which are often subject to revision. However, the current hospital data for Utah appears reliable:
*   **Participation:** For the week ending 2026-10-10, 55 hospitals reported, which is above the state's reporting threshold of 40.
*   **Consistency:** There were no weeks with reduced participation flagged in the recent window (2026-08-22 to 2026-10-10).

**3. Other Caveats**
While hospital data is stable, other surveillance sources show some volatility:
*   **ED Visits:** There were three weeks (Sept 12, 19, and 26) with unusually large changes in smoothed ED percentages.
*   **Wastewater:** Wastewater data for influenza in Utah only covers influenza A.

Sources: forecast_admissions, check_reliability

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "window": {
    "start": "2026-08-22",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 8
    },
    "reporting_hospitals_latest": 55,
    "reporting_threshold": 40,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 5,
      "flagged_anomalous": 3
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 33,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 29,
      "Low": 3,
      "High": 1
    },
    "sites_reduced_participation": 5,
    "anomalous_site_weeks": 20
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-12, 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 30,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 33,
      "interval_50": [
        26,
        38
      ],
      "interval_95": [
        10,
        65
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 38,
      "interval_50": [
        27,
        49
      ],
      "interval_95": [
        10,
        97
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 32,
      "interval_50": [
        22,
        67
      ],
      "interval_95": [
        7,
        234
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 52,
      "interval_50": [
        26,
        81
      ],
      "interval_95": [
        8,
        341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N08

**Question:** What are influenza hospital admissions in Utah expected to be over the next four weeks, and how much can I trust that?

**Numbers to review:** 2025.0, 2026.0

**Answer:**

Based on a model forecast, influenza hospital admissions in Utah are expected to be as follows for the next four weeks:

*   **2026-10-17:** Median of **33** (95% interval: 10-65)
*   **2026-10-24:** Median of **38** (95% interval: 10-97)
*   **2026-10-31:** Median of **32** (95% interval: 7-234)
*   **2026-11-07:** Median of **52** (95% interval: 8-341)

### Reliability and Trustworthiness
To determine how much you can trust these numbers, consider the following:

**1. Model Accuracy**
This is a model forecast using LightGBM quantile regression. In backtests conducted from April 2025 to July 2026, the 95% intervals contained the actual reported value **90.2%** of the time.

**2. Data Quality (Hospital Data)**
The forecast is based on the most recent reported data, which are often first reports and subject to revision. However, the current hospital data for Utah appears reliable:
*   **Reporting Volume:** As of the latest week (2026-10-10), 55 hospitals were reporting, which is above the state's minimum threshold of 40.
*   **Consistency:** There were no weeks with reduced participation flagged in the recent window.

**3. Other Indicators**
While hospital data is stable, other surveillance sources show some volatility:
*   **ED Visits:** Three of the last eight weeks were flagged as anomalous, with unusually large changes in smoothed percentages between September 12 and September 26, 2026.
*   **Wastewater:** Data is available from 33 sites, though 5 sites had reduced participation and 20 site-weeks were flagged as anomalous. Note that wastewater data for influenza in Utah only covers Influenza A.

Sources: forecast_admissions, check_reliability

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "window": {
    "start": "2026-08-22",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 8
    },
    "reporting_hospitals_latest": 55,
    "reporting_threshold": 40,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 8,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 5,
      "flagged_anomalous": 3
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 33,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 29,
      "Low": 3,
      "High": 1
    },
    "sites_reduced_participation": 5,
    "anomalous_site_weeks": 20
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-12, 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 30,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 33,
      "interval_50": [
        26,
        38
      ],
      "interval_95": [
        10,
        65
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 38,
      "interval_50": [
        27,
        49
      ],
      "interval_95": [
        10,
        97
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 32,
      "interval_50": [
        22,
        67
      ],
      "interval_95": [
        7,
        234
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 52,
      "interval_50": [
        26,
        81
      ],
      "interval_95": [
        8,
        341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N09

**Question:** Where are COVID-19 hospital admissions in Georgia headed over the next month?

**Numbers to review:** 70.0

**Answer:**

Based on the latest available data (week ending 2026-10-10) and the forecast, COVID-19 hospital admissions in Georgia are expected to continue a downward trend over the next month:

| Week ending (Saturday) | Median admissions | 95 % confidence interval |
|------------------------|-------------------|---------------------------|
| 2026-10-17 | 76 | [51 - 119] |
| 2026-10-24 | 72 | [44 - 140] |
| 2026-10-31 | 72 | [30 - 161] |
| 2026-11-07 | 69 | [32 - 190] |

**Key details**

* **Last reported value:** 84 admissions (week 2026-10-10).  
* **Trend:** The median forecast shows a steady decline from 84 to 69 admissions over the four-week period.  
* **Reliability:** The hospital-admission data for the most recent four weeks (2026-09-19 to 2026-10-10) are fully reliable: all weeks are flagged “observed_valid,” and the number of reporting hospitals (113) exceeds the state threshold (91). No weeks showed reduced participation or other data-quality issues.

**Caveats**

* The forecast is a model-based projection (LightGBM quantile regression) and should not be treated as a definitive count.  
* The 95 % intervals are wide, reflecting the inherent uncertainty in the forecast, but they indicate that admissions are unlikely to exceed 190 and are likely to remain above 32 during this period.  
* The back-test shows the 95 % intervals captured the actual reported values 90.2 % of the time, suggesting the model performs as expected.

**Bottom line:** Georgia’s COVID-19 hospital admissions are forecast to fall to around 70 admissions by early November, with the current reporting data being of high quality.

**Sources:** `forecast_admissions`, `check_reliability`

**Tool outputs:**

<details><summary>check_reliability({"end": "2026-10-10", "pathogen": "covid", "state": "GA", "weeks": 4})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 113,
    "reporting_threshold": 91,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "latest_trend": "Decreasing"
  },
  "wastewater": {
    "sites_with_data": 25,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 3,
      "Low": 3,
      "Moderate": 3,
      "High": 4,
      "Very High": 7
    },
    "sites_reduced_participation": 2,
    "anomalous_site_weeks": 10
  },
  "caveats": []
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "covid", "state": "GA"})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 84,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 76,
      "interval_50": [
        67,
        88
      ],
      "interval_95": [
        51,
        119
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 72,
      "interval_50": [
        60,
        86
      ],
      "interval_95": [
        44,
        140
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 72,
      "interval_50": [
        55,
        89
      ],
      "interval_95": [
        30,
        161
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 69,
      "interval_50": [
        55,
        93
      ],
      "interval_95": [
        32,
        190
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N10

**Question:** What are influenza hospital admissions in Utah expected to be over the next four weeks, and how much can I trust that?

**Numbers to review:** 0.71, 90.0

**Answer:**

**Influenza hospital admissions forecast for Utah (UT)**  

| Week ending (Saturday) | Median forecast | 50 % interval (lower-upper) | 95 % interval (lower-upper) |
|------------------------|----------------|-----------------------------|-----------------------------|
| 2026-10-17 | 33 | 26 - 38 | 10 - 65 |
| 2026-10-24 | 38 | 27 - 49 | 10 - 97 |
| 2026-10-31 | 32 | 22 - 67 | 7 - 234 |
| 2026-11-07 | 52 | 26 - 81 | 8 - 341 |

*These values are produced by a LightGBM quantile-regression model (15 leaves, learning-rate 0.03) that was selected on a development set in the CDC B1 benchmark.*

**Model back-test performance**  
- Relative weighted interval score (WIS) vs. a persistence baseline: **0.712** (95 % CI 0.666 - 0.755).  
- 50 % interval coverage: **47.5 %** (close to the nominal 50 %).  
- 95 % interval coverage: **90.2 %** (slightly below the nominal 95 %).  

**Reliability of the recent hospital data that the forecast builds on**  

- The most recent 4 weeks (2026-09-19 to 2026-10-10) all have **valid observed flags** for hospital admissions.  
- Reporting hospitals in the latest week: **55**, which exceeds the state’s threshold of **40** (so counts are not under-reported due to insufficient participation).  
- No weeks in this window show reduced hospital participation.  

**Other surveillance streams (for context)**  

- Emergency-department (ED) visits: 2 weeks flagged as anomalous (large changes on 2026-09-19 and 2026-09-26).  
- Wastewater: 33 sites reporting; 5 sites had reduced participation, and 12 site-weeks were flagged anomalous. Wastewater influenza data cover only influenza A.  

**Interpretation / trust level**  

- Hospital admission data for the recent period are fully flagged as valid and meet reporting thresholds, giving a solid foundation for the forecast.  
- The model’s back-test shows good overall skill (WIS ≈ 0.71 of persistence) and the 95 % intervals captured the true values about 90 % of the time in historical tests, indicating reasonable uncertainty quantification.  
- The presence of a few anomalous weeks in the ED stream and some reduced participation in wastewater sites does not directly affect the hospital admission forecast, but it signals that other surveillance signals are noisier this season.  

**Bottom line:** The median forecast suggests modest influenza hospital admissions in Utah over the next month (≈ 30-50 admissions per week), with fairly wide 95 % intervals reflecting uncertainty, especially for the later weeks. The underlying hospital data are reliable, and the model has demonstrated solid predictive performance, so the forecasts can be trusted as a useful guide while acknowledging the inherent uncertainty.  

*Sources: forecast_admissions (influenza, UT), check_reliability (influenza, UT).*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "UT", "weeks": 4})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 55,
    "reporting_threshold": 40,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 2,
      "observed_valid": 2
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 33,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 29,
      "Low": 3,
      "High": 1
    },
    "sites_reduced_participation": 5,
    "anomalous_site_weeks": 12
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 30,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 33,
      "interval_50": [
        26,
        38
      ],
      "interval_95": [
        10,
        65
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 38,
      "interval_50": [
        27,
        49
      ],
      "interval_95": [
        10,
        97
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 32,
      "interval_50": [
        22,
        67
      ],
      "interval_95": [
        7,
        234
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 52,
      "interval_50": [
        26,
        81
      ],
      "interval_95": [
        8,
        341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N11

**Question:** Which state is forecast to have more influenza hospital admissions over the next four weeks, New York or Pennsylvania?

**Numbers to review:** 988.0, 1253.0, 1253.0, 988.0

**Answer:**

**Forecasted median influenza hospital admissions (next 4 weeks)**  

| State | Week 1 (2026-10-17) | Week 2 (2026-10-24) | Week 3 (2026-10-31) | Week 4 (2026-11-07) | **4-week total (median)** |
|-------|-------------------|-------------------|-------------------|-------------------|---------------------------|
| New York (NY) | 190 | 242 | 203 | 353 | **988** |
| Pennsylvania (PA) | 255 | 312 | 270 | 416 | **1 253** |

**Result:** Pennsylvania is forecast to have more influenza hospital admissions than New York over the next four weeks (median total 1 253 vs 988).

**Model performance (same for both states)**  
* LightGBM quantile-regression model (leaves 15, learning rate 0.03).  
* Back-test (forecast dates 2025-04-04 to 2026-07-24, 69 Fridays):  
  * Relative weighted interval score vs. persistence = 0.712 (95 % CI 0.666 - 0.755).  
  * 95 % prediction intervals covered the observed value 90.2 % of the time.

**Data reliability caveats (latest 4 weeks, 2026-09-19 to 2026-10-10)**  

*Hospital admissions* - both states have **observed-valid flags for all 4 weeks** and meet the reporting-hospital thresholds (NY 172 ≥ 125; PA 193 ≥ 150). No weeks with reduced participation.

*ED visits* - each state shows some anomalous weeks (NY 2 weeks, PA 3 weeks) and unusually large changes in smoothed percent; however, hospital admission values themselves are not flagged.

*Wastewater* - both states have many sites reporting, but a subset shows reduced participation (NY 12 sites, PA 6 sites) and anomalous weeks (NY 14 site-weeks, PA 3 site-weeks). Wastewater data cover influenza A only.

Overall, the hospital-admission series that the forecast is based on are **fully valid** for the recent period; the noted ED and wastewater anomalies do not affect the admission forecasts.

**Answer:** Pennsylvania is forecast to experience higher influenza hospital admissions than New York over the next four weeks.

**Sources:** forecast_admissions (NY), forecast_admissions (PA), check_reliability (NY), check_reliability (PA)

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "NY", "weeks": 4})</summary>

```
{
  "state": "NY",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 172,
    "reporting_threshold": 125,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 2,
      "observed_valid": 2
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 77,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 55,
      "Low": 4
    },
    "sites_reduced_participation": 12,
    "anomalous_site_weeks": 14
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>check_reliability({"pathogen": "influenza", "state": "PA", "weeks": 4})</summary>

```
{
  "state": "PA",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 193,
    "reporting_threshold": 150,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 1,
      "flagged_anomalous": 3
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 31,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 11,
      "Low": 1
    },
    "sites_reduced_participation": 6,
    "anomalous_site_weeks": 3
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-26, 2026-10-03, 2026-10-10.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "NY"})</summary>

```
{
  "state": "NY",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 163,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 190,
      "interval_50": [
        164,
        220
      ],
      "interval_95": [
        105,
        309
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 242,
      "interval_50": [
        181,
        284
      ],
      "interval_95": [
        87,
        492
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 203,
      "interval_50": [
        163,
        396
      ],
      "interval_95": [
        49,
        927
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 353,
      "interval_50": [
        251,
        478
      ],
      "interval_95": [
        60,
        1341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "PA"})</summary>

```
{
  "state": "PA",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 238,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 255,
      "interval_50": [
        234,
        315
      ],
      "interval_95": [
        147,
        368
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 312,
      "interval_50": [
        250,
        342
      ],
      "interval_95": [
        120,
        466
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 270,
      "interval_50": [
        211,
        419
      ],
      "interval_95": [
        72,
        710
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 416,
      "interval_50": [
        315,
        526
      ],
      "interval_95": [
        83,
        947
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N12

**Question:** Forecast influenza hospital admissions for the Greenville area of South Carolina over the next four weeks.

**Numbers to review:** 90.0

**Answer:**

**Influenza hospital-admission forecast for South Carolina (state-level)**  

| Forecast week (Saturday) | Weeks after last reported week | Median forecast | 50 % interval (Q25-Q75) | 95 % interval (Q2.5-Q97.5) |
|--------------------------|--------------------------------|----------------|------------------------|----------------------------|
| 2026-10-17 | 1 | 60 | 50 - 67 | 23 - 117 |
| 2026-10-24 | 2 | 75 | 54 - 87 | 21 - 188 |
| 2026-10-31 | 3 | 64 | 43 - 129 | 14 - 420 |
| 2026-11-07 | 4 | 102 | 65 - 152 | 16 - 609 |

*The forecast is produced by a LightGBM quantile-regression model (15 leaves, learning-rate 0.03).*

**Model back-test performance (forecast dates 2025-04-04 to 2026-07-24, 69 Fridays)**  

* Relative weighted interval score vs. a persistence baseline: **0.712** (95 % CI 0.666 - 0.755) - lower is better.  
* 50 % interval coverage: **47.5 %** (the interval contains the observed value about half the time).  
* 95 % interval coverage: **90.2 %** (the interval contains the observed value in > 90 % of weeks).

**Reliability caveats for the most recent data (weeks 2026-09-19 to 2026-10-10)**  

* Hospital admissions: 4 weeks of data, all flagged **observed_valid**; 70 hospitals reported (threshold = 50). No weeks with reduced participation.  
* Emergency-department (ED) visits: 4 weeks of data; 3 weeks flagged **anomalous** (large changes on 2026-09-19, 2026-09-26, 2026-10-03). Only 1 week flagged valid.  
* Wastewater: 24 sites reported; 20 sites in “Very Low” category, 3 in “Very High”. 2 sites showed reduced participation and 3 site-weeks were flagged anomalous. Wastewater influenza data cover influenza A only.

**Note on the Greenville area**  
The forecasting tool provides state-level forecasts only; it does not generate separate forecasts for individual Hospital Service Areas (HSAs) such as the Greenville HSA. The numbers above represent the best available projection for the entire state of South Carolina. Local patterns in Greenville may differ from the state average.

**Sources**: forecast_admissions (SC influenza), check_reliability (SC influenza)

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "SC", "weeks": 4})</summary>

```
{
  "state": "SC",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 70,
    "reporting_threshold": 50,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 3,
      "observed_valid": 1
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 24,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 20,
      "Very High": 3
    },
    "sites_reduced_participation": 2,
    "anomalous_site_weeks": 3
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26, 2026-10-03.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "SC"})</summary>

```
{
  "state": "SC",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 51,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 60,
      "interval_50": [
        50,
        67
      ],
      "interval_95": [
        23,
        117
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 75,
      "interval_50": [
        54,
        87
      ],
      "interval_95": [
        21,
        188
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 64,
      "interval_50": [
        43,
        129
      ],
      "interval_95": [
        14,
        420
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 102,
      "interval_50": [
        65,
        152
      ],
      "interval_95": [
        16,
        609
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N13

**Question:** Forecast COVID-19 hospital admissions in Illinois for each of the next eight weeks.

**Numbers to review:** 5.0, 8.0

**Answer:**

**COVID-19 Hospital Admissions Forecast - Illinois**

| Week ending (Saturday) | Weeks after last reported | Median forecast | 95 % prediction interval (low - high) |
|------------------------|---------------------------|----------------|--------------------------------------|
| 2026-10-17 | 1 | 78 | 43 - 119 |
| 2026-10-24 | 2 | 81 | 33 - 142 |
| 2026-10-31 | 3 | 82 | 27 - 180 |
| 2026-11-07 | 4 | 85 | 31 - 217 |

**Model & Back-test performance**  
*Model*: LightGBM quantile regression (15 leaves, learning-rate 0.03) - the model selected on the B1 benchmark.  
*Back-test period*: 2025-04-04 to 2026-07-24 (69 forecast dates).  
*Relative weighted interval score vs. a persistence baseline*: **0.712** (95 % CI 0.666 - 0.755).  
*Coverage*: 50 % interval covered the observed value 47.5 % of the time; 95 % interval coverage was 90.2 %.

**Data reliability (hospital admissions)** - Illinois, COVID-19, recent 4-week window (2026-09-19 to 2026-10-10)  

- All 4 weeks have **observed_valid** flags (no data-quality flags).  
- Reporting hospitals = 157, which exceeds the required threshold of 109.  
- No weeks with reduced participation or other caveats were identified.  

*Note*: The forecast starts from the latest reported week (2026-10-10, value = 78). Those “first-report” values are often revised, so the forecast inherits that uncertainty.

**Limitation** - The forecasting tool provides up to 4 weeks ahead. Forecasts for weeks 5-8 are not available from the current CDC model.

**Sources**: forecast_admissions (COVID-19, IL), check_reliability (IL, covid)

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "covid", "state": "IL", "weeks": 4})</summary>

```
{
  "state": "IL",
  "pathogen": "covid",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 157,
    "reporting_threshold": 109,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "latest_trend": "No Change"
  },
  "wastewater": {
    "sites_with_data": 76,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 49,
      "Low": 19,
      "Moderate": 3,
      "High": 1,
      "Very High": 1
    },
    "sites_reduced_participation": 10,
    "anomalous_site_weeks": 16
  },
  "caveats": []
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "COVID-19", "state": "IL"})</summary>

```
pathogen must be one of covid, influenza, rsv
```

</details>

<details><summary>forecast_admissions({"pathogen": "covid", "state": "IL"})</summary>

```
{
  "state": "IL",
  "pathogen": "covid",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 78,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 78,
      "interval_50": [
        66,
        90
      ],
      "interval_95": [
        43,
        119
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 81,
      "interval_50": [
        61,
        103
      ],
      "interval_95": [
        33,
        142
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 82,
      "interval_50": [
        66,
        97
      ],
      "interval_95": [
        27,
        180
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 85,
      "interval_50": [
        63,
        113
      ],
      "interval_95": [
        31,
        217
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N14

**Question:** Where are COVID-19 hospital admissions in Georgia headed over the next month?

**Numbers to review:** 70.0

**Answer:**

**COVID-19 Hospital Admissions Forecast for Georgia (next ≈ 4 weeks)**  

| Week ending (Saturday) | Median forecast | 50 % interval (low-high) | 95 % interval (low-high) |
|------------------------|----------------|--------------------------|--------------------------|
| 2026-10-17 | 76 | 67 - 88 | 51 - 119 |
| 2026-10-24 | 72 | 60 - 86 | 44 - 140 |
| 2026-10-31 | 72 | 55 - 89 | 30 - 161 |
| 2026-11-07 | 69 | 55 - 93 | 32 - 190 |

*The latest reported week (2026-10-10) had 84 admissions.*

**Model & Back-test performance**  
- LightGBM quantile-regression model (15 leaves, learning-rate 0.03).  
- Back-test (2025-04-04 → 2026-07-24, 69 forecast dates):  
  * Relative Weighted Interval Score vs. persistence: **0.712** (95 % CI 0.666 - 0.755).  
  * 50 % interval coverage: **47.5 %** (below nominal).  
  * 95 % interval coverage: **90.2 %** (close to nominal).  

**Data reliability for the recent period (2026-09-19 → 2026-10-10)**  
- Hospital admissions: 4 weeks of data, all flagged **observed_valid**.  
- Reporting hospitals = 113, exceeding the required threshold of 91 (no reduced-participation weeks).  
- No additional caveats were flagged for hospital data.  

**Interpretation**  
The model projects a modest decline from the most recent 84 admissions to a median of about 70-76 admissions per week over the next month, with fairly wide uncertainty-especially at the 95 % level-reflecting typical variability in weekly reporting. The underlying hospital data for the recent weeks are complete and meet reporting thresholds, so the forecast rests on a solid recent data foundation.

*Sources: forecast_admissions (v2.0.0+2026-10-16), check_reliability*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "covid", "state": "GA", "weeks": 4})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 113,
    "reporting_threshold": 91,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "latest_trend": "Decreasing"
  },
  "wastewater": {
    "sites_with_data": 25,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 3,
      "Low": 3,
      "Moderate": 3,
      "High": 4,
      "Very High": 7
    },
    "sites_reduced_participation": 2,
    "anomalous_site_weeks": 10
  },
  "caveats": []
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "COVID-19", "state": "GA"})</summary>

```
pathogen must be one of covid, influenza, rsv
```

</details>

<details><summary>forecast_admissions({"pathogen": "covid", "state": "GA"})</summary>

```
{
  "state": "GA",
  "pathogen": "covid",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 84,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 76,
      "interval_50": [
        67,
        88
      ],
      "interval_95": [
        51,
        119
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 72,
      "interval_50": [
        60,
        86
      ],
      "interval_95": [
        44,
        140
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 72,
      "interval_50": [
        55,
        89
      ],
      "interval_95": [
        30,
        161
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 69,
      "interval_50": [
        55,
        93
      ],
      "interval_95": [
        32,
        190
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N15

**Question:** Which state is forecast to have more influenza hospital admissions over the next four weeks, New York or Pennsylvania?

**Numbers to review:** 988.0, 1253.0, 1253.0, 988.0, 90.0

**Answer:**

**Forecasted median influenza hospital admissions (next 4 weeks)**  

| State | Median weekly forecasts | Total median over 4 weeks |
|-------|------------------------|---------------------------|
| New York | 190  (2026-10-17)  <br>242  (2026-10-24)  <br>203  (2026-10-31)  <br>353  (2026-11-07) | **988** |
| Pennsylvania | 255  (2026-10-17)  <br>312  (2026-10-24)  <br>270  (2026-10-31)  <br>416  (2026-11-07) | **1 253** |

**Answer:** Pennsylvania is forecast to have more influenza hospital admissions than New York over the next four weeks (median total 1 253 vs 988).

**Reliability caveats** (hospital-admission data)  
* New York - all 4 recent weeks have the flag **observed_valid**; 172 hospitals reported (threshold 125). No weeks of reduced participation.  
* Pennsylvania - all 4 recent weeks have the flag **observed_valid**; 193 hospitals reported (threshold 150). No weeks of reduced participation.  

Thus the hospital-admission series that the forecasts are built on are considered reliable for both states.

**Model information** (same for both states)  
* Model: LightGBM quantile regression (leaves 15, learning rate 0.03).  
* Back-test (2025-04-04 to 2026-07-24): relative weighted interval score vs. persistence = 0.712 (95 % CI 0.666 - 0.755).  
* 95 % prediction-interval coverage in back-test ≈ 90 %.

**Conclusion:** Based on the CDC’s forecast model, Pennsylvania is expected to experience a higher number of influenza hospital admissions than New York in the coming four weeks, and the underlying hospital-admission data for both states are flagged as valid with sufficient reporting coverage.

**Sources:** forecast_admissions (NY), forecast_admissions (PA), check_reliability (NY), check_reliability (PA)

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "NY", "weeks": 4})</summary>

```
{
  "state": "NY",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 172,
    "reporting_threshold": 125,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 2,
      "observed_valid": 2
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 77,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 55,
      "Low": 4
    },
    "sites_reduced_participation": 12,
    "anomalous_site_weeks": 14
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>check_reliability({"pathogen": "influenza", "state": "PA", "weeks": 4})</summary>

```
{
  "state": "PA",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 193,
    "reporting_threshold": 150,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 1,
      "flagged_anomalous": 3
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 31,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 11,
      "Low": 1
    },
    "sites_reduced_participation": 6,
    "anomalous_site_weeks": 3
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-26, 2026-10-03, 2026-10-10.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "NY"})</summary>

```
{
  "state": "NY",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 163,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 190,
      "interval_50": [
        164,
        220
      ],
      "interval_95": [
        105,
        309
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 242,
      "interval_50": [
        181,
        284
      ],
      "interval_95": [
        87,
        492
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 203,
      "interval_50": [
        163,
        396
      ],
      "interval_95": [
        49,
        927
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 353,
      "interval_50": [
        251,
        478
      ],
      "interval_95": [
        60,
        1341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "PA"})</summary>

```
{
  "state": "PA",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 238,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 255,
      "interval_50": [
        234,
        315
      ],
      "interval_95": [
        147,
        368
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 312,
      "interval_50": [
        250,
        342
      ],
      "interval_95": [
        120,
        466
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 270,
      "interval_50": [
        211,
        419
      ],
      "interval_95": [
        72,
        710
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 416,
      "interval_50": [
        315,
        526
      ],
      "interval_95": [
        83,
        947
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>

## N16

**Question:** What are influenza hospital admissions in Utah expected to be over the next four weeks, and how much can I trust that?

**Numbers to review:** 2025.0, 2026.0

**Answer:**

**Influenza hospital admissions forecast for Utah (next 4 weeks)**  

| Week ending (Saturday) | Median forecast | 95 % prediction interval (low - high) |
|------------------------|----------------|---------------------------------------|
| 2026-10-17 | **33** admissions | 10 - 65 |
| 2026-10-24 | **38** admissions | 10 - 97 |
| 2026-10-31 | **32** admissions | 7 - 234 |
| 2026-11-07 | **52** admissions | 8 - 341 |

**Model & back-test performance**  
* Model: LightGBM quantile regression (15 leaves, learning-rate 0.03).  
* Back-test (April 2025 - July 2026, 69 forecast dates):  
  * Relative weighted interval score vs. a persistence baseline: **0.712** (95 % CI 0.666 - 0.755).  
  * 95 % interval coverage in back-test: **90.2 %** (the intervals contained the observed value about nine times out of ten).  

**Reliability of the underlying recent hospital data** (checked for the most recent 4 weeks, 2026-09-19 to 2026-10-10):

* All 4 weeks have **valid** hospital-admission flags.  
* Reporting hospitals in the latest week: **55**, which exceeds the state’s threshold of **40** (so counts are not under-reported due to insufficient participation).  
* No weeks flagged for reduced participation.  

**Caveats**

* The forecast starts from the latest reported week (2026-10-10). Those first-report values are often revised, so the forecast inherits any future revisions.  
* ED visit data for the same period show two weeks flagged as anomalous, but this does not affect the hospital-admission series used for the forecast.  
* Wastewater influenza data (influenza A only) are available from 33 sites, with a few sites showing reduced participation or anomalous weeks, but these do not influence the hospital-admission forecast.  

**Bottom line:** The median forecasts suggest modest influenza hospital admissions in Utah over the next month, with relatively wide 95 % intervals reflecting uncertainty. The recent hospital data meet reporting thresholds and have no flagged participation issues, giving a solid foundation for the forecast, though future revisions to the latest week’s data could shift the predictions slightly.  

*Sources: forecast_admissions, check_reliability*

**Tool outputs:**

<details><summary>check_reliability({"pathogen": "influenza", "state": "UT", "weeks": 4})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "window": {
    "start": "2026-09-19",
    "end": "2026-10-10"
  },
  "hospital_admissions": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "observed_valid": 4
    },
    "reporting_hospitals_latest": 55,
    "reporting_threshold": 40,
    "weeks_reduced_participation": []
  },
  "ed_visits": {
    "weeks_with_data": 4,
    "last_week": "2026-10-10",
    "flag_counts": {
      "flagged_anomalous": 2,
      "observed_valid": 2
    },
    "latest_trend": "Increasing"
  },
  "wastewater": {
    "sites_with_data": 33,
    "last_week": "2026-10-10",
    "latest_week_categories": {
      "Very Low": 29,
      "Low": 3,
      "High": 1
    },
    "sites_reduced_participation": 5,
    "anomalous_site_weeks": 12
  },
  "caveats": [
    "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26.",
    "Wastewater influenza covers influenza A only."
  ]
}
```

</details>

<details><summary>forecast_admissions({"pathogen": "influenza", "state": "UT"})</summary>

```
{
  "state": "UT",
  "pathogen": "influenza",
  "measure": "hospital_admission_count",
  "data_release": "v2.0.0+2026-10-16",
  "last_reported_week": "2026-10-10",
  "last_reported_value": 30,
  "forecasts": [
    {
      "week": "2026-10-17",
      "weeks_after_last_reported": 1,
      "median": 33,
      "interval_50": [
        26,
        38
      ],
      "interval_95": [
        10,
        65
      ]
    },
    {
      "week": "2026-10-24",
      "weeks_after_last_reported": 2,
      "median": 38,
      "interval_50": [
        27,
        49
      ],
      "interval_95": [
        10,
        97
      ]
    },
    {
      "week": "2026-10-31",
      "weeks_after_last_reported": 3,
      "median": 32,
      "interval_50": [
        22,
        67
      ],
      "interval_95": [
        7,
        234
      ]
    },
    {
      "week": "2026-11-07",
      "weeks_after_last_reported": 4,
      "median": 52,
      "interval_50": [
        26,
        81
      ],
      "interval_95": [
        8,
        341
      ]
    }
  ],
  "model": "LightGBM quantile regression (leaves 15, learning rate 0.03), chosen on dev in the B1 benchmark",
  "backtest": {
    "forecast_dates": "2025-04-04 to 2026-07-24 (69 Fridays)",
    "data": "as published on each date",
    "relative_wis_vs_persistence": 0.712,
    "relative_wis_ci95": [
      0.666,
      0.755
    ],
    "coverage_50_interval_percent": 47.5,
    "coverage_95_interval_percent": 90.2
  },
  "notes": [
    "The forecast starts from the latest reported weeks, which are first reports and are often revised.",
    "Intervals are model quantiles; in the backtest the 95% intervals held the reported value 90.2% of the time."
  ]
}
```

</details>
