# B1: real-time forecasting benchmark (pre-registration)

Status: **frozen 2026-11-09** (drafted 2026-11-05; implementation details reviewed by the author 2026-11-09). The first part of B1 is the LLM experiment in [`llm-forecast-eval.md`](llm-forecast-eval.md). Changes after freezing are added below with dates. Results: [`forecast-results.md`](forecast-results.md) (2026-11-10).

## Question

Weekly hospital admissions are revised after they are first published. A forecast made on a given day could only use the values published by then, but backtests usually take the latest, revised values. This benchmark asks two questions:

1. **Which forecasting methods beat a simple baseline when they see only the data that was available at the time?**
2. **How much does a backtest on revised data overstate accuracy, and does it change which method looks best?**

## What the data allow (checked 2026-11-05)

Revision history in the pinned release `v2.0.0+2026-10-16` (`metadata/release_assets.csv`, read through `Dataset.versions`). Each release contains the full series back to its first week, so the series as it stood on any release date can be rebuilt exactly.

| Source | Release dates in the history | Releases | Series starts |
|---|---|---|---|
| NHSN hospital admissions | 2025-04-04 to 2026-10-16 | 116 (47 preliminary, from 2025-11-19) | 2020-08-08 |
| NSSP ED visits | 2025-08-15 to 2026-10-14 | 54 | 2022-10-01 |
| NWSS wastewater | 2026-08-07 to 2026-10-16 | 11 | 2022-01-08 |

- Checked on South Carolina, Wyoming and the District of Columbia, which have identical release dates; all 51 locations have history files. The implementation checks every location.
- Gaps between consecutive NHSN releases longer than a week: 2025-06-27 to 07-07 (10 days), 2025-08-15 to 09-12 (two 14-day gaps), **2025-09-26 to 2025-11-14 (49 days)**, 2025-11-21 to 12-03 and 2025-12-19 to 12-31 (12 days each), 2026-06-24 to 07-02 (8 days). NSSP has a 54-day gap over the same autumn (2025-09-26 to 11-19). The long gap falls at the start of the 2025-26 season. Whether it coincides with the October 2025 federal government shutdown requires verification.
- A standard NHSN release usually ends with the week that ended 6 days earlier (65 of 71 standard releases in South Carolina).
- How much values change: for influenza admissions in the three states, the value in the first standard release differed from the value in the pinned release for 31-40% of weeks (17-22 of 55); 4 weeks after the week ended, 6-11% (4-7 of 65); 10 weeks after, 3-6% (2-4 of 65).
- NWSS history is too short (11 releases) to use as a real-time input; it is excluded.

## Forecast setup

- **Locations**: 50 states and DC.
- **Targets**: weekly NHSN hospital admissions for COVID-19, influenza, and RSV (state level).
- **Forecast dates**: every Friday from 2025-04-04. On each date, a model sees the latest release published on or before that date (preliminary or standard).
- **Horizons**: the 4 weeks ending 1, 8, 15, and 22 days after the forecast date (weeks end on Saturday). Horizons are fixed by the calendar, not by the last week in the data: when the data are stale (during the autumn 2025 gap), the model has to forecast further ahead, as a forecaster did at the time.
- **Output**: 23 quantiles (0.01, 0.025, 0.05, 0.10, ..., 0.95, 0.975, 0.99) and the median.
- **Truth**: values in the pinned release. Because about 3-6% of weeks still change 10 weeks after they end, only target weeks ending on or before **2026-08-15** (9 weeks before the last release) are scored. The last forecast date is therefore 2026-07-24.

## Two versions of the same backtest

For every forecast date, each model is run twice:

- **Real time (vintage)**: the series as published on the forecast date.
- **Revised (latest)**: the series from the pinned release, cut at **the same last week** as the vintage. Only the values differ, not the amount of data, so the difference between the two scores is the effect of revisions alone.

Both are scored against the same truth. The gap (revised score minus real-time score) is the optimism of a backtest that ignores revisions.

## Models

| Model | Inputs | Notes |
|---|---|---|
| Persistence (baseline) | target series | Median = last observed value; quantiles from past changes over the same horizon |
| Seasonal naive | target series | Same week one year earlier, scaled to the current level |
| ARIMA, ETS | target series | Automatic order selection per series |
| LightGBM (global) | lags of the target, all locations | One model per pathogen and horizon, quantile loss |
| LightGBM + ED visits | as above + NSSP ED percent | Only from 2025-08-15, when NSSP history starts; compared with LightGBM on the same dates |
| Chronos-2, zero-shot | target series | Time-series foundation model (decision 6); Chronos-2-Synth with the same settings as a sensitivity analysis |
| TabPFN v2, zero-shot | lags of the target as a table | A tabular foundation model used for regression on lag features; it returns a predictive distribution, from which the quantiles are read |
| Median ensemble | seasonal naive, ARIMA, ETS, LightGBM, Chronos-2, TabPFN v2 | Quantile-wise median; fixed in advance, not selected on test. Chronos-2-Synth (a sensitivity arm) and LightGBM + ED visits (fewer dates) are left out |

