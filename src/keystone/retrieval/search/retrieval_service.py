"""Top-level retrieval service.

Stitches the search sub-package components into a single surface:

    chunker -> embedder -> vector store + BM25 index -> hybrid -> reranker

``ingest(records)`` turns Lane E evidence records into chunks, embeds
them, and writes to both the vector store and the BM25 index
atomically (the BM25 index is rebuilt on each ingest to keep the two
views consistent).

``search(query)`` runs the hybrid pipeline and optionally reranks. When
the reranker fails or is missing, the service returns the pre-rerank
RRF-sorted list instead of failing -- the gateway should keep serving
search traffic even when Cohere is down.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.embeddings import EmbeddingError
from keystone.retrieval.search.hybrid_search import (
    HybridSearchConfig,
    HybridSearcher,
)
from keystone.retrieval.search.models import (
    IngestResult,
    RetrievalSource,
    SearchQuery,
)
from keystone.retrieval.search.query_router import RuleBasedQueryRouter
from keystone.retrieval.search.reranker import (
    PassthroughReranker,
    RerankerError,
)
from keystone.retrieval.search.vector_store import VectorStoreError

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from keystone.retrieval.parse_models import EvidencePrepRecord
    from keystone.retrieval.search.bm25_index import BM25Index
    from keystone.retrieval.search.chunker import SemanticChunker
    from keystone.retrieval.search.embeddings import EmbeddingClient
    from keystone.retrieval.search.models import (
        DocumentChunk,
        QueryRoute,
        RetrievalResult,
    )
    from keystone.retrieval.search.query_router import QueryRouter
    from keystone.retrieval.search.reranker import RerankerClient
    from keystone.retrieval.search.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """Top-level orchestrator for the retrieval stack."""

    def __init__(
        self,
        *,
        chunker: SemanticChunker,
        embedder: EmbeddingClient,
        vector_store: VectorStore,
        bm25_index: BM25Index | None = None,
        reranker: RerankerClient | None = None,
        router: QueryRouter | None = None,
        hybrid_config: HybridSearchConfig | None = None,
        engagement_context: str | None = None,
    ) -> None:
        """Construct a retrieval service.

        ``engagement_context`` binds the service to a specific
        engagement for callers that use the string-form
        :meth:`search` path: those calls automatically apply the
        context as ``exclude_engagement_id`` so current-engagement
        chunks from sibling agents are hidden. System-level or
        aggregator callers that need full corpus access construct
        the service without an ``engagement_context``.

        A :class:`SearchQuery` passed to :meth:`search` is treated as
        a caller-authored object — its ``exclude_engagement_id`` field
        is honored literally (including ``None``, which is read as an
        explicit opt-out). The production path for agent traffic is
        the :mod:`keystone.gateway.retrieval_bridge`, which constructs
        :class:`SearchQuery` objects and therefore bypasses the
        ``engagement_context`` auto-apply; that bridge enforces the
        founder-intent inter-agent isolation invariant structurally by
        injecting ``exclude_engagement_id=<caller ToolCall's
        engagement_id>`` whenever the caller did not already specify
        one. ``engagement_context`` therefore mainly protects string-
        form callers and serves as a belt-and-braces default for
        non-bridge code paths.
        """

        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_index: BM25Index = bm25_index or InMemoryBM25Index()
        self.reranker: RerankerClient = reranker or PassthroughReranker()
        self.router: QueryRouter = router or RuleBasedQueryRouter()
        self._engagement_context = engagement_context
        self._hybrid = HybridSearcher(
            embedder=embedder,
            vector_store=vector_store,
            bm25_index=self.bm25_index,
            config=hybrid_config,
        )

    @property
    def engagement_context(self) -> str | None:
        """Active engagement id for default-on isolation (read-only)."""

        return self._engagement_context

    # --- Ingest ---------------------------------------------------------

    async def ingest(
        self,
        records: Iterable[EvidencePrepRecord],
        *,
        engagement_id: str | None,
    ) -> IngestResult:
        """Ingest Lane E records into the vector store and BM25 index.

        ``engagement_id`` is a required kwarg. Pass the active engagement
        id so active-engagement search callers can exclude chunks from
        other agents working in the same engagement. Pass ``None``
        explicitly for institutional-memory ingest (visible everywhere)
        — the preferred spelling for that case is
        :meth:`ingest_institutional`, which names the intent without
        repeating the ``engagement_id=None`` incantation at every call
        site.
        """

        records_list = list(records)
        if not records_list:
            return IngestResult(
                artifacts_ingested=0,
                chunks_created=0,
                chunks_updated=0,
                chunks_skipped=0,
            )
        artifact_ids = {record.artifact_id for record in records_list}
        chunks = self.chunker.chunk(records_list, engagement_id=engagement_id)
        if not chunks:
            return IngestResult(
                artifacts_ingested=len(artifact_ids),
                chunks_created=0,
                chunks_updated=0,
                chunks_skipped=0,
            )
        embedded = await self._embed_chunks(chunks)
        # Refresh pgvector + BM25 state before upsert so a partial write
        # doesn't desynchronize them. Delete-then-insert is idempotent
        # and keeps chunk_ids stable across re-ingestion of the same
        # artifact.
        for artifact_id in artifact_ids:
            await self.vector_store.delete_by_artifact_id(artifact_id)
            await self.bm25_index.delete_by_artifact_id(artifact_id)
        created, updated = await self.vector_store.upsert_chunks(embedded)
        await self.bm25_index.add_chunks(embedded)
        skipped = len(chunks) - len(embedded)
        return IngestResult(
            artifacts_ingested=len(artifact_ids),
            chunks_created=created,
            chunks_updated=updated,
            chunks_skipped=skipped,
        )

    async def ingest_institutional(
        self,
        records: Iterable[EvidencePrepRecord],
    ) -> IngestResult:
        """Ingest records as institutional memory (visible to every engagement).

        Thin wrapper over :meth:`ingest` with ``engagement_id=None``.
        Use this for cross-engagement corpora (curated reference
        documents, prior engagement artifacts that are intentionally
        shared) so the call site names the intent rather than passing
        a naked ``None``.
        """

        return await self.ingest(records, engagement_id=None)

    # --- Search ---------------------------------------------------------

    async def search(
        self,
        query: str | SearchQuery,
        *,
        top_k: int | None = None,
        exclude_engagement_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Run hybrid retrieval + reranking and return ``top_k`` results.

        Degradation contract:

        - Vector store / embedder failures already degrade inside
          :class:`HybridSearcher` (BM25-only results).
        - Reranker failure or empty rerank output falls back to the
          pre-rerank RRF-ordered list, sliced to the caller's
          ``top_k``. ``result.source`` reveals which path served the
          final list (``RERANKED`` vs. ``HYBRID``).

        Internal pool rewrite:

        The hybrid stage needs a wider candidate pool than the caller's
        final ``top_k`` so the reranker has real candidates to reorder.
        This method therefore clones the incoming :class:`SearchQuery`
        with ``candidate_pool`` and ``top_k`` both set to
        ``max(candidate_pool, top_k)`` before running hybrid. The
        reranker is then invoked with the caller's original ``top_k``
        and the returned list is sliced back down. Callers see the
        original ``top_k`` honored in the result list -- only the
        hybrid-stage clone is affected.

        Inter-agent isolation:

        ``exclude_engagement_id`` (or the same-named field on a
        :class:`SearchQuery`) is threaded through to the vector store
        and BM25 path so chunks tagged with the excluded engagement are
        dropped from the result set. Chunks with
        ``engagement_id=None`` (institutional memory) always remain
        visible. When the service was constructed with
        ``engagement_context=<eid>``, a string-form call without an
        explicit ``exclude_engagement_id`` kwarg inherits that context
        automatically; a :class:`SearchQuery` passed in is honored
        literally (a ``None`` field is read as an explicit opt-out).
        """

        query_is_search_query_object = isinstance(query, SearchQuery)
        search_query = self._coerce_query(
            query, top_k=top_k, exclude_engagement_id=exclude_engagement_id
        )
        # Auto-apply the service-level engagement_context to string-form
        # calls that didn't specify their own exclusion. SearchQuery
        # objects are passed through unchanged -- a caller that builds
        # its own query object is trusted to set the field explicitly.
        if (
            self._engagement_context is not None
            and search_query.exclude_engagement_id is None
            and not query_is_search_query_object
        ):
            search_query = search_query.model_copy(
                update={"exclude_engagement_id": self._engagement_context}
            )
        hybrid_pool_size = max(search_query.candidate_pool, search_query.top_k)
        pool_query = search_query.model_copy(
            update={
                "candidate_pool": hybrid_pool_size,
                "top_k": hybrid_pool_size,
            }
        )
        hybrid_results = await self._hybrid.search(pool_query)
        if not hybrid_results:
            return []
        try:
            reranked = await self.reranker.rerank(
                search_query.text,
                hybrid_results,
                top_k=search_query.top_k,
            )
        except RerankerError:
            logger.warning("reranker failed; returning unranked RRF results", exc_info=True)
            return hybrid_results[: search_query.top_k]
        if not reranked:
            return hybrid_results[: search_query.top_k]
        return reranked

    async def search_semantic(
        self,
        query: str | SearchQuery,
        *,
        top_k: int | None = None,
        exclude_engagement_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Run pure vector similarity search and return ``top_k`` results.

        Embeds the query text and calls the vector store directly. No
        BM25, no RRF fusion, no reranking.

        Degradation contract:

        - If the embedding call fails, return an empty list and log a
          warning. The caller keeps serving; a missing vector store or
          embedder failure is not fatal for the semantic path.

        Inter-agent isolation:

        ``exclude_engagement_id`` is honoured through the vector store's
        filter dict, identical to the hybrid path. The
        ``engagement_context`` auto-apply rules from :meth:`search` also
        apply here for string-form calls.
        """

        query_is_search_query_object = isinstance(query, SearchQuery)
        search_query = self._coerce_query(
            query, top_k=top_k, exclude_engagement_id=exclude_engagement_id
        )
        if (
            self._engagement_context is not None
            and search_query.exclude_engagement_id is None
            and not query_is_search_query_object
        ):
            search_query = search_query.model_copy(
                update={"exclude_engagement_id": self._engagement_context}
            )
        try:
            embedding = await self.embedder.embed_query(search_query.text)
        except EmbeddingError:
            logger.warning("semantic_search skipped: query embed failed", exc_info=True)
            return []
        filters: dict[str, Any] | None
        if search_query.filters or search_query.exclude_engagement_id is not None:
            filters = dict(search_query.filters) if search_query.filters else {}
            if search_query.exclude_engagement_id is not None:
                filters["exclude_engagement_id"] = search_query.exclude_engagement_id
        else:
            filters = None
        try:
            results = await self.vector_store.search_similar(
                embedding,
                top_k=search_query.top_k,
                filters=filters,
            )
        except VectorStoreError:
            logger.warning("semantic_search skipped: vector store unavailable", exc_info=True)
            return []
        for rank, result in enumerate(results, start=1):
            result.rank = rank
            result.source = RetrievalSource.VECTOR
        return results

    async def classify(self, query: str) -> QueryRoute:
        return await self.router.classify(query)

    # --- Lifecycle ------------------------------------------------------

    async def ensure_ready(self) -> None:
        """Run any one-time setup (create schema, indexes)."""

        await self.vector_store.ensure_schema()

    async def close(self) -> None:
        await self.vector_store.close()

    # --- Helpers --------------------------------------------------------

    async def _embed_chunks(self, chunks: Sequence[DocumentChunk]) -> list[DocumentChunk]:
        if not chunks:
            return []
        try:
            vectors = await self.embedder.embed([chunk.content for chunk in chunks])
        except EmbeddingError:
            logger.exception("embedding batch failed; skipping ingest")
            raise
        if len(vectors) != len(chunks):
            raise EmbeddingError(
                f"embedder returned {len(vectors)} vectors for {len(chunks)} chunks"
            )
        return [chunk.with_embedding(vec) for chunk, vec in zip(chunks, vectors, strict=True)]

    def _coerce_query(
        self,
        query: str | SearchQuery,
        *,
        top_k: int | None,
        exclude_engagement_id: str | None = None,
    ) -> SearchQuery:
        if isinstance(query, SearchQuery):
            updates: dict[str, Any] = {}
            if top_k is not None and top_k != query.top_k:
                updates["top_k"] = top_k
                updates["candidate_pool"] = max(query.candidate_pool, top_k)
            if exclude_engagement_id is not None and query.exclude_engagement_id is None:
                # Caller's top-level kwarg wins only when the SearchQuery
                # left it unset; explicit query.exclude_engagement_id
                # already covers the intent.
                updates["exclude_engagement_id"] = exclude_engagement_id
            if not updates:
                return query
            return query.model_copy(update=updates)
        if top_k is None:
            return SearchQuery(text=query, exclude_engagement_id=exclude_engagement_id)
        return SearchQuery(
            text=query,
            top_k=top_k,
            candidate_pool=max(top_k, 150),
            exclude_engagement_id=exclude_engagement_id,
        )
