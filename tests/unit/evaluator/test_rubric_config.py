"""Tests for rubric configuration: profiles, tiers, weights, gate logic."""

from __future__ import annotations

import pytest

from keystone.evaluator.rubric_config import (
    ENGAGEMENT_PROFILE_MAP,
    STRATEGIC_WEIGHT_OVERRIDES,
    TIER_1_DIMENSIONS,
    TIER_1_FLOOR_THRESHOLDS,
    TIER_2_DIMENSIONS,
    EvaluationProfile,
    get_profile_weights,
    get_tier1_passed,
    get_tier2_scores,
)
from keystone.models.evaluation import (
    RUBRIC_WEIGHTS,
    DimensionScore,
    RubricDimension,
)
from keystone.models.research import EngagementType


# ---------------------------------------------------------------------------
# Weight sum tests
# ---------------------------------------------------------------------------


class TestProfileWeights:
    """All profiles must produce weights summing to 1.0."""

    @pytest.mark.parametrize("profile", list(EvaluationProfile))
    def test_weights_sum_to_one(self, profile: EvaluationProfile) -> None:
        weights = get_profile_weights(profile)
        assert abs(sum(weights.values()) - 1.0) < 1e-9, (
            f"{profile} weights sum to {sum(weights.values())}"
        )

    @pytest.mark.parametrize("profile", list(EvaluationProfile))
    def test_all_dimensions_present(self, profile: EvaluationProfile) -> None:
        weights = get_profile_weights(profile)
        assert set(weights.keys()) == set(RubricDimension)

    @pytest.mark.parametrize("profile", list(EvaluationProfile))
    def test_all_weights_positive(self, profile: EvaluationProfile) -> None:
        weights = get_profile_weights(profile)
        for dim, w in weights.items():
            assert w > 0, f"{profile}.{dim} has non-positive weight {w}"

    def test_default_matches_base(self) -> None:
        weights = get_profile_weights(EvaluationProfile.DEFAULT)
        for dim in RubricDimension:
            assert abs(weights[dim] - RUBRIC_WEIGHTS[dim]) < 1e-9

    def test_strategic_emphasizes_analytical_depth(self) -> None:
        default = get_profile_weights(EvaluationProfile.DEFAULT)
        strategic = get_profile_weights(EvaluationProfile.STRATEGIC)
        assert (
            strategic[RubricDimension.ANALYTICAL_DEPTH] > default[RubricDimension.ANALYTICAL_DEPTH]
        )

    def test_strategic_emphasizes_actionability(self) -> None:
        default = get_profile_weights(EvaluationProfile.DEFAULT)
        strategic = get_profile_weights(EvaluationProfile.STRATEGIC)
        assert strategic[RubricDimension.ACTIONABILITY] > default[RubricDimension.ACTIONABILITY]

    def test_estimative_emphasizes_calibrated_confidence(self) -> None:
        default = get_profile_weights(EvaluationProfile.DEFAULT)
        estimative = get_profile_weights(EvaluationProfile.ESTIMATIVE)
        assert (
            estimative[RubricDimension.CALIBRATED_CONFIDENCE]
            > default[RubricDimension.CALIBRATED_CONFIDENCE]
        )


# ---------------------------------------------------------------------------
# Tier structure tests
# ---------------------------------------------------------------------------


class TestTierStructure:
    """Tier 1 and Tier 2 must partition the 10 dimensions exactly."""

    def test_tier1_has_four_dimensions(self) -> None:
        assert len(TIER_1_DIMENSIONS) == 4

    def test_tier2_has_six_dimensions(self) -> None:
        assert len(TIER_2_DIMENSIONS) == 6

    def test_no_overlap(self) -> None:
        assert TIER_1_DIMENSIONS & TIER_2_DIMENSIONS == set()

    def test_union_is_all_dimensions(self) -> None:
        assert TIER_1_DIMENSIONS | TIER_2_DIMENSIONS == set(RubricDimension)

    def test_floor_thresholds_cover_tier1(self) -> None:
        assert set(TIER_1_FLOOR_THRESHOLDS.keys()) == TIER_1_DIMENSIONS


