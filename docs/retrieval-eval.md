# A2 retrieval evaluation plan

Status: complete, 2026-10-22. The plan below was written before any experiment; the pre-registered configurations, test results, and findings follow it. Where the work departed from the plan, the plan's text is kept and the change is noted.

## Questions this stage answers

1. When is retrieval needed at all? ObsAwareData's own documentation is about 5,300 words and fits in a prompt, so retrieval must beat the simple alternative of putting everything in context.
2. On a corpus too large for that (CDC documentation of NHSN, NSSP, and NWSS), which retrieval setup finds the passage that answers a question, and at what cost?

## Corpus

Two tiers, each recorded in `corpus/manifest.csv` with source URL, retrieval date, SHA-256 of the fetched file, license note, and word count:

- **Tier 1, ObsAwareData docs** (CC BY 4.0): `README.md`, `DATA_DICTIONARY.md`, `METHODS.md`, `DATA_SOURCES.md` at the pinned data tag.
- **Tier 2, CDC documentation**: public pages and documents on the three surveillance systems (list under review). Raw files are kept unchanged; text extraction is a separate, logged step.

State quality reports are not in the corpus: they hold state-specific numbers that the A1 tools already return.

## Question set

`eval/questions.jsonl`, one question per line:

```json
{"id": "q017", "split": "test", "type": "definition", "tier": 2,
 "question": "What does a hospital's NHSN respiratory reporting requirement cover?",
 "answer": "...",
 "evidence": [{"doc": "nhsn_hrd_faq", "quote": "exact sentence from the source"}],
 "origin": "llm_draft", "reviewed": false}
```

- About 40 questions: 15 `dev` for tuning, 25 `test` used once at the end.
- Types: definition or field meaning, number or date, multi-passage, cross-document comparison, and unanswerable (about 15%, to test abstention later in A3).
- Drafted by an LLM from the source text with an exact evidence quote, then reviewed by hand; `origin` and `reviewed` record this. Questions are fixed before any tuning.
- Evidence is matched by quote text, not chunk ID, so different chunkings can be compared.

## Metrics

- **Recall@k** (k = 1, 3, 5, 10): a retrieved chunk contains an evidence quote (whitespace- and case-normalized match). Multi-passage questions need every quote.
- **MRR** of the first matching chunk.
- **Cost**: index build time, index size, query latency (p50, p95).
- Answer quality (correctness, faithfulness, abstention) is measured in A3, where answers are generated. (Changed: it was measured in A2 instead, comparing retrieval with the whole corpus in context; see `answer-eval.md`.)

## Systems compared

| Factor | Values |
|---|---|
| Lexical | BM25 |
| Dense | two or three open embedding models (chosen at build time; names and versions recorded) |
| Hybrid | BM25 + dense with reciprocal rank fusion |
| Reranking | none, cross-encoder over the top 30 |
| Chunking | about 200, 400, 800 tokens; split at headings first |
| Long-context baseline (Tier 1 only) | whole document set in the prompt; measured in A3, since it has no ranking |

Changed during the work: chunk sizes became 200, 300, and 400 embedding tokens for `nomic-embed-text-v2-moe` (512-token input limit) and 300 to 512 for `bge-m3`; the long-context baseline used the whole corpus (both tiers), because it fits in the generator's window, and was measured in A2 (`answer-eval.md`).

One factor at a time from a BM25 baseline on `dev`, then the best combination and the baseline once on `test`.

## Smoke-test findings (2026-10-22, local gemma4:31b Q4_K_M on one H100 NVL, Ollama 0.20.0)

These are single runs that shaped the design, not results.

- The built corpus (28 documents, 74,368 words at the time; 74,405 after the extraction fixes below) is about 131,000 tokens for this model, about 1.76 tokens per word because of tables and identifiers. The HRD column dictionary alone is about 28,000 tokens.
- Whole corpus in context with `num_ctx` 131,072: the prompt filled the window with no room for output. The model answered a threshold question with a wrong number and an invented "quote". With `num_ctx` 262,144 the same question was answered correctly with exact quotes. **Rule: every long-context run checks that prompt plus maximum output fits in the window, and fails otherwise.**
- Cost of the long-context baseline: about 125 s to read the prompt cold and about 10 s per question when the document prefix is cached; 69 GB of GPU memory at 262,144 context. (Correction: the 10 s figure was most likely a repeat of the identical prompt. A controlled measurement later showed that `gemma4:31b` in this runtime reuses its cache only for an identical prompt, so a new question re-reads the whole corpus, about 125 s; see `answer-eval.md`.) Results must report cold and cached latency separately, since hosted APIs also cache and bill cached input differently.
- `nomic-embed-text-v2-moe` accepts at most 512 tokens per input, so chunks for that model must stay below about 400 tokens.

## Implementation findings (2026-10-22)

