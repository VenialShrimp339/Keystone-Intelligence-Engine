"""Tests for the confidence map builder.

Validates tier routing based on agreement ratio, metadata population
for each tier, boundary values, and serialization.
"""

from __future__ import annotations

import pytest

from keystone.deliberation.aggregator import AggregatedClaim
from keystone.deliberation.confidence_builder import build_confidence_map
from keystone.deliberation.gap_detector import GapReport
from keystone.deliberation.wwhtb import WWHTBResult
from keystone.models.confidence import (
    ConfidenceMap,
    ContestedClaim,
    HighConfidenceClaim,
    InsufficientEvidenceClaim,
    ModerateConfidenceClaim,
    WeakConfidenceClaim,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _claim(
    idx: int,
    text: str,
    agreement: float,
    total: int = 4,
    confidence: float | None = None,
) -> AggregatedClaim:
    all_types = ["ach", "quantitative", "adversarial", "historical_analogy"][:total]
    agreeing_count = max(0, min(total, round(agreement * total)))
    agreeing = all_types[:agreeing_count]
    dissenting = all_types[agreeing_count:]
    conf = confidence if confidence is not None else agreement
    return AggregatedClaim(
        claim_text=text,
        index=idx,
        agreement_ratio=agreement,
        agreeing_analysts=agreeing,
        dissenting_analysts=dissenting,
        total_analysts=total,
        mean_confidence=conf,
        source_count=3,
        corroboration_count=2,
        citation_ids=["CIT-001"],
        analyst_scores={"ach": 0.8, "adversarial": 0.3},
        analyst_reasoning={
            "ach": "Supported by evidence",
            "adversarial": "Potential bias detected",
        },
    )


def _insufficient_claim(idx: int = 0, text: str = "Unknown") -> AggregatedClaim:
    return AggregatedClaim(
        claim_text=text,
        index=idx,
        agreement_ratio=0.0,
        agreeing_analysts=[],
        dissenting_analysts=[],
        total_analysts=0,
        mean_confidence=0.5,
        source_count=0,
        corroboration_count=0,
        citation_ids=[],
        analyst_scores={},
        analyst_reasoning={},
    )


def _gap_report(
    gaps: list[str] | None = None,
    absences: list[str] | None = None,
) -> GapReport:
    return GapReport(gaps=gaps or [], absence_items=absences or [])


# ---------------------------------------------------------------------------
# Tier routing tests
# ---------------------------------------------------------------------------


class TestTierRouting:
    def test_high_confidence_above_80(self) -> None:
        claims = [_claim(0, "Strong claim", 0.85)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.high_confidence_above_80pct) == 1
        assert len(cm.moderate_confidence_60_80pct) == 0
        assert isinstance(cm.high_confidence_above_80pct[0], HighConfidenceClaim)

    def test_moderate_confidence_60_80(self) -> None:
        claims = [_claim(0, "Moderate claim", 0.75)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.moderate_confidence_60_80pct) == 1
        assert isinstance(cm.moderate_confidence_60_80pct[0], ModerateConfidenceClaim)

    def test_weak_confidence_50_60(self) -> None:
        claims = [_claim(0, "Weak claim", 0.55)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.weak_confidence_50_60pct) == 1
        assert isinstance(cm.weak_confidence_50_60pct[0], WeakConfidenceClaim)

    def test_contested_below_50(self) -> None:
        claims = [_claim(0, "Contested claim", 0.30)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.contested_below_50pct) == 1
        assert isinstance(cm.contested_below_50pct[0], ContestedClaim)

    def test_insufficient_evidence_no_analysts(self) -> None:
        claims = [_insufficient_claim()]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.insufficient_evidence) == 1
        assert isinstance(cm.insufficient_evidence[0], InsufficientEvidenceClaim)


class TestAllTiersPopulated:
    def test_all_five_tiers(self) -> None:
        claims = [
            _claim(0, "High", 0.90),
            _claim(1, "Moderate", 0.70),
            _claim(2, "Weak", 0.55),
            _claim(3, "Contested", 0.25),
            _insufficient_claim(4, "Insufficient"),
        ]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert cm.tiers_populated == 5
        assert cm.total_claims == 5


# ---------------------------------------------------------------------------
# Boundary value tests
# ---------------------------------------------------------------------------


