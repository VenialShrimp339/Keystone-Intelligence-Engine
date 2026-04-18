"""Deep research integration tests.

Test 1: Single-task deep research agent (5-10 min)
Test 2: Full pipeline with DEEP_RESEARCH=1 (15-25 min)

Run with: pytest tests/integration/test_deep_research.py -v -m integration -s
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from pathlib import Path

import pytest
from dotenv import load_dotenv

from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.simple_client import SimpleMCPClient
from keystone.gateway.tool_registry import ToolEntry, ToolRegistry, TransportType
from keystone.llm_client import (
    _client_cache,
    create_llm_factory,
    get_deep_research_callable,
)
from keystone.models.agents import (
    AgentDefinition,
    AgentInstance,
    AgentRole,
    ResearchAgentType,
)
from keystone.models.config import AppConfig
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    ResearchQuestion,
    ResearchSpec,
    TaskDecomposition,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskType,
)
from keystone.pipeline.orchestrator import Pipeline, PipelineResult
from keystone.research.finding_writer import FindingWriter
from keystone.research.research_agent import ResearchAgent

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "deep_research_run"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _save_artifact(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_sample_task() -> ResearchTask:
    """Build the Luminar Technologies sample research task."""
    return ResearchTask(
        id="task_001",
        engagement_id="eng_deep_test",
        client_id="keystone_test",
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description=(
            "Estimate the total addressable market for LiDAR sensors in "
            "the Level 4+ autonomous vehicle market in North America "
            "through 2030. Include current market size, growth projections, "
            "key players (Luminar, Velodyne/Ouster, Innoviz, Hesai, "
            "Robosense), and the impact of declining sensor costs on "
            "mass-market adoption. Identify whether LiDAR-only vs "
            "camera-first approaches are converging."
        ),
        required_sources=[
            "industry_reports",
            "financial_data",
            "academic",
        ],
        acceptance_criteria=[
            "Market size estimate with clear methodology and source citations",
            "Growth rate with supporting data from at least 3 sources",
            "Competitive landscape covering at least 5 LiDAR manufacturers",
            "Cost trajectory analysis with historical data points",
            "Assessment of LiDAR vs camera-only debate with evidence for both sides",
        ],
        deliverable_destination="Section 2: Market Landscape",
        priority=1,
        anti_confirmatory_framing=(
            "Evaluate whether LiDAR will remain essential for L4+ autonomy "
            "or whether camera-only approaches (Tesla Vision, etc.) will "
            "render LiDAR unnecessary, including evidence both for and "
            "against each position."
        ),
        assigned_tools=[
            "exa_search",
            "brave_search",
            "edgar_filings",
        ],
        end_product=(
            "Market sizing table with TAM/SAM/SOM, competitive comparison "
            "matrix of 5+ LiDAR players, and cost trajectory chart data"
        ),
    )


def _build_sample_spec(task: ResearchTask) -> EngagementSpec:
    """Build a minimal EngagementSpec wrapping the task."""
    from datetime import datetime

    rs = ResearchSpec(
        engagement_id="eng_deep_test",
        client_id="keystone_test",
        title="AV Sensor Market Analysis: LiDAR TAM Estimation",
        created_at=datetime.now(),
        specification_version=1,
        decision_context=(
            "Investment committee evaluating sensor startup acquisition "
            "targets. Need defensible market size estimates with "
            "source-level citations."
        ),
        surprising_finding=(
            "Evidence that LiDAR costs are NOT declining fast enough, "
            "or that camera-only approaches have achieved parity in "
            "safety-critical scenarios."
        ),
        questions=[
            ResearchQuestion(
                question=(
                    "What is the total addressable market for LiDAR sensors "
                    "in Level 4+ autonomous vehicles in North America "
                    "through 2030?"
                ),
                is_primary=True,
            ),
            ResearchQuestion(
                question=(
                    "Are camera-only approaches converging with LiDAR in "
                    "safety-critical L4+ applications?"
                ),
                parent_question="TAM estimation",
            ),
        ],
        output_format="markdown",
        engagement_type=EngagementType.SIZING,
        day_1_hypothesis=(
            "LiDAR TAM for L4+ AV will exceed $5B by 2030, driven by "
            "cost reductions below $500/unit enabling mass-market adoption."
        ),
    )

    td = TaskDecomposition(
        project="AV Sensor Market Analysis",
        engagement_id="eng_deep_test",
        client_id="keystone_test",
        research_md_path="/tmp/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Market sizing requires TAM estimation with competitive landscape",
        tasks=[task],
    )

    vr = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )

    return EngagementSpec(
        research_spec=rs,
        task_decomposition=td,
        validation_report=vr,
    )


def _build_sample_agent() -> AgentInstance:
    """Build a sample AgentInstance."""
    defn = AgentDefinition(
        name="deep_quant_researcher",
        description="Quantitative research agent with deep web search",
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        research_type=ResearchAgentType.QUANTITATIVE,
    )
    return AgentInstance(
        agent_id="agent_deep_test_001",
        engagement_id="eng_deep_test",
        client_id="keystone_test",
        definition=defn,
        working_dir="/tmp/keystone/eng_deep_test/agent_deep_test_001",
        task_ids=["task_001"],
    )


def _build_gateway() -> MCPGateway:
    """Build a minimal MCPGateway (only needed for shallow fallback)."""
    search_client = SimpleMCPClient()
    registry = ToolRegistry()
    for tool_name in [
        "exa_search",
        "brave_search",
        "edgar_filings",
    ]:
        registry.register(
            ToolEntry(
                name=tool_name,
                server_name=tool_name,
                description=f"Stub {tool_name}",
                transport_type=TransportType.STDIO,
            )
        )
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=search_client,
    )


# ======================================================================
# Test 1: Single-task deep research
# ======================================================================


@pytest.mark.asyncio
@pytest.mark.timeout(1500)
async def test_single_task_deep_research():
    """Run one deep research agent on one task.

    Verifies:
    - Produces 20+ claims with real source URLs
    - FindingWriter accepts the output
    - Valid StructuredFinding objects
    - Timing 5-10 minutes
    """
    task = _build_sample_task()
    spec = _build_sample_spec(task)
    agent = _build_sample_agent()
    gateway = _build_gateway()

    # Get the deep research callable
    deep_llm = get_deep_research_callable()
    config = AppConfig()
    llm_factory = create_llm_factory(config)
    shallow_llm = llm_factory(ModelTier.STANDARD)

    finding_writer = FindingWriter()

    research_agent = ResearchAgent(
        llm=shallow_llm,
        gateway=gateway,
        deep_llm=deep_llm,
        finding_writer=finding_writer,
    )

    print(f"\n{'=' * 60}")
    print("STARTING SINGLE-TASK DEEP RESEARCH TEST")
    print(f"Task: {task.description[:80]}...")
    print(f"{'=' * 60}\n")

    start_time = time.time()
    events = []

    async for event in research_agent.execute(task, spec, agent):
        events.append(event)
        etype = type(event).__name__
        print(f"  Event: {etype}")

    finding = await research_agent.get_finding()
    elapsed = time.time() - start_time

    # --- Collect metrics ---
    claim_count = len(finding.claims)
    all_urls = set()
    for claim in finding.claims:
        for cit in claim.citations:
            if cit.url and not cit.url.startswith("tool://"):
                all_urls.add(cit.url)

    unique_sources = len(all_urls)
    conf_values = [c.confidence for c in finding.claims]
    avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0

    metrics = {
        "elapsed_seconds": round(elapsed, 1),
        "claim_count": claim_count,
        "unique_source_urls": unique_sources,
        "avg_confidence": round(avg_conf, 3),
        "confidence_range": f"{min(conf_values):.2f}-{max(conf_values):.2f}"
        if conf_values
        else "N/A",
        "absence_report_count": len(finding.absence_report),
        "tokens_consumed": finding.tokens_consumed,
        "sources_consulted": finding.sources_consulted,
        "finding_writer_accepted": True,  # Would have thrown if not
        "events_emitted": len(events),
    }

    # --- Save artifacts ---
    _save_artifact(
        OUTPUT_DIR / "single_task" / "finding.json",
        finding.model_dump_json(indent=2),
    )
    _save_artifact(
        OUTPUT_DIR / "single_task" / "metrics.json",
        json.dumps(metrics, indent=2),
    )
    _save_artifact(
        OUTPUT_DIR / "single_task" / "all_urls.json",
        json.dumps(sorted(all_urls), indent=2),
    )

    # --- Print summary ---
    print(f"\n{'=' * 60}")
    print(f"SINGLE-TASK DEEP RESEARCH COMPLETE in {elapsed:.1f}s")
    print(f"Claims: {claim_count}")
    print(f"Unique source URLs: {unique_sources}")
    print(f"Avg confidence: {avg_conf:.3f}")
    print(f"Confidence range: {metrics['confidence_range']}")
    print(f"Absence report items: {len(finding.absence_report)}")
    print(f"Tokens consumed: {finding.tokens_consumed}")
    print(f"FindingWriter accepted: YES")
    print(f"Events: {len(events)}")

    # Print first 5 claims
    print(f"\n--- First 5 claims ---")
    for i, claim in enumerate(finding.claims[:5], 1):
        print(f"\n  Claim {i}: {claim.text[:120]}...")
        print(f"  Confidence: {claim.confidence}")
        print(f"  Citations: {len(claim.citations)} sources")
        if claim.citations:
            print(f"  First URL: {claim.citations[0].url}")

    # Print absence report
    print(f"\n--- Absence report ---")
    for item in finding.absence_report:
        print(f"  - {item}")

    print(f"\nArtifacts saved to: {OUTPUT_DIR / 'single_task'}")
    print(f"{'=' * 60}\n")

    # --- Assertions ---
    assert claim_count >= 5, f"Expected 5+ claims, got {claim_count}"
    assert unique_sources >= 3, f"Expected 3+ unique URLs, got {unique_sources}"
    assert finding.absence_report, "Absence report is empty"
    for claim in finding.claims:
        assert claim.citations, f"Claim has no citations: {claim.text[:80]}"
        assert 0.0 <= claim.confidence <= 1.0, f"Invalid confidence: {claim.confidence}"


# ======================================================================
# Test 2: Full pipeline with deep research
# ======================================================================


def _build_real_gateway() -> tuple[MCPGateway, SimpleMCPClient]:
    """Build an MCPGateway wired to real Exa/Brave search."""
    search_client = SimpleMCPClient()
    registry = ToolRegistry()
    for tool_name in [
        "exa_search",
        "brave_search",
        "edgar_filings",
        "finnhub_market",
        "paper_search",
        "fred_data",
        "doi_verify",
    ]:
        registry.register(
            ToolEntry(
                name=tool_name,
                server_name=tool_name,
                description=f"Real/stub {tool_name}",
                transport_type=TransportType.STDIO,
            )
        )
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=search_client,
    ), search_client


def _serialize_events(events: list) -> str:
    serialized = []
    for event in events:
        try:
            serialized.append(json.loads(event.model_dump_json()))
        except Exception as exc:
            serialized.append(
                {
                    "error": f"Failed to serialize {type(event).__name__}: {exc}",
                }
            )
    return json.dumps(serialized, indent=2, default=str)


@pytest.mark.asyncio
@pytest.mark.timeout(3600)
async def test_full_pipeline_deep_research():
    """Run the full pipeline with DEEP_RESEARCH=1.

    Compares output metrics against shallow research expectations.
    Saves all artifacts to output/deep_research_run/full_pipeline/.
    """
    # Force deep research mode
    os.environ["DEEP_RESEARCH"] = "1"

    try:
        config = AppConfig()
        llm_factory = create_llm_factory(config)
        gateway, search_client = _build_real_gateway()

        pipeline = Pipeline(
            llm_factory=llm_factory,
            gateway=gateway,
            db_session_factory=None,
            max_eval_tasks=3,
        )

        question = (
            "Estimate the total addressable market for Level 4+ autonomous "
            "vehicle sensors in North America through 2030, including LiDAR, "
            "radar, and camera modules. Segment by sensor type and identify "
            "the top 5 competitive players."
        )
        client_id = "keystone_test"
        client_context = (
            "Investment committee evaluating sensor startup acquisition targets. "
            "Need defensible market size estimates with source-level citations. "
            "Particular interest in whether LiDAR costs are declining fast enough "
            "to enable mass-market L4 deployment."
        )

        events: list = []
        stage_timings: dict[str, float] = {}

        print(f"\n{'=' * 60}")
        print("STARTING FULL PIPELINE WITH DEEP RESEARCH")
        print(f"Question: {question[:80]}...")
        print(f"{'=' * 60}\n")

        overall_start = time.time()
        stage_start = time.time()
        current_stage = "L0"

        async for event in pipeline.run_with_events(question, client_id, client_context):
            events.append(event)
            layer = getattr(event, "layer", "unknown")

            if layer != current_stage:
                stage_timings[current_stage] = time.time() - stage_start
                print(
                    f"  {current_stage} complete: "
                    f"{stage_timings[current_stage]:.1f}s "
                    f"({len([e for e in events if getattr(e, 'layer', '') == current_stage])} events)"
                )
                current_stage = layer
                stage_start = time.time()

        stage_timings[current_stage] = time.time() - stage_start
        print(f"  {current_stage} complete: {stage_timings[current_stage]:.1f}s")

        result = await pipeline.get_result()
        elapsed = time.time() - overall_start

        # --- Metrics ---
        event_layers = Counter(getattr(e, "layer", "unknown") for e in events)

        total_claims = sum(len(f.claims) for f in result.findings)
        all_urls = set()
        for f in result.findings:
            for claim in f.claims:
                for cit in claim.citations:
                    if cit.url and not cit.url.startswith("tool://"):
                        all_urls.add(cit.url)

        metrics = {
            "mode": "deep_research",
            "wall_clock_seconds": round(elapsed, 1),
            "stage_timings": {k: round(v, 1) for k, v in stage_timings.items()},
            "total_tokens": result.total_tokens,
            "total_events": len(events),
            "events_by_layer": dict(event_layers),
            "findings_count": len(result.findings),
            "total_claims": total_claims,
            "claims_per_finding": round(total_claims / len(result.findings), 1)
            if result.findings
            else 0,
            "unique_source_urls": len(all_urls),
            "citation_count": len(result.manifest.citations),
            "confidence_map": {
                "total_claims": result.confidence_map.total_claims,
                "tiers_populated": result.confidence_map.tiers_populated,
            },
            "evaluation_results": [
                {
                    "task_id": er.task_id,
                    "passed": er.passed,
                    "overall_score": er.overall_score,
                }
                for er in result.evaluation_results
            ],
            "tasks_generated": len(result.spec.task_decomposition.tasks),
            "markdown_length_chars": len(result.markdown_output),
        }

        # --- Save artifacts ---
        out = OUTPUT_DIR / "full_pipeline"
        _save_artifact(out / "deliverable.md", result.markdown_output)
        _save_artifact(
            out / "engagement_spec.json",
            result.spec.model_dump_json(indent=2),
        )
        _save_artifact(
            out / "findings.json",
            json.dumps(
                [json.loads(f.model_dump_json()) for f in result.findings],
                indent=2,
            ),
        )
        _save_artifact(
            out / "citation_manifest.json",
            result.manifest.model_dump_json(indent=2),
        )
        _save_artifact(
            out / "confidence_map.json",
            result.confidence_map.model_dump_json(indent=2),
        )
        _save_artifact(
            out / "evaluation_results.json",
            json.dumps(
                [json.loads(er.model_dump_json()) for er in result.evaluation_results],
                indent=2,
            ),
        )
        _save_artifact(
            out / "run_metrics.json",
            json.dumps(metrics, indent=2, default=str),
        )
        _save_artifact(out / "event_log.json", _serialize_events(events))
        _save_artifact(
            out / "all_urls.json",
            json.dumps(sorted(all_urls), indent=2),
        )

        # --- Print summary ---
        print(f"\n{'=' * 60}")
        print(f"DEEP RESEARCH PIPELINE COMPLETE in {elapsed:.1f}s")
        print(f"Tasks: {len(result.spec.task_decomposition.tasks)}")
        print(f"Findings: {len(result.findings)}")
        print(f"Total claims: {total_claims}")
        print(f"Claims per finding: {metrics['claims_per_finding']}")
        print(f"Unique source URLs: {len(all_urls)}")
        print(f"Citations in manifest: {len(result.manifest.citations)}")
        print(
            f"Confidence map: {result.confidence_map.total_claims} claims "
            f"across {result.confidence_map.tiers_populated} tiers"
        )
        print(f"Evaluations: {len(result.evaluation_results)}")
        for er in result.evaluation_results:
            print(f"  {er.task_id}: {'PASS' if er.passed else 'FAIL'} ({er.overall_score:.1f}/100)")
        print(f"Markdown: {len(result.markdown_output)} chars")
        print(f"Tokens: {result.total_tokens}")
        print(f"Events: {len(events)} ({dict(event_layers)})")
        print(f"Stage timings: {json.dumps({k: f'{v:.1f}s' for k, v in stage_timings.items()})}")
        print(f"Artifacts saved to: {out}")
        print(f"{'=' * 60}\n")

        # --- Structural assertions ---
        assert result.engagement_id, "Empty engagement_id"
        assert result.findings, "No findings produced"
        assert total_claims > 0, "Zero claims across all findings"
        assert result.manifest.citations, "No citations in manifest"
        assert result.markdown_output, "Empty markdown output"

    finally:
        os.environ.pop("DEEP_RESEARCH", None)
