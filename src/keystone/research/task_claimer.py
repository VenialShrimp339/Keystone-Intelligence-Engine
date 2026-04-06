"""Lock-file-based task claiming for concurrent research agents.

Agents claim tasks before executing them. Claims are advisory file
locks -- one lock file per task in a shared directory. The async
mutex serializes concurrent claim attempts within a single process.
"""

from __future__ import annotations

import asyncio
from pathlib import Path


class TaskClaimError(Exception):
    """Raised when a task cannot be claimed."""

    def __init__(self, task_id: str, reason: str) -> None:
        self.task_id = task_id
        self.reason = reason
        super().__init__(f"Cannot claim task '{task_id}': {reason}")


class TaskClaimer:
    """Lock-file-based task claiming for concurrent agents."""

    def __init__(self, lock_dir: Path) -> None:
        self._lock_dir = lock_dir
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        self._mutex = asyncio.Lock()

    def _lock_path(self, task_id: str) -> Path:
        return self._lock_dir / f"{task_id}.lock"

    async def claim(self, task_id: str, agent_id: str) -> bool:
        """Attempt to claim a task. Returns True if successfully claimed."""
        async with self._mutex:
            lock_file = self._lock_path(task_id)
            if lock_file.exists():
                existing = lock_file.read_text().strip()
                if existing == agent_id:
                    return True  # Re-claim by same agent
                return False
            lock_file.write_text(agent_id)
            return True

    async def release(self, task_id: str, agent_id: str) -> bool:
        """Release a claimed task. Returns True if released."""
        async with self._mutex:
            lock_file = self._lock_path(task_id)
            if not lock_file.exists():
                return False
            if lock_file.read_text().strip() != agent_id:
                return False
            lock_file.unlink()
            return True

    async def get_owner(self, task_id: str) -> str | None:
        """Return the agent_id that owns a task, or None."""
        lock_file = self._lock_path(task_id)
        if lock_file.exists():
            return lock_file.read_text().strip()
        return None

    async def is_claimed(self, task_id: str) -> bool:
        """Check if a task is currently claimed."""
        return self._lock_path(task_id).exists()

    async def release_all(self, agent_id: str) -> list[str]:
        """Release all tasks claimed by an agent. Returns released task IDs."""
        released: list[str] = []
        async with self._mutex:
            for lock_file in self._lock_dir.glob("*.lock"):
                if lock_file.read_text().strip() == agent_id:
                    task_id = lock_file.stem
                    lock_file.unlink()
                    released.append(task_id)
        return released
