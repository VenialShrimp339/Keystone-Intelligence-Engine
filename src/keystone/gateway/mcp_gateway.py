"""Central MCP Gateway router for the Keystone Intelligence Engine.

All tool calls from research agents flow through this gateway.
Orchestrates: authorization -> rate limiting -> circuit breaking ->
execution -> citation extraction -> audit logging.

Directive 9: every tool execution has max 3 retries with exponential
backoff. Dead-letter logging after exhaustion (tool call recorded as
failed, not silently dropped).

Phase 1: MCP server calls are stubbed via MockMCPClient.
Phase 1B: RealMCPClient uses FastMCP to talk to real MCP servers.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import AuthorizationError, ToolAuthorizer
from keystone.gateway.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimitExceeded
from keystone.gateway.tool_registry import HealthStatus, ToolRegistry


# ---------------------------------------------------------------------------
# Data classes for tool call I/O
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """A request to execute a tool via the gateway."""

    agent_id: str
    tool_name: str
    parameters: dict[str, Any]
    engagement_id: str
    client_id: str
    assigned_tools: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    result: Any
    citations: list[dict[str, Any]]
    tokens_used: int
    latency_ms: float
    cache_hit: bool = False


# ---------------------------------------------------------------------------
# MCP Client Protocol + Implementations
# ---------------------------------------------------------------------------

@runtime_checkable
class MCPClient(Protocol):
    """Protocol for MCP server communication.

    Phase 1: MockMCPClient returns canned responses.
    Phase 1B: RealMCPClient uses FastMCP client to talk to real servers.
    """

    async def call_tool(
        self, server: str, tool: str, params: dict[str, Any]
    ) -> Any: ...


class MockMCPClient:
    """Returns canned responses for testing and Phase 1 development.

    Configurable responses per tool for test scenarios.
    """

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {}
        self._should_fail: dict[str, Exception] = {}
        self.call_count: int = 0

    def set_response(self, tool: str, response: Any) -> None:
        """Set a canned response for a tool."""
        self._responses[tool] = response

    def set_failure(self, tool: str, error: Exception) -> None:
        """Set a tool to raise an exception on call."""
        self._should_fail[tool] = error

    def clear_failure(self, tool: str) -> None:
        """Remove a configured failure for a tool."""
        self._should_fail.pop(tool, None)

    async def call_tool(
        self, server: str, tool: str, params: dict[str, Any]
    ) -> Any:
        self.call_count += 1

        if tool in self._should_fail:
            raise self._should_fail[tool]

        if tool in self._responses:
            return self._responses[tool]

        # Default canned response
        return {
            "status": "ok",
            "tool": tool,
            "server": server,
            "data": f"Mock result for {tool}",
        }


# ---------------------------------------------------------------------------
# Citation extraction (Phase 1: basic URL and reference extraction)
# ---------------------------------------------------------------------------

# URL pattern for basic citation extraction
_URL_PATTERN = re.compile(r'https?://[^\s<>"\')\]]+')


def extract_citations(result: Any) -> list[dict[str, Any]]:
    """Extract citations from tool output.

    Phase 1: basic URL extraction and direct attribute references.
    Full deduplication and verification happens in CitationProcessor.
    Structured citations are extracted first (they carry richer metadata
    like titles), then URL-pattern extraction fills in any remaining.
    """
    citations: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Structured citations first (richer metadata: title, source type)
    if isinstance(result, dict):
        _extract_structured_citations(result, citations, seen_urls)
        # Recurse into nested result lists (e.g., search API responses)
        for key in ("results", "items", "data"):
            nested = result.get(key)
            if isinstance(nested, list):
                for item in nested:
                    if isinstance(item, dict):
                        _extract_structured_citations(item, citations, seen_urls)
    elif isinstance(result, list):
        for item in result:
            if isinstance(item, dict):
                _extract_structured_citations(item, citations, seen_urls)

    # Then URL-pattern extraction for anything not already captured
    text = _result_to_text(result)
    for url in _URL_PATTERN.findall(text):
        url = url.rstrip(".,;:")
        if url not in seen_urls:
            seen_urls.add(url)
            citations.append({"url": url, "source": "tool_output"})

    return citations


def _result_to_text(result: Any) -> str:
    """Convert a tool result to searchable text."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return " ".join(str(v) for v in result.values())
    if isinstance(result, list):
        return " ".join(_result_to_text(item) for item in result)
    return str(result)


