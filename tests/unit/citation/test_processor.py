"""Tests for the CitationProcessor orchestrator.

Validates deduplication, corroboration scoring, URL checking,
content hashing, event emission, and manifest production.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock

from keystone.citation.hash import compute_metadata_hash
from keystone.citation.processor import CitationProcessor, CitationProcessorResult
from keystone.contracts import CitationProcessorContract
from keystone.events import (
    CitationDeduped,
    CorroborationScored,
    ManifestProduced,
    URLVerified,
)
from keystone.models.citations import (
    Citation,
    CitationAlias,
    CitationManifest,
    ConfidenceTier,
    CorroborationPair,
    SourceType,
)
from keystone.models.research import FindingClaim, StructuredFinding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cit(
    cid: str = "CIT-001",
    url: str = "https://example.com/doc",
    title: str = "Test Document",
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
        title=title,
        source_type=SourceType.REPORT,
        quality_score=quality,
        access_date=datetime(2026, 4, 1),
        found_by_agents=agents or [],
        doi=doi,
        content_hash=content_hash,
        metadata_hash=metadata_hash,
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
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Revenue grew 15%",
                    [
                        _cit("CIT-001", shared, agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Revenue increased",
                    [
                        _cit("CIT-002", shared, agents=["agent-2"]),
                    ],
                )
            ],
        )
        f3 = _finding(
            "agent-3",
            [
                _claim(
                    "Costs were flat",
                    [
                        _cit("CIT-003", "https://other.com/report", agents=["agent-3"]),
                    ],
                )
            ],
        )

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
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Market is $50B",
                    [
                        _cit(
                            "CIT-001",
                            "https://site-a.com/paper",
                            doi="10.1234/test",
                            agents=["agent-1"],
                        ),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Market size 50B",
                    [
                        _cit(
                            "CIT-002",
                            "https://site-b.com/paper",
                            doi="10.1234/test",
                            agents=["agent-2"],
                        ),
                    ],
                )
            ],
        )

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
    async def test_canonical_self_pairs_are_dropped(self, _mock):
        """Canonical corroboration pairs never retain identical endpoints."""
        shared_url = "https://statista.com/market-size"
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Market is $50B",
                    [
                        _cit("CIT-001", shared_url, agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "TAM estimate $50B",
                    [
                        _cit("CIT-002", shared_url, agents=["agent-2"]),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        events = await _collect(processor, [f1, f2])

        corr_events = [e for e in events if isinstance(e, CorroborationScored)]
        assert corr_events == []

        manifest = await processor.get_manifest()
        assert manifest.corroboration_pairs == []

    def test_rewrite_corroboration_pairs_drops_canonical_self_pairs(self) -> None:
        processor = CitationProcessor()
        rewritten = processor._rewrite_corroboration_pairs_to_canonical(
            [
                CorroborationPair(
                    citation_a="CIT-001",
                    citation_b="CIT-002",
                    overlap_score=1.0,
                )
            ],
            [
                CitationAlias(
                    source_instance_id="CIT-001",
                    canonical_citation_id="CAN-001",
                    engagement_id="ENG-001",
                    task_id="TASK-001",
                    agent_id="agent-1",
                ),
                CitationAlias(
                    source_instance_id="CIT-002",
                    canonical_citation_id="CAN-001",
                    engagement_id="ENG-001",
                    task_id="TASK-002",
                    agent_id="agent-2",
                ),
            ],
        )

        assert rewritten == []


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

        f1 = _finding(
            "agent-1",
            [
                _claim("Live source", [_cit("CIT-001", live_url, agents=["agent-1"])]),
                _claim("Dead source", [_cit("CIT-002", dead_url, agents=["agent-1"])]),
            ],
        )

        processor = CitationProcessor()
        events = await _collect(processor, [f1])

        url_events = [e for e in events if isinstance(e, URLVerified)]
        assert len(url_events) == 2

        live_ev = next(e for e in url_events if e.url == live_url)
        dead_ev = next(e for e in url_events if e.url == dead_url)
        assert live_ev.is_live is True
        assert dead_ev.is_live is False

        manifest = await processor.get_manifest()
        alias_by_src = {
            alias.source_instance_id: alias.canonical_citation_id for alias in manifest.aliases
        }
        assert alias_by_src["CIT-002"] in manifest.dead_urls
        assert alias_by_src["CIT-001"] not in manifest.dead_urls


# ---------------------------------------------------------------------------
# Metadata/content hash tests
# ---------------------------------------------------------------------------


class TestCitationHashes:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_all_citations_have_metadata_hash(self, _mock):
        """Every canonical citation gets a metadata_hash derived from url:title."""
        f1 = _finding(
            "agent-1",
            [
                _claim("Claim A", [_cit("CIT-001", "https://a.com", content_hash=None)]),
                _claim("Claim B", [_cit("CIT-002", "https://b.com", content_hash="ab" * 32)]),
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        for cit in manifest.citations:
            assert cit.metadata_hash is not None
            assert len(cit.metadata_hash) == 64
            assert cit.metadata_hash == compute_metadata_hash(cit.url, cit.title)

        by_url = {citation.url: citation for citation in manifest.citations}
        assert by_url["https://b.com"].content_hash == "ab" * 32

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_doi_dedup_recomputes_stale_loser_metadata_hash(self, _mock):
        """Final canonical citations must hash their own url:title after DOI merges."""
        stale_hash = compute_metadata_hash(
            "https://loser.example.com/paper",
            "Loser Title",
        )
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Winner claim",
                    [
                        _cit(
                            "CIT-001",
                            "https://winner.example.com/paper",
                            title="Winner Title",
                            doi="10.1234/test",
                            quality=0.9,
                            agents=["agent-1"],
                        ),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Loser claim",
                    [
                        _cit(
                            "CIT-002",
                            "https://loser.example.com/paper",
                            title="Loser Title",
                            doi="10.1234/test",
                            quality=0.4,
                            agents=["agent-2"],
                            metadata_hash=stale_hash,
                        ),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1, f2])
        manifest = await processor.get_manifest()

        assert len(manifest.citations) == 1
        canonical = manifest.citations[0]
        assert canonical.url == "https://winner.example.com/paper"
        assert canonical.title == "Winner Title"
        assert canonical.metadata_hash == compute_metadata_hash(
            canonical.url,
            canonical.title,
        )
        assert canonical.metadata_hash != stale_hash

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_existing_content_hash_preserved(self, _mock):
        """Existing real content_hash values survive canonicalization."""
        existing_hash = "ab" * 32
        f1 = _finding(
            "agent-1",
            [
                _claim("Claim", [_cit("CIT-001", "https://a.com", content_hash=existing_hash)]),
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        assert manifest.citations[0].content_hash == existing_hash
        assert manifest.citations[0].metadata_hash is not None


# ---------------------------------------------------------------------------
# Event emission tests
# ---------------------------------------------------------------------------


class TestEventEmission:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_event_order_when_canonical_self_pairs_are_dropped(self, _mock):
        """Events stay ordered even when canonical corroboration self-pairs are removed."""
        shared_url = "https://sec.gov/filing.pdf"
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Rev grew",
                    [
                        _cit("CIT-001", shared_url, agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Rev up",
                    [
                        _cit("CIT-002", shared_url, agents=["agent-2"]),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        events = await _collect(processor, [f1, f2])

        types = [type(e) for e in events]

        assert CitationDeduped in types
        assert CorroborationScored not in types
        assert URLVerified in types
        assert ManifestProduced in types

        last_dedup = max(i for i, t in enumerate(types) if t is CitationDeduped)
        first_url = min(i for i, t in enumerate(types) if t is URLVerified)
        last_url = max(i for i, t in enumerate(types) if t is URLVerified)
        manifest_idx = types.index(ManifestProduced)

        assert last_dedup < first_url
        assert last_url < manifest_idx

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_events_carry_engagement_context(self, _mock):
        """All events carry correct engagement_id and client_id."""
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Claim",
                    [
                        _cit("CIT-001", "https://a.com", agents=["agent-1"]),
                    ],
                )
            ],
        )

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
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Solo claim",
                    [
                        _cit("CIT-001", "https://a.com", agents=["agent-1"]),
                    ],
                )
            ],
        )

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
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Claim A",
                    [
                        _cit("CIT-001", "https://a.com", agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Claim B",
                    [
                        _cit("CIT-002", "https://b.com", agents=["agent-2"]),
                    ],
                )
            ],
        )

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
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Claim",
                    [
                        _cit("CIT-001", "https://a.com", agents=["agent-1"]),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1])
        manifest = await processor.get_manifest()

        json_str = manifest.model_dump_json()
        restored = CitationManifest.model_validate_json(json_str)
        assert restored.manifest_id == manifest.manifest_id
        assert len(restored.citations) == len(manifest.citations)


# ---------------------------------------------------------------------------
# Alias map and canonical ID rewriting (Task #12)
# ---------------------------------------------------------------------------


class TestAliasMapAndCanonicalRewriting:
    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_citation_processor_builds_alias_map(self, _mock):
        """Alias map in manifest covers all source-instance IDs, including the winner."""
        shared_url = "https://sec.gov/filing.pdf"
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Revenue grew 15%",
                    [
                        _cit("CIT-SRC-001", shared_url, agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Revenue increased",
                    [
                        _cit("CIT-SRC-002", shared_url, agents=["agent-2"]),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1, f2])
        manifest = await processor.get_manifest()

        # Both source IDs should appear in alias map
        alias_source_ids = {a.source_instance_id for a in manifest.aliases}
        assert "CIT-SRC-001" in alias_source_ids
        assert "CIT-SRC-002" in alias_source_ids

        # Both aliases point to the same canonical ID
        alias_by_src = {a.source_instance_id: a.canonical_citation_id for a in manifest.aliases}
        assert alias_by_src["CIT-SRC-001"] == alias_by_src["CIT-SRC-002"]

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_citation_processor_rewrites_findings_to_canonical_ids(self, _mock):
        """get_result() returns findings with claim.citation_ids pointing to canonical IDs."""
        shared_url = "https://sec.gov/filing.pdf"
        # agent-1 cites shared URL: source ID CIT-SRC-001, will be merged into canonical
        # agent-2 cites same URL: source ID CIT-SRC-002, will be aliased to same canonical
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Revenue grew",
                    [
                        _cit("CIT-SRC-001", shared_url, agents=["agent-1"]),
                    ],
                )
            ],
        )
        # Give the finding claims citation_ids as source-instance IDs
        f1 = f1.model_copy(
            update={"claims": [f1.claims[0].model_copy(update={"citation_ids": ["CIT-SRC-001"]})]}
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "Revenue up",
                    [
                        _cit("CIT-SRC-002", shared_url, agents=["agent-2"]),
                    ],
                )
            ],
        )
        f2 = f2.model_copy(
            update={"claims": [f2.claims[0].model_copy(update={"citation_ids": ["CIT-SRC-002"]})]}
        )

        processor = CitationProcessor()
        await _collect(processor, [f1, f2])
        result = await processor.get_result()

        assert isinstance(result, CitationProcessorResult)
        # Both findings' claims should reference the same canonical ID
        canonical_ids_f1 = result.canonicalized_findings[0].claims[0].citation_ids
        canonical_ids_f2 = result.canonicalized_findings[1].claims[0].citation_ids

        assert len(canonical_ids_f1) == 1
        assert len(canonical_ids_f2) == 1
        # Both point to the same canonical ID
        assert canonical_ids_f1[0] == canonical_ids_f2[0]
        assert canonical_ids_f1[0].startswith("CAN-")

    @patch("keystone.citation.processor.batch_check_urls", side_effect=_all_urls_live)
    async def test_task_manifest_contains_exact_canonical_citations(self, _mock):
        """Manifest citations are deduplicated canonicals; no source-instance duplicates."""
        shared_url = "https://reports.com/market-analysis.pdf"
        unique_url = "https://other.com/report.pdf"

        # Three agents: two cite shared_url, one cites unique_url
        f1 = _finding(
            "agent-1",
            [
                _claim(
                    "Market is $50B",
                    [
                        _cit("CIT-A1", shared_url, quality=0.9, agents=["agent-1"]),
                    ],
                )
            ],
        )
        f2 = _finding(
            "agent-2",
            [
                _claim(
                    "TAM $50B",
                    [
                        _cit("CIT-A2", shared_url, quality=0.7, agents=["agent-2"]),
                    ],
                )
            ],
        )
        f3 = _finding(
            "agent-3",
            [
                _claim(
                    "Unique finding",
                    [
                        _cit("CIT-B1", unique_url, quality=0.8, agents=["agent-3"]),
                    ],
                )
            ],
        )

        processor = CitationProcessor()
        await _collect(processor, [f1, f2, f3])
        manifest = await processor.get_manifest()

        # Exactly 2 canonical citations: one for shared_url, one for unique_url
        assert len(manifest.citations) == 2
        manifest_urls = {c.url for c in manifest.citations}
        assert shared_url in manifest_urls
        assert unique_url in manifest_urls

        # The merged shared_url citation has both agents
        merged = next(c for c in manifest.citations if c.url == shared_url)
        assert set(merged.found_by_agents) == {"agent-1", "agent-2"}

        # Alias map has 3 entries (one per source instance)
        assert len(manifest.aliases) == 3

    async def test_get_result_before_process_raises(self):
        """Calling get_result before process raises RuntimeError."""
        processor = CitationProcessor()
        with pytest.raises(RuntimeError, match="process.*must be called"):
            await processor.get_result()


# ---------------------------------------------------------------------------
# Contract compliance
# ---------------------------------------------------------------------------


class TestContractCompliance:
    async def test_satisfies_citation_processor_contract(self):
        """CitationProcessor satisfies CitationProcessorContract Protocol."""
        processor = CitationProcessor()
        assert isinstance(processor, CitationProcessorContract)
