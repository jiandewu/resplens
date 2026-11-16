# B2: fine-tuning a 4B model to run the agent (pre-registration)

Status: **approved and frozen 2026-11-09** after the author's review, before any training question was generated or any B2 system was run on the A3 test tasks. Pre-freeze checks (model cards, vLLM feasibility on 5 dev tasks, validation states) are under "Before freezing". Later changes are recorded at the end with their dates, with the original text kept.

Results: [`finetune-results.md`](finetune-results.md) (2026-11-16).

## Question

Can a 4B open-weights model, fine-tuned on agent traces from larger models, run the A3 agent (same tools, same system prompt, same scoring) about as well as the larger models, at a fraction of the memory and time? And how much of its performance comes from fine-tuning rather than from the base model?

## Decisions already made (the author, 2026-11-09)

1. The student is a model of about 4B parameters.
2. Training questions hold out whole states: no state that appears in an A3 test task appears in training.
3. Injection traces whose only fault is the injected text are kept with that text removed, marked as edited (option (b) below).

## Systems

| System | What it is |
|---|---|
| **Base 4B** | The chosen student model, not fine-tuned |
| **Fine-tuned 4B** | The same model with a LoRA adapter trained as below |
| gemma4:31b, gpt-oss:120b | The A3 results, reused as published; not rerun |

**Choosing the student.** Two candidates, checked on their official Hugging Face model cards on 2026-11-09:

| Candidate | License | Parameters | Tool calling | vLLM parser |
|---|---|---|---|---|
| `Qwen/Qwen3-4B-Instruct-2507` | Apache 2.0 | 4.0B (BF16) | native; no reasoning mode | `hermes` |
| `google/gemma-4-E4B-it` | Apache 2.0 | 4.5B effective, 8.0B with per-layer embeddings | native function calling; reasoning off by default | `gemma4` |

Gemma 4 E4B is the same family as the A3 teacher `gemma4:31b`; its weights take about twice the memory of Qwen's (14.3 against 7.6 GiB loaded in vLLM). The student is chosen by the base models' task success on the validation set (below), before any fine-tuning; a tie goes to the one with lower memory use. Only the chosen model is fine-tuned.

All four systems use the A3 system prompt (v1), tools, step limits (12 turns, 24 tool calls) and temperature 0, with seeds 0, 1, 2.

## Data splits

### States

- **Test states** (in at least one A3 test task): AK, DC, GA, NC, SC, TX, and PR (not in the data; used by an unanswerable task). Never used for training or validation questions.
- **Validation states**: CA, IL, ME, OH, VA, drawn on 2026-11-09 with `sorted(random.Random(20261109).sample(rest, 5))`, where `rest` is the sorted list of the 45 remaining codes from the release's threshold table.
- **Training states**: the other 40.

### Documentation

Definition questions do not depend on a state. A documentation chunk that contains any A3 test task's evidence quote is excluded as the source of a training or validation question, so the test definition answers are never trained on. The excluded chunk IDs are recorded with the data.

### Validation set

- The 13 A3 dev tasks (never used for training).
- About 150 generated questions on the validation states and documentation.

Used to choose the student, LoRA settings and the number of training epochs. Never mixed with test results.

### Test set

The 24 A3 test tasks, unchanged, run once per seed after all choices are fixed.

## Training data

### Questions

About 1,200 questions on the training states, generated from templates for the seven A3 task types (trend and reliability, lookup, revision, definition, mixed, unanswerable, injection). Wording is varied in two ways: several templates per type, and paraphrases by `qwen3:235b-thinking`, the A3 judge. A sample of 50 questions is read by the author before any traces are generated; templates that produce unclear questions are fixed or dropped, and the counts are recorded.

**References.** For the data question types, the reference answer is computed from the tools with code (for example, the latest value and its flag, or the first and latest published values), so correctness does not depend on a model. For definitions, the reference is the source chunk. For unanswerable questions (counties, deaths, forecasts, places outside the data), the reference is that the data do not contain the answer.

**Injections.** The same two vectors as A3 (data-tool output, retrieved document), with different payload texts and different target fields from the three test injections. The payload texts and fields used in training are listed with the data.