def _extract_structured_citations(
    data: dict[str, Any],
    citations: list[dict[str, Any]],
    seen_urls: set[str],
) -> None:
    """Extract citations from structured dict fields."""
    citation_keys = {"url", "link", "href", "source_url", "reference_url"}
    title_keys = {"title", "name", "headline"}
    text_keys = {"text", "description", "snippet", "content", "summary"}

    url = None
    title = None
    text = None

    for key, value in data.items():
        if key.lower() in citation_keys and isinstance(value, str):
            url = value
        if key.lower() in title_keys and isinstance(value, str):
            title = value
        if key.lower() in text_keys and isinstance(value, str) and value:
            text = value

    if url and url not in seen_urls:
        seen_urls.add(url)
        citation: dict[str, Any] = {"url": url, "source": "structured"}
        if title:
            citation["title"] = title
        if text:
            citation["text"] = text
        citations.append(citation)


# ---------------------------------------------------------------------------
# Dead-letter record
# ---------------------------------------------------------------------------

@dataclass
class DeadLetter:
    """Record of a tool call that exhausted all retries."""

    call: ToolCall
    error: Exception
    attempts: int
    total_latency_ms: float


# ---------------------------------------------------------------------------
# MCPGateway: central router
# ---------------------------------------------------------------------------

