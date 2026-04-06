"""Claim-level SELECTION aggregator for L1.5 Deliberation.

For each disputed finding, a judge LLM selects the best-supported claim
(81% win rate vs. 51.2% for synthesis-based blending per the spec).
Post-selection consistency check ensures selected claims don't contradict.

Uses LLMCallable at FLAGSHIP tier for the judge.
"""

from __future__ import annotations

import json
import statistics

from pydantic import BaseModel, Field

from keystone.deliberation.analyst import AnalystOutput, InputClaim
from keystone.evaluator.retry import LLMCallable, retry_llm_call

# Variance threshold above which analyst disagreement triggers judge selection.
# 0.04 corresponds to stddev ~0.2 (a 20+ point spread between analysts).
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


class Aggregator:
    """Claim-level SELECTION aggregator.

    Uses a judge LLM (flagship tier) to resolve disputes where analysts
    disagree significantly. Does NOT blend or synthesize -- picks the
    best-supported analyst assessment.
    """

    def __init__(self, judge_llm: LLMCallable) -> None:
        self._judge = judge_llm

    async def aggregate(
        self,
        analyst_outputs: list[AnalystOutput],
        claims: list[InputClaim],
    ) -> list[AggregatedClaim]:
        """Aggregate analyst assessments into final claims."""
        if not claims:
            return []

        aggregated: list[AggregatedClaim] = []
        for claim in claims:
            scores: dict[str, float] = {}
            reasoning: dict[str, str] = {}
            source_counts: dict[str, int] = {}

            for output in analyst_outputs:
                for sc in output.scored_claims:
                    if sc.index == claim.index:
                        scores[output.analyst_type] = sc.analyst_confidence
                        reasoning[output.analyst_type] = sc.reasoning
                        source_counts[output.analyst_type] = sc.source_count

            if not scores:
                aggregated.append(self._build_unscored(claim))
                continue

            confidences = list(scores.values())
            variance = statistics.variance(confidences) if len(confidences) > 1 else 0.0

            # Judge-based selection for disputed claims
            if variance > DISPUTE_VARIANCE_THRESHOLD and len(confidences) >= 2:
                selected_type, sel_reasoning = await self._judge_select(
                    claim, scores, reasoning
                )
                mean_conf = scores.get(selected_type, statistics.mean(confidences))
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
                    source_count=max(source_counts.values()) if source_counts else len(claim.citation_ids),
                    corroboration_count=len(claim.citation_ids),
                    citation_ids=claim.citation_ids,
                    analyst_scores=scores,
                    analyst_reasoning=reasoning,
                    selected_from=selected_type,
                    selection_reasoning=sel_reasoning,
                )
            )

        # Post-selection consistency check
        await self._consistency_check(aggregated)
        return aggregated

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
        prompt = (
            f"Multiple analysts evaluated this claim with different conclusions.\n\n"
            f"Claim: {claim.text}\n"
            f"Evidence: {claim.evidence}\n\n"
            f"Analyst assessments:\n{assessments}\n\n"
            f"Select the analyst whose assessment is best supported by the evidence. "
            f"Do NOT blend or average. Pick one.\n\n"
            f'Respond with JSON: {{"selected_analyst": "<analyst_type>", "reasoning": "..."}}'
        )
        response = await retry_llm_call(
            self._judge, prompt, description="judge_selection"
        )
        try:
            parsed = json.loads(response)
            selected = parsed.get("selected_analyst", "")
            sel_reasoning = parsed.get("reasoning", "")
            if selected in scores:
                return selected, sel_reasoning
        except (json.JSONDecodeError, KeyError):
            pass

        # Fallback: pick highest confidence analyst
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        return best, "Fallback: selected highest confidence analyst"

    async def _consistency_check(self, claims: list[AggregatedClaim]) -> None:
        """Screen selected claims for incoherence."""
        high_conf = [c for c in claims if c.mean_confidence >= 0.6]
        if len(high_conf) < 2:
            return

        summaries = "\n".join(
            f"- [{c.index}] {c.claim_text} (confidence: {c.mean_confidence:.2f})"
            for c in high_conf[:10]
        )
        prompt = (
            f"Review these selected claims for logical contradictions:\n\n"
            f"{summaries}\n\n"
            f"Identify any pairs that directly contradict each other. "
            f'Respond with JSON: {{"contradictions": ['
            f'{{"claim_a": <index>, "claim_b": <index>, "issue": "..."}}]}}'
        )
        response = await retry_llm_call(
            self._judge, prompt, description="consistency_check"
        )
        try:
            parsed = json.loads(response)
            contradictions = parsed.get("contradictions", [])
            claim_by_idx = {c.index: c for c in claims}
            for cont in contradictions:
                a_idx = cont.get("claim_a")
                b_idx = cont.get("claim_b")
                if a_idx in claim_by_idx:
                    claim_by_idx[a_idx].consistency_passed = False
                if b_idx in claim_by_idx:
                    claim_by_idx[b_idx].consistency_passed = False
        except (json.JSONDecodeError, KeyError):
            pass

    @staticmethod
    def _build_unscored(claim: InputClaim) -> AggregatedClaim:
        return AggregatedClaim(
            claim_text=claim.text,
            index=claim.index,
            agreement_ratio=0.0,
            agreeing_analysts=[],
            dissenting_analysts=[],
            total_analysts=0,
            mean_confidence=claim.original_confidence,
            source_count=len(claim.citation_ids),
            corroboration_count=0,
            citation_ids=claim.citation_ids,
            analyst_scores={},
            analyst_reasoning={},
        )
