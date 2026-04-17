"""Typed event hierarchy for the Keystone Intelligence Engine.

The repo analysis's #1 finding: "Generator-based agent loop is the right
orchestration primitive. Adopt for ALL pipeline stages." Every pipeline
transition yields typed events for observability and trajectory storage.

Event design follows the nano-claude-code pattern: the agent loop is a
generator yielding typed events (TextChunk, ToolStart, ToolEnd, TurnDone).
We extend this to cover all 6 pipeline layers + META.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Base event
# ---------------------------------------------------------------------------


class PipelineEvent(BaseModel):
    """Base class for all pipeline events.

    Every event carries engagement context for multi-tenancy isolation,
    a timestamp, and the pipeline layer that produced it.
    """

    event_id: str = Field(description="Unique event identifier")
    engagement_id: str = Field(description="Parent engagement")
    client_id: str = Field(description="Client identifier for data sandboxing")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this event occurred"
    )
    layer: str = Field(description="Pipeline layer that produced this event")


# ---------------------------------------------------------------------------
# L0: Specification Engine events
# ---------------------------------------------------------------------------


class SpecificationGenerated(PipelineEvent):
    """RESEARCH.md specification has been generated and validated."""

    layer: str = "L0"
    spec_version: int = Field(description="Specification version number")
    question_count: int = Field(description="Number of research questions")
    validation_passed: bool = Field(description="Whether all 4 validation checks passed")


class TasksDecomposed(PipelineEvent):
    """Research question decomposed into discrete tasks."""

    layer: str = "L0"
    task_count: int = Field(description="Number of tasks created")
    categories: list[str] = Field(description="Task categories present")
    rationale: str = Field(description="Why the decomposition was structured this way")


class AgentDispatched(PipelineEvent):
    """An agent has been dispatched to work on a task."""

    layer: str = "L0"
    agent_id: str = Field(description="ID of the dispatched agent")
    agent_type: str = Field(description="Agent specialization type")
    task_id: str = Field(description="Task assigned to this agent")
    model_tier: str = Field(description="Model tier assigned")
    tools: list[str] = Field(description="Tools assigned to this agent")


# ---------------------------------------------------------------------------
# L1: Research Agent events
# ---------------------------------------------------------------------------


class ResearchStarted(PipelineEvent):
    """A research agent has started working on its assigned task."""

    layer: str = "L1"
    agent_id: str = Field(description="Agent instance ID")
    task_id: str = Field(description="Task being researched")


class SourceFound(PipelineEvent):
    """A research agent discovered a relevant source."""

    layer: str = "L1"
    agent_id: str = Field(description="Agent that found the source")
    url: str = Field(description="Source URL")
    source_type: str = Field(description="Classification of the source")
    quality_score: float = Field(description="Admiralty Code quality score")


class CitationExtracted(PipelineEvent):
    """A citation has been extracted from a source."""

    layer: str = "L1"
    agent_id: str = Field(description="Agent that extracted the citation")
    citation_id: str = Field(description="The extracted citation's ID")
    title: str = Field(description="Citation title")


class FindingSynthesized(PipelineEvent):
    """A research agent has synthesized a finding from its evidence."""

    layer: str = "L1"
    agent_id: str = Field(description="Agent that produced the finding")
    claim_count: int = Field(description="Number of claims in the finding")
    confidence_range: str = Field(description="Range of confidence scores")


class ResearchComplete(PipelineEvent):
    """A research agent has finished all assigned work."""

    layer: str = "L1"
    agent_id: str = Field(description="Agent that completed")
    task_id: str = Field(description="Task that was completed")
    sources_consulted: int = Field(description="Total sources reviewed")
    tokens_consumed: int = Field(description="Total tokens used")
    absence_count: int = Field(description="Items in the absence report")


# ---------------------------------------------------------------------------
# CitationProcessor events
# ---------------------------------------------------------------------------


class CitationDeduped(PipelineEvent):
    """Two citations have been merged (same source, different agents)."""

    layer: str = "CitationProcessor"
    citation_id: str = Field(description="Merged citation ID")
    merged_from: list[str] = Field(description="Original citation IDs that were merged")
    agents_involved: list[str] = Field(description="Agents that found this source")


class CorroborationScored(PipelineEvent):
    """Two findings have been scored for independent corroboration."""

    layer: str = "CitationProcessor"
    citation_a: str = Field(description="First citation")
    citation_b: str = Field(description="Second citation")
    overlap_score: float = Field(description="Degree of evidentiary overlap")


class URLVerified(PipelineEvent):
    """A citation URL has been checked for liveness."""

    layer: str = "CitationProcessor"
    citation_id: str = Field(description="Citation checked")
    url: str = Field(description="URL checked")
    is_live: bool = Field(description="Whether the URL is reachable")


class ManifestProduced(PipelineEvent):
    """The CitationProcessor has finished producing the citation manifest."""

    layer: str = "CitationProcessor"
    manifest_id: str = Field(description="Manifest identifier")
    total_citations: int = Field(description="Total unique citations")
    dead_urls: int = Field(description="Number of dead URLs found")
    fabrication_flags: int = Field(description="Number of fabrication flags")
    corroboration_pairs: int = Field(description="Number of corroboration pairs")


# ---------------------------------------------------------------------------
# L1.5: Deliberation events
# ---------------------------------------------------------------------------


class AnalystSpawned(PipelineEvent):
    """A deliberation analyst has been spawned."""

    layer: str = "L1.5"
    analyst_id: str = Field(description="Analyst agent ID")
    analyst_type: str = Field(description="Analytical methodology (ACH, quantitative, etc.)")
    model_tier: str = Field(description="Model tier assigned")


class IndependentAnalysisComplete(PipelineEvent):
    """A deliberation analyst has completed their independent assessment."""

    layer: str = "L1.5"
    analyst_id: str = Field(description="Analyst that completed")
    analyst_type: str = Field(description="Analytical methodology used")
    claim_count: int = Field(description="Number of claims produced")


class AggregationComplete(PipelineEvent):
    """The aggregator has completed structured aggregation."""

    layer: str = "L1.5"
    convergent_findings: int = Field(description="Claims supported by 2+ methodologies")
    genuine_disagreements: int = Field(
        description="Claims with genuine methodological disagreement"
    )
    blind_spots: int = Field(description="Evidence types no methodology addressed")


class ConfidenceMapProduced(PipelineEvent):
    """The confidence map has been produced."""

    layer: str = "L1.5"
    total_claims: int = Field(description="Total claims in the map")
    tiers_populated: int = Field(description="Number of confidence tiers with claims")
    gaps_count: int = Field(description="Research gaps identified")


# ---------------------------------------------------------------------------
# L2: Content Structuring events
# ---------------------------------------------------------------------------


class OutlineGenerated(PipelineEvent):
    """A deliverable outline has been generated."""

    layer: str = "L2"
    section_count: int = Field(description="Number of sections in the outline")


class SectionDrafted(PipelineEvent):
    """A section draft has been produced."""

    layer: str = "L2"
    section_id: str = Field(description="Section identifier")
    section_title: str = Field(description="Section title")
    claim_count: int = Field(description="Claims incorporated in this section")


class SprintContractProposed(PipelineEvent):
    """A sprint contract has been proposed for a section.

    Phase 1 is unilateral proposal by the Evaluator-side generator; Phase 2
    will add bidirectional negotiation without a schema change.
    """

    layer: str = "L2"
    section_id: str = Field(description="Section this contract covers")
    criteria_count: int = Field(description="Number of acceptance criteria")


# ---------------------------------------------------------------------------
# L3: Generation events
# ---------------------------------------------------------------------------


class DraftGenerated(PipelineEvent):
    """A deliverable draft has been generated."""

    layer: str = "L3"
    section_id: str = Field(description="Section drafted")
    word_count: int = Field(description="Words in the draft")


class CitationFormatted(PipelineEvent):
    """Citations have been formatted for a section."""

    layer: str = "L3"
    section_id: str = Field(description="Section with formatted citations")
    citation_count: int = Field(description="Number of citations formatted")


class DeliverableAssembled(PipelineEvent):
    """The final deliverable has been assembled."""

    layer: str = "L3"
    format: str = Field(description="Output format (markdown, slides, etc.)")
    total_sections: int = Field(description="Total sections in the deliverable")
    total_citations: int = Field(description="Total citations in the deliverable")


# ---------------------------------------------------------------------------
# L4: Evaluator events
# ---------------------------------------------------------------------------


class DeterministicCheckPassed(PipelineEvent):
    """Layer 1 deterministic verification completed."""

    layer: str = "L4"
    facts_verified: int = Field(description="Atomic facts verified")
    facts_failed: int = Field(description="Atomic facts that failed")
    numerical_issues: int = Field(description="Numerical inconsistencies found")


class CitationGateResult(PipelineEvent):
    """Layer 2 citation gate result. Any fabrication = immediate rejection."""

    layer: str = "L4"
    citations_checked: int = Field(description="Total citations checked")
    citations_verified: int = Field(description="Citations confirmed real")
    fabrications_found: int = Field(description="Fabricated citations found")
    gate_passed: bool = Field(description="Whether the gate passed (zero fabrications)")


class RubricDimensionScored(PipelineEvent):
    """Layer 3: a single rubric dimension has been scored."""

    layer: str = "L4"
    dimension: str = Field(description="Rubric dimension name")
    score: float = Field(description="Score on 0-100 scale")
    weight: float = Field(description="Weight of this dimension")


class EvaluationComplete(PipelineEvent):
    """Full evaluation has completed."""

    layer: str = "L4"
    task_id: str = Field(description="Task that was evaluated")
    passed: bool = Field(description="Whether the output passed")
    overall_score: float = Field(description="Final composite score")
    layer2_gate_passed: bool = Field(description="Whether citation gate passed")
    feedback_length: int = Field(description="Length of feedback in characters")


# ---------------------------------------------------------------------------
# META: Self-Improvement events
# ---------------------------------------------------------------------------


class ObservationRecorded(PipelineEvent):
    """An observation has been recorded in the Observation Library."""

    layer: str = "META"
    observation_id: str = Field(description="Observation entry ID")
    observation_type: str = Field(description="rejection or success")
    category: int = Field(description="1=structural, 2=analytical, 3=judgment")
    dimension: str = Field(description="Rubric dimension involved")


class PatternPromoted(PipelineEvent):
    """A validated pattern has been promoted to a skill file."""

    layer: str = "META"
    observation_id: str = Field(description="Source observation ID")
    skill_path: str = Field(description="Skill file that was updated")
    validated_across: int = Field(description="Engagements where this pattern was observed")


class ConstraintEncoded(PipelineEvent):
    """A failure pattern has been encoded as a permanent constraint."""

    layer: str = "META"
    observation_id: str = Field(description="Source observation ID")
    constraint: str = Field(description="The constraint that was encoded")
    propagated_to: list[str] = Field(description="Files updated with this constraint")


# ---------------------------------------------------------------------------
# HITL: Human-in-the-Loop events
# ---------------------------------------------------------------------------


class ReviewGateCreated(PipelineEvent):
    """A human review gate has been created. Pipeline is paused."""

    layer: str = "HITL"
    gate_id: str = Field(description="Review gate ID")
    gate_type: str = Field(description="Gate type: 'post_specification' or 'post_deliberation'")
    item_count: int = Field(description="Number of review artifacts")


class ReviewDecisionSubmitted(PipelineEvent):
    """A human has submitted a decision on a review gate."""

    layer: str = "HITL"
    gate_id: str = Field(description="Review gate ID")
    decision: str = Field(description="Decision: 'approve', 'modify', or 'reject'")
    decided_by: str = Field(description="Reviewer identifier")
    has_modifications: bool = Field(
        description="Whether the decision includes artifact modifications"
    )


class ReviewGateApproved(PipelineEvent):
    """A review gate was approved. Pipeline resumes with no changes."""

    layer: str = "HITL"
    gate_id: str = Field(description="Review gate ID")
    gate_type: str = Field(description="Which gate was approved")


class ReviewGateModified(PipelineEvent):
    """A review gate was approved with modifications. Pipeline resumes with changes."""

    layer: str = "HITL"
    gate_id: str = Field(description="Review gate ID")
    gate_type: str = Field(description="Which gate was modified")
    modification_keys: list[str] = Field(description="Top-level keys in the modifications payload")


class ReviewGateRejected(PipelineEvent):
    """A review gate was rejected. Pipeline halts."""

    layer: str = "HITL"
    gate_id: str = Field(description="Review gate ID")
    gate_type: str = Field(description="Which gate was rejected")
    reasoning: str | None = Field(default=None, description="Reviewer's reason for rejection")


# ---------------------------------------------------------------------------
# Event type union for dispatch/routing
# ---------------------------------------------------------------------------

AnyPipelineEvent = (
    # L0
    SpecificationGenerated
    | TasksDecomposed
    | AgentDispatched
    # L1
    | ResearchStarted
    | SourceFound
    | CitationExtracted
    | FindingSynthesized
    | ResearchComplete
    # CitationProcessor
    | CitationDeduped
    | CorroborationScored
    | URLVerified
    | ManifestProduced
    # L1.5
    | AnalystSpawned
    | IndependentAnalysisComplete
    | AggregationComplete
    | ConfidenceMapProduced
    # L2
    | OutlineGenerated
    | SectionDrafted
    | SprintContractProposed
    # L3
    | DraftGenerated
    | CitationFormatted
    | DeliverableAssembled
    # L4
    | DeterministicCheckPassed
    | CitationGateResult
    | RubricDimensionScored
    | EvaluationComplete
    # META
    | ObservationRecorded
    | PatternPromoted
    | ConstraintEncoded
    # HITL
    | ReviewGateCreated
    | ReviewDecisionSubmitted
    | ReviewGateApproved
    | ReviewGateModified
    | ReviewGateRejected
)
