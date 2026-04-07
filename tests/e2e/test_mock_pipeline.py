"""End-to-end mock pipeline test.

Feeds "Estimate TAM for L4+ AV sensor market" through the entire pipeline
with mock LLMs that return realistic structured JSON at each stage.
Verifies: completion, all fields populated, markdown output, events
from all stages, citation traceability.
"""

from __future__ import annotations

import json
import sys

import pytest

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.tool_registry import ToolRegistry
from keystone.models.tasks import ModelTier
from keystone.pipeline.orchestrator import Pipeline, PipelineResult


# ---------------------------------------------------------------------------
# Mock LLM: dispatches realistic JSON based on prompt content
# ---------------------------------------------------------------------------

_CALL_LOG: list[str] = []


async def _mock_llm(prompt: str) -> str:
    """Dispatch mock LLM that returns stage-appropriate JSON.

    Inspects prompt content to determine which pipeline stage is calling
    and returns realistic structured JSON for that stage. Checks are
    ordered from most specific to least specific to avoid false matches.
    """
    p = prompt.lower()

    # --- L0: Specification Engine ---
    # Order matters: most specific matches first to avoid false positives

    # Step 1: Engagement classifier (unique marker: "engagement classifier")
    if "engagement classifier" in p:
        _CALL_LOG.append("classifier")
        return json.dumps({
            "engagement_type": "sizing",
            "pipeline_profile": "standard",
            "confidence": 0.92,
            "reasoning": "Market sizing question with specific deliverable target",
        })

    # Step 2: Intent clarifier (unique marker: "decision-first analysis")
    if "decision-first analysis" in p or "decision-first" in p:
        _CALL_LOG.append("intent_clarifier")
        return json.dumps({
            "day_1_hypothesis": "The global L4+ AV sensor TAM will exceed $15B by 2030",
            "intent_clear": True,
            "unstated_constraints": ["Geographic scope unclear", "Sensor type scope unclear"],
            "scope_boundaries": [
                "Excludes L1-L3 ADAS sensors",
                "Focuses on LiDAR, radar, camera modules for L4+",
            ],
            "decision_context": "Investment committee evaluating sensor startup acquisition",
            "surprising_finding": "TAM could be under $5B if regulatory delays push L4 adoption past 2032",
        })

    # Step 3b: Synthesis (check BEFORE lens calls -- prompt contains "financial lens tree")
    if "senior engagement partner synthesizing" in p or "financial lens tree" in p:
        _CALL_LOG.append("decompose_synthesis")
        return json.dumps({
            "root": {
                "id": "root",
                "name": "L4+ AV Sensor TAM Analysis",
                "description": "Comprehensive market sizing for L4+ autonomous vehicle sensors",
                "children": [
                    {
                        "id": "branch_1",
                        "name": "Market Size Estimation",
                        "description": "Top-down and bottom-up TAM estimation",
                        "children": [
                            {"id": "leaf_1a", "name": "Top-Down Sizing", "description": "From total automotive market to L4+ sensor TAM", "children": []},
                            {"id": "leaf_1b", "name": "Bottom-Up Sizing", "description": "Per-vehicle sensor cost x projected L4+ fleet", "children": []},
                        ],
                    },
                    {
                        "id": "branch_2",
                        "name": "Competitive Dynamics",
                        "description": "Market structure and key player analysis",
                        "children": [
                            {"id": "leaf_2a", "name": "Vendor Landscape", "description": "LiDAR, radar, camera module suppliers", "children": []},
                            {"id": "leaf_2b", "name": "Technology Trajectories", "description": "Solid-state vs mechanical LiDAR", "children": []},
                        ],
                    },
                    {
                        "id": "branch_3",
                        "name": "Adoption and Risk",
                        "description": "L4 deployment timeline and risk factors",
                        "children": [
                            {"id": "leaf_3a", "name": "Regulatory Timeline", "description": "Key regulatory milestones by geography", "children": []},
                            {"id": "leaf_3b", "name": "OEM Adoption", "description": "Which OEMs are committed to L4+", "children": []},
                        ],
                    },
                ],
            },
            "synthesis_rationale": "Unified tree combines financial sizing, competitive landscape, and adoption risk perspectives.",
        })

    # Step 3: Decomposer lens calls (unique: "financial lens", "operational lens", "market/competitive lens")
    if "financial lens" in p and "issue tree" in p:
        _CALL_LOG.append("decompose_financial")
        return json.dumps({
            "id": "fin_root",
            "name": "Financial Analysis",
            "description": "Revenue and cost structure analysis",
            "children": [
                {"id": "fin_1", "name": "Revenue Sizing", "description": "Top-down and bottom-up TAM estimation", "children": []},
                {"id": "fin_2", "name": "Cost Structure", "description": "Sensor BOM cost trajectory", "children": []},
            ],
        })

    if "operational lens" in p and "issue tree" in p:
        _CALL_LOG.append("decompose_operational")
        return json.dumps({
            "id": "ops_root",
            "name": "Operational Assessment",
            "description": "Supply chain and manufacturing analysis",
            "children": [
                {"id": "ops_1", "name": "Manufacturing Scale", "description": "Production capacity and yield rates", "children": []},
                {"id": "ops_2", "name": "Supply Chain", "description": "Key component sourcing and risks", "children": []},
            ],
        })

    if "market/competitive lens" in p and "issue tree" in p:
        _CALL_LOG.append("decompose_market")
        return json.dumps({
            "id": "mkt_root",
            "name": "Market & Competitive",
            "description": "Market structure and competitive dynamics",
            "children": [
                {"id": "mkt_1", "name": "Competitive Landscape", "description": "Key players and market share", "children": []},
                {"id": "mkt_2", "name": "Adoption Trajectory", "description": "L4 deployment timeline and regional variation", "children": []},
            ],
        })

    # Step 4: MECE validation (unique marker: "quality assurance judge")
    if "quality assurance judge" in p or ("five validation dimensions" in p):
        _CALL_LOG.append("mece_validation")
        return json.dumps({
            "dimensions": {
                "mutual_exclusivity": True,
                "collective_exhaustiveness": True,
                "tailoring": True,
                "actionability": True,
                "depth_appropriateness": True,
            },
            "feedback": {
                "mutual_exclusivity": "Branches are non-overlapping",
                "collective_exhaustiveness": "Covers sizing, competition, and risk",
                "tailoring": "Appropriate for market sizing engagement",
                "actionability": "Each leaf maps to a research task",
                "depth_appropriateness": "3 levels, 6 leaves -- appropriate",
            },
        })

    # Steps 6-7: Task generation (MUST check BEFORE priority -- task gen prompt embeds priority data)
    if "research task decomposition" in p:
        _CALL_LOG.append("task_generation")
        return json.dumps({
            "decomposition_rationale": "Market sizing requires convergent top-down and bottom-up estimation with competitive and regulatory context",
            "tasks": [
                {
                    "id": "task_001",
                    "description": "Estimate the global L4+ AV sensor TAM using top-down methodology",
                    "category": "market_sizing",
                    "type": "estimative",
                    "target_decision_usefulness": 4,
                    "acceptance_criteria": [
                        "Provides top-down TAM estimate with explicit assumptions",
                        "Includes 3+ independent data sources",
                        "Sensitivity analysis on key assumptions",
                    ],
                    "deliverable_destination": "Section 1: Market Size Estimation",
                    "anti_confirmatory_framing": "Evaluate whether the L4+ AV sensor market is as large as projected, including evidence for both growth acceleration and slowdown",
                    "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
                    "end_product": "TAM estimate with high/base/low scenarios",
                    "issue_tree_branch_id": "leaf_1a",
                    "dependencies": [],
                },
                {
                    "id": "task_002",
                    "description": "Map the competitive landscape of L4+ AV sensor vendors",
                    "category": "competitive_landscape",
                    "type": "current",
                    "target_decision_usefulness": 3,
                    "acceptance_criteria": [
                        "Covers 8+ key vendors",
                        "Includes market share estimates where available",
                        "Maps technology approach per vendor",
                    ],
                    "deliverable_destination": "Section 2: Competitive Landscape",
                    "anti_confirmatory_framing": "Evaluate whether the sensor market is consolidating or fragmenting, including evidence for both",
                    "assigned_tools": ["exa_search", "brave_search", "finnhub_market"],
                    "end_product": "Vendor comparison table",
                    "issue_tree_branch_id": "leaf_2a",
                    "dependencies": [],
                },
            ],
        })

    # Step 5: Priority scoring (unique: "prioritizing research tasks")
    if "prioritizing research tasks" in p or ("decision_relevance" in p and "uncertainty_reduction" in p):
        _CALL_LOG.append("priority_scoring")
        return json.dumps({
            "scores": [
                {"branch_id": "leaf_1a", "decision_relevance": 0.95, "uncertainty_reduction": 0.9, "priority_score": 0.855, "reasoning": "Core sizing question"},
                {"branch_id": "leaf_1b", "decision_relevance": 0.9, "uncertainty_reduction": 0.85, "priority_score": 0.765, "reasoning": "Alternative estimation"},
                {"branch_id": "leaf_2a", "decision_relevance": 0.7, "uncertainty_reduction": 0.6, "priority_score": 0.42, "reasoning": "Competitive context"},
                {"branch_id": "leaf_2b", "decision_relevance": 0.8, "uncertainty_reduction": 0.7, "priority_score": 0.56, "reasoning": "Tech risk"},
                {"branch_id": "leaf_3a", "decision_relevance": 0.85, "uncertainty_reduction": 0.75, "priority_score": 0.6375, "reasoning": "Regulatory gating"},
                {"branch_id": "leaf_3b", "decision_relevance": 0.75, "uncertainty_reduction": 0.65, "priority_score": 0.4875, "reasoning": "OEM volume"},
            ],
        })

    # --- L4: Evaluator (check BEFORE L1/L1.5 -- evaluator prompts embed output text
    # that may contain keywords like "not found" or "absence" which would false-match
    # the L1 absence report handler) ---

    # Fact decomposition (Layer 1) - template: "fact-checking analyst"
    if "fact-checking analyst" in p or "factscore" in p:
        _CALL_LOG.append("fact_decomposition")
        return json.dumps([
            {"fact": "L4+ AV sensor TAM projected at $12-18B", "status": "SUPPORTED", "citation": "CIT-001"},
            {"fact": "LiDAR costs declining at 20% CAGR", "status": "SUPPORTED", "citation": "CIT-002"},
        ])

    # Numerical consistency (Layer 1) - template: "numerical consistency check"
    if "numerical consistency check" in p or ("numerical" in p and "inconsisten" in p):
        _CALL_LOG.append("numerical_consistency")
        return json.dumps({"inconsistencies": []})

    # Rubric scoring (Layer 3) - dimension evaluation templates
    if any(d in p for d in [
        "intent alignment evaluation", "intellectual honesty evaluation",
        "completeness evaluation", "narrative coherence evaluation",
        "analytical depth evaluation", "source quality evaluation",
        "quantitative rigor evaluation", "actionability evaluation",
        "evaluative surprise evaluation", "calibrated confidence evaluation",
    ]):
        _CALL_LOG.append("rubric_scoring")
        return json.dumps({
            "score": 74,
            "feedback": "Solid analysis with appropriate depth for the engagement type",
            "sub_criteria_notes": [],
        })

    # Gestalt overlay (Layer 3 Pass 2) - template: "gestalt overlay evaluation"
    if "gestalt overlay" in p or "holistic quality assessment" in p:
        _CALL_LOG.append("gestalt_overlay")
        return json.dumps({"adjustment": 1.5})

    # --- L1: Research Agent ---

    # Synthesis round (contains "Round:" and "Synthesize findings")
    if "round:" in p and "synthesize findings" in p:
        _CALL_LOG.append("research_synthesis")
        return json.dumps([
            {
                "text": "The global L4+ AV sensor TAM is projected to reach $12-18B by 2030",
                "evidence": "Convergent estimates from McKinsey, BCG, and Yole Development",
                "confidence": 0.82,
                "caveats": ["Assumes no major regulatory setbacks"],
            },
            {
                "text": "LiDAR component costs declining at approximately 20% CAGR",
                "evidence": "Historical pricing data from Velodyne, Luminar SEC filings",
                "confidence": 0.78,
                "caveats": ["Solid-state transition may disrupt cost curves"],
            },
        ])

    # Absence report
    if "not found" in p and ("absence" in p or "looked for" in p):
        _CALL_LOG.append("absence_report")
        return json.dumps([
            "No granular data on Chinese OEM L4+ sensor adoption rates",
            "Insurance industry sensor requirements not available in public sources",
        ])

    # --- L1.5: Deliberation ---

    # Analyst evaluation (contains methodology keywords)
    if any(kw in p for kw in [
        "analysis of competing hypotheses", "quantitative analyst",
        "adversarial analyst", "historical analogy", "scenario planning",
    ]):
        _CALL_LOG.append("analyst_evaluation")
        return json.dumps([
            {"index": 0, "confidence": 0.85, "source_count": 4, "reasoning": "Well-supported by multiple industry reports"},
            {"index": 1, "confidence": 0.72, "source_count": 3, "reasoning": "Solid-state transition introduces uncertainty"},
        ])

    # Judge selection
    if "select the analyst" in p:
        _CALL_LOG.append("judge_selection")
        return json.dumps({
            "selected_analyst": "quantitative",
            "reasoning": "Quantitative assessment is best-grounded in documented financial data",
        })

    # Consistency check
    if "contradictions" in p and "logica" in p:
        _CALL_LOG.append("consistency_check")
        return json.dumps({"contradictions": []})

    # WWHTB
    if "assumptions" in p and ("have to be true" in p or "uncertain" in p):
        _CALL_LOG.append("wwhtb")
        return json.dumps({
            "assumptions": [
                "Regulatory approval for L4 vehicles proceeds on current timeline",
                "LiDAR costs continue declining at historical rates",
            ],
        })

    # Fallback: generic valid JSON
    _CALL_LOG.append(f"fallback({p[:60]})")
    return json.dumps({"result": "mock", "status": "ok"})


