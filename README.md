# resplens

Reliability-aware AI tools for US respiratory surveillance data (COVID-19, influenza, RSV).

Public health surveillance numbers are revised after publication, some weeks rest on few reporting hospitals, and some sudden jumps are reporting artifacts. An AI assistant that reads these numbers at face value will state wrong trends with confidence. resplens gives language models tools that return every value **with its reliability flag**, summarize what can and cannot be trusted, and reconstruct what was known on any past date.

The data come from [ObsAwareData](https://github.com/DMA-PRIME/ObsAwareData) (CC BY 4.0): weekly CDC hospital admissions (NHSN), emergency department visits (NSSP), and wastewater (NWSS) for the 50 states and DC, with a flag on every value and the full revision history.

## Status

| Stage | Contents | State |
|---|---|---|
| A1 | Data tools and MCP server | Done |
| A2 | Retrieval over data documentation, with a retrieval evaluation | Planned |
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

## Data handling

- All data are read from one tagged ObsAwareData release (`DATA_TAG` in `src/resplens/data.py`, currently `v2.0.0+2026-10-16`), so answers are reproducible.
- Files are downloaded on first use to `~/.cache/resplens/` (override with `RESPLENS_CACHE`) and checked against the release's published SHA-256 checksums.
- A state's revision history is downloaded the first time `get_revisions` or `get_as_of` is called for it (about 15 MB compressed for South Carolina).

## Development

```bash
uv run pytest                                   # offline tests on a small synthetic mirror
RESPLENS_NETWORK_TESTS=1 uv run pytest -k real  # also check against the real release
```

## Data citation

ObsAwareData is licensed under CC BY 4.0. Cite it as described in its [CITATION.cff](https://github.com/DMA-PRIME/ObsAwareData/blob/main/CITATION.cff). Measure and flag descriptions in `src/resplens/tools.py` are adapted from its data dictionary.

## License

Code: MIT.
