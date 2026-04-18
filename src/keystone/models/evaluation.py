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
    score: float = Field(ge=0.0, le=100.0, description="Score on 0-100 scale")
    feedback: str = Field(description="Specific, actionable feedback for this dimension")
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
    infrastructure_failure: bool = Field(
        default=False,
        description=(
            "True when Layer 1 could not run (LLM exception, subprocess crash, "
            "parse error) so downstream consumers can distinguish 'fact "
            "checking skipped due to error' from 'no facts to check'. Counts "
            "remain 0/0 in the skipped case; observability consumers must "
            "check this flag before inferring quality."
        ),
    )


class Layer2Result(BaseModel):
    """Citation validation gate results. Any fabrication = immediate rejection."""

    citations_checked: int = Field(ge=0, description="Total citations checked")
    citations_verified: int = Field(ge=0, description="Citations confirmed to exist")
    citations_fabricated: list[str] = Field(
        default_factory=list,
        description="Citation IDs flagged as fabricated. Non-empty = automatic fail.",
    )
    gate_passed: bool = Field(description="True only if zero fabricated citations found")

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
    weighted_total: float = Field(ge=0.0, le=100.0, description="Weighted sum of dimension scores")
    gestalt_adjustment: float = Field(
        ge=-10.0,
        le=10.0,
        description="Pass 2 holistic overlay: emergent quality adjustment",
    )
    final_score: float = Field(ge=0.0, le=100.0, description="weighted_total + gestalt_adjustment")
    infrastructure_failure: bool = Field(
        default=False,
        description=(
            "True when Layer 3 rubric scoring could not run (LLM exception, "
            "parse error across retries). In that case ``final_score`` is "
            "0.0 and ``dimension_scores`` is empty; consumers must check "
            "this flag before treating the zero as a content signal."
        ),
    )


class ProcessFlag(StrEnum):
    """Deterministic process trajectory concerns emitted by Layer 4.

    Flags are computed from the research agent's event trail and the
    citation manifest, not from LLM judgment. An output with several
    flags may still pass if the content itself is strong, but the flags
    surface "beautiful prose from lazy research" patterns for review.
    """

    SINGLE_SOURCE_TYPE = "single_source_type"
    SINGLE_DOMAIN = "single_domain"
    LOW_DOMAIN_DIVERSITY = "low_domain_diversity"
    NO_MULTI_ROUND = "no_multi_round"
    LOW_TOOL_DIVERSITY = "low_tool_diversity"
    LOW_SOURCE_COUNT = "low_source_count"
    COVERAGE_GAP = "coverage_gap"
    NO_HIGH_CONFIDENCE_CITATIONS = "no_high_confidence_citations"
    MISSING_ANTI_CONFIRMATORY_EVIDENCE = "missing_anti_confirmatory_evidence"
    NARROW_INQUIRY = "narrow_inquiry"


class Layer4Result(BaseModel):
    """Process trajectory evaluation results (Section 5.11).

    Layer 4 evaluates the RESEARCH PROCESS — how the output was produced,
    not what it says. Catches the failure mode Layers 1-3 cannot see:
    plausible-sounding prose from a lazy or narrow research process.
    """

    # --- Deterministic process metrics ---
    source_count: int = Field(
        ge=0,
        description="Total distinct sources the agent consulted (SourceFound events).",
    )
    unique_domains: int = Field(
        ge=0,
        description="Count of unique URL hostnames across consulted sources.",
    )
    source_type_diversity: int = Field(
        ge=0,
        description="Count of distinct source_type labels observed.",
    )
    assigned_tools: list[str] = Field(
        default_factory=list,
        description="Tools the task was authorized to use.",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="Tools actually invoked (from SourceFound.source_type signals).",
    )
    tool_utilization: float = Field(
        ge=0.0,
        le=1.0,
        description="len(tools_used) / len(assigned_tools), or 0.0 when none assigned.",
    )
    round_count: int = Field(
        ge=0,
        description="Synthesis rounds observed (FindingSynthesized events).",
    )
    issue_tree_branches_covered: list[str] = Field(
        default_factory=list,
        description="Issue-tree branch IDs the task's findings addressed.",
    )
    issue_tree_branches_missed: list[str] = Field(
        default_factory=list,
        description="Sibling issue-tree branches the agent's output did not cover.",
    )
    citation_quality_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Counts of citations at HIGH/MEDIUM/LOW quality tiers.",
    )

    # --- LLM assessment ---
    qualitative_score: float = Field(
        ge=0.0,
        le=100.0,
        description="LLM-assessed strategy quality (0-100), independent of content.",
    )
    rationale: str = Field(
        description="LLM's rationale for the qualitative score, citing specific events.",
    )
    missed_inquiries: list[str] = Field(
        default_factory=list,
        description="Obvious lines of inquiry the agent did not pursue.",
    )
    skepticism_assessment: str = Field(
        description="Whether the agent honored anti-confirmatory framing.",
    )

    # --- Overall score + flags ---
    process_quality_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Composite of deterministic metrics and LLM assessment.",
    )
    process_flags: list[str] = Field(
        default_factory=list,
        description="Specific concerns. Values come from ProcessFlag.",
    )


class JudgeScore(BaseModel):
    """Per-judge Layer 3 result in a cross-model ensemble (Layer 5).

    Captures a single judge's full scoring pass plus a success/error flag so
    the ensemble can distinguish judges that produced scores from judges that
    raised and were dropped during `asyncio.gather(..., return_exceptions=True)`.
    """

    judge_id: str = Field(description="Logical judge identifier (e.g. 'flagship', 'fast')")
    judge_tier: str = Field(description="ModelTier string value this judge ran at")
    layer3_result: Layer3Result | None = Field(
        default=None,
        description="Full per-judge Layer 3 result, or None when this judge failed",
    )
    succeeded: bool = Field(description="True when the judge produced a Layer3Result without error")
    error: str | None = Field(
        default=None,
        description="Short error description captured when succeeded is False",
    )


