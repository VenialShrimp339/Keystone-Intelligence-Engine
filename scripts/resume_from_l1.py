"""Resume pipeline from existing L1 findings: CitProc → L1.5 → L2 → L4 → Render.

Loads the EngagementSpec and StructuredFindings from a previous run's
output directory, skipping L0 and L1 entirely. Use this to:
  - Test downstream layers without re-running expensive research
  - Resume after a crash in deliberation/evaluation
  - Re-process findings with updated prompts or config

Run from the repo root:

    source .venv/bin/activate
    python scripts/resume_from_l1.py output/eng_74e67db162c7

Or specify an engagement directory:

    python scripts/resume_from_l1.py /path/to/output/eng_XXXX
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

from keystone.citation.processor import CitationProcessor
from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.llm_client import LayerAwareLLMFactory
from keystone.models.config import AppConfig
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ModelTier
from keystone.pipeline.markdown_renderer import MarkdownRenderer
from keystone.structuring.content_structuring import (
    ContentStructurer,
    filter_outline_by_passed_tasks,
)


def _finding_to_text(finding: StructuredFinding) -> str:
    """Convert a StructuredFinding to evaluator-readable text."""
    parts = [f"Task: {finding.task_id}", f"Agent: {finding.agent_id}"]
    for i, claim in enumerate(finding.claims, 1):
        parts.append(f"\nClaim {i}: {claim.text}")
        parts.append(f"  Evidence: {claim.evidence}")
        parts.append(f"  Confidence: {claim.confidence:.0%} ({claim.confidence_tier.value})")
        cite_ids = ", ".join(claim.citation_ids or [c.citation_id for c in claim.citations])
        if cite_ids:
            parts.append(f"  Citations: {cite_ids}")
        if claim.caveats:
            parts.append(f"  Caveats: {'; '.join(claim.caveats)}")
    if finding.gaps:
        parts.append(f"\nGaps: {'; '.join(finding.gaps)}")
    if finding.absence_report:
        parts.append(f"\nAbsence report: {'; '.join(finding.absence_report[:5])}")
    return "\n".join(parts)


def _load_spec(eng_dir: Path) -> EngagementSpec:
    tasks_path = eng_dir / "l0_tasks.json"
    if not tasks_path.exists():
        print(f"ERROR: {tasks_path} not found", file=sys.stderr)
        sys.exit(1)

    # The l0_tasks.json is a TaskDecomposition. We need the full
    # EngagementSpec. Check if spec.json was saved by the test script.
    spec_path = eng_dir / "spec.json"
    if spec_path.exists():
        return EngagementSpec.model_validate_json(spec_path.read_text())

    # Build a minimal spec from the artifacts we have
    classification = json.loads((eng_dir / "l0_classification.json").read_text())
    intent = json.loads((eng_dir / "l0_intent_clarification.json").read_text())
    tasks_data = json.loads(tasks_path.read_text())
    issue_tree = json.loads((eng_dir / "l0_issue_tree.json").read_text())

    from datetime import UTC, datetime
    from keystone.models.research import (
        EngagementType,
        PipelineProfile,
        ResearchQuestion,
        ResearchSpec,
        ValidationReport,
    )
    from keystone.models.tasks import TaskDecomposition

    engagement_id = tasks_data.get("engagement_id", eng_dir.name)
    client_id = tasks_data.get("client_id", "client_keystone_internal")

    research_spec = ResearchSpec(
        engagement_id=engagement_id,
        client_id=client_id,
        title=tasks_data.get("project", "Resumed engagement"),
        created_at=datetime.now(UTC),
        specification_version=tasks_data.get("specification_version", 1),
        decision_context=intent.get("decision_context", ""),
        surprising_finding=intent.get("surprising_finding", ""),
        questions=[
            ResearchQuestion(question=q["question"], is_primary=q.get("is_primary", False))
            for q in intent.get("questions", [{"question": "Resumed", "is_primary": True}])
        ],
        output_format="markdown",
        day_1_hypothesis=intent.get("day_1_hypothesis", ""),
        engagement_type=EngagementType(classification.get("engagement_type", "evaluative")),
        effective_pipeline_profile=PipelineProfile(
            classification.get("pipeline_profile", "standard")
        ),
        profile_source=classification.get("profile_source", "classifier"),
    )

    decomposition = TaskDecomposition.model_validate(tasks_data)

    return EngagementSpec(
        research_spec=research_spec,
        task_decomposition=decomposition,
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
        issue_tree=issue_tree,
    )


def _load_findings(eng_dir: Path) -> list[StructuredFinding]:
    findings_dir = eng_dir / "l1_findings"
    if not findings_dir.exists():
        print(f"ERROR: {findings_dir} not found", file=sys.stderr)
        sys.exit(1)

    findings = []
    for f in sorted(findings_dir.glob("*.json")):
        try:
            finding = StructuredFinding.model_validate_json(f.read_text())
            if finding.claims:
                findings.append(finding)
                print(f"  Loaded {f.name}: {len(finding.claims)} claims")
            else:
                print(f"  Skipped {f.name}: 0 claims")
        except Exception as exc:
            print(f"  Failed to load {f.name}: {exc}")

    return findings


def _event_summary(event) -> str:
    parts = [f"[{type(event).__name__}]"]
    for attr in (
        "engagement_id",
        "agent_id",
        "task_id",
        "claim_count",
        "total_claims",
        "tiers_populated",
        "convergent_findings",
        "genuine_disagreements",
        "blind_spots",
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
            "ERROR: ANTHROPIC_API_KEY is set. Run `unset ANTHROPIC_API_KEY` and retry.",
            file=sys.stderr,
        )
        return 2

    if len(sys.argv) < 2:
        # Default to the most recent engagement directory
        output_dir = REPO_ROOT / "output"
        eng_dirs = sorted(
            [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("eng_")],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if not eng_dirs:
            print("ERROR: No engagement directories found in output/", file=sys.stderr)
            return 1
        eng_dir = eng_dirs[0]
    else:
        eng_dir = Path(sys.argv[1])
        if not eng_dir.is_absolute():
            eng_dir = REPO_ROOT / eng_dir

    if not eng_dir.exists():
        print(f"ERROR: {eng_dir} does not exist", file=sys.stderr)
        return 1

    print("=" * 70)
    print("PIPELINE RESUME FROM L1 FINDINGS")
    print("=" * 70)
    print(f"Engagement dir: {eng_dir}")
    print()

    print("Loading spec...")
    spec = _load_spec(eng_dir)
    eid = spec.research_spec.engagement_id
    cid = spec.research_spec.client_id
    print(f"  Engagement: {eid}")
    print(f"  Type: {spec.research_spec.engagement_type.value}")
    print(f"  Tasks: {len(spec.task_decomposition.tasks)}")
    print()

    print("Loading findings...")
    findings = _load_findings(eng_dir)
    total_claims = sum(len(f.claims) for f in findings)
    print(f"  Loaded: {len(findings)} findings, {total_claims} total claims")
    print()

    if not findings:
        print("ERROR: No findings with claims found. Nothing to process.", file=sys.stderr)
        return 1

    config = AppConfig()
    factory = LayerAwareLLMFactory(config)

    print("=" * 70)
    print("Running downstream layers: CitProc → L1.5 → L2 → L4 → Render")
    print("=" * 70)
    print()

    start = time.monotonic()

    # --- CitationProcessor ---
    print("--- CitationProcessor ---")
    manifest = None
    processed_findings = findings
    try:
        citation_processor = CitationProcessor()
        async for event in citation_processor.process(findings, eid, cid):
            elapsed = time.monotonic() - start
            print(f"  [{elapsed:7.1f}s] {_event_summary(event)}")

        manifest = await citation_processor.get_manifest()
        processed_findings = citation_processor._canonicalized_findings or findings
        print(f"  Citations: {len(manifest.citations)}")
        print(f"  Live URLs: {sum(1 for c in manifest.citations if c.url_live)}")
        print(f"  Dead URLs: {len(manifest.dead_urls)}")
        print(f"  Elapsed: {time.monotonic() - start:.1f}s")

        manifest_path = eng_dir / "citation_manifest_resumed.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2))
        print(f"  Written: {manifest_path.name}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        traceback.print_exc()
    print()

    # --- Deliberation ---
    print("--- L1.5 Deliberation ---")
    delib_start = time.monotonic()
    try:
        analyst_llm = factory.for_layer("l15_deliberation")
        judge_llm = factory.for_layer("l4_evaluator")
        deliberation = Deliberation(
            analyst_llm=analyst_llm,
            judge_llm=judge_llm,
        )
        async for event in deliberation.deliberate(manifest, processed_findings, eid, cid):
            elapsed = time.monotonic() - start
            print(f"  [{elapsed:7.1f}s] {_event_summary(event)}")

        confidence_map = await deliberation.get_confidence_map()
        print(f"  Total claims: {confidence_map.total_claims}")
        print(f"  Tiers: {confidence_map.tiers_populated}")
        print(f"  Elapsed: {time.monotonic() - delib_start:.1f}s")

        cm_path = eng_dir / "l15_confidence_map_resumed.json"
        cm_path.write_text(confidence_map.model_dump_json(indent=2))
        print(f"  Written: {cm_path.name}")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        traceback.print_exc()
        confidence_map = None
    print()

    # --- Content Structuring (L2) ---
    print("--- L2 Content Structuring ---")
    l2_start = time.monotonic()
    outline = None
    try:
        structurer_llm = factory.for_layer("l2_structuring")
        structurer = ContentStructurer(llm=structurer_llm)
        tasks = spec.task_decomposition.tasks
        async for event in structurer.structure(
            confidence_map=confidence_map,
            findings=processed_findings,
            spec=spec,
            tasks=tasks,
            engagement_id=eid,
            client_id=cid,
        ):
            elapsed = time.monotonic() - start
            print(f"  [{elapsed:7.1f}s] {_event_summary(event)}")

        outline = await structurer.get_outline()
        print(f"  Sections: {len(outline.sections) if outline else 0}")
        print(f"  Elapsed: {time.monotonic() - l2_start:.1f}s")
    except Exception as exc:
        print(f"  FAILED: {exc}")
        traceback.print_exc()
    print()

    # --- Evaluator (L4) ---
    print("--- L4 Evaluator ---")
    eval_start = time.monotonic()
    evaluation_results = {}
    try:
        eval_llm = factory.for_layer("l4_evaluator")
        extraction_llm = factory.for_layer("l4_extraction")

        # Generate sprint contracts for each task
        contract_llm = factory.for_layer("sprint_contract")
        contract_gen = SprintContractGenerator(llm=contract_llm)

        renderer_for_eval = MarkdownRenderer()
        for finding in processed_findings:
            task = next(
                (t for t in spec.task_decomposition.tasks if t.id == finding.task_id),
                None,
            )
            if task is None:
                continue

            # Build sprint contract
            try:
                contract = await contract_gen.generate(task, spec)
            except Exception as exc:
                print(f"  {finding.task_id} contract generation failed: {exc}")
                from keystone.models.evaluation import SprintContract

                contract = SprintContract(
                    task_id=task.id,
                    acceptance_criteria=task.acceptance_criteria,
                    mandatory_elements=[],
                    anti_patterns=[],
                    dimension_emphasis={},
                )

            output_text = _finding_to_text(finding)
            try:
                evaluator = Evaluator(
                    llm=eval_llm,
                    extraction_llm=extraction_llm,
                )
                async for event in evaluator.evaluate(
                    output_text=output_text,
                    contract=contract,
                    task=task,
                    manifest=manifest,
                    spec=spec,
                ):
                    elapsed = time.monotonic() - start
                    print(f"  [{elapsed:7.1f}s] {_event_summary(event)}")
                eval_result = await evaluator.get_result()
                evaluation_results[finding.task_id] = eval_result
                score = eval_result.composite_score if eval_result else "N/A"
                passed = eval_result.passed if eval_result else "N/A"
                print(f"  {finding.task_id}: score={score}, passed={passed}")
            except Exception as exc:
                print(f"  {finding.task_id} FAILED: {exc}")

        print(f"  Elapsed: {time.monotonic() - eval_start:.1f}s")
    except Exception as exc:
        print(f"  EVALUATOR FAILED: {exc}")
        traceback.print_exc()
    print()

    # --- Renderer ---
    print("--- Markdown Render ---")
    try:
        renderer = MarkdownRenderer()
        if outline and evaluation_results:
            passed_tasks = {tid for tid, er in evaluation_results.items() if er.passed}
            filtered_outline = filter_outline_by_passed_tasks(outline, passed_tasks)
        else:
            filtered_outline = outline

        markdown = renderer.render(
            spec=spec,
            outline=filtered_outline,
            evaluation_results=evaluation_results if evaluation_results else None,
            confidence_map=confidence_map,
        )
        brief_path = eng_dir / "final_brief_resumed.md"
        brief_path.write_text(markdown)
        word_count = len(markdown.split())
        print(f"  Words: {word_count}")
        print(f"  Written: {brief_path.name}")
    except Exception as exc:
        print(f"  RENDER FAILED: {exc}")
        traceback.print_exc()
    print()

    # --- Summary ---
    total_elapsed = time.monotonic() - start
    print("=" * 70)
    print("RESUME COMPLETE")
    print("=" * 70)
    print(f"Total elapsed: {total_elapsed:.1f}s")
    print(f"Findings processed: {len(findings)}")
    print(f"Evaluations completed: {len(evaluation_results)}")
    if evaluation_results:
        passed = sum(1 for er in evaluation_results.values() if er.passed)
        scores = [er.composite_score for er in evaluation_results.values() if er.composite_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"Tasks passed: {passed}/{len(evaluation_results)}")
        print(f"Average score: {avg_score:.1f}/100")
    print(f"Output dir: {eng_dir}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
