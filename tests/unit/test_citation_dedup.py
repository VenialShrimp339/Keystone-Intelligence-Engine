"""Tests for citation deduplication and corroboration detection.

Validates merge logic for same-URL and same-DOI citations,
agent list combination, quality score preservation, and
corroboration pair identification across agent findings.
"""

from __future__ import annotations

from datetime import datetime

from keystone.citation.dedup import deduplicate_citations, find_corroboration_pairs
from keystone.models.citations import (
    Citation,
    ConfidenceTier,
    SourceType,
)
from keystone.models.research import FindingClaim, StructuredFinding


def _cit(
    cid: str = "CIT-001",
    url: str = "https://example.com/a.pdf",
    doi: str | None = None,
    quality: float = 0.8,
    agents: list[str] | None = None,
    content_hash: str | None = None,
    metadata_hash: str | None = None,
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        url=url,
        title="Test",
        source_type=SourceType.REPORT,
        quality_score=quality,
        access_date=datetime(2026, 4, 1),
        found_by_agents=agents or [],
        doi=doi,
        content_hash=content_hash,
        metadata_hash=metadata_hash,
    )


def _finding(
    agent_id: str,
    claims: list[FindingClaim],
) -> StructuredFinding:
    return StructuredFinding(
        task_id="TASK-001",
        agent_id=agent_id,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        agent_type="quantitative",
        claims=claims,
        absence_report=[],
        sources_consulted=5,
        tokens_consumed=1000,
    )


def _finding_claim(
    text: str,
    citations: list[Citation],
    confidence: float = 0.8,
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence="Supporting evidence",
        citations=citations,
        confidence=confidence,
        confidence_tier=ConfidenceTier.HIGH,
    )


# ---------------------------------------------------------------------------
# deduplicate_citations tests
# ---------------------------------------------------------------------------


class TestDeduplicateCitations:
    def test_merges_same_url(self):
        c1 = _cit(cid="CIT-001", url="https://same.com/doc", quality=0.7, agents=["agent-1"])
        c2 = _cit(cid="CIT-002", url="https://same.com/doc", quality=0.9, agents=["agent-2"])
        result = deduplicate_citations([c1, c2])
        assert len(result) == 1
        merged = result[0]
        assert merged.quality_score == 0.9
        assert set(merged.found_by_agents) == {"agent-1", "agent-2"}

    def test_merges_same_doi(self):
        c1 = _cit(
            cid="CIT-001",
            url="https://site-a.com/paper",
            doi="10.1234/test",
            quality=0.6,
            agents=["agent-1"],
        )
        c2 = _cit(
            cid="CIT-002",
            url="https://site-b.com/paper",
            doi="10.1234/test",
            quality=0.8,
            agents=["agent-2"],
        )
        result = deduplicate_citations([c1, c2])
        assert len(result) == 1
        merged = result[0]
        assert merged.quality_score == 0.8
        assert set(merged.found_by_agents) == {"agent-1", "agent-2"}

    def test_agents_combined_correctly(self):
        c1 = _cit(cid="CIT-001", url="https://same.com", agents=["a1", "a2"])
        c2 = _cit(cid="CIT-002", url="https://same.com", agents=["a2", "a3"])
        result = deduplicate_citations([c1, c2])
        assert len(result) == 1
        assert set(result[0].found_by_agents) == {"a1", "a2", "a3"}

    def test_highest_quality_preserved(self):
        c1 = _cit(cid="CIT-001", url="https://same.com", quality=0.3)
        c2 = _cit(cid="CIT-002", url="https://same.com", quality=0.9)
        c3 = _cit(cid="CIT-003", url="https://same.com", quality=0.5)
        result = deduplicate_citations([c1, c2, c3])
        assert len(result) == 1
        assert result[0].quality_score == 0.9

    def test_no_duplicates_returns_all(self):
        c1 = _cit(cid="CIT-001", url="https://a.com")
        c2 = _cit(cid="CIT-002", url="https://b.com")
        c3 = _cit(cid="CIT-003", url="https://c.com")
        result = deduplicate_citations([c1, c2, c3])
        assert len(result) == 3

    def test_empty_input(self):
        result = deduplicate_citations([])
        assert result == []

    def test_single_citation(self):
        """Single citation gets a fresh CAN- canonical ID; source ID goes in merged_from_ids."""
        c = _cit(cid="CIT-001")
        result = deduplicate_citations([c])
        assert len(result) == 1
        assert result[0].citation_id.startswith("CAN-")
        assert "CIT-001" in result[0].merged_from_ids

    def test_preserves_most_complete_metadata(self):
        """When merging, the record with more metadata fields wins."""
        existing_hash = "ab" * 32
        c1 = _cit(cid="CIT-001", url="https://same.com", quality=0.5)
        c2 = _cit(
            cid="CIT-002",
            url="https://same.com",
            quality=0.9,
            doi="10.1234/test",
            content_hash=existing_hash,
        )
        result = deduplicate_citations([c1, c2])
        assert len(result) == 1
        assert result[0].doi == "10.1234/test"
        assert result[0].citation_id.startswith("CAN-")
        assert result[0].content_hash == existing_hash

    def test_metadata_hash_preserved_from_best_record(self):
        """metadata_hash (url:title identity) is preserved through merge."""
        existing_hash = "ff" * 32
        c1 = _cit(
            cid="CIT-001",
            url="https://same.com",
            quality=0.9,
            metadata_hash=existing_hash,
        )
        c2 = _cit(cid="CIT-002", url="https://same.com", quality=0.5)
        result = deduplicate_citations([c1, c2])
        assert result[0].metadata_hash == existing_hash

    def test_real_content_hash_preserved_from_any_group_member(self):
        """Canonical citation keeps a real content_hash even if only one member had it."""
        existing_hash = "ab" * 32
        c1 = _cit(cid="CIT-001", url="https://same.com", quality=0.9)
        c2 = _cit(
            cid="CIT-002",
            url="https://same.com",
            quality=0.4,
            content_hash=existing_hash,
        )
        result = deduplicate_citations([c1, c2])
        assert result[0].content_hash == existing_hash


