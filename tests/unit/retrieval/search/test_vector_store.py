"""Unit + live-DB tests for the vector store.

The live-DB tests run only when a PostgreSQL instance is reachable at
``KEYSTONE_TEST_DATABASE_URL`` (falls back to
``postgresql://localhost/keystone``). In CI that should point at a
disposable database with pgvector installed.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

import pytest

from keystone.retrieval.parse_models import SourceFamily

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import InMemoryEmbeddingClient
from keystone.retrieval.search.models import RetrievalSource
from keystone.retrieval.search.vector_store import (
    InMemoryVectorStore,
    PgVectorStore,
    VectorStoreError,
    _build_filters,
    _embedding_to_pgvector,
)


async def _make_chunks(records: list[EvidencePrepRecord], *, dimension: int):
    chunker = SemanticChunker(
        target_tokens=80,
        max_tokens=120,
        overlap_tokens=16,
        add_contextual_preamble=False,
    )
    embedder = InMemoryEmbeddingClient(dimension=dimension)
    chunks = chunker.chunk(records, engagement_id=None)
    vectors = await embedder.embed([c.content for c in chunks])
    return [c.with_embedding(v) for c, v in zip(chunks, vectors, strict=True)]


# ---------------------------------------------------------------------------
# InMemoryVectorStore
# ---------------------------------------------------------------------------


class TestInMemoryVectorStore:
    async def test_upsert_and_search(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        records = [
            make_record(
                artifact_id="art-A",
                paragraph_index=0,
                text="Microsoft cloud growth is strong.",
            ),
            make_record(
                artifact_id="art-B",
                paragraph_index=0,
                text="Apple's iPhone sales fell.",
            ),
        ]
        store = InMemoryVectorStore(dimension=32)
        embedded = await _make_chunks(records, dimension=32)
        created, updated = await store.upsert_chunks(embedded)
        assert created == 2
        assert updated == 0

        embedder = InMemoryEmbeddingClient(dimension=32)
        query_vec = await embedder.embed_query("Microsoft cloud growth is strong.")
        results = await store.search_similar(query_vec, top_k=2)
        assert results[0].chunk.metadata.artifact_id == "art-A"
        assert results[0].source is RetrievalSource.VECTOR

    async def test_upsert_rejects_missing_embedding(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        chunker = SemanticChunker(add_contextual_preamble=False)
        chunks = chunker.chunk([make_record(text="hi there")], engagement_id=None)
        store = InMemoryVectorStore(dimension=16)
        with pytest.raises(VectorStoreError):
            await store.upsert_chunks(chunks)

    async def test_dimension_mismatch_rejected(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        store = InMemoryVectorStore(dimension=16)
        chunks = await _make_chunks([make_record(text="hi")], dimension=32)
        with pytest.raises(VectorStoreError):
            await store.upsert_chunks(chunks)

    async def test_delete_by_artifact(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        records = [
            make_record(artifact_id="art-A", text="alpha"),
            make_record(artifact_id="art-B", text="beta"),
        ]
        store = InMemoryVectorStore(dimension=16)
        await store.upsert_chunks(await _make_chunks(records, dimension=16))
        removed = await store.delete_by_artifact_id("art-A")
        assert removed == 1
        assert await store.count() == 1

    async def test_upsert_updates_existing(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        store = InMemoryVectorStore(dimension=16)
        chunks_v1 = await _make_chunks(
            [make_record(artifact_id="art-A", paragraph_index=0, text="old")],
            dimension=16,
        )
        await store.upsert_chunks(chunks_v1)
        chunks_v2 = await _make_chunks(
            [make_record(artifact_id="art-A", paragraph_index=0, text="new")],
            dimension=16,
        )
        created, updated = await store.upsert_chunks(chunks_v2)
        assert created == 0
        assert updated == 1

    async def test_filter_by_artifact_id(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        store = InMemoryVectorStore(dimension=16)
        chunks = await _make_chunks(
            [
                make_record(artifact_id="art-A", text="alpha"),
                make_record(artifact_id="art-B", text="beta"),
            ],
            dimension=16,
        )
        await store.upsert_chunks(chunks)
        embedder = InMemoryEmbeddingClient(dimension=16)
        query_vec = await embedder.embed_query("anything")
        results = await store.search_similar(query_vec, top_k=10, filters={"artifact_id": "art-B"})
        assert all(r.chunk.metadata.artifact_id == "art-B" for r in results)

    async def test_filter_by_source_family(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        store = InMemoryVectorStore(dimension=16)
        records = [
            make_record(
                artifact_id="art-A",
                text="article prose",
                source_family=SourceFamily.ARTICLE,
            ),
            make_record(
                artifact_id="art-B",
                text="pdf prose",
                source_family=SourceFamily.PDF,
            ),
        ]
        await store.upsert_chunks(await _make_chunks(records, dimension=16))
        embedder = InMemoryEmbeddingClient(dimension=16)
        query_vec = await embedder.embed_query("anything")
        results = await store.search_similar(
            query_vec, top_k=5, filters={"source_family": SourceFamily.PDF}
        )
        assert all(r.chunk.metadata.source_family is SourceFamily.PDF for r in results)

    async def test_invalid_query_dim(self) -> None:
        store = InMemoryVectorStore(dimension=16)
        with pytest.raises(VectorStoreError):
            await store.search_similar([0.1, 0.2, 0.3], top_k=1)

    async def test_constructor_rejects_tiny_dim(self) -> None:
        with pytest.raises(ValueError):
            InMemoryVectorStore(dimension=1)


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


class TestEmbeddingToPgvector:
    def test_formats_floats(self) -> None:
        formatted = _embedding_to_pgvector([0.1, -0.2, 3.0])
        assert formatted.startswith("[")
        assert formatted.endswith("]")
        assert formatted.count(",") == 2


class TestBuildFilters:
    def test_empty(self) -> None:
        where_sql, args = _build_filters({})
        assert where_sql == ""
        assert args == []

    def test_single_artifact_id(self) -> None:
        where_sql, args = _build_filters({"artifact_id": "art-A"})
        assert "artifact_id IN ($2)" in where_sql
        assert args == ["art-A"]

    def test_artifact_id_list_and_source_family(self) -> None:
        where_sql, args = _build_filters(
            {
                "artifact_id": ["art-A", "art-B"],
                "source_family": "pdf",
            }
        )
        assert "artifact_id IN ($2,$3)" in where_sql
        assert "metadata ->> 'source_family' IN ($4)" in where_sql
        assert args == ["art-A", "art-B", "pdf"]


# ---------------------------------------------------------------------------
# Live pgvector tests (skip gracefully when no DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPgVectorStoreLive:
    async def test_ingest_and_search_roundtrip(
        self,
        live_pg_dsn: str,
        make_record: Callable[..., EvidencePrepRecord],
    ) -> None:
        dimension = 32
        artifact_id = f"pg-test-{uuid.uuid4().hex[:8]}"
        records = [
            make_record(
                artifact_id=artifact_id,
                paragraph_index=0,
                text=" ".join(["Microsoft"] + [f"word{i}" for i in range(100)]),
            ),
            make_record(
                artifact_id=artifact_id,
                paragraph_index=1,
                text=" ".join(["Apple"] + [f"token{i}" for i in range(100)]),
            ),
        ]
        embedded = await _make_chunks(records, dimension=dimension)
        assert len(embedded) == 2
        store = PgVectorStore(dsn=live_pg_dsn, dimension=dimension)
        try:
            await store.ensure_schema()
            # clean slate for this artifact
            await store.delete_by_artifact_id(artifact_id)
            created, updated = await store.upsert_chunks(embedded)
            assert created == 2
            assert updated == 0

            # Idempotent re-ingest counts as update
            created2, updated2 = await store.upsert_chunks(embedded)
            assert created2 == 0
            assert updated2 == 2

            embedder = InMemoryEmbeddingClient(dimension=dimension)
            query_vec = await embedder.embed_query("Microsoft cloud growth is strong.")
            results = await store.search_similar(
                query_vec, top_k=2, filters={"artifact_id": artifact_id}
            )
            assert len(results) == 2
            top = results[0]
            assert top.chunk.metadata.artifact_id == artifact_id
            assert top.vector_score is not None
            assert top.chunk.embedding is None

            removed = await store.delete_by_artifact_id(artifact_id)
            assert removed == 2
        finally:
            await store.close()

    async def test_close_is_idempotent(self, live_pg_dsn: str) -> None:
        store = PgVectorStore(dsn=live_pg_dsn, dimension=16)
        await store.close()
        await store.close()

    async def test_ensure_schema_is_idempotent(self, live_pg_dsn: str) -> None:
        store = PgVectorStore(dsn=live_pg_dsn, dimension=16)
        try:
            await asyncio.gather(store.ensure_schema(), store.ensure_schema())
        finally:
            await store.close()
