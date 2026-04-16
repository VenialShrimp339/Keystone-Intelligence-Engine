"""Tests for the task generator (Step 7)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from keystone.models.research import (
    EngagementType,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
)
from keystone.models.tasks import TaskImportance
from keystone.specification.decomposer import IssueTree, IssueTreeMetadata, IssueTreeNode
from keystone.specification.priority_scorer import PriorityScore
from keystone.specification.task_generator import TaskGenerator
from keystone.specification.template_registry import TemplateRegistry


def _make_spec() -> ResearchSpec:
    return ResearchSpec(
        engagement_id="eng_test_001",
        client_id="client_test",
        title="Test Engagement",
        created_at=datetime.now(UTC),
        specification_version=1,
        decision_context="Investment committee deciding on allocation",
        surprising_finding="Market is actually shrinking",
        questions=[
            ResearchQuestion(question="Is the market growing?", is_primary=True),
            ResearchQuestion(question="Who are the competitors?", is_primary=False, parent_question="Is the market growing?"),
        ],
        output_format="markdown",
        non_goals=["Investment recommendation"],
        engagement_type=EngagementType.EVALUATIVE,
        day_1_hypothesis="Market is growing at 15% CAGR",
    )


def _make_tree() -> IssueTree:
    return IssueTree(
        root=IssueTreeNode(
            id="root", name="Root", description="Root",
            children=[
                IssueTreeNode(
                    id="branch_1", name="Market", description="Market analysis",
                    children=[
                        IssueTreeNode(id="branch_1.1", name="TAM", description="Total addressable market"),
                        IssueTreeNode(id="branch_1.2", name="Growth", description="Growth trajectory"),
                        IssueTreeNode(id="branch_1.3", name="Segmentation", description="Market segments"),
                    ],
                ),
                IssueTreeNode(
                    id="branch_2", name="Competition", description="Competitive landscape",
                    children=[
                        IssueTreeNode(id="branch_2.1", name="Key players", description="Top competitors"),
                        IssueTreeNode(id="branch_2.2", name="Moats", description="Competitive advantages"),
                        IssueTreeNode(id="branch_2.3", name="Pricing", description="Pricing dynamics"),
                    ],
                ),
                IssueTreeNode(
                    id="branch_3", name="Technology", description="Technology assessment",
                    children=[
                        IssueTreeNode(id="branch_3.1", name="Core tech", description="Core technology"),
                        IssueTreeNode(id="branch_3.2", name="Alternatives", description="Alternative approaches"),
                        IssueTreeNode(id="branch_3.3", name="IP", description="IP landscape"),
                        IssueTreeNode(id="branch_3.4", name="Maturity", description="Tech maturity"),
                    ],
                ),
            ],
        ),
        metadata=IssueTreeMetadata(
            depth=2, leaf_count=10,
            lenses_used=["financial", "operational", "market"],
            synthesis_rationale="Test.",
        ),
    )


def _make_priorities() -> list[PriorityScore]:
    leaves = ["branch_1.1", "branch_1.2", "branch_1.3",
              "branch_2.1", "branch_2.2", "branch_2.3",
              "branch_3.1", "branch_3.2", "branch_3.3", "branch_3.4"]
    return [
        PriorityScore(
            branch_id=b,
            decision_relevance=0.8,
            uncertainty_reduction=0.7,
            priority_score=0.56,
            reasoning="Test.",
        )
        for b in leaves
    ]


def _make_task_llm():
    """Create a mock LLM that returns a valid task decomposition."""
    async def llm(prompt: str) -> str:
        tasks = []
        for i in range(1, 11):
            tasks.append({
                "id": f"task_{i:03d}",
                "category": ["market_sizing", "competitive_landscape", "financial_analysis",
                             "technology_assessment", "regulatory", "strategic_positioning",
                             "market_sizing", "competitive_landscape", "technology_assessment",
                             "strategic_positioning"][i - 1],
                "type": "estimative" if i % 2 == 0 else "current",
                "target_decision_usefulness": 4,
                "description": f"Investigate topic {i}",
                "required_sources": ["industry_reports", "news"],
                "acceptance_criteria": [f"Criterion {i}a", f"Criterion {i}b"],
                "deliverable_destination": f"Section {i}",
                "priority": i,
                "anti_confirmatory_framing": f"Evaluate whether topic {i} is valid, including evidence both for and against",
                "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
                "assigned_model": "standard",
                "end_product": f"Analysis table for topic {i}",
                "dependencies": [f"task_{i - 1:03d}"] if i > 3 else [],
                "issue_tree_branch_id": f"branch_{(i - 1) // 3 + 1}.{(i - 1) % 3 + 1}" if i <= 9 else "branch_3.4",
                "custom_category": None,
            })
        return json.dumps({
            "decomposition_rationale": "Structured by issue tree branches.",
            "tasks": tasks,
        })
    return llm


class TestTaskGenerator:

    async def test_generates_10_plus_tasks(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        assert len(result.tasks) >= 10

    async def test_tasks_form_valid_dag(self):
        """TaskDecomposition validates DAG via Kahn's algorithm."""
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        # If this doesn't raise, the DAG is valid
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        assert result is not None

    async def test_each_task_has_anti_confirmatory_framing(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        for task in result.tasks:
            assert len(task.anti_confirmatory_framing) > 0
            lower = task.anti_confirmatory_framing.lower()
            assert not lower.startswith("find evidence for")
            assert not lower.startswith("prove that")

    async def test_each_task_has_end_product(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        for task in result.tasks:
            assert len(task.end_product) > 0

    async def test_each_task_has_3_to_5_tools(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        for task in result.tasks:
            assert 3 <= len(task.assigned_tools) <= 5

    async def test_dependencies_reference_valid_ids(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        task_ids = {t.id for t in result.tasks}
        for task in result.tasks:
            for dep in task.dependencies:
                assert dep in task_ids, f"task {task.id} depends on {dep} which doesn't exist"

    async def test_sets_primary_importance_for_first_task(self):
        llm = _make_task_llm()
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)
        result = await generator.generate(
            _make_tree(), _make_priorities(), EngagementType.EVALUATIVE, _make_spec()
        )
        assert result.tasks[0].importance == TaskImportance.PRIMARY

    async def test_uses_priority_scores_when_highest_scored_branch_is_listed_second(self):
        async def llm(prompt: str) -> str:
            return json.dumps(
                {
                    "decomposition_rationale": "Order is intentionally inverted.",
                    "tasks": [
                        {
                            "id": "task_low",
                            "category": "market_sizing",
                            "type": "current",
                            "target_decision_usefulness": 4,
                            "description": "Lower-scored branch listed first",
                            "required_sources": ["industry_reports"],
                            "acceptance_criteria": ["Criterion low"],
                            "deliverable_destination": "Section Low",
                            "priority": 1,
                            "anti_confirmatory_framing": "Evaluate whether the low branch holds, including evidence both for and against",
                            "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
                            "assigned_model": "standard",
                            "end_product": "Low branch analysis",
                            "dependencies": [],
                            "issue_tree_branch_id": "branch_1.1",
                            "custom_category": None,
                        },
                        {
                            "id": "task_high",
                            "category": "competitive_landscape",
                            "type": "estimative",
                            "target_decision_usefulness": 5,
                            "description": "Higher-scored branch listed second",
                            "required_sources": ["industry_reports"],
                            "acceptance_criteria": ["Criterion high"],
                            "deliverable_destination": "Section High",
                            "priority": 2,
                            "anti_confirmatory_framing": "Evaluate whether the high branch holds, including evidence both for and against",
                            "assigned_tools": ["exa_search", "brave_search", "edgar_filings"],
                            "assigned_model": "standard",
                            "end_product": "High branch analysis",
                            "dependencies": [],
                            "issue_tree_branch_id": "branch_2.1",
                            "custom_category": None,
                        },
                    ],
                }
            )

        priorities = [
            PriorityScore(
                branch_id="branch_1.1",
                decision_relevance=0.6,
                uncertainty_reduction=0.5,
                priority_score=0.3,
                reasoning="Lower score.",
            ),
            PriorityScore(
                branch_id="branch_2.1",
                decision_relevance=0.9,
                uncertainty_reduction=0.9,
                priority_score=0.81,
                reasoning="Higher score.",
            ),
        ]
        spec = _make_spec().model_copy(
            update={"effective_pipeline_profile": PipelineProfile.DEEP}
        )
        registry = TemplateRegistry()
        generator = TaskGenerator(llm, registry)

        result = await generator.generate(
            _make_tree(),
            priorities,
            EngagementType.EVALUATIVE,
            spec,
        )
        tasks_by_id = {task.id: task for task in result.tasks}

        assert result.tasks[0].id == "task_high"
        assert tasks_by_id["task_high"].priority == 1
        assert tasks_by_id["task_high"].importance == TaskImportance.PRIMARY
        assert tasks_by_id["task_low"].priority == 2
        assert tasks_by_id["task_low"].importance == TaskImportance.CRITICAL
