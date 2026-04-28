"""First live L1 deep-mode run: single ResearchAgent, real web research.

Hand-crafted task mirroring the A1 ("Multi-Agent Research & Analysis
Systems") stream from the project's founding research. Bypasses L0 so
the test targets exactly one moving part -- the deep-research path
through ``claude -p --allowedTools WebSearch,WebFetch``.

Run from the repo root:

    source .venv/bin/activate
    python scripts/l1_deep_mode_test.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from keystone.gateway.factory import build_mcp_gateway
from keystone.llm_client import LayerAwareLLMFactory
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
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskImportance,
    TaskType,
)
from keystone.research.research_agent import ResearchAgent

ENGAGEMENT_ID = "eng_a1_deep_test"
CLIENT_ID = "client_keystone_internal"
TASK_ID = "task_a1_multi_agent_survey"
AGENT_ID = "agent_a1_qualitative"

OUT_DIR = REPO_ROOT / "output"
FINDING_PATH = OUT_DIR / "l1_deep_mode_test_finding.json"
EVENTS_PATH = OUT_DIR / "l1_deep_mode_test_events.json"


def _build_task() -> ResearchTask:
    return ResearchTask(
        id=TASK_ID,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        category=TaskCategory.TECHNOLOGY_ASSESSMENT,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description=(
            "Survey and evaluate existing multi-agent AI systems designed for "
            "automated research and analysis. Assess GPT-Researcher, STORM/Co-STORM "
            "from Stanford, deep research skill implementations (199-Biotechnologies, "
            "Cranot), and any production multi-agent research systems. For each "
            "system analyze: architecture and agent coordination patterns, quality "
            "control and evaluation mechanisms, search infrastructure and source "
            "coverage, failure modes and limitations. Determine which architectural "
            "patterns produce the deepest analysis and which components could be "
            "reused vs must be built from scratch."
        ),
        acceptance_criteria=[
            "Name at least 5 distinct multi-agent research systems with sources",
            "For each system, describe the agent coordination pattern",
            "Identify at least 3 documented failure modes across the surveyed systems",
            "State explicit adopt / adapt / skip verdict for each system",
            "Cite at least one primary source (paper, official docs, or repo) per system",
        ],
        deliverable_destination="Section 2: A1 Multi-Agent Research Architecture Survey",
        priority=1,
        importance=TaskImportance.PRIMARY,
        anti_confirmatory_framing=(
            "Evaluate both the strengths and fundamental limitations of existing "
            "multi-agent research systems, including evidence that simpler "
            "single-agent approaches may outperform multi-agent architectures "
            "in certain conditions"
        ),
        assigned_tools=["exa_search", "brave_search", "paper_search"],
        assigned_model=ModelTier.STANDARD,
        end_product=(
            "Comparative architecture analysis with specific recommendations on "
            "adopt/adapt/skip for each system"
        ),
    )


def _build_spec(task: ResearchTask) -> EngagementSpec:
    research_spec = ResearchSpec(
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        title="Multi-Agent Research Architecture Survey for Keystone Intelligence Engine",
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context=(
            "Keystone is designing a consulting-grade multi-agent research pipeline. "
            "This research informs which architectural patterns to adopt, which to "
            "adapt, and which to skip -- deciding whether to reuse prior components "
            "vs. build new ones. The output feeds component selection for L1 research."
        ),
        surprising_finding=(
            "A surprising finding would be that simpler single-agent deep research "
            "outperforms multi-agent coordination on consulting-grade analytical depth, "
            "or that one of the existing systems already solves the coordination "
            "problem we think we need to solve from scratch."
        ),
        questions=[
            ResearchQuestion(
                question=(
                    "Which architectural patterns in existing multi-agent research "
                    "systems produce the deepest analysis, and which components can "
                    "Keystone reuse vs. must build from scratch?"
                ),
                is_primary=True,
            ),
            ResearchQuestion(
                question=(
                    "Under what conditions do simpler single-agent approaches "
                    "outperform multi-agent architectures?"
                ),
            ),
        ],
        output_format="markdown",
        quality_bar=(
            "MBB-grade: a McKinsey/Bain/BCG partner would accept this as a "
            "credible technology landscape chapter. Claims are sourced, hedged "
            "appropriately, and actionable."
        ),
        engagement_type=EngagementType.EVALUATIVE,
        effective_pipeline_profile=PipelineProfile.DEEP,
    )
    decomposition = TaskDecomposition(
        project=research_spec.title,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        research_md_path=f"{ENGAGEMENT_ID}/RESEARCH.md",
        specification_version=1,
        decomposition_rationale=(
            "Single-task decomposition for the L1 deep-mode smoke test. "
            "Mirrors the original A1 research stream."
        ),
        tasks=[task],
    )
    validation_report = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )
    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=validation_report,
    )


def _build_agent() -> AgentInstance:
    definition = AgentDefinition(
        name="a1_qualitative_analyst",
        description=(
            "Qualitative research specialist surveying multi-agent research system "
            "architectures for Keystone L1 selection."
        ),
        role=AgentRole.RESEARCH,
        model=ModelTier.STANDARD,
        tools=["exa_search", "brave_search", "paper_search"],
        research_type=ResearchAgentType.QUALITATIVE,
    )
    return AgentInstance(
        agent_id=AGENT_ID,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        definition=definition,
        working_dir=f"/tmp/keystone/{AGENT_ID}",
    )


def _event_summary(event) -> str:
    parts = [f"[{type(event).__name__}]"]
    for attr in (
        "agent_id",
        "task_id",
        "claim_count",
        "confidence_range",
        "sources_consulted",
        "tokens_consumed",
        "absence_count",
        "url",
        "source_type",
        "citation_id",
        "title",
    ):
        val = getattr(event, attr, None)
        if val is None:
            continue
        s = str(val)
        if len(s) > 100:
            s = s[:97] + "..."
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

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    config = AppConfig()
    factory = LayerAwareLLMFactory(config)
    standard_llm = factory(ModelTier.STANDARD)
    deep_llm = factory.deep_research_callable()

    gateway = build_mcp_gateway()

    task = _build_task()
    spec = _build_spec(task)
    agent_instance = _build_agent()

    research_agent = ResearchAgent(
        llm=standard_llm,
        gateway=gateway,
        deep_llm=deep_llm,
        current_tier=ModelTier.STANDARD,
    )

    print(f"=== L1 DEEP MODE TEST ===")
    print(f"Task: {TASK_ID}")
    print(f"Agent: {AGENT_ID} (research_type={agent_instance.definition.research_type.value})")
    print(f"Tools (for audit parity only): {task.assigned_tools}")
    print(f"Deep timeout: {config.pipeline.deep_research_timeout_s}s")
    print(f"Claude model (deep): {config.standard_model}")
    print()
    print("--- Streaming events ---")

    start = time.monotonic()
    events: list = []
    try:
        async for event in research_agent.execute(task, spec, agent_instance):
            events.append(event)
            print(_event_summary(event), flush=True)
    except Exception as exc:
        print(f"\nFATAL: execute() raised {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        # Still dump any events we accumulated for diagnosis
        events_blob = [e.model_dump(mode="json") for e in events]
        EVENTS_PATH.write_text(json.dumps(events_blob, indent=2))
        print(f"\nPartial events written to {EVENTS_PATH}")
        return 1

    elapsed = time.monotonic() - start
    print(f"\n--- execute() finished in {elapsed:.1f}s ({len(events)} events) ---\n")

    try:
        finding = await research_agent.get_finding()
    except RuntimeError as exc:
        print(f"FATAL: get_finding() failed: {exc}", file=sys.stderr)
        return 1

    # --- Summary ---
    n_claims = len(finding.claims)
    n_sources = finding.sources_consulted
    n_tokens = finding.tokens_consumed

    # URL sanity: real URLs vs placeholder-shaped refs
    placeholder_prefixes = ("ref://", "tool://", "placeholder://", "example://")
    real_urls = [
        cit.url
        for claim in finding.claims
        for cit in claim.citations
        if cit.url and not cit.url.startswith(placeholder_prefixes)
    ]
    unique_real_urls = sorted(set(real_urls))

    print("=" * 60)
    print(f"Claims produced:       {n_claims}")
    print(f"Sources consulted:     {n_sources}")
    print(f"Unique real URLs:      {len(unique_real_urls)}")
    print(f"Tokens consumed (est): {n_tokens}")
    print(f"Status:                {finding.status.value}")
    print(f"Absence report items:  {len(finding.absence_report)}")
    print(f"Dropped claims:        {len(finding.dropped_claims)}")
    print("=" * 60)

    print("\n--- Per-claim sample ---")
    for idx, claim in enumerate(finding.claims, start=1):
        first_url = claim.citations[0].url if claim.citations else "<no citation>"
        snippet = claim.text.strip()
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        print(
            f"{idx:02d}. [{claim.confidence_tier.value} {claim.confidence:.2f}] "
            f"cits={len(claim.citations)}  url0={first_url}"
        )
        print(f"    {snippet}")

    print("\n--- Absence report ---")
    for i, gap in enumerate(finding.absence_report, start=1):
        print(f"{i:02d}. {gap}")

    if finding.dropped_claims:
        print("\n--- Dropped claims ---")
        for dc in finding.dropped_claims:
            print(f"- {dc}")

    # --- Persist full finding JSON ---
    FINDING_PATH.write_text(finding.model_dump_json(indent=2))
    events_blob = [e.model_dump(mode="json") for e in events]
    EVENTS_PATH.write_text(json.dumps(events_blob, indent=2))
    print(f"\nFinding JSON: {FINDING_PATH}")
    print(f"Events JSON:  {EVENTS_PATH}")

    # --- Success criteria ---
    ok = True
    if n_claims < 15:
        print(f"WARN: only {n_claims} claims (target 15+)")
        ok = False
    if n_sources < 10:
        print(f"WARN: only {n_sources} sources consulted (target 10+)")
        ok = False
    if not unique_real_urls:
        print("WARN: no real URLs surfaced")
        ok = False
    if elapsed > 15 * 60:
        print(f"WARN: runtime {elapsed:.0f}s exceeded 15-min target")
        ok = False
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
