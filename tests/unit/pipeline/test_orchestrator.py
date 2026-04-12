"""Unit tests for the pipeline orchestrator."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from keystone.deliberation.aggregator import Aggregator
from keystone.deliberation.analyst import AnalystOutput, InputClaim, ScoredClaim
from keystone.deliberation.confidence_builder import build_confidence_map
from keystone.deliberation.gap_detector import GapReport
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.events import (
    ConfidenceMapProduced,
    EvaluationComplete,
    ManifestProduced,
    SpecificationGenerated,
)
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.models.agents import AgentDefinition, AgentRole
from keystone.models.citations import (
    Citation,
    CitationAlias,
    CitationManifest,
    ConfidenceTier,
    CorroborationPair,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap, HighConfidenceClaim
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    FindingClaim,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)
from keystone.citation.processor import CitationProcessorResult
from keystone.pipeline.markdown_renderer import MarkdownRenderer
from keystone.pipeline.orchestrator import (
    Pipeline,
    PipelineComponents,
    PipelineResult,
    _filter_confidence_map_by_passed_tasks,
    _finding_to_text,
)
from keystone.research.agent_pool import AgentResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_citation(cid: str = "CIT-001", eid: str = "eng_test", client: str = "c1") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id=eid,
        client_id=client,
        url="https://example.com/source",
        title="Test Source",
        access_date=datetime.now(UTC),
        source_type=SourceType.NEWS,
        quality_score=0.8,
    )


def _make_task(
    task_id: str = "task_001",
    eid: str = "eng_test",
    cid: str = "c1",
) -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id=eid,
        client_id=cid,
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Estimate the TAM for L4+ AV sensors",
        acceptance_criteria=["Provide top-down and bottom-up estimates", "Include 3+ sources"],
        deliverable_destination="Section 1: Market Size",
        priority=1,
        anti_confirmatory_framing="Evaluate whether the AV sensor market is as large as projected",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        end_product="TAM estimate with ranges",
    )


def _make_spec(eid: str = "eng_test", cid: str = "c1") -> EngagementSpec:
    task = _make_task(eid=eid, cid=cid)
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id=eid,
            client_id=cid,
            title="TAM for L4+ AV Sensor Market",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Investment decision for sensor startup",
            surprising_finding="Market smaller than expected",
            questions=[ResearchQuestion(question="What is the TAM?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="L4+ AV sensor TAM exceeds $10B by 2030",
        ),
        task_decomposition=TaskDecomposition(
            project="AV Sensors",
            engagement_id=eid,
            client_id=cid,
            research_md_path="/tmp/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="Market sizing requires multiple approaches",
            tasks=[task],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _make_finding(
    task_id: str = "task_001",
    agent_id: str = "agent_001",
    eid: str = "eng_test",
    cid: str = "c1",
) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=agent_id,
        engagement_id=eid,
        client_id=cid,
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="L4+ AV sensor TAM is projected at $12B by 2030",
                evidence="Multiple industry reports converge",
                citations=[_make_citation(eid=eid, client=cid)],
                confidence=0.85,
                confidence_tier=ConfidenceTier.HIGH,
            ),
        ],
        absence_report=["No data found on Chinese OEM adoption rates"],
        sources_consulted=5,
        tokens_consumed=1200,
    )


def _make_manifest(eid: str = "eng_test", cid: str = "c1") -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id=eid,
        client_id=cid,
        citations=[_make_citation(eid=eid, client=cid)],
    )


def _make_confidence_map(eid: str = "eng_test", cid: str = "c1") -> ConfidenceMap:
    return ConfidenceMap(
        engagement_id=eid,
        client_id=cid,
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="L4+ AV sensor TAM exceeds $10B by 2030",
                methodological_agreement="3/4 (Quant, Market, Historical)",
                sources=5,
                corroboration_count=3,
                robustness="Holds under +/-20% assumption variation",
                curmudgeon_challenge="Adoption pace may slow due to regulation",
            ),
        ],
        gaps_identified=["Chinese OEM adoption data"],
    )


def _make_two_task_spec(eid: str = "eng_test", cid: str = "c1") -> EngagementSpec:
    task_1 = _make_task(task_id="task_001", eid=eid, cid=cid)
    task_2 = _make_task(task_id="task_002", eid=eid, cid=cid).model_copy(
        update={
            "description": "Map the competitive landscape of L4+ AV sensor vendors",
            "deliverable_destination": "Section 2: Competitive Landscape",
        }
    )
    spec = _make_spec(eid=eid, cid=cid)
    return spec.model_copy(
        update={
            "task_decomposition": spec.task_decomposition.model_copy(
                update={"tasks": [task_1, task_2]}
            )
        }
    )


def _make_three_task_spec(eid: str = "eng_test", cid: str = "c1") -> EngagementSpec:
    task_1 = _make_task(task_id="task_001", eid=eid, cid=cid)
    task_2 = _make_task(task_id="task_002", eid=eid, cid=cid).model_copy(
        update={
            "description": "Map the competitive landscape of L4+ AV sensor vendors",
            "deliverable_destination": "Section 2: Competitive Landscape",
        }
    )
    task_3 = _make_task(task_id="task_003", eid=eid, cid=cid).model_copy(
        update={
            "description": "Stress test downside adoption scenarios for L4+ AV sensors",
            "deliverable_destination": "Section 3: Downside Scenarios",
        }
    )
    spec = _make_spec(eid=eid, cid=cid)
    return spec.model_copy(
        update={
            "task_decomposition": spec.task_decomposition.model_copy(
                update={"tasks": [task_1, task_2, task_3]}
            )
        }
    )


def _make_task_scoped_confidence_map(
    claims: list[tuple[str, str, str, list[str]]],
    eid: str = "eng_test",
    cid: str = "c1",
) -> ConfidenceMap:
    return ConfidenceMap(
        engagement_id=eid,
        client_id=cid,
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim=claim_text,
                methodological_agreement="3/4 (ach, quantitative, adversarial)",
                sources=3,
                corroboration_count=2,
                robustness="Stable across analyst methods",
                curmudgeon_challenge="Needs more downside testing",
                aggregated_claim_id=agg_id,
                task_ids=task_ids,
            )
            for claim_text, agg_id, _, task_ids in claims
        ],
        provenance_index={agg_id: list(task_ids) for _, agg_id, _, task_ids in claims},
    )


def _make_eval_result(
    task_id: str = "task_001",
    eid: str = "eng_test",
    cid: str = "c1",
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=str(uuid.uuid4()),
        engagement_id=eid,
        client_id=cid,
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=True,
        overall_score=72.0,
        layer1_results=Layer1Result(facts_verified=5, facts_failed=0),
        layer2_results=Layer2Result(
            citations_checked=3, citations_verified=3, gate_passed=True
        ),
        feedback="PASSED with score 72.0/100.",
    )


def _make_gateway() -> MCPGateway:
    from keystone.gateway.audit_log import AuditLogger
    from keystone.gateway.auth import ToolAuthorizer
    from keystone.gateway.rate_limiter import InMemoryRateLimiter
    from keystone.gateway.tool_registry import ToolRegistry

    registry = ToolRegistry()
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=MockMCPClient(),
    )


def _mock_llm_factory() -> MagicMock:
    """Create a mock llm_factory that returns an async callable for any tier."""
    mock_llm = AsyncMock(return_value='{"result": "mock"}')
    factory = MagicMock(return_value=mock_llm)
    return factory


# ---------------------------------------------------------------------------
# Tests: Pipeline instantiation
# ---------------------------------------------------------------------------

class TestPipelineInstantiation:
    def test_creates_with_mock_factory(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)
        c = pipeline._build_components()

        assert c.spec_engine is not None
        assert c.agent_pool is not None
        assert c.citation_processor is not None
        assert c.deliberation is not None
        assert c.renderer is not None

    def test_factory_called_for_each_tier(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)
        pipeline._build_components()

        # Should be called at least for FLAGSHIP and STANDARD
        tier_calls = [call.args[0] for call in factory.call_args_list]
        assert ModelTier.FLAGSHIP in tier_calls
        assert ModelTier.STANDARD in tier_calls

    def test_no_db_session_factory_by_default(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)
        assert pipeline._db_session_factory is None


# ---------------------------------------------------------------------------
# Tests: Pipeline stages called in order
# ---------------------------------------------------------------------------

class TestPipelineStageOrder:
    @pytest.mark.asyncio
    async def test_stages_called_in_order(self) -> None:
        """Patch all internal components and verify call sequence."""
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result()

        call_order: list[str] = []

        # Build components, patch them, inject back
        c = pipeline._build_components()

        # Patch L0
        async def mock_generate_spec(*args, **kwargs):
            call_order.append("L0")
            return
            yield  # make it an async generator

        c.spec_engine.generate_spec = mock_generate_spec
        c.spec_engine.get_spec = AsyncMock(return_value=spec)

        # Patch L1
        async def mock_execute_all(assignments):
            call_order.append("L1")
            return [
                AgentResult(
                    agent_id="agent_001",
                    task_id="task_001",
                    finding=finding,
                    events=[],
                )
            ]

        c.agent_pool.execute_all = mock_execute_all
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])

        # Patch CitProc
        async def mock_citproc_process(*args, **kwargs):
            call_order.append("CitProc")
            return
            yield

        c.citation_processor.process = mock_citproc_process
        c.citation_processor.get_result = AsyncMock(return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding]))

        # Patch L1.5
        async def mock_deliberate(*args, **kwargs):
            call_order.append("L1.5")
            return
            yield

        c.deliberation.deliberate = mock_deliberate
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)

        pipeline._pending_components = c

        # Patch L4 -- evaluator is created per-task in the loop, so patch the class
        with patch(
            "keystone.pipeline.orchestrator.Evaluator"
        ) as MockEvaluator:
            mock_eval_instance = MagicMock()

            async def mock_evaluate(*args, **kwargs):
                call_order.append("L4")
                return
                yield

            mock_eval_instance.evaluate = mock_evaluate
            mock_eval_instance.get_result = AsyncMock(return_value=eval_result)
            MockEvaluator.return_value = mock_eval_instance

            result = await pipeline.run("Test question", "c1")

        assert call_order == ["L0", "L1", "CitProc", "L1.5", "L4"]

    @pytest.mark.asyncio
    async def test_pipeline_result_has_all_fields(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result()

        # Patch all stages
        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding]))
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            inst.evaluate = noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            result = await pipeline.run("Test question", "c1")

        assert isinstance(result, PipelineResult)
        assert result.engagement_id == "eng_test"
        assert result.client_id == "c1"
        assert result.spec is spec
        assert result.findings == [finding]
        assert result.manifest is manifest
        assert result.confidence_map is cm
        assert len(result.evaluation_results) == 1
        assert len(result.markdown_output) > 0
        assert result.total_tokens == 1200
        assert result.total_events == 0  # no events emitted from mock generators


# ---------------------------------------------------------------------------
# Tests: Event collection
# ---------------------------------------------------------------------------

class TestEventCollection:
    @pytest.mark.asyncio
    async def test_events_collected_from_stages(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result()

        # L0 yields one event
        spec_event = SpecificationGenerated(
            event_id="e1",
            engagement_id="eng_test",
            client_id="c1",
            spec_version=1,
            question_count=1,
            validation_passed=True,
        )

        async def l0_gen(*a, **kw):
            yield spec_event

        # L1 returns results with events
        manifest_event = ManifestProduced(
            event_id="e2",
            engagement_id="eng_test",
            client_id="c1",
            manifest_id="MAN-001",
            total_citations=1,
            dead_urls=0,
            fabrication_flags=0,
            corroboration_pairs=0,
        )

        async def citproc_gen(*a, **kw):
            yield manifest_event

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = l0_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = citproc_gen
        c.citation_processor.get_result = AsyncMock(return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding]))
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            inst.evaluate = noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            events = []
            async for event in pipeline.run_with_events("Q", "c1"):
                events.append(event)

        assert len(events) == 2
        assert events[0] is spec_event
        assert events[1] is manifest_event


# ---------------------------------------------------------------------------
# Tests: HITL gates
# ---------------------------------------------------------------------------

class TestHITLGates:
    def test_hitl_skipped_when_no_db(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw, db_session_factory=None)
        c = pipeline._build_components()

        # Both SpecEngine and Deliberation should have None for db_session_factory
        assert c.spec_engine._db_session_factory is None
        assert c.deliberation._db_session_factory is None

    def test_hitl_wired_when_db_provided(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        mock_db = MagicMock()
        pipeline = Pipeline(llm_factory=factory, gateway=gw, db_session_factory=mock_db)
        c = pipeline._build_components()

        assert c.spec_engine._db_session_factory is mock_db
        assert c.deliberation._db_session_factory is mock_db


# ---------------------------------------------------------------------------
# Tests: Partial pipeline (no findings)
# ---------------------------------------------------------------------------

class TestPartialPipeline:
    @pytest.mark.asyncio
    async def test_empty_findings_halt_under_standard_coverage(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        empty_manifest = CitationManifest(
            manifest_id="MAN-empty",
            engagement_id="eng_test",
            client_id="c1",
        )
        cm = ConfidenceMap(engagement_id="eng_test", client_id="c1")
        eval_result = _make_eval_result()

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        # All agents fail -> no findings
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", error=RuntimeError("fail"))]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(return_value=CitationProcessorResult(manifest=empty_manifest, canonicalized_findings=[]))
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            inst.evaluate = noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            with pytest.raises(
                RuntimeError,
                match="STANDARD profile requires all PRIMARY tasks to pass",
            ):
                await pipeline.run("Test question", "c1")


class TestRendererGating:
    @pytest.mark.asyncio
    async def test_renderer_drops_claims_from_failed_tasks(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_three_task_spec()
        finding_pass = _make_finding(task_id="task_001").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Passed task claim should render",
                        evidence="Primary branch evidence",
                        citations=[_make_citation(cid="CAN-001")],
                        citation_ids=["CAN-001"],
                        confidence=0.85,
                        confidence_tier=ConfidenceTier.HIGH,
                    )
                ]
            }
        )
        finding_fail = _make_finding(task_id="task_002", agent_id="agent_002").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Competitive landscape is consolidating rapidly",
                        evidence="Vendor count and funding patterns",
                        citations=[_make_citation(cid="CAN-002")],
                        citation_ids=["CAN-002"],
                        confidence=0.7,
                        confidence_tier=ConfidenceTier.MODERATE,
                    )
                ]
            }
        )
        finding_pass_support = _make_finding(
            task_id="task_003",
            agent_id="agent_003",
        ).model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Downside scenario claim should render",
                        evidence="Scenario stress-test evidence",
                        citations=[_make_citation(cid="CAN-003")],
                        citation_ids=["CAN-003"],
                        confidence=0.81,
                        confidence_tier=ConfidenceTier.HIGH,
                    )
                ]
            }
        )
        manifest = CitationManifest(
            manifest_id="MAN-002",
            engagement_id="eng_test",
            client_id="c1",
            citations=[
                _make_citation(cid="CAN-001"),
                _make_citation(cid="CAN-002"),
                _make_citation(cid="CAN-003"),
            ],
            dead_urls=["CAN-002"],
            fabrication_flags=["CAN-002"],
            corroboration_pairs=[
                CorroborationPair(
                    citation_a="CAN-001",
                    citation_b="CAN-002",
                    overlap_score=1.0,
                )
            ],
            aliases=[
                CitationAlias(
                    source_instance_id="CIT-pass-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_001",
                    agent_id="agent_001",
                ),
                CitationAlias(
                    source_instance_id="CIT-fail-001",
                    canonical_citation_id="CAN-002",
                    engagement_id="eng_test",
                    task_id="task_002",
                    agent_id="agent_002",
                ),
                CitationAlias(
                    source_instance_id="CIT-pass-003",
                    canonical_citation_id="CAN-003",
                    engagement_id="eng_test",
                    task_id="task_003",
                    agent_id="agent_003",
                ),
            ],
        )
        confidence_map = _make_task_scoped_confidence_map(
            [
                ("Passed claim", "AGG-pass", "task_001", ["task_001"]),
                ("Failed claim", "AGG-fail", "task_002", ["task_002"]),
                ("Passed supporting claim", "AGG-pass-003", "task_003", ["task_003"]),
            ]
        )

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[
                AgentResult("a1", "task_001", finding=finding_pass),
                AgentResult("a2", "task_002", finding=finding_fail),
                AgentResult("a3", "task_003", finding=finding_pass_support),
            ]
        )
        c.agent_pool.get_successful_findings = MagicMock(
            return_value=[finding_pass, finding_fail, finding_pass_support]
        )
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(
                manifest=manifest,
                canonicalized_findings=[
                    finding_pass,
                    finding_fail,
                    finding_pass_support,
                ],
            )
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=confidence_map)
        c.renderer.render = MagicMock(return_value="filtered markdown")
        pipeline._pending_components = c

        pass_result = _make_eval_result(task_id="task_001")
        fail_result = _make_eval_result(task_id="task_002").model_copy(
            update={"passed": False, "overall_score": 41.0}
        )
        pass_support_result = _make_eval_result(task_id="task_003")

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            eval_instances = []
            for result in [pass_result, fail_result, pass_support_result]:
                inst = MagicMock()
                inst.evaluate = noop_gen
                inst.get_result = AsyncMock(return_value=result)
                eval_instances.append(inst)
            MockEval.side_effect = eval_instances

            result = await pipeline.run("Test question", "c1")

        rendered_findings = c.renderer.render.call_args.args[1]
        rendered_confidence_map = c.renderer.render.call_args.args[2]
        rendered_evaluation_results = c.renderer.render.call_args.args[3]
        rendered_manifest = c.renderer.render.call_args.args[4]

        assert [f.task_id for f in rendered_findings] == ["task_001", "task_003"]
        assert [claim.claim for claim in rendered_confidence_map.high_confidence_above_80pct] == [
            "Passed claim",
            "Passed supporting claim",
        ]
        assert [result.task_id for result in rendered_evaluation_results] == [
            "task_001",
            "task_003",
        ]
        assert rendered_confidence_map.provenance_index == {
            "AGG-pass": ["task_001"],
            "AGG-pass-003": ["task_003"],
        }
        assert [citation.citation_id for citation in rendered_manifest.citations] == [
            "CAN-001",
            "CAN-003",
        ]
        assert rendered_manifest.dead_urls == []
        assert rendered_manifest.fabrication_flags == []
        assert rendered_manifest.corroboration_pairs == []
        assert [
            (alias.task_id, alias.canonical_citation_id)
            for alias in rendered_manifest.aliases
        ] == [
            ("task_001", "CAN-001"),
            ("task_003", "CAN-003"),
        ]
        assert len(result.findings) == 3

    @pytest.mark.asyncio
    async def test_renderer_drops_claims_from_unevaluated_tasks(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw, max_eval_tasks=2)

        spec = _make_three_task_spec()
        finding_evald_1 = _make_finding(task_id="task_001").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Evaluated task claim should render",
                        evidence="Primary branch evidence",
                        citations=[_make_citation(cid="CAN-001")],
                        citation_ids=["CAN-001"],
                        confidence=0.85,
                        confidence_tier=ConfidenceTier.HIGH,
                    )
                ]
            }
        )
        finding_evald_2 = _make_finding(task_id="task_002", agent_id="agent_002").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Second evaluated task claim should render",
                        evidence="Secondary branch evidence",
                        citations=[_make_citation(cid="CAN-002")],
                        citation_ids=["CAN-002"],
                        confidence=0.78,
                        confidence_tier=ConfidenceTier.MODERATE,
                    )
                ]
            }
        )
        finding_unevald = _make_finding(task_id="task_003", agent_id="agent_003").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Unevaluated task claim should not render",
                        evidence="Secondary branch evidence",
                        citations=[_make_citation(cid="CAN-003")],
                        citation_ids=["CAN-003"],
                        confidence=0.72,
                        confidence_tier=ConfidenceTier.MODERATE,
                    )
                ]
            }
        )
        manifest = CitationManifest(
            manifest_id="MAN-003",
            engagement_id="eng_test",
            client_id="c1",
            citations=[
                _make_citation(cid="CAN-001"),
                _make_citation(cid="CAN-002"),
                _make_citation(cid="CAN-003"),
            ],
            dead_urls=["CAN-003"],
            aliases=[
                CitationAlias(
                    source_instance_id="CIT-pass-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_001",
                    agent_id="agent_001",
                ),
                CitationAlias(
                    source_instance_id="CIT-pass-002",
                    canonical_citation_id="CAN-002",
                    engagement_id="eng_test",
                    task_id="task_002",
                    agent_id="agent_002",
                ),
                CitationAlias(
                    source_instance_id="CIT-skip-001",
                    canonical_citation_id="CAN-003",
                    engagement_id="eng_test",
                    task_id="task_003",
                    agent_id="agent_003",
                ),
            ],
        )
        confidence_map = _make_task_scoped_confidence_map(
            [
                ("Evaluated claim", "AGG-pass", "task_001", ["task_001"]),
                ("Second evaluated claim", "AGG-pass-002", "task_002", ["task_002"]),
                ("Unevaluated claim", "AGG-skip", "task_003", ["task_003"]),
            ]
        )

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[
                AgentResult("a1", "task_001", finding=finding_evald_1),
                AgentResult("a2", "task_002", finding=finding_evald_2),
                AgentResult("a3", "task_003", finding=finding_unevald),
            ]
        )
        c.agent_pool.get_successful_findings = MagicMock(
            return_value=[finding_evald_1, finding_evald_2, finding_unevald]
        )
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(
                manifest=manifest,
                canonicalized_findings=[
                    finding_evald_1,
                    finding_evald_2,
                    finding_unevald,
                ],
            )
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=confidence_map)
        c.renderer.render = MagicMock(return_value="filtered markdown")
        pipeline._pending_components = c

        pass_result = _make_eval_result(task_id="task_001")
        pass_result_2 = _make_eval_result(task_id="task_002")

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            eval_instances = []
            for result in [pass_result, pass_result_2]:
                inst = MagicMock()
                inst.evaluate = noop_gen
                inst.get_result = AsyncMock(return_value=result)
                eval_instances.append(inst)
            MockEval.side_effect = eval_instances

            result = await pipeline.run("Test question", "c1")

        rendered_findings = c.renderer.render.call_args.args[1]
        rendered_confidence_map = c.renderer.render.call_args.args[2]
        rendered_evaluation_results = c.renderer.render.call_args.args[3]
        rendered_manifest = c.renderer.render.call_args.args[4]

        assert [f.task_id for f in rendered_findings] == ["task_001", "task_002"]
        assert [claim.claim for claim in rendered_confidence_map.high_confidence_above_80pct] == [
            "Evaluated claim",
            "Second evaluated claim",
        ]
        assert [result.task_id for result in rendered_evaluation_results] == [
            "task_001",
            "task_002",
        ]
        assert rendered_confidence_map.provenance_index == {
            "AGG-pass": ["task_001"],
            "AGG-pass-002": ["task_002"],
        }
        assert [citation.citation_id for citation in rendered_manifest.citations] == [
            "CAN-001",
            "CAN-002",
        ]
        assert rendered_manifest.dead_urls == []
        assert [alias.canonical_citation_id for alias in rendered_manifest.aliases] == [
            "CAN-001",
            "CAN-002",
        ]
        assert len(result.evaluation_results) == 2

    @pytest.mark.asyncio
    async def test_renderer_drops_failed_task_feedback_and_shared_alias_rows(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_three_task_spec()
        finding_pass = _make_finding(task_id="task_001").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Passed shared-source claim should render",
                        evidence="Primary branch evidence",
                        citations=[_make_citation(cid="CAN-001")],
                        citation_ids=["CAN-001"],
                        confidence=0.85,
                        confidence_tier=ConfidenceTier.HIGH,
                    )
                ]
            }
        )
        finding_fail = _make_finding(task_id="task_002", agent_id="agent_002").model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Failed shared-source claim should not render",
                        evidence="Secondary branch evidence",
                        citations=[_make_citation(cid="CAN-001")],
                        citation_ids=["CAN-001"],
                        confidence=0.7,
                        confidence_tier=ConfidenceTier.MODERATE,
                    )
                ]
            }
        )
        finding_pass_support = _make_finding(
            task_id="task_003",
            agent_id="agent_003",
        ).model_copy(
            update={
                "claims": [
                    FindingClaim(
                        text="Second passed claim should render",
                        evidence="Independent branch evidence",
                        citations=[_make_citation(cid="CAN-003")],
                        citation_ids=["CAN-003"],
                        confidence=0.84,
                        confidence_tier=ConfidenceTier.HIGH,
                    )
                ]
            }
        )
        manifest = CitationManifest(
            manifest_id="MAN-shared",
            engagement_id="eng_test",
            client_id="c1",
            citations=[
                _make_citation(cid="CAN-001"),
                _make_citation(cid="CAN-003"),
            ],
            aliases=[
                CitationAlias(
                    source_instance_id="CIT-pass-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_001",
                    agent_id="agent_001",
                ),
                CitationAlias(
                    source_instance_id="CIT-fail-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_002",
                    agent_id="agent_002",
                ),
                CitationAlias(
                    source_instance_id="CIT-pass-003",
                    canonical_citation_id="CAN-003",
                    engagement_id="eng_test",
                    task_id="task_003",
                    agent_id="agent_003",
                ),
            ],
        )
        confidence_map = _make_task_scoped_confidence_map(
            [
                ("Passed claim", "AGG-pass", "task_001", ["task_001"]),
                ("Failed claim", "AGG-fail", "task_002", ["task_002"]),
                ("Second passed claim", "AGG-pass-003", "task_003", ["task_003"]),
            ]
        )

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[
                AgentResult("a1", "task_001", finding=finding_pass),
                AgentResult("a2", "task_002", finding=finding_fail),
                AgentResult("a3", "task_003", finding=finding_pass_support),
            ]
        )
        c.agent_pool.get_successful_findings = MagicMock(
            return_value=[finding_pass, finding_fail, finding_pass_support]
        )
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(
                manifest=manifest,
                canonicalized_findings=[
                    finding_pass,
                    finding_fail,
                    finding_pass_support,
                ],
            )
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=confidence_map)
        c.renderer.render = MagicMock(return_value="filtered markdown")
        pipeline._pending_components = c

        pass_result = _make_eval_result(task_id="task_001")
        fail_result = _make_eval_result(task_id="task_002").model_copy(
            update={
                "passed": False,
                "overall_score": 41.0,
                "feedback": "REJECTED: fabricated citation(s) detected (CAN-FAIL).",
            }
        )
        pass_support_result = _make_eval_result(task_id="task_003")

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            eval_instances = []
            for result in [pass_result, fail_result, pass_support_result]:
                inst = MagicMock()
                inst.evaluate = noop_gen
                inst.get_result = AsyncMock(return_value=result)
                eval_instances.append(inst)
            MockEval.side_effect = eval_instances

            await pipeline.run("Test question", "c1")

        rendered_evaluation_results = c.renderer.render.call_args.args[3]
        rendered_manifest = c.renderer.render.call_args.args[4]

        assert [result.task_id for result in rendered_evaluation_results] == [
            "task_001",
            "task_003",
        ]
        assert all("CAN-FAIL" not in result.feedback for result in rendered_evaluation_results)
        assert [citation.citation_id for citation in rendered_manifest.citations] == [
            "CAN-001",
            "CAN-003",
        ]
        assert rendered_manifest.citations[0].found_by_agents == ["agent_001"]
        assert rendered_manifest.citations[1].found_by_agents == ["agent_003"]
        assert [
            (alias.source_instance_id, alias.task_id, alias.canonical_citation_id)
            for alias in rendered_manifest.aliases
        ] == [
            ("CIT-pass-001", "task_001", "CAN-001"),
            ("CIT-pass-003", "task_003", "CAN-003"),
        ]


# ---------------------------------------------------------------------------
# Tests: Helper functions
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_finding_to_text(self) -> None:
        finding = _make_finding().model_copy(
            update={
                "claims": [
                    _make_finding().claims[0].model_copy(
                        update={"citation_ids": ["CAN-001"]}
                    )
                ]
            }
        )
        text = _finding_to_text(finding)

        assert "task_001" in text
        assert "agent_001" in text
        assert "$12B" in text
        assert "CAN-001" in text
        assert "Citations: CIT-001" not in text
        assert "Chinese OEM" in text

class TestBuildAssignments:
    def test_assignments_created_for_each_task(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        c = pipeline._build_components()
        assignments = pipeline._build_assignments(spec, c.template_registry)

        assert len(assignments) == 1
        task, returned_spec, agent_instance = assignments[0]
        assert task.id == "task_001"
        assert returned_spec is spec
        assert agent_instance.engagement_id == "eng_test"
        assert agent_instance.client_id == "c1"
        assert "task_001" in agent_instance.task_ids
        assert agent_instance.definition.role == AgentRole.RESEARCH


class TestConfidenceMapFiltering:
    @pytest.mark.asyncio
    async def test_shared_canonical_failed_claim_does_not_survive_filtering(self) -> None:
        manifest = CitationManifest(
            manifest_id="MAN-shared",
            engagement_id="eng_test",
            client_id="c1",
            citations=[_make_citation(cid="CAN-001")],
            aliases=[
                CitationAlias(
                    source_instance_id="CIT-pass-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_pass",
                    agent_id="agent_pass",
                ),
                CitationAlias(
                    source_instance_id="CIT-fail-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="eng_test",
                    task_id="task_fail",
                    agent_id="agent_fail",
                ),
            ],
        )
        claims = [
            InputClaim(
                index=0,
                task_id="task_pass",
                agent_id="agent_pass",
                text="Passed claim",
                evidence="Shared source support",
                citation_ids=["CIT-pass-001"],
                original_confidence=0.85,
            ),
            InputClaim(
                index=1,
                task_id="task_fail",
                agent_id="agent_fail",
                text="Failed claim",
                evidence="Same shared source support",
                citation_ids=["CIT-fail-001"],
                original_confidence=0.8,
            ),
        ]
        outputs = [
            AnalystOutput(
                analyst_id="analyst-ach",
                analyst_type="ach",
                scored_claims=[
                    ScoredClaim(
                        index=0,
                        claim_text="Passed claim",
                        analyst_confidence=0.88,
                        source_count=1,
                        reasoning="Supported",
                    ),
                    ScoredClaim(
                        index=1,
                        claim_text="Failed claim",
                        analyst_confidence=0.81,
                        source_count=1,
                        reasoning="Supported",
                    ),
                ],
            )
        ]

        async def judge(prompt: str) -> str:
            return '{"contradictions": []}'

        aggregated = await Aggregator(judge_llm=judge).aggregate(
            outputs,
            claims,
            manifest=manifest,
        )
        confidence_map = build_confidence_map(
            aggregated,
            [],
            GapReport(),
            "eng_test",
            "c1",
        )

        filtered = _filter_confidence_map_by_passed_tasks(
            confidence_map,
            {"task_pass"},
        )

        assert [claim.claim for claim in filtered.high_confidence_above_80pct] == [
            "Passed claim"
        ]
        assert all(
            claim.claim != "Failed claim"
            for claim in filtered.high_confidence_above_80pct
        )
        assert filtered.high_confidence_above_80pct[0].corroboration_count == 1
        assert filtered.provenance_index == {
            filtered.high_confidence_above_80pct[0].aggregated_claim_id: ["task_pass"]
        }

        output = MarkdownRenderer().render(
            _make_spec(),
            [_make_finding(task_id="task_pass", agent_id="agent_pass")],
            filtered,
            [_make_eval_result(task_id="task_pass")],
            manifest,
        )
        assert "Corroboration: 1" in output
        assert "Corroboration: 2" not in output

    def test_failed_task_gap_text_does_not_render(self) -> None:
        confidence_map = ConfidenceMap(
            engagement_id="eng_test",
            client_id="c1",
            high_confidence_above_80pct=[
                HighConfidenceClaim(
                    claim="Passed claim",
                    methodological_agreement="1/1 (ach)",
                    sources=1,
                    corroboration_count=1,
                    robustness="Stable",
                    curmudgeon_challenge="None",
                    aggregated_claim_id="AGG-pass",
                    task_ids=["task_pass"],
                )
            ],
            gaps_identified=["Passed task gap", "Failed task gap"],
            gap_provenance={
                "Passed task gap": ["task_pass"],
                "Failed task gap": ["task_fail"],
            },
            provenance_index={"AGG-pass": ["task_pass"]},
        )

        filtered = _filter_confidence_map_by_passed_tasks(
            confidence_map,
            {"task_pass"},
        )
        output = MarkdownRenderer().render(
            _make_spec(),
            [_make_finding(task_id="task_pass")],
            filtered,
            [_make_eval_result(task_id="task_pass")],
            _make_manifest(),
        )

        assert "Passed task gap" in output
        assert "Failed task gap" not in output


class TestWave2BWiring:
    @pytest.mark.asyncio
    async def test_orchestrator_propagates_pipeline_profile_to_deliberation(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        base_spec = _make_spec()
        spec = base_spec.model_copy(
            update={
                "research_spec": base_spec.research_spec.model_copy(
                    update={
                        "recommended_pipeline_profile": PipelineProfile.LIGHT,
                        "effective_pipeline_profile": PipelineProfile.LIGHT,
                    }
                )
            }
        )
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result().model_copy(
            update={"intensity": EvaluationIntensity.LIGHT_TOUCH}
        )
        seen: dict[str, PipelineProfile] = {}

        async def noop_gen(*a, **kw):
            return
            yield

        async def deliberate_with_profile(*a, **kw):
            seen["profile"] = c.deliberation._effective_pipeline_profile
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(
                manifest=manifest,
                canonicalized_findings=[finding],
            )
        )
        c.deliberation.deliberate = deliberate_with_profile
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        c.sprint_contract_generator.generate = AsyncMock(
            return_value=SprintContract(
                section_id="generated_task_001",
                engagement_id="eng_test",
                client_id="c1",
                task_id="task_001",
                section_title="Generated Section",
                acceptance_criteria=["Generated criterion"],
            )
        )
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            inst.evaluate = noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            await pipeline.run("Test question", "c1")

        assert seen["profile"] == PipelineProfile.LIGHT

    @pytest.mark.asyncio
    async def test_orchestrator_uses_sprint_contract_generator(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        spec = _make_spec()
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result()
        generated_contract = SprintContract(
            section_id="generated_task_001",
            engagement_id="eng_test",
            client_id="c1",
            task_id="task_001",
            section_title="Generated Section",
            acceptance_criteria=["Generated criterion"],
        )

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding])
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        c.sprint_contract_generator.generate = AsyncMock(return_value=generated_contract)
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            
            async def noop_gen_eval(*a, **kw):
                return
                yield

            inst.evaluate = MagicMock(side_effect=noop_gen_eval)
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            await pipeline.run("Test question", "c1")

        c.sprint_contract_generator.generate.assert_awaited_once_with(
            spec.task_decomposition.tasks[0], spec
        )
        assert inst.evaluate.call_args.args[1] is generated_contract

    @pytest.mark.asyncio
    async def test_orchestrator_passes_profile_to_evaluator(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw)

        base_spec = _make_spec()
        spec = base_spec.model_copy(
            update={
                "research_spec": base_spec.research_spec.model_copy(
                    update={
                        "engagement_type": EngagementType.STRATEGIC,
                        "recommended_pipeline_profile": PipelineProfile.DEEP,
                        "effective_pipeline_profile": PipelineProfile.DEEP,
                    }
                )
            }
        )
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()
        eval_result = _make_eval_result()

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding])
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        c.sprint_contract_generator.generate = AsyncMock(return_value=SprintContract(
            section_id="generated_task_001",
            engagement_id="eng_test",
            client_id="c1",
            task_id="task_001",
            section_title="Generated Section",
            acceptance_criteria=["Generated criterion"],
        ))
        pipeline._pending_components = c

        with patch("keystone.pipeline.orchestrator.Evaluator") as MockEval:
            inst = MagicMock()
            inst.evaluate = noop_gen
            inst.get_result = AsyncMock(return_value=eval_result)
            MockEval.return_value = inst

            await pipeline.run("Test question", "c1")

        assert MockEval.call_args.kwargs["profile"] == EvaluationProfile.STRATEGIC
        assert MockEval.call_args.kwargs["intensity"] == EvaluationIntensity.DEEP

    @pytest.mark.asyncio
    async def test_light_coverage_halts_on_unevaluated_rendered(self) -> None:
        factory = _mock_llm_factory()
        gw = _make_gateway()
        pipeline = Pipeline(llm_factory=factory, gateway=gw, max_eval_tasks=0)

        base_spec = _make_spec()
        spec = base_spec.model_copy(
            update={
                "research_spec": base_spec.research_spec.model_copy(
                    update={
                        "recommended_pipeline_profile": PipelineProfile.LIGHT,
                        "effective_pipeline_profile": PipelineProfile.LIGHT,
                    }
                )
            }
        )
        finding = _make_finding()
        manifest = _make_manifest()
        cm = _make_confidence_map()

        async def noop_gen(*a, **kw):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("a1", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop_gen
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=[finding])
        )
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        pipeline._pending_components = c

        with pytest.raises(RuntimeError, match="LIGHT profile requires every renderable task"):
            await pipeline.run("Test question", "c1")
