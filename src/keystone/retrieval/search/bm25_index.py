"""In-process BM25 keyword index over the same chunk corpus as the vector store.

Hybrid search research consistently shows that dense embeddings alone
miss queries that turn on a specific rare term (tickers, cited statute
numbers, exact phrase matches). A lexical BM25 signal catches those
cases. Merging the two rankings via RRF gives a ~26-31% NDCG lift over
dense-only on FinMTEB-style benchmarks.

This implementation is deliberately in-process and rebuilds from the
stored corpus on each startup. For the current dataset sizes (tens of
thousands of chunks), an in-memory BM25Okapi is far cheaper than
running a separate OpenSearch cluster. When the corpus grows past
~10^6 chunks, swap the implementation behind :class:`BM25Index` without
touching callers.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from keystone.retrieval.search.models import (
    DocumentChunk,
    RetrievalResult,
    RetrievalSource,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

# Simple word tokenizer: lowercased runs of unicode word characters.
# BM25 is robust to tokenizer choice; avoiding a heavyweight tokenizer
# keeps the index build cheap.
_TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercased, punctuation-stripped tokenization for BM25."""

    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


@runtime_checkable
class BM25Index(Protocol):
    """Swappable BM25 surface."""

    async def index_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        """Replace any existing state with this corpus."""
        ...

    async def add_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        """Append ``chunks`` to the current corpus; rebuilds internal state."""
        ...

    async def search(self, query: str, *, top_k: int) -> list[RetrievalResult]:
        """Return up to ``top_k`` chunks ranked by BM25 score."""
        ...

    async def delete_by_artifact_id(self, artifact_id: str) -> int:
        """Remove every chunk for ``artifact_id``. Returns delete count."""
        ...

    def __len__(self) -> int: ...


class InMemoryBM25Index:
    """rank_bm25-backed in-memory index."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []
        self._tokenized: list[list[str]] = []
        self._bm25: object | None = None

    async def index_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        self._chunks = list(chunks)
        self._tokenized = [tokenize(chunk.content) for chunk in self._chunks]
        self._rebuild()

    async def add_chunks(self, chunks: Sequence[DocumentChunk]) -> None:
        existing_ids = {c.chunk_id for c in self._chunks}
        for chunk in chunks:
            if chunk.chunk_id in existing_ids:
                idx = next(i for i, c in enumerate(self._chunks) if c.chunk_id == chunk.chunk_id)
                self._chunks[idx] = chunk
                self._tokenized[idx] = tokenize(chunk.content)
            else:
                self._chunks.append(chunk)
                self._tokenized.append(tokenize(chunk.content))
                existing_ids.add(chunk.chunk_id)
        self._rebuild()

    async def search(self, query: str, *, top_k: int) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not self._chunks or self._bm25 is None:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)  # type: ignore[attr-defined]
        ordered = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        results: list[RetrievalResult] = []
        for rank, (idx, score) in enumerate(ordered[:top_k], start=1):
            # rank_bm25 returns floats; 0.0 scores mean no overlap and
            # we prefer to drop them so the hybrid path doesn't pad
            # with noise.
            if float(score) <= 0.0:
                break
            redacted = self._chunks[idx].model_copy(update={"embedding": None})
            results.append(
                RetrievalResult(
                    chunk=redacted,
                    score=float(score),
                    bm25_score=float(score),
                    source=RetrievalSource.BM25,
                    rank=rank,
                )
            )
        return results

    async def delete_by_artifact_id(self, artifact_id: str) -> int:
        keep: list[DocumentChunk] = []
        keep_tokens: list[list[str]] = []
        removed = 0
        for chunk, tokens in zip(self._chunks, self._tokenized, strict=True):
            if chunk.metadata.artifact_id == artifact_id:
                removed += 1
            else:
                keep.append(chunk)
                keep_tokens.append(tokens)
        self._chunks = keep
        self._tokenized = keep_tokens
        self._rebuild()
        return removed

    def __len__(self) -> int:
        return len(self._chunks)

    # --- Internal --------------------------------------------------------

    def _rebuild(self) -> None:
        if not self._tokenized:
            self._bm25 = None
            return
        try:
            from rank_bm25 import BM25Okapi
        except ImportError as exc:
            raise RuntimeError(
                "rank_bm25 is not installed; install keystone[retrieval-search]"
            ) from exc
        self._bm25 = BM25Okapi(self._tokenized)
