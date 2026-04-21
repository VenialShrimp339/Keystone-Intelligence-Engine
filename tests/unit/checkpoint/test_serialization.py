"""Unit tests for checkpoint serialization round-trips."""

from __future__ import annotations

from datetime import UTC, datetime

from keystone.checkpoint.serialization import (
    deserialize_events_by_agent,
    deserialize_post_deliberation,
    deserialize_post_evaluation,
    deserialize_post_l1_citproc,
    deserialize_post_spec,
    deserialize_post_structuring,
    serialize_events_by_agent,
    serialize_post_deliberation,
    serialize_post_evaluation,
    serialize_post_l1_citproc,
    serialize_post_spec,
    serialize_post_structuring,
)
from keystone.events import ResearchStarted, SourceFound
from keystone.governance.models import GovernanceState
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap, HighConfidenceClaim
from keystone.models.evaluation import (
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    EvaluationProfileName,
    FindingClaim,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
    ValidationReport,
)
from keystone.models.structuring import StructuredOutline
from keystone.models.tasks import (
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)

# -----------------------------------------------------------------------
# Test data factories
# -----------------------------------------------------------------------


def _task(task_id: str = "task_001") -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id="eng_test",
        client_id="c1",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Estimate the TAM",
        acceptance_criteria=["Provide estimates"],
        deliverable_destination="Section 1",
        priority=1,
        anti_confirmatory_framing="Evaluate assumptions",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        end_product="TAM estimate",
    )


def _spec() -> EngagementSpec:
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id="eng_test",
            client_id="c1",
            title="Test",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Test",
            surprising_finding="Nothing",
            questions=[ResearchQuestion(question="What?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="None",
            effective_evaluation_profile=EvaluationProfileName.ESTIMATIVE,
        ),
        task_decomposition=TaskDecomposition(
            project="Test",
            engagement_id="eng_test",
            client_id="c1",
            research_md_path="/tmp/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="Test",
            tasks=[_task()],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _governance() -> GovernanceState:
    return GovernanceState(profile=PipelineProfile.STANDARD)


def _finding() -> StructuredFinding:
    return StructuredFinding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_test",
        client_id="c1",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="TAM is $12B",
                evidence="Reports converge",
                citations=[
                    Citation(
                        citation_id="CIT-001",
                        engagement_id="eng_test",
                        client_id="c1",
                        url="https://example.com",
                        title="Source",
                        access_date=datetime.now(UTC),
                        source_type=SourceType.NEWS,
                        quality_score=0.8,
                    )
                ],
                confidence=0.85,
                confidence_tier=ConfidenceTier.HIGH,
            )
        ],
        absence_report=["No data on Chinese OEM adoption rates"],
        sources_consulted=5,
        tokens_consumed=1200,
    )


def _manifest() -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="eng_test",
        client_id="c1",
        citations=[
            Citation(
                citation_id="CAN-001",
                engagement_id="eng_test",
                client_id="c1",
                url="https://example.com",
                title="Source",
                access_date=datetime.now(UTC),
                source_type=SourceType.NEWS,
                quality_score=0.8,
            )
        ],
    )


def _confidence_map() -> ConfidenceMap:
    return ConfidenceMap(
        engagement_id="eng_test",
        client_id="c1",
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="TAM exceeds $10B",
                methodological_agreement="3/4",
                sources=5,
                corroboration_count=3,
                robustness="Holds",
                curmudgeon_challenge="Maybe not",
            )
        ],
    )


def _outline() -> StructuredOutline:
    return StructuredOutline(
        engagement_id="eng_test",
        client_id="c1",
        engagement_type="sizing",
        frameworks=[],
        sections=[],
        rendered_task_ids=["task_001"],
        uncovered_branch_ids=[],
    )


def _sprint_contract() -> SprintContract:
    return SprintContract(
        section_id="section_task_001",
        engagement_id="eng_test",
        client_id="c1",
        task_id="task_001",
        section_title="Section 1",
        acceptance_criteria=["Provide estimates"],
        dimension_emphasis={},
        mandatory_elements=[],
        anti_patterns=[],
    )


def _evaluation_result() -> EvaluationResult:
    from keystone.models.evaluation import EvaluationIntensity

    return EvaluationResult(
        evaluation_id="eval_001",
        task_id="task_001",
        engagement_id="eng_test",
        client_id="c1",
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=True,
        overall_score=75.0,
        layer1_results=Layer1Result(
            facts_verified=3,
            facts_failed=0,
            numerical_issues=[],
            tokens_consumed=500,
        ),
        layer2_results=Layer2Result(
            citations_checked=1,
            citations_verified=1,
            fabrications_found=0,
            gate_passed=True,
            dead_urls_found=0,
        ),
        feedback="Good work.",
    )


# -----------------------------------------------------------------------
# POST_SPEC round-trip
# -----------------------------------------------------------------------


def test_post_spec_round_trip():
    spec = _spec()
    gov = _governance()
    payload = serialize_post_spec(spec, gov)
    result = deserialize_post_spec(payload)
    assert result.spec.research_spec.engagement_id == "eng_test"
    assert result.governance.profile == PipelineProfile.STANDARD


