"""pgvector-backed vector store with asyncpg connection pooling.

Storage layout: a single ``keystone_chunks`` table keyed on ``chunk_id``
with a JSONB metadata column and an HNSW index on the embedding.

Operations exposed here: ``ensure_schema``, ``upsert_chunks``,
``search_similar`` (cosine distance), and ``delete_by_artifact_id``. Each
call acquires a connection from the pool; no connection state leaks
between callers.

Implementation is guarded against missing asyncpg/pgvector at import
time: the Protocol lets callers inject a test double, and the real
:class:`PgVectorStore` only imports the drivers lazily when a method is
invoked -- so ``pytest`` can collect the module in environments without
a database.

All asyncpg transport failures (pool creation, connection loss, driver
errors) are wrapped as :class:`VectorStoreError` so the
:class:`HybridSearcher` can honour its graceful-degradation contract
when PostgreSQL is unreachable.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from keystone.retrieval.parse_models import (
    Locator,
    ParseConfidence,
    ParseConfidenceTier,
    SourceFamily,
)
from keystone.retrieval.search.models import (
    ChunkMetadata,
    DocumentChunk,
    RetrievalResult,
    RetrievalSource,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# Canonical schema DDL. Kept as module-level strings so operators can
# reproduce the schema manually if they prefer hand-managed migrations.
_CHUNKS_TABLE_DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS keystone_chunks (
    chunk_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    metadata JSONB NOT NULL,
    embedding vector({dim}) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_INDEX_DDL_ARTIFACT = """
CREATE INDEX IF NOT EXISTS keystone_chunks_artifact_idx
    ON keystone_chunks (artifact_id);
"""

_INDEX_DDL_EMBEDDING = """
CREATE INDEX IF NOT EXISTS keystone_chunks_embedding_idx
    ON keystone_chunks
    USING hnsw (embedding vector_cosine_ops);
"""


class VectorStoreError(RuntimeError):
    """Raised when the vector store cannot satisfy a request."""


@runtime_checkable
class VectorStore(Protocol):
    """Swappable vector store surface.

    Every implementation must accept :class:`DocumentChunk` with a
    non-None embedding and must return :class:`RetrievalResult` with
    ``source=RetrievalSource.VECTOR`` from :meth:`search_similar`.
    """

    async def ensure_schema(self) -> None:
        """Create the schema + indexes if they are missing. Idempotent."""
        ...

    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> tuple[int, int]:
        """Insert or overwrite chunks. Returns ``(created, updated)`` counts."""
        ...

    async def search_similar(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Return the ``top_k`` closest chunks by cosine similarity."""
        ...

    async def delete_by_artifact_id(self, artifact_id: str) -> int:
        """Remove every chunk from an artifact. Returns delete count."""
        ...

    async def count(self) -> int:
        """Return the total number of chunks."""
        ...

    async def close(self) -> None:
        """Release pooled resources. Idempotent."""
        ...


# ---------------------------------------------------------------------------
# PostgreSQL + pgvector
# ---------------------------------------------------------------------------


