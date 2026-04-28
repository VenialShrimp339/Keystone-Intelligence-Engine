"""Full end-to-end pipeline test: L0 → L1 → CitProc → L1.5 → L2 → L4 → Render.

Exercises the complete Pipeline.run_with_events() path with a real question.
Writes all intermediate outputs to output/{engagement_id}/ for inspection.

Run from the repo root:

    source .venv/bin/activate
    python scripts/full_pipeline_test.py

Optional env vars:
    TEST_QUESTION="your question here"   Override the default test question
    PIPELINE__RESEARCH_QUALITY_THRESHOLD=0.5   Lower the quality bar for testing
    DEEP_RESEARCH=1                      Enable deep web research mode
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from keystone.gateway.factory import build_mcp_gateway
from keystone.llm_client import LayerAwareLLMFactory
from keystone.models.config import AppConfig
from keystone.pipeline.orchestrator import Pipeline


DEFAULT_QUESTION = (
    "Evaluate the competitive landscape of the US auto body repair industry "
    "across the top 10 metropolitan areas by population. Identify the largest "
    "chains, their market share, and whether the market is consolidating or "
    "fragmenting. What would a new entrant need to know?"
)

CLIENT_ID = "client_keystone_internal"

OUT_DIR = REPO_ROOT / "output"


def _event_summary(event) -> str:
    parts = [f"[{type(event).__name__}]"]
    for attr in (
        "engagement_id",
        "agent_id",
        "task_id",
        "claim_count",
        "confidence_range",
        "sources_consulted",
        "tokens_consumed",
        "absence_count",
        "task_count",
        "categories",
        "spec_version",
        "validation_passed",
        "layer",
    ):
        val = getattr(event, attr, None)
        if val is None:
            continue
        s = str(val)
        if len(s) > 120:
            s = s[:117] + "..."
        parts.append(f"{attr}={s}")
    return " ".join(parts)


async def _main() -> int:
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY is set. claude -p would bill to API, not the "
            "Max subscription. Run `unset ANTHROPIC_API_KEY` and retry.",
            file=sys.stderr,
        )
        return 2

    question = os.environ.get("TEST_QUESTION", DEFAULT_QUESTION)
    client_context = os.environ.get(
        "TEST_CLIENT_CONTEXT",
        "Internal research for The Keystone Group, a boutique consulting firm. "
        "This research informs a potential client engagement.",
    )

    config = AppConfig()
    factory = LayerAwareLLMFactory(config)
    gateway = build_mcp_gateway()

    pipeline = Pipeline(
        llm_factory=factory,
        gateway=gateway,
        pipeline_config=config.pipeline,
    )

    print("=" * 70)
    print("FULL PIPELINE END-TO-END TEST")
    print("=" * 70)
    print(f"Question: {question[:200]}")
    print(f"Client:   {CLIENT_ID}")
    print(f"Profile:  (auto-classified)")
    print(f"Deep:     {os.environ.get('DEEP_RESEARCH', '0')}")
    print(f"Models:   flagship={config.flagship_model}, standard={config.standard_model}")
    print("=" * 70)
    print()

    start = time.monotonic()
    events: list = []
    engagement_id = None

    try:
        async for event in pipeline.run_with_events(
            question=question,
            client_id=CLIENT_ID,
            client_context=client_context,
        ):
            events.append(event)
            summary = _event_summary(event)
            elapsed = time.monotonic() - start
            print(f"[{elapsed:7.1f}s] {summary}", flush=True)

            if engagement_id is None:
                eid = getattr(event, "engagement_id", None)
                if eid:
                    engagement_id = eid

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.", file=sys.stderr)
        _dump_partial(events, engagement_id, start)
        return 130

    except Exception as exc:
        print(f"\nFATAL: pipeline raised {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        _dump_partial(events, engagement_id, start)
        return 1

    elapsed = time.monotonic() - start
    print(f"\n--- Pipeline finished in {elapsed:.1f}s ({len(events)} events) ---\n")

    try:
        result = await pipeline.get_result()
    except RuntimeError as exc:
        print(f"FATAL: get_result() failed: {exc}", file=sys.stderr)
        return 1

    _print_summary(result, elapsed)
    _persist_results(result, events)

    return 0


def _dump_partial(events: list, engagement_id: str | None, start: float) -> None:
    elapsed = time.monotonic() - start
    eid = engagement_id or "unknown"
    out = OUT_DIR / eid
    out.mkdir(parents=True, exist_ok=True)

    events_blob = []
    for e in events:
        try:
            events_blob.append(e.model_dump(mode="json"))
        except Exception:
            events_blob.append({"type": type(e).__name__, "error": "serialization_failed"})

    path = out / "partial_events.json"
    path.write_text(json.dumps(events_blob, indent=2))
    print(f"\nPartial events ({len(events)}) written to {path}")
    print(f"Elapsed before interruption: {elapsed:.1f}s")


def _print_summary(result, elapsed: float) -> None:
    print("=" * 70)
    print("PIPELINE RESULT SUMMARY")
    print("=" * 70)
    print(f"Engagement ID:     {result.engagement_id}")
    print(f"Total events:      {result.total_events}")
    print(f"Total tokens:      {result.total_tokens}")
    print(f"Elapsed:           {elapsed:.1f}s")
    print()

    if result.spec:
        spec = result.spec
        rs = spec.research_spec
        print(f"Profile:           {rs.effective_pipeline_profile.value}")
        if hasattr(rs, "engagement_type") and rs.engagement_type:
            print(f"Engagement type:   {rs.engagement_type.value}")
        if hasattr(rs, "domain") and rs.domain:
            print(f"Domain:            {rs.domain}")
        print(f"Tasks:             {len(spec.task_decomposition.tasks)}")
        print(
            f"Validation:        intent_clear={spec.validation_report.intent_clear}, "
            f"scope_valid={spec.validation_report.scope_valid}"
        )
        print()

    if result.findings:
        total_claims = sum(len(f.claims) for f in result.findings)
        total_sources = sum(f.sources_consulted for f in result.findings)
        print(f"Findings:          {len(result.findings)}")
        print(f"Total claims:      {total_claims}")
        print(f"Total sources:     {total_sources}")
        print()

    if result.evaluation_results:
        for task_id, eval_result in result.evaluation_results.items():
            score = eval_result.composite_score if eval_result.composite_score else "N/A"
            passed = eval_result.passed
            print(f"  [{task_id}] score={score}, passed={passed}")
        print()

    if result.markdown_output:
        word_count = len(result.markdown_output.split())
        print(f"Output:            {word_count} words")
    else:
        print("Output:            (none)")

    if result.tokens_by_layer:
        print()
        print("Tokens by layer:")
        for layer, tokens in sorted(result.tokens_by_layer.items()):
            print(f"  {layer}: {tokens}")

    print("=" * 70)


def _persist_results(result, events: list) -> None:
    out = OUT_DIR / result.engagement_id
    out.mkdir(parents=True, exist_ok=True)

    events_blob = []
    for e in events:
        try:
            events_blob.append(e.model_dump(mode="json"))
        except Exception:
            events_blob.append({"type": type(e).__name__, "error": "serialization_failed"})

    (out / "events.json").write_text(json.dumps(events_blob, indent=2))

    if result.spec:
        (out / "spec.json").write_text(result.spec.model_dump_json(indent=2))

    if result.manifest:
        (out / "citation_manifest.json").write_text(result.manifest.model_dump_json(indent=2))

    if result.confidence_map:
        (out / "confidence_map.json").write_text(result.confidence_map.model_dump_json(indent=2))

    if result.findings:
        findings_dir = out / "findings"
        findings_dir.mkdir(exist_ok=True)
        for finding in result.findings:
            path = findings_dir / f"{finding.task_id}.json"
            path.write_text(finding.model_dump_json(indent=2))

    if result.evaluation_results:
        evals_dir = out / "evaluations"
        evals_dir.mkdir(exist_ok=True)
        for task_id, eval_result in result.evaluation_results.items():
            path = evals_dir / f"{task_id}.json"
            path.write_text(eval_result.model_dump_json(indent=2))

    if result.markdown_output:
        (out / "final_brief.md").write_text(result.markdown_output)

    print(f"\nAll results written to {out}/")
    print(f"  spec.json, events.json, citation_manifest.json, confidence_map.json")
    print(f"  findings/*.json, evaluations/*.json, final_brief.md")


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
