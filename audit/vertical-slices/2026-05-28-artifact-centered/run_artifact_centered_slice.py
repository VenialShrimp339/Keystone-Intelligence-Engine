from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from keystone.artifacts import LocalArtifactStore, ProviderKind
from keystone.ingestion.vertical_slice import (
    CompletedProviderReport,
    run_artifact_centered_first_slice,
)
from keystone.providers import (
    BrowserJobSubmission,
    BrowserProviderAdapter,
    BrowserProviderExportBundle,
    BrowserSnapshot,
    BrowserTabClaim,
    ProviderLedgerStore,
)
from keystone.specification.issue_tree_package import (
    ApprovalStatus,
    CandidateAxis,
    ConfidenceTarget,
    CoverageLogic,
    EvaluationLogic,
    ExclusivityClaim,
    ExhaustivenessClaim,
    IssueTreeApproval,
    IssueTreeLeafTask,
    IssueTreePackage,
    IssueTreePackageEdge,
    IssueTreePackageNode,
    IssueTreeProblemFrame,
    PruneStatus,
    PruningDecision,
    QualityGateId,
    QualityGateResult,
    QualityGateResultStatus,
    RequiredArtifactType,
    SelectedAxis,
    SiblingGroup,
    SourceLogic,
    TruthLogic,
)

if TYPE_CHECKING:
    from keystone.providers.browser_provider import ProviderJobRecord

ROOT = Path(__file__).resolve().parent
INPUTS = ROOT / "inputs"
RUN_ROOT = ROOT / "run"
RUN_ID = "sqsp-permira-artifact-slice"
ROOT_REQUEST = (
    "We're advising a PE operating partner after Permira's Squarespace take-private. "
    "The ask is messy: is this a durable value-creation platform, or did the sponsor "
    "overpay for a mature website-builder asset? Build the issue tree, launch branch "
    "research, ingest completed provider reports, and produce a cited first-pass brief."
)


class FixtureController:
    def __init__(self) -> None:
        self.snapshots: dict[str, list[str]] = {}
        self.exports: dict[str, BrowserProviderExportBundle] = {}

    def open_or_claim_tab(self, record: ProviderJobRecord) -> BrowserTabClaim:
        return BrowserTabClaim(
            url=f"https://provider.local/{record.provider.value}/{record.branch_id}",
            tab_id=f"fixture-{record.branch_id}",
            claimed_existing=False,
        )

    def submit_research_job(self, record: ProviderJobRecord) -> BrowserJobSubmission:
        return BrowserJobSubmission(
            url=f"https://provider.local/{record.provider.value}/{record.branch_id}/job",
            provider_job_ref=f"fixture-{record.branch_id}",
        )

    def snapshot(self, record: ProviderJobRecord) -> BrowserSnapshot:
        queue = self.snapshots[record.job_id]
        dom_text = queue.pop(0) if queue else "Research complete. Download Markdown Word."
        return BrowserSnapshot(url=record.job_url or "", dom_text=dom_text)

    def export_completed_report(self, record: ProviderJobRecord) -> BrowserProviderExportBundle:
        return self.exports[record.job_id]


