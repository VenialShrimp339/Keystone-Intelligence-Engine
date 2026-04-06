"""Unit tests for research and task models (Component #1).

Tests written FIRST per build protocol. These will fail until
models are updated with Batch 2 fields.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskStatus,
    TaskType,
)


# ---------------------------------------------------------------------------
# Helpers: factory functions for valid model instances
# ---------------------------------------------------------------------------


def _make_task(
    *,
    id: str = "task_001",
    engagement_id: str = "eng_001",
    client_id: str = "client_001",
    category: TaskCategory = TaskCategory.MARKET_SIZING,
    type: TaskType = TaskType.ESTIMATIVE,
    target_decision_usefulness: int = 3,
    description: str = "Estimate TAM for AV sensor market",
    acceptance_criteria: list[str] | None = None,
    deliverable_destination: str = "Section 2: Market Landscape",
    priority: int = 1,
    anti_confirmatory_framing: str = (
        "Evaluate the size and growth trajectory, including evidence "
        "for both larger-than-expected and smaller-than-expected scenarios"
    ),
    assigned_tools: list[str] | None = None,
    end_product: str = "Market size table with TAM/SAM/SOM breakdown",
    dependencies: list[str] | None = None,
    issue_tree_branch_id: str | None = None,
    custom_category: str | None = None,
    **overrides,
) -> ResearchTask:
    return ResearchTask(
        id=id,
        engagement_id=engagement_id,
        client_id=client_id,
        category=category,
        type=type,
        target_decision_usefulness=target_decision_usefulness,
        description=description,
        acceptance_criteria=acceptance_criteria or ["Criteria 1", "Criteria 2"],
        deliverable_destination=deliverable_destination,
        priority=priority,
        anti_confirmatory_framing=anti_confirmatory_framing,
        assigned_tools=assigned_tools or ["exa_search", "brave_search", "edgar_filings"],
        end_product=end_product,
        dependencies=dependencies if dependencies is not None else [],
        issue_tree_branch_id=issue_tree_branch_id,
        custom_category=custom_category,
        **overrides,
    )


def _make_decomposition(
    tasks: list[ResearchTask] | None = None,
) -> TaskDecomposition:
    if tasks is None:
        tasks = [_make_task()]
    return TaskDecomposition(
        project="Test Project",
        engagement_id="eng_001",
        client_id="client_001",
        research_md_path="RESEARCH.md",
        specification_version=1,
        decomposition_rationale="Standard market research decomposition",
        tasks=tasks,
    )


# ---------------------------------------------------------------------------
# ResearchTask: Basic validation
# ---------------------------------------------------------------------------


class TestResearchTaskBasic:
    def test_valid_task_creation(self):
        task = _make_task()
        assert task.id == "task_001"
        assert task.passes is False
        assert task.status == TaskStatus.PENDING

    def test_required_fields(self):
        with pytest.raises(ValidationError):
            ResearchTask()  # type: ignore[call-arg]

    def test_target_decision_usefulness_range(self):
        _make_task(target_decision_usefulness=1)  # min
        _make_task(target_decision_usefulness=5)  # max
        with pytest.raises(ValidationError):
            _make_task(target_decision_usefulness=0)
        with pytest.raises(ValidationError):
            _make_task(target_decision_usefulness=6)


# ---------------------------------------------------------------------------
# Anti-confirmatory framing validator
# ---------------------------------------------------------------------------


class TestAntiConfirmatoryFraming:
    def test_valid_evaluative_framing(self):
        task = _make_task(
            anti_confirmatory_framing="Evaluate whether lidar is superior to camera-only"
        )
        assert "Evaluate" in task.anti_confirmatory_framing

    def test_rejects_find_evidence_for(self):
        with pytest.raises(ValidationError, match="(?i)anti.confirmatory"):
            _make_task(anti_confirmatory_framing="Find evidence for lidar superiority")

    def test_rejects_prove_that(self):
        with pytest.raises(ValidationError, match="(?i)anti.confirmatory"):
            _make_task(anti_confirmatory_framing="Prove that the market is growing")

    def test_rejects_confirm_that(self):
        with pytest.raises(ValidationError, match="(?i)anti.confirmatory"):
            _make_task(anti_confirmatory_framing="Confirm that Luminar leads the market")

    def test_rejects_show_that(self):
        with pytest.raises(ValidationError, match="(?i)anti.confirmatory"):
            _make_task(anti_confirmatory_framing="Show that margins are improving")

    def test_case_insensitive_rejection(self):
        with pytest.raises(ValidationError):
            _make_task(anti_confirmatory_framing="FIND EVIDENCE FOR the hypothesis")


# ---------------------------------------------------------------------------
# Tool count validator
# ---------------------------------------------------------------------------


class TestToolCountValidator:
    def test_valid_3_tools(self):
        task = _make_task(assigned_tools=["a", "b", "c"])
        assert len(task.assigned_tools) == 3

    def test_valid_5_tools(self):
        task = _make_task(assigned_tools=["a", "b", "c", "d", "e"])
        assert len(task.assigned_tools) == 5

    def test_rejects_2_tools(self):
        with pytest.raises(ValidationError, match="3-5"):
            _make_task(assigned_tools=["a", "b"])

    def test_rejects_6_tools(self):
        with pytest.raises(ValidationError, match="3-5"):
            _make_task(assigned_tools=["a", "b", "c", "d", "e", "f"])

    def test_rejects_1_tool(self):
        with pytest.raises(ValidationError, match="3-5"):
            _make_task(assigned_tools=["only_one"])


# ---------------------------------------------------------------------------
# passes / status invariant
# ---------------------------------------------------------------------------


class TestPassesStatusInvariant:
    def test_default_passes_false(self):
        task = _make_task()
        assert task.passes is False

    def test_passes_true_requires_passed_status(self):
        with pytest.raises(ValidationError, match="passes=True requires status=PASSED"):
            _make_task(passes=True, status=TaskStatus.IN_PROGRESS)

    def test_passes_true_with_passed_status_ok(self):
        task = _make_task(passes=True, status=TaskStatus.PASSED)
        assert task.passes is True
        assert task.status == TaskStatus.PASSED


# ---------------------------------------------------------------------------
# New Batch 2 fields on ResearchTask
# ---------------------------------------------------------------------------


class TestBatch2TaskFields:
    def test_end_product_required(self):
        """end_product is a required field per MASTER-SYNTHESIS Change #10."""
        task = _make_task(end_product="Comparison table with 8+ competitors")
        assert task.end_product == "Comparison table with 8+ competitors"

    def test_dependencies_default_empty(self):
        task = _make_task()
        assert task.dependencies == []

    def test_dependencies_with_values(self):
        task = _make_task(dependencies=["task_001", "task_002"])
        assert task.dependencies == ["task_001", "task_002"]

    def test_issue_tree_branch_id_optional(self):
        task = _make_task(issue_tree_branch_id=None)
        assert task.issue_tree_branch_id is None

    def test_issue_tree_branch_id_set(self):
        task = _make_task(issue_tree_branch_id="branch_1.2.3")
        assert task.issue_tree_branch_id == "branch_1.2.3"

    def test_custom_category_default_none(self):
        task = _make_task()
        assert task.custom_category is None

    def test_custom_category_override(self):
        """Directive 1: categories are templates, not hard constraints."""
        task = _make_task(
            category=TaskCategory.MARKET_SIZING,
            custom_category="auto_body_repair_demand",
        )
        assert task.custom_category == "auto_body_repair_demand"
        assert task.category == TaskCategory.MARKET_SIZING  # enum still present

    @property
    def effective_category(self):
        """custom_category takes precedence when set."""
        task = _make_task(custom_category="specialty_chemicals")
        assert task.effective_category == "specialty_chemicals"


