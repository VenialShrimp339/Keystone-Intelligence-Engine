"""Factory wiring for the retrieval stack.

Builds a production-ready :class:`RetrievalService` from the typed
:class:`AppConfig` + :class:`RetrievalConfig` pair. Callers that want
a test-friendly service should keep constructing components by hand
and injecting :class:`InMemoryVectorStore` / :class:`InMemoryBM25Index`
test doubles directly.

The factory cross-checks embedding dimensions at the boundary so a
mis-set ``RetrievalConfig.embedding_dimension`` cannot silently diverge
from the Voyage model's native output and corrupt the pgvector index.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from keystone.retrieval.search.bm25_index import InMemoryBM25Index
from keystone.retrieval.search.chunker import SemanticChunker
from keystone.retrieval.search.embeddings import (
    VOYAGE_FINANCE_DIM,
    VOYAGE_FINANCE_MODEL,
    EmbeddingClient,
    VoyageEmbeddingClient,
)
from keystone.retrieval.search.hybrid_search import HybridSearchConfig
from keystone.retrieval.search.query_router import RuleBasedQueryRouter
from keystone.retrieval.search.reranker import (
    CohereReranker,
    PassthroughReranker,
    RerankerClient,
)
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import (
    PgVectorStore,
    VectorStore,
)

if TYPE_CHECKING:
    from keystone.models.config import AppConfig, RetrievalConfig


class RetrievalFactoryError(RuntimeError):
    """Raised when the factory cannot assemble a consistent stack."""


def build_retrieval_service(
    app_config: AppConfig,
    retrieval_config: RetrievalConfig,
    *,
    embedder: EmbeddingClient | None = None,
    vector_store: VectorStore | None = None,
    reranker: RerankerClient | None = None,
) -> RetrievalService:
    """Build a :class:`RetrievalService` wired for production use.

    Parameters
    ----------
    app_config:
        Environment-loaded settings. Supplies ``keystone_database_url``,
        ``voyage_api_key``, ``cohere_api_key``.
    retrieval_config:
        Service-level retrieval knobs: embedding model + dimension,
        chunk sizing, hybrid pool size, rerank top-k, RRF damping.

    The three injection hooks (``embedder``, ``vector_store``,
    ``reranker``) exist for tests and custom deployments -- when
    supplied they replace the default production component for that
    slot. The factory still validates any injected embedder /
    vector store against ``retrieval_config.embedding_dimension`` so
    the cross-check guarantee holds regardless of source.

    Consistency checks performed at construction time:

    - ``retrieval_config.embedding_dimension`` matches the embedder's
      ``dimension`` attribute.
    - The vector store's stored ``dimension`` matches the embedder's.
    - When the embedder is the default Voyage client and the model is
      ``voyage-finance-2``, the dimension must be ``1024``
      (``VOYAGE_FINANCE_DIM``). Operators that want to use a different
      Voyage model should pass a pre-built embedder.
    """

    embedding_dim = retrieval_config.embedding_dimension

    resolved_embedder = embedder or _build_default_embedder(
        app_config=app_config,
        retrieval_config=retrieval_config,
    )
    _assert_embedder_dimension(resolved_embedder, embedding_dim)

    resolved_vector_store = vector_store or PgVectorStore(
        dsn=app_config.keystone_database_url,
        dimension=embedding_dim,
    )
    _assert_vector_store_dimension(resolved_vector_store, embedding_dim)

    resolved_reranker = reranker or _build_default_reranker(app_config=app_config)

    # ``chunk_size_tokens`` is the soft target; ``max_tokens`` is the hard
    # cap. Use a 33% headroom so the passage-merging step has room to keep
    # adjacent short passages together without flushing prematurely
    # (matches the 384/512 ratio used in the test suite).
    target = retrieval_config.chunk_size_tokens
    chunker = SemanticChunker(
        target_tokens=target,
        max_tokens=max(target + retrieval_config.chunk_overlap_tokens, int(target * 4 / 3)),
        overlap_tokens=retrieval_config.chunk_overlap_tokens,
    )
    bm25_index = InMemoryBM25Index()
    hybrid_config = HybridSearchConfig(rrf_k=retrieval_config.rrf_k)
    router = RuleBasedQueryRouter()

    return RetrievalService(
        chunker=chunker,
        embedder=resolved_embedder,
        vector_store=resolved_vector_store,
        bm25_index=bm25_index,
        reranker=resolved_reranker,
        router=router,
        hybrid_config=hybrid_config,
    )


def _build_default_embedder(
    *,
    app_config: AppConfig,
    retrieval_config: RetrievalConfig,
) -> EmbeddingClient:
    if not app_config.voyage_api_key:
        raise RetrievalFactoryError(
            "AppConfig.voyage_api_key is empty; set VOYAGE_API_KEY or inject an embedder"
        )
    # When the operator keeps the voyage-finance-2 default, pin the
    # dimension to the documented value so a mis-set RetrievalConfig
    # fails loudly instead of corrupting the index.
    if retrieval_config.voyage_model == VOYAGE_FINANCE_MODEL and (
        retrieval_config.embedding_dimension != VOYAGE_FINANCE_DIM
    ):
        raise RetrievalFactoryError(
            f"voyage-finance-2 returns {VOYAGE_FINANCE_DIM}-dim vectors, but "
            f"RetrievalConfig.embedding_dimension={retrieval_config.embedding_dimension}. "
            "Fix the config or inject a custom embedder."
        )
    return VoyageEmbeddingClient(
        api_key=app_config.voyage_api_key,
        model=retrieval_config.voyage_model,
        dimension=retrieval_config.embedding_dimension,
    )


def _build_default_reranker(*, app_config: AppConfig) -> RerankerClient:
    if not app_config.cohere_api_key:
        # Degrade gracefully: the retrieval service catches reranker
        # failure and falls back to the RRF-ordered list anyway. A
        # PassthroughReranker makes the fallback explicit and avoids
        # spamming warnings on every search when Cohere is simply
        # not configured.
        return PassthroughReranker()
    return CohereReranker(api_key=app_config.cohere_api_key)


def _assert_embedder_dimension(embedder: EmbeddingClient, expected: int) -> None:
    actual = getattr(embedder, "dimension", None)
    if actual != expected:
        raise RetrievalFactoryError(
            f"embedder.dimension={actual} does not match "
            f"RetrievalConfig.embedding_dimension={expected}"
        )


def _assert_vector_store_dimension(vector_store: VectorStore, expected: int) -> None:
    actual = getattr(vector_store, "dimension", None)
    if actual is None:
        # Protocol does not mandate the attribute; accept but skip the check.
        return
    if actual != expected:
        raise RetrievalFactoryError(
            f"vector_store.dimension={actual} does not match "
            f"RetrievalConfig.embedding_dimension={expected}"
        )
