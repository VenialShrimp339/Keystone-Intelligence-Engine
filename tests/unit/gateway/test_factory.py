"""Tests for the production-wired MCP gateway factory."""

from __future__ import annotations

import pytest

from keystone.gateway import (
    SERVER_RATE_LIMITS,
    AuditLogger,
    InMemoryRateLimiter,
    MCPGateway,
    MockMCPClient,
    RateLimit,
    ToolRegistry,
    build_default_rate_limits,
    build_mcp_gateway,
)
from keystone.gateway.servers import (
    EDGAR_SERVER_NAME,
    RETRIEVAL_SERVER_NAME,
    TOOL_CONFIGS,
)


class TestBuildDefaultRateLimits:
    def test_returns_fresh_copy(self) -> None:
        a = build_default_rate_limits()
        b = build_default_rate_limits()
        assert a == b
        # Mutating one does not affect the other
        a[EDGAR_SERVER_NAME].max_tokens = 9999
        assert b[EDGAR_SERVER_NAME].max_tokens != 9999

    def test_edgar_capped_at_10_per_second(self) -> None:
        limits = build_default_rate_limits()
        edgar = limits[EDGAR_SERVER_NAME]
        assert edgar.max_tokens == 10
        assert edgar.refill_rate == 10.0

    def test_retrieval_bucket_present(self) -> None:
        limits = build_default_rate_limits()
        assert RETRIEVAL_SERVER_NAME in limits
        assert limits[RETRIEVAL_SERVER_NAME].refill_rate >= 10.0

    def test_covers_all_unique_servers(self) -> None:
        unique_servers = {entry.server_name for entry in TOOL_CONFIGS.values()}
        limits = build_default_rate_limits()
        missing = unique_servers - limits.keys()
        assert not missing, f"servers without default rate limit: {missing}"


class TestBuildMCPGateway:
    def test_default_factory_produces_gateway(self) -> None:
        gw = build_mcp_gateway()
        assert isinstance(gw, MCPGateway)

    def test_default_registry_contains_every_tool(self) -> None:
        gw = build_mcp_gateway()
        names = set(gw._registry.list_tool_names())
        expected = set(TOOL_CONFIGS.keys())
        assert names == expected

    def test_default_rate_limiter_applies_edgar_cap(self) -> None:
        gw = build_mcp_gateway()
        assert isinstance(gw._rate_limiter, InMemoryRateLimiter)
        # Token-bucket capacity matches SERVER_RATE_LIMITS
        edgar_bucket = gw._rate_limiter._buckets[EDGAR_SERVER_NAME]
        assert edgar_bucket.capacity == SERVER_RATE_LIMITS[EDGAR_SERVER_NAME].max_tokens

    @pytest.mark.asyncio
    async def test_default_rate_limiter_exhausts_edgar_bucket(self) -> None:
        gw = build_mcp_gateway()
        acquired = 0
        for _ in range(SERVER_RATE_LIMITS[EDGAR_SERVER_NAME].max_tokens + 5):
            if await gw._rate_limiter.try_acquire(EDGAR_SERVER_NAME):
                acquired += 1
        assert acquired == SERVER_RATE_LIMITS[EDGAR_SERVER_NAME].max_tokens

    def test_custom_client_passes_through(self) -> None:
        client = MockMCPClient()
        gw = build_mcp_gateway(client=client)
        assert gw._client is client

    def test_custom_rate_limiter_override(self) -> None:
        custom = InMemoryRateLimiter({"foo": RateLimit(max_tokens=1, refill_rate=0.1)})
        gw = build_mcp_gateway(rate_limiter=custom)
        assert gw._rate_limiter is custom

    def test_custom_registry_override(self) -> None:
        registry = ToolRegistry()
        gw = build_mcp_gateway(registry=registry)
        assert gw._registry is registry
        # Custom registry is NOT auto-populated
        assert gw._registry.list_tool_names() == []

    def test_custom_audit_logger_override(self) -> None:
        logger = AuditLogger(debug=True)
        gw = build_mcp_gateway(audit_logger=logger)
        assert gw.audit_logger is logger
