"""Tests for per-agent filesystem isolation."""

import asyncio
from pathlib import Path

import pytest

from keystone.research.isolation import AgentWorkspace, IsolationManager


@pytest.fixture()
def iso_manager(tmp_path: Path) -> IsolationManager:
    return IsolationManager(base_dir=tmp_path)


# ---------------------------------------------------------------------------
# Workspace creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_workspace(iso_manager: IsolationManager) -> None:
    ws = await iso_manager.create_workspace("agent_001")
    assert ws.path.exists()
    assert ws.agent_id == "agent_001"
    assert (ws.path / ".lock").exists()


@pytest.mark.asyncio
async def test_create_workspace_idempotent(iso_manager: IsolationManager) -> None:
    ws1 = await iso_manager.create_workspace("agent_001")
    ws2 = await iso_manager.create_workspace("agent_001")
    assert ws1 is ws2


# ---------------------------------------------------------------------------
# Isolation enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agents_cannot_see_each_other(iso_manager: IsolationManager) -> None:
    ws_a = await iso_manager.create_workspace("agent_A")
    ws_b = await iso_manager.create_workspace("agent_B")

    await ws_a.write_file("notes.txt", "agent A data")

    # Agent B's workspace should not contain agent A's file
    assert not (ws_b.path / "notes.txt").exists()

    # Agent B cannot verify paths inside Agent A's workspace
    agent_a_file = ws_a.path / "notes.txt"
    assert not ws_b.is_within_workspace(agent_a_file)
    assert ws_a.is_within_workspace(agent_a_file)


@pytest.mark.asyncio
async def test_verify_isolation(iso_manager: IsolationManager) -> None:
    ws = await iso_manager.create_workspace("agent_001")
    inside = ws.path / "data.txt"
    outside = iso_manager.base_dir / "other_agent" / "data.txt"

    assert iso_manager.verify_isolation("agent_001", inside)
    assert not iso_manager.verify_isolation("agent_001", outside)
    assert not iso_manager.verify_isolation("nonexistent", inside)


@pytest.mark.asyncio
async def test_path_escape_rejected(iso_manager: IsolationManager) -> None:
    ws = await iso_manager.create_workspace("agent_001")

    with pytest.raises(PermissionError, match="escapes workspace"):
        await ws.write_file("../../escape.txt", "bad data")

    with pytest.raises(PermissionError, match="escapes workspace"):
        await ws.read_file("../../escape.txt")


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_and_read_file(iso_manager: IsolationManager) -> None:
    ws = await iso_manager.create_workspace("agent_001")
    path = await ws.write_file("subdir/notes.md", "# Research notes")
    assert path.exists()

    content = await ws.read_file("subdir/notes.md")
    assert content == "# Research notes"


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_all(iso_manager: IsolationManager) -> None:
    ws_a = await iso_manager.create_workspace("agent_A")
    ws_b = await iso_manager.create_workspace("agent_B")

    await iso_manager.cleanup_all()

    assert not ws_a.path.exists()
    assert not ws_b.path.exists()
    assert iso_manager.get_workspace("agent_A") is None
