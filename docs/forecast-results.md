# Full B1 benchmark: test results

Plan: [`forecast-eval.md`](forecast-eval.md), frozen 2026-11-09, with the changes recorded there after freezing (the quantile cap and the dev choices, 2026-11-10, before any test forecast). Analysis: `eval/forecast-b1/analysis.json`, produced by `python -m resplens.forecast.bench_analyze`.

## Setup

- 51 locations, COVID-19, influenza and RSV, NHSN weekly hospital admissions; 69 forecast dates (Fridays 2025-04-04 to 2026-07-24); four target weeks per date, fixed by the calendar; 23 quantiles.
- Each model was run on the real-time data (as published on the forecast date) and on the revised data (the pinned release cut at the same last week), and scored against the pinned release up to 2026-08-15.
- Settings were chosen on dev (2022-10-07 to 2025-03-07) and fixed in the plan before any test forecast. All test runs started at commit `fa66ee2`; the ensemble was built at `f35f1b5` from those runs. Every run finished with no errors.
- Every quantile is capped at 5 times the largest value in that series' input (plan change of 2026-11-10). All results below use capped forecasts unless marked uncapped.
- **Rows**: 42,216 scored rows per model and version. Seasonal naive fell back to persistence on 640 real-time and 784 revised rows (no value a year earlier); as planned, those rows are removed for every system, leaving 41,576 real-time and 41,432 revised rows. No other model fell back.
- Relative WIS is a model's mean WIS over persistence's on the same rows, pooled over pathogens; the 95% interval is a block bootstrap over forecast dates (10,000 resamples). "Better" means the interval lies entirely below 1. Nine comparisons, no correction for multiplicity.

## Primary result (real-time data)

| System | Relative WIS [95% CI] | Verdict | Relative MAE | 50% cov. | 95% cov. |
|---|---|---|---|---|---|
| LightGBM | 0.712 [0.666, 0.755] | better | 0.732 | 0.475 | 0.902 |
| TabPFN v2 | 0.731 [0.627, 0.859] | better | 0.756 | 0.424 | 0.880 |
| Median ensemble | 0.740 [0.679, 0.812] | better | 0.784 | 0.522 | 0.960 |
| Chronos-2 | 0.787 [0.734, 0.853] | better | 0.837 | 0.416 | 0.978 |
| Chronos-2-Synth | 0.819 [0.736, 0.931] | better | 0.877 | 0.406 | 0.977 |
| ARIMA | 0.965 [0.940, 0.989] | better | 0.960 | 0.520 | 0.927 |
| ETS | 1.096 [0.933, 1.307] | no detectable difference | 1.124 | 0.520 | 0.932 |
| Seasonal naive | 2.898 [1.891, 4.277] | worse | 3.052 | 0.494 | 0.910 |
| Persistence | 1 (mean WIS 26.6) | | 1 | 0.435 | 0.935 |

- Six of the eight systems beat persistence. LightGBM, TabPFN v2 and the ensemble are within each other's intervals; the point estimates order them as listed.
- ARIMA's gain is small (3.5%) and its interval's upper end is 0.989; with nine uncorrected comparisons it is the weakest of the "better" verdicts.
- The ensemble did not beat its best member (LightGBM 0.712 against 0.740), but it has the best-calibrated intervals (50% coverage 0.522, 95% coverage 0.960).
- Persistence's 50% intervals are too narrow (coverage 0.435), and so are those of TabPFN v2 (0.424) and both Chronos-2 models (0.416, 0.406). The Chronos-2 models' 95% intervals are wide (0.978, 0.977); TabPFN v2's are too narrow (0.880).

## Revised data and the revision effect

On revised data the ranking by mean WIS is the same as on real-time data: LightGBM, TabPFN v2, ensemble, Chronos-2, Chronos-2-Synth, ARIMA, persistence, ETS, seasonal naive.

| System | Relative WIS, revised [95% CI] | Revision effect (revised minus real time) [95% CI] |
|---|---|---|
| LightGBM | 0.668 [0.618, 0.715] | -0.044 [-0.063, -0.028], revised better |
| TabPFN v2 | 0.711 [0.596, 0.847] | -0.020 [-0.052, 0.008], no detectable difference |
| Median ensemble | 0.721 [0.650, 0.801] | -0.019 [-0.034, -0.005], revised better |
| Chronos-2 | 0.761 [0.700, 0.835] | -0.027 [-0.044, -0.011], revised better |
| Chronos-2-Synth | 0.793 [0.698, 0.914] | -0.027 [-0.050, -0.005], revised better |
| ARIMA | 0.966 [0.939, 0.993] | +0.001 [-0.005, 0.008], no detectable difference |
| ETS | 1.127 [0.945, 1.347] | +0.031 [0.007, 0.058], revised worse |
| Seasonal naive | 2.946 [1.927, 4.310] | +0.048 [-0.051, 0.128], no detectable difference |

- A backtest on revised data flatters LightGBM by 4.4 points of relative WIS and Chronos-2 by 2.7; it changes nothing for ARIMA and makes ETS look worse. The effect is measured against persistence on the same data version, and persistence itself scores worse on revised data (mean WIS 27.3 against 26.6), as it did in B1a.
- The revision effect compares each version on its own rows (41,576 and 41,432); the two sets differ only in the seasonal-naive fallback rows.

## Secondary measures (real-time data)

### By pathogen (relative WIS, point estimates)

