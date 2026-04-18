"""Remediation coverage for audit findings.

Six tests filling the gaps called out in the pipeline-config audit:

1. ``sprint_contract_fallback`` governance flag fires end-to-end when
   the :class:`SprintContractGenerator` raises, proving the orchestrator
   reads ``ContentStructurer.get_fallback_task_ids()`` and applies a
   per-task WARN flag.
2. ``Layer3Result.infrastructure_failure=True`` is distinguishable from
   a genuine zero-rubric score: different feedback, same pass/fail
   behavior (both fail, but observability can tell them apart).
3. :func:`get_deep_research_callable` honors a programmatically-built
   ``AppConfig`` when one is passed explicitly — custom model IDs flow
   into the deep-research transport.
4. Layer 4 trajectory runs at FLAGSHIP/high because the orchestrator
   wires ``Evaluator.llm`` from ``_layer_llm("l4_evaluator", FLAGSHIP,
   high)`` and the :class:`Layer4Evaluator` uses that same LLM.
5. The orchestrator constructs a fresh :class:`Evaluator` for every
   task in the L4 loop — evaluator state must not leak between tasks.
6. Setting ``PIPELINE__MODEL_MIXING__L1_5_ANALYSTS=flagship`` threads
   through to :class:`Deliberation.analyst_tier` via the orchestrator,
   and :class:`AnalystSpawned` events report ``model_tier="flagship"``.
"""

from __future__ import annotations

import contextlib
import json
import os
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from keystone.citation.processor import CitationProcessorResult
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer4_trajectory import Layer4Evaluator
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.events import AnalystSpawned
from keystone.gateway.audit_log import AuditLogger
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.mcp_gateway import MCPGateway, MockMCPClient
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.tool_registry import ToolRegistry
from keystone.llm_client import (
    create_llm_factory,
    get_deep_research_callable,
)
from keystone.models.citations import (
    Citation,
    CitationManifest,
    ConfidenceTier,
    SourceType,
)
from keystone.models.confidence import ConfidenceMap, HighConfidenceClaim
from keystone.models.config import AppConfig
from keystone.models.evaluation import (
    EvaluationIntensity,
    EvaluationResult,
    Layer1Result,
    Layer2Result,
    Layer3Result,
    SprintContract,
)
from keystone.models.research import (
    EngagementSpec,
    EngagementType,
    EvaluationProfileName,
    FindingClaim,
    PipelineProfile,
    ResearchQuestion,
    ResearchSpec,
    StructuredFinding,
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
from keystone.pipeline.orchestrator import Pipeline
from keystone.research.agent_pool import AgentResult

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _citation(
    cid: str = "CIT-001",
    *,
    eid: str = "eng_test",
    client: str = "client_test",
) -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id=eid,
        client_id=client,
        url="https://example.com/source",
        title="Test Source",
        access_date=datetime.now(UTC),
        source_type=SourceType.NEWS,
        quality_score=0.8,
    )


def _task(
    task_id: str = "task_001",
    *,
    eid: str = "eng_test",
    cid: str = "client_test",
) -> ResearchTask:
    return ResearchTask(
        id=task_id,
        engagement_id=eid,
        client_id=cid,
        category=TaskCategory.MARKET_SIZING,
        type=TaskType.ESTIMATIVE,
        target_decision_usefulness=3,
        description=f"Investigate {task_id}",
        acceptance_criteria=["Provide evidence-backed claims"],
        deliverable_destination=f"Section for {task_id}",
        priority=1,
        importance=TaskImportance.PRIMARY,
        anti_confirmatory_framing="Evaluate for and against",
        assigned_tools=["exa_search", "brave_search", "paper_search"],
        assigned_model=ModelTier.STANDARD,
        end_product=f"Structured output for {task_id}",
        dependencies=[],
    )


