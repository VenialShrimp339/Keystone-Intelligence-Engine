"""Pydantic schemas for the HITL REST API.

These are the request/response models for the API layer. They are
separate from the SQLAlchemy ORM models (models.py) and the pipeline
Pydantic models (keystone.models.*).

All schemas include engagement_id/client_id for multi-tenancy (Decision 10).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class GateType(StrEnum):
    """The two mandatory human review gates (Directive 7)."""

    POST_SPECIFICATION = "post_specification"
    POST_DELIBERATION = "post_deliberation"


class GateStatus(StrEnum):
    """Gate lifecycle states. Terminal: approved, modified, rejected."""

    PENDING = "pending"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"


class DecisionType(StrEnum):
    """Human decision options."""

    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"


class ReviewItemType(StrEnum):
    """Types of artifacts presented for review."""

    ISSUE_TREE = "issue_tree"
    AGENT_CONFIG = "agent_config"
    CONFIDENCE_MAP = "confidence_map"
    DIVERGENCE_POINTS = "divergence_points"
    SPRINT_CONTRACT = "sprint_contract"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ReviewItemCreate(BaseModel):
    """A single artifact to include in a review gate."""

    item_type: ReviewItemType = Field(description="Type of review artifact")
    content: dict = Field(description="The artifact content as JSON")
    display_order: int = Field(ge=0, description="Display ordering (0-indexed)")


class CreateGateRequest(BaseModel):
    """Request to create a new review gate."""

    engagement_id: str = Field(description="Parent engagement ID")
    client_id: str = Field(description="Client ID for multi-tenancy")
    gate_type: GateType = Field(description="Which pipeline gate")
    items: list[ReviewItemCreate] = Field(
        min_length=1, description="Artifacts for the reviewer to inspect"
    )


class SubmitDecisionRequest(BaseModel):
    """Request to submit a human decision on a gate."""

    decision: DecisionType = Field(description="The reviewer's verdict")
    decided_by: str = Field(description="Reviewer identifier")
    modifications: dict | None = Field(
        default=None,
        description="Modified artifacts (required when decision is 'modify')",
    )
    reasoning: str | None = Field(default=None, description="Reviewer's rationale for the decision")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ReviewItemResponse(BaseModel):
    """A review artifact in a gate response."""

    id: str
    item_type: ReviewItemType
    content: dict
    display_order: int


class DecisionResponse(BaseModel):
    """A decision record in a gate response."""

    id: str
    gate_id: str
    decision: DecisionType
    modifications: dict | None = None
    reasoning: str | None = None
    decided_by: str
    decided_at: datetime


class GateResponse(BaseModel):
    """Full gate state including items and decision."""

    id: str
    engagement_id: str
    client_id: str
    gate_type: GateType
    status: GateStatus
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    items: list[ReviewItemResponse] = Field(default_factory=list)
    decision: DecisionResponse | None = None


class GateResolution(BaseModel):
    """Resolved gate state plus patch application semantics."""

    status: GateStatus = Field(description="Resolved gate status")
    gate_response: GateResponse = Field(
        description="Underlying gate response returned from the service"
    )
    patch_applied: bool = Field(
        default=False,
        description="Whether requested modifications were applied downstream",
    )

    @model_validator(mode="after")
    def _validate_status_matches_response(self) -> GateResolution:
        if self.status != self.gate_response.status:
            msg = "GateResolution.status must match gate_response.status"
            raise ValueError(msg)
        return self

    @property
    def id(self) -> str:
        return self.gate_response.id

    @property
    def engagement_id(self) -> str:
        return self.gate_response.engagement_id

    @property
    def client_id(self) -> str:
        return self.gate_response.client_id

    @property
    def gate_type(self) -> GateType:
        return self.gate_response.gate_type

    @property
    def created_at(self) -> datetime:
        return self.gate_response.created_at

    @property
    def resolved_at(self) -> datetime | None:
        return self.gate_response.resolved_at

    @property
    def resolved_by(self) -> str | None:
        return self.gate_response.resolved_by

    @property
    def items(self) -> list[ReviewItemResponse]:
        return self.gate_response.items

    @property
    def decision(self) -> DecisionResponse | None:
        return self.gate_response.decision


class GateSummaryResponse(BaseModel):
    """Lightweight gate listing without full item content."""

    id: str
    engagement_id: str
    client_id: str
    gate_type: GateType
    status: GateStatus
    created_at: datetime
    resolved_at: datetime | None = None
    item_count: int = 0