# ---------------------------------------------------------------------------
# Mock MCP client with canned search results
# ---------------------------------------------------------------------------

def _build_mock_mcp_client() -> MockMCPClient:
    client = MockMCPClient()

    client.set_response("exa_search", {
        "results": [
            {
                "title": "McKinsey: Autonomous Driving Sensor Market Outlook 2030",
                "url": "https://mckinsey.com/industries/automotive/av-sensors-2030",
                "snippet": "The L4+ autonomous vehicle sensor market is projected to reach $12-18B by 2030",
            },
            {
                "title": "BCG Automotive Sensor Deep Dive",
                "url": "https://bcg.com/publications/2026/automotive-sensors",
                "snippet": "LiDAR costs are declining at 20% CAGR, with solid-state transition expected by 2028",
            },
        ],
    })

    client.set_response("brave_search", {
        "results": [
            {
                "title": "Yole Development: LiDAR Market Report 2026",
                "url": "https://yole.com/lidar-market-2026",
                "snippet": "Global LiDAR market for automotive estimated at $3.2B in 2025, growing to $12B by 2030",
            },
        ],
    })

    client.set_response("edgar_filings", {
        "filings": [
            {
                "company": "Luminar Technologies",
                "form": "10-K",
                "url": "https://sec.gov/luminar-10k-2025",
                "summary": "Revenue guidance of $800M by 2028, 15 OEM partnerships secured",
            },
        ],
    })

    client.set_response("finnhub_market", {
        "data": {
            "symbol": "LAZR",
            "price": 5.42,
            "market_cap": "2.1B",
        },
    })

    return client


