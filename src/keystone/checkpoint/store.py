"""Aiosqlite-backed persistence for pipeline checkpoint data.

Stores serialized stage-boundary snapshots so a crashed or paused
pipeline run can resume from the last completed stage instead of
restarting from L0.  Follows the identical pattern as
``ObservationStore``: ``__init__(db_path)``, ``async initialize()``,
``async close()``, ``_conn()`` guard.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS checkpoints (
    engagement_id  TEXT    NOT NULL,
    stage_name     TEXT    NOT NULL,
    written_at     TEXT    NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    payload        TEXT    NOT NULL,
    PRIMARY KEY (engagement_id, stage_name)
);
CREATE INDEX IF NOT EXISTS idx_chk_eid
    ON checkpoints(engagement_id);
CREATE INDEX IF NOT EXISTS idx_chk_written
    ON checkpoints(written_at);
"""

STAGE_ORDER = [
    "POST_SPEC",
    "POST_L1_CITPROC",
    "POST_DELIBERATION",
    "POST_STRUCTURING",
    "POST_EVALUATION",
]


class CheckpointVersionError(Exception):
    """Raised when a checkpoint was written by a newer code version."""


class CheckpointStore:
    """Async SQLite store for pipeline checkpoint data."""

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
            raise RuntimeError("CheckpointStore not initialized — call initialize() first")
        return self._db

    async def save(
        self,
        engagement_id: str,
        stage_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Write a checkpoint. INSERT OR REPLACE. Fire-and-log on failure."""
        try:
            ts = datetime.now(UTC).isoformat()
            await self._conn().execute(
                "INSERT OR REPLACE INTO checkpoints "
                "(engagement_id, stage_name, written_at, schema_version, payload) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    engagement_id,
                    stage_name,
                    ts,
                    CURRENT_SCHEMA_VERSION,
                    json.dumps(payload),
                ),
            )
            await self._conn().commit()
        except Exception:
            logger.warning(
                "Checkpoint write failed for %s/%s — run continues without checkpoint",
                engagement_id,
                stage_name,
                exc_info=True,
            )

    async def load(
        self,
        engagement_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Load all checkpoints for an engagement.

        Returns ``{stage_name: payload}`` ordered by stage sequence.
        Raises :class:`CheckpointVersionError` if any checkpoint was
        written by a newer schema version.
        """
        cursor = await self._conn().execute(
            "SELECT stage_name, schema_version, payload FROM checkpoints WHERE engagement_id = ?",
            (engagement_id,),
        )
        rows = await cursor.fetchall()

        result: dict[str, dict[str, Any]] = {}
        for stage_name, schema_version, payload_json in rows:
            if schema_version > CURRENT_SCHEMA_VERSION:
                raise CheckpointVersionError(
                    f"Checkpoint {engagement_id}/{stage_name} has schema_version "
                    f"{schema_version}, but this code only supports up to "
                    f"{CURRENT_SCHEMA_VERSION}"
                )
            result[stage_name] = json.loads(payload_json)

        ordered: dict[str, dict[str, Any]] = {}
        for stage in STAGE_ORDER:
            if stage in result:
                ordered[stage] = result[stage]
        return ordered

    async def load_stage(
        self,
        engagement_id: str,
        stage_name: str,
    ) -> dict[str, Any] | None:
        """Load a single stage's checkpoint, or None if not found."""
        cursor = await self._conn().execute(
            "SELECT schema_version, payload FROM checkpoints "
            "WHERE engagement_id = ? AND stage_name = ?",
            (engagement_id, stage_name),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        schema_version, payload_json = row
        if schema_version > CURRENT_SCHEMA_VERSION:
            raise CheckpointVersionError(
                f"Checkpoint {engagement_id}/{stage_name} has schema_version "
                f"{schema_version}, but this code only supports up to "
                f"{CURRENT_SCHEMA_VERSION}"
            )
        return json.loads(payload_json)

    async def is_resumable(self, engagement_id: str) -> bool:
        """True if at least one checkpoint exists for this engagement."""
        cursor = await self._conn().execute(
            "SELECT COUNT(*) FROM checkpoints WHERE engagement_id = ?",
            (engagement_id,),
        )
        row = await cursor.fetchone()
        return row is not None and row[0] > 0

    async def delete(self, engagement_id: str) -> None:
        """Delete all checkpoints for an engagement."""
        await self._conn().execute(
            "DELETE FROM checkpoints WHERE engagement_id = ?",
            (engagement_id,),
        )
        await self._conn().commit()

    async def cleanup_expired(self, max_age_days: int = 7) -> int:
        """Delete checkpoints older than max_age_days. Returns count deleted."""
        cutoff = datetime.now(UTC)
        from datetime import timedelta

        cutoff = (cutoff - timedelta(days=max_age_days)).isoformat()
        cursor = await self._conn().execute(
            "DELETE FROM checkpoints WHERE written_at < ?",
            (cutoff,),
        )
        await self._conn().commit()
        return cursor.rowcount
