"""Embedding clients for the retrieval stack.

Defines the :class:`EmbeddingClient` Protocol plus two implementations:

- :class:`VoyageEmbeddingClient` calls the Voyage AI API using the
  ``voyage-finance-2`` model (1024-dim by default). Voyage's
  finance-tuned model materially outperforms general-purpose
  embeddings on financial retrieval benchmarks (FinMTEB). The client
  batches internally at Voyage's 128-item limit and re-raises as
  :class:`EmbeddingError` when the upstream is down so callers can
  degrade cleanly (return fewer results, skip vector search, etc.)
  rather than crash mid-pipeline.
- :class:`InMemoryEmbeddingClient` produces deterministic fixed-size
  vectors from a SHA-256 hash of the input, so tests never need to hit
  the network.

Both implementations validate output dimensionality and raise when the
upstream returns unexpected shapes -- silent dimension drift corrupts
the pgvector index.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import struct
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

logger = logging.getLogger(__name__)

# Voyage's public batch limit for the embeddings endpoint.
VOYAGE_MAX_BATCH = 128
VOYAGE_FINANCE_MODEL = "voyage-finance-2"
VOYAGE_FINANCE_DIM = 1024


class EmbeddingError(RuntimeError):
    """Raised when an embedding call fails in a way the caller should handle.

    Wraps transport errors (network, timeout, auth, quota) so the
    retrieval service can decide whether to skip vector search and fall
    back to BM25-only, rather than propagating a provider-specific
    exception up the stack.
    """


class EmbeddingDimensionError(EmbeddingError):
    """Raised when a returned vector has a dimension different from expected."""


@runtime_checkable
class EmbeddingClient(Protocol):
    """Swappable embedding surface.

    All embedding calls are async so a single client can batch concurrent
    requests without blocking the orchestrator's event loop.
    """

    model: str
    dimension: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in order.

        Implementations must preserve input order and validate the output
        dimension against ``self.dimension``. On upstream failure, raise
        :class:`EmbeddingError` (or a subclass) -- do not return
        placeholder zeros.
        """
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string.

        Voyage (and most providers) expose a separate ``query`` input
        type so queries can be projected differently from documents.
        Implementations that don't distinguish should delegate to
        :meth:`embed` with a one-element list.
        """
        ...


# ---------------------------------------------------------------------------
# Voyage
# ---------------------------------------------------------------------------


class VoyageEmbeddingClient:
    """Voyage AI embedding client.

    Uses the official ``voyageai`` SDK. The SDK exposes a synchronous
    ``embed`` method that handles HTTP + retries; we wrap it in
    :func:`asyncio.to_thread` so the async surface does not block the
    event loop.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = VOYAGE_FINANCE_MODEL,
        dimension: int = VOYAGE_FINANCE_DIM,
        batch_size: int = VOYAGE_MAX_BATCH,
        client: Any = None,
    ) -> None:
        if not api_key:
            raise EmbeddingError("VoyageEmbeddingClient requires a non-empty api_key")
        if batch_size < 1 or batch_size > VOYAGE_MAX_BATCH:
            raise ValueError(
                f"batch_size must be between 1 and {VOYAGE_MAX_BATCH}; got {batch_size}"
            )
        self.model = model
        self.dimension = dimension
        self.batch_size = batch_size
        self._client = client if client is not None else self._build_default_client(api_key)

    @staticmethod
    def _build_default_client(api_key: str) -> Any:
        try:
            import voyageai
        except ImportError as exc:
            raise EmbeddingError(
                "voyageai is not installed; install keystone[retrieval-search] to use "
                "VoyageEmbeddingClient"
            ) from exc
        # voyageai re-exports Client but doesn't mark it __all__; cast through Any
        # so mypy's attr-defined check stays happy.
        voyage_mod: Any = voyageai
        return voyage_mod.Client(api_key=api_key)

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        for batch in _chunked(list(texts), self.batch_size):
            vectors = await asyncio.to_thread(self._embed_sync, batch, "document")
            out.extend(vectors)
        return out

    async def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingError("embed_query called with empty text")
        vectors = await asyncio.to_thread(self._embed_sync, [text], "query")
        return vectors[0]

    def _embed_sync(self, batch: list[str], input_type: str) -> list[list[float]]:
        try:
            result = self._client.embed(batch, model=self.model, input_type=input_type)
        except Exception as exc:
            logger.exception("voyage embed failed (model=%s, n=%d)", self.model, len(batch))
            raise EmbeddingError(f"voyage embed failed: {exc}") from exc
        vectors = getattr(result, "embeddings", None)
        if vectors is None or len(vectors) != len(batch):
            raise EmbeddingError(
                f"voyage returned {0 if vectors is None else len(vectors)} vectors "
                f"for {len(batch)} inputs"
            )
        validated: list[list[float]] = []
        for i, vec in enumerate(vectors):
            values = [float(v) for v in vec]
            if len(values) != self.dimension:
                raise EmbeddingDimensionError(
                    f"voyage returned {len(values)}-dim vector at index {i}; "
                    f"expected {self.dimension}"
                )
            for j, value in enumerate(values):
                if not math.isfinite(value):
                    raise EmbeddingError(
                        f"voyage returned non-finite value at batch[{i}][{j}]: {value!r}"
                    )
            validated.append(values)
        return validated


# ---------------------------------------------------------------------------
# In-memory test client
# ---------------------------------------------------------------------------


class InMemoryEmbeddingClient:
    """Deterministic embeddings derived from SHA-256 of the input.

    For the same text the client produces the same vector across process
    restarts, which makes test assertions stable. The vector is projected
    onto the unit sphere so cosine-similarity math in tests behaves like
    a real embedder.
    """

    def __init__(self, dimension: int = 16, model: str = "inmemory-sha256") -> None:
        if dimension < 2:
            raise ValueError("InMemoryEmbeddingClient dimension must be >= 2")
        self.model = model
        self.dimension = dimension

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingError("embed_query called with empty text")
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        if not text:
            raise EmbeddingError("cannot embed empty string")
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Stretch digest to cover dimension*4 bytes by re-hashing with counter
        buf = bytearray()
        counter = 0
        while len(buf) < self.dimension * 4:
            buf.extend(hashlib.sha256(digest + counter.to_bytes(4, "big")).digest())
            counter += 1
        floats = [
            struct.unpack(">i", bytes(buf[i * 4 : (i + 1) * 4]))[0] / 2**31
            for i in range(self.dimension)
        ]
        norm = math.sqrt(sum(v * v for v in floats))
        if norm == 0.0:  # pragma: no cover -- near-impossible for SHA-256
            return [1.0 / math.sqrt(self.dimension)] * self.dimension
        return [v / norm for v in floats]


def _chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
