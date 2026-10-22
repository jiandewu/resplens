# A2 answer evaluation plan: retrieval versus the whole corpus in context

Status: pre-registered 2026-10-22, before any answer-generation run on the test split. No results yet.

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

## Records

Each run stores the configuration, model names and digests, prompt text, git commit, per-question outputs, judge outputs (including the judge's reasoning), and timing under `eval/answers/<timestamp>/`.