# ---------------------------------------------------------------------------
# DAG validation in TaskDecomposition
# ---------------------------------------------------------------------------


class TestDAGValidation:
    def test_valid_linear_dag(self):
        """A -> B -> C is a valid DAG."""
        tasks = [
            _make_task(id="task_001", dependencies=[]),
            _make_task(id="task_002", dependencies=["task_001"]),
            _make_task(id="task_003", dependencies=["task_002"]),
        ]
        decomp = _make_decomposition(tasks=tasks)
        assert len(decomp.tasks) == 3

    def test_valid_diamond_dag(self):
        """A -> B, A -> C, B -> D, C -> D is a valid DAG."""
        tasks = [
            _make_task(id="task_001", dependencies=[]),
            _make_task(id="task_002", dependencies=["task_001"]),
            _make_task(id="task_003", dependencies=["task_001"]),
            _make_task(id="task_004", dependencies=["task_002", "task_003"]),
        ]
        decomp = _make_decomposition(tasks=tasks)
        assert len(decomp.tasks) == 4

    def test_no_dependencies_valid(self):
        """All independent tasks is a valid DAG."""
        tasks = [
            _make_task(id="task_001", dependencies=[]),
            _make_task(id="task_002", dependencies=[]),
            _make_task(id="task_003", dependencies=[]),
        ]
        decomp = _make_decomposition(tasks=tasks)
        assert len(decomp.tasks) == 3

    def test_cycle_detected_raises(self):
        """A -> B -> A is a cycle and must be rejected."""
        tasks = [
            _make_task(id="task_001", dependencies=["task_002"]),
            _make_task(id="task_002", dependencies=["task_001"]),
        ]
        with pytest.raises(ValidationError, match="[Cc]ycle"):
            _make_decomposition(tasks=tasks)

    def test_self_cycle_detected(self):
        """A task depending on itself is a cycle."""
        tasks = [
            _make_task(id="task_001", dependencies=["task_001"]),
        ]
        with pytest.raises(ValidationError, match="[Cc]ycle"):
            _make_decomposition(tasks=tasks)

    def test_three_node_cycle_detected(self):
        """A -> B -> C -> A is a cycle."""
        tasks = [
            _make_task(id="task_001", dependencies=["task_003"]),
            _make_task(id="task_002", dependencies=["task_001"]),
            _make_task(id="task_003", dependencies=["task_002"]),
        ]
        with pytest.raises(ValidationError, match="[Cc]ycle"):
            _make_decomposition(tasks=tasks)

    def test_invalid_dependency_reference(self):
        """A dependency referencing a non-existent task should fail."""
        tasks = [
            _make_task(id="task_001", dependencies=["task_999"]),
        ]
        with pytest.raises(ValidationError, match="[Ii]nvalid.*depend"):
            _make_decomposition(tasks=tasks)


