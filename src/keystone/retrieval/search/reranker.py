"""Cross-encoder reranker.

The hybrid search path produces a ranked list of 50-150 candidates;
Cohere Rerank v3.5 re-scores the top-k by running each query/document
pair through a cross-encoder. That lifts nDCG another ~5-15% on top of
RRF fusion because the cross-encoder can attend to query and document
tokens jointly, unlike bi-encoders.

The reranker is a soft dependency: when Cohere is unavailable (network
down, quota exceeded, SDK missing) the retrieval service falls back to
the unranked RRF list. That keeps the stack live at degraded quality
rather than failing hard.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from keystone.retrieval.search.models import (
    RetrievalResult,
    RetrievalSource,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

COHERE_RERANK_MODEL = "rerank-v3.5"


class RerankerError(RuntimeError):
    """Raised when reranking fails in a way the caller should handle."""


@runtime_checkable
class RerankerClient(Protocol):
    """Swappable reranker surface."""

    async def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        """Return a reranked slice of at most ``top_k`` results.

        Implementations must preserve the ``chunk`` identity of each
        returned result (same chunk_id, content, metadata) -- only
        ``score`` / ``rerank_score`` / ``rank`` / ``source`` may change.
        """
        ...


# ---------------------------------------------------------------------------
# Cohere
# ---------------------------------------------------------------------------


class CohereReranker:
    """Cohere Rerank v3.5 cross-encoder reranker.

    Uses the async ``cohere.AsyncClientV2``. On upstream failure the
    reranker raises :class:`RerankerError` and expects the caller
    (the retrieval service) to fall back to the pre-rerank list.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = COHERE_RERANK_MODEL,
        client: Any = None,
    ) -> None:
        if not api_key:
            raise RerankerError("CohereReranker requires a non-empty api_key")
        self._api_key = api_key
        self.model = model
        self._client = client if client is not None else self._build_default_client(api_key)

    @staticmethod
    def _build_default_client(api_key: str) -> Any:
        try:
            import cohere
        except ImportError as exc:
            raise RerankerError(
                "cohere is not installed; install keystone[retrieval-search]"
            ) from exc
        return cohere.AsyncClientV2(api_key=api_key)

    async def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        if not results:
            return []
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not query.strip():
            raise RerankerError("rerank called with empty query")
        documents = [result.chunk.content for result in results]
        try:
            response = await self._client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_k, len(documents)),
            )
        except Exception as exc:
            logger.exception("cohere rerank failed (model=%s, n=%d)", self.model, len(documents))
            raise RerankerError(f"cohere rerank failed: {exc}") from exc

        out: list[RetrievalResult] = []
        for rank, ranked in enumerate(getattr(response, "results", []) or [], start=1):
            index = int(ranked.index)
            if index < 0 or index >= len(results):
                logger.warning("cohere returned out-of-range index: %s", index)
                continue
            score = float(ranked.relevance_score)
            base = results[index]
            out.append(
                RetrievalResult(
                    chunk=base.chunk,
                    score=score,
                    vector_score=base.vector_score,
                    bm25_score=base.bm25_score,
                    rrf_score=base.rrf_score,
                    rerank_score=score,
                    source=RetrievalSource.RERANKED,
                    rank=rank,
                )
            )
        return out


# ---------------------------------------------------------------------------
# Passthrough test double
# ---------------------------------------------------------------------------


class PassthroughReranker:
    """No-op reranker useful for tests and for the graceful-degradation path.

    Returns the input results sliced to ``top_k`` with their rank
    recomputed. ``rerank_score`` copies whichever score the result is
    already carrying so downstream consumers can still read the field.
    """

    model = "passthrough"

    async def rerank(
        self,
        query: str,
        results: Sequence[RetrievalResult],
        *,
        top_k: int,
    ) -> list[RetrievalResult]:
        await asyncio.sleep(0)  # stay cooperative under event loop
        out: list[RetrievalResult] = []
        for rank, base in enumerate(results[:top_k], start=1):
            out.append(
                RetrievalResult(
                    chunk=base.chunk,
                    score=base.score,
                    vector_score=base.vector_score,
                    bm25_score=base.bm25_score,
                    rrf_score=base.rrf_score,
                    rerank_score=base.score,
                    source=RetrievalSource.RERANKED,
                    rank=rank,
                )
            )
        return out