def main() -> None:
    if RUN_ROOT.exists():
        shutil.rmtree(RUN_ROOT)
    RUN_ROOT.mkdir(parents=True)

    package = build_issue_tree_package()
    controller = FixtureController()
    provider_ledger_store = ProviderLedgerStore(RUN_ROOT / "provider-ledger.json")
    adapter = BrowserProviderAdapter(
        controller=controller,
        ledger_store=provider_ledger_store,
    )

    growth_prompt = package.leaf_tasks[0].task_seed_prompt
    margin_prompt = package.leaf_tasks[1].task_seed_prompt
    growth_job = adapter.start_job(
        run_id=RUN_ID,
        provider=ProviderKind.CHATGPT,
        prompt=growth_prompt,
        branch_id="SQSP-1",
    )
    margin_job = adapter.start_job(
        run_id=RUN_ID,
        provider=ProviderKind.CLAUDE,
        prompt=margin_prompt,
        branch_id="SQSP-2",
    )

    controller.snapshots[growth_job.job_id] = [
        "Thinking. Searching. Stop answering.",
        "Download Markdown Word Sources used",
    ]
    controller.snapshots[margin_job.job_id] = [
        "Research complete. Artifact panel: Squarespace Margin And Cash Flow. 37 sources.",
    ]
    growth_report = INPUTS / "chatgpt-sqsp-growth-quality.md"
    growth_docx = INPUTS / "chatgpt-sqsp-source-links.docx"
    margin_report = INPUTS / "claude-sqsp-margin-fcf.md"
    controller.exports[growth_job.job_id] = BrowserProviderExportBundle(
        provider=ProviderKind.CHATGPT,
        markdown_path=str(growth_report),
        docx_source_path=str(growth_docx),
        source_urls=[
            "https://www.squarespace.com/press-releases/2024/10/17/permira-completes-acquisition-of-squarespace",
            "https://www.prnewswire.com/news-releases/squarespace-announces-second-quarter-2024-financial-results-302212968.html",
        ],
    )
    controller.exports[margin_job.job_id] = BrowserProviderExportBundle(
        provider=ProviderKind.CLAUDE,
        report_path=str(margin_report),
        source_urls=[
            "https://www.prnewswire.com/news-releases/squarespace-announces-second-quarter-2024-financial-results-302212968.html",
            "https://www.squarespace.com/press-releases/2024/6/21/squarespace-agrees-to-sell-tock-platform-to-american-express-for-400-million",
        ],
    )

    adapter.watch_until_terminal(
        run_id=RUN_ID,
        job_ids=[growth_job.job_id, margin_job.job_id],
        max_polls=4,
        poll_interval_seconds=0,
    )
    adapter.export_and_ingest(RUN_ID, growth_job.job_id)
    adapter.export_and_ingest(RUN_ID, margin_job.job_id)

    store = LocalArtifactStore(RUN_ROOT / "artifact-store")
    result = run_artifact_centered_first_slice(
        store=store,
        run_id=RUN_ID,
        root_request=ROOT_REQUEST,
        issue_tree_package=package,
        completed_reports=[
            CompletedProviderReport(
                provider=ProviderKind.CHATGPT,
                prompt=growth_prompt,
                report_path=growth_report,
                branch_id="SQSP-1",
                job_url=growth_job.job_url,
                export_paths=[str(growth_report), str(growth_docx)],
                source_urls=controller.exports[growth_job.job_id].source_urls,
            ),
            CompletedProviderReport(
                provider=ProviderKind.CLAUDE,
                prompt=margin_prompt,
                report_path=margin_report,
                branch_id="SQSP-2",
                job_url=margin_job.job_url,
                export_paths=[str(margin_report)],
                source_urls=controller.exports[margin_job.job_id].source_urls,
            ),
        ],
        domain="private_equity_software_diligence",
    )

    (RUN_ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (RUN_ROOT / "issue-tree-package.json").write_text(
        package.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))


