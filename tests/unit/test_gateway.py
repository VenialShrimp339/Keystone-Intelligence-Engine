"""Integration tests for the MCP Gateway.

Tests the full flow: auth -> rate limit -> circuit break -> execute -> audit.
Uses MockMCPClient for all MCP server calls.
"""

import asyncio

import pytest

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import AuthorizationError, ToolAuthorizer
from keystone.gateway.circuit_breaker import CircuitOpenError, CircuitState
from keystone.gateway.mcp_gateway import (
    MCPGateway,
    MockMCPClient,
    ToolCall,
    ToolResult,
    extract_citations,
)
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit, RateLimitExceeded
from keystone.gateway.servers import register_all_tools
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _build_gateway(
    mock_client: MockMCPClient | None = None,
    rate_limits: dict[str, RateLimit] | None = None,
    debug: bool = False,
) -> tuple[MCPGateway, MockMCPClient, AuditLogger]:
    """Build a fully wired gateway with default config."""
    registry = ToolRegistry()
    register_all_tools(registry)

    authorizer = ToolAuthorizer(registry)

    if rate_limits is None:
        rate_limits = {
            "exa-mcp-server": RateLimit(max_tokens=10, refill_rate=1.0),
            "brave-search-mcp-server": RateLimit(max_tokens=10, refill_rate=1.0),
        }
    limiter = InMemoryRateLimiter(rate_limits)

    audit = AuditLogger(debug=debug)

    client = mock_client or MockMCPClient()

    gateway = MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=limiter,
        audit_logger=audit,
        client=client,
    )

    return gateway, client, audit


def _make_call(
    tool_name: str = "exa_search",
    assigned_tools: list[str] | None = None,
) -> ToolCall:
    if assigned_tools is None:
        assigned_tools = ["exa_search", "brave_search", "edgar_filings"]
    return ToolCall(
        agent_id="agent_001",
        tool_name=tool_name,
        parameters={"query": "market size for EV batteries"},
        engagement_id="eng_001",
        client_id="client_001",
        assigned_tools=assigned_tools,
    )


# ---------------------------------------------------------------------------
# Full flow: success path
# ---------------------------------------------------------------------------


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_successful_execution(self) -> None:
        """Full flow: auth -> rate limit -> circuit break -> execute -> audit."""
        gateway, client, audit = _build_gateway()
        client.set_response(
            "exa_search",
            {
                "results": [
                    {"title": "EV Battery Market", "url": "https://example.com/ev"},
                ],
            },
        )

        call = _make_call("exa_search")
        result = await gateway.execute(call)

        assert isinstance(result, ToolResult)
        assert result.result["results"][0]["title"] == "EV Battery Market"
        assert result.latency_ms > 0

        # Audit log should have the success
        entries = audit.get_entries(agent_id="agent_001")
        assert len(entries) >= 1
        assert entries[-1].success is True

    @pytest.mark.asyncio
    async def test_citations_extracted(self) -> None:
        """Tool results with URLs produce citations."""
        gateway, client, audit = _build_gateway()
        client.set_response(
            "exa_search",
            {
                "results": [
                    {"title": "Report", "url": "https://example.com/report"},
                    {"title": "Data", "link": "https://data.gov/ev"},
                ],
            },
        )

        result = await gateway.execute(_make_call("exa_search"))
        urls = {c["url"] for c in result.citations}
        assert "https://example.com/report" in urls

    @pytest.mark.asyncio
    async def test_mock_client_default_response(self) -> None:
        """MockMCPClient returns default response for unconfigured tools."""
        gateway, client, audit = _build_gateway()
        result = await gateway.execute(_make_call("exa_search"))
        assert result.result["tool"] == "exa_search"
        assert result.result["status"] == "ok"


# ---------------------------------------------------------------------------
# Authorization failures
# ---------------------------------------------------------------------------


