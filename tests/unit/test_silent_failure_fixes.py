"""Phase 3 silent-failure coverage.

Failed Layer 1 evaluation no longer looks like "0 facts to check".
Failed Layer 3 rubric scoring no longer looks like "scored zero".
Sprint contract fallback no longer happens silently — the task ID is
surfaced so the orchestrator can emit a WARN governance flag.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.models.citations import Citation, CitationManifest, SourceType
from keystone.models.evaluation import (
    EvaluationIntensity,
    Layer1Result,
    Layer3Result,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    EvaluationProfileName,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ModelTier,
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskImportance,
    TaskType,
)
from keystone.structuring.content_structuring import ContentStructurer


# ---- Fix E: Layer1Result infrastructure_failure --------------------------


class TestLayer1InfrastructureFailure:
    def test_field_default_is_false(self):
        """Happy-path Layer 1 results keep ``infrastructure_failure=False``."""
        r = Layer1Result(facts_verified=3, facts_failed=1)
        assert r.infrastructure_failure is False

    def test_flag_surfaces_through_model_dump(self):
        r = Layer1Result(facts_verified=0, facts_failed=0, infrastructure_failure=True)
        assert r.model_dump()["infrastructure_failure"] is True

    async def test_evaluator_marks_flag_when_layer1_throws(self):
        """When Layer 1 raises, Evaluator produces a result with infrastructure_failure=True."""

        async def raising_llm(_prompt: str) -> str:
            raise RuntimeError("simulated LLM crash")

        extraction_llm = raising_llm
        # Rubric LLM must succeed so we reach the Layer1-failure branch
        # without the whole evaluate() call blowing up.
        rubric_llm: AsyncMock = AsyncMock(return_value='{"score": 50, "feedback": "ok"}')

        ev = Evaluator(
            llm=rubric_llm,
            profile=EvaluationProfile.DEFAULT,
            intensity=EvaluationIntensity.LIGHT_TOUCH,
            extraction_llm=extraction_llm,
        )

        task, spec, contract, manifest = _build_minimal_fixtures()

        # LIGHT_TOUCH runs Layer 1 + Layer 2 only, so the failure shows
        # up on the result without the test needing to mock the rubric path.
        async for _ in ev.evaluate("short output", contract, task, manifest, spec):
            pass
        result = await ev.get_result()

        assert result.layer1_results.infrastructure_failure is True
        assert result.layer1_results.facts_verified == 0


# ---- Fix F: Layer3Result infrastructure_failure --------------------------


class TestLayer3InfrastructureFailure:
    def test_field_default_is_false(self):
        r = Layer3Result(
            dimension_scores=[],
            weighted_total=50.0,
            gestalt_adjustment=0.0,
            final_score=50.0,
        )
        assert r.infrastructure_failure is False

    def test_flag_surfaces_through_model_dump(self):
        r = Layer3Result(
            dimension_scores=[],
            weighted_total=0.0,
            gestalt_adjustment=0.0,
            final_score=0.0,
            infrastructure_failure=True,
        )
        assert r.model_dump()["infrastructure_failure"] is True

    async def test_evaluator_marks_flag_when_three_pass_throws(self):
        """Layer 3 failure in single-judge mode sets the new flag."""

        async def raising_llm(_prompt: str) -> str:
            raise RuntimeError("simulated rubric crash")

        ev = Evaluator(
            llm=raising_llm,
            profile=EvaluationProfile.DEFAULT,
            intensity=EvaluationIntensity.STANDARD,
        )

        task, spec, contract, manifest = _build_minimal_fixtures()
        # Evaluator.evaluate needs Layer 1 + Layer 2 to pass first. Layer 2
        # is empty (no citations) so it passes by default. Layer 1 will
        # fail because ``raising_llm`` raises; but the flag we are
        # asserting on is Layer 3, so we bypass by using STANDARD intensity
        # and the fact that the internal exception handling catches
        # per-layer failures in isolation.
        async for _ in ev.evaluate("short output", contract, task, manifest, spec):
            pass
        result = await ev.get_result()

        assert result.layer3_results is not None
        assert result.layer3_results.infrastructure_failure is True
        assert result.layer3_results.final_score == 0.0


# ---- Fix G: Sprint contract fallback tracking ---------------------------


class TestSprintContractFallbackTracking:
    async def test_happy_path_leaves_set_empty(self):
        """When the generator succeeds, no fallback task is recorded."""

        class _OkGenerator:
            async def generate(self, task, spec):
                return SprintContract(
                    section_id=f"section_{task.id}",
                    engagement_id=task.engagement_id,
                    client_id=task.client_id,
                    task_id=task.id,
                    section_title="Title",
                    acceptance_criteria=["criterion"],
                    dimension_emphasis={},
                    mandatory_elements=[],
                    anti_patterns=[],
                )

        task, spec, _contract, _manifest = _build_minimal_fixtures()
        structurer = ContentStructurer(sprint_contract_generator=_OkGenerator())

        from keystone.models.confidence import ConfidenceMap

        confidence_map = ConfidenceMap(
            engagement_id=spec.research_spec.engagement_id,
            client_id=spec.research_spec.client_id,
        )

        async for _ in structurer.structure(
            confidence_map,
            [],
            spec,
            [task],
            spec.research_spec.engagement_id,
            spec.research_spec.client_id,
        ):
            pass

        assert structurer.get_fallback_task_ids() == set()

    async def test_generator_failure_records_task(self):
        """When the generator raises, the task ID is added to the fallback set."""

        class _FailingGenerator:
            async def generate(self, task, spec):
                raise RuntimeError("simulated sprint contract LLM crash")

        task, spec, _contract, _manifest = _build_minimal_fixtures()
        structurer = ContentStructurer(sprint_contract_generator=_FailingGenerator())

        from keystone.models.confidence import ConfidenceMap

        confidence_map = ConfidenceMap(
            engagement_id=spec.research_spec.engagement_id,
            client_id=spec.research_spec.client_id,
        )

        async for _ in structurer.structure(
            confidence_map,
            [],
            spec,
            [task],
            spec.research_spec.engagement_id,
            spec.research_spec.client_id,
        ):
            pass

        # The task made it through L2 via the fallback contract, and the
        # orchestrator can now see that the fallback fired.
        assert task.id in structurer.get_fallback_task_ids()
        contract = await structurer.get_sprint_contract(task.id)
        assert contract is not None
        # Fallback contract copies acceptance_criteria verbatim from the task.
        assert list(contract.acceptance_criteria) == list(task.acceptance_criteria)


# ---- Fixtures ------------------------------------------------------------


def _build_minimal_fixtures() -> tuple[
    ResearchTask, EngagementSpec, SprintContract, CitationManifest
]:
    eid = "eng_test_0001"
    cid = "client_test"

    task = ResearchTask(
        id="task_001",
        engagement_id=eid,
        client_id=cid,
        category=TaskCategory.STRATEGIC_POSITIONING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description="Probe task",
        required_sources=[],
        acceptance_criteria=["criterion"],
        deliverable_destination="Section TBD",
        priority=1,
        importance=TaskImportance.PRIMARY,
        anti_confirmatory_framing="look for both sides",
        assigned_tools=["exa_search", "brave_search", "paper_search"],
        assigned_model=ModelTier.STANDARD,
        end_product="analysis",
        dependencies=[],
    )

    research_spec = ResearchSpec(
        engagement_id=eid,
        client_id=cid,
        title="Test engagement",
        created_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        specification_version=1,
        decision_context="decide something",
        surprising_finding="something surprising",
        questions=[ResearchQuestion(question="probe?", is_primary=True)],
        methodology=[],
        source_requirements=[],
        output_format="markdown",
        non_goals=[],
        engagement_type=EngagementType.EVALUATIVE,
        day_1_hypothesis="hypothesis",
        recommended_pipeline_profile=PipelineProfile.STANDARD,
        effective_pipeline_profile=PipelineProfile.STANDARD,
        effective_evaluation_profile=EvaluationProfileName.DEFAULT,
        profile_source="test",
    )

    task_decomp = TaskDecomposition(
        project="Test engagement",
        engagement_id=eid,
        client_id=cid,
        research_md_path=f"engagements/{eid}/RESEARCH.md",
        specification_version=1,
        decomposition_rationale="test",
        tasks=[task],
    )

    validation_report = ValidationReport(
        intent_clear=True,
        scope_valid=True,
        within_frontier=True,
        quality_threshold_met=True,
    )
    spec = EngagementSpec(
        research_spec=research_spec,
        task_decomposition=task_decomp,
        validation_report=validation_report,
        issue_tree={},
    )

    contract = SprintContract(
        section_id="section_task_001",
        engagement_id=eid,
        client_id=cid,
        task_id="task_001",
        section_title="Section",
        acceptance_criteria=["criterion"],
        dimension_emphasis={},
        mandatory_elements=[],
        anti_patterns=[],
    )

    manifest = CitationManifest(
        manifest_id="man_test_0001",
        engagement_id=eid,
        client_id=cid,
        citations=[],
    )

    return task, spec, contract, manifest