def _spec(
    tasks: list[ResearchTask] | None = None,
    *,
    eid: str = "eng_test",
    cid: str = "client_test",
) -> EngagementSpec:
    if tasks is None:
        tasks = [_task(eid=eid, cid=cid)]
    return EngagementSpec(
        research_spec=ResearchSpec(
            engagement_id=eid,
            client_id=cid,
            title="Test engagement",
            created_at=datetime.now(UTC),
            specification_version=1,
            decision_context="Decide something",
            surprising_finding="Something unexpected",
            questions=[ResearchQuestion(question="What?", is_primary=True)],
            output_format="markdown",
            engagement_type=EngagementType.SIZING,
            day_1_hypothesis="Hypothesis",
            recommended_pipeline_profile=PipelineProfile.STANDARD,
            effective_pipeline_profile=PipelineProfile.STANDARD,
            effective_evaluation_profile=EvaluationProfileName.DEFAULT,
            profile_source="test",
        ),
        task_decomposition=TaskDecomposition(
            project="Test",
            engagement_id=eid,
            client_id=cid,
            research_md_path=f"engagements/{eid}/RESEARCH.md",
            specification_version=1,
            decomposition_rationale="Test",
            tasks=tasks,
        ),
        validation_report=ValidationReport(
            intent_clear=True,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        ),
    )


def _finding(
    task_id: str = "task_001",
    *,
    eid: str = "eng_test",
    cid: str = "client_test",
) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=f"agent_{task_id}",
        engagement_id=eid,
        client_id=cid,
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text="Test claim",
                evidence="Test evidence",
                citations=[_citation(eid=eid, client=cid)],
                confidence=0.85,
                confidence_tier=ConfidenceTier.HIGH,
            ),
        ],
        absence_report=["No gap identified"],
        sources_consulted=3,
        tokens_consumed=500,
    )


def _manifest(eid: str = "eng_test", cid: str = "client_test") -> CitationManifest:
    return CitationManifest(
        manifest_id="MAN-001",
        engagement_id=eid,
        client_id=cid,
        citations=[_citation(eid=eid, client=cid)],
    )


def _confidence_map(eid: str = "eng_test", cid: str = "client_test") -> ConfidenceMap:
    return ConfidenceMap(
        engagement_id=eid,
        client_id=cid,
        high_confidence_above_80pct=[
            HighConfidenceClaim(
                claim="Stable claim",
                methodological_agreement="3/4",
                sources=3,
                corroboration_count=2,
                robustness="Stable",
                curmudgeon_challenge="Challenge",
                aggregated_claim_id="AGG-001",
                task_ids=["task_001"],
            ),
        ],
        provenance_index={"AGG-001": ["task_001"]},
    )


def _eval_result(
    task_id: str = "task_001",
    *,
    eid: str = "eng_test",
    cid: str = "client_test",
    passed: bool = True,
) -> EvaluationResult:
    return EvaluationResult(
        evaluation_id=f"eval_{task_id}_{uuid.uuid4().hex[:6]}",
        engagement_id=eid,
        client_id=cid,
        task_id=task_id,
        evaluated_at=datetime.now(UTC),
        intensity=EvaluationIntensity.STANDARD,
        passed=passed,
        overall_score=72.0 if passed else 30.0,
        layer1_results=Layer1Result(facts_verified=1, facts_failed=0),
        layer2_results=Layer2Result(
            citations_checked=1,
            citations_verified=1,
            citations_fabricated=[],
            gate_passed=True,
        ),
        layer3_results=Layer3Result(
            dimension_scores=[],
            weighted_total=72.0 if passed else 30.0,
            gestalt_adjustment=0.0,
            final_score=72.0 if passed else 30.0,
        ),
        feedback=f"{'PASSED' if passed else 'FAILED'} with score.",
    )


def _gateway() -> MCPGateway:
    registry = ToolRegistry()
    return MCPGateway(
        registry=registry,
        authorizer=ToolAuthorizer(registry),
        rate_limiter=InMemoryRateLimiter(limits={}),
        audit_logger=AuditLogger(),
        client=MockMCPClient(),
    )


def _sprint_contract(task: ResearchTask) -> SprintContract:
    return SprintContract(
        section_id=f"section_{task.id}",
        engagement_id=task.engagement_id,
        client_id=task.client_id,
        task_id=task.id,
        section_title=task.deliverable_destination,
        acceptance_criteria=task.acceptance_criteria,
    )


# ---------------------------------------------------------------------------
# Test 1: sprint_contract_fallback governance flag end-to-end
# ---------------------------------------------------------------------------


