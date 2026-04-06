"""MCP server configurations for the Keystone Intelligence Engine.

Registry entries for all 7 MCP servers. These are configuration entries,
not the servers themselves. API keys are loaded from environment variables.

Servers:
- Exa: web search with neural retrieval (HTTP)
- Brave Search: web search with privacy focus (HTTP)
- EdgarTools: SEC EDGAR filings and company data (stdio)
- FRED: Federal Reserve economic data (stdio)
- paper-search-mcp: academic papers from 21+ sources (HTTP)
- doi-mcp: DOI verification for citation validation (stdio)
- Finnhub: real-time market data, financials, earnings (HTTP)
"""

from __future__ import annotations

from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType
from keystone.tool_names import ToolName

TOOL_CONFIGS: dict[str, ToolEntry] = {
    ToolName.EXA_SEARCH: ToolEntry(
        name=ToolName.EXA_SEARCH,
        server_name="exa-mcp-server",
        description="Neural web search via Exa. Returns relevant pages with content snippets.",
        transport_type=TransportType.HTTP,
        config={
            "api_key_env": "EXA_API_KEY",
            "base_url": "https://api.exa.ai",
        },
    ),
    ToolName.BRAVE_SEARCH: ToolEntry(
        name=ToolName.BRAVE_SEARCH,
        server_name="brave-search-mcp-server",
        description="Privacy-focused web search via Brave. Returns web results with snippets.",
        transport_type=TransportType.HTTP,
        config={
            "api_key_env": "BRAVE_SEARCH_API_KEY",
            "base_url": "https://api.search.brave.com",
        },
    ),
    ToolName.EDGAR_FILINGS: ToolEntry(
        name=ToolName.EDGAR_FILINGS,
        server_name="edgartools-mcp",
        description="SEC EDGAR filings lookup. 10-K, 10-Q, 8-K, proxy statements by company.",
        transport_type=TransportType.STDIO,
        config={
            "command": "python",
            "args": ["-m", "edgartools.mcp"],
        },
    ),
    ToolName.FRED_DATA: ToolEntry(
        name=ToolName.FRED_DATA,
        server_name="fred-mcp-server",
        description="Federal Reserve economic data (FRED). GDP, inflation, rates, employment.",
        transport_type=TransportType.STDIO,
        config={
            "api_key_env": "FRED_API_KEY",
            "command": "npx",
            "args": ["-y", "@stefanoamorelli/fred-mcp-server"],
        },
    ),
    ToolName.PAPER_SEARCH: ToolEntry(
        name=ToolName.PAPER_SEARCH,
        server_name="paper-search-mcp",
        description="Academic paper search across 21+ sources. Full-text retrieval with fallback.",
        transport_type=TransportType.HTTP,
        config={
            "base_url": "http://localhost:3100",
        },
    ),
    ToolName.DOI_VERIFY: ToolEntry(
        name=ToolName.DOI_VERIFY,
        server_name="doi-mcp",
        description="DOI verification and metadata lookup for citation validation.",
        transport_type=TransportType.STDIO,
        config={
            "command": "npx",
            "args": ["-y", "@tfscharff/doi-mcp"],
        },
    ),
    ToolName.FINNHUB_MARKET: ToolEntry(
        name=ToolName.FINNHUB_MARKET,
        server_name="finnhub-mcp",
        description="Real-time market data via Finnhub. Quotes, financials, earnings, company profiles.",
        transport_type=TransportType.HTTP,
        config={
            "api_key_env": "FINNHUB_API_KEY",
            "base_url": "https://finnhub.io/api/v1",
        },
    ),
}


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all configured MCP server tools in the registry."""
    for entry in TOOL_CONFIGS.values():
        registry.register(entry)
