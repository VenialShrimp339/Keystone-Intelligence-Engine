"""Smoke test for downstream layers with real claude -p LLM calls.

Feeds a synthetic ``StructuredFinding`` through each downstream component
(CitationProcessor -> L1.5 Deliberation -> L4 Evaluator -> Renderer),
isolated so that one layer's failure does not block the others. Prints
events as they arrive and writes the final rendered markdown to
``output/downstream_test_render.md``.

Run:
    source .venv/bin/activate
    python scripts/downstream_smoke_test.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import UTC, date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from keystone.citation.processor import CitationProcessor
from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.llm_client import create_llm_factory
from keystone.models.agents import DeliberationAnalystType
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.config import AppConfig
from keystone.models.evaluation import (
    EvaluationIntensity,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    EvaluationProfileName,
    FindingClaim,
    FindingStatus,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
    ValidationReport,
)
from keystone.models.structuring import (
    AnalyticalFramework,
    FrameworkHint,
    OutlineItem,
    OutlineItemType,
    OutlineSectionType,
    StructuredOutline,
    StructuredSection,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskImportance,
    TaskType,
)
from keystone.pipeline.markdown_renderer import MarkdownRenderer

ENGAGEMENT_ID = "eng_downstream_smoke"
CLIENT_ID = "client_keystone_internal"
TASK_ID = "task_multi_agent_survey"
AGENT_ID = "agent_qualitative_01"

OUT_DIR = REPO_ROOT / "output"
RENDER_PATH = OUT_DIR / "downstream_test_render.md"
EVENTS_PATH = OUT_DIR / "downstream_test_events.json"


# ---------------------------------------------------------------------------
# Synthetic fixture builders
# ---------------------------------------------------------------------------


def _citation(
    cid: str,
    url: str,
    title: str,
    source_type: SourceType,
    quality: float,
    pub: str = "",
    authors: list[str] | None = None,
    published: date | None = None,
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        url=url,
        title=title,
        authors=authors or [],
        publication=pub,
        date_published=published,
        access_date=datetime.now(UTC),
        source_type=source_type,
        quality_score=quality,
        found_by_agents=[AGENT_ID],
    )


def _claim(
    text: str,
    evidence: str,
    citations: list[Citation],
    confidence: float,
    tier: ConfidenceTier,
    caveats: list[str] | None = None,
    claim_id: str | None = None,
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence=evidence,
        citations=citations,
        confidence=confidence,
        confidence_tier=tier,
        caveats=caveats or [],
        claim_id=claim_id,
    )


def build_finding() -> StructuredFinding:
    """Synthetic finding: 6 claims about multi-agent AI systems with real URLs.

    Confidence tiers intentionally span the range: HIGH (0.85), MODERATE
    (0.75, 0.65), WEAK (0.55), CONTESTED (0.45), INSUFFICIENT (0.30).
    Includes one contradictory claim pair on hallucination / CoT reasoning.
    """
    autogen_paper = _citation(
        "CIT-001",
        "https://arxiv.org/abs/2308.08155",
        "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
        SourceType.ACADEMIC,
        quality=0.88,
        pub="arXiv",
        authors=["Wu", "Bansal", "Zhang"],
        published=date(2023, 8, 16),
    )
    autogen_repo = _citation(
        "CIT-002",
        "https://github.com/microsoft/autogen",
        "microsoft/autogen",
        SourceType.REPORT,
        quality=0.70,
        pub="GitHub",
    )
    anthropic_mas = _citation(
        "CIT-003",
        "https://www.anthropic.com/research/multi-agent-research-system",
        "How we built our multi-agent research system",
        SourceType.REPORT,
        quality=0.82,
        pub="Anthropic Research",
        published=date(2025, 6, 13),
    )
    storm_repo = _citation(
        "CIT-004",
        "https://github.com/stanford-oval/storm",
        "stanford-oval/storm",
        SourceType.REPORT,
        quality=0.74,
        pub="GitHub",
    )
    cot_paper = _citation(
        "CIT-005",
        "https://arxiv.org/abs/2201.11903",
        "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        SourceType.ACADEMIC,
        quality=0.90,
        pub="NeurIPS 2022",
        authors=["Wei", "Wang", "Schuurmans"],
        published=date(2022, 1, 28),
    )
    cot_faithful_paper = _citation(
        "CIT-006",
        "https://arxiv.org/abs/2305.04388",
        "Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting",
        SourceType.ACADEMIC,
        quality=0.86,
        pub="NeurIPS 2023",
        authors=["Turpin", "Michael", "Perez", "Bowman"],
        published=date(2023, 5, 7),
    )
    dead_url = _citation(
        "CIT-007",
        "https://example.com/notarealmultiagentsurvey-404",
        "Fictional Multi-Agent Survey (dead link to exercise URL check)",
        SourceType.REPORT,
        quality=0.40,
    )

    claims = [
        _claim(
            text=(
                "AutoGen's conversable-agent abstraction has become the de facto "
                "reference pattern for multi-agent LLM applications, with >35k "
                "GitHub stars and broad adoption across industry prototypes."
            ),
            evidence=(
                "Wu et al. (2023) introduce the agent-conversation framework; the "
                "microsoft/autogen repository shows sustained commit velocity and "
                "community adoption consistent with reference-pattern status."
            ),
            citations=[autogen_paper, autogen_repo],
            confidence=0.85,
            tier=ConfidenceTier.HIGH,
            claim_id="CLM-001",
        ),
        _claim(
            text=(
                "Anthropic's production multi-agent research system relies on an "
                "orchestrator-subagent hierarchy with context isolation per "
                "subtask, reporting a ~90% reduction in research time versus a "
                "single-agent baseline."
            ),
            evidence=(
                "Anthropic's engineering post describes a LeadResearcher agent "
                "that plans and delegates to parallel subresearchers, each with "
                "its own context window and tool budget."
            ),
            citations=[anthropic_mas],
            confidence=0.75,
            tier=ConfidenceTier.MODERATE,
            caveats=[
                "Self-reported benchmark; no external replication yet",
                "Evaluation set not released publicly",
            ],
            claim_id="CLM-002",
        ),
        _claim(
            text=(
                "Stanford's STORM pipeline demonstrates that multi-perspective "
                "question decomposition with retrieval grounding materially "
                "improves topical coverage versus single-agent report writers."
            ),
            evidence=(
                "The stanford-oval/storm repository and associated NAACL 2024 "
                "paper show perspective-conditioned retrieval outperforming "
                "direct-generation baselines on Wikipedia-style article tasks."
            ),
            citations=[storm_repo],
            confidence=0.65,
            tier=ConfidenceTier.MODERATE,
            caveats=["Benchmarked on narrow Wikipedia-article domain"],
            claim_id="CLM-003",
        ),
        _claim(
            text=(
                "Chain-of-thought prompting materially reduces hallucinations in "
                "multi-hop reasoning by forcing intermediate computation to be "
                "visible and externally verifiable."
            ),
            evidence=(
                "Wei et al. (2022) show CoT substantially improves arithmetic "
                "and commonsense reasoning accuracy on GSM8K and SVAMP."
            ),
            citations=[cot_paper],
            confidence=0.55,
            tier=ConfidenceTier.WEAK,
            claim_id="CLM-004",
        ),
        _claim(
            # Deliberate contradiction with CLM-004.
            text=(
                "Chain-of-thought explanations frequently misrepresent the model's "
                "actual reasoning, so treating CoT as a hallucination-reduction "
                "mechanism is unsound."
            ),
            evidence=(
                "Turpin et al. (2023) show that biasing features (e.g. answer "
                "reordering) change final answers while CoT explanations remain "
                "fluent, indicating CoT text is post-hoc rather than causal."
            ),
            citations=[cot_faithful_paper],
            confidence=0.45,
            tier=ConfidenceTier.CONTESTED,
            caveats=["Evaluated on biased-feature suite, not general inference"],
            claim_id="CLM-005",
        ),
        _claim(
            text=(
                "No peer-reviewed head-to-head benchmark yet compares "
                "orchestrator-subagent, debate, and swarm patterns on a "
                "consistent research-quality rubric, leaving architectural "
                "choice largely under-evidenced."
            ),
            evidence=(
                "Public literature surfaces pattern-specific reports but no "
                "cross-pattern controlled comparison; the gap is acknowledged "
                "in Anthropic's engineering write-up."
            ),
            citations=[dead_url],
            confidence=0.30,
            tier=ConfidenceTier.INSUFFICIENT,
            caveats=["Absence evidence; survey may be incomplete"],
            claim_id="CLM-006",
        ),
    ]

    return StructuredFinding(
        task_id=TASK_ID,
        agent_id=AGENT_ID,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        agent_type="qualitative",
        claims=claims,
        status=FindingStatus.COMPLETE,
        gaps=[
            "Controlled comparison of orchestrator vs. debate vs. swarm patterns",
            "Long-horizon reliability benchmarks on multi-day research workflows",
        ],
        absence_report=[
            "No peer-reviewed empirical comparison of orchestrator vs. debate architectures",
            "No public dataset measuring subagent coordination quality",
            "No production deployment report disclosing agent-tool budgets",
        ],
        sources_consulted=14,
        tokens_consumed=8200,
    )


def build_task() -> ResearchTask:
    return ResearchTask(
        id=TASK_ID,
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        category=TaskCategory.TECHNOLOGY_ASSESSMENT,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=4,
        description=(
            "Survey multi-agent AI research systems, characterize their "
            "architectural patterns, and assess maturity for production "
            "analytical work."
        ),
        required_sources=["academic", "engineering_blog", "code_repository"],
        acceptance_criteria=[
            "At least four distinct systems analyzed with named architectures",
            "Explicit statement of strongest counter-evidence per claim",
            "Absence report enumerating gaps in the literature",
        ],
        deliverable_destination="Section 2: Multi-Agent Architecture Landscape",
        priority=1,
        importance=TaskImportance.PRIMARY,
        anti_confirmatory_framing=(
            "Evaluate whether existing multi-agent systems are mature enough "
            "for boutique-consulting workflows, surfacing evidence both for "
            "and against production readiness."
        ),
        assigned_tools=["web_search", "fetch_url", "arxiv_search"],
        assigned_model=ModelTier.STANDARD,
        end_product=(
            "Narrative comparison of 4-6 named systems with architecture "
            "diagram callouts, maturity verdict, and an absence report."
        ),
        dependencies=[],
    )


def build_spec(task: ResearchTask) -> EngagementSpec:
    research_spec = ResearchSpec(
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        title="Multi-Agent Research Systems: Architectural Landscape",
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context=(
            "Keystone's internal tools team must choose a multi-agent "
            "architecture for the production research pipeline within 30 days."
        ),
        surprising_finding=(
            "Evidence that orchestrator-subagent hierarchies underperform flat "
            "debate patterns on open-ended research, or that no pattern is yet "
            "production-ready without heavy scaffolding."
        ),
        questions=[
            ResearchQuestion(
                question=(
                    "Which multi-agent research architectures are mature enough "
                    "to support boutique-grade analytical output today?"
                ),
                is_primary=True,
            ),
            ResearchQuestion(
                question=(
                    "Where do existing systems fail on dimensions Keystone "
                    "cares about (citation fidelity, governance, reproducibility)?"
                ),
                is_primary=False,
            ),
        ],
        output_format="markdown",
        non_goals=["Building a new multi-agent framework from scratch"],
        engagement_type=EngagementType.EXPLORATORY,
        day_1_hypothesis=(
            "Orchestrator-subagent hierarchies are the leading pattern but "
            "none are yet production-grade without bespoke evaluation harnesses."
        ),
        recommended_pipeline_profile=PipelineProfile.STANDARD,
        effective_pipeline_profile=PipelineProfile.STANDARD,
        effective_evaluation_profile=EvaluationProfileName.DEFAULT,
    )

    decomposition = TaskDecomposition(
        project="Multi-Agent Landscape",
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        research_md_path="engagements/eng_downstream_smoke/RESEARCH.md",
        specification_version=1,
        decomposition_rationale=(
            "Single exploratory task covering the full architectural landscape."
        ),
        tasks=[task],
    )

    report = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )

    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=report,
    )


def build_synthetic_outline(
    spec: EngagementSpec,
    finding: StructuredFinding,
    manifest: CitationManifest,
) -> StructuredOutline:
    """Minimal outline that routes the finding's claims through the renderer.

    Uses the canonicalized citation IDs from ``manifest`` so inline ``[N]``
    references resolve. Sections are grouped by confidence tier to exercise
    both the executive-summary and uncertainty render paths.
    """
    citation_ids_by_claim: dict[str, list[str]] = {}
    for claim in finding.claims:
        if claim.claim_id:
            citation_ids_by_claim[claim.claim_id] = list(claim.citation_ids) or [
                c.citation_id for c in claim.citations
            ]

    def _items_for_tier(tier: ConfidenceTier) -> list[OutlineItem]:
        items: list[OutlineItem] = []
        for claim in finding.claims:
            if claim.confidence_tier != tier:
                continue
            items.append(
                OutlineItem(
                    item_id=claim.claim_id,
                    item_type=OutlineItemType.CLAIM,
                    text=claim.text,
                    task_ids=[finding.task_id],
                    citation_ids=citation_ids_by_claim.get(claim.claim_id, []),
                    confidence=claim.confidence,
                    confidence_tier=claim.confidence_tier,
                    evidence=claim.evidence,
                    caveats=claim.caveats,
                )
            )
        return items

    exec_items = _items_for_tier(ConfidenceTier.HIGH)
    moderate_items = _items_for_tier(ConfidenceTier.MODERATE)
    weak_items = _items_for_tier(ConfidenceTier.WEAK)
    contested_items = _items_for_tier(ConfidenceTier.CONTESTED)
    insufficient_items = _items_for_tier(ConfidenceTier.INSUFFICIENT)

    all_citation_ids = sorted({c.citation_id for c in manifest.citations})

    def _section(
        section_id: str,
        section_type: OutlineSectionType,
        title: str,
        items: list[OutlineItem],
        framework: AnalyticalFramework | None = None,
    ) -> StructuredSection:
        return StructuredSection(
            section_id=section_id,
            section_type=section_type,
            title=title,
            framework=framework,
            task_ids=[finding.task_id],
            claim_ids=[item.item_id for item in items if item.item_id],
            citation_ids=sorted({cid for item in items for cid in item.citation_ids}),
            items=items,
        )

    sections: list[StructuredSection] = [
        _section(
            "sec_exec",
            OutlineSectionType.EXECUTIVE_SUMMARY,
            "Executive Summary",
            exec_items,
        ),
        _section(
            "sec_framework",
            OutlineSectionType.FRAMEWORK_ANALYSIS,
            "Analytical Framework",
            [
                OutlineItem(
                    item_id="note_framework",
                    item_type=OutlineItemType.FRAMEWORK_NOTE,
                    text=(
                        "Landscape mapping framework: enumerate distinct "
                        "architectures, score on production-readiness axes, "
                        "surface cross-system gaps."
                    ),
                    task_ids=[finding.task_id],
                    citation_ids=[],
                )
            ],
            framework=AnalyticalFramework.LANDSCAPE_MAPPING,
        ),
        _section(
            "sec_branch",
            OutlineSectionType.BRANCH,
            "Key Findings: Multi-Agent Architectures",
            moderate_items,
            framework=AnalyticalFramework.LANDSCAPE_MAPPING,
        ),
        _section(
            "sec_weak",
            OutlineSectionType.WEAK,
            "Weak-Confidence Findings",
            weak_items,
        ),
        _section(
            "sec_contested",
            OutlineSectionType.CONTESTED,
            "Contested Claims",
            contested_items,
        ),
        _section(
            "sec_gaps",
            OutlineSectionType.GAPS,
            "Evidence Gaps",
            [
                OutlineItem(
                    item_id=f"gap_{i}",
                    item_type=OutlineItemType.GAP,
                    text=gap,
                    task_ids=[finding.task_id],
                )
                for i, gap in enumerate(finding.gaps, 1)
            ],
        ),
        _section(
            "sec_insufficient",
            OutlineSectionType.INSUFFICIENT,
            "Insufficient Evidence",
            insufficient_items,
        ),
        _section(
            "sec_absence",
            OutlineSectionType.ABSENCE,
            "Absence Report",
            [
                OutlineItem(
                    item_id=f"absence_{i}",
                    item_type=OutlineItemType.ABSENCE,
                    text=topic,
                    task_ids=[finding.task_id],
                )
                for i, topic in enumerate(finding.absence_report, 1)
            ],
        ),
    ]

    return StructuredOutline(
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        engagement_type=spec.research_spec.engagement_type.value,
        frameworks=[
            FrameworkHint(
                framework=AnalyticalFramework.LANDSCAPE_MAPPING,
                rationale="Exploratory engagement mapping a solution space.",
                mandatory=True,
            )
        ],
        sections=sections,
        rendered_task_ids=[finding.task_id],
        uncovered_branch_ids=[],
    )


def build_section_output_text(finding: StructuredFinding) -> str:
    """Plaintext section body fed to the Evaluator.

    Mirrors what L2 ContentStructurer would render so Layer 1/3 have
    substantive content to score.
    """
    lines: list[str] = []
    lines.append(
        "# Section 2: Multi-Agent Architecture Landscape\n\n"
        "We evaluated whether today's multi-agent research architectures are "
        "mature enough to underpin a boutique-consulting analytical pipeline. "
        "The evidence picture is mixed: reference patterns exist but "
        "production readiness remains under-evidenced.\n"
    )
    for claim in finding.claims:
        lines.append(f"## {claim.text}\n")
        lines.append(f"{claim.evidence}\n")
        if claim.caveats:
            lines.append("Caveats:\n")
            for cav in claim.caveats:
                lines.append(f"- {cav}\n")
        cite_ids = list(claim.citation_ids) or [c.citation_id for c in claim.citations]
        if cite_ids:
            lines.append("Citations: " + ", ".join(f"[{cid}]" for cid in cite_ids) + "\n")
        lines.append("\n")
    lines.append(
        "## Absence Report\n\n"
        "Notable gaps persist: no controlled cross-pattern benchmark, no "
        "public dataset measuring coordination quality, and no production "
        "deployment disclosure of agent-tool budgets.\n"
    )
    return "".join(lines)


def build_sprint_contract(task: ResearchTask) -> SprintContract:
    return SprintContract(
        section_id=f"section_{task.id}",
        engagement_id=task.engagement_id,
        client_id=task.client_id,
        task_id=task.id,
        section_title=task.deliverable_destination,
        acceptance_criteria=[
            "Four or more distinct multi-agent systems named and summarized",
            "Counter-evidence explicitly stated for each maturity claim",
            "Absence report enumerating at least two literature gaps",
        ],
        dimension_emphasis={},
        mandatory_elements=[
            "Named-system inventory",
            "Architecture taxonomy",
            "Maturity verdict with justification",
        ],
        anti_patterns=[
            "Hype-laden adjectives unsupported by evidence",
            "Citations that do not connect to a specific claim",
        ],
    )


# ---------------------------------------------------------------------------
# Layer runners (each is isolated and handles its own errors)
# ---------------------------------------------------------------------------


def _banner(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72, flush=True)


async def run_citation_processor(findings: list[StructuredFinding]) -> tuple[object, object]:
    _banner("Layer: CitationProcessor (deterministic, real HTTP URL checks)")
    processor = CitationProcessor()
    events: list[dict] = []
    try:
        t0 = time.monotonic()
        async for event in processor.process(findings, ENGAGEMENT_ID, CLIENT_ID):
            payload = event.model_dump(mode="json")
            events.append(payload)
            print(f"  [event] {event.__class__.__name__}: {payload}")
        result = await processor.get_result()
        elapsed = time.monotonic() - t0

        manifest = result.manifest
        print(
            f"\n  CitationProcessor OK in {elapsed:.1f}s: "
            f"{len(manifest.citations)} citations, "
            f"{len(manifest.dead_urls)} dead URLs, "
            f"{len(manifest.corroboration_pairs)} corroboration pairs, "
            f"{len(manifest.aliases)} aliases."
        )
        for cit in manifest.citations:
            live_marker = (
                "LIVE" if cit.url_live else ("DEAD" if cit.url_live is False else "UNCHECKED")
            )
            print(f"    - [{live_marker}] {cit.citation_id}  {cit.url}")
        return result.manifest, result.canonicalized_findings, events
    except Exception as exc:  # noqa: BLE001
        print(f"\n  CitationProcessor FAILED: {exc}")
        traceback.print_exc()
        return None, None, events


async def run_deliberation(
    manifest,
    canonicalized_findings,
    analyst_llm,
    judge_llm,
) -> tuple[object, list[dict]]:
    _banner("Layer: L1.5 Deliberation (4 analysts + aggregator, real LLM calls)")
    events: list[dict] = []
    if manifest is None or canonicalized_findings is None:
        print("  Skipped: upstream CitationProcessor did not produce a manifest.")
        return None, events

    delib = Deliberation(
        analyst_llm=analyst_llm,
        judge_llm=judge_llm,
        analyst_types=[
            DeliberationAnalystType.ACH,
            DeliberationAnalystType.QUANTITATIVE,
            DeliberationAnalystType.ADVERSARIAL,
            DeliberationAnalystType.HISTORICAL_ANALOGY,
        ],
    )
    try:
        t0 = time.monotonic()
        async for event in delib.deliberate(
            manifest, canonicalized_findings, ENGAGEMENT_ID, CLIENT_ID
        ):
            payload = event.model_dump(mode="json")
            events.append(payload)
            print(f"  [event] {event.__class__.__name__}: {payload}")
        confidence_map = await delib.get_confidence_map()
        elapsed = time.monotonic() - t0

        print(f"\n  Deliberation OK in {elapsed:.1f}s:")
        print(f"    total_claims          = {confidence_map.total_claims}")
        print(f"    tiers_populated       = {confidence_map.tiers_populated}")
        print(f"    high (>80%)           = {len(confidence_map.high_confidence_above_80pct)}")
        print(f"    moderate (60-80%)     = {len(confidence_map.moderate_confidence_60_80pct)}")
        print(f"    weak (50-60%)         = {len(confidence_map.weak_confidence_50_60pct)}")
        print(f"    contested (<50%)      = {len(confidence_map.contested_below_50pct)}")
        print(f"    insufficient_evidence = {len(confidence_map.insufficient_evidence)}")
        print(f"    gaps_identified       = {len(confidence_map.gaps_identified)}")
        return confidence_map, events
    except Exception as exc:  # noqa: BLE001
        print(f"\n  Deliberation FAILED: {exc}")
        traceback.print_exc()
        return None, events


async def run_evaluator(
    llm,
    manifest,
    task,
    spec,
    output_text,
    contract,
) -> tuple[object, list[dict]]:
    _banner("Layer: L4 Evaluator (3-layer rubric, real LLM calls)")
    events: list[dict] = []
    if manifest is None:
        print("  Skipped: no manifest from upstream layers.")
        return None, events

    evaluator = Evaluator(
        llm=llm,
        intensity=EvaluationIntensity.STANDARD,
    )
    try:
        t0 = time.monotonic()
        async for event in evaluator.evaluate(
            output_text,
            contract,
            task,
            manifest,
            spec,
            process_context=None,  # Skip Layer 4 for this smoke test.
        ):
            payload = event.model_dump(mode="json")
            events.append(payload)
            print(f"  [event] {event.__class__.__name__}: {payload}")
        result = await evaluator.get_result()
        elapsed = time.monotonic() - t0

        print(f"\n  Evaluator OK in {elapsed:.1f}s:")
        print(f"    passed         = {result.passed}")
        print(f"    overall_score  = {result.overall_score:.1f}/100")
        print(f"    layer2_passed  = {result.layer2_results.gate_passed}")
        if result.layer3_results is not None:
            print("    per-dimension scores:")
            for ds in result.layer3_results.dimension_scores:
                print(
                    f"      - {ds.dimension.value:<24} {ds.score:5.1f}  "
                    f"(feedback: {ds.feedback[:80] + '...' if len(ds.feedback) > 80 else ds.feedback})"
                )
            print(f"    gestalt_adjustment = {result.layer3_results.gestalt_adjustment:+.1f}")
        print(f"    feedback: {result.feedback[:200]}...")
        return result, events
    except Exception as exc:  # noqa: BLE001
        print(f"\n  Evaluator FAILED: {exc}")
        traceback.print_exc()
        return None, events


def run_renderer(
    spec,
    findings,
    confidence_map,
    evaluation_results,
    manifest,
    outline,
) -> str | None:
    _banner("Layer: MarkdownRenderer (pure Python)")
    if manifest is None:
        print("  Skipped: no manifest.")
        return None
    try:
        renderer = MarkdownRenderer()
        md = renderer.render(
            spec,
            findings,
            confidence_map,
            evaluation_results,
            manifest,
            outline,
        )
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        RENDER_PATH.write_text(md)
        print(f"  Renderer OK: wrote {len(md)} chars to {RENDER_PATH}")
        preview = "\n".join(md.splitlines()[:30])
        print("  --- first 30 lines ---")
        print(preview)
        print("  --- end preview ---")
        return md
    except Exception as exc:  # noqa: BLE001
        print(f"\n  Renderer FAILED: {exc}")
        traceback.print_exc()
        return None


# ---------------------------------------------------------------------------
# Fallback: synthesize a minimal ConfidenceMap from the finding so the
# renderer has something to show if Deliberation fails.
# ---------------------------------------------------------------------------


def synthesize_confidence_map_fallback(finding: StructuredFinding):
    from keystone.models.confidence import (
        ConfidenceMap,
        ContestedClaim,
        HighConfidenceClaim,
        InsufficientEvidenceClaim,
        ModerateConfidenceClaim,
        WeakConfidenceClaim,
    )

    high: list[HighConfidenceClaim] = []
    moderate: list[ModerateConfidenceClaim] = []
    weak: list[WeakConfidenceClaim] = []
    contested: list[ContestedClaim] = []
    insufficient: list[InsufficientEvidenceClaim] = []

    for claim in finding.claims:
        cites = list(claim.citation_ids) or [c.citation_id for c in claim.citations]
        if claim.confidence_tier == ConfidenceTier.HIGH:
            high.append(
                HighConfidenceClaim(
                    claim=claim.text,
                    methodological_agreement="fallback (no live deliberation)",
                    sources=len(cites),
                    corroboration_count=1,
                    robustness="single-agent fallback",
                    curmudgeon_challenge="Not deliberated; treat as unvalidated.",
                    aggregated_claim_id=claim.claim_id,
                    task_ids=[finding.task_id],
                )
            )
        elif claim.confidence_tier == ConfidenceTier.MODERATE:
            moderate.append(
                ModerateConfidenceClaim(
                    claim=claim.text,
                    methodological_agreement="fallback (no live deliberation)",
                    dissent="No deliberation run; dissent unmeasured.",
                    sources=len(cites),
                    sensitivity="Not assessed in smoke-test fallback.",
                    aggregated_claim_id=claim.claim_id,
                    task_ids=[finding.task_id],
                )
            )
        elif claim.confidence_tier == ConfidenceTier.WEAK:
            weak.append(
                WeakConfidenceClaim(
                    claim=claim.text,
                    methodological_agreement="fallback (no live deliberation)",
                    key_issue="Deliberation skipped in smoke test.",
                    sources=len(cites),
                    recommendation="Run full L1.5 deliberation before publishing.",
                    aggregated_claim_id=claim.claim_id,
                    task_ids=[finding.task_id],
                )
            )
        elif claim.confidence_tier == ConfidenceTier.CONTESTED:
            contested.append(
                ContestedClaim(
                    claim=claim.text,
                    methodological_agreement="fallback (no live deliberation)",
                    key_disagreement="Deliberation skipped in smoke test.",
                    sources=len(cites),
                    steelmanned_opposing_view="Not constructed in fallback.",
                    aggregated_claim_id=claim.claim_id,
                    task_ids=[finding.task_id],
                )
            )
        else:
            insufficient.append(
                InsufficientEvidenceClaim(
                    claim=claim.text,
                    reason="Smoke-test fallback; deliberation skipped.",
                    priority="medium",
                    aggregated_claim_id=claim.claim_id,
                    task_ids=[finding.task_id],
                )
            )

    return ConfidenceMap(
        engagement_id=ENGAGEMENT_ID,
        client_id=CLIENT_ID,
        high_confidence_above_80pct=high,
        moderate_confidence_60_80pct=moderate,
        weak_confidence_50_60pct=weak,
        contested_below_50pct=contested,
        insufficient_evidence=insufficient,
        gaps_identified=[],
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is set; claude -p would bill to the API instead "
            "of the Max subscription. Unset it before running this smoke test."
        )

    print(f"[downstream smoke test] repo_root={REPO_ROOT}")
    print(f"[downstream smoke test] writing events to {EVENTS_PATH}")
    print(f"[downstream smoke test] writing render to {RENDER_PATH}")

    task = build_task()
    spec = build_spec(task)
    finding = build_finding()

    print(
        f"\nSynthetic fixture: task={task.id}, agent={finding.agent_id}, "
        f"claims={len(finding.claims)}, citations="
        f"{sum(len(c.citations) for c in finding.claims)}"
    )

    # LLM factory for downstream layers that need real LLM calls.
    config = AppConfig()
    factory = create_llm_factory(config)
    analyst_llm = factory.for_layer("l1_5_analysts")
    judge_llm = factory.for_layer("l1_5_aggregator")
    evaluator_llm = factory.for_layer("l4_evaluator")

    # --- 1. CitationProcessor ---
    manifest, canonicalized_findings, cit_events = await run_citation_processor([finding])

    # --- 2. L1.5 Deliberation ---
    confidence_map, delib_events = await run_deliberation(
        manifest,
        canonicalized_findings,
        analyst_llm,
        judge_llm,
    )

    if confidence_map is None:
        print("\n[downstream smoke test] Synthesizing fallback ConfidenceMap for renderer.")
        confidence_map = synthesize_confidence_map_fallback(
            canonicalized_findings[0] if canonicalized_findings else finding
        )

    # --- 3. L4 Evaluator ---
    output_text = build_section_output_text(finding)
    contract = build_sprint_contract(task)
    eval_result, eval_events = await run_evaluator(
        evaluator_llm,
        manifest,
        task,
        spec,
        output_text,
        contract,
    )

    # --- 4. Renderer ---
    outline = None
    if manifest is not None:
        outline = build_synthetic_outline(
            spec,
            canonicalized_findings[0] if canonicalized_findings else finding,
            manifest,
        )
    evaluation_results = [eval_result] if eval_result is not None else []
    md = run_renderer(
        spec,
        canonicalized_findings if canonicalized_findings else [finding],
        confidence_map,
        evaluation_results,
        manifest,
        outline,
    )

    # --- Persist event log ---
    log_payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "citation_processor": cit_events,
        "deliberation": delib_events,
        "evaluator": eval_events,
        "render_bytes": len(md) if md else 0,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_PATH.write_text(json.dumps(log_payload, indent=2, default=str))

    _banner("Summary")
    print(
        "  CitationProcessor: "
        + ("OK" if manifest is not None else "FAILED")
        + f" ({len(cit_events)} events)"
    )
    print(
        "  Deliberation:      "
        + ("OK" if confidence_map and confidence_map.total_claims else "FALLBACK/FAILED")
        + f" ({len(delib_events)} events)"
    )
    print(
        "  Evaluator:         "
        + ("OK" if eval_result is not None else "FAILED")
        + f" ({len(eval_events)} events)"
    )
    print(
        "  Renderer:          " + ("OK" if md else "FAILED") + (f" -> {RENDER_PATH}" if md else "")
    )


if __name__ == "__main__":
    asyncio.run(main())
