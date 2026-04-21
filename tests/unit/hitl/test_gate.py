"""Tests for the pipeline gate integration module.

Tests the create_and_wait_for_gate function and the convenience
builders for spec and deliberation gate items.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from keystone.events import (
    ReviewGateApproved,
    ReviewGateCreated,
    ReviewGateModified,
    ReviewGateRejected,
)
from keystone.hitl.gate import (
    GateModificationRequiredError,
    GateRejectedError,
    GateTimeoutError,
    build_deliberation_gate_items,
    build_spec_gate_items,
    create_and_wait_for_gate,
)
from keystone.hitl.models import Base
from keystone.hitl.schemas import (
    DecisionType,
    GateResolution,
    GateStatus,
    GateType,
    ReviewItemType,
    SubmitDecisionRequest,
)
from keystone.hitl.service import HITLService


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(session_factory):
    async with session_factory() as sess:
        yield sess


# ---------------------------------------------------------------------------
# Convenience builder tests
# ---------------------------------------------------------------------------


class TestBuildSpecGateItems:
    def test_builds_issue_tree_and_agent_config(self):
        items = build_spec_gate_items(
            issue_tree={"branches": []},
            agent_configs=[{"name": "quant"}],
        )
        assert len(items) == 2
        assert items[0].item_type == ReviewItemType.ISSUE_TREE
        assert items[1].item_type == ReviewItemType.AGENT_CONFIG

    def test_includes_sprint_contract_when_provided(self):
        items = build_spec_gate_items(
            issue_tree={"branches": []},
            agent_configs=[],
            sprint_contract={"criteria": ["factual accuracy > 90%"]},
        )
        assert len(items) == 3
        assert items[2].item_type == ReviewItemType.SPRINT_CONTRACT

    def test_display_order_ascending(self):
        items = build_spec_gate_items(
            issue_tree={},
            agent_configs=[],
            sprint_contract={},
        )
        orders = [i.display_order for i in items]
        assert orders == [0, 1, 2]


class TestBuildDeliberationGateItems:
    def test_builds_confidence_map(self):
        items = build_deliberation_gate_items(
            confidence_map={"high_confidence": []},
        )
        assert len(items) == 1
        assert items[0].item_type == ReviewItemType.CONFIDENCE_MAP

    def test_includes_divergence_points(self):
        items = build_deliberation_gate_items(
            confidence_map={"high_confidence": []},
            divergence_points={"points": ["method A vs B"]},
        )
        assert len(items) == 2
        assert items[1].item_type == ReviewItemType.DIVERGENCE_POINTS


# ---------------------------------------------------------------------------
# create_and_wait_for_gate tests
# ---------------------------------------------------------------------------


class TestCreateAndWaitForGate:
    async def test_returns_on_approve(self, session_factory):
        """Simulate: gate created, then approved in a background task."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )

            async def approve_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    assert len(pending) == 1
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
                    )

            task = asyncio.create_task(approve_after_delay())

            result = await create_and_wait_for_gate(
                session,
                engagement_id="eng-001",
                client_id="client-001",
                gate_type=GateType.POST_SPECIFICATION,
                items=items,
                poll_interval=0.05,
                timeout=5.0,
            )

            await task
            assert isinstance(result, GateResolution)
            assert result.status == GateStatus.APPROVED

    async def test_raises_on_reject(self, session_factory):
        """Simulate: gate created, then rejected."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )

            async def reject_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.REJECT,
                            decided_by="jack",
                            reasoning="Bad decomposition",
                        ),
                    )

            task = asyncio.create_task(reject_after_delay())

            with pytest.raises(GateRejectedError, match="rejected"):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                )

            await task

    async def test_timeout_raises(self, session_factory):
        """Gate created but no decision arrives within timeout."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )

            with pytest.raises(GateTimeoutError):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=0.1,
                )

    async def test_modified_gate_halts_until_patch_is_applied(self, session_factory):
        """Modified gates block when no downstream patch application exists."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            mods = {"issue_tree": {"branches": [{"label": "New Branch"}]}}

            async def modify_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.MODIFY,
                            decided_by="jack",
                            modifications=mods,
                        ),
                    )

            task = asyncio.create_task(modify_after_delay())

            with pytest.raises(
                GateModificationRequiredError,
                match="modifications are not yet supported",
            ) as exc_info:
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                )

            await task
            result = exc_info.value.resolution
            assert isinstance(result, GateResolution)
            assert result.status == GateStatus.MODIFIED
            assert result.decision is not None
            assert result.decision.modifications == mods
            assert result.patch_applied is False


# ---------------------------------------------------------------------------
# HITL event emission (Task #13)
# ---------------------------------------------------------------------------


class TestHITLEventEmission:
    async def test_approve_emits_created_and_approved_events(self, session_factory):
        """Approved gate emits ReviewGateCreated then ReviewGateApproved."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            collector: list = []

            async def approve_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
                    )

            task = asyncio.create_task(approve_after_delay())
            await create_and_wait_for_gate(
                session,
                engagement_id="eng-001",
                client_id="client-001",
                gate_type=GateType.POST_SPECIFICATION,
                items=items,
                poll_interval=0.05,
                timeout=5.0,
                event_collector=collector,
            )
            await task

            types = [type(e) for e in collector]
            assert ReviewGateCreated in types
            assert ReviewGateApproved in types
            created = next(e for e in collector if isinstance(e, ReviewGateCreated))
            approved = next(e for e in collector if isinstance(e, ReviewGateApproved))
            assert created.engagement_id == "eng-001"
            assert created.item_count == 2
            assert approved.gate_id == created.gate_id

    async def test_reject_emits_created_and_rejected_events(self, session_factory):
        """Rejected gate emits ReviewGateCreated then ReviewGateRejected."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            collector: list = []

            async def reject_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.REJECT,
                            decided_by="jack",
                            reasoning="Bad decomposition",
                        ),
                    )

            task = asyncio.create_task(reject_after_delay())
            with pytest.raises(GateRejectedError):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                    event_collector=collector,
                )
            await task

            types = [type(e) for e in collector]
            assert ReviewGateCreated in types
            assert ReviewGateRejected in types
            rejected = next(e for e in collector if isinstance(e, ReviewGateRejected))
            assert rejected.reasoning == "Bad decomposition"

    async def test_modify_emits_created_and_modified_events(self, session_factory):
        """Modified gate emits ReviewGateCreated then ReviewGateModified."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            mods = {"issue_tree": {"branches": [{"label": "New Branch"}]}}
            collector: list = []

            async def modify_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.MODIFY,
                            decided_by="jack",
                            modifications=mods,
                        ),
                    )

            task = asyncio.create_task(modify_after_delay())
            with pytest.raises(GateModificationRequiredError):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                    event_collector=collector,
                )
            await task

            types = [type(e) for e in collector]
            assert ReviewGateCreated in types
            assert ReviewGateModified in types
            modified = next(e for e in collector if isinstance(e, ReviewGateModified))
            assert "issue_tree" in modified.modification_keys

    async def test_modify_emits_event_with_modifications_path(self, session_factory, tmp_path):
        """ReviewGateModified event carries the path where modifications were persisted."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            mods = {"issue_tree": {"branches": [{"label": "Revised"}]}}
            collector: list = []

            async def modify_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.MODIFY,
                            decided_by="jack",
                            modifications=mods,
                        ),
                    )

            task = asyncio.create_task(modify_after_delay())
            with (
                patch(
                    "keystone.hitl.gate._persist_modifications",
                    return_value=str(tmp_path / "hitl_mod.json"),
                ),
                pytest.raises(GateModificationRequiredError),
            ):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                    event_collector=collector,
                )
            await task

            modified = next(e for e in collector if isinstance(e, ReviewGateModified))
            assert modified.modifications_path == str(tmp_path / "hitl_mod.json")

    async def test_no_event_collector_does_not_error(self, session_factory):
        """Omitting event_collector is backward-compatible (no AttributeError)."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )

            async def approve_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(decision=DecisionType.APPROVE, decided_by="jack"),
                    )

            task = asyncio.create_task(approve_after_delay())
            result = await create_and_wait_for_gate(
                session,
                engagement_id="eng-001",
                client_id="client-001",
                gate_type=GateType.POST_SPECIFICATION,
                items=items,
                poll_interval=0.05,
                timeout=5.0,
                # No event_collector argument
            )
            await task
            assert result.status == GateStatus.APPROVED


