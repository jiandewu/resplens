# B1a: can a general LLM forecast hospital admissions? (pre-registration)

Status: **approved and frozen 2026-11-05**, before any forecast was run. The prompt variant is chosen on dev and recorded here before any test forecast; later changes are listed at the end with their dates.

Results: [`llm-forecast-results.md`](llm-forecast-results.md) (test runs 2026-11-06).

This is the first part of B1. The full real-time benchmark ([`forecast-eval.md`](forecast-eval.md)) is planned but deferred.

## Question

Given only a state's recent weekly influenza hospital admissions as text, can a general-purpose LLM produce 1-4 week probabilistic forecasts that beat a persistence baseline, using only the data that were published at the time? And does a backtest on revised data make the LLM look better than it was?

## Systems

| System | Setting | Training data cutoff |
|---|---|---|
| `gemma4:31b` | thinking off | January 2025 (Google's Gemma 4 model card) |
| `gpt-oss:120b` | reasoning `medium` | June 2024 (OpenAI's model documentation) |
| Persistence (baseline) | see below | none |

The two LLMs are the A3 systems with the A3 settings, on local Ollama 0.40.13, temperature 0, seed 0, one run per forecast. Both cutoffs are before the first test forecast date (2025-04-04), so neither model can have seen the test period. Either may have seen published surveillance figures for earlier seasons; that cannot be checked and is stated as a limit.

**Persistence**: the median is the last observed value. For a target `k` weeks after the last observed week, the quantiles add the empirical quantiles of `log(1 + y[t]) - log(1 + y[t-k])` over the previous 104 weeks of the same series (as published on the forecast date) to `log(1 + last value)`, then transform back. Values below 0 become 0.

## Data

- Weekly NHSN influenza hospital admissions, state level, from the pinned ObsAwareData release `v2.0.0+2026-10-16`.
- **States**: CT, DE, FL, GA, MT, NC, PA, RI, SC, TX: 10 of the 51 locations, drawn with `random.Random(20261105).sample(sorted(codes), 10)` before any forecast. Each series starts in 2020.
- **Revision history**: NHSN releases from 2025-04-04 to 2026-10-16 (116 releases; preliminary releases from 2025-11-19). Each release contains the full series, so the series as published on any date can be rebuilt. NHSN published no release between 2025-09-26 and 2025-11-14. Details: [`forecast-eval.md`](forecast-eval.md), "What the data allow".

## Forecasts

- **Forecast dates (test)**: the 69 Fridays from 2025-04-04 to 2026-07-24. On each date, the series is taken from the latest release published on or before it.
- **Targets**: the 4 weeks ending 1, 8, 15 and 22 days after the forecast date. When the latest release is old (autumn 2025), the gap between the last observed week and the targets is larger, as it was for a forecaster at the time.
- **Two versions**: each forecast is made twice, from the series as published on the forecast date (**real time**) and from the pinned release cut at the same last week (**revised**). Only the values differ.
- **Output**: 23 quantiles (0.01, 0.025, 0.05, 0.10, 0.15, ..., 0.90, 0.95, 0.975, 0.99) for each target week.
- **Truth**: the pinned release. All test targets end on or before 2026-08-15, at least 9 weeks before the last release.

## Prompt

The model receives the state, the pathogen, the forecast date, the four target weeks, and the series as text, one line per week (week-ending date and count; a missing week is written as `missing`). It is asked for the 23 quantiles of each target week, as JSON constrained by a schema (four arrays of 23 numbers). No tools, documents or other data.

Chosen on dev (below), from at most 4 variants:

- history: the last 26 weeks, or the last 52;
- with or without the 8 weeks one year earlier that match the last 4 observed weeks and the 4 target weeks.

**Output handling**:

- **Preventing failures**: the schema, passed as Ollama's `format`, fixes the structure (four arrays of exactly 23 numbers), so malformed JSON should not occur. The output limit leaves room for gpt-oss's reasoning; a response cut off by the limit counts as a failure.
- **Repair instead of a blind retry**: at temperature 0, retrying with another seed may return the same output, so a failed response (cut off, wrong number of values, or not numbers) gets one repair turn: the error is sent back to the model ("week 2 has 22 values; return exactly 23 numbers per week") and it answers again. The number of repairs is reported for each system.
- **Clean-up**: quantiles are sorted and values below 0 set to 0; how often each is needed is reported.
- **Forecasts that still fail** are reported as a failure rate for each system. **Primary analysis**: a failed forecast (state, date, target week, data version) is removed for every system, so all systems are compared on the forecasts they all produced. **Sensitivity analysis**: failed forecasts are replaced by the persistence forecast and kept, which shows whether removing them favors the LLMs.

## Dev

- Forecast dates: the 26 Fridays from 2024-10-04 to 2025-03-28 (the 2024-25 season), revised data only, since no release history exists then.
- Used only to choose the prompt variant, by mean WIS relative to persistence over both LLMs; ties go to the shorter prompt.
- Both LLMs' training data overlap this period, so dev scores may be optimistic. They are reported as dev results and never mixed with test.

### Prompt variant chosen on dev (2026-11-06, before any test forecast)

Runs at commit `58874de`, revised data, 260 forecasts per run (10 states x 26 dates), 4 target weeks each. No run had a failed or repaired forecast; gpt-oss's quantiles needed sorting in 2, 1 and 3 forecasts (h26, h26_last_year, h52), gemma's in none; no values were clipped.

| Variant | gemma4 relative WIS | gpt-oss relative WIS | Mean over both |
|---|---|---|---|
| `h26` | 1.044 [0.809, 1.289] | 1.825 [1.143, 2.620] | 1.434 |
| `h26_last_year` | 0.817 [0.664, 0.967] | 1.487 [0.932, 2.134] | 1.152 |
| `h52` | 0.911 [0.732, 1.118] | 1.262 [0.858, 1.673] | **1.087** |

Relative WIS against persistence, with 95% date-block bootstrap intervals. By the rule above, the test variant is **`h52`**. gemma4 alone would have chosen `h26_last_year`; the difference between the two variants is small next to the intervals. Coverage of the 95% interval on dev: gemma4 0.65-0.72, gpt-oss 0.44-0.52, persistence 0.86.

## Metrics and analysis

- **Primary**: for each LLM, mean WIS divided by persistence's mean WIS, over all states, real-time test dates and target weeks for which every system produced a forecast (see "Output handling"). The 95% interval comes from a block bootstrap over forecast dates (all states and targets of a date resampled together), 10,000 resamples. An LLM is called better than persistence only if the whole interval is below 1; worse only if it is entirely above 1; otherwise no detectable difference.
- **Secondary**:
  - **MAE** of the median forecast, relative to persistence's MAE, with the same block bootstrap interval; reported overall, by target week and by state. MAE is used rather than MSE because the point forecast is the median, which absolute error evaluates (squared error evaluates a mean), and because squared errors would be dominated by the largest states and peak weeks;
  - coverage of the 50% and 95% intervals; WIS results by target week and by state;
  - the revision effect: each system's relative WIS on revised minus on real-time data, with the same bootstrap;
  - gemma4 against gpt-oss, paired on the same forecasts;
  - schema failures, sorted or clipped quantiles, seconds per forecast.
- 10 states, one pathogen and one season: the results describe these, not LLM forecasting in general.

## Follow-up (not part of this experiment)

This experiment gives the LLMs numbers only. Whether text or other context helps (ED visits, holidays and school calendars, CDC weekly report text, news) is a separate experiment, B1b, with its own pre-registration. It compares the same LLM with and without context on the same states and dates, so this experiment is its control. Every context source must have a reliable publication time before the forecast date, and published forecasts (for example CDC's ensemble) are excluded.

## Records

Each run saves under `eval/forecast-runs/<timestamp>-<split>-<system>-<version>/`: configuration (model, digest, Ollama version, settings, prompt template, states, dates, data tag), the git commit at the start, and per forecast the prompt, the raw response, any retry, the parsed quantiles, and timing. Scores are computed from the saved forecasts by a separate command.

## Code layout (planned)

- `src/resplens/forecast/vintage.py`: series as published on a date; series from the pinned release cut at a given week.
- `src/resplens/forecast/persistence.py`: the baseline.
- `src/resplens/forecast/llm.py`: prompt, schema, request, parsing.
- `src/resplens/forecast/score.py`: WIS, coverage, relative WIS, block bootstrap.
- `src/resplens/forecast/run.py`: command line to run a system over a split and to score runs.
- Tests: hand-computed WIS cases, the vintage reconstruction on the synthetic mirror `ZZ`, and the LLM path with a scripted fake model.

All code is written for this repository; no forecasts are submitted to any hub.

## Changes after freezing

### 2026-11-05, before any forecast: two implementation details

- **Persistence quantiles**: the past changes are used together with their negatives (each change `d` also as `-d`), so the median is exactly the last observed value, as specified above; with the changes alone, the 0.5 quantile need not be zero.
- **Prompt variants**: three, not four: `h26`, `h26_last_year`, `h52`. With 52 weeks of history, the weeks one year earlier are already in the prompt (except when the data are stale), so `h52` with last year would repeat them.
