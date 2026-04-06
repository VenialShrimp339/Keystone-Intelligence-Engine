"""Integration tests for the Evaluator orchestrator."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from keystone.contracts import EvaluatorContract
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer2_citation_gate import DOIVerificationResult
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.events import (
    CitationGateResult,
    DeterministicCheckPassed,
    EvaluationComplete,
    RubricDimensionScored,
)
from keystone.models.citations import Citation, CitationManifest, SourceType
from keystone.models.evaluation import EvaluationIntensity, RubricDimension, SprintContract
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    ResearchQuestion,
    ResearchSpec,
    ValidationReport,
)
from keystone.models.tasks import (
    ResearchTask,
    TaskCategory,
    TaskDecomposition,
    TaskType,
)

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "evaluator"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _cit(cid: str, doi: str | None = None) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLT-001",
        url=f"https://example.com/{cid}",
        doi=doi,
        title=f"Source {cid}",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime.now(UTC),
    )


def _manifest(*citations: Citation) -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        citations=list(citations),
    )


def _task() -> ResearchTask:
    return ResearchTask(
        id="task_001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        category=TaskCategory.COMPETITIVE_LANDSCAPE,
        type=TaskType.CURRENT,
        target_decision_usefulness=4,
        description="Analyze competitive dynamics",
        acceptance_criteria=["Identify 5+ competitors"],
        deliverable_destination="Section 2",
        priority=1,
        anti_confirmatory_framing="Evaluate whether market is consolidating or fragmenting",
        assigned_tools=["web_search", "sec_filings", "news_api"],
        end_product="comparison table",
        dependencies=[],
    )


def _contract() -> SprintContract:
    return SprintContract(
        section_id="section_task_001",
        engagement_id="ENG-001",
        client_id="CLT-001",
        task_id="task_001",
        section_title="Competitive Landscape",
        acceptance_criteria=["Identify 5+ competitors", "Compare pricing"],
    )


def _spec() -> EngagementSpec:
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id="ENG-001",
            client_id="CLT-001",
            title="Telematics Market Analysis",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Evaluating market entry",
            surprising_finding="Telematics adoption plateau",
            questions=[ResearchQuestion(question="Competitive landscape?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.EVALUATIVE,
        ),
        task_decomposition=TaskDecomposition(
            project="Telematics",
            engagement_id="ENG-001",
            client_id="CLT-001",
            research_md_path="/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="MECE",
            tasks=[_task()],
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _make_mock_llm(
    tier1_scores: dict[RubricDimension, float] | None = None,
    tier2_scores: dict[RubricDimension, float] | None = None,
    gestalt: float = 0.0,
):
    """Create a mock LLM for the full evaluator pipeline."""
    from keystone.evaluator.rubric_config import TIER_1_DIMENSIONS, TIER_2_DIMENSIONS

    t1 = tier1_scores or {d: 70.0 for d in TIER_1_DIMENSIONS}
    t2 = tier2_scores or {d: 65.0 for d in TIER_2_DIMENSIONS}
    all_scores = {**t1, **t2}

    async def mock_llm(prompt: str) -> str:
        lower = prompt.lower()
        # Gestalt
        if "gestalt overlay" in lower:
            return json.dumps({"adjustment": gestalt, "rationale": "test"})
        # Fact decomposition
        if "fact decomposition" in lower:
            return json.dumps([
                {"claim": "test fact", "status": "SUPPORTED", "citation_id": "CIT-001", "reasoning": "ok"},
            ])
        # Numerical consistency
        if "numerical consistency" in lower:
            return json.dumps({"numerical_claims": [], "inconsistencies": []})
        # Dimension prompts
        for dim in RubricDimension:
            header = f"# {dim.value.replace('_', ' ')} evaluation"
            if header in lower:
                return json.dumps({
                    "score": all_scores.get(dim, 60),
                    "feedback": f"Feedback for {dim.value}",
                    "sub_criteria_notes": [f"note for {dim.value}"],
                    "slop_detected": False,
                    "slop_details": None,
                })
        return json.dumps({"score": 60, "feedback": "fallback"})

    return mock_llm


class MockDOIVerifier:
    def __init__(self, results: dict[str, bool]) -> None:
        self._results = results

    async def verify(self, doi: str) -> DOIVerificationResult:
        return DOIVerificationResult(exists=self._results.get(doi, True))


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_clean_input_passes(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Clean research text.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            result = await evaluator.get_result()
            assert result.passed is True
            assert 60 <= result.overall_score <= 85

    @pytest.mark.asyncio
    async def test_fabricated_citation_rejects(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({"10.9999/fake.1": False})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001", doi="10.9999/fake.1"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Text with fabricated citation.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            result = await evaluator.get_result()
            assert result.passed is False
            assert result.layer3_results is None
            assert "fabricated" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_tier1_failure_rejects(self) -> None:
        llm = _make_mock_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 35.0,
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 60.0,
                RubricDimension.NARRATIVE_COHERENCE: 50.0,
            }
        )
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Text with weak intent alignment.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            result = await evaluator.get_result()
            assert result.passed is False
            assert result.overall_score == 0.0

    @pytest.mark.asyncio
    async def test_events_in_correct_order(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Test text.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            types = [type(e) for e in events]
            assert types[0] is DeterministicCheckPassed
            assert types[1] is CitationGateResult
            # Then RubricDimensionScored events
            rubric_events = [e for e in events if isinstance(e, RubricDimensionScored)]
            assert len(rubric_events) == 10
            assert types[-1] is EvaluationComplete


# ---------------------------------------------------------------------------
# Intensity tests
# ---------------------------------------------------------------------------


class TestIntensity:
    @pytest.mark.asyncio
    async def test_light_touch_skips_layer3(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=llm, doi_verifier=verifier,
            intensity=EvaluationIntensity.LIGHT_TOUCH,
        )
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Test text.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            rubric_events = [e for e in events if isinstance(e, RubricDimensionScored)]
            assert len(rubric_events) == 0
            result = await evaluator.get_result()
            assert result.layer3_results is None
            assert "LIGHT_TOUCH" in result.feedback

    @pytest.mark.asyncio
    async def test_deep_same_as_standard_phase1(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=llm, doi_verifier=verifier,
            intensity=EvaluationIntensity.DEEP,
        )
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Test text.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

            rubric_events = [e for e in events if isinstance(e, RubricDimensionScored)]
            assert len(rubric_events) == 10  # full stack runs


# ---------------------------------------------------------------------------
# Contract compliance tests
# ---------------------------------------------------------------------------


class TestContractCompliance:
    def test_protocol_satisfied(self) -> None:
        llm = _make_mock_llm()
        evaluator = Evaluator(llm=llm)
        assert isinstance(evaluator, EvaluatorContract)

    @pytest.mark.asyncio
    async def test_get_result_before_evaluate_raises(self) -> None:
        llm = _make_mock_llm()
        evaluator = Evaluator(llm=llm)
        with pytest.raises(RuntimeError, match="evaluate.*must be called"):
            await evaluator.get_result()


# ---------------------------------------------------------------------------
# Feedback quality tests
# ---------------------------------------------------------------------------


class TestFeedbackQuality:
    @pytest.mark.asyncio
    async def test_failed_feedback_mentions_reason(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({"10.9999/fake": False})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001", doi="10.9999/fake"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={},
        ):
            async for _ in evaluator.evaluate(
                "Text.", _contract(), _task(), manifest, _spec()
            ):
                pass
            result = await evaluator.get_result()
            assert "CIT-001" in result.feedback
            assert len(result.feedback) > 20

    @pytest.mark.asyncio
    async def test_passing_feedback_has_dimension_info(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            async for _ in evaluator.evaluate(
                "Test.", _contract(), _task(), manifest, _spec()
            ):
                pass
            result = await evaluator.get_result()
            assert result.feedback
            assert len(result.feedback) > 20


# ---------------------------------------------------------------------------
# Profile variance tests
# ---------------------------------------------------------------------------


class TestProfileVariance:
    @pytest.mark.asyncio
    async def test_different_profiles_different_weights(self) -> None:
        """ESTIMATIVE and DEFAULT produce different weight distributions."""
        from keystone.evaluator.rubric_config import get_profile_weights

        default_w = get_profile_weights(EvaluationProfile.DEFAULT)
        est_w = get_profile_weights(EvaluationProfile.ESTIMATIVE)
        # At least one dimension differs
        diffs = [
            dim for dim in RubricDimension
            if abs(default_w[dim] - est_w[dim]) > 0.001
        ]
        assert len(diffs) >= 1
