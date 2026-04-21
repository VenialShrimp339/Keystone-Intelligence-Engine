"""Sub-research models for the L1 two-tier orchestrator-worker pattern.

LeadResearcher decomposes a task into SubQuery objects, dispatches
SubResearcher workers, and merges their PartialFinding outputs into
one StructuredFinding. These models are internal to the research layer —
downstream stages never see them.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class SubQuery(BaseModel):
    """A methodologically-scoped sub-question dispatched to one SubResearcher.

    Each SubQuery within a task must use a genuinely different analytical
    lens and target non-overlapping source universes. The LeadResearcher
    produces 3 of these per task (Phase 1 hardcoded N=3).
    """

    sub_id: str = Field(description="Unique within task, format SUB-001")
    objective: str = Field(
        description="What this sub-agent should investigate — must be specific and falsifiable"
    )
    methodology: str = Field(
        description="The analytical lens: financial_data, market_intelligence, "
        "academic_technical, regulatory_legal, or competitive_positioning"
    )
    allowed_tools: list[str] = Field(
        description="Subset of parent task's assigned_tools appropriate for this methodology"
    )
    anti_confirmatory_framing: str = Field(
        description="Evaluative framing requiring evidence both for and against, "
        "scoped to this sub-query's methodology"
    )
    stop_criterion: str = Field(
        description="When this sub-agent should stop researching "
        "(e.g., '3+ independent sources corroborate or contradict the claim')"
    )
    output_focus: str = Field(
        description="What kind of claims to prioritize "
        "(e.g., 'quantitative market data with specific figures')"
    )

    @field_validator("anti_confirmatory_framing")
    @classmethod
    def validate_not_confirmatory(cls, v: str) -> str:
        """Mirror the ResearchTask validator — sub-queries inherit the constraint."""
        confirmatory_patterns = ["find evidence for", "prove that", "confirm that", "show that"]
        lower = v.lower()
        for pattern in confirmatory_patterns:
            if lower.startswith(pattern):
                raise ValueError(
                    f"Anti-confirmatory framing must not start with '{pattern}'. "
                    "Use evaluative framing: 'evaluate whether..., "
                    "including evidence both for and against'"
                )
        return v

    @field_validator("allowed_tools")
    @classmethod
    def validate_tools_nonempty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("SubQuery must have at least one allowed tool")
        return v


class PartialClaim(BaseModel):
    """A single claim from a SubResearcher, carrying sub-agent attribution."""

    text: str = Field(description="The claim statement")
    evidence: str = Field(description="Supporting evidence summary")
    citation_refs: list[str] = Field(
        description="SRC-NNN and/or EV-NNN refs from this sub-agent's round"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Sub-agent's confidence")
    caveats: list[str] = Field(default_factory=list)
    sub_id: str = Field(description="Which sub-agent produced this claim")


class PartialFinding(BaseModel):
    """Output of a single SubResearcher — ephemeral, never leaves the LeadResearcher."""

    sub_id: str = Field(description="Matches the SubQuery.sub_id that produced it")
    task_id: str = Field(description="Parent task")
    methodology: str = Field(description="The methodology this sub-agent used")
    claims: list[PartialClaim] = Field(description="Claims with sub_id attribution")
    sources_consulted: int = Field(ge=0)
    tokens_consumed: int = Field(ge=0)
    absence_items: list[str] = Field(
        default_factory=list,
        description="What this sub-agent searched for but could not find",
    )