# ---------------------------------------------------------------------------
# find_corroboration_pairs tests
# ---------------------------------------------------------------------------


class TestFindCorroborationPairs:
    def test_identifies_shared_citation(self):
        shared_cit = _cit(cid="CIT-001", url="https://sec.gov/10k")
        f1 = _finding(
            "agent-1",
            [_finding_claim("Revenue grew 15%", [shared_cit])],
        )
        f2 = _finding(
            "agent-2",
            [_finding_claim("Revenue increased by 15%", [shared_cit])],
        )
        pairs = find_corroboration_pairs([f1, f2])
        assert len(pairs) >= 1
        pair = pairs[0]
        assert pair.overlap_score > 0

    def test_no_corroboration_without_shared_citations(self):
        f1 = _finding(
            "agent-1",
            [_finding_claim("Claim A", [_cit(cid="CIT-001", url="https://a.com")])],
        )
        f2 = _finding(
            "agent-2",
            [_finding_claim("Claim B", [_cit(cid="CIT-002", url="https://b.com")])],
        )
        pairs = find_corroboration_pairs([f1, f2])
        assert len(pairs) == 0

    def test_same_agent_not_corroboration(self):
        shared_cit = _cit(cid="CIT-001")
        f1 = _finding(
            "agent-1",
            [
                _finding_claim("Claim A", [shared_cit]),
                _finding_claim("Claim B", [shared_cit]),
            ],
        )
        pairs = find_corroboration_pairs([f1])
        assert len(pairs) == 0

    def test_empty_findings(self):
        pairs = find_corroboration_pairs([])
        assert pairs == []

    def test_multiple_corroboration_pairs(self):
        cit1 = _cit(cid="CIT-001", url="https://sec.gov/10k")
        cit2 = _cit(cid="CIT-002", url="https://reuters.com/article")
        f1 = _finding(
            "agent-1",
            [
                _finding_claim("Revenue fact", [cit1]),
                _finding_claim("Market news", [cit2]),
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _finding_claim("Revenue growth", [cit1]),
                _finding_claim("Market update", [cit2]),
            ],
        )
        pairs = find_corroboration_pairs([f1, f2])
        assert len(pairs) >= 2
