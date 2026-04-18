"""Tests for Layer 5 cross-model ensemble evaluator with dissenter veto.

These tests focus on the aggregation math, dissenter-veto semantics, and
graceful-degradation behavior of ``EnsembleL3Evaluator``. They use per-judge
mock LLMs that dispatch on the prompt content and on a ``judge_id`` marker
embedded in the retry description (by way of the shared ``_mock_llm_factory``
that wraps a per-judge scoring dictionary).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import pytest

from keystone.evaluator.layer5_ensemble import EnsembleL3Evaluator
from keystone.evaluator.rubric_config import (
    TIER_1_DIMENSIONS,
    TIER_2_DIMENSIONS,
    EvaluationProfile,
)
from keystone.models.evaluation import (
    Layer3Result,
    RubricDimension,
    SprintContract,
)

LLMCallable = Callable[[str], Awaitable[str]]


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_contract() -> SprintContract:
    return SprintContract(
        section_id="section_task_L5",
        engagement_id="ENG-L5",
        client_id="CLT-L5",
        task_id="task_L5",
        section_title="Cross-model ensemble section",
        acceptance_criteria=["All claims cited", "Sources diverse"],
    )


def _make_judge_llm(
    *,
    tier1_scores: dict[RubricDimension, float] | None = None,
    tier2_scores: dict[RubricDimension, float] | None = None,
    gestalt: float = 0.0,
    raise_on: str | None = None,
) -> LLMCallable:
    """Return an async callable that mocks a single judge's LLM.

    ``raise_on="any"`` makes every dimension call raise RuntimeError (the
    retry helper will exhaust retries and surface the error, which the
    ensemble should capture as a failed judge).
    """
    t1 = {d: 70.0 for d in TIER_1_DIMENSIONS}
    if tier1_scores:
        t1.update(tier1_scores)
    t2 = {d: 65.0 for d in TIER_2_DIMENSIONS}
    if tier2_scores:
        t2.update(tier2_scores)
    all_scores: dict[RubricDimension, float] = {**t1, **t2}

    async def llm(prompt: str) -> str:
        if raise_on == "any":
            raise RuntimeError("mock judge failure")
        lower = prompt.lower()
        if "gestalt overlay" in lower:
            return json.dumps({"adjustment": gestalt, "rationale": "mock"})
        for dim in RubricDimension:
            header = f"# {dim.value.replace('_', ' ')} evaluation"
            if header in lower:
                return json.dumps(
                    {
                        "score": all_scores.get(dim, 60),
                        "feedback": f"[j-feedback] {dim.value}",
                        "sub_criteria_notes": [],
                    }
                )
        return json.dumps({"score": 60, "feedback": "fallback"})

    return llm


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestEnsembleConstruction:
    def test_zero_judges_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 1 judge"):
            EnsembleL3Evaluator(judges=[], profile=EvaluationProfile.DEFAULT)

    def test_two_judges_construct_cleanly(self) -> None:
        ensemble = EnsembleL3Evaluator(
            judges=[
                ("flagship", _make_judge_llm()),
                ("fast", _make_judge_llm()),
            ],
            profile=EvaluationProfile.DEFAULT,
        )
        # Internal invariant: one ThreePassEvaluator per judge
        assert len(ensemble._judges) == 2

    def test_three_judges_construct_cleanly(self) -> None:
        ensemble = EnsembleL3Evaluator(
            judges=[
                ("flagship", _make_judge_llm()),
                ("standard", _make_judge_llm()),
                ("fast", _make_judge_llm()),
            ],
            profile=EvaluationProfile.STRATEGIC,
        )
        assert len(ensemble._judges) == 3


# ---------------------------------------------------------------------------
# Aggregation math
# ---------------------------------------------------------------------------


class TestAggregationMath:
    @pytest.mark.asyncio
    async def test_two_judges_clean_pass_produces_median(self) -> None:
        # Judge A scores 70 on everything; Judge B scores 90 on everything.
        # Median per dimension = 80, weighted geometric mean ~ 80.
        judge_a = _make_judge_llm(
            tier1_scores={d: 70.0 for d in TIER_1_DIMENSIONS},
            tier2_scores={d: 70.0 for d in TIER_2_DIMENSIONS},
        )
        judge_b = _make_judge_llm(
            tier1_scores={d: 90.0 for d in TIER_1_DIMENSIONS},
            tier2_scores={d: 90.0 for d in TIER_2_DIMENSIONS},
        )
        ensemble = EnsembleL3Evaluator(
            judges=[("flagship", judge_a), ("fast", judge_b)],
            profile=EvaluationProfile.DEFAULT,
        )

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert isinstance(l3, Layer3Result)
        assert len(l5.judge_scores) == 2
        assert all(js.succeeded for js in l5.judge_scores)
        assert l5.tier1_vetoed is False
        # Median of 70 and 90 is 80
        for ds in l5.aggregated_dimension_scores:
            assert abs(ds.score - 80.0) < 0.01
        assert abs(l5.ensemble_weighted_total - 80.0) < 1.0

    @pytest.mark.asyncio
    async def test_three_judges_median_is_middle_value(self) -> None:
        # Scores 70, 80, 90: median = 80
        judges = [
            (
                "flagship",
                _make_judge_llm(
                    tier1_scores={d: 70.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 70.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
            (
                "standard",
                _make_judge_llm(
                    tier1_scores={d: 80.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 80.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
            (
                "fast",
                _make_judge_llm(
                    tier1_scores={d: 90.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 90.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)

        _, l5 = await ensemble.run("Test output.", _make_contract())

        for ds in l5.aggregated_dimension_scores:
            assert abs(ds.score - 80.0) < 0.01
        assert l5.tier1_vetoed is False


# ---------------------------------------------------------------------------
# Dissenter veto on Tier 1
# ---------------------------------------------------------------------------


class TestDissenterVeto:
    @pytest.mark.asyncio
    async def test_no_veto_when_all_above_floor(self) -> None:
        judges = [
            ("flagship", _make_judge_llm()),
            ("fast", _make_judge_llm()),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        l3, l5 = await ensemble.run("Test output.", _make_contract())
        assert l5.tier1_vetoed is False
        assert l5.veto_events == []
        assert l3.final_score > 0

    @pytest.mark.asyncio
    async def test_veto_when_any_judge_below_tier1_floor(self) -> None:
        # Judge A scores INTENT_ALIGNMENT at 35 (below floor 40);
        # Judge B scores INTENT_ALIGNMENT at 85. Median is 60 -> above
        # floor. Without veto logic the dimension would pass. With veto
        # logic, the ensemble must reject because Judge A dissents.
        judge_a = _make_judge_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 35.0,
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 70.0,
                RubricDimension.NARRATIVE_COHERENCE: 70.0,
            },
        )
        judge_b = _make_judge_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 85.0,
                RubricDimension.INTELLECTUAL_HONESTY: 85.0,
                RubricDimension.COMPLETENESS: 85.0,
                RubricDimension.NARRATIVE_COHERENCE: 85.0,
            },
        )
        ensemble = EnsembleL3Evaluator(
            judges=[("flagship", judge_a), ("fast", judge_b)],
            profile=EvaluationProfile.DEFAULT,
        )

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.tier1_vetoed is True
        assert len(l5.veto_events) == 1
        ve = l5.veto_events[0]
        assert ve.dimension == RubricDimension.INTENT_ALIGNMENT
        assert ve.min_score == pytest.approx(35.0)
        assert ve.dissenting_judge_ids == ["flagship"]
        assert ve.judge_scores == pytest.approx({"flagship": 35.0, "fast": 85.0})

        # Aggregated Layer3Result is forced to zero
        assert l3.final_score == 0.0
        assert l3.weighted_total == 0.0
        # But the median per-dimension score is preserved for audit
        intent_score = next(
            ds.score
            for ds in l5.aggregated_dimension_scores
            if ds.dimension == RubricDimension.INTENT_ALIGNMENT
        )
        assert intent_score == pytest.approx(60.0)  # median(35, 85)

    @pytest.mark.asyncio
    async def test_no_veto_on_tier2_low_score(self) -> None:
        # Judge A scores ANALYTICAL_DEPTH at 10 (Tier 2, no floor).
        # Median still reflects the low score but no veto fires.
        judge_a = _make_judge_llm(
            tier2_scores={RubricDimension.ANALYTICAL_DEPTH: 10.0},
        )
        judge_b = _make_judge_llm(
            tier2_scores={RubricDimension.ANALYTICAL_DEPTH: 80.0},
        )
        ensemble = EnsembleL3Evaluator(
            judges=[("flagship", judge_a), ("fast", judge_b)],
            profile=EvaluationProfile.DEFAULT,
        )

        _, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.tier1_vetoed is False
        assert l5.veto_events == []

    @pytest.mark.asyncio
    async def test_veto_fires_even_when_median_above_floor(self) -> None:
        # Three judges: two score INTENT_ALIGNMENT at 80, one at 35.
        # Median = 80 (above floor 40), but veto must still trigger.
        low_tier1 = {RubricDimension.INTENT_ALIGNMENT: 35.0}
        high_tier1 = {RubricDimension.INTENT_ALIGNMENT: 80.0}
        judges = [
            ("flagship", _make_judge_llm(tier1_scores=high_tier1)),
            ("standard", _make_judge_llm(tier1_scores=high_tier1)),
            ("fast", _make_judge_llm(tier1_scores=low_tier1)),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.tier1_vetoed is True
        assert l3.final_score == 0.0
        intent_score = next(
            ds.score
            for ds in l5.aggregated_dimension_scores
            if ds.dimension == RubricDimension.INTENT_ALIGNMENT
        )
        assert intent_score == pytest.approx(80.0)


# ---------------------------------------------------------------------------
# Judge failure paths
# ---------------------------------------------------------------------------


class TestJudgeFailure:
    @pytest.mark.asyncio
    async def test_one_of_two_judges_fails_aggregates_over_survivor(self) -> None:
        failing = _make_judge_llm(raise_on="any")
        surviving = _make_judge_llm(
            tier1_scores={d: 75.0 for d in TIER_1_DIMENSIONS},
            tier2_scores={d: 75.0 for d in TIER_2_DIMENSIONS},
        )
        ensemble = EnsembleL3Evaluator(
            judges=[("flagship", failing), ("fast", surviving)],
            profile=EvaluationProfile.DEFAULT,
        )

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.all_judges_failed is False
        assert "flagship" in l5.failed_judge_ids
        assert len(l5.judge_scores) == 2
        assert sum(1 for js in l5.judge_scores if js.succeeded) == 1
        # Aggregated score reflects only the surviving judge (single value
        # -> median is that value itself). Score ~ 75 before gestalt.
        for ds in l5.aggregated_dimension_scores:
            assert abs(ds.score - 75.0) < 0.01
        assert l3.final_score > 0

    @pytest.mark.asyncio
    async def test_all_judges_fail_returns_zero_with_flag(self) -> None:
        ensemble = EnsembleL3Evaluator(
            judges=[
                ("flagship", _make_judge_llm(raise_on="any")),
                ("fast", _make_judge_llm(raise_on="any")),
            ],
            profile=EvaluationProfile.DEFAULT,
        )

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.all_judges_failed is True
        assert len(l5.failed_judge_ids) == 2
        assert l3.final_score == 0.0
        assert l3.dimension_scores == []
        assert l5.aggregated_dimension_scores == []

    @pytest.mark.asyncio
    async def test_failed_judge_error_is_captured(self) -> None:
        ensemble = EnsembleL3Evaluator(
            judges=[
                ("flagship", _make_judge_llm(raise_on="any")),
                ("fast", _make_judge_llm()),
            ],
            profile=EvaluationProfile.DEFAULT,
        )

        _, l5 = await ensemble.run("Test output.", _make_contract())

        failed = next(js for js in l5.judge_scores if not js.succeeded)
        assert failed.judge_id == "flagship"
        assert failed.error is not None
        # RuntimeError comes via retry_llm_call wrapping the original failure
        assert "mock judge failure" in failed.error or "RuntimeError" in failed.error


# ---------------------------------------------------------------------------
# Gestalt aggregation
# ---------------------------------------------------------------------------


class TestGestaltAggregation:
    @pytest.mark.asyncio
    async def test_gestalt_is_median_across_judges(self) -> None:
        # Judge gestalts: +5, +8, -2. Median = +5.
        judges = [
            ("flagship", _make_judge_llm(gestalt=5.0)),
            ("standard", _make_judge_llm(gestalt=8.0)),
            ("fast", _make_judge_llm(gestalt=-2.0)),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5 = await ensemble.run("Test output.", _make_contract())
        assert l5.ensemble_gestalt_adjustment == pytest.approx(5.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_gestalt_ignores_failed_judges(self) -> None:
        judges = [
            ("flagship", _make_judge_llm(gestalt=7.0)),
            ("fast", _make_judge_llm(raise_on="any")),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5 = await ensemble.run("Test output.", _make_contract())
        assert l5.ensemble_gestalt_adjustment == pytest.approx(7.0, abs=0.01)


# ---------------------------------------------------------------------------
# Agreement level
# ---------------------------------------------------------------------------


class TestAgreementLevel:
    @pytest.mark.asyncio
    async def test_high_agreement_when_judges_within_threshold(self) -> None:
        # Both judges 70 / 72 across the board -> spread <= 10 on all dims
        judges = [
            (
                "flagship",
                _make_judge_llm(
                    tier1_scores={d: 70.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 70.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
            (
                "fast",
                _make_judge_llm(
                    tier1_scores={d: 72.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 72.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5 = await ensemble.run("Test output.", _make_contract())
        assert l5.agreement_level == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_low_agreement_on_split_judges(self) -> None:
        # Both judges clear Tier 1 floors (each scores >= 50 there) so neither
        # bails early; then they disagree by 30+ points on every dimension.
        judges = [
            (
                "flagship",
                _make_judge_llm(
                    tier1_scores={d: 50.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 50.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
            (
                "fast",
                _make_judge_llm(
                    tier1_scores={d: 90.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 90.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5 = await ensemble.run("Test output.", _make_contract())
        # Spread on every dimension is 40 > 10 threshold -> no concordance.
        assert l5.tier1_vetoed is False
        assert l5.agreement_level == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_agreement_counts_dimensions_near_threshold_boundary(self) -> None:
        # Spread of exactly 10 should count as concordant (<= threshold).
        judges = [
            (
                "flagship",
                _make_judge_llm(
                    tier1_scores={d: 70.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 70.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
            (
                "fast",
                _make_judge_llm(
                    tier1_scores={d: 80.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 80.0 for d in TIER_2_DIMENSIONS},
                ),
            ),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5 = await ensemble.run("Test output.", _make_contract())
        assert l5.agreement_level == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Retry description signature (judge_id threading)
# ---------------------------------------------------------------------------


class TestRetryDescriptionSignature:
    @pytest.mark.asyncio
    async def test_judge_id_is_used_in_retry_description(self) -> None:
        captured: list[str] = []

        async def instrumented_llm(prompt: str) -> str:
            # Inside Layer3RubricScorer, retry_llm_call passes a description
            # to retry_llm_call, but the LLM itself doesn't see it. Instead,
            # we inspect the log output by capturing retry warnings. That is
            # overkill for a unit test; we check the trait indirectly by
            # wrapping retry.retry_llm_call with a spy.
            lower = prompt.lower()
            if "gestalt overlay" in lower:
                return json.dumps({"adjustment": 0.0})
            for dim in RubricDimension:
                header = f"# {dim.value.replace('_', ' ')} evaluation"
                if header in lower:
                    return json.dumps({"score": 70, "feedback": "ok"})
            return json.dumps({"score": 60, "feedback": "fallback"})

        import keystone.evaluator.layer3_rubric as l3mod

        original = l3mod.retry_llm_call

        async def spy(llm, prompt, *, max_retries=3, base_delay=1.0, description=""):  # noqa: ANN001
            captured.append(description)
            return await original(
                llm, prompt, max_retries=max_retries, base_delay=base_delay, description=description
            )

        l3mod.retry_llm_call = spy  # type: ignore[assignment]
        try:
            ensemble = EnsembleL3Evaluator(
                judges=[("flagship", instrumented_llm), ("fast", instrumented_llm)],
                profile=EvaluationProfile.DEFAULT,
            )
            await ensemble.run("Test output.", _make_contract())
        finally:
            l3mod.retry_llm_call = original  # type: ignore[assignment]

        # At least one description should carry each judge_id tag
        assert any("[flagship]" in d for d in captured)
        assert any("[fast]" in d for d in captured)


# ---------------------------------------------------------------------------
# Single-judge ensemble (panel minimum)
# ---------------------------------------------------------------------------


class TestSingleJudgeEnsemble:
    @pytest.mark.asyncio
    async def test_one_judge_runs_cleanly_and_reports_trivial_agreement(self) -> None:
        """A single-judge ensemble is a degenerate PoLL that the aggregator must still handle.

        Agreement is trivially 1.0 (no peers to disagree with) and the
        aggregated median is that judge's own score per dimension.
        """
        judges = [
            (
                "flagship_a",
                _make_judge_llm(
                    tier1_scores={d: 75.0 for d in TIER_1_DIMENSIONS},
                    tier2_scores={d: 75.0 for d in TIER_2_DIMENSIONS},
                    gestalt=2.0,
                ),
            ),
        ]
        ensemble = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert len(l5.judges_used) == 1
        assert len(l5.judge_scores) == 1
        assert l5.judge_scores[0].succeeded is True
        assert l5.tier1_vetoed is False
        assert l5.agreement_level == pytest.approx(1.0)
        assert l5.ensemble_gestalt_adjustment == pytest.approx(2.0, abs=0.01)
        for ds in l5.aggregated_dimension_scores:
            assert abs(ds.score - 75.0) < 0.01
        assert l3.final_score > 0


# ---------------------------------------------------------------------------
# Mixed dimension coverage (one judge bails at Tier 1)
# ---------------------------------------------------------------------------


class TestMixedDimensionCoverage:
    @pytest.mark.asyncio
    async def test_tier1_bailout_one_judge_veto_fires_and_tier2_only_has_other_judge(
        self,
    ) -> None:
        """Judge A scores below the INTENT_ALIGNMENT floor (35 < 40), so its
        Layer3Result carries only 4 Tier 1 dimension scores. Judge B passes
        Tier 1 and returns all 10 dimension scores. Expected behavior:

        - Veto fires on INTENT_ALIGNMENT (Judge A dissents, final_score = 0.0).
        - The four Tier 1 dimensions aggregate median over both judges.
        - The six Tier 2 dimensions appear with only Judge B's score.
        - Feedback on Tier 2 dims is prefixed with Judge B's id.
        """
        judge_a = _make_judge_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 35.0,
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 70.0,
                RubricDimension.NARRATIVE_COHERENCE: 70.0,
            },
        )
        judge_b = _make_judge_llm(
            tier1_scores={d: 80.0 for d in TIER_1_DIMENSIONS},
            tier2_scores={d: 80.0 for d in TIER_2_DIMENSIONS},
        )
        ensemble = EnsembleL3Evaluator(
            judges=[("flagship_a", judge_a), ("flagship_b", judge_b)],
            profile=EvaluationProfile.DEFAULT,
        )

        l3, l5 = await ensemble.run("Test output.", _make_contract())

        assert l5.tier1_vetoed is True
        assert l3.final_score == 0.0

        # Tier 1: median of both judges for each Tier 1 dim
        tier1_agg = {
            ds.dimension: ds.score
            for ds in l5.aggregated_dimension_scores
            if ds.dimension in TIER_1_DIMENSIONS
        }
        assert tier1_agg[RubricDimension.INTENT_ALIGNMENT] == pytest.approx(57.5)
        assert tier1_agg[RubricDimension.INTELLECTUAL_HONESTY] == pytest.approx(75.0)
        assert tier1_agg[RubricDimension.COMPLETENESS] == pytest.approx(75.0)
        assert tier1_agg[RubricDimension.NARRATIVE_COHERENCE] == pytest.approx(75.0)

        # Tier 2: only Judge B scored; median of one is that value
        tier2_agg = [
            ds for ds in l5.aggregated_dimension_scores if ds.dimension in TIER_2_DIMENSIONS
        ]
        assert len(tier2_agg) == len(TIER_2_DIMENSIONS)
        for ds in tier2_agg:
            assert ds.score == pytest.approx(80.0)
            # Judge B is the only voter on Tier 2 → feedback attributed solely to it
            assert ds.feedback.startswith("[flagship_b]")

        # Veto event identifies Judge A as the dissenter
        assert len(l5.veto_events) == 1
        ve = l5.veto_events[0]
        assert ve.dimension == RubricDimension.INTENT_ALIGNMENT
        assert ve.dissenting_judge_ids == ["flagship_a"]
        assert ve.judge_scores == pytest.approx({"flagship_a": 35.0, "flagship_b": 80.0})


# ---------------------------------------------------------------------------
# sub_criteria_notes per-judge attribution
# ---------------------------------------------------------------------------


class TestSubCriteriaAttribution:
    @pytest.mark.asyncio
    async def test_sub_criteria_notes_prefixed_with_judge_id(self) -> None:
        """Every aggregated sub_criteria_note should carry its originating judge_id.

        This preserves the audit trail when Phase 2 readers reconstruct which
        judge flagged which concern. Matches the existing ``[judge_id]`` prefix
        already applied to ``feedback``.
        """

        def _judge_with_notes(judge_label: str) -> LLMCallable:
            async def llm(prompt: str) -> str:
                lower = prompt.lower()
                if "gestalt overlay" in lower:
                    return json.dumps({"adjustment": 0.0, "rationale": "mock"})
                for dim in RubricDimension:
                    header = f"# {dim.value.replace('_', ' ')} evaluation"
                    if header in lower:
                        return json.dumps(
                            {
                                "score": 70,
                                "feedback": f"{judge_label} feedback on {dim.value}",
                                "sub_criteria_notes": [f"{judge_label} concern {dim.value}"],
                            }
                        )
                return json.dumps({"score": 70, "feedback": "fallback"})

            return llm

        ensemble = EnsembleL3Evaluator(
            judges=[
                ("flagship_a", _judge_with_notes("flagship_a")),
                ("flagship_b", _judge_with_notes("flagship_b")),
            ],
            profile=EvaluationProfile.DEFAULT,
        )
        _, l5 = await ensemble.run("Test output.", _make_contract())

        # Every aggregated dimension should have two sub-criteria notes, one
        # per judge, each prefixed with its judge_id.
        for ds in l5.aggregated_dimension_scores:
            assert any(note.startswith("[flagship_a]") for note in ds.sub_criteria_notes)
            assert any(note.startswith("[flagship_b]") for note in ds.sub_criteria_notes)
            # Nothing is unattributed
            for note in ds.sub_criteria_notes:
                assert note.startswith("[flagship_a]") or note.startswith("[flagship_b]")


# ---------------------------------------------------------------------------
# Dimension emphasis threading
# ---------------------------------------------------------------------------


class TestDimensionEmphasisThroughEnsemble:
    @pytest.mark.asyncio
    async def test_emphasis_shifts_ensemble_weighted_total(self) -> None:
        """A non-empty ``SprintContract.dimension_emphasis`` must flow into the
        ensemble's weighted_geometric_mean computation.

        With two judges producing identical dimension scores, the two runs
        must only differ by the weights used in aggregation. Boosting a
        high-scoring dimension raises the weighted total; damping it lowers it.
        """
        # Both judges identical. Analytical Depth scores 95; everything else 60.
        high_dim = RubricDimension.ANALYTICAL_DEPTH
        t1 = {d: 60.0 for d in TIER_1_DIMENSIONS}
        t2 = {d: (95.0 if d == high_dim else 60.0) for d in TIER_2_DIMENSIONS}
        judges: list[tuple[str, LLMCallable]] = [
            ("flagship_a", _make_judge_llm(tier1_scores=t1, tier2_scores=t2)),
            ("flagship_b", _make_judge_llm(tier1_scores=t1, tier2_scores=t2)),
        ]

        base_contract = _make_contract()
        boost_contract = base_contract.model_copy(update={"dimension_emphasis": {high_dim: 1.5}})
        damp_contract = base_contract.model_copy(update={"dimension_emphasis": {high_dim: 0.7}})

        ensemble_boost = EnsembleL3Evaluator(judges=judges, profile=EvaluationProfile.DEFAULT)
        _, l5_boost = await ensemble_boost.run("Test output.", boost_contract)

        # Re-construct to reset per-judge state
        judges2 = [
            ("flagship_a", _make_judge_llm(tier1_scores=t1, tier2_scores=t2)),
            ("flagship_b", _make_judge_llm(tier1_scores=t1, tier2_scores=t2)),
        ]
        ensemble_damp = EnsembleL3Evaluator(judges=judges2, profile=EvaluationProfile.DEFAULT)
        _, l5_damp = await ensemble_damp.run("Test output.", damp_contract)

        # Boosting the high-score dim raises the weighted total above the damped run
        assert l5_boost.ensemble_weighted_total > l5_damp.ensemble_weighted_total
        # Both paths still produce valid non-vetoed scores
        assert l5_boost.tier1_vetoed is False
        assert l5_damp.tier1_vetoed is False
