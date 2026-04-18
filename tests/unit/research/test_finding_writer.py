"""Tests for StructuredFinding validation and construction.

Structural enforcement: citations required, confidence scores present,
absence report non-empty. These are the core acceptance criteria
for Component #7.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from keystone.models.citations import Citation, ConfidenceTier, SourceType
from keystone.models.research import FindingStatus
from keystone.research.finding_writer import (
    FindingValidationError,
    FindingWriter,
    _tier_from_confidence,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_citation(cit_id: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=cit_id,
        engagement_id="eng_001",
        client_id="client_001",
        url="https://example.com/report",
        title="EV Battery Market Report",
        access_date=datetime.now(UTC),
        source_type=SourceType.REPORT,
        quality_score=0.8,
    )


def _make_raw_claim(**overrides) -> dict:
    base = {
        "text": "Global EV battery market projected at $150B by 2030",
        "evidence": "BloombergNEF and IEA projections converge on this range",
        "citations": [_make_citation()],
        "confidence": 0.85,
        "caveats": ["Projections vary by 20% across sources"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Confidence tier mapping
# ---------------------------------------------------------------------------


def test_tier_high() -> None:
    assert _tier_from_confidence(0.85) == ConfidenceTier.HIGH


def test_tier_moderate() -> None:
    assert _tier_from_confidence(0.65) == ConfidenceTier.MODERATE


def test_tier_weak() -> None:
    assert _tier_from_confidence(0.55) == ConfidenceTier.WEAK


def test_tier_contested() -> None:
    assert _tier_from_confidence(0.3) == ConfidenceTier.CONTESTED


def test_tier_insufficient() -> None:
    assert _tier_from_confidence(0.0) == ConfidenceTier.INSUFFICIENT


# ---------------------------------------------------------------------------
# Valid finding construction
# ---------------------------------------------------------------------------


def test_build_valid_finding() -> None:
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["No sub-Saharan Africa market data found"],
        sources_consulted=5,
        tokens_consumed=1200,
    )

    assert finding.task_id == "task_001"
    assert finding.agent_id == "agent_001"
    assert len(finding.claims) == 1
    assert finding.claims[0].confidence == 0.85
    assert finding.claims[0].confidence_tier == ConfidenceTier.HIGH
    assert len(finding.claims[0].citations) == 1
    assert finding.absence_report == ["No sub-Saharan Africa market data found"]
    assert finding.status == FindingStatus.COMPLETE


def test_build_finding_with_multiple_claims() -> None:
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="qualitative",
        raw_claims=[
            _make_raw_claim(text="Claim A", confidence=0.9),
            _make_raw_claim(
                text="Claim B",
                confidence=0.55,
                citations=[_make_citation("CIT-002")],
            ),
        ],
        absence_report=["Missing data point X"],
        sources_consulted=10,
        tokens_consumed=2400,
    )

    assert len(finding.claims) == 2
    assert finding.claims[0].confidence_tier == ConfidenceTier.HIGH
    assert finding.claims[1].confidence_tier == ConfidenceTier.WEAK


# ---------------------------------------------------------------------------
# Structural enforcement: all-claims-invalid raises; partial failure salvages.
# When ALL claims fail, FindingValidationError is raised (nothing to salvage).
# When SOME claims fail, valid ones are kept and dropped recorded.
# ---------------------------------------------------------------------------


def test_all_claims_invalid_raises() -> None:
    """When every claim fails validation, FindingValidationError is raised."""
    writer = FindingWriter()
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[_make_raw_claim(citations=[])],
            absence_report=["Something missing"],
            sources_consulted=1,
            tokens_consumed=100,
        )


def test_claim_missing_citations_key_raises_when_only_claim() -> None:
    """Single claim with missing citations key raises (all claims fail)."""
    writer = FindingWriter()
    raw = _make_raw_claim()
    del raw["citations"]
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[raw],
            absence_report=["Something missing"],
            sources_consulted=1,
            tokens_consumed=100,
        )


# ---------------------------------------------------------------------------
# Structural enforcement: confidence required (all-fail raises)
# ---------------------------------------------------------------------------


def test_claim_missing_confidence_raises_when_only_claim() -> None:
    """Single claim missing confidence raises (all claims fail)."""
    writer = FindingWriter()
    raw = _make_raw_claim()
    del raw["confidence"]
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[raw],
            absence_report=["Something missing"],
            sources_consulted=1,
            tokens_consumed=100,
        )


def test_claim_confidence_out_of_range_raises_when_only_claim() -> None:
    """Single claim with confidence > 1.0 raises (all claims fail)."""
    writer = FindingWriter()
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[_make_raw_claim(confidence=1.5)],
            absence_report=["Something missing"],
            sources_consulted=1,
            tokens_consumed=100,
        )


# ---------------------------------------------------------------------------
# Structural enforcement: absence report
# ---------------------------------------------------------------------------


def test_reject_empty_absence_report() -> None:
    writer = FindingWriter()
    with pytest.raises(FindingValidationError, match="Absence report must be non-empty"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[_make_raw_claim()],
            absence_report=[],
            sources_consulted=1,
            tokens_consumed=100,
        )


# ---------------------------------------------------------------------------
# Structural enforcement: text and evidence (all-fail raises)
# ---------------------------------------------------------------------------


def test_claim_missing_text_raises_when_only_claim() -> None:
    """Single claim with empty text raises (all claims fail)."""
    writer = FindingWriter()
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[_make_raw_claim(text="")],
            absence_report=["Missing data"],
            sources_consulted=1,
            tokens_consumed=100,
        )


def test_claim_missing_evidence_raises_when_only_claim() -> None:
    """Single claim with empty evidence raises (all claims fail)."""
    writer = FindingWriter()
    with pytest.raises(FindingValidationError, match="claims failed validation"):
        writer.build_finding(
            task_id="task_001",
            agent_id="agent_001",
            engagement_id="eng_001",
            client_id="client_001",
            agent_type="quantitative",
            raw_claims=[_make_raw_claim(evidence="")],
            absence_report=["Missing data"],
            sources_consulted=1,
            tokens_consumed=100,
        )


# ---------------------------------------------------------------------------
# Artifact writing
# ---------------------------------------------------------------------------


def test_write_artifact(tmp_path: Path) -> None:
    writer = FindingWriter(artifact_dir=tmp_path)
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["No sub-Saharan data"],
        sources_consulted=5,
        tokens_consumed=1200,
    )

    path = writer.write_artifact(finding)
    assert path is not None
    assert Path(path).exists()
    content = Path(path).read_text()
    assert "Research Finding: task_001" in content
    assert "agent_001" in content


def test_artifact_path_set_when_dir_provided(tmp_path: Path) -> None:
    writer = FindingWriter(artifact_dir=tmp_path)
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["Missing data"],
        sources_consulted=1,
        tokens_consumed=100,
    )
    assert finding.artifact_path is not None
    assert "eng_001" in finding.artifact_path


def test_no_artifact_path_without_dir() -> None:
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["Missing data"],
        sources_consulted=1,
        tokens_consumed=100,
    )
    assert finding.artifact_path is None


# ---------------------------------------------------------------------------
# Gaps and status
# ---------------------------------------------------------------------------


def test_finding_with_gaps() -> None:
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["Missing data"],
        sources_consulted=1,
        tokens_consumed=100,
        status=FindingStatus.GAP_FOUND,
        gaps=["Need more recent data", "Conflicting sources on market share"],
    )
    assert finding.status == FindingStatus.GAP_FOUND
    assert len(finding.gaps) == 2


# ---------------------------------------------------------------------------
# claim_id minting and citation_ids derivation (Wave 1C)
# ---------------------------------------------------------------------------


def test_valid_claim_gets_claim_id() -> None:
    """Every valid claim must have a minted claim_id."""
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["No data found"],
        sources_consulted=1,
        tokens_consumed=100,
    )
    assert len(finding.claims) == 1
    claim = finding.claims[0]
    assert claim.claim_id is not None
    assert claim.claim_id.startswith("eng_001_task_001_")


def test_claim_ids_are_unique_across_claims() -> None:
    """Each claim gets a distinct claim_id."""
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[
            _make_raw_claim(text="Claim A"),
            _make_raw_claim(text="Claim B"),
        ],
        absence_report=["No data found"],
        sources_consulted=2,
        tokens_consumed=200,
    )
    ids = [c.claim_id for c in finding.claims]
    assert len(ids) == len(set(ids)), "claim_ids must be unique"


def test_citation_ids_derived_from_embedded_citations() -> None:
    """citation_ids on each claim must match its embedded Citation.citation_id values."""
    writer = FindingWriter()
    cit_a = _make_citation("CIT-A01")
    cit_b = _make_citation("CIT-B02")
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim(citations=[cit_a, cit_b])],
        absence_report=["No data found"],
        sources_consulted=2,
        tokens_consumed=100,
    )
    assert finding.claims[0].citation_ids == ["CIT-A01", "CIT-B02"]


# ---------------------------------------------------------------------------
# Partial-claim salvage (Wave 1C)
# ---------------------------------------------------------------------------


def test_finding_writer_salvages_valid_claims_on_partial_failure() -> None:
    """Canary: valid claims survive when some claims in the batch fail validation."""
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[
            _make_raw_claim(text="Valid claim A"),  # good
            _make_raw_claim(citations=[]),  # dropped: no citations
            _make_raw_claim(text="Valid claim B"),  # good
            _make_raw_claim(text="", evidence="ev"),  # dropped: missing text
        ],
        absence_report=["Something was not found"],
        sources_consulted=4,
        tokens_consumed=400,
    )

    assert len(finding.claims) == 2
    assert len(finding.dropped_claims) == 2
    assert finding.status == FindingStatus.PARTIAL
    assert finding.claims[0].text == "Valid claim A"
    assert finding.claims[1].text == "Valid claim B"
    # Verify dropped claim reasons are recorded
    reasons_all = [r for d in finding.dropped_claims for r in d["reasons"]]
    assert any("citation" in r for r in reasons_all)
    assert any("text" in r for r in reasons_all)


def test_partial_status_not_set_when_no_claims_dropped() -> None:
    """Status is not degraded to PARTIAL when all claims are valid."""
    writer = FindingWriter()
    finding = writer.build_finding(
        task_id="task_001",
        agent_id="agent_001",
        engagement_id="eng_001",
        client_id="client_001",
        agent_type="quantitative",
        raw_claims=[_make_raw_claim()],
        absence_report=["No data found"],
        sources_consulted=1,
        tokens_consumed=100,
    )
    assert finding.status == FindingStatus.COMPLETE
    assert finding.dropped_claims == []