# ---------------------------------------------------------------------------
# ResearchSpec Batch 2 fields
# ---------------------------------------------------------------------------


class TestResearchSpecBatch2:
    def _make_spec(self, **overrides):
        from keystone.models.research import (
            EngagementType,
            ResearchQuestion,
            ResearchSpec,
        )

        defaults = dict(
            engagement_id="eng_001",
            client_id="client_001",
            title="Test Engagement",
            created_at=datetime.now(tz=timezone.utc),
            specification_version=1,
            decision_context="Evaluate competitive position",
            surprising_finding="Company X has no real moat",
            questions=[
                ResearchQuestion(
                    question="What is Company X's competitive position?",
                    is_primary=True,
                )
            ],
            output_format="markdown",
            non_goals=["Political positioning"],
            engagement_type=EngagementType.EVALUATIVE,
        )
        defaults.update(overrides)
        return ResearchSpec(**defaults)

    def test_engagement_type_required(self):
        from keystone.models.research import EngagementType

        spec = self._make_spec(engagement_type=EngagementType.SIZING)
        assert spec.engagement_type == EngagementType.SIZING

    def test_all_engagement_types_valid(self):
        from keystone.models.research import EngagementType

        for etype in EngagementType:
            spec = self._make_spec(engagement_type=etype)
            assert spec.engagement_type == etype

    def test_day_1_hypothesis_optional(self):
        spec = self._make_spec()
        assert spec.day_1_hypothesis is None

    def test_day_1_hypothesis_set(self):
        spec = self._make_spec(
            day_1_hypothesis="Luminar's technology lead is sustainable through 2028"
        )
        assert "Luminar" in spec.day_1_hypothesis

    def test_invalid_engagement_type_rejected(self):
        with pytest.raises(ValidationError):
            self._make_spec(engagement_type="invalid_type")


# ---------------------------------------------------------------------------
# EngagementSpec: issue_tree field
# ---------------------------------------------------------------------------


class TestEngagementSpecIssueTree:
    def _make_engagement_spec(self, issue_tree=None):
        from keystone.models.research import (
            EngagementSpec,
            EngagementType,
            ResearchQuestion,
            ResearchSpec,
            ValidationReport,
        )

        spec = ResearchSpec(
            engagement_id="eng_001",
            client_id="client_001",
            title="Test",
            created_at=datetime.now(tz=timezone.utc),
            specification_version=1,
            decision_context="Test context",
            surprising_finding="Test surprise",
            questions=[
                ResearchQuestion(question="Primary?", is_primary=True)
            ],
            output_format="markdown",
            non_goals=["None"],
            engagement_type=EngagementType.EVALUATIVE,
        )
        decomp = _make_decomposition()
        report = ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        )
        return EngagementSpec(
            research_spec=spec,
            task_decomposition=decomp,
            validation_report=report,
            issue_tree=issue_tree,
        )

    def test_issue_tree_default_none(self):
        es = self._make_engagement_spec()
        assert es.issue_tree is None

    def test_issue_tree_with_data(self):
        tree = {
            "root": "Competitive Position",
            "branches": [
                {"id": "1", "label": "Market Size", "children": []},
                {"id": "2", "label": "Competitive Landscape", "children": []},
            ],
        }
        es = self._make_engagement_spec(issue_tree=tree)
        assert es.issue_tree["root"] == "Competitive Position"
        assert len(es.issue_tree["branches"]) == 2
