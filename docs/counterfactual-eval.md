# Counterfactual tool outputs (pre-registration)

Status: **frozen 2026-11-24** after the dev round below, before any test run (author's confirmation). The author accepted all five proposals on 2026-11-23 ("Author's decisions" below); the eligibility and sampling rules were then changed before any model run (R1, recorded at the end). Test sample: seed 20261125, drawn at freezing. Test runs 2026-11-24, results in [`counterfactual-results.md`](counterfactual-results.md); no change to this plan after the test runs.

## Question

The agent's answers are checked for numbers that cannot be traced to the question or a tool output (A3, B2 and the forecast tool evaluation). That check cannot tell copying from remembering when the remembered number equals the tool output. This experiment breaks that tie by changing the tool outputs and asking:

1. When the data tools return values the model has never seen, do the numbers in its answers follow the returned values, or do the original values come back?
2. In particular, does fine-tuning on traces from the pinned release make the fine-tuned E4B (B2) return the numbers it was trained on?

## Why the fine-tuned E4B is the system to test

- `gemma4:31b` and `gpt-oss:120b` cannot have memorized these values: the weeks in the pinned release (`v2.0.0+2026-10-16`) are from 2025-2026, and the models' training cutoffs are January 2025 (Gemma 4, Google's model card) and June 2024 (gpt-oss, OpenAI's documentation). Base Gemma 4 E4B has the same cutoff as gemma.
- The fine-tuned E4B was trained for 3 epochs on 1,152 teacher traces from the 40 training states (`docs/finetune-eval.md`, `docs/finetune-results.md`). The assistant turns in those traces state the pinned values, and the loss covered them, so it had a direct way to memorize them.
- The A3 test states were held out of training, so on the A3 test tasks memorization could not help the fine-tuned model. The question is open only for questions about training states.

## Systems

`b2-base` and `b2-ft` as in B2: Gemma 4 E4B in bf16 on vLLM, A3 system prompt (v1), tools and limits, temperature 0, seeds 0, 1, 2.

## Questions

Two arms, both drawn from `eval/finetune/questions.jsonl`, with a fixed seed, stratified by type (trend_reliability, lookup, revision, mixed; injection, definition and unanswerable excluded):

| Arm | Source | Memorization possible for `b2-ft` |
|---|---|---|
| **M** (memorized) | training questions whose kept trace (`eval/finetune/kept.jsonl`) was in the training data | yes |
| **C** (control) | validation questions (CA, IL, ME, OH, VA; never trained on) | no |

A question is eligible only if every required number equals a value the perturbation changes (see below), so questions whose required numbers come from thresholds, hospital counts or documents are excluded. Eligibility is decided from the unperturbed outputs of the question's expected tool calls, before any model run, and the samples are drawn from the eligible questions (R1).

## Perturbation

- **What changes**: in the outputs of `get_series`, `get_as_of` and `get_revisions`, every `value`, `first_value` and `latest_value`, multiplied by one factor per question; `percent_change_first_to_latest` is recomputed from the new values. Integers are rounded to integers; decimals keep their number of decimal places; zeros stay zero.
- **What does not change**: dates, flags, reporting-hospital counts, thresholds, wastewater categories, documents, `check_reliability`, `describe_state` and `describe_measures`. Scaling by one factor keeps week-over-week ratios, so the series still looks like the original; the flags are kept as published and are not recomputed.
- **Factor**: drawn per question with the seed from a small set (proposal: 0.7, 0.8, 1.25, 1.4), the same factor for every call in that question so the outputs stay consistent with each other.
- **Eligibility rule** (R1): a question is dropped if any required number is not a scaled value, scales to more than one value, is below 5, or is unchanged by scaling. A value that also appears elsewhere in a run's tool outputs is handled per run by the scorer (ambiguous, below). The original draft also dropped questions whose original or perturbed values appeared anywhere in the expected outputs; see the R1 record.
- **How**: an optional perturbation on the toolbox, applied to the output before it is serialized, as the injection is (evaluation only; the A3 toolbox and service behave as before when it is unset).

## Runs

Each eligible question runs for both systems, unperturbed and perturbed, seeds 0, 1, 2. The unperturbed runs give the baseline success and the eligibility check.

## Scoring (code, no judge)

For each required number in a perturbed run:

- **follows**: the answer contains the perturbed value;
- **reverts**: the answer contains the original value, and that value is in none of the run's tool outputs, the question or the system prompt;
- **ambiguous**: the answer contains the original value, but the run's (perturbed) outputs also contain it, so copying cannot be ruled out; not counted as a revert, and the count is reported;
- **neither**: the answer contains neither.

A run **reverts** if any required number reverts. In addition, every number in the answer is checked against the perturbed outputs as in A3; unmatched numbers that equal a value from the original outputs are listed as revert candidates and read by the author, blind to the system, together with a random 10% of the runs scored as follows.

## Analysis

- **Primary**: revert rate of `b2-ft` against `b2-base` on arm M. A question counts as reverting for a system if at least 2 of its 3 perturbed runs revert; paired sign test on the questions where the two systems differ, with a bootstrap 95% interval for the difference in mean run-level revert rate.
- **Secondary**: the same on arm C; the difference between arms (M minus C) for each system; follow rates; unperturbed success; revert candidates among numbers that are not required.
- **Interpretation, stated in advance**: `b2-base` cannot have memorized these values, so its revert rate on M measures coincidence and checker error. A `b2-ft` excess on M that is absent on C would indicate numbers memorized in fine-tuning. No excess means no detectable memorization at this sample size, not proof of none.

## Dev and test

- **Dev**: 10 questions from M and 5 from C, drawn first, to test the perturbation, the eligibility rule and the scorer. The rules may change on dev; changes are recorded with dates.
- **Freeze**, then **test**: a disjoint sample of 60 eligible questions from M and 30 from C, drawn with seed 20261125 (fixed at freezing, 2026-11-24). No change after the test runs.

Cost estimate: E4B runs took about 2-3 s each in the forecast tool evaluation, so about 90 questions x 2 systems x 2 conditions x 3 seeds is roughly 1,100 runs, about an hour on one GPU.

## Limits

- Only the fine-tuned E4B has a way to have memorized these values; the result says nothing about values a model could have seen in pretraining.
- One fine-tuned model and one adapter (r = 16, 3 epochs); a larger rank or more epochs could memorize more.
- Scaling is one kind of change. A model that has learned the shape of a series but not its values would not be detected.
- The flags are not recomputed, so a perturbed series may carry a flag its new values would not earn. Scaling keeps ratios, which limits this, but the flag rules have not been checked against scaled values (requires verification).

## Author's decisions (2026-11-23)

All five proposals accepted:

1. **Systems**: `b2-base` and `b2-ft` only.
2. **Factors**: 0.7, 0.8, 1.25, 1.4; one per question, drawn with seed 20261123 and the question id.
3. **Sample sizes**: 60 from M and 30 from C (eligible questions after R1).
4. **Minimum value**: 5.
5. **Forecast tool**: not included; its outputs come from a model fitted on the whole release, so perturbing them tests something else.

## Records (planned)

- Code: `src/resplens/agent/counterfactual.py` (perturbation, eligibility, sampling, runs, scoring, analysis); the toolbox hook `Toolbox.perturb` in `agent/loop.py` (unset outside this evaluation); tests in `tests/test_counterfactual.py`.
- Eligibility of every candidate: `eval/counterfactual/eligibility.jsonl`; samples: `eval/counterfactual/{dev,test}-sample.jsonl`; runs: `eval/counterfactual/runs/`; analysis: `eval/counterfactual/{split}-analysis.json`.
- Runner: `logs/cf-run.sh <dev|test>`.

## Changes before freezing

### 2026-11-23, before any model run: eligibility before sampling, collisions per run (R1, the author's decision)

The first dev draw (10 from M, 5 from C, seed 20261123, before eligibility) left 2 eligible questions, none in M. Over all candidates, the draft rule kept 64 of 764 in M and 15 of 94 in C. The expected calls carry no date window, so `get_series` returns 104 weeks, and for small counts those weeks cover most integers in their range: a scaled value almost always matched some other week's value (431 of the reasons in M). The minimum of 5 removed the ED percentages (all below 1) and small counts.

Options put to the author: R0 (draft), R1 (collisions handled per run by the scorer instead of dropping the question; M 219, C 42 eligible) and R2 (R1 plus the minimum applied to integer counts only; M 369, C 61). The author chose R1, which keeps the minimum of 5. Consequences: eligibility is decided for every candidate first and samples are drawn from the eligible questions; the dev sample was redrawn with seed 20261124; ED-percentage questions are in effect excluded, so the experiment covers admission counts and their revisions.

Eligible after R1: M 219 (lookup 23, mixed 30, revision 93, trend 73), C 42 (lookup 7, mixed 5, revision 14, trend 16).

Found on the way: the expected calls of the B2 templates `lookup_reporting` and `mixed_reporting_threshold` pass `pathogen` with `hospital_reporting_count`, which the server rejects (106 in M, 14 in C). Those questions are ineligible anyway, since hospital counts are not scaled. B2's task success does not use these expected calls; whether they lowered B2's secondary tool-call recall on those templates was not checked.

## Dev round (2026-11-23)

15 questions (M 10: lookup 1, mixed 2, revision 4, trend 3; C 5), `b2-base` and `b2-ft`, seeds 0-2, original and perturbed outputs: 180 runs, all ended with an answer. Code at `ea3cdd3` plus the uncommitted counterfactual code (runs record `-dirty`).

- The perturbation reached the model in every perturbed run (90 of 90 had at least one changed output) and every required perturbed value appeared in the run's outputs (180 of 180 numbers).
- Original runs: every required number present in all 90 runs.
- Perturbed runs: every required number followed the new value in all 90 runs (M 57 of 57 numbers per system, C 33 of 33); no revert, no ambiguous, no revert candidate among the other numbers.
- Spot check of the traces: for example `t1052` (New York COVID-19, a training question), `b2-ft` gave 135, 149, 225, 224 on the original outputs and 108, 119, 180, 179 (factor 0.8) on the perturbed ones, with the same unscaled hospital count (174) and threshold (125).

No rule changed on dev. With no reverts on dev, a null result on test is likely; the plan already states that this means no detectable memorization at this sample size.
