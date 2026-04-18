"""Full pipeline integration test -- real GPT-5.4 + real Exa/Brave search.

First end-to-end run of the Keystone Intelligence Engine with live APIs.
Captures all artifacts to output/first_real_run/ for human review.

Run with: pytest tests/integration/test_pipeline_real.py -v -m integration -s
Consumes significant API quota (~10+ LLM calls, ~10+ search calls).
"""

from __future__ import annotations

import json
import logging
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
from keystone.llm_client import _client_cache, create_llm_factory
from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier
from keystone.pipeline.orchestrator import Pipeline, PipelineResult

# Load .env for OPENAI_AUTH_TYPE, CODEX_AUTH_FILE, API keys
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration

# Project root for output directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "first_real_run"


@pytest.fixture(autouse=True)
def _fresh_client():
    _client_cache.clear()
    yield
    _client_cache.clear()


def _build_real_gateway() -> tuple[MCPGateway, SimpleMCPClient]:
    """Build an MCPGateway wired to real Exa/Brave search."""
    search_client = SimpleMCPClient()

    registry = ToolRegistry()
    # Register the tools that agents will be assigned by the spec engine.
    # SimpleMCPClient handles exa_search and brave_search natively;
    # other tools return stubs (which is fine -- agents continue with partial data).
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

    gateway = MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=search_client,
    )

    return gateway, search_client


