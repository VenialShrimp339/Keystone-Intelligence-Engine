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

from pydantic import BaseModel, Field

from keystone.citation.processor import CitationProcessor
from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.retry import LLMCallable
from keystone.events import AnyPipelineEvent
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.llm_client import get_deep_research_callable
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole
from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.evaluation import EvaluationResult, SprintContract
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ModelTier, ResearchTask
from keystone.pipeline.markdown_renderer import MarkdownRenderer
from keystone.research.agent_pool import AgentPool
from keystone.research.error_recovery import ErrorRecovery
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.template_registry import TemplateRegistry

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
    renderer: MarkdownRenderer
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
    ) -> None:
        self._llm_factory = llm_factory
        self._gateway = gateway
        self._db_session_factory = db_session_factory
        self._max_eval_tasks = max_eval_tasks
        # Internal run state (overwritten on each run).
        self._result: PipelineResult | None = None
        # Tests may call _build_components(), mutate fields, then assign here
        # before calling run() to inject mocks.
        self._pending_components: PipelineComponents | None = None

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
            deep_llm = get_deep_research_callable()

        return PipelineComponents(
            spec_engine=SpecificationEngine(
                llm=self._llm_factory(ModelTier.FLAGSHIP),
                template_registry=TemplateRegistry(),
                db_session_factory=self._db_session_factory,
            ),
            agent_pool=AgentPool(
                llm=self._llm_factory(ModelTier.STANDARD),
                gateway=self._gateway,
                deep_llm=deep_llm,
                error_recovery=ErrorRecovery(llm_factory=self._llm_factory),
            ),
            citation_processor=CitationProcessor(),
            deliberation=Deliberation(
                analyst_llm=self._llm_factory(ModelTier.STANDARD),
                judge_llm=self._llm_factory(ModelTier.FLAGSHIP),
                db_session_factory=self._db_session_factory,
            ),
            renderer=MarkdownRenderer(),
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
        logger.info("L0 complete: %d tasks", len(spec.task_decomposition.tasks))

        # --- Stage 2: L1 Research Agents ---
        logger.info("L1: Dispatching %d agents", len(spec.task_decomposition.tasks))
        assignments = self._build_assignments(spec, c.template_registry)
        agent_results = await c.agent_pool.execute_all(assignments)

        # Collect events from agent results
        for ar in agent_results:
            for event in ar.events:
                yield event

        findings = c.agent_pool.get_successful_findings(agent_results)
        for f in findings:
            total_tokens += f.tokens_consumed
        logger.info(
            "L1 complete: %d/%d agents succeeded",
            len(findings),
            len(agent_results),
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

        # --- Stage 4: L1.5 Deliberation ---
        logger.info("L1.5: Deliberating over %d findings", len(findings))
        async for event in c.deliberation.deliberate(
            manifest, findings, eid, client_id
        ):
            yield event

        confidence_map = await c.deliberation.get_confidence_map()
        logger.info(
            "L1.5 complete: %d claims, %d tiers",
            confidence_map.total_claims,
            confidence_map.tiers_populated,
        )

        # --- Stage 5: L4 Evaluation ---
        eval_tasks = spec.task_decomposition.tasks
        if self._max_eval_tasks is not None:
            eval_tasks = eval_tasks[: self._max_eval_tasks]
        logger.info("L4: Evaluating %d/%d tasks", len(eval_tasks), len(spec.task_decomposition.tasks))
        evaluation_results: list[EvaluationResult] = []
        for task in eval_tasks:
            # Find the finding for this task (if any)
            task_finding = next(
                (f for f in findings if f.task_id == task.id), None
            )
            output_text = _finding_to_text(task_finding) if task_finding else ""

            contract = _build_sprint_contract(task, eid, client_id)

            # Build task-scoped sub-manifest so citation gating only checks
            # citations this task actually used (not the full engagement)
            task_manifest = _build_task_manifest(task_finding, manifest)

            # Fresh evaluator per task (each stores one result)
            evaluator = Evaluator(llm=self._llm_factory(ModelTier.FLAGSHIP))
            async for event in evaluator.evaluate(
                output_text, contract, task, task_manifest, spec
            ):
                yield event

            result = await evaluator.get_result()
            evaluation_results.append(result)

        passed_count = sum(1 for r in evaluation_results if r.passed)
        failed_count = len(evaluation_results) - passed_count
        logger.info("L4 complete: %d/%d passed", passed_count, len(evaluation_results))

        # Gate rendering on evaluation results: only render findings that passed.
        # This must key off passed_task_ids directly so unevaluated tasks do not
        # leak through when only a subset of tasks reached L4.
        passed_task_ids = {r.task_id for r in evaluation_results if r.passed}
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

        # --- Stage 6: Render (only passed findings + filtered confidence map) ---
        markdown_output = c.renderer.render(
            spec,
            passed_findings,
            filtered_confidence_map,
            evaluation_results,
            render_manifest,
        )

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
        )

    async def get_result(self) -> PipelineResult:
        """Return the pipeline result after run_with_events() completes."""
        if self._result is None:
            raise RuntimeError("run() or run_with_events() must complete first")
        return self._result

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


def _finding_to_text(finding: StructuredFinding) -> str:
    """Convert a StructuredFinding to evaluator-readable text."""
    parts = [f"Task: {finding.task_id}", f"Agent: {finding.agent_id}"]
    for i, claim in enumerate(finding.claims, 1):
        parts.append(f"\nClaim {i}: {claim.text}")
        parts.append(f"  Evidence: {claim.evidence}")
        parts.append(f"  Confidence: {claim.confidence:.0%} ({claim.confidence_tier.value})")
        if claim.citations:
            cite_ids = ", ".join(c.citation_id for c in claim.citations)
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
    task_citations = [
        c for c in full_manifest.citations if c.citation_id in task_citation_ids
    ]

    return CitationManifest(
        manifest_id=f"{full_manifest.manifest_id}_{finding.task_id}",
        engagement_id=full_manifest.engagement_id,
        client_id=full_manifest.client_id,
        citations=task_citations,
    )


def _build_sprint_contract(
    task: ResearchTask, engagement_id: str, client_id: str
) -> SprintContract:
    """Build a SprintContract from a ResearchTask's acceptance criteria."""
    return SprintContract(
        section_id=f"sec_{task.id}",
        engagement_id=engagement_id,
        client_id=client_id,
        task_id=task.id,
        section_title=task.deliverable_destination,
        acceptance_criteria=task.acceptance_criteria,
    )


def _filter_manifest_by_findings(
    findings: list[StructuredFinding],
    full_manifest: CitationManifest,
) -> CitationManifest:
    """Keep only citations referenced by the findings that remain renderable."""
    source_to_canonical = {
        alias.source_instance_id: alias.canonical_citation_id
        for alias in full_manifest.aliases
    }

    citation_ids: set[str] = set()
    for finding in findings:
        for claim in finding.claims:
            claim_citation_ids = claim.citation_ids or [
                citation.citation_id for citation in claim.citations
            ]
            for citation_id in claim_citation_ids:
                citation_ids.add(source_to_canonical.get(citation_id, citation_id))

    filtered_citations = [
        citation
        for citation in full_manifest.citations
        if citation.citation_id in citation_ids
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
        if alias.canonical_citation_id in citation_ids
    ]

    return full_manifest.model_copy(
        update={
            "citations": filtered_citations,
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

    def _keep(task_ids: list[str]) -> bool:
        return bool(task_ids) and bool(set(task_ids) & passed_task_ids)

    filtered_high = [c for c in confidence_map.high_confidence_above_80pct if _keep(list(c.task_ids))]
    filtered_moderate = [c for c in confidence_map.moderate_confidence_60_80pct if _keep(list(c.task_ids))]
    filtered_weak = [c for c in confidence_map.weak_confidence_50_60pct if _keep(list(c.task_ids))]
    filtered_contested = [c for c in confidence_map.contested_below_50pct if _keep(list(c.task_ids))]
    filtered_insufficient = [c for c in confidence_map.insufficient_evidence if _keep(list(c.task_ids))]

    # Rebuild provenance_index for surviving claims only
    all_surviving = (
        filtered_high + filtered_moderate + filtered_weak
        + filtered_contested + filtered_insufficient
    )
    surviving_agg_ids: set[str] = {
        c.aggregated_claim_id
        for c in all_surviving
        if c.aggregated_claim_id is not None
    }
    filtered_provenance = {
        agg_id: task_ids
        for agg_id, task_ids in confidence_map.provenance_index.items()
        if agg_id in surviving_agg_ids
    }

    return ConfidenceMap(
        engagement_id=confidence_map.engagement_id,
        client_id=confidence_map.client_id,
        high_confidence_above_80pct=filtered_high,
        moderate_confidence_60_80pct=filtered_moderate,
        weak_confidence_50_60pct=filtered_weak,
        contested_below_50pct=filtered_contested,
        insufficient_evidence=filtered_insufficient,
        gaps_identified=confidence_map.gaps_identified,
        absence_report=confidence_map.absence_report,
        provenance_index=filtered_provenance,
    )
