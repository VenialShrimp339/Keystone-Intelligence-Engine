"""Main Evaluator orchestrator (L4). Satisfies EvaluatorContract Protocol.

Three-layer evaluation stack (Phase 1):
  Layer 1: Deterministic verification (FActScore, numerical, URLs)
  Layer 2: Citation validation gate (any fabrication = rejection)
  Layer 3: Multi-rubric scoring (10 dimensions, geometric mean)

Layers 4-5 (process trajectory, diverse judge ensemble) are Phase 2.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from keystone.evaluator.layer1_deterministic import Layer1Evaluator
from keystone.evaluator.layer2_citation_gate import DOIVerifier, Layer2CitationGate
from keystone.evaluator.retry import LLMCallable
from keystone.evaluator.rubric_config import EvaluationProfile, get_profile_weights
from keystone.evaluator.three_pass import ThreePassEvaluator
from keystone.events import (
    AnyPipelineEvent,
    CitationGateResult,
    DeterministicCheckPassed,
    EvaluationComplete,
    RubricDimensionScored,
)
from keystone.models.citations import CitationManifest
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    SprintContract,
)
from keystone.models.research import EngagementSpec
from keystone.models.tasks import ResearchTask

# EvaluationResult uses TYPE_CHECKING for datetime; rebuild for runtime use
EvaluationResult.model_rebuild()

# Default pass threshold on 0-100 scale
DEFAULT_PASS_THRESHOLD = 60.0


class Evaluator:
    """L4 Evaluator: 3-layer quality gate (Phase 1).

    Implements EvaluatorContract Protocol.

    Usage:
        evaluator = Evaluator(llm=llm_client, profile=EvaluationProfile.DEFAULT)
        async for event in evaluator.evaluate(output_text, contract, task, manifest, spec):
            # Handle events (log, store in trajectory)
            pass
        result = await evaluator.get_result()
    """

    def __init__(
        self,
        llm: LLMCallable,
        profile: EvaluationProfile = EvaluationProfile.DEFAULT,
        doi_verifier: DOIVerifier | None = None,
        intensity: EvaluationIntensity = EvaluationIntensity.STANDARD,
        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
    ) -> None:
        self._llm = llm
        self._profile = profile
        self._weights = get_profile_weights(profile)
        self._intensity = intensity
        self._pass_threshold = pass_threshold
        self._layer1 = Layer1Evaluator(llm=llm)
        self._layer2 = Layer2CitationGate(doi_verifier=doi_verifier)
        self._three_pass = ThreePassEvaluator(llm=llm, profile=profile)
        self._result: EvaluationResult | None = None

    async def evaluate(
        self,
        output_text: str,
        contract: SprintContract,
        task: ResearchTask,
        manifest: CitationManifest,
        spec: EngagementSpec,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 3-layer evaluation stack.

        Yields events at each layer boundary. Implements early termination:
        - Layer 2 fabrication -> yield CitationGateResult(gate_passed=False), return
        - Tier 1 floor failure -> yield EvaluationComplete(passed=False), return
        """
        eid = contract.engagement_id
        cid = contract.client_id

        # --- Layer 1: Deterministic verification ---
        layer1_result = await self._layer1.evaluate(output_text, manifest)
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
            self._result = self._build_light_result(
                task, eid, cid, layer1_result, layer2_result
            )
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

        layer3_result = await self._three_pass.run(output_text, contract)
        for score in layer3_result.dimension_scores:
            yield RubricDimensionScored(
                event_id=_uid(),
                engagement_id=eid,
                client_id=cid,
                layer="L4",
                dimension=score.dimension.value,
                score=score.score,
                weight=self._weights.get(score.dimension, 0.0),
            )

        # --- Determine pass/fail ---
        passed = layer3_result.final_score >= self._pass_threshold
        self._result = self._build_result(
            task, eid, cid,
            layer1_result, layer2_result, layer3_result, passed
        )
        yield EvaluationComplete(
            event_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            layer="L4",
            task_id=task.id,
            passed=passed,
            overall_score=layer3_result.final_score,
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
            issues.append(
                f"{len(l1.numerical_inconsistencies)} numerical inconsistencies"
            )
        if l1.dead_urls:
            issues.append(f"{len(l1.dead_urls)} dead URLs")
        feedback = (
            "LIGHT_TOUCH evaluation: Layers 1-2 passed. "
            + (f"Issues noted: {'; '.join(issues)}." if issues else "No issues found.")
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
        passed: bool,
    ) -> EvaluationResult:
        feedback_parts = []
        if passed:
            feedback_parts.append(
                f"PASSED with score {l3.final_score:.1f}/100 "
                f"(threshold: {self._pass_threshold})."
            )
        else:
            feedback_parts.append(
                f"FAILED with score {l3.final_score:.1f}/100 "
                f"(threshold: {self._pass_threshold})."
            )

        # Per-dimension feedback
        strengths = []
        weaknesses = []
        for ds in l3.dimension_scores:
            if ds.score >= 70:
                strengths.append(f"{ds.dimension.value}: {ds.score:.0f}")
            elif ds.score < 50:
                weaknesses.append(
                    f"{ds.dimension.value}: {ds.score:.0f} - {ds.feedback}"
                )

        if strengths:
            feedback_parts.append(f"Strengths: {', '.join(strengths)}.")
        if weaknesses:
            feedback_parts.append(f"Weaknesses: {'; '.join(weaknesses)}.")

        if l1.numerical_inconsistencies:
            feedback_parts.append(
                f"Numerical issues: {'; '.join(l1.numerical_inconsistencies)}."
            )
        if l3.gestalt_adjustment != 0:
            feedback_parts.append(
                f"Gestalt adjustment: {l3.gestalt_adjustment:+.1f}."
            )

        return EvaluationResult(
            evaluation_id=_uid(),
            engagement_id=eid,
            client_id=cid,
            task_id=task.id,
            evaluated_at=datetime.now(UTC),
            intensity=self._intensity,
            passed=passed,
            overall_score=l3.final_score,
            layer1_results=l1,
            layer2_results=l2,
            layer3_results=l3,
            feedback=" ".join(feedback_parts),
        )


def _uid() -> str:
    return str(uuid.uuid4())
