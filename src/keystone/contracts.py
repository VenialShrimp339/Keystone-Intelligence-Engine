"""Handoff contract interfaces for the Keystone Intelligence Engine.

Based on CAPSTONE-PLAN-v2.md Section 2 handoff contract table.
Every pipeline boundary has an explicit contract defining input format,
output format, quality threshold, and completion signal.

These are Protocol classes (structural subtyping) so that implementations
don't need to inherit from them. This follows the nano-claude-code pattern
where the Tool interface is a protocol, not a class hierarchy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from keystone.events import (
        AnyPipelineEvent,
    )
    from keystone.hitl.schemas import GateResponse
    from keystone.models.agents import AgentInstance
    from keystone.models.citations import CitationManifest
    from keystone.models.confidence import ConfidenceMap
    from keystone.models.evaluation import EvaluationResult, SprintContract
    from keystone.models.observations import ObservationEntry
    from keystone.models.research import EngagementSpec, StructuredFinding
    from keystone.models.tasks import ResearchTask

# ---------------------------------------------------------------------------
# L0: Specification Engine -> Research Agents
# ---------------------------------------------------------------------------

@runtime_checkable
class SpecificationEngineContract(Protocol):
    """Contract for the Specification Engine (L0).

    Input:  User question (natural language)
    Output: EngagementSpec (RESEARCH.md + tasks + validation report)
    Gate:   All 4 validation checks must pass before agent dispatch.
    """

    async def generate_spec(
        self,
        question: str,
        client_id: str,
        client_context: str | None = None,
        constraints: list[str] | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Generate RESEARCH.md and decompose into tasks.

        Yields SpecificationGenerated, TasksDecomposed, AgentDispatched events.
        Final yield contains the complete EngagementSpec.
        """
        ...

    async def get_spec(self) -> EngagementSpec:
        """Return the generated engagement specification."""
        ...


# ---------------------------------------------------------------------------
# L1: Research Agents -> CitationProcessor
# ---------------------------------------------------------------------------

