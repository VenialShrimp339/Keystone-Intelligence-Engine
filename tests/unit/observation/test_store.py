"""Tests for the ObservationStore (GAP-05 first slice)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from keystone.observation.store import ObservationStore


@pytest.fixture
async def store():
    s = ObservationStore(":memory:")
    await s.initialize()
    yield s
    await s.close()


async def _insert_sample(
    store: ObservationStore,
    *,
    observation_id: str = "OBS-abc12345-task001-001",
    client_id: str = "client_001",
    engagement_id: str = "eng_001",
    engagement_type: str = "SIZING",
    task_id: str = "task_001",
    obs_type: str = "rejection",
    category: int = 2,
    dimension: str = "analytical_depth",
    composite_score: float = 45.0,
    dimension_scores: dict[str, float] | None = None,
    governance_flags: list[str] | None = None,
    recorded_at: datetime | None = None,
) -> None:
    await store.record(
        observation_id=observation_id,
        client_id=client_id,
        engagement_id=engagement_id,
        engagement_type=engagement_type,
        task_id=task_id,
        obs_type=obs_type,
        category=category,
        dimension=dimension,
        composite_score=composite_score,
        dimension_scores=dimension_scores or {"analytical_depth": 35.0, "intent_alignment": 72.0},
        governance_flags=governance_flags or [],
        recorded_at=recorded_at,
    )


class TestObservationStoreLifecycle:
    @pytest.mark.asyncio
    async def test_initialize_creates_table(self, store: ObservationStore) -> None:
        assert await store.count() == 0

    @pytest.mark.asyncio
    async def test_record_and_count(self, store: ObservationStore) -> None:
        await _insert_sample(store)
        assert await store.count() == 1

    @pytest.mark.asyncio
    async def test_record_upserts_on_duplicate_id(self, store: ObservationStore) -> None:
        await _insert_sample(store, composite_score=40.0)
        await _insert_sample(store, composite_score=55.0)
        assert await store.count() == 1
        rows = await store.query_by_client("client_001")
        assert rows[0].composite_score == 55.0

    @pytest.mark.asyncio
    async def test_uninitialized_raises(self) -> None:
        s = ObservationStore(":memory:")
        with pytest.raises(RuntimeError, match="not initialized"):
            await s.record(
                observation_id="x",
                client_id="c",
                engagement_id="e",
                engagement_type="SIZING",
                task_id="t",
                obs_type="success",
                category=3,
                dimension="actionability",
                composite_score=80.0,
                dimension_scores={},
                governance_flags=[],
            )


class TestObservationStoreQueries:
    @pytest.mark.asyncio
    async def test_query_by_client_returns_matching(self, store: ObservationStore) -> None:
        await _insert_sample(store, observation_id="OBS-1", client_id="alpha")
        await _insert_sample(store, observation_id="OBS-2", client_id="beta")
        rows = await store.query_by_client("alpha")
        assert len(rows) == 1
        assert rows[0].client_id == "alpha"

    @pytest.mark.asyncio
    async def test_query_by_client_with_type_filter(self, store: ObservationStore) -> None:
        await _insert_sample(store, observation_id="OBS-1", obs_type="rejection")
        await _insert_sample(store, observation_id="OBS-2", obs_type="success")
        rejections = await store.query_by_client("client_001", obs_type="rejection")
        assert len(rejections) == 1
        assert rejections[0].type == "rejection"

    @pytest.mark.asyncio
    async def test_query_by_dimension(self, store: ObservationStore) -> None:
        await _insert_sample(store, observation_id="OBS-1", dimension="analytical_depth")
        await _insert_sample(store, observation_id="OBS-2", dimension="source_quality")
        rows = await store.query_by_dimension("client_001", "analytical_depth")
        assert len(rows) == 1
        assert rows[0].dimension == "analytical_depth"

    @pytest.mark.asyncio
    async def test_query_by_dimension_with_type(self, store: ObservationStore) -> None:
        await _insert_sample(
            store, observation_id="OBS-1", dimension="actionability", obs_type="rejection"
        )
        await _insert_sample(
            store, observation_id="OBS-2", dimension="actionability", obs_type="success"
        )
        successes = await store.query_by_dimension(
            "client_001", "actionability", obs_type="success"
        )
        assert len(successes) == 1
        assert successes[0].type == "success"

    @pytest.mark.asyncio
    async def test_query_respects_limit(self, store: ObservationStore) -> None:
        for i in range(10):
            await _insert_sample(
                store,
                observation_id=f"OBS-{i}",
                recorded_at=datetime(2026, 4, 21, i, 0, tzinfo=UTC),
            )
        rows = await store.query_by_client("client_001", limit=3)
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_query_orders_by_recorded_at_desc(self, store: ObservationStore) -> None:
        await _insert_sample(
            store,
            observation_id="OBS-old",
            recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await _insert_sample(
            store,
            observation_id="OBS-new",
            recorded_at=datetime(2026, 4, 21, tzinfo=UTC),
        )
        rows = await store.query_by_client("client_001")
        assert rows[0].observation_id == "OBS-new"
        assert rows[1].observation_id == "OBS-old"

    @pytest.mark.asyncio
    async def test_count_scoped_to_client(self, store: ObservationStore) -> None:
        await _insert_sample(store, observation_id="OBS-1", client_id="alpha")
        await _insert_sample(store, observation_id="OBS-2", client_id="alpha")
        await _insert_sample(store, observation_id="OBS-3", client_id="beta")
        assert await store.count("alpha") == 2
        assert await store.count("beta") == 1
        assert await store.count() == 3


class TestObservationRowDeserialization:
    @pytest.mark.asyncio
    async def test_dimension_scores_deserialized_as_dict(self, store: ObservationStore) -> None:
        scores = {"analytical_depth": 35.0, "intent_alignment": 72.0, "source_quality": 60.0}
        await _insert_sample(store, dimension_scores=scores)
        rows = await store.query_by_client("client_001")
        assert rows[0].dimension_scores == scores

    @pytest.mark.asyncio
    async def test_governance_flags_deserialized_as_list(self, store: ObservationStore) -> None:
        flags = ["l4_rubric_threshold", "sprint_contract_fallback"]
        await _insert_sample(store, governance_flags=flags)
        rows = await store.query_by_client("client_001")
        assert rows[0].governance_flags == flags