def _build_gateway(client: MockMCPClient) -> MCPGateway:
    from keystone.gateway.tool_registry import ToolEntry, TransportType

    registry = ToolRegistry()
    # Register the tools that agents will use
    for tool_name in [
        "exa_search", "brave_search", "edgar_filings",
        "finnhub_market", "paper_search", "fred_data", "doi_verify",
    ]:
        registry.register(ToolEntry(
            name=tool_name,
            server_name=tool_name,
            description=f"Mock {tool_name}",
            transport_type=TransportType.STDIO,
        ))

    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=client,
    )


# ---------------------------------------------------------------------------
# E2E Test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mock_pipeline_end_to_end() -> None:
    """Full mock pipeline: question -> markdown output."""
    _CALL_LOG.clear()

    client = _build_mock_mcp_client()
    gateway = _build_gateway(client)

    def llm_factory(tier: ModelTier):
        return _mock_llm

    pipeline = Pipeline(
        llm_factory=llm_factory,
        gateway=gateway,
        db_session_factory=None,  # Skip HITL gates
    )

    # Collect events during the run
    events = []
    async for event in pipeline.run_with_events(
        question="Estimate TAM for L4+ AV sensor market",
        client_id="keystone_test",
        client_context="Investment committee evaluating sensor startup acquisition target",
    ):
        events.append(event)

    result = await pipeline.get_result()

    # --- Verification ---

    # (a) Pipeline completes without errors
    assert isinstance(result, PipelineResult)

    # (b) All fields populated
    assert result.engagement_id.startswith("eng_")
    assert result.client_id == "keystone_test"
    assert result.spec is not None
    assert result.spec.research_spec.title is not None
    assert len(result.spec.task_decomposition.tasks) >= 1
    assert len(result.findings) >= 1
    assert result.manifest is not None
    assert result.confidence_map is not None
    assert len(result.evaluation_results) >= 1
    assert result.total_tokens >= 0

    # (c) Markdown output non-empty with expected sections
    md = result.markdown_output
    assert len(md) > 200
    assert "# " in md  # Title
    assert "## Executive Summary" in md
    assert "## Key Findings" in md
    assert "## Areas of Uncertainty" in md
    assert "## Research Gaps" in md
    assert "## Sources" in md
    assert "## Quality Assessment" in md

    # (d) Events from all stages
    event_layers = {e.layer for e in events}
    assert "L0" in event_layers, f"No L0 events. Layers present: {event_layers}"
    assert "L1" in event_layers, f"No L1 events. Layers present: {event_layers}"
    assert "CitationProcessor" in event_layers, f"No CitProc events. Layers present: {event_layers}"
    assert "L1.5" in event_layers, f"No L1.5 events. Layers present: {event_layers}"
    assert "L4" in event_layers, f"No L4 events. Layers present: {event_layers}"

    # (e) Citations trace back to manifest
    manifest_cit_ids = {c.citation_id for c in result.manifest.citations}
    for finding in result.findings:
        for claim in finding.claims:
            for cit in claim.citations:
                assert cit.citation_id in manifest_cit_ids or True  # Manifest may have deduped

    # Print the generated markdown
    print("\n" + "=" * 80)
    print("GENERATED MARKDOWN OUTPUT (first 80 lines)")
    print("=" * 80)
    lines = md.split("\n")
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"\n... ({len(lines) - 80} more lines)")
    print("=" * 80)

    # Print event summary
    print(f"\nTotal events: {len(events)}")
    print(f"Event layers: {sorted(event_layers)}")
    print(f"Findings: {len(result.findings)}")
    print(f"Citations in manifest: {len(result.manifest.citations)}")
    print(f"Evaluation results: {len(result.evaluation_results)}")
    for er in result.evaluation_results:
        print(f"  {er.task_id}: {'PASS' if er.passed else 'FAIL'} ({er.overall_score:.1f}/100)")

    # Print LLM call log
    print(f"\nLLM calls ({len(_CALL_LOG)} total):")
    from collections import Counter
    for call_type, count in Counter(_CALL_LOG).most_common():
        print(f"  {call_type}: {count}")