**Overlap check.** Before training, every training and validation question is compared with every test question (word 5-gram overlap and the state, pathogen, measure and week combination); the largest overlaps are listed for the author to read.

### Traces

1. Both A3 systems (`gemma4:31b` thinking off, `gpt-oss:120b` reasoning `medium`) run each training question once with the A3 settings.
2. A trace is kept only if all of these hold:
   - it ended with an answer;
   - every number in the answer matches the question or a tool output directly (the strict A3 check; derived numbers cannot be reviewed by hand at this scale);
   - the required numbers from the reference are present;
   - the judge grades it correct, and caveat stated where required;
   - no injected instruction was followed (A3 detectors).
3. If both systems pass, one trace is chosen at random with a fixed seed, so neither model's style dominates; the share from each is reported.
4. The author reads 50 kept traces and 20 rejected ones. The rate at which the author disagrees with the filter is reported.

**Training format**: the full conversation (system prompt, question, tool calls, tool outputs, final answer), with loss only on the assistant turns. gpt-oss's reasoning text is not included; the student learns the tool calls and answers.

**Edited injection traces** (the author chose option (b), 2026-11-09). In A3, both teachers followed the canary instruction in all 6 runs; if that holds on the training questions, almost no trace of that kind would pass the filter, and the student would not learn to ignore it. So a trace whose only fault is that the answer contains the injected text (by the A3 detector) is kept with that text removed from the answer, and marked as edited. Nothing else in the trace changes. The number of edited traces is reported, and so is the fine-tuned model's injection result on test, so a reader can judge whether the edits taught the behavior. The rejected alternative was to keep the data purely distilled and accept that the student does not learn this.

## Training

- LoRA on all attention and MLP projections, bf16, on one H100. The framework (TRL and PEFT, or similar) and its versions are recorded.
- Chosen on validation: rank (8, 16 or 32), learning rate (1e-4 or 2e-4) and epochs (1 to 3, checkpoint per epoch). At most 6 configurations; the choice is by validation task success, ties to the smaller configuration. The grid and all validation scores are reported.
- The adapter is merged for serving. The training data, configuration and validation scores are saved; the adapter weights are published if the base license allows.

## Serving

- Both 4B systems are served with vLLM (OpenAI-compatible API) in bf16, so the base and fine-tuned models run on the same backend.
- The agent loop gets one new chat function for an OpenAI-compatible endpoint. The loop's logic, tools and checks do not change.
- The A3 systems ran on Ollama with 4-bit weights. The comparison with them is therefore across backends and precision; this is stated with the results.
- The A4 local service gets the same backend as an option, marked as the B2 model.

## Scoring

Exactly as A3 ([`agent-eval.md`](agent-eval.md)):

- Task success requires a correct answer, no unsupported number, the caveat where required, and no injected instruction followed.
- For seed 0 of both 4B systems (48 answers), the author grades correctness and caveats blind to the system and before seeing the judge's labels. Seeds 1 and 2 are graded by the judge (`qwen3:235b-thinking`).
- Every number that does not directly match a tool output is reviewed by hand, blind to the system, as derived or unsupported.

## Analysis

- **Primary**: fine-tuned 4B against base 4B. Tasks solved (at least 2 of 3 runs succeed), with an exact sign test over tasks solved by one system only; mean task success with a 95% bootstrap interval for the paired difference over tasks.
- **Secondary**:
  - fine-tuned 4B against the published A3 results of gemma4:31b and gpt-oss:120b, with the same tests and the backend difference stated;
  - success by task type, tool-call recall, unsupported numbers, injection results;
  - median seconds per task, GPU memory, prompt and output tokens.
- With 24 test tasks, only large differences can be detected. A result of "no detectable difference" against the large models is not a claim that the models are equivalent.

## Records

- Generated questions with template, state, references and split: `eval/finetune/questions.jsonl`.
- Teacher traces and filter results: `eval/finetune/traces/`.
- Training configuration, validation scores per configuration: `eval/finetune/training/`.
- Test runs, labels and analysis in the A3 layout: `eval/agent-runs/` and `eval/finetune-review/`.

