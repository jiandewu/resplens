# B1a results: LLM as forecaster

Test results for the experiment pre-registered in [`llm-forecast-eval.md`](llm-forecast-eval.md), frozen on 2026-11-05. The prompt variant (`h52`) was chosen on dev and recorded there before any test forecast. No method was changed after the test runs started.

## Setup

- 6 runs at commit `c1b4380` (2026-11-06): persistence, `gemma4:31b` (thinking off) and `gpt-oss:120b` (reasoning `medium`), each on real-time and revised data. Local Ollama 0.40.13, temperature 0, seed 0.
- 690 forecasts per run (10 states x 69 Friday forecast dates, 2025-04-04 to 2026-07-24), 4 target weeks each: 2,760 scored targets per run.
- **Output handling**: no forecast failed and none needed a repair turn, so the primary analysis uses all 2,760 targets and the sensitivity analysis (failures replaced by persistence) is identical to it. gpt-oss's quantiles needed sorting in 2 real-time and 4 revised forecasts; gemma's in none. No values were clipped.
- Intervals are 95% block bootstrap intervals over the 69 forecast dates, 10,000 resamples. "Better" means the whole interval is below 1; "worse", entirely above 1.
- Analysis: `uv run python -m resplens.forecast.analyze eval/forecast-runs/20261106-*-test-*`; the output is saved as [`eval/forecast-review/analysis.json`](../eval/forecast-review/analysis.json).

## Primary result

Mean WIS relative to persistence on real-time data (lower is better):

| System | Relative WIS | Verdict |
|---|---|---|
| `gemma4:31b` | 0.992 [0.684, 1.375] | no detectable difference |
| `gpt-oss:120b` | 0.916 [0.805, 1.058] | no detectable difference |

**Neither LLM is detectably better or worse than persistence when forecasting from the data published at the time.** Mean WIS: persistence 74.99, gemma 74.42, gpt-oss 68.66.

## Revised data and the revision effect

| System | Relative WIS, revised | Revision effect (revised minus real time) |
|---|---|---|
| `gemma4:31b` | 1.004 [0.701, 1.355], no detectable difference | +0.011 [-0.040, 0.055] |
| `gpt-oss:120b` | **0.829 [0.744, 0.913], better** | -0.086 [-0.199, 0.008] |

A backtest on revised data would have reported gpt-oss as better than persistence; on the data available at the time, the difference is not detectable. The revision effect itself is not detectable for either system: gpt-oss's interval just includes 0.

Persistence's own mean WIS is higher on revised data (77.81, against 74.99 real time). This is not an error. The last observed week is the same in both versions for all 690 forecasts, but the revised last value is higher in 402 of them: early releases are later revised upward, which raises persistence's anchor. The relative numbers above compare each system with persistence on the same data version.

## Secondary measures

### MAE of the median

| System | Real time | Revised |
|---|---|---|
| `gemma4:31b` | 1.018 [0.723, 1.405] | 1.013 [0.736, 1.359] |
| `gpt-oss:120b` | 0.845 [0.737, 1.009] | **0.765 [0.688, 0.858]** |

### By target week (real time)

| Target week | gemma WIS | gpt-oss WIS | gemma MAE | gpt-oss MAE |
|---|---|---|---|---|
| 1 | 1.104 [0.927, 1.368] | 1.043 [0.938, 1.189] | 1.165 [0.948, 1.492] | 0.980 [0.878, 1.153] |
| 2 | 1.083 [0.817, 1.449] | 0.961 [0.850, 1.122] | 1.075 [0.808, 1.457] | 0.886 [0.775, 1.082] |
| 3 | 0.969 [0.623, 1.416] | 0.890 [0.769, 1.056] | 0.963 [0.642, 1.400] | **0.799 [0.688, 0.976]** |
| 4 | 0.913 [0.541, 1.377] | 0.860 [0.734, 1.013] | 0.965 [0.608, 1.428] | **0.801 [0.680, 0.974]** |

