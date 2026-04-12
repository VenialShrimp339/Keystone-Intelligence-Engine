"""Tests for Wave 2B governance policy routing."""

from __future__ import annotations

from keystone.governance import EnforcementAction, ProfileExecutionPolicy, ResearchStatus
from keystone.models.citations import ConfidenceTier
from keystone.models.research import (
    FindingClaim,
    FindingStatus,
    PipelineProfile,
    StructuredFinding,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskImportance,
    TaskType,
)


def _task(task_id: str, *, importance: TaskImportance = TaskImportance.SUPPORTING) -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id="eng-001",
        client_id="client-001",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Test task",
        acceptance_criteria=["criterion"],
        deliverable_destination="Section 1",
        priority=1,
        importance=importance,
        anti_confirmatory_framing="Evaluate whether the market is growing, including evidence both for and against",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        assigned_model=ModelTier.STANDARD,
        end_product="table",
    )


def _partial_finding(task_id: str) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id="agent-001",
        engagement_id="eng-001",
        client_id="client-001",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="Partial claim",
                evidence="Some evidence",
                citations=[],
                confidence=0.6,
                confidence_tier=ConfidenceTier.MODERATE,
            )
        ],
        status=FindingStatus.PARTIAL,
        gaps=["Need more evidence"],
        absence_report=[],
        sources_consulted=1,
        tokens_consumed=100,
    )


class TestProfileExecutionPolicy:
    def test_failed_no_output_task_non_renderable(self) -> None:
        task = _task("task_001")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        outcome = policy.record_research_outcome(state, task, None)

        assert outcome.research_status == ResearchStatus.FAILED_NO_OUTPUT
        assert outcome.renderable is False

    def test_partial_output_degrade_supporting_only(self) -> None:
        task = _task("task_001", importance=TaskImportance.SUPPORTING)
        policy = ProfileExecutionPolicy(PipelineProfile.DEEP)
        state = policy.new_state([task])

        outcome = policy.record_research_outcome(state, task, _partial_finding(task.id))

        assert outcome.research_status == ResearchStatus.PARTIAL
        assert outcome.renderable is True
        assert outcome.flags[0].action == EnforcementAction.DEGRADE

    def test_coverage_policy_standard_requires_primary_pass(self) -> None:
        primary = _task("task_001", importance=TaskImportance.PRIMARY)
        supporting = _task("task_002")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([primary, supporting])

        state.task_outcomes["task_001"].evaluation_status = "failed"
        state.task_outcomes["task_002"].evaluation_status = "passed"

        flag = policy.evaluate_coverage(state)

        assert flag is not None
        assert flag.action == EnforcementAction.HALT

    def test_light_coverage_halts_on_unevaluated_rendered(self) -> None:
        task = _task("task_001")
        policy = ProfileExecutionPolicy(PipelineProfile.LIGHT)
        state = policy.new_state([task])
        state.task_outcomes["task_001"].renderable = True

        flag = policy.evaluate_coverage(state)

        assert flag is not None
        assert flag.action == EnforcementAction.HALT
