"""Shared fixtures for retrieval/search tests."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from keystone.retrieval.parse_models import (
    Coverage,
    CoverageStatus,
    EvidencePrepRecord,
    Locator,
    ParserIdentity,
    PassageKind,
    SourceFamily,
    confidence,
)

if TYPE_CHECKING:
    from collections.abc import Callable

PG_DSN_ENV = "KEYSTONE_TEST_DATABASE_URL"
PG_DEFAULT_DSN = "postgresql://localhost/keystone"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def parser_identity() -> ParserIdentity:
    return ParserIdentity(name="keystone.test.v1", version="1.0.0")


@pytest.fixture
def make_record(parser_identity: ParserIdentity) -> Callable[..., EvidencePrepRecord]:
    def _build(
        *,
        artifact_id: str = "art-001",
        record_id: str | None = None,
        text: str = "A short passage.",
        section_path: list[str] | None = None,
        paragraph_index: int = 0,
        page_number: int | None = None,
        source_family: SourceFamily = SourceFamily.ARTICLE,
        title: str | None = "Test Document",
        parse_score: float = 0.9,
    ) -> EvidencePrepRecord:
        if record_id is None:
            record_id = f"ev:{artifact_id}-{paragraph_index}"
        locator = Locator(
            section_path=section_path or [],
            paragraph_index=paragraph_index,
            page_number=page_number,
        )
        return EvidencePrepRecord(
            record_id=record_id,
            artifact_id=artifact_id,
            canonical_url="https://example.com/doc",
            content_hash=_hash(text + artifact_id),
            coverage=Coverage(status=CoverageStatus.COMPLETE),
            source_family=source_family,
            parser=parser_identity,
            locator=locator,
            passage_kind=PassageKind.PARAGRAPH,
            text=text,
            parse_confidence=confidence(parse_score),
            fetched_at=datetime(2026, 4, 17, 12, 0, tzinfo=UTC),
            title=title,
        )

    return _build


@pytest.fixture
def pg_dsn() -> str | None:
    return os.environ.get(PG_DSN_ENV, PG_DEFAULT_DSN)


async def _check_pg_available(dsn: str) -> bool:
    try:
        import asyncpg
    except ImportError:
        return False
    try:
        conn = await asyncpg.connect(dsn, timeout=2.0)
    except Exception:
        return False
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()
    return True


@pytest.fixture
async def live_pg_dsn(pg_dsn: str) -> str:
    import pytest as _pytest

    available = await _check_pg_available(pg_dsn)
    if not available:
        _pytest.skip(f"no PostgreSQL available at {pg_dsn}")
    return pg_dsn