# ---------------------------------------------------------------------------
# Engagement profile map tests
# ---------------------------------------------------------------------------


class TestEngagementProfileMap:
    """Map must cover all 5 EngagementType values."""

    def test_covers_all_engagement_types(self) -> None:
        assert set(ENGAGEMENT_PROFILE_MAP.keys()) == set(EngagementType)

    def test_strategic_maps_to_strategic(self) -> None:
        assert ENGAGEMENT_PROFILE_MAP[EngagementType.STRATEGIC] == EvaluationProfile.STRATEGIC

    def test_sizing_maps_to_estimative(self) -> None:
        assert ENGAGEMENT_PROFILE_MAP[EngagementType.SIZING] == EvaluationProfile.ESTIMATIVE


# ---------------------------------------------------------------------------
# Tier 1 gate logic tests
# ---------------------------------------------------------------------------


def _make_score(dim: RubricDimension, score: float) -> DimensionScore:
    return DimensionScore(dimension=dim, score=score, feedback="test")


class TestTier1Gate:
    """Tier 1 gate: below floor = fail, at floor = pass."""

    def test_all_above_floor_passes(self) -> None:
        scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 80.0),
            _make_score(RubricDimension.INTELLECTUAL_HONESTY, 70.0),
            _make_score(RubricDimension.COMPLETENESS, 60.0),
            _make_score(RubricDimension.NARRATIVE_COHERENCE, 50.0),
        ]
        assert get_tier1_passed(scores) is True

    def test_one_below_floor_fails(self) -> None:
        scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 80.0),
            _make_score(RubricDimension.INTELLECTUAL_HONESTY, 39.0),  # below 40
            _make_score(RubricDimension.COMPLETENESS, 60.0),
            _make_score(RubricDimension.NARRATIVE_COHERENCE, 50.0),
        ]
        assert get_tier1_passed(scores) is False

    def test_completeness_below_floor_fails(self) -> None:
        scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 80.0),
            _make_score(RubricDimension.INTELLECTUAL_HONESTY, 70.0),
            _make_score(RubricDimension.COMPLETENESS, 39.0),  # below 40
            _make_score(RubricDimension.NARRATIVE_COHERENCE, 50.0),
        ]
        assert get_tier1_passed(scores) is False

    def test_exactly_at_floor_passes(self) -> None:
        scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 40.0),
            _make_score(RubricDimension.INTELLECTUAL_HONESTY, 40.0),
            _make_score(RubricDimension.COMPLETENESS, 40.0),
            _make_score(RubricDimension.NARRATIVE_COHERENCE, 40.0),
        ]
        assert get_tier1_passed(scores) is True

    def test_tier2_scores_ignored(self) -> None:
        """Tier 2 dimensions don't affect Tier 1 gate."""
        scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 80.0),
            _make_score(RubricDimension.INTELLECTUAL_HONESTY, 70.0),
            _make_score(RubricDimension.COMPLETENESS, 60.0),
            _make_score(RubricDimension.NARRATIVE_COHERENCE, 50.0),
            _make_score(RubricDimension.ANALYTICAL_DEPTH, 5.0),  # very low, Tier 2
        ]
        assert get_tier1_passed(scores) is True


# ---------------------------------------------------------------------------
# Tier 2 filter tests
# ---------------------------------------------------------------------------


class TestTier2Filter:
    def test_filters_to_tier2_only(self) -> None:
        all_scores = [
            _make_score(RubricDimension.INTENT_ALIGNMENT, 80.0),
            _make_score(RubricDimension.ANALYTICAL_DEPTH, 70.0),
            _make_score(RubricDimension.SOURCE_QUALITY, 65.0),
        ]
        tier2 = get_tier2_scores(all_scores)
        dims = {s.dimension for s in tier2}
        assert dims == {RubricDimension.ANALYTICAL_DEPTH, RubricDimension.SOURCE_QUALITY}

    def test_returns_empty_for_only_tier1(self) -> None:
        scores = [_make_score(RubricDimension.INTENT_ALIGNMENT, 80.0)]
        assert get_tier2_scores(scores) == []
