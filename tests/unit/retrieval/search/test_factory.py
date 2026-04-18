"""Unit tests for the retrieval-stack factory.

The factory wires production components together from
:class:`AppConfig` + :class:`RetrievalConfig`, and crucially
cross-checks embedding dimension so a mis-set config cannot silently
diverge from the Voyage model output.
"""

from __future__ import annotations

from typing import Any

import pytest

from keystone.models.config import AppConfig, RetrievalConfig
from keystone.retrieval.search.embeddings import (
    VOYAGE_FINANCE_DIM,
    VOYAGE_FINANCE_MODEL,
    InMemoryEmbeddingClient,
)
from keystone.retrieval.search.factory import (
    RetrievalFactoryError,
    build_retrieval_service,
)
from keystone.retrieval.search.query_router import RuleBasedQueryRouter
from keystone.retrieval.search.reranker import (
    CohereReranker,
    PassthroughReranker,
)
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import (
    InMemoryVectorStore,
    PgVectorStore,
)


def _app_config(
    *,
    voyage_api_key: str = "vk",
    cohere_api_key: str = "ck",
    db_url: str = "postgresql://localhost/keystone_test",
) -> AppConfig:
    return AppConfig(
        voyage_api_key=voyage_api_key,
        cohere_api_key=cohere_api_key,
        keystone_database_url=db_url,
    )


class _FakeCohereSdkClient:
    async def rerank(self, **kwargs: Any) -> Any:  # pragma: no cover - not invoked
        raise AssertionError("not expected to be called in factory tests")


class _FakeVoyageSdkClient:
    """Just enough of voyageai.Client to satisfy VoyageEmbeddingClient init."""

    def embed(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("not expected to be called in factory tests")


class TestBuildRetrievalService:
    def test_builds_ready_service_with_injected_components(self) -> None:
        embedder = InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM)
        vector_store = InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM)
        service = build_retrieval_service(
            _app_config(),
            RetrievalConfig(),
            embedder=embedder,
            vector_store=vector_store,
        )
        assert isinstance(service, RetrievalService)
        assert service.embedder is embedder
        assert service.vector_store is vector_store
        assert isinstance(service.router, RuleBasedQueryRouter)

    def test_embedder_dimension_mismatch_rejected(self) -> None:
        # Config says 1024, embedder says 32 -> factory must refuse.
        embedder = InMemoryEmbeddingClient(dimension=32)
        vector_store = InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM)
        with pytest.raises(RetrievalFactoryError, match="embedder.dimension"):
            build_retrieval_service(
                _app_config(),
                RetrievalConfig(),
                embedder=embedder,
                vector_store=vector_store,
            )

    def test_vector_store_dimension_mismatch_rejected(self) -> None:
        embedder = InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM)
        vector_store = InMemoryVectorStore(dimension=32)
        with pytest.raises(RetrievalFactoryError, match="vector_store.dimension"):
            build_retrieval_service(
                _app_config(),
                RetrievalConfig(),
                embedder=embedder,
                vector_store=vector_store,
            )

    def test_config_dimension_mismatch_rejected(self) -> None:
        # Config says 512 but the default embedder would produce 1024 ->
        # factory must refuse before constructing the Voyage client.
        cfg = RetrievalConfig(embedding_dimension=512)
        with pytest.raises(RetrievalFactoryError, match=r"voyage-finance-2"):
            build_retrieval_service(
                _app_config(),
                cfg,
                vector_store=InMemoryVectorStore(dimension=512),
            )

    def test_missing_voyage_key_raises(self) -> None:
        with pytest.raises(RetrievalFactoryError, match="voyage_api_key"):
            build_retrieval_service(
                _app_config(voyage_api_key=""),
                RetrievalConfig(),
                vector_store=InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM),
            )

    def test_missing_cohere_key_uses_passthrough(self) -> None:
        # Without a Cohere key the factory must install a
        # PassthroughReranker instead of raising, so search still works.
        service = build_retrieval_service(
            _app_config(cohere_api_key=""),
            RetrievalConfig(),
            embedder=InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM),
            vector_store=InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM),
        )
        assert isinstance(service.reranker, PassthroughReranker)

    def test_cohere_reranker_wired_when_key_present(self) -> None:
        service = build_retrieval_service(
            _app_config(),
            RetrievalConfig(),
            embedder=InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM),
            vector_store=InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM),
            reranker=CohereReranker(api_key="ck", client=_FakeCohereSdkClient()),
        )
        assert isinstance(service.reranker, CohereReranker)

    def test_custom_voyage_model_allows_any_dimension(self) -> None:
        # Non-default model: the dimension pin is skipped, caller's
        # config value is trusted (but still cross-checked against the
        # embedder/store).
        from keystone.retrieval.search.embeddings import VoyageEmbeddingClient

        cfg = RetrievalConfig(voyage_model="voyage-3", embedding_dimension=512)
        # Use an injected embedder so we don't need a real Voyage key
        # path. The factory still runs the _assert_embedder_dimension
        # check against the cfg value.
        embedder = VoyageEmbeddingClient(
            api_key="k", model="voyage-3", dimension=512, client=_FakeVoyageSdkClient()
        )
        service = build_retrieval_service(
            _app_config(),
            cfg,
            embedder=embedder,
            vector_store=InMemoryVectorStore(dimension=512),
        )
        assert service.embedder is embedder

    def test_default_pgvector_used_when_vector_store_omitted(self) -> None:
        service = build_retrieval_service(
            _app_config(),
            RetrievalConfig(),
            embedder=InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM),
        )
        assert isinstance(service.vector_store, PgVectorStore)
        assert service.vector_store.dimension == VOYAGE_FINANCE_DIM

    def test_chunker_wired_from_retrieval_config(self) -> None:
        cfg = RetrievalConfig(chunk_size_tokens=128, chunk_overlap_tokens=16)
        service = build_retrieval_service(
            _app_config(),
            cfg,
            embedder=InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM),
            vector_store=InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM),
        )
        assert service.chunker.target_tokens == 128
        assert service.chunker.overlap_tokens == 16
        # max_tokens uses the 4/3 headroom; for target=128 that's at
        # least 170 (int(128*4/3)).
        assert service.chunker.max_tokens >= 170

    def test_rrf_k_threaded_into_hybrid(self) -> None:
        cfg = RetrievalConfig(rrf_k=42)
        service = build_retrieval_service(
            _app_config(),
            cfg,
            embedder=InMemoryEmbeddingClient(dimension=VOYAGE_FINANCE_DIM),
            vector_store=InMemoryVectorStore(dimension=VOYAGE_FINANCE_DIM),
        )
        # Access via the hybrid config the service built internally
        hybrid = service._hybrid  # noqa: SLF001 (test-only inspection)
        assert hybrid._config.rrf_k == 42  # noqa: SLF001


class TestVoyageDefaultDimensionPin:
    def test_mismatched_finance_model_dimension_caught(self) -> None:
        # voyage-finance-2 is 1024-dim; a cfg of 768 must be rejected
        # before VoyageEmbeddingClient is ever built, so the factory
        # does not need a real API key or network.
        cfg = RetrievalConfig(embedding_dimension=768)
        with pytest.raises(RetrievalFactoryError) as exc:
            build_retrieval_service(
                _app_config(),
                cfg,
                vector_store=InMemoryVectorStore(dimension=768),
            )
        assert VOYAGE_FINANCE_MODEL in str(exc.value)
