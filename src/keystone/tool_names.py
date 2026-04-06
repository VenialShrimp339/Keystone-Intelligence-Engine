"""Single source of truth for MCP tool name constants.

Every component that references tool names by string MUST import from
here. This prevents drift between the Gateway's registered tool names
and the Spec Engine's template tool assignments.

Created after the overnight audit found 9 of 11 tool name strings
mismatched between gateway/servers.py and specification/template_registry.py.
"""

from __future__ import annotations

from enum import StrEnum


class ToolName(StrEnum):
    """Registered MCP tool identifiers.

    Each value corresponds to exactly one tool entry in
    gateway/servers.py. Adding a new MCP server means adding
    a new enum member here first.
    """

    # Search
    EXA_SEARCH = "exa_search"
    BRAVE_SEARCH = "brave_search"

    # Financial
    EDGAR_FILINGS = "edgar_filings"
    FRED_DATA = "fred_data"
    FINNHUB_MARKET = "finnhub_market"

    # Academic
    PAPER_SEARCH = "paper_search"

    # Citation verification
    DOI_VERIFY = "doi_verify"


# ---------------------------------------------------------------------------
# Semantic groupings for template tool assignment
# ---------------------------------------------------------------------------

SEARCH_TOOLS: list[str] = [ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH]

FINANCIAL_TOOLS: list[str] = [
    ToolName.EDGAR_FILINGS,
    ToolName.FRED_DATA,
    ToolName.FINNHUB_MARKET,
]

ACADEMIC_TOOLS: list[str] = [ToolName.PAPER_SEARCH, ToolName.DOI_VERIFY]

# Tools available to every agent as a baseline
DEFAULT_TOOLS: list[str] = [ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH]

# Full set of all registered tools
ALL_TOOLS: list[str] = list(ToolName)
