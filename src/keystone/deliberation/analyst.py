"""Independent analyst agents for L1.5 Deliberation.

Each analyst applies a distinct analytical methodology (ACH, Quantitative,
Adversarial, Historical Analogy, Scenario Planning) to independently
evaluate claims from L1 research agents. No inter-analyst communication.

Methodological diversity replaces persona diversity (DMAD, ICLR 2025).
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.agents import DeliberationAnalystType

if TYPE_CHECKING:
    from keystone.models.research import StructuredFinding


class InputClaim(BaseModel):
    """A claim extracted from findings for analyst evaluation."""

    index: int = Field(description="Position in the flattened claim list")
    task_id: str = Field(description="Task this claim addresses")
    agent_id: str = Field(description="L1 agent that produced this claim")
    text: str = Field(description="The claim statement")
    evidence: str = Field(description="Supporting evidence summary")
    citation_ids: list[str] = Field(description="Citation IDs backing this claim")
    original_confidence: float = Field(ge=0.0, le=1.0)
    caveats: list[str] = Field(default_factory=list)


class ScoredClaim(BaseModel):
    """A claim scored by a single analyst."""

    index: int = Field(description="Matches InputClaim.index")
    claim_text: str
    analyst_confidence: float = Field(ge=0.0, le=1.0)
    source_count: int = Field(ge=0)
    reasoning: str


class AnalystOutput(BaseModel):
    """Complete output of one deliberation analyst."""

    analyst_id: str
    analyst_type: str
    scored_claims: list[ScoredClaim]


# Methodology prompt templates -- these are the specification layer for each
# analyst type. In production, these become .md files with YAML frontmatter.
METHODOLOGY_PROMPTS: dict[str, str] = {
    DeliberationAnalystType.ACH: (
        "You are an intelligence analyst using Analysis of Competing Hypotheses (ACH) "
        "per ICD 203. For each claim, identify competing hypotheses and rate evidence "
        "diagnosticity. Assign confidence based on how well evidence discriminates."
    ),
    DeliberationAnalystType.QUANTITATIVE: (
        "You are a quantitative analyst. For each claim, evaluate numerical evidence, "
        "statistical validity, sample sizes, and data source reliability. Assign "
        "confidence based on quantitative rigor."
    ),
    DeliberationAnalystType.ADVERSARIAL: (
        "You are an adversarial analyst tasked with finding weaknesses. For each claim, "
        "identify the strongest counter-argument and test for confirmation bias. "
        "Assign confidence based on how well the claim survives scrutiny."
    ),
    DeliberationAnalystType.HISTORICAL_ANALOGY: (
        "You are a historical analogy analyst. For each claim, identify relevant "
        "historical precedents. Assess base rates and reference class forecasting. "
        "Assign confidence based on historical pattern support."
    ),
    DeliberationAnalystType.SCENARIO_PLANNING: (
        "You are a scenario planning analyst. For each claim, consider multiple "
        "future scenarios (optimistic, baseline, pessimistic). Assign confidence "
        "based on robustness across plausible scenarios."
    ),
}


def extract_claims(findings: list[StructuredFinding]) -> list[InputClaim]:
    """Flatten all claims from all findings into an indexed list."""
    claims: list[InputClaim] = []
    idx = 0
    for finding in findings:
        for fc in finding.claims:
            citation_ids = (
                list(fc.citation_ids) if fc.citation_ids else [c.citation_id for c in fc.citations]
            )
            claims.append(
                InputClaim(
                    index=idx,
                    task_id=finding.task_id,
                    agent_id=finding.agent_id,
                    text=fc.text,
                    evidence=fc.evidence,
                    citation_ids=citation_ids,
                    original_confidence=fc.confidence,
                    caveats=fc.caveats,
                )
            )
            idx += 1
    return claims


class Analyst:
    """Independent deliberation analyst agent.

    Uses LLMCallable for all LLM calls. Each analyst applies a
    methodology-specific prompt to evaluate claims independently.
    """

    def __init__(
        self,
        llm: LLMCallable,
        analyst_type: DeliberationAnalystType,
        analyst_id: str | None = None,
    ) -> None:
        self._llm = llm
        self._analyst_type = analyst_type
        self._analyst_id = analyst_id or f"analyst-{analyst_type.value}-{uuid.uuid4().hex[:8]}"

    @property
    def analyst_id(self) -> str:
        return self._analyst_id

    @property
    def analyst_type(self) -> DeliberationAnalystType:
        return self._analyst_type

    async def analyze(self, claims: list[InputClaim]) -> AnalystOutput:
        """Evaluate all claims using this analyst's methodology."""
        if not claims:
            return AnalystOutput(
                analyst_id=self._analyst_id,
                analyst_type=self._analyst_type.value,
                scored_claims=[],
            )

        prompt = self._build_prompt(claims)
        response = await retry_llm_call(
            self._llm,
            prompt,
            description=f"analyst_{self._analyst_type.value}",
        )
        scored_claims = self._parse_response(response, claims)
        return AnalystOutput(
            analyst_id=self._analyst_id,
            analyst_type=self._analyst_type.value,
            scored_claims=scored_claims,
        )

    def _build_prompt(self, claims: list[InputClaim]) -> str:
        methodology = METHODOLOGY_PROMPTS.get(
            self._analyst_type,
            "Evaluate each claim for confidence.",
        )
        claims_text = "\n".join(
            f"[{c.index}] {c.text}\n"
            f"  Evidence: {c.evidence}\n"
            f"  Sources: {len(c.citation_ids)}\n"
            f"  Original confidence: {c.original_confidence}"
            for c in claims
        )
        return (
            f"{methodology}\n\n"
            f"Evaluate each claim below. For each, provide:\n"
            f"- confidence: float 0.0 to 1.0\n"
            f"- source_count: integer number of supporting sources\n"
            f"- reasoning: one sentence explaining your assessment\n\n"
            f"Claims:\n{claims_text}\n\n"
            f"Respond with a JSON array:\n"
            f'[{{"index": 0, "confidence": 0.85, "source_count": 3, "reasoning": "..."}}]'
        )

    def _parse_response(self, response: str, claims: list[InputClaim]) -> list[ScoredClaim]:
        """Parse LLM JSON response into ScoredClaim list."""
        try:
            items = safe_llm_json(response, expect_list=True)
        except ParseError:
            logger.warning("Failed to parse analyst response for analyst %s", self._analyst_id)
            # Fallback: preserve original confidence for all claims
            return [
                ScoredClaim(
                    index=c.index,
                    claim_text=c.text,
                    analyst_confidence=c.original_confidence,
                    source_count=len(c.citation_ids),
                    reasoning="Failed to parse analyst response",
                )
                for c in claims
            ]

        scored_by_idx: dict[int, ScoredClaim] = {}
        for item in items:
            idx = item.get("index", -1)
            claim_text = next((c.text for c in claims if c.index == idx), "")
            scored_by_idx[idx] = ScoredClaim(
                index=idx,
                claim_text=claim_text,
                analyst_confidence=min(1.0, max(0.0, float(item.get("confidence", 0.5)))),
                source_count=int(item.get("source_count", 0)),
                reasoning=str(item.get("reasoning", "")),
            )

        result: list[ScoredClaim] = []
        for c in claims:
            if c.index in scored_by_idx:
                result.append(scored_by_idx[c.index])
            else:
                result.append(
                    ScoredClaim(
                        index=c.index,
                        claim_text=c.text,
                        analyst_confidence=c.original_confidence,
                        source_count=len(c.citation_ids),
                        reasoning="Not evaluated by analyst",
                    )
                )
        return result
