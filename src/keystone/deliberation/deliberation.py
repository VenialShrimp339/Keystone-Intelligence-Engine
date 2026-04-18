"""Main Deliberation orchestrator (L1.5). Satisfies DeliberationContract.

Two-phase deliberation:
Phase 1: Independent parallel analysis (3-5 analysts, no communication)
Phase 2: Structured aggregation + WWHTB + gap detection + confidence map
         + HITL Gate 2 (conditional)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Callable

logger = logging.getLogger(__name__)

from keystone.deliberation.aggregator import Aggregator
from keystone.deliberation.analyst import Analyst, AnalystOutput, extract_claims
from keystone.deliberation.confidence_builder import build_confidence_map
from keystone.deliberation.gap_detector import detect_gaps
from keystone.deliberation.wwhtb import run_wwhtb
from keystone.evaluator.retry import LLMCallable
from keystone.events import (
    AggregationComplete,
    AnalystSpawned,
    AnyPipelineEvent,
    ConfidenceMapProduced,
    IndependentAnalysisComplete,
)
from keystone.governance.policy import ProfileExecutionPolicy
from keystone.models.agents import DeliberationAnalystType
from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.research import StructuredFinding
from keystone.models.research import PipelineProfile
from keystone.models.tasks import ModelTier

DEFAULT_ANALYST_TYPES = [
    DeliberationAnalystType.ACH,
    DeliberationAnalystType.QUANTITATIVE,
    DeliberationAnalystType.ADVERSARIAL,
    DeliberationAnalystType.HISTORICAL_ANALOGY,
]


class Deliberation:
    """L1.5 Deliberation orchestrator.

    Implements DeliberationContract Protocol.

    Usage:
        delib = Deliberation(analyst_llm=llm, judge_llm=judge)
        async for event in delib.deliberate(manifest, findings, eid, cid):
            pass
        cm = await delib.get_confidence_map()
    """

    def __init__(
        self,
        analyst_llm: LLMCallable,
        judge_llm: LLMCallable | None = None,
        wwhtb_llm: LLMCallable | None = None,
        analyst_types: list[DeliberationAnalystType] | None = None,
        db_session_factory: Callable | None = None,
        effective_pipeline_profile: PipelineProfile = PipelineProfile.STANDARD,
    ) -> None:
        self._analyst_llm = analyst_llm
        self._judge_llm = judge_llm or analyst_llm
        self._wwhtb_llm = wwhtb_llm or analyst_llm
        self._analyst_types = analyst_types or list(DEFAULT_ANALYST_TYPES)
        self._db_session_factory = db_session_factory
        self._effective_pipeline_profile = effective_pipeline_profile
        self._confidence_map: ConfidenceMap | None = None

    async def deliberate(
        self,
        manifest: CitationManifest,
        findings: list[StructuredFinding],
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run two-phase deliberation.

        Phase 1: Independent parallel analysis.
        Phase 2: Aggregation, WWHTB, gap detection, confidence map, HITL Gate 2.
        """
        claims = extract_claims(findings)

        # --- Phase 1: Spawn and run independent analysts ---
        analysts: list[Analyst] = []
        for at in self._analyst_types:
            analyst = Analyst(llm=self._analyst_llm, analyst_type=at)
            analysts.append(analyst)
            yield AnalystSpawned(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                analyst_id=analyst.analyst_id,
                analyst_type=at.value,
                model_tier=ModelTier.STANDARD.value,
            )

        # Run all analysts in parallel (no inter-agent communication).
        # return_exceptions=True prevents one analyst crash from killing the rest.
        raw_results: list[AnalystOutput | BaseException] = await asyncio.gather(
            *(a.analyze(claims) for a in analysts),
            return_exceptions=True,
        )

        analyst_outputs: list[AnalystOutput] = []
        for analyst, result in zip(analysts, raw_results):
            if isinstance(result, BaseException):
                logger.warning(
                    "Analyst %s (%s) failed and will be excluded: %s",
                    analyst.analyst_id,
                    analyst.analyst_type.value,
                    result,
                )
            else:
                analyst_outputs.append(result)

        for output in analyst_outputs:
            yield IndependentAnalysisComplete(
                event_id=_uid(),
                engagement_id=engagement_id,
                client_id=client_id,
                analyst_id=output.analyst_id,
                analyst_type=output.analyst_type,
                claim_count=len(output.scored_claims),
            )

        # --- Phase 2: Aggregation ---
        aggregator = Aggregator(judge_llm=self._judge_llm)
        aggregated = await aggregator.aggregate(analyst_outputs, claims, manifest)

        wwhtb_results = await run_wwhtb(self._wwhtb_llm, aggregated)

        gap_report = detect_gaps(findings, aggregated)

        convergent = sum(1 for c in aggregated if c.agreement_ratio > 0.6)
        disagreements = sum(1 for c in aggregated if c.agreement_ratio < 0.5)
        blind_spots = len(gap_report.gaps)

        yield AggregationComplete(
            event_id=_uid(),
            engagement_id=engagement_id,
            client_id=client_id,
            convergent_findings=convergent,
            genuine_disagreements=disagreements,
            blind_spots=blind_spots,
        )

        # Build confidence map
        confidence_map = build_confidence_map(
            aggregated_claims=aggregated,
            wwhtb_results=wwhtb_results,
            gap_report=gap_report,
            engagement_id=engagement_id,
            client_id=client_id,
        )
        self._confidence_map = confidence_map

        yield ConfidenceMapProduced(
            event_id=_uid(),
            engagement_id=engagement_id,
            client_id=client_id,
            total_claims=confidence_map.total_claims,
            tiers_populated=confidence_map.tiers_populated,
            gaps_count=len(confidence_map.gaps_identified),
        )

        # --- HITL Gate 2 (conditional on db_session_factory) ---
        if self._db_session_factory:
            await self._trigger_hitl_gate(confidence_map, engagement_id, client_id)

    async def get_confidence_map(self) -> ConfidenceMap:
        """Return the produced confidence map."""
        if self._confidence_map is None:
            msg = "deliberate() must be called before get_confidence_map()"
            raise RuntimeError(msg)
        return self._confidence_map

    async def _trigger_hitl_gate(
        self,
        confidence_map: ConfidenceMap,
        engagement_id: str,
        client_id: str,
    ) -> None:
        """Trigger HITL Gate 2 (post-deliberation review)."""
        if not ProfileExecutionPolicy(self._effective_pipeline_profile).should_run_hitl_gate():
            logger.info("Skipping HITL Gate 2 for LIGHT profile")
            return

        from keystone.hitl.gate import (
            build_deliberation_gate_items,
            create_and_wait_for_gate,
        )
        from keystone.hitl.schemas import GateStatus, GateType

        items = build_deliberation_gate_items(
            confidence_map=confidence_map.model_dump(),
        )
        async with self._db_session_factory() as session:
            resolution = await create_and_wait_for_gate(
                session=session,
                engagement_id=engagement_id,
                client_id=client_id,
                gate_type=GateType.POST_DELIBERATION,
                items=items,
            )
        if resolution.status == GateStatus.MODIFIED and not resolution.patch_applied:
            msg = "Modifications are not yet supported in this phase."
            raise RuntimeError(msg)


def _uid() -> str:
    return str(uuid.uuid4())