| System | COVID-19 | Influenza | RSV |
|---|---|---|---|
| LightGBM | 0.680 | 0.681 | 0.890 |
| TabPFN v2 | 0.724 | 0.689 | 0.904 |
| Median ensemble | 0.760 | 0.735 | 0.718 |
| Chronos-2 | 0.875 | 0.723 | 0.855 |
| Chronos-2-Synth | 0.819 | 0.806 | 0.870 |
| ARIMA | 0.949 | 0.962 | 1.008 |
| ETS | 1.013 | 1.166 | 1.003 |
| Seasonal naive | 5.125 | 1.783 | 2.602 |

On RSV the ensemble (0.718) is better than every member.

### By target week (relative WIS [95% CI])

| System | Week 1 | Week 2 | Week 3 | Week 4 |
|---|---|---|---|---|
| LightGBM | 0.792 [0.745, 0.843] | 0.743 [0.696, 0.793] | 0.704 [0.649, 0.757] | 0.663 [0.600, 0.724] |
| TabPFN v2 | 0.734 [0.647, 0.830] | 0.695 [0.589, 0.831] | 0.716 [0.592, 0.869] | 0.766 [0.621, 0.935] |
| Median ensemble | 0.805 [0.761, 0.861] | 0.766 [0.711, 0.833] | 0.732 [0.662, 0.813] | 0.703 [0.622, 0.796] |
| Chronos-2 | 0.917 [0.846, 1.018] | 0.830 [0.772, 0.909] | 0.769 [0.707, 0.845] | 0.719 [0.658, 0.786] |
| ARIMA | 0.993 [0.960, 1.031] | 0.976 [0.947, 1.008] | 0.963 [0.936, 0.988] | 0.948 [0.917, 0.973] |

Gains over persistence grow with the horizon for LightGBM, the ensemble, Chronos-2 and ARIMA; TabPFN v2's are about flat (best at week 2). Chronos-2's week-1 gain and ARIMA's week-1 and week-2 gains are not detectable.

### Location-normalized relative WIS

Each state's WIS divided by its persistence WIS, then averaged over the 51 states: LightGBM 0.755, ensemble 0.762, Chronos-2 0.807, TabPFN v2 0.825, Chronos-2-Synth 0.840, ARIMA 0.970, ETS 1.104, seasonal naive 2.089. TabPFN v2 drops from second to fourth: its gain is concentrated in the large states. Per-state ratios are in the analysis file.

### Chronos-2-Synth against Chronos-2

Chronos-2-Synth, trained only on synthetic data, scores 1.040 [0.980, 1.103] relative to Chronos-2 on real-time data (1.042 [0.973, 1.110] revised): no detectable difference. Chronos-2's real-data pretraining did not give it a detectable advantage here, which is consistent with, but does not prove, the absence of a memorization effect.

### LightGBM with NSSP ED visits

From 2025-08-15 (50 forecast dates, 30,600 rows), adding ED-visit lags gives 0.955 [0.863, 1.077] relative to LightGBM on the same rows (0.968 [0.857, 1.119] revised): no detectable difference. Against persistence on those rows: LightGBM + ED 0.689 [0.613, 0.792], LightGBM 0.722 [0.673, 0.768].

## Sensitivity analyses

- **Uncapped forecasts**: relative WIS moves by at most 0.008 for every system except seasonal naive (2.898 capped, 4.826 uncapped). The cap matters for test only through seasonal naive; on dev it mattered for TabPFN v2 and Chronos-2.
- **Fallback rows kept** (seasonal naive's rows scored with persistence's forecast, all 42,216 rows): every relative WIS changes by at most 0.016 (seasonal naive; at most 0.003 for the others).

## Notes

- **Seasonal naive fails for a data reason.** Its worst rows are Texas COVID-19 forecasts made during the autumn 2025 data gap (forecasts of about 55,000 against 329 admissions). Its level adjustment divides the last four weeks by the same weeks a year earlier, and a year earlier Texas reported 4 to 15 COVID-19 admissions a week (August to early October 2024; probably voluntary NHSN reporting, requires verification). Its 14% of WIS in its top 10 rows contrasts with about 2-3% for the other models.
- **Dev pointed the same way.** With the cap, LightGBM had the lowest dev WIS on COVID-19 (49.6 against persistence's 53.5) and TabPFN v2 on influenza (41.1 against 52.1). The cap was added after the dev runs, so the dev numbers for TabPFN v2 and Chronos-2 depend on a change made with dev results in hand; it was fixed before any test forecast.
- **Persistence is a tuned baseline**: its window was chosen on dev like every model's settings.

## Limits

- One test period with one full respiratory season (2025-26); results may not hold for other seasons.
- Truth is the pinned release; weeks after 2026-08-15 are not scored.
- Nine comparisons with persistence without a multiplicity correction; ARIMA's interval comes closest to 1.
- RSV settings were not really tuned on dev (series shorter than 104 weeks, so the settings tied).
- TabPFN v2's synthetic-only pretraining and Chronos-2's listed training datasets are taken from their documentation, not checked independently.
- The 5x cap is a post-freeze change, chosen on dev; the uncapped results are reported above.

## Records

- Runs: `eval/forecast-b1/runs/*-test-*` (`config.json` and `removed.json` in git; forecasts and scores kept locally, see the plan's change of 2026-11-10).
- Dev selection: `eval/forecast-b1/dev-selection.json`.
- Analysis: `eval/forecast-b1/analysis.json`.