class PgVectorStore:
    """PostgreSQL + pgvector vector store using asyncpg."""

    def __init__(
        self,
        *,
        dsn: str,
        dimension: int,
        pool_min_size: int = 1,
        pool_max_size: int = 10,
    ) -> None:
        if not dsn:
            raise VectorStoreError("PgVectorStore requires a non-empty dsn")
        if dimension < 2:
            raise ValueError("dimension must be >= 2")
        self._dsn = dsn
        self._dimension = dimension
        self._pool_min_size = pool_min_size
        self._pool_max_size = pool_max_size
        self._pool: Any = None
        self._asyncpg: Any = None

    @property
    def dimension(self) -> int:
        return self._dimension

    async def _get_pool(self) -> Any:
        if self._pool is not None:
            return self._pool
        try:
            import asyncpg
        except ImportError as exc:
            raise VectorStoreError(
                "asyncpg is not installed; install keystone[retrieval-search]"
            ) from exc
        self._asyncpg = asyncpg
        try:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=self._pool_min_size,
                max_size=self._pool_max_size,
            )
        except Exception as exc:
            # Wrap any asyncpg transport/connection failure so the hybrid
            # searcher's graceful-degradation path (catches VectorStoreError)
            # still fires when PostgreSQL is unreachable.
            raise VectorStoreError(f"failed to open pgvector pool: {exc}") from exc
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.execute(_CHUNKS_TABLE_DDL_TEMPLATE.format(dim=self._dimension))
                await conn.execute(_INDEX_DDL_ARTIFACT)
                await conn.execute(_INDEX_DDL_EMBEDDING)
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"ensure_schema failed: {exc}") from exc

    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> tuple[int, int]:
        if not chunks:
            return (0, 0)
        self._validate_chunk_batch(chunks)
        pool = await self._get_pool()
        created = 0
        updated = 0
        try:
            async with pool.acquire() as conn, conn.transaction():
                for chunk in chunks:
                    row = await conn.fetchrow(
                        "SELECT 1 FROM keystone_chunks WHERE chunk_id = $1",
                        chunk.chunk_id,
                    )
                    existed = row is not None
                    assert chunk.embedding is not None  # validated above
                    await conn.execute(
                        """
                            INSERT INTO keystone_chunks (
                                chunk_id, artifact_id, canonical_url, content_hash,
                                content, raw_text, token_count, metadata, embedding
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::vector)
                            ON CONFLICT (chunk_id) DO UPDATE SET
                                artifact_id = EXCLUDED.artifact_id,
                                canonical_url = EXCLUDED.canonical_url,
                                content_hash = EXCLUDED.content_hash,
                                content = EXCLUDED.content,
                                raw_text = EXCLUDED.raw_text,
                                token_count = EXCLUDED.token_count,
                                metadata = EXCLUDED.metadata,
                                embedding = EXCLUDED.embedding,
                                created_at = now()
                            """,
                        chunk.chunk_id,
                        chunk.metadata.artifact_id,
                        chunk.metadata.canonical_url,
                        chunk.metadata.content_hash,
                        chunk.content,
                        chunk.raw_text,
                        chunk.token_count,
                        json.dumps(_metadata_to_jsonable(chunk.metadata)),
                        _embedding_to_pgvector(chunk.embedding),
                    )
                    if existed:
                        updated += 1
                    else:
                        created += 1
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"upsert_chunks failed: {exc}") from exc
        return (created, updated)

    async def search_similar(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        self._validate_query_embedding(embedding)
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        pool = await self._get_pool()
        where_sql, where_args = _build_filters(filters or {})
        sql = f"""
        SELECT chunk_id, artifact_id, canonical_url, content_hash, content,
               raw_text, token_count, metadata, created_at,
               1 - (embedding <=> $1::vector) AS similarity
        FROM keystone_chunks
        {where_sql}
        ORDER BY embedding <=> $1::vector ASC
        LIMIT ${len(where_args) + 2}
        """
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    sql,
                    _embedding_to_pgvector(embedding),
                    *where_args,
                    top_k,
                )
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"search_similar failed: {exc}") from exc
        return [_row_to_result(row, rank) for rank, row in enumerate(rows, start=1)]

    async def delete_by_artifact_id(self, artifact_id: str) -> int:
        if not artifact_id:
            raise ValueError("artifact_id must be non-empty")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM keystone_chunks WHERE artifact_id = $1",
                    artifact_id,
                )
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"delete_by_artifact_id failed: {exc}") from exc
        # asyncpg returns 'DELETE <count>' as a status string
        try:
            return int(result.split()[-1])
        except (ValueError, AttributeError):
            return 0

    async def count(self) -> int:
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                value = await conn.fetchval("SELECT COUNT(*) FROM keystone_chunks")
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(f"count failed: {exc}") from exc
        return int(value or 0)

    async def close(self) -> None:
        if self._pool is not None:
            try:
                await self._pool.close()
            except Exception:
                # Closing a broken pool should never raise from our surface —
                # we're tearing down either way.
                logger.exception("error closing pgvector pool")
            self._pool = None

    # --- Validation helpers ---------------------------------------------

    def _validate_chunk_batch(self, chunks: Sequence[DocumentChunk]) -> None:
        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise VectorStoreError(
                    f"chunk[{i}] ({chunk.chunk_id}) has no embedding; call embedder before upsert"
                )
            if len(chunk.embedding) != self._dimension:
                raise VectorStoreError(
                    f"chunk[{i}] ({chunk.chunk_id}) has {len(chunk.embedding)}-dim "
                    f"embedding; store expects {self._dimension}"
                )

    def _validate_query_embedding(self, embedding: Sequence[float]) -> None:
        if len(embedding) != self._dimension:
            raise VectorStoreError(
                f"query embedding has {len(embedding)} dimensions; store expects {self._dimension}"
            )


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _embedding_to_pgvector(embedding: Sequence[float]) -> str:
    """Convert a Python sequence to pgvector text representation.

    We emit the textual form ``[0.1, 0.2, ...]`` so asyncpg does not need
    to be told about the ``vector`` type (which requires an explicit
    codec registration). The cast ``$N::vector`` in each query tells
    PostgreSQL to parse the text.
    """

    return "[" + ",".join(f"{float(v):.8f}" for v in embedding) + "]"


