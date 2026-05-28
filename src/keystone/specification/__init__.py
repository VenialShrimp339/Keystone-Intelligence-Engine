"""Specification Engine (L0): Question -> EngagementSpec pipeline.

The highest-leverage component in the system. Takes a natural language
question and produces a complete engagement specification: RESEARCH.md,
research-tasks.json (DAG structure), issue tree, agent configurations,
and Day-1 Hypothesis.

10-step pipeline:
1. Classification (engagement type + pipeline profile)
2. Intent clarification (Decision-First CoT + Day-1 Hypothesis)
3. Issue tree decomposition (3 heterogeneous lens agents + flagship synthesis)
4. MECE validation (5 binary dimensions)
5. Priority scoring (heuristic: decision_relevance x uncertainty_reduction)
6. Template matching (seed AgentDefinition registry)
7. Task generation (research-tasks.json with DAG)
8. HITL Gate 1 (blocks until human approval)
9-10. Research execution + feedback (stubs for Phase 1)
"""

from keystone.specification.engagement_classifier import (
    ClassificationResult,
    EngagementClassifier,
    PipelineProfile,
)
from keystone.specification.intent_clarifier import (
    IntentClarificationResult,
    IntentClarifier,
)
from keystone.specification.issue_tree_package import (
    ApprovalStatus as IssueTreeApprovalStatus,
    CandidateAxis,
    ConfidenceTarget,
    IssueTreeApproval,
    IssueTreeLeafTask,
    IssueTreePackage,
    IssueTreePackageNode,
    IssueTreeProblemFrame,
    PruneStatus,
    RequiredArtifactType,
    SelectedAxis,
)
from keystone.specification.decomposer import (
    Decomposer,
    IssueTree,
    IssueTreeMetadata,
    IssueTreeNode,
)
from keystone.specification.validator import (
    MECEValidationResult,
    MECEValidator,
    ValidationDimension,
)
from keystone.specification.priority_scorer import (
    PriorityScore,
    PriorityScorer,
)
from keystone.specification.template_registry import (
    TemplateMatch,
    TemplateRegistry,
)
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.spec_engine import SpecificationEngine

__all__ = [
    "ClassificationResult",
    "Decomposer",
    "EngagementClassifier",
    "IntentClarificationResult",
    "IntentClarifier",
    "CandidateAxis",
    "ConfidenceTarget",
    "IssueTreeApproval",
    "IssueTreeApprovalStatus",
    "IssueTreeLeafTask",
    "IssueTreePackage",
    "IssueTreePackageNode",
    "IssueTreeProblemFrame",
    "IssueTree",
    "IssueTreeMetadata",
    "IssueTreeNode",
    "MECEValidationResult",
    "MECEValidator",
    "PipelineProfile",
    "PruneStatus",
    "PriorityScore",
    "PriorityScorer",
    "RequiredArtifactType",
    "SelectedAxis",
    "SpecificationEngine",
    "TaskGenerator",
    "TemplateMatch",
    "TemplateRegistry",
    "ValidationDimension",
]
