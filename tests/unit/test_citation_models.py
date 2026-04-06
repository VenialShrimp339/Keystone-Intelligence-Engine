"""Tests for citation and claim data models.

Validates Citation, Claim, CitationManifest, WikiCompilationRecord,
and CorroborationPair creation, field constraints, and validators.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from keystone.models.citations import (
    ACHDiagnosticity,
    Citation,
    CitationManifest,
    Claim,
    ConfidenceTier,
    CorroborationPair,
    SourceType,
    WikiCompilationRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_citation(**overrides) -> Citation:
    """Factory for valid Citation instances."""
    defaults = {
        "citation_id": "CIT-001",
        "engagement_id": "ENG-001",
        "client_id": "CLIENT-001",
        "url": "https://example.com/report.pdf",
        "title": "Test Report",
        "source_type": SourceType.REPORT,
        "quality_score": 0.85,
        "access_date": datetime(2026, 4, 1, 12, 0, 0),
    }
    defaults.update(overrides)
    return Citation(**defaults)


def _make_claim(**overrides) -> Claim:
    """Factory for valid Claim instances."""
    defaults = {
        "claim_id": "CLM-001",
        "engagement_id": "ENG-001",
        "client_id": "CLIENT-001",
        "text": "Market share is 23%",
        "citation_ids": ["CIT-001", "CIT-002"],
        "confidence": 0.85,
        "corroboration_count": 2,
        "provenance_chain": "task_001 -> agent_quant -> CitationProcessor",
        "confidence_tier": ConfidenceTier.HIGH,
    }
    defaults.update(overrides)
    return Claim(**defaults)


# ---------------------------------------------------------------------------
# Citation tests
# ---------------------------------------------------------------------------


class TestCitation:
    def test_valid_creation(self):
        c = _make_citation()
        assert c.citation_id == "CIT-001"
        assert c.quality_score == 0.85
        assert c.source_type == SourceType.REPORT
        assert c.content_hash is None

    def test_citation_id_must_start_with_cit(self):
        with pytest.raises(ValidationError, match="CIT-"):
            _make_citation(citation_id="BAD-001")

    def test_quality_score_bounds(self):
        _make_citation(quality_score=0.0)
        _make_citation(quality_score=1.0)
        with pytest.raises(ValidationError):
            _make_citation(quality_score=-0.1)
        with pytest.raises(ValidationError):
            _make_citation(quality_score=1.1)

    def test_content_hash_none_allowed(self):
        c = _make_citation(content_hash=None)
        assert c.content_hash is None

    def test_content_hash_valid_hex(self):
        valid_hash = "a" * 64
        c = _make_citation(content_hash=valid_hash)
        assert c.content_hash == valid_hash

    def test_content_hash_rejects_non_hex(self):
        with pytest.raises(ValidationError, match="content_hash"):
            _make_citation(content_hash="not-a-hex-string")

    def test_content_hash_rejects_wrong_length(self):
        with pytest.raises(ValidationError, match="content_hash"):
            _make_citation(content_hash="abcd1234")  # too short

    def test_doi_optional(self):
        c = _make_citation(doi="10.1234/test.2026")
        assert c.doi == "10.1234/test.2026"

    def test_found_by_agents_default_empty(self):
        c = _make_citation()
        assert c.found_by_agents == []

    def test_found_by_agents_populated(self):
        c = _make_citation(found_by_agents=["agent-1", "agent-2"])
        assert len(c.found_by_agents) == 2

    def test_all_source_types(self):
        for st in SourceType:
            c = _make_citation(source_type=st)
            assert c.source_type == st

    def test_frozen(self):
        c = _make_citation()
        with pytest.raises(ValidationError):
            c.quality_score = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Claim tests
# ---------------------------------------------------------------------------


class TestClaim:
    def test_valid_creation(self):
        c = _make_claim()
        assert c.claim_id == "CLM-001"
        assert c.confidence == 0.85
        assert c.proposition_hashes == []

    def test_claim_id_must_start_with_clm(self):
        with pytest.raises(ValidationError, match="CLM-"):
            _make_claim(claim_id="BAD-001")

    def test_confidence_bounds(self):
        _make_claim(confidence=0.0)
        _make_claim(confidence=1.0)
        with pytest.raises(ValidationError):
            _make_claim(confidence=-0.1)
        with pytest.raises(ValidationError):
            _make_claim(confidence=1.1)

    def test_proposition_hashes_default_empty(self):
        c = _make_claim()
        assert c.proposition_hashes == []

    def test_proposition_hashes_populated(self):
        hashes = ["ab" * 32, "cd" * 32]
        c = _make_claim(proposition_hashes=hashes)
        assert c.proposition_hashes == hashes

    def test_all_confidence_tiers(self):
        for tier in ConfidenceTier:
            c = _make_claim(confidence_tier=tier)
            assert c.confidence_tier == tier

    def test_ach_diagnosticity_optional(self):
        c = _make_claim(ach_diagnosticity=None)
        assert c.ach_diagnosticity is None
        c2 = _make_claim(ach_diagnosticity=ACHDiagnosticity.HIGH)
        assert c2.ach_diagnosticity == ACHDiagnosticity.HIGH

    def test_frozen(self):
        c = _make_claim()
        with pytest.raises(ValidationError):
            c.text = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CorroborationPair tests
# ---------------------------------------------------------------------------


class TestCorroborationPair:
    def test_valid_creation(self):
        cp = CorroborationPair(
            citation_a="CIT-001", citation_b="CIT-002", overlap_score=0.75
        )
        assert cp.citation_a == "CIT-001"
        assert cp.overlap_score == 0.75

    def test_overlap_score_bounds(self):
        CorroborationPair(citation_a="CIT-001", citation_b="CIT-002", overlap_score=0.0)
        CorroborationPair(citation_a="CIT-001", citation_b="CIT-002", overlap_score=1.0)
        with pytest.raises(ValidationError):
            CorroborationPair(
                citation_a="CIT-001", citation_b="CIT-002", overlap_score=1.5
            )


# ---------------------------------------------------------------------------
# CitationManifest tests
# ---------------------------------------------------------------------------


class TestCitationManifest:
    def test_assembly(self):
        c1 = _make_citation(citation_id="CIT-001")
        c2 = _make_citation(citation_id="CIT-002", url="https://other.com")
        pair = CorroborationPair(
            citation_a="CIT-001", citation_b="CIT-002", overlap_score=0.9
        )
        manifest = CitationManifest(
            manifest_id="MAN-001",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            citations=[c1, c2],
            corroboration_pairs=[pair],
            dead_urls=["CIT-003"],
            fabrication_flags=["CIT-004"],
        )
        assert len(manifest.citations) == 2
        assert len(manifest.corroboration_pairs) == 1
        assert manifest.dead_urls == ["CIT-003"]
        assert manifest.fabrication_flags == ["CIT-004"]

    def test_empty_manifest(self):
        manifest = CitationManifest(
            manifest_id="MAN-001",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
        )
        assert manifest.citations == []
        assert manifest.corroboration_pairs == []
        assert manifest.dead_urls == []


# ---------------------------------------------------------------------------
# WikiCompilationRecord tests
# ---------------------------------------------------------------------------


class TestWikiCompilationRecord:
    def test_valid_creation(self):
        record = WikiCompilationRecord(
            citation_id="CIT-001",
            engagement_id="ENG-001",
            raw_path="ENG-001/memory/raw/r1_agent1_task1.md",
            content_hash="ab" * 32,
        )
        assert record.citation_id == "CIT-001"
        assert record.compiled_path is None
        assert record.compiled_at is None

    def test_with_compiled_data(self):
        now = datetime(2026, 4, 5, 12, 0, 0)
        record = WikiCompilationRecord(
            citation_id="CIT-001",
            engagement_id="ENG-001",
            raw_path="ENG-001/memory/raw/r1_agent1_task1.md",
            compiled_path="ENG-001/memory/compiled/market_share.md",
            content_hash="ab" * 32,
            compiled_at=now,
        )
        assert record.compiled_path is not None
        assert record.compiled_at == now
