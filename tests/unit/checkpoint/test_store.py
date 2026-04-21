"""Unit tests for CheckpointStore."""

from __future__ import annotations

import pytest

from keystone.checkpoint.store import (
    CURRENT_SCHEMA_VERSION,
    STAGE_ORDER,
    CheckpointStore,
    CheckpointVersionError,
)


@pytest.fixture
async def store():
    s = CheckpointStore(":memory:")
    await s.initialize()
    yield s
    await s.close()


# -----------------------------------------------------------------------
# Basic CRUD
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_and_load(store: CheckpointStore):
    payload = {"spec": {"a": 1}, "governance": {"b": 2}}
    await store.save("eng_1", "POST_SPEC", payload)

    result = await store.load("eng_1")
    assert "POST_SPEC" in result
    assert result["POST_SPEC"] == payload


@pytest.mark.asyncio
async def test_save_overwrites(store: CheckpointStore):
    await store.save("eng_1", "POST_SPEC", {"version": 1})
    await store.save("eng_1", "POST_SPEC", {"version": 2})

    result = await store.load("eng_1")
    assert result["POST_SPEC"]["version"] == 2


@pytest.mark.asyncio
async def test_load_returns_ordered_by_stage(store: CheckpointStore):
    await store.save("eng_1", "POST_DELIBERATION", {"step": 3})
    await store.save("eng_1", "POST_SPEC", {"step": 1})
    await store.save("eng_1", "POST_L1_CITPROC", {"step": 2})

    result = await store.load("eng_1")
    assert list(result.keys()) == ["POST_SPEC", "POST_L1_CITPROC", "POST_DELIBERATION"]


@pytest.mark.asyncio
async def test_load_empty_engagement(store: CheckpointStore):
    result = await store.load("nonexistent")
    assert result == {}


@pytest.mark.asyncio
async def test_load_stage(store: CheckpointStore):
    await store.save("eng_1", "POST_SPEC", {"data": "spec"})
    await store.save("eng_1", "POST_L1_CITPROC", {"data": "l1"})

    result = await store.load_stage("eng_1", "POST_SPEC")
    assert result == {"data": "spec"}

    result = await store.load_stage("eng_1", "POST_EVALUATION")
    assert result is None


@pytest.mark.asyncio
async def test_is_resumable(store: CheckpointStore):
    assert not await store.is_resumable("eng_1")

    await store.save("eng_1", "POST_SPEC", {"data": 1})
    assert await store.is_resumable("eng_1")


@pytest.mark.asyncio
async def test_delete(store: CheckpointStore):
    await store.save("eng_1", "POST_SPEC", {"data": 1})
    await store.save("eng_1", "POST_L1_CITPROC", {"data": 2})

    await store.delete("eng_1")
    assert not await store.is_resumable("eng_1")
    assert await store.load("eng_1") == {}


# -----------------------------------------------------------------------
# Schema versioning
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_rejects_future_schema_version(store: CheckpointStore):
    """Checkpoints written by a newer code version raise CheckpointVersionError."""
    conn = store._conn()
    await conn.execute(
        "INSERT INTO checkpoints (engagement_id, stage_name, written_at, schema_version, payload) "
        "VALUES (?, ?, ?, ?, ?)",
        ("eng_future", "POST_SPEC", "2026-01-01T00:00:00", CURRENT_SCHEMA_VERSION + 1, "{}"),
    )
    await conn.commit()

    with pytest.raises(CheckpointVersionError):
        await store.load("eng_future")


@pytest.mark.asyncio
async def test_load_stage_rejects_future_schema_version(store: CheckpointStore):
    conn = store._conn()
    await conn.execute(
        "INSERT INTO checkpoints (engagement_id, stage_name, written_at, schema_version, payload) "
        "VALUES (?, ?, ?, ?, ?)",
        ("eng_future", "POST_SPEC", "2026-01-01T00:00:00", CURRENT_SCHEMA_VERSION + 1, "{}"),
    )
    await conn.commit()

    with pytest.raises(CheckpointVersionError):
        await store.load_stage("eng_future", "POST_SPEC")


# -----------------------------------------------------------------------
# Cleanup / TTL
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_expired(store: CheckpointStore):
    conn = store._conn()
    await conn.execute(
        "INSERT INTO checkpoints (engagement_id, stage_name, written_at, schema_version, payload) "
        "VALUES (?, ?, ?, ?, ?)",
        ("eng_old", "POST_SPEC", "2020-01-01T00:00:00+00:00", 1, '{"old": true}'),
    )
    await conn.commit()

    await store.save("eng_fresh", "POST_SPEC", {"fresh": True})

    deleted = await store.cleanup_expired(max_age_days=7)
    assert deleted == 1
    assert not await store.is_resumable("eng_old")
    assert await store.is_resumable("eng_fresh")


# -----------------------------------------------------------------------
# Fire-and-log (save failure does not propagate)
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_failure_does_not_raise(store: CheckpointStore):
    """If the DB write fails, save() logs but does not raise."""
    await store.close()
    store._db = None

    # Should not raise — fire-and-log pattern.
    await store.save("eng_1", "POST_SPEC", {"data": 1})


# -----------------------------------------------------------------------
# Not-initialized guard
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conn_guard_before_initialize():
    store = CheckpointStore(":memory:")
    with pytest.raises(RuntimeError, match="not initialized"):
        store._conn()


# -----------------------------------------------------------------------
# Stage order constant
# -----------------------------------------------------------------------


def test_stage_order_contains_all_stages():
    assert len(STAGE_ORDER) == 5
    assert STAGE_ORDER[0] == "POST_SPEC"
    assert STAGE_ORDER[-1] == "POST_EVALUATION"


# -----------------------------------------------------------------------
# Isolation: separate engagements don't leak
# -----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_engagement_isolation(store: CheckpointStore):
    await store.save("eng_A", "POST_SPEC", {"owner": "A"})
    await store.save("eng_B", "POST_SPEC", {"owner": "B"})

    result_a = await store.load("eng_A")
    result_b = await store.load("eng_B")
    assert result_a["POST_SPEC"]["owner"] == "A"
    assert result_b["POST_SPEC"]["owner"] == "B"

    await store.delete("eng_A")
    assert not await store.is_resumable("eng_A")
    assert await store.is_resumable("eng_B")
