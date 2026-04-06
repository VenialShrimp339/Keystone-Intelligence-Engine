"""'What Would You Have to Believe?' step for L1.5 Deliberation.

For claims with confidence below 0.6, elicits structured assumptions
that would have to be true for the claim to hold. Surfaces hidden
assumptions and improves downstream uncertainty framing.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.evaluator.retry import LLMCallable, retry_llm_call

CONFIDENCE_THRESHOLD = 0.6


class WWHTBResult(BaseModel):
    """Output of the WWHTB step for a single claim."""

    claim_index: int
    claim_text: str
    assumptions: list[str] = Field(default_factory=list)


async def run_wwhtb(
    llm: LLMCallable,
    claims: list[AggregatedClaim],
) -> list[WWHTBResult]:
    """Run WWHTB on claims below the confidence threshold.

    Only fires for claims with mean_confidence < 0.6.
    Returns results only for claims that were evaluated.
    """
    low_conf = [c for c in claims if c.mean_confidence < CONFIDENCE_THRESHOLD]
    if not low_conf:
        return []

    results: list[WWHTBResult] = []
    for claim in low_conf:
        prompt = (
            f"For the following uncertain claim, identify the key assumptions "
            f"that would have to be true for it to hold. List 2-5 specific, "
            f"testable assumptions.\n\n"
            f"Claim: {claim.claim_text}\n"
            f"Current confidence: {claim.mean_confidence:.2f}\n"
            f"Dissenting views: {', '.join(claim.dissenting_analysts) or 'none'}\n\n"
            f'Respond with JSON: {{"assumptions": ["assumption 1", "assumption 2"]}}'
        )
        response = await retry_llm_call(
            llm, prompt, description=f"wwhtb_claim_{claim.index}"
        )
        try:
            parsed = json.loads(response)
            assumptions = parsed.get("assumptions", [])
        except json.JSONDecodeError:
            assumptions = ["Unable to elicit assumptions"]

        results.append(
            WWHTBResult(
                claim_index=claim.index,
                claim_text=claim.claim_text,
                assumptions=assumptions,
            )
        )
    return results
