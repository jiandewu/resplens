# A2 answer evaluation plan: retrieval versus the whole corpus in context

Status: complete, 2026-10-22. The plan was pre-registered before any answer-generation run on the test split; notes recorded during the dev and test runs, results, and failure analysis follow it.

## Question

The corpus (28 documents, about 131,000 tokens for the generator) fits in a long-context model. Does retrieval still earn its place? Compare answers generated from retrieved passages with answers generated from the whole corpus, on correctness, unsupported claims, abstention, citations, latency, and cost.

## Systems

Both use the same generator and instructions; only the context differs.

| System | Context given to the generator |
|---|---|
| RAG | Top 5 chunks from hybrid retrieval (BM25 + `BAAI/bge-m3`) with cross-encoder reranking, 300-token chunks: the pre-registered configuration 4 of `retrieval-eval.md` |
| Long context | All 28 documents, each wrapped with its document ID |

- Generator: `gemma4:31b` (Q4_K_M) via Ollama, temperature 0, thinking off. Long-context runs use `num_ctx` 262,144; every call checks that prompt tokens plus the output limit fit the window and fails otherwise.
- Instructions: answer only from the provided documents; cite the document IDs used; if the documents do not answer the question, say so explicitly.
- Prompt wording is tuned on the dev split only, then frozen before the test run.

## Questions

Test split: 25 questions, 21 answerable and 4 unanswerable. Each system answers each question once.

## Scoring

**Judge**: `qwen3:235b-thinking` via Ollama, a different model family from the generator. For each answer the judge sees the question, the reference answer, the evidence quotes, and the generated answer (not the system's context), and returns JSON:

- `correctness`: `correct`, `partial`, or `incorrect` against the reference answer.
- `unsupported_claims`: whether the answer states facts that neither the reference answer nor the evidence supports (a proxy for hallucination; the judge does not see the whole corpus, so a true statement found elsewhere in the corpus can be counted here; such cases are reviewed by hand).
- For unanswerable questions: `abstained`, whether the answer says the documents do not answer the question.

**Programmatic**:

- Citation recall: the answer cites at least one document that contains an evidence quote.
- Latency: RAG per question including retrieval; long context cold (prompt not cached) and warm (document prefix cached), measured separately.
- Tokens per question: prompt and output.

**Human calibration**: 15 of the 50 answers, stratified by system and question type, scored by the author blind to the judge's labels and to which system produced the answer. Report agreement and Cohen's kappa on `correctness`; if agreement is poor, report human scores for those 15 and treat judge results as unreliable.

## Analysis

- Primary: correctness rate per system with paired comparison on the same questions (exact sign test on questions where they differ, paired bootstrap interval).
- Secondary: unsupported-claim rate, abstention on the 4 unanswerable questions, citation recall, latency, and prompt tokens.
- With 21 answerable questions, only large differences can be detected; small differences are reported as inconclusive.
- Failure analysis for every incorrect answer: retrieval miss, generation error, or question problem.

## Notes recorded after the dev run, before the test run (2026-10-22)

- **Prompt frozen unchanged.** On the 15 dev questions every answer ended with a parseable `Sources:` line. Abstentions used varied wording ("The provided documents do not state ...") instead of the exact sentence, and some listed sources; the judge's `abstained` label does not depend on exact wording, and citations are not scored for unanswerable questions, so the prompt was not changed.
- **No warm long-context measurement is possible with this generator.** In Ollama 0.20.0, `gemma4:31b` reused its KV cache only for an identical prompt: on a 13,223-token prompt, prefill took 6.94 s, then 0.02 s for the identical prompt, and 6.93 s when only the question at the end changed. `qwen3-vl:32b` on the same server reused the shared prefix (6.6 s, then 0.04 s with a new question). This is consistent with Gemma's sliding-window attention preventing partial-prefix reuse in this runtime, but the cause was not verified. Every long-context answer with `gemma4:31b` therefore re-reads the whole corpus (about 125 s per question on one H100 NVL). Results report this measured latency, plus one cold start that includes model loading, and note that a runtime or model with prefix caching would change the latency comparison but not the correctness comparison.

- **Judge rubric clarified on dev, before judging the test split.** The first dev judging (kept as `judgments-v1.jsonl`) followed the rubric literally in two ways that did not match its intent: an answer that named the right unit but said the documents did not give the count was graded `incorrect` (the rubric said abstaining on any part made an answer incorrect), and an answer that gave both numbers the question asked for was graded `partial` for omitting a third number that only the reference mentioned. The rubric now grades the facts the question asks for, and treats a partly abstaining answer as `partial`. Grades that contradicted the evidence (for example, a denominator described by geography instead of age group) were unaffected.
- **Unsupported-claim flags need a corpus check.** The long-context system sees the whole corpus and often adds true details that are not in the evidence quotes (for example, how the wastewater baseline is defined); the judge, which sees only the evidence, flags these. Every flagged answer is checked against the corpus by hand and reported as either supported elsewhere in the corpus or not found.
- **Judge now sees the full source documents (third dev judging, before the test split).** With the clarified rubric, a correct and more specific long-context answer (it named the metadata file that lists the revision-history downloads, which the data dictionary documents) was downgraded to `partial` because the step was not in the evidence quotes. Grading from evidence sentences alone penalizes the system that sees more of the corpus. The judge now also receives the full text of every document that contains an evidence quote (up to about 28,000 tokens; `num_ctx` 65,536), `unsupported_claims` is defined against those documents as well, and the rubric states that extra details never lower correctness. The two earlier dev judgings are kept as `judgments-v1.jsonl` and `judgments-v2.jsonl`.

## Notes recorded during the test judging (2026-10-22)

- **Output cap added after 9 of 50 test judgments.** Judgments took 13 to 90 seconds each, but the judge did not stop on the 10th item (q14, RAG answer) and the request timed out after one hour; the 9 completed judgments were kept. The judge now has an output cap of 8,192 tokens (thinking plus verdict; the longest completed reasoning so far was about 19,000 characters, well under it), a 15-minute request timeout, and one retry with a different seed. An item with no verdict after the retry is recorded as `judge_failed` and reported, not dropped. The rubric and prompt are unchanged.

## Results (test split, 2026-10-22)

Run: `eval/answers/20261022-123659-test/`. The answers were generated from code later committed as `a3275f4` (the run records `fa29ee9-dirty`); judging used the frozen third rubric with the output cap described above.

Run records, checked 2026-10-23: the dev run records a clean `fa29ee9`, but `answer.py` was not yet committed; the dirty check of the time ignored untracked files (now fixed; see the correction in `retrieval-eval.md`). The system prompt, context sizes, output limit, and top k saved in both runs' `config.json` match `a3275f4`, and the RAG chunk IDs saved for every question (15 dev, 25 test) are reproduced exactly by the committed retrieval code. Generation itself was not rerun. Judging recorded no commit at the time; judgments now carry the judge model and commit on every row, and answer runs record the commit at the start of the run rather than at the end.

### Judge as pre-registered

| | RAG | Long context |
|---|---|---|
| Correct (of 21 answerable) | 17 | 20 |
| Partial / incorrect | 1 / 2 | 0 / 1 |
| Judge failed (no verdict after a retry) | 1 (q22) | 0 |
| Judge `abstained` on the 4 unanswerable | 2 | 2 |
| Answerable questions where the system said the documents do not answer | 2 | 0 |
| Answers flagged for unsupported claims | 4 | 3 (incl. unanswerable) |
| Citation recall (cites a document that contains the evidence) | 0.90 | 0.95 |
| Prompt tokens, median | 1,273 | 130,005 |
| Seconds per question, median | 1.7 | 125.5 (cold start with model load: 132.5) |

Paired correctness: long context correct where RAG was not on 4 questions, the reverse on 1; sign test p = 0.38.

**Human calibration**: the author scored 15 answers (8 long context, 7 RAG) blind to system and judge. Agreement with the judge's correctness labels: 15 of 15 (Cohen's kappa 1.0). The human labels were concentrated (14 correct, 1 incorrect), so the sample says the judge agrees on clear cases; it says little about borderline ones.

