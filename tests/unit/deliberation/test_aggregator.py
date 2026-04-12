"""Tests for the Deliberation aggregator module.

Validates: claim-level SELECTION (not blending), agreement ratio
computation, dispute resolution via judge LLM, and post-selection
consistency check.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from keystone.deliberation.aggregator import Aggregator, AggregatedClaim
from keystone.deliberation.analyst import AnalystOutput, InputClaim, ScoredClaim
from keystone.models.citations import (
    Citation,
    CitationAlias,
    CitationManifest,
    SourceType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _claim(idx: int = 0, text: str = "Test claim") -> InputClaim:
    return InputClaim(
        index=idx, task_id="T1", agent_id="A1", text=text,
        evidence="Evidence", citation_ids=["CIT-001"],
        original_confidence=0.7,
    )


def _analyst_output(analyst_type: str, scored: list[ScoredClaim]) -> AnalystOutput:
    return AnalystOutput(
        analyst_id=f"analyst-{analyst_type}-001",
        analyst_type=analyst_type,
        scored_claims=scored,
    )


def _scored(idx: int, confidence: float, reasoning: str = "test") -> ScoredClaim:
    return ScoredClaim(
        index=idx, claim_text="Test claim",
        analyst_confidence=confidence, source_count=3, reasoning=reasoning,
    )


def _mock_judge(selected: str = "ach", reasoning: str = "Best supported"):
    """Mock judge LLM that always selects the specified analyst."""
    async def llm(prompt: str) -> str:
        if "contradict" in prompt.lower():
            return json.dumps({"contradictions": []})
        return json.dumps({
            "selected_analyst": selected,
            "reasoning": reasoning,
        })
    return llm


def _shared_canonical_manifest() -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        citations=[
            Citation(
                citation_id="CAN-001",
                engagement_id="ENG-001",
                client_id="CLIENT-001",
                url="https://example.com/shared-source",
                title="Shared Source",
                source_type=SourceType.REPORT,
                quality_score=0.9,
                access_date=datetime(2026, 4, 1),
                found_by_agents=["A1", "A2"],
            )
        ],
        aliases=[
            CitationAlias(
                source_instance_id="CIT-pass",
                canonical_citation_id="CAN-001",
                engagement_id="ENG-001",
                task_id="task_pass",
                agent_id="A1",
            ),
            CitationAlias(
                source_instance_id="CIT-fail",
                canonical_citation_id="CAN-001",
                engagement_id="ENG-001",
                task_id="task_fail",
                agent_id="A2",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Agreement / consensus tests
# ---------------------------------------------------------------------------


class TestConsensus:
    @pytest.mark.asyncio
    async def test_consensus_no_dispute(self) -> None:
        """When analysts agree, use consensus (no judge call)."""
        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.85)]),
            _analyst_output("quantitative", [_scored(0, 0.80)]),
            _analyst_output("adversarial", [_scored(0, 0.78)]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert len(result) == 1
        assert result[0].agreement_ratio == 1.0  # all >= 0.5
        assert result[0].selected_from is None
        assert 0.78 <= result[0].mean_confidence <= 0.85

    @pytest.mark.asyncio
    async def test_agreement_ratio_computation(self) -> None:
        """agreement_ratio = count(confidence >= 0.5) / total."""
        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.80)]),
            _analyst_output("quantitative", [_scored(0, 0.70)]),
            _analyst_output("adversarial", [_scored(0, 0.30)]),
            _analyst_output("historical_analogy", [_scored(0, 0.60)]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert result[0].agreement_ratio == 0.75  # 3/4

    @pytest.mark.asyncio
    async def test_dissenting_analysts_tracked(self) -> None:
        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.80)]),
            _analyst_output("adversarial", [_scored(0, 0.30)]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert "ach" in result[0].agreeing_analysts
        assert "adversarial" in result[0].dissenting_analysts


# ---------------------------------------------------------------------------
# Selection (not blending) tests
# ---------------------------------------------------------------------------


class TestSelection:
    @pytest.mark.asyncio
    async def test_dispute_triggers_judge_selection(self) -> None:
        """When analysts disagree significantly, judge selects one."""
        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.90, "Strong ACH support")]),
            _analyst_output("adversarial", [_scored(0, 0.20, "Major weakness found")]),
            _analyst_output("quantitative", [_scored(0, 0.85, "Numbers check out")]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge("ach"))
        result = await aggregator.aggregate(outputs, claims)

        assert len(result) == 1
        assert result[0].selected_from == "ach"
        assert result[0].selection_reasoning is not None

    @pytest.mark.asyncio
    async def test_selection_not_blending(self) -> None:
        """Judge SELECTS one analyst's confidence, not the average."""
        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.90)]),
            _analyst_output("adversarial", [_scored(0, 0.10)]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge("ach"))
        result = await aggregator.aggregate(outputs, claims)

        # Selected confidence from ach (0.90), not average (0.50)
        assert result[0].selected_from == "ach"
        assert result[0].mean_confidence == 0.90

    @pytest.mark.asyncio
    async def test_judge_fallback_on_bad_json(self) -> None:
        """If judge returns bad JSON, fallback to highest confidence analyst."""
        async def bad_judge(prompt: str) -> str:
            if "contradict" in prompt.lower():
                return json.dumps({"contradictions": []})
            return "not json"

        claims = [_claim(0)]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.90)]),
            _analyst_output("adversarial", [_scored(0, 0.10)]),
        ]
        aggregator = Aggregator(judge_llm=bad_judge)
        result = await aggregator.aggregate(outputs, claims)

        assert result[0].selected_from == "ach"  # highest confidence
        assert "Fallback" in (result[0].selection_reasoning or "")


