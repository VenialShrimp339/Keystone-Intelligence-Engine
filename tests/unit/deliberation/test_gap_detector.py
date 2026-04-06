"""Tests for the gap detector module."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.deliberation.gap_detector import LOW_CONFIDENCE_GAP_THRESHOLD, detect_gaps
from keystone.models.citations import Citation, ConfidenceTier, SourceType
from keystone.models.research import FindingClaim, StructuredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cit() -> Citation:
    return Citation(
        citation_id="CIT-001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        url="https://example.com",
        title="Source",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _finding(
    absences: list[str] | None = None,
    gaps: list[str] | None = None,
) -> StructuredFinding:
    return StructuredFinding(
        task_id="TASK-001",
        agent_id="agent-1",
        engagement_id="ENG-001",
        client_id="CLT-001",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="Test claim",
                evidence="Evidence",
                citations=[_cit()],
                confidence=0.8,
                confidence_tier=ConfidenceTier.HIGH,
            ),
        ],
        absence_report=absences or [],
        gaps=gaps or [],
        sources_consulted=5,
        tokens_consumed=1000,
    )


def _agg_claim(
    idx: int = 0,
    confidence: float = 0.8,
    consistent: bool = True,
) -> AggregatedClaim:
    return AggregatedClaim(
        claim_text="Test claim",
        index=idx,
        agreement_ratio=confidence,
        agreeing_analysts=["ach"],
        dissenting_analysts=[],
        total_analysts=1,
        mean_confidence=confidence,
        source_count=3,
        corroboration_count=1,
        citation_ids=["CIT-001"],
        analyst_scores={"ach": confidence},
        analyst_reasoning={},
        consistency_passed=consistent,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAbsenceReports:
    def test_absence_reports_collected(self) -> None:
        findings = [
            _finding(absences=["No Eastern European data"]),
            _finding(absences=["No pricing data for Q4"]),
        ]
        report = detect_gaps(findings, [])
        assert len(report.absence_items) == 2
        assert "No Eastern European data" in report.absence_items

    def test_empty_absence_reports(self) -> None:
        findings = [_finding(absences=[])]
        report = detect_gaps(findings, [])
        assert report.absence_items == []


class TestLowConfidenceGaps:
    def test_low_confidence_creates_gap(self) -> None:
        claims = [_agg_claim(0, confidence=0.3)]
        report = detect_gaps([], claims)
        assert len(report.gaps) == 1
        assert "Low confidence" in report.gaps[0]

    def test_high_confidence_no_gap(self) -> None:
        claims = [_agg_claim(0, confidence=0.8)]
        report = detect_gaps([], claims)
        assert len(report.gaps) == 0

    def test_threshold_boundary(self) -> None:
        claims = [_agg_claim(0, confidence=LOW_CONFIDENCE_GAP_THRESHOLD)]
        report = detect_gaps([], claims)
        assert len(report.gaps) == 0  # exactly at threshold, not below


class TestConsistencyGaps:
    def test_consistency_failure_creates_gap(self) -> None:
        claims = [_agg_claim(0, confidence=0.8, consistent=False)]
        report = detect_gaps([], claims)
        assert any("Consistency" in g for g in report.gaps)

    def test_consistent_claims_no_gap(self) -> None:
        claims = [_agg_claim(0, confidence=0.8, consistent=True)]
        report = detect_gaps([], claims)
        assert not any("Consistency" in g for g in report.gaps)


class TestFindingGaps:
    def test_finding_gaps_included(self) -> None:
        findings = [_finding(gaps=["Insufficient data on market size"])]
        report = detect_gaps(findings, [])
        assert "Insufficient data on market size" in report.gaps

    def test_no_duplicate_gaps(self) -> None:
        """Same gap from finding shouldn't duplicate."""
        findings = [_finding(gaps=["Gap X"])]
        report = detect_gaps(findings, [])
        assert report.gaps.count("Gap X") == 1


class TestCombinedSources:
    def test_all_gap_sources_combined(self) -> None:
        findings = [_finding(absences=["Missing A"], gaps=["Gap X"])]
        claims = [_agg_claim(0, confidence=0.2)]
        report = detect_gaps(findings, claims)

        assert len(report.absence_items) == 1
        assert len(report.gaps) >= 2  # gap from finding + gap from low confidence


class TestEdgeCases:
    def test_empty_inputs(self) -> None:
        report = detect_gaps([], [])
        assert report.gaps == []
        assert report.absence_items == []

    def test_threshold_value(self) -> None:
        assert LOW_CONFIDENCE_GAP_THRESHOLD == 0.4
