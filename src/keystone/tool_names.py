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
    EDGAR_FINANCIALS = "edgar_financials"
    EDGAR_COMPANY_FACTS = "edgar_company_facts"
    FRED_DATA = "fred_data"
    FINNHUB_MARKET = "finnhub_market"

    # Academic
    PAPER_SEARCH = "paper_search"

    # Citation verification
    DOI_VERIFY = "doi_verify"

    # Retrieval (system-owned, not task-assignable)
    SEMANTIC_SEARCH = "semantic_search"
    HYBRID_SEARCH = "hybrid_search"


# ---------------------------------------------------------------------------
# Semantic groupings for template tool assignment
# ---------------------------------------------------------------------------

SEARCH_TOOLS: list[str] = [ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH]

FINANCIAL_TOOLS: list[str] = [
    ToolName.EDGAR_FILINGS,
    ToolName.EDGAR_FINANCIALS,
    ToolName.EDGAR_COMPANY_FACTS,
    ToolName.FRED_DATA,
    ToolName.FINNHUB_MARKET,
]

# Tools exposed by the edgartools MCP server (share one server_name)
EDGAR_TOOLS: list[str] = [
    ToolName.EDGAR_FILINGS,
    ToolName.EDGAR_FINANCIALS,
    ToolName.EDGAR_COMPANY_FACTS,
]

ACADEMIC_TOOLS: list[str] = [ToolName.PAPER_SEARCH, ToolName.DOI_VERIFY]

# Tools available to every agent as a baseline
DEFAULT_TOOLS: list[str] = [ToolName.EXA_SEARCH, ToolName.BRAVE_SEARCH]

# Retrieval tools served in-process by the RetrievalService. The spec
# engine MUST NOT hand these out in template tool assignments -- they
# are invoked by the gateway directly in response to agent queries and
# by the orchestrator during context assembly.
RETRIEVAL_TOOLS: list[str] = [ToolName.SEMANTIC_SEARCH, ToolName.HYBRID_SEARCH]

# System-owned tools: never appear in agent-assignable groupings above.
# Kept as its own list so the Specification Engine can import one name
# to know what to exclude.
SYSTEM_OWNED_TOOLS: list[str] = list(RETRIEVAL_TOOLS)

# Full set of all registered tools
ALL_TOOLS: list[str] = list(ToolName)