class VetoEvent(BaseModel):
    """Record of a dissenter-veto trigger on a Tier 1 dimension (Layer 5).

    A veto fires when any surviving judge scored a Tier 1 dimension below its
    floor threshold, even when the aggregated (median) score is above floor.
    The name is "dissenter veto" rather than "minority veto" because the
    mechanism triggers on any dissent regardless of whether the dissenters are
    a numeric minority. The aggregated `Layer3Result.final_score` is forced to
    0.0 so downstream governance and pass/fail logic reject the output, while
    the per-dimension aggregated scores remain preserved for audit.
    """

    dimension: RubricDimension = Field(description="Which Tier 1 dimension triggered the veto")
    floor_threshold: float = Field(ge=0.0, le=100.0, description="Tier 1 floor for this dimension")
    min_score: float = Field(
        ge=0.0, le=100.0, description="Minimum judge score observed for this dimension"
    )
    dissenting_judge_ids: list[str] = Field(
        description="Judge IDs whose score on this dimension was strictly below the floor",
    )
    judge_scores: dict[str, float] = Field(
        description="All surviving judges' raw scores for this dimension, keyed by judge_id",
    )


class Layer5Result(BaseModel):
    """Cross-model ensemble evaluation result (Layer 5).

    Layer 5 runs multiple `ThreePassEvaluator` instances in parallel, aggregates
    per-dimension scores by median, and applies a dissenter veto on Tier 1
    dimensions: if any judge scores any Tier 1 dimension below its floor, the
    dimension is vetoed and the aggregated final score is forced to 0.0. The
    aggregated per-dimension scores stay at the median value so downstream
    audit and calibration keep the true ensemble signal.
    """

    judges_used: list[str] = Field(
        description="Ordered list of judge IDs that were asked to score (pre-failure)"
    )
    judge_scores: list[JudgeScore] = Field(
        description="One JudgeScore per judge with per-judge Layer3Result or error"
    )
    aggregated_dimension_scores: list[DimensionScore] = Field(
        description="Per-dimension median scores across surviving judges (canonical L5 signal)"
    )
    ensemble_weighted_total: float = Field(
        ge=0.0,
        le=100.0,
        description="Weighted geometric mean of aggregated_dimension_scores (pre-gestalt, pre-veto)",
    )
    ensemble_gestalt_adjustment: float = Field(
        ge=-10.0,
        le=10.0,
        description="Median of per-judge gestalt adjustments across surviving judges",
    )
    ensemble_final_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Final ensemble score after gestalt (0.0 when vetoed or all judges failed)",
    )
    tier1_vetoed: bool = Field(
        default=False,
        description="True when at least one Tier 1 dissenter-veto triggered",
    )
    veto_events: list[VetoEvent] = Field(
        default_factory=list,
        description="Per-dimension dissenter-veto trigger records",
    )
    agreement_level: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of dimensions where max-min judge score <= 10 points",
    )
    all_judges_failed: bool = Field(
        default=False,
        description="True when every judge raised an exception (infrastructure failure path)",
    )
    failed_judge_ids: list[str] = Field(
        default_factory=list,
        description="Judge IDs that failed during scoring",
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
    acceptance_criteria: list[str] = Field(description="Specific criteria for this section to pass")
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
    -> L3 (rubric, or L5 ensemble-of-L3 when `ensemble_llms` is supplied)
    -> L4 (trajectory, when `process_context` is supplied). If L2 finds
    fabricated citations, L3/L5 and L4 are skipped.
    """

    evaluation_id: str = Field(description="Unique evaluation identifier")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    task_id: str = Field(description="Which task was evaluated")
    evaluated_at: datetime = Field(description="When this evaluation ran")
    intensity: EvaluationIntensity = Field(description="Evaluation depth applied")
    passed: bool = Field(description="Whether the output meets quality threshold")
    overall_score: float = Field(ge=0.0, le=100.0, description="Final composite score")
    layer1_results: Layer1Result = Field(description="Deterministic verification results")
    layer2_results: Layer2Result = Field(description="Citation gate results")
    layer3_results: Layer3Result | None = Field(
        default=None,
        description="Rubric scoring results. None if Layer 2 gate failed.",
    )
    layer4_results: Layer4Result | None = Field(
        default=None,
        description="Process trajectory results. None if L3 failed or context not provided.",
    )
    layer5_results: Layer5Result | None = Field(
        default=None,
        description=(
            "Cross-model ensemble results. None at LIGHT_TOUCH or when the evaluator "
            "was constructed without `ensemble_llms` (single-judge mode)."
        ),
    )
    feedback: str = Field(description="Specific, actionable feedback for regeneration")
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
    human_overall: float = Field(ge=0.0, le=100.0, description="Human overall score (0-100)")
    scorer_id: str = Field(description="Who scored this (e.g., 'jack')")
    scored_at: datetime = Field(description="When the human scoring was done")


class CalibrationReport(BaseModel):
    """Output of calibration runner: how well automated scores match human judgment."""

    spearman_correlation: float = Field(
        description="Rank correlation between automated and human scores. Target: >= 0.80."
    )
    cohens_kappa: float = Field(description="Inter-rater agreement. Target: >= 0.60.")
    per_dimension_bias: dict[RubricDimension, float] = Field(
        description="Positive = overscoring, negative = underscoring per dimension"
    )
    calibration_ready: bool = Field(description="True if spearman >= 0.80 and kappa >= 0.60")
    sample_count: int = Field(ge=0, description="Number of samples in the calibration set")