class TestAuthorizationFailures:
    @pytest.mark.asyncio
    async def test_unauthorized_tool_rejected(self) -> None:
        """Tool not in assigned_tools is rejected."""
        gateway, client, audit = _build_gateway()
        call = _make_call("edgar_filings", assigned_tools=["exa_search"])

        with pytest.raises(AuthorizationError) as exc_info:
            await gateway.execute(call)
        assert "edgar_filings" in str(exc_info.value)

        # Audit should record the failure
        entries = audit.get_entries()
        assert any(not e.success for e in entries)

    @pytest.mark.asyncio
    async def test_empty_assigned_tools_blocks(self) -> None:
        """Empty assigned_tools blocks all tool calls."""
        gateway, client, audit = _build_gateway()
        call = _make_call("exa_search", assigned_tools=[])

        with pytest.raises(AuthorizationError):
            await gateway.execute(call)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_exhaustion(self) -> None:
        """Rate limit exceeded after bucket depleted."""
        gateway, client, audit = _build_gateway(
            rate_limits={"exa-mcp-server": RateLimit(max_tokens=2, refill_rate=0.01)}
        )

        # First 2 succeed
        await gateway.execute(_make_call("exa_search"))
        await gateway.execute(_make_call("exa_search"))

        # Third should be rate limited
        with pytest.raises(RateLimitExceeded) as exc_info:
            await gateway.execute(_make_call("exa_search"))
        assert "exa-mcp-server" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_per_provider(self) -> None:
        """Rate limiting is per-provider, not global."""
        gateway, client, audit = _build_gateway(
            rate_limits={
                "exa-mcp-server": RateLimit(max_tokens=1, refill_rate=0.01),
                "brave-search-mcp-server": RateLimit(max_tokens=1, refill_rate=0.01),
            }
        )

        # Exa exhausted
        await gateway.execute(_make_call("exa_search"))
        with pytest.raises(RateLimitExceeded):
            await gateway.execute(_make_call("exa_search"))

        # Brave still works
        result = await gateway.execute(_make_call("brave_search"))
        assert result.result is not None


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self) -> None:
        """Circuit opens after 3 consecutive failures."""
        gateway, client, audit = _build_gateway()
        client.set_failure("exa_search", ConnectionError("server down"))

        # Override retry settings for fast test
        gateway.MAX_RETRIES = 1
        gateway.BACKOFF_BASE = 0.0

        # 3 failures to open the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await gateway.execute(_make_call("exa_search"))

        # Circuit should now be open
        state = gateway.get_circuit_state("exa-mcp-server")
        assert state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_open_rejects_immediately(self) -> None:
        """Open circuit rejects without calling the server."""
        gateway, client, audit = _build_gateway()
        client.set_failure("exa_search", ConnectionError("down"))

        gateway.MAX_RETRIES = 1
        gateway.BACKOFF_BASE = 0.0

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await gateway.execute(_make_call("exa_search"))

        # Next call gets CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await gateway.execute(_make_call("exa_search"))


# ---------------------------------------------------------------------------
# Retry + dead-letter (Directive 9)
# ---------------------------------------------------------------------------


class TestRetryAndDeadLetter:
    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self) -> None:
        """Gateway retries on failure, succeeds when server recovers."""
        client = MockMCPClient()
        gateway, _, audit = _build_gateway(mock_client=client)
        gateway.BACKOFF_BASE = 0.0  # No delay in tests

        call_count = 0
        original_call = client.call_tool

        async def flaky_call(server: str, tool: str, params: dict) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("transient failure")
            return {"status": "ok", "data": "recovered"}

        client.call_tool = flaky_call

        result = await gateway.execute(_make_call("exa_search"))
        assert result.result["data"] == "recovered"
        assert call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_dead_letter_after_max_retries(self) -> None:
        """Tool call dead-lettered after exhausting all retries."""
        gateway, client, audit = _build_gateway()
        gateway.MAX_RETRIES = 3
        gateway.BACKOFF_BASE = 0.0

        client.set_failure("exa_search", ConnectionError("permanent failure"))

        with pytest.raises(ConnectionError):
            await gateway.execute(_make_call("exa_search"))

        # Dead-letter should be recorded
        dead_letters = gateway.dead_letters
        assert len(dead_letters) >= 1
        assert dead_letters[-1].call.tool_name == "exa_search"
        assert dead_letters[-1].attempts == 3

        # Audit should have a dead-letter entry
        dead = audit.get_dead_letters()
        assert len(dead) >= 1

    @pytest.mark.asyncio
    async def test_audit_records_all_attempts(self) -> None:
        """Every retry attempt is individually logged."""
        gateway, client, audit = _build_gateway()
        gateway.MAX_RETRIES = 3
        gateway.BACKOFF_BASE = 0.0

        client.set_failure("exa_search", ConnectionError("fail"))

        with pytest.raises(ConnectionError):
            await gateway.execute(_make_call("exa_search"))

        # Should have entries for each attempt + dead-letter
        entries = audit.get_entries(tool_name="exa_search")
        assert len(entries) >= 3


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------


class TestCitationExtraction:
    def test_extract_urls_from_text(self) -> None:
        result = "Found at https://example.com/report and https://data.gov/ev"
        citations = extract_citations(result)
        urls = {c["url"] for c in citations}
        assert "https://example.com/report" in urls
        assert "https://data.gov/ev" in urls

    def test_extract_from_dict_url_field(self) -> None:
        result = {"url": "https://sec.gov/filing", "title": "10-K Filing"}
        citations = extract_citations(result)
        assert any(c["url"] == "https://sec.gov/filing" for c in citations)

    def test_extract_from_list_of_dicts(self) -> None:
        result = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
        ]
        citations = extract_citations(result)
        urls = {c["url"] for c in citations}
        assert "https://a.com" in urls
        assert "https://b.com" in urls

    def test_deduplicates_urls(self) -> None:
        result = "Visit https://example.com and https://example.com again"
        citations = extract_citations(result)
        urls = [c["url"] for c in citations]
        assert urls.count("https://example.com") == 1

    def test_empty_result(self) -> None:
        assert extract_citations(None) == [] or extract_citations("no urls") == []
