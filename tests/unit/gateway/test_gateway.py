"""Integration tests for the MCP Gateway.

Tests the full pipeline: auth -> rate limit -> circuit break ->
execute -> citation extract -> audit log. Also tests error paths:
authorization failure, rate limit exhaustion, circuit open,
retry + dead-letter behavior.
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
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        ToolEntry(
            name="exa_search",
            server_name="exa-mcp-server",
            description="Web search",
            transport_type=TransportType.HTTP,
        )
    )
    reg.register(
        ToolEntry(
            name="brave_search",
            server_name="brave-search-mcp-server",
            description="Web search",
            transport_type=TransportType.HTTP,
        )
    )
    reg.register(
        ToolEntry(
            name="edgar_filings",
            server_name="edgartools-mcp",
            description="SEC filings",
            transport_type=TransportType.STDIO,
        )
    )
    return reg


@pytest.fixture
def rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter(
        {
            "exa-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "brave-search-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "edgartools-mcp": RateLimit(max_tokens=100, refill_rate=10.0),
        }
    )


@pytest.fixture
def mock_client() -> MockMCPClient:
    client = MockMCPClient()
    client.set_response(
        "exa_search",
        {
            "results": [
                {"title": "Test Result", "url": "https://example.com/result1"},
                {"title": "Another Result", "url": "https://example.com/result2"},
            ]
        },
    )
    return client


@pytest.fixture
def gateway(registry, rate_limiter, mock_client) -> MCPGateway:
    authorizer = ToolAuthorizer(registry)
    audit_logger = AuditLogger(debug=True)
    return MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=mock_client,
    )


def _make_call(
    tool_name: str = "exa_search",
    assigned_tools: list[str] | None = None,
) -> ToolCall:
    return ToolCall(
        agent_id="agent-001",
        tool_name=tool_name,
        parameters={"query": "test query"},
        engagement_id="eng-001",
        client_id="client-001",
        assigned_tools=assigned_tools or ["exa_search", "brave_search"],
    )


# ---------------------------------------------------------------------------
# Full flow tests
# ---------------------------------------------------------------------------


class TestFullFlow:
    @pytest.mark.asyncio
    async def test_successful_execution(self, gateway):
        call = _make_call("exa_search")
        result = await gateway.execute(call)

        assert isinstance(result, ToolResult)
        assert result.result is not None
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_citations_extracted(self, gateway):
        call = _make_call("exa_search")
        result = await gateway.execute(call)

        # MockMCPClient returns URLs in structured format
        assert len(result.citations) >= 1
        urls = {c["url"] for c in result.citations}
        assert "https://example.com/result1" in urls

    @pytest.mark.asyncio
    async def test_audit_log_records_success(self, gateway):
        call = _make_call("exa_search")
        await gateway.execute(call)

        entries = gateway._audit_logger.get_entries(agent_id="agent-001")
        assert len(entries) >= 1
        assert entries[-1].success is True
        assert entries[-1].tool_name == "exa_search"

    @pytest.mark.asyncio
    async def test_result_fields_populated(self, gateway):
        call = _make_call("exa_search")
        result = await gateway.execute(call)

        assert isinstance(result.citations, list)
        assert isinstance(result.tokens_used, int)
        assert isinstance(result.latency_ms, float)
        assert isinstance(result.cache_hit, bool)


# ---------------------------------------------------------------------------
# Authorization failure
# ---------------------------------------------------------------------------


class TestAuthorizationFailure:
    @pytest.mark.asyncio
    async def test_unauthorized_tool_rejected(self, gateway):
        call = _make_call(
            tool_name="edgar_filings",
            assigned_tools=["exa_search", "brave_search"],
        )

        with pytest.raises(AuthorizationError) as exc_info:
            await gateway.execute(call)

        assert exc_info.value.tool_name == "edgar_filings"
        assert "edgar_filings" not in exc_info.value.assigned_tools

    @pytest.mark.asyncio
    async def test_unauthorized_call_is_audited(self, gateway):
        call = _make_call(
            tool_name="edgar_filings",
            assigned_tools=["exa_search", "brave_search"],
        )

        with pytest.raises(AuthorizationError):
            await gateway.execute(call)

        entries = gateway._audit_logger.get_entries(tool_name="edgar_filings")
        assert len(entries) == 1
        assert entries[0].success is False
        assert entries[0].error_type == "AuthorizationError"


# ---------------------------------------------------------------------------
# Rate limit exhaustion
# ---------------------------------------------------------------------------


class TestRateLimitExhaustion:
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, registry, mock_client):
        # Tiny bucket: 1 token, slow refill
        rate_limiter = InMemoryRateLimiter(
            {
                "exa-mcp-server": RateLimit(max_tokens=1, refill_rate=0.01),
            }
        )
        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=mock_client,
        )

        # First call should succeed (consumes the 1 token)
        call = _make_call("exa_search")
        await gw.execute(call)

        # Second call should fail (bucket exhausted)
        with pytest.raises(RateLimitExceeded):
            await gw.execute(call)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, registry, rate_limiter):
        client = MockMCPClient()
        client.set_failure("exa_search", ConnectionError("server down"))

        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=client,
        )

        call = _make_call("exa_search")

        # First call: 3 retries, all fail -> circuit opens
        with pytest.raises(ConnectionError):
            await gw.execute(call)

        # Circuit should now be open
        state = gw.get_circuit_state("exa-mcp-server")
        assert state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_open_rejects_immediately(self, registry, rate_limiter):
        client = MockMCPClient()
        client.set_failure("exa_search", ConnectionError("server down"))

        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=client,
        )

        call = _make_call("exa_search")

        # Open the circuit
        with pytest.raises(ConnectionError):
            await gw.execute(call)

        # Next call should be rejected immediately with CircuitOpenError
        with pytest.raises(CircuitOpenError):
            await gw.execute(call)


# ---------------------------------------------------------------------------
# Retry + dead-letter (Directive 9)
# ---------------------------------------------------------------------------


class TestRetryAndDeadLetter:
    @pytest.mark.asyncio
    async def test_retries_on_transient_failure(self, registry, rate_limiter):
        """First 2 calls fail, 3rd succeeds."""
        call_count = 0

        class FlakeyClient:
            async def call_tool(self, server, tool, params):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise ConnectionError("transient")
                return {"data": "success"}

        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=FlakeyClient(),
        )
        # Use shorter backoff for test speed
        gw.BACKOFF_BASE = 0.01

        call = _make_call("exa_search")
        result = await gw.execute(call)

        assert result.result == {"data": "success"}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_dead_letter_after_max_retries(self, registry, rate_limiter):
        client = MockMCPClient()
        client.set_failure("exa_search", ConnectionError("permanent failure"))

        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=client,
        )
        gw.BACKOFF_BASE = 0.01

        call = _make_call("exa_search")

        with pytest.raises(ConnectionError):
            await gw.execute(call)

        # Should have dead-lettered
        assert len(gw.dead_letters) == 1
        dl = gw.dead_letters[0]
        assert dl.attempts == 3
        assert dl.call.tool_name == "exa_search"

    @pytest.mark.asyncio
    async def test_dead_letter_audit_entry(self, registry, rate_limiter):
        client = MockMCPClient()
        client.set_failure("exa_search", ConnectionError("permanent"))

        authorizer = ToolAuthorizer(registry)
        audit_logger = AuditLogger()
        gw = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            client=client,
        )
        gw.BACKOFF_BASE = 0.01

        call = _make_call("exa_search")

        with pytest.raises(ConnectionError):
            await gw.execute(call)

        # Check audit log has dead-letter entry
        dead_letters = audit_logger.get_dead_letters()
        assert len(dead_letters) == 1
        assert dead_letters[0].dead_lettered is True


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------


class TestCitationExtraction:
    def test_extract_urls_from_text(self):
        result = "Check https://example.com and https://example.org/page for details"
        citations = extract_citations(result)
        urls = {c["url"] for c in citations}
        assert "https://example.com" in urls
        assert "https://example.org/page" in urls

    def test_extract_structured_citations(self):
        result = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "content": "Some content",
        }
        citations = extract_citations(result)
        assert len(citations) >= 1
        assert any(
            c["url"] == "https://example.com/article" and c.get("title") == "Test Article"
            for c in citations
        )

    def test_extract_from_list_of_dicts(self):
        result = [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]
        citations = extract_citations(result)
        urls = {c["url"] for c in citations}
        assert "https://a.com" in urls
        assert "https://b.com" in urls

    def test_deduplicates_urls(self):
        result = "https://example.com and https://example.com again"
        citations = extract_citations(result)
        urls = [c["url"] for c in citations]
        assert urls.count("https://example.com") == 1

    def test_empty_result(self):
        assert extract_citations("no urls here") == []
        assert extract_citations({}) == []
        assert extract_citations([]) == []


# ---------------------------------------------------------------------------
# Mock client
# ---------------------------------------------------------------------------


class TestMockMCPClient:
    @pytest.mark.asyncio
    async def test_default_response(self):
        client = MockMCPClient()
        result = await client.call_tool("server", "tool", {})
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_set_response(self):
        client = MockMCPClient()
        client.set_response("my_tool", {"custom": True})
        result = await client.call_tool("server", "my_tool", {})
        assert result == {"custom": True}

    @pytest.mark.asyncio
    async def test_set_failure(self):
        client = MockMCPClient()
        client.set_failure("my_tool", ValueError("test error"))

        with pytest.raises(ValueError, match="test error"):
            await client.call_tool("server", "my_tool", {})

    @pytest.mark.asyncio
    async def test_clear_failure(self):
        client = MockMCPClient()
        client.set_failure("my_tool", ValueError("fail"))
        client.clear_failure("my_tool")

        result = await client.call_tool("server", "my_tool", {})
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_call_count(self):
        client = MockMCPClient()
        await client.call_tool("s", "t", {})
        await client.call_tool("s", "t", {})
        assert client.call_count == 2
