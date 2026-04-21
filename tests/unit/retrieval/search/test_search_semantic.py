"""Tests for RetrievalService.search_semantic() — GAP-12.

Verifies that semantic_search:
- calls the vector store directly (not the hybrid searcher)
- returns RetrievalSource.VECTOR results
- respects exclude_engagement_id isolation
- degrades gracefully when the embedder or vector store fails
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord

from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import EmbeddingError, InMemoryEmbeddingClient
from keystone.retrieval.search.models import (
    RetrievalResult,
    RetrievalSource,
    SearchQuery,
)
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import InMemoryVectorStore, VectorStoreError


def _make_service(*, dimension: int = 32) -> RetrievalService:
    return RetrievalService(
        chunker=SemanticChunker(
            target_tokens=80,
            max_tokens=120,
            overlap_tokens=16,
            add_contextual_preamble=False,
        ),
        embedder=InMemoryEmbeddingClient(dimension=dimension),
        vector_store=InMemoryVectorStore(dimension=dimension),
        bm25_index=InMemoryBM25Index(),
    )


class TestSearchSemanticCallsVectorStoreDirect:
    """semantic_search must bypass the hybrid searcher and go straight to vector_store."""

    async def test_search_semantic_calls_vector_store_not_hybrid(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Apple iPhone sales fell in the latest quarter "
                + " ".join(f"w{i}" for i in range(60)),
            )
        ]
        await service.ingest(records, engagement_id=None)

        # Spy on vector_store.search_similar and hybrid._hybrid.search.
        orig_vector_search = service.vector_store.search_similar
        orig_hybrid_search = service._hybrid.search

        vector_calls: list[Any] = []
        hybrid_calls: list[Any] = []

        async def spy_vector(embedding: Any, *, top_k: int, filters: Any = None) -> Any:
            vector_calls.append((top_k, filters))
            return await orig_vector_search(embedding, top_k=top_k, filters=filters)

        async def spy_hybrid(query: Any) -> Any:
            hybrid_calls.append(query)
            return await orig_hybrid_search(query)

        service.vector_store.search_similar = spy_vector  # type: ignore[method-assign]
        service._hybrid.search = spy_hybrid  # type: ignore[method-assign]

        results = await service.search_semantic("iPhone sales", top_k=5)

        assert results, "expected at least one result"
        # Vector store was called, hybrid was not.
        assert len(vector_calls) == 1, "vector_store.search_similar must be called exactly once"
        assert len(hybrid_calls) == 0, "hybrid searcher must NOT be called by search_semantic"

    async def test_search_semantic_results_have_vector_source(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Apple iPhone sales " + " ".join(f"w{i}" for i in range(60)),
            )
        ]
        await service.ingest(records, engagement_id=None)
        results = await service.search_semantic("iPhone", top_k=3)
        assert results
        for r in results:
            assert r.source is RetrievalSource.VECTOR

    async def test_search_semantic_accepts_search_query_object(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Microsoft Azure cloud " + " ".join(f"w{i}" for i in range(80)),
            )
        ]
        await service.ingest(records, engagement_id=None)
        q = SearchQuery(text="Azure cloud", top_k=1, candidate_pool=5)
        results = await service.search_semantic(q)
        assert len(results) == 1

    async def test_search_semantic_empty_index_returns_empty(self) -> None:
        service = _make_service()
        results = await service.search_semantic("anything", top_k=5)
        assert results == []


class TestSearchSemanticEngagementIsolation:
    """exclude_engagement_id must be threaded to the vector store filter."""

    async def test_semantic_respects_exclude_engagement_id(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        # Institutional memory — always visible.
        await service.ingest(
            [
                make_record(
                    artifact_id="inst-target",
                    text=(
                        "Apple iPhone sales fell in the latest quarter as "
                        "consumers held onto older models longer."
                    ),
                )
            ],
            engagement_id=None,
        )
        # Current-engagement chunk — must NOT appear when excluded.
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text=(
                        "Apple iPhone sales jumped dramatically on the "
                        "new model launch, opposite of the prior quarter."
                    ),
                )
            ],
            engagement_id="eng-active",
        )

        results = await service.search_semantic(
            "iPhone sales", top_k=5, exclude_engagement_id="eng-active"
        )
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur-secret" not in ids, "current-engagement chunk leaked to semantic search"
        assert "inst-target" in ids, "institutional memory must remain visible"

    async def test_semantic_via_search_query_exclude_honored(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()
        await service.ingest(
            [
                make_record(
                    artifact_id="cur", text="iPhone sales " + " ".join(f"w{i}" for i in range(40))
                )
            ],
            engagement_id="eng-active",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="inst", text="iPhone report " + " ".join(f"w{i}" for i in range(40))
                )
            ],
            engagement_id=None,
        )
        q = SearchQuery(
            text="iPhone sales",
            top_k=3,
            candidate_pool=20,
            exclude_engagement_id="eng-active",
        )
        results = await service.search_semantic(q)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur" not in ids
        assert "inst" in ids

    async def test_semantic_engagement_context_auto_applies(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = RetrievalService(
            chunker=SemanticChunker(
                target_tokens=80,
                max_tokens=120,
                overlap_tokens=16,
                add_contextual_preamble=False,
            ),
            embedder=InMemoryEmbeddingClient(dimension=32),
            vector_store=InMemoryVectorStore(dimension=32),
            bm25_index=InMemoryBM25Index(),
            engagement_context="eng-active",
        )
        await service.ingest(
            [
                make_record(
                    artifact_id="cur-secret",
                    text="iPhone current " + " ".join(f"w{i}" for i in range(40)),
                )
            ],
            engagement_id="eng-active",
        )
        await service.ingest_institutional(
            [
                make_record(
                    artifact_id="inst-target",
                    text="iPhone institutional " + " ".join(f"w{i}" for i in range(40)),
                )
            ]
        )
        # String-form call, no explicit exclude — context auto-applies.
        results = await service.search_semantic("iPhone", top_k=5)
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "cur-secret" not in ids, "engagement_context did not auto-apply on semantic path"
        assert "inst-target" in ids


class TestSearchSemanticDegradation:
    """Degradation: embedding failure → empty list + warning."""

    async def test_embedding_failure_returns_empty_list(self) -> None:
        class BrokenEmbedder:
            model = "broken"
            dimension = 32

            async def embed(self, texts: Any) -> Any:
                raise EmbeddingError("provider down")

            async def embed_query(self, text: str) -> list[float]:
                raise EmbeddingError("provider down")

        service = RetrievalService(
            chunker=SemanticChunker(add_contextual_preamble=False),
            embedder=BrokenEmbedder(),
            vector_store=InMemoryVectorStore(dimension=32),
            bm25_index=InMemoryBM25Index(),
        )
        results = await service.search_semantic("iPhone sales", top_k=5)
        assert results == []

    async def test_vector_store_failure_returns_empty_list(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _make_service()

        async def broken_search_similar(
            embedding: Any, *, top_k: int, filters: Any = None
        ) -> list[RetrievalResult]:
            raise VectorStoreError("store unavailable")

        service.vector_store.search_similar = broken_search_similar  # type: ignore[method-assign]
        results = await service.search_semantic("iPhone sales", top_k=5)
        assert results == []


class TestHybridSearchUnchanged:
    """Regression: hybrid_search still runs the full pipeline."""

    async def test_hybrid_search_uses_reranker(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        """After GAP-12, service.search() must still return RERANKED results."""
        service = _make_service()
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} " + " ".join(f"w{j}" for j in range(50)),
            )
            for i in range(5)
        ]
        records.append(
            make_record(
                artifact_id="art-target",
                text=(
                    "Apple iPhone sales fell in the latest quarter as "
                    "consumers held onto older models longer."
                ),
            )
        )
        await service.ingest(records, engagement_id=None)
        results = await service.search("iPhone sales", top_k=3)
        assert results
        # The full pipeline always ends in PassthroughReranker which marks
        # results as RERANKED.
        assert results[0].source is RetrievalSource.RERANKED

    async def test_hybrid_search_calls_hybrid_not_only_vector(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        """Verify hybrid path goes through _hybrid.search, not vector_store directly."""
        service = _make_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Apple iPhone sales " + " ".join(f"w{i}" for i in range(60)),
            )
        ]
        await service.ingest(records, engagement_id=None)

        orig_hybrid_search = service._hybrid.search
        hybrid_calls: list[Any] = []

        async def spy_hybrid(query: Any) -> Any:
            hybrid_calls.append(query)
            return await orig_hybrid_search(query)

        service._hybrid.search = spy_hybrid  # type: ignore[method-assign]

        await service.search("iPhone", top_k=3)
        assert len(hybrid_calls) == 1, "service.search must call the hybrid searcher"
