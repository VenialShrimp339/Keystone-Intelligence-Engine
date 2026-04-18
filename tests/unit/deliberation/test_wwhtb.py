"""Tests for the WWHTB (What Would You Have to Believe?) module."""

from __future__ import annotations

import json

import pytest

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.deliberation.wwhtb import CONFIDENCE_THRESHOLD, run_wwhtb


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _aggregated(
    idx: int = 0,
    text: str = "Test claim",
    confidence: float = 0.4,
) -> AggregatedClaim:
    return AggregatedClaim(
        claim_text=text,
        index=idx,
        agreement_ratio=confidence,
        agreeing_analysts=["ach"],
        dissenting_analysts=["adversarial"],
        total_analysts=2,
        mean_confidence=confidence,
        source_count=3,
        corroboration_count=1,
        citation_ids=["CIT-001"],
        analyst_scores={"ach": confidence + 0.1, "adversarial": confidence - 0.1},
        analyst_reasoning={"ach": "Supported", "adversarial": "Questioned"},
    )


def _mock_wwhtb_llm():
    async def llm(prompt: str) -> str:
        return json.dumps(
            {
                "assumptions": [
                    "Market growth continues at current rate",
                    "No major regulatory changes",
                ],
            }
        )

    return llm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWWHTBFiring:
    @pytest.mark.asyncio
    async def test_fires_for_low_confidence(self) -> None:
        """WWHTB fires for claims below 0.6 confidence."""
        claims = [_aggregated(0, "Low conf claim", 0.4)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)

        assert len(results) == 1
        assert results[0].claim_index == 0
        assert len(results[0].assumptions) == 2

    @pytest.mark.asyncio
    async def test_does_not_fire_for_high_confidence(self) -> None:
        """WWHTB does NOT fire for claims above 0.6."""
        claims = [_aggregated(0, "High conf claim", 0.85)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_threshold_exactly_06_does_not_fire(self) -> None:
        """Claims at exactly 0.6 should NOT trigger WWHTB (< not <=)."""
        claims = [_aggregated(0, "Boundary claim", 0.6)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_threshold_just_below_fires(self) -> None:
        """Claims at 0.59 should trigger WWHTB."""
        claims = [_aggregated(0, "Below threshold", 0.59)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert len(results) == 1


class TestWWHTBContent:
    @pytest.mark.asyncio
    async def test_multiple_low_confidence_claims(self) -> None:
        """All low-confidence claims get WWHTB evaluation."""
        claims = [
            _aggregated(0, "Low A", 0.3),
            _aggregated(1, "High B", 0.9),
            _aggregated(2, "Low C", 0.5),
        ]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert len(results) == 2
        indices = {r.claim_index for r in results}
        assert indices == {0, 2}

    @pytest.mark.asyncio
    async def test_assumptions_populated(self) -> None:
        claims = [_aggregated(0, "Low claim", 0.3)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert results[0].assumptions[0] == "Market growth continues at current rate"

    @pytest.mark.asyncio
    async def test_malformed_json_fallback(self) -> None:
        async def bad_llm(prompt: str) -> str:
            return "not json"

        claims = [_aggregated(0, "Claim", 0.4)]
        results = await run_wwhtb(bad_llm, claims)
        assert len(results) == 1
        assert results[0].assumptions == ["Unable to elicit assumptions"]


class TestWWHTBEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_claims(self) -> None:
        results = await run_wwhtb(_mock_wwhtb_llm(), [])
        assert results == []

    @pytest.mark.asyncio
    async def test_all_above_threshold(self) -> None:
        claims = [_aggregated(0, "A", 0.7), _aggregated(1, "B", 0.8)]
        results = await run_wwhtb(_mock_wwhtb_llm(), claims)
        assert results == []

    def test_threshold_value(self) -> None:
        assert CONFIDENCE_THRESHOLD == 0.6
