"""Wave 2B execution policy for profile-aware enforcement."""

from __future__ import annotations

from keystone.governance.models import (
    EnforcementAction,
    EnforcementScope,
    GovernanceState,
    QualityFlag,
    ResearchStatus,
    TaskOutcome,
)
from keystone.models.evaluation import EvaluationResult
from keystone.models.research import FindingStatus, PipelineProfile, StructuredFinding
from keystone.models.tasks import ResearchTask, TaskImportance


class ProfileExecutionPolicy:
    """Apply the Wave 2B enforcement matrix for a specific pipeline profile."""

    def __init__(self, profile: PipelineProfile) -> None:
        self.profile = profile

    def new_state(self, tasks: list[ResearchTask]) -> GovernanceState:
        return GovernanceState(
            profile=self.profile,
            task_outcomes={
                task.id: TaskOutcome(
                    task_id=task.id,
                    importance=task.importance,
                    research_status=ResearchStatus.NOT_RUN,
                    evaluation_status="not_evaluated",
                    renderable=False,
                )
                for task in tasks
            },
        )

    def should_run_hitl_gate(self) -> bool:
        return self.profile != PipelineProfile.LIGHT

    def apply_flag(
        self,
        state: GovernanceState,
        flag: QualityFlag,
        *,
        task_id: str | None = None,
    ) -> None:
        state.flags.append(flag)
        if flag.action in {EnforcementAction.DEGRADE, EnforcementAction.WARN}:
            state.degraded = True
        if flag.action in {EnforcementAction.HALT, EnforcementAction.ESCALATE}:
            state.halted = True

        if task_id is not None and task_id in state.task_outcomes:
            outcome = state.task_outcomes[task_id]
            outcome.flags.append(flag)
            state.task_outcomes[task_id] = outcome

    def record_research_outcome(
        self,
        state: GovernanceState,
        task: ResearchTask,
        finding: StructuredFinding | None,
    ) -> TaskOutcome:
        outcome = state.task_outcomes[task.id]
        if finding is None:
            outcome.research_status = ResearchStatus.FAILED_NO_OUTPUT
            outcome.renderable = False
            if self.profile == PipelineProfile.LIGHT:
                self.apply_flag(
                    state,
                    QualityFlag(
                        gate="l1_failed_no_output",
                        action=EnforcementAction.HALT,
                        scope=EnforcementScope.TASK,
                        severity="critical",
                        message=f"Task {task.id} produced no output under LIGHT profile.",
                        task_id=task.id,
                    ),
                    task_id=task.id,
                )
            return outcome

        if finding.status == FindingStatus.COMPLETE:
            outcome.research_status = ResearchStatus.SUCCESS
            outcome.renderable = True
            return outcome

        outcome.research_status = ResearchStatus.PARTIAL
        outcome.renderable = self._partial_output_renderable(task.importance)
        action = self._partial_output_action(task.importance)
        if action is not None:
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l1_partial_output",
                    action=action,
                    scope=EnforcementScope.TASK,
                    severity="warn" if action == EnforcementAction.DEGRADE else "error",
                    message=f"Task {task.id} produced partial output.",
                    task_id=task.id,
                ),
                task_id=task.id,
            )
        return outcome

    def evaluate_coverage(self, state: GovernanceState) -> QualityFlag | None:
        outcomes = list(state.task_outcomes.values())
        if not outcomes:
            return None

        if self.profile == PipelineProfile.LIGHT:
            uncovered = [
                outcome.task_id
                for outcome in outcomes
                if self._requires_light_pass(outcome)
            ]
            if uncovered:
                return QualityFlag(
                    gate="evaluation_coverage",
                    action=EnforcementAction.HALT,
                    scope=EnforcementScope.PIPELINE,
                    severity="critical",
                    message=(
                        "LIGHT profile requires every renderable task to be evaluated "
                        "and passed, including tasks that produced output and later "
                        f"failed evaluation. Missing or failed tasks: {sorted(uncovered)}"
                    ),
                )
            return None

        passed = [outcome for outcome in outcomes if outcome.evaluation_status == "passed"]
        ratio = len(passed) / len(outcomes)

        if self.profile == PipelineProfile.STANDARD:
            primary_failed = [
                outcome.task_id
                for outcome in outcomes
                if outcome.importance == TaskImportance.PRIMARY
                and outcome.evaluation_status != "passed"
            ]
            if primary_failed or ratio < 0.60:
                return QualityFlag(
                    gate="evaluation_coverage",
                    action=EnforcementAction.HALT,
                    scope=EnforcementScope.PIPELINE,
                    severity="critical",
                    message=(
                        "STANDARD profile requires all PRIMARY tasks to pass and at least "
                        f"60% overall pass coverage. primary_failed={sorted(primary_failed)}, "
                        f"pass_ratio={ratio:.2f}"
                    ),
                )
            return None

        required_failed = [
            outcome.task_id
            for outcome in outcomes
            if outcome.importance in {TaskImportance.PRIMARY, TaskImportance.CRITICAL}
            and outcome.evaluation_status != "passed"
        ]
        if required_failed or ratio < 0.80:
            return QualityFlag(
                gate="evaluation_coverage",
                action=EnforcementAction.HALT,
                scope=EnforcementScope.PIPELINE,
                severity="critical",
                message=(
                    "DEEP profile requires all PRIMARY/CRITICAL tasks to pass and at least "
                    f"80% overall pass coverage. required_failed={sorted(required_failed)}, "
                    f"pass_ratio={ratio:.2f}"
                ),
            )
        return None

    def record_evaluation_outcome(
        self,
        state: GovernanceState,
        task: ResearchTask,
        result: EvaluationResult,
    ) -> TaskOutcome:
        outcome = state.task_outcomes[task.id]
        outcome.evaluation_status = "passed" if result.passed else "failed"
        outcome.renderable = outcome.renderable and result.passed

        if not result.layer2_results.gate_passed:
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l4_citation_fabrication",
                    action=EnforcementAction.HALT,
                    scope=EnforcementScope.TASK,
                    severity="critical",
                    message=f"Task {task.id} failed citation fabrication gate.",
                    task_id=task.id,
                ),
                task_id=task.id,
            )
            return outcome

        layer1_has_discrepancies = (
            result.layer1_results.facts_failed > 0
            or bool(result.layer1_results.numerical_inconsistencies)
            or bool(result.layer1_results.dead_urls)
        )
        if layer1_has_discrepancies:
            action = (
                EnforcementAction.WARN
                if self.profile == PipelineProfile.LIGHT
                else EnforcementAction.DEGRADE
            )
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l4_layer1_discrepancies",
                    action=action,
                    scope=EnforcementScope.TASK,
                    severity="warn",
                    message=f"Task {task.id} has deterministic evaluation discrepancies.",
                    task_id=task.id,
                ),
                task_id=task.id,
            )

        if not result.passed and self.profile != PipelineProfile.LIGHT:
            action = (
                EnforcementAction.ESCALATE
                if self.profile == PipelineProfile.DEEP
                else EnforcementAction.DEGRADE
            )
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l4_rubric_threshold",
                    action=action,
                    scope=EnforcementScope.TASK,
                    severity="error",
                    message=f"Task {task.id} missed the rubric pass threshold.",
                    task_id=task.id,
                ),
                task_id=task.id,
            )

        return outcome

    def _partial_output_action(
        self,
        importance: TaskImportance,
    ) -> EnforcementAction | None:
        if self.profile in {PipelineProfile.LIGHT, PipelineProfile.STANDARD}:
            return EnforcementAction.DEGRADE
        if importance in {TaskImportance.SUPPORTING, TaskImportance.OPTIONAL}:
            return EnforcementAction.DEGRADE
        return EnforcementAction.ESCALATE

    def _partial_output_renderable(self, importance: TaskImportance) -> bool:
        if self.profile != PipelineProfile.DEEP:
            return True
        return importance in {TaskImportance.SUPPORTING, TaskImportance.OPTIONAL}

    def _requires_light_pass(self, outcome: TaskOutcome) -> bool:
        if outcome.evaluation_status == "failed":
            return outcome.research_status in {
                ResearchStatus.SUCCESS,
                ResearchStatus.PARTIAL,
            }
        return outcome.renderable and outcome.evaluation_status != "passed"