Both LLMs do worst against persistence one week ahead and better further out: persistence is hard to beat when little has changed since the last observed week. On revised data, gpt-oss's WIS is better than persistence for weeks 2-4 (0.867, 0.784, 0.782, intervals below 1) and not for week 1 (0.991 [0.836, 1.174]).

### By state (real time, relative WIS)

| State | gemma | gpt-oss |
|---|---|---|
| CT | 1.017 | 0.902 |
| DE | 0.932 | **0.600 [0.457, 0.784]** |
| FL | 0.938 | *1.337 [1.015, 1.733]* |
| GA | 0.962 | 0.881 |
| MT | 1.039 | 1.062 |
| NC | 1.087 | **0.741 [0.539, 0.973]** |
| PA | 1.140 | 0.801 |
| RI | 1.232 | 0.845 |
| SC | 1.100 | 1.023 |
| TX | 0.783 | **0.741 [0.550, 0.961]** |

Bold: better than persistence; italics: worse. No gemma state result is detectably different. With 10 per-state tests per system, one or two detectable results could occur by chance, so these describe where errors fell; they are not separate findings.

### Interval coverage

| System | 50% real time | 95% real time | 50% revised | 95% revised |
|---|---|---|---|---|
| Persistence | 0.568 | 0.946 | 0.563 | 0.959 |
| `gemma4:31b` | 0.472 | 0.820 | 0.439 | 0.809 |
| `gpt-oss:120b` | 0.319 | 0.654 | 0.333 | 0.674 |

Both LLMs' intervals are too narrow, as they were on dev; gpt-oss's 95% interval covers the truth about two times in three. gpt-oss's lower WIS comes from better medians despite overconfident intervals.

### gemma against gpt-oss

| | Real time | Revised |
|---|---|---|
| WIS, gemma / gpt-oss | 1.084 [0.752, 1.497] | 1.210 [0.840, 1.642] |
| MAE, gemma / gpt-oss | 1.204 [0.881, 1.590] | 1.325 [0.970, 1.732] |

No detectable difference between the two LLMs.

### Cost

| System | Median seconds per forecast (max) | Median output tokens (max) |
|---|---|---|
| `gemma4:31b` | 7.5 (21.0) | 389 (574) |
| `gpt-oss:120b` | 20.4 (60.5) | 3,582 (10,560) |

Real-time runs; the revised runs are similar. gpt-oss's tokens are mostly reasoning.

## Dev and test disagree

On dev (2024-25 season, revised data, `h52`), gemma was ahead of persistence (0.911 [0.732, 1.118]) and gpt-oss behind it (1.262 [0.858, 1.673]). On test, revised data, the order is reversed: gemma 1.004, gpt-oss 0.829. Possible reasons, none tested:

- the dev period is one severe season; the test period covers the end of that season, the 2025 summer, the 2025-26 season and part of the 2026 summer;
- gemma's training data (cutoff January 2025) overlap the first part of dev, so gemma may have seen some of the values it forecast there. gpt-oss's cutoff (June 2024) is before dev. The pre-registration said both models overlap dev; that is true only for gemma.

Dev was used only to choose the prompt variant, not to choose a model. Had it been used to choose a model, it would have picked the one that did worse on test. One season of dev is a weak basis for choosing between models.

## Limits

- 10 states, one pathogen, one test period of 69 forecast dates. The results describe these.
- One run per forecast at temperature 0; run-to-run variation was not measured.
- Both cutoffs are before the first test date, but the models may have seen surveillance figures for earlier seasons; this cannot be checked.
- Persistence run configurations record `"variant": "h52"`; persistence does not use a prompt, and the field has no effect.

## Records

- Runs: `eval/forecast-runs/20261106-*-test-*` (configuration, commit, prompts, raw responses, parsed quantiles, timing, scores).
- Dev runs: `eval/forecast-runs/20261105-*-dev-*`.
- Analysis code: `src/resplens/forecast/analyze.py`; tests in `tests/test_forecast.py`.
