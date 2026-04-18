"""Tests for the MCP Gateway per-agent tool authorization."""

import pytest

from keystone.gateway.auth import AuthorizationError, ToolAuthorizer
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_entry(name: str) -> ToolEntry:
    return ToolEntry(
        name=name,
        server_name=f"{name}-server",
        description=f"Tool: {name}",
        transport_type=TransportType.HTTP,
    )


@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(_make_entry("exa_search"))
    reg.register(_make_entry("brave_search"))
    reg.register(_make_entry("edgar_filings"))
    return reg


@pytest.fixture
def authorizer(registry: ToolRegistry) -> ToolAuthorizer:
    return ToolAuthorizer(registry)


# ---------------------------------------------------------------------------
# Authorization checks
# ---------------------------------------------------------------------------


class TestCheck:
    def test_authorized_tool_succeeds(self, authorizer: ToolAuthorizer) -> None:
        """Agent with assigned tools can access them."""
        authorizer.check(
            agent_id="agent_001",
            assigned_tools=["exa_search", "brave_search"],
            tool_name="exa_search",
        )

    def test_unauthorized_tool_raises(self, authorizer: ToolAuthorizer) -> None:
        """Agent without assigned tool gets AuthorizationError."""
        with pytest.raises(AuthorizationError) as exc_info:
            authorizer.check(
                agent_id="agent_001",
                assigned_tools=["exa_search"],
                tool_name="edgar_filings",
            )
        assert "agent_001" in str(exc_info.value)
        assert "edgar_filings" in str(exc_info.value)

    def test_empty_assigned_tools_blocks_all(self, authorizer: ToolAuthorizer) -> None:
        """Empty assigned_tools list blocks all tools."""
        with pytest.raises(AuthorizationError):
            authorizer.check(
                agent_id="agent_002",
                assigned_tools=[],
                tool_name="exa_search",
            )

    def test_unregistered_tool_raises(self, authorizer: ToolAuthorizer) -> None:
        """Tool not in registry raises AuthorizationError even if in assigned list."""
        with pytest.raises(AuthorizationError):
            authorizer.check(
                agent_id="agent_003",
                assigned_tools=["nonexistent_tool"],
                tool_name="nonexistent_tool",
            )

    def test_error_contains_agent_id_and_tool(self, authorizer: ToolAuthorizer) -> None:
        """AuthorizationError message has useful diagnostics."""
        try:
            authorizer.check(
                agent_id="agent_007",
                assigned_tools=["brave_search"],
                tool_name="exa_search",
            )
            pytest.fail("Should have raised AuthorizationError")
        except AuthorizationError as e:
            assert e.agent_id == "agent_007"
            assert e.tool_name == "exa_search"
            assert e.assigned_tools == ["brave_search"]


# ---------------------------------------------------------------------------
# get_agent_tools
# ---------------------------------------------------------------------------


class TestGetAgentTools:
    def test_returns_matching_entries(self, authorizer: ToolAuthorizer) -> None:
        entries = authorizer.get_agent_tools(["exa_search", "brave_search"])
        assert len(entries) == 2
        names = {e.name for e in entries}
        assert names == {"exa_search", "brave_search"}

    def test_skips_unregistered_tools(self, authorizer: ToolAuthorizer) -> None:
        entries = authorizer.get_agent_tools(["exa_search", "nonexistent"])
        assert len(entries) == 1
        assert entries[0].name == "exa_search"

    def test_empty_list_returns_empty(self, authorizer: ToolAuthorizer) -> None:
        entries = authorizer.get_agent_tools([])
        assert entries == []
