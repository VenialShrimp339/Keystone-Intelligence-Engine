"""Orchestrator tests for the retrieval wiring.

These exercise the per-run retrieval integration added to
:class:`Pipeline`: building the engagement-scoped RetrievalService via
the injected factory, ingesting Lane E records, registering the
gateway handlers, emitting :class:`ChunkIngested`, and surfacing
:class:`SearchCompleted` events from agent-triggered tool calls.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from keystone.citation.processor import CitationProcessorResult
from keystone.events import ChunkIngested, SearchCompleted, SpecificationGenerated
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient, ToolCall
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.tool_registry import (
    ToolEntry,
    ToolRegistry,
    TransportType,
)
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
)
from keystone.models.structuring import StructuredOutline
from keystone.pipeline.orchestrator import Pipeline
from keystone.research.agent_pool import AgentResult
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

# Reuse fixtures from the existing orchestrator tests.
from tests.unit.pipeline.test_orchestrator import (
    _make_confidence_map,
    _make_finding,
    _make_manifest,
    _make_spec,
    _mock_llm_factory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_gateway() -> MCPGateway:
    registry = ToolRegistry()
    # Register the retrieval tools so IN_PROCESS dispatch resolves.
    registry.register(
        ToolEntry(
            name=ToolName.SEMANTIC_SEARCH.value,
            server_name="keystone-retrieval",
            description="semantic",
            transport_type=TransportType.IN_PROCESS,
        )
    )
    registry.register(
        ToolEntry(
            name=ToolName.HYBRID_SEARCH.value,
            server_name="keystone-retrieval",
            description="hybrid",
            transport_type=TransportType.IN_PROCESS,
        )
    )
    rate_limiter = InMemoryRateLimiter({})
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=rate_limiter,
        audit_logger=AuditLogger(),
        client=MockMCPClient(),
    )


def _make_record(text: str = "AV sensor market grew 28% in 2024.") -> EvidencePrepRecord:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return EvidencePrepRecord(
        record_id="EV-0001",
        artifact_id="ART-001",
        canonical_url="https://example.com/report",
        content_hash=content_hash,
        source_family=SourceFamily.ARTICLE,
        title="AV Market Report",
        text=text,
        locator=Locator(section_path=["Market"], paragraph_index=0),
        coverage=Coverage(status=CoverageStatus.COMPLETE),
        parse_confidence=confidence(0.9),
        parser=ParserIdentity(name="unit-test-parser", version="1.0"),
        passage_kind=PassageKind.PARAGRAPH,
        fetched_at=datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
    )


def _make_service(engagement_context: str | None = None) -> RetrievalService:
    return RetrievalService(
        chunker=SemanticChunker(),
        embedder=InMemoryEmbeddingClient(dimension=8),
        vector_store=InMemoryVectorStore(dimension=8),
        bm25_index=InMemoryBM25Index(),
        engagement_context=engagement_context,
    )


def _make_eval_result(task_id: str = "task_001") -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=str(uuid.uuid4()),
        engagement_id="eng_test",
        client_id="c1",
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=True,
        overall_score=72.0,
        layer1_results=Layer1Result(facts_verified=5, facts_failed=0),
        layer2_results=Layer2Result(citations_checked=3, citations_verified=3, gate_passed=True),
        feedback="PASSED",
    )


async def _noop_gen(*args, **kwargs):
    return
    yield  # pragma: no cover


def _patch_stages(pipeline: Pipeline) -> None:
    spec = _make_spec()
    finding = _make_finding()
    manifest = _make_manifest()
    cm = _make_confidence_map()

    c = pipeline._build_components()

    async def l0_gen(*args, **kwargs):
        yield SpecificationGenerated(
            event_id="e0",
            engagement_id="eng_test",
            client_id="c1",
            spec_version=1,
            question_count=1,
            validation_passed=True,
        )

    c.spec_engine.generate_spec = l0_gen
    c.spec_engine.get_spec = AsyncMock(return_value=spec)
    c.agent_pool.execute_all = AsyncMock(
        return_value=[AgentResult("a1", "task_001", finding=finding, events=[])]
    )
    c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
    c.citation_processor.process = _noop_gen
    c.citation_processor.get_result = AsyncMock(
        return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding])
    )
    c.deliberation.deliberate = _noop_gen
    c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
    c.content_structurer.structure = _noop_gen
    c.content_structurer.get_outline = AsyncMock(
        return_value=StructuredOutline(
            engagement_id="eng_test",
            client_id="c1",
            engagement_type="sizing",
        )
    )
    c.content_structurer.get_task_section_text = AsyncMock(return_value="")
    c.content_structurer.get_sprint_contract = AsyncMock(return_value=None)
    pipeline._pending_components = c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRetrievalFactoryInvocation:
    @pytest.mark.asyncio
    async def test_factory_is_called_with_engagement_id(self) -> None:
        gw = _build_gateway()
        factory_calls: list[str] = []

        def factory(eid: str) -> RetrievalService:
            factory_calls.append(eid)
            return _make_service(engagement_context=eid)

        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[_make_record()],
            retrieval_service_factory=factory,
        )
        _patch_stages(pipeline)
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            await pipeline.run("Q", "c1")

        assert factory_calls == ["eng_test"]

    @pytest.mark.asyncio
    async def test_no_factory_skips_retrieval(self) -> None:
        """When no factory is supplied, no ChunkIngested events appear."""
        gw = _build_gateway()
        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[_make_record()],
        )
        _patch_stages(pipeline)
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        assert not [e for e in events if isinstance(e, ChunkIngested)]
        # Gateway should have no IN_PROCESS handler registered
        assert not gw._in_process_handlers


class TestChunkIngestedEvent:
    @pytest.mark.asyncio
    async def test_chunk_ingested_emitted_with_counts(self) -> None:
        gw = _build_gateway()

        def factory(eid: str) -> RetrievalService:
            return _make_service(engagement_context=eid)

        records = [_make_record(text=f"Passage number {i} about markets.") for i in range(3)]
        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=records,
            retrieval_service_factory=factory,
        )
        _patch_stages(pipeline)
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        ingested = [e for e in events if isinstance(e, ChunkIngested)]
        assert len(ingested) == 1
        ev = ingested[0]
        assert ev.engagement_id == "eng_test"
        assert ev.client_id == "c1"
        assert ev.artifact_count == 1  # all records share artifact_id "ART-001"
        assert ev.chunk_count >= 1
        assert ev.chunks_created >= 1
        assert ev.chunks_skipped == 0

    @pytest.mark.asyncio
    async def test_no_records_no_ingest_event(self) -> None:
        """Factory present but no evidence records -> still no ChunkIngested."""
        gw = _build_gateway()

        def factory(eid: str) -> RetrievalService:
            return _make_service(engagement_context=eid)

        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=None,
            retrieval_service_factory=factory,
        )
        _patch_stages(pipeline)
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        assert not [e for e in events if isinstance(e, ChunkIngested)]
        # But handlers ARE registered so downstream agents can still search.
        assert ToolName.SEMANTIC_SEARCH.value in gw._in_process_handlers
        assert ToolName.HYBRID_SEARCH.value in gw._in_process_handlers


class TestSearchCompletedPropagation:
    @pytest.mark.asyncio
    async def test_search_events_are_yielded(self) -> None:
        """SearchCompleted events from in-flight agent searches surface to the stream."""
        gw = _build_gateway()

        def factory(eid: str) -> RetrievalService:
            return _make_service(engagement_context=eid)

        # Simulate the system-owned retrieval path: the bridge handler
        # is invoked directly (not through gateway.execute, which would
        # be rejected by the SYSTEM_OWNED_TOOLS authorizer gate).
        async def mock_execute_all(assignments):
            # Each assignment drives one retrieval call so the test
            # asserts per-agent correlation.
            for task, _spec, agent in assignments:
                handler = gw._in_process_handlers[ToolName.SEMANTIC_SEARCH.value]
                await handler(
                    ToolCall(
                        agent_id=agent.agent_id,
                        tool_name=ToolName.SEMANTIC_SEARCH.value,
                        parameters={"query": f"market for {task.id}"},
                        engagement_id=agent.engagement_id,
                        client_id=agent.client_id,
                        assigned_tools=[ToolName.SEMANTIC_SEARCH.value],
                    )
                )
            return [
                AgentResult(
                    agent_id=agent.agent_id,
                    task_id=task.id,
                    finding=_make_finding(),
                    events=[],
                )
                for task, _spec, agent in assignments
            ]

        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[_make_record()],
            retrieval_service_factory=factory,
        )
        _patch_stages(pipeline)
        pipeline._pending_components.agent_pool.execute_all = mock_execute_all
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        search_events = [e for e in events if isinstance(e, SearchCompleted)]
        assert len(search_events) == 1
        assert search_events[0].tool_name == ToolName.SEMANTIC_SEARCH.value
        assert search_events[0].engagement_id == "eng_test"
        assert search_events[0].agent_id  # populated from the ToolCall


# ---------------------------------------------------------------------------
# Multi-run / second-invocation freshness (Fix 4 + Fix 7 coverage)
# ---------------------------------------------------------------------------


class TestMultiRunRetrievalWiring:
    """A Pipeline instance reused across runs must re-register fresh handlers
    backed by a fresh service and a fresh ``search_events`` list. Nothing
    from run N may leak into run N+1.
    """

    @pytest.mark.asyncio
    async def test_second_run_reregisters_fresh_service_and_events(self) -> None:
        gw = _build_gateway()

        services_built: list[RetrievalService] = []

        def factory(eid: str) -> RetrievalService:
            svc = _make_service(engagement_context=eid)
            services_built.append(svc)
            return svc

        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[_make_record()],
            retrieval_service_factory=factory,
        )

        handlers_per_run: list[dict] = []
        eval_result = _make_eval_result()

        async def _one_run() -> None:
            _patch_stages(pipeline)

            # Snapshot the handler objects immediately before the stream
            # drains so we can compare closures across runs.
            async def capture_execute_all(assignments):
                # Mimic an in-flight search so search_events is populated.
                handler = gw._in_process_handlers[ToolName.SEMANTIC_SEARCH.value]
                for _task, _spec, agent in assignments:
                    await handler(
                        ToolCall(
                            agent_id=agent.agent_id,
                            tool_name=ToolName.SEMANTIC_SEARCH.value,
                            parameters={"query": "anything"},
                            engagement_id=agent.engagement_id,
                            client_id=agent.client_id,
                            assigned_tools=[ToolName.SEMANTIC_SEARCH.value],
                        )
                    )
                handlers_per_run.append(dict(gw._in_process_handlers))
                return [
                    AgentResult(
                        agent_id=agent.agent_id,
                        task_id=_task.id,
                        finding=_make_finding(),
                        events=[],
                    )
                    for _task, _spec, agent in assignments
                ]

            pipeline._pending_components.agent_pool.execute_all = capture_execute_all
            with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
                inst = MagicMock()
                inst.evaluate = _noop_gen
                inst.get_result = AsyncMock(return_value=eval_result)
                MockEval.return_value = inst
                events: list = []
                async for event in pipeline.run_with_events("Q", "c1"):
                    events.append(event)
            return events

        run_one_events = await _one_run()
        run_two_events = await _one_run()

        # A fresh RetrievalService was built for each run.
        assert len(services_built) == 2
        assert services_built[0] is not services_built[1]

        # Handlers registered during run 1 are a different object from those
        # registered during run 2 (fresh closures over fresh search_events).
        run1_handler = handlers_per_run[0][ToolName.SEMANTIC_SEARCH.value]
        run2_handler = handlers_per_run[1][ToolName.SEMANTIC_SEARCH.value]
        assert run1_handler is not run2_handler

        # Each run yields exactly one SearchCompleted; run 2 must not
        # replay run 1's search or carry its event identity.
        run1_search = [e for e in run_one_events if isinstance(e, SearchCompleted)]
        run2_search = [e for e in run_two_events if isinstance(e, SearchCompleted)]
        assert len(run1_search) == 1
        assert len(run2_search) == 1
        assert run1_search[0].event_id != run2_search[0].event_id

        # Each run yields exactly one ChunkIngested (Lane E re-ingested).
        assert len([e for e in run_one_events if isinstance(e, ChunkIngested)]) == 1
        assert len([e for e in run_two_events if isinstance(e, ChunkIngested)]) == 1

    @pytest.mark.asyncio
    async def test_evidence_records_without_factory_are_silently_dropped(self) -> None:
        """Documented behavior: evidence_records present but no factory => no ingest.

        This protects against a regression that tries to ingest records
        without wiring a service. The pipeline must complete normally and
        produce no ChunkIngested / SearchCompleted events, and the
        gateway must have no in-process handlers registered.
        """
        gw = _build_gateway()
        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[_make_record(), _make_record(text="Another passage.")],
            retrieval_service_factory=None,
        )
        _patch_stages(pipeline)
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events: list = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        assert not [e for e in events if isinstance(e, ChunkIngested)]
        assert not [e for e in events if isinstance(e, SearchCompleted)]
        assert not gw._in_process_handlers

    @pytest.mark.asyncio
    async def test_lane_e_institutional_is_visible_to_agent_search(self) -> None:
        """End-to-end visibility: Lane E ingested as institutional memory
        is reachable by the bridge handler under the caller's engagement_id.

        This crosses the wire we opened in Fix 1: the orchestrator
        routes Lane E through ``ingest_institutional`` (engagement_id=
        None), and the bridge defaults ``exclude_engagement_id`` to the
        caller's engagement. An institutional chunk passes the filter,
        so a search executed with the bridge handler should return it.
        """
        gw = _build_gateway()

        def factory(eid: str) -> RetrievalService:
            return _make_service(engagement_context=eid)

        pipeline = Pipeline(
            llm_factory=_mock_llm_factory(),
            gateway=gw,
            evidence_records=[
                _make_record(
                    text=(
                        "AV sensor market institutional memory passage about "
                        "shipments and unit economics."
                    )
                ),
            ],
            retrieval_service_factory=factory,
        )
        _patch_stages(pipeline)

        payloads: list[dict] = []

        async def exercising_execute_all(assignments):
            handler = gw._in_process_handlers[ToolName.SEMANTIC_SEARCH.value]
            for _task, _spec, agent in assignments:
                payload = await handler(
                    ToolCall(
                        agent_id=agent.agent_id,
                        tool_name=ToolName.SEMANTIC_SEARCH.value,
                        parameters={"query": "AV sensor market shipments"},
                        engagement_id=agent.engagement_id,
                        client_id=agent.client_id,
                        assigned_tools=[ToolName.SEMANTIC_SEARCH.value],
                    )
                )
                payloads.append(payload)
            return [
                AgentResult(
                    agent_id=agent.agent_id,
                    task_id=_task.id,
                    finding=_make_finding(),
                    events=[],
                )
                for _task, _spec, agent in assignments
            ]

        pipeline._pending_components.agent_pool.execute_all = exercising_execute_all
        eval_result = _make_eval_result()
        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:  # noqa: N806
            inst = MagicMock()
            inst.evaluate = _noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst
            async for _ in pipeline.run_with_events("Q", "c1"):
                pass

        assert len(payloads) == 1
        urls = {item["url"] for item in payloads[0]["results"]}
        assert "https://example.com/report" in urls, (
            "Lane E institutional passage must be visible to agents via the bridge"
        )
