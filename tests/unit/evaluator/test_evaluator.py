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
    DissenterVetoTriggered,
    EnsembleEvaluationComplete,
    EnsembleJudgeScored,
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
            return json.dumps(
                [
                    {
                        "claim": "test fact",
                        "status": "SUPPORTED",
                        "citation_id": "CIT-001",
                        "reasoning": "ok",
                    },
                ]
            )
        # Numerical consistency
        if "numerical consistency" in lower:
            return json.dumps({"numerical_claims": [], "inconsistencies": []})
        # Dimension prompts
        for dim in RubricDimension:
            header = f"# {dim.value.replace('_', ' ')} evaluation"
            if header in lower:
                return json.dumps(
                    {
                        "score": all_scores.get(dim, 60),
                        "feedback": f"Feedback for {dim.value}",
                        "sub_criteria_notes": [f"note for {dim.value}"],
                    }
                )
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
# Layer 4 integration
# ---------------------------------------------------------------------------


class TestProcessTrajectoryIntegration:
    """``ProcessTrajectoryScored`` must fire when a ProcessContext is supplied
    and Layers 1-3 pass. Regression guard against L4 silently dropping out.
    """

    @pytest.mark.asyncio
    async def test_process_trajectory_scored_event_emitted(self) -> None:
        from keystone.evaluator.layer4_trajectory import ProcessContext
        from keystone.events import ProcessTrajectoryScored
        from keystone.models.agents import (
            AgentDefinition,
            AgentInstance,
            AgentRole,
            ResearchAgentType,
        )
        from keystone.models.tasks import ModelTier

        # Reuse the Layer4 test helpers' event shape to build a
        # realistic process trail.
        from tests.unit.evaluator.test_layer4_trajectory import (  # type: ignore[import-not-found]
            _good_process_events,
        )

        llm = _make_mock_llm()  # includes a rubric + L4 LLM response
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))

        agent = AgentInstance(
            agent_id="agent_eval_l4",
            engagement_id="ENG-001",
            client_id="CLT-001",
            definition=AgentDefinition(
                name="integration_agent",
                description="Integration agent for L4 test",
                role=AgentRole.RESEARCH,
                model=ModelTier.STANDARD,
                tools=["web_search", "sec_filings", "news_api"],
                research_type=ResearchAgentType.QUANTITATIVE,
            ),
            working_dir="/tmp/keystone/integration",
            task_ids=["task_001"],
        )
        context = ProcessContext(
            agent_id=agent.agent_id,
            task=_task(),
            agent=agent,
            events=_good_process_events(agent.agent_id),
            issue_tree={
                "root": {
                    "id": "root",
                    "name": "Root",
                    "children": [
                        {"id": "leaf_1", "name": "Leaf 1"},
                    ],
                }
            },
        )

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Clean research text.",
                _contract(),
                _task(),
                manifest,
                _spec(),
                process_context=context,
            ):
                events.append(event)

        l4_events = [e for e in events if isinstance(e, ProcessTrajectoryScored)]
        assert len(l4_events) == 1, (
            "ProcessTrajectoryScored must be emitted when L4 runs; "
            f"saw event types: {[type(e).__name__ for e in events]}"
        )
        l4 = l4_events[0]
        assert l4.layer == "L4"
        assert l4.task_id == "task_001"
        assert 0.0 <= l4.process_quality_score <= 100.0
        assert 0.0 <= l4.qualitative_score <= 100.0
        assert l4.source_count >= 1
        assert l4.round_count >= 1
        assert 0.0 <= l4.tool_utilization <= 1.0
        assert l4.flag_count >= 0

        # The overall EvaluationComplete must carry a composite score
        # that incorporates L4 (strictly <= L3 alone).
        result = await evaluator.get_result()
        assert result.layer4_results is not None
        # L4 never lifts the score above L3 alone (per docstring
        # guarantee). With matching scores the geometric mean equals
        # the L3 score; with divergent scores it drops below.
        if result.layer3_results is not None:
            assert result.overall_score <= result.layer3_results.final_score + 0.01

    @pytest.mark.asyncio
    async def test_process_trajectory_event_omitted_without_process_context(self) -> None:
        from keystone.events import ProcessTrajectoryScored

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
                "Clean research text.",
                _contract(),
                _task(),
                manifest,
                _spec(),
                # process_context omitted -> L4 must be skipped entirely
            ):
                events.append(event)

        l4_events = [e for e in events if isinstance(e, ProcessTrajectoryScored)]
        assert l4_events == []
        result = await evaluator.get_result()
        assert result.layer4_results is None


# ---------------------------------------------------------------------------
# Intensity tests
# ---------------------------------------------------------------------------


