"""Main Evaluator orchestrator (L4). Satisfies EvaluatorContract Protocol.

Five-layer evaluation stack:
  Layer 1: Deterministic verification (FActScore, numerical, URLs)
  Layer 2: Citation validation gate (any fabrication = rejection)
  Layer 3: Multi-rubric scoring (10 dimensions, geometric mean)
  Layer 5: Cross-model ensemble of Layer 3 with dissenter veto (optional)
  Layer 4: Process trajectory (research-process quality; optional)

Layer 5 wraps Layer 3 when ``ensemble_llms`` is supplied: multiple judges
run independently, scores aggregate by median, and any Tier 1 below-floor
score from any judge triggers a dissenter veto. Without ``ensemble_llms``
the evaluator runs the single-judge Layer 3 path.

Layer 4 runs only when a ProcessContext is provided to ``evaluate``. It
evaluates HOW the output was produced — Layers 1-3 can be fooled by
plausible prose from a narrow research process. When Layer 4 runs, the
overall score is the weighted geometric mean of L3 and L4 (default
80/20), so lazy research lowers the composite without erasing it.
"""

from __future__ import annotations

import math
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from keystone.evaluator.layer1_deterministic import Layer1Evaluator
from keystone.evaluator.layer2_citation_gate import DOIVerifier, Layer2CitationGate
from keystone.evaluator.layer3_rubric import _apply_dimension_emphasis
from keystone.evaluator.layer4_trajectory import Layer4Evaluator, ProcessContext
from keystone.evaluator.layer5_ensemble import EnsembleL3Evaluator
from keystone.evaluator.retry import LLMCallable
from keystone.evaluator.rubric_config import EvaluationProfile, get_profile_weights
from keystone.evaluator.three_pass import ThreePassEvaluator
from keystone.events import (
    AnyPipelineEvent,
    CitationGateResult,
    DeterministicCheckPassed,
    DissenterVetoTriggered,
    EnsembleEvaluationComplete,
    EnsembleJudgeScored,
    EvaluationComplete,
    ProcessTrajectoryScored,
    RubricDimensionScored,
)
from keystone.models.citations import CitationManifest
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    Layer4Result,
    Layer5Result,
    SprintContract,
)
from keystone.models.research import EngagementSpec
from keystone.models.tasks import ResearchTask

# EvaluationResult uses TYPE_CHECKING for datetime; rebuild for runtime use
EvaluationResult.model_rebuild()

# Default pass threshold on 0-100 scale
DEFAULT_PASS_THRESHOLD = 60.0

# Default weight ratio for composite = geometric_mean(L3, L4)
# L3 weight 0.8 keeps content the dominant signal; Layer 4 lowers the
# composite for narrow or lazy research but cannot lift a weak L3.
DEFAULT_LAYER3_WEIGHT = 0.8
_GEOMETRIC_MEAN_EPSILON = 0.01


