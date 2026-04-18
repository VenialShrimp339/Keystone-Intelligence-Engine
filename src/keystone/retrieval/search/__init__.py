"""Retrieval search: pgvector + BM25 + RRF + Cohere rerank.

This sub-package is the semantic-search half of the retrieval system.
Lane H fetches documents, Lane E parses them into EvidencePrepRecords,
and this package takes those records and makes them searchable by
meaning (dense embeddings) and by lexical match (BM25) simultaneously.

The RetrievalService is the orchestration entry point; the MCP gateway
exposes it to agents via the ``semantic_search`` and ``hybrid_search``
system-owned tools.
"""

from __future__ import annotations

from keystone.retrieval.search.bm25_index import (
    BM25Index,
    InMemoryBM25Index,
    tokenize,
)
from keystone.retrieval.search.chunker import SemanticChunker, count_tokens
from keystone.retrieval.search.embeddings import (
    VOYAGE_FINANCE_DIM,
    VOYAGE_FINANCE_MODEL,
    EmbeddingClient,
    EmbeddingDimensionError,
    EmbeddingError,
    InMemoryEmbeddingClient,
    VoyageEmbeddingClient,
)
from keystone.retrieval.search.factory import (
    RetrievalFactoryError,
    build_retrieval_service,
)
from keystone.retrieval.search.hybrid_search import (
    DEFAULT_RRF_K,
    HybridSearchConfig,
    HybridSearcher,
)
from keystone.retrieval.search.models import (
    ChunkMetadata,
    DocumentChunk,
    IngestResult,
    QueryClassification,
    QueryRoute,
    RetrievalResult,
    RetrievalSource,
    SearchQuery,
)
from keystone.retrieval.search.query_router import (
    QueryRouter,
    RuleBasedQueryRouter,
)
from keystone.retrieval.search.reranker import (
    COHERE_RERANK_MODEL,
    CohereReranker,
    PassthroughReranker,
    RerankerClient,
    RerankerError,
)
from keystone.retrieval.search.retrieval_service import RetrievalService
from keystone.retrieval.search.vector_store import (
    InMemoryVectorStore,
    PgVectorStore,
    VectorStore,
    VectorStoreError,
)

__all__ = [
    "BM25Index",
    "COHERE_RERANK_MODEL",
    "ChunkMetadata",
    "CohereReranker",
    "DEFAULT_RRF_K",
    "DocumentChunk",
    "EmbeddingClient",
    "EmbeddingDimensionError",
    "EmbeddingError",
    "HybridSearchConfig",
    "HybridSearcher",
    "InMemoryBM25Index",
    "InMemoryEmbeddingClient",
    "InMemoryVectorStore",
    "IngestResult",
    "PassthroughReranker",
    "PgVectorStore",
    "QueryClassification",
    "QueryRoute",
    "QueryRouter",
    "RerankerClient",
    "RerankerError",
    "RetrievalFactoryError",
    "RetrievalResult",
    "RetrievalService",
    "RetrievalSource",
    "RuleBasedQueryRouter",
    "SearchQuery",
    "SemanticChunker",
    "VOYAGE_FINANCE_DIM",
    "VOYAGE_FINANCE_MODEL",
    "VectorStore",
    "VectorStoreError",
    "VoyageEmbeddingClient",
    "build_retrieval_service",
    "count_tokens",
    "tokenize",
]
