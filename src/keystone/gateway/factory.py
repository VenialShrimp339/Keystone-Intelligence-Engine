"""Production-wired MCP gateway factory.

The gateway constructor is intentionally explicit: it takes every
sub-component so tests can inject in-memory doubles for the registry,
rate limiter, authorizer, audit logger, or client. That flexibility is
the right default for tests but it shifts assembly cost onto every
orchestrator caller. This module holds the canonical "wire everything
up with defaults" function so the orchestrator and integration scripts
do not re-invent the same boilerplate.

Defaults applied by :func:`build_mcp_gateway`:

- ``ToolRegistry`` is populated by :func:`register_all_tools` so every
  entry from :data:`TOOL_CONFIGS` is available.
- ``InMemoryRateLimiter`` is built from :func:`build_default_rate_limits`
  so EDGAR calls stay under SEC's 10 req/sec ceiling and internal
  retrieval traffic gets a generous 50 req/sec budget out of the box.
- ``ToolAuthorizer`` is wired to the populated registry so the
  specification engine's tool assignments are the single source of
  truth for per-agent tool access.
- ``AuditLogger`` is created with default settings. Callers that need a
  shared logger instance (e.g. for cross-process export) inject their
  own.

Every component is injectable so tests can exercise the factory path
while still overriding individual surfaces.
"""

from __future__ import annotations

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPClient, MCPGateway
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.servers import build_default_rate_limits, register_all_tools
from keystone.gateway.tool_registry import ToolRegistry


def build_mcp_gateway(
    *,
    client: MCPClient | None = None,
    registry: ToolRegistry | None = None,
    rate_limiter: InMemoryRateLimiter | None = None,
    audit_logger: AuditLogger | None = None,
) -> MCPGateway:
    """Return an :class:`MCPGateway` with production defaults applied.

    Inject any component to override the default. Leaving all four
    kwargs at ``None`` produces the canonical gateway used by the
    orchestrator.
    """

    if registry is None:
        registry = ToolRegistry()
        register_all_tools(registry)
    if rate_limiter is None:
        rate_limiter = InMemoryRateLimiter(build_default_rate_limits())
    if audit_logger is None:
        audit_logger = AuditLogger()

    authorizer = ToolAuthorizer(registry)
    return MCPGateway(
        registry=registry,
        authorizer=authorizer,
        rate_limiter=rate_limiter,
        audit_logger=audit_logger,
        client=client,
    )
