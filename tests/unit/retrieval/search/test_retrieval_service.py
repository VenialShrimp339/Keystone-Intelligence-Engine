"""End-to-end tests for RetrievalService using in-memory components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import (
    EmbeddingError,
    InMemoryEmbeddingClient,
)
from keystone.retrieval.search.models import (
    QueryClassification,
    RetrievalResult,
    RetrievalSource,
    SearchQuery,
)
from keystone.retrieval.search.reranker import (
    PassthroughReranker,
    RerankerError,
)
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import InMemoryVectorStore


def _build_service(
    *,
    dimension: int = 32,
    reranker: Any | None = None,
) -> RetrievalService:
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
        reranker=reranker or PassthroughReranker(),
    )


class TestRetrievalServiceIngest:
    async def test_empty_returns_zero_counts(self) -> None:
        service = _build_service()
        result = await service.ingest([], engagement_id=None)
        assert result.chunks_created == 0
        assert result.artifacts_ingested == 0

    async def test_creates_chunks_and_counts(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _build_service()
        records = [
            make_record(
                artifact_id="art-A",
                paragraph_index=0,
                text="Microsoft Azure cloud " + " ".join(f"w{i}" for i in range(100)),
            ),
            make_record(
                artifact_id="art-A",
                paragraph_index=1,
                text="Apple iPhone sales " + " ".join(f"t{i}" for i in range(100)),
            ),
        ]
        result = await service.ingest(records, engagement_id=None)
        assert result.artifacts_ingested == 1
        assert result.chunks_created == 2
        assert await service.vector_store.count() == 2
        assert len(service.bm25_index) == 2

    async def test_reingest_is_idempotent(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _build_service()
        records = [
            make_record(
                artifact_id="art-A",
                paragraph_index=0,
                text="hello " + " ".join(f"w{i}" for i in range(60)),
            )
        ]
        first = await service.ingest(records, engagement_id=None)
        assert first.chunks_created == 1
        # Re-ingest wipes artifact first, so it's a new create, not an update
        second = await service.ingest(records, engagement_id=None)
        assert second.chunks_created == 1
        assert await service.vector_store.count() == 1


class TestRetrievalServiceSearch:
    async def test_end_to_end(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        service = _build_service()
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
        assert results[0].source is RetrievalSource.RERANKED
        assert results[0].chunk.metadata.artifact_id == "art-target"
        assert results[0].chunk.embedding is None

    async def test_search_with_search_query_object(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _build_service()
        records = [
            make_record(
                artifact_id="art-A",
                text="Microsoft Azure cloud " + " ".join(f"w{i}" for i in range(80)),
            )
        ]
        await service.ingest(records, engagement_id=None)
        q = SearchQuery(text="Azure cloud", top_k=1, candidate_pool=5)
        out = await service.search(q)
        assert len(out) == 1

    async def test_search_empty_index(self) -> None:
        service = _build_service()
        out = await service.search("anything", top_k=5)
        assert out == []

    async def test_reranker_failure_falls_back(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        class BrokenReranker:
            model = "broken"

            async def rerank(
                self, query: str, results: Sequence[RetrievalResult], *, top_k: int
            ) -> list[RetrievalResult]:
                raise RerankerError("upstream down")

        service = _build_service(reranker=BrokenReranker())
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} " + " ".join(f"w{j}" for j in range(50)),
            )
            for i in range(3)
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
        # Falls back to pre-rerank hybrid source
        assert results[0].source is RetrievalSource.HYBRID

    async def test_reranker_returns_empty_falls_back(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        class EmptyReranker:
            model = "empty"

            async def rerank(
                self, query: str, results: Sequence[RetrievalResult], *, top_k: int
            ) -> list[RetrievalResult]:
                return []

        service = _build_service(reranker=EmptyReranker())
        records = [
            make_record(
                artifact_id=f"pad-{i}",
                text=f"padding {i} " + " ".join(f"w{j}" for j in range(50)),
            )
            for i in range(3)
        ]
        records.append(
            make_record(
                artifact_id="art-target",
                text="Apple iPhone sales fell in the latest quarter.",
            )
        )
        await service.ingest(records, engagement_id=None)
        out = await service.search("iPhone", top_k=3)
        assert out
        assert out[0].source is RetrievalSource.HYBRID

    async def test_classify_delegates_to_router(self) -> None:
        service = _build_service()
        route = await service.classify("What was Apple's revenue in FY2023?")
        assert route.classification in (
            QueryClassification.QUANTITATIVE,
            QueryClassification.HYBRID,
        )

    async def test_embed_failure_during_ingest_propagates(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
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
        records = [make_record(text="hello world.")]
        with pytest.raises(EmbeddingError):
            await service.ingest(records, engagement_id=None)

    async def test_default_reranker_is_passthrough(self) -> None:
        service = RetrievalService(
            chunker=SemanticChunker(add_contextual_preamble=False),
            embedder=InMemoryEmbeddingClient(dimension=16),
            vector_store=InMemoryVectorStore(dimension=16),
        )
        assert isinstance(service.reranker, PassthroughReranker)

    async def test_search_top_k_overrides_search_query(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        service = _build_service()
        records = [
            make_record(
                artifact_id=f"art-{i}",
                text=f"kw{i} padding " + " ".join(f"w{j}" for j in range(60)),
            )
            for i in range(5)
        ]
        await service.ingest(records, engagement_id=None)
        base = SearchQuery(text="kw0 kw1 kw2", top_k=5, candidate_pool=20)
        out = await service.search(base, top_k=2)
        assert len(out) <= 2
