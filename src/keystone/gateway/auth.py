"""Per-agent tool authorization for the MCP Gateway.

Structural enforcement: agents can only call tools in their assigned_tools
list. This is checked at the gateway level before any tool execution,
not enforced via prompts (which drift ~40% per CLAUDE.md empirical anchors).

The Specification Engine assigns 3-5 tools per research agent via
ResearchTask.assigned_tools. The gateway enforces this structurally.
"""

from __future__ import annotations

from keystone.gateway.tool_registry import ToolEntry, ToolRegistry
from keystone.tool_names import SYSTEM_OWNED_TOOLS


class AuthorizationError(Exception):
    """Agent attempted to call a tool not in its assigned_tools list."""

    def __init__(self, agent_id: str, tool_name: str, assigned_tools: list[str]) -> None:
        self.agent_id = agent_id
        self.tool_name = tool_name
        self.assigned_tools = assigned_tools
        super().__init__(
            f"Agent '{agent_id}' not authorized for tool '{tool_name}'. "
            f"Assigned tools: {assigned_tools}"
        )


class ToolAuthorizer:
    """Per-agent tool authorization.

    Enforces two invariants on every :meth:`check` call:

    1. ``tool_name`` must not be in :data:`SYSTEM_OWNED_TOOLS` -- those
       are invoked by the gateway / orchestrator directly (via the
       in-process handler registry) and must never be reachable through
       ``gateway.execute()``. This is defense-in-depth behind the
       template-level canary that already prevents system-owned tools
       from appearing in agent templates; a template regression cannot
       slip past this gate.
    2. ``tool_name`` must be in the agent's ``assigned_tools`` list and
       must also be registered in the :class:`ToolRegistry`.
    """

    _SYSTEM_OWNED: frozenset[str] = frozenset(SYSTEM_OWNED_TOOLS)

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def check(self, agent_id: str, assigned_tools: list[str], tool_name: str) -> None:
        """Verify agent is authorized to call tool_name.

        Raises AuthorizationError if:
        - tool_name is in :data:`SYSTEM_OWNED_TOOLS` (regardless of
          what ``assigned_tools`` contains)
        - tool_name is not in the agent's assigned_tools list
        - tool_name is not registered in the registry
        """
        if tool_name in self._SYSTEM_OWNED:
            raise AuthorizationError(agent_id, tool_name, assigned_tools)

        if tool_name not in assigned_tools:
            raise AuthorizationError(agent_id, tool_name, assigned_tools)

        entry = self._registry.get(tool_name)
        if entry is None:
            raise AuthorizationError(agent_id, tool_name, assigned_tools)

    def get_agent_tools(self, assigned_tools: list[str]) -> list[ToolEntry]:
        """Return ToolEntry objects for the agent's assigned tools.

        Filters out any tools not found in the registry (graceful
        degradation if a tool was deregistered mid-engagement).
        """
        entries = []
        for tool_name in assigned_tools:
            entry = self._registry.get(tool_name)
            if entry is not None:
                entries.append(entry)
        return entries
