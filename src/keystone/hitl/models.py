"""SQLAlchemy 2.0 ORM models for the HITL review gate state machine.

Three tables:
- review_gates: tracks gate lifecycle (pending -> approved/modified/rejected)
- review_items: artifacts presented to the human reviewer
- review_decisions: the human's decision record

Design for Temporal migration: the state machine is a simple status column
that maps directly to Temporal Signal-driven state in Phase 2. No agent
code needs to change -- only the wait mechanism (polling -> signal).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all HITL ORM models."""

    pass


class ReviewGate(Base):
    """A human review checkpoint in the pipeline.

    State machine:
        pending -> approved  (human approves, pipeline continues)
        pending -> modified  (human modifies artifacts, pipeline continues with changes)
        pending -> rejected  (human rejects, pipeline halts)

    Terminal states: approved, modified, rejected. No further transitions.
    """

    __tablename__ = "review_gates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    gate_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "post_specification" | "post_deliberation"
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # "pending" | "approved" | "modified" | "rejected"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    items: Mapped[list[ReviewItem]] = relationship(
        back_populates="gate", cascade="all, delete-orphan", order_by="ReviewItem.display_order"
    )
    decision: Mapped[ReviewDecision | None] = relationship(
        back_populates="gate", cascade="all, delete-orphan", uselist=False
    )

    __table_args__ = (
        Index("ix_review_gates_engagement_gate_type", "engagement_id", "gate_type"),
        Index("ix_review_gates_status", "status"),
    )


class ReviewItem(Base):
    """An artifact displayed to the human reviewer.

    Each gate presents one or more items for review. Item types depend
    on the gate type:

    Post-Specification gate:
        - issue_tree: the MECE issue tree JSON
        - agent_config: proposed agent configurations
        - sprint_contract: evaluator's proposed criteria

    Post-Deliberation gate:
        - confidence_map: five-tier confidence map
        - divergence_points: where analysts disagreed
    """

    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gate_id: Mapped[str] = mapped_column(
        ForeignKey("review_gates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # "issue_tree" | "agent_config" | "confidence_map" | "divergence_points" | "sprint_contract"
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    gate: Mapped[ReviewGate] = relationship(back_populates="items")


class ReviewDecision(Base):
    """The human's decision on a review gate.

    One decision per gate (enforced by unique constraint on gate_id).
    modifications_json carries the human's edits when decision is "modify".
    """

    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    gate_id: Mapped[str] = mapped_column(
        ForeignKey("review_gates.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    decision: Mapped[str] = mapped_column(String, nullable=False)  # "approve" | "modify" | "reject"
    modifications_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str] = mapped_column(String, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    gate: Mapped[ReviewGate] = relationship(back_populates="decision")
