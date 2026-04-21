"""Claim-level SELECTION aggregator for L1.5 Deliberation.

For each disputed finding, a judge LLM selects the best-supported claim
(81% win rate vs. 51.2% for synthesis-based blending per the spec).
Post-selection consistency check ensures selected claims don't contradict.

Uses LLMCallable at FLAGSHIP tier for the judge.
"""

from __future__ import annotations

import logging
import statistics
import uuid

from pydantic import BaseModel, Field

from keystone.deliberation._prompts import load_prompt as load_deliberation_prompt
from keystone.deliberation.analyst import AnalystOutput, InputClaim
from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.citations import CitationManifest

logger = logging.getLogger(__name__)

# Variance threshold above which analyst disagreement triggers judge selection.
# 0.04 corresponds to stddev ~0.2 (a 20+ point spread between analysts). Kept
# as a module-level constant so legacy callers keep working; the
# ``Aggregator`` constructor accepts an override sourced from
# :class:`PipelineConfig.dispute_variance_threshold`.
DISPUTE_VARIANCE_THRESHOLD = 0.04


class AggregatedClaim(BaseModel):
    """A claim after aggregation with full agreement tracking."""

    claim_text: str
    index: int
    agreement_ratio: float = Field(ge=0.0, le=1.0)
    agreeing_analysts: list[str]
    dissenting_analysts: list[str]
    total_analysts: int
    mean_confidence: float = Field(ge=0.0, le=1.0)
    source_count: int = Field(ge=0)
    corroboration_count: int = Field(ge=0)
    citation_ids: list[str]
    analyst_scores: dict[str, float]
    analyst_reasoning: dict[str, str]
    selected_from: str | None = None
    selection_reasoning: str | None = None
    consistency_passed: bool = True
    aggregated_claim_id: str | None = Field(
        default=None, description="Unique ID for this aggregated claim"
    )
    task_ids: list[str] = Field(default_factory=list, description="Source task IDs for this claim")


