"""Aiosqlite-backed persistence for evaluation observations.

Stores per-task evaluation outcomes so future runs can detect recurring
failure and success patterns.  This is the data-accumulation layer of
the Observation Library (GAP-05 first slice).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS observations (
    observation_id   TEXT PRIMARY KEY,
    client_id        TEXT NOT NULL,
    engagement_id    TEXT NOT NULL,
    engagement_type  TEXT NOT NULL,
    task_id          TEXT NOT NULL,
    type             TEXT NOT NULL CHECK (type IN ('rejection', 'success')),
    category         INTEGER NOT NULL CHECK (category IN (1, 2, 3)),
    dimension        TEXT NOT NULL,
    composite_score  REAL NOT NULL,
    dimension_scores TEXT NOT NULL,
    governance_flags TEXT NOT NULL,
    recorded_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obs_client_type
    ON observations(client_id, type);
CREATE INDEX IF NOT EXISTS idx_obs_dim
    ON observations(client_id, dimension, type);
CREATE INDEX IF NOT EXISTS idx_obs_etype
    ON observations(client_id, engagement_type);
"""


class ObservationRow:
    """Lightweight read-only projection of a stored observation."""

    __slots__ = (
        "observation_id",
        "client_id",
        "engagement_id",
        "engagement_type",
        "task_id",
        "type",
        "category",
        "dimension",
        "composite_score",
        "dimension_scores",
        "governance_flags",
        "recorded_at",
    )

    def __init__(self, row: aiosqlite.Row | tuple) -> None:
        (
            self.observation_id,
            self.client_id,
            self.engagement_id,
            self.engagement_type,
            self.task_id,
            self.type,
            self.category,
            self.dimension,
            self.composite_score,
            dimension_scores_json,
            governance_flags_json,
            self.recorded_at,
        ) = row
        self.dimension_scores: dict[str, float] = json.loads(dimension_scores_json)
        self.governance_flags: list[str] = json.loads(governance_flags_json)


class ObservationStore:
    """Async SQLite store for evaluation observations."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Open the database and ensure the schema exists."""
        self._db = await aiosqlite.connect(self._db_path)
        for statement in _SCHEMA.split(";"):
            statement = statement.strip()
            if statement:
                await self._db.execute(statement)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    def _conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("ObservationStore not initialized — call initialize() first")
        return self._db

    async def record(
        self,
        *,
        observation_id: str,
        client_id: str,
        engagement_id: str,
        engagement_type: str,
        task_id: str,
        obs_type: str,
        category: int,
        dimension: str,
        composite_score: float,
        dimension_scores: dict[str, float],
        governance_flags: list[str],
        recorded_at: datetime | None = None,
    ) -> None:
        """Insert a single observation row."""
        ts = (recorded_at or datetime.now(UTC)).isoformat()
        await self._conn().execute(
            "INSERT OR REPLACE INTO observations "
            "(observation_id, client_id, engagement_id, engagement_type, "
            "task_id, type, category, dimension, composite_score, "
            "dimension_scores, governance_flags, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                observation_id,
                client_id,
                engagement_id,
                engagement_type,
                task_id,
                obs_type,
                category,
                dimension,
                composite_score,
                json.dumps(dimension_scores),
                json.dumps(governance_flags),
                ts,
            ),
        )
        await self._conn().commit()

    async def query_by_client(
        self,
        client_id: str,
        *,
        obs_type: str | None = None,
        limit: int = 100,
    ) -> Sequence[ObservationRow]:
        """Return observations for a client, optionally filtered by type."""
        if obs_type is not None:
            cursor = await self._conn().execute(
                "SELECT * FROM observations WHERE client_id = ? AND type = ? "
                "ORDER BY recorded_at DESC LIMIT ?",
                (client_id, obs_type, limit),
            )
        else:
            cursor = await self._conn().execute(
                "SELECT * FROM observations WHERE client_id = ? ORDER BY recorded_at DESC LIMIT ?",
                (client_id, limit),
            )
        rows = await cursor.fetchall()
        return [ObservationRow(r) for r in rows]

    async def query_by_dimension(
        self,
        client_id: str,
        dimension: str,
        *,
        obs_type: str | None = None,
        limit: int = 50,
    ) -> Sequence[ObservationRow]:
        """Return observations for a client + dimension, optionally filtered."""
        if obs_type is not None:
            cursor = await self._conn().execute(
                "SELECT * FROM observations "
                "WHERE client_id = ? AND dimension = ? AND type = ? "
                "ORDER BY recorded_at DESC LIMIT ?",
                (client_id, dimension, obs_type, limit),
            )
        else:
            cursor = await self._conn().execute(
                "SELECT * FROM observations "
                "WHERE client_id = ? AND dimension = ? "
                "ORDER BY recorded_at DESC LIMIT ?",
                (client_id, dimension, limit),
            )
        rows = await cursor.fetchall()
        return [ObservationRow(r) for r in rows]

    async def count(self, client_id: str | None = None) -> int:
        """Count observations, optionally scoped to a client."""
        if client_id is not None:
            cursor = await self._conn().execute(
                "SELECT COUNT(*) FROM observations WHERE client_id = ?",
                (client_id,),
            )
        else:
            cursor = await self._conn().execute("SELECT COUNT(*) FROM observations")
        row = await cursor.fetchone()
        return row[0] if row else 0
