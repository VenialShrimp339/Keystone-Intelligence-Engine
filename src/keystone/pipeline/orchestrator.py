"""Pipeline orchestrator: the main() that wires all components end-to-end.

Runs the full DPVI pipeline:
  L0 (Specification) -> L1 (Research Agents) -> CitationProcessor ->
  L1.5 (Deliberation) -> L4 (Evaluator) -> MarkdownRenderer

Yields AnyPipelineEvent throughout for observability.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from keystone.checkpoint.serialization import (
    deserialize_post_deliberation,
    deserialize_post_evaluation,
    deserialize_post_l1_citproc,
    deserialize_post_spec,
    deserialize_post_structuring,
    serialize_post_deliberation,
    serialize_post_evaluation,
    serialize_post_l1_citproc,
    serialize_post_spec,
    serialize_post_structuring,
)
from keystone.checkpoint.store import STAGE_ORDER, CheckpointStore
from keystone.citation.processor import CitationProcessor
from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.layer4_trajectory import ProcessContext
from keystone.evaluator.retry import LLMCallable
from keystone.evaluator.rubric_config import EvaluationProfile
from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.events import AnyPipelineEvent, ChunkIngested, ObservationRecorded, SearchCompleted
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.gateway.retrieval_bridge import register_retrieval_handlers
from keystone.governance.models import GovernanceState
from keystone.governance.policy import ProfileExecutionPolicy
from keystone.llm_client import LayerAwareLLMFactory, get_deep_research_callable
from keystone.models.agents import AgentInstance
from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.config import PipelineConfig
from keystone.models.evaluation import EvaluationIntensity, EvaluationResult
from keystone.models.research import EngagementSpec, PipelineProfile, StructuredFinding
from keystone.models.structuring import StructuredOutline
from keystone.models.tasks import ModelTier, ResearchTask
from keystone.observation.store import ObservationStore
from keystone.pipeline.markdown_renderer import MarkdownRenderer
from keystone.research.agent_pool import AgentPool
from keystone.research.error_recovery import ErrorRecovery
from keystone.research.evidence_context import (
    EvidenceContextProvider,
    build_default_task_filter,
    build_default_task_ranker,
)
from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.template_registry import TemplateRegistry
from keystone.structuring.content_structuring import (
    ContentStructurer,
    filter_outline_by_passed_tasks,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineComponents:
    """All per-run components built fresh by _build_components().

    Tests may construct a Pipeline, call _build_components(), mutate fields
    on the returned object, then assign it to pipeline._pending_components
    before calling run() to inject mocks without touching __init__.
    """

    spec_engine: SpecificationEngine
    agent_pool: AgentPool
    citation_processor: CitationProcessor
    deliberation: Deliberation
    content_structurer: ContentStructurer
    renderer: MarkdownRenderer
    sprint_contract_generator: SprintContractGenerator
    template_registry: TemplateRegistry


class PipelineResult(BaseModel):
    """Complete output of a pipeline run."""

    engagement_id: str
    client_id: str
    spec: EngagementSpec
    findings: list[StructuredFinding]
    manifest: CitationManifest
    confidence_map: ConfidenceMap
    evaluation_results: list[EvaluationResult]
    markdown_output: str
    total_tokens: int = Field(default=0, ge=0)
    total_events: int = Field(default=0, ge=0)
    tokens_by_layer: dict[str, int] = Field(default_factory=dict)


class Pipeline:
    """End-to-end pipeline orchestrator.

    Wires L0 -> L1 -> CitProc -> L1.5 -> L4 -> Render.
    HITL gates fire inside SpecificationEngine and Deliberation
    when db_session_factory is provided.

    Usage:
        pipeline = Pipeline(llm_factory=get_llm_for_tier, gateway=gw)
        result = await pipeline.run("Estimate TAM for AV sensors", "client_1")
    """

    def __init__(
        self,
        llm_factory: Callable[[ModelTier], LLMCallable],
        gateway: MCPGateway,
        db_session_factory: Callable | None = None,
        max_eval_tasks: int | None = None,
        evidence_records: list[EvidencePrepRecord] | None = None,
        retrieval_service_factory: Callable[[str], RetrievalService] | None = None,
        ensemble_panel_override: Callable[
            [EvaluationIntensity, Callable[[ModelTier], LLMCallable]],
            list[tuple[str, LLMCallable]] | None,
        ]
        | None = None,
        pipeline_config: PipelineConfig | None = None,
        observation_store: ObservationStore | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        """Construct a pipeline.

        ``retrieval_service_factory`` takes the active engagement_id and
        returns a :class:`RetrievalService`. When supplied, the
        orchestrator builds a fresh service per run, ingests Lane E
        records (``evidence_records``) into it as institutional memory
        (``engagement_id=None``), and registers the retrieval tool
        handlers on ``gateway`` so agents calling ``semantic_search`` or
        ``hybrid_search`` hit the live service. Pass ``None`` to skip
        retrieval wiring entirely -- the pipeline runs exactly as it did
        before retrieval existed.

        Lane E is treated as institutional memory because the records
        are pre-fetched reference material (PDFs, articles, EDGAR
        filings), not mid-research agent output. They are meant to be
        visible to every engagement. Inter-agent isolation is enforced
        structurally one level down: the
        :mod:`keystone.gateway.retrieval_bridge` handlers inject
        ``exclude_engagement_id=<caller-agent's engagement_id>`` into
        every :class:`SearchQuery`, so any future chunk ingested with
        ``engagement_id=<active>`` (a sibling agent's work-in-progress)
        is automatically hidden from other agents in the same
        engagement while institutional chunks pass through.

        Passing ``engagement_context=<eid>`` when constructing the
        service remains useful for system callers that bypass the
        bridge (e.g. string-form :meth:`RetrievalService.search`
        calls) -- those paths still inherit the context automatically.

        ``ensemble_panel_override`` lets operators swap the default
        Layer 5 judge panel without patching this module. When supplied,
        it is called instead of :func:`_resolve_ensemble_judges` with
        the same signature ``(intensity, llm_factory) -> panel | None``,
        and its return value flows straight through to the Evaluator.
        Passing ``None`` (default) preserves the built-in mapping.
        """
        self._llm_factory = llm_factory
        self._gateway = gateway
        self._db_session_factory = db_session_factory
        self._max_eval_tasks = max_eval_tasks
        self._evidence_records = evidence_records
        self._retrieval_service_factory = retrieval_service_factory
        self._ensemble_panel_override = ensemble_panel_override
        self._observation_store = observation_store
        self._checkpoint_store = checkpoint_store
        # Pipeline-wide behavior knobs. Resolved in preference order:
        # explicit parameter, factory's own ``pipeline_config`` attribute
        # (when the factory is a LayerAwareLLMFactory), fresh default
        # instance. Tests that inject a plain callable for ``llm_factory``
        # still get a fresh PipelineConfig and so see historical defaults.
        if pipeline_config is not None:
            self._pipeline_config = pipeline_config
        elif isinstance(llm_factory, LayerAwareLLMFactory):
            self._pipeline_config = llm_factory.pipeline_config
        else:
            self._pipeline_config = PipelineConfig()
        # Internal run state (overwritten on each run).
        self._result: PipelineResult | None = None
        # Tests may call _build_components(), mutate fields, then assign here
        # before calling run() to inject mocks.
        self._pending_components: PipelineComponents | None = None

    def _layer_llm(
        self,
        layer_name: str,
        *,
        fallback_tier: ModelTier,
        fallback_effort: str | None = None,  # noqa: ARG002
    ) -> LLMCallable:
        """Resolve an LLMCallable for a pipeline layer.

        Prefers the factory's ``for_layer`` method (real factory knows
        about config, including per-layer reasoning effort); falls back
        to the tier-based callable interface for test doubles that only
        implement ``(tier) -> LLMCallable``. ``fallback_effort`` is kept
        on the signature as a readability aid for call sites — it
        documents the intended effort when a real factory is wired, even
        though the parameter is unused on the test-double path.
        """
        factory = self._llm_factory
        if isinstance(factory, LayerAwareLLMFactory):
            return factory.for_layer(layer_name)
        return factory(fallback_tier)

    def _build_components(self) -> PipelineComponents:
        """Build and return a fresh set of pipeline components.

        Called at the start of each run_with_events() invocation so that
        consecutive runs never share mutable component state.

        Tests may call this method, mutate fields on the returned dataclass,
        then assign it to self._pending_components before calling run().
        """
        deep_llm = None
        if os.environ.get("DEEP_RESEARCH", "").strip() == "1":
            logger.info("DEEP_RESEARCH=1: L1 agents will use multi-turn web research")
            # Prefer the factory's own deep_research_callable when we have a
            # real LayerAwareLLMFactory — it reuses the factory's AppConfig
            # (so programmatic model-ID overrides flow through) and the
            # factory's instance-level research_semaphore. Fall back to the
            # module helper for test doubles that implement only the
            # ``(tier) -> LLMCallable`` callable interface.
            if isinstance(self._llm_factory, LayerAwareLLMFactory):
                deep_llm = self._llm_factory.deep_research_callable()
            else:
                deep_llm = get_deep_research_callable(
                    pipeline_config=self._pipeline_config,
                )

        evidence_provider: EvidenceContextProvider | None = None
        if self._evidence_records:
            evidence_provider = EvidenceContextProvider(
                self._evidence_records,
                task_filter=build_default_task_filter(),
                task_ranker=build_default_task_ranker(),
            )

        sprint_contract_generator = SprintContractGenerator(
            llm=self._layer_llm(
                "sprint_contract",
                fallback_tier=ModelTier.FLAGSHIP,
                fallback_effort="high",
            ),
        )
        pc = self._pipeline_config
        return PipelineComponents(
            spec_engine=SpecificationEngine(
                llm=self._layer_llm(
                    "l0_specification",
                    fallback_tier=ModelTier.FLAGSHIP,
                    fallback_effort="xhigh",
                ),
                template_registry=TemplateRegistry(),
                db_session_factory=self._db_session_factory,
                classifier_llm=self._layer_llm(
                    "l0_engagement_classifier",
                    fallback_tier=ModelTier.STANDARD,
                ),
                clarifier_llm=self._layer_llm(
                    "l0_intent_clarifier",
                    fallback_tier=ModelTier.FLAGSHIP,
                ),
                decomposer_lens_llm=self._layer_llm(
                    "l0_decomposer_lens",
                    fallback_tier=ModelTier.STANDARD,
                ),
                decomposer_synth_llm=self._layer_llm(
                    "l0_decomposer_synth",
                    fallback_tier=ModelTier.FLAGSHIP,
                ),
                mece_validator_llm=self._layer_llm(
                    "l0_mece_validator",
                    fallback_tier=ModelTier.FLAGSHIP,
                ),
                priority_scorer_llm=self._layer_llm(
                    "l0_priority_scorer",
                    fallback_tier=ModelTier.FLAGSHIP,
                ),
                task_generator_llm=self._layer_llm(
                    "l0_task_generator",
                    fallback_tier=ModelTier.STANDARD,
                ),
            ),
            agent_pool=AgentPool(
                llm=self._layer_llm(
                    "l1_research",
                    fallback_tier=ModelTier.STANDARD,
                ),
                gateway=self._gateway,
                deep_llm=deep_llm,
                error_recovery=ErrorRecovery(llm_factory=self._llm_factory),
                evidence_provider=evidence_provider,
                research_default_rounds=pc.research_default_rounds,
                research_max_rounds=pc.research_max_rounds,
                research_quality_threshold=pc.research_quality_threshold,
                current_tier=_resolve_layer_tier_or(
                    self._pipeline_config,
                    "l1_research",
                    ModelTier.STANDARD,
                ),
                llm_factory=self._llm_factory,
                l1_orchestrator_enabled=pc.l1_orchestrator_enabled,
            ),
            citation_processor=CitationProcessor(),
            deliberation=Deliberation(
                analyst_llm=self._layer_llm(
                    "l1_5_analysts",
                    fallback_tier=ModelTier.STANDARD,
                ),
                judge_llm=self._layer_llm(
                    "l1_5_aggregator",
                    fallback_tier=ModelTier.FLAGSHIP,
                ),
                db_session_factory=self._db_session_factory,
                analyst_tier=_resolve_layer_tier_or(
                    self._pipeline_config,
                    "l1_5_analysts",
                    ModelTier.STANDARD,
                ),
                dispute_variance_threshold=pc.dispute_variance_threshold,
                wwhtb_confidence_threshold=pc.wwhtb_confidence_threshold,
            ),
            content_structurer=ContentStructurer(
                sprint_contract_generator=sprint_contract_generator,
            ),
            renderer=MarkdownRenderer(),
            sprint_contract_generator=sprint_contract_generator,
            template_registry=TemplateRegistry(),
        )

    async def run(
        self,
        question: str,
        client_id: str,
        client_context: str | None = None,
    ) -> PipelineResult:
        """Run the full pipeline, collecting events internally.

        Returns PipelineResult with all outputs and the rendered markdown.
        """
        events: list[AnyPipelineEvent] = []
        async for event in self.run_with_events(question, client_id, client_context):
            events.append(event)

        assert self._result is not None
        self._result = self._result.model_copy(update={"total_events": len(events)})
        return self._result

    async def run_with_events(
        self,
        question: str,
        client_id: str,
        client_context: str | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the full pipeline, yielding events for observability.

        Builds fresh components each run (or uses _pending_components if set
        by tests for injection). After exhausting the iterator, call
        get_result() for the PipelineResult.
        """
        self._result = None
        # Use injected test components if present, otherwise build fresh.
        if self._pending_components is not None:
            c = self._pending_components
            self._pending_components = None
        else:
            c = self._build_components()

        total_tokens = 0

        # --- Stage 1: L0 Specification ---
        logger.info("L0: Generating specification for '%s'", question[:80])
        async for event in c.spec_engine.generate_spec(
            question, client_id, client_context=client_context
        ):
            yield event

        spec = await c.spec_engine.get_spec()
        eid = spec.research_spec.engagement_id
        # Deliberation is built before L0 runs, so propagate the classified
        # pipeline profile once the finalized spec is available.
        c.deliberation._effective_pipeline_profile = spec.research_spec.effective_pipeline_profile
        policy = ProfileExecutionPolicy(
            spec.research_spec.effective_pipeline_profile,
            low_agreement_threshold=self._pipeline_config.l5_low_agreement_threshold,
        )
        governance = policy.new_state(spec.task_decomposition.tasks)
        if not spec.validation_report.scope_valid:
            policy.flag_mece_failure(governance)
        _raise_if_halted(governance)
        logger.info("L0 complete: %d tasks", len(spec.task_decomposition.tasks))

        # Intermediate artifacts
        out_dir = Path(self._pipeline_config.output_dir) / eid
        _write_artifact(
            out_dir / "l0_classification.json",
            json.dumps(
                {
                    "engagement_type": spec.research_spec.engagement_type.value,
                    "pipeline_profile": spec.research_spec.effective_pipeline_profile.value,
                    "profile_source": spec.research_spec.profile_source,
                },
                indent=2,
            ),
        )
        _write_artifact(
            out_dir / "l0_intent_clarification.json",
            json.dumps(
                {
                    "decision_context": spec.research_spec.decision_context,
                    "surprising_finding": spec.research_spec.surprising_finding,
                    "day_1_hypothesis": spec.research_spec.day_1_hypothesis,
                    "questions": [q.model_dump() for q in spec.research_spec.questions],
                },
                indent=2,
                default=str,
            ),
        )
        _write_artifact(
            out_dir / "l0_issue_tree.json",
            json.dumps(spec.issue_tree, indent=2),
        )
        _write_artifact(
            out_dir / "l0_tasks.json",
            spec.task_decomposition.model_dump_json(indent=2),
        )

        if self._checkpoint_store is not None:
            await self._checkpoint_store.save(
                eid, "POST_SPEC", serialize_post_spec(spec, governance)
            )

        # --- Stage 1b: Retrieval wiring ---
        # Build an engagement-scoped RetrievalService, ingest Lane E
        # records into it, and register the retrieval tool handlers on
        # the gateway so any agent call to semantic_search / hybrid_search
        # hits the live service. SearchCompleted events emitted by the
        # handlers are collected into ``search_events`` and yielded
        # after agent execution so they show up alongside agent event
        # trails for Layer 4's trajectory scoring.
        search_events: list[SearchCompleted] = []
        async for event in self._wire_retrieval(eid, client_id, search_events):
            yield event

        # --- Stage 2: L1 Research Agents ---
        logger.info("L1: Dispatching %d agents", len(spec.task_decomposition.tasks))
        assignments = self._build_assignments(spec, c.template_registry)
        dead_letters_before = len(self._gateway.dead_letters)
        agent_results = await c.agent_pool.execute_all(assignments)

        # Preserve per-agent event trails so Layer 4 can inspect the
        # research process after citations have been dedup/canonicalized.
        events_by_agent: dict[str, list[AnyPipelineEvent]] = {}
        agent_by_task: dict[str, AgentInstance] = {task.id: agent for task, _, agent in assignments}

        # Collect events from agent results
        for ar in agent_results:
            events_by_agent.setdefault(ar.agent_id, []).extend(ar.events)
            for event in ar.events:
                yield event

        # Layer 4 inspects retrieval usage per agent; fold the search
        # events collected during agent execution into each agent's
        # trail and yield them to the top-level event stream.
        for search_event in search_events:
            events_by_agent.setdefault(search_event.agent_id, []).append(search_event)
            yield search_event

        findings = c.agent_pool.get_successful_findings(agent_results)
        l1_tokens = 0
        for f in findings:
            l1_tokens += f.tokens_consumed
        total_tokens += l1_tokens
        finding_by_task = {finding.task_id: finding for finding in findings}
        for task in spec.task_decomposition.tasks:
            policy.record_research_outcome(
                governance,
                task,
                finding_by_task.get(task.id),
            )
        # Cost ceiling check: scale ceiling for orchestrated tasks.
        base_ceiling = self._pipeline_config.research_token_ceiling_per_task
        if self._pipeline_config.l1_orchestrator_enabled:
            token_ceiling = base_ceiling * (1 + self._pipeline_config.l1_max_sub_agents)
        else:
            token_ceiling = base_ceiling
        for f in findings:
            if f.tokens_consumed > token_ceiling:
                policy.flag_cost_ceiling(
                    governance,
                    task_id=f.task_id,
                    tokens_used=f.tokens_consumed,
                    ceiling=token_ceiling,
                )
        # Degraded dispatch check: flag tasks that fell back from orchestrated to single-agent.
        for ar in agent_results:
            if ar.degraded_dispatch:
                policy.flag_degraded_dispatch(governance, task_id=ar.task_id)
        task_id_by_agent: dict[str, str] = {
            agent.agent_id: task_id for task_id, agent in agent_by_task.items()
        }
        for dl in self._gateway.dead_letters[dead_letters_before:]:
            task_id = task_id_by_agent.get(dl.call.agent_id, dl.call.agent_id)
            policy.flag_tool_dead_letter(
                governance,
                tool_name=dl.call.tool_name,
                task_id=task_id,
            )
        _raise_if_halted(governance)
        logger.info(
            "L1 complete: %d/%d agents succeeded",
            len(findings),
            len(agent_results),
        )

        for finding in findings:
            _write_artifact(
                out_dir / "l1_findings" / f"{finding.task_id}.json",
                finding.model_dump_json(indent=2),
            )

        # --- Stage 3: CitationProcessor ---
        logger.info("CitProc: Processing %d findings", len(findings))
        async for event in c.citation_processor.process(findings, eid, client_id):
            yield event

        cit_result = await c.citation_processor.get_result()
        manifest = cit_result.manifest
        # Use canonicalized findings so downstream stages reference canonical
        # citation IDs (not source-instance IDs that may have been dedup-merged).
        findings = cit_result.canonicalized_findings
        logger.info("CitProc complete: %d citations", len(manifest.citations))

        _write_artifact(
            out_dir / "citation_manifest.json",
            manifest.model_dump_json(indent=2),
        )

        if self._checkpoint_store is not None:
            await self._checkpoint_store.save(
                eid,
                "POST_L1_CITPROC",
                serialize_post_l1_citproc(
                    findings, manifest, events_by_agent, agent_by_task, governance
                ),
            )

        # --- Stage 4: L1.5 Deliberation ---
        logger.info("L1.5: Deliberating over %d findings", len(findings))
        async for event in c.deliberation.deliberate(manifest, findings, eid, client_id):
            yield event

        confidence_map = await c.deliberation.get_confidence_map()
        logger.info(
            "L1.5 complete: %d claims, %d tiers",
            confidence_map.total_claims,
            confidence_map.tiers_populated,
        )

        _write_artifact(
            out_dir / "l15_confidence_map.json",
            confidence_map.model_dump_json(indent=2),
        )

        if self._checkpoint_store is not None:
            await self._checkpoint_store.save(
                eid,
                "POST_DELIBERATION",
                serialize_post_deliberation(confidence_map, governance),
            )

        # --- Stage 5: L2 Content Structuring ---
        eval_tasks = [
            task
            for task in spec.task_decomposition.tasks
            if governance.task_outcomes[task.id].renderable
        ]
        if self._max_eval_tasks is not None:
            eval_tasks = eval_tasks[: self._max_eval_tasks]
        logger.info("L2: Structuring content for %d renderable tasks", len(eval_tasks))
        async for event in c.content_structurer.structure(
            confidence_map,
            findings,
            spec,
            eval_tasks,
            eid,
            client_id,
        ):
            yield event
        outline = await c.content_structurer.get_outline()
        logger.info("L2 complete: %d outline sections", len(outline.sections))

        # Surface sprint-contract fallback as a WARN governance flag per
        # task. Silent fallback was the audit finding: operators need to
        # see when the generator failed even though L2/L4 continued.
        for fallback_task_id in sorted(c.content_structurer.get_fallback_task_ids()):
            from keystone.governance.models import (
                EnforcementAction,
                EnforcementScope,
                QualityFlag,
            )

            policy.apply_flag(
                governance,
                QualityFlag(
                    gate="sprint_contract_fallback",
                    action=EnforcementAction.WARN,
                    scope=EnforcementScope.TASK,
                    severity="warn",
                    message=(
                        f"Task {fallback_task_id} sprint contract negotiation "
                        "failed; L2 used the task-derived fallback contract."
                    ),
                    task_id=fallback_task_id,
                ),
                task_id=fallback_task_id,
            )

        if self._checkpoint_store is not None:
            await self._checkpoint_store.save(
                eid,
                "POST_STRUCTURING",
                serialize_post_structuring(
                    outline,
                    eval_tasks,
                    c.content_structurer.get_section_texts(),
                    c.content_structurer.get_sprint_contracts_map(),
                    c.content_structurer.get_fallback_task_ids(),
                    governance,
                ),
            )

        # --- Stage 6: L4 Evaluation ---
        logger.info(
            "L4: Evaluating %d/%d renderable tasks",
            len(eval_tasks),
            len(spec.task_decomposition.tasks),
        )
        evaluation_results: list[EvaluationResult] = []
        l4_tokens = 0
        for task in eval_tasks:
            # Find the finding for this task (if any)
            task_finding = next((f for f in findings if f.task_id == task.id), None)

            # L2 produces the per-task output_text; fall back to raw
            # finding text only if L2 produced nothing (defensive).
            output_text = await c.content_structurer.get_task_section_text(task.id)
            if not output_text and task_finding is not None:
                output_text = _finding_to_text(task_finding)

            # L2 negotiates the sprint contract per task; fall back to
            # direct generator call if L2 did not produce one.
            contract = await c.content_structurer.get_sprint_contract(task.id)
            if contract is None:
                contract = await c.sprint_contract_generator.generate(task, spec)

            # Build task-scoped sub-manifest so citation gating only checks
            # citations this task actually used (not the full engagement)
            task_manifest = _build_task_manifest(task_finding, manifest)

            # Build Layer 4 process context from the agent that handled this task
            process_context = _build_process_context(task, agent_by_task, events_by_agent, spec)

            # Fresh evaluator per task (each stores one result)
            intensity = _resolve_evaluation_intensity(spec)
            resolver = self._ensemble_panel_override or _resolve_ensemble_judges
            evaluator = Evaluator(
                llm=self._layer_llm(
                    "l4_evaluator",
                    fallback_tier=ModelTier.FLAGSHIP,
                    fallback_effort="high",
                ),
                extraction_llm=self._layer_llm(
                    "l4_extraction",
                    fallback_tier=ModelTier.STANDARD,
                ),
                profile=_resolve_evaluation_profile(spec),
                intensity=intensity,
                ensemble_llms=resolver(intensity, self._llm_factory),
                pass_threshold=self._pipeline_config.evaluator_pass_threshold,
                layer3_weight=self._pipeline_config.evaluator_layer3_weight,
            )
            async for event in evaluator.evaluate(
                output_text,
                contract,
                task,
                task_manifest,
                spec,
                process_context=process_context,
            ):
                yield event

            result = await evaluator.get_result()
            evaluation_results.append(result)
            if result.layer4_results is not None:
                l4_tokens += result.layer4_results.tokens_consumed
            policy.record_evaluation_outcome(governance, task, result)

        passed_count = sum(1 for r in evaluation_results if r.passed)
        logger.info("L4 complete: %d/%d passed", passed_count, len(evaluation_results))

        _write_artifact(
            out_dir / "l4_evaluation.json",
            json.dumps(
                [r.model_dump() for r in evaluation_results],
                indent=2,
                default=str,
            ),
        )

        coverage_flag = policy.evaluate_coverage(governance)
        if coverage_flag is not None:
            policy.apply_flag(governance, coverage_flag)
        _raise_if_halted(governance)

        if self._checkpoint_store is not None:
            await self._checkpoint_store.save(
                eid,
                "POST_EVALUATION",
                serialize_post_evaluation(evaluation_results, governance),
            )

        # Gate rendering on evaluation results: only render findings that passed.
        # This must key off passed_task_ids directly so unevaluated tasks do not
        # leak through when only a subset of tasks reached L4.
        passed_task_ids = {
            task_id
            for task_id, outcome in governance.task_outcomes.items()
            if outcome.renderable and outcome.evaluation_status == "passed"
        }
        evaluated_task_ids = {r.task_id for r in evaluation_results}
        failed_task_ids = {r.task_id for r in evaluation_results if not r.passed}
        finding_task_ids = {f.task_id for f in findings}
        unevaluated_task_ids = finding_task_ids - evaluated_task_ids
        dropped_task_ids = finding_task_ids - passed_task_ids

        if dropped_task_ids:
            logger.warning(
                "L4: excluding %d task(s) from deliverable (failed=%s, unevaluated=%s)",
                len(dropped_task_ids),
                failed_task_ids,
                unevaluated_task_ids,
            )
        passed_findings = [f for f in findings if f.task_id in passed_task_ids]

        # Filter confidence_map to only include claims from passed tasks.
        # Claims from failed or unevaluated tasks must not reach the renderer.
        filtered_confidence_map = _filter_confidence_map_by_passed_tasks(
            confidence_map, passed_task_ids
        )
        render_manifest = _filter_manifest_by_findings(passed_findings, manifest)
        render_evaluation_results = [
            result for result in evaluation_results if result.task_id in passed_task_ids
        ]
        filtered_outline = filter_outline_by_passed_tasks(outline, passed_task_ids)

        # --- Stage 7: Render (only passed findings + filtered confidence map + outline) ---
        markdown_output = c.renderer.render(
            spec,
            passed_findings,
            filtered_confidence_map,
            render_evaluation_results,
            render_manifest,
            filtered_outline,
        )

        _write_artifact(out_dir / "final_brief.md", markdown_output)

        self._result = PipelineResult(
            engagement_id=eid,
            client_id=client_id,
            spec=spec,
            findings=findings,  # Full findings preserved for record-keeping
            manifest=manifest,
            confidence_map=confidence_map,
            evaluation_results=evaluation_results,
            markdown_output=markdown_output,
            total_tokens=total_tokens,
            total_events=0,  # Updated by run() after counting
            tokens_by_layer={"l1": l1_tokens, "l4": l4_tokens},
        )

        # --- Stage 8: Write-back (GAP-13 + GAP-05 first slice) ---
        if self._observation_store is not None:
            async for event in self._write_back_outcomes(evaluation_results, spec, governance):
                yield event

        # Successful run — checkpoints are no longer needed.
        if self._checkpoint_store is not None:
            try:
                await self._checkpoint_store.delete(eid)
            except Exception:
                logger.warning("Failed to clean up checkpoints for %s", eid, exc_info=True)

    async def get_result(self) -> PipelineResult:
        """Return the pipeline result after run_with_events() completes."""
        if self._result is None:
            raise RuntimeError("run() or run_with_events() must complete first")
        return self._result

    async def resume_with_events(
        self,
        engagement_id: str,
        question: str,
        client_id: str,
        client_context: str | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Resume a pipeline run from the last completed checkpoint.

        Same return type as ``run_with_events``. Requires
        ``self._checkpoint_store`` to be set. Raises ``ValueError`` if no
        checkpoints exist for the engagement.
        """
        if self._checkpoint_store is None:
            raise RuntimeError("Cannot resume without a checkpoint_store")

        checkpoints = await self._checkpoint_store.load(engagement_id)
        if not checkpoints:
            raise ValueError(f"No checkpoints found for engagement {engagement_id}")

        last_completed = max(
            (s for s in STAGE_ORDER if s in checkpoints),
            key=STAGE_ORDER.index,
        )
        logger.info("Resuming engagement %s from %s", engagement_id, last_completed)

        # -- Deserialize all boundary variables from prior stages --
        spec_data = deserialize_post_spec(checkpoints["POST_SPEC"])
        spec = spec_data.spec
        eid = spec.research_spec.engagement_id

        findings: list[StructuredFinding] = []
        manifest: CitationManifest | None = None
        events_by_agent: dict[str, list[AnyPipelineEvent]] = {}
        agent_by_task: dict[str, AgentInstance] = {}
        confidence_map: ConfidenceMap | None = None
        outline: StructuredOutline | None = None
        eval_tasks: list[ResearchTask] = []
        evaluation_results: list[EvaluationResult] = []

        if "POST_L1_CITPROC" in checkpoints:
            l1_data = deserialize_post_l1_citproc(checkpoints["POST_L1_CITPROC"])
            findings = l1_data.findings
            manifest = l1_data.manifest
            events_by_agent = l1_data.events_by_agent
            agent_by_task = l1_data.agent_by_task

        if "POST_DELIBERATION" in checkpoints:
            delib_data = deserialize_post_deliberation(checkpoints["POST_DELIBERATION"])
            confidence_map = delib_data.confidence_map

        if "POST_STRUCTURING" in checkpoints:
            struct_data = deserialize_post_structuring(checkpoints["POST_STRUCTURING"])
            outline = struct_data.outline
            eval_tasks = struct_data.eval_tasks

        if "POST_EVALUATION" in checkpoints:
            eval_data = deserialize_post_evaluation(checkpoints["POST_EVALUATION"])
            evaluation_results = eval_data.evaluation_results

        # Governance is always taken from the latest checkpoint.
        governance_payload = checkpoints[last_completed]
        governance = GovernanceState.model_validate(governance_payload["governance"])

        # -- Reconstruct non-serializable infrastructure --
        self._result = None
        c = self._build_components()

        c.deliberation._effective_pipeline_profile = spec.research_spec.effective_pipeline_profile
        policy = ProfileExecutionPolicy(
            spec.research_spec.effective_pipeline_profile,
            low_agreement_threshold=self._pipeline_config.l5_low_agreement_threshold,
        )

        # Populate ContentStructurer if resuming at POST_STRUCTURING or later.
        if "POST_STRUCTURING" in checkpoints:
            struct_data = deserialize_post_structuring(checkpoints["POST_STRUCTURING"])
            c.content_structurer._outline = struct_data.outline
            c.content_structurer._section_texts = struct_data.section_texts
            c.content_structurer._sprint_contracts = struct_data.sprint_contracts
            c.content_structurer._fallback_task_ids = struct_data.fallback_task_ids

        total_tokens = 0

        # Wire retrieval unconditionally (idempotent).
        search_events: list[SearchCompleted] = []
        async for event in self._wire_retrieval(eid, client_id, search_events):
            yield event

        def _should_run(stage: str) -> bool:
            return STAGE_ORDER.index(stage) > STAGE_ORDER.index(last_completed)

        # -- Stage 1: L0 Specification --
        if _should_run("POST_SPEC"):
            logger.info("L0: Generating specification for '%s'", question[:80])
            async for event in c.spec_engine.generate_spec(
                question, client_id, client_context=client_context
            ):
                yield event
            spec = await c.spec_engine.get_spec()
            eid = spec.research_spec.engagement_id
            c.deliberation._effective_pipeline_profile = (
                spec.research_spec.effective_pipeline_profile
            )
            policy = ProfileExecutionPolicy(
                spec.research_spec.effective_pipeline_profile,
                low_agreement_threshold=self._pipeline_config.l5_low_agreement_threshold,
            )
            governance = policy.new_state(spec.task_decomposition.tasks)
            if not spec.validation_report.scope_valid:
                policy.flag_mece_failure(governance)
            _raise_if_halted(governance)
            if self._checkpoint_store is not None:
                await self._checkpoint_store.save(
                    eid, "POST_SPEC", serialize_post_spec(spec, governance)
                )

        # -- Stage 2+3: L1 Research + CitationProcessor --
        if _should_run("POST_L1_CITPROC"):
            logger.info("L1: Dispatching %d agents", len(spec.task_decomposition.tasks))
            assignments = self._build_assignments(spec, c.template_registry)
            dead_letters_before = len(self._gateway.dead_letters)
            agent_results = await c.agent_pool.execute_all(assignments)

            events_by_agent = {}
            agent_by_task = {task.id: agent for task, _, agent in assignments}
            for ar in agent_results:
                events_by_agent.setdefault(ar.agent_id, []).extend(ar.events)
                for event in ar.events:
                    yield event
            for search_event in search_events:
                events_by_agent.setdefault(search_event.agent_id, []).append(search_event)
                yield search_event

            findings = c.agent_pool.get_successful_findings(agent_results)
            l1_tokens = 0
            for f in findings:
                l1_tokens += f.tokens_consumed
            total_tokens += l1_tokens
            finding_by_task = {finding.task_id: finding for finding in findings}
            for task in spec.task_decomposition.tasks:
                policy.record_research_outcome(governance, task, finding_by_task.get(task.id))
            base_ceiling = self._pipeline_config.research_token_ceiling_per_task
            if self._pipeline_config.l1_orchestrator_enabled:
                token_ceiling = base_ceiling * (1 + self._pipeline_config.l1_max_sub_agents)
            else:
                token_ceiling = base_ceiling
            for f in findings:
                if f.tokens_consumed > token_ceiling:
                    policy.flag_cost_ceiling(
                        governance,
                        task_id=f.task_id,
                        tokens_used=f.tokens_consumed,
                        ceiling=token_ceiling,
                    )
            for ar in agent_results:
                if ar.degraded_dispatch:
                    policy.flag_degraded_dispatch(governance, task_id=ar.task_id)
            task_id_by_agent: dict[str, str] = {
                agent.agent_id: task_id for task_id, agent in agent_by_task.items()
            }
            for dl in self._gateway.dead_letters[dead_letters_before:]:
                task_id = task_id_by_agent.get(dl.call.agent_id, dl.call.agent_id)
                policy.flag_tool_dead_letter(
                    governance, tool_name=dl.call.tool_name, task_id=task_id
                )
            _raise_if_halted(governance)

            async for event in c.citation_processor.process(findings, eid, client_id):
                yield event
            cit_result = await c.citation_processor.get_result()
            manifest = cit_result.manifest
            findings = cit_result.canonicalized_findings

            if self._checkpoint_store is not None:
                await self._checkpoint_store.save(
                    eid,
                    "POST_L1_CITPROC",
                    serialize_post_l1_citproc(
                        findings, manifest, events_by_agent, agent_by_task, governance
                    ),
                )

        # -- Stage 4: L1.5 Deliberation --
        if _should_run("POST_DELIBERATION"):
            assert manifest is not None
            logger.info("L1.5: Deliberating over %d findings", len(findings))
            async for event in c.deliberation.deliberate(manifest, findings, eid, client_id):
                yield event
            confidence_map = await c.deliberation.get_confidence_map()
            if self._checkpoint_store is not None:
                await self._checkpoint_store.save(
                    eid,
                    "POST_DELIBERATION",
                    serialize_post_deliberation(confidence_map, governance),
                )

        # -- Stage 5: L2 Content Structuring --
        if _should_run("POST_STRUCTURING"):
            assert confidence_map is not None
            eval_tasks = [
                task
                for task in spec.task_decomposition.tasks
                if governance.task_outcomes[task.id].renderable
            ]
            if self._max_eval_tasks is not None:
                eval_tasks = eval_tasks[: self._max_eval_tasks]
            async for event in c.content_structurer.structure(
                confidence_map,
                findings,
                spec,
                eval_tasks,
                eid,
                client_id,
            ):
                yield event
            outline = await c.content_structurer.get_outline()

            for fallback_task_id in sorted(c.content_structurer.get_fallback_task_ids()):
                from keystone.governance.models import (
                    EnforcementAction,
                    EnforcementScope,
                    QualityFlag,
                )

                policy.apply_flag(
                    governance,
                    QualityFlag(
                        gate="sprint_contract_fallback",
                        action=EnforcementAction.WARN,
                        scope=EnforcementScope.TASK,
                        severity="warn",
                        message=(
                            f"Task {fallback_task_id} sprint contract negotiation "
                            "failed; L2 used the task-derived fallback contract."
                        ),
                        task_id=fallback_task_id,
                    ),
                    task_id=fallback_task_id,
                )

            if self._checkpoint_store is not None:
                await self._checkpoint_store.save(
                    eid,
                    "POST_STRUCTURING",
                    serialize_post_structuring(
                        outline,
                        eval_tasks,
                        c.content_structurer.get_section_texts(),
                        c.content_structurer.get_sprint_contracts_map(),
                        c.content_structurer.get_fallback_task_ids(),
                        governance,
                    ),
                )

        # -- Stage 6: L4 Evaluation --
        if _should_run("POST_EVALUATION"):
            assert outline is not None
            assert confidence_map is not None
            evaluation_results = []
            l4_tokens = 0
            for task in eval_tasks:
                task_finding = next((f for f in findings if f.task_id == task.id), None)
                output_text = await c.content_structurer.get_task_section_text(task.id)
                if not output_text and task_finding is not None:
                    output_text = _finding_to_text(task_finding)

                contract = await c.content_structurer.get_sprint_contract(task.id)
                if contract is None:
                    contract = await c.sprint_contract_generator.generate(task, spec)

                assert manifest is not None
                task_manifest = _build_task_manifest(task_finding, manifest)
                process_context = _build_process_context(task, agent_by_task, events_by_agent, spec)

                intensity = _resolve_evaluation_intensity(spec)
                resolver = self._ensemble_panel_override or _resolve_ensemble_judges
                evaluator = Evaluator(
                    llm=self._layer_llm(
                        "l4_evaluator",
                        fallback_tier=ModelTier.FLAGSHIP,
                        fallback_effort="high",
                    ),
                    extraction_llm=self._layer_llm(
                        "l4_extraction",
                        fallback_tier=ModelTier.STANDARD,
                    ),
                    profile=_resolve_evaluation_profile(spec),
                    intensity=intensity,
                    ensemble_llms=resolver(intensity, self._llm_factory),
                    pass_threshold=self._pipeline_config.evaluator_pass_threshold,
                    layer3_weight=self._pipeline_config.evaluator_layer3_weight,
                )
                async for event in evaluator.evaluate(
                    output_text,
                    contract,
                    task,
                    task_manifest,
                    spec,
                    process_context=process_context,
                ):
                    yield event
                result = await evaluator.get_result()
                evaluation_results.append(result)
                if result.layer4_results is not None:
                    l4_tokens += result.layer4_results.tokens_consumed
                policy.record_evaluation_outcome(governance, task, result)

            coverage_flag = policy.evaluate_coverage(governance)
            if coverage_flag is not None:
                policy.apply_flag(governance, coverage_flag)
            _raise_if_halted(governance)

            if self._checkpoint_store is not None:
                await self._checkpoint_store.save(
                    eid,
                    "POST_EVALUATION",
                    serialize_post_evaluation(evaluation_results, governance),
                )

        # -- Stage 7+8: Render + Write-back (always runs on resume) --
        assert manifest is not None
        assert confidence_map is not None
        assert outline is not None

        passed_task_ids = {
            task_id
            for task_id, outcome in governance.task_outcomes.items()
            if outcome.renderable and outcome.evaluation_status == "passed"
        }
        evaluated_task_ids = {r.task_id for r in evaluation_results}
        failed_task_ids = {r.task_id for r in evaluation_results if not r.passed}
        finding_task_ids = {f.task_id for f in findings}
        dropped_task_ids = finding_task_ids - passed_task_ids

        if dropped_task_ids:
            unevaluated_task_ids = finding_task_ids - evaluated_task_ids
            logger.warning(
                "L4: excluding %d task(s) from deliverable (failed=%s, unevaluated=%s)",
                len(dropped_task_ids),
                failed_task_ids,
                unevaluated_task_ids,
            )
        passed_findings = [f for f in findings if f.task_id in passed_task_ids]
        filtered_confidence_map = _filter_confidence_map_by_passed_tasks(
            confidence_map, passed_task_ids
        )
        render_manifest = _filter_manifest_by_findings(passed_findings, manifest)
        render_evaluation_results = [
            result for result in evaluation_results if result.task_id in passed_task_ids
        ]
        filtered_outline = filter_outline_by_passed_tasks(outline, passed_task_ids)

        markdown_output = c.renderer.render(
            spec,
            passed_findings,
            filtered_confidence_map,
            render_evaluation_results,
            render_manifest,
            filtered_outline,
        )

        self._result = PipelineResult(
            engagement_id=eid,
            client_id=client_id,
            spec=spec,
            findings=findings,
            manifest=manifest,
            confidence_map=confidence_map,
            evaluation_results=evaluation_results,
            markdown_output=markdown_output,
            total_tokens=total_tokens,
            total_events=0,
            tokens_by_layer={"l1": 0, "l4": l4_tokens if _should_run("POST_EVALUATION") else 0},
        )

        if self._observation_store is not None:
            async for event in self._write_back_outcomes(evaluation_results, spec, governance):
                yield event

        if self._checkpoint_store is not None:
            try:
                await self._checkpoint_store.delete(eid)
            except Exception:
                logger.warning("Failed to clean up checkpoints for %s", eid, exc_info=True)

    async def _wire_retrieval(
        self,
        engagement_id: str,
        client_id: str,
        search_events: list[SearchCompleted],
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Build the per-engagement retrieval service and register it on the gateway.

        Yields a :class:`ChunkIngested` event summarizing the ingest
        batch. ``search_events`` is the shared list the registered
        handlers append to whenever an agent calls a retrieval tool;
        the orchestrator drains it into the main event stream after
        agent execution completes.
        """

        factory = self._retrieval_service_factory
        if factory is None:
            return
        service = factory(engagement_id)
        register_retrieval_handlers(self._gateway, service, event_sink=search_events.append)
        records = self._evidence_records or []
        if not records:
            return
        logger.info("Retrieval: ingesting %d Lane E records", len(records))
        # Lane E records are pre-fetched reference material (PDFs, articles,
        # EDGAR filings), not mid-research agent output. They are ingested
        # as institutional memory (engagement_id=None) so they remain
        # visible to every engagement and pass through the bridge's
        # inter-agent isolation filter, while any future mid-research
        # ingest tagged with engagement_id=<active> is hidden from sibling
        # agents in the same engagement.
        ingest_result = await service.ingest_institutional(records)
        yield ChunkIngested(
            event_id=f"evt-{uuid4().hex[:12]}",
            engagement_id=engagement_id,
            client_id=client_id,
            artifact_count=ingest_result.artifacts_ingested,
            chunk_count=ingest_result.chunks_created + ingest_result.chunks_updated,
            chunks_created=ingest_result.chunks_created,
            chunks_updated=ingest_result.chunks_updated,
            chunks_skipped=ingest_result.chunks_skipped,
        )

    async def _write_back_outcomes(
        self,
        evaluation_results: list[EvaluationResult],
        spec: EngagementSpec,
        governance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Persist evaluation outcomes to the observation store (GAP-13).

        For each evaluated task, writes one observation row and yields
        an :class:`ObservationRecorded` event.
        """
        assert self._observation_store is not None
        store = self._observation_store
        eid = spec.research_spec.engagement_id
        client_id = spec.research_spec.client_id
        etype = spec.research_spec.engagement_type.value

        for seq, result in enumerate(evaluation_results):
            obs_type = "success" if result.passed else "rejection"
            category = _classify_observation_category(result)
            dim = _lowest_scoring_dimension(result)
            dim_scores = _extract_dimension_scores(result)
            task_flags = [
                f.gate for f in governance.flags if getattr(f, "task_id", None) == result.task_id
            ]
            obs_id = f"OBS-{eid[:8]}-{result.task_id[:8]}-{seq:03d}"

            try:
                await store.record(
                    observation_id=obs_id,
                    client_id=client_id,
                    engagement_id=eid,
                    engagement_type=etype,
                    task_id=result.task_id,
                    obs_type=obs_type,
                    category=category,
                    dimension=dim,
                    composite_score=result.overall_score,
                    dimension_scores=dim_scores,
                    governance_flags=task_flags,
                )
                yield ObservationRecorded(
                    event_id=f"evt-{uuid4().hex[:12]}",
                    engagement_id=eid,
                    client_id=client_id,
                    observation_id=obs_id,
                    observation_type=obs_type,
                    category=category,
                    dimension=dim,
                )
            except Exception:
                logger.warning(
                    "Failed to record observation for task %s",
                    result.task_id,
                    exc_info=True,
                )

        logger.info(
            "Write-back: recorded %d observations (%d passed, %d rejected)",
            len(evaluation_results),
            sum(1 for r in evaluation_results if r.passed),
            sum(1 for r in evaluation_results if not r.passed),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_assignments(
        self,
        spec: EngagementSpec,
        template_registry: TemplateRegistry,
    ) -> list[tuple[ResearchTask, EngagementSpec, AgentInstance]]:
        """Create (task, spec, agent_instance) tuples for the AgentPool."""
        assignments = []
        eid = spec.research_spec.engagement_id
        cid = spec.research_spec.client_id
        etype = spec.research_spec.engagement_type

        for task in spec.task_decomposition.tasks:
            match = template_registry.match(task, etype)
            agent_id = f"agent_{task.id}_{uuid.uuid4().hex[:6]}"

            instance = AgentInstance(
                agent_id=agent_id,
                engagement_id=eid,
                client_id=cid,
                definition=match.template,
                working_dir=f"/tmp/keystone/{eid}/{agent_id}",
                task_ids=[task.id],
            )
            assignments.append((task, spec, instance))

        return assignments


def _build_process_context(
    task: ResearchTask,
    agent_by_task: dict[str, AgentInstance],
    events_by_agent: dict[str, list[AnyPipelineEvent]],
    spec: EngagementSpec,
) -> ProcessContext | None:
    """Assemble the Layer 4 ProcessContext for a single evaluation task.

    Returns None when the task has no agent or no event trail, so the
    evaluator skips Layer 4 rather than running it against empty input.
    """
    agent = agent_by_task.get(task.id)
    if agent is None:
        return None

    events = events_by_agent.get(agent.agent_id, [])
    if not events:
        return None

    return ProcessContext(
        agent_id=agent.agent_id,
        task=task,
        agent=agent,
        events=list(events),
        issue_tree=spec.issue_tree,
    )


def _write_artifact(path: Path, content: str) -> None:
    """Best-effort write of an intermediate pipeline artifact."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    except Exception:
        logger.warning("Failed to write artifact %s", path, exc_info=True)


def _finding_to_text(finding: StructuredFinding) -> str:
    """Convert a StructuredFinding to evaluator-readable text."""
    parts = [f"Task: {finding.task_id}", f"Agent: {finding.agent_id}"]
    for i, claim in enumerate(finding.claims, 1):
        parts.append(f"\nClaim {i}: {claim.text}")
        parts.append(f"  Evidence: {claim.evidence}")
        parts.append(f"  Confidence: {claim.confidence:.0%} ({claim.confidence_tier.value})")
        cite_ids = ", ".join(claim.citation_ids or [c.citation_id for c in claim.citations])
        if cite_ids:
            parts.append(f"  Citations: {cite_ids}")
        if claim.caveats:
            parts.append(f"  Caveats: {'; '.join(claim.caveats)}")

    if finding.gaps:
        parts.append(f"\nGaps: {'; '.join(finding.gaps)}")
    if finding.absence_report:
        parts.append(f"Absence Report: {'; '.join(finding.absence_report)}")

    return "\n".join(parts)


def _build_task_manifest(
    finding: StructuredFinding | None,
    full_manifest: CitationManifest,
) -> CitationManifest:
    """Build a task-scoped sub-manifest containing only citations this task used.

    This prevents a fabricated citation in an unrelated task from failing
    this task's citation gate. The full manifest is preserved for
    engagement-level observability.
    """
    if finding is None:
        return CitationManifest(
            manifest_id=f"{full_manifest.manifest_id}_empty",
            engagement_id=full_manifest.engagement_id,
            client_id=full_manifest.client_id,
            citations=[],
        )

    # Collect all citation IDs referenced by this finding's claims.
    # Prefer claim.citation_ids (canonical CAN-* IDs rewritten by CitationProcessor)
    # over claim.citations[].citation_id (original CIT-* source-instance IDs).
    # After dedup, the manifest only contains CAN-* IDs, so using source-instance
    # IDs here would produce an empty sub-manifest and silently skip fabrication checks.
    task_citation_ids: set[str] = set()
    for claim in finding.claims:
        if claim.citation_ids:
            task_citation_ids.update(claim.citation_ids)
        else:
            for cit in claim.citations:
                task_citation_ids.add(cit.citation_id)

    # Filter manifest to only this task's citations
    task_citations = [c for c in full_manifest.citations if c.citation_id in task_citation_ids]

    return CitationManifest(
        manifest_id=f"{full_manifest.manifest_id}_{finding.task_id}",
        engagement_id=full_manifest.engagement_id,
        client_id=full_manifest.client_id,
        citations=task_citations,
    )


def _filter_manifest_by_findings(
    findings: list[StructuredFinding],
    full_manifest: CitationManifest,
) -> CitationManifest:
    """Keep only manifest data referenced by the findings that remain renderable."""
    source_to_canonical = {
        alias.source_instance_id: alias.canonical_citation_id for alias in full_manifest.aliases
    }

    citation_ids: set[str] = set()
    surviving_task_ids = {finding.task_id for finding in findings}
    for finding in findings:
        for claim in finding.claims:
            claim_citation_ids = claim.citation_ids or [
                citation.citation_id for citation in claim.citations
            ]
            for citation_id in claim_citation_ids:
                citation_ids.add(source_to_canonical.get(citation_id, citation_id))

    filtered_citations = [
        citation for citation in full_manifest.citations if citation.citation_id in citation_ids
    ]
    filtered_corroboration_pairs = [
        pair
        for pair in full_manifest.corroboration_pairs
        if pair.citation_a in citation_ids and pair.citation_b in citation_ids
    ]
    filtered_dead_urls = [
        citation_id for citation_id in full_manifest.dead_urls if citation_id in citation_ids
    ]
    filtered_fabrication_flags = [
        citation_id
        for citation_id in full_manifest.fabrication_flags
        if citation_id in citation_ids
    ]
    filtered_aliases = [
        alias
        for alias in full_manifest.aliases
        if alias.canonical_citation_id in citation_ids and alias.task_id in surviving_task_ids
    ]
    surviving_agents_by_citation: dict[str, list[str]] = {}
    for alias in filtered_aliases:
        if not alias.agent_id:
            continue
        agent_ids = surviving_agents_by_citation.setdefault(alias.canonical_citation_id, [])
        if alias.agent_id not in agent_ids:
            agent_ids.append(alias.agent_id)

    pruned_citations = [
        citation.model_copy(
            update={
                "found_by_agents": surviving_agents_by_citation.get(
                    citation.citation_id,
                    list(citation.found_by_agents),
                )
            }
        )
        for citation in filtered_citations
    ]

    return full_manifest.model_copy(
        update={
            "citations": pruned_citations,
            "corroboration_pairs": filtered_corroboration_pairs,
            "dead_urls": filtered_dead_urls,
            "fabrication_flags": filtered_fabrication_flags,
            "aliases": filtered_aliases,
        }
    )


def _filter_confidence_map_by_passed_tasks(
    confidence_map: ConfidenceMap,
    passed_task_ids: set[str],
) -> ConfidenceMap:
    """Remove claims from failed or unevaluated tasks.

    Keeps a claim only if its task_ids intersects passed_task_ids. Claims
    with empty task_ids have no provenance and are excluded by default.
    Rebuilds provenance_index to match the filtered tier lists.

    This is the concrete implementation of PostSynthesisVerifierContract.
    The Protocol in contracts.py defines the interface for Wave 3.
    """

    def _surviving_task_ids(task_ids: list[str]) -> list[str]:
        surviving: list[str] = []
        seen: set[str] = set()
        for task_id in task_ids:
            if task_id in passed_task_ids and task_id not in seen:
                surviving.append(task_id)
                seen.add(task_id)
        return surviving

    def _filter_claims(claims):
        filtered = []
        for claim in claims:
            surviving_task_ids = _surviving_task_ids(list(claim.task_ids))
            if not surviving_task_ids:
                continue

            update = {"task_ids": surviving_task_ids}
            if hasattr(claim, "corroboration_count"):
                # Recompute from surviving task provenance so failed or
                # unevaluated support cannot leak into render surfaces.
                update["corroboration_count"] = len(surviving_task_ids)

            filtered.append(claim.model_copy(update=update))
        return filtered

    filtered_high = _filter_claims(confidence_map.high_confidence_above_80pct)
    filtered_moderate = _filter_claims(confidence_map.moderate_confidence_60_80pct)
    filtered_weak = _filter_claims(confidence_map.weak_confidence_50_60pct)
    filtered_contested = _filter_claims(confidence_map.contested_below_50pct)
    filtered_insufficient = _filter_claims(confidence_map.insufficient_evidence)

    # Rebuild provenance_index for surviving claims only
    all_surviving = (
        filtered_high
        + filtered_moderate
        + filtered_weak
        + filtered_contested
        + filtered_insufficient
    )
    filtered_provenance = {
        c.aggregated_claim_id: list(c.task_ids)
        for c in all_surviving
        if c.aggregated_claim_id is not None
    }

    filtered_gaps: list[str] = []
    filtered_gap_provenance: dict[str, list[str]] = {}
    for gap in confidence_map.gaps_identified:
        task_ids = _surviving_task_ids(list(confidence_map.gap_provenance.get(gap, [])))
        if task_ids:
            filtered_gaps.append(gap)
            filtered_gap_provenance[gap] = task_ids

    return ConfidenceMap(
        engagement_id=confidence_map.engagement_id,
        client_id=confidence_map.client_id,
        high_confidence_above_80pct=filtered_high,
        moderate_confidence_60_80pct=filtered_moderate,
        weak_confidence_50_60pct=filtered_weak,
        contested_below_50pct=filtered_contested,
        insufficient_evidence=filtered_insufficient,
        gaps_identified=filtered_gaps,
        absence_report=confidence_map.absence_report,
        gap_provenance=filtered_gap_provenance,
        provenance_index=filtered_provenance,
    )


def _resolve_evaluation_profile(spec: EngagementSpec) -> EvaluationProfile:
    """Route the persisted evaluation profile from ResearchSpec."""
    stored_profile = spec.research_spec.effective_evaluation_profile
    return EvaluationProfile(
        stored_profile.value if hasattr(stored_profile, "value") else stored_profile
    )


def _resolve_evaluation_intensity(spec: EngagementSpec) -> EvaluationIntensity:
    """Make pipeline profile load-bearing for evaluator depth."""
    profile = spec.research_spec.effective_pipeline_profile
    if profile == PipelineProfile.LIGHT:
        return EvaluationIntensity.LIGHT_TOUCH
    if profile == PipelineProfile.DEEP:
        return EvaluationIntensity.DEEP
    return EvaluationIntensity.STANDARD


def _resolve_ensemble_judges(
    intensity: EvaluationIntensity,
    llm_factory: Callable[[ModelTier], LLMCallable],
) -> list[tuple[str, LLMCallable]] | None:
    """Compose the Layer 5 judge panel for the given evaluation intensity.

    Judge-panel selection rationale:
    - LIGHT_TOUCH skips Layer 3 entirely; Layer 5 must be inert.
    - STANDARD uses two independent FLAGSHIP (Opus) runs. Same model,
      different calls — sampling stochasticity between runs exposes
      unstable rubric scores while avoiding the weaker Haiku tier, which
      is a classification/extraction model without the reasoning depth
      needed for a nuanced 10-dimension rubric. Zero Play Favorites risk
      (neither judge is the STANDARD/Sonnet tier that L1 generates with).
    - DEEP adds one STANDARD (Sonnet) judge alongside the two FLAGSHIP
      judges for cross-model diversity. Sonnet IS the L1 generator tier,
      so there is a Play Favorites risk, but it is bounded to 1-of-3
      votes by median aggregation and is further surfaced by the
      agreement_level signal on Layer5Result. The STANDARD slot here is
      an INTERIM choice: it is intended to be replaced by an external
      provider (GPT-5.4, Gemini) once a second provider family is wired
      into the LLM client factory. Until then, Sonnet is the best
      available cross-model diversity signal inside the Anthropic
      family. See TODO.md "L5 ensemble follow-ups" for the external-
      provider tracking item.

    Haiku (FAST tier) is deliberately NOT used as a judge. FAST stays in
    the research-agent fallback chain (error_recovery.FALLBACK_CHAIN)
    and in the Layer 1 deterministic fact decomposer where its
    extraction properties are appropriate, but judging a 10-dimension
    rubric is a reasoning task that requires at least Sonnet-class.
    """
    if intensity == EvaluationIntensity.LIGHT_TOUCH:
        return None
    flagship_a = llm_factory(ModelTier.FLAGSHIP)
    flagship_b = llm_factory(ModelTier.FLAGSHIP)
    if intensity == EvaluationIntensity.DEEP:
        return [
            ("flagship_a", flagship_a),
            ("flagship_b", flagship_b),
            # INTERIM slot: swap to an external provider (GPT-5.4 / Gemini)
            # when one is integrated. Sonnet is the L1 generator tier, so
            # Play Favorites is mitigated by median aggregation (1 of 3).
            ("standard_crossmodel", llm_factory(ModelTier.STANDARD)),
        ]
    return [
        ("flagship_a", flagship_a),
        ("flagship_b", flagship_b),
    ]


def _resolve_layer_tier_or(
    pipeline_config: PipelineConfig,
    layer_name: str,
    default: ModelTier,
) -> ModelTier:
    """Read a layer's configured ModelTier from PipelineConfig.model_mixing.

    Falls back to ``default`` when the layer is unknown or the config's
    value is not a valid tier string. Used by orchestrator code that has
    to report the tier (e.g. truthful AnalystSpawned events) without
    re-deriving the mapping.
    """
    raw = getattr(pipeline_config.model_mixing, layer_name, None)
    if raw is None:
        return default
    try:
        return ModelTier(raw)
    except ValueError:
        return default


def _raise_if_halted(governance) -> None:
    if not governance.halted:
        return

    critical_flags = [flag for flag in governance.flags if flag.action in {"halt", "escalate"}]
    if critical_flags:
        raise RuntimeError(critical_flags[-1].message)
    raise RuntimeError("Pipeline halted by governance policy.")


# ---------------------------------------------------------------------------
# GAP-13: Observation classification helpers
# ---------------------------------------------------------------------------


def _classify_observation_category(result: EvaluationResult) -> int:
    """Derive ObservationCategory (1/2/3) from the evaluation result.

    1 (STRUCTURAL) — citation gate failed (Layer 2 fabrication).
    2 (ANALYTICAL) — a Tier 1 rubric dimension fell below its floor.
    3 (JUDGMENT)   — everything else (Tier 2 failure, blend, trajectory).
    """
    if not result.layer2_results.gate_passed:
        return 1

    if result.layer3_results is not None and result.layer3_results.dimension_scores:
        from keystone.evaluator.rubric_config import (
            TIER_1_DIMENSIONS,
            TIER_1_FLOOR_THRESHOLDS,
        )

        for ds in result.layer3_results.dimension_scores:
            if ds.dimension in TIER_1_DIMENSIONS:
                floor = TIER_1_FLOOR_THRESHOLDS.get(ds.dimension, 0.0)
                if ds.score < floor:
                    return 2

    return 3


def _lowest_scoring_dimension(result: EvaluationResult) -> str:
    """Return the name of the lowest-scoring rubric dimension, or 'unknown'."""
    if result.layer3_results is None or not result.layer3_results.dimension_scores:
        return "unknown"
    lowest = min(result.layer3_results.dimension_scores, key=lambda d: d.score)
    return lowest.dimension.value


def _extract_dimension_scores(result: EvaluationResult) -> dict[str, float]:
    """Build a {dimension_name: score} dict from the Layer 3 results."""
    if result.layer3_results is None or not result.layer3_results.dimension_scores:
        return {}
    return {ds.dimension.value: ds.score for ds in result.layer3_results.dimension_scores}
