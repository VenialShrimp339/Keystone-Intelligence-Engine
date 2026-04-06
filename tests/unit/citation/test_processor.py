"""Tests for the CitationProcessor orchestrator.

Validates deduplication, corroboration scoring, URL checking,
content hashing, event emission, and manifest production.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from keystone.citation.processor import CitationProcessor
from keystone.contracts import CitationProcessorContract
from keystone.events import (
    CitationDeduped,
    CorroborationScored,
    ManifestProduced,
    URLVerified,
)
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.research import FindingClaim, StructuredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cit(
    cid: str = "CIT-001",
    url: str = "https://example.com/doc",
    doi: str | None = None,
    quality: float = 0.8,
    agents: list[str] | None = None,
    content_hash: str | None = None,
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        url=url,
        title="Test Document",
        source_type=SourceType.REPORT,
        quality_score=quality,
        access_date=datetime(2026, 4, 1),
        found_by_agents=agents or [],
        doi=doi,
        content_hash=content_hash,
    )


def _claim(
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


async def _all_urls_live(citations, concurrency=10):
    """Mock for batch_check_urls that marks all URLs as live."""
    return {c.citation_id: True for c in citations}


async def _collect(processor, findings, eid="ENG-001", cid="CLIENT-001"):
    """Run processor.process() and collect all emitted events."""
    events = []
    async for event in processor.process(findings, eid, cid):
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


class TestDeduplication:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_dedup_same_url_from_three_agents(self, _mock):
        """Two of three agents cite the same URL. Verify merge to 2 citations."""
        shared = "https://sec.gov/10k/filing.pdf"
        f1 = _finding("agent-1", [_claim("Revenue grew 15%", [
            _cit("CIT-001", shared, agents=["agent-1"]),
        ])])
        f2 = _finding("agent-2", [_claim("Revenue increased", [
            _cit("CIT-002", shared, agents=["agent-2"]),
        ])])
        f3 = _finding("agent-3", [_claim("Costs were flat", [
            _cit("CIT-003", "https://other.com/report", agents=["agent-3"]),
        ])])

        processor = CitationProcessor()
        await _collect(processor, [f1, f2, f3])
        manifest = await processor.get_manifest()

        assert len(manifest.citations) == 2
        merged = [c for c in manifest.citations if len(c.found_by_agents) > 1]
        assert len(merged) == 1
        assert set(merged[0].found_by_agents) == {"agent-1", "agent-2"}

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_dedup_same_doi_different_urls(self, _mock):
        """Two citations with different URLs but same DOI. Verify merge."""
        f1 = _finding("agent-1", [_claim("Market is $50B", [
            _cit("CIT-001", "https://site-a.com/paper", doi="10.1234/test", agents=["agent-1"]),
        ])])
        f2 = _finding("agent-2", [_claim("Market size 50B", [
            _cit("CIT-002", "https://site-b.com/paper", doi="10.1234/test", agents=["agent-2"]),
        ])])

        processor = CitationProcessor()
        await _collect(processor, [f1, f2])
        manifest = await processor.get_manifest()

        assert len(manifest.citations) == 1
        assert set(manifest.citations[0].found_by_agents) == {"agent-1", "agent-2"}


# ---------------------------------------------------------------------------
# Corroboration tests
# ---------------------------------------------------------------------------


class TestCorroboration:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_corroboration_detected(self, _mock):
        """Two agents independently cite the same source. Verify pair detected."""
        shared_url = "https://statista.com/market-size"
        f1 = _finding("agent-1", [_claim("Market is $50B", [
            _cit("CIT-001", shared_url, agents=["agent-1"]),
        ])])
        f2 = _finding("agent-2", [_claim("TAM estimate $50B", [
            _cit("CIT-002", shared_url, agents=["agent-2"]),
        ])])

        processor = CitationProcessor()
        events = await _collect(processor, [f1, f2])

        corr_events = [e for e in events if isinstance(e, CorroborationScored)]
        assert len(corr_events) >= 1
        assert corr_events[0].overlap_score > 0

        manifest = await processor.get_manifest()
        assert len(manifest.corroboration_pairs) >= 1


# ---------------------------------------------------------------------------
# URL check tests
# ---------------------------------------------------------------------------


class TestURLCheck:
    async def test_dead_url_flagged(self, httpx_mock: HTTPXMock):
        """A citation with a dead URL (404) is flagged in the manifest."""
        live_url = "https://live.example.com/doc"
        dead_url = "https://dead.example.com/gone"

        httpx_mock.add_response(url=live_url, method="HEAD", status_code=200)
        httpx_mock.add_response(url=dead_url, method="HEAD", status_code=404)
        httpx_mock.add_response(url=dead_url, method="GET", status_code=404)

        f1 = _finding("agent-1", [
            _claim("Live source", [_cit("CIT-001", live_url, agents=["agent-1"])]),
            _claim("Dead source", [_cit("CIT-002", dead_url, agents=["agent-1"])]),
        ])

        processor = CitationProcessor()
        events = await _collect(processor, [f1])

        url_events = [e for e in events if isinstance(e, URLVerified)]
        assert len(url_events) == 2

        live_ev = next(e for e in url_events if e.url == live_url)
        dead_ev = next(e for e in url_events if e.url == dead_url)
        assert live_ev.is_live is True
        assert dead_ev.is_live is False

        manifest = await processor.get_manifest()
        assert "CIT-002" in manifest.dead_urls
        assert "CIT-001" not in manifest.dead_urls


# ---------------------------------------------------------------------------
# Content hash tests
# ---------------------------------------------------------------------------


class TestContentHash:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_all_citations_have_content_hash(self, _mock):
        """Every citation in the manifest must have a content_hash."""
        f1 = _finding("agent-1", [
            _claim("Claim A", [_cit("CIT-001", "https://a.com", content_hash=None)]),
            _claim("Claim B", [_cit("CIT-002", "https://b.com", content_hash="ab" * 32)]),
        ])

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        for cit in manifest.citations:
            assert cit.content_hash is not None
            assert len(cit.content_hash) == 64

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_existing_content_hash_preserved(self, _mock):
        """Citations that already have a content_hash keep it unchanged."""
        existing_hash = "ab" * 32
        f1 = _finding("agent-1", [
            _claim("Claim", [_cit("CIT-001", "https://a.com", content_hash=existing_hash)]),
        ])

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        assert manifest.citations[0].content_hash == existing_hash


# ---------------------------------------------------------------------------
# Event emission tests
# ---------------------------------------------------------------------------


class TestEventEmission:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_all_four_event_types_in_order(self, _mock):
        """Events: CitationDeduped -> CorroborationScored -> URLVerified -> ManifestProduced."""
        shared_url = "https://sec.gov/filing.pdf"
        f1 = _finding("agent-1", [_claim("Rev grew", [
            _cit("CIT-001", shared_url, agents=["agent-1"]),
        ])])
        f2 = _finding("agent-2", [_claim("Rev up", [
            _cit("CIT-002", shared_url, agents=["agent-2"]),
        ])])

        processor = CitationProcessor()
        events = await _collect(processor, [f1, f2])

        types = [type(e) for e in events]

        assert CitationDeduped in types
        assert CorroborationScored in types
        assert URLVerified in types
        assert ManifestProduced in types

        last_dedup = max(i for i, t in enumerate(types) if t is CitationDeduped)
        first_corr = min(i for i, t in enumerate(types) if t is CorroborationScored)
        last_corr = max(i for i, t in enumerate(types) if t is CorroborationScored)
        first_url = min(i for i, t in enumerate(types) if t is URLVerified)
        last_url = max(i for i, t in enumerate(types) if t is URLVerified)
        manifest_idx = types.index(ManifestProduced)

        assert last_dedup < first_corr
        assert last_corr < first_url
        assert last_url < manifest_idx

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_events_carry_engagement_context(self, _mock):
        """All events carry correct engagement_id and client_id."""
        f1 = _finding("agent-1", [_claim("Claim", [
            _cit("CIT-001", "https://a.com", agents=["agent-1"]),
        ])])

        processor = CitationProcessor()
        events = await _collect(processor, [f1], eid="ENG-X", cid="CLIENT-Y")

        for event in events:
            assert event.engagement_id == "ENG-X"
            assert event.client_id == "CLIENT-Y"


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    async def test_empty_findings(self):
        """No findings -> empty manifest, only ManifestProduced event."""
        processor = CitationProcessor()
        events = await _collect(processor, [])

        assert len(events) == 1
        assert isinstance(events[0], ManifestProduced)
        assert events[0].total_citations == 0

        manifest = await processor.get_manifest()
        assert len(manifest.citations) == 0
        assert len(manifest.dead_urls) == 0

    async def test_findings_with_no_citations(self):
        """Findings exist but have no claims -> empty manifest."""
        f1 = _finding("agent-1", [])
        processor = CitationProcessor()
        events = await _collect(processor, [f1])

        assert len(events) == 1
        assert isinstance(events[0], ManifestProduced)

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_single_agent_single_citation(self, _mock):
        """One agent, one citation. No dedup/corroboration. Manifest produced."""
        f1 = _finding("agent-1", [_claim("Solo claim", [
            _cit("CIT-001", "https://a.com", agents=["agent-1"]),
        ])])

        processor = CitationProcessor()
        events = await _collect(processor, [f1])
        types = [type(e) for e in events]

        assert CitationDeduped not in types
        assert CorroborationScored not in types
        assert URLVerified in types
        assert ManifestProduced in types

        manifest = await processor.get_manifest()
        assert len(manifest.citations) == 1

    async def test_get_manifest_before_process_raises(self):
        """Calling get_manifest before process raises RuntimeError."""
        processor = CitationProcessor()
        with pytest.raises(RuntimeError, match="process.*must be called"):
            await processor.get_manifest()


# ---------------------------------------------------------------------------
# Manifest schema tests
# ---------------------------------------------------------------------------


class TestManifestSchema:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_output_is_citation_manifest(self, _mock):
        """Output conforms to CitationManifest Pydantic model."""
        f1 = _finding("agent-1", [_claim("Claim A", [
            _cit("CIT-001", "https://a.com", agents=["agent-1"]),
        ])])
        f2 = _finding("agent-2", [_claim("Claim B", [
            _cit("CIT-002", "https://b.com", agents=["agent-2"]),
        ])])

        processor = CitationProcessor()
        await _collect(processor, [f1, f2])
        manifest = await processor.get_manifest()

        assert isinstance(manifest, CitationManifest)
        assert manifest.manifest_id.startswith("MAN-")
        assert manifest.engagement_id == "ENG-001"
        assert manifest.client_id == "CLIENT-001"
        assert isinstance(manifest.citations, list)
        assert isinstance(manifest.corroboration_pairs, list)
        assert isinstance(manifest.dead_urls, list)
        assert isinstance(manifest.fabrication_flags, list)

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_manifest_serializes_to_json(self, _mock):
        """Manifest round-trips through JSON serialization."""
        f1 = _finding("agent-1", [_claim("Claim", [
            _cit("CIT-001", "https://a.com", agents=["agent-1"]),
        ])])

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        json_str = manifest.model_dump_json()
        restored = CitationManifest.model_validate_json(json_str)
        assert restored.manifest_id == manifest.manifest_id
        assert len(restored.citations) == len(manifest.citations)


# ---------------------------------------------------------------------------
# Contract compliance
# ---------------------------------------------------------------------------


class TestContractCompliance:
    async def test_satisfies_citation_processor_contract(self):
        """CitationProcessor satisfies CitationProcessorContract Protocol."""
        processor = CitationProcessor()
        assert isinstance(processor, CitationProcessorContract)
