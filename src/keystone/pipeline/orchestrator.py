"""Pipeline orchestrator: the main() that wires all components end-to-end.

Runs the full DPVI pipeline:
  L0 (Specification) -> L1 (Research Agents) -> CitationProcessor ->
  L1.5 (Deliberation) -> L4 (Evaluator) -> MarkdownRenderer

Yields AnyPipelineEvent throughout for observability.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator, Callable

from pydantic import BaseModel, Field

from keystone.citation.processor import CitationProcessor
from keystone.deliberation.deliberation import Deliberation
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.retry import LLMCallable
from keystone.events import AnyPipelineEvent
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.models.agents import AgentDefinition, AgentInstance, AgentRole
from keystone.models.citations import CitationManifest
from keystone.models.confidence import ConfidenceMap
from keystone.models.evaluation import EvaluationResult, SprintContract
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ModelTier, ResearchTask
from keystone.pipeline.markdown_renderer import MarkdownRenderer
from keystone.research.agent_pool import AgentPool
from keystone.specification.spec_engine import SpecificationEngine
from keystone.specification.template_registry import TemplateRegistry

logger = logging.getLogger(__name__)


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
    ) -> None:
        self._llm_factory = llm_factory
        self._gateway = gateway
        self._db_session_factory = db_session_factory

        # L0: Specification Engine (Flagship)
        self._spec_engine = SpecificationEngine(
            llm=llm_factory(ModelTier.FLAGSHIP),
            template_registry=TemplateRegistry(),
            db_session_factory=db_session_factory,
        )

        # L1: Agent Pool (Standard)
        self._agent_pool = AgentPool(
            llm=llm_factory(ModelTier.STANDARD),
            gateway=gateway,
        )

        # CitationProcessor (no LLM)
        self._citation_processor = CitationProcessor()

        # L1.5: Deliberation (Standard analysts, Flagship aggregator)
        self._deliberation = Deliberation(
            analyst_llm=llm_factory(ModelTier.STANDARD),
            judge_llm=llm_factory(ModelTier.FLAGSHIP),
            db_session_factory=db_session_factory,
        )

        # L4: Evaluator (Flagship)
        self._evaluator = Evaluator(
            llm=llm_factory(ModelTier.FLAGSHIP),
        )

        # L3 MVP: Markdown renderer (no LLM)
        self._renderer = MarkdownRenderer()

        # Internal state
        self._result: PipelineResult | None = None
        self._template_registry = TemplateRegistry()

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

        After exhausting the iterator, call get_result() for the PipelineResult.
        """
        total_tokens = 0

        # --- Stage 1: L0 Specification ---
        logger.info("L0: Generating specification for '%s'", question[:80])
        async for event in self._spec_engine.generate_spec(
            question, client_id, client_context=client_context
        ):
            yield event

        spec = await self._spec_engine.get_spec()
        eid = spec.research_spec.engagement_id
        logger.info("L0 complete: %d tasks", len(spec.task_decomposition.tasks))

        # --- Stage 2: L1 Research Agents ---
        logger.info("L1: Dispatching %d agents", len(spec.task_decomposition.tasks))
        assignments = self._build_assignments(spec)
        agent_results = await self._agent_pool.execute_all(assignments)

        # Collect events from agent results
        for ar in agent_results:
            for event in ar.events:
                yield event

        findings = self._agent_pool.get_successful_findings(agent_results)
        for f in findings:
            total_tokens += f.tokens_consumed
        logger.info(
            "L1 complete: %d/%d agents succeeded",
            len(findings),
            len(agent_results),
        )

        # --- Stage 3: CitationProcessor ---
        logger.info("CitProc: Processing %d findings", len(findings))
        async for event in self._citation_processor.process(findings, eid, client_id):
            yield event

        manifest = await self._citation_processor.get_manifest()
        logger.info("CitProc complete: %d citations", len(manifest.citations))

        # --- Stage 4: L1.5 Deliberation ---
        logger.info("L1.5: Deliberating over %d findings", len(findings))
        async for event in self._deliberation.deliberate(
            manifest, findings, eid, client_id
        ):
            yield event

        confidence_map = await self._deliberation.get_confidence_map()
        logger.info(
            "L1.5 complete: %d claims, %d tiers",
            confidence_map.total_claims,
            confidence_map.tiers_populated,
        )

        # --- Stage 5: L4 Evaluation ---
        logger.info("L4: Evaluating %d tasks", len(spec.task_decomposition.tasks))
        evaluation_results: list[EvaluationResult] = []
        for task in spec.task_decomposition.tasks:
            # Find the finding for this task (if any)
            task_finding = next(
                (f for f in findings if f.task_id == task.id), None
            )
            output_text = _finding_to_text(task_finding) if task_finding else ""

            contract = _build_sprint_contract(task, eid, client_id)

            # Fresh evaluator per task (each stores one result)
            evaluator = Evaluator(llm=self._llm_factory(ModelTier.FLAGSHIP))
            async for event in evaluator.evaluate(
                output_text, contract, task, manifest, spec
            ):
                yield event

            result = await evaluator.get_result()
            evaluation_results.append(result)

        passed = sum(1 for r in evaluation_results if r.passed)
        logger.info("L4 complete: %d/%d passed", passed, len(evaluation_results))

        # --- Stage 6: Render ---
        markdown_output = self._renderer.render(
            spec, findings, confidence_map, evaluation_results, manifest
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
        self, spec: EngagementSpec
    ) -> list[tuple[ResearchTask, EngagementSpec, AgentInstance]]:
        """Create (task, spec, agent_instance) tuples for the AgentPool."""
        assignments = []
        eid = spec.research_spec.engagement_id
        cid = spec.research_spec.client_id
        etype = spec.research_spec.engagement_type

        for task in spec.task_decomposition.tasks:
            match = self._template_registry.match(task, etype)
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