class MCPGateway:
    """Central router for all MCP tool calls.

    Orchestrates: authorization -> rate limiting -> circuit breaking ->
    execution -> citation extraction -> audit logging.

    Every tool call goes through this gateway. Research agents never
    call MCP servers directly.
    """

    MAX_RETRIES = 3
    BACKOFF_BASE = 0.5  # seconds, doubled each retry

    def __init__(
        self,
        registry: ToolRegistry,
        authorizer: ToolAuthorizer,
        rate_limiter: InMemoryRateLimiter,
        audit_logger: AuditLogger,
        client: MCPClient | None = None,
    ) -> None:
        self._registry = registry
        self._authorizer = authorizer
        self._rate_limiter = rate_limiter
        self._audit_logger = audit_logger
        self._client: MCPClient = client or MockMCPClient()
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._dead_letters: list[DeadLetter] = []

    def _get_circuit_breaker(self, server_name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a server."""
        if server_name not in self._circuit_breakers:
            self._circuit_breakers[server_name] = CircuitBreaker(
                provider=server_name
            )
        return self._circuit_breakers[server_name]

    async def execute(self, call: ToolCall) -> ToolResult:
        """Execute a tool call through the full pipeline.

        Flow:
        1. Authorize: agent has tool in assigned_tools?
        2. Rate limit: provider has capacity?
        3. Circuit break: provider healthy?
        4. Execute: call MCP server (with retry + dead-letter)
        5. Extract citations from result
        6. Audit log: record full call context
        7. Return ToolResult
        """
        start_time = time.monotonic()

        # 1. Authorize
        try:
            self._authorizer.check(
                call.agent_id, call.assigned_tools, call.tool_name
            )
        except AuthorizationError as exc:
            self._audit_logger.log_call(
                agent_id=call.agent_id,
                engagement_id=call.engagement_id,
                client_id=call.client_id,
                tool_name=call.tool_name,
                parameters=call.parameters,
                error=exc,
                latency_ms=_elapsed_ms(start_time),
            )
            raise

        # 2. Rate limit
        tool_entry = self._registry.get(call.tool_name)
        server_name = tool_entry.server_name if tool_entry else call.tool_name

        if not await self._rate_limiter.try_acquire(server_name):
            retry_after = self._rate_limiter.get_retry_after(server_name)
            exc = RateLimitExceeded(server_name, retry_after)
            self._audit_logger.log_call(
                agent_id=call.agent_id,
                engagement_id=call.engagement_id,
                client_id=call.client_id,
                tool_name=call.tool_name,
                parameters=call.parameters,
                error=exc,
                latency_ms=_elapsed_ms(start_time),
            )
            raise exc

        # 3. Circuit break + 4. Execute with retry
        cb = self._get_circuit_breaker(server_name)

        last_error: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            attempt_start = time.monotonic()
            try:
                raw_result = await cb.call(
                    self._client.call_tool,
                    server_name,
                    call.tool_name,
                    call.parameters,
                )

                # 5. Extract citations
                citations = extract_citations(raw_result)

                latency = _elapsed_ms(start_time)

                # 6. Audit log (success)
                self._audit_logger.log_call(
                    agent_id=call.agent_id,
                    engagement_id=call.engagement_id,
                    client_id=call.client_id,
                    tool_name=call.tool_name,
                    parameters=call.parameters,
                    result=raw_result,
                    latency_ms=latency,
                    retry_attempt=attempt,
                )

                # 7. Return result
                return ToolResult(
                    result=raw_result,
                    citations=citations,
                    tokens_used=0,  # Phase 1: not tracked at gateway level
                    latency_ms=latency,
                )

            except CircuitOpenError:
                # Don't retry if circuit is open, propagate immediately
                exc = CircuitOpenError(server_name, cb.recovery_timeout)
                self._audit_logger.log_call(
                    agent_id=call.agent_id,
                    engagement_id=call.engagement_id,
                    client_id=call.client_id,
                    tool_name=call.tool_name,
                    parameters=call.parameters,
                    error=exc,
                    latency_ms=_elapsed_ms(start_time),
                )
                raise exc

            except Exception as exc:
                last_error = exc

                # Log the retry attempt
                self._audit_logger.log_call(
                    agent_id=call.agent_id,
                    engagement_id=call.engagement_id,
                    client_id=call.client_id,
                    tool_name=call.tool_name,
                    parameters=call.parameters,
                    error=exc,
                    latency_ms=_elapsed_ms(attempt_start),
                    retry_attempt=attempt,
                )

                # Exponential backoff before retry (skip on last attempt)
                if attempt < self.MAX_RETRIES - 1:
                    backoff = self.BACKOFF_BASE * (2 ** attempt)
                    await asyncio.sleep(backoff)

        # All retries exhausted: dead-letter
        total_latency = _elapsed_ms(start_time)
        assert last_error is not None

        dead_letter = DeadLetter(
            call=call,
            error=last_error,
            attempts=self.MAX_RETRIES,
            total_latency_ms=total_latency,
        )
        self._dead_letters.append(dead_letter)

        # Log the dead-letter
        self._audit_logger.log_call(
            agent_id=call.agent_id,
            engagement_id=call.engagement_id,
            client_id=call.client_id,
            tool_name=call.tool_name,
            parameters=call.parameters,
            error=last_error,
            latency_ms=total_latency,
            retry_attempt=self.MAX_RETRIES - 1,
            dead_lettered=True,
        )

        raise last_error

    @property
    def dead_letters(self) -> list[DeadLetter]:
        """Return all dead-lettered tool calls."""
        return list(self._dead_letters)

    def get_circuit_state(self, server_name: str) -> CircuitState:
        """Return circuit breaker state for a server."""
        cb = self._circuit_breakers.get(server_name)
        if cb is None:
            return CircuitState.CLOSED
        return cb.state


def _elapsed_ms(start: float) -> float:
    """Calculate elapsed milliseconds since start (monotonic)."""
    return (time.monotonic() - start) * 1000