class TestSprintContractFallbackFlagEmitted:
    """When SprintContractGenerator raises, the orchestrator must apply a
    per-task ``sprint_contract_fallback`` WARN flag so operators see the
    L2 degradation. Silent fallback was the audit finding."""

    @pytest.mark.asyncio
    async def test_failing_generator_emits_governance_flag(self) -> None:
        """Patch the generator to always raise; assert the flag is applied."""
        from keystone.governance.policy import ProfileExecutionPolicy

        spec = _spec()
        finding = _finding()
        manifest = _manifest()
        cm = _confidence_map()

        # Collect every apply_flag call the orchestrator makes so we can
        # look for the sprint_contract_fallback gate after the pipeline ran.
        applied_flags: list = []
        original_apply_flag = ProfileExecutionPolicy.apply_flag

        def spying_apply_flag(self, state, flag, *, task_id=None):
            applied_flags.append((flag.gate, flag.action.value, task_id))
            return original_apply_flag(self, state, flag, task_id=task_id)

        factory = MagicMock(return_value=AsyncMock(return_value='{"result": "ok"}'))
        pipeline = Pipeline(llm_factory=factory, gateway=_gateway())

        async def noop(*args, **kwargs):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[AgentResult("agent_task_001", "task_001", finding=finding)]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=[finding])
        c.citation_processor.process = noop
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(
                manifest=manifest, canonicalized_findings=[finding]
            )
        )
        c.deliberation.deliberate = noop
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)

        # Replace the sprint-contract generator's generate() with a
        # raising stub so the ContentStructurer walks its fallback path
        # and records the task_id. Both the structurer's generator and
        # the orchestrator-level generator (used in the L4 loop) come
        # from the same instance, so patching once is enough.
        async def raising_generate(task, spec):
            raise RuntimeError("simulated sprint contract crash")

        c.sprint_contract_generator.generate = raising_generate

        pipeline._pending_components = c

        # Patch Evaluator so L4 runs without LLM calls.
        class _PassingEvaluator:
            def __init__(self, *args, **kwargs):
                self._result = _eval_result()

            async def evaluate(self, *args, **kwargs):
                return
                yield

            async def get_result(self):
                return self._result

        with (
            patch.object(ProfileExecutionPolicy, "apply_flag", new=spying_apply_flag),
            patch("keystone.pipeline.orchestrator.Evaluator", new=_PassingEvaluator),
        ):
            await pipeline.run("Test question", "client_test")

        # Exactly one sprint_contract_fallback flag must have been emitted,
        # scoped to the only task in the run.
        sprint_flags = [
            (gate, action, task_id)
            for (gate, action, task_id) in applied_flags
            if gate == "sprint_contract_fallback"
        ]
        assert sprint_flags == [("sprint_contract_fallback", "warn", "task_001")]


# ---------------------------------------------------------------------------
# Test 2: infrastructure_failure is distinguishable from genuine zero
# ---------------------------------------------------------------------------


