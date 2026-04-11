"""RESEARCH.md specification model and research output models.

Based on Component #1 schemas and CAPSTONE-PLAN-v2.md Section 3.2.
The RESEARCH.md is the engagement specification that every agent reads,
every output validates against, and every deliverable traces to.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 (Pydantic needs runtime access for frozen model)
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from keystone.models.citations import (  # noqa: TC001 (Pydantic v2 needs runtime access)
    Citation,
    ConfidenceTier,
)
from keystone.models.tasks import TaskDecomposition  # noqa: TC001


class EngagementType(StrEnum):
    """Five-type analytical taxonomy for pipeline routing.

    Drives pipeline profile selection (Light/Standard/Deep),
    evaluation weight profiles, and template registry queries.
    From CAPSTONE-PLAN-v2.md Section 3.8 and MASTER-SYNTHESIS Section 1.
    """

    SIZING = "sizing"
    DIAGNOSTIC = "diagnostic"
    EVALUATIVE = "evaluative"
    EXPLORATORY = "exploratory"
    STRATEGIC = "strategic"


class ResearchQuestion(BaseModel):
    """A research question within the engagement specification."""

    question: str = Field(description="The research question text")
    is_primary: bool = Field(
        default=False,
        description="Whether this is the primary question (exactly one per engagement)",
    )
    parent_question: str | None = Field(
        default=None,
        description="If secondary, which primary question this supports",
    )


class MethodologyRequirement(BaseModel):
    """An analytical framework or approach required for the engagement."""

    framework: str = Field(description="Name of the analytical framework")
    mandatory: bool = Field(
        default=True, description="Whether this framework is required vs. optional"
    )
    rationale: str = Field(description="Why this framework applies")


class SourceRequirement(BaseModel):
    """A data source category required for the engagement."""

    source_type: str = Field(
        description="Category of source (academic, financial_filings, news, etc.)"
    )
    minimum_count: int = Field(
        ge=1, description="Minimum number of sources from this category"
    )
    quality_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum Admiralty Code quality score for sources in this category",
    )


class ResearchSpec(BaseModel):
    """The RESEARCH.md engagement specification.

    This is the most important data structure in the system. It defines
    what the engagement is about, what questions it answers, and what
    quality standards apply. Every agent reads it. Every output validates
    against it.
    """

    model_config = ConfigDict(frozen=True)

    engagement_id: str = Field(description="Unique engagement identifier")
    client_id: str = Field(description="Client identifier for data sandboxing")
    title: str = Field(description="Engagement title")
    created_at: datetime = Field(description="When this spec was created")
    specification_version: int = Field(ge=1, description="Spec version number")

    # Section: Client Decision Context
    decision_context: str = Field(
        description="What decision will this research inform? "
        "What are the client's constraints?"
    )
    surprising_finding: str = Field(
        description="What would a surprising finding look like? "
        "What evidence would change the client's mind?"
    )

    # Section: Research Questions
    questions: list[ResearchQuestion] = Field(
        description="Primary and secondary research questions"
    )

    # Section: Methodology Requirements
    methodology: list[MethodologyRequirement] = Field(
        default_factory=list,
        description="Required analytical frameworks",
    )

    # Section: Source Requirements
    source_requirements: list[SourceRequirement] = Field(
        default_factory=list,
        description="Minimum source coverage by category",
    )

    # Section: Output Format & Quality
    output_format: str = Field(
        description="Expected deliverable format (markdown, slides, etc.)"
    )
    quality_bar: str = Field(
        default="Goldman-grade: would a domain expert call this solid on its own merits?",
        description="Quality standard for this engagement",
    )

    # Section: Non-Goals
    non_goals: list[str] = Field(
        default_factory=list,
        description="Explicit boundaries on what this engagement does NOT cover",
    )

    # --- Batch 2 additions ---

    engagement_type: EngagementType = Field(
        description="Classified engagement type. Drives pipeline depth, "
        "agent configuration, and evaluation profiles.",
    )
    day_1_hypothesis: str | None = Field(
        default=None,
        description="Initial testable hypothesis that anchors the research. "
        "Prevents open-ended exploration (AutoGPT failure mode).",
    )


class ValidationReport(BaseModel):
    """Result of the Specification Engine's four-step verification."""

    intent_clear: bool = Field(
        description="Is the client's decision context unambiguous?"
    )
    scope_valid: bool = Field(
        description="Is the research scope achievable within constraints?"
    )
    within_frontier: bool = Field(
        description="Is this within the system's capability frontier (tasks, not jobs)?"
    )
    quality_threshold_met: bool = Field(
        description="Does the spec meet minimum quality for agent dispatch?"
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found during validation",
    )

    @property
    def all_passed(self) -> bool:
        return (
            self.intent_clear
            and self.scope_valid
            and self.within_frontier
            and self.quality_threshold_met
        )


