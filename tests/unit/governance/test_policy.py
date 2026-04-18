"""Tests for Wave 2B governance policy routing."""

from __future__ import annotations

from datetime import UTC, datetime

from keystone.governance import EnforcementAction, ProfileExecutionPolicy, ResearchStatus
from keystone.models.citations import ConfidenceTier
from keystone.models.evaluation import (
    DimensionScore,
    EvaluationIntensity,
    EvaluationResult,
    JudgeScore,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    Layer5Result,
    RubricDimension,
    VetoEvent,
)
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


def _failed_evaluation(task_id: str) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=f"eval-{task_id}",
        engagement_id="eng-001",
        client_id="client-001",
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.LIGHT_TOUCH,
        passed=False,
        overall_score=48.0,
        layer1_results=Layer1Result(facts_verified=5, facts_failed=0),
        layer2_results=Layer2Result(
            citations_checked=3,
            citations_verified=3,
            gate_passed=True,
        ),
        feedback="Needs revision.",
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

    def test_light_coverage_halts_on_failed_evaluated_output(self) -> None:
        task = _task("task_001")
        policy = ProfileExecutionPolicy(PipelineProfile.LIGHT)
        state = policy.new_state([task])

        research_outcome = policy.record_research_outcome(
            state,
            task,
            _partial_finding(task.id),
        )
        assert research_outcome.renderable is True

        evaluation_outcome = policy.record_evaluation_outcome(
            state,
            task,
            _failed_evaluation(task.id),
        )

        assert evaluation_outcome.evaluation_status == "failed"
        assert evaluation_outcome.renderable is False

        flag = policy.evaluate_coverage(state)

        assert flag is not None
        assert flag.action == EnforcementAction.HALT
        assert "task_001" in flag.message


def _ensemble_failed_evaluation(
    task_id: str,
    *,
    layer5: Layer5Result,
    intensity: EvaluationIntensity = EvaluationIntensity.STANDARD,
    passed: bool = False,
    overall_score: float = 0.0,
) -> EvaluationResult:
    """EvaluationResult carrying a Layer5Result for ensemble-gate tests."""
    return EvaluationResult(
        evaluation_id=f"eval-{task_id}",
        engagement_id="eng-001",
        client_id="client-001",
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=intensity,
        passed=passed,
        overall_score=overall_score,
        layer1_results=Layer1Result(facts_verified=5, facts_failed=0),
        layer2_results=Layer2Result(
            citations_checked=3,
            citations_verified=3,
            gate_passed=True,
        ),
        layer3_results=Layer3Result(
            dimension_scores=[],
            weighted_total=0.0,
            gestalt_adjustment=0.0,
            final_score=0.0,
        ),
        layer5_results=layer5,
        feedback="Dissenter veto triggered.",
    )


def _judge_layer3(final_score: float, gestalt: float = 0.0) -> Layer3Result:
    """Build a populated Layer3Result for JudgeScore fixtures.

    succeeded=True implies layer3_result is not None. Encoding that invariant
    in the helper keeps test fixtures coherent with the ensemble's runtime
    contract.
    """
    return Layer3Result(
        dimension_scores=[
            DimensionScore(
                dimension=RubricDimension.INTENT_ALIGNMENT,
                score=max(0.0, min(100.0, final_score)),
                feedback="mock",
            )
        ],
        weighted_total=final_score,
        gestalt_adjustment=gestalt,
        final_score=final_score,
    )


