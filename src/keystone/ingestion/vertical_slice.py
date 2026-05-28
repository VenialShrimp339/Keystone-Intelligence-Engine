"""Repeatable local first-slice flow that avoids the old full pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

from keystone.artifacts.models import (
    ApprovalStatus,
    ArtifactStatus,
    DeliverableArtifact,
    DeliverableType,
    EvaluationArtifact,
    SpecificationArtifact,
    SynthesisArtifact,
    make_artifact_id,
)
from keystone.ingestion.manual_report import ManualUploadAdapter, ReportIngestionResult
from keystone.specification.lens_selector import LensSelector

if TYPE_CHECKING:
    from pathlib import Path

    from keystone.artifacts.store import LocalArtifactStore


def run_manual_first_slice(
    *,
    store: LocalArtifactStore,
    run_id: str,
    root_request: str,
    report_path: str | Path,
    domain: str | None = None,
    output_target: str | None = "markdown brief",
) -> dict[str, str]:
    """Create a run ledger, ingest one report, synthesize a brief, and evaluate it."""
    store.create_ledger(
        run_id=run_id,
        root_request=root_request,
        status=ArtifactStatus.READY,
        notes=["First-slice local run. No full Keystone pipeline execution."],
    )

    lens_selection = LensSelector().select(
        question=root_request,
        domain=domain,
        output_target=output_target,
    )
    spec = SpecificationArtifact(
        artifact_id=make_artifact_id("spec", run_id, root_request),
        run_id=run_id,
        status=ArtifactStatus.PENDING_APPROVAL,
        question=root_request,
        domain=domain,
        output_target=output_target,
        selected_lenses=[lens.model_dump() for lens in lens_selection.lenses],
        clarifying_questions=lens_selection.clarifying_questions,
        approval_status=ApprovalStatus.REQUIRED
        if lens_selection.approval_required
        else ApprovalStatus.NOT_REQUIRED,
        metadata={"selection_rationale": lens_selection.rationale},
    )
    store.write_artifact(spec)

    ingestion = ManualUploadAdapter(store).ingest_file(
        report_path,
        run_id=run_id,
        issue_node_ids=[spec.artifact_id],
    )
    synthesis = _build_synthesis(store, ingestion, spec.artifact_id)
    evaluation = _evaluate_evidence_bundle(ingestion.evidence_bundle, synthesis)
    store.write_artifact(synthesis)
    store.write_artifact(evaluation)

    deliverable_path = synthesis.markdown_path
    if deliverable_path is None:
        raise RuntimeError("Synthesis did not produce a markdown path")

    deliverable = DeliverableArtifact(
        artifact_id=make_artifact_id("deliverable", run_id, deliverable_path),
        run_id=run_id,
        status=ArtifactStatus.READY if evaluation.passed else ArtifactStatus.PARTIAL,
        parent_artifact_ids=[synthesis.artifact_id, evaluation.artifact_id],
        deliverable_type=DeliverableType.MARKDOWN_BRIEF,
        title=f"First-slice brief: {ingestion.report.title}",
        path=deliverable_path,
        input_artifact_ids=[synthesis.artifact_id],
        quality_gate_artifact_ids=[evaluation.artifact_id],
    )
    store.write_artifact(deliverable)

    return {
        "run_id": run_id,
        "specification_artifact_id": spec.artifact_id,
        "report_artifact_id": ingestion.report.artifact_id,
        "source_bundle_artifact_id": ingestion.source_bundle.artifact_id,
        "evidence_bundle_artifact_id": ingestion.evidence_bundle.artifact_id,
        "synthesis_artifact_id": synthesis.artifact_id,
        "evaluation_artifact_id": evaluation.artifact_id,
        "deliverable_artifact_id": deliverable.artifact_id,
        "deliverable_path": deliverable.path,
    }


def _build_synthesis(
    store: LocalArtifactStore,
    ingestion: ReportIngestionResult,
    specification_artifact_id: str,
) -> SynthesisArtifact:
    cited_claims = [
        claim for claim in ingestion.evidence_bundle.claim_records if claim.get("citation_ids")
    ]
    uncited_claims = [
        claim for claim in ingestion.evidence_bundle.claim_records if not claim.get("citation_ids")
    ]
    lead_claim = cited_claims[0]["text"] if cited_claims else "No cited claims were extracted."
    gap_questions = [
        f"Can this claim be independently sourced: {claim['text'][:120]}?"
        for claim in uncited_claims[:5]
    ]
    evidence_map = {
        claim["claim_id"]: list(claim.get("citation_ids", [])) for claim in cited_claims
    }
    branch_summaries = [
        {
            "section_id": section["section_id"],
            "title": section["title"],
            "claim_count": sum(
                1
                for claim in ingestion.evidence_bundle.claim_records
                if claim.get("section_id") == section["section_id"]
            ),
        }
        for section in ingestion.report.section_records
    ]

    markdown = _render_brief(
        title=ingestion.report.title,
        thesis=lead_claim,
        claims=ingestion.evidence_bundle.claim_records[:8],
        source_records=ingestion.evidence_bundle.source_records,
        gap_questions=gap_questions,
    )
    synthesis_id = make_artifact_id("synthesis", ingestion.report.artifact_id)
    markdown_path = store.write_text_file(
        ingestion.report.run_id,
        f"deliverables/{synthesis_id}.md",
        markdown,
    )

    return SynthesisArtifact(
        artifact_id=synthesis_id,
        run_id=ingestion.report.run_id,
        status=ArtifactStatus.READY if cited_claims else ArtifactStatus.PARTIAL,
        parent_artifact_ids=[
            specification_artifact_id,
            ingestion.report.artifact_id,
            ingestion.evidence_bundle.artifact_id,
        ],
        input_artifact_ids=[ingestion.evidence_bundle.artifact_id],
        thesis=lead_claim,
        branch_summaries=branch_summaries,
        evidence_map=evidence_map,
        gap_questions=gap_questions,
        markdown_path=str(markdown_path),
    )


def _evaluate_evidence_bundle(
    evidence_bundle,
    synthesis: SynthesisArtifact,
) -> EvaluationArtifact:
    checks = [
        {
            "name": "claims_extracted",
            "passed": len(evidence_bundle.claim_records) >= 5,
            "observed": len(evidence_bundle.claim_records),
        },
        {
            "name": "sources_extracted",
            "passed": len(evidence_bundle.source_records) >= 5,
            "observed": len(evidence_bundle.source_records),
        },
        {
            "name": "citation_gaps_recorded",
            "passed": evidence_bundle.uncited_claim_count >= 1,
            "observed": evidence_bundle.uncited_claim_count,
        },
        {
            "name": "synthesis_has_traceable_evidence",
            "passed": bool(synthesis.evidence_map),
            "observed": len(synthesis.evidence_map),
        },
    ]
    issues = [check["name"] for check in checks if not check["passed"]]
    score = sum(1 for check in checks if check["passed"]) / len(checks)
    return EvaluationArtifact(
        artifact_id=make_artifact_id("evaluation", evidence_bundle.artifact_id),
        run_id=evidence_bundle.run_id,
        status=ArtifactStatus.READY if not issues else ArtifactStatus.PARTIAL,
        parent_artifact_ids=[evidence_bundle.artifact_id, synthesis.artifact_id],
        target_artifact_id=evidence_bundle.artifact_id,
        passed=not issues,
        score=score,
        checks=checks,
        issues=issues,
    )


def _render_brief(
    *,
    title: str,
    thesis: str,
    claims: list[dict],
    source_records: list[dict],
    gap_questions: list[str],
) -> str:
    lines = [
        f"# {title}",
        "",
        "## Working Thesis",
        thesis,
        "",
        "## Traceable Claims",
    ]
    for claim in claims:
        citations = ", ".join(claim.get("citation_ids", [])) or "missing citation"
        lines.append(f"- {claim['text']} ({citations})")
    lines.extend(["", "## Sources"])
    for source in source_records:
        lines.append(f"- {source['source_id']}: {source['url']}")
    lines.extend(["", "## Evidence Gaps"])
    if gap_questions:
        for question in gap_questions:
            lines.append(f"- {question}")
    else:
        lines.append("- No uncited claims were extracted in this first-slice run.")
    return "\n".join(lines) + "\n"