def _save_artifact(path: Path, content: str) -> None:
    """Write content to path, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _serialize_events(events: list) -> str:
    """Serialize pipeline events to JSON array."""
    serialized = []
    for event in events:
        try:
            serialized.append(json.loads(event.model_dump_json()))
        except Exception as exc:
            serialized.append(
                {
                    "error": f"Failed to serialize {type(event).__name__}: {exc}",
                    "event_type": type(event).__name__,
                    "layer": getattr(event, "layer", "unknown"),
                }
            )
    return json.dumps(serialized, indent=2, default=str)


@pytest.mark.asyncio
@pytest.mark.timeout(600)
async def test_full_pipeline_real():
    """Run the complete pipeline with real LLM and real search.

    This is a DIAGNOSTIC run. We capture everything and save artifacts
    for human review. We do NOT judge output quality.
    """
    # --- Setup ---
    config = AppConfig()
    llm_factory = create_llm_factory(config)
    gateway, search_client = _build_real_gateway()

    pipeline = Pipeline(
        llm_factory=llm_factory,
        gateway=gateway,
        db_session_factory=None,  # Skip HITL gates
        max_eval_tasks=3,  # Cap evaluation to first 3 tasks (Codex OAuth is slow)
    )

    question = (
        "Estimate the total addressable market for Level 4+ autonomous vehicle "
        "sensors in North America through 2030, including LiDAR, radar, and "
        "camera modules. Segment by sensor type and identify the top 5 "
        "competitive players."
    )
    client_id = "keystone_test"
    client_context = (
        "Investment committee evaluating sensor startup acquisition targets. "
        "Need defensible market size estimates with source-level citations. "
        "Particular interest in whether LiDAR costs are declining fast enough "
        "to enable mass-market L4 deployment."
    )

    # --- Run pipeline, collecting events and per-stage timing ---
    events: list = []
    stage_timings: dict[str, float] = {}
    errors_encountered: list[dict] = []

    print(f"\n{'=' * 60}")
    print("STARTING FULL PIPELINE RUN")
    print(f"Question: {question[:80]}...")
    print(f"{'=' * 60}\n")

    overall_start = time.time()

    try:
        # Use run_with_events for event collection, then get_result
        stage_start = time.time()
        current_stage = "L0"

        async for event in pipeline.run_with_events(question, client_id, client_context):
            events.append(event)
            layer = getattr(event, "layer", "unknown")

            # Track stage transitions for timing
            if layer != current_stage:
                stage_timings[current_stage] = time.time() - stage_start
                print(
                    f"  {current_stage} complete: {stage_timings[current_stage]:.1f}s "
                    f"({len([e for e in events if getattr(e, 'layer', '') == current_stage])} events)"
                )
                current_stage = layer
                stage_start = time.time()

        # Record final stage timing
        stage_timings[current_stage] = time.time() - stage_start
        print(f"  {current_stage} complete: {stage_timings[current_stage]:.1f}s")

        result = await pipeline.get_result()
        result = result.model_copy(update={"total_events": len(events)})

    except Exception as exc:
        elapsed = time.time() - overall_start
        errors_encountered.append(
            {
                "stage": "pipeline_run",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "elapsed_seconds": elapsed,
            }
        )
        # Save what we have even on failure
        _save_artifact(
            OUTPUT_DIR / "run_errors.json",
            json.dumps(errors_encountered, indent=2, default=str),
        )
        _save_artifact(
            OUTPUT_DIR / "event_log.json",
            _serialize_events(events),
        )
        raise

    elapsed = time.time() - overall_start

    # --- Collect metrics ---
    event_layers = Counter(getattr(e, "layer", "unknown") for e in events)
    agent_count = len(result.findings)
    succeeded_agents = sum(1 for f in result.findings if f.claims)

    live_citations = (
        sum(1 for c in result.manifest.citations if c.url_live is True)
        if result.manifest.citations
        else 0
    )
    dead_citations = (
        sum(1 for c in result.manifest.citations if c.url_live is False)
        if result.manifest.citations
        else 0
    )

    metrics = {
        "wall_clock_seconds": round(elapsed, 1),
        "stage_timings": {k: round(v, 1) for k, v in stage_timings.items()},
        "total_tokens": result.total_tokens,
        "total_events": len(events),
        "events_by_layer": dict(event_layers),
        "llm_call_count": "see_event_log",  # LLM calls aren't individually tracked yet
        "search_calls": {
            "total": search_client.call_count,
            "exa": search_client.exa_calls,
            "brave": search_client.brave_calls,
        },
        "agent_count": agent_count,
        "succeeded_agents": succeeded_agents,
        "citation_count": {
            "total": len(result.manifest.citations),
            "live": live_citations,
            "dead": dead_citations,
        },
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
        "errors_encountered": errors_encountered,
    }

    # --- Save all artifacts ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _save_artifact(
        OUTPUT_DIR / "deliverable.md",
        result.markdown_output,
    )
    _save_artifact(
        OUTPUT_DIR / "engagement_spec.json",
        result.spec.model_dump_json(indent=2),
    )
    _save_artifact(
        OUTPUT_DIR / "findings.json",
        json.dumps(
            [json.loads(f.model_dump_json()) for f in result.findings],
            indent=2,
        ),
    )
    _save_artifact(
        OUTPUT_DIR / "citation_manifest.json",
        result.manifest.model_dump_json(indent=2),
    )
    _save_artifact(
        OUTPUT_DIR / "confidence_map.json",
        result.confidence_map.model_dump_json(indent=2),
    )
    _save_artifact(
        OUTPUT_DIR / "evaluation_results.json",
        json.dumps(
            [json.loads(er.model_dump_json()) for er in result.evaluation_results],
            indent=2,
        ),
    )
    _save_artifact(
        OUTPUT_DIR / "run_metrics.json",
        json.dumps(metrics, indent=2, default=str),
    )
    _save_artifact(
        OUTPUT_DIR / "event_log.json",
        _serialize_events(events),
    )

    # --- Structural assertions ONLY (not quality) ---
    assert result.engagement_id, "Empty engagement_id"
    assert result.findings, "No findings produced"
    assert result.manifest.citations, "No citations in manifest"
    assert result.confidence_map.total_claims > 0, "Empty confidence map"
    assert result.markdown_output, "Empty markdown output"
    assert "## Executive Summary" in result.markdown_output, "Missing Executive Summary"
    assert "## Sources" in result.markdown_output, "Missing Sources section"

    # --- Print summary ---
    print(f"\n{'=' * 60}")
    print(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    print(f"Tasks: {len(result.spec.task_decomposition.tasks)}")
    print(f"Findings: {len(result.findings)}")
    print(
        f"Citations: {len(result.manifest.citations)} "
        f"(live: {live_citations}, dead: {dead_citations})"
    )
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
    print(
        f"Search calls: {search_client.call_count} "
        f"(exa: {search_client.exa_calls}, brave: {search_client.brave_calls})"
    )
    print(f"Stage timings: {json.dumps({k: f'{v:.1f}s' for k, v in stage_timings.items()})}")
    print(f"Artifacts saved to: {OUTPUT_DIR}")
    print(f"{'=' * 60}\n")

    # Print deliverable preview
    lines = result.markdown_output.split("\n")
    print("=== DELIVERABLE PREVIEW (first 100 lines) ===")
    print("\n".join(lines[:100]))
    if len(lines) > 100:
        print(f"\n... [{len(lines) - 100} more lines in {OUTPUT_DIR / 'deliverable.md'}]")
