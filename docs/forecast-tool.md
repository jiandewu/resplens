# Forecast tool for the agent

Status: started 2026-11-16; evaluated with a pre-registered task set ([plan](forecast-tool-eval.md), [results](forecast-tool-results.md)). The A3 and B2 results do not cover it.

## Goal

The plan joins the two lines here: the best B1 model becomes a `forecast` tool, and the agent answers questions about the coming weeks with the forecast intervals and the data's reliability.

## Design

- **Model**: LightGBM quantile regression with the settings chosen on dev in B1 (`models.CHOSEN["lightgbm"]`: 15 leaves, learning rate 0.03, all pathogens). It had the lowest relative WIS on the B1 test (0.712 [0.666, 0.755] against persistence, real-time data) and runs on CPU.
- **Data**: every state's NHSN hospital admission series for the pathogen in the pinned release (`DATA_TAG`), with the B1 rules: at least 26 reported weeks among the last 52, interior gaps filled. The forecast date is the Friday after the latest reported week across states, and the targets are the next four weeks, as in B1. A state whose data end earlier gets longer horizons.
- **Output**: last reported week and value; for each target week the median and the 50% and 95% intervals (rounded to whole admissions, capped at 5 times the series' largest value, the rule used when B1 was scored); the model, the B1 test accuracy (relative WIS, interval coverage), and two notes (recent weeks are first reports; 95% intervals held the value 90.2% of the time in the backtest).
- **Agent integration**: `forecast/tool.py`. `make_toolbox_class()` returns a subclass of the A3 `Toolbox` that adds `forecast_admissions` and runs it in-process; `forecast_prompt()` adds one rule to the A3 system prompt (use the tool only for future weeks, report median and 95% interval with their weeks, give the backtest accuracy, and call `check_reliability`). The A3 loop, toolbox, system prompt, MCP server, runner and service are unchanged, so the evaluated configurations are unaffected and the public code does not diverge from `dev` in shared files.
- **Fit**: once per pathogen and process (4 horizons x 23 quantile levels); about 26 s for influenza including building every state's series.

## Tests

`tests/test_forecast_tool.py` (synthetic series, 20 trees): four target weeks with ordered intervals and integer values; longer horizons for a state behind the latest week; cap; unknown state and pathogen reported as tool errors; the toolbox adds the tool after the A3 tools and never sends it to the MCP server; the forecast prompt extends the A3 prompt. Suite 117 passed, 1 skipped.

## Smoke check (2026-11-16, gemma4:31b on Ollama, thinking off, seed 0)

Traces in `logs/forecast-tool/smoke-20261116.jsonl` (git-ignored).

| Question | Tools called | Result |
|---|---|---|
| SC influenza, next four weeks, how much to trust it | `forecast_admissions`, `check_reliability` | Medians and 95% intervals for 2026-10-17 to 11-07, backtest coverage 90.2%, last report 51 and its revision caveat, hospitals 70 against threshold 50; 56.8 s including the fit. Numbers not found: 2025 and 2026 (dates rewritten as "April 2025 to July 2026") and two interval widths (94, 593) computed without showing the calculation. |
| Dev task `a01` (SC influenza, past four weeks) | `get_series`, `check_reliability` | Same answer as without the tool; the forecast tool was not called. |
| PR COVID-19, next month | `forecast_admissions` (error), `check_reliability` (error) | Says the tools cover the 50 states and DC only. |

Same three questions with the B2 fine-tuned Gemma 4 E4B (vLLM 0.33.0, bf16), which never saw this tool in training (traces `logs/forecast-tool/smoke-b2-ft-20261116.jsonl`):

| Question | Tools called | Result |
|---|---|---|
| SC influenza forecast | `forecast_admissions`, `check_reliability` | All four weeks with medians and 95% intervals, last report 51, backtest coverage 90.2%, hospital reliability; every number found (29.4 s including the fit). Two unsupported judgments: "relies on the assumption that recent trends continue" and "historical performance is strong". |
| Dev task `a01` | `get_series`, `check_reliability` | Same answer as before; forecast tool not called (1.9 s). |
| PR COVID-19 | `describe_state` (error), `search_docs` | Says PR is not covered; did not call the forecast tool. |

## Findings so far

- The medians need not rise or fall steadily across horizons (SC influenza: 60, 75, 64, 102), because B1 fits one model per horizon. This is the evaluated model's behavior, not a bug; the agent did not comment on it.
- The 95% intervals widen quickly with horizon (SC influenza week 4: 16 to 609).

## Open

- Done 2026-11-19: the task set and pre-registered evaluation ([results](forecast-tool-results.md)). The B2 fine-tuned model, without retraining, did clearly worse than `gemma4:31b` with the tool.
- Not tried: fine-tuning with traces that use the tool.
