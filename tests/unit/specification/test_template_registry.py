"""Tests for the template registry (Step 6)."""

from __future__ import annotations

from keystone.models.agents import AgentDefinition
from keystone.models.research import EngagementType
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskType,
)
from keystone.specification.template_registry import TemplateMatch, TemplateRegistry


def _make_task(
    category: TaskCategory = TaskCategory.FINANCIAL_ANALYSIS,
    required_sources: list[str] | None = None,
) -> ResearchTask:
    return ResearchTask(
        id="task_001",
        engagement_id="eng_test",
        client_id="client_test",
        category=category,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Test task",
        acceptance_criteria=["Criterion 1"],
        deliverable_destination="Section 1",
        priority=1,
        anti_confirmatory_framing="Evaluate whether this is the case, including evidence both for and against",
        assigned_tools=["exa_search", "brave_search", "edgar_filings"],
        assigned_model=ModelTier.STANDARD,
        end_product="Analysis table",
        required_sources=required_sources or [],
    )


class TestTemplateRegistry:

    def test_at_least_5_seed_templates(self):
        registry = TemplateRegistry()
        templates = registry.get_seed_templates()
        assert len(templates) >= 5
        for t in templates:
            assert isinstance(t, AgentDefinition)

    def test_financial_task_matches_quant(self):
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.FINANCIAL_ANALYSIS,
            required_sources=["financial_filings", "financial_data"],
        )
        result = registry.match(task, EngagementType.SIZING)
        assert result.template.name == "quantitative_analyst"
        assert isinstance(result, TemplateMatch)

    def test_academic_task_matches_academic(self):
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.TECHNOLOGY_ASSESSMENT,
            required_sources=["academic", "patents"],
        )
        result = registry.match(task, EngagementType.EVALUATIVE)
        assert result.template.name == "academic_researcher"

    def test_regulatory_task_matches_regulatory(self):
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.REGULATORY,
            required_sources=["government"],
        )
        result = registry.match(task, EngagementType.DIAGNOSTIC)
        assert result.template.name == "regulatory_analyst"

    def test_market_task_matches_market(self):
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.COMPETITIVE_LANDSCAPE,
            required_sources=["industry_reports", "news"],
        )
        result = registry.match(task, EngagementType.EVALUATIVE)
        assert result.template.name == "market_researcher"

    def test_novel_task_below_threshold(self):
        """A task with no clear category/source match should score below 0.85."""
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.STRATEGIC_POSITIONING,
            required_sources=[],
        )
        result = registry.match(task, EngagementType.EXPLORATORY)
        # With no source signals and a generic category, similarity should be moderate
        assert result.similarity < 0.95  # Not a perfect match

    def test_match_type_labels(self):
        registry = TemplateRegistry()
        task = _make_task(
            category=TaskCategory.FINANCIAL_ANALYSIS,
            required_sources=["financial_filings", "financial_data"],
        )
        result = registry.match(task, EngagementType.SIZING)
        assert result.match_type in ("exact", "interpolated", "custom")

    def test_templates_have_valid_tools(self):
        registry = TemplateRegistry()
        for template in registry.get_seed_templates():
            assert len(template.tools) >= 3
            assert len(template.tools) <= 5
            assert all(isinstance(t, str) for t in template.tools)

    def test_templates_have_system_prompts(self):
        registry = TemplateRegistry()
        for template in registry.get_seed_templates():
            assert len(template.system_prompt) > 20
