# Counterfactual tool outputs: results

Test results for the evaluation pre-registered in [`counterfactual-eval.md`](counterfactual-eval.md) (frozen 2026-11-24, before any test run). No change was made to the plan, sample or scoring after the test runs.

## Setup

- 90 test questions drawn with seed 20261125 from the eligible B2 questions, disjoint from dev: arm M (training questions whose kept trace the fine-tuned model was trained on) 60, arm C (validation questions, never trained on) 30.
- `b2-base` and `b2-ft` (Gemma 4 E4B, bf16, vLLM, the A3 system prompt, tools and limits), seeds 0, 1, 2, each question with the original and with the perturbed tool outputs: 1,080 runs at commit `c314a90`, 2026-11-24. All ended with an answer.
- Perturbation: every value of the scaled measures in `get_series`, `get_as_of` and `get_revisions` multiplied by the question's factor (0.7, 0.8, 1.25 or 1.4). It changed at least one output in all 540 perturbed runs, and every required perturbed value appeared in the run's tool outputs (1,158 of 1,158 numbers).

## Primary comparison (pre-specified): arm M, `b2-ft` against `b2-base`

| | `b2-base` | `b2-ft` |
|---|---|---|
| Questions reverting (2 of 3 perturbed runs) | 0 / 60 | 0 / 60 |
| Perturbed runs reverting | 0 / 180 | 0 / 180 |
| Required numbers: follows / reverts / ambiguous / neither | 378 / 0 / 0 / 3 | 381 / 0 / 0 / 0 |

Solved only by one system: 0 and 0, sign test p = 1.0; mean difference in run-level revert rate 0.000 [0.000, 0.000]. **No detectable memorization**: on the exact questions it was trained on, the fine-tuned model reported the perturbed values every time and never the values in its training answers.

## Secondary

| Arm C (control) | `b2-base` | `b2-ft` |
|---|---|---|
| Perturbed runs reverting | 0 / 90 | 0 / 90 |
| Required numbers: follows / neither | 198 / 0 | 198 / 0 |

- M minus C: 0 for both systems.
- No revert candidates among the other numbers in any perturbed answer.
- Original outputs: every required number present in 177 of 180 `b2-base` runs and in all other system-arm cells.
- The 3 `neither` (and the 3 original-run misses) are one question, `t0831`, all seeds of `b2-base`: asked about "Washington", it queried DC instead of WA, and reported DC's value (61 on the original outputs, 85 = 61 x 1.4 on the perturbed ones). A wrong state, not a revert; it still copied the value it was given.

## What the null result covers

Not pre-specified, added after the test results to size the null: with 0 of 60 arm-M questions reverting for `b2-ft`, the exact (Clopper-Pearson) 95% upper bound on the question-level revert rate is 6.0%; at the run level, ignoring the clustering of runs within questions, 0 of 180 gives 2.0%.

## Limits

- Only the fine-tuned E4B had a way to have memorized these values (the other models' training cutoffs predate the data); the result says nothing about values seen in pretraining.
- One adapter (r = 16, 3 epochs on 1,152 traces). Larger ranks, more epochs or more repeated questions could memorize more.
- Scaling by one factor per question is one kind of change; a model that remembered the shape of a series but not its values would not be detected.
- Eligibility kept admission counts of at least 5 and their revisions; ED percentages and small counts are not covered (R1, the author's decision).
- 60 + 30 questions; a revert rate of a few percent cannot be ruled out (above).

## Records

- Runs: `eval/counterfactual/runs/test-*` (traces with the original outputs, scores); dev runs `dev-*`.
- Sample and eligibility: `eval/counterfactual/test-sample.jsonl`, `eligibility.jsonl`.
- Analysis: `uv run python -m resplens.agent.counterfactual analyze --split test` writes `eval/counterfactual/test-analysis.json`.
