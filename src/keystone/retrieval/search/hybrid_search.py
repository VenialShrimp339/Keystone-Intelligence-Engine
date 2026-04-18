"""Hybrid search via Reciprocal Rank Fusion (RRF).

Runs the dense (vector) and sparse (BM25) retrievers in parallel, then
fuses their rankings using RRF with the standard ``k=60`` constant:

    score(d) = sum over retrievers of 1 / (k + rank_i(d))

RRF is rank-sensitive only -- it ignores the raw magnitude of scores,
which makes it robust when combining retrievers whose score ranges are
not comparable (cosine similarity is bounded on [-1, 1]; BM25 is
unbounded). Empirically it beats linear-combination fusion on most
heterogeneous retrieval stacks.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from keystone.retrieval.search.embeddings import EmbeddingError
from keystone.retrieval.search.models import (
    RetrievalResult,
    RetrievalSource,
)
from keystone.retrieval.search.vector_store import VectorStoreError

if TYPE_CHECKING:
    from keystone.retrieval.search.bm25_index import BM25Index
    from keystone.retrieval.search.embeddings import EmbeddingClient
    from keystone.retrieval.search.models import DocumentChunk, SearchQuery
    from keystone.retrieval.search.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_RRF_K = 60


@dataclass(frozen=True)
class HybridSearchConfig:
    """Knobs for :class:`HybridSearcher`."""

    rrf_k: int = DEFAULT_RRF_K
    vector_weight: float = 1.0
    bm25_weight: float = 1.0

    def __post_init__(self) -> None:
        if self.rrf_k < 1:
            raise ValueError("rrf_k must be >= 1")
        if self.vector_weight < 0.0 or self.bm25_weight < 0.0:
            raise ValueError("retriever weights must be non-negative")
        if self.vector_weight == 0.0 and self.bm25_weight == 0.0:
            raise ValueError("at least one retriever weight must be positive")


class HybridSearcher:
    """Orchestrates vector + BM25 retrieval and RRF fusion.

    The searcher is stateless -- it holds references to the retrievers
    and the embedder but keeps no per-query state, so a single instance
    is safe to share across concurrent agents.
    """

    def __init__(
        self,
        *,
        embedder: EmbeddingClient,
        vector_store: VectorStore,
        bm25_index: BM25Index,
        config: HybridSearchConfig | None = None,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._bm25_index = bm25_index
        self._config = config or HybridSearchConfig()

    async def search(self, query: SearchQuery) -> list[RetrievalResult]:
        vector_task = asyncio.create_task(self._vector_search(query))
        bm25_task = asyncio.create_task(self._bm25_search(query))
        vector_results, bm25_results = await asyncio.gather(
            vector_task, bm25_task, return_exceptions=False
        )
        # BM25 has no metadata filtering inside the index itself, so
        # apply the exclusion filter here if the caller set one.
        if query.exclude_engagement_id is not None:
            bm25_results = _drop_engagement(bm25_results, query.exclude_engagement_id)
        fused = self._fuse(vector_results, bm25_results)
        return fused[: query.top_k]

    # --- Retriever invocation ------------------------------------------

    async def _vector_search(self, query: SearchQuery) -> list[RetrievalResult]:
        if self._config.vector_weight == 0.0:
            return []
        try:
            embedding = await self._embedder.embed_query(query.text)
        except EmbeddingError:
            logger.exception("vector search skipped: query embed failed")
            return []
        # Thread the engagement-exclusion filter through the store-level
        # filter dict so PgVectorStore can push it into WHERE clauses.
        filters: dict[str, Any] | None
        if query.filters or query.exclude_engagement_id is not None:
            filters = dict(query.filters) if query.filters else {}
            if query.exclude_engagement_id is not None:
                filters["exclude_engagement_id"] = query.exclude_engagement_id
        else:
            filters = None
        try:
            return await self._vector_store.search_similar(
                embedding,
                top_k=query.candidate_pool,
                filters=filters,
            )
        except VectorStoreError:
            logger.exception("vector search skipped: store unavailable")
            return []

    async def _bm25_search(self, query: SearchQuery) -> list[RetrievalResult]:
        if self._config.bm25_weight == 0.0:
            return []
        return await self._bm25_index.search(query.text, top_k=query.candidate_pool)

    # --- Fusion ---------------------------------------------------------

    def _fuse(
        self,
        vector_results: list[RetrievalResult],
        bm25_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        by_id: dict[str, RetrievalResult] = {}
        rrf: dict[str, float] = {}

        for rank, result in enumerate(vector_results, start=1):
            contribution = self._config.vector_weight / (self._config.rrf_k + rank)
            rrf[result.chunk.chunk_id] = rrf.get(result.chunk.chunk_id, 0.0) + contribution
            _merge_into(by_id, result)

        for rank, result in enumerate(bm25_results, start=1):
            contribution = self._config.bm25_weight / (self._config.rrf_k + rank)
            rrf[result.chunk.chunk_id] = rrf.get(result.chunk.chunk_id, 0.0) + contribution
            _merge_into(by_id, result)

        ordered_ids = sorted(rrf.keys(), key=lambda cid: rrf[cid], reverse=True)
        fused: list[RetrievalResult] = []
        for rank, chunk_id in enumerate(ordered_ids, start=1):
            result = by_id[chunk_id]
            score = rrf[chunk_id]
            fused.append(
                RetrievalResult(
                    chunk=result.chunk,
                    score=score,
                    rrf_score=score,
                    vector_score=result.vector_score,
                    bm25_score=result.bm25_score,
                    source=RetrievalSource.HYBRID,
                    rank=rank,
                )
            )
        return fused


def _merge_into(by_id: dict[str, RetrievalResult], result: RetrievalResult) -> None:
    """Merge a retriever result into the ``by_id`` accumulator.

    When the same chunk appears in both retrievers the second result
    overwrites the chunk reference (they should be identical up to
    ``embedding=None``) while preserving the already-known per-retriever
    score from the first result.
    """

    existing = by_id.get(result.chunk.chunk_id)
    if existing is None:
        by_id[result.chunk.chunk_id] = _clone_with_sources(result)
        return
    merged_vector = (
        result.vector_score if result.vector_score is not None else existing.vector_score
    )
    merged_bm25 = result.bm25_score if result.bm25_score is not None else existing.bm25_score
    # Keep the richer chunk reference (prefer one with more populated fields)
    chunk: DocumentChunk = existing.chunk
    by_id[result.chunk.chunk_id] = RetrievalResult(
        chunk=chunk,
        score=existing.score,
        vector_score=merged_vector,
        bm25_score=merged_bm25,
        source=existing.source,
        rank=existing.rank,
    )


def _clone_with_sources(result: RetrievalResult) -> RetrievalResult:
    return RetrievalResult(
        chunk=result.chunk,
        score=result.score,
        vector_score=result.vector_score,
        bm25_score=result.bm25_score,
        rrf_score=result.rrf_score,
        rerank_score=result.rerank_score,
        source=result.source,
        rank=result.rank,
    )


def _drop_engagement(
    results: list[RetrievalResult], exclude_engagement_id: str
) -> list[RetrievalResult]:
    """Post-filter BM25 output to honour the engagement-exclusion filter.

    BM25 has no native metadata filter, so this runs in-process after
    the index has returned its top-k candidates. Chunks with
    ``engagement_id=None`` (institutional memory) always pass.
    """

    kept: list[RetrievalResult] = []
    for result in results:
        chunk_engagement = result.chunk.metadata.engagement_id
        if chunk_engagement is not None and chunk_engagement == exclude_engagement_id:
            continue
        kept.append(result)
    return kept
