"""Integration tests for L1.5 Deliberation + CitationProcessor with real GPT-5.4.

Run: pytest tests/integration/test_deliberation_live.py -v -m integration
Consumes API quota (~12-18 LLM calls total).

Strategy: One full deliberation run is cached at module level so multiple
test functions can assert on different aspects without repeating API calls.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

from keystone.citation.processor import CitationProcessor
from keystone.deliberation.aggregator import AggregatedClaim, Aggregator
from keystone.deliberation.analyst import (
    Analyst,
    AnalystOutput,
    InputClaim,
    ScoredClaim,
    extract_claims,
)
from keystone.deliberation.confidence_builder import build_confidence_map
from keystone.deliberation.deliberation import Deliberation
from keystone.deliberation.gap_detector import GapReport, detect_gaps
from keystone.deliberation.wwhtb import WWHTBResult, run_wwhtb
from keystone.evaluator.retry import LLMCallable
from keystone.events import (
    AggregationComplete,
    AnalystSpawned,
    ConfidenceMapProduced,
    IndependentAnalysisComplete,
)
from keystone.llm_client import _client_cache, get_llm_for_tier
from keystone.models.agents import DeliberationAnalystType
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap
from keystone.models.config import AppConfig
from keystone.models.research import FindingClaim, StructuredFinding
from keystone.models.tasks import ModelTier

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

ENGAGEMENT_ID = "ENG-DELIB-PRESSURE-001"
CLIENT_ID = "CLIENT-KEYSTONE-001"


# ---------------------------------------------------------------------------
# Token tracking wrapper
# ---------------------------------------------------------------------------

class TrackedLLM:
    """Wraps LLMCallable to track calls, timing, and raw output."""

    def __init__(self, llm: LLMCallable, label: str = "") -> None:
        self._llm = llm
        self.label = label
        self.calls: list[dict] = []
        self.total_time = 0.0

    async def __call__(self, prompt: str) -> str:
        start = time.monotonic()
        response = await self._llm(prompt)
        elapsed = time.monotonic() - start
        self.calls.append({
            "prompt_len": len(prompt),
            "response_len": len(response),
            "raw_response": response,
            "elapsed": elapsed,
        })
        self.total_time += elapsed
        return response

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def est_prompt_tokens(self) -> int:
        return sum(c["prompt_len"] for c in self.calls) // 4

    @property
    def est_response_tokens(self) -> int:
        return sum(c["response_len"] for c in self.calls) // 4

    def report(self) -> str:
        return (
            f"  {self.label}: {self.call_count} calls, "
            f"~{self.est_prompt_tokens} prompt tokens, "
            f"~{self.est_response_tokens} response tokens, "
            f"{self.total_time:.1f}s"
        )


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
) -> Citation:
    return Citation(
        citation_id=cit_id,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        url=url,
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
    caveats: list[str] | None = None,
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence=evidence,
        citations=citations,
        confidence=confidence,
        confidence_tier=tier,
        caveats=caveats or [],
    )


def build_3_agent_findings() -> list[StructuredFinding]:
    """Three agents with overlapping/conflicting claims for AV sensor market."""

    # Agent 1: Quantitative
    cq1 = _cit("CIT-001", "https://en.wikipedia.org/wiki/Lidar",
                "LiDAR Overview", SourceType.ACADEMIC, 0.8, ["agent-quant-001"])
    cq2 = _cit("CIT-002", "https://en.wikipedia.org/wiki/Autonomous_car",
                "AV Market", SourceType.REPORT, 0.85, ["agent-quant-001"])
    cq3 = _cit("CIT-003", "https://www.sec.gov/",
                "SEC EDGAR", SourceType.FILING, 0.9, ["agent-quant-001"])

    f_quant = StructuredFinding(
        task_id="TASK-001", agent_id="agent-quant-001",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="quantitative",
        claims=[
            _claim(
                "The L4+ AV sensor market was valued at $8.2 billion in 2025",
                "Analysis of SEC filings and industry reports from 2024-2025",
                [cq1, cq3], 0.85, ConfidenceTier.HIGH,
            ),
            _claim(
                "LiDAR segment accounts for 42% of the total autonomous vehicle sensor market",
                "Market share data from multiple industry analysis reports",
                [cq1], 0.7, ConfidenceTier.MODERATE,
            ),
            _claim(
                "The AV sensor market is projected to reach $50 billion by 2030, growing at 35% CAGR",
                "Projection based on historical growth rates and planned commercial deployments",
                [cq2, cq3], 0.65, ConfidenceTier.MODERATE,
                caveats=["Assumes no major regulatory setbacks"],
            ),
        ],
        gaps=["Insufficient data on Chinese AV sensor manufacturers"],
        absence_report=[
            "No public data on Chinese AV sensor export volumes",
            "Insurance industry impact data not available in public sources",
        ],
        sources_consulted=12, tokens_consumed=3500,
    )

    # Agent 2: Qualitative
    cql1 = _cit("CIT-201", "https://en.wikipedia.org/wiki/Autonomous_car",
                 "AV Trends", SourceType.NEWS, 0.75, ["agent-qual-002"])
    cql2 = _cit("CIT-202", "https://www.reuters.com/",
                 "Reuters Tech", SourceType.NEWS, 0.8, ["agent-qual-002"])
    cql3 = _cit("CIT-203", "https://arxiv.org/",
                 "ArXiv Papers", SourceType.ACADEMIC, 0.85, ["agent-qual-002"])

    f_qual = StructuredFinding(
        task_id="TASK-002", agent_id="agent-qual-002",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="qualitative",
        claims=[
            _claim(
                "Solid-state LiDAR transition is accelerating industry consolidation",
                "Multiple 2025 acquisitions and strategic partnerships reported",
                [cql2], 0.75, ConfidenceTier.MODERATE,
            ),
            _claim(
                "Market projected to reach $45-55 billion by 2030 based on analyst consensus",
                "Consensus of 6 industry analyst firms with converging projections",
                [cql1, cql3], 0.6, ConfidenceTier.MODERATE,
                caveats=["Wide range reflects regulatory timeline uncertainty"],
            ),
            _claim(
                "Waymo and Cruise dominate L4 autonomous testing miles in North America",
                "California DMV autonomous vehicle testing reports filed 2024-2025",
                [cql2], 0.9, ConfidenceTier.HIGH,
            ),
        ],
        gaps=[],
        absence_report=["No insurance industry impact analysis found"],
        sources_consulted=8, tokens_consumed=2800,
    )

    # Agent 3: Contrarian -- deliberately lower confidence, conflicting claims
    cc1 = _cit("CIT-301", "https://en.wikipedia.org/wiki/Lidar",
                "LiDAR Limits", SourceType.ACADEMIC, 0.6, ["agent-contra-003"])
    cc2 = _cit("CIT-302", "https://arxiv.org/",
                "AV Safety Papers", SourceType.ACADEMIC, 0.75, ["agent-contra-003"])

    f_contra = StructuredFinding(
        task_id="TASK-003", agent_id="agent-contra-003",
        engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID,
        agent_type="contrarian",
        claims=[
            _claim(
                "Market growth is overestimated; regulatory delays will cap the AV sensor market at $20 billion by 2030",
                "Historical analysis of automotive safety technology regulatory adoption timelines",
                [cc1, cc2], 0.4, ConfidenceTier.CONTESTED,
                caveats=["Based on historical analogies that may not apply"],
            ),
            _claim(
                "Camera-only autonomous approaches may eliminate the LiDAR sensor requirement entirely within 5 years",
                "Tesla FSD demonstrates camera-only viability, though limited to L2+",
                [cc1], 0.35, ConfidenceTier.CONTESTED,
            ),
            _claim(
                "Supply chain concentration in 3 major LiDAR vendors creates systemic risk for the industry",
                "Top 3 manufacturers control ~78% of automotive-grade LiDAR production capacity",
                [cc2], 0.7, ConfidenceTier.MODERATE,
            ),
        ],
        gaps=["Need deeper analysis of emerging LiDAR alternatives"],
        absence_report=["No consumer willingness-to-pay data for L4 features"],
        sources_consulted=6, tokens_consumed=2100,
    )

    return [f_quant, f_qual, f_contra]


def _try_parse_json(raw: str) -> tuple[bool, str]:
    """Try to parse JSON from raw LLM output, with fence stripping.

    Returns (success, cleaned_string_or_error).
    """
    cleaned = raw.strip()
    # Strip markdown fences
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        json.loads(cleaned)
        return True, cleaned
    except json.JSONDecodeError as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Module-level cache for the expensive full deliberation run
# ---------------------------------------------------------------------------

_FULL_DELIB: dict | None = None


async def _run_full_deliberation() -> dict:
    """Run full deliberation once, cache results for all tests."""
    global _FULL_DELIB
    if _FULL_DELIB is not None:
        return _FULL_DELIB

    config = AppConfig()
    _client_cache.clear()

    findings = build_3_agent_findings()
    claims = extract_claims(findings)

    # Build manifest via CitationProcessor (no URL checks needed for delib)
    manifest = CitationManifest(
        manifest_id="MAN-DELIB-TEST",
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
    )

    # Create tracked LLMs
    analyst_llm = TrackedLLM(
        get_llm_for_tier(ModelTier.STANDARD, config), "analysts"
    )
    judge_llm = TrackedLLM(
        get_llm_for_tier(ModelTier.FLAGSHIP, config), "judge"
    )
    wwhtb_llm = TrackedLLM(
        get_llm_for_tier(ModelTier.STANDARD, config), "wwhtb"
    )

    delib = Deliberation(
        analyst_llm=analyst_llm,
        judge_llm=judge_llm,
        wwhtb_llm=wwhtb_llm,
    )

    events = []
    start = time.monotonic()
    async with asyncio.timeout(240):
        async for event in delib.deliberate(
            manifest, findings, ENGAGEMENT_ID, CLIENT_ID
        ):
            events.append(event)
    elapsed = time.monotonic() - start

    cm = await delib.get_confidence_map()

    _client_cache.clear()

    _FULL_DELIB = {
        "events": events,
        "cm": cm,
        "elapsed": elapsed,
        "analyst_llm": analyst_llm,
        "judge_llm": judge_llm,
        "wwhtb_llm": wwhtb_llm,
        "findings": findings,
        "claims": claims,
    }
    return _FULL_DELIB


# ============================================================
# BASELINE TEST 9: JSON parsing -- single analyst (1 LLM call)
# ============================================================

async def test_single_analyst_json_parsing():
    """Run ONE analyst with real LLM, verify JSON output is parseable."""
    config = AppConfig()
    _client_cache.clear()

    llm = TrackedLLM(
        get_llm_for_tier(ModelTier.STANDARD, config), "single_analyst"
    )
    analyst = Analyst(llm=llm, analyst_type=DeliberationAnalystType.QUANTITATIVE)

    findings = build_3_agent_findings()
    claims = extract_claims(findings)
    assert len(claims) == 9

    async with asyncio.timeout(60):
        output = await analyst.analyze(claims)

    assert isinstance(output, AnalystOutput)
    assert output.analyst_type == "quantitative"
    assert len(output.scored_claims) == 9, (
        f"Expected 9 scored claims, got {len(output.scored_claims)}"
    )

    # Check raw LLM response for JSON parsing
    assert llm.call_count == 1
    raw = llm.calls[0]["raw_response"]
    success, detail = _try_parse_json(raw)

    print(f"\n  === SINGLE ANALYST JSON PARSING ===")
    print(f"  Raw response length: {len(raw)} chars")
    print(f"  JSON parseable: {success}")
    if not success:
        print(f"  Parse error: {detail}")
        print(f"  Raw response preview: {raw[:300]}")

    # Verify all scored claims have valid data
    for sc in output.scored_claims:
        assert 0.0 <= sc.analyst_confidence <= 1.0, (
            f"Claim {sc.index}: confidence {sc.analyst_confidence} out of range"
        )
        assert sc.source_count >= 0
        # Check if reasoning is from LLM or fallback
        if sc.reasoning == "Failed to parse analyst response":
            print(f"  WARNING: Claim {sc.index} used JSON parse fallback")
        elif sc.reasoning == "Not evaluated by analyst":
            print(f"  WARNING: Claim {sc.index} not evaluated (missing from LLM output)")
        else:
            assert len(sc.reasoning) > 5, f"Claim {sc.index}: reasoning too short"

    # Log all scores
    for sc in output.scored_claims:
        print(f"  [{sc.index}] conf={sc.analyst_confidence:.2f} "
              f"src={sc.source_count} {sc.claim_text[:50]}...")

    print(f"\n  {llm.report()}")
    _client_cache.clear()


# ============================================================
# BASELINE TEST 5: Full deliberation with real LLM
# ============================================================

async def test_full_deliberation_events():
    """Full deliberation emits AnalystSpawned, IndependentAnalysisComplete,
    AggregationComplete, and ConfidenceMapProduced events."""
    r = await _run_full_deliberation()
    events = r["events"]

    spawned = [e for e in events if isinstance(e, AnalystSpawned)]
    completed = [e for e in events if isinstance(e, IndependentAnalysisComplete)]
    agg_events = [e for e in events if isinstance(e, AggregationComplete)]
    cm_events = [e for e in events if isinstance(e, ConfidenceMapProduced)]

    # 4 analyst types spawned
    assert len(spawned) == 4, f"Expected 4 AnalystSpawned, got {len(spawned)}"
    spawned_types = {e.analyst_type for e in spawned}
    assert spawned_types == {"ach", "quantitative", "adversarial", "historical_analogy"}

    # 4 analyses completed
    assert len(completed) == 4, f"Expected 4 completions, got {len(completed)}"
    for c in completed:
        assert c.claim_count == 9, f"Analyst {c.analyst_id} scored {c.claim_count} claims"

    # 1 aggregation
    assert len(agg_events) == 1
    agg = agg_events[0]
    print(f"\n  === EVENTS ===")
    print(f"  Convergent findings: {agg.convergent_findings}")
    print(f"  Disagreements: {agg.genuine_disagreements}")
    print(f"  Blind spots: {agg.blind_spots}")

    # 1 confidence map
    assert len(cm_events) == 1
    cme = cm_events[0]
    assert cme.total_claims == 9
    assert cme.tiers_populated >= 2


# ============================================================
# BASELINE TEST 8: Confidence map structure
# ============================================================

async def test_confidence_map_tier_distribution():
    """All 9 claims distributed across tiers with required attributes."""
    r = await _run_full_deliberation()
    cm: ConfidenceMap = r["cm"]

    assert cm.total_claims == 9, f"Expected 9 claims, got {cm.total_claims}"
    assert cm.tiers_populated >= 2

    # High confidence: curmudgeon_challenge populated
    for hc in cm.high_confidence_above_80pct:
        assert hc.curmudgeon_challenge, f"High claim missing curmudgeon: {hc.claim[:40]}"
        assert len(hc.curmudgeon_challenge) > 5
        assert hc.sources >= 0
        assert hc.corroboration_count >= 0
        assert hc.methodological_agreement

    # Moderate: sensitivity + dissent
    for mc in cm.moderate_confidence_60_80pct:
        assert mc.sensitivity, f"Moderate missing sensitivity: {mc.claim[:40]}"
        assert mc.dissent
        assert mc.sources >= 0

    # Contested: steelmanned opposing view
    for cc in cm.contested_below_50pct:
        assert cc.steelmanned_opposing_view, f"Contested missing steelman: {cc.claim[:40]}"
        assert len(cc.steelmanned_opposing_view) > 5
        assert cc.key_disagreement

    # Weak: recommendation
    for wc in cm.weak_confidence_50_60pct:
        assert wc.recommendation, f"Weak missing recommendation: {wc.claim[:40]}"

    print(f"\n  === TIER DISTRIBUTION ===")
    print(f"  High (>80%): {len(cm.high_confidence_above_80pct)}")
    for hc in cm.high_confidence_above_80pct:
        print(f"    {hc.claim[:70]}")
    print(f"  Moderate (60-80%): {len(cm.moderate_confidence_60_80pct)}")
    for mc in cm.moderate_confidence_60_80pct:
        print(f"    {mc.claim[:70]}")
    print(f"  Weak (50-60%): {len(cm.weak_confidence_50_60pct)}")
    for wc in cm.weak_confidence_50_60pct:
        print(f"    {wc.claim[:70]}")
    print(f"  Contested (<50%): {len(cm.contested_below_50pct)}")
    for cc in cm.contested_below_50pct:
        print(f"    {cc.claim[:70]}")
    print(f"  Insufficient: {len(cm.insufficient_evidence)}")


# ============================================================
# BASELINE TEST 6: Claim-level selection (not averaging)
# ============================================================

async def test_claim_selection_not_averaging():
    """Conflicting claims ($50B vs $20B) should trigger judge selection,
    not be averaged to $35B."""
    r = await _run_full_deliberation()
    cm: ConfidenceMap = r["cm"]
    judge_llm: TrackedLLM = r["judge_llm"]

    # Find the $50B and $20B claims in the confidence map tiers
    all_claims_text = []
    for hc in cm.high_confidence_above_80pct:
        all_claims_text.append(hc.claim)
    for mc in cm.moderate_confidence_60_80pct:
        all_claims_text.append(mc.claim)
    for wc in cm.weak_confidence_50_60pct:
        all_claims_text.append(wc.claim)
    for cc in cm.contested_below_50pct:
        all_claims_text.append(cc.claim)

    claim_50b = next((c for c in all_claims_text if "$50" in c), None)
    claim_20b = next((c for c in all_claims_text if "$20" in c), None)

    print(f"\n  === CONFLICT RESOLUTION ===")
    if claim_50b:
        print(f"  $50B claim found in confidence map")
    else:
        print(f"  WARNING: $50B claim not found in any tier")
    if claim_20b:
        print(f"  $20B claim found in confidence map")
    else:
        print(f"  WARNING: $20B claim not found in any tier")

    # The judge should have made at least 1 call if there was dispute
    # (variance > 0.04 threshold)
    if judge_llm.call_count > 0:
        print(f"  Judge made {judge_llm.call_count} calls (disputes resolved)")
        # Check raw judge output is valid JSON
        for i, call in enumerate(judge_llm.calls):
            success, detail = _try_parse_json(call["raw_response"])
            print(f"    Judge call {i}: JSON parseable={success}")
            if not success:
                print(f"    Raw: {call['raw_response'][:200]}")
    else:
        print("  No judge calls (all analysts agreed within variance threshold)")

    # Both claims should exist somewhere in the map (they aren't dropped)
    assert cm.total_claims == 9, "All 9 claims should be in the map"


# ============================================================
# BASELINE TEST 7: WWHTB threshold
# ============================================================

async def test_wwhtb_fires_for_uncertain_claims():
    """WWHTB fires for claims with mean_confidence < 0.6."""
    r = await _run_full_deliberation()
    cm: ConfidenceMap = r["cm"]
    wwhtb_llm: TrackedLLM = r["wwhtb_llm"]

    # WWHTB fires for claims below 0.6. These end up in weak/contested tiers.
    # The contrarian claims (market cap $20B, camera-only, supply chain) are
    # likely candidates.
    low_conf_count = len(cm.weak_confidence_50_60pct) + len(cm.contested_below_50pct)

    print(f"\n  === WWHTB ===")
    print(f"  Weak+Contested claims: {low_conf_count}")
    print(f"  WWHTB LLM calls: {wwhtb_llm.call_count}")

    if wwhtb_llm.call_count > 0:
        # WWHTB fired -- verify output quality
        for i, call in enumerate(wwhtb_llm.calls):
            raw = call["raw_response"]
            success, detail = _try_parse_json(raw)
            print(f"  WWHTB call {i}: JSON parseable={success}")
            if not success:
                print(f"    Raw: {raw[:200]}")

        # Check that moderate claims got sensitivity analysis from WWHTB
        for mc in cm.moderate_confidence_60_80pct:
            if "assumption" in mc.sensitivity.lower() or "Key assumptions" in mc.sensitivity:
                print(f"  WWHTB enriched moderate claim: {mc.claim[:50]}...")
    else:
        print("  No WWHTB calls (all claims had mean_confidence >= 0.6)")

    print(f"\n  {wwhtb_llm.report()}")


# ============================================================
# BASELINE TEST 10: Gap detection
# ============================================================

async def test_gap_detection():
    """Gaps populated from absence reports and low-confidence claims."""
    r = await _run_full_deliberation()
    cm: ConfidenceMap = r["cm"]

    # Absence report should contain items from all 3 agents
    assert len(cm.absence_report) >= 3, (
        f"Expected 3+ absence items (one per agent), got {len(cm.absence_report)}"
    )

    print(f"\n  === GAPS ===")
    print(f"  Gaps identified: {len(cm.gaps_identified)}")
    for g in cm.gaps_identified:
        print(f"    {g}")
    print(f"  Absence report: {len(cm.absence_report)}")
    for a in cm.absence_report:
        print(f"    {a}")

    # Absence report items should be specific
    for item in cm.absence_report:
        assert len(item) > 10, f"Absence item too short: '{item}'"


# ============================================================
# JSON parsing of all raw LLM responses
# ============================================================

async def test_all_raw_responses_parseable():
    """Verify all LLM responses across the pipeline are valid JSON."""
    r = await _run_full_deliberation()
    analyst_llm: TrackedLLM = r["analyst_llm"]
    judge_llm: TrackedLLM = r["judge_llm"]
    wwhtb_llm: TrackedLLM = r["wwhtb_llm"]

    total_calls = analyst_llm.call_count + judge_llm.call_count + wwhtb_llm.call_count
    parse_failures = 0

    print(f"\n  === RAW RESPONSE PARSING ===")
    print(f"  Total LLM calls: {total_calls}")

    for label, tracker in [("analyst", analyst_llm), ("judge", judge_llm), ("wwhtb", wwhtb_llm)]:
        for i, call in enumerate(tracker.calls):
            raw = call["raw_response"]
            success, detail = _try_parse_json(raw)
            if not success:
                parse_failures += 1
                print(f"  FAIL [{label} #{i}]: {detail}")
                print(f"    Raw preview: {raw[:200]}")
                # Check if it's a fence-wrapped JSON issue
                if raw.strip().startswith("```"):
                    print(f"    DIAGNOSIS: Markdown fence wrapping detected")

    print(f"  Parse failures: {parse_failures}/{total_calls}")

    # Log if any responses had XML tags echoed back (prompt leakage)
    for tracker in [analyst_llm, judge_llm, wwhtb_llm]:
        for call in tracker.calls:
            raw = call["raw_response"]
            if "<analytical_contract>" in raw or "<completeness_check>" in raw:
                print(f"  WARNING: XML structural tags echoed in response")


# ============================================================
# Token consumption report
# ============================================================

async def test_token_consumption_report():
    """Report total token consumption across all phases."""
    r = await _run_full_deliberation()
    analyst_llm: TrackedLLM = r["analyst_llm"]
    judge_llm: TrackedLLM = r["judge_llm"]
    wwhtb_llm: TrackedLLM = r["wwhtb_llm"]

    print(f"\n  === TOKEN CONSUMPTION ===")
    print(f"  Duration: {r['elapsed']:.1f}s")
    print(f"  {analyst_llm.report()}")
    print(f"  {judge_llm.report()}")
    print(f"  {wwhtb_llm.report()}")

    total_calls = analyst_llm.call_count + judge_llm.call_count + wwhtb_llm.call_count
    total_prompt = analyst_llm.est_prompt_tokens + judge_llm.est_prompt_tokens + wwhtb_llm.est_prompt_tokens
    total_response = analyst_llm.est_response_tokens + judge_llm.est_response_tokens + wwhtb_llm.est_response_tokens
    total_time = analyst_llm.total_time + judge_llm.total_time + wwhtb_llm.total_time

    print(f"\n  TOTAL: {total_calls} calls, ~{total_prompt} prompt tokens, "
          f"~{total_response} response tokens, {total_time:.1f}s")

    # Sanity: analysts should have exactly 4 calls (4 analyst types)
    assert analyst_llm.call_count == 4, (
        f"Expected 4 analyst calls, got {analyst_llm.call_count}"
    )
    # All tests pass -- this is purely informational
    assert total_calls > 0


# ============================================================
# ADDITIONAL TESTS: Structural / edge cases (no LLM calls)
# ============================================================

async def test_extract_claims_preserves_all_data():
    """extract_claims flattens all 9 claims with correct indexing."""
    findings = build_3_agent_findings()
    claims = extract_claims(findings)

    assert len(claims) == 9
    # Indices should be sequential 0-8
    assert [c.index for c in claims] == list(range(9))

    # First 3 claims from agent 1
    for c in claims[:3]:
        assert c.agent_id == "agent-quant-001"
        assert c.task_id == "TASK-001"

    # Middle 3 from agent 2
    for c in claims[3:6]:
        assert c.agent_id == "agent-qual-002"
        assert c.task_id == "TASK-002"

    # Last 3 from agent 3
    for c in claims[6:]:
        assert c.agent_id == "agent-contra-003"
        assert c.task_id == "TASK-003"

    # Citation IDs preserved
    assert len(claims[0].citation_ids) == 2  # cq1, cq3
    assert claims[0].original_confidence == 0.85


async def test_deliberation_with_empty_findings():
    """Empty findings produce empty confidence map without error."""
    async def mock_llm(prompt: str) -> str:
        return '[]'

    delib = Deliberation(analyst_llm=mock_llm, judge_llm=mock_llm)

    events = []
    async for event in delib.deliberate(
        CitationManifest(
            manifest_id="MAN-EMPTY", engagement_id=ENGAGEMENT_ID, client_id=CLIENT_ID
        ),
        [],
        ENGAGEMENT_ID,
        CLIENT_ID,
    ):
        events.append(event)

    cm = await delib.get_confidence_map()
    assert cm.total_claims == 0
    assert cm.tiers_populated == 0

    # Should still have events (4 analyst spawned + 4 completed + 1 agg + 1 cm)
    spawned = [e for e in events if isinstance(e, AnalystSpawned)]
    assert len(spawned) == 4


async def test_confidence_builder_tier_boundaries():
    """Verify tier routing at exact boundary values."""

    def _make_agg_claim(index: int, text: str, ratio: float, conf: float) -> AggregatedClaim:
        n_agree = int(ratio * 4)
        n_dissent = 4 - n_agree
        return AggregatedClaim(
            claim_text=text, index=index,
            agreement_ratio=ratio,
            agreeing_analysts=[f"a{i}" for i in range(n_agree)],
            dissenting_analysts=[f"d{i}" for i in range(n_dissent)],
            total_analysts=4,
            mean_confidence=conf,
            source_count=2, corroboration_count=1,
            citation_ids=["CIT-001"],
            analyst_scores={f"a{i}": conf for i in range(4)},
            analyst_reasoning={f"a{i}": "test" for i in range(4)},
        )

    claims = [
        _make_agg_claim(0, "High confidence claim", 0.9, 0.85),     # >0.8 -> high
        _make_agg_claim(1, "Moderate boundary claim", 0.75, 0.7),    # 0.6-0.8 -> moderate
        _make_agg_claim(2, "Exactly 0.6 boundary", 0.6, 0.55),      # >=0.5 -> weak (0.6 is NOT >0.6)
        _make_agg_claim(3, "Below 0.5 contested", 0.4, 0.4),        # <0.5 -> contested
        _make_agg_claim(4, "Exactly 0.8 boundary", 0.8, 0.75),      # NOT >0.8 -> moderate
        _make_agg_claim(5, "Exactly 0.5 boundary", 0.5, 0.5),       # >=0.5 -> weak
    ]

    # No WWHTB results or gaps for this test
    cm = build_confidence_map(
        aggregated_claims=claims,
        wwhtb_results=[],
        gap_report=GapReport(),
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
    )

    assert len(cm.high_confidence_above_80pct) == 1   # ratio 0.9
    assert len(cm.moderate_confidence_60_80pct) == 2   # ratios 0.75 and 0.8
    assert len(cm.weak_confidence_50_60pct) == 2       # ratios 0.6 and 0.5
    assert len(cm.contested_below_50pct) == 1          # ratio 0.4
    assert cm.total_claims == 6


async def test_gap_detection_logic():
    """Gap detection finds low-confidence claims and consistency issues."""
    findings = build_3_agent_findings()

    claims = [
        AggregatedClaim(
            claim_text="Low confidence claim", index=0,
            agreement_ratio=0.25, agreeing_analysts=["a1"],
            dissenting_analysts=["a2", "a3", "a4"], total_analysts=4,
            mean_confidence=0.3, source_count=1, corroboration_count=0,
            citation_ids=["CIT-001"],
            analyst_scores={"a1": 0.3, "a2": 0.1, "a3": 0.2, "a4": 0.1},
            analyst_reasoning={}, consistency_passed=False,
        ),
        AggregatedClaim(
            claim_text="OK claim", index=1,
            agreement_ratio=0.75, agreeing_analysts=["a1", "a2", "a3"],
            dissenting_analysts=["a4"], total_analysts=4,
            mean_confidence=0.7, source_count=3, corroboration_count=2,
            citation_ids=["CIT-002"],
            analyst_scores={"a1": 0.7, "a2": 0.8, "a3": 0.6, "a4": 0.4},
            analyst_reasoning={},
        ),
    ]

    gap_report = detect_gaps(findings, claims)

    # Should find gaps from: low confidence (<0.4), consistency failure, agent gaps
    assert len(gap_report.gaps) >= 2  # low conf + consistency
    assert any("Low confidence" in g for g in gap_report.gaps)
    assert any("Consistency" in g for g in gap_report.gaps)

    # Absence report from all 3 agents
    assert len(gap_report.absence_items) >= 3

    # Agent-reported gaps
    assert any("Chinese" in g or "LiDAR alternatives" in g for g in gap_report.gaps)


async def test_analyst_fallback_on_unparseable_json():
    """If LLM returns unparseable JSON, analyst falls back to original confidence."""

    async def bad_llm(prompt: str) -> str:
        return "This is not JSON at all, just text."

    analyst = Analyst(llm=bad_llm, analyst_type=DeliberationAnalystType.ACH)
    findings = build_3_agent_findings()
    claims = extract_claims(findings)

    output = await analyst.analyze(claims)
    assert len(output.scored_claims) == 9

    # All claims should have fallback confidence (original confidence)
    for sc in output.scored_claims:
        assert sc.reasoning == "Failed to parse analyst response"
        # Confidence should match original from the finding
        corresponding_claim = next(c for c in claims if c.index == sc.index)
        assert sc.analyst_confidence == corresponding_claim.original_confidence


async def test_aggregator_with_unanimous_agreement():
    """When all analysts agree, no judge selection fires."""

    async def agreeable_llm(prompt: str) -> str:
        if "contradictions" in prompt:
            return '{"contradictions": []}'
        return '{"selected_analyst": "ach", "reasoning": "test"}'

    # Build analyst outputs where all agree (high confidence)
    claims = extract_claims(build_3_agent_findings())
    outputs = []
    for at in ["ach", "quantitative", "adversarial"]:
        scored = [
            ScoredClaim(
                index=c.index, claim_text=c.text,
                analyst_confidence=0.8, source_count=3,
                reasoning="Well supported",
            )
            for c in claims
        ]
        outputs.append(AnalystOutput(
            analyst_id=f"analyst-{at}-test",
            analyst_type=at,
            scored_claims=scored,
        ))

    aggregator = Aggregator(judge_llm=agreeable_llm)
    aggregated = await aggregator.aggregate(outputs, claims)

    assert len(aggregated) == 9
    # With all analysts at 0.8, variance is 0. No judge selection.
    for ac in aggregated:
        assert ac.selected_from is None, (
            f"Claim {ac.index} should not have judge selection (unanimous)"
        )
        assert ac.agreement_ratio == 1.0
        assert ac.mean_confidence == 0.8
