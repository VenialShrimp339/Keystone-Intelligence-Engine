"""Gateway-level integration tests for the edgartools MCP server.

Verifies that every configured EDGAR Keystone tool:

1. Resolves to the same upstream ``edgartools-mcp`` server so the
   gateway's rate limiter, circuit breaker, and audit log aggregate
   per-server.
2. Carries the SEC User-Agent contract via ``EDGAR_IDENTITY`` in its
   ``config`` -- required by ``data.sec.gov`` on every request.
3. Advertises the correct stdio transport + ``python -m edgartools.mcp``
   launch command so the real MCP layer can drive it in Phase 1B.
4. Is rate-limited at SEC's documented 10 req/sec ceiling via the
   shared bucket. A burst of 11 requests must fail the 11th; the
   bucket must also aggregate across sub-tools.

None of these tests make real SEC API calls. They drive the gateway
end-to-end with the in-process ``MockMCPClient`` so behaviour is
deterministic and offline.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient, ToolCall
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimitExceeded
from keystone.gateway.servers import (
    EDGAR_IDENTITY_ENV,
    EDGAR_MAX_REQ_PER_SEC,
    EDGAR_SERVER_NAME,
    SERVER_RATE_LIMITS,
    TOOL_CONFIGS,
    build_default_rate_limits,
    register_all_tools,
)
from keystone.gateway.tool_registry import ToolRegistry, TransportType
from keystone.tool_names import EDGAR_TOOLS, FINANCIAL_TOOLS, ToolName

# ---------------------------------------------------------------------------
# Registration + config shape
# ---------------------------------------------------------------------------


class TestEdgarRegistration:
    def test_registry_exposes_all_three_edgar_tools(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)

        for name in EDGAR_TOOLS:
            entry = registry.get(name)
            assert entry is not None, f"{name} missing from registry"
            assert entry.server_name == EDGAR_SERVER_NAME

    def test_edgar_tools_share_upstream_server(self) -> None:
        # All EDGAR sub-tools must share one server_name so
        # rate-limiting and circuit-breaking aggregate per-agency.
        entries = [TOOL_CONFIGS[name] for name in EDGAR_TOOLS]
        server_names = {e.server_name for e in entries}
        assert server_names == {EDGAR_SERVER_NAME}

    def test_edgar_tools_use_stdio_transport(self) -> None:
        for name in EDGAR_TOOLS:
            entry = TOOL_CONFIGS[name]
            assert entry.transport_type is TransportType.STDIO

    def test_edgar_tools_declare_edgartools_mcp_launch_command(self) -> None:
        for name in EDGAR_TOOLS:
            cfg = TOOL_CONFIGS[name].config
            assert cfg["command"] == "python"
            assert cfg["args"] == ["-m", "edgartools.mcp"]

    def test_registered_tools_match_tool_name_enum(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)

        for tool_name in EDGAR_TOOLS:
            assert registry.get(tool_name) is not None

    def test_edgar_tools_appear_in_financial_group(self) -> None:
        # FINANCIAL_TOOLS drives template tool assignment. Every EDGAR
        # tool must be addressable from that group so financial
        # research agents can be authorized for them.
        for name in EDGAR_TOOLS:
            assert name in FINANCIAL_TOOLS


# ---------------------------------------------------------------------------
# SEC compliance
# ---------------------------------------------------------------------------


class TestSecComplianceConfig:
    def test_identity_env_var_present_on_every_edgar_tool(self) -> None:
        # SEC EDGAR mandates a User-Agent that identifies the caller
        # and contains a contact email. edgartools reads this from
        # the EDGAR_IDENTITY env var, so every edgartools-mcp tool
        # config must point at it.
        for name in EDGAR_TOOLS:
            cfg = TOOL_CONFIGS[name].config
            assert cfg.get("identity_env") == EDGAR_IDENTITY_ENV

    def test_identity_env_constant_matches_edgartools_convention(self) -> None:
        assert EDGAR_IDENTITY_ENV == "EDGAR_IDENTITY"

    def test_rate_limit_per_second_declared_on_every_edgar_tool(self) -> None:
        for name in EDGAR_TOOLS:
            cfg = TOOL_CONFIGS[name].config
            assert cfg.get("rate_limit_per_second") == EDGAR_MAX_REQ_PER_SEC

    def test_sec_rate_cap_is_ten_per_second(self) -> None:
        # This is a regression guardrail for SEC's published limit. If
        # the agency changes its docs, update this number _and_ the
        # bucket config together.
        assert EDGAR_MAX_REQ_PER_SEC == 10


# ---------------------------------------------------------------------------
# Per-server rate limiting
# ---------------------------------------------------------------------------


class TestEdgarRateLimit:
    def test_default_rate_limits_include_edgar_at_sec_cap(self) -> None:
        limit = SERVER_RATE_LIMITS[EDGAR_SERVER_NAME]
        assert limit.max_tokens == EDGAR_MAX_REQ_PER_SEC
        assert limit.refill_rate == pytest.approx(float(EDGAR_MAX_REQ_PER_SEC))

    def test_build_default_rate_limits_is_isolated_copy(self) -> None:
        a = build_default_rate_limits()
        b = build_default_rate_limits()
        # Rate-limit objects must be independent instances so callers
        # can mutate one without bleeding into the shared registry.
        assert a is not b
        assert a[EDGAR_SERVER_NAME] is not b[EDGAR_SERVER_NAME]
        assert a[EDGAR_SERVER_NAME].max_tokens == b[EDGAR_SERVER_NAME].max_tokens

    @pytest.mark.asyncio
    async def test_edgar_bucket_exhausts_after_ten_requests(self) -> None:
        limiter = InMemoryRateLimiter(build_default_rate_limits())
        for _ in range(EDGAR_MAX_REQ_PER_SEC):
            assert await limiter.try_acquire(EDGAR_SERVER_NAME) is True
        # 11th call in the same instant hits the SEC-aligned ceiling.
        assert await limiter.try_acquire(EDGAR_SERVER_NAME) is False

    @pytest.mark.asyncio
    async def test_edgar_sub_tools_share_rate_bucket(self) -> None:
        # The whole point of sharing ``server_name`` is that three sub-
        # tools can't collectively stage an 30 req/sec burst. Drive the
        # bucket through the full gateway pipeline using all three
        # EDGAR tool names.
        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)
        limiter = InMemoryRateLimiter(build_default_rate_limits())
        audit = AuditLogger()
        client = MockMCPClient()
        for name in EDGAR_TOOLS:
            client.set_response(name, {"results": [], "status": "ok"})

        gateway = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=limiter,
            audit_logger=audit,
            client=client,
        )

        calls: list[ToolCall] = []
        for i in range(EDGAR_MAX_REQ_PER_SEC):
            tool = EDGAR_TOOLS[i % len(EDGAR_TOOLS)]
            calls.append(
                ToolCall(
                    agent_id="agent-edgar",
                    tool_name=tool,
                    parameters={"cik": "0001045810"},
                    engagement_id="eng-edgar",
                    client_id="client-edgar",
                    assigned_tools=list(EDGAR_TOOLS),
                )
            )

        for call in calls:
            result = await gateway.execute(call)
            assert result.result["status"] == "ok"

        # One more spread across any EDGAR sub-tool must fail -- the
        # bucket is shared.
        with pytest.raises(RateLimitExceeded):
            await gateway.execute(
                ToolCall(
                    agent_id="agent-edgar",
                    tool_name=ToolName.EDGAR_FINANCIALS,
                    parameters={"cik": "0001045810"},
                    engagement_id="eng-edgar",
                    client_id="client-edgar",
                    assigned_tools=list(EDGAR_TOOLS),
                )
            )


# ---------------------------------------------------------------------------
# Per-agent authorization + tool discovery
# ---------------------------------------------------------------------------


class TestEdgarAuthorization:
    def test_authorizer_allows_edgar_financials_when_assigned(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)

        assigned = [ToolName.EDGAR_FINANCIALS]
        # check() raises on failure; smoke-test the happy path.
        authorizer.check("agent-x", assigned, ToolName.EDGAR_FINANCIALS)

    def test_authorizer_rejects_edgar_tool_not_in_assigned_list(self) -> None:
        from keystone.gateway.auth import AuthorizationError

        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)

        assigned = [ToolName.EDGAR_FILINGS]
        with pytest.raises(AuthorizationError):
            authorizer.check("agent-y", assigned, ToolName.EDGAR_FINANCIALS)

    def test_agent_tool_discovery_returns_edgar_entries(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)

        assigned = list(EDGAR_TOOLS)
        entries = authorizer.get_agent_tools(assigned)
        assert {e.name for e in entries} == set(EDGAR_TOOLS)


# ---------------------------------------------------------------------------
# Description budget sanity
# ---------------------------------------------------------------------------


class TestBudgetStaysUnderCap:
    def test_budget_under_10k_with_new_edgar_tools(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        # The new EDGAR sub-tool descriptions must still leave the
        # aggregate tool-description budget comfortably under the
        # documented 10k-token ceiling.
        assert registry.get_description_budget() < 10_000


# ---------------------------------------------------------------------------
# End-to-end discovery via MCPGateway + mocked stdio server
# ---------------------------------------------------------------------------


class TestEdgarToolDiscoveryEndToEnd:
    @pytest.mark.asyncio
    async def test_gateway_dispatches_each_edgar_tool(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)
        limiter = InMemoryRateLimiter(build_default_rate_limits())
        audit = AuditLogger()

        client = MockMCPClient()
        # Canned responses mimic what edgartools.mcp would return.
        client.set_response(
            ToolName.EDGAR_FILINGS,
            {"filings": [{"form": "10-K", "cik": "0001045810", "filed": "2025-02-21"}]},
        )
        client.set_response(
            ToolName.EDGAR_FINANCIALS,
            {"statements": {"income": [{"concept": "Revenues", "value": 60_922_000_000}]}},
        )
        client.set_response(
            ToolName.EDGAR_COMPANY_FACTS,
            {
                "facts": {
                    "us-gaap": {
                        "Revenues": {"units": {"USD": [{"fy": 2025, "val": 60_922_000_000}]}}
                    }
                }
            },
        )

        gateway = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=limiter,
            audit_logger=audit,
            client=client,
        )

        results: list[Any] = []
        for name in EDGAR_TOOLS:
            out = await gateway.execute(
                ToolCall(
                    agent_id="agent-edgar",
                    tool_name=name,
                    parameters={"ticker": "NVDA"},
                    engagement_id="eng-1",
                    client_id="client-1",
                    assigned_tools=list(EDGAR_TOOLS),
                )
            )
            results.append(out.result)

        # All three sub-tools dispatched successfully and produced the
        # canned payloads, proving registry-based discovery works for
        # each EDGAR capability.
        assert "filings" in results[0]
        assert "statements" in results[1]
        assert "facts" in results[2]

    @pytest.mark.asyncio
    async def test_audit_log_records_edgar_calls_under_shared_server(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        authorizer = ToolAuthorizer(registry)
        limiter = InMemoryRateLimiter(build_default_rate_limits())
        audit = AuditLogger()
        client = MockMCPClient()
        for name in EDGAR_TOOLS:
            client.set_response(name, {"status": "ok"})

        gateway = MCPGateway(
            registry=registry,
            authorizer=authorizer,
            rate_limiter=limiter,
            audit_logger=audit,
            client=client,
        )

        for name in EDGAR_TOOLS:
            await gateway.execute(
                ToolCall(
                    agent_id="agent-a",
                    tool_name=name,
                    parameters={"cik": "0000320193"},
                    engagement_id="eng-a",
                    client_id="client-a",
                    assigned_tools=list(EDGAR_TOOLS),
                )
            )

        entries = audit.get_entries()
        edgar_entries = [e for e in entries if e.tool_name in set(EDGAR_TOOLS)]
        assert len(edgar_entries) == len(EDGAR_TOOLS)
        # Every EDGAR entry records the same upstream server, which is
        # what makes per-server rate/circuit aggregation work.
        servers = {registry.get(e.tool_name).server_name for e in edgar_entries}  # type: ignore[union-attr]
        assert servers == {EDGAR_SERVER_NAME}


# Allow this module to be run directly for fast iteration:
#   python -m pytest tests/unit/gateway/test_edgar_integration.py -q
if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(asyncio.run(pytest.main(["-x", __file__])))