**Pretraining and the test period**: a pretrained model must not have seen the test period. Each one is used only if its training data, by its documentation, end before 2025-04-04, or are synthetic (TabPFN is trained on synthetic data, which requires verification); the check is recorded with the model's version.

All code is written for this repository. Nothing is reused from the FluSight or MetroCast competition models, and no forecasts are submitted to any hub.

The LLM-as-forecaster experiment is pre-registered separately in [`llm-forecast-eval.md`](llm-forecast-eval.md) and runs first.

## Metrics

- **Primary**: weighted interval score (WIS) of each model relative to persistence, on real-time data: the ratio of mean WIS over all locations, pathogens, forecast dates and horizons.
- **Secondary**: coverage of the 50% and 95% intervals; absolute error of the median; results by pathogen, horizon, and location; the revised-minus-real-time gap for each model, and whether the ranking of models changes between the two versions.
- WIS is computed on counts. Scale differs a lot between states, so results are also reported with each location's WIS divided by its persistence WIS before averaging.

## Analysis

- **Uncertainty**: forecasts for different locations on the same date are correlated, so intervals come from a block bootstrap over forecast dates (all locations, pathogens and horizons of a date resampled together), 10,000 resamples.
- **Model comparison**: relative WIS with its 95% interval; a model is called better than persistence only if the interval lies entirely below 1.
- **Revision effect**: for each model, the gap with its 95% interval (same bootstrap), and the rank of each model under both versions.
- One test period of about 16 months, containing one full respiratory season (2025-26). Results may not hold for other seasons; this is stated with the results.

## Dev and test

**Decision 1: what to tune on.** Choices made on dev: transformations (for example log), the window of past changes for persistence quantiles, LightGBM features and hyperparameters, the foundation model's context length.

- **(a) Recommended**: dev = forecast dates from 2022-10 to 2025-03 on the latest data, before any real-time history exists; test = all real-time forecast dates (2025-04-04 to 2026-07-24). Tuning never sees the test period. Dev scores use revised data and are therefore optimistic; they are used only to compare settings, never reported as results.
- (b) Dev = real-time dates 2025-04-04 to 2025-09-26; test = 2025-11-14 to 2026-07-24. Tuning uses real-time data, but dev is only off-season weeks and the test period shrinks.

## Decisions (the author, 2026-11-05)

1. **Dev period**: (a). Dev on the latest data, forecast dates 2022-10 to 2025-03; test on every real-time forecast date.
2. **Pathogens**: COVID-19, influenza and RSV, reported per pathogen.
3. **Foundation models**: one or two of Chronos-Bolt, TimesFM, Moirai, TiRex, with permissive licenses, plus **TabPFN v2** (added by the author). Versions, licenses, training-data dates and GPU needs are checked before the freeze.
4. **Fine-tuning a foundation model**: a follow-up after the zero-shot results, with its own dated addition and its own training and validation split.
5. **Truth cutoff**: target weeks ending on or before 2026-08-15.

## Decisions (the author, 2026-11-09, after the pre-freeze checks)

6. **Foundation models**: Chronos-2 (zero-shot), Chronos-2-Synth as a sensitivity analysis, and TabPFN v2 pinned to the v2 weights. TimesFM, Moirai, TiRex and Chronos-Bolt are excluded for the reasons in the table above.
7. **RSV on dev**: RSV stays in dev. Only forecast dates with enough observed history are used (threshold to be fixed in the plan before freezing), settings are tuned per pathogen, and the short RSV dev period (about one season) is reported as a limitation.

## Pre-freeze checks (2026-11-09)

### Foundation models

Rule: a pretrained model is used only if its documentation lists its pretraining data and they end before 2025-04-04 or are synthetic. Added here: the corpus should not contain CDC respiratory surveillance series (FluView ILINet, WHO/NREVSS), which are closely related to the targets even before the test period.

