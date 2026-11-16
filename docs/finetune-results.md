# B2 results: fine-tuning a 4B model to run the agent

Test results for the plan in [`finetune-eval.md`](finetune-eval.md), frozen on 2026-11-09. Every change made after freezing is listed there with its date; all of them were made before any test run. The test runs, labels and analysis are in `eval/agent-runs/*-test-b2-*` and `eval/finetune-review/`.

## Setup

- **Student**: Gemma 4 E4B (`google/gemma-4-E4B-it`, revision `4ecc2ba6`), chosen over Qwen3-4B-Instruct on validation (108 against 79 of 158 successes) before any training.
- **Training data**: 1,152 conversations from two teachers (`gemma4:31b` 795, `gpt-oss:120b` 357) on generated questions about states and documents held out from the A3 test set, filtered by code checks, the judge and the author's review of a sample.
- **Fine-tuning**: LoRA on the language model's attention and MLP projections. A grid of 6 configurations x 3 epochs was scored on the 158 validation items; the chosen one is r = 16, learning rate 2e-4, epoch 3 (147 of 158; base 108). Training took 1.5 h on one H100.
- **Test**: the 24 A3 test tasks, unchanged; seeds 0, 1 and 2 for each system; temperature 0; both systems served by vLLM 0.33.0 in bf16 with the same tools, system prompt and limits as A3. All 144 runs ended with an answer (2 of them, base on b19, with empty text).
- **Labels**: for seed 0, the author's blind grades of all 48 answers (24 tasks x 2 systems); for seeds 1 and 2, the judge (`qwen3:235b-thinking`). Every number in every answer matched the question or a tool output directly, so there was no hand review of numbers. The 3 injection detector hits were checked by hand; none followed the instruction.
- **Task success**, as in A3: a correct answer, no unsupported number, the reliability caveat where required, and no injected instruction followed.

## Primary comparison: fine-tuned against base

| | Base E4B | Fine-tuned E4B |
|---|---|---|
| Mean task success over 3 runs | 0.847 (61 / 72) | 0.903 (65 / 72) |
| Tasks solved (at least 2 of 3 runs) | 20 / 24 | 22 / 24 |

Paired over tasks: 3 tasks were solved only by the fine-tuned model and 1 only by the base (exact sign test p = 0.63). The mean difference in per-task success (fine-tuned minus base) is +0.056, 95% bootstrap interval [-0.083, 0.208].

**There is no detectable difference on test.** The fine-tuned model is ahead on both measures, but with 24 tasks the interval includes zero and a small loss. On validation the same comparison was 147 against 108 of 158; the test set is smaller and the base already solves most of it.

| Analysis | Base | Fine-tuned | Solved only by fine-tuned / only by base | p |
|---|---|---|---|---|
| Primary (author labels for seed 0, judge for seeds 1-2) | 0.847, 20 solved | 0.903, 22 solved | 3 / 1 | 0.63 |
| Seed 0 only, author labels | 0.875, 21 solved | 0.875, 21 solved | 2 / 2 | 1.0 |
| Judge labels for all seeds | 0.847, 20 solved | 0.931, 22 solved | 3 / 1 | 0.63 |
| System prompt counted as a number source | same as primary | same as primary | 3 / 1 | 0.63 |

On seed 0 alone, graded by the author, the two systems are tied.

## Secondary: against the A3 systems

The A3 systems ran on Ollama with 4-bit weights; B2 runs on vLLM in bf16. These comparisons cross backends and precision. The A3 numbers are the published ones, with the same labels and success rule.

| | gemma4:31b | gpt-oss:120b | Fine-tuned E4B |
|---|---|---|---|
| Mean task success | 0.819 | 0.792 | 0.903 |
| Tasks solved | 20 | 18 | 22 |
| Paired, solved only by fine-tuned / only by the other | 2 / 0 (p = 0.50) | 6 / 2 (p = 0.29) | |
| Mean difference, fine-tuned minus the other | +0.083 [-0.014, 0.208] | +0.111 [-0.069, 0.292] | |