class TestInfrastructureFailureDistinguishable:
    """Two evaluations with ``final_score=0`` but different
    ``infrastructure_failure`` flags must be distinguishable downstream.
    Same pass/fail behavior (both fail threshold), different observability.
    """

    @pytest.mark.asyncio
    async def test_genuine_zero_vs_infrastructure_failure(self) -> None:
        task = _task()
        spec = _spec([task])
        manifest = CitationManifest(
            manifest_id="MAN-EMPTY",
            engagement_id=task.engagement_id,
            client_id=task.client_id,
        )
        contract = _sprint_contract(task)

        # --- Path A: genuine zero score ---
        # Rubric LLM returns real scores but all at zero on every dimension.
        async def zero_rubric_llm(prompt: str) -> str:
            lower = prompt.lower()
            if "gestalt overlay" in lower or "holistic" in lower:
                return json.dumps({"adjustment": 0.0, "rationale": "flat"})
            if "fact decomposition" in lower:
                return json.dumps([])
            if "numerical consistency" in lower:
                return json.dumps({"numerical_claims": [], "inconsistencies": []})
            # Any rubric dimension: return 0 score.
            return json.dumps({"score": 0, "feedback": "floor", "sub_criteria_notes": []})

        genuine_evaluator = Evaluator(llm=zero_rubric_llm, profile=EvaluationProfile.DEFAULT)
        async for _ in genuine_evaluator.evaluate(
            "Output text",
            contract,
            task,
            manifest,
            spec,
        ):
            pass
        genuine_result = await genuine_evaluator.get_result()

        # --- Path B: infrastructure failure (LLM raises) ---
        async def raising_llm(prompt: str) -> str:
            raise RuntimeError("LLM unavailable")

        infra_evaluator = Evaluator(llm=raising_llm, profile=EvaluationProfile.DEFAULT)
        async for _ in infra_evaluator.evaluate(
            "Output text",
            contract,
            task,
            manifest,
            spec,
        ):
            pass
        infra_result = await infra_evaluator.get_result()

        # Both produced a Layer3Result but with different infrastructure_failure.
        assert genuine_result.layer3_results is not None
        assert infra_result.layer3_results is not None
        assert genuine_result.layer3_results.infrastructure_failure is False
        assert infra_result.layer3_results.infrastructure_failure is True

        # Genuine zero has actual dimension scores (all at 0); infra failure
        # has an empty scores list — the audit signal for "didn't run."
        assert genuine_result.layer3_results.dimension_scores  # non-empty
        assert infra_result.layer3_results.dimension_scores == []

        # Same pass/fail outcome (both fail) — operators distinguish via
        # the flag, not via pass/fail.
        assert genuine_result.passed is False
        assert infra_result.passed is False

        # Feedback must differ so a human reviewing the output can tell
        # "scored zero" apart from "scoring didn't run".
        assert genuine_result.feedback != infra_result.feedback


# ---------------------------------------------------------------------------
# Test 3: get_deep_research_callable with programmatic AppConfig
# ---------------------------------------------------------------------------