| Model | License | Pretraining data (documented) | CDC series in corpus | Quantiles | Verdict |
|---|---|---|---|---|---|
| Chronos-2 (`amazon/chronos-2`, 120M, 2025-10) | Apache-2.0 | Real datasets listed in the paper's Table 6 (energy, transport, nature, cloud operations, web, M4), plus synthetic data | None in Table 6 (checked 2026-11-09) | 21 levels, 0.01 to 0.99 | Proposed |
| Chronos-2-Synth (`autogluon/chronos-2-synth`) | Apache-2.0 | "only been trained on synthetic univariate and multivariate data" (model card) | None | as Chronos-2 | Proposed, sensitivity |
| TabPFN v2 (`Prior-Labs/TabPFN-v2-reg`), via `tabpfn-time-series` | Prior Labs License (Apache-2.0 with an attribution requirement) | Synthetic datasets (project README; the model card does not say) | None | From its predictive distribution | Proposed; pin v2 explicitly (newer package defaults use later, non-commercial checkpoints) |
| Chronos-Bolt | Apache-2.0 | Not released ("not planning to release the training data") | Unknown | 0.1 to 0.9 | Excluded: data not documented |
| TimesFM 2.0 / 2.5 | Apache-2.0 | LOTSA subset / GiftEvalPretrain, Wikipedia, Trends, synthetic | Yes: `cdc_fluview_ilinet`, `cdc_fluview_who_nrevss` | 0.1 to 0.9 | Excluded |
| Moirai 1.1 / 2.0 | CC-BY-NC-4.0 | LOTSA / GIFT-Eval pretrain plus internal data from about 2024 | Yes (1.1, documented); likely (2.0) | sampled / 0.1 to 0.9 | Excluded |
| TiRex | NXAI Community License | Chronos data, synthetic, GIFT-Eval pretrain subset | Yes (paper Table 6) | 0.1 to 0.9 | Excluded |

The data end dates of Chronos-2's real datasets are not stated; that they predate 2025 is an inference from their sources (all older public archives). Quantile levels 0.025 and 0.975 are not native to Chronos-2 and would be interpolated (linear in the quantile level), the same rule for every model that needs it. All three proposed models are small enough for one GPU with about 20 GB free.

### Data in the dev period

In the pinned release, COVID-19 and influenza admissions have no missing weeks from 2022-10 on (checked in SC, CA, TX, WY, NY). RSV admissions start in late 2023 (2023-11-25 to 2023-12-16 in those states), and some states have further missing weeks into 2024 (SC to 2024-08-03, WY to 2024-05-25). Dev for RSV therefore covers about one season.

## Implementation details (reviewed by the author 2026-11-09)

### Dates and rows

