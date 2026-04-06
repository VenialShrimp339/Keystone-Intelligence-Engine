"""Tests for the Deliberation analyst module."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from keystone.deliberation.analyst import (
    Analyst,
    AnalystOutput,
    InputClaim,
    extract_claims,
)
from keystone.models.agents import DeliberationAnalystType
from keystone.models.citations import Citation, ConfidenceTier, SourceType
from keystone.models.research import FindingClaim, StructuredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cit(cid: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLT-001",
        url=f"https://example.com/{cid}",
        title=f"Source {cid}",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _finding(agent_id: str, claims: list[FindingClaim]) -> StructuredFinding:
    return StructuredFinding(
        task_id="TASK-001",
        agent_id=agent_id,
        engagement_id="ENG-001",
        client_id="CLT-001",
        agent_type="quantitative",
        claims=claims,
        absence_report=["No data on Eastern European markets"],
        sources_consulted=5,
        tokens_consumed=1000,
    )


def _fc(text: str, confidence: float = 0.8) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence="Supporting evidence",
        citations=[_cit()],
        confidence=confidence,
        confidence_tier=ConfidenceTier.HIGH,
    )


def _mock_analyst_llm(scores: list[dict] | None = None):
    """Return a mock LLM that produces analyst scores."""
    default_scores = [
        {"index": 0, "confidence": 0.85, "source_count": 3, "reasoning": "Strong quantitative evidence"},
        {"index": 1, "confidence": 0.45, "source_count": 1, "reasoning": "Weak supporting data"},
    ]
    output = scores or default_scores

    async def llm(prompt: str) -> str:
        return json.dumps(output)

    return llm


# ---------------------------------------------------------------------------
# Extract claims tests
# ---------------------------------------------------------------------------


class TestExtractClaims:
    def test_extracts_all_claims(self) -> None:
        f1 = _finding("agent-1", [_fc("Market is $50B"), _fc("Growth is 10%")])
        f2 = _finding("agent-2", [_fc("Revenue grew 15%")])
        claims = extract_claims([f1, f2])
        assert len(claims) == 3
        assert claims[0].index == 0
        assert claims[1].index == 1
        assert claims[2].index == 2

    def test_preserves_metadata(self) -> None:
        f1 = _finding("agent-1", [_fc("Market is $50B", confidence=0.7)])
        claims = extract_claims([f1])
        assert claims[0].task_id == "TASK-001"
        assert claims[0].agent_id == "agent-1"
        assert claims[0].original_confidence == 0.7
        assert len(claims[0].citation_ids) == 1

    def test_empty_findings(self) -> None:
        assert extract_claims([]) == []

    def test_findings_with_no_claims(self) -> None:
        f1 = _finding("agent-1", [])
        assert extract_claims([f1]) == []


# ---------------------------------------------------------------------------
# Analyst tests
# ---------------------------------------------------------------------------


class TestAnalyst:
    @pytest.mark.asyncio
    async def test_produces_scored_claims(self) -> None:
        llm = _mock_analyst_llm()
        analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.ACH)
        claims = [
            InputClaim(
                index=0, task_id="T1", agent_id="A1", text="Claim A",
                evidence="Evidence A", citation_ids=["CIT-001"],
                original_confidence=0.8,
            ),
            InputClaim(
                index=1, task_id="T1", agent_id="A1", text="Claim B",
                evidence="Evidence B", citation_ids=["CIT-002"],
                original_confidence=0.6,
            ),
        ]
        output = await analyst.analyze(claims)

        assert isinstance(output, AnalystOutput)
        assert output.analyst_type == "ach"
        assert len(output.scored_claims) == 2
        assert output.scored_claims[0].analyst_confidence == 0.85
        assert output.scored_claims[1].analyst_confidence == 0.45

    @pytest.mark.asyncio
    async def test_each_analyst_type_valid(self) -> None:
        for at in DeliberationAnalystType:
            llm = _mock_analyst_llm([
                {"index": 0, "confidence": 0.7, "source_count": 2, "reasoning": "test"},
            ])
            analyst = Analyst(llm=llm, analyst_type=at)
            claims = [
                InputClaim(
                    index=0, task_id="T1", agent_id="A1", text="Test",
                    evidence="Ev", citation_ids=["CIT-001"],
                    original_confidence=0.5,
                ),
            ]
            output = await analyst.analyze(claims)
            assert output.analyst_type == at.value
            assert len(output.scored_claims) == 1

    @pytest.mark.asyncio
    async def test_empty_claims_returns_empty(self) -> None:
        llm = _mock_analyst_llm()
        analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.ADVERSARIAL)
        output = await analyst.analyze([])
        assert output.scored_claims == []

    @pytest.mark.asyncio
    async def test_malformed_json_fallback(self) -> None:
        async def bad_llm(prompt: str) -> str:
            return "not valid json"

        analyst = Analyst(llm=bad_llm, analyst_type=DeliberationAnalystType.QUANTITATIVE)
        claims = [
            InputClaim(
                index=0, task_id="T1", agent_id="A1", text="Claim",
                evidence="Ev", citation_ids=["CIT-001"],
                original_confidence=0.7,
            ),
        ]
        output = await analyst.analyze(claims)
        assert len(output.scored_claims) == 1
        assert output.scored_claims[0].analyst_confidence == 0.7

    @pytest.mark.asyncio
    async def test_analyst_id_generated(self) -> None:
        llm = _mock_analyst_llm()
        analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.ACH)
        assert analyst.analyst_id.startswith("analyst-ach-")

    @pytest.mark.asyncio
    async def test_custom_analyst_id(self) -> None:
        llm = _mock_analyst_llm()
        analyst = Analyst(
            llm=llm, analyst_type=DeliberationAnalystType.ACH, analyst_id="custom-id"
        )
        assert analyst.analyst_id == "custom-id"

    @pytest.mark.asyncio
    async def test_source_count_from_llm(self) -> None:
        llm = _mock_analyst_llm([
            {"index": 0, "confidence": 0.7, "source_count": 5, "reasoning": "test"},
        ])
        analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.ACH)
        claims = [
            InputClaim(
                index=0, task_id="T1", agent_id="A1", text="Claim",
                evidence="Ev", citation_ids=["CIT-001"],
                original_confidence=0.5,
            ),
        ]
        output = await analyst.analyze(claims)
        assert output.scored_claims[0].source_count == 5

    @pytest.mark.asyncio
    async def test_missing_index_gets_fallback(self) -> None:
        """If LLM returns scores for only some claims, missing ones get fallback."""
        llm = _mock_analyst_llm([
            {"index": 0, "confidence": 0.9, "source_count": 3, "reasoning": "ok"},
            # index 1 is missing
        ])
        analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.ACH)
        claims = [
            InputClaim(
                index=0, task_id="T1", agent_id="A1", text="Present",
                evidence="Ev", citation_ids=["CIT-001"], original_confidence=0.5,
            ),
            InputClaim(
                index=1, task_id="T1", agent_id="A1", text="Missing",
                evidence="Ev", citation_ids=["CIT-002"], original_confidence=0.6,
            ),
        ]
        output = await analyst.analyze(claims)
        assert output.scored_claims[0].analyst_confidence == 0.9
        assert output.scored_claims[1].analyst_confidence == 0.6  # fallback to original
