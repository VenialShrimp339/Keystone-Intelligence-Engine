"""FastAPI router for HITL review gates.

Endpoints:
    GET  /api/hitl/gates                       - List pending gates (optional engagement filter)
    GET  /api/hitl/gates/{engagement_id}        - List all gates for an engagement
    POST /api/hitl/gates                        - Create a new review gate
    GET  /api/hitl/gates/{gate_id}/detail       - Get full gate with items and decision
    POST /api/hitl/gates/{gate_id}/decision     - Submit a human decision

All endpoints return JSON. The pipeline calls POST to create gates;
the human reviewer calls GET to inspect and POST to decide.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from keystone.hitl.db import get_session
from keystone.hitl.schemas import (
    CreateGateRequest,
    GateResponse,
    GateSummaryResponse,
    SubmitDecisionRequest,
)
from keystone.hitl.service import HITLService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/hitl", tags=["hitl"])

# Single service instance (stateless, safe to share)
_service = HITLService()


@router.get("/gates", response_model=list[GateSummaryResponse])
async def list_pending_gates(
    engagement_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[GateSummaryResponse]:
    """List all pending review gates, optionally filtered by engagement."""
    return await _service.get_pending_gates(session, engagement_id=engagement_id)


@router.get("/gates/{engagement_id}", response_model=list[GateSummaryResponse])
async def list_gates_for_engagement(
    engagement_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[GateSummaryResponse]:
    """List all review gates (any status) for a specific engagement."""
    return await _service.list_gates(session, engagement_id)


@router.post("/gates", response_model=GateResponse, status_code=201)
async def create_gate(
    request: CreateGateRequest,
    session: AsyncSession = Depends(get_session),
) -> GateResponse:
    """Create a new review gate with artifacts for human review.

    Called by the pipeline at gate boundaries (post-specification,
    post-deliberation). Returns the created gate with all items.
    """
    logger.info(
        "creating_review_gate",
        engagement_id=request.engagement_id,
        gate_type=request.gate_type,
        item_count=len(request.items),
    )
    return await _service.create_gate(session, request)


@router.get("/gates/{gate_id}/detail", response_model=GateResponse)
async def get_gate_detail(
    gate_id: str,
    session: AsyncSession = Depends(get_session),
) -> GateResponse:
    """Get full gate details including items and decision."""
    try:
        return await _service.get_gate(session, gate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/gates/{gate_id}/decision", response_model=GateResponse)
async def submit_decision(
    gate_id: str,
    request: SubmitDecisionRequest,
    session: AsyncSession = Depends(get_session),
) -> GateResponse:
    """Submit a human decision on a review gate.

    Valid decisions: approve, modify, reject.
    When decision is 'modify', the modifications field is required.

    Returns the updated gate with the decision record.
    """
    try:
        result = await _service.submit_decision(session, gate_id, request)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e

    logger.info(
        "review_decision_submitted",
        gate_id=gate_id,
        decision=request.decision,
        decided_by=request.decided_by,
        engagement_id=result.engagement_id,
    )
    return result
