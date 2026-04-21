"""'What Would You Have to Believe?' step for L1.5 Deliberation.

For claims with confidence below 0.6, elicits structured assumptions
that would have to be true for the claim to hold. Surfaces hidden
assumptions and improves downstream uncertainty framing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.deliberation._prompts import load_prompt as load_deliberation_prompt
from keystone.deliberation.aggregator import AggregatedClaim
from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json

CONFIDENCE_THRESHOLD = 0.6


class WWHTBResult(BaseModel):
    """Output of the WWHTB step for a single claim."""

    claim_index: int
    claim_text: str
    assumptions: list[str] = Field(default_factory=list)


async def run_wwhtb(
    llm: LLMCallable,
    claims: list[AggregatedClaim],
    *,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
) -> list[WWHTBResult]:
    """Run WWHTB on claims below the confidence threshold.

    Only fires for claims with ``mean_confidence < confidence_threshold``.
    Threshold is tunable via :class:`PipelineConfig.wwhtb_confidence_threshold`;
    the default matches the historic 0.6 constant.
    """
    low_conf = [c for c in claims if c.mean_confidence < confidence_threshold]
    if not low_conf:
        return []

    results: list[WWHTBResult] = []
    for claim in low_conf:
        prompt = load_deliberation_prompt(
            "wwhtb",
            claim_text=claim.claim_text,
            mean_confidence=f"{claim.mean_confidence:.2f}",
            dissenting_views=", ".join(claim.dissenting_analysts) or "none",
        )
        response = await retry_llm_call(llm, prompt, description=f"wwhtb_claim_{claim.index}")
        try:
            parsed = safe_llm_json(response)
            assumptions = parsed.get("assumptions", [])
        except ParseError:
            assumptions = ["Unable to elicit assumptions"]

        results.append(
            WWHTBResult(
                claim_index=claim.index,
                claim_text=claim.claim_text,
                assumptions=assumptions,
            )
        )
    return results
