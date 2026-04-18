"""Observation Library data models for the Keystone Intelligence Engine.

Based on CAPSTONE-PLAN-v2.md Section 7.1.
The Observation Library captures all evaluator outcomes (successes and
failures), detects patterns in both directions, and promotes validated
patterns to skills. It is the primary self-improvement mechanism and
the most durable thing the system creates.
"""

from __future__ import annotations

from enum import Enum, StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from keystone.models.evaluation import (
    RubricDimension,  # noqa: TC001 (Pydantic v2 needs runtime access)
)

if TYPE_CHECKING:
    from datetime import datetime


class ObservationType(StrEnum):
    """Whether the observation records a failure or success."""

    REJECTION = "rejection"
    SUCCESS = "success"


class ObservationCategory(int, Enum):
    """Three-tier taxonomy for observation severity/type.

    Category 1: Detected automatically by Layers 1-2.
    Category 2: Detected by Layer 3, flagged for expert review.
    Category 3: Detected by Layers 4-5, requires human calibration.
    """

    STRUCTURAL = 1
    ANALYTICAL = 2
    JUDGMENT = 3


class ObservationEntry(BaseModel):
    """A single observation in the Observation Library.

    Captures both positive patterns (reinforcement) and negative patterns
    (correction). Quality is better defined by what it excludes than
    what it includes (Heuer's disconfirmation principle).

    Examples from CAPSTONE-PLAN-v2.md Section 7.1:
    - Rejection: Competitive moat analysis conflated temporary cost advantage
      with structural network effect.
    - Success: Historical Analogy agent cross-referenced regulatory timelines
      with GDPR market dynamics, producing evaluative surprise.
    """

    observation_id: str = Field(description="Unique identifier, format OBS-NNN")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    type: ObservationType = Field(
        description="Whether this captures a failure (rejection) or success"
    )
    category: ObservationCategory = Field(
        description="1=structural/machine-checkable, 2=analytical/expert-checkable, "
        "3=judgment/human-calibrated"
    )
    project: str = Field(description="Human-readable project name")
    task_id: str = Field(description="Which research task this observation relates to")
    recorded_at: datetime = Field(description="When this observation was recorded")

    # What happened
    dimension: RubricDimension = Field(description="Which rubric dimension failed or excelled")
    what_was_produced: str = Field(
        description="Description of the output that triggered this observation"
    )
    assessment: str = Field(
        description="What was wrong (for rejections) or why it worked (for successes)"
    )

    # Root cause and action
    root_cause: str | None = Field(
        default=None,
        description="Identified root cause (rejections) or enabling factor (successes)",
    )
    action_taken: str = Field(
        description="Constraint encoded (rejections) or pattern promoted (successes)"
    )
    propagated_to: list[str] = Field(
        default_factory=list,
        description="Files updated with this observation (skill files, constraints, etc.)",
    )

    # Validation
    validated_across: int = Field(
        default=1,
        ge=1,
        description="Number of engagements where this pattern has been observed",
    )
    promoted_to_skill: bool = Field(
        default=False,
        description="Whether this pattern has been promoted to a skill file",
    )
    superseded_by: str | None = Field(
        default=None,
        description="If this observation was superseded by a newer one, its ID",
    )


class ObservationLibrary(BaseModel):
    """The full Observation Library for an engagement or globally.

    The library is:
    - The primary input to self-improvement
    - A compounding asset (every observation makes the next project better)
    - Transferable across engagement types
    - A real-time evaluation mechanism (Pass 3 negative-space scan)
    """

    engagement_id: str | None = Field(
        default=None,
        description="If scoped to an engagement; None for global library",
    )
    entries: list[ObservationEntry] = Field(
        default_factory=list, description="All observation entries"
    )

    @property
    def rejections(self) -> list[ObservationEntry]:
        return [e for e in self.entries if e.type == ObservationType.REJECTION]

    @property
    def successes(self) -> list[ObservationEntry]:
        return [e for e in self.entries if e.type == ObservationType.SUCCESS]

    @property
    def structural(self) -> list[ObservationEntry]:
        return [e for e in self.entries if e.category == ObservationCategory.STRUCTURAL]

    @property
    def analytical(self) -> list[ObservationEntry]:
        return [e for e in self.entries if e.category == ObservationCategory.ANALYTICAL]

    @property
    def judgment(self) -> list[ObservationEntry]:
        return [e for e in self.entries if e.category == ObservationCategory.JUDGMENT]