@runtime_checkable
class ResearchAgentContract(Protocol):
    """Contract for a single L1 Research Agent.

    Input:  ResearchTask + RESEARCH.md + assigned tools
    Output: StructuredFinding with claims, citations, absence report
    Gate:   All claims must have citations (structural enforcement).
    """

    async def execute(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Execute research on the assigned task.

        Yields ResearchStarted, SourceFound, CitationExtracted,
        FindingSynthesized, ResearchComplete events.
        """
        ...

    async def get_finding(self) -> StructuredFinding:
        """Return the structured finding produced by this agent."""
        ...


# ---------------------------------------------------------------------------
# CitationProcessor: Research Agents -> Deliberation
# ---------------------------------------------------------------------------

@runtime_checkable
class CitationProcessorContract(Protocol):
    """Contract for the CitationProcessor.

    Input:  All StructuredFindings from L1 agents
    Output: CitationManifest (deduplicated, verified, corroboration-scored)
    Gate:   All findings independently produced; URLs verified.
    """

    async def process(
        self,
        findings: list[StructuredFinding],
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Process all agent findings into a citation manifest.

        Yields CitationDeduped, CorroborationScored, URLVerified,
        ManifestProduced events.
        """
        ...

    async def get_manifest(self) -> CitationManifest:
        """Return the produced citation manifest."""
        ...


# ---------------------------------------------------------------------------
# L1.5: Deliberation -> Content Structuring
# ---------------------------------------------------------------------------

@runtime_checkable
class DeliberationContract(Protocol):
    """Contract for the Deliberation phase (L1.5).

    Input:  CitationManifest + corroborated findings
    Output: ConfidenceMap + claims + gap report + absence report
    Gate:   Independent analyses aggregated; curmudgeon challenge passed.
    """

    async def deliberate(
        self,
        manifest: CitationManifest,
        findings: list[StructuredFinding],
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run two-phase deliberation.

        Phase 1: Independent parallel analysis (3-5 analysts, no interaction).
        Phase 2: Structured aggregation with curmudgeon challenge.

        Yields AnalystSpawned, IndependentAnalysisComplete,
        AggregationComplete, ConfidenceMapProduced events.
        """
        ...

    async def get_confidence_map(self) -> ConfidenceMap:
        """Return the produced confidence map."""
        ...


# ---------------------------------------------------------------------------
# L2: Content Structuring -> Evaluator
# ---------------------------------------------------------------------------

@runtime_checkable
class ContentStructuringContract(Protocol):
    """Contract for Content Structuring (L2).

    Input:  ConfidenceMap + claims (from L1.5)
    Output: Section drafts + sprint contracts
    Gate:   Sprint contracts negotiated for each section.
    """

    async def structure(
        self,
        confidence_map: ConfidenceMap,
        spec: EngagementSpec,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Structure findings into deliverable outline and sections.

        Yields OutlineGenerated, SectionDrafted, SprintContractNegotiated events.
        """
        ...

    async def get_sprint_contracts(self) -> list[SprintContract]:
        """Return the negotiated sprint contracts."""
        ...


# ---------------------------------------------------------------------------
# L3: Generation -> Evaluator
# ---------------------------------------------------------------------------

@runtime_checkable
class GenerationContract(Protocol):
    """Contract for Deliverable Generation (L3).

    Input:  Structured sections + sprint contracts + citation manifest
    Output: Formatted deliverable with citations
    Gate:   Output format matches specification.
    """

    async def generate(
        self,
        contracts: list[SprintContract],
        manifest: CitationManifest,
        spec: EngagementSpec,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Generate the final deliverable.

        Yields DraftGenerated, CitationFormatted, DeliverableAssembled events.
        """
        ...

    async def get_deliverable(self) -> str:
        """Return the assembled deliverable content."""
        ...


# ---------------------------------------------------------------------------
# L4: Evaluator -> Self-Improvement
# ---------------------------------------------------------------------------

@runtime_checkable
class EvaluatorContract(Protocol):
    """Contract for the Evaluator (L4).

    Input:  Section draft + sprint contract + task + citations + RESEARCH.md
    Output: EvaluationResult with scores + specific feedback
    Gate:   Layer 2 citation gate: any fabrication = full rejection.
    """

    async def evaluate(
        self,
        output_text: str,
        contract: SprintContract,
        task: ResearchTask,
        manifest: CitationManifest,
        spec: EngagementSpec,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 5-layer evaluation stack (Layers 1-3 in Phase 1).

        Yields DeterministicCheckPassed, CitationGateResult,
        RubricDimensionScored, EvaluationComplete events.
        """
        ...

    async def get_result(self) -> EvaluationResult:
        """Return the evaluation result."""
        ...


# ---------------------------------------------------------------------------
# META: Self-Improvement
# ---------------------------------------------------------------------------

@runtime_checkable
class ObservationLibraryContract(Protocol):
    """Contract for the Observation Library (META).

    Input:  EvaluationResult (from L4)
    Output: ObservationEntry (constraint encoded or pattern promoted)
    Gate:   Root cause identified and encoded.
    """

    async def record(
        self,
        evaluation: EvaluationResult,
        task: ResearchTask,
        engagement_id: str,
        client_id: str,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Record an observation from an evaluation result.

        Yields ObservationRecorded, PatternPromoted, ConstraintEncoded events.
        """
        ...

    async def get_entry(self) -> ObservationEntry:
        """Return the recorded observation entry."""
        ...


# ---------------------------------------------------------------------------
# HITL: Human-in-the-Loop Gate
# ---------------------------------------------------------------------------

@runtime_checkable
class HITLGateContract(Protocol):
    """Contract for the Human-in-the-Loop review gate.

    Input:  Review artifacts (issue tree, agent configs, confidence map, etc.)
    Output: GateResponse with human decision (approve/modify/reject)
    Gate:   Pipeline blocks until human decides.

    Phase 1: Database state machine with polling.
    Phase 2: Temporal Signal (no interface change needed).
    """

    async def submit_for_review(
        self,
        engagement_id: str,
        client_id: str,
        gate_type: str,
        artifacts: list[dict],
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Create a review gate and wait for human decision.

        Yields ReviewGateCreated, then blocks until decision,
        then yields ReviewGateApproved/Modified/Rejected.
        """
        ...

    async def get_decision(self) -> GateResponse:
        """Return the human's decision on this gate."""
        ...
