"""Tests for HITLService business logic.

Uses aiosqlite for in-memory testing (no PostgreSQL required).
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from keystone.hitl.models import Base
from keystone.hitl.schemas import (
    CreateGateRequest,
    DecisionType,
    GateStatus,
    GateType,
    ReviewItemCreate,
    ReviewItemType,
    SubmitDecisionRequest,
)
from keystone.hitl.service import HITLService


@pytest.fixture
async def engine():
    """Create an in-memory SQLite engine for testing."""
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Provide a fresh async session per test."""
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest.fixture
def service() -> HITLService:
    return HITLService()


@pytest.fixture
def spec_gate_request() -> CreateGateRequest:
    """Sample post-specification gate creation request."""
    return CreateGateRequest(
        engagement_id="eng-001",
        client_id="client-001",
        gate_type=GateType.POST_SPECIFICATION,
        items=[
            ReviewItemCreate(
                item_type=ReviewItemType.ISSUE_TREE,
                content={"branches": [{"label": "Market Size", "children": []}]},
                display_order=0,
            ),
            ReviewItemCreate(
                item_type=ReviewItemType.AGENT_CONFIG,
                content={"agents": [{"name": "quant", "tools": ["exa", "brave"]}]},
                display_order=1,
            ),
        ],
    )


@pytest.fixture
def deliberation_gate_request() -> CreateGateRequest:
    """Sample post-deliberation gate creation request."""
    return CreateGateRequest(
        engagement_id="eng-001",
        client_id="client-001",
        gate_type=GateType.POST_DELIBERATION,
        items=[
            ReviewItemCreate(
                item_type=ReviewItemType.CONFIDENCE_MAP,
                content={"high_confidence": [], "moderate_confidence": []},
                display_order=0,
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Gate creation tests
# ---------------------------------------------------------------------------


class TestCreateGate:
    async def test_creates_gate_with_items(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        assert gate.engagement_id == "eng-001"
        assert gate.client_id == "client-001"
        assert gate.gate_type == GateType.POST_SPECIFICATION
        assert gate.status == GateStatus.PENDING
        assert len(gate.items) == 2
        assert gate.decision is None

    async def test_items_ordered_by_display_order(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        assert gate.items[0].item_type == ReviewItemType.ISSUE_TREE
        assert gate.items[0].display_order == 0
        assert gate.items[1].item_type == ReviewItemType.AGENT_CONFIG
        assert gate.items[1].display_order == 1

    async def test_item_content_preserved(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        tree_item = gate.items[0]
        assert tree_item.content["branches"][0]["label"] == "Market Size"

    async def test_gate_id_is_uuid(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)
        # UUID4 format: 8-4-4-4-12 hex digits
        parts = gate.id.split("-")
        assert len(parts) == 5

    async def test_creates_deliberation_gate(
        self,
        session: AsyncSession,
        service: HITLService,
        deliberation_gate_request: CreateGateRequest,
    ):
        gate = await service.create_gate(session, deliberation_gate_request)

        assert gate.gate_type == GateType.POST_DELIBERATION
        assert len(gate.items) == 1
        assert gate.items[0].item_type == ReviewItemType.CONFIDENCE_MAP


# ---------------------------------------------------------------------------
# Gate retrieval tests
# ---------------------------------------------------------------------------


class TestGetGate:
    async def test_get_existing_gate(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        created = await service.create_gate(session, spec_gate_request)
        fetched = await service.get_gate(session, created.id)

        assert fetched.id == created.id
        assert fetched.engagement_id == created.engagement_id
        assert len(fetched.items) == len(created.items)

    async def test_get_nonexistent_gate_raises(
        self, session: AsyncSession, service: HITLService
    ):
        with pytest.raises(ValueError, match="not found"):
            await service.get_gate(session, "nonexistent-id")


class TestGetPendingGates:
    async def test_returns_only_pending(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        pending = await service.get_pending_gates(session)
        assert len(pending) == 1
        assert pending[0].id == gate.id

        # Approve the gate
        await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(
                decision=DecisionType.APPROVE, decided_by="jack"
            ),
        )

        pending = await service.get_pending_gates(session)
        assert len(pending) == 0

    async def test_filters_by_engagement(
        self, session: AsyncSession, service: HITLService
    ):
        # Create gates for different engagements
        for eng_id in ["eng-A", "eng-B", "eng-A"]:
            await service.create_gate(
                session,
                CreateGateRequest(
                    engagement_id=eng_id,
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=[
                        ReviewItemCreate(
                            item_type=ReviewItemType.ISSUE_TREE,
                            content={"test": True},
                            display_order=0,
                        )
                    ],
                ),
            )

        all_pending = await service.get_pending_gates(session)
        assert len(all_pending) == 3

        eng_a_pending = await service.get_pending_gates(session, engagement_id="eng-A")
        assert len(eng_a_pending) == 2


class TestListGates:
    async def test_lists_all_statuses(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        # Approve it
        await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
        )

        # Create another (still pending)
        await service.create_gate(session, spec_gate_request)

        all_gates = await service.list_gates(session, "eng-001")
        assert len(all_gates) == 2

        statuses = {g.status for g in all_gates}
        assert GateStatus.APPROVED in statuses
        assert GateStatus.PENDING in statuses


# ---------------------------------------------------------------------------
# Decision submission tests
# ---------------------------------------------------------------------------


class TestSubmitDecision:
    async def test_approve_transitions_to_approved(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)
        result = await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
        )

        assert result.status == GateStatus.APPROVED
        assert result.resolved_by == "jack"
        assert result.resolved_at is not None
        assert result.decision is not None
        assert result.decision.decision == DecisionType.APPROVE

    async def test_modify_transitions_to_modified(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)
        modifications = {"issue_tree": {"branches": [{"label": "Updated Branch"}]}}

        result = await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(
                decision=DecisionType.MODIFY,
                decided_by="jack",
                modifications=modifications,
                reasoning="Added a branch for regulatory analysis",
            ),
        )

        assert result.status == GateStatus.MODIFIED
        assert result.decision is not None
        assert result.decision.modifications == modifications
        assert result.decision.reasoning == "Added a branch for regulatory analysis"

    async def test_reject_transitions_to_rejected(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)
        result = await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(
                decision=DecisionType.REJECT,
                decided_by="jack",
                reasoning="Issue tree misses operational analysis entirely",
            ),
        )

        assert result.status == GateStatus.REJECTED
        assert result.decision is not None
        assert result.decision.reasoning == "Issue tree misses operational analysis entirely"

    async def test_modify_without_modifications_raises(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        with pytest.raises(ValueError, match="Modifications required"):
            await service.submit_decision(
                session,
                gate.id,
                SubmitDecisionRequest(
                    decision=DecisionType.MODIFY, decided_by="jack"
                ),
            )

    async def test_double_decision_raises(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
        )

        with pytest.raises(ValueError, match="already resolved"):
            await service.submit_decision(
                session,
                gate.id,
                SubmitDecisionRequest(
                    decision=DecisionType.REJECT, decided_by="jack"
                ),
            )

    async def test_decision_on_nonexistent_gate_raises(
        self, session: AsyncSession, service: HITLService
    ):
        with pytest.raises(ValueError, match="not found"):
            await service.submit_decision(
                session,
                "nonexistent",
                SubmitDecisionRequest(
                    decision=DecisionType.APPROVE, decided_by="jack"
                ),
            )


# ---------------------------------------------------------------------------
# Wait for decision tests
# ---------------------------------------------------------------------------


class TestWaitForDecision:
    async def test_returns_immediately_if_already_resolved(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)
        await service.submit_decision(
            session,
            gate.id,
            SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
        )

        result = await service.wait_for_decision(session, gate.id, poll_interval=0.1)
        assert result.status == GateStatus.APPROVED

    async def test_timeout_on_no_decision(
        self, session: AsyncSession, service: HITLService, spec_gate_request: CreateGateRequest
    ):
        gate = await service.create_gate(session, spec_gate_request)

        with pytest.raises(TimeoutError, match="Timeout"):
            await service.wait_for_decision(
                session, gate.id, poll_interval=0.05, timeout=0.1
            )

    async def test_wait_nonexistent_gate_raises(
        self, session: AsyncSession, service: HITLService
    ):
        with pytest.raises(ValueError, match="not found"):
            await service.wait_for_decision(
                session, "nonexistent", poll_interval=0.05, timeout=0.1
            )
