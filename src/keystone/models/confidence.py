"""Confidence map data models for the Keystone Intelligence Engine.

Based on CAPSTONE-PLAN-v2.md Section 4.3.
The confidence map is the output of L1.5 Deliberation. It uses a 5-tier
taxonomy grounded in DiscoUQ (AUROC 0.802) and ACH matrix structures
from ICD 203.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from keystone.models.citations import (
    ACHDiagnosticity,  # noqa: TC001 (Pydantic v2 needs runtime access)
)


class DiscoUQFeatures(BaseModel):
    """Computational confidence features from DiscoUQ (March 2026).

    DiscoUQ achieves AUROC 0.802 vs 0.098 ECE for baselines. Largest
    improvements in the weak disagreement tier (50-60% agreement),
    exactly where simple voting fails.
    """

    evidence_overlap: float = Field(
        ge=0.0,
        le=1.0,
        description="Degree of evidentiary overlap across analysts (0=disjoint, 1=identical)",
    )
    minority_argument_strength: float = Field(
        ge=0.0,
        le=1.0,
        description="How strong the dissenting position is (0=trivial, 1=compelling)",
    )
    divergence_depth: str = Field(
        description="How deep the disagreement runs: 'shallow' (data interpretation), "
        "'medium' (methodology), 'deep' (fundamental assumptions)"
    )


class ACHMatrix(BaseModel):
    """Analysis of Competing Hypotheses matrix (ICD 203, Heuer methodology).

    Evaluates which evidence discriminates between hypotheses vs. which
    is consistent with all hypotheses.
    """

    hypotheses: list[str] = Field(
        description="Competing hypotheses under evaluation"
    )
    diagnostic_evidence: list[str] = Field(
        description="Evidence items that discriminate between hypotheses"
    )
    inconsistent_evidence_per_hypothesis: list[int] = Field(
        description="Count of inconsistent evidence items per hypothesis (same order as hypotheses)"
    )


class HighConfidenceClaim(BaseModel):
    """A claim with >80% methodological agreement. Presented as assertion."""

    claim: str = Field(description="The claim statement")
    methodological_agreement: str = Field(
        description="Agreement ratio and which methods agree (e.g., '4/4 (ACH, Quant, Adv, Hist)')"
    )
    sources: int = Field(ge=0, description="Number of independent sources")
    corroboration_count: int = Field(
        ge=0, description="How many agents independently found this"
    )
    robustness: str = Field(
        description="How the claim holds under assumption variations"
    )
    curmudgeon_challenge: str = Field(
        description="Specific, non-trivial reason this could be wrong"
    )
    discouq_features: DiscoUQFeatures | None = Field(
        default=None, description="Computational confidence features"
    )
    aggregated_claim_id: str | None = Field(
        default=None, description="Links to provenance index"
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Source task IDs"
    )


class ModerateConfidenceClaim(BaseModel):
    """A claim with 60-80% agreement. Presented with explicit sensitivity analysis."""

    claim: str = Field(description="The claim statement")
    methodological_agreement: str = Field(description="Agreement ratio")
    dissent: str = Field(description="Who disagrees and why")
    sources: int = Field(ge=0, description="Number of independent sources")
    sensitivity: str = Field(
        description="What assumption change would flip the conclusion"
    )
    ach_diagnosticity: ACHDiagnosticity | None = Field(
        default=None, description="How diagnostic the evidence is"
    )
    aggregated_claim_id: str | None = Field(
        default=None, description="Links to provenance index"
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Source task IDs"
    )


class WeakConfidenceClaim(BaseModel):
    """A claim with 50-60% agreement. Prominent uncertainty framing required.

    This is the tier where DiscoUQ provides the largest improvement
    over naive agreement counting.
    """

    claim: str = Field(description="The claim statement")
    methodological_agreement: str = Field(description="Agreement ratio")
    key_issue: str = Field(
        description="The primary source of uncertainty"
    )
    sources: int = Field(ge=0, description="Number of independent sources")
    recommendation: str = Field(
        description="How to present this in the deliverable"
    )
    aggregated_claim_id: str | None = Field(
        default=None, description="Links to provenance index"
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Source task IDs"
    )


class ContestedClaim(BaseModel):
    """A claim with <50% agreement. Presented as competing perspectives."""

    claim: str = Field(description="The claim statement")
    methodological_agreement: str = Field(description="Agreement ratio")
    key_disagreement: str = Field(
        description="The fundamental point of contention"
    )
    sources: int = Field(ge=0, description="Number of independent sources")
    steelmanned_opposing_view: str = Field(
        description="Strongest version of the position against this claim"
    )
    ach_matrix: ACHMatrix | None = Field(
        default=None, description="ACH analysis of competing hypotheses"
    )
    aggregated_claim_id: str | None = Field(
        default=None, description="Links to provenance index"
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Source task IDs"
    )


class InsufficientEvidenceClaim(BaseModel):
    """A claim where evidence is too sparse to assess confidence."""

    claim: str = Field(description="The claim or question")
    reason: str = Field(description="Why evidence is insufficient")
    priority: str = Field(
        description="How important it is to fill this gap (high/medium/low)"
    )
    aggregated_claim_id: str | None = Field(
        default=None, description="Links to provenance index"
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Source task IDs"
    )


class ConfidenceMap(BaseModel):
    """The complete confidence map output of L1.5 Deliberation.

    Five-tier taxonomy with DiscoUQ features. This tells the structuring
    agent (L2) exactly how to handle each claim in the deliverable.

    High-confidence -> assertions
    Moderate -> explicit sensitivity analysis
    Weak -> prominent uncertainty framing
    Contested -> competing perspectives with steelmanned views
    Insufficient -> trigger additional research threads
    """

    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")

    high_confidence_above_80pct: list[HighConfidenceClaim] = Field(
        default_factory=list, description="Claims with >80% methodological agreement"
    )
    moderate_confidence_60_80pct: list[ModerateConfidenceClaim] = Field(
        default_factory=list, description="Claims with 60-80% agreement"
    )
    weak_confidence_50_60pct: list[WeakConfidenceClaim] = Field(
        default_factory=list, description="Claims with 50-60% agreement"
    )
    contested_below_50pct: list[ContestedClaim] = Field(
        default_factory=list, description="Claims with <50% agreement"
    )
    insufficient_evidence: list[InsufficientEvidenceClaim] = Field(
        default_factory=list, description="Claims without enough evidence to assess"
    )

    gaps_identified: list[str] = Field(
        default_factory=list,
        description="Research gaps that need additional investigation",
    )
    absence_report: list[str] = Field(
        default_factory=list,
        description="What was looked for but not found (analytically significant)",
    )
    provenance_index: dict[str, list[str]] = Field(
        default_factory=dict,
        description="aggregated_claim_id -> task_ids",
    )

    @property
    def total_claims(self) -> int:
        return (
            len(self.high_confidence_above_80pct)
            + len(self.moderate_confidence_60_80pct)
            + len(self.weak_confidence_50_60pct)
            + len(self.contested_below_50pct)
            + len(self.insufficient_evidence)
        )

    @property
    def tiers_populated(self) -> int:
        count = 0
        if self.high_confidence_above_80pct:
            count += 1
        if self.moderate_confidence_60_80pct:
            count += 1
        if self.weak_confidence_50_60pct:
            count += 1
        if self.contested_below_50pct:
            count += 1
        if self.insufficient_evidence:
            count += 1
        return count
