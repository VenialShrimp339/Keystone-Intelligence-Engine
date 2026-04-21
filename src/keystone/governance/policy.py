"""Wave 2B execution policy for profile-aware enforcement."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from keystone.models.evaluation import Layer5Result


class ProfileExecutionPolicy:
    """Apply the Wave 2B enforcement matrix for a specific pipeline profile."""

    # Class default; the constructor copies this to an instance attribute so
    # operators can override per-pipeline via PipelineConfig without mutating
    # the class.
    _LOW_AGREEMENT_THRESHOLD: float = 0.30

    def __init__(
        self,
        profile: PipelineProfile,
        *,
        low_agreement_threshold: float | None = None,
    ) -> None:
        self.profile = profile
        self.low_agreement_threshold: float = (
            low_agreement_threshold
            if low_agreement_threshold is not None
            else self._LOW_AGREEMENT_THRESHOLD
        )

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

    def flag_mece_failure(self, state: GovernanceState) -> None:
        """Fire the l0_mece_failed gate with profile-dependent action."""
        if self.profile == PipelineProfile.LIGHT:
            action = EnforcementAction.WARN
        elif self.profile == PipelineProfile.STANDARD:
            action = EnforcementAction.DEGRADE
        else:
            action = EnforcementAction.HALT
        self.apply_flag(
            state,
            QualityFlag(
                gate="l0_mece_failed",
                action=action,
                scope=EnforcementScope.PIPELINE,
                severity="warn" if action == EnforcementAction.WARN else "error",
                message=(
                    "MECE validation failed after all retry attempts; "
                    "issue tree may contain overlapping or incomplete branches."
                ),
            ),
        )

    def flag_cost_ceiling(
        self,
        state: GovernanceState,
        *,
        task_id: str,
        tokens_used: int,
        ceiling: int,
    ) -> None:
        """Fire the l1_cost_ceiling gate when a research agent exceeds the token ceiling."""
        self.apply_flag(
            state,
            QualityFlag(
                gate="l1_cost_ceiling",
                action=EnforcementAction.WARN,
                scope=EnforcementScope.TASK,
                severity="warn",
                message=(
                    f"Task {task_id} agent used {tokens_used:,} tokens, "
                    f"exceeding the ceiling of {ceiling:,}."
                ),
                task_id=task_id,
            ),
            task_id=task_id,
        )

    def flag_tool_dead_letter(
        self,
        state: GovernanceState,
        *,
        tool_name: str,
        task_id: str,
    ) -> None:
        """Fire the l1_tool_dead_letter gate for an exhausted tool call."""
        action = (
            EnforcementAction.DEGRADE
            if self.profile == PipelineProfile.DEEP
            else EnforcementAction.WARN
        )
        self.apply_flag(
            state,
            QualityFlag(
                gate="l1_tool_dead_letter",
                action=action,
                scope=EnforcementScope.TASK,
                severity="warn",
                message=(
                    f"Tool {tool_name!r} exhausted all retries for task {task_id}; "
                    "coverage may be reduced."
                ),
                task_id=task_id,
            ),
            task_id=task_id,
        )

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
                outcome.task_id for outcome in outcomes if self._requires_light_pass(outcome)
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

        # Layer 5 ensemble-specific gates. These fire in addition to the
        # generic l4_rubric_threshold above so operators can distinguish
        # ensemble-driven rejections from single-judge rejections.
        layer5 = result.layer5_results
        if layer5 is not None and layer5.all_judges_failed:
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l5_ensemble_infrastructure_failure",
                    action=EnforcementAction.WARN,
                    scope=EnforcementScope.TASK,
                    severity="warn",
                    message=(
                        f"Task {task.id} ensemble judges all failed; "
                        f"score degraded but not a content signal."
                    ),
                    task_id=task.id,
                ),
                task_id=task.id,
            )
        if (
            layer5 is not None
            and layer5.tier1_vetoed
            and not result.passed
            and self.profile != PipelineProfile.LIGHT
        ):
            # Disagreement across judges is ambiguous evidence, not a
            # definitive rejection. Escalate for human review regardless of
            # profile (DEGRADE would hide the signal on STANDARD profile).
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l5_ensemble_dissenter_veto",
                    action=EnforcementAction.ESCALATE,
                    scope=EnforcementScope.TASK,
                    severity="error",
                    message=(
                        f"Task {task.id} failed Tier 1 dissenter-veto from ensemble judges "
                        f"({len(layer5.veto_events)} dimension(s))."
                    ),
                    task_id=task.id,
                ),
                task_id=task.id,
            )

        # Reduced-panel warning: some judges failed but aggregation still
        # produced a score. Operators need to know the ensemble degraded to
        # fewer judges than designed; a score from N-1 judges carries less
        # cross-model signal than a score from the full panel.
        if layer5 is not None and not layer5.all_judges_failed and layer5.failed_judge_ids:
            self.apply_flag(
                state,
                QualityFlag(
                    gate="l5_ensemble_degraded_panel",
                    action=EnforcementAction.WARN,
                    scope=EnforcementScope.TASK,
                    severity="warn",
                    message=(
                        f"Task {task.id} ensemble ran with a reduced panel: "
                        f"{len(layer5.failed_judge_ids)} of {len(layer5.judges_used)} "
                        f"judge(s) failed ({sorted(layer5.failed_judge_ids)})."
                    ),
                    task_id=task.id,
                ),
                task_id=task.id,
            )

        # Low cross-judge agreement is the most valuable signal an ensemble
        # produces. Surface it whenever judges spread enough to keep most
        # dimensions above the 10-point concordance threshold but still
        # disagreed on majority of the rubric. Tier 1 veto already covers
        # the hard failure case; this gate catches the quieter "judges
        # disagreed a lot but no single dimension crossed a floor" path.
        low_agreement_gate = self._low_agreement_gate(layer5, task_id=task.id)
        if low_agreement_gate is not None:
            self.apply_flag(state, low_agreement_gate, task_id=task.id)

        return outcome

    def _low_agreement_gate(
        self,
        layer5: Layer5Result | None,
        *,
        task_id: str,
    ) -> QualityFlag | None:
        """Return a low-agreement flag when judges disagreed enough to warn."""
        if layer5 is None:
            return None
        if layer5.tier1_vetoed or layer5.all_judges_failed:
            return None
        if len(layer5.judges_used) < 2:
            # Agreement is trivially 1.0 with a single judge; nothing to warn.
            return None
        if layer5.agreement_level >= self.low_agreement_threshold:
            return None
        if self.profile == PipelineProfile.LIGHT:
            return None
        action = (
            EnforcementAction.ESCALATE
            if self.profile == PipelineProfile.DEEP
            else EnforcementAction.WARN
        )
        return QualityFlag(
            gate="l5_low_agreement",
            action=action,
            scope=EnforcementScope.TASK,
            severity="warn" if action == EnforcementAction.WARN else "error",
            message=(
                f"Task {task_id} ensemble agreement_level={layer5.agreement_level:.2f} "
                f"is below {self.low_agreement_threshold:.2f}; "
                f"judges disagreed substantially across dimensions."
            ),
            task_id=task_id,
        )

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
