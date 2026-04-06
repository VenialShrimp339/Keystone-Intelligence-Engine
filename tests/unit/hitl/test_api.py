"""Tests for the HITL REST API endpoints.

Uses FastAPI's TestClient with an in-memory SQLite backend.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from keystone.hitl.api import router
from keystone.hitl.db import get_session
from keystone.hitl.models import Base


@pytest.fixture
async def app():
    """Create a FastAPI app with in-memory DB for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with factory() as session:
            yield session

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_session] = override_get_session

    yield test_app

    await engine.dispose()


@pytest.fixture
async def client(app: FastAPI):
    """Async HTTP client for the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def gate_payload() -> dict:
    """Sample gate creation payload."""
    return {
        "engagement_id": "eng-001",
        "client_id": "client-001",
        "gate_type": "post_specification",
        "items": [
            {
                "item_type": "issue_tree",
                "content": {"branches": [{"label": "Market Size"}]},
                "display_order": 0,
            },
            {
                "item_type": "agent_config",
                "content": {"agents": [{"name": "quant"}]},
                "display_order": 1,
            },
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/hitl/gates
# ---------------------------------------------------------------------------


class TestCreateGateEndpoint:
    async def test_create_gate_returns_201(self, client: AsyncClient, gate_payload: dict):
        resp = await client.post("/api/hitl/gates", json=gate_payload)
        assert resp.status_code == 201

        data = resp.json()
        assert data["engagement_id"] == "eng-001"
        assert data["status"] == "pending"
        assert len(data["items"]) == 2
        assert data["decision"] is None

    async def test_create_gate_requires_items(self, client: AsyncClient):
        resp = await client.post(
            "/api/hitl/gates",
            json={
                "engagement_id": "eng-001",
                "client_id": "client-001",
                "gate_type": "post_specification",
                "items": [],
            },
        )
        assert resp.status_code == 422  # Validation error (min_length=1)


# ---------------------------------------------------------------------------
# GET /api/hitl/gates
# ---------------------------------------------------------------------------


class TestListPendingGatesEndpoint:
    async def test_list_pending_empty(self, client: AsyncClient):
        resp = await client.get("/api/hitl/gates")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_pending_after_create(self, client: AsyncClient, gate_payload: dict):
        await client.post("/api/hitl/gates", json=gate_payload)

        resp = await client.get("/api/hitl/gates")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"
        assert data[0]["item_count"] == 2

    async def test_filter_by_engagement(self, client: AsyncClient, gate_payload: dict):
        await client.post("/api/hitl/gates", json=gate_payload)

        gate_payload["engagement_id"] = "eng-002"
        await client.post("/api/hitl/gates", json=gate_payload)

        resp = await client.get("/api/hitl/gates", params={"engagement_id": "eng-001"})
        data = resp.json()
        assert len(data) == 1
        assert data[0]["engagement_id"] == "eng-001"


# ---------------------------------------------------------------------------
# GET /api/hitl/gates/{engagement_id}
# ---------------------------------------------------------------------------


class TestListGatesForEngagement:
    async def test_list_all_for_engagement(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        # Approve it
        await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={"decision": "approve", "decided_by": "jack"},
        )

        # Create another (still pending)
        await client.post("/api/hitl/gates", json=gate_payload)

        resp = await client.get("/api/hitl/gates/eng-001")
        data = resp.json()
        assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /api/hitl/gates/{gate_id}/detail
# ---------------------------------------------------------------------------


class TestGetGateDetail:
    async def test_get_detail(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        resp = await client.get(f"/api/hitl/gates/{gate_id}/detail")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == gate_id
        assert len(data["items"]) == 2
        assert data["items"][0]["content"]["branches"][0]["label"] == "Market Size"

    async def test_get_nonexistent_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/hitl/gates/nonexistent/detail")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/hitl/gates/{gate_id}/decision
# ---------------------------------------------------------------------------


class TestSubmitDecisionEndpoint:
    async def test_approve(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={"decision": "approve", "decided_by": "jack"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "approved"
        assert data["decision"]["decision"] == "approve"
        assert data["decision"]["decided_by"] == "jack"

    async def test_modify_with_payload(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={
                "decision": "modify",
                "decided_by": "jack",
                "modifications": {"issue_tree": {"branches": [{"label": "Updated"}]}},
                "reasoning": "Added regulatory branch",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "modified"
        assert data["decision"]["modifications"]["issue_tree"]["branches"][0]["label"] == "Updated"

    async def test_reject(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={
                "decision": "reject",
                "decided_by": "jack",
                "reasoning": "Misses operational analysis",
            },
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["status"] == "rejected"
        assert data["decision"]["reasoning"] == "Misses operational analysis"

    async def test_modify_without_payload_returns_400(
        self, client: AsyncClient, gate_payload: dict
    ):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        resp = await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={"decision": "modify", "decided_by": "jack"},
        )
        assert resp.status_code == 400

    async def test_double_decision_returns_400(self, client: AsyncClient, gate_payload: dict):
        create_resp = await client.post("/api/hitl/gates", json=gate_payload)
        gate_id = create_resp.json()["id"]

        await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={"decision": "approve", "decided_by": "jack"},
        )

        resp = await client.post(
            f"/api/hitl/gates/{gate_id}/decision",
            json={"decision": "reject", "decided_by": "jack"},
        )
        assert resp.status_code == 400

    async def test_decision_nonexistent_returns_404(self, client: AsyncClient):
        resp = await client.post(
            "/api/hitl/gates/nonexistent/decision",
            json={"decision": "approve", "decided_by": "jack"},
        )
        assert resp.status_code == 404
