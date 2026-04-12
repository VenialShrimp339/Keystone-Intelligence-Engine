"""Integration tests for CitationProcessor with real URL liveness checks.

Run: pytest tests/integration/test_citation_processor_live.py -v -m integration
No LLM calls. Makes real HTTP requests for URL liveness verification.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import pytest

from keystone.citation.dedup import deduplicate_citations, find_corroboration_pairs
from keystone.citation.hash import compute_content_hash, compute_metadata_hash
from keystone.citation.processor import CitationProcessor
from keystone.citation.url_check import batch_check_urls, check_url_liveness
from keystone.events import (
    CitationDeduped,
    CorroborationScored,
    ManifestProduced,
    URLVerified,
)
from keystone.models.citations import (
    Citation,
    ConfidenceTier,
    SourceType,
)
from keystone.models.research import FindingClaim, StructuredFinding

pytestmark = pytest.mark.integration

ENGAGEMENT_ID = "ENG-CITPROC-PRESSURE-001"
CLIENT_ID = "CLIENT-KEYSTONE-001"

# Stable real URLs (should be live with polite User-Agent)
LIVE_URLS = [
    "https://en.wikipedia.org/wiki/Lidar",
    "https://en.wikipedia.org/wiki/Autonomous_car",
    "https://arxiv.org/",
    "https://github.com/",
    "https://httpbin.org/status/200",
]
SHARED_URL = "https://en.wikipedia.org/wiki/Autonomous_car"

# Non-resolving domains (guaranteed dead)
DEAD_URLS = [
    "https://this-domain-does-not-exist-keystone-99999.com/report.pdf",
    "https://expired-test-domain-keystone-404.invalid/data",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cit(
    cit_id: str,
    url: str,
    title: str,
    source_type: SourceType = SourceType.NEWS,
    quality: float = 0.7,
    agents: list[str] | None = None,
    doi: str | None = None,
) -> Citation:
    return Citation(
        citation_id=cit_id,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        url=url,
        doi=doi,
        title=title,
        access_date=datetime.now(UTC),
        source_type=source_type,
        quality_score=quality,
        found_by_agents=agents or [],
    )


def _claim(
    text: str,
    evidence: str,
    citations: list[Citation],
    confidence: float = 0.7,
    tier: ConfidenceTier = ConfidenceTier.MODERATE,
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence=evidence,
        citations=citations,
        confidence=confidence,
        confidence_tier=tier,
    )


def build_3_agent_findings() -> list[StructuredFinding]:
    """Three agents with overlapping citations, real URLs, and dead URLs.

    Shared URLs:
      - SHARED_URL cited by agents 1 and 2  (dedup + corroboration)
      - LiDAR wiki cited by agents 1 and 3  (dedup + corroboration)
      - arxiv.org cited by agents 2 and 3   (dedup + corroboration)

    Dead URLs:
      - DEAD_URLS[0] cited by agent 2
      - DEAD_URLS[1] cited by agent 3
    """
    # --- Agent 1: Quantitative ---
    cq1 = _cit("CIT-001", "https://en.wikipedia.org/wiki/Lidar",
                "LiDAR Overview", SourceType.ACADEMIC, 0.8, ["agent-quant-001"])
    cq2 = _cit("CIT-002", SHARED_URL,
                "Autonomous Car Analysis", SourceType.REPORT, 0.85, ["agent-quant-001"])
    cq3 = _cit("CIT-003", "https://github.com/",
                "GitHub Data", SourceType.FILING, 0.9, ["agent-quant-001"])

    f_quant = StructuredFinding(
        task_id="TASK-001", agent_id="agent-quant-001",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="quantitative",
        claims=[
            _claim("L4+ AV sensor market valued at $8.2B in 2025",
                   "SEC filings and industry reports", [cq1, cq3], 0.85, ConfidenceTier.HIGH),
            _claim("LiDAR accounts for 42% of total sensor market",
                   "Market share analysis", [cq1], 0.7, ConfidenceTier.MODERATE),
            _claim("Market projected to reach $50B by 2030 at 35% CAGR",
                   "Growth rate extrapolation", [cq2, cq3], 0.65, ConfidenceTier.MODERATE),
        ],
        gaps=["Insufficient data on Chinese AV sensor manufacturers"],
        absence_report=["No public data on Chinese AV sensor export volumes",
                        "Insurance industry impact data not available"],
        sources_consulted=12, tokens_consumed=3500,
    )

    # --- Agent 2: Qualitative ---
    cql1 = _cit("CIT-201", SHARED_URL,
                 "AV Industry Trends", SourceType.NEWS, 0.75, ["agent-qual-002"])
    cql2 = _cit("CIT-202", "https://httpbin.org/status/200",
                 "HTTPBin Test", SourceType.NEWS, 0.8, ["agent-qual-002"])
    cql3 = _cit("CIT-203", "https://arxiv.org/",
                 "ArXiv Papers", SourceType.ACADEMIC, 0.85, ["agent-qual-002"])
    cql_dead = _cit("CIT-204", DEAD_URLS[0],
                     "Defunct Report", SourceType.REPORT, 0.3, ["agent-qual-002"])

    f_qual = StructuredFinding(
        task_id="TASK-002", agent_id="agent-qual-002",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="qualitative",
        claims=[
            _claim("Solid-state LiDAR transition accelerating consolidation",
                   "Acquisitions in 2025", [cql2], 0.75, ConfidenceTier.MODERATE),
            _claim("Market projected to reach $45-55B by 2030",
                   "Analyst consensus", [cql1, cql3], 0.6, ConfidenceTier.MODERATE),
            _claim("Waymo and Cruise dominate L4 testing miles",
                   "DMV filings", [cql2, cql_dead], 0.9, ConfidenceTier.HIGH),
        ],
        gaps=[],
        absence_report=["No insurance industry impact analysis found"],
        sources_consulted=8, tokens_consumed=2800,
    )

    # --- Agent 3: Contrarian ---
    cc1 = _cit("CIT-301", "https://en.wikipedia.org/wiki/Lidar",
                "LiDAR Limits", SourceType.ACADEMIC, 0.6, ["agent-contra-003"])
    cc2 = _cit("CIT-302", DEAD_URLS[1],
                "Expired Analysis", SourceType.REPORT, 0.2, ["agent-contra-003"])
    cc3 = _cit("CIT-303", "https://arxiv.org/",
                "AV Safety Papers", SourceType.ACADEMIC, 0.75, ["agent-contra-003"])

    f_contra = StructuredFinding(
        task_id="TASK-003", agent_id="agent-contra-003",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="contrarian",
        claims=[
            _claim("Regulatory delays will cap market at $20B by 2030",
                   "Historical regulatory timeline analysis",
                   [cc1, cc3], 0.4, ConfidenceTier.CONTESTED),
            _claim("Camera-only approaches may eliminate LiDAR requirement",
                   "Tesla FSD viability demonstration",
                   [cc1, cc2], 0.35, ConfidenceTier.CONTESTED),
            _claim("Supply chain concentration in 3 vendors = systemic risk",
                   "Top 3 control 78% of automotive-grade LiDAR production",
                   [cc3], 0.7, ConfidenceTier.MODERATE),
        ],
        gaps=["Need deeper analysis of emerging LiDAR alternatives"],
        absence_report=["No consumer willingness-to-pay data for L4 features"],
        sources_consulted=6, tokens_consumed=2100,
    )

    return [f_quant, f_qual, f_contra]


# ============================================================
# BASELINE TEST 1: Dedup with real data (shared URL)
# ============================================================

async def test_dedup_shared_url():
    """Two agents cite same URL; merged citation has both agent IDs."""
    findings = build_3_agent_findings()
    all_citations: list[Citation] = []
    for f in findings:
        for c in f.claims:
            all_citations.extend(c.citations)

    original_count = len(all_citations)
    deduped = deduplicate_citations(all_citations)

    assert len(deduped) < original_count, (
        f"Dedup should reduce {original_count} citations, got {len(deduped)}"
    )

    # Shared URL should produce exactly 1 merged citation
    shared = [c for c in deduped if c.url == SHARED_URL]
    assert len(shared) == 1, f"Expected 1 citation for shared URL, got {len(shared)}"
    shared_cit = shared[0]
    assert shared_cit.citation_id.startswith("CAN-")
    assert "agent-quant-001" in shared_cit.found_by_agents
    assert "agent-qual-002" in shared_cit.found_by_agents

    # Merged citation keeps highest quality score (0.85 from agent-quant-001)
    assert shared_cit.quality_score >= 0.85

    # LiDAR URL also shared between agents 1 and 3
    lidar = [c for c in deduped if c.url == "https://en.wikipedia.org/wiki/Lidar"]
    assert len(lidar) == 1
    assert "agent-quant-001" in lidar[0].found_by_agents
    assert "agent-contra-003" in lidar[0].found_by_agents

    print(f"\n  Original: {original_count}, Deduped: {len(deduped)}")
    print(f"  Shared URL agents: {shared_cit.found_by_agents}")


# ============================================================
# BASELINE TEST 2: URL liveness with real URLs
# ============================================================

async def test_url_liveness_individual():
    """Individual URL checks: live URLs return True, dead URLs return False."""
    results: dict[str, bool] = {}

    async with asyncio.timeout(60):
        for url in LIVE_URLS:
            results[url] = await check_url_liveness(url, timeout=15.0)
        for url in DEAD_URLS:
            results[url] = await check_url_liveness(url, timeout=10.0)

    live = [u for u, v in results.items() if v]
    dead = [u for u, v in results.items() if not v]

    # All LIVE_URLS should be live
    for url in LIVE_URLS:
        assert results[url], f"Expected live: {url}"

    # All DEAD_URLS should be dead
    for url in DEAD_URLS:
        assert not results[url], f"Expected dead: {url}"

    print(f"\n  Live: {len(live)}, Dead: {len(dead)}")
    for url, status in results.items():
        print(f"  {'LIVE' if status else 'DEAD'}: {url[:70]}")


async def test_batch_url_check():
    """batch_check_urls returns results for every citation."""
    findings = build_3_agent_findings()
    all_cits: list[Citation] = []
    for f in findings:
        for c in f.claims:
            all_cits.extend(c.citations)
    deduped = deduplicate_citations(all_cits)

    start = time.monotonic()
    async with asyncio.timeout(60):
        results = await batch_check_urls(deduped)
    elapsed = time.monotonic() - start

    assert len(results) == len(deduped), "Must return result for every citation"

    live = sum(1 for v in results.values() if v)
    dead = sum(1 for v in results.values() if not v)
    assert live >= 3, f"Expected 3+ live URLs, got {live}"
    assert dead >= 1, f"Expected 1+ dead URLs, got {dead}"

    print(f"\n  Batch: {len(deduped)} citations in {elapsed:.2f}s")
    print(f"  Live: {live}, Dead: {dead}")


# ============================================================
# BASELINE TEST 3: Corroboration detection
# ============================================================

async def test_corroboration_pairs():
    """Cross-agent citations to same URL produce corroboration pairs."""
    findings = build_3_agent_findings()
    pairs = find_corroboration_pairs(findings)

    # Shared URLs across agents:
    #   SHARED_URL:     agent-quant-001 + agent-qual-002
    #   LiDAR wiki:     agent-quant-001 + agent-contra-003
    #   arxiv.org:      agent-qual-002  + agent-contra-003
    assert len(pairs) >= 3, f"Expected 3+ corroboration pairs, got {len(pairs)}"

    for pair in pairs:
        assert 0.0 <= pair.overlap_score <= 1.0
        assert pair.citation_a != pair.citation_b

    print(f"\n  Corroboration pairs: {len(pairs)}")
    for p in pairs:
        print(f"  {p.citation_a} <-> {p.citation_b} (overlap: {p.overlap_score})")


# ============================================================
# BASELINE TEST 4: Content hash integrity
# ============================================================

async def test_content_hash_deterministic():
    """Content hashes are deterministic, 64-char hex, unique per input."""
    h1 = compute_content_hash("AV sensor market analysis")
    h2 = compute_content_hash("AV sensor market analysis")
    h3 = compute_content_hash("Different content entirely")

    assert h1 == h2, "Same input must produce same hash"
    assert h1 != h3, "Different inputs must produce different hashes"
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


async def test_processor_assigns_metadata_hashes():
    """After processing, every canonical citation has a metadata_hash."""
    findings = build_3_agent_findings()
    processor = CitationProcessor()

    async with asyncio.timeout(90):
        async for _ in processor.process(findings, ENGAGEMENT_ID, CLIENT_ID):
            pass

    manifest = await processor.get_manifest()
    for cit in manifest.citations:
        assert cit.citation_id.startswith("CAN-")
        assert cit.metadata_hash is not None, f"{cit.citation_id} missing metadata_hash"
        assert len(cit.metadata_hash) == 64
        assert cit.metadata_hash == compute_metadata_hash(cit.url, cit.title)

    # Metadata hashes should be unique per citation (different url:title combos)
    hashes = [c.metadata_hash for c in manifest.citations]
    assert len(set(hashes)) == len(hashes), "Metadata hashes should be unique"


# ============================================================
# Full pipeline event emission
# ============================================================

async def test_full_pipeline_events():
    """Full processor pipeline emits all event types with correct data."""
    findings = build_3_agent_findings()
    processor = CitationProcessor()

    events = []
    start = time.monotonic()
    async with asyncio.timeout(90):
        async for event in processor.process(findings, ENGAGEMENT_ID, CLIENT_ID):
            events.append(event)
    elapsed = time.monotonic() - start

    dedup_events = [e for e in events if isinstance(e, CitationDeduped)]
    corrob_events = [e for e in events if isinstance(e, CorroborationScored)]
    url_events = [e for e in events if isinstance(e, URLVerified)]
    manifest_events = [e for e in events if isinstance(e, ManifestProduced)]

    # Exactly one ManifestProduced
    assert len(manifest_events) == 1
    me = manifest_events[0]
    assert me.total_citations > 0
    assert me.engagement_id == ENGAGEMENT_ID

    # URL checks for every deduped citation
    manifest = await processor.get_manifest()
    assert len(url_events) == len(manifest.citations)

    # Dead URLs tracked
    dead_events = [e for e in url_events if not e.is_live]
    assert len(dead_events) >= 1
    assert len(manifest.dead_urls) == len(dead_events)

    # Dedup events for merged citations
    assert len(dedup_events) >= 1

    # Corroboration events
    assert all(e.citation_a != e.citation_b for e in corrob_events)
    assert all(
        pair.citation_a != pair.citation_b
        for pair in manifest.corroboration_pairs
    )

    # ManifestProduced has correct counts
    assert me.total_citations == len(manifest.citations)
    assert me.dead_urls == len(dead_events)
    assert me.corroboration_pairs == len(corrob_events)

    print(f"\n  Pipeline: {elapsed:.2f}s")
    print(f"  Events: {len(events)} total")
    print(f"    CitationDeduped: {len(dedup_events)}")
    print(f"    CorroborationScored: {len(corrob_events)}")
    print(f"    URLVerified: {len(url_events)} ({len(dead_events)} dead)")
    print(f"    ManifestProduced: 1 ({me.total_citations} citations)")

    # Log URL results
    for e in url_events:
        tag = "LIVE" if e.is_live else "DEAD"
        print(f"    {e.citation_id}: {e.url[:60]} -> {tag}")


# ============================================================
# ADDITIONAL TESTS (beyond baseline)
# ============================================================

async def test_doi_based_dedup():
    """Same DOI, different URLs are merged into one citation."""
    shared_doi = "10.1234/av-sensor-test-doi"
    c1 = _cit("CIT-D01", "https://example.com/paper-v1", "Paper V1",
              SourceType.ACADEMIC, 0.7, ["agent-a"], doi=shared_doi)
    c2 = _cit("CIT-D02", "https://example.org/paper-v2", "Paper V2",
              SourceType.ACADEMIC, 0.9, ["agent-b"], doi=shared_doi)
    c3 = _cit("CIT-D03", "https://example.net/unrelated", "Unrelated",
              SourceType.NEWS, 0.5, ["agent-c"])

    deduped = deduplicate_citations([c1, c2, c3])
    assert len(deduped) == 2, f"DOI dedup should produce 2, got {len(deduped)}"

    doi_cit = next((c for c in deduped if c.doi == shared_doi), None)
    assert doi_cit is not None
    assert "agent-a" in doi_cit.found_by_agents
    assert "agent-b" in doi_cit.found_by_agents
    assert doi_cit.quality_score >= 0.9


async def test_empty_findings():
    """Empty findings list produces empty manifest without error."""
    processor = CitationProcessor()
    events = []
    async for event in processor.process([], ENGAGEMENT_ID, CLIENT_ID):
        events.append(event)

    assert len(events) == 1
    assert isinstance(events[0], ManifestProduced)
    assert events[0].total_citations == 0

    manifest = await processor.get_manifest()
    assert len(manifest.citations) == 0
    assert len(manifest.dead_urls) == 0


async def test_batch_concurrency():
    """Batch URL check is concurrent, not sequential.

    2 dead URLs with 10s timeout each: sequential = 20s+, concurrent < 15s.
    """
    findings = build_3_agent_findings()
    all_cits: list[Citation] = []
    for f in findings:
        for c in f.claims:
            all_cits.extend(c.citations)
    deduped = deduplicate_citations(all_cits)

    start = time.monotonic()
    async with asyncio.timeout(45):
        await batch_check_urls(deduped)
    elapsed = time.monotonic() - start

    print(f"\n  Batch: {len(deduped)} citations in {elapsed:.2f}s")
    # Sequential with 2 dead URLs (10s timeout each) = 20s minimum.
    # Concurrent should be ~10-12s. Use 18s as generous threshold.
    assert elapsed < 25, (
        f"Batch took {elapsed:.2f}s; if >20s it's likely sequential not concurrent"
    )


async def test_dedup_preserves_highest_quality():
    """When merging citations, the highest quality_score is kept."""
    c_low = _cit("CIT-X01", "https://example.com/same", "Same Source",
                 SourceType.NEWS, 0.3, ["agent-x"])
    c_high = _cit("CIT-X02", "https://example.com/same", "Same Source",
                  SourceType.NEWS, 0.95, ["agent-y"])

    deduped = deduplicate_citations([c_low, c_high])
    assert len(deduped) == 1
    assert deduped[0].quality_score >= 0.95
    assert "agent-x" in deduped[0].found_by_agents
    assert "agent-y" in deduped[0].found_by_agents


async def test_manifest_dead_url_ids_are_citation_ids():
    """Manifest.dead_urls contains citation_ids, not raw URLs."""
    findings = build_3_agent_findings()
    processor = CitationProcessor()

    async with asyncio.timeout(90):
        async for _ in processor.process(findings, ENGAGEMENT_ID, CLIENT_ID):
            pass

    manifest = await processor.get_manifest()
    all_cit_ids = {c.citation_id for c in manifest.citations}
    for dead_id in manifest.dead_urls:
        assert dead_id in all_cit_ids, (
            f"Dead URL ID '{dead_id}' not found in manifest citations"
        )


async def test_get_manifest_before_process_raises():
    """Calling get_manifest() before process() raises RuntimeError."""
    processor = CitationProcessor()
    with pytest.raises(RuntimeError, match="process.*must be called"):
        await processor.get_manifest()