class TestEnsembleGovernanceGates:
    def test_tier1_veto_escalates_under_standard(self) -> None:
        task = _task("task_veto", importance=TaskImportance.PRIMARY)
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        veto = VetoEvent(
            dimension=RubricDimension.INTENT_ALIGNMENT,
            floor_threshold=40.0,
            min_score=35.0,
            dissenting_judge_ids=["flagship_a"],
            judge_scores={"flagship_a": 35.0, "flagship_b": 85.0},
        )
        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[
                JudgeScore(
                    judge_id="flagship_a",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(35.0),
                    succeeded=True,
                ),
                JudgeScore(
                    judge_id="flagship_b",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(85.0),
                    succeeded=True,
                ),
            ],
            aggregated_dimension_scores=[
                DimensionScore(
                    dimension=RubricDimension.INTENT_ALIGNMENT,
                    score=60.0,
                    feedback="median",
                )
            ],
            ensemble_weighted_total=0.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=0.0,
            tier1_vetoed=True,
            veto_events=[veto],
            agreement_level=1.0,
        )

        policy.record_evaluation_outcome(
            state, task, _ensemble_failed_evaluation(task.id, layer5=layer5)
        )

        veto_flags = [flag for flag in state.flags if flag.gate == "l5_ensemble_dissenter_veto"]
        assert len(veto_flags) == 1
        assert veto_flags[0].action == EnforcementAction.ESCALATE

    def test_tier1_veto_skipped_under_light_profile(self) -> None:
        task = _task("task_veto_light")
        policy = ProfileExecutionPolicy(PipelineProfile.LIGHT)
        state = policy.new_state([task])

        veto = VetoEvent(
            dimension=RubricDimension.INTENT_ALIGNMENT,
            floor_threshold=40.0,
            min_score=35.0,
            dissenting_judge_ids=["flagship_a"],
            judge_scores={"flagship_a": 35.0, "flagship_b": 85.0},
        )
        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=0.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=0.0,
            tier1_vetoed=True,
            veto_events=[veto],
            agreement_level=1.0,
        )

        policy.record_evaluation_outcome(
            state,
            task,
            _ensemble_failed_evaluation(
                task.id, layer5=layer5, intensity=EvaluationIntensity.LIGHT_TOUCH
            ),
        )

        veto_flags = [flag for flag in state.flags if flag.gate == "l5_ensemble_dissenter_veto"]
        assert veto_flags == []

    def test_all_judges_failed_warns_regardless_of_pass(self) -> None:
        task = _task("task_infra")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[
                JudgeScore(
                    judge_id="flagship_a",
                    judge_tier="flagship",
                    layer3_result=None,
                    succeeded=False,
                    error="RuntimeError: mock",
                ),
                JudgeScore(
                    judge_id="flagship_b",
                    judge_tier="flagship",
                    layer3_result=None,
                    succeeded=False,
                    error="RuntimeError: mock",
                ),
            ],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=0.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=0.0,
            tier1_vetoed=False,
            veto_events=[],
            agreement_level=0.0,
            all_judges_failed=True,
            failed_judge_ids=["flagship_a", "flagship_b"],
        )

        policy.record_evaluation_outcome(
            state, task, _ensemble_failed_evaluation(task.id, layer5=layer5)
        )

        infra_flags = [
            flag for flag in state.flags if flag.gate == "l5_ensemble_infrastructure_failure"
        ]
        assert len(infra_flags) == 1
        assert infra_flags[0].action == EnforcementAction.WARN

    def test_low_agreement_emits_warn_under_standard(self) -> None:
        """Judges disagreed across most dimensions → low-agreement flag fires as WARN."""
        task = _task("task_low_agree")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[
                JudgeScore(
                    judge_id="flagship_a",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(75.0),
                    succeeded=True,
                ),
                JudgeScore(
                    judge_id="flagship_b",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(50.0),
                    succeeded=True,
                ),
            ],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=60.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=60.0,
            tier1_vetoed=False,
            veto_events=[],
            agreement_level=0.10,
        )

        result = _ensemble_failed_evaluation(
            task.id, layer5=layer5, passed=True, overall_score=60.0
        )
        policy.record_evaluation_outcome(state, task, result)

        flags = [flag for flag in state.flags if flag.gate == "l5_low_agreement"]
        assert len(flags) == 1
        assert flags[0].action == EnforcementAction.WARN

    def test_low_agreement_escalates_under_deep(self) -> None:
        """Same disagreement under DEEP profile is severe enough to escalate."""
        task = _task("task_low_agree_deep")
        policy = ProfileExecutionPolicy(PipelineProfile.DEEP)
        state = policy.new_state([task])

        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b", "standard_crossmodel"],
            judge_scores=[
                JudgeScore(
                    judge_id=jid,
                    judge_tier=tier,
                    layer3_result=_judge_layer3(score),
                    succeeded=True,
                )
                for jid, tier, score in (
                    ("flagship_a", "flagship", 85.0),
                    ("flagship_b", "flagship", 50.0),
                    ("standard_crossmodel", "standard", 65.0),
                )
            ],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=65.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=65.0,
            tier1_vetoed=False,
            veto_events=[],
            agreement_level=0.20,
        )

        result = _ensemble_failed_evaluation(
            task.id, layer5=layer5, passed=True, overall_score=65.0
        )
        policy.record_evaluation_outcome(state, task, result)

        flags = [flag for flag in state.flags if flag.gate == "l5_low_agreement"]
        assert len(flags) == 1
        assert flags[0].action == EnforcementAction.ESCALATE

    def test_low_agreement_suppressed_when_already_vetoed(self) -> None:
        """Low agreement is subsumed by Tier 1 veto; do not double-signal."""
        task = _task("task_low_agree_veto")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        veto = VetoEvent(
            dimension=RubricDimension.INTENT_ALIGNMENT,
            floor_threshold=40.0,
            min_score=30.0,
            dissenting_judge_ids=["flagship_a"],
            judge_scores={"flagship_a": 30.0, "flagship_b": 80.0},
        )
        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[
                JudgeScore(
                    judge_id="flagship_a",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(30.0),
                    succeeded=True,
                ),
                JudgeScore(
                    judge_id="flagship_b",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(80.0),
                    succeeded=True,
                ),
            ],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=0.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=0.0,
            tier1_vetoed=True,
            veto_events=[veto],
            agreement_level=0.0,
        )

        policy.record_evaluation_outcome(
            state, task, _ensemble_failed_evaluation(task.id, layer5=layer5)
        )

        low_flags = [flag for flag in state.flags if flag.gate == "l5_low_agreement"]
        veto_flags = [flag for flag in state.flags if flag.gate == "l5_ensemble_dissenter_veto"]
        assert low_flags == []
        assert len(veto_flags) == 1

    def test_degraded_panel_warns_when_one_judge_fails(self) -> None:
        """1 of 2 judges failed; ensemble still produced a score → WARN flag."""
        task = _task("task_degraded")
        policy = ProfileExecutionPolicy(PipelineProfile.STANDARD)
        state = policy.new_state([task])

        layer5 = Layer5Result(
            judges_used=["flagship_a", "flagship_b"],
            judge_scores=[
                JudgeScore(
                    judge_id="flagship_a",
                    judge_tier="flagship",
                    layer3_result=None,
                    succeeded=False,
                    error="RuntimeError: mock",
                ),
                JudgeScore(
                    judge_id="flagship_b",
                    judge_tier="flagship",
                    layer3_result=_judge_layer3(70.0),
                    succeeded=True,
                ),
            ],
            aggregated_dimension_scores=[],
            ensemble_weighted_total=70.0,
            ensemble_gestalt_adjustment=0.0,
            ensemble_final_score=70.0,
            tier1_vetoed=False,
            veto_events=[],
            agreement_level=1.0,
            all_judges_failed=False,
            failed_judge_ids=["flagship_a"],
        )

        result = _ensemble_failed_evaluation(
            task.id, layer5=layer5, passed=True, overall_score=70.0
        )
        policy.record_evaluation_outcome(state, task, result)

        degraded = [flag for flag in state.flags if flag.gate == "l5_ensemble_degraded_panel"]
        assert len(degraded) == 1
        assert degraded[0].action == EnforcementAction.WARN
        assert "flagship_a" in degraded[0].message
