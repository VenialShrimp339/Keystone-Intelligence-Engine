from __future__ import annotations

from pathlib import Path

from keystone.artifacts import LocalArtifactStore, ProviderKind
from keystone.ingestion.vertical_slice import (
    CompletedProviderReport,
    run_artifact_centered_first_slice,
    run_manual_first_slice,
)
from keystone.specification.issue_tree_package import (
    ApprovalStatus,
    CandidateAxis,
    ConfidenceTarget,
    IssueTreeApproval,
    IssueTreeLeafTask,
    IssueTreePackage,
    IssueTreePackageNode,
    IssueTreeProblemFrame,
    RequiredArtifactType,
    SelectedAxis,
)

FIXTURE = Path("tests/fixtures/ingestion/sample_public_deep_research_report.md")


def test_manual_first_slice_writes_traceable_artifacts(tmp_path):
    store = LocalArtifactStore(tmp_path)

    result = run_manual_first_slice(
        store=store,
        run_id="slice-run",
        root_request="Research U.S. auto body repair consolidation",
        report_path=FIXTURE,
        domain="business_strategy",
        output_target="markdown brief",
    )

    ledger = store.read_ledger("slice-run")
    assert result["report_artifact_id"] in ledger.artifact_ids
    assert result["evidence_bundle_artifact_id"] in ledger.artifact_ids
    assert result["deliverable_artifact_id"] in ledger.artifact_ids

    deliverable_path = Path(result["deliverable_path"])
    assert deliverable_path.exists()
    deliverable_text = deliverable_path.read_text(encoding="utf-8")
    assert "## Traceable Claims" in deliverable_text
    assert "SRC-001" in deliverable_text

    evaluation = store.read_artifact("slice-run", result["evaluation_artifact_id"])
    assert evaluation["passed"] is True


def test_artifact_centered_slice_dispatches_approved_package_leaves(tmp_path):
    store = LocalArtifactStore(tmp_path)
    report = tmp_path / "provider-report.md"
    report.write_text(
        """# Market Entry Branch Report

## Findings
- Reachable demand appears large enough for deeper diligence [SRC1].
- Customer concentration creates a disconfirming risk for market entry [SRC2].
- Margin sensitivity depends most on support cost and discounting [SRC3].
- Public comparables show a wide range of gross margins [SRC4].
- The branch should proceed only if demand and margin evidence both hold [SRC5].

[SRC1]: https://example.com/demand
[SRC2]: https://example.com/concentration
[SRC3]: https://example.com/support-cost
[SRC4]: https://example.com/comparables
[SRC5]: https://example.com/decision
""",
        encoding="utf-8",
    )

    result = run_artifact_centered_first_slice(
        store=store,
        run_id="artifact-slice",
        root_request="Should we enter this market?",
        issue_tree_package=_approved_package(),
        completed_reports=[
            CompletedProviderReport(
                provider=ProviderKind.CHATGPT,
                prompt="Research reachable demand.",
                report_path=report,
                branch_id="demand",
                job_url="https://chatgpt.test/job",
                export_paths=[str(report), str(tmp_path / "sources.docx")],
                source_urls=["https://example.com/demand"],
            )
        ],
        domain="business_strategy",
    )

    task_path = Path(result["task_decomposition_path"])
    assert task_path.exists()
    assert "issue_tree_branch_id" in task_path.read_text(encoding="utf-8")

    package_artifact = store.read_artifact(
        "artifact-slice",
        result["issue_tree_package_artifact_id"],
    )
    assert package_artifact["artifact_type"] == "issue_tree_package"

    deliverable = Path(result["deliverable_path"]).read_text(encoding="utf-8")
    assert "## Traceable Claims" in deliverable
    assert "SRC-001" in deliverable


def _approved_package() -> IssueTreePackage:
    frame = IssueTreeProblemFrame(
        original_prompt="Should we enter this market?",
        reconstructed_problem="Decide whether demand and margin evidence justify entry.",
        decision_maker="Investment committee",
        decision_or_question="Should the firm enter this market?",
        situation="The team has an entry concept.",
        complication="Demand and margins are uncertain.",
        r1_undesired_result="Commit to entry despite weak demand or poor margins.",
        r2_desired_result="Proceed only if demand and margin hurdles hold.",
        constraints=["Public-source first pass"],
    )
    root = IssueTreePackageNode(
        node_id="root",
        parent_id=None,
        tree_scope="both",
        depth=0,
        statement="Market entry decision",
        question_or_hypothesis="Can the opportunity clear demand and margin gates?",
        decomposition_axis="must_be_true",
    )
    demand = IssueTreePackageNode(
        node_id="demand",
        parent_id="root",
        tree_scope="both",
        depth=1,
        statement="Reachable demand is sufficient",
        question_or_hypothesis="Is reachable demand sufficient?",
        decomposition_axis="must_be_true",
        priority="high",
        decision_relevance="high",
    )
    return IssueTreePackage(
        package_id="pkg-artifact-slice",
        problem_frame=frame,
        candidate_axes=[
            CandidateAxis(
                axis_id="a1",
                label="Must-be-true gates",
                what_it_reveals="Entry blockers",
                what_it_hides="Implementation detail",
                risk="Can underweight optional upside",
                selected=True,
            )
        ],
        selected_axis=SelectedAxis(axis_id="a1", rationale="Demand and margin gates decide entry."),
        full_tree=[root, demand],
        pruned_tree=[root, demand],
        leaf_tasks=[
            IssueTreeLeafTask(
                leaf_id="leaf-demand",
                node_id="demand",
                research_question="How much reachable demand exists?",
                resolution_criteria=["Demand estimate is source-backed"],
                evidence_requirements=["Market size and reachable segment evidence"],
                expected_artifact="Demand memo",
                disconfirming_evidence_to_seek=["Demand is concentrated in unreachable accounts"],
                likely_sources_or_methods=["Public sources"],
                task_seed_prompt="Research reachable demand.",
                required_artifact_type=RequiredArtifactType.MEMO,
                acceptance_criteria=["Cited demand estimate"],
                confidence_target=ConfidenceTarget.HIGH,
                downstream_agent_routing_hint="market_sizing",
            )
        ],
        approval=IssueTreeApproval(
            status=ApprovalStatus.APPROVED,
            approved_leaf_ids=["leaf-demand"],
        ),
    )