def build_issue_tree_package() -> IssueTreePackage:
    frame = IssueTreeProblemFrame(
        original_prompt=ROOT_REQUEST,
        reconstructed_problem=(
            "Determine whether Squarespace is an attractive sponsor-owned value "
            "creation platform after the Permira take-private."
        ),
        decision_maker="PE operating partner and investment committee",
        decision_or_question=(
            "Can Permira create durable value in Squarespace after the take-private?"
        ),
        situation=(
            "Permira completed the acquisition, Squarespace is private, and the last "
            "public disclosures show subscription growth plus cash generation."
        ),
        complication=(
            "The asset is exposed to website-builder competition, ARPUS growth is modest, "
            "and sponsor returns require both operating execution and underwriting discipline."
        ),
        r1_undesired_result=(
            "Underwrite value creation from headline growth while missing mature-product, "
            "pricing, margin, integration, or competitive risks."
        ),
        r2_desired_result=(
            "Identify the few must-be-true branches that determine whether the platform "
            "can support a credible PE value-creation plan."
        ),
        constraints=[
            "Use public sources only for this first pass.",
            "Produce a cited markdown brief.",
            "Treat provider reports as completed exports before ingestion.",
        ],
        assumptions=[
            "No access to sponsor debt package, cohort data, or management forecast.",
            (
                "The first slice should identify diligence priorities, not issue a final "
                "investment memo."
            ),
        ],
    )
    nodes = [
        IssueTreePackageNode(
            node_id="SQSP-root",
            parent_id=None,
            tree_scope="both",
            depth=0,
            statement="Squarespace value creation clears PE must-be-true gates",
            question_or_hypothesis=(
                "Can growth quality, cash-flow expansion, and execution risk support "
                "a credible sponsor case?"
            ),
            decomposition_axis="must_be_true_value_creation",
            source_logic=SourceLogic.CRITERIA,
            priority="high",
            decision_relevance="high",
        ),
        IssueTreePackageNode(
            node_id="SQSP-1",
            parent_id="SQSP-root",
            tree_scope="both",
            depth=1,
            statement="Growth base is durable and monetizable",
            question_or_hypothesis=(
                "Are subscriptions, ARRR, ARPUS, commerce, and competitive position "
                "strong enough to support upside?"
            ),
            decomposition_axis="value_creation_gate",
            source_logic=SourceLogic.CRITERIA,
            priority="high",
            decision_relevance="high",
            measurable_variable_or_proxy=(
                "ARRR growth, unique subscriptions, ARPUS, competitor bookings"
            ),
            named_mechanism="subscription base monetization",
            decision_consequence="Determines whether growth underwriting is credible",
            disconfirming_test="Growth is migration-driven, low-retention, or competitively capped",
        ),
        IssueTreePackageNode(
            node_id="SQSP-2",
            parent_id="SQSP-root",
            tree_scope="both",
            depth=1,
            statement="Margins and free cash flow support sponsor economics",
            question_or_hypothesis=(
                "Can EBITDA, unlevered free cash flow, and portfolio focus support "
                "deleveraging and reinvestment?"
            ),
            decomposition_axis="value_creation_gate",
            source_logic=SourceLogic.CRITERIA,
            priority="high",
            decision_relevance="high",
            measurable_variable_or_proxy=(
                "Adjusted EBITDA, UFCF, operating cash flow, divestiture proceeds"
            ),
            named_mechanism="operating leverage and portfolio simplification",
            decision_consequence="Determines debt capacity and value-creation runway",
            disconfirming_test=(
                "Cash generation is non-recurring or consumed by reinvestment and debt service"
            ),
        ),
        IssueTreePackageNode(
            node_id="SQSP-3",
            parent_id="SQSP-root",
            tree_scope="full",
            depth=1,
            statement="Transaction and execution risks are manageable",
            question_or_hypothesis=(
                "Are financing, retention, integration, and disruption risks bounded enough?"
            ),
            decomposition_axis="risk_gate",
            source_logic=SourceLogic.CRITERIA,
            priority="medium",
            decision_relevance="medium",
            prune_status=PruneStatus.DEFER,
        ),
    ]
    return IssueTreePackage(
        package_id="sqsp-permira-package",
        problem_frame=frame,
        candidate_axes=[
            CandidateAxis(
                axis_id="must_be_true",
                label="Must-be-true value creation gates",
                what_it_reveals="Sponsor case blockers and branch-level research prompts",
                what_it_hides="Detailed operating plan sequencing",
                risk="May underweight upside options not needed for the first pass",
                selected=True,
            ),
            CandidateAxis(
                axis_id="functional",
                label="Growth, product, finance, risk functions",
                what_it_reveals="Clean workstream ownership",
                what_it_hides="Whether a branch can actually change the investment answer",
                risk="Can become a generic diligence checklist",
                selected=False,
            ),
        ],
        selected_axis=SelectedAxis(
            axis_id="must_be_true",
            rationale=(
                "A take-private diligence slice should dispatch provider research only "
                "to branches that can change the sponsor value-creation answer."
            ),
            rejected_axis_notes=[
                (
                    "Functional workstreams are useful after gates are proven, but too "
                    "broad for slice one."
                )
            ],
        ),
        full_tree=nodes,
        pruned_tree=[nodes[0], nodes[1], nodes[2]],
        edges=[
            IssueTreePackageEdge(parent_id="SQSP-root", child_id="SQSP-1"),
            IssueTreePackageEdge(parent_id="SQSP-root", child_id="SQSP-2"),
            IssueTreePackageEdge(parent_id="SQSP-root", child_id="SQSP-3"),
        ],
        sibling_logic=[
            SiblingGroup(
                group_id="sqsp-root-gates",
                parent_id="SQSP-root",
                child_ids=["SQSP-1", "SQSP-2", "SQSP-3"],
                decomposition_axis="must_be_true_value_creation",
                coverage_logic=CoverageLogic.EXHAUSTIVE,
                truth_logic=TruthLogic.AND,
                evaluation_logic=EvaluationLogic.EVIDENCE_SUFFICIENCY,
                exclusivity_claim=ExclusivityClaim.MATERIALLY_DISTINCT,
                exhaustiveness_claim=ExhaustivenessClaim.COMPLETE_FOR_DECISION,
                validation_note=(
                    "Growth, cash-flow, and execution-risk gates are distinct enough "
                    "for first-pass research and jointly cover the sponsor case."
                ),
            )
        ],
        leaf_tasks=[
            IssueTreeLeafTask(
                leaf_id="SQSP-L1-growth",
                node_id="SQSP-1",
                research_question=(
                    "Is Squarespace's post-take-private growth base durable and monetizable?"
                ),
                resolution_criteria=[
                    "ARRR, subscription, ARPUS, and competitive data are cited.",
                    "Disconfirming risks to growth quality are explicit.",
                ],
                evidence_requirements=[
                    "Squarespace Q2 2024 operating metrics",
                    "Transaction close facts",
                    "Competitor benchmark evidence",
                ],
                expected_artifact="Growth-quality memo with source map",
                disconfirming_evidence_to_seek=[
                    "Growth is driven by low-quality migrated domains or weak retention",
                    "Competitors have stronger agency, AI, or commerce momentum",
                ],
                likely_sources_or_methods=[
                    "Company press releases",
                    "Competitor public results",
                    "Transaction announcement risk factors",
                ],
                task_seed_prompt=(
                    "Assess whether Squarespace's post-take-private growth base is "
                    "strong enough for a PE sponsor to underwrite value creation "
                    "without relying mainly on multiple expansion."
                ),
                required_artifact_type=RequiredArtifactType.MEMO,
                acceptance_criteria=[
                    "At least five source-backed claims",
                    "Explicit disconfirming evidence",
                ],
                source_policy="Use public company and credible competitor sources.",
                confidence_target=ConfidenceTarget.HIGH,
                downstream_agent_routing_hint="strategic_positioning",
            ),
            IssueTreeLeafTask(
                leaf_id="SQSP-L2-margin",
                node_id="SQSP-2",
                research_question=(
                    "Can Squarespace's margin and cash flow support PE value creation?"
                ),
                resolution_criteria=[
                    (
                        "Adjusted EBITDA, UFCF, operating cash flow, and Tock perimeter "
                        "facts are cited."
                    ),
                    "Non-GAAP and debt-service caveats are explicit.",
                ],
                evidence_requirements=[
                    "Squarespace Q2 2024 financial metrics",
                    "Tock divestiture evidence",
                    "Transaction risk factors",
                ],
                expected_artifact="Margin and cash-flow bridge memo",
                disconfirming_evidence_to_seek=[
                    "EBITDA expansion is absent despite growth",
                    "Cash flow is insufficient after debt service and reinvestment",
                ],
                likely_sources_or_methods=[
                    "Financial results press release",
                    "Divestiture announcements",
                    "Transaction announcement risk factors",
                ],
                task_seed_prompt=(
                    "Assess whether Squarespace's margin, cash-flow, and portfolio "
                    "posture can support private-equity value creation after the "
                    "Permira take-private."
                ),
                required_artifact_type=RequiredArtifactType.MEMO,
                acceptance_criteria=[
                    "At least five source-backed claims",
                    "Explicit non-GAAP caveats",
                ],
                source_policy="Use public company, acquirer, and transaction sources.",
                confidence_target=ConfidenceTarget.HIGH,
                downstream_agent_routing_hint="financial_analysis",
            ),
        ],
        pruning_decisions=[
            PruningDecision(
                node_id="SQSP-1",
                action=PruneStatus.KEEP,
                rationale="Growth quality is a high-impact and still-uncertain sponsor-case gate.",
                impact_score=5,
                uncertainty_score=4,
                evidence_cost_score=2,
                discriminating_power_score=5,
                influenceability_score=4,
                value_of_information_note=(
                    "Determines whether value creation can start from durable growth."
                ),
                risk_if_wrong="high",
                reopen_condition=(
                    "New cohort, retention, or competitor evidence changes growth quality."
                ),
            ),
            PruningDecision(
                node_id="SQSP-2",
                action=PruneStatus.KEEP,
                rationale=(
                    "Cash-flow support is required for debt, reinvestment, and sponsor returns."
                ),
                impact_score=5,
                uncertainty_score=4,
                evidence_cost_score=2,
                discriminating_power_score=5,
                influenceability_score=4,
                value_of_information_note="Determines whether the sponsor case can fund itself.",
                risk_if_wrong="high",
                reopen_condition=(
                    "Debt package, management forecast, or non-GAAP reconciliation changes."
                ),
            ),
            PruningDecision(
                node_id="SQSP-3",
                action=PruneStatus.DEFER,
                rationale=(
                    "Execution risks matter, but first-pass public evidence should establish "
                    "whether growth and cash-flow gates merit deeper risk work."
                ),
                impact_score=4,
                uncertainty_score=4,
                evidence_cost_score=3,
                discriminating_power_score=3,
                influenceability_score=3,
                value_of_information_note=(
                    "Reopen after branch reports if either retained gate passes."
                ),
                risk_if_wrong="medium",
                reopen_condition=(
                    "Provider reports show growth and cash-flow gates are strong enough."
                ),
            ),
        ],
        approval=IssueTreeApproval(
            status=ApprovalStatus.APPROVED,
            approved_leaf_ids=["SQSP-L1-growth", "SQSP-L2-margin"],
            reviewer="codex-autonomous-slice",
            notes=["Approved for first public-source vertical slice."],
        ),
        quality_gate_results=[
            QualityGateResult(
                gate_id=QualityGateId.PROBLEM_FRAME,
                result=QualityGateResultStatus.PASS,
                finding="Decision maker, R1, R2, constraints, and assumptions are explicit.",
            ),
            QualityGateResult(
                gate_id=QualityGateId.AXIS_FIT,
                result=QualityGateResultStatus.PASS,
                finding="Must-be-true gates fit a PE take-private value-creation question.",
            ),
            QualityGateResult(
                gate_id=QualityGateId.PRUNING,
                result=QualityGateResultStatus.PASS,
                finding="Pruned tree keeps two branch prompts and defers execution risk.",
            ),
            QualityGateResult(
                gate_id=QualityGateId.LEAF_ACTIONABILITY,
                result=QualityGateResultStatus.PASS,
                finding=(
                    "Approved leaves contain research prompts, evidence requirements, "
                    "and artifacts."
                ),
            ),
        ],
    )


if __name__ == "__main__":
    main()