class EngagementSpec(BaseModel):
    """Complete output of the Specification Engine (L0).

    Combines the RESEARCH.md specification, the task decomposition,
    and the validation report. This is what L1 agents receive.
    """

    research_spec: ResearchSpec = Field(description="The RESEARCH.md content")
    task_decomposition: TaskDecomposition = Field(
        description="research-tasks.json decomposition"
    )
    validation_report: ValidationReport = Field(
        description="Four-step verification results"
    )
    issue_tree: dict[str, Any] | None = Field(
        default=None,
        description="The MECE issue tree produced by Step 3 of the Spec Engine. "
        "JSON representation of the tree structure.",
    )


class FindingStatus(StrEnum):
    """Completion status of a research agent's finding."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    GAP_FOUND = "gap_found"


class StructuredFinding(BaseModel):
    """Output of a single L1 research agent.

    Each agent produces structured findings with mandatory citations,
    confidence assessments, caveats, and an absence report. The absence
    report is analytically significant: what was looked for but not found.

    The condensed output should be 1,000-2,000 tokens. Full artifacts
    are written to {engagement_id}/memory/raw/ via artifact_path.
    """

    task_id: str = Field(description="Which task this finding addresses")
    agent_id: str = Field(description="ID of the agent that produced this finding")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    agent_type: str = Field(
        description="Agent specialization "
        "(quantitative, qualitative, contrarian, historical, internal)"
    )
    claims: list[FindingClaim] = Field(
        description="Structured claims with evidence and citations"
    )
    status: FindingStatus = Field(
        default=FindingStatus.COMPLETE,
        description="Whether the agent completed its task fully, partially, or found a gap",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Research gaps identified during investigation",
    )
    artifact_path: str | None = Field(
        default=None,
        description="Path to full artifact in raw/ directory (condensed summary is in claims)",
    )
    absence_report: list[str] = Field(
        description="What was looked for but not found (analytically significant)"
    )
    sources_consulted: int = Field(
        ge=0, description="Total number of sources reviewed"
    )
    tokens_consumed: int = Field(
        ge=0, description="Total tokens used by this agent"
    )
    dropped_claims: list[dict] = Field(
        default_factory=list,
        description="Claims that failed validation, with reasons",
    )


class FindingClaim(BaseModel):
    """A single claim within a structured finding, with full evidence chain."""

    text: str = Field(description="The claim statement")
    evidence: str = Field(description="Supporting evidence summary")
    citations: list[Citation] = Field(
        description="Citations backing this claim (structurally enforced, not prompt-based)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Agent's confidence in this claim"
    )
    confidence_tier: ConfidenceTier = Field(
        description="Discrete confidence tier"
    )
    caveats: list[str] = Field(
        default_factory=list, description="Known limitations or qualifications"
    )
    claim_id: str | None = Field(default=None, description="Stable claim identifier")
    citation_ids: list[str] = Field(
        default_factory=list,
        description="Canonical citation IDs after processor rewrite",
    )