class Aggregator:
    """Claim-level SELECTION aggregator.

    Uses a judge LLM (flagship tier) to resolve disputes where analysts
    disagree significantly. Does NOT blend or synthesize -- picks the
    best-supported analyst assessment.
    """

    def __init__(
        self,
        judge_llm: LLMCallable,
        *,
        dispute_variance_threshold: float = DISPUTE_VARIANCE_THRESHOLD,
    ) -> None:
        self._judge = judge_llm
        self._dispute_variance_threshold = dispute_variance_threshold

    async def aggregate(
        self,
        analyst_outputs: list[AnalystOutput],
        claims: list[InputClaim],
        manifest: CitationManifest | None = None,
    ) -> list[AggregatedClaim]:
        """Aggregate analyst assessments into final claims."""
        if not claims:
            return []

        source_to_canonical, agent_ids_by_canonical = self._build_manifest_provenance(manifest)

        aggregated: list[AggregatedClaim] = []
        for claim in claims:
            scores: dict[str, float] = {}
            reasoning: dict[str, str] = {}
            source_counts: dict[str, int] = {}

            (
                citation_ids,
                task_ids,
                corroboration_count,
            ) = self._derive_claim_provenance(
                claim,
                source_to_canonical,
                agent_ids_by_canonical,
            )

            for output in analyst_outputs:
                for sc in output.scored_claims:
                    if sc.index == claim.index:
                        scores[output.analyst_type] = sc.analyst_confidence
                        reasoning[output.analyst_type] = sc.reasoning
                        source_counts[output.analyst_type] = sc.source_count

            if not scores:
                aggregated.append(
                    self._build_unscored(
                        claim,
                        citation_ids,
                        task_ids,
                        corroboration_count,
                    )
                )
                continue

            confidences = list(scores.values())
            variance = statistics.variance(confidences) if len(confidences) > 1 else 0.0

            # Judge-based selection for disputed claims
            if variance > self._dispute_variance_threshold and len(confidences) >= 2:
                selected_type, sel_reasoning = await self._judge_select(claim, scores, reasoning)
                if selected_type is not None and selected_type in scores:
                    mean_conf = scores[selected_type]
                else:
                    mean_conf = statistics.median(confidences)
            else:
                selected_type = None
                sel_reasoning = None
                mean_conf = statistics.mean(confidences)

            agreeing = [at for at, c in scores.items() if c >= 0.5]
            dissenting = [at for at, c in scores.items() if c < 0.5]
            agreement_ratio = len(agreeing) / len(scores) if scores else 0.0

            aggregated.append(
                AggregatedClaim(
                    claim_text=claim.text,
                    index=claim.index,
                    agreement_ratio=agreement_ratio,
                    agreeing_analysts=agreeing,
                    dissenting_analysts=dissenting,
                    total_analysts=len(scores),
                    mean_confidence=mean_conf,
                    source_count=max(source_counts.values())
                    if source_counts
                    else len(citation_ids),
                    corroboration_count=corroboration_count,
                    citation_ids=citation_ids,
                    analyst_scores=scores,
                    analyst_reasoning=reasoning,
                    selected_from=selected_type,
                    selection_reasoning=sel_reasoning,
                    aggregated_claim_id=f"AGG-{uuid.uuid4().hex[:12]}",
                    task_ids=task_ids,
                )
            )

        # Post-selection consistency check
        await self._consistency_check(aggregated)
        return aggregated

    @staticmethod
    def _build_manifest_provenance(
        manifest: CitationManifest | None,
    ) -> tuple[dict[str, str], dict[str, list[str]]]:
        """Index canonical citation provenance from the manifest.

        Returns:
            source_instance_id -> canonical_citation_id
            canonical_citation_id -> agent_ids[]
        """
        if manifest is None:
            return {}, {}

        source_to_canonical: dict[str, str] = {}
        agent_ids_by_canonical: dict[str, list[str]] = {}

        for alias in manifest.aliases:
            source_to_canonical[alias.source_instance_id] = alias.canonical_citation_id

            if alias.agent_id:
                agent_ids = agent_ids_by_canonical.setdefault(alias.canonical_citation_id, [])
                if alias.agent_id not in agent_ids:
                    agent_ids.append(alias.agent_id)

        for citation in manifest.citations:
            agent_ids = agent_ids_by_canonical.setdefault(citation.citation_id, [])
            for agent_id in citation.found_by_agents:
                if agent_id and agent_id not in agent_ids:
                    agent_ids.append(agent_id)

        return source_to_canonical, agent_ids_by_canonical

    @staticmethod
    def _derive_claim_provenance(
        claim: InputClaim,
        source_to_canonical: dict[str, str],
        agent_ids_by_canonical: dict[str, list[str]],
    ) -> tuple[list[str], list[str], int]:
        """Resolve canonical citations plus manifest-backed agent corroboration.

        Claim/task provenance stays anchored to the originating claim. Shared
        canonical citation history is allowed to increase corroboration_count,
        but it must never widen the claim's own task_ids for L4 gating.
        """
        citation_ids: list[str] = []
        seen_citations: set[str] = set()
        for citation_id in claim.citation_ids:
            canonical_id = source_to_canonical.get(citation_id, citation_id)
            if canonical_id not in seen_citations:
                seen_citations.add(canonical_id)
                citation_ids.append(canonical_id)

        task_ids = [claim.task_id] if claim.task_id else []
        agent_ids: list[str] = []
        seen_agents: set[str] = set()

        for citation_id in citation_ids:
            for agent_id in agent_ids_by_canonical.get(citation_id, []):
                if agent_id and agent_id not in seen_agents:
                    seen_agents.add(agent_id)
                    agent_ids.append(agent_id)

        if not agent_ids and claim.agent_id:
            agent_ids = [claim.agent_id]

        return citation_ids, task_ids, len(agent_ids)

    async def _judge_select(
        self,
        claim: InputClaim,
        scores: dict[str, float],
        reasoning: dict[str, str],
    ) -> tuple[str, str]:
        """Judge selects the best-supported analyst assessment."""
        assessments = "\n".join(
            f"- {at}: confidence={scores[at]:.2f}, reasoning: {reasoning.get(at, 'N/A')}"
            for at in sorted(scores.keys())
        )
        prompt = load_deliberation_prompt(
            "judge",
            claim_text=claim.text,
            claim_evidence=claim.evidence,
            assessments=assessments,
        )
        response = await retry_llm_call(self._judge, prompt, description="judge_selection")
        try:
            parsed = safe_llm_json(response, required_keys=("selected_analyst",))
            selected = parsed.get("selected_analyst", "")
            sel_reasoning = parsed.get("reasoning", "")
            if selected in scores:
                return selected, sel_reasoning
        except (ParseError, KeyError):
            logger.warning(
                "Judge select parse failed for claim %d, falling back to max confidence",
                claim.index,
            )

        # Fallback: median confidence, no selected analyst. Median is
        # conservative and mathematically neutral; max picks the most
        # aggressive analyst, which is the wrong default on parse failure.
        return None, "Fallback: judge parse failed, using median confidence"

    async def _consistency_check(self, claims: list[AggregatedClaim]) -> None:
        """Screen selected claims for incoherence."""
        high_conf = [c for c in claims if c.mean_confidence >= 0.6]
        if len(high_conf) < 2:
            return

        summaries = "\n".join(
            f"- [{c.index}] {c.claim_text} (confidence: {c.mean_confidence:.2f})"
            for c in high_conf[:10]
        )
        prompt = load_deliberation_prompt(
            "consistency_check",
            summaries=summaries,
        )
        response = await retry_llm_call(self._judge, prompt, description="consistency_check")
        try:
            parsed = safe_llm_json(response)
            contradictions = parsed.get("contradictions", [])
            claim_by_idx = {c.index: c for c in claims}
            for cont in contradictions:
                a_idx = cont.get("claim_a")
                b_idx = cont.get("claim_b")
                if a_idx in claim_by_idx:
                    claim_by_idx[a_idx].consistency_passed = False
                if b_idx in claim_by_idx:
                    claim_by_idx[b_idx].consistency_passed = False
        except (ParseError, KeyError):
            logger.warning(
                "Consistency check parse failed, all claims default to consistency_passed=True"
            )

    @staticmethod
    def _build_unscored(
        claim: InputClaim,
        citation_ids: list[str] | None = None,
        task_ids: list[str] | None = None,
        corroboration_count: int = 0,
    ) -> AggregatedClaim:
        return AggregatedClaim(
            claim_text=claim.text,
            index=claim.index,
            agreement_ratio=0.0,
            agreeing_analysts=[],
            dissenting_analysts=[],
            total_analysts=0,
            mean_confidence=claim.original_confidence,
            source_count=len(citation_ids if citation_ids is not None else claim.citation_ids),
            corroboration_count=corroboration_count,
            citation_ids=citation_ids if citation_ids is not None else claim.citation_ids,
            analyst_scores={},
            analyst_reasoning={},
            aggregated_claim_id=f"AGG-{uuid.uuid4().hex[:12]}",
            task_ids=task_ids if task_ids is not None else [claim.task_id],
        )