class TestIntensity:
    @pytest.mark.asyncio
    async def test_light_touch_skips_layer3(self) -> None:
        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=llm,
            doi_verifier=verifier,
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
            llm=llm,
            doi_verifier=verifier,
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
            async for _ in evaluator.evaluate("Text.", _contract(), _task(), manifest, _spec()):
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
            async for _ in evaluator.evaluate("Test.", _contract(), _task(), manifest, _spec()):
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
        diffs = [dim for dim in RubricDimension if abs(default_w[dim] - est_w[dim]) > 0.001]
        assert len(diffs) >= 1

    @pytest.mark.asyncio
    async def test_rubric_events_emit_adjusted_weights(self) -> None:
        from keystone.evaluator.rubric_config import get_profile_weights

        llm = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(llm=llm, doi_verifier=verifier)
        manifest = _manifest(_cit("CIT-001"))
        contract = _contract().model_copy(
            update={
                "dimension_emphasis": {
                    RubricDimension.ANALYTICAL_DEPTH: 1.5,
                }
            }
        )

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Test text.", contract, _task(), manifest, _spec()
            ):
                events.append(event)

        rubric_events = [e for e in events if isinstance(e, RubricDimensionScored)]
        weights_by_dimension = {
            RubricDimension(event.dimension): event.weight for event in rubric_events
        }
        base_weights = get_profile_weights(EvaluationProfile.DEFAULT)

        assert (
            weights_by_dimension[RubricDimension.ANALYTICAL_DEPTH]
            > base_weights[RubricDimension.ANALYTICAL_DEPTH]
        )
        assert (
            weights_by_dimension[RubricDimension.SOURCE_QUALITY]
            < base_weights[RubricDimension.SOURCE_QUALITY]
        )


# ---------------------------------------------------------------------------
# Layer 5 ensemble path: end-to-end behavior through Evaluator
# ---------------------------------------------------------------------------


