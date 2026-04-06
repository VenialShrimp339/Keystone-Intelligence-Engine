"""Per-agent filesystem isolation for research agents.

Each agent gets an isolated working directory. Agents cannot read
each other's files. Advisory file locks prevent concurrent writes.
Async-safe operations throughout.

Isolation is structural, not framework-level (68.8% leakage in
AgentLeak benchmark confirms this necessity).
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path


class AgentWorkspace:
    """Isolated filesystem workspace for a single research agent."""

    def __init__(self, base_dir: Path, agent_id: str) -> None:
        self._base_dir = base_dir
        self._agent_id = agent_id
        self._workspace_dir = base_dir / agent_id
        self._lock_path = self._workspace_dir / ".lock"
        self._lock = asyncio.Lock()

    @property
    def path(self) -> Path:
        return self._workspace_dir

    @property
    def agent_id(self) -> str:
        return self._agent_id

    async def setup(self) -> Path:
        """Create the isolated workspace directory and advisory lock."""
        self._workspace_dir.mkdir(parents=True, exist_ok=True)
        self._lock_path.write_text(self._agent_id)
        return self._workspace_dir

    async def cleanup(self) -> None:
        """Remove the workspace directory."""
        if self._workspace_dir.exists():
            shutil.rmtree(self._workspace_dir)

    def is_within_workspace(self, path: Path) -> bool:
        """Check if a path is within this agent's workspace."""
        try:
            path.resolve().relative_to(self._workspace_dir.resolve())
            return True
        except ValueError:
            return False

    async def write_file(self, relative_path: str, content: str) -> Path:
        """Write a file within the workspace. Raises on path escape."""
        async with self._lock:
            target = self._workspace_dir / relative_path
            if not self.is_within_workspace(target):
                msg = f"Path escapes workspace: {relative_path}"
                raise PermissionError(msg)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return target

    async def read_file(self, relative_path: str) -> str:
        """Read a file within the workspace. Raises on path escape."""
        async with self._lock:
            target = self._workspace_dir / relative_path
            if not self.is_within_workspace(target):
                msg = f"Path escapes workspace: {relative_path}"
                raise PermissionError(msg)
            return target.read_text()


class IsolationManager:
    """Manages isolated workspaces for all agents in an engagement."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is None:
            base_dir = Path(tempfile.mkdtemp(prefix="keystone_research_"))
        self._base_dir = base_dir
        self._workspaces: dict[str, AgentWorkspace] = {}

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    async def create_workspace(self, agent_id: str) -> AgentWorkspace:
        """Create an isolated workspace for an agent."""
        if agent_id in self._workspaces:
            return self._workspaces[agent_id]
        workspace = AgentWorkspace(self._base_dir, agent_id)
        await workspace.setup()
        self._workspaces[agent_id] = workspace
        return workspace

    def get_workspace(self, agent_id: str) -> AgentWorkspace | None:
        """Return an existing workspace or None."""
        return self._workspaces.get(agent_id)

    async def cleanup_all(self) -> None:
        """Remove all agent workspaces."""
        for ws in self._workspaces.values():
            await ws.cleanup()
        self._workspaces.clear()

    def verify_isolation(self, agent_id: str, target_path: Path) -> bool:
        """Verify an agent can only access its own workspace."""
        workspace = self._workspaces.get(agent_id)
        if workspace is None:
            return False
        return workspace.is_within_workspace(target_path)
