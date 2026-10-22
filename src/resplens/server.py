"""MCP server exposing the ObsAwareData query tools.

Run over stdio (for Claude Code, Codex, and other MCP clients):

    uv run resplens-mcp
"""

from __future__ import annotations

import functools
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from . import tools
from .data import DataError, Dataset


INSTRUCTIONS = """\
Weekly US respiratory surveillance data (COVID-19, influenza, RSV) for the 50 states and DC from
ObsAwareData: NHSN hospital admissions, NSSP emergency department visits, and NWSS wastewater.
Every value carries a reliability flag; only observed_valid and observed_zero are normal readings.
Start with describe_measures or describe_state, report numbers only as returned by the tools,
and mention the caveats from check_reliability when describing recent trends."""

State = Annotated[str, Field(description='Two-letter postal code, e.g. "SC" or "DC".')]
Measure = Annotated[str, Field(description='Measure name from describe_measures, e.g. "hospital_admission_count".')]
Pathogen = Annotated[Literal["covid", "influenza", "rsv", "combined", "not_applicable"],
                     Field(description="combined is ED visits only; not_applicable is ED participation_status only.")]
RegionType = Annotated[Literal["state", "sub_state_hsa", "sampling_site"],
                       Field(description="state; sub_state_hsa for an ED region; sampling_site for a wastewater site.")]
RegionId = Annotated[str | None, Field(description="HSA code or wastewater site ID (e.g. ID:113) from describe_state; "
                                                   "required unless region_type is state.")]
Week = Annotated[str | None, Field(description="Week ending date (Saturday), YYYY-MM-DD.")]
MaxWeeks = Annotated[int, Field(ge=1, le=520, description="Keep at most this many of the most recent weeks.")]

mcp = MCPServer("resplens", instructions=INSTRUCTIONS)
_dataset: Dataset | None = None


def tool(func):
    """Register a tool; DataError messages reach the model so it can correct its call."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DataError as exc:
            raise ToolError(str(exc)) from exc
    return mcp.tool()(wrapper)


def dataset() -> Dataset:
    global _dataset
    if _dataset is None:
        _dataset = Dataset()
    return _dataset


@tool
def describe_measures() -> dict[str, Any]:
    """List the measures (with their source, pathogens, and region types) and the reliability flag codes."""
    return tools.describe_measures()


@tool
def describe_state(state: State) -> dict[str, Any]:
    """Coverage dates, flag thresholds, ED regions (HSAs), and wastewater sites for one state."""
    return tools.describe_state(dataset(), state)


@tool
def get_series(state: State, measure: Measure, pathogen: Pathogen, region_type: RegionType = "state",
               region_id: RegionId = None, start: Week = None, end: Week = None,
               max_weeks: MaxWeeks = 104) -> dict[str, Any]:
    """Weekly values of one measure, latest published versions, with a reliability flag for every week.

    start and end bound the weeks returned (inclusive).
    """
    return tools.get_series(dataset(), state, measure, pathogen, region_type, region_id, start, end, max_weeks)


@tool
def check_reliability(state: State,
                      pathogen: Annotated[Literal["covid", "influenza", "rsv"], Field(description="Pathogen.")],
                      weeks: Annotated[int, Field(ge=1, le=52, description="Number of weeks to look back.")] = 8,
                      end: Annotated[str | None, Field(description="Last week of the window, YYYY-MM-DD; defaults "
                                                                       "to the latest hospital week.")] = None,
                      ) -> dict[str, Any]:
    """Summarize recent data quality across hospital, ED, and wastewater sources, with plain-language caveats."""
    return tools.check_reliability(dataset(), state, pathogen, weeks, end)


@tool
def get_revisions(state: State, measure: Measure, pathogen: Pathogen,
                  week: Annotated[str, Field(description="Week ending date (Saturday), YYYY-MM-DD.")],
                  region_type: RegionType = "state", region_id: RegionId = None) -> dict[str, Any]:
    """How one week's value changed across CDC releases: first value, latest value, and each change.

    The first call for a state downloads its revision history, which can take a minute.
    """
    return tools.get_revisions(dataset(), state, measure, pathogen, week, region_type, region_id)


@tool
def get_as_of(state: State, measure: Measure, pathogen: Pathogen,
              as_of: Annotated[str, Field(description="Publication date, YYYY-MM-DD. History starts 2025-04-04 "
                                                      "(NHSN), 2025-08-15 (NSSP), 2026-08-07 (NWSS).")],
              region_type: RegionType = "state", region_id: RegionId = None, start: Week = None,
              max_weeks: MaxWeeks = 104) -> dict[str, Any]:
    """The series exactly as it had been published on a past date, for real-time backtests and audits."""
    return tools.get_as_of(dataset(), state, measure, pathogen, as_of, region_type, region_id, start, max_weeks)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