- Word-based token estimates were off by up to 5.8x (median 1.4x) against the embedding tokenizer, because of URLs, identifiers, and tables; 16 chunks of a nominal 200 tokens overflowed the 512-token input of `nomic-embed-text-v2-moe`. Chunks are now sized with the model's own tokenizer (XLM-RoBERTa, shared by nomic v2 and bge-m3; exact match with Ollama's counts on 196 chunks), the heading path counts toward the budget, and embedding requests disable truncation so an overflow fails loudly.
- Socrata dataset descriptions are HTML; long `<li>` lists of URLs became single 269-token "words". The extractor now converts that HTML to plain text.
- Split tables repeat their header row in every chunk, so a single row still says what its columns mean.
- Ollama's build of `bge-m3` returned NaN for some inputs, deterministically (one question failed whenever it included the word "total,"); `bge-m3` now runs with sentence-transformers at a pinned revision. nomic v2 runs through Ollama.
- `nomic-embed-text-v2-moe` cannot take 512-token chunks with its `search_document: ` prefix; it was tested at 200, 300, and 400 tokens.

## Pre-registered test configurations (fixed 2026-10-22, before any test-split run)

Chosen from dev results (13 answerable questions; differences there are within noise). All use 300-token chunks with heading paths:

1. BM25 (baseline)
2. Dense, `BAAI/bge-m3`
3. Hybrid: BM25 + `BAAI/bge-m3`, reciprocal rank fusion
4. Hybrid + cross-encoder reranking of the top 30 with `BAAI/bge-reranker-v2-m3` (the RAG configuration carried into the long-context comparison)

Each runs once on the test split. Latency is measured after the models are loaded; the first query's warm-up is not representative.

## Test results (2026-10-22)

Test split, 21 answerable questions (25 minus 4 unanswerable), 300-token chunks, reviewed question set. Runs are in `eval/runs/`. Latency is per query on one H100 NVL after models are loaded, including query encoding and reranking.

| Configuration | Recall@1 | Recall@5 | Recall@10 | MRR | Latency p50 |
|---|---|---|---|---|---|
| BM25 | 0.29 | 0.48 | 0.52 | 0.38 | 1 ms |
| Dense, bge-m3 | 0.38 | 0.62 | 0.76 | 0.48 | 9 ms |
| Hybrid, BM25 + bge-m3 | 0.38 | 0.57 | 0.71 | 0.47 | 10 ms |
| Hybrid + rerank | 0.33 | **0.86** | **0.86** | 0.50 | 206 ms |

Paired comparisons on the same questions (exact sign test on questions where the two disagree; 95% paired bootstrap interval of the difference):

- Hybrid + rerank vs BM25, Recall@5: 8 gained, 0 lost, p = 0.008, difference +0.38 [+0.19, +0.62].
- Hybrid + rerank vs dense, Recall@5: 5 gained, 0 lost, p = 0.06, +0.24 [+0.05, +0.43].
- Dense vs BM25, Recall@5: 4 gained, 1 lost, p = 0.38.
- No configuration differs reliably at Recall@1; reranking finds the evidence within the top five but does not reliably put it first.
- Hybrid fusion did not improve on dense alone here (it did on dev); with 21 questions this is within noise.

Questions the final configuration misses in the top five:

- **q15**, a South Carolina threshold in a 50-row table: the question says "South Carolina", the table says "SC", and the answer is one row of numbers. Table lookups are a poor fit for text retrieval; in the agent stage they belong to structured tools.
- **q19**, two quotes of formula text extracted from a PDF table.
- **q28**, a definition question (to be analysed with the answer-generation results). Analysed in `answer-eval.md`: the RAG answer used a different, also correct description of the site ID from the ObsAwareData documentation and was graded `partial`.

The test split was run twice with identical configurations: the first run cached query embeddings, which understated dense and hybrid latency. Query encoding is no longer cached; retrieval metrics were identical in both runs.

### Correction to the run records (2026-10-23)

The four test runs record `git_commit` `035f3ec`, but that commit predates the code that produced them: dense, hybrid, and reranked retrieval were committed afterwards in `6e2a9d5`, and the reviewed question set in `086cc93`. At the time the commit stamp had no dirty check; the check added later (`19ba982`) ignored untracked files, so a new, uncommitted module still looked clean. The corpus is not affected: every run records the manifest hash `913342e9b6d4ecec`, which is the manifest committed in `6e2a9d5`.

To settle what the runs used, all four were rebuilt from committed code with an empty embedding cache (document embeddings recomputed) and compared question by question: the retrieved chunk IDs and evidence ranks are identical for all four, so the published results are reproducible from the committed code. The dirty check now includes untracked files under the run inputs (`src`, `corpus`, `eval/questions.jsonl`, `pyproject.toml`, `uv.lock`), with a test.

## Statistics and records

- Retrieval is deterministic; each configuration runs once.
- 95% bootstrap intervals over questions; paired comparisons between configurations on the same questions.
- With 25 test questions, differences under about 10 points of recall are likely noise; results say so.
- Each run stores configuration, corpus manifest hash, model names, git commit, and per-question results under `eval/runs/<timestamp>/`.
- Commit IDs in run records and in these documents refer to the development history; the public repository has one commit per milestone, so they cannot be checked out there. The code that produced the published results is in the public milestone commit that added them.
