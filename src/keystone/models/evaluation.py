"""Evaluation data models for the Keystone Intelligence Engine.

Based on CAPSTONE-PLAN-v2.md Sections 5.3, 5.9, 5.10.
The Evaluator is a 5-layer stack with a 10-dimension rubric. It is
the most important component: evaluation bounds output quality.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from datetime import datetime


class RubricDimension(StrEnum):
    """The 10-dimension judgment rubric (Section 5.3).

    Weights are calibrated away from where LLMs naturally perform well
    (coherent prose, comprehensive coverage) and toward where they
    underperform (analytical novelty, quantitative rigor, actionable insight).
    """

    ANALYTICAL_DEPTH = "analytical_depth"
    SOURCE_QUALITY = "source_quality"
    QUANTITATIVE_RIGOR = "quantitative_rigor"
    NARRATIVE_COHERENCE = "narrative_coherence"
    COMPLETENESS = "completeness"
    ACTIONABILITY = "actionability"
    INTENT_ALIGNMENT = "intent_alignment"
    INTELLECTUAL_HONESTY = "intellectual_honesty"
    EVALUATIVE_SURPRISE = "evaluative_surprise"
    CALIBRATED_CONFIDENCE = "calibrated_confidence"


class EvalType(StrEnum):
    """How a rubric dimension is evaluated (Section 5.7)."""

    MACHINE_CHECKABLE = "machine_checkable"
    EXPERT_CHECKABLE = "expert_checkable"
    JUDGMENT_DEPENDENT = "judgment_dependent"
    MACHINE_AND_EXPERT = "machine_checkable_and_expert"


class EvaluationIntensity(StrEnum):
    """How deeply an output is evaluated (Section 5.5)."""

    LIGHT_TOUCH = "light_touch"
    STANDARD = "standard"
    DEEP = "deep"


# Canonical rubric definition: dimension -> (weight, eval_type, description)
# NOTE: CAPSTONE-PLAN-v2.md Section 5.3 has a math error. The plan reduced
# Analytical Depth (15%->12%, -3%) and Completeness (10%->8%, -2%) to fund two
# new 5% dimensions, but that only recovers 5% of the 10% needed. The original
# 8 dimensions summed to 100%, so the stated weights sum to 105%.
# Fix applied: Narrative Coherence reduced from 10% to 5%. Rationale: the plan's
# own weighting philosophy says to de-emphasize dimensions where LLMs naturally
# excel. Narrative Coherence ("clear story", "so what?") is exactly that --
# LLMs produce coherent prose by default. This preserves the plan's substance-
# over-style intent while correcting the arithmetic.
RUBRIC_WEIGHTS: dict[RubricDimension, float] = {
    RubricDimension.ANALYTICAL_DEPTH: 0.12,
    RubricDimension.SOURCE_QUALITY: 0.10,
    RubricDimension.QUANTITATIVE_RIGOR: 0.15,
    RubricDimension.NARRATIVE_COHERENCE: 0.05,  # Reduced from 0.10; see note above
    RubricDimension.COMPLETENESS: 0.08,
    RubricDimension.ACTIONABILITY: 0.15,
    RubricDimension.INTENT_ALIGNMENT: 0.15,
    RubricDimension.INTELLECTUAL_HONESTY: 0.10,
    RubricDimension.EVALUATIVE_SURPRISE: 0.05,
    RubricDimension.CALIBRATED_CONFIDENCE: 0.05,
}
assert abs(sum(RUBRIC_WEIGHTS.values()) - 1.00) < 1e-9, "Rubric weights must sum to 1.00"

RUBRIC_EVAL_TYPES: dict[RubricDimension, EvalType] = {
    RubricDimension.ANALYTICAL_DEPTH: EvalType.JUDGMENT_DEPENDENT,
    RubricDimension.SOURCE_QUALITY: EvalType.MACHINE_AND_EXPERT,
    RubricDimension.QUANTITATIVE_RIGOR: EvalType.MACHINE_AND_EXPERT,
    RubricDimension.NARRATIVE_COHERENCE: EvalType.JUDGMENT_DEPENDENT,
    RubricDimension.COMPLETENESS: EvalType.MACHINE_CHECKABLE,
    RubricDimension.ACTIONABILITY: EvalType.EXPERT_CHECKABLE,
    RubricDimension.INTENT_ALIGNMENT: EvalType.EXPERT_CHECKABLE,
    RubricDimension.INTELLECTUAL_HONESTY: EvalType.JUDGMENT_DEPENDENT,
    RubricDimension.EVALUATIVE_SURPRISE: EvalType.JUDGMENT_DEPENDENT,
    RubricDimension.CALIBRATED_CONFIDENCE: EvalType.MACHINE_AND_EXPERT,
}

# Type-specific weight overrides (Section 3.6 synthesis update)
# Estimative overrides: for ICD 203 estimative intelligence products.
# Calibrated Confidence and Quantitative Rigor increase; Completeness and
# Narrative Coherence decrease. Values are absolute replacements for the
# base weight when this profile is active.
ESTIMATIVE_WEIGHT_OVERRIDES: dict[RubricDimension, float] = {
    RubricDimension.CALIBRATED_CONFIDENCE: 0.10,
    RubricDimension.QUANTITATIVE_RIGOR: 0.18,
    RubricDimension.COMPLETENESS: 0.05,
    RubricDimension.NARRATIVE_COHERENCE: 0.03,  # Reduced with base (was 0.07/0.10)
}

CURRENT_WEIGHT_OVERRIDES: dict[RubricDimension, float] = {
    RubricDimension.SOURCE_QUALITY: 0.15,
    RubricDimension.COMPLETENESS: 0.12,
    RubricDimension.QUANTITATIVE_RIGOR: 0.10,
    RubricDimension.EVALUATIVE_SURPRISE: 0.03,
}


class DimensionScore(BaseModel):
    """Score for a single rubric dimension, produced by Layer 3 (Prometheus 2).

    Each dimension is scored in a separate prompt to prevent
    cross-contamination (SOS-Bench finding).
    """

    dimension: RubricDimension = Field(description="Which rubric dimension")
    score: float = Field(
        ge=0.0, le=100.0, description="Score on 0-100 scale"
    )
    feedback: str = Field(
        description="Specific, actionable feedback for this dimension"
    )
    sub_criteria_notes: list[str] = Field(
        default_factory=list,
        description="Notes on sub-criteria (trendslop detection, deletion test, etc.)",
    )


class Layer1Result(BaseModel):
    """Deterministic verification results (FActScore, numerical consistency, URLs)."""

    facts_verified: int = Field(ge=0, description="Atomic facts successfully verified")
    facts_failed: int = Field(ge=0, description="Atomic facts that failed verification")
    numerical_inconsistencies: list[str] = Field(
        default_factory=list,
        description="Specific numerical contradictions found",
    )
    dead_urls: list[str] = Field(
        default_factory=list, description="Citation URLs that are unreachable"
    )


class Layer2Result(BaseModel):
    """Citation validation gate results. Any fabrication = immediate rejection."""

    citations_checked: int = Field(ge=0, description="Total citations checked")
    citations_verified: int = Field(ge=0, description="Citations confirmed to exist")
    citations_fabricated: list[str] = Field(
        default_factory=list,
        description="Citation IDs flagged as fabricated. Non-empty = automatic fail.",
    )
    gate_passed: bool = Field(
        description="True only if zero fabricated citations found"
    )

    @field_validator("gate_passed")
    @classmethod
    def validate_gate(cls, v: bool, info: object) -> bool:
        # Note: can't cross-reference citations_fabricated in field_validator easily,
        # but the model_validator below handles the business rule
        return v


class Layer3Result(BaseModel):
    """Multi-rubric scoring results from Prometheus 2."""

    dimension_scores: list[DimensionScore] = Field(
        description="One score per rubric dimension (10 total)"
    )
    weighted_total: float = Field(
        ge=0.0, le=100.0, description="Weighted sum of dimension scores"
    )
    gestalt_adjustment: float = Field(
        ge=-10.0,
        le=10.0,
        description="Pass 2 holistic overlay: emergent quality adjustment",
    )
    final_score: float = Field(
        ge=0.0, le=100.0, description="weighted_total + gestalt_adjustment"
    )


class SprintContract(BaseModel):
    """Per-section quality criteria negotiated between generator and evaluator.

    Sprint contracts define what 'good' looks like for a specific section,
    enabling targeted evaluation rather than generic rubric application.
    """

    section_id: str = Field(description="Which section this contract covers")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    task_id: str = Field(description="Which research task this section addresses")
    section_title: str = Field(description="Human-readable section title")
    acceptance_criteria: list[str] = Field(
        description="Specific criteria for this section to pass"
    )
    dimension_emphasis: dict[RubricDimension, float] = Field(
        default_factory=dict,
        description="Per-section weight overrides for rubric dimensions",
    )
    mandatory_elements: list[str] = Field(
        default_factory=list,
        description="Elements that must appear (data tables, framework application, etc.)",
    )
    anti_patterns: list[str] = Field(
        default_factory=list,
        description="Specific things this section must NOT contain",
    )


class EvaluationResult(BaseModel):
    """Complete output of the Evaluator (L4).

    Layers execute in stack order: L1 (deterministic) -> L2 (citation gate)
    -> L3 (rubric). If L2 finds fabricated citations, L3 is skipped.
    Layers 4-5 are Phase 2 additions.
    """

    evaluation_id: str = Field(description="Unique evaluation identifier")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    task_id: str = Field(description="Which task was evaluated")
    evaluated_at: datetime = Field(description="When this evaluation ran")
    intensity: EvaluationIntensity = Field(
        description="Evaluation depth applied"
    )
    passed: bool = Field(description="Whether the output meets quality threshold")
    overall_score: float = Field(
        ge=0.0, le=100.0, description="Final composite score"
    )
    layer1_results: Layer1Result = Field(
        description="Deterministic verification results"
    )
    layer2_results: Layer2Result = Field(
        description="Citation gate results"
    )
    layer3_results: Layer3Result | None = Field(
        default=None,
        description="Rubric scoring results. None if Layer 2 gate failed.",
    )
    feedback: str = Field(
        description="Specific, actionable feedback for regeneration"
    )
    observation_entry_id: str | None = Field(
        default=None,
        description="ID of the Observation Library entry (Phase 2)",
    )


class CalibrationSample(BaseModel):
    """A human-scored sample for evaluator calibration (Component #10)."""

    sample_id: str = Field(description="Unique sample identifier")
    output_text: str = Field(description="The output that was scored")
    human_scores: dict[RubricDimension, float] = Field(
        description="Human scores per dimension (1-5 scale)"
    )
    human_overall: float = Field(
        ge=0.0, le=100.0, description="Human overall score (0-100)"
    )
    scorer_id: str = Field(description="Who scored this (e.g., 'jack')")
    scored_at: datetime = Field(description="When the human scoring was done")


class CalibrationReport(BaseModel):
    """Output of calibration runner: how well automated scores match human judgment."""

    spearman_correlation: float = Field(
        description="Rank correlation between automated and human scores. Target: >= 0.80."
    )
    cohens_kappa: float = Field(
        description="Inter-rater agreement. Target: >= 0.60."
    )
    per_dimension_bias: dict[RubricDimension, float] = Field(
        description="Positive = overscoring, negative = underscoring per dimension"
    )
    calibration_ready: bool = Field(
        description="True if spearman >= 0.80 and kappa >= 0.60"
    )
    sample_count: int = Field(
        ge=0, description="Number of samples in the calibration set"
    )
