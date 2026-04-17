"""Tests for the MCP Gateway tool registry."""

import pytest

from keystone.gateway.servers import TOOL_CONFIGS, register_all_tools
from keystone.gateway.tool_registry import (
    HealthStatus,
    ToolEntry,
    ToolRegistry,
    TransportType,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_entry(name: str = "test_tool", **overrides) -> ToolEntry:
    defaults = {
        "name": name,
        "server_name": "test-server",
        "description": "A test tool for unit testing.",
        "transport_type": TransportType.HTTP,
    }
    defaults.update(overrides)
    return ToolEntry(**defaults)


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


# ---------------------------------------------------------------------------
# Registration and retrieval
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_and_get(self, registry: ToolRegistry) -> None:
        entry = _make_entry("exa_search")
        registry.register(entry)
        assert registry.get("exa_search") is not None
        assert registry.get("exa_search").name == "exa_search"

    def test_get_unknown_returns_none(self, registry: ToolRegistry) -> None:
        assert registry.get("nonexistent") is None

    def test_register_overwrites(self, registry: ToolRegistry) -> None:
        entry1 = _make_entry("tool_a", description="version 1")
        entry2 = _make_entry("tool_a", description="version 2")
        registry.register(entry1)
        registry.register(entry2)
        assert registry.get("tool_a").description == "version 2"
        assert len(registry) == 1

    def test_list_tools(self, registry: ToolRegistry) -> None:
        registry.register(_make_entry("b_tool"))
        registry.register(_make_entry("a_tool"))
        tools = registry.list_tools()
        assert len(tools) == 2

    def test_list_tool_names(self, registry: ToolRegistry) -> None:
        registry.register(_make_entry("z_tool"))
        registry.register(_make_entry("a_tool"))
        names = registry.list_tool_names()
        assert "a_tool" in names
        assert "z_tool" in names

    def test_len(self, registry: ToolRegistry) -> None:
        assert len(registry) == 0
        registry.register(_make_entry("tool1"))
        assert len(registry) == 1
        registry.register(_make_entry("tool2"))
        assert len(registry) == 2

    def test_get_by_server(self, registry: ToolRegistry) -> None:
        registry.register(_make_entry("tool_a", server_name="server_x"))
        registry.register(_make_entry("tool_b", server_name="server_x"))
        registry.register(_make_entry("tool_c", server_name="server_y"))
        results = registry.get_by_server("server_x")
        assert len(results) == 2
        assert all(t.server_name == "server_x" for t in results)


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_unknown_tool(self, registry: ToolRegistry) -> None:
        status = await registry.health_check("nonexistent")
        assert status == HealthStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_health_check_returns_stored_status(self, registry: ToolRegistry) -> None:
        entry = _make_entry("tool_a", health_status=HealthStatus.HEALTHY)
        registry.register(entry)
        status = await registry.health_check("tool_a")
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_all(self, registry: ToolRegistry) -> None:
        registry.register(_make_entry("tool_a", health_status=HealthStatus.HEALTHY))
        registry.register(_make_entry("tool_b", health_status=HealthStatus.DEGRADED))
        statuses = await registry.health_check_all()
        assert statuses["tool_a"] == HealthStatus.HEALTHY
        assert statuses["tool_b"] == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_update_health(self, registry: ToolRegistry) -> None:
        registry.register(_make_entry("tool_a"))
        await registry.update_health("tool_a", HealthStatus.UNHEALTHY)
        status = await registry.health_check("tool_a")
        assert status == HealthStatus.UNHEALTHY


# ---------------------------------------------------------------------------
# Description budget
# ---------------------------------------------------------------------------


class TestDescriptionBudget:
    def test_budget_with_all_servers(self) -> None:
        """All 7 server configs should total under 10,000 tokens."""
        registry = ToolRegistry()
        register_all_tools(registry)
        budget = registry.get_description_budget()
        assert budget < 10_000, f"Description budget {budget} exceeds 10,000 token limit"

    def test_budget_empty_registry(self, registry: ToolRegistry) -> None:
        assert registry.get_description_budget() == 0


# ---------------------------------------------------------------------------
# Server configurations
# ---------------------------------------------------------------------------


class TestServerConfigs:
    def test_tool_count_matches_configured_entries(self) -> None:
        # Exa, Brave, three EDGAR sub-tools, FRED, paper search, DOI, Finnhub.
        assert len(TOOL_CONFIGS) == 9

    def test_unique_server_count(self) -> None:
        # Multiple tool names can share a server_name (e.g. all EDGAR tools
        # speak to edgartools-mcp). The distinct upstream-server count is 7.
        server_names = {entry.server_name for entry in TOOL_CONFIGS.values()}
        assert len(server_names) == 7

    def test_register_all_tools(self) -> None:
        registry = ToolRegistry()
        register_all_tools(registry)
        assert len(registry) == len(TOOL_CONFIGS)

    def test_transport_types_correct(self) -> None:
        # HTTP servers
        assert TOOL_CONFIGS["exa_search"].transport_type == TransportType.HTTP
        assert TOOL_CONFIGS["brave_search"].transport_type == TransportType.HTTP
        assert TOOL_CONFIGS["paper_search"].transport_type == TransportType.HTTP
        assert TOOL_CONFIGS["finnhub_market"].transport_type == TransportType.HTTP

        # stdio servers
        assert TOOL_CONFIGS["edgar_filings"].transport_type == TransportType.STDIO
        assert TOOL_CONFIGS["fred_data"].transport_type == TransportType.STDIO
        assert TOOL_CONFIGS["doi_verify"].transport_type == TransportType.STDIO

    def test_security_approved_defaults(self) -> None:
        for entry in TOOL_CONFIGS.values():
            assert entry.security_approved is True

    def test_each_tool_has_description(self) -> None:
        for name, entry in TOOL_CONFIGS.items():
            assert entry.description, f"{name} has empty description"
            assert len(entry.description) > 10, f"{name} description too short"