# -----------------------------------------------------------------------
# POST_L1_CITPROC round-trip
# -----------------------------------------------------------------------


def test_post_l1_citproc_round_trip():
    findings = [_finding()]
    manifest = _manifest()
    events = {
        "agent_001": [
            ResearchStarted(
                event_id="e1",
                engagement_id="eng_test",
                client_id="c1",
                agent_id="agent_001",
                task_id="task_001",
            )
        ]
    }
    agents = {
        "task_001": AgentInstance(
            agent_id="agent_001",
            engagement_id="eng_test",
            client_id="c1",
            definition=AgentDefinition(
                name="quant_agent",
                description="Quantitative research",
                role=AgentRole.RESEARCH,
                tools=["exa_search", "brave_search", "edgar_filings"],
            ),
            working_dir="/tmp",
            task_ids=["task_001"],
        )
    }
    gov = _governance()

    payload = serialize_post_l1_citproc(findings, manifest, events, agents, gov)
    result = deserialize_post_l1_citproc(payload)

    assert len(result.findings) == 1
    assert result.findings[0].task_id == "task_001"
    assert result.manifest.manifest_id == "MAN-001"
    assert "agent_001" in result.events_by_agent
    assert len(result.events_by_agent["agent_001"]) == 1
    assert isinstance(result.events_by_agent["agent_001"][0], ResearchStarted)
    assert "task_001" in result.agent_by_task
    assert result.governance.profile == PipelineProfile.STANDARD


# -----------------------------------------------------------------------
# POST_DELIBERATION round-trip
# -----------------------------------------------------------------------


def test_post_deliberation_round_trip():
    cm = _confidence_map()
    gov = _governance()
    payload = serialize_post_deliberation(cm, gov)
    result = deserialize_post_deliberation(payload)
    assert len(result.confidence_map.high_confidence_above_80pct) == 1
    assert result.governance.profile == PipelineProfile.STANDARD


# -----------------------------------------------------------------------
# POST_STRUCTURING round-trip
# -----------------------------------------------------------------------


def test_post_structuring_round_trip():
    outline = _outline()
    tasks = [_task()]
    texts = {"task_001": "Some analysis text"}
    contracts = {"task_001": _sprint_contract()}
    fallbacks: set[str] = set()
    gov = _governance()

    payload = serialize_post_structuring(outline, tasks, texts, contracts, fallbacks, gov)
    result = deserialize_post_structuring(payload)

    assert result.outline.engagement_id == "eng_test"
    assert len(result.eval_tasks) == 1
    assert result.section_texts["task_001"] == "Some analysis text"
    assert "task_001" in result.sprint_contracts
    assert result.fallback_task_ids == set()
    assert result.governance.profile == PipelineProfile.STANDARD


def test_post_structuring_with_fallback_ids():
    outline = _outline()
    tasks = [_task()]
    texts = {"task_001": "text"}
    contracts = {"task_001": _sprint_contract()}
    fallbacks = {"task_001"}
    gov = _governance()

    payload = serialize_post_structuring(outline, tasks, texts, contracts, fallbacks, gov)
    result = deserialize_post_structuring(payload)
    assert result.fallback_task_ids == {"task_001"}


# -----------------------------------------------------------------------
# POST_EVALUATION round-trip
# -----------------------------------------------------------------------


def test_post_evaluation_round_trip():
    results = [_evaluation_result()]
    gov = _governance()
    payload = serialize_post_evaluation(results, gov)
    result = deserialize_post_evaluation(payload)
    assert len(result.evaluation_results) == 1
    assert result.evaluation_results[0].passed is True
    assert result.governance.profile == PipelineProfile.STANDARD


# -----------------------------------------------------------------------
# Event serialization
# -----------------------------------------------------------------------


def test_events_by_agent_round_trip():
    events = {
        "agent_001": [
            ResearchStarted(
                event_id="e1",
                engagement_id="eng_test",
                client_id="c1",
                agent_id="agent_001",
                task_id="task_001",
            ),
            SourceFound(
                event_id="e2",
                engagement_id="eng_test",
                client_id="c1",
                agent_id="agent_001",
                url="https://example.com",
                source_type="news",
                quality_score=0.8,
            ),
        ]
    }
    serialized = serialize_events_by_agent(events)
    assert len(serialized["agent_001"]) == 2
    assert serialized["agent_001"][0]["event_type"] == "ResearchStarted"
    assert serialized["agent_001"][1]["event_type"] == "SourceFound"

    restored = deserialize_events_by_agent(serialized)
    assert len(restored["agent_001"]) == 2
    assert isinstance(restored["agent_001"][0], ResearchStarted)
    assert isinstance(restored["agent_001"][1], SourceFound)


def test_unknown_event_type_skipped():
    data = {
        "agent_001": [
            {"event_type": "NonExistentEvent", "event_id": "e1"},
        ]
    }
    result = deserialize_events_by_agent(data)
    assert result["agent_001"] == []


def test_missing_event_type_skipped():
    data = {
        "agent_001": [
            {"event_id": "e1", "engagement_id": "eng_test"},
        ]
    }
    result = deserialize_events_by_agent(data)
    assert result["agent_001"] == []
