"""Pipeline-L2 structured outline and framework models.

L2 Content Structuring transforms a ConfidenceMap + findings into a
provenance-preserving outline aligned to consulting analytical frameworks.
Models here are the L1.5 -> L4 handoff payload: the outline that downstream
renderers traverse and the per-task section text that the Evaluator scores.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from keystone.models.citations import (
    ConfidenceTier,  # noqa: TC001 (Pydantic v2 needs runtime access)
)


class AnalyticalFramework(StrEnum):
    """Consulting analytical frameworks selectable by engagement type.

    The framework label is stamped on the section header and carried into
    the Evaluator's prompt context so rubric scoring can reward on-framework
    reasoning (e.g. Analytical Depth, Quantitative Rigor).
    """

    ESTIMATION = "estimation"
    ROOT_CAUSE = "root_cause"
    PORTERS_FIVE_FORCES = "porters_five_forces"
    VALUE_CHAIN = "value_chain"
    LANDSCAPE_MAPPING = "landscape_mapping"
    SCENARIO_PLANNING = "scenario_planning"
    SWOT = "swot"


class OutlineSectionType(StrEnum):
    """Top-level section kinds in the L2 outline.

    Section order in the rendered deliverable follows this enum's order:
    executive summary first, framework-scoped analysis, then branches,
    then uncertainty, then gaps. Absence and insufficient trail.
    """

    EXECUTIVE_SUMMARY = "executive_summary"
    FRAMEWORK_ANALYSIS = "framework_analysis"
    BRANCH = "branch"
    MODERATE = "moderate"
    WEAK = "weak"
    CONTESTED = "contested"
    GAPS = "gaps"
    INSUFFICIENT = "insufficient"
    ABSENCE = "absence"


class OutlineItemType(StrEnum):
    """Item kinds that can appear inside an outline section."""

    CLAIM = "claim"
    GAP = "gap"
    ABSENCE = "absence"
    INSUFFICIENT = "insufficient"
    FRAMEWORK_NOTE = "framework_note"


class FrameworkHint(BaseModel):
    """Explains why a framework was chosen for this engagement."""

    framework: AnalyticalFramework = Field(description="Selected framework")
    rationale: str = Field(description="Why this framework applies to the engagement type")
    mandatory: bool = Field(
        default=True,
        description="Whether this framework must be applied (vs. optional augmentation)",
    )


class OutlineItem(BaseModel):
    """Single provenance-bearing unit in an outline section.

    An OutlineItem always carries the task IDs that support it, so
    post-evaluation filtering (`filter_outline_by_passed_tasks`) can
    drop items whose tasks failed L4.
    """

    item_id: str | None = Field(
        default=None,
        description="Original claim ID, aggregated claim ID, or synthetic gap item ID",
    )
    item_type: OutlineItemType = Field(
        default=OutlineItemType.CLAIM,
        description="What kind of unit this item represents",
    )
    text: str = Field(description="User-visible content for the item")
    task_ids: list[str] = Field(
        default_factory=list,
        description="Tasks whose evidence supports this outline item",
    )
    citation_ids: list[str] = Field(
        default_factory=list,
        description="Canonical citation IDs traceable to this item",
    )
    issue_tree_branch_id: str | None = Field(
        default=None,
        description="Issue-tree branch this item belongs to when known",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score when the item originates from a finding claim",
    )
    confidence_tier: ConfidenceTier | None = Field(
        default=None,
        description="Confidence tier when the item originates from a finding claim",
    )
    evidence: str | None = Field(
        default=None,
        description="Evidence text associated with the item when available",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Caveats associated with the item when available",
    )
    note: str | None = Field(
        default=None,
        description="Auxiliary note such as dissent, sensitivity, or reason text",
    )


class StructuredSection(BaseModel):
    """Provenance-preserving section in the L2 outline."""

    section_id: str = Field(description="Stable section identifier")
    section_type: OutlineSectionType = Field(description="Kind of section")
    title: str = Field(description="Rendered title for the section")
    framework: AnalyticalFramework | None = Field(
        default=None,
        description="Framework applied to this section (stamped on FRAMEWORK_ANALYSIS and BRANCH)",
    )
    issue_tree_branch_id: str | None = Field(
        default=None,
        description="Primary issue-tree branch represented by this section when applicable",
    )
    task_ids: list[str] = Field(
        default_factory=list,
        description="Union of task IDs represented in the section",
    )
    claim_ids: list[str] = Field(
        default_factory=list,
        description="Union of claim or aggregated-claim IDs represented in the section",
    )
    citation_ids: list[str] = Field(
        default_factory=list,
        description="Union of canonical citation IDs represented in the section",
    )
    items: list[OutlineItem] = Field(
        default_factory=list,
        description="Ordered items rendered within the section",
    )


class StructuredOutline(BaseModel):
    """Pipeline-L2 output consumed by L4 (as section text) and renderer (as outline)."""

    engagement_id: str = Field(description="Parent engagement identifier")
    client_id: str = Field(description="Client identifier for sandboxing")
    engagement_type: str = Field(
        description="EngagementType value; echoed for framework traceability"
    )
    frameworks: list[FrameworkHint] = Field(
        default_factory=list,
        description="Analytical frameworks selected for this engagement",
    )
    sections: list[StructuredSection] = Field(
        default_factory=list,
        description="Ordered outline sections",
    )
    rendered_task_ids: list[str] = Field(
        default_factory=list,
        description="Tasks that contributed renderable material to this outline",
    )
    uncovered_branch_ids: list[str] = Field(
        default_factory=list,
        description="Issue-tree branches still not covered by renderable material",
    )
