"""Unit tests for hybrid search (RRF fusion over vector + BM25)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import (
    EmbeddingError,
    InMemoryEmbeddingClient,
)
from keystone.retrieval.search.hybrid_search import (
    DEFAULT_RRF_K,
    HybridSearchConfig,
    HybridSearcher,
)
from keystone.retrieval.search.models import RetrievalSource, SearchQuery
from keystone.retrieval.search.vector_store import (
    InMemoryVectorStore,
    PgVectorStore,
    VectorStoreError,
)


async def _ingest_corpus(
    records: list[EvidencePrepRecord],
    *,
    dimension: int = 32,
) -> tuple[InMemoryVectorStore, InMemoryBM25Index, InMemoryEmbeddingClient]:
    embedder = InMemoryEmbeddingClient(dimension=dimension)
    chunker = SemanticChunker(
        target_tokens=80,
        max_tokens=120,
        overlap_tokens=16,
        add_contextual_preamble=False,
    )
    chunks = chunker.chunk(records, engagement_id=None)
    vectors = await embedder.embed([c.content for c in chunks])
    embedded = [c.with_embedding(v) for c, v in zip(chunks, vectors, strict=True)]

    store = InMemoryVectorStore(dimension=dimension)
    await store.upsert_chunks(embedded)

    index = InMemoryBM25Index()
    await index.index_chunks(embedded)
    return store, index, embedder


class TestHybridSearchConfig:
    def test_negative_weights_rejected(self) -> None:
        with pytest.raises(ValueError):
            HybridSearchConfig(vector_weight=-1.0)

    def test_both_zero_rejected(self) -> None:
        with pytest.raises(ValueError):
            HybridSearchConfig(vector_weight=0.0, bm25_weight=0.0)

    def test_rrf_k_positive(self) -> None:
        with pytest.raises(ValueError):
            HybridSearchConfig(rrf_k=0)

    def test_default_k_is_60(self) -> None:
        assert DEFAULT_RRF_K == 60


class TestHybridSearcher:
    async def test_returns_fused_results(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"Padding prose {i} {' '.join(f'corpus{j}' for j in range(30))}",
            )
            for i in range(5)
        ]
        records += [
            make_record(
                artifact_id="art-iphone",
                text=(
                    "Apple iPhone sales fell in the latest quarter as "
                    "consumers held onto older models longer."
                ),
            ),
            make_record(
                artifact_id="art-cloud",
                text=("Microsoft cloud revenue grew year over year driven by Azure AI services."),
            ),
        ]
        store, index, embedder = await _ingest_corpus(records)
        searcher = HybridSearcher(embedder=embedder, vector_store=store, bm25_index=index)
        query = SearchQuery(text="iPhone sales", top_k=5, candidate_pool=20)
        results = await searcher.search(query)
        assert results
        top = results[0]
        assert top.source is RetrievalSource.HYBRID
        assert top.rrf_score is not None
        assert top.chunk.metadata.artifact_id == "art-iphone"

    async def test_vector_weight_zero_still_returns_bm25(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"corpus prose {i} {' '.join(f'w{j}' for j in range(30))}",
            )
            for i in range(5)
        ]
        records.append(
            make_record(
                artifact_id="art-target",
                text="The unique keyword zelkova appeared in this passage.",
            )
        )
        store, index, embedder = await _ingest_corpus(records)
        searcher = HybridSearcher(
            embedder=embedder,
            vector_store=store,
            bm25_index=index,
            config=HybridSearchConfig(vector_weight=0.0, bm25_weight=1.0),
        )
        results = await searcher.search(SearchQuery(text="zelkova", top_k=5, candidate_pool=10))
        assert results
        assert results[0].chunk.metadata.artifact_id == "art-target"

    async def test_bm25_weight_zero_returns_vector_only(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding prose {i} {' '.join(f'w{j}' for j in range(30))}",
            )
            for i in range(5)
        ]
        store, index, embedder = await _ingest_corpus(records)
        searcher = HybridSearcher(
            embedder=embedder,
            vector_store=store,
            bm25_index=index,
            config=HybridSearchConfig(vector_weight=1.0, bm25_weight=0.0),
        )
        results = await searcher.search(
            SearchQuery(text="padding prose", top_k=3, candidate_pool=10)
        )
        assert results
        # All results fused from vector only (BM25 zero-weighted)
        for result in results:
            assert result.source is RetrievalSource.HYBRID
            # bm25_score may still be None since BM25 path was skipped
            assert result.vector_score is not None

    async def test_embedding_failure_drops_vector_path(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        class BrokenEmbedder:
            model = "broken"
            dimension = 32

            async def embed(self, texts: Any) -> Any:
                raise EmbeddingError("provider down")

            async def embed_query(self, text: str) -> list[float]:
                raise EmbeddingError("provider down")

        records = [
            make_record(
                artifact_id="art-T",
                text="The unique keyword zelkova appeared in this passage.",
            )
        ]
        store, index, _ = await _ingest_corpus(records)
        searcher = HybridSearcher(
            embedder=BrokenEmbedder(),
            vector_store=store,
            bm25_index=index,
        )
        # BM25 alone should still return something (single-doc corpora give 0
        # scores so we also prime with padding).
        padding_records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} {' '.join(f'w{j}' for j in range(30))}",
            )
            for i in range(5)
        ]
        store2, index2, embedder2 = await _ingest_corpus(records + padding_records)
        searcher = HybridSearcher(
            embedder=BrokenEmbedder(),
            vector_store=store2,
            bm25_index=index2,
        )
        results = await searcher.search(SearchQuery(text="zelkova", top_k=3, candidate_pool=10))
        assert results
        assert results[0].chunk.metadata.artifact_id == "art-T"

    async def test_vector_store_failure_drops_vector_path(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        class BrokenStore:
            dimension = 32

            async def ensure_schema(self) -> None:
                return None

            async def upsert_chunks(self, chunks: Any) -> tuple[int, int]:
                return (0, 0)

            async def search_similar(
                self, embedding: Any, *, top_k: int, filters: Any = None
            ) -> list[Any]:
                raise VectorStoreError("store down")

            async def delete_by_artifact_id(self, artifact_id: str) -> int:
                return 0

            async def count(self) -> int:
                return 0

            async def close(self) -> None:
                return None

        embedder = InMemoryEmbeddingClient(dimension=32)
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} {' '.join(f'w{j}' for j in range(30))}",
            )
            for i in range(4)
        ]
        records.append(
            make_record(
                artifact_id="art-T",
                text="The unique keyword zelkova appeared in this passage.",
            )
        )
        index = InMemoryBM25Index()
        chunker = SemanticChunker(
            target_tokens=80,
            max_tokens=120,
            overlap_tokens=16,
            add_contextual_preamble=False,
        )
        chunks = chunker.chunk(records, engagement_id=None)
        await index.index_chunks(chunks)
        searcher = HybridSearcher(embedder=embedder, vector_store=BrokenStore(), bm25_index=index)
        results = await searcher.search(SearchQuery(text="zelkova", top_k=3, candidate_pool=10))
        assert results
        assert results[0].chunk.metadata.artifact_id == "art-T"

    async def test_rrf_score_monotonic_with_rank(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(
                artifact_id=f"art-{i}",
                text=f"Padding text {i} " + " ".join(f"kw{j}" for j in range(50)),
            )
            for i in range(10)
        ]
        store, index, embedder = await _ingest_corpus(records)
        searcher = HybridSearcher(embedder=embedder, vector_store=store, bm25_index=index)
        results = await searcher.search(SearchQuery(text="kw0 kw1 kw2", top_k=5, candidate_pool=20))
        assert results
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    async def test_pg_unreachable_falls_back_to_bm25(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        # Point PgVectorStore at a DSN that nothing is listening on. The
        # _get_pool call inside search_similar must surface the asyncpg
        # transport failure as VectorStoreError, which HybridSearcher
        # catches and degrades to the BM25-only path.
        unreachable_dsn = "postgresql://nobody:nobody@127.0.0.1:1/keystone_none"
        pg_store = PgVectorStore(dsn=unreachable_dsn, dimension=32)

        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} {' '.join(f'w{j}' for j in range(30))}",
            )
            for i in range(4)
        ]
        records.append(
            make_record(
                artifact_id="art-T",
                text="The unique keyword zelkova appeared in this passage.",
            )
        )
        chunker = SemanticChunker(
            target_tokens=80,
            max_tokens=120,
            overlap_tokens=16,
            add_contextual_preamble=False,
        )
        chunks = chunker.chunk(records, engagement_id=None)
        index = InMemoryBM25Index()
        await index.index_chunks(chunks)

        embedder = InMemoryEmbeddingClient(dimension=32)
        searcher = HybridSearcher(embedder=embedder, vector_store=pg_store, bm25_index=index)
        try:
            results = await searcher.search(SearchQuery(text="zelkova", top_k=3, candidate_pool=10))
        finally:
            await pg_store.close()
        assert results
        assert results[0].chunk.metadata.artifact_id == "art-T"

    async def test_pg_unreachable_surfaces_as_vector_store_error(self) -> None:
        # Direct assertion on the error wrapping so future refactors can't
        # silently let raw asyncpg exceptions escape again.
        pg_store = PgVectorStore(
            dsn="postgresql://nobody:nobody@127.0.0.1:1/keystone_none",
            dimension=16,
        )
        try:
            with pytest.raises(VectorStoreError):
                await pg_store.search_similar([0.0] * 16, top_k=1)
        finally:
            await pg_store.close()
