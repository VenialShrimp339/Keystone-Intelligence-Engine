"""Adversarial canary tests for Keystone's architectural guarantees.

These tests attack the specific runtime claims the architecture makes
about itself: evaluation gating, HITL modification propagation,
dependency-aware scheduling, per-task citation scoping, truthful L0
validation, claim-level citation narrowing, deep-research audit parity,
and evaluator fallback safety.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer2_citation_gate import DOIVerificationResult
from keystone.events import CitationExtracted, SourceFound, SpecificationGenerated
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.servers import register_all_tools
from keystone.gateway.tool_registry import ToolRegistry
from keystone.hitl.schemas import (
    DecisionResponse,
    DecisionType,
    GateResponse,
    GateStatus,
    GateType,
)
from keystone.models.agents import (
    AgentDefinition,
    AgentInstance,
    AgentRole,
    ResearchAgentType,
)
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap, HighConfidenceClaim
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    RubricDimension,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    FindingClaim,
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
from keystone.pipeline.orchestrator import Pipeline, PipelineComponents, PipelineResult
from keystone.research.research_agent import ResearchAgent
from keystone.specification.decomposer import IssueTree, IssueTreeMetadata, IssueTreeNode
from keystone.specification.engagement_classifier import (
    ClassificationResult,
    PipelineProfile,
)
from keystone.specification.intent_clarifier import IntentClarificationResult
from keystone.specification.priority_scorer import PriorityScore
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.validator import MECEValidationResult, ValidationDimension

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _DummySessionContext:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class _DummySessionFactory:
    def __call__(self) -> _DummySessionContext:
        return _DummySessionContext()


def _confidence_tier(confidence: float) -> ConfidenceTier:
    if confidence >= 0.8:
        return ConfidenceTier.HIGH
    if confidence >= 0.6:
        return ConfidenceTier.MODERATE
    if confidence >= 0.5:
        return ConfidenceTier.WEAK
    if confidence > 0.0:
        return ConfidenceTier.CONTESTED
    return ConfidenceTier.INSUFFICIENT


def _citation(
    citation_id: str,
    *,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
    url: str | None = None,
    doi: str | None = None,
    title: str | None = None,
) -> Citation:
    return Citation(
        citation_id=citation_id,
        engagement_id=eid,
        client_id=cid,
        url=url or f"https://example.com/{citation_id.lower()}",
        doi=doi,
        title=title or f"Source {citation_id}",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _claim(
    text: str,
    *,
    citations: list[Citation],
    confidence: float = 0.75,
    evidence: str = "Supporting evidence.",
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence=evidence,
        citations=citations,
        confidence=confidence,
        confidence_tier=_confidence_tier(confidence),
    )


def _finding(
    task_id: str,
    *,
    claims: list[FindingClaim],
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
    agent_id: str | None = None,
) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=agent_id or f"agent_{task_id}",
        engagement_id=eid,
        client_id=cid,
        agent_type="quantitative",
        claims=claims,
        absence_report=["No additional absent evidence surfaced."],
        sources_consulted=max(1, sum(len(claim.citations) for claim in claims)),
        tokens_consumed=250,
    )


def _task(
    task_id: str,
    *,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
    description: str | None = None,
    dependencies: list[str] | None = None,
) -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id=eid,
        client_id=cid,
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description=description or f"Investigate {task_id}",
        acceptance_criteria=["Provide evidence-backed claims."],
        deliverable_destination=f"Section for {task_id}",
        priority=1,
        anti_confirmatory_framing=(
            f"Evaluate whether {task_id} holds, including evidence for and against."
        ),
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        assigned_model=ModelTier.STANDARD,
        end_product=f"Structured output for {task_id}",
        dependencies=dependencies or [],
        issue_tree_branch_id=f"branch_{task_id}",
    )


def _spec(
    tasks: list[ResearchTask],
    *,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
) -> EngagementSpec:
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id=eid,
            client_id=cid,
            title="Architectural Canary Engagement",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Verify runtime architectural invariants.",
            surprising_finding="The runtime violates its own guarantees.",
            questions=[ResearchQuestion(question="Do runtime guarantees hold?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="Architectural guarantees are enforced at runtime.",
        ),
        task_decomposition=TaskDecomposition(
            project="Architectural Canary",
            engagement_id=eid,
            client_id=cid,
            research_md_path="/tmp/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="One task per architectural invariant.",
            tasks=tasks,
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _manifest(
    *citations: Citation,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
) -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-CANARY",
        engagement_id=eid,
        client_id=cid,
        citations=list(citations),
    )


def _empty_confidence_map(
    *,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
) -> ConfidenceMap:
    return ConfidenceMap(engagement_id=eid, client_id=cid)


def _issue_tree() -> IssueTree:
    root = IssueTreeNode(
        id="root",
        name="Root",
        description="Root issue tree node",
        children=[
            IssueTreeNode(
                id="leaf_001",
                name="Leaf 1",
                description="Investigate the primary branch",
            ),
        ],
    )
    return IssueTree(
        root=root,
        metadata=IssueTreeMetadata(
            depth=1,
            leaf_count=1,
            lenses_used=["financial", "operational", "market"],
            synthesis_rationale="Single-leaf test tree.",
        ),
    )


def _agent(
    *,
    agent_id: str = "agent_001",
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
) -> AgentInstance:
    definition = AgentDefinition(
        name="quantitative_analyst",
        description="Quantitative research specialist",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "edgar_filings"],
        research_type=ResearchAgentType.QUANTITATIVE,
    )
    return AgentInstance(
        agent_id=agent_id,
        engagement_id=eid,
        client_id=cid,
        definition=definition,
        working_dir=f"/tmp/keystone/{eid}/{agent_id}",
        task_ids=["task_001"],
    )


def _build_gateway(
    client: MockMCPClient | None = None,
) -> tuple[MCPGateway, MockMCPClient]:
    registry = ToolRegistry()
    register_all_tools(registry)
    mock_client = client or MockMCPClient()
    gateway = MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=mock_client,
    )
    return gateway, mock_client


def _sprint_contract(task: ResearchTask) -> SprintContract:
    return SprintContract(
        section_id=f"sec_{task.id}",
        engagement_id=task.engagement_id,
        client_id=task.client_id,
        task_id=task.id,
        section_title=task.deliverable_destination,
        acceptance_criteria=task.acceptance_criteria,
    )


def _evaluation_result(
    task_id: str,
    *,
    eid: str = "ENG-CANARY",
    cid: str = "CLIENT-CANARY",
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=f"eval_{task_id}",
        engagement_id=eid,
        client_id=cid,
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=True,
        overall_score=75.0,
        layer1_results=Layer1Result(
            facts_verified=1,
            facts_failed=0,
            numerical_inconsistencies=[],
            dead_urls=[],
        ),
        layer2_results=Layer2Result(
            citations_checked=1,
            citations_verified=1,
            citations_fabricated=[],
            gate_passed=True,
        ),
        layer3_results=Layer3Result(
            dimension_scores=[],
            weighted_total=75.0,
            gestalt_adjustment=0.0,
            final_score=75.0,
        ),
        feedback="PASSED with score 75.0/100.",
    )


async def _empty_event_stream(*args, **kwargs):
    if False:
        yield None


async def _all_urls_live(citations, concurrency: int = 10) -> dict[str, bool]:
    del concurrency
    return {citation.citation_id: True for citation in citations}


async def _fake_doi_verify(self, doi: str) -> DOIVerificationResult:
    return DOIVerificationResult(exists=doi != "10.9999/fabricated")


async def _unused_llm(prompt: str) -> str:
    raise AssertionError(f"Unexpected LLM call: {prompt[:80]}")


async def _evaluator_llm(prompt: str) -> str:
    lower = prompt.lower()

    if (
        "fact decomposition" in lower
        or "fact-checking analyst" in lower
        or "factscore" in lower
    ):
        return json.dumps([
            {
                "claim": "Test claim",
                "status": "SUPPORTED",
                "citation_id": "CIT-001",
                "reasoning": "Supported by the cited source.",
            },
        ])

    if "numerical consistency" in lower:
        return json.dumps({"numerical_claims": [], "inconsistencies": []})

    if "gestalt overlay" in lower or "holistic quality assessment" in lower:
        return json.dumps({"adjustment": 0.0, "rationale": "No adjustment needed."})

    for dimension in RubricDimension:
        header = f"{dimension.value.replace('_', ' ')} evaluation"
        if header in lower or (
            dimension.value in lower and "evaluation" in lower
        ):
            return json.dumps({
                "score": 75,
                "feedback": f"Strong {dimension.value}.",
                "sub_criteria_notes": [],
            })

    return json.dumps({"score": 75, "feedback": "Fallback evaluator response."})


async def _deliberation_llm(prompt: str) -> str:
    lower = prompt.lower()

    if "evaluate each claim" in lower:
        return json.dumps([
            {
                "index": 0,
                "confidence": 0.82,
                "source_count": 2,
                "reasoning": "Supported by multiple sources.",
            },
        ])

    if "select the analyst" in lower:
        return json.dumps({
            "selected_analyst": "quantitative",
            "reasoning": "Quantitative view is best supported.",
        })

    if "logical contradictions" in lower or "contradictions" in lower:
        return json.dumps({"contradictions": []})

    if "assumptions" in lower and "have to be true" in lower:
        return json.dumps({"assumptions": ["Key assumption remains true."]})

    return json.dumps({"result": "ok"})


async def _two_round_shallow_llm(prompt: str) -> str:
    lower = prompt.lower()

    if "round:" in lower and "synthesize findings" in lower:
        match = re.search(r"round:\s*(\d+)", prompt, flags=re.IGNORECASE)
        round_num = int(match.group(1)) if match else 1
        return json.dumps([
            {
                "text": f"Round {round_num} claim",
                "evidence": f"Evidence synthesized in round {round_num}",
                "confidence": 0.55,
                "caveats": [],
            },
        ])

    if "not found" in lower and "absence" in lower:
        return json.dumps(["No proprietary pricing dataset was publicly available."])

    return json.dumps({"result": "ok"})


async def _run_pipeline_result(
    spec: EngagementSpec,
    findings: list[StructuredFinding],
) -> PipelineResult:
    gateway, _ = _build_gateway()
    pipeline = Pipeline(llm_factory=lambda tier: _evaluator_llm, gateway=gateway)
    c = pipeline._build_components()
    c.spec_engine.generate_spec = _empty_event_stream
    c.spec_engine.get_spec = AsyncMock(return_value=spec)
    c.agent_pool.execute_all = AsyncMock(return_value=[])
    c.agent_pool.get_successful_findings = MagicMock(return_value=findings)
    c.deliberation.deliberate = _empty_event_stream
    c.deliberation.get_confidence_map = AsyncMock(
        return_value=_empty_confidence_map(
            eid=spec.research_spec.engagement_id,
            cid=spec.research_spec.client_id,
        )
    )
    pipeline._pending_components = c

    with (
        patch("keystone.citation.processor.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer1_deterministic.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer2_citation_gate.batch_check_urls", new=_all_urls_live),
        patch(
            "keystone.evaluator.layer2_citation_gate.HTTPDOIVerifier.verify",
            new=_fake_doi_verify,
        ),
    ):
        return await pipeline.run("Architectural canary question", spec.research_spec.client_id)


async def test_failed_evaluation_blocks_rendering() -> None:
    """Architectural claim: Layer 2 failures must not leak into rendered output."""
    good_task = _task("task_001")
    bad_task = _task("task_002")
    spec = _spec([good_task, bad_task])

    good_claim_text = "Good task claim survives evaluation."
    bad_claim_text = "Fabricated task claim must be blocked."

    good_finding = _finding(
        good_task.id,
        claims=[
            _claim(
                good_claim_text,
                citations=[_citation("CIT-001", title="Verified source")],
                confidence=0.84,
            ),
        ],
    )
    bad_finding = _finding(
        bad_task.id,
        claims=[
            _claim(
                bad_claim_text,
                citations=[
                    _citation(
                        "CIT-002",
                        doi="10.9999/fabricated",
                        title="Fabricated source",
                    ),
                ],
                confidence=0.82,
            ),
        ],
    )

    result = await _run_pipeline_result(spec, [good_finding, bad_finding])

    assert good_claim_text in result.markdown_output
    assert bad_claim_text not in result.markdown_output


@pytest.mark.xfail(reason="fix in progress")
async def test_hitl_modify_changes_downstream_artifact() -> None:
    """Architectural claim: a HITL modify decision must alter the post-gate artifact."""
    findings = [
        _finding(
            "task_001",
            claims=[
                _claim(
                    "Original confidence-map claim",
                    citations=[_citation("CIT-001")],
                    confidence=0.83,
                ),
            ],
        ),
    ]
    manifest = _manifest(_citation("CIT-001"))

    original_map = ConfidenceMap(
        engagement_id="ENG-CANARY",
        client_id="CLIENT-CANARY",
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="Original confidence-map claim",
                methodological_agreement="4/4",
                sources=1,
                corroboration_count=1,
                robustness="Original robustness",
                curmudgeon_challenge="Original challenge",
            ),
        ],
    )
    modified_map = ConfidenceMap(
        engagement_id="ENG-CANARY",
        client_id="CLIENT-CANARY",
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="Human-modified confidence-map claim",
                methodological_agreement="4/4",
                sources=1,
                corroboration_count=1,
                robustness="Modified robustness",
                curmudgeon_challenge="Modified challenge",
            ),
        ],
        gaps_identified=["Human requested follow-up"],
    )

    gate_response = GateResponse(
        id="gate-001",
        engagement_id="ENG-CANARY",
        client_id="CLIENT-CANARY",
        gate_type=GateType.POST_DELIBERATION,
        status=GateStatus.MODIFIED,
        created_at=datetime.now(UTC),
        resolved_at=datetime.now(UTC),
        resolved_by="reviewer",
        decision=DecisionResponse(
            id="decision-001",
            gate_id="gate-001",
            decision=DecisionType.MODIFY,
            modifications={"confidence_map": modified_map.model_dump(mode="json")},
            decided_by="reviewer",
            decided_at=datetime.now(UTC),
        ),
    )

    deliberation = Deliberation(
        analyst_llm=_deliberation_llm,
        db_session_factory=_DummySessionFactory(),
    )

    with (
        patch(
            "keystone.deliberation.deliberation.build_confidence_map",
            return_value=original_map,
        ),
        patch(
            "keystone.hitl.gate.create_and_wait_for_gate",
            new=AsyncMock(return_value=gate_response),
        ),
    ):
        async for _ in deliberation.deliberate(
            manifest,
            findings,
            "ENG-CANARY",
            "CLIENT-CANARY",
        ):
            pass

    post_gate_map = await deliberation.get_confidence_map()
    assert post_gate_map.model_dump(mode="json") == modified_map.model_dump(mode="json")


@pytest.mark.xfail(reason="fix in progress")
async def test_dependent_tasks_do_not_start_before_dependencies_complete() -> None:
    """Architectural claim: downstream tasks must wait for declared dependencies."""
    task_a = _task("task_001", description="Root task")
    task_b = _task(
        "task_002",
        description="Dependent task",
        dependencies=["task_001"],
    )
    spec = _spec([task_a, task_b])
    gateway, _ = _build_gateway()
    pipeline = Pipeline(llm_factory=lambda tier: _evaluator_llm, gateway=gateway)

    started_at: dict[str, float] = {}
    completed_at: dict[str, float] = {}

    async def fake_execute(self, task: ResearchTask, spec: EngagementSpec, agent: AgentInstance):
        started_at[task.id] = time.perf_counter()
        if task.id == "task_001":
            await asyncio.sleep(0.05)
        self._finding = _finding(
            task.id,
            claims=[
                _claim(
                    f"{task.id} completed",
                    citations=[],
                    confidence=0.6,
                ),
            ],
            eid=spec.research_spec.engagement_id,
            cid=spec.research_spec.client_id,
            agent_id=agent.agent_id,
        )
        completed_at[task.id] = time.perf_counter()
        if False:
            yield None

    class _PassingEvaluator:
        def __init__(self, *args, **kwargs) -> None:
            self._result: EvaluationResult | None = None

        async def evaluate(self, output_text, contract, task, manifest, spec):
            del output_text, contract, manifest, spec
            self._result = _evaluation_result(
                task.id,
                eid=task.engagement_id,
                cid=task.client_id,
            )
            if False:
                yield None

        async def get_result(self) -> EvaluationResult:
            assert self._result is not None
            return self._result

    c = pipeline._build_components()
    c.spec_engine.generate_spec = _empty_event_stream
    c.spec_engine.get_spec = AsyncMock(return_value=spec)
    c.citation_processor.process = _empty_event_stream
    c.citation_processor.get_manifest = AsyncMock(
        return_value=CitationManifest(
            manifest_id="MAN-EMPTY",
            engagement_id=spec.research_spec.engagement_id,
            client_id=spec.research_spec.client_id,
        )
    )
    c.deliberation.deliberate = _empty_event_stream
    c.deliberation.get_confidence_map = AsyncMock(
        return_value=_empty_confidence_map(
            eid=spec.research_spec.engagement_id,
            cid=spec.research_spec.client_id,
        )
    )
    c.renderer.render = MagicMock(return_value="# Rendered")
    pipeline._pending_components = c

    with (
        patch("keystone.pipeline.orchestrator.Evaluator", new=_PassingEvaluator),
        patch.object(ResearchAgent, "execute", new=fake_execute),
    ):
        await pipeline.run("Dependency canary", spec.research_spec.client_id)

    assert started_at["task_002"] >= completed_at["task_001"]


@pytest.mark.xfail(reason="fix in progress")
async def test_fabricated_citation_in_task_a_does_not_fail_task_b() -> None:
    """Architectural claim: citation gating must be task-scoped, not engagement-scoped."""
    task_a = _task("task_001", description="Task A with fabricated citation")
    task_b = _task("task_002", description="Task B with clean citation")
    spec = _spec([task_a, task_b])

    finding_a = _finding(
        task_a.id,
        claims=[
            _claim(
                "Task A claim",
                citations=[
                    _citation(
                        "CIT-001",
                        doi="10.9999/fabricated",
                        title="Fabricated DOI source",
                    ),
                ],
                confidence=0.82,
            ),
        ],
    )
    finding_b = _finding(
        task_b.id,
        claims=[
            _claim(
                "Task B claim",
                citations=[_citation("CIT-002", title="Verified URL source")],
                confidence=0.84,
            ),
        ],
    )

    result = await _run_pipeline_result(spec, [finding_a, finding_b])
    by_task = {evaluation.task_id: evaluation for evaluation in result.evaluation_results}

    assert by_task["task_001"].passed is False
    assert by_task["task_002"].passed is True


async def test_l0_validation_state_is_truthful() -> None:
    """Architectural claim: SpecificationGenerated must report real validation state."""
    engine = SpecificationEngine(_unused_llm)
    issue_tree = _issue_tree()

    engine._classifier.classify = AsyncMock(
        return_value=ClassificationResult(
            engagement_type=EngagementType.SIZING,
            pipeline_profile=PipelineProfile.STANDARD,
            confidence=0.9,
            reasoning="Sizing engagement.",
        )
    )
    engine._clarifier.clarify = AsyncMock(
        return_value=IntentClarificationResult(
            day_1_hypothesis="Hypothesis",
            intent_clear=True,
            unstated_constraints=[],
            scope_boundaries=["Boundary"],
            decision_context="Decision context",
            surprising_finding="Surprising finding",
        )
    )
    engine._decomposer.decompose = AsyncMock(return_value=issue_tree)
    engine._validator.validate = AsyncMock(
        return_value=MECEValidationResult(
            dimensions={
                ValidationDimension.MUTUAL_EXCLUSIVITY: True,
                ValidationDimension.COLLECTIVE_EXHAUSTIVENESS: False,
                ValidationDimension.TAILORING: True,
                ValidationDimension.ACTIONABILITY: True,
                ValidationDimension.DEPTH_APPROPRIATENESS: True,
            },
            feedback={dimension: "feedback" for dimension in ValidationDimension},
            all_passed=False,
            regeneration_needed=True,
        )
    )
    engine._scorer.score = AsyncMock(
        return_value=[
            PriorityScore(
                branch_id="leaf_001",
                decision_relevance=0.9,
                uncertainty_reduction=0.8,
                priority_score=0.72,
                reasoning="Important branch.",
            ),
        ]
    )

    async def fake_generate_tasks(
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
    ) -> TaskDecomposition:
        del tree, priorities, engagement_type
        return TaskDecomposition(
            project=spec.title,
            engagement_id=spec.engagement_id,
            client_id=spec.client_id,
            research_md_path="/tmp/RESEARCH.md",
            specification_version=spec.specification_version,
            decomposition_rationale="Single-task test decomposition.",
            tasks=[
                _task(
                    "task_001",
                    eid=spec.engagement_id,
                    cid=spec.client_id,
                    description="Investigate the only branch.",
                ),
            ],
        )

    engine._task_generator.generate = AsyncMock(side_effect=fake_generate_tasks)

    events = [
        event
        async for event in engine.generate_spec(
            question="Test truthful validation state",
            client_id="CLIENT-CANARY",
        )
    ]

    spec_event = next(event for event in events if isinstance(event, SpecificationGenerated))
    assert spec_event.validation_passed is False


async def test_claim_level_citations_are_narrower_than_round_level() -> None:
    """Architectural claim: claim citations must be narrower than round citation pools."""
    gateway, client = _build_gateway()
    client.set_response(
        "exa_search",
        {"url": "https://example.com/exa", "title": "Exa source", "text": "Exa text"},
    )
    client.set_response(
        "brave_search",
        {"url": "https://example.com/brave", "title": "Brave source", "text": "Brave text"},
    )
    client.set_response(
        "edgar_filings",
        {"url": "https://sec.gov/filing", "title": "EDGAR filing", "text": "Filing text"},
    )

    task = _task("task_001")
    spec = _spec([task])
    agent = ResearchAgent(llm=_two_round_shallow_llm, gateway=gateway, max_rounds=2)
    agent_instance = _agent()

    async for _ in agent.execute(task, spec, agent_instance):
        pass

    finding = await agent.get_finding()
    assert list(agent._round_citations) == [1, 2]
    assert len(finding.claims) >= 2

    for round_num, claim in enumerate(finding.claims[:2], start=1):
        round_ids = {citation.citation_id for citation in agent._round_citations[round_num]}
        claim_ids = {citation.citation_id for citation in claim.citations}
        assert claim_ids < round_ids


async def test_deep_research_emits_audit_equivalent_events() -> None:
    """Architectural claim: deep mode must still emit source and citation audit events."""
    gateway, _ = _build_gateway()
    task = _task("task_001")
    spec = _spec([task])
    agent_instance = _agent(agent_id="agent_deep")

    expected_sources = [
        {
            "url": "https://example.com/source-a",
            "title": "Source A",
            "content_snippet": "Snippet A",
        },
        {
            "url": "https://example.com/source-b",
            "title": "Source B",
            "content_snippet": "Snippet B",
        },
        {
            "url": "https://example.com/source-c",
            "title": "Source C",
            "content_snippet": "Snippet C",
        },
    ]

    async def deep_llm(prompt: str) -> str:
        del prompt
        return json.dumps({
            "claims": [
                {
                    "text": "Deep mode claim A",
                    "evidence": "Deep evidence A",
                    "confidence": 0.86,
                    "caveats": [],
                    "sources": expected_sources[:2],
                },
                {
                    "text": "Deep mode claim B",
                    "evidence": "Deep evidence B",
                    "confidence": 0.78,
                    "caveats": [],
                    "sources": expected_sources[2:],
                },
            ],
            "absence_report": ["No proprietary benchmarking dataset located."],
        })

    research_agent = ResearchAgent(
        llm=_unused_llm,
        gateway=gateway,
        deep_llm=deep_llm,
    )

    events = []
    async for event in research_agent.execute(task, spec, agent_instance):
        events.append(event)

    finding = await research_agent.get_finding()
    source_events = [event for event in events if isinstance(event, SourceFound)]
    citation_events = [event for event in events if isinstance(event, CitationExtracted)]

    expected_urls = {source["url"] for source in expected_sources}
    expected_titles = {source["title"] for source in expected_sources}
    finding_urls = {
        citation.url
        for claim in finding.claims
        for citation in claim.citations
    }
    finding_titles = {
        citation.title
        for claim in finding.claims
        for citation in claim.citations
    }

    assert source_events
    assert citation_events
    assert {event.url for event in source_events} == expected_urls
    assert {event.title for event in citation_events} == expected_titles
    assert finding_urls == expected_urls
    assert finding_titles == expected_titles


async def test_evaluator_fallback_constructors_produce_valid_models() -> None:
    """Architectural claim: evaluator fallbacks must still build valid Pydantic models."""
    task = _task("task_001")
    evaluator = Evaluator(llm=AsyncMock(side_effect=RuntimeError("LLM unavailable")))

    async for _ in evaluator.evaluate(
        "Non-empty output so both fallback paths execute.",
        _sprint_contract(task),
        task,
        _manifest(),
        _spec([task]),
    ):
        pass

    result = await evaluator.get_result()
    assert isinstance(result.layer1_results, Layer1Result)
    assert isinstance(result.layer3_results, Layer3Result)
    assert result.layer1_results.model_dump() == {
        "facts_verified": 0,
        "facts_failed": 0,
        "numerical_inconsistencies": [],
        "dead_urls": [],
    }
    assert result.layer3_results.model_dump() == {
        "dimension_scores": [],
        "weighted_total": 0.0,
        "gestalt_adjustment": 0.0,
        "final_score": 0.0,
    }


async def test_pipeline_fresh_components_per_run() -> None:
    """Architectural claim: each Pipeline.run() must use fresh component instances.

    Two consecutive runs must not share SpecificationEngine, AgentPool,
    CitationProcessor, Deliberation, or MarkdownRenderer objects. Sharing
    mutable component state across runs would allow findings, manifests,
    and agent configs from run N to contaminate run N+1.
    """
    gateway, _ = _build_gateway()
    pipeline = Pipeline(llm_factory=lambda tier: _evaluator_llm, gateway=gateway)
    spec = _spec([_task("task_001")])
    findings: list[StructuredFinding] = []

    async def noop_gen(*a, **kw):
        return
        yield

    def _make_components() -> PipelineComponents:
        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(return_value=[])
        c.agent_pool.get_successful_findings = MagicMock(return_value=findings)
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(
            return_value=_empty_confidence_map(
                eid=spec.research_spec.engagement_id,
                cid=spec.research_spec.client_id,
            )
        )
        return c

    components_seen: list[PipelineComponents] = []

    with (
        patch("keystone.citation.processor.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer1_deterministic.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer2_citation_gate.batch_check_urls", new=_all_urls_live),
        patch(
            "keystone.evaluator.layer2_citation_gate.HTTPDOIVerifier.verify",
            new=_fake_doi_verify,
        ),
    ):
        for _ in range(2):
            c = _make_components()
            components_seen.append(c)
            pipeline._pending_components = c
            await pipeline.run("Canary question", spec.research_spec.client_id)

    first, second = components_seen
    assert first.spec_engine is not second.spec_engine, (
        "spec_engine must be a fresh instance on each run"
    )
    assert first.agent_pool is not second.agent_pool, (
        "agent_pool must be a fresh instance on each run"
    )
    assert first.citation_processor is not second.citation_processor, (
        "citation_processor must be a fresh instance on each run"
    )
    assert first.deliberation is not second.deliberation, (
        "deliberation must be a fresh instance on each run"
    )
    assert first.renderer is not second.renderer, (
        "renderer must be a fresh instance on each run"
    )


async def test_spec_engine_no_agent_config_leak() -> None:
    """Architectural claim: spec_engine._agent_configs must not leak across runs.

    SpecificationEngine.__init__ sets self._agent_configs = [] and generate_spec
    appends to it. If the same engine were reused across runs, configs from run N
    would contaminate run N+1. Per-run construction (E1) prevents this: the second
    run's engine must start with an empty _agent_configs list regardless of what
    the first run populated.
    """
    gateway, _ = _build_gateway()
    pipeline = Pipeline(llm_factory=lambda tier: _evaluator_llm, gateway=gateway)

    spec_a = _spec([_task("task_001", description="Run A task")])
    spec_b = _spec([_task("task_002", description="Run B task")])

    async def noop_gen(*a, **kw):
        return
        yield

    engines_captured: list = []

    def _make_components(spec):
        c = pipeline._build_components()
        engines_captured.append(c.spec_engine)
        c.spec_engine.generate_spec = noop_gen
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(return_value=[])
        c.agent_pool.get_successful_findings = MagicMock(return_value=[])
        c.deliberation.deliberate = noop_gen
        c.deliberation.get_confidence_map = AsyncMock(
            return_value=_empty_confidence_map(
                eid=spec.research_spec.engagement_id,
                cid=spec.research_spec.client_id,
            )
        )
        return c

    with (
        patch("keystone.citation.processor.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer1_deterministic.batch_check_urls", new=_all_urls_live),
        patch("keystone.evaluator.layer2_citation_gate.batch_check_urls", new=_all_urls_live),
        patch(
            "keystone.evaluator.layer2_citation_gate.HTTPDOIVerifier.verify",
            new=_fake_doi_verify,
        ),
    ):
        # Run 1: manually populate _agent_configs on run 1's engine to simulate
        # what generate_spec would do (proving it can get dirty).
        c1 = _make_components(spec_a)
        c1.spec_engine._agent_configs = [{"task_id": "task_001", "template": "research"}]
        pipeline._pending_components = c1
        await pipeline.run("Run A question", spec_a.research_spec.client_id)

        # Run 2: fresh engine — must start empty regardless of run 1's state.
        c2 = _make_components(spec_b)
        pipeline._pending_components = c2
        await pipeline.run("Run B question", spec_b.research_spec.client_id)

    engine_a, engine_b = engines_captured
    assert engine_a is not engine_b, "run 2 must use a different SpecificationEngine"
    # After run 1 polluted engine_a, engine_b must still have started empty.
    assert engine_b._agent_configs == [], (
        "second run's spec_engine._agent_configs must be empty (no leak from run 1)"
    )


async def test_one_analyst_failure_does_not_kill_others() -> None:
    """Architectural claim: a single analyst crash must not abort deliberation.

    With bare asyncio.gather, one analyst raising an exception propagates to
    the caller and discards all other results. With return_exceptions=True and
    per-failure filtering, the remaining analysts' outputs still reach the
    aggregator and a ConfidenceMap is produced.
    """
    from keystone.deliberation.analyst import AnalystOutput

    async def flaky_llm(prompt: str) -> str:
        # The quantitative analyst prompt always contains this phrase.
        if "quantitative analyst" in prompt:
            raise RuntimeError("Simulated analyst LLM failure")
        return '[{"index": 0, "confidence": 0.75, "source_count": 2, "reasoning": "ok"}]'

    task = _task("task_001")
    spec = _spec([task])
    finding = _finding(
        "task_001",
        claims=[_claim("Claim A", citations=[], confidence=0.7)],
    )

    delib = Deliberation(analyst_llm=flaky_llm, judge_llm=flaky_llm)

    events = []
    # Suppress retry backoff so the test doesn't sleep 3+ seconds.
    with patch("keystone.evaluator.retry.asyncio.sleep", new=AsyncMock(return_value=None)):
        async for event in delib.deliberate(
            CitationManifest(
                manifest_id="MAN-TEST",
                engagement_id=spec.research_spec.engagement_id,
                client_id=spec.research_spec.client_id,
            ),
            [finding],
            spec.research_spec.engagement_id,
            spec.research_spec.client_id,
        ):
            events.append(event)

    confidence_map = await delib.get_confidence_map()

    # Deliberation must complete even though one analyst failed.
    assert confidence_map is not None
    # ConfidenceMapProduced event must have been emitted.
    from keystone.events import ConfidenceMapProduced
    assert any(isinstance(e, ConfidenceMapProduced) for e in events), (
        "ConfidenceMapProduced must be emitted even when one analyst fails"
    )
    # Three of the four analysts should have succeeded (one failed).
    from keystone.events import IndependentAnalysisComplete
    completed = [e for e in events if isinstance(e, IndependentAnalysisComplete)]
    assert len(completed) == 3, (
        f"Expected 3 analyst completions (1 failed), got {len(completed)}"
    )


async def test_subprocess_killed_on_cancellation() -> None:
    """Architectural claim: a cancelled _call_claude_cli must not leak subprocesses.

    Without try/finally around proc.communicate(), asyncio.CancelledError bypasses
    the TimeoutError handler and the subprocess runs forever. With try/finally,
    proc.kill() fires on any exit path including cancellation.
    """
    import signal

    from keystone.llm_client import _call_claude_cli

    semaphore = asyncio.Semaphore(1)
    proc_ref: list[asyncio.subprocess.Process] = []

    # Patch create_subprocess_exec to capture the process object and run
    # a long-lived command so we can verify it gets killed.
    original_create = asyncio.create_subprocess_exec

    async def capturing_create(*args, **kwargs):
        # Replace the 'claude' command with a long sleep so the process
        # doesn't exit on its own.
        new_args = ("sleep", "60")
        proc = await original_create(*new_args, **kwargs)
        proc_ref.append(proc)
        return proc

    with patch("keystone.llm_client.asyncio.create_subprocess_exec", new=capturing_create):
        task = asyncio.create_task(
            _call_claude_cli("prompt", "claude-sonnet-4-6", "medium", semaphore)
        )
        # Give the subprocess time to start.
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert proc_ref, "subprocess was never created"
    proc = proc_ref[0]
    # After cancellation, the process must be dead (returncode is set).
    assert proc.returncode is not None, (
        "subprocess was not killed after coroutine cancellation (leak detected)"
    )


async def test_circuit_breaker_single_probe_in_half_open() -> None:
    """Architectural claim: only one probe must execute when circuit is HALF_OPEN.

    Without locking through probe execution, multiple concurrent callers all
    see HALF_OPEN, release the lock, and execute simultaneously. With the fix,
    the lock is held for the duration of the probe, so concurrent callers block
    and then see either CLOSED (probe succeeded) or OPEN (probe failed).
    """
    from keystone.gateway.circuit_breaker import CircuitBreaker, CircuitOpenError

    cb = CircuitBreaker(provider="test", failure_threshold=1, recovery_timeout=0.0)

    # Open the circuit with one failure.
    async def failing_func():
        raise RuntimeError("forced failure")

    with pytest.raises(RuntimeError):
        await cb.call(failing_func)

    # Circuit is now OPEN. recovery_timeout=0.0 means it transitions to HALF_OPEN
    # immediately on the next call.

    probe_started = asyncio.Event()
    probe_gate = asyncio.Event()
    probe_count = 0

    async def gated_probe():
        nonlocal probe_count
        probe_count += 1
        probe_started.set()
        await probe_gate.wait()  # Hold until test releases the gate
        return "ok"

    # Launch 5 concurrent callers. The first to acquire the lock will be the
    # probe (HALF_OPEN path). The other 4 must block on the lock while the
    # probe is in flight.
    async def _gather():
        return await asyncio.gather(
            *(cb.call(gated_probe) for _ in range(5)),
            return_exceptions=True,
        )

    gather_task = asyncio.create_task(_gather())

    # Wait for the probe to start, then verify no additional probes fired.
    await asyncio.wait_for(probe_started.wait(), timeout=1.0)
    # Yield to let other tasks run — they should all be blocked on the lock.
    await asyncio.sleep(0)
    assert probe_count == 1, (
        f"Expected exactly 1 probe to start while lock is held, got {probe_count}"
    )

    # Release the probe gate and wait for all callers to finish.
    probe_gate.set()
    results = await gather_task

    # After the probe succeeds, circuit is CLOSED. Remaining 4 callers (which
    # were blocked on the lock) now execute via the CLOSED path — they call
    # gated_probe too but the gate is already open so they return immediately.
    # Total calls = 5 (1 probe + 4 CLOSED). All must return "ok".
    unexpected = [r for r in results if r != "ok"]
    assert not unexpected, f"Unexpected results: {unexpected}"
