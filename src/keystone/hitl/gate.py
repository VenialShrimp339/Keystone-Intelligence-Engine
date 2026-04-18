"""Pipeline integration for HITL review gates.

This module provides the function that pipeline stages call to trigger
a human review gate. It creates the gate, emits events, and blocks
until the human decides.

Used by:
    - Specification Engine (Step 8): post-specification gate
    - Deliberation (after confidence map): post-deliberation gate

Phase 2: The wait mechanism changes from DB polling to Temporal Signal.
The create_and_wait_for_gate interface stays the same.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

from keystone.events import (
    ReviewGateApproved,
    ReviewGateCreated,
    ReviewGateModified,
    ReviewGateRejected,
)
from keystone.hitl.schemas import (
    CreateGateRequest,
    GateResolution,
    GateStatus,
    GateType,
    ReviewItemCreate,
    ReviewItemType,
)
from keystone.hitl.service import HITLService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class GateRejectedError(Exception):
    """Raised when a human rejects a review gate, halting the pipeline."""

    def __init__(self, gate_id: str, reasoning: str | None = None) -> None:
        self.gate_id = gate_id
        self.reasoning = reasoning
        msg = f"Review gate {gate_id} rejected"
        if reasoning:
            msg += f": {reasoning}"
        super().__init__(msg)


class GateTimeoutError(Exception):
    """Raised when no human decision arrives within the timeout."""

    def __init__(self, gate_id: str, timeout: float) -> None:
        self.gate_id = gate_id
        self.timeout = timeout
        super().__init__(f"No decision on gate {gate_id} after {timeout}s")


class GateModificationRequiredError(Exception):
    """Raised when a reviewer requests changes that are not auto-applied."""

    def __init__(self, resolution: GateResolution) -> None:
        self.resolution = resolution
        super().__init__(
            f"Review gate {resolution.id} returned modified, but modifications "
            "are not yet supported in this phase."
        )


async def create_and_wait_for_gate(
    session: AsyncSession,
    engagement_id: str,
    client_id: str,
    gate_type: GateType,
    items: list[ReviewItemCreate],
    poll_interval: float = 1.0,
    timeout: float = 3600.0,
    event_collector: list | None = None,
) -> GateResolution:
    """Create a review gate and block until the human decides.

    This is the primary interface for pipeline stages. It:
    1. Creates the gate with review artifacts
    2. Polls the DB until a decision arrives (or timeout)
    3. Returns the resolved gate

    On rejection, raises GateRejectedError so the pipeline can halt.
    On timeout, raises GateTimeoutError.

    Args:
        session: Async DB session.
        engagement_id: Parent engagement.
        client_id: Client for multi-tenancy.
        gate_type: Which gate (post_specification or post_deliberation).
        items: Artifacts to present for review.
        poll_interval: Seconds between DB polls.
        timeout: Maximum wait time.

    Returns:
        The resolved GateResolution (status plus wrapped GateResponse).

    Raises:
        GateRejectedError: Human rejected. Pipeline must halt.
        GateModificationRequiredError: Human requested modifications that have
            not been applied in this phase.
        GateTimeoutError: No decision within timeout.
    """
    service = HITLService()

    request = CreateGateRequest(
        engagement_id=engagement_id,
        client_id=client_id,
        gate_type=gate_type,
        items=items,
    )

    gate = await service.create_gate(session, request)

    logger.info(
        "hitl_gate_created",
        gate_id=gate.id,
        gate_type=gate_type,
        engagement_id=engagement_id,
        item_count=len(items),
    )

    if event_collector is not None:
        event_collector.append(
            ReviewGateCreated(
                event_id=str(uuid.uuid4()),
                engagement_id=engagement_id,
                client_id=client_id,
                gate_id=gate.id,
                gate_type=str(gate_type),
                item_count=len(items),
            )
        )

    try:
        resolved = await service.wait_for_decision(
            session, gate.id, poll_interval=poll_interval, timeout=timeout
        )
    except TimeoutError as e:
        raise GateTimeoutError(gate.id, timeout) from e

    if resolved.status == GateStatus.REJECTED:
        reasoning = resolved.decision.reasoning if resolved.decision else None
        if event_collector is not None:
            event_collector.append(
                ReviewGateRejected(
                    event_id=str(uuid.uuid4()),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    gate_id=gate.id,
                    gate_type=str(gate_type),
                    reasoning=reasoning,
                )
            )
        raise GateRejectedError(gate.id, reasoning)

    logger.info(
        "hitl_gate_resolved",
        gate_id=gate.id,
        status=resolved.status,
        decided_by=resolved.resolved_by,
        engagement_id=engagement_id,
    )

    resolution = GateResolution(
        status=resolved.status,
        gate_response=resolved,
        patch_applied=resolved.status != GateStatus.MODIFIED,
    )

    if event_collector is not None:
        if resolved.status == GateStatus.MODIFIED:
            modification_keys = (
                list(resolved.decision.modifications.keys())
                if (resolved.decision and resolved.decision.modifications)
                else []
            )
            event_collector.append(
                ReviewGateModified(
                    event_id=str(uuid.uuid4()),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    gate_id=gate.id,
                    gate_type=str(gate_type),
                    modification_keys=modification_keys,
                )
            )
        else:
            event_collector.append(
                ReviewGateApproved(
                    event_id=str(uuid.uuid4()),
                    engagement_id=engagement_id,
                    client_id=client_id,
                    gate_id=gate.id,
                    gate_type=str(gate_type),
                )
            )

    if resolution.status == GateStatus.MODIFIED and not resolution.patch_applied:
        raise GateModificationRequiredError(resolution)

    return resolution


def build_spec_gate_items(
    issue_tree: dict,
    agent_configs: list[dict],
    sprint_contract: dict | None = None,
) -> list[ReviewItemCreate]:
    """Build review items for the post-specification gate (Gate 1).

    Convenience function for the Specification Engine to package its
    outputs for human review.
    """
    items = [
        ReviewItemCreate(
            item_type=ReviewItemType.ISSUE_TREE,
            content=issue_tree,
            display_order=0,
        ),
        ReviewItemCreate(
            item_type=ReviewItemType.AGENT_CONFIG,
            content={"agents": agent_configs},
            display_order=1,
        ),
    ]

    if sprint_contract is not None:
        items.append(
            ReviewItemCreate(
                item_type=ReviewItemType.SPRINT_CONTRACT,
                content=sprint_contract,
                display_order=2,
            )
        )

    return items


def build_deliberation_gate_items(
    confidence_map: dict,
    divergence_points: dict | None = None,
) -> list[ReviewItemCreate]:
    """Build review items for the post-deliberation gate (Gate 2).

    Convenience function for the Deliberation stage to package its
    outputs for human review.
    """
    items = [
        ReviewItemCreate(
            item_type=ReviewItemType.CONFIDENCE_MAP,
            content=confidence_map,
            display_order=0,
        ),
    ]

    if divergence_points is not None:
        items.append(
            ReviewItemCreate(
                item_type=ReviewItemType.DIVERGENCE_POINTS,
                content=divergence_points,
                display_order=1,
            )
        )

    return items