- **Dev forecast dates**: every Friday from 2022-10-07 to 2025-03-07, on the pinned (latest) data cut at the week ending 6 days before the date. The last dev date is 2025-03-07 so that no dev target week (latest 2025-03-29) is also a test target week. (B1a's dev ran to 2025-03-28; the full benchmark does not reuse it.)
- **Test forecast dates**: every Friday from 2025-04-04 to 2026-07-24 (69), real-time and revised, as above.
- **Minimum history**: a location-pathogen pair is forecast on a date only if its input series has at least 26 observed weeks among the last 52. This only removes RSV dev dates; it is checked for every row and the removed rows are counted. The same rows are used for every model.
- **Missing weeks inside a series**: filled by linear interpolation of log1p(value) before any model sees the series (weeks before the first observed value are dropped). The same filled series goes to every model, persistence included.
- **Failures**: a model that errors or returns invalid quantiles on a row gets persistence's forecast for that row. As in B1a, the primary analysis removes those rows for all systems, and a sensitivity analysis keeps them with the fallback. Fallbacks are counted per model.
- **Quantiles**: all models return the 23 levels; levels a model does not produce natively are interpolated linearly in the quantile level between its neighbouring native levels; quantiles are sorted and clipped at 0.

### Models

All transformations are log1p on the way in and expm1 on the way out, unless stated. Horizons are counted in weeks from the last observed week (k = 1 to 4 when the data are current; larger during the 2025 autumn gap).

| Model | Fixed settings | Tuned on dev (per pathogen) |
|---|---|---|
| Persistence | As in B1a: last value; quantiles from past k-week changes, symmetrised | Window of past changes: 52, 104, 156 weeks |
| Seasonal naive | Median: log1p of the value 52 weeks before the target, plus (mean log1p of the last 4 weeks minus mean log1p of the same 4 weeks a year earlier). Quantiles: this rule's own errors over the window, added to the median. If a week a year earlier is missing, the row falls back to persistence (counted) | Window: 52, 104 weeks |
| ARIMA, ETS | `statsforecast` AutoARIMA and AutoETS, non-seasonal (season length 1; 52 is too long for AutoETS and too few seasons for ARIMA), prediction intervals at the levels matching the 23 quantiles | Context: last 104 or 208 weeks |
| LightGBM | Global per pathogen, direct model per k, one quantile-loss model per level (23). Target: log1p(y at t+k) minus log1p(y at t). Features: log1p lags 0-7, change over 1 and 4 weeks, week of year (sine, cosine), the location's mean log1p over the last 52 weeks. Training rows are built only from the series as it stood on the forecast date (the real-time vintage on test). Refit every 4th forecast date | 4 configurations: number of leaves 15 or 31 x learning rate 0.03 or 0.1 (300 trees, min 20 rows per leaf) |
| LightGBM + ED visits | As LightGBM, plus log1p NSSP ED percent for the same pathogen, lags 0-3 (as published on the date for real time; pinned, cut at the same week, for revised). Test dates from 2025-08-15 only; compared with LightGBM on the same dates | Same configuration as LightGBM's choice |
| Chronos-2 | `amazon/chronos-2` through `chronos-forecasting`, univariate, raw values (the model scales internally), 21 native quantile levels; 0.025 and 0.975 interpolated | Context: last 104, 208 weeks, or the whole series |
| Chronos-2-Synth | `autogluon/chronos-2-synth`, Chronos-2's chosen settings, no tuning of its own | None |
| TabPFN v2 | `TabPFNRegressor` from the `tabpfn` package, loaded from the v2 regressor checkpoint downloaded from Hugging Face (`Prior-Labs/TabPFN-v2-reg`) with its SHA-256 recorded; no account or token is needed. Same features and target as LightGBM; one call per pathogen, k and forecast date, with all locations' rows in context (v2 row limit 10,000, checked 2026-11-09); quantiles read from its predictive distribution | Training window: last 52 or 104 weeks of rows |

Package versions and model revisions (Hugging Face commit hashes) are recorded in each run's configuration. Libraries: `statsforecast`, `lightgbm`, `chronos-forecasting`, `tabpfn` (not `tabpfn-time-series`, which adds a cloud client and telemetry).

### Selection on dev

For each model and pathogen, the configuration with the lowest mean WIS on dev (all locations, dates, horizons) is chosen; ties go to the simpler configuration (shorter window, fewer leaves). Persistence's window is chosen the same way, so the baseline is tuned as much as the models. The choices are written into this plan with a date before any test forecast; dev scores are not reported as results.

### Comparisons

Nine systems (seasonal naive, ARIMA, ETS, LightGBM, LightGBM + ED visits, Chronos-2, Chronos-2-Synth, TabPFN v2, the ensemble) are compared with persistence, plus the revision effect for each, without a correction for multiple comparisons; all are reported, and claims are limited to intervals that exclude 1 (or 0 for the gap). The primary comparison is per model, pooled over the three pathogens; per-pathogen results are secondary.

## Records

Each run saves under `eval/forecast-runs/<timestamp>-<split>-<model>/`: configuration (model, package versions, settings, data tag, forecast dates), the git commit at the start of the run, and one row per forecast (location, pathogen, forecast date, data version, target week, quantiles). Scores are computed from these files by a separate command, so scoring changes never require new forecasts.

## Code layout (planned)

- `src/resplens/forecast/vintage.py`: series as published on a date; series from the pinned release cut at a given week.
- `src/resplens/forecast/models/`: one module per model family, all with the same interface (series in, quantiles out).
- `src/resplens/forecast/score.py`: WIS, coverage, relative WIS, block bootstrap.
- `src/resplens/forecast/run.py`: command line for running a model over a split and scoring runs.
- Tests on a synthetic vintage history (the existing mirror state `ZZ`), with hand-computed WIS for a few cases.

## Changes after freezing

**2026-11-09, before any dev forecast: implementation details and one data fact.**

- **NSSP history by state**: the NSSP revision history starts on 2025-08-15 in 50 locations but on 2026-06-12 in Missouri. Real-time ED inputs for Missouri are empty before that date (LightGBM + ED visits sees missing values there; the revised version is cut the same way, so it is empty too).
- **TabPFN v2 version check**: the v2 row limit is 10,000 (`MAX_NUMBER_OF_SAMPLES` in `tabpfn` 9.2.0), so the table above is updated. Ensemble size fixed at 8 estimators, random state 0, so results do not depend on the package's `auto` setting.
- **Libraries and revisions**: `statsforecast` 2.1.1, `lightgbm` 4.7.0, `chronos-forecasting` 2.3.2, `tabpfn` 9.2.0, torch 2.14.1. Chronos-2 revision `29ec376`, Chronos-2-Synth `3607918`, TabPFN v2 checkpoint `tabpfn-v2-regressor.ckpt` at revision `02a4470`, SHA-256 `2ab5a07d...0736` (checked before use). Each run records these.
- **ARIMA and ETS**: the median is the forecast mean on the log1p scale (equal to the median of the Gaussian predictive distribution there); quantiles from `statsforecast`'s prediction intervals at levels 98, 95, 90, 80, ..., 10. All series of a date and pathogen are fitted in one call; if that call fails, the series are refitted one at a time so a failure costs one fallback.
- **LightGBM**: deterministic mode, row-wise histograms, random state 0. The week-of-year features describe the origin week t. "Every 4th forecast date" counts dates within the run (for LightGBM + ED visits, from 2025-08-15).
- **Inputs**: all series are built once from the pinned release into a cache (`resplens.forecast.inputs`) and filled and filtered when loaded, so every model sees identical inputs.

**2026-11-10, after the dev runs and before any test forecast: a cap on quantiles (the author's decision), and the dev choices.**

- **Why**: on dev, two models produced upper quantiles orders of magnitude above anything plausible when a series fell to near zero. TabPFN v2's mean COVID-19 WIS (window 104) was 5,995 against persistence's 53.5, almost all from one row: Texas on 2024-05-17, whose series fell 643, 274, 8 in its last three weeks (North Carolina: 148, 52, 2), probably the end of mandatory NHSN reporting in May 2024 (requires verification); its median was 5.6 but its 99% quantile 1.8e11. Chronos-2's RSV WIS was 529 against 28.6, from Texas and Michigan series near zero from 2023-12 to 2024-09 that then jumped to hundreds. The frozen plan had no rule for this.
- **Rule**: every quantile of every model (the ensemble's members included, before the median is taken, and persistence fallbacks included) is capped at 5 times the largest value of the input series that model saw for that location, pathogen and forecast date. The cap is applied at scoring time; the raw forecasts are kept, and every score row also carries the uncapped WIS.
- **Analysis**: all primary and secondary results use capped forecasts. A sensitivity analysis reports the uncapped results.
- **How 5 was chosen**: dev mean WIS with the cap at 2, 5 and 10 times the maximum (computed from the existing dev forecasts). 2 scored best for most models, but dev maxima come from short or partly reported histories, and a cap that tight could clip a real record season on test; 5 keeps nearly all of the gain (TabPFN COVID-19 68.3, Chronos-2 RSV 28.9). The author chose 5. This choice used dev only.
- **Edge case**: one series (Virginia RSV, 80 dev rows) has a maximum of 0, so the cap sets its quantiles to 0; total WIS on those rows is 104-106 for every model with or without the cap.
- **Fallbacks on test** use persistence with the window chosen below for that pathogen (on dev they used a 104-week window).

**Settings chosen on dev (capped scores; `eval/forecast-b1/dev-selection.json`; `models.CHOSEN`).** Dev mean WIS of the chosen setting in brackets; dev scores are for selection, not results.

| Model | COVID-19 | Influenza | RSV |
|---|---|---|---|
| Persistence | window 156 (53.5) | window 104 (52.1) | window 104 (26.5) |
| Seasonal naive | window 104 (105.7) | window 104 (83.1) | window 52 (19.2; only 32 rows without a fallback) |
| ARIMA | context 208 (54.3) | context 104 (50.8) | context 104 (49.0) |
| ETS | context 208 (52.0) | context 208 (58.0) | context 104 (39.4) |
| LightGBM | 15 leaves, rate 0.03 (49.6) | 15 leaves, rate 0.03 (46.7) | 15 leaves, rate 0.03 (25.1) |
| Chronos-2 | whole series (52.6) | whole series (47.9) | context 104 (28.9) |
| TabPFN v2 | window 104 (68.3) | window 104 (41.1) | window 104 (23.6) |

- On RSV every dev series is shorter than 104 weeks, so context and window settings above 104 give identical forecasts and the tie goes to the simpler setting; RSV's choices are not really tuned.
- With the cap, persistence's influenza window changed from 156 to 104; no other choice changed.
- LightGBM + ED visits uses LightGBM's settings and Chronos-2-Synth uses Chronos-2's, as planned.
- **Records in git**: each B1 run's `config.json` and `removed.json`, and `dev-selection.json`, are committed. `forecasts.jsonl` and `scores.jsonl` are kept locally and out of git (829 MB for the dev runs alone); scores are recomputed from forecasts by `bench score`. Runs are saved under `eval/forecast-b1/runs/`, not `eval/forecast-runs/` as written in "Records".