def _metadata_to_jsonable(metadata: ChunkMetadata) -> dict[str, Any]:
    dump = metadata.model_dump(mode="json")
    return dump


def _build_filters(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    """Translate a small filter dict into ``WHERE`` SQL + positional args.

    Unknown filter keys are ignored so callers can pass a shared filter
    bag across retrievers. Supported inclusion filters: ``artifact_id``
    and ``source_family`` (single value or list). Supported exclusion
    filter: ``exclude_engagement_id`` (single string; chunks with a
    matching ``metadata->>'engagement_id'`` are dropped, NULL values
    always pass).
    """

    clauses: list[str] = []
    args: list[Any] = []
    supported: dict[str, str] = {
        "artifact_id": "artifact_id",
        "source_family": "metadata ->> 'source_family'",
    }
    next_index = 2
    for key, column in supported.items():
        if key not in filters:
            continue
        raw = filters[key]
        values = raw if isinstance(raw, list | tuple) else [raw]
        if not values:
            continue
        placeholders = ",".join(f"${next_index + i}" for i in range(len(values)))
        clauses.append(f"{column} IN ({placeholders})")
        args.extend(list(values))
        next_index += len(values)

    exclude_engagement = filters.get("exclude_engagement_id")
    if exclude_engagement is not None:
        clauses.append(
            f"(metadata ->> 'engagement_id' IS NULL "
            f"OR metadata ->> 'engagement_id' <> ${next_index})"
        )
        args.append(exclude_engagement)
        next_index += 1

    where_sql = "" if not clauses else "WHERE " + " AND ".join(clauses)
    return where_sql, args


def _row_to_result(row: Any, rank: int) -> RetrievalResult:
    metadata_raw = row["metadata"]
    metadata_dict = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
    metadata = _metadata_from_dict(metadata_dict)
    chunk = DocumentChunk(
        chunk_id=row["chunk_id"],
        content=row["content"],
        raw_text=row["raw_text"],
        metadata=metadata,
        token_count=int(row["token_count"]),
        created_at=row["created_at"],
        embedding=None,  # don't ship the vector back to callers
    )
    similarity = float(row["similarity"])
    return RetrievalResult(
        chunk=chunk,
        score=similarity,
        vector_score=similarity,
        source=RetrievalSource.VECTOR,
        rank=rank,
    )


def _metadata_from_dict(data: dict[str, Any]) -> ChunkMetadata:
    """Rehydrate ChunkMetadata from the JSON-serialised form."""

    locator_payload = data["locator"]
    locator = Locator(
        section_path=list(locator_payload.get("section_path") or []),
        paragraph_index=int(locator_payload["paragraph_index"]),
        page_number=locator_payload.get("page_number"),
        char_start=locator_payload.get("char_start"),
        char_end=locator_payload.get("char_end"),
    )
    confidence_payload = data["parse_confidence"]
    parse_confidence = ParseConfidence(
        score=float(confidence_payload["score"]),
        tier=ParseConfidenceTier(confidence_payload["tier"]),
        reasons=list(confidence_payload.get("reasons") or []),
    )
    return ChunkMetadata(
        artifact_id=data["artifact_id"],
        canonical_url=data["canonical_url"],
        content_hash=data["content_hash"],
        source_family=SourceFamily(data["source_family"]),
        locator=locator,
        parse_confidence=parse_confidence,
        title=data.get("title"),
        fetched_at=data.get("fetched_at"),
        record_ids=list(data.get("record_ids") or []),
        engagement_id=data.get("engagement_id"),
    )


# ---------------------------------------------------------------------------
# In-memory test double
# ---------------------------------------------------------------------------


class InMemoryVectorStore:
    """In-memory vector store for tests.

    Brute-force cosine similarity over a Python dict. Not suitable for
    anything other than exercising the RetrievalService pipeline, but
    it keeps unit tests independent of the database and matches the
    :class:`VectorStore` Protocol exactly.
    """

    def __init__(self, *, dimension: int = 16) -> None:
        if dimension < 2:
            raise ValueError("dimension must be >= 2")
        self._dimension = dimension
        self._chunks: dict[str, DocumentChunk] = {}

    @property
    def dimension(self) -> int:
        return self._dimension

    async def ensure_schema(self) -> None:  # pragma: no cover - no-op
        return None

    async def upsert_chunks(self, chunks: Sequence[DocumentChunk]) -> tuple[int, int]:
        created = 0
        updated = 0
        for chunk in chunks:
            if chunk.embedding is None:
                raise VectorStoreError(f"chunk {chunk.chunk_id} missing embedding")
            if len(chunk.embedding) != self._dimension:
                raise VectorStoreError(
                    f"chunk {chunk.chunk_id} embedding has {len(chunk.embedding)} "
                    f"dims; store expects {self._dimension}"
                )
            if chunk.chunk_id in self._chunks:
                updated += 1
            else:
                created += 1
            self._chunks[chunk.chunk_id] = chunk
        return (created, updated)

    async def search_similar(
        self,
        embedding: Sequence[float],
        *,
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        if len(embedding) != self._dimension:
            raise VectorStoreError(f"query has {len(embedding)} dims; expects {self._dimension}")
        filters = filters or {}
        candidates: list[tuple[float, DocumentChunk]] = []
        for chunk in self._chunks.values():
            if not _matches_filters(chunk, filters):
                continue
            score = _cosine(embedding, chunk.embedding or [])
            candidates.append((score, chunk))
        candidates.sort(key=lambda item: item[0], reverse=True)
        results: list[RetrievalResult] = []
        for rank, (score, chunk) in enumerate(candidates[:top_k], start=1):
            redacted = chunk.model_copy(update={"embedding": None})
            results.append(
                RetrievalResult(
                    chunk=redacted,
                    score=score,
                    vector_score=score,
                    source=RetrievalSource.VECTOR,
                    rank=rank,
                )
            )
        return results

    async def delete_by_artifact_id(self, artifact_id: str) -> int:
        removed = [
            chunk_id
            for chunk_id, chunk in self._chunks.items()
            if chunk.metadata.artifact_id == artifact_id
        ]
        for chunk_id in removed:
            del self._chunks[chunk_id]
        return len(removed)

    async def count(self) -> int:
        return len(self._chunks)

    async def close(self) -> None:  # pragma: no cover - no-op
        return None


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    import math

    num = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return num / (na * nb)


def _matches_filters(chunk: DocumentChunk, filters: dict[str, Any]) -> bool:
    for key, raw in filters.items():
        if key == "exclude_engagement_id":
            # Exclusion filter: drop chunks whose engagement_id matches
            # the scalar value. Chunks with engagement_id=None
            # (institutional memory) always remain visible.
            if chunk.metadata.engagement_id is not None and chunk.metadata.engagement_id == raw:
                return False
            continue
        values = raw if isinstance(raw, list | tuple) else [raw]
        if not values:
            continue
        if key == "artifact_id" and chunk.metadata.artifact_id not in values:
            return False
        if key == "source_family" and chunk.metadata.source_family.value not in {
            v.value if hasattr(v, "value") else v for v in values
        }:
            return False
    return True