class Evaluator:
    """L4 Evaluator: 4-layer quality gate.

    Implements EvaluatorContract Protocol.

    Usage:
        evaluator = Evaluator(llm=llm_client, profile=EvaluationProfile.DEFAULT)
        async for event in evaluator.evaluate(
            output_text, contract, task, manifest, spec, process_context=ctx,
        ):
            # Handle events (log, store in trajectory)
            pass
        result = await evaluator.get_result()

    Layer 4 runs only when ``process_context`` is supplied and Layers 1-3
    have produced content scores. A failure in Layers 1-3 never runs
    Layer 4; Layer 4 cannot lift such a failure.
    """

    def __init__(
        self,
        llm: LLMCallable,
        profile: EvaluationProfile = EvaluationProfile.DEFAULT,
        doi_verifier: DOIVerifier | None = None,
        intensity: EvaluationIntensity = EvaluationIntensity.STANDARD,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
        layer3_weight: float = DEFAULT_LAYER3_WEIGHT,
        ensemble_llms: list[tuple[str, LLMCallable]] | None = None,
        extraction_llm: LLMCallable | None = None,
    ) -> None:
        if not 0.0 < layer3_weight <= 1.0:
            raise ValueError("layer3_weight must be in (0, 1]")
        self._llm = llm
        self._profile = profile
        self._weights = get_profile_weights(profile)
        self._intensity = intensity
        self._pass_threshold = pass_threshold
        self._layer3_weight = layer3_weight
        # Layer 1 handles fact decomposition + numerical extraction — work
        # that Sonnet (STANDARD) is fully capable of, reserving Opus
        # (FLAGSHIP) for Layer 3 rubric judgment. When callers do not
        # supply a dedicated extraction LLM we fall back to ``llm`` so
        # existing single-LLM tests keep working.
        self._extraction_llm = extraction_llm if extraction_llm is not None else llm
        self._layer1 = Layer1Evaluator(llm=self._extraction_llm)
        self._layer2 = Layer2CitationGate(doi_verifier=doi_verifier)
        self._three_pass = ThreePassEvaluator(llm=llm, profile=profile)
        self._layer4 = Layer4Evaluator(llm=llm)
        # Layer 5 is inert for LIGHT_TOUCH (Layer 3 is skipped) and when no
        # ensemble judges are provided. Otherwise construct an ensemble wrapper.
        self._ensemble: EnsembleL3Evaluator | None
        if ensemble_llms and intensity != EvaluationIntensity.LIGHT_TOUCH:
            self._ensemble = EnsembleL3Evaluator(judges=ensemble_llms, profile=profile)
        else:
            self._ensemble = None
        self._result: EvaluationResult | None = None

    async def evaluate(
        self,
        output_text: str,
        contract: SprintContract,
        task: ResearchTask,
        manifest: CitationManifest,
        spec: EngagementSpec,
        process_context: ProcessContext | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 3-layer evaluation stack (plus optional Layer 4).

        Yields events at each layer boundary. Implements early termination:
        - Layer 2 fabrication -> yield CitationGateResult(gate_passed=False), return
        - Tier 1 floor failure -> yield EvaluationComplete(passed=False), return

        When ``process_context`` is provided and Layers 1-3 have passed,
        Layer 4 evaluates the research trajectory and blends its score
        into the overall composite (L3 weighted ``layer3_weight``, L4
        weighted ``1 - layer3_weight`` via geometric mean).
        """
        eid = contract.engagement_id
        cid = contract.client_id

        # --- Layer 1: Deterministic verification ---
        try:
            layer1_result = await self._layer1.evaluate(output_text, manifest)
        except Exception as exc:
            import logging as _log

            _log.getLogger(__name__).warning(
                "Layer 1 evaluation failed for task %s, marking infrastructure "
                "failure on result: %s",
                task.id,
                exc,
            )
            # infrastructure_failure=True distinguishes this skipped-run case
            # from a real zero-facts result (0/0 counts are otherwise ambiguous).
            layer1_result = Layer1Result(
                facts_verified=0,
                facts_failed=0,
                numerical_inconsistencies=[],
                dead_urls=[],
                infrastructure_failure=True,
            )
        yield DeterministicCheckPassed(
            event_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            layer="L4",
            facts_verified=layer1_result.facts_verified,
            facts_failed=layer1_result.facts_failed,
            numerical_issues=len(layer1_result.numerical_inconsistencies),
        )

        # --- Layer 2: Citation gate ---
        layer2_result = await self._layer2.evaluate(manifest)
        yield CitationGateResult(
            event_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            layer="L4",
            citations_checked=layer2_result.citations_checked,
            citations_verified=layer2_result.citations_verified,
            fabrications_found=len(layer2_result.citations_fabricated),
            gate_passed=layer2_result.gate_passed,
        )
        if not layer2_result.gate_passed:
            self._result = self._build_failed_result(
                task, eid, cid, layer1_result, layer2_result, reason="fabrication"
            )
            yield EvaluationComplete(
                event_id=_uid(),
                engagement_id=eid,
                client_id=cid,
                layer="L4",
                task_id=task.id,
                passed=False,
                overall_score=0.0,
                layer2_gate_passed=False,
                feedback_length=len(self._result.feedback),
            )
            return

        # --- Layer 3: Rubric scoring (skipped for LIGHT_TOUCH) ---
        if self._intensity == EvaluationIntensity.LIGHT_TOUCH:
            self._result = self._build_light_result(task, eid, cid, layer1_result, layer2_result)
            yield EvaluationComplete(
                event_id=_uid(),
                engagement_id=eid,
                client_id=cid,
                layer="L4",
                task_id=task.id,
                passed=True,
                overall_score=0.0,
                layer2_gate_passed=True,
                feedback_length=len(self._result.feedback),
            )
            return

        layer5_result: Layer5Result | None = None
        if self._ensemble is not None:
            try:
                layer3_result, layer5_result = await self._ensemble.run(output_text, contract)
            except Exception as exc:
                import logging as _log

                _log.getLogger(__name__).warning(
                    "Layer 5 ensemble evaluation failed for task %s, marking "
                    "infrastructure failure on result: %s",
                    task.id,
                    exc,
                )
                # infrastructure_failure=True differentiates "rubric scoring
                # failed" from a legitimate 0/100 score. Downstream logic
                # that treats 0 as "content is terrible" must skip this path.
                layer3_result = Layer3Result(
                    dimension_scores=[],
                    weighted_total=0.0,
                    gestalt_adjustment=0.0,
                    final_score=0.0,
                    infrastructure_failure=True,
                )
                layer5_result = None
        else:
            try:
                layer3_result = await self._three_pass.run(output_text, contract)
            except Exception as exc:
                import logging as _log

                _log.getLogger(__name__).warning(
                    "Layer 3 evaluation failed for task %s, marking "
                    "infrastructure failure on result: %s",
                    task.id,
                    exc,
                )
                layer3_result = Layer3Result(
                    dimension_scores=[],
                    weighted_total=0.0,
                    gestalt_adjustment=0.0,
                    final_score=0.0,
                    infrastructure_failure=True,
                )

        # Emit L5 per-judge + veto events before the aggregated L4 events so
        # consumers see judge detail first, then the aggregated picture.
        if layer5_result is not None:
            for js in layer5_result.judge_scores:
                judge_l3 = js.layer3_result
                yield EnsembleJudgeScored(
                    event_id=_uid(),
                    engagement_id=eid,
                    client_id=cid,
                    task_id=task.id,
                    judge_id=js.judge_id,
                    judge_tier=js.judge_tier,
                    judge_succeeded=js.succeeded,
                    judge_final_score=judge_l3.final_score if judge_l3 is not None else 0.0,
                    judge_weighted_total=judge_l3.weighted_total if judge_l3 is not None else 0.0,
                    judge_gestalt=judge_l3.gestalt_adjustment if judge_l3 is not None else 0.0,
                    error=js.error,
                )
            for ve in layer5_result.veto_events:
                yield DissenterVetoTriggered(
                    event_id=_uid(),
                    engagement_id=eid,
                    client_id=cid,
                    task_id=task.id,
                    dimension=ve.dimension.value,
                    floor_threshold=ve.floor_threshold,
                    min_judge_score=ve.min_score,
                    dissenting_judge_ids=list(ve.dissenting_judge_ids),
                    judge_count=len(layer5_result.judge_scores),
                )

        event_weights = _apply_dimension_emphasis(
            self._weights,
            contract.dimension_emphasis,
        )
        for score in layer3_result.dimension_scores:
            yield RubricDimensionScored(
                event_id=_uid(),
                engagement_id=eid,
                client_id=cid,
                layer="L4",
                dimension=score.dimension.value,
                score=score.score,
                weight=event_weights.get(score.dimension, 0.0),
            )

        if layer5_result is not None:
            yield EnsembleEvaluationComplete(
                event_id=_uid(),
                engagement_id=eid,
                client_id=cid,
                task_id=task.id,
                n_judges=len(layer5_result.judges_used),
                n_judges_succeeded=sum(1 for js in layer5_result.judge_scores if js.succeeded),
                aggregated_score=layer5_result.ensemble_final_score,
                agreement_level=layer5_result.agreement_level,
                veto_count=len(layer5_result.veto_events),
                tier1_vetoed=layer5_result.tier1_vetoed,
            )

        # --- Layer 4: Process trajectory (optional, only when context provided) ---
        layer4_result: Layer4Result | None = None
        composite_score = layer3_result.final_score
        if process_context is not None and layer3_result.dimension_scores:
            try:
                layer4_result = await self._layer4.evaluate(process_context, manifest)
            except Exception as exc:
                import logging as _log

                _log.getLogger(__name__).warning(
                    "Layer 4 evaluation failed for task %s, skipping process score: %s",
                    task.id,
                    exc,
                )
                layer4_result = None

            if layer4_result is not None:
                composite_score = _blend_layer3_layer4(
                    layer3_result.final_score,
                    layer4_result.process_quality_score,
                    self._layer3_weight,
                )
                yield ProcessTrajectoryScored(
                    event_id=_uid(),
                    engagement_id=eid,
                    client_id=cid,
                    layer="L4",
                    task_id=task.id,
                    process_quality_score=layer4_result.process_quality_score,
                    qualitative_score=layer4_result.qualitative_score,
                    source_count=layer4_result.source_count,
                    unique_domains=layer4_result.unique_domains,
                    round_count=layer4_result.round_count,
                    tool_utilization=layer4_result.tool_utilization,
                    flag_count=len(layer4_result.process_flags),
                )

        # --- Determine pass/fail ---
        passed = composite_score >= self._pass_threshold
        self._result = self._build_result(
            task,
            eid,
            cid,
            layer1_result,
            layer2_result,
            layer3_result,
            layer4_result,
            layer5_result,
            composite_score,
            passed,
        )
        yield EvaluationComplete(
            event_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            layer="L4",
            task_id=task.id,
            passed=passed,
            overall_score=composite_score,
            layer2_gate_passed=True,
            feedback_length=len(self._result.feedback),
        )

    async def get_result(self) -> EvaluationResult:
        if self._result is None:
            msg = "evaluate() must be called before get_result()"
            raise RuntimeError(msg)
        return self._result

    # ------------------------------------------------------------------
    # Result builders
    # ------------------------------------------------------------------

    def _build_failed_result(
        self,
        task: ResearchTask,
        eid: str,
        cid: str,
        l1: Layer1Result,
        l2: Layer2Result,
        *,
        reason: str,
    ) -> EvaluationResult:
        if reason == "fabrication":
            fab_ids = ", ".join(l2.citations_fabricated)
            feedback = (
                f"REJECTED: {len(l2.citations_fabricated)} fabricated citation(s) detected "
                f"({fab_ids}). Layer 3 rubric scoring was skipped. "
                f"Remove or replace fabricated citations before resubmission."
            )
        else:
            feedback = f"REJECTED: {reason}"

        return EvaluationResult(
            evaluation_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            task_id=task.id,
            evaluated_at=datetime.now(UTC),
            intensity=self._intensity,
            passed=False,
            overall_score=0.0,
            layer1_results=l1,
            layer2_results=l2,
            layer3_results=None,
            feedback=feedback,
        )

    def _build_light_result(
        self,
        task: ResearchTask,
        eid: str,
        cid: str,
        l1: Layer1Result,
        l2: Layer2Result,
    ) -> EvaluationResult:
        issues = []
        if l1.facts_failed > 0:
            issues.append(f"{l1.facts_failed} unverified facts")
        if l1.numerical_inconsistencies:
            issues.append(f"{len(l1.numerical_inconsistencies)} numerical inconsistencies")
        if l1.dead_urls:
            issues.append(f"{len(l1.dead_urls)} dead URLs")
        feedback = "LIGHT_TOUCH evaluation: Layers 1-2 passed. " + (
            f"Issues noted: {'; '.join(issues)}." if issues else "No issues found."
        )

        return EvaluationResult(
            evaluation_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            task_id=task.id,
            evaluated_at=datetime.now(UTC),
            intensity=self._intensity,
            passed=True,
            overall_score=0.0,
            layer1_results=l1,
            layer2_results=l2,
            layer3_results=None,
            feedback=feedback,
        )

    def _build_result(
        self,
        task: ResearchTask,
        eid: str,
        cid: str,
        l1: Layer1Result,
        l2: Layer2Result,
        l3: Layer3Result,
        l4: Layer4Result | None,
        l5: Layer5Result | None,
        composite_score: float,
        passed: bool,
    ) -> EvaluationResult:
        feedback_parts = []
        verdict = "PASSED" if passed else "FAILED"
        if l4 is not None:
            feedback_parts.append(
                f"{verdict} with composite {composite_score:.1f}/100 "
                f"(L3 content {l3.final_score:.1f}, L4 process {l4.process_quality_score:.1f}, "
                f"threshold: {self._pass_threshold})."
            )
        else:
            feedback_parts.append(
                f"{verdict} with score {l3.final_score:.1f}/100 (threshold: {self._pass_threshold})."
            )

        if l5 is not None:
            if l5.all_judges_failed:
                feedback_parts.append(
                    f"Ensemble infrastructure failure: all {len(l5.judges_used)} "
                    f"judge(s) raised. Score degraded to zero; not a content signal."
                )
            elif l5.tier1_vetoed:
                vetoed = ", ".join(ve.dimension.value for ve in l5.veto_events)
                feedback_parts.append(
                    f"Dissenter veto triggered on Tier 1 dimension(s): {vetoed}. "
                    f"Agreement level {l5.agreement_level:.2f}."
                )
            else:
                feedback_parts.append(
                    f"Ensemble of {len(l5.judges_used)} judge(s) aggregated; "
                    f"agreement level {l5.agreement_level:.2f}."
                )

        # Per-dimension feedback
        strengths = []
        weaknesses = []
        for ds in l3.dimension_scores:
            if ds.score >= 70:
                strengths.append(f"{ds.dimension.value}: {ds.score:.0f}")
            elif ds.score < 50:
                weaknesses.append(f"{ds.dimension.value}: {ds.score:.0f} - {ds.feedback}")

        if strengths:
            feedback_parts.append(f"Strengths: {', '.join(strengths)}.")
        if weaknesses:
            feedback_parts.append(f"Weaknesses: {'; '.join(weaknesses)}.")

        if l1.numerical_inconsistencies:
            feedback_parts.append(f"Numerical issues: {'; '.join(l1.numerical_inconsistencies)}.")
        if l3.gestalt_adjustment != 0:
            feedback_parts.append(f"Gestalt adjustment: {l3.gestalt_adjustment:+.1f}.")

        if l4 is not None and l4.process_flags:
            feedback_parts.append(f"Process flags: {', '.join(l4.process_flags)}.")
        if l4 is not None and l4.missed_inquiries:
            feedback_parts.append(f"Missed inquiries: {'; '.join(l4.missed_inquiries)}.")

        return EvaluationResult(
            evaluation_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            task_id=task.id,
            evaluated_at=datetime.now(UTC),
            intensity=self._intensity,
            passed=passed,
            overall_score=composite_score,
            layer1_results=l1,
            layer2_results=l2,
            layer3_results=l3,
            layer4_results=l4,
            layer5_results=l5,
            feedback=" ".join(feedback_parts),
        )


def _blend_layer3_layer4(
    layer3_score: float,
    layer4_score: float,
    layer3_weight: float,
) -> float:
    """Weighted geometric mean of L3 and L4 scores, clamped to [0, 100].

    Geometric mean prevents a high L3 from completely masking a low L4:
    a score near zero on either side drags the composite down. Floors
    both sides at ``_GEOMETRIC_MEAN_EPSILON`` to avoid log(0).
    """
    layer4_weight = 1.0 - layer3_weight
    l3 = max(layer3_score, _GEOMETRIC_MEAN_EPSILON)
    l4 = max(layer4_score, _GEOMETRIC_MEAN_EPSILON)
    blended = math.exp(layer3_weight * math.log(l3) + layer4_weight * math.log(l4))
    return round(max(0.0, min(100.0, blended)), 2)


def _uid() -> str:
    return str(uuid.uuid4())
