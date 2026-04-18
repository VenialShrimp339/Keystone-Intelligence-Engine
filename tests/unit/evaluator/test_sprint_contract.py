"""Tests for sprint contract generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.models.evaluation import RubricDimension
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)


def _make_task() -> ResearchTask:
    return ResearchTask(
        id="task_001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        category=TaskCategory.COMPETITIVE_LANDSCAPE,
        type=TaskType.CURRENT,
        target_decision_usefulness=4,
        description="Analyze competitive dynamics in auto insurance telematics market",
        required_sources=["industry_reports", "financial_data"],
        acceptance_criteria=[
            "Identify at least 5 major players",
            "Compare pricing models",
        ],
        deliverable_destination="Section 2: Competitive Landscape",
        priority=1,
        anti_confirmatory_framing="Evaluate whether telematics adoption is accelerating or plateauing, including evidence for both directions",
        assigned_tools=["web_search", "sec_filings", "news_api"],
        end_product="comparison table with 8+ competitors and market share estimates",
        dependencies=[],
    )


def _make_spec() -> EngagementSpec:
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id="ENG-001",
            client_id="CLT-001",
            title="Auto Insurance Telematics Market Analysis",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Client considering entry into telematics-based auto insurance",
            surprising_finding="Evidence that telematics adoption has plateaued despite investment",
            questions=[
                ResearchQuestion(question="What is the competitive landscape?", is_primary=True),
            ],
            output_format="markdown",
            engagement_type=EngagementType.EVALUATIVE,
        ),
        task_decomposition=TaskDecomposition(
            project="Auto Insurance Telematics",
            engagement_id="ENG-001",
            client_id="CLT-001",
            research_md_path="/engagements/ENG-001/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="MECE decomposition of competitive landscape",
            tasks=[_make_task()],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


class TestSprintContractGeneration:
    @pytest.mark.asyncio
    async def test_generates_non_empty_criteria(self) -> None:
        mock_response = json.dumps(
            {
                "acceptance_criteria": [
                    "Identify at least 5 competitors with market share data",
                    "Include pricing comparison across at least 3 models",
                ],
                "mandatory_elements": ["competitive comparison table"],
                "anti_patterns": ["Generic SWOT without company-specific data"],
                "dimension_emphasis": {"analytical_depth": 1.5, "source_quality": 1.2},
            }
        )

        async def mock_llm(prompt: str) -> str:
            return mock_response

        gen = SprintContractGenerator(llm=mock_llm)
        contract = await gen.generate(_make_task(), _make_spec())
        assert len(contract.acceptance_criteria) >= 2
        assert contract.task_id == "task_001"
        assert contract.engagement_id == "ENG-001"

    @pytest.mark.asyncio
    async def test_dimension_emphasis_valid_enums(self) -> None:
        mock_response = json.dumps(
            {
                "acceptance_criteria": ["test"],
                "mandatory_elements": [],
                "anti_patterns": ["generic advice"],
                "dimension_emphasis": {"analytical_depth": 1.5, "actionability": 1.3},
            }
        )

        async def mock_llm(prompt: str) -> str:
            return mock_response

        gen = SprintContractGenerator(llm=mock_llm)
        contract = await gen.generate(_make_task(), _make_spec())
        for dim in contract.dimension_emphasis:
            assert isinstance(dim, RubricDimension)

    @pytest.mark.asyncio
    async def test_anti_patterns_populated(self) -> None:
        mock_response = json.dumps(
            {
                "acceptance_criteria": ["test"],
                "mandatory_elements": [],
                "anti_patterns": ["Industry-generic SWOT", "No competitor names"],
                "dimension_emphasis": {},
            }
        )

        async def mock_llm(prompt: str) -> str:
            return mock_response

        gen = SprintContractGenerator(llm=mock_llm)
        contract = await gen.generate(_make_task(), _make_spec())
        assert len(contract.anti_patterns) >= 1

    @pytest.mark.asyncio
    async def test_contract_references_correct_ids(self) -> None:
        mock_response = json.dumps(
            {
                "acceptance_criteria": ["test"],
                "mandatory_elements": [],
                "anti_patterns": [],
                "dimension_emphasis": {},
            }
        )

        async def mock_llm(prompt: str) -> str:
            return mock_response

        gen = SprintContractGenerator(llm=mock_llm)
        contract = await gen.generate(_make_task(), _make_spec())
        assert contract.task_id == "task_001"
        assert contract.engagement_id == "ENG-001"
        assert contract.client_id == "CLT-001"

    @pytest.mark.asyncio
    async def test_malformed_json_raises_explicit_error(self) -> None:
        async def mock_llm(prompt: str) -> str:
            return "{not valid json"

        gen = SprintContractGenerator(llm=mock_llm)

        with pytest.raises(
            RuntimeError,
            match="Failed to parse sprint contract JSON for task task_001",
        ):
            await gen.generate(_make_task(), _make_spec())