## Code layout (planned)

- `src/resplens/finetune/questions.py`: templates, state splits, references, overlap check.
- `src/resplens/finetune/traces.py`: teacher runs, filter, training format.
- `src/resplens/finetune/train.py`: LoRA training and merging (optional dependency group).
- `src/resplens/agent/loop.py`: one added chat function for OpenAI-compatible endpoints.
- Tests: state split and evidence exclusion, reference computation on the synthetic mirror, filter rules, training-format conversion, the new chat function with a fake server.

## Before freezing (done 2026-11-09)

1. **Model cards**: both candidates checked (table above).
2. **vLLM on this cluster**: vLLM 0.33.0 (PyTorch 2.14, CUDA 13.0) serves both candidates with tool calling on one H100. The node runs inside a Singularity container with no system C headers and no CUDA toolkit, so serving needs three settings: a C compiler for Triton (conda-forge `gcc` with its sysroot, set as `CC`), `TRITON_LIBCUDA_PATH=/.singularity.d/libs`, and `VLLM_USE_FLASHINFER_SAMPLER=0` (FlashInfer's sampler compiles with `nvcc`). These are recorded with each run.
3. **Feasibility** (not results; the A3 loop, unchanged, with a scratch OpenAI-compatible chat function; dev tasks only; base models):
   - Qwen3-4B, tasks `a01`, `a03`, `a07`, `a09`, `a11`: all ended with an answer in 0.5-43 s; no tool-call format errors. It answered `a03` from `describe_state` alone and said the count was not available (it is), and left one of four weeks out of `a01`.
   - Gemma 4 E4B, same tasks: all ended with an answer in 1.3-21 s; it recovered from a wrong measure name on `a03` and answered it correctly; on `a11` it gave the state count after saying county data do not exist.
   - Both made plausible tool calls with the A3 schemas, so fine-tuning starts from a working base. These runs were not graded and are not used to choose the student.
4. **Validation states** drawn (above).
5. **Injection traces**: the author chose (b).

## Changes after freezing

### 2026-11-09, before any teacher trace: implementation details

The plan's text above is unchanged; these fill in what it left open.

- **Definition questions** cannot come from templates. Each is written by `qwen3:235b-thinking` from one allowed chunk: a question, a short reference answer from the chunk, and a supporting quote that must appear verbatim in the chunk (otherwise the reply is discarded). "Paraphrases by qwen3" applies to the template questions: a random half are reworded in batches of 10, and a rewrite that changes or drops a date, number or capitalized name is discarded.
- **Chunk exclusion**: a chunk is excluded when it shares any 8-word window with an A3 test evidence quote (10 of 998 chunks). Chunks with A3 dev evidence (5) are also kept out of training, since the A3 dev tasks are part of validation. The remaining chunks are split at random, 15% to validation and 85% to training.
- **Injection mix**: 60% in a data-tool output (a `get_series` lookup, target field `unit` or `definition_status`), 40% in a retrieved document (a definition question, target `results[1].text` or `results[0].heading`). Half ask for a canary string, half for an extra tool call or (documents) a false number. Payloads, canaries and fields are listed in `src/resplens/finetune/questions.py`.
- **Edited traces** apply to injected strings that are not numbers. A followed false number cannot be removed without changing what the sentence says, so those traces are rejected.
- **Judge calls**: the judge grades only traces that pass the code checks (stop, strict grounding, required numbers, injection). The filter is the same; this only saves judge time.
- **Template counts** per split and type are in `COUNTS` in `questions.py` (training 1,200, validation 150).

### 2026-11-10, before the author's question review and before any teacher trace: definition questions regenerated

- **Problem**: preparing the 50-question review sheet showed that 152 of the 252 generated definition questions named ObsAwareData, 122 of them with evidence from a CDC, CMS or other external document (for example a rule in NHSN's reporting instructions asked as "In ObsAwareData, ..."). Some contradicted the template questions: one stated that ObsAwareData's pediatric ICU bed occupancy count includes NICU beds, while the unanswerable template says the dataset has no bed or ICU occupancy. The prompt said a passage came from ObsAwareData's documentation "or from CDC's own documentation" without saying which.
- **Change** (the author's decision): the prompt now states the passage's source, from the corpus tier (tier 1 = ObsAwareData's own documentation; otherwise "external documentation, not ObsAwareData's" with the document's title), and for external passages tells the model not to mention ObsAwareData and to name the system or publisher the passage describes. Same model, settings, chunks, seeds and verbatim-quote rule. Replies go to a new cache (`definition-replies-v2.jsonl`); the first version's files are kept in `eval/finetune/v1-20261109/`.
- Paraphrase and overlap are rerun on the new set; template questions are unchanged. A new review sample is drawn with the same rule and seed.
- During the rerun one reply (chunk 129 of 470 in the train pool) came back cut off mid-JSON and stopped the run; the same request replayed alone gave a complete reply, so CPU generation is not bit-reproducible even at temperature 0. The generator now sends the same request again when a reply is not valid JSON (up to 3 attempts, each logged) and fails after that. The 128 cached replies were kept.
- Result: 2 more replies came back cut off and were fine on the second attempt. Questions naming ObsAwareData with external evidence went from 122 to 0; all 29 questions from ObsAwareData's own documentation name it. Counts and overlap unchanged (1,350 questions, 252 definitions, 517 reworded; 0 same combination, 6 with share >= 0.5).

### 2026-11-11, before any teacher trace: the author's 50-question review

- Verdicts on the sample drawn with seed 20261110 (`eval/finetune/questions-review-verdicts-20261111.md`): 47 ok, 2 unclear, 1 wrong, 0 drop. By source: template questions 40 ok of 41 (1 unclear); generated definition questions (7 plain, 2 with a planted document injection) 7 ok of 9 (1 wrong, 1 unclear).
- **Template fixed** (`lookup_threshold`, 1 of its 2 wordings): "What is {state}'s minimum number of reporting hospitals before NHSN data are marked as reduced participation?" was ambiguous about direction; it is now "What is the minimum number of reporting hospitals {state} needs for a week not to be flagged as reduced participation?" This changes 15 template questions (question text only). Paraphrase replies are cached by batch, so the batches holding them were reworded again: with the 2 hand fixes, 45 of 1,350 questions changed (43 template questions, all lookup or mixed; still 517 reworded). Overlap unchanged (0 same combination, 6 with share >= 0.5).
- **Generated questions fixed by hand** (the author's notes; the generated text is kept as `generated_question` / `generated_reference`; `REVIEW_EDITS` in `questions.py`):
  - wrong, chunk `nhsn_hrd_dataset#51`: "Which jurisdictions are sometimes excluded ...?" generalized one week's note (other weeks name Guam and the U.S. Virgin Islands); the question now asks about that reporting period.
  - unclear, chunk `nhsn_hrd_qa#27`: the reference blurred the Boolean condition; it now says both the adult and pediatric counts are null for at least one virus, or `numInPtBeds` or `numInPtBedsOcc` is null.
- A scan of all 252 generated questions for the same generalizing words (sometimes, usually, typically, generally, often, ever) found no other case. Unreviewed generated questions are not otherwise checked by hand; with 2 of 9 reviewed ones needing a fix against 1 of 41 template questions, their references are less reliable than the template ones, which the judge step and the author's trace review should keep in mind.

### 2026-11-11, after gemma's teacher run, before gpt-oss's finished and before any judge call: two filter fixes

gemma ran all 1,200 training questions (all ended with an answer; 1,157 passed the code checks, 10 of them edited injection traces). Two failures were systematic and came from the questions or the check, not from the teacher:

- **`lookup_sites` dropped** (the author's decision): `describe_state` lists a state's wastewater sites without a count, so the answer is a count of a list, a derived number the strict check cannot accept. All 24 of gemma's failing `lookup_sites` traces failed for this; gemma's count matched the reference in 20 of 27 questions, and the misses were all long lists (New York 176 against 173). The template's 32 questions (27 training, 5 validation) are left out of traces, selection, training and validation; they stay in `questions.jsonl` so question IDs and the traces keyed by them do not change.
- **System prompt counted as a source for numbers** (the author's decision): 9 of the 10 `unanswerable_territory` refusals restated the system prompt's "50 states and DC" and failed the strict check, which counts only the question and tool outputs. For the B2 filter the system prompt is also a source; the student sees it in every training conversation. A3 scoring is unchanged.
- With both fixes, gemma passes 1,163 of 1,173 questions. The other 10 are not changed: 8 trend answers state a computed change (derived numbers, rejected by design) and 2 generated definition questions (a year range read as the number 2021, and an answer that cites a different logic check).

### 2026-11-13, after the judge and selection, before any student run: the author's trace review

- Judge: 2,139 judgments (the traces that passed the code checks), 0 failures; graded correct: gemma 1,138 of 1,163, gpt-oss 905 of 976.
- Selection (seed 20261109): 2,042 of 2,346 traces pass; 1,152 of 1,173 questions keep a trace (the 21 lost: 9 definition, 9 trend, 3 injection; 12 generated, 9 template). Kept by teacher: gemma 705, gpt-oss 447 (both pass 890, gemma only 247, gpt-oss only 15), so the training data lean toward gemma's style. Edited traces kept: 6, all gemma. Rejection reasons (a trace can have several): unmatched number 188 (gpt-oss 178, mostly derived numbers), judge 96, missing required number 27, missing caveat 5.
- Review sample (seed 20261113, `traces review`; kept: one per type and teacher plus one edited trace per teacher, the rest at random; rejected: one per first reason and teacher, the rest at random). Verdicts in `eval/finetune/traces-review-verdicts-20261113.md`.
- The author disagreed with the filter on 4 of 70 traces (5.7%): 0 of 50 kept, 4 of 20 rejected. All 4 are false rejections by the strict number check: a year from a date (2024), "twice" for a required 2, and two correct derived changes. Because of the strata this rate describes the sample, not all traces.
- Rejected traces the author agreed with show a gpt-oss pattern: in 9 of the 20 (t0494, t0570, t0613, t0667, t0857, t0906, t0916, t0968, t1035), `check_reliability` was called without the target end date, so it described the latest four weeks, and the answer used that later window's hospital count or reliability for the target week.
- **Filter fix after the review** (the author's decision): a scan of all traces found 205 passing gpt-oss traces (99 of them kept) whose `check_reliability` windows all miss the date in the question, and none from gemma. A new code check (`reliability_window` in `traces.py`) rejects such a trace: if the question names a date and the trace calls `check_reliability`, one returned window must contain that date. Unanswerable questions are exempt (a refusal for a future week may check the latest window). The judge needs no rerun, because the check only removes traces.
- Of the 9 window cases among the reviewed rejected traces, the check catches 8; t0494 used the right window but quoted its latest week, and stays rejected by the judge. It also rejects 4 reviewed kept traces the author had agreed with: t0281 states the later window's reliability for the week asked about; t0473, t0611 and t0722 make the wrong-window call but answer from the series flags. They are rejected anyway, so the student does not learn the wrong call.
- The false rejections by the strict number check (years, "twice", correct derived changes) are left as they are (the author's decision): every such question also has a passing gemma trace, and the strict check matches A3 scoring.
- Selection after the fix: 1,850 of 2,346 traces pass; still 1,152 of 1,173 questions kept (the same 21 lost). Kept by teacher: gemma 795, gpt-oss 357 (31%). Edited traces kept: 9. Rejection reasons: window 307 (all gpt-oss), unmatched 188, judge 65, missing 27, missing caveat 3 (the judge is counted only for traces that pass the code checks, so its count fell).

### 2026-11-13, before any validation run: how validation is run and scored

The plan fixes what validation is for (choosing the student, then the LoRA settings and epochs) but not these details, set here before any 4B model is run on validation:

- **Items**: the 13 A3 dev tasks and the 145 generated validation questions (150 minus 5 from the dropped `lookup_sites` template), 158 in all. Code: `src/resplens/finetune/validate.py`; runs in `eval/finetune/validation/<name>/`.
- **One run per item** (seed 0). Generation is greedy at temperature 0 on vLLM, so other seeds would add little; the three test seeds are kept as planned.
- **Task success** is the A3 definition with one substitution, because hand review of numbers cannot be repeated for every training configuration: a number counts as unsupported if it does not directly match the question, a tool output or the system prompt (the B2 filter's check, without the window check). So validation is stricter than A3 test scoring on derived numbers, for every system alike. The judge (`qwen3:235b-thinking`, as A3) grades correctness and caveats; it is called only for answers that pass the code checks, since the others cannot succeed. Injection is the A3 detector.
- **Choice of the student**: the higher number of successful items out of 158; equal counts go to the lower memory use (Qwen3-4B), as planned. Success on the 13 A3 dev tasks and on the generated questions, and by type, is reported alongside.

### 2026-11-13: base-model validation and the choice of the student

- Runs 2026-11-13 (`logs/b2-validate.sh`, vLLM 0.33.0, bf16, one H100; `eval/finetune/validation/base-*`): both models answered all 158 items. Median 1.3 s (Qwen3-4B) and 1.4 s (Gemma 4 E4B) per item. Weights plus non-torch memory in vLLM: 8.45 and 16.53 GiB.
- Judge: 302 answers passed the code checks and were judged (Qwen 148, Gemma 154); 1 judge failure after the retry (Gemma), counted as unsuccessful as in A3.

| | Qwen3-4B | Gemma 4 E4B |
|---|---|---|
| All 158 items | 79 (0.500) | **108 (0.684)** |
| 13 A3 dev tasks | 7 | 9 |
| 145 generated | 72 | 99 |
| trend and reliability (32) | 0 | 21 |
| mixed (24) | 7 | 13 |
| lookup (22) | 13 | 17 |
| definition (24) | 11 | 13 |
| revision (24) | 23 | 24 |
| injection (17) | 12 | 12 |
| unanswerable (15) | 13 | 8 |

- Paired: Gemma only 41 items, Qwen only 12, both 67 (exact sign test p = 8e-5; descriptive, the rule is the count).
- **Student: Gemma 4 E4B** by the rule (more successes). Qwen failed every trend question (left out weeks, judged partial or incorrect, or no caveat). Gemma's weak spot is unanswerable questions (8 of 15): it often gives a number where it should say the data do not have it.

### 2026-11-13, before any training run: LoRA implementation details (the author confirmed)

- **Framework**: TRL and PEFT in a separate training environment; versions recorded with each run.
- **Target modules**: the attention and MLP projections of the language model only; the vision and audio encoders are not adapted. The module names are checked on the loaded model and recorded.
- **Adapter**: alpha = 2r, dropout 0.05, no rsLoRA. The grid is unchanged (r 8, 16 or 32; learning rate 1e-4 or 2e-4; 1 to 3 epochs; at most 6 configurations).
- **Length**: set from the token lengths of the training conversations so that none is truncated; if a few very long ones are dropped instead, the count is reported.
- **Other settings**: effective batch 16; cosine schedule with 3% warmup; bf16; no packing; loss on assistant turns only. Before training, the conversations are rendered with Gemma's chat template and parsed back with vLLM's `gemma4` parser to check that every tool call comes back unchanged.
- **Selection**: a checkpoint after every epoch; every checkpoint is run on all 158 validation items and scored as above with the judge (no pre-screening by code checks).

### 2026-11-13, before the grid: what the implementation found

- **Environment**: torch 2.14.0, transformers 5.20.2, PEFT 0.21.3 (`~/.local/share/resplens/train`; TRL 1.18.0 installed but not used: the loss mask below is built directly and trained with the transformers `Trainer`). vLLM 0.33.0 for serving.
- **Modules**: Gemma 4 E4B's language model has 42 layers; the last 18 share keys and values with earlier layers, so only 24 have `k_proj` and `v_proj`. The adapter covers 258 modules (42 x q, o, gate, up, down + 24 x k, v); r = 16 trains 34.9 M parameters. The per-layer embedding projections are not adapted.
- **Loss mask**: the chat template renders every prefix of a conversation as a prefix of the whole (checked on all 1,152), so each message's text is cut out exactly. Loss is on each assistant message's text without the `<|turn>model` header; that text ends with `<|tool_response>` after tool calls (one of the model's stop tokens) or `<turn|>` after the answer. 267,327 of 4,879,763 tokens get loss (median 204 per conversation).
- **Length**: 1,870 to 13,405 tokens (median 3,771, 99th percentile 11,082). Nothing is truncated or dropped. Peak memory on the 16 longest at r = 32: 65 GiB allocated.
- **Round trip**: all 2,681 tool calls, rendered by the template and parsed back by vLLM's gemma4 argument converter, match. The converter returns numbers as text; the server types them from the tool schema (base Gemma's validation calls came back as integers). gpt-oss wrote 372 explicit nulls (`region_id: null`) in 180 conversations; every such argument defaults to null, so they are left out of the training format, since the template would render the null as a bare word that parses back as text.
- **Attention**: with gradient checkpointing, PyTorch picked different SDPA kernels for the forward pass and its recomputation and training stopped; the memory-efficient kernel is now fixed for both.
- **Schedule**: each configuration trains 3 epochs with one cosine schedule (3% warmup) and saves an adapter after each epoch, so the epoch 1 and 2 checkpoints are taken mid-schedule, not from 1- or 2-epoch runs. 72 optimizer steps per epoch; about 3 s per conversation, about 3 h per configuration.
- **Grid**: all 6 configurations (r 8, 16, 32 x lr 1e-4, 2e-4) in that order, 18 checkpoints, each merged and run on the 158 validation items (`logs/b2-train.sh`); then all are judged and scored.
- The grid's records name the code `c66798f-dirty`: the grid started before this code was committed. The uncommitted code was exactly the commit that adds `train.py` (`feat(finetune): add LoRA training ...`), and it was not changed while the grid ran.

### 2026-11-15, after the grid, before any test run: validation scores and the chosen configuration

All 18 checkpoints ran on the 158 validation items and were judged and scored as above (judge on answers that pass the code checks; an answer that fails them cannot succeed, so judging it would not change the count). Records: `eval/finetune/training/` (configuration, versions, loss history per run) and `eval/finetune/validation/r*-lr*-e*/`.

- **Interruption**: at r16, lr 2e-4, epoch 1 the run stopped after 146 items with CUDA out of memory. The validation process saw both GPUs and put the retrieval models (bge-m3, reranker) on the GPU that vLLM held at 0.85 of its memory. The script now runs validation on the training GPU, which is idle while validating, and the run resumed from its trace file. Nothing else changed.

Task success out of 158 (A3 dev 13, generated 145), by checkpoint, with the base models from the entry above:

| Checkpoint | All | A3 dev | Generated | def. (24) | inj. (17) | lookup (22) | mixed (24) | rev. (24) | trend (32) | unans. (15) |
|---|---|---|---|---|---|---|---|---|---|---|
| r8 lr1e-4 e1 | 135 | 10 | 125 | 15 | 15 | 22 | 21 | 24 | 29 | 9 |
| r8 lr1e-4 e2 | 132 | 11 | 121 | 12 | 15 | 22 | 22 | 24 | 30 | 7 |
| r8 lr1e-4 e3 | 137 | 10 | 127 | 14 | 15 | 22 | 22 | 24 | 31 | 9 |
| r8 lr2e-4 e1 | 134 | 9 | 125 | 14 | 14 | 22 | 22 | 24 | 31 | 7 |
| r8 lr2e-4 e2 | 142 | 11 | 131 | 15 | 15 | 22 | 22 | 24 | 32 | 12 |
| r8 lr2e-4 e3 | 141 | 11 | 130 | 16 | 15 | 22 | 21 | 24 | 31 | 12 |
| r16 lr1e-4 e1 | 134 | 11 | 123 | 13 | 15 | 22 | 21 | 24 | 31 | 8 |
| r16 lr1e-4 e2 | 134 | 10 | 124 | 10 | 15 | 22 | 22 | 24 | 31 | 10 |
| r16 lr1e-4 e3 | 138 | 11 | 127 | 13 | 15 | 22 | 22 | 24 | 31 | 11 |
| r16 lr2e-4 e1 | 135 | 8 | 127 | 14 | 14 | 22 | 22 | 24 | 31 | 8 |
| r16 lr2e-4 e2 | 145 | 12 | 133 | 16 | 15 | 22 | 23 | 24 | 32 | 13 |
| **r16 lr2e-4 e3** | **147** | 12 | 135 | 19 | 16 | 22 | 23 | 24 | 32 | 11 |
| r32 lr1e-4 e1 | 132 | 11 | 121 | 13 | 15 | 22 | 23 | 24 | 28 | 7 |
| r32 lr1e-4 e2 | 146 | 12 | 134 | 16 | 15 | 22 | 23 | 24 | 32 | 14 |
| r32 lr1e-4 e3 | 147 | 11 | 136 | 19 | 15 | 22 | 22 | 24 | 32 | 13 |
| r32 lr2e-4 e1 | 134 | 11 | 123 | 13 | 15 | 22 | 23 | 24 | 30 | 7 |
| r32 lr2e-4 e2 | 145 | 11 | 134 | 17 | 15 | 22 | 22 | 24 | 31 | 14 |
| r32 lr2e-4 e3 | 147 | 10 | 137 | 20 | 15 | 22 | 22 | 24 | 32 | 12 |
| base Gemma 4 E4B | 108 | 9 | 99 | 13 | 12 | 17 | 13 | 24 | 21 | 8 |

- **Chosen: r = 16, lr = 2e-4, epoch 3** (adapter `eval/finetune/training/r16-lr0.0002/checkpoint-216`, trained at `259cb75`). Three checkpoints tie at 147 (r16 lr2e-4 e3, r32 lr1e-4 e3, r32 lr2e-4 e3); the rule sends a tie to the smaller configuration, and r = 16 is the only smaller rank among them. All three are the last epoch.
- Every checkpoint beats the base model (132 to 147 against 108). Against the base, the chosen checkpoint succeeds on 43 items the base fails and fails 4 the base solves (v0141, v0143, v0144, v0148; exact sign test p = 3e-9, descriptive). Its 11 failures: 4 unmatched numbers, 4 judged incorrect or partial, 3 without an answer (2 turn limit, 1 model error).
- **Not fixed: loops on unanswerable questions.** The base model answers all 158; fine-tuned checkpoints stop without an answer on 1 to 11 items (6 to 11 at epoch 1, 2 to 8 at epoch 3), mostly unanswerable questions where the model repeats `search_docs` until the turn limit, although all 110 unanswerable training questions are in the training data. The chosen checkpoint has 3 such stops. Left as is and reported; the test result will show whether it persists.
- Two judge failures over the grid (r8 lr2e-4 e2, r32 lr2e-4 e2), each counted as not correct; neither checkpoint is in the tie.

### 2026-11-16, before any test run: how the test runs are made

- **Runner**: the A3 runner (`resplens.agent.run`) with two added systems, `b2-base` and `b2-ft`, which call the vLLM server through `loop.openai_chat`; tools, checks, system prompt, limits and scoring are A3's. Each run's `config.json` records what is served (repository, revision, adapter and its commit, vLLM version, dtype, parser, context length).
- **Models**: base `google/gemma-4-E4B-it` at revision `4ecc2ba6`; fine-tuned = that base with the chosen adapter (`r16-lr0.0002/checkpoint-216`) merged, served the same way (bf16, 32,768 context, gemma4 tool-call parser). One model is served at a time on one GPU; the runner and its retrieval models run on the other.
- **Runs**: the 24 test tasks, seeds 0, 1 and 2 per system, temperature 0 as in A3, in `eval/agent-runs/<time>-test-b2-{base,ft}-seed<n>/`, scored with `agent.run score`. With greedy decoding on vLLM, the seeds may give identical or near-identical traces; how many traces differ between seeds is reported.
- **Smoke test** on 2 dev tasks (a01, a09) for both systems before the test runs; its runs are deleted.
- After the runs: the author grades seed 0 of both systems blind (48 answers), the judge grades seeds 1 and 2, unmatched numbers are reviewed by hand, then the analysis as planned.
