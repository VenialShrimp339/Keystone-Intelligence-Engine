"""Tool registry for the MCP Gateway.

Maintains a registry of all available MCP servers and their tools.
The Specification Engine queries this when assigning tools to agents.
Each tool entry tracks transport type, health status, and server config.

Extraction patterns from mcp-gateway:
- GatewayState singleton pattern (core/state.py): centralized registry
- Pydantic Settings config (core/config.py): env-based configuration
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TransportType(StrEnum):
    """MCP server transport mechanism.

    ``IN_PROCESS`` covers system-owned tools (like the retrieval
    service's ``semantic_search`` / ``hybrid_search``) that are
    served inside the Keystone process itself rather than through a
    separate MCP server binary. The gateway still routes through the
    usual authorization/rate-limit/audit path but the underlying
    client delegates to an in-process handler.
    """

    HTTP = "http"
    STDIO = "stdio"
    DOCKER = "docker"
    IN_PROCESS = "in_process"


class HealthStatus(StrEnum):
    """Health state of an MCP server."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ToolEntry(BaseModel):
    """A registered MCP tool.

    Each entry represents a single tool exposed by an MCP server.
    Multiple tools can share the same server_name (e.g., exa_search
    and exa_find_similar both come from exa-mcp-server).
    """

    name: str = Field(description="Tool identifier, e.g. 'exa_search'")
    server_name: str = Field(description="MCP server name, e.g. 'exa-mcp-server'")
    description: str = Field(description="Short description for context-window budget")
    transport_type: TransportType = Field(description="How the gateway connects to this server")
    security_approved: bool = Field(
        default=True, description="Whether this tool has passed security review"
    )
    health_status: HealthStatus = Field(
        default=HealthStatus.UNKNOWN, description="Current health state"
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Server-specific config (API key env var names, URLs, etc.)",
    )


class ToolRegistry:
    """Registry of available MCP servers with health checks.

    Singleton pattern extracted from mcp-gateway's GatewayState.
    Provides tool lookup, health monitoring, and description budget
    tracking for context-window efficiency.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}
        self._lock = asyncio.Lock()

    def register(self, entry: ToolEntry) -> None:
        """Register a tool. Overwrites if name already exists."""
        self._tools[entry.name] = entry

    def get(self, tool_name: str) -> ToolEntry | None:
        """Look up a tool by name. Returns None if not found."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[ToolEntry]:
        """Return all registered tools."""
        return list(self._tools.values())

    def list_tool_names(self) -> list[str]:
        """Return names of all registered tools."""
        return list(self._tools.keys())

    def get_by_server(self, server_name: str) -> list[ToolEntry]:
        """Return all tools provided by a specific MCP server."""
        return [t for t in self._tools.values() if t.server_name == server_name]

    def get_description_budget(self) -> int:
        """Estimate total tokens for all tool descriptions.

        Uses a simple word-count heuristic (1 token ~ 0.75 words).
        Target: < 10,000 tokens with all servers registered.
        """
        total_chars = sum(len(t.name) + len(t.description) for t in self._tools.values())
        # ~4 chars per token is a reasonable estimate for English text
        return total_chars // 4

    async def health_check(self, tool_name: str) -> HealthStatus:
        """Check health of a single tool's server.

        Phase 1: returns current stored status.
        Phase 1B: will actually probe the MCP server.
        """
        entry = self._tools.get(tool_name)
        if entry is None:
            return HealthStatus.UNKNOWN
        return entry.health_status

    async def health_check_all(self) -> dict[str, HealthStatus]:
        """Check health of all registered tools.

        Phase 1: returns stored statuses.
        Phase 1B: will probe all MCP servers concurrently.
        """
        return {name: entry.health_status for name, entry in self._tools.items()}

    async def update_health(self, tool_name: str, status: HealthStatus) -> None:
        """Update the health status of a tool."""
        async with self._lock:
            entry = self._tools.get(tool_name)
            if entry is not None:
                self._tools[tool_name] = entry.model_copy(update={"health_status": status})

    def __len__(self) -> int:
        return len(self._tools)
