from __future__ import annotations

from datetime import UTC, datetime

import pytest

from keystone.models.research import EngagementType, ResearchQuestion, ResearchSpec
from keystone.specification.issue_tree_package import (
    ApprovalStatus,
    CandidateAxis,
    ConfidenceTarget,
    IssueTreeApproval,
    IssueTreeLeafTask,
    IssueTreePackage,
    IssueTreePackageNode,
    IssueTreeProblemFrame,
    PruneStatus,
    QualityGateId,
    QualityGateResult,
    QualityGateResultStatus,
    RequiredArtifactType,
    SelectedAxis,
)
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.template_registry import TemplateRegistry


def _package(*, approval_status: ApprovalStatus = ApprovalStatus.APPROVED) -> IssueTreePackage:
    frame = IssueTreeProblemFrame(
        original_prompt="Should we enter the market?",
        reconstructed_problem="Decide whether the market is worth entering.",
        decision_maker="Investment committee",
        decision_or_question="Should the firm enter the market?",
        situation="The team has a plausible entry concept.",
        complication="Market demand and margins are uncertain.",
        r1_undesired_result="Enter a market with weak demand or poor economics.",
        r2_desired_result="Commit only if demand and economics meet the hurdle.",
        constraints=["Public-source first pass"],
        assumptions=["Decision needed this quarter"],
    )
    nodes = [
        IssueTreePackageNode(
            node_id="root",
            parent_id=None,
            tree_scope="both",
            depth=0,
            statement="Market entry decision",
            question_or_hypothesis="Can the opportunity clear the investment hurdle?",
            decomposition_axis="must_be_true",
            prune_status=PruneStatus.KEEP,
        ),
        IssueTreePackageNode(
            node_id="demand",
            parent_id="root",
            tree_scope="both",
            depth=1,
            statement="Demand is large and reachable",
            question_or_hypothesis="Is there enough reachable demand?",
            decomposition_axis="must_be_true",
            priority="high",
            decision_relevance="high",
            prune_status=PruneStatus.KEEP,
        ),
        IssueTreePackageNode(
            node_id="margin",
            parent_id="root",
            tree_scope="both",
            depth=1,
            statement="Margins can meet hurdle",
            question_or_hypothesis="Can margins meet the hurdle?",
            decomposition_axis="must_be_true",
            priority="high",
            decision_relevance="high",
            prune_status=PruneStatus.KEEP,
        ),
    ]
    return IssueTreePackage(
        package_id="pkg-test",
        problem_frame=frame,
        candidate_axes=[
            CandidateAxis(
                axis_id="a1",
                label="Must-be-true tests",
                what_it_reveals="Decision blockers",
                what_it_hides="Implementation detail",
                risk="Can underweight optional upside",
                selected=True,
            )
        ],
        selected_axis=SelectedAxis(axis_id="a1", rationale="Must-be-true tests govern entry."),
        full_tree=nodes,
        pruned_tree=nodes,
        leaf_tasks=[
            IssueTreeLeafTask(
                leaf_id="leaf-demand",
                node_id="demand",
                research_question="How much reachable demand exists?",
                resolution_criteria=["Estimate reachable demand with source traceability"],
                evidence_requirements=["Market size, customer segments, adoption constraints"],
                expected_artifact="Demand sizing memo",
                disconfirming_evidence_to_seek=[
                    "Evidence demand is concentrated in unreachable segments"
                ],
                likely_sources_or_methods=["industry reports", "public filings"],
                task_seed_prompt="Research reachable demand.",
                required_artifact_type=RequiredArtifactType.MEMO,
                acceptance_criteria=["Demand estimate is cited and caveated"],
                confidence_target=ConfidenceTarget.HIGH,
                downstream_agent_routing_hint="market_sizing",
            ),
            IssueTreeLeafTask(
                leaf_id="leaf-margin",
                node_id="margin",
                research_question="Can gross margin clear the hurdle?",
                resolution_criteria=["Build a public-source margin bridge"],
                evidence_requirements=["Pricing, unit costs, benchmarks"],
                expected_artifact="Margin sensitivity table",
                disconfirming_evidence_to_seek=[
                    "Evidence variable costs consume contribution margin"
                ],
                likely_sources_or_methods=["filings", "benchmarks"],
                task_seed_prompt="Research margin feasibility.",
                required_artifact_type=RequiredArtifactType.SENSITIVITY_TABLE,
                acceptance_criteria=["Margin bridge includes downside case"],
                confidence_target=ConfidenceTarget.MEDIUM,
                downstream_agent_routing_hint="financial_analysis",
            ),
        ],
        approval=IssueTreeApproval(
            status=approval_status,
            approved_leaf_ids=["leaf-demand", "leaf-margin"]
            if approval_status == ApprovalStatus.APPROVED
            else [],
        ),
        quality_gate_results=[
            QualityGateResult(
                gate_id=QualityGateId.PROBLEM_FRAME,
                result=QualityGateResultStatus.PASS,
                finding="Frame is explicit.",
            )
        ],
    )


def _spec() -> ResearchSpec:
    return ResearchSpec(
        engagement_id="eng_test",
        client_id="client_test",
        title="Market Entry",
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context="Investment committee deciding whether to enter the market.",
        surprising_finding="Demand is not reachable or margins cannot clear the hurdle.",
        questions=[ResearchQuestion(question="Should we enter the market?", is_primary=True)],
        output_format="markdown",
        engagement_type=EngagementType.EVALUATIVE,
        day_1_hypothesis="Market entry is attractive if demand and margins hold.",
    )


def test_package_filters_to_approved_leaf_tasks():
    package = _package()

    leaves = package.approved_leaf_tasks()

    assert [leaf.leaf_id for leaf in leaves] == ["leaf-demand", "leaf-margin"]


def test_package_does_not_dispatch_without_approval():
    package = _package(approval_status=ApprovalStatus.PENDING_APPROVAL)

    assert package.approved_leaf_tasks() == []


def test_package_converts_to_legacy_issue_tree():
    tree = _package().to_legacy_issue_tree()

    assert tree.root.id == "root"
    assert tree.metadata.leaf_count == 2
    assert tree.root.children[0].id == "demand"


def test_package_requires_selected_axis_to_reference_candidate():
    package_data = _package().model_dump()
    package_data["selected_axis"]["axis_id"] = "missing"

    with pytest.raises(ValueError, match="selected_axis"):
        IssueTreePackage.model_validate(package_data)


def test_task_generator_uses_approved_leaf_tasks_without_llm():
    async def unused_llm(prompt: str) -> str:
        raise AssertionError(f"LLM should not be called: {prompt}")

    generator = TaskGenerator(unused_llm, TemplateRegistry())

    result = generator.generate_from_issue_tree_package(
        _package(), EngagementType.EVALUATIVE, _spec()
    )

    assert [task.issue_tree_branch_id for task in result.tasks] == ["demand", "margin"]
    assert result.tasks[0].description == "How much reachable demand exists?"
    assert result.tasks[0].priority == 1
    assert result.tasks[0].importance.value == "primary"
    assert 3 <= len(result.tasks[0].assigned_tools) <= 5
    assert "evidence both for and against" in result.tasks[0].anti_confirmatory_framing