No detectable difference against either teacher. This is not a claim that the 4B model is as good as the teachers in general: the test set is 24 tasks of the kinds it was trained on, and the base E4B already scores 0.847 here, above both A3 systems.

## By task type (successful runs out of 3 per task)

| Type | Base | Fine-tuned | gemma4:31b | gpt-oss:120b |
|---|---|---|---|---|
| trend_reliability (5) | 12/15 | 15/15 | 15/15 | 13/15 |
| lookup (3) | 9/9 | 9/9 | 9/9 | 7/9 |
| revision (3) | 9/9 | 9/9 | 9/9 | 6/9 |
| definition (3) | 9/9 | 7/9 | 7/9 | 8/9 |
| mixed (4) | 6/12 | 8/12 | 8/12 | 10/12 |
| unanswerable (3) | 7/9 | 8/9 | 5/9 | 7/9 |
| injection (3) | 9/9 | 9/9 | 6/9 | 6/9 |

## What changed with fine-tuning

- **Gained**: b04 (Georgia influenza ED trend; the base skipped the smoothed series in all 3 runs), b15 (Texas reporting count against its cutoff; the base never fetched the count), b19 (Puerto Rico COVID-19 admissions, unanswerable; in seeds 1 and 2 the base ended with an empty answer, which the loop records as an answer and the judge graded incorrect).
- **Lost**: b13 (definition of reduced participation for HSAs): judged partial in seeds 1 and 2, correct in seed 0. The task is solved by the base in all 3 runs.
- **Both fail**: b23 (Charleston HSA: value, participation status and how it is set), partial with a missing caveat in all 6 runs; neither fetches the HSA's participation status.
- **Mixed runs**: the fine-tuned model succeeds in 2 of 3 runs on b18 and b24 (so they count as solved) and 1 of 3 on b13; the base 1 of 3 on b19.
- **Behavior**: the fine-tuned model makes more calls (2.33 against 1.65 per run, recall 0.889 against 0.861), includes all required numbers in all 72 runs (base 66), says the data do not have the answer on all 9 unanswerable runs (base 7), and has no injection detector hit (base 3, none followed). Median time per task is the same (1.6 s); median prompt tokens rise from 4,944 to 8,816 because of the extra tool outputs.
- **The validation loops did not appear on test.** On validation, fine-tuned checkpoints sometimes repeated `search_docs` on unanswerable questions until the turn limit (3 such items for the chosen one); on test all 72 runs ended with an answer, including the 9 unanswerable ones.

## Judge and author agreement (seed 0, 48 answers)

- Correctness: agreed on 46 of 48 (kappa 0.78); in both disagreements the author said partial and the judge correct.
- Caveat: agreed on 36 of 48 overall (kappa 0.47), and on all 12 answers to tasks that require it (kappa 1.0). Disagreement is on tasks where the caveat is optional, so it does not affect success.
- The judge needed a second attempt on b15 in 2 runs (no verdict within 16,384 tokens on the first); no answer is left without a verdict.

## Notes and limits

- **Seeds at temperature 0**: the three seeds gave different answers on 9 of 24 tasks for the base and 7 for the fine-tuned model, and different tool calls on 3 and 0. The runs are not independent samples of a sampling distribution; they show the residual nondeterminism of the server.
- **Small test set**: 24 tasks, one held-out set of states; the analysis was fixed before the runs, and none of the training or selection used them.
- **Same family**: the student and one teacher are both Gemma 4, and 69% of the training traces came from that teacher.
- **What fine-tuning bought**: on validation, which covers more question variants, a clear gain (147 against 108 of 158); on test, consistent direction but no detectable difference. A model this size answering in about 1.6 s on one GPU matches the large local models on this task set, though that comparison crosses backends.
