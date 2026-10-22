# resplens

Reliability-aware AI tools for US respiratory surveillance data (COVID-19, influenza, RSV).

Public health surveillance numbers are revised after publication, some weeks rest on few reporting hospitals, and some sudden jumps are reporting artifacts. An AI assistant that reads these numbers at face value will state wrong trends with confidence. resplens gives language models tools that return every value **with its reliability flag**, summarize what can and cannot be trusted, and reconstruct what was known on any past date.

The data come from [ObsAwareData](https://github.com/DMA-PRIME/ObsAwareData) (CC BY 4.0): weekly CDC hospital admissions (NHSN), emergency department visits (NSSP), and wastewater (NWSS) for the 50 states and DC, with a flag on every value and the full revision history.

## Status

| Stage | Contents | State |
|---|---|---|
| A1 | Data tools and MCP server | Done |
| A2 | Retrieval over data documentation, with a retrieval evaluation | Retrieval done; answer comparison in progress |
| A3 | Agent that answers trend and reliability questions, with a task evaluation | Planned |
| B1 | Real-time forecasting benchmark on as-of data | Planned |
| B2 | Fine-tuned small model for tool calling | Planned |
| A4 | Deployed service | Planned |

## Tools

| Tool | What it returns |
|---|---|
| `describe_measures` | Measures, the pathogens and region types each is published for, and the reliability flag codes |
| `describe_state` | Coverage dates, flag thresholds, ED regions, and wastewater sites for a state |
| `get_series` | Weekly values of one measure with a flag on every week |
| `check_reliability` | Recent data quality across hospital, ED, and wastewater sources, with plain-language caveats |
| `get_revisions` | How one week's value changed across CDC releases |
| `get_as_of` | A series exactly as it had been published on a past date |

Example: `check_reliability(state="SC", pathogen="influenza", weeks=4)` on the 2026-10-16 release returns, along with per-source counts:

```json
"caveats": [
  "Smoothed ED percent had an unusually large change in: 2026-09-19, 2026-09-26, 2026-10-03.",
  "Wastewater influenza covers influenza A only."
]
```

Tools never average, fill in, or reinterpret values. Invalid requests (an unknown measure, a measure that is not published for the requested region type, a date before the revision history starts) return an error message that tells the model how to correct the call.

## Use with an MCP client

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/jiandewu/resplens.git
cd resplens
uv sync
```

Claude Code:

```bash
claude mcp add resplens -- uv run --directory /path/to/resplens resplens-mcp
```

Other clients: run `uv run --directory /path/to/resplens resplens-mcp` as a stdio server.

## Retrieval over the documentation

A corpus of 28 public documents (about 74,000 words) explains the three surveillance systems: CDC dataset descriptions, reporting protocols, methodology pages, FAQs, two MMWR reports, and the ObsAwareData documentation. `corpus/` keeps every source file unchanged with its URL, retrieval date, and SHA-256, plus the extracted text.

Retrieval was evaluated on a hand-reviewed set of 40 questions, each with verbatim evidence from the documents; 15 were used for tuning and 25 were held out. The four test configurations were fixed before the held-out run. On the 21 answerable held-out questions, with 300-token chunks:

| Configuration | Recall@5 | Recall@10 | MRR | Latency (median) |
|---|---|---|---|---|
| BM25 | 0.48 | 0.52 | 0.38 | 1 ms |
| Dense (`BAAI/bge-m3`) | 0.62 | 0.76 | 0.48 | 9 ms |
| Hybrid (BM25 + dense) | 0.57 | 0.71 | 0.47 | 10 ms |
| Hybrid + cross-encoder rerank | **0.86** | **0.86** | 0.50 | 206 ms |

Hybrid retrieval with reranking found the evidence in the top five for 8 more questions than BM25 and none fewer (sign test p = 0.008). No configuration was reliably better at putting the evidence first. Method, findings, and failure analysis: [`docs/retrieval-eval.md`](docs/retrieval-eval.md).

The whole corpus is about 131,000 tokens and fits in a long-context model, so the next comparison is answers generated from retrieved passages against answers generated from the whole corpus in context: [`docs/answer-eval.md`](docs/answer-eval.md).

## Data handling

- All data are read from one tagged ObsAwareData release (`DATA_TAG` in `src/resplens/data.py`, currently `v2.0.0+2026-10-16`), so answers are reproducible.
- Files are downloaded on first use to `~/.cache/resplens/` (override with `RESPLENS_CACHE`) and checked against the release's published SHA-256 checksums.
- A state's revision history is downloaded the first time `get_revisions` or `get_as_of` is called for it (about 15 MB compressed for South Carolina).

## Development

```bash
uv run pytest                                   # offline tests on a small synthetic mirror
RESPLENS_NETWORK_TESTS=1 uv run pytest -k real  # also check against the real release
```

Retrieval experiments use the `models` extra (sentence-transformers) and, for some embedding models, a local [Ollama](https://ollama.com) server:

```bash
uv sync --extra models
uv run --extra models python -m resplens.retrieval.evaluate --split dev --retriever hybrid --embed-model BAAI/bge-m3 --rerank
```

Rebuilding the corpus from its sources: `uv run --extra corpus python -m resplens.retrieval.corpus`.

## Sources and attribution

- **ObsAwareData** is licensed under CC BY 4.0. Cite it as described in its [CITATION.cff](https://github.com/DMA-PRIME/ObsAwareData/blob/main/CITATION.cff). Measure and flag descriptions in `src/resplens/tools.py` are adapted from its data dictionary.
- **CDC documents** in `corpus/` (Source: CDC) are public domain under CDC's [Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html) policy and are available at no charge from cdc.gov and data.cdc.gov; MMWR material is public domain under the [MMWR series](https://www.cdc.gov/mmwr/about.html) terms. One CMS memorandum and one National Cancer Institute (SEER) page are also included. Each document's source URL and retrieval date are in `corpus/manifest.csv`; files in `corpus/text/` are text extracted from the originals without changes to their content.
- This project is independent. Its use of these materials does not imply endorsement by CDC, ATSDR, HHS, CMS, NCI, or the United States Government.

## License

Code: MIT. Corpus documents keep their original terms, listed above.