class TestBoundaryValues:
    def test_exactly_80_is_moderate(self) -> None:
        """80% agreement is moderate (>80% required for high)."""
        claims = [_claim(0, "Boundary 80", 0.80)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        assert len(cm.moderate_confidence_60_80pct) == 1
        assert len(cm.high_confidence_above_80pct) == 0

    def test_exactly_60_is_weak(self) -> None:
        """60% agreement is weak (>60% required for moderate)."""
        claims = [_claim(0, "Boundary 60", 0.60)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        assert len(cm.weak_confidence_50_60pct) == 1
        assert len(cm.moderate_confidence_60_80pct) == 0

    def test_exactly_50_is_weak(self) -> None:
        """50% agreement is weak (>=50% threshold)."""
        claims = [_claim(0, "Boundary 50", 0.50)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        assert len(cm.weak_confidence_50_60pct) == 1

    def test_49_is_contested(self) -> None:
        claims = [_claim(0, "Below 50", 0.49)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        assert len(cm.contested_below_50pct) == 1

    def test_81_is_high(self) -> None:
        claims = [_claim(0, "Just above 80", 0.81)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        assert len(cm.high_confidence_above_80pct) == 1


# ---------------------------------------------------------------------------
# Metadata population tests
# ---------------------------------------------------------------------------


class TestMetadataPopulation:
    def test_high_has_curmudgeon_challenge(self) -> None:
        claims = [_claim(0, "High claim", 0.90)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        high = cm.high_confidence_above_80pct[0]
        assert high.curmudgeon_challenge  # non-empty

    def test_high_curmudgeon_from_adversarial(self) -> None:
        """Curmudgeon challenge should come from adversarial analyst reasoning."""
        claims = [_claim(0, "High claim", 0.90)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        high = cm.high_confidence_above_80pct[0]
        assert high.curmudgeon_challenge == "Potential bias detected"

    def test_moderate_has_dissent(self) -> None:
        claims = [_claim(0, "Moderate claim", 0.75)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        mod = cm.moderate_confidence_60_80pct[0]
        assert mod.dissent

    def test_contested_has_steelmanned_view(self) -> None:
        claims = [_claim(0, "Contested claim", 0.30)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        contested = cm.contested_below_50pct[0]
        assert contested.steelmanned_opposing_view

    def test_gaps_and_absences_included(self) -> None:
        gap = _gap_report(gaps=["Missing data on X"], absences=["No info on Y"])
        cm = build_confidence_map([], [], gap, "ENG-001", "CLT-001")
        assert "Missing data on X" in cm.gaps_identified
        assert "No info on Y" in cm.absence_report

    def test_wwhtb_results_in_sensitivity(self) -> None:
        claims = [_claim(0, "Moderate claim", 0.75)]
        wwhtb = [
            WWHTBResult(
                claim_index=0, claim_text="Moderate claim",
                assumptions=["Assumption A"],
            ),
        ]
        cm = build_confidence_map(claims, wwhtb, _gap_report(), "ENG-001", "CLT-001")
        mod = cm.moderate_confidence_60_80pct[0]
        assert "Assumption A" in mod.sensitivity

    def test_methodological_agreement_string(self) -> None:
        claims = [_claim(0, "High claim", 0.90, total=4)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        high = cm.high_confidence_above_80pct[0]
        # Should contain count and analyst names
        assert "/" in high.methodological_agreement
        assert "(" in high.methodological_agreement


# ---------------------------------------------------------------------------
# Map metadata tests
# ---------------------------------------------------------------------------


class TestMapMetadata:
    def test_engagement_and_client_ids(self) -> None:
        cm = build_confidence_map([], [], _gap_report(), "ENG-X", "CLT-Y")
        assert cm.engagement_id == "ENG-X"
        assert cm.client_id == "CLT-Y"

    def test_empty_claims_produces_empty_map(self) -> None:
        cm = build_confidence_map([], [], _gap_report(), "ENG-001", "CLT-001")
        assert cm.total_claims == 0
        assert cm.tiers_populated == 0

    def test_serializes_to_json(self) -> None:
        claims = [_claim(0, "Test", 0.90)]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")
        json_str = cm.model_dump_json()
        restored = ConfidenceMap.model_validate_json(json_str)
        assert restored.total_claims == cm.total_claims


# ---------------------------------------------------------------------------
# Provenance propagation tests
# ---------------------------------------------------------------------------


class TestProvenancePropagation:
    def _claim_with_provenance(
        self,
        idx: int,
        text: str,
        agreement: float,
        aggregated_claim_id: str,
        task_ids: list[str],
        total: int = 4,
    ) -> AggregatedClaim:
        all_types = ["ach", "quantitative", "adversarial", "historical_analogy"][:total]
        agreeing_count = max(0, min(total, round(agreement * total)))
        agreeing = all_types[:agreeing_count]
        dissenting = all_types[agreeing_count:]
        return AggregatedClaim(
            claim_text=text,
            index=idx,
            agreement_ratio=agreement,
            agreeing_analysts=agreeing,
            dissenting_analysts=dissenting,
            total_analysts=total,
            mean_confidence=agreement,
            source_count=3,
            corroboration_count=2,
            citation_ids=["CIT-001"],
            analyst_scores={"ach": 0.8, "adversarial": 0.3},
            analyst_reasoning={
                "ach": "Supported by evidence",
                "adversarial": "Potential bias detected",
            },
            aggregated_claim_id=aggregated_claim_id,
            task_ids=task_ids,
        )

    def test_confidence_map_claims_carry_task_provenance(self) -> None:
        """Tier claims carry aggregated_claim_id and task_ids from AggregatedClaim.
        ConfidenceMap.provenance_index maps each aggregated_claim_id to its task_ids.
        """
        high_claim = self._claim_with_provenance(
            0, "High claim", 0.90, "AGG-aaa111", ["TASK-001", "TASK-002"]
        )
        moderate_claim = self._claim_with_provenance(
            1, "Moderate claim", 0.70, "AGG-bbb222", ["TASK-003"]
        )
        weak_claim = self._claim_with_provenance(
            2, "Weak claim", 0.55, "AGG-ccc333", ["TASK-001"]
        )
        contested_claim = self._claim_with_provenance(
            3, "Contested claim", 0.30, "AGG-ddd444", ["TASK-004"]
        )

        cm = build_confidence_map(
            [high_claim, moderate_claim, weak_claim, contested_claim],
            [],
            _gap_report(),
            "ENG-001",
            "CLT-001",
        )

        # Each tier claim carries the provenance fields
        high = cm.high_confidence_above_80pct[0]
        assert high.aggregated_claim_id == "AGG-aaa111"
        assert high.task_ids == ["TASK-001", "TASK-002"]

        mod = cm.moderate_confidence_60_80pct[0]
        assert mod.aggregated_claim_id == "AGG-bbb222"
        assert mod.task_ids == ["TASK-003"]

        weak = cm.weak_confidence_50_60pct[0]
        assert weak.aggregated_claim_id == "AGG-ccc333"
        assert weak.task_ids == ["TASK-001"]

        cont = cm.contested_below_50pct[0]
        assert cont.aggregated_claim_id == "AGG-ddd444"
        assert cont.task_ids == ["TASK-004"]

        # provenance_index is built correctly on ConfidenceMap
        assert cm.provenance_index["AGG-aaa111"] == ["TASK-001", "TASK-002"]
        assert cm.provenance_index["AGG-bbb222"] == ["TASK-003"]
        assert cm.provenance_index["AGG-ccc333"] == ["TASK-001"]
        assert cm.provenance_index["AGG-ddd444"] == ["TASK-004"]

    def test_insufficient_claim_carries_provenance(self) -> None:
        """InsufficientEvidenceClaim also carries provenance fields."""
        from keystone.deliberation.aggregator import AggregatedClaim as AC
        insuf = AC(
            claim_text="Unknown",
            index=0,
            agreement_ratio=0.0,
            agreeing_analysts=[],
            dissenting_analysts=[],
            total_analysts=0,
            mean_confidence=0.5,
            source_count=0,
            corroboration_count=0,
            citation_ids=[],
            analyst_scores={},
            analyst_reasoning={},
            aggregated_claim_id="AGG-eee555",
            task_ids=["TASK-005"],
        )
        cm = build_confidence_map([insuf], [], _gap_report(), "ENG-001", "CLT-001")

        ie = cm.insufficient_evidence[0]
        assert ie.aggregated_claim_id == "AGG-eee555"
        assert ie.task_ids == ["TASK-005"]
        assert cm.provenance_index["AGG-eee555"] == ["TASK-005"]

    def test_claims_without_complete_provenance_not_in_provenance_index(self) -> None:
        """Claims missing aggregated IDs or task_ids are omitted from provenance_index."""
        no_id = _claim(0, "No ID claim", 0.90)
        no_tasks = _claim(1, "No task IDs claim", 0.90).model_copy(
            update={"aggregated_claim_id": "AGG-missing-tasks", "task_ids": []}
        )
        claims = [no_id, no_tasks]
        cm = build_confidence_map(claims, [], _gap_report(), "ENG-001", "CLT-001")

        assert len(cm.provenance_index) == 0
        assert "AGG-missing-tasks" not in cm.provenance_index
