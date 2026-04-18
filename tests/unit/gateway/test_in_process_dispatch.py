"""Tests for the MCPGateway IN_PROCESS dispatch path.

Covers:
- A registered IN_PROCESS handler is invoked instead of the MCP client.
- The full gateway envelope (authorization, rate limiting, circuit
  breaker, retry, audit logging, citation extraction) still wraps the
  in-process call.
- A tool declared IN_PROCESS without a registered handler fails loudly.
- The retrieval bridge translates gateway parameters into a SearchQuery
  and serializes RetrievalResult back to a JSON-able payload.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import pytest

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient, ToolCall
from keystone.gateway.rate_limiter import InMemoryRateLimiter, RateLimit
from keystone.gateway.retrieval_bridge import (
    build_retrieval_handlers,
    register_retrieval_handlers,
)
from keystone.gateway.tool_registry import (
    ToolEntry,
    ToolRegistry,
    TransportType,
)
from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    Locator,
    ParserIdentity,
    PassageKind,
    SourceFamily,
    confidence,
)
from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import InMemoryEmbeddingClient
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import InMemoryVectorStore
from keystone.tool_names import ToolName


def _make_record(
    *,
    record_id: str = "EV-0001",
    artifact_id: str = "ART-001",
    canonical_url: str = "https://example.com/report",
    text: str = "The autonomous vehicle market grew 28% year-over-year in 2024.",
    title: str = "AV Market Report",
) -> EvidencePrepRecord:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return EvidencePrepRecord(
        record_id=record_id,
        artifact_id=artifact_id,
        canonical_url=canonical_url,
        content_hash=content_hash,
        source_family=SourceFamily.ARTICLE,
        title=title,
        text=text,
        locator=Locator(section_path=["Market"], paragraph_index=0),
        coverage=Coverage(status=CoverageStatus.COMPLETE),
        parse_confidence=confidence(0.9),
        parser=ParserIdentity(name="unit-test-parser", version="1.0"),
        passage_kind=PassageKind.PARAGRAPH,
        fetched_at=datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
    )


# Name of a non-system-owned IN_PROCESS tool used by the generic
# dispatch tests. The real retrieval tools (semantic_search /
# hybrid_search) are system-owned and must be rejected by the gateway
# authorizer, so they cannot be used to exercise the IN_PROCESS
# mechanism through ``gateway.execute``. A fake agent-assignable
# IN_PROCESS tool gives the dispatch tests a clean handle without
# weakening the system-owned gate.
FAKE_IN_PROCESS_TOOL = "fake_in_process_tool"
FAKE_IN_PROCESS_SERVER = "fake-in-process-server"


def _build_registry(
    *,
    include_retrieval: bool = True,
    include_fake_in_process: bool = True,
) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        ToolEntry(
            name="exa_search",
            server_name="exa-mcp-server",
            description="Web search",
            transport_type=TransportType.HTTP,
        )
    )
    if include_fake_in_process:
        reg.register(
            ToolEntry(
                name=FAKE_IN_PROCESS_TOOL,
                server_name=FAKE_IN_PROCESS_SERVER,
                description="Fake agent-assignable IN_PROCESS tool for dispatch tests",
                transport_type=TransportType.IN_PROCESS,
            )
        )
    if include_retrieval:
        reg.register(
            ToolEntry(
                name=ToolName.SEMANTIC_SEARCH.value,
                server_name="keystone-retrieval",
                description="Semantic search over the internal corpus",
                transport_type=TransportType.IN_PROCESS,
            )
        )
    return reg


def _build_gateway(registry: ToolRegistry) -> MCPGateway:
    rate_limiter = InMemoryRateLimiter(
        {
            "exa-mcp-server": RateLimit(max_tokens=100, refill_rate=10.0),
            "keystone-retrieval": RateLimit(max_tokens=100, refill_rate=10.0),
            FAKE_IN_PROCESS_SERVER: RateLimit(max_tokens=100, refill_rate=10.0),
        }
    )
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=rate_limiter,
        audit_logger=AuditLogger(debug=True),
        client=MockMCPClient(),
    )


def _make_retrieval_service() -> RetrievalService:
    return RetrievalService(
        chunker=SemanticChunker(),
        embedder=InMemoryEmbeddingClient(dimension=8),
        vector_store=InMemoryVectorStore(dimension=8),
        bm25_index=InMemoryBM25Index(),
    )


class TestInProcessDispatch:
    """Generic IN_PROCESS dispatch tests.

    These exercise the gateway's dispatch mechanism through a
    non-system-owned IN_PROCESS tool (``FAKE_IN_PROCESS_TOOL``) so the
    SYSTEM_OWNED_TOOLS gate in :class:`ToolAuthorizer` does not
    interfere. Tests that specifically exercise the retrieval bridge
    live in :class:`TestRetrievalBridge` and invoke handlers directly.
    """

    @pytest.mark.asyncio
    async def test_registered_handler_is_invoked(self) -> None:
        registry = _build_registry()
        gateway = _build_gateway(registry)

        calls_seen: list[ToolCall] = []

        async def handler(call: ToolCall) -> dict[str, Any]:
            calls_seen.append(call)
            return {"results": [{"url": "https://corpus.internal/chunk-1"}]}

        gateway.register_in_process_handler(FAKE_IN_PROCESS_TOOL, handler)

        call = ToolCall(
            agent_id="agent-A",
            tool_name=FAKE_IN_PROCESS_TOOL,
            parameters={"query": "autonomous vehicles"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[FAKE_IN_PROCESS_TOOL],
        )
        result = await gateway.execute(call)

        assert len(calls_seen) == 1
        assert calls_seen[0].parameters["query"] == "autonomous vehicles"
        assert calls_seen[0].agent_id == "agent-A"
        assert calls_seen[0].engagement_id == "ENG-1"
        urls = {c["url"] for c in result.citations}
        assert "https://corpus.internal/chunk-1" in urls

    @pytest.mark.asyncio
    async def test_in_process_call_audited(self) -> None:
        registry = _build_registry()
        gateway = _build_gateway(registry)

        async def handler(call: ToolCall) -> dict[str, Any]:
            return {"results": []}

        gateway.register_in_process_handler(FAKE_IN_PROCESS_TOOL, handler)

        call = ToolCall(
            agent_id="agent-A",
            tool_name=FAKE_IN_PROCESS_TOOL,
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[FAKE_IN_PROCESS_TOOL],
        )
        await gateway.execute(call)

        entries = gateway.audit_logger.get_entries(tool_name=FAKE_IN_PROCESS_TOOL)
        assert len(entries) == 1
        assert entries[0].success is True
        assert entries[0].agent_id == "agent-A"

    @pytest.mark.asyncio
    async def test_missing_handler_raises(self) -> None:
        registry = _build_registry()
        gateway = _build_gateway(registry)
        call = ToolCall(
            agent_id="agent-A",
            tool_name=FAKE_IN_PROCESS_TOOL,
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[FAKE_IN_PROCESS_TOOL],
        )
        with pytest.raises(RuntimeError, match="IN_PROCESS"):
            await gateway.execute(call)

    @pytest.mark.asyncio
    async def test_handler_error_is_retried_then_dead_lettered(self) -> None:
        registry = _build_registry()
        gateway = _build_gateway(registry)

        attempts = 0

        async def flaky_handler(call: ToolCall) -> dict[str, Any]:
            nonlocal attempts
            attempts += 1
            raise RuntimeError("upstream blew up")

        gateway.register_in_process_handler(FAKE_IN_PROCESS_TOOL, flaky_handler)

        call = ToolCall(
            agent_id="agent-A",
            tool_name=FAKE_IN_PROCESS_TOOL,
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[FAKE_IN_PROCESS_TOOL],
        )
        with pytest.raises(RuntimeError, match="upstream blew up"):
            await gateway.execute(call)

        assert attempts == gateway.MAX_RETRIES
        assert len(gateway.dead_letters) == 1

    @pytest.mark.asyncio
    async def test_non_in_process_tool_still_uses_client(self) -> None:
        """HTTP tools must not be affected by the IN_PROCESS branch."""
        registry = _build_registry()
        gateway = _build_gateway(registry)

        async def handler(call: ToolCall) -> dict[str, Any]:
            raise AssertionError("HTTP tool should not hit the in-process handler")

        gateway.register_in_process_handler(FAKE_IN_PROCESS_TOOL, handler)
        gateway._client.set_response("exa_search", {"results": [{"url": "https://x.test"}]})

        call = ToolCall(
            agent_id="agent-A",
            tool_name="exa_search",
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=["exa_search"],
        )
        result = await gateway.execute(call)
        assert any(c["url"] == "https://x.test" for c in result.citations)


class TestSystemOwnedToolGating:
    """Verify the authorizer rejects system-owned tools regardless of
    ``assigned_tools``. Defense-in-depth behind the template canary.
    """

    @pytest.mark.asyncio
    async def test_system_owned_tool_rejected_even_when_assigned(self) -> None:
        """Agent with semantic_search in assigned_tools (template regression) still blocked."""
        registry = _build_registry()
        gateway = _build_gateway(registry)

        async def handler(call: ToolCall) -> dict[str, Any]:
            raise AssertionError("system-owned handler must never be invoked via gateway.execute")

        gateway.register_in_process_handler(ToolName.SEMANTIC_SEARCH.value, handler)

        call = ToolCall(
            agent_id="agent-A",
            tool_name=ToolName.SEMANTIC_SEARCH.value,
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[ToolName.SEMANTIC_SEARCH.value],
        )
        with pytest.raises(Exception) as exc_info:
            await gateway.execute(call)
        # AuthorizationError from gateway.auth
        assert "not authorized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_hybrid_search_is_also_system_owned(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolEntry(
                name=ToolName.HYBRID_SEARCH.value,
                server_name="keystone-retrieval",
                description="hybrid",
                transport_type=TransportType.IN_PROCESS,
            )
        )
        gateway = MCPGateway(
            registry=registry,
            authorizer=ToolAuthorizer(registry),
            rate_limiter=InMemoryRateLimiter(
                {"keystone-retrieval": RateLimit(max_tokens=100, refill_rate=10.0)}
            ),
            audit_logger=AuditLogger(),
            client=MockMCPClient(),
        )

        call = ToolCall(
            agent_id="agent-X",
            tool_name=ToolName.HYBRID_SEARCH.value,
            parameters={"query": "x"},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[ToolName.HYBRID_SEARCH.value],
        )
        with pytest.raises(Exception) as exc_info:
            await gateway.execute(call)
        assert "not authorized" in str(exc_info.value).lower()

    def test_authorizer_unit_rejects_system_owned(self) -> None:
        """Direct ToolAuthorizer.check call confirms the rule without gateway plumbing."""
        from keystone.gateway.auth import AuthorizationError

        registry = _build_registry()
        authorizer = ToolAuthorizer(registry)
        with pytest.raises(AuthorizationError):
            authorizer.check(
                "agent-A", [ToolName.SEMANTIC_SEARCH.value], ToolName.SEMANTIC_SEARCH.value
            )
        with pytest.raises(AuthorizationError):
            authorizer.check(
                "agent-A", [ToolName.HYBRID_SEARCH.value], ToolName.HYBRID_SEARCH.value
            )


def _tool_call(
    *,
    tool_name: str = ToolName.SEMANTIC_SEARCH.value,
    parameters: dict[str, Any] | None = None,
    agent_id: str = "agent-A",
    engagement_id: str = "ENG-1",
    client_id: str = "CLI-1",
) -> ToolCall:
    return ToolCall(
        agent_id=agent_id,
        tool_name=tool_name,
        parameters=parameters or {"query": "market"},
        engagement_id=engagement_id,
        client_id=client_id,
        assigned_tools=[tool_name],
    )


class TestRetrievalBridge:
    @pytest.mark.asyncio
    async def test_handler_runs_against_in_memory_service(self) -> None:
        service = _make_retrieval_service()
        await service.ingest([_make_record()], engagement_id="ENG-OTHER")

        handlers = build_retrieval_handlers(service)
        payload = await handlers[ToolName.SEMANTIC_SEARCH.value](_tool_call())

        assert payload["result_count"] >= 1
        first = payload["results"][0]
        assert first["url"] == "https://example.com/report"
        assert first["text"].startswith("The autonomous vehicle")
        assert first["chunk_id"].startswith("ART-001:")

    @pytest.mark.asyncio
    async def test_register_bridge_on_gateway(self) -> None:
        """register_retrieval_handlers populates the gateway's in-process map.

        The handlers themselves are invoked by system code (the
        orchestrator or internal retrieval paths), not through
        ``gateway.execute`` -- that call would be rejected by the
        SYSTEM_OWNED_TOOLS gate in :class:`ToolAuthorizer`. This test
        therefore pulls the handler out of the gateway's registry and
        invokes it directly, proving the registration contract wires
        both retrieval tools.
        """
        service = _make_retrieval_service()
        await service.ingest([_make_record()], engagement_id="ENG-OTHER")

        registry = _build_registry()
        registry.register(
            ToolEntry(
                name=ToolName.HYBRID_SEARCH.value,
                server_name="keystone-retrieval",
                description="hybrid",
                transport_type=TransportType.IN_PROCESS,
            )
        )

        gateway = _build_gateway(registry)
        register_retrieval_handlers(gateway, service)

        assert ToolName.SEMANTIC_SEARCH.value in gateway._in_process_handlers
        assert ToolName.HYBRID_SEARCH.value in gateway._in_process_handlers

        call = ToolCall(
            agent_id="agent-B",
            tool_name=ToolName.HYBRID_SEARCH.value,
            parameters={"query": "market", "top_k": 5},
            engagement_id="ENG-1",
            client_id="CLI-1",
            assigned_tools=[ToolName.HYBRID_SEARCH.value],
        )
        handler = gateway._in_process_handlers[ToolName.HYBRID_SEARCH.value]
        payload = await handler(call)
        urls = {item["url"] for item in payload["results"]}
        assert "https://example.com/report" in urls

    @pytest.mark.asyncio
    async def test_handler_rejects_empty_query(self) -> None:
        service = _make_retrieval_service()
        handlers = build_retrieval_handlers(service)
        with pytest.raises(ValueError, match="query"):
            await handlers[ToolName.SEMANTIC_SEARCH.value](_tool_call(parameters={"query": ""}))

    @pytest.mark.asyncio
    async def test_handler_validates_top_k(self) -> None:
        service = _make_retrieval_service()
        handlers = build_retrieval_handlers(service)
        with pytest.raises(ValueError, match="top_k"):
            await handlers[ToolName.SEMANTIC_SEARCH.value](
                _tool_call(parameters={"query": "x", "top_k": 0})
            )
        with pytest.raises(ValueError, match="top_k"):
            await handlers[ToolName.SEMANTIC_SEARCH.value](
                _tool_call(parameters={"query": "x", "top_k": "abc"})
            )

    @pytest.mark.asyncio
    async def test_handler_threads_exclude_engagement(self) -> None:
        """Explicit exclude_engagement_id parameter must win over the bridge default."""
        service = _make_retrieval_service()
        await service.ingest([_make_record()], engagement_id="ENG-SELF")
        handlers = build_retrieval_handlers(service)

        payload = await handlers[ToolName.SEMANTIC_SEARCH.value](
            _tool_call(parameters={"query": "market", "exclude_engagement_id": "ENG-SELF"})
        )
        assert payload["result_count"] == 0

        # Default call (engagement_id=ENG-1) does not exclude ENG-SELF chunks.
        payload = await handlers[ToolName.SEMANTIC_SEARCH.value](
            _tool_call(parameters={"query": "market"})
        )
        assert payload["result_count"] >= 1

    @pytest.mark.asyncio
    async def test_bridge_isolates_caller_engagement_by_default(self) -> None:
        """Lane E (institutional) visible; sibling-agent chunks in the caller's engagement hidden.

        Structural inter-agent isolation: when the caller does not pass
        an explicit ``exclude_engagement_id``, the bridge injects the
        caller's own ``call.engagement_id`` so chunks tagged with that
        engagement (i.e. mid-research output from sibling agents) are
        hidden, while institutional chunks (``engagement_id=None``)
        pass through.
        """
        service = _make_retrieval_service()
        # Institutional Lane E passage (visible everywhere)
        await service.ingest_institutional(
            [
                _make_record(
                    record_id="EV-INSTITUTIONAL",
                    artifact_id="ART-INST",
                    canonical_url="https://example.com/institutional",
                    text="Institutional AV market passage with industry shipments data.",
                    title="Institutional AV Passage",
                )
            ]
        )
        # Agent-produced mid-research chunk in the caller's active engagement
        await service.ingest(
            [
                _make_record(
                    record_id="EV-SIBLING",
                    artifact_id="ART-SIB",
                    canonical_url="https://example.com/sibling-agent-note",
                    text="Sibling agent draft note about AV market shipments. Not for peers.",
                    title="Sibling Agent Note",
                )
            ],
            engagement_id="ENG-1",
        )
        handlers = build_retrieval_handlers(service)

        payload = await handlers[ToolName.SEMANTIC_SEARCH.value](
            _tool_call(
                parameters={"query": "AV market shipments"},
                engagement_id="ENG-1",
            )
        )
        urls = {item["url"] for item in payload["results"]}
        assert "https://example.com/institutional" in urls, (
            "Lane E institutional passages must remain visible to agents"
        )
        assert "https://example.com/sibling-agent-note" not in urls, (
            "Sibling-agent chunks in the caller's engagement must be hidden"
        )


class TestSearchCompletedEvent:
    @pytest.mark.asyncio
    async def test_event_emitted_on_search(self) -> None:
        from keystone.events import SearchCompleted  # noqa: TC001

        service = _make_retrieval_service()
        await service.ingest([_make_record()], engagement_id="ENG-OTHER")

        emitted: list[SearchCompleted] = []
        handlers = build_retrieval_handlers(service, event_sink=emitted.append)
        await handlers[ToolName.SEMANTIC_SEARCH.value](
            _tool_call(
                parameters={"query": "autonomous vehicle sensor market"},
                agent_id="agent-007",
                engagement_id="ENG-ACTIVE",
                client_id="CLI-ZZ",
            )
        )

        assert len(emitted) == 1
        event = emitted[0]
        assert event.tool_name == ToolName.SEMANTIC_SEARCH.value
        assert event.agent_id == "agent-007"
        assert event.engagement_id == "ENG-ACTIVE"
        assert event.client_id == "CLI-ZZ"
        assert event.query_preview.startswith("autonomous")
        assert event.result_count >= 1
        assert event.latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_no_event_when_sink_missing(self) -> None:
        service = _make_retrieval_service()
        handlers = build_retrieval_handlers(service)
        # Should simply run without error
        await handlers[ToolName.SEMANTIC_SEARCH.value](_tool_call(parameters={"query": "x"}))

    @pytest.mark.asyncio
    async def test_long_query_preview_is_truncated(self) -> None:
        from keystone.events import SearchCompleted  # noqa: TC001

        service = _make_retrieval_service()
        emitted: list[SearchCompleted] = []
        handlers = build_retrieval_handlers(service, event_sink=emitted.append)
        long_query = "a" * 500
        await handlers[ToolName.SEMANTIC_SEARCH.value](_tool_call(parameters={"query": long_query}))
        assert len(emitted) == 1
        assert len(emitted[0].query_preview) <= 120
        assert emitted[0].query_preview.endswith("\u2026")
