"""Tests for Layer 3 rubric scorer: geometric mean, tier gating, scoring."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from keystone.evaluator.layer3_rubric import (
    Layer3RubricScorer,
    _DIMENSION_PROMPT_FILES,
    weighted_geometric_mean,
)
from keystone.evaluator.rubric_config import (
    TIER_1_DIMENSIONS,
    TIER_2_DIMENSIONS,
    EvaluationProfile,
    get_profile_weights,
)
from keystone.models.evaluation import (
    DimensionScore,
    RubricDimension,
    SprintContract,
)


# ---------------------------------------------------------------------------
# Geometric mean mathematical verification (no LLM needed)
# ---------------------------------------------------------------------------


class TestWeightedGeometricMean:
    def test_equal_scores_return_that_score(self) -> None:
        """[80, 80, 80] with equal weights = 80.0 exactly."""
        scores = [
            DimensionScore(dimension=RubricDimension.ANALYTICAL_DEPTH, score=80, feedback="ok"),
            DimensionScore(dimension=RubricDimension.SOURCE_QUALITY, score=80, feedback="ok"),
            DimensionScore(dimension=RubricDimension.QUANTITATIVE_RIGOR, score=80, feedback="ok"),
        ]
        weights = {
            RubricDimension.ANALYTICAL_DEPTH: 1 / 3,
            RubricDimension.SOURCE_QUALITY: 1 / 3,
            RubricDimension.QUANTITATIVE_RIGOR: 1 / 3,
        }
        result = weighted_geometric_mean(scores, weights)
        assert abs(result - 80.0) < 0.01

    def test_one_low_score_drags_down(self) -> None:
        """[100, 1, 100] with equal weights << arithmetic mean of 67."""
        scores = [
            DimensionScore(dimension=RubricDimension.ANALYTICAL_DEPTH, score=100, feedback="ok"),
            DimensionScore(dimension=RubricDimension.SOURCE_QUALITY, score=1, feedback="ok"),
            DimensionScore(dimension=RubricDimension.QUANTITATIVE_RIGOR, score=100, feedback="ok"),
        ]
        weights = {
            RubricDimension.ANALYTICAL_DEPTH: 1 / 3,
            RubricDimension.SOURCE_QUALITY: 1 / 3,
            RubricDimension.QUANTITATIVE_RIGOR: 1 / 3,
        }
        result = weighted_geometric_mean(scores, weights)
        # Geometric mean of [100, 1, 100] = (100*1*100)^(1/3) = 10000^(1/3) ~ 21.5
        assert result < 30.0
        assert result > 15.0  # should be ~21.5

    def test_all_perfect_returns_100(self) -> None:
        all_dims = list(RubricDimension)
        scores = [DimensionScore(dimension=d, score=100, feedback="ok") for d in all_dims]
        weights = get_profile_weights(EvaluationProfile.DEFAULT)
        result = weighted_geometric_mean(scores, weights)
        assert abs(result - 100.0) < 0.01

    def test_floor_score_handling(self) -> None:
        """Score of 0 is floored at 0.01 in log computation."""
        scores = [
            DimensionScore(dimension=RubricDimension.ANALYTICAL_DEPTH, score=0, feedback="ok"),
            DimensionScore(dimension=RubricDimension.SOURCE_QUALITY, score=100, feedback="ok"),
        ]
        weights = {
            RubricDimension.ANALYTICAL_DEPTH: 0.5,
            RubricDimension.SOURCE_QUALITY: 0.5,
        }
        result = weighted_geometric_mean(scores, weights)
        assert result == pytest.approx(1.0, abs=0.01)
        assert result < 2.0  # heavily penalized

    def test_empty_scores_returns_zero(self) -> None:
        assert weighted_geometric_mean([], {}) == 0.0

    def test_subset_normalization(self) -> None:
        """Scoring only a subset of dimensions normalizes by weight_sum."""
        scores = [
            DimensionScore(dimension=RubricDimension.ANALYTICAL_DEPTH, score=80, feedback="ok"),
        ]
        weights = get_profile_weights(EvaluationProfile.DEFAULT)
        result = weighted_geometric_mean(scores, weights)
        # With normalization, single score of 80 should return ~80
        assert abs(result - 80.0) < 1.0


# ---------------------------------------------------------------------------
# Tier 1 gate logic (mock LLM)
# ---------------------------------------------------------------------------


def _make_contract() -> SprintContract:
    return SprintContract(
        section_id="section_task_001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        task_id="task_001",
        section_title="Competitive Landscape",
        acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
    )


def _mock_dimension_scores(
    tier1_scores: dict[RubricDimension, float] | None = None,
    tier2_scores: dict[RubricDimension, float] | None = None,
    gestalt: float = 0.0,
) -> callable:
    """Create a mock LLM that returns predictable scores per dimension."""
    t1 = tier1_scores or {d: 70.0 for d in TIER_1_DIMENSIONS}
    t2 = tier2_scores or {d: 65.0 for d in TIER_2_DIMENSIONS}
    all_scores = {**t1, **t2}

    async def mock_llm(prompt: str) -> str:
        lower = prompt.lower()
        # Gestalt overlay (check first since it's unique)
        if "gestalt overlay" in lower:
            return json.dumps({"adjustment": gestalt, "rationale": "Test gestalt"})
        # Match dimension by unique prompt header: "# <name> evaluation"
        for dim in RubricDimension:
            header = f"# {dim.value.replace('_', ' ')} evaluation"
            if header in lower:
                return json.dumps(
                    {
                        "score": all_scores.get(dim, 60),
                        "feedback": f"Test feedback for {dim.value}",
                        "sub_criteria_notes": [f"note for {dim.value}"],
                    }
                )
        return json.dumps({"score": 60, "feedback": "fallback", "sub_criteria_notes": []})

    return mock_llm


class TestTier1Gate:
    @pytest.mark.asyncio
    async def test_all_tier1_pass_runs_tier2(self) -> None:
        llm = _mock_dimension_scores()
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert len(result.dimension_scores) == 10  # All 10 scored
        assert result.final_score > 0

    @pytest.mark.asyncio
    async def test_tier1_failure_skips_tier2(self) -> None:
        llm = _mock_dimension_scores(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 35.0,  # below 40 floor
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 60.0,
                RubricDimension.NARRATIVE_COHERENCE: 50.0,
            }
        )
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        # Only Tier 1 scored (4 dimensions)
        assert len(result.dimension_scores) == 4
        assert result.final_score == 0.0
        assert result.weighted_total == 0.0

    @pytest.mark.asyncio
    async def test_tier1_boundary_at_floor_passes(self) -> None:
        llm = _mock_dimension_scores(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 40.0,  # exactly at floor
                RubricDimension.INTELLECTUAL_HONESTY: 40.0,
                RubricDimension.COMPLETENESS: 40.0,  # floor raised from 30 to 40
                RubricDimension.NARRATIVE_COHERENCE: 40.0,
            }
        )
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert len(result.dimension_scores) == 10  # Tier 2 ran


# ---------------------------------------------------------------------------
# Profile weight tests
# ---------------------------------------------------------------------------


class TestProfileScoring:
    @pytest.mark.asyncio
    async def test_estimative_applies_overrides(self) -> None:
        llm = _mock_dimension_scores()
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.ESTIMATIVE)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert result.final_score > 0
        # ESTIMATIVE weights differ from DEFAULT
        default_weights = get_profile_weights(EvaluationProfile.DEFAULT)
        est_weights = get_profile_weights(EvaluationProfile.ESTIMATIVE)
        assert (
            est_weights[RubricDimension.CALIBRATED_CONFIDENCE]
            != default_weights[RubricDimension.CALIBRATED_CONFIDENCE]
        )

    @pytest.mark.asyncio
    async def test_strategic_applies_overrides(self) -> None:
        llm = _mock_dimension_scores()
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.STRATEGIC)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert result.final_score > 0

    @pytest.mark.asyncio
    async def test_dimension_emphasis_changes_weighted_total(self) -> None:
        tier2_scores = {
            RubricDimension.ANALYTICAL_DEPTH: 20.0,
            RubricDimension.SOURCE_QUALITY: 80.0,
            RubricDimension.QUANTITATIVE_RIGOR: 80.0,
            RubricDimension.ACTIONABILITY: 80.0,
            RubricDimension.EVALUATIVE_SURPRISE: 80.0,
            RubricDimension.CALIBRATED_CONFIDENCE: 80.0,
        }
        llm = _mock_dimension_scores(tier2_scores=tier2_scores)
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)

        baseline = await scorer.score_all_dimensions("Test output.", _make_contract())
        emphasized_contract = SprintContract(
            section_id="section_task_001",
            engagement_id="ENG-001",
            client_id="CLT-001",
            task_id="task_001",
            section_title="Competitive Landscape",
            acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
            dimension_emphasis={RubricDimension.ANALYTICAL_DEPTH: 2.0},
        )
        emphasized = await scorer.score_all_dimensions("Test output.", emphasized_contract)

        assert emphasized.weighted_total < baseline.weighted_total

    @pytest.mark.asyncio
    async def test_dimension_emphasis_clamped_to_documented_range(self) -> None:
        tier2_scores = {
            RubricDimension.ANALYTICAL_DEPTH: 20.0,
            RubricDimension.SOURCE_QUALITY: 80.0,
            RubricDimension.QUANTITATIVE_RIGOR: 80.0,
            RubricDimension.ACTIONABILITY: 80.0,
            RubricDimension.EVALUATIVE_SURPRISE: 80.0,
            RubricDimension.CALIBRATED_CONFIDENCE: 80.0,
        }
        llm = _mock_dimension_scores(tier2_scores=tier2_scores)
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)

        over_emphasized = SprintContract(
            section_id="section_task_001",
            engagement_id="ENG-001",
            client_id="CLT-001",
            task_id="task_001",
            section_title="Competitive Landscape",
            acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
            dimension_emphasis={RubricDimension.ANALYTICAL_DEPTH: 5.0},
        )
        capped = SprintContract(
            section_id="section_task_001",
            engagement_id="ENG-001",
            client_id="CLT-001",
            task_id="task_001",
            section_title="Competitive Landscape",
            acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
            dimension_emphasis={RubricDimension.ANALYTICAL_DEPTH: 1.5},
        )

        over_emphasized_result = await scorer.score_all_dimensions("Test output.", over_emphasized)
        capped_result = await scorer.score_all_dimensions("Test output.", capped)

        assert over_emphasized_result.weighted_total == pytest.approx(
            capped_result.weighted_total,
            abs=0.01,
        )


# ---------------------------------------------------------------------------
# Gestalt overlay tests
# ---------------------------------------------------------------------------


class TestGestaltOverlay:
    @pytest.mark.asyncio
    async def test_positive_gestalt_adjustment(self) -> None:
        llm = _mock_dimension_scores(gestalt=5.0)
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert result.gestalt_adjustment == 5.0
        assert result.final_score == pytest.approx(result.weighted_total + 5.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_gestalt_clamped_to_bounds(self) -> None:
        llm = _mock_dimension_scores(gestalt=25.0)  # beyond +10
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert result.gestalt_adjustment == 10.0

    @pytest.mark.asyncio
    async def test_final_score_clamped_to_100(self) -> None:
        # All perfect scores + positive gestalt
        llm = _mock_dimension_scores(
            tier1_scores={d: 100 for d in TIER_1_DIMENSIONS},
            tier2_scores={d: 100 for d in TIER_2_DIMENSIONS},
            gestalt=10.0,
        )
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)
        result = await scorer.score_all_dimensions("Test output.", _make_contract())
        assert result.final_score <= 100.0

    @pytest.mark.asyncio
    async def test_geometric_mean_uses_epsilon_floor_in_live_scoring_path(self) -> None:
        llm = _mock_dimension_scores(
            tier1_scores={d: 100.0 for d in TIER_1_DIMENSIONS},
            tier2_scores={
                RubricDimension.ANALYTICAL_DEPTH: 0.0,
                RubricDimension.SOURCE_QUALITY: 100.0,
                RubricDimension.QUANTITATIVE_RIGOR: 100.0,
                RubricDimension.ACTIONABILITY: 100.0,
                RubricDimension.EVALUATIVE_SURPRISE: 100.0,
                RubricDimension.CALIBRATED_CONFIDENCE: 100.0,
            },
        )
        scorer = Layer3RubricScorer(llm=llm, profile=EvaluationProfile.DEFAULT)

        result = await scorer.score_all_dimensions("Test output.", _make_contract())

        assert result.weighted_total == pytest.approx(33.11, abs=0.1)
        assert result.weighted_total < 40.0


# ---------------------------------------------------------------------------
# Prompt template loading tests
# ---------------------------------------------------------------------------


class TestPromptTemplates:
    PROMPTS_DIR = (
        Path(__file__).parent.parent.parent.parent / "src" / "keystone" / "evaluator" / "prompts"
    )

    def test_all_11_templates_exist(self) -> None:
        expected = list(_DIMENSION_PROMPT_FILES.values()) + ["gestalt_overlay.md"]
        for fname in expected:
            path = self.PROMPTS_DIR / fname
            assert path.exists(), f"Missing prompt: {fname}"

    def test_templates_have_output_text_placeholder(self) -> None:
        for fname in _DIMENSION_PROMPT_FILES.values():
            content = (self.PROMPTS_DIR / fname).read_text()
            assert "{{output_text}}" in content, f"{fname} missing {{{{output_text}}}}"

    def test_dimension_templates_have_contract_placeholder(self) -> None:
        for fname in _DIMENSION_PROMPT_FILES.values():
            content = (self.PROMPTS_DIR / fname).read_text()
            assert "{{sprint_contract_criteria}}" in content, (
                f"{fname} missing {{{{sprint_contract_criteria}}}}"
            )

    @pytest.mark.asyncio
    async def test_prompt_context_includes_sprint_contract_fields(self) -> None:
        prompts: list[str] = []
        base_llm = _mock_dimension_scores()

        async def capturing_llm(prompt: str) -> str:
            prompts.append(prompt)
            return await base_llm(prompt)

        contract = SprintContract(
            section_id="section_task_001",
            engagement_id="ENG-001",
            client_id="CLT-001",
            task_id="task_001",
            section_title="Competitive Landscape",
            acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
            mandatory_elements=["competitive comparison table"],
            anti_patterns=["generic SWOT without company-specific data"],
        )
        scorer = Layer3RubricScorer(llm=capturing_llm, profile=EvaluationProfile.DEFAULT)
        await scorer.score_all_dimensions("Test output.", contract)

        prompt_text = "\n".join(prompts)
        assert "Mandatory elements:" in prompt_text
        assert "competitive comparison table" in prompt_text
        assert "Anti-patterns:" in prompt_text
        assert "generic SWOT without company-specific data" in prompt_text
