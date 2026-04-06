"""Tests for per-agent tool authorization."""

import pytest

from keystone.gateway.auth import AuthorizationError, ToolAuthorizer
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType


def _make_registry(*tool_names: str) -> ToolRegistry:
    registry = ToolRegistry()
    for name in tool_names:
        registry.register(
            ToolEntry(
                name=name,
                server_name=f"{name}-server",
                description=f"Test tool {name}",
                transport_type=TransportType.HTTP,
            )
        )
    return registry


class TestToolAuthorizer:
    def test_authorized_tool_passes(self):
        registry = _make_registry("exa_search", "brave_search")
        authorizer = ToolAuthorizer(registry)

        # Should not raise
        authorizer.check("agent-1", ["exa_search", "brave_search"], "exa_search")

    def test_unauthorized_tool_raises(self):
        registry = _make_registry("exa_search", "brave_search", "edgar_filings")
        authorizer = ToolAuthorizer(registry)

        with pytest.raises(AuthorizationError) as exc_info:
            authorizer.check(
                "agent-1", ["exa_search", "brave_search"], "edgar_filings"
            )

        assert exc_info.value.agent_id == "agent-1"
        assert exc_info.value.tool_name == "edgar_filings"
        assert exc_info.value.assigned_tools == ["exa_search", "brave_search"]

    def test_empty_assigned_tools_blocks_all(self):
        registry = _make_registry("exa_search")
        authorizer = ToolAuthorizer(registry)

        with pytest.raises(AuthorizationError):
            authorizer.check("agent-1", [], "exa_search")

    def test_unregistered_tool_raises(self):
        """Tool in assigned_tools but not in registry should raise."""
        registry = _make_registry("exa_search")
        authorizer = ToolAuthorizer(registry)

        with pytest.raises(AuthorizationError):
            authorizer.check("agent-1", ["nonexistent_tool"], "nonexistent_tool")

    def test_get_agent_tools_returns_entries(self):
        registry = _make_registry("exa_search", "brave_search", "edgar_filings")
        authorizer = ToolAuthorizer(registry)

        tools = authorizer.get_agent_tools(["exa_search", "brave_search"])
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"exa_search", "brave_search"}

    def test_get_agent_tools_skips_missing(self):
        """If a tool was deregistered, get_agent_tools gracefully skips it."""
        registry = _make_registry("exa_search")
        authorizer = ToolAuthorizer(registry)

        tools = authorizer.get_agent_tools(["exa_search", "removed_tool"])
        assert len(tools) == 1
        assert tools[0].name == "exa_search"

    def test_authorization_error_message_format(self):
        registry = _make_registry("exa_search")
        authorizer = ToolAuthorizer(registry)

        with pytest.raises(AuthorizationError, match="not authorized"):
            authorizer.check("agent-42", ["exa_search"], "brave_search")
