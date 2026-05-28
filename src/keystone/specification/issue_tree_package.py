"""Typed issue-tree package for artifact-centered research planning.

The existing :mod:`keystone.specification.decomposer` produces a compact
legacy issue tree. This module adds the richer upstream package needed by the
problem-decomposition skill: problem frame, axis selection, full/pruned tree
state, pruning decisions, approval state, and executable leaf tasks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from keystone.specification.decomposer import IssueTree, IssueTreeMetadata, IssueTreeNode
from keystone.specification.priority_scorer import PriorityScore


def _now() -> datetime:
    return datetime.now(UTC)


class TreeScope(StrEnum):
    """Where a node appears in the issue-tree package."""

    FULL = "full"
    PRUNED = "pruned"
    BOTH = "both"


class SourceLogic(StrEnum):
    """Sibling source logic for a decomposition group."""

    SEQUENCE = "sequence"
    STRUCTURE = "structure"
    CLASS = "class"
    CRITERIA = "criteria"
    DIAGNOSTIC = "diagnostic"
    DEDUCTIVE = "deductive"
    CUSTOM = "custom"


class CoverageLogic(StrEnum):
    """Coverage claim for a sibling group."""

    EXHAUSTIVE = "exhaustive"
    REPRESENTATIVE = "representative"
    RANKED = "ranked"
    SCENARIO_SET = "scenario_set"
    CUSTOM = "custom"


class TruthLogic(StrEnum):
    """Truth relationship between siblings and parent."""

    AND = "AND"
    OR = "OR"
    WEIGHTED_FACTOR = "weighted_factor"
    CONSTRAINT_GATE = "constraint_gate"
    MINIMUM_BOTTLENECK = "minimum_bottleneck"
    NONE = "none"
    CUSTOM = "custom"


class EvaluationLogic(StrEnum):
    """How siblings should be evaluated."""

    DIAGNOSTIC_CANDIDATES = "diagnostic_candidates"
    PORTFOLIO = "portfolio"
    SEQUENCE = "sequence"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    TRADEOFF = "tradeoff"
    NONE = "none"
    CUSTOM = "custom"


class ExclusivityClaim(StrEnum):
    """MECE exclusivity claim for a sibling group."""

    MUTUALLY_EXCLUSIVE = "mutually_exclusive"
    MATERIALLY_DISTINCT = "materially_distinct"
    OVERLAPPING_BY_DESIGN = "overlapping_by_design"


class ExhaustivenessClaim(StrEnum):
    """MECE exhaustiveness claim for a sibling group."""

    COMPLETE_FOR_DECISION = "complete_for_decision"
    PARTIAL_PENDING_CLARIFICATION = "partial_pending_clarification"
    NOT_EXHAUSTIVE_BY_DESIGN = "not_exhaustive_by_design"


class PriorityLevel(StrEnum):
    """Discrete priority level used by the issue-tree package."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PruneStatus(StrEnum):
    """Pruning action for a node."""

    KEEP = "keep"
    PRUNE = "prune"
    DEFER = "defer"
    MERGE = "merge"


class RequiredArtifactType(StrEnum):
    """Expected artifact type from a leaf task."""

    MEMO = "memo"
    MODEL = "model"
    DATASET = "dataset"
    TIMELINE = "timeline"
    SOURCE_MAP = "source_map"
    SENSITIVITY_TABLE = "sensitivity_table"
    OTHER = "other"


class ConfidenceTarget(StrEnum):
    """Confidence target for resolving a leaf."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(StrEnum):
    """Approval state for dispatching issue-tree leaves into execution."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class QualityGateId(StrEnum):
    """Quality gates mirrored from the problem-decomposition skill."""

    PROBLEM_FRAME = "problem_frame"
    AXIS_FIT = "axis_fit"
    SIBLING_LOGIC = "sibling_logic"
    MECE = "mece"
    HYPOTHESIS = "hypothesis"
    PRUNING = "pruning"
    LEAF_ACTIONABILITY = "leaf_actionability"
    ANTI_GENERICITY = "anti_genericity"
    EVAL_HYGIENE = "eval_hygiene"


class QualityGateResultStatus(StrEnum):
    """Result of a package quality gate."""

    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVISION = "needs_revision"