### Manual checks (pre-registered for unsupported claims; the rest reported as corrections to judge fields)

- **Unsupported claims: none found.** Every flagged detail is in the corpus: the CITATION.cff pointer and "weeks end on Saturday" (`oad_readme`), the Missouri exclusion (NSSP documentation), and the `ID:113` site example (`oad_data_dictionary`). Most flags came from unanswerable questions, where the judge had no source documents to check against. Neither system stated a fact that is absent from the corpus.
- **Abstention: 4 of 4 for both systems.** All 8 answers to unanswerable questions say the documents do not give the answer; the judge's `abstained` field was false for the 4 that added a sentence of related context. Correctness was `correct` for all 8.
- **q22, RAG (judge failed):** the answer gives both facts asked for (they must report, once a year beginning in January). Graded `correct` by the author; reported separately from judge grades.
- **q25, long context (judge: incorrect) is contestable:** the answer says the week is rising when the slope's 95% confidence interval "is positive and does not contain 0", which is equivalent to the reference (interval excludes 0 and the slope estimate is positive); the judge objected to calling an interval positive. Left as graded.

### Failure analysis

| Question | System | Grade | Cause |
|---|---|---|---|
| q15 | RAG | incorrect | Retrieval miss: the South Carolina row of the threshold table was not in the top 5; the model said the documents do not answer |
| q19 | RAG | incorrect | Retrieval miss: formula text from a PDF table; the model said the documents do not answer |
| q28 | RAG | partial | Answered from a different, also correct, description of the site ID (ObsAwareData) and omitted "arbitrary integer" |
| q25 | long context | incorrect (contestable) | See above |

### Conclusion

On this 74,000-word corpus, answering from the whole corpus in context was right on 20 of 21 questions and retrieval on 17 to 18 (counting the author-graded q22); with the author's grade for q22 the paired comparison is 3 to 1 (p = 0.63). The difference in correctness is not reliable at this sample size. The cost difference is: the long-context prompt was about 100 times larger and, with this generator and runtime, each answer took about 73 times longer. Every RAG error came from retrieval missing the evidence, and in those cases the model said the documents did not answer rather than inventing one; neither system stated facts absent from the corpus. Improving retrieval for table rows and PDF-extracted formulas, or routing table lookups to structured tools, addresses the RAG errors directly.

## Records

Each run stores the configuration, model names, the generator's prompt text, git commit, per-question outputs, judge outputs (including the judge's reasoning and seed), and timing under `eval/answers/<timestamp>/`. (Correction: the plan also listed model digests; they were not recorded. The judge prompt is in `judge.py` at the recorded commit, not in the run directory.)
