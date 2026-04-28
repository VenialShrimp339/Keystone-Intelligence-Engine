"""Rubric configuration: profiles, tiers, weights, and gate thresholds.

This module is the foundation of the Evaluator. Every scoring decision
flows through profile weights and tier gates defined here.
"""

from __future__ import annotations

from enum import StrEnum

from keystone.models.evaluation import (
    CURRENT_WEIGHT_OVERRIDES,
    ESTIMATIVE_WEIGHT_OVERRIDES,
    RUBRIC_WEIGHTS,
    DimensionScore,
    RubricDimension,
)
from keystone.models.research import EngagementType


class EvaluationProfile(StrEnum):
    """Named weight vectors for Tier 2 dimension scoring.

    Phase 1: 4 profiles. Phase 2 expands to 8-10 as engagement
    data accumulates (Directive 13).
    """

    DEFAULT = "default"
    ESTIMATIVE = "estimative"
    CURRENT = "current"
    STRATEGIC = "strategic"


# ---------------------------------------------------------------------------
# Tier 1: Universal gate dimensions (Section 5.3)
# Floor thresholds on 0-100 scale. Below floor = immediate rejection,
# skip Tier 2 entirely. These apply identically across all profiles.
# ---------------------------------------------------------------------------

TIER_1_DIMENSIONS: set[RubricDimension] = {
    RubricDimension.INTENT_ALIGNMENT,
    RubricDimension.INTELLECTUAL_HONESTY,
    RubricDimension.COMPLETENESS,
    RubricDimension.NARRATIVE_COHERENCE,
}

TIER_1_FLOOR_THRESHOLDS: dict[RubricDimension, float] = {
    RubricDimension.INTENT_ALIGNMENT: 40.0,
    RubricDimension.INTELLECTUAL_HONESTY: 40.0,
    RubricDimension.COMPLETENESS: 40.0,
    RubricDimension.NARRATIVE_COHERENCE: 40.0,
}

# ---------------------------------------------------------------------------
# Tier 2: Adaptive dimensions (weights flex by profile)
# ---------------------------------------------------------------------------

TIER_2_DIMENSIONS: set[RubricDimension] = {d for d in RubricDimension if d not in TIER_1_DIMENSIONS}

# ---------------------------------------------------------------------------
# Engagement type -> evaluation profile mapping
# ---------------------------------------------------------------------------

ENGAGEMENT_PROFILE_MAP: dict[EngagementType, EvaluationProfile] = {
    EngagementType.SIZING: EvaluationProfile.ESTIMATIVE,
    EngagementType.DIAGNOSTIC: EvaluationProfile.DEFAULT,
    EngagementType.EVALUATIVE: EvaluationProfile.DEFAULT,
    EngagementType.EXPLORATORY: EvaluationProfile.DEFAULT,
    EngagementType.STRATEGIC: EvaluationProfile.STRATEGIC,
    EngagementType.DESIGN: EvaluationProfile.DEFAULT,
    EngagementType.SYNTHESIS: EvaluationProfile.DEFAULT,
}

# ---------------------------------------------------------------------------
# Strategic weight overrides (new, not in evaluation.py)
#
# Rationale: Strategic engagements emphasize forward-looking analytical
# insight and Monday-morning actionability over raw quantitative rigor.
# Completeness is de-emphasized because strategic analyses are inherently
# scoped (you can't be exhaustive about the future).
#
# Overridden dimensions (absolute replacements):
#   Analytical Depth:     0.12 -> 0.15  (+3%)
#   Actionability:        0.15 -> 0.18  (+3%)
#   Evaluative Surprise:  0.05 -> 0.08  (+3%)
#   Quantitative Rigor:   0.15 -> 0.10  (-5%)
#   Completeness:         0.08 -> 0.05  (-3%)
#   Calibrated Confidence: 0.05 -> 0.06 (+1%)
#
# Net delta from overridden dims: +3+3+3-5-3+1 = +2%
# Non-overridden dims (Intent Alignment 0.15, Intellectual Honesty 0.10,
# Narrative Coherence 0.05, Source Quality 0.10) sum to 0.40.
# Overridden dims sum to 0.62. Total needs to be 1.0, so non-overridden
# share the remaining 0.38 -> each scaled by 0.38/0.40 = 0.95.
# ---------------------------------------------------------------------------

STRATEGIC_WEIGHT_OVERRIDES: dict[RubricDimension, float] = {
    RubricDimension.ANALYTICAL_DEPTH: 0.15,
    RubricDimension.ACTIONABILITY: 0.18,
    RubricDimension.EVALUATIVE_SURPRISE: 0.08,
    RubricDimension.QUANTITATIVE_RIGOR: 0.10,
    RubricDimension.COMPLETENESS: 0.05,
    RubricDimension.CALIBRATED_CONFIDENCE: 0.06,
}


def _apply_overrides(
    overrides: dict[RubricDimension, float],
) -> dict[RubricDimension, float]:
    """Apply partial weight overrides to base RUBRIC_WEIGHTS.

    Only dimensions listed in overrides are replaced. The remaining
    dimensions are proportionally rescaled so the total sums to 1.0.
    This is the same pattern used by ESTIMATIVE and CURRENT overrides.
    """
    result = dict(RUBRIC_WEIGHTS)
    overridden_sum = sum(overrides.values())
    non_overridden_dims = [d for d in RubricDimension if d not in overrides]
    non_overridden_base_sum = sum(RUBRIC_WEIGHTS[d] for d in non_overridden_dims)

    remaining = 1.0 - overridden_sum
    if non_overridden_base_sum > 0:
        scale = remaining / non_overridden_base_sum
    else:
        scale = 0.0

    for d in non_overridden_dims:
        result[d] = RUBRIC_WEIGHTS[d] * scale
    for d, w in overrides.items():
        result[d] = w

    return result


def get_profile_weights(
    profile: EvaluationProfile,
) -> dict[RubricDimension, float]:
    """Return the full weight vector for a given evaluation profile.

    Applies profile-specific overrides to the canonical base weights.
    Validates the result sums to 1.0 (within floating-point tolerance).

    Raises:
        ValueError: If the computed weights don't sum to 1.0.
    """
    if profile == EvaluationProfile.DEFAULT:
        weights = dict(RUBRIC_WEIGHTS)
    elif profile == EvaluationProfile.ESTIMATIVE:
        weights = _apply_overrides(ESTIMATIVE_WEIGHT_OVERRIDES)
    elif profile == EvaluationProfile.CURRENT:
        weights = _apply_overrides(CURRENT_WEIGHT_OVERRIDES)
    elif profile == EvaluationProfile.STRATEGIC:
        weights = _apply_overrides(STRATEGIC_WEIGHT_OVERRIDES)
    else:
        msg = f"Unknown profile: {profile}"
        raise ValueError(msg)

    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        msg = f"Profile {profile} weights sum to {total}, expected 1.0"
        raise ValueError(msg)

    return weights


def get_tier1_passed(scores: list[DimensionScore]) -> bool:
    """Check whether all Tier 1 dimensions meet their floor thresholds.

    Returns False if ANY Tier 1 dimension score is below its floor.
    Dimensions not in Tier 1 are ignored.
    """
    for score in scores:
        if score.dimension in TIER_1_DIMENSIONS:
            floor = TIER_1_FLOOR_THRESHOLDS[score.dimension]
            if score.score < floor:
                return False
    return True


def get_tier2_scores(scores: list[DimensionScore]) -> list[DimensionScore]:
    """Filter a list of DimensionScores to only Tier 2 dimensions."""
    return [s for s in scores if s.dimension in TIER_2_DIMENSIONS]
