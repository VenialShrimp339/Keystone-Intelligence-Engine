"""Tests for SubQuery and PartialFinding models."""

import pytest

from keystone.models.sub_research import PartialClaim, PartialFinding, SubQuery


class TestSubQuery:
    def test_valid_subquery(self) -> None:
        sq = SubQuery(
            sub_id="SUB-001",
            objective="Analyze SEC filings for revenue trends",
            methodology="financial_data",
            allowed_tools=["edgar_filings", "exa_search"],
            anti_confirmatory_framing=(
                "Evaluate whether revenue growth is sustainable, "
                "including evidence of deceleration or one-time boosts"
            ),
            stop_criterion="3+ independent sources corroborate or contradict",
            output_focus="quantitative financial metrics",
        )
        assert sq.sub_id == "SUB-001"
        assert sq.methodology == "financial_data"
        assert len(sq.allowed_tools) == 2

    def test_anti_confirmatory_validator_rejects_find_evidence_for(self) -> None:
        with pytest.raises(ValueError, match="Anti-confirmatory"):
            SubQuery(
                sub_id="SUB-001",
                objective="Test",
                methodology="financial_data",
                allowed_tools=["exa_search"],
                anti_confirmatory_framing="Find evidence for market growth",
                stop_criterion="done",
                output_focus="data",
            )

    def test_anti_confirmatory_validator_rejects_prove_that(self) -> None:
        with pytest.raises(ValueError, match="Anti-confirmatory"):
            SubQuery(
                sub_id="SUB-001",
                objective="Test",
                methodology="financial_data",
                allowed_tools=["exa_search"],
                anti_confirmatory_framing="Prove that the market is growing",
                stop_criterion="done",
                output_focus="data",
            )

    def test_anti_confirmatory_validator_rejects_confirm_that(self) -> None:
        with pytest.raises(ValueError, match="Anti-confirmatory"):
            SubQuery(
                sub_id="SUB-001",
                objective="Test",
                methodology="financial_data",
                allowed_tools=["exa_search"],
                anti_confirmatory_framing="Confirm that revenue is increasing",
                stop_criterion="done",
                output_focus="data",
            )

    def test_empty_tools_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            SubQuery(
                sub_id="SUB-001",
                objective="Test",
                methodology="financial_data",
                allowed_tools=[],
                anti_confirmatory_framing="Evaluate whether X holds",
                stop_criterion="done",
                output_focus="data",
            )

    def test_three_distinct_methodologies(self) -> None:
        """Phase 1 invariant: 3 sub-queries with distinct methodologies."""
        sqs = [
            SubQuery(
                sub_id=f"SUB-{i + 1:03d}",
                objective=f"Objective {i}",
                methodology=m,
                allowed_tools=["exa_search"],
                anti_confirmatory_framing=f"Evaluate whether claim {i} holds",
                stop_criterion="done",
                output_focus="data",
            )
            for i, m in enumerate(["financial_data", "market_intelligence", "academic_technical"])
        ]
        methodologies = {sq.methodology for sq in sqs}
        assert len(methodologies) == 3


class TestPartialFinding:
    def test_partial_finding_with_claims(self) -> None:
        pf = PartialFinding(
            sub_id="SUB-001",
            task_id="task_001",
            methodology="financial_data",
            claims=[
                PartialClaim(
                    text="Revenue grew 25% YoY",
                    evidence="SEC filing Q4 2025",
                    citation_refs=["SRC-001"],
                    confidence=0.85,
                    sub_id="SUB-001",
                ),
                PartialClaim(
                    text="Operating margin declining",
                    evidence="Earnings call transcript",
                    citation_refs=["SRC-002"],
                    confidence=0.7,
                    caveats=["Single quarter data point"],
                    sub_id="SUB-001",
                ),
            ],
            sources_consulted=5,
            tokens_consumed=1200,
            absence_items=["No data on international revenue breakdown"],
        )
        assert len(pf.claims) == 2
        assert all(c.sub_id == "SUB-001" for c in pf.claims)
        assert pf.sources_consulted == 5

    def test_partial_claim_sub_id_attribution(self) -> None:
        """Every claim carries the sub_id of its producing sub-agent."""
        claim = PartialClaim(
            text="Test claim",
            evidence="Test evidence",
            citation_refs=["SRC-001"],
            confidence=0.75,
            sub_id="SUB-002",
        )
        assert claim.sub_id == "SUB-002"

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValueError):
            PartialClaim(
                text="Bad",
                evidence="Bad",
                citation_refs=["SRC-001"],
                confidence=1.5,
                sub_id="SUB-001",
            )
        with pytest.raises(ValueError):
            PartialClaim(
                text="Bad",
                evidence="Bad",
                citation_refs=["SRC-001"],
                confidence=-0.1,
                sub_id="SUB-001",
            )