class TestGetDeepResearchCallableProgrammaticConfig:
    """A programmatically-constructed AppConfig with custom model IDs must
    flow into the deep-research transport when passed explicitly. The
    audit found this path was silently dropping programmatic overrides."""

    @pytest.mark.asyncio
    async def test_programmatic_standard_model_flows_to_claude_cli(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Custom ``standard_model`` set in-code must reach ``_call_claude_cli_research``."""
        # Unset ANTHROPIC_API_KEY (the transport raises if present).
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "claude_cli")

        captured: dict[str, object] = {}

        async def capturing_research(prompt, model, semaphore, timeout_s=None):
            captured["prompt"] = prompt
            captured["model"] = model
            captured["timeout_s"] = timeout_s
            return "{}"

        custom_config = AppConfig(
            standard_model="custom-sonnet-programmatic",
        )

        with patch(
            "keystone.llm_client._call_claude_cli_research",
            new=capturing_research,
        ):
            llm = get_deep_research_callable(config=custom_config)
            await llm("probe prompt")

        assert captured["model"] == "custom-sonnet-programmatic"

    @pytest.mark.asyncio
    async def test_no_config_uses_default_standard_model(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Omitting ``config`` re-reads AppConfig defaults (BaseSettings) — env
        vars flow, but programmatic overrides from any prior in-memory
        AppConfig do NOT leak into the fresh one."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "claude_cli")

        captured: dict[str, object] = {}

        async def capturing_research(prompt, model, semaphore, timeout_s=None):
            captured["model"] = model
            return "{}"

        with patch(
            "keystone.llm_client._call_claude_cli_research",
            new=capturing_research,
        ):
            llm = get_deep_research_callable()  # No config passed.
            await llm("probe")

        # Without config, AppConfig default for ``standard_model`` is the
        # Claude Sonnet baseline. Programmatic overrides only apply when
        # the caller passes their own AppConfig.
        assert captured["model"] == AppConfig.model_fields["standard_model"].default


# ---------------------------------------------------------------------------
# Test 4: Layer 4 trajectory runs at FLAGSHIP/high
# ---------------------------------------------------------------------------


class TestLayer4TrajectoryTier:
    """Layer 4 process-trajectory evaluation reuses the primary evaluator
    LLM, which the orchestrator wires from ``_layer_llm("l4_evaluator",
    FLAGSHIP, high)``. Verify both halves of this claim."""

    def test_layer4_evaluator_shares_primary_llm(self) -> None:
        """Structural: ``Evaluator._layer4`` is constructed with the primary LLM."""
        primary_llm = AsyncMock(return_value="{}")
        extraction_llm = AsyncMock(return_value="{}")

        ev = Evaluator(
            llm=primary_llm,
            profile=EvaluationProfile.DEFAULT,
            extraction_llm=extraction_llm,
        )
        assert isinstance(ev._layer4, Layer4Evaluator)
        assert ev._layer4._llm is primary_llm
        # Not a copy of the extraction LLM — trajectory is a judgment task.
        assert ev._layer4._llm is not extraction_llm

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    @pytest.mark.asyncio
    async def test_orchestrator_l4_evaluator_layer_runs_at_flagship_high(
        self,
    ) -> None:
        """End-to-end: the pipeline's ``l4_evaluator`` layer resolves to
        FLAGSHIP/high and the API call carries ``reasoning.effort="high"``
        and the FLAGSHIP model ID."""
        config = AppConfig(openai_api_key="test-key")
        factory = create_llm_factory(config)
        pipeline = Pipeline(llm_factory=factory, gateway=_gateway())

        seen_kwargs: list[dict] = []

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()

            async def capture(**kwargs):
                seen_kwargs.append(kwargs)
                return MagicMock(output_text='{"score": 70, "feedback": "ok"}')

            mock_client.responses.create = capture
            mock_get.return_value = mock_client

            # Resolve the same LLM the orchestrator uses for the Evaluator's
            # primary llm slot (which Layer4Evaluator shares).
            l4_llm = pipeline._layer_llm(
                "l4_evaluator",
                fallback_tier=ModelTier.FLAGSHIP,
                fallback_effort="high",
            )
            await l4_llm("probe")

        assert len(seen_kwargs) == 1
        assert seen_kwargs[0]["reasoning"] == {"effort": "high"}
        # FLAGSHIP model ID must match config default.
        assert seen_kwargs[0]["model"] == config.flagship_model


# ---------------------------------------------------------------------------
# Test 5: per-task Evaluator freshness
# ---------------------------------------------------------------------------


class TestPerTaskEvaluatorFreshness:
    """Each iteration of the L4 loop must build a fresh Evaluator. Reusing
    a single Evaluator across tasks would let one task's stored result
    leak into the next via ``_result``."""

    @pytest.mark.asyncio
    async def test_fresh_evaluator_constructed_per_task(self) -> None:
        tasks = [_task(task_id="task_A"), _task(task_id="task_B")]
        spec = _spec(tasks)
        findings = [_finding(t.id) for t in tasks]
        manifest = _manifest()
        cm = _confidence_map()

        factory = MagicMock(return_value=AsyncMock(return_value='{"result": "ok"}'))
        pipeline = Pipeline(llm_factory=factory, gateway=_gateway())

        async def noop(*args, **kwargs):
            return
            yield

        c = pipeline._build_components()
        c.spec_engine.generate_spec = noop
        c.spec_engine.get_spec = AsyncMock(return_value=spec)
        c.agent_pool.execute_all = AsyncMock(
            return_value=[
                AgentResult(f"agent_{t.id}", t.id, finding=f)
                for t, f in zip(tasks, findings, strict=True)
            ]
        )
        c.agent_pool.get_successful_findings = MagicMock(return_value=findings)
        c.citation_processor.process = noop
        c.citation_processor.get_result = AsyncMock(
            return_value=CitationProcessorResult(manifest=manifest, canonicalized_findings=findings)
        )
        c.deliberation.deliberate = noop
        c.deliberation.get_confidence_map = AsyncMock(return_value=cm)
        pipeline._pending_components = c

        # Capture every Evaluator instance built during the L4 loop.
        constructed: list[object] = []

        original_evaluator = Evaluator

        class _SpyEvaluator(original_evaluator):  # type: ignore[misc, valid-type]
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                constructed.append(self)
                self._captured_task_id: str | None = None
                self._result_override: EvaluationResult | None = None

            async def evaluate(self, *args, **kwargs):
                # Signature: evaluate(output_text, contract, task, manifest, spec, ...)
                task = kwargs.get("task") or (args[2] if len(args) >= 3 else None)
                if task is not None:
                    self._captured_task_id = task.id
                return
                yield

            async def get_result(self):
                if self._result_override is None:
                    task_id = self._captured_task_id or "unknown"
                    self._result_override = _eval_result(task_id=task_id)
                return self._result_override

        with (
            patch("keystone.pipeline.orchestrator.Evaluator", new=_SpyEvaluator),
            contextlib.suppress(RuntimeError),
        ):
            # Governance halts on missing passes; suppress the RuntimeError
            # so the test can still inspect the captured evaluator list
            # (the L4 loop ran to completion before the halt check).
            await pipeline.run("probe", "client_test")

        # Two tasks ⇒ two distinct Evaluator instances.
        assert len(constructed) == 2
        assert constructed[0] is not constructed[1]
        # Independent state: modifying one must not affect the other.
        constructed[0]._result = "sentinel"
        assert constructed[1]._result != "sentinel"


# ---------------------------------------------------------------------------
# Test 6: analyst_tier env-var end-to-end
# ---------------------------------------------------------------------------


class TestAnalystTierEnvVarEndToEnd:
    """``PIPELINE__MODEL_MIXING__L1_5_ANALYSTS=flagship`` must end up on the
    :class:`AnalystSpawned` event as ``model_tier="flagship"``. The
    orchestrator resolves the tier from :class:`PipelineConfig`
    at component-build time, and :class:`Deliberation` stores it."""

    def test_env_var_threads_to_deliberation_analyst_tier(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PIPELINE__MODEL_MIXING__L1_5_ANALYSTS", "flagship")
        # Ensure no stray LLM_PROVIDER config interferes.
        monkeypatch.setenv("LLM_PROVIDER", "api_key")

        # Fresh AppConfig reads the env var through BaseSettings.
        config = AppConfig(openai_api_key="test-key")
        assert config.pipeline.model_mixing.l1_5_analysts == "flagship"

        factory = create_llm_factory(config)
        pipeline = Pipeline(llm_factory=factory, gateway=_gateway())
        c = pipeline._build_components()

        # Orchestrator reads the env-set tier and stores it on Deliberation.
        assert c.deliberation._analyst_tier == ModelTier.FLAGSHIP

    @pytest.mark.asyncio
    async def test_env_var_surfaces_on_analyst_spawned_event(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Run Deliberation (with stub analyst) and inspect AnalystSpawned events."""
        monkeypatch.setenv("PIPELINE__MODEL_MIXING__L1_5_ANALYSTS", "flagship")
        monkeypatch.setenv("LLM_PROVIDER", "api_key")

        config = AppConfig(openai_api_key="test-key")
        factory = create_llm_factory(config)
        pipeline = Pipeline(llm_factory=factory, gateway=_gateway())
        c = pipeline._build_components()

        # Feed Deliberation an analyst LLM that returns the minimal
        # JSON its Analyst expects.
        async def stub_analyst_llm(prompt: str) -> str:
            if "evaluate each claim" in prompt.lower():
                return json.dumps(
                    [
                        {
                            "index": 0,
                            "confidence": 0.8,
                            "source_count": 1,
                            "reasoning": "ok",
                        }
                    ]
                )
            return json.dumps({"result": "ok"})

        # Swap out the orchestrator-built LLMs with the stub so we do not
        # hit the LayerAwareLLMFactory during this test.
        c.deliberation._analyst_llm = stub_analyst_llm
        c.deliberation._judge_llm = stub_analyst_llm
        c.deliberation._wwhtb_llm = stub_analyst_llm

        task = _task()
        finding = _finding(task.id)
        manifest = _manifest()

        events: list = []
        async for event in c.deliberation.deliberate(
            manifest, [finding], "eng_test", "client_test"
        ):
            events.append(event)

        spawned = [e for e in events if isinstance(e, AnalystSpawned)]
        assert spawned, "Deliberation must have emitted AnalystSpawned events"
        for event in spawned:
            assert event.model_tier == "flagship", (
                f"Expected flagship but got {event.model_tier!r} — "
                "PIPELINE__MODEL_MIXING__L1_5_ANALYSTS did not thread through."
            )