# ---------------------------------------------------------------------------
# Consistency check tests
# ---------------------------------------------------------------------------


class TestConsistencyCheck:
    @pytest.mark.asyncio
    async def test_consistency_check_flags_contradictions(self) -> None:
        claims = [_claim(0, "Market is growing"), _claim(1, "Market is shrinking")]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.80), _scored(1, 0.70)]),
        ]

        async def judge_with_contradictions(prompt: str) -> str:
            if "contradict" in prompt.lower():
                return json.dumps({"contradictions": [
                    {"claim_a": 0, "claim_b": 1, "issue": "Direct contradiction"},
                ]})
            return json.dumps({"selected_analyst": "ach", "reasoning": "ok"})

        aggregator = Aggregator(judge_llm=judge_with_contradictions)
        result = await aggregator.aggregate(outputs, claims)

        assert any(not c.consistency_passed for c in result)

    @pytest.mark.asyncio
    async def test_no_contradictions_all_pass(self) -> None:
        claims = [_claim(0, "A"), _claim(1, "B")]
        outputs = [
            _analyst_output("ach", [_scored(0, 0.80), _scored(1, 0.70)]),
        ]
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert all(c.consistency_passed for c in result)


class TestProvenance:
    @pytest.mark.asyncio
    async def test_shared_canonical_support_does_not_widen_task_ids(self) -> None:
        claims = [
            InputClaim(
                index=0,
                task_id="task_pass",
                agent_id="A1",
                text="Passed claim",
                evidence="Shared source evidence",
                citation_ids=["CIT-pass"],
                original_confidence=0.8,
            ),
            InputClaim(
                index=1,
                task_id="task_fail",
                agent_id="A2",
                text="Failed claim",
                evidence="Same shared source evidence",
                citation_ids=["CIT-fail"],
                original_confidence=0.7,
            ),
        ]
        outputs = [_analyst_output("ach", [_scored(0, 0.85), _scored(1, 0.82)])]

        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(
            outputs,
            claims,
            manifest=_shared_canonical_manifest(),
        )

        by_text = {claim.claim_text: claim for claim in result}
        assert by_text["Passed claim"].citation_ids == ["CAN-001"]
        assert by_text["Failed claim"].citation_ids == ["CAN-001"]
        assert by_text["Passed claim"].task_ids == ["task_pass"]
        assert by_text["Failed claim"].task_ids == ["task_fail"]
        assert by_text["Failed claim"].corroboration_count == 2


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_claims(self) -> None:
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate([], [])
        assert result == []

    @pytest.mark.asyncio
    async def test_single_analyst(self) -> None:
        claims = [_claim(0)]
        outputs = [_analyst_output("ach", [_scored(0, 0.75)])]
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert len(result) == 1
        assert result[0].total_analysts == 1
        assert result[0].mean_confidence == 0.75

    @pytest.mark.asyncio
    async def test_no_analysts_scored_claim(self) -> None:
        """Claim not scored by any analyst gets unscored treatment."""
        claims = [_claim(0)]
        outputs = [_analyst_output("ach", [])]  # analyst returned no scores
        aggregator = Aggregator(judge_llm=_mock_judge())
        result = await aggregator.aggregate(outputs, claims)

        assert len(result) == 1
        assert result[0].total_analysts == 0
        assert result[0].mean_confidence == 0.7  # original_confidence
