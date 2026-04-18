"""Tests for the MCP Gateway tool registry."""

import pytest

from keystone.gateway.servers import TOOL_CONFIGS, register_all_tools
from keystone.gateway.tool_registry import (
    HealthStatus,
    ToolEntry,
    ToolRegistry,
    TransportType,
)


def _make_entry(name: str = "test_tool", **kwargs) -> ToolEntry:
    defaults = {
        "name": name,
        "server_name": "test-server",
        "description": "A test tool for unit testing",
        "transport_type": TransportType.HTTP,
    }
    defaults.update(kwargs)
    return ToolEntry(**defaults)


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        entry = _make_entry("exa_search")
        registry.register(entry)

        result = registry.get("exa_search")
        assert result is not None
        assert result.name == "exa_search"

    def test_get_unknown_returns_none(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a"))
        registry.register(_make_entry("tool_b"))

        tools = registry.list_tools()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"tool_a", "tool_b"}

    def test_list_tool_names(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a"))
        registry.register(_make_entry("tool_b"))

        names = registry.list_tool_names()
        assert set(names) == {"tool_a", "tool_b"}

    def test_overwrite_on_duplicate(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a", description="v1"))
        registry.register(_make_entry("tool_a", description="v2"))

        assert len(registry) == 1
        assert registry.get("tool_a").description == "v2"

    def test_get_by_server(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a", server_name="server-1"))
        registry.register(_make_entry("tool_b", server_name="server-1"))
        registry.register(_make_entry("tool_c", server_name="server-2"))

        server_1_tools = registry.get_by_server("server-1")
        assert len(server_1_tools) == 2
        assert {t.name for t in server_1_tools} == {"tool_a", "tool_b"}

    def test_len(self):
        registry = ToolRegistry()
        assert len(registry) == 0
        registry.register(_make_entry("tool_a"))
        assert len(registry) == 1


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_unknown_tool(self):
        registry = ToolRegistry()
        status = await registry.health_check("nonexistent")
        assert status == HealthStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_health_check_returns_stored_status(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a", health_status=HealthStatus.HEALTHY))
        status = await registry.health_check("tool_a")
        assert status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_all(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a", health_status=HealthStatus.HEALTHY))
        registry.register(_make_entry("tool_b", health_status=HealthStatus.DEGRADED))

        statuses = await registry.health_check_all()
        assert statuses["tool_a"] == HealthStatus.HEALTHY
        assert statuses["tool_b"] == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_update_health(self):
        registry = ToolRegistry()
        registry.register(_make_entry("tool_a"))

        await registry.update_health("tool_a", HealthStatus.UNHEALTHY)
        status = await registry.health_check("tool_a")
        assert status == HealthStatus.UNHEALTHY


class TestDescriptionBudget:
    def test_budget_under_10k_with_all_servers(self):
        """All 7 configured servers must fit under 10,000 token budget."""
        registry = ToolRegistry()
        register_all_tools(registry)

        budget = registry.get_description_budget()
        assert budget < 10_000, f"Description budget {budget} tokens exceeds 10,000 limit"

    def test_budget_is_zero_when_empty(self):
        registry = ToolRegistry()
        assert registry.get_description_budget() == 0


class TestServerConfigs:
    def test_tool_count_matches_configured_entries(self):
        """TOOL_CONFIGS tracks every registered tool (assignable + system-owned)."""
        # Exa, Brave, three EDGAR sub-tools (all on edgartools-mcp), FRED,
        # paper search, DOI, Finnhub, plus semantic_search / hybrid_search
        # (both on keystone-retrieval) => 11 tool names across 8 unique
        # upstream servers.
        assert len(TOOL_CONFIGS) == 11

    def test_unique_server_count(self):
        """Exactly 8 distinct upstream servers back the registered tools."""
        server_names = {entry.server_name for entry in TOOL_CONFIGS.values()}
        assert len(server_names) == 8

    def test_register_all_tools_populates_registry(self):
        registry = ToolRegistry()
        register_all_tools(registry)
        assert len(registry) == len(TOOL_CONFIGS)

    def test_transport_types_mixed(self):
        """Must have both HTTP and stdio servers."""
        http = [e for e in TOOL_CONFIGS.values() if e.transport_type == TransportType.HTTP]
        stdio = [e for e in TOOL_CONFIGS.values() if e.transport_type == TransportType.STDIO]
        assert len(http) >= 1
        assert len(stdio) >= 1

    def test_each_entry_has_description(self):
        for name, entry in TOOL_CONFIGS.items():
            assert entry.description, f"{name} missing description"

    def test_api_keys_reference_env_vars(self):
        """Servers requiring API keys must reference env var names, not values."""
        for name, entry in TOOL_CONFIGS.items():
            if "api_key_env" in entry.config:
                assert entry.config["api_key_env"].isupper(), (
                    f"{name} api_key_env should be an env var name"
                )