class IssueTreeProblemFrame(BaseModel):
    """Decision frame that governs the tree."""

    model_config = ConfigDict(extra="forbid")

    original_prompt: str
    reconstructed_problem: str
    decision_maker: str
    decision_or_question: str
    situation: str
    complication: str
    r1_undesired_result: str
    r2_desired_result: str
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguity_status: str = "clear"
    blocking_unknowns: list[str] = Field(default_factory=list)
    objective_definition_branches: list[str] = Field(default_factory=list)

    @field_validator(
        "decision_maker",
        "decision_or_question",
        "r1_undesired_result",
        "r2_desired_result",
    )
    @classmethod
    def require_semantic_frame(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("required problem-frame fields must be explicit")
        return value


class CandidateAxis(BaseModel):
    """A candidate top-level decomposition axis."""

    model_config = ConfigDict(extra="forbid")

    axis_id: str
    label: str
    what_it_reveals: str
    what_it_hides: str
    risk: str
    selected: bool = False


class SelectedAxis(BaseModel):
    """Selected decomposition axis and rationale."""

    model_config = ConfigDict(extra="forbid")

    axis_id: str
    rationale: str
    rejected_axis_notes: list[str] = Field(default_factory=list)


class IssueTreePackageNode(BaseModel):
    """Node in the full or pruned issue tree."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    parent_id: str | None = None
    tree_scope: TreeScope = TreeScope.FULL
    depth: int = Field(ge=0)
    statement: str
    question_or_hypothesis: str
    decomposition_axis: str
    source_logic: SourceLogic = SourceLogic.CUSTOM
    priority: PriorityLevel = PriorityLevel.MEDIUM
    decision_relevance: PriorityLevel = PriorityLevel.MEDIUM
    measurable_variable_or_proxy: str | None = None
    named_mechanism: str | None = None
    decision_consequence: str | None = None
    disconfirming_test: str | None = None
    prune_status: PruneStatus = PruneStatus.KEEP


class IssueTreePackageEdge(BaseModel):
    """Directed parent-child edge in the tree package."""

    model_config = ConfigDict(extra="forbid")

    parent_id: str
    child_id: str
    relation_note: str = ""


class SiblingGroup(BaseModel):
    """Sibling-group logic and MECE claims."""

    model_config = ConfigDict(extra="forbid")

    group_id: str
    parent_id: str
    child_ids: list[str]
    decomposition_axis: str
    coverage_logic: CoverageLogic = CoverageLogic.EXHAUSTIVE
    truth_logic: TruthLogic = TruthLogic.NONE
    evaluation_logic: EvaluationLogic = EvaluationLogic.NONE
    exclusivity_claim: ExclusivityClaim = ExclusivityClaim.MATERIALLY_DISTINCT
    exhaustiveness_claim: ExhaustivenessClaim = ExhaustivenessClaim.COMPLETE_FOR_DECISION
    validation_note: str


class IssueTreeEvidenceRequirement(BaseModel):
    """Reusable evidence requirement attached to a leaf task."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    leaf_id: str
    description: str
    source_policy: str
    required_artifact_type: RequiredArtifactType = RequiredArtifactType.MEMO
    confidence_target: ConfidenceTarget = ConfidenceTarget.MEDIUM


class IssueTreeLeafTask(BaseModel):
    """Approved bridge unit from issue tree to research execution."""

    model_config = ConfigDict(extra="forbid")

    leaf_id: str
    node_id: str | None = None
    research_question: str
    resolution_criteria: list[str] = Field(default_factory=list)
    evidence_requirements: list[str] = Field(default_factory=list)
    expected_artifact: str
    disconfirming_evidence_to_seek: list[str] = Field(default_factory=list)
    likely_sources_or_methods: list[str] = Field(default_factory=list)
    task_seed_prompt: str
    required_artifact_type: RequiredArtifactType = RequiredArtifactType.MEMO
    acceptance_criteria: list[str] = Field(default_factory=list)
    source_policy: str = "Use traceable primary and credible secondary sources."
    confidence_target: ConfidenceTarget = ConfidenceTarget.MEDIUM
    human_approval_required: bool = True
    downstream_agent_routing_hint: str | None = None

    @property
    def branch_id(self) -> str:
        """Stable branch id to preserve in downstream ``ResearchTask`` records."""
        return self.node_id or self.leaf_id


class PruningDecision(BaseModel):
    """Decision record explaining keep/prune/defer/merge actions."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    action: PruneStatus
    rationale: str
    impact_score: int = Field(ge=1, le=5)
    uncertainty_score: int = Field(ge=1, le=5)
    evidence_cost_score: int = Field(ge=1, le=5)
    discriminating_power_score: int = Field(ge=1, le=5)
    influenceability_score: int = Field(ge=1, le=5)
    dependency_ids: list[str] = Field(default_factory=list)
    value_of_information_note: str
    risk_if_wrong: PriorityLevel = PriorityLevel.MEDIUM
    reopen_condition: str | None = None


class IssueTreeApproval(BaseModel):
    """Human approval state for dispatchable leaves."""

    model_config = ConfigDict(extra="forbid")

    status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    approved_leaf_ids: list[str] = Field(default_factory=list)
    reviewer: str | None = None
    approved_at: datetime | None = None
    notes: list[str] = Field(default_factory=list)


class QualityGateResult(BaseModel):
    """Result for one package quality gate."""

    model_config = ConfigDict(extra="forbid")

    gate_id: QualityGateId
    result: QualityGateResultStatus
    finding: str
    revision_made: str | None = None


class EvalHygiene(BaseModel):
    """Evaluation hygiene metadata for benchmark or skill-produced packages."""

    model_config = ConfigDict(extra="forbid")

    examples_used_as_priors: list[str] = Field(default_factory=list)
    potential_contamination_notes: list[str] = Field(default_factory=list)
    benchmark_case_overlap_risk: str = "unknown"


class IssueTreePackage(BaseModel):
    """Artifact-centered issue tree package upstream of the legacy decomposer."""

    model_config = ConfigDict(extra="forbid")

    package_id: str
    created_at: datetime = Field(default_factory=_now)
    problem_frame: IssueTreeProblemFrame
    candidate_axes: list[CandidateAxis]
    selected_axis: SelectedAxis
    full_tree: list[IssueTreePackageNode]
    pruned_tree: list[IssueTreePackageNode]
    edges: list[IssueTreePackageEdge] = Field(default_factory=list)
    sibling_logic: list[SiblingGroup] = Field(default_factory=list)
    leaf_tasks: list[IssueTreeLeafTask] = Field(default_factory=list)
    evidence_requirements: list[IssueTreeEvidenceRequirement] = Field(default_factory=list)
    pruning_decisions: list[PruningDecision] = Field(default_factory=list)
    approval: IssueTreeApproval = Field(default_factory=IssueTreeApproval)
    quality_gate_results: list[QualityGateResult] = Field(default_factory=list)
    eval_hygiene: EvalHygiene = Field(default_factory=EvalHygiene)

    @model_validator(mode="after")
    def validate_package_links(self) -> Self:
        selected_axes = [axis.axis_id for axis in self.candidate_axes if axis.selected]
        if self.selected_axis.axis_id not in {axis.axis_id for axis in self.candidate_axes}:
            raise ValueError("selected_axis must reference a candidate axis")
        if selected_axes and self.selected_axis.axis_id not in selected_axes:
            raise ValueError("candidate_axes selected flag conflicts with selected_axis")

        full_ids = [node.node_id for node in self.full_tree]
        pruned_ids = [node.node_id for node in self.pruned_tree]
        if len(set(full_ids)) != len(full_ids):
            raise ValueError("node_id values must be unique within full_tree")
        if len(set(pruned_ids)) != len(pruned_ids):
            raise ValueError("node_id values must be unique within pruned_tree")
        node_ids = set(full_ids) | set(pruned_ids)
        for edge in self.edges:
            if edge.parent_id not in node_ids or edge.child_id not in node_ids:
                raise ValueError("edges must reference package nodes")
        for group in self.sibling_logic:
            if group.parent_id not in node_ids:
                raise ValueError("sibling group parent_id must reference a package node")
            missing = [child_id for child_id in group.child_ids if child_id not in node_ids]
            if missing:
                raise ValueError(f"sibling group child_ids missing nodes: {missing}")

        leaf_ids = {leaf.leaf_id for leaf in self.leaf_tasks}
        if len(leaf_ids) != len(self.leaf_tasks):
            raise ValueError("leaf_task leaf_id values must be unique")
        approved_missing = [
            leaf_id for leaf_id in self.approval.approved_leaf_ids if leaf_id not in leaf_ids
        ]
        if approved_missing:
            raise ValueError(f"approval references missing leaf_ids: {approved_missing}")
        for requirement in self.evidence_requirements:
            if requirement.leaf_id not in leaf_ids:
                raise ValueError("evidence requirement leaf_id must reference a leaf task")
        return self

    def approved_leaf_tasks(self) -> list[IssueTreeLeafTask]:
        """Return leaf tasks cleared for research execution."""
        if self.approval.status != ApprovalStatus.APPROVED:
            return []
        if not self.approval.approved_leaf_ids:
            return list(self.leaf_tasks)
        allowed = set(self.approval.approved_leaf_ids)
        return [leaf for leaf in self.leaf_tasks if leaf.leaf_id in allowed]

    def priority_scores_from_leaf_tasks(self) -> list[PriorityScore]:
        """Create deterministic priority scores for approved leaves."""
        scores: list[PriorityScore] = []
        for leaf in self.approved_leaf_tasks():
            relevance = _priority_to_score(
                _node_priority(self.pruned_tree, leaf.branch_id, "decision_relevance")
            )
            uncertainty = _confidence_to_uncertainty(leaf.confidence_target)
            scores.append(
                PriorityScore(
                    branch_id=leaf.branch_id,
                    decision_relevance=relevance,
                    uncertainty_reduction=uncertainty,
                    priority_score=round(relevance * uncertainty, 4),
                    reasoning=(
                        "Derived from approved IssueTreePackage leaf task priority "
                        "and confidence target."
                    ),
                )
            )
        return scores

    def to_legacy_issue_tree(self, *, pruned: bool = True) -> IssueTree:
        """Down-convert package nodes into the legacy ``IssueTree`` contract."""
        nodes = self.pruned_tree if pruned else self.full_tree
        if not nodes:
            raise ValueError("cannot convert an empty issue tree package")

        by_parent: dict[str | None, list[IssueTreePackageNode]] = {}
        for node in nodes:
            by_parent.setdefault(node.parent_id, []).append(node)

        roots = by_parent.get(None, [])
        if len(roots) == 1:
            root = _to_legacy_node(roots[0], by_parent)
        else:
            root = IssueTreeNode(
                id="root",
                name=self.problem_frame.decision_or_question,
                description=self.problem_frame.reconstructed_problem,
                children=[_to_legacy_node(node, by_parent) for node in roots],
                lens_annotations={"source": "issue_tree_package"},
            )

        metadata = IssueTreeMetadata(
            depth=max((node.depth for node in nodes), default=0),
            leaf_count=_legacy_leaf_count(root),
            lenses_used=["problem_decomposition_skill"],
            synthesis_rationale=self.selected_axis.rationale,
        )
        return IssueTree(root=root, metadata=metadata)


def _to_legacy_node(
    node: IssueTreePackageNode,
    by_parent: dict[str | None, list[IssueTreePackageNode]],
) -> IssueTreeNode:
    return IssueTreeNode(
        id=node.node_id,
        name=node.statement,
        description=node.question_or_hypothesis,
        children=[_to_legacy_node(child, by_parent) for child in by_parent.get(node.node_id, [])],
        lens_annotations={
            "tree_scope": node.tree_scope.value,
            "source_logic": node.source_logic.value,
            "prune_status": node.prune_status.value,
        },
    )


def _legacy_leaf_count(node: IssueTreeNode) -> int:
    if not node.children:
        return 1
    return sum(_legacy_leaf_count(child) for child in node.children)


def _node_priority(
    nodes: list[IssueTreePackageNode],
    node_id: str,
    attribute: str,
) -> PriorityLevel:
    for node in nodes:
        if node.node_id == node_id:
            value = getattr(node, attribute)
            if isinstance(value, PriorityLevel):
                return value
    return PriorityLevel.MEDIUM


def _priority_to_score(priority: PriorityLevel) -> float:
    return {
        PriorityLevel.HIGH: 0.9,
        PriorityLevel.MEDIUM: 0.65,
        PriorityLevel.LOW: 0.35,
    }[priority]


def _confidence_to_uncertainty(confidence: ConfidenceTarget) -> float:
    return {
        ConfidenceTarget.HIGH: 0.9,
        ConfidenceTarget.MEDIUM: 0.7,
        ConfidenceTarget.LOW: 0.45,
    }[confidence]
