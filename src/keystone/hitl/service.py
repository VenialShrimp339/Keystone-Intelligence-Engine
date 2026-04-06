"""HITL service: business logic for the review gate state machine.

All methods take an AsyncSession parameter (dependency injection) to
keep business logic separate from I/O management (Day-1 coding standard #1).

State machine transitions:
    pending -> approved  (via approve decision)
    pending -> modified  (via modify decision, modifications_json required)
    pending -> rejected  (via reject decision)

Terminal states are final. Attempting to decide on a resolved gate raises.

Phase 2 migration note: the service layer stays identical. Only the
wait_for_decision mechanism changes (DB polling -> Temporal Signal).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from keystone.hitl.models import ReviewDecision, ReviewGate, ReviewItem
from keystone.hitl.schemas import (
    CreateGateRequest,
    DecisionResponse,
    DecisionType,
    GateResponse,
    GateStatus,
    GateSummaryResponse,
    ReviewItemResponse,
    SubmitDecisionRequest,
)


def _gate_to_response(gate: ReviewGate) -> GateResponse:
    """Map a SQLAlchemy ReviewGate (with loaded relationships) to a Pydantic response."""
    items = [
        ReviewItemResponse(
            id=item.id,
            item_type=item.item_type,
            content=item.content_json,
            display_order=item.display_order,
        )
        for item in gate.items
    ]

    decision = None
    if gate.decision is not None:
        decision = DecisionResponse(
            id=gate.decision.id,
            gate_id=gate.decision.gate_id,
            decision=gate.decision.decision,
            modifications=gate.decision.modifications_json,
            reasoning=gate.decision.reasoning,
            decided_by=gate.decision.decided_by,
            decided_at=gate.decision.decided_at,
        )

    return GateResponse(
        id=gate.id,
        engagement_id=gate.engagement_id,
        client_id=gate.client_id,
        gate_type=gate.gate_type,
        status=gate.status,
        created_at=gate.created_at,
        resolved_at=gate.resolved_at,
        resolved_by=gate.resolved_by,
        items=items,
        decision=decision,
    )


def _gate_to_summary(gate: ReviewGate) -> GateSummaryResponse:
    """Map a ReviewGate to a lightweight summary (no item content)."""
    return GateSummaryResponse(
        id=gate.id,
        engagement_id=gate.engagement_id,
        client_id=gate.client_id,
        gate_type=gate.gate_type,
        status=gate.status,
        created_at=gate.created_at,
        resolved_at=gate.resolved_at,
        item_count=len(gate.items),
    )


# Map decision types to gate statuses
_DECISION_TO_STATUS: dict[str, str] = {
    DecisionType.APPROVE: GateStatus.APPROVED,
    DecisionType.MODIFY: GateStatus.MODIFIED,
    DecisionType.REJECT: GateStatus.REJECTED,
}

_TERMINAL_STATUSES = frozenset({GateStatus.APPROVED, GateStatus.MODIFIED, GateStatus.REJECTED})


class HITLService:
    """Manages the lifecycle of human review gates.

    All methods are stateless -- state lives in the database.
    Session is injected per-call for Temporal migration readiness.
    """

    async def create_gate(
        self,
        session: AsyncSession,
        request: CreateGateRequest,
    ) -> GateResponse:
        """Create a new review gate with artifacts for human review.

        Returns the created gate with all items populated.
        """
        gate_id = str(uuid.uuid4())

        gate = ReviewGate(
            id=gate_id,
            engagement_id=request.engagement_id,
            client_id=request.client_id,
            gate_type=request.gate_type,
            status=GateStatus.PENDING,
        )

        for item_req in request.items:
            item = ReviewItem(
                id=str(uuid.uuid4()),
                gate_id=gate_id,
                item_type=item_req.item_type,
                content_json=item_req.content,
                display_order=item_req.display_order,
            )
            gate.items.append(item)

        session.add(gate)
        await session.commit()
        await session.refresh(gate, ["items", "decision"])

        return _gate_to_response(gate)

    async def get_gate(
        self,
        session: AsyncSession,
        gate_id: str,
    ) -> GateResponse:
        """Retrieve a gate with all its items and decision.

        Raises ValueError if gate not found.
        """
        stmt = (
            select(ReviewGate)
            .options(selectinload(ReviewGate.items), selectinload(ReviewGate.decision))
            .where(ReviewGate.id == gate_id)
        )
        result = await session.execute(stmt)
        gate = result.scalar_one_or_none()

        if gate is None:
            msg = f"Review gate not found: {gate_id}"
            raise ValueError(msg)

        return _gate_to_response(gate)

    async def get_pending_gates(
        self,
        session: AsyncSession,
        engagement_id: str | None = None,
    ) -> list[GateSummaryResponse]:
        """List all pending review gates, optionally filtered by engagement."""
        stmt = (
            select(ReviewGate)
            .options(selectinload(ReviewGate.items))
            .where(ReviewGate.status == GateStatus.PENDING)
            .order_by(ReviewGate.created_at.desc())
        )

        if engagement_id is not None:
            stmt = stmt.where(ReviewGate.engagement_id == engagement_id)

        result = await session.execute(stmt)
        gates = result.scalars().all()

        return [_gate_to_summary(g) for g in gates]

    async def list_gates(
        self,
        session: AsyncSession,
        engagement_id: str,
    ) -> list[GateSummaryResponse]:
        """List all review gates for an engagement (any status)."""
        stmt = (
            select(ReviewGate)
            .options(selectinload(ReviewGate.items))
            .where(ReviewGate.engagement_id == engagement_id)
            .order_by(ReviewGate.created_at.desc())
        )

        result = await session.execute(stmt)
        gates = result.scalars().all()

        return [_gate_to_summary(g) for g in gates]

    async def submit_decision(
        self,
        session: AsyncSession,
        gate_id: str,
        request: SubmitDecisionRequest,
    ) -> GateResponse:
        """Record a human decision on a gate.

        State transitions:
            pending -> approved  (proceed to next pipeline stage)
            pending -> modified  (apply modifications, then proceed)
            pending -> rejected  (abort pipeline stage)

        Raises:
            ValueError: if gate not found or already resolved.
            ValueError: if decision is 'modify' but no modifications provided.
        """
        stmt = (
            select(ReviewGate)
            .options(selectinload(ReviewGate.items), selectinload(ReviewGate.decision))
            .where(ReviewGate.id == gate_id)
        )
        result = await session.execute(stmt)
        gate = result.scalar_one_or_none()

        if gate is None:
            msg = f"Review gate not found: {gate_id}"
            raise ValueError(msg)

        if gate.status in _TERMINAL_STATUSES:
            msg = f"Gate {gate_id} already resolved with status '{gate.status}'"
            raise ValueError(msg)

        if request.decision == DecisionType.MODIFY and not request.modifications:
            msg = "Modifications required when decision is 'modify'"
            raise ValueError(msg)

        now = datetime.now(timezone.utc)

        # Create decision record
        decision = ReviewDecision(
            id=str(uuid.uuid4()),
            gate_id=gate_id,
            decision=request.decision,
            modifications_json=request.modifications,
            reasoning=request.reasoning,
            decided_by=request.decided_by,
            decided_at=now,
        )
        session.add(decision)

        # Transition gate status
        gate.status = _DECISION_TO_STATUS[request.decision]
        gate.resolved_at = now
        gate.resolved_by = request.decided_by

        await session.commit()
        await session.refresh(gate, ["items", "decision"])

        return _gate_to_response(gate)

    async def wait_for_decision(
        self,
        session: AsyncSession,
        gate_id: str,
        poll_interval: float = 1.0,
        timeout: float = 3600.0,
    ) -> GateResponse:
        """Block until a human decision is made on this gate.

        Used by the pipeline orchestrator to pause at gate boundaries.
        Polls the database at poll_interval seconds.

        Phase 2: Replace with Temporal Signal wait (no polling needed).

        Args:
            session: Database session (will be used for periodic queries).
            gate_id: The gate to wait on.
            poll_interval: Seconds between polls. Default 1s.
            timeout: Maximum wait time in seconds. Default 1 hour.

        Raises:
            TimeoutError: if no decision within timeout.
            ValueError: if gate not found.
        """
        elapsed = 0.0

        while elapsed < timeout:
            stmt = (
                select(ReviewGate)
                .options(selectinload(ReviewGate.items), selectinload(ReviewGate.decision))
                .where(ReviewGate.id == gate_id)
            )
            result = await session.execute(stmt)
            gate = result.scalar_one_or_none()

            if gate is None:
                msg = f"Review gate not found: {gate_id}"
                raise ValueError(msg)

            if gate.status in _TERMINAL_STATUSES:
                return _gate_to_response(gate)

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            # Expire cached state so next query hits the DB
            session.expire_all()

        msg = f"Timeout waiting for decision on gate {gate_id} after {timeout}s"
        raise TimeoutError(msg)