class TestEnsembleEvaluatorIntegration:
    """Tests that drive :class:`Evaluator` with ``ensemble_llms`` set, so the
    event stream, composite score blending, and weight plumbing are exercised
    end-to-end rather than only inside :class:`EnsembleL3Evaluator`.
    """

    @pytest.mark.asyncio
    async def test_event_order_emits_judge_then_complete(self) -> None:
        """Confirm the L5 event sequence: per-judge scored, then aggregate complete.

        Locks in the ordering documented in contracts.py::EvaluatorContract.
        """
        llm = _make_mock_llm()
        judge_a = _make_mock_llm()
        judge_b = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=llm,
            doi_verifier=verifier,
            ensemble_llms=[("flagship_a", judge_a), ("flagship_b", judge_b)],
        )
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

        judge_events = [e for e in events if isinstance(e, EnsembleJudgeScored)]
        complete_events = [e for e in events if isinstance(e, EnsembleEvaluationComplete)]
        assert len(judge_events) == 2
        assert {je.judge_id for je in judge_events} == {"flagship_a", "flagship_b"}
        assert len(complete_events) == 1

        # Judge events land before the aggregate-complete event, which in turn
        # lands before EvaluationComplete.
        judge_idxs = [i for i, e in enumerate(events) if isinstance(e, EnsembleJudgeScored)]
        complete_idx = next(
            i for i, e in enumerate(events) if isinstance(e, EnsembleEvaluationComplete)
        )
        eval_complete_idx = next(
            i for i, e in enumerate(events) if isinstance(e, EvaluationComplete)
        )
        assert max(judge_idxs) < complete_idx < eval_complete_idx

    @pytest.mark.asyncio
    async def test_dissenter_veto_emits_event_and_rejects_output(self) -> None:
        """A Tier 1 dissenter triggers a DissenterVetoTriggered event and a failed pass."""
        llm = _make_mock_llm()
        dissenter = _make_mock_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 35.0,
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 70.0,
                RubricDimension.NARRATIVE_COHERENCE: 70.0,
            }
        )
        majority = _make_mock_llm(
            tier1_scores={d: 85.0 for d in RubricDimension if d in _tier1_dims()}
        )
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=llm,
            doi_verifier=verifier,
            ensemble_llms=[
                ("flagship_a", dissenter),
                ("flagship_b", majority),
            ],
        )
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Output under veto.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

        result = await evaluator.get_result()
        assert result.passed is False
        assert result.overall_score == pytest.approx(0.0, abs=0.1)
        assert result.layer5_results is not None
        assert result.layer5_results.tier1_vetoed is True

        veto_events = [e for e in events if isinstance(e, DissenterVetoTriggered)]
        assert len(veto_events) == 1
        assert veto_events[0].dimension == RubricDimension.INTENT_ALIGNMENT.value
        assert "flagship_a" in veto_events[0].dissenting_judge_ids

    @pytest.mark.asyncio
    async def test_rubric_events_weights_come_from_ensemble_profile(self) -> None:
        """RubricDimensionScored.weight must match the profile weights the
        ensemble used to aggregate, so downstream calibration readers see the
        same weighting as the composite score."""
        from keystone.evaluator.rubric_config import get_profile_weights

        judge_a = _make_mock_llm()
        judge_b = _make_mock_llm()
        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=_make_mock_llm(),
            doi_verifier=verifier,
            profile=EvaluationProfile.STRATEGIC,
            ensemble_llms=[("flagship_a", judge_a), ("flagship_b", judge_b)],
        )
        manifest = _manifest(_cit("CIT-001"))

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            events = []
            async for event in evaluator.evaluate(
                "Clean output.", _contract(), _task(), manifest, _spec()
            ):
                events.append(event)

        rubric_events = [e for e in events if isinstance(e, RubricDimensionScored)]
        assert rubric_events, "expected at least one RubricDimensionScored event"
        strategic_weights = get_profile_weights(EvaluationProfile.STRATEGIC)
        for event in rubric_events:
            dim = RubricDimension(event.dimension)
            assert event.weight == pytest.approx(strategic_weights[dim], abs=1e-6)

    @pytest.mark.asyncio
    async def test_tier1_veto_cannot_be_lifted_by_layer4_process_quality(self) -> None:
        """L3 tier1 veto → L3.final_score=0.0 → composite near zero even with high L4.

        Validates the "process quality cannot save failed content" principle
        when the content-side failure comes from the ensemble path rather than
        a single-judge Tier 1 failure.
        """
        from keystone.evaluator.layer4_trajectory import ProcessContext
        from keystone.events import FindingSynthesized, SourceFound
        from keystone.models.agents import (
            AgentDefinition,
            AgentInstance,
            AgentRole,
            ResearchAgentType,
        )

        dissenter = _make_mock_llm(
            tier1_scores={
                RubricDimension.INTENT_ALIGNMENT: 30.0,
                RubricDimension.INTELLECTUAL_HONESTY: 70.0,
                RubricDimension.COMPLETENESS: 70.0,
                RubricDimension.NARRATIVE_COHERENCE: 70.0,
            }
        )
        majority = _make_mock_llm(
            tier1_scores={d: 85.0 for d in RubricDimension if d in _tier1_dims()}
        )

        # Layer 4 LLM returns a high qualitative score — if the blend did not
        # enforce "content failure cannot be lifted," composite would rise.
        async def high_l4_llm(prompt: str) -> str:
            if "process" in prompt.lower() or "trajectory" in prompt.lower():
                return json.dumps(
                    {
                        "qualitative_score": 90.0,
                        "rationale": "exhaustive research",
                        "missed_inquiries": [],
                        "skepticism_assessment": "strong",
                    }
                )
            return json.dumps({"score": 60, "feedback": "fallback"})

        verifier = MockDOIVerifier({})
        evaluator = Evaluator(
            llm=high_l4_llm,
            doi_verifier=verifier,
            ensemble_llms=[
                ("flagship_a", dissenter),
                ("flagship_b", majority),
            ],
        )
        manifest = _manifest(_cit("CIT-001"))

        # Build a minimal ProcessContext so Layer 4 runs. Agent/events are
        # synthesized just enough to exercise the metric path.
        agent_def = AgentDefinition(
            name="mock",
            description="mock research agent",
            role=AgentRole.RESEARCH,
            tools=["exa_search"],
            research_type=ResearchAgentType.QUANTITATIVE,
        )
        agent = AgentInstance(
            agent_id="agent_ens",
            engagement_id="ENG-001",
            client_id="CLT-001",
            definition=agent_def,
            working_dir="/tmp/mock",
            task_ids=[_task().id],
        )
        events_trail = [
            SourceFound(
                event_id="e1",
                engagement_id="ENG-001",
                client_id="CLT-001",
                agent_id=agent.agent_id,
                url="https://example.com/a",
                source_type="academic",
                quality_score=0.8,
            ),
            FindingSynthesized(
                event_id="e2",
                engagement_id="ENG-001",
                client_id="CLT-001",
                agent_id=agent.agent_id,
                claim_count=3,
                confidence_range="0.6-0.9",
            ),
        ]
        ctx = ProcessContext(
            agent_id=agent.agent_id, task=_task(), agent=agent, events=events_trail
        )

        with patch(
            "keystone.evaluator.layer1_deterministic.batch_check_urls",
            new_callable=AsyncMock,
            return_value={"CIT-001": True},
        ):
            async for _ in evaluator.evaluate(
                "Text.",
                _contract(),
                _task(),
                manifest,
                _spec(),
                process_context=ctx,
            ):
                pass

        result = await evaluator.get_result()
        # L3 vetoed to 0.0; composite = blend(L3=0.0, L4=90.0, w=0.8) ~ 0.06
        assert result.passed is False
        assert result.overall_score < 1.0
        assert result.layer3_results is not None
        assert result.layer3_results.final_score == 0.0
        # Layer 4 still ran and produced a quality score — not a reason to lift failure
        assert result.layer4_results is not None
        assert result.layer4_results.qualitative_score > 50.0


def _tier1_dims() -> set[RubricDimension]:
    from keystone.evaluator.rubric_config import TIER_1_DIMENSIONS

    return set(TIER_1_DIMENSIONS)
