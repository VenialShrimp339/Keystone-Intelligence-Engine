"""MCP server configurations for the Keystone Intelligence Engine.

Registry entries for the configured MCP servers. These are configuration
entries, not the servers themselves. API keys and the SEC EDGAR identity
string are loaded from environment variables.

Servers (unique ``server_name`` values):
- Exa: web search with neural retrieval (HTTP)
- Brave Search: web search with privacy focus (HTTP)
- edgartools-mcp: SEC EDGAR filings, XBRL financials, and time-series
  company facts (stdio). Exposes three Keystone tool names that share
  one upstream MCP server.
- FRED: Federal Reserve economic data (stdio)
- paper-search-mcp: academic papers from 21+ sources (HTTP)
- doi-mcp: DOI verification for citation validation (stdio)
- Finnhub: real-time market data, financials, earnings (HTTP)

SEC EDGAR compliance (applies to every ``edgartools-mcp`` tool):
- A User-Agent identifying the application and a contact email is
  required on every request. edgartools reads this from the
  ``EDGAR_IDENTITY`` env var (format: ``"Name email@example.com"``).
- Aggregate request rate to data.sec.gov must stay at or below 10
  req/sec. ``SERVER_RATE_LIMITS`` pins the server-level bucket at that
  cap so multiple EDGAR sub-tools cannot collectively blow past it.
"""

from __future__ import annotations

from keystone.gateway.rate_limiter import RateLimit
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType
from keystone.tool_names import ToolName

# ---------------------------------------------------------------------------
# EDGAR compliance constants
# ---------------------------------------------------------------------------

# edgartools reads this env var for the SEC-required User-Agent.
EDGAR_IDENTITY_ENV = "EDGAR_IDENTITY"

# SEC documents a soft 10 req/sec ceiling for data.sec.gov. We pin the
# bucket refill rate to 10/s and the burst ceiling to 10 so multiple
# EDGAR sub-tools cannot aggregate past the agency limit.
EDGAR_MAX_REQ_PER_SEC = 10

# Shared edgartools MCP server name. All three EDGAR tool names share
# this server so gateway rate limiting, circuit breaking, and audit
# logging aggregate per-server.
EDGAR_SERVER_NAME = "edgartools-mcp"

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

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
        server_name=EDGAR_SERVER_NAME,
        description=(
            "SEC EDGAR filings lookup via edgartools. 10-K, 10-Q, 8-K, and proxy "
            "statements by ticker or CIK. Returns filing metadata plus narrative "
            "Items (1, 1A, 7, 7A) as text for downstream article-style parsing."
        ),
        transport_type=TransportType.STDIO,
        config={
            "command": "python",
            "args": ["-m", "edgartools.mcp"],
            "identity_env": EDGAR_IDENTITY_ENV,
            "rate_limit_per_second": EDGAR_MAX_REQ_PER_SEC,
        },
    ),
    ToolName.EDGAR_FINANCIALS: ToolEntry(
        name=ToolName.EDGAR_FINANCIALS,
        server_name=EDGAR_SERVER_NAME,
        description=(
            "Structured XBRL financial statements from edgartools. Returns balance "
            "sheet, income statement, and cash flow data with semantic GAAP/IFRS "
            "labels. Prefer over parsing HTML tables when both are available."
        ),
        transport_type=TransportType.STDIO,
        config={
            "command": "python",
            "args": ["-m", "edgartools.mcp"],
            "identity_env": EDGAR_IDENTITY_ENV,
            "rate_limit_per_second": EDGAR_MAX_REQ_PER_SEC,
        },
    ),
    ToolName.EDGAR_COMPANY_FACTS: ToolEntry(
        name=ToolName.EDGAR_COMPANY_FACTS,
        server_name=EDGAR_SERVER_NAME,
        description=(
            "Time-series of SEC XBRL company facts "
            "(data.sec.gov/api/xbrl/companyfacts). Returns concept-level "
            "history (e.g. Revenues, EarningsPerShareBasic) as JSON for "
            "multi-year trend analysis without re-parsing individual filings."
        ),
        transport_type=TransportType.STDIO,
        config={
            "command": "python",
            "args": ["-m", "edgartools.mcp"],
            "identity_env": EDGAR_IDENTITY_ENV,
            "rate_limit_per_second": EDGAR_MAX_REQ_PER_SEC,
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
        description=(
            "Real-time market data via Finnhub. Quotes, financials, earnings, company profiles."
        ),
        transport_type=TransportType.HTTP,
        config={
            "api_key_env": "FINNHUB_API_KEY",
            "base_url": "https://finnhub.io/api/v1",
        },
    ),
}


# ---------------------------------------------------------------------------
# Per-server rate limit defaults
# ---------------------------------------------------------------------------

# SERVER_RATE_LIMITS gives the gateway a single source of truth for the
# per-server token-bucket configuration. Callers build an
# ``InMemoryRateLimiter`` from this via ``build_default_rate_limits``.
# The EDGAR entry is pinned to SEC's documented 10 req/sec cap; all
# EDGAR sub-tools aggregate through this single bucket (they share
# ``server_name="edgartools-mcp"``).
SERVER_RATE_LIMITS: dict[str, RateLimit] = {
    "exa-mcp-server": RateLimit(max_tokens=10, refill_rate=5.0),
    "brave-search-mcp-server": RateLimit(max_tokens=10, refill_rate=5.0),
    EDGAR_SERVER_NAME: RateLimit(
        max_tokens=EDGAR_MAX_REQ_PER_SEC,
        refill_rate=float(EDGAR_MAX_REQ_PER_SEC),
    ),
    "fred-mcp-server": RateLimit(max_tokens=10, refill_rate=5.0),
    "paper-search-mcp": RateLimit(max_tokens=10, refill_rate=5.0),
    "doi-mcp": RateLimit(max_tokens=10, refill_rate=5.0),
    "finnhub-mcp": RateLimit(max_tokens=30, refill_rate=10.0),
}


def build_default_rate_limits() -> dict[str, RateLimit]:
    """Return a fresh copy of ``SERVER_RATE_LIMITS`` for rate-limiter setup."""
    return {server: limit.model_copy() for server, limit in SERVER_RATE_LIMITS.items()}


def register_all_tools(registry: ToolRegistry) -> None:
    """Register all configured MCP server tools in the registry."""
    for entry in TOOL_CONFIGS.values():
        registry.register(entry)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

# Number of unique upstream MCP servers backing ``TOOL_CONFIGS``.
# Tools can share a server_name (EDGAR's three tool names all use
# ``edgartools-mcp``), so the server count is strictly <= tool count.
UNIQUE_SERVER_COUNT = len({entry.server_name for entry in TOOL_CONFIGS.values()})
