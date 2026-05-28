"""Repeatable local first-slice flow that avoids the old full pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from keystone.artifacts.models import (
    ApprovalStatus,
    ArtifactStatus,
    DeliverableArtifact,
    DeliverableType,
    EvaluationArtifact,
    EvidenceBundleArtifact,
    IssueTreePackageArtifact,
    ProviderJobArtifact,
    ProviderJobStatus,
    ProviderKind,
    ProviderSurface,
    SourceBundleArtifact,
    SpecificationArtifact,
    SynthesisArtifact,
    make_artifact_id,
)
from keystone.ingestion.manual_report import ManualUploadAdapter, ReportIngestionResult
from keystone.models.research import EngagementType, ResearchQuestion, ResearchSpec
from keystone.specification.issue_tree_package import (
    ApprovalStatus as PackageApprovalStatus,
)
from keystone.specification.issue_tree_package import (
    IssueTreePackage,
)
from keystone.specification.lens_selector import LensSelector
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.template_registry import TemplateRegistry

if TYPE_CHECKING:
    from pathlib import Path

    from keystone.artifacts.store import LocalArtifactStore


@dataclass(frozen=True)
class CompletedProviderReport:
    """Completed provider export ready for ingestion by the slice runner."""

    provider: ProviderKind
    prompt: str
    report_path: str | Path
    branch_id: str
    job_url: str | None = None
    export_paths: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
    provider_job_id: str | None = None
    surface: ProviderSurface = ProviderSurface.WEB


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


def run_artifact_centered_first_slice(
    *,
    store: LocalArtifactStore,
    run_id: str,
    root_request: str,
    issue_tree_package: IssueTreePackage,
    completed_reports: list[CompletedProviderReport],
    engagement_type: EngagementType = EngagementType.EVALUATIVE,
    domain: str | None = None,
    output_target: str | None = "markdown brief",
) -> dict[str, str]:
    """Run the first artifact-centered autonomous research slice.

    Provider automation is expected to pass only completed exports into this
    function. Incomplete provider pages remain in the provider ledger and do
    not enter ingestion.
    """
    if issue_tree_package.approval.status != PackageApprovalStatus.APPROVED:
        raise ValueError("IssueTreePackage must be approved before research dispatch")
    if not completed_reports:
        raise ValueError("At least one completed provider report is required")

    store.create_ledger(
        run_id=run_id,
        root_request=root_request,
        status=ArtifactStatus.READY,
        notes=["Artifact-centered first slice from approved IssueTreePackage."],
        metadata={"domain": domain or "", "output_target": output_target or ""},
    )

    spec_artifact = SpecificationArtifact(
        artifact_id=make_artifact_id("spec", run_id, root_request),
        run_id=run_id,
        status=ArtifactStatus.READY,
        question=root_request,
        domain=domain,
        output_target=output_target,
        decision_context=issue_tree_package.problem_frame.decision_or_question,
        day_1_hypothesis=issue_tree_package.problem_frame.reconstructed_problem,
        approval_status=ApprovalStatus.APPROVED,
        metadata={
            "problem_frame": issue_tree_package.problem_frame.model_dump(mode="json"),
            "selected_axis": issue_tree_package.selected_axis.model_dump(mode="json"),
        },
    )
    store.write_artifact(spec_artifact)

    package_artifact = IssueTreePackageArtifact(
        artifact_id=make_artifact_id("issue-tree-package", run_id, issue_tree_package.package_id),
        run_id=run_id,
        status=ArtifactStatus.READY,
        parent_artifact_ids=[spec_artifact.artifact_id],
        package=issue_tree_package.model_dump(mode="json"),
        approval_status=ApprovalStatus.APPROVED,
    )
    store.write_artifact(package_artifact)

    task_decomposition = _tasks_from_package(issue_tree_package, engagement_type, root_request)
    task_path = store.write_text_file(
        run_id,
        "research-tasks.json",
        task_decomposition.model_dump_json(indent=2) + "\n",
    )

    ingestions: list[ReportIngestionResult] = []
    provider_job_ids: list[str] = []
    for completed in completed_reports:
        provider_artifact = _write_completed_provider_job(
            store=store,
            run_id=run_id,
            package_artifact_id=package_artifact.artifact_id,
            completed=completed,
        )
        provider_job_ids.append(provider_artifact.artifact_id)
        ingestion = ManualUploadAdapter(store).ingest_file(
            completed.report_path,
            run_id=run_id,
            provider_job_id=provider_artifact.artifact_id,
            issue_node_ids=[completed.branch_id],
        )
        ingestions.append(ingestion)

    combined_source_bundle, combined_evidence_bundle = _combine_ingestions(
        run_id=run_id,
        ingestions=ingestions,
    )
    store.write_artifact(combined_source_bundle)
    store.write_artifact(combined_evidence_bundle)

    synthesis = _build_synthesis_from_evidence(
        store=store,
        evidence_bundle=combined_evidence_bundle,
        parent_artifact_ids=[
            package_artifact.artifact_id,
            combined_evidence_bundle.artifact_id,
            *provider_job_ids,
        ],
        title=issue_tree_package.problem_frame.decision_or_question,
    )
    evaluation = _evaluate_evidence_bundle(combined_evidence_bundle, synthesis)
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
        title=f"Artifact-centered brief: {issue_tree_package.problem_frame.decision_or_question}",
        path=deliverable_path,
        input_artifact_ids=[synthesis.artifact_id],
        quality_gate_artifact_ids=[evaluation.artifact_id],
    )
    store.write_artifact(deliverable)

    return {
        "run_id": run_id,
        "specification_artifact_id": spec_artifact.artifact_id,
        "issue_tree_package_artifact_id": package_artifact.artifact_id,
        "task_decomposition_path": str(task_path),
        "provider_job_artifact_ids": ",".join(provider_job_ids),
        "combined_source_bundle_artifact_id": combined_source_bundle.artifact_id,
        "combined_evidence_bundle_artifact_id": combined_evidence_bundle.artifact_id,
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
        claims=cited_claims[:8],
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


def _tasks_from_package(
    issue_tree_package: IssueTreePackage,
    engagement_type: EngagementType,
    root_request: str,
):
    async def unused_llm(prompt: str) -> str:
        raise RuntimeError(f"LLM task generation is bypassed for package leaves: {prompt}")

    spec = ResearchSpec(
        engagement_id=issue_tree_package.package_id,
        client_id="artifact_slice",
        title=issue_tree_package.problem_frame.decision_or_question,
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context=issue_tree_package.problem_frame.decision_or_question,
        surprising_finding=(
            "Evidence disconfirms the approved issue-tree branch hypothesis or "
            "changes the recommended action."
        ),
        questions=[ResearchQuestion(question=root_request, is_primary=True)],
        output_format="markdown",
        engagement_type=engagement_type,
        day_1_hypothesis=issue_tree_package.problem_frame.reconstructed_problem,
    )
    return TaskGenerator(unused_llm, TemplateRegistry()).generate_from_issue_tree_package(
        issue_tree_package,
        engagement_type,
        spec,
    )


def _write_completed_provider_job(
    *,
    store: LocalArtifactStore,
    run_id: str,
    package_artifact_id: str,
    completed: CompletedProviderReport,
) -> ProviderJobArtifact:
    artifact_id = completed.provider_job_id or make_artifact_id(
        "provider-job",
        run_id,
        completed.provider.value,
        completed.branch_id,
        completed.prompt,
    )
    export_paths = list(completed.export_paths)
    report_path = str(completed.report_path)
    if report_path not in export_paths:
        export_paths.append(report_path)
    artifact = ProviderJobArtifact(
        artifact_id=artifact_id,
        run_id=run_id,
        status=ArtifactStatus.READY,
        parent_artifact_ids=[package_artifact_id],
        provider=completed.provider,
        surface=completed.surface,
        provider_status=ProviderJobStatus.EXPORTED,
        prompt=completed.prompt,
        job_url=completed.job_url,
        completed_at=None,
        exported_at=None,
        export_paths=export_paths,
        metadata={
            "branch_id": completed.branch_id,
            "source_urls": json.dumps(completed.source_urls),
            "ingestion_state": "completed_export_supplied",
        },
    )
    store.write_artifact(artifact)
    return artifact


def _combine_ingestions(
    *,
    run_id: str,
    ingestions: list[ReportIngestionResult],
) -> tuple[SourceBundleArtifact, EvidenceBundleArtifact]:
    source_records: list[dict] = []
    claim_records: list[dict] = []
    source_id_maps: dict[str, dict[str, str]] = {}

    for ingestion in ingestions:
        report_map: dict[str, str] = {}
        for source in ingestion.source_bundle.source_records:
            new_source_id = f"SRC-{len(source_records) + 1:03d}"
            report_map[source["source_id"]] = new_source_id
            copied = dict(source)
            copied["source_id"] = new_source_id
            copied["original_source_id"] = source["source_id"]
            copied["report_artifact_id"] = ingestion.report.artifact_id
            source_records.append(copied)
        source_id_maps[ingestion.report.artifact_id] = report_map

    for ingestion in ingestions:
        source_map = source_id_maps[ingestion.report.artifact_id]
        for claim in ingestion.evidence_bundle.claim_records:
            copied = dict(claim)
            copied["claim_id"] = f"CLM-{len(claim_records) + 1:03d}"
            copied["original_claim_id"] = claim["claim_id"]
            copied["report_artifact_id"] = ingestion.report.artifact_id
            copied["citation_ids"] = [
                source_map[citation_id]
                for citation_id in claim.get("citation_ids", [])
                if citation_id in source_map
            ]
            claim_records.append(copied)

    report_ids = [ingestion.report.artifact_id for ingestion in ingestions]
    source_bundle = SourceBundleArtifact(
        artifact_id=make_artifact_id("sources-combined", run_id, *report_ids),
        run_id=run_id,
        status=ArtifactStatus.READY if source_records else ArtifactStatus.PARTIAL,
        report_artifact_ids=report_ids,
        source_records=source_records,
        extraction_method="artifact_centered_provider_ingestion",
    )
    evidence_bundle = EvidenceBundleArtifact(
        artifact_id=make_artifact_id("evidence-combined", run_id, *report_ids),
        run_id=run_id,
        status=ArtifactStatus.READY if claim_records else ArtifactStatus.PARTIAL,
        parent_artifact_ids=[source_bundle.artifact_id, *report_ids],
        report_artifact_ids=report_ids,
        source_bundle_artifact_id=source_bundle.artifact_id,
        claim_records=claim_records,
        source_records=source_records,
        quality_flags=_combined_quality_flags(source_records, claim_records),
    )
    return source_bundle, evidence_bundle


def _build_synthesis_from_evidence(
    *,
    store: LocalArtifactStore,
    evidence_bundle: EvidenceBundleArtifact,
    parent_artifact_ids: list[str],
    title: str,
) -> SynthesisArtifact:
    cited_claims = [claim for claim in evidence_bundle.claim_records if claim.get("citation_ids")]
    uncited_claims = [
        claim for claim in evidence_bundle.claim_records if not claim.get("citation_ids")
    ]
    lead_claim = cited_claims[0]["text"] if cited_claims else "No cited claims were extracted."
    gap_questions = [
        f"Can this claim be independently sourced: {claim['text'][:120]}?"
        for claim in uncited_claims[:5]
    ]
    evidence_map = {
        claim["claim_id"]: list(claim.get("citation_ids", [])) for claim in cited_claims
    }
    by_report: dict[str, int] = {}
    for claim in evidence_bundle.claim_records:
        report_id = claim.get("report_artifact_id", "unknown_report")
        by_report[report_id] = by_report.get(report_id, 0) + 1
    branch_summaries = [
        {"report_artifact_id": report_id, "claim_count": claim_count}
        for report_id, claim_count in sorted(by_report.items())
    ]
    markdown = _render_brief(
        title=title,
        thesis=lead_claim,
        claims=cited_claims[:10],
        source_records=evidence_bundle.source_records,
        gap_questions=gap_questions,
    )
    synthesis_id = make_artifact_id("synthesis", evidence_bundle.artifact_id)
    markdown_path = store.write_text_file(
        evidence_bundle.run_id,
        f"deliverables/{synthesis_id}.md",
        markdown,
    )
    return SynthesisArtifact(
        artifact_id=synthesis_id,
        run_id=evidence_bundle.run_id,
        status=ArtifactStatus.READY if cited_claims else ArtifactStatus.PARTIAL,
        parent_artifact_ids=parent_artifact_ids,
        input_artifact_ids=[evidence_bundle.artifact_id],
        thesis=lead_claim,
        branch_summaries=branch_summaries,
        evidence_map=evidence_map,
        gap_questions=gap_questions,
        markdown_path=str(markdown_path),
    )


def _combined_quality_flags(source_records: list[dict], claim_records: list[dict]) -> list[str]:
    flags: list[str] = []
    if len(source_records) < 5:
        flags.append("fewer_than_5_sources")
    if len(claim_records) < 5:
        flags.append("fewer_than_5_claims")
    uncited = [claim for claim in claim_records if not claim.get("citation_ids")]
    if uncited:
        flags.append(f"{len(uncited)}_claims_missing_citations")
    return flags


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
    cited_claims = [claim for claim in claims if claim.get("citation_ids")]
    for claim in cited_claims:
        citations = ", ".join(claim.get("citation_ids", [])) or "missing citation"
        lines.append(f"- {claim['text']} ({citations})")
    if not cited_claims:
        lines.append("- No cited claims were extracted in this first-slice run.")
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