# ---------------------------------------------------------------------------
# GAP-04 Phase 1: modification persistence tests
# ---------------------------------------------------------------------------


class TestModificationPersistence:
    async def test_modifications_json_written_to_expected_path(self, session_factory, tmp_path):
        """When MODIFIED, the modifications JSON file is written under the expected directory."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            mods = {"issue_tree": {"branches": [{"label": "New Branch"}]}}

            async def modify_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.MODIFY,
                            decided_by="jack",
                            modifications=mods,
                        ),
                    )

            task = asyncio.create_task(modify_after_delay())
            persist_dir = tmp_path / "keystone" / "eng-persist" / "hitl_modifications"

            def fake_persist(engagement_id, client_id, gate_name, modifications):
                persist_dir.mkdir(parents=True, exist_ok=True)
                out = persist_dir / f"{gate_name}_test.json"
                payload = {
                    "engagement_id": engagement_id,
                    "client_id": client_id,
                    "gate_name": gate_name,
                    "modifications": modifications,
                }
                out.write_text(json.dumps(payload))
                return str(out)

            with (
                patch("keystone.hitl.gate._persist_modifications", side_effect=fake_persist),
                pytest.raises(GateModificationRequiredError),
            ):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-persist",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                )
            await task

            written = list(persist_dir.iterdir())
            assert len(written) == 1
            payload = json.loads(written[0].read_text())
            assert payload["engagement_id"] == "eng-persist"
            assert payload["modifications"] == mods

    async def test_persist_failure_does_not_mask_modification_error(self, session_factory):
        """A write failure during persistence still raises GateModificationRequiredError."""
        async with session_factory() as session:
            items = build_spec_gate_items(
                issue_tree={"branches": []},
                agent_configs=[],
            )
            mods = {"issue_tree": {"branches": []}}

            async def modify_after_delay():
                await asyncio.sleep(0.1)
                async with session_factory() as bg_session:
                    service = HITLService()
                    pending = await service.get_pending_gates(bg_session)
                    await service.submit_decision(
                        bg_session,
                        pending[0].id,
                        SubmitDecisionRequest(
                            decision=DecisionType.MODIFY,
                            decided_by="jack",
                            modifications=mods,
                        ),
                    )

            task = asyncio.create_task(modify_after_delay())

            # Simulate _persist_modifications returning None (failure absorbed internally)
            with (
                patch(
                    "keystone.hitl.gate._persist_modifications",
                    return_value=None,
                ),
                pytest.raises(GateModificationRequiredError),
            ):
                await create_and_wait_for_gate(
                    session,
                    engagement_id="eng-001",
                    client_id="client-001",
                    gate_type=GateType.POST_SPECIFICATION,
                    items=items,
                    poll_interval=0.05,
                    timeout=5.0,
                )
            await task
