"""Tests for lock-file-based task claiming."""

import asyncio
from pathlib import Path

import pytest

from keystone.research.task_claimer import TaskClaimer


@pytest.fixture()
def claimer(tmp_path: Path) -> TaskClaimer:
    return TaskClaimer(lock_dir=tmp_path / "locks")


# ---------------------------------------------------------------------------
# Basic claiming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_claim_unclaimed_task(claimer: TaskClaimer) -> None:
    assert await claimer.claim("task_001", "agent_A")
    assert await claimer.is_claimed("task_001")
    assert await claimer.get_owner("task_001") == "agent_A"


@pytest.mark.asyncio
async def test_claim_already_claimed_by_other(claimer: TaskClaimer) -> None:
    await claimer.claim("task_001", "agent_A")
    assert not await claimer.claim("task_001", "agent_B")
    assert await claimer.get_owner("task_001") == "agent_A"


@pytest.mark.asyncio
async def test_reclaim_by_same_agent(claimer: TaskClaimer) -> None:
    await claimer.claim("task_001", "agent_A")
    assert await claimer.claim("task_001", "agent_A")


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_release_claimed_task(claimer: TaskClaimer) -> None:
    await claimer.claim("task_001", "agent_A")
    assert await claimer.release("task_001", "agent_A")
    assert not await claimer.is_claimed("task_001")


@pytest.mark.asyncio
async def test_release_by_wrong_agent(claimer: TaskClaimer) -> None:
    await claimer.claim("task_001", "agent_A")
    assert not await claimer.release("task_001", "agent_B")
    assert await claimer.is_claimed("task_001")


@pytest.mark.asyncio
async def test_release_unclaimed(claimer: TaskClaimer) -> None:
    assert not await claimer.release("task_001", "agent_A")


# ---------------------------------------------------------------------------
# Concurrent claiming
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_claim_only_one_wins(claimer: TaskClaimer) -> None:
    results = await asyncio.gather(
        claimer.claim("task_001", "agent_A"),
        claimer.claim("task_001", "agent_B"),
        claimer.claim("task_001", "agent_C"),
    )
    assert sum(results) == 1  # Exactly one agent wins


# ---------------------------------------------------------------------------
# Release all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_release_all(claimer: TaskClaimer) -> None:
    await claimer.claim("task_001", "agent_A")
    await claimer.claim("task_002", "agent_A")
    await claimer.claim("task_003", "agent_B")

    released = await claimer.release_all("agent_A")
    assert set(released) == {"task_001", "task_002"}
    assert not await claimer.is_claimed("task_001")
    assert not await claimer.is_claimed("task_002")
    assert await claimer.is_claimed("task_003")  # agent_B's task untouched


@pytest.mark.asyncio
async def test_unclaimed_task_not_claimed(claimer: TaskClaimer) -> None:
    assert not await claimer.is_claimed("task_999")
    assert await claimer.get_owner("task_999") is None
