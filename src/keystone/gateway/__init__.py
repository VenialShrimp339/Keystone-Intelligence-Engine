"""MCP Gateway: Central router for all tool calls in the Keystone Intelligence Engine.

Every research agent calls tools exclusively through this gateway.
Enforces per-agent authorization, rate limits, circuit breaking, and audit logging.

Usage:
    from keystone.gateway import MCPGateway, ToolRegistry, ToolAuthorizer
"""

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import AuthorizationError, ToolAuthorizer
from keystone.gateway.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from keystone.gateway.factory import build_mcp_gateway
from keystone.gateway.mcp_gateway import (
    DeadLetter,
    InProcessHandler,
    MCPClient,
    MCPGateway,
    MockMCPClient,
    ToolCall,
    ToolResult,
)
from keystone.gateway.rate_limiter import (
    InMemoryRateLimiter,
    RateLimit,
    RateLimitExceeded,
    RateLimiterBackend,
)
from keystone.gateway.retrieval_bridge import (
    build_retrieval_handlers,
    register_retrieval_handlers,
)
from keystone.gateway.servers import (
    SERVER_RATE_LIMITS,
    TOOL_CONFIGS,
    build_default_rate_limits,
    register_all_tools,
)
from keystone.gateway.tool_registry import HealthStatus, ToolEntry, ToolRegistry, TransportType

__all__ = [
    "AuditLogger",
    "AuthorizationError",
    "CircuitBreaker",
    "CircuitOpenError",
    "CircuitState",
    "DeadLetter",
    "HealthStatus",
    "InMemoryRateLimiter",
    "InProcessHandler",
    "MCPClient",
    "MCPGateway",
    "MockMCPClient",
    "RateLimit",
    "RateLimitExceeded",
    "RateLimiterBackend",
    "SERVER_RATE_LIMITS",
    "TOOL_CONFIGS",
    "ToolAuthorizer",
    "ToolCall",
    "ToolEntry",
    "ToolRegistry",
    "ToolResult",
    "TransportType",
    "build_default_rate_limits",
    "build_mcp_gateway",
    "build_retrieval_handlers",
    "register_all_tools",
    "register_retrieval_handlers",
]
