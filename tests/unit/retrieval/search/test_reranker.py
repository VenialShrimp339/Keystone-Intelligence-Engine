"""Unit tests for the reranker implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from keystone.retrieval.parse_models import (
    Locator,
    SourceFamily,
    confidence,
)
from keystone.retrieval.search.models import (
    ChunkMetadata,
    DocumentChunk,
    RetrievalResult,
    RetrievalSource,
)
from keystone.retrieval.search.reranker import (
    COHERE_RERANK_MODEL,
    CohereReranker,
    PassthroughReranker,
    RerankerError,
)


def _meta(artifact_id: str = "art-1") -> ChunkMetadata:
    return ChunkMetadata(
        artifact_id=artifact_id,
        canonical_url="https://example.com/doc",
        content_hash="a" * 64,
        source_family=SourceFamily.ARTICLE,
        locator=Locator(paragraph_index=0),
        parse_confidence=confidence(0.9),
    )


def _make_result(
    chunk_id: str,
    *,
    score: float = 0.5,
    rank: int = 1,
    source: RetrievalSource = RetrievalSource.HYBRID,
) -> RetrievalResult:
    chunk = DocumentChunk(
        chunk_id=chunk_id,
        content=f"content for {chunk_id}",
        raw_text=f"raw {chunk_id}",
        metadata=_meta(),
        token_count=5,
    )
    return RetrievalResult(
        chunk=chunk,
        score=score,
        rrf_score=score,
        source=source,
        rank=rank,
    )


class TestPassthroughReranker:
    async def test_preserves_order(self) -> None:
        results = [
            _make_result("art:0001", score=0.9, rank=1),
            _make_result("art:0002", score=0.8, rank=2),
            _make_result("art:0003", score=0.7, rank=3),
        ]
        reranker = PassthroughReranker()
        out = await reranker.rerank("q", results, top_k=2)
        assert len(out) == 2
        assert [r.chunk.chunk_id for r in out] == ["art:0001", "art:0002"]
        assert all(r.source is RetrievalSource.RERANKED for r in out)

    async def test_rerank_score_copies_score(self) -> None:
        results = [_make_result("art:0001", score=0.42, rank=1)]
        out = await PassthroughReranker().rerank("q", results, top_k=5)
        assert out[0].rerank_score == 0.42


# ---------------------------------------------------------------------------
# Cohere with fake client
# ---------------------------------------------------------------------------


@dataclass
class _FakeRanked:
    index: int
    relevance_score: float


@dataclass
class _FakeResponse:
    results: list[_FakeRanked]


class _FakeCohereClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.fail: bool = False
        # Default: reverse input order and drop half
        self.override_ranking: list[_FakeRanked] | None = None

    async def rerank(
        self, *, model: str, query: str, documents: list[str], top_n: int
    ) -> _FakeResponse:
        if self.fail:
            raise RuntimeError("cohere down")
        self.calls.append({"model": model, "query": query, "documents": documents, "top_n": top_n})
        if self.override_ranking is not None:
            return _FakeResponse(results=self.override_ranking[:top_n])
        # Reverse input order
        return _FakeResponse(
            results=[
                _FakeRanked(index=i, relevance_score=(len(documents) - i) / len(documents))
                for i in reversed(range(len(documents)))
            ][:top_n]
        )


class TestCohereReranker:
    def test_requires_api_key(self) -> None:
        with pytest.raises(RerankerError):
            CohereReranker(api_key="", client=_FakeCohereClient())

    def test_default_model_constant(self) -> None:
        assert COHERE_RERANK_MODEL == "rerank-v3.5"

    async def test_reorders_and_marks_source(self) -> None:
        fake = _FakeCohereClient()
        reranker = CohereReranker(api_key="k", client=fake)
        inputs = [
            _make_result("art:0001", score=0.9, rank=1),
            _make_result("art:0002", score=0.8, rank=2),
            _make_result("art:0003", score=0.7, rank=3),
        ]
        out = await reranker.rerank("test query", inputs, top_k=2)
        assert [r.chunk.chunk_id for r in out] == ["art:0003", "art:0002"]
        assert all(r.source is RetrievalSource.RERANKED for r in out)
        assert all(r.rerank_score is not None for r in out)
        # ranks are 1-based contiguous
        assert [r.rank for r in out] == [1, 2]

    async def test_upstream_failure_raises_reranker_error(self) -> None:
        fake = _FakeCohereClient()
        fake.fail = True
        reranker = CohereReranker(api_key="k", client=fake)
        with pytest.raises(RerankerError):
            await reranker.rerank("q", [_make_result("art:0001")], top_k=1)

    async def test_empty_input_returns_empty(self) -> None:
        reranker = CohereReranker(api_key="k", client=_FakeCohereClient())
        out = await reranker.rerank("q", [], top_k=5)
        assert out == []

    async def test_empty_query_rejected(self) -> None:
        reranker = CohereReranker(api_key="k", client=_FakeCohereClient())
        with pytest.raises(RerankerError):
            await reranker.rerank("   ", [_make_result("art:0001")], top_k=1)

    async def test_top_k_at_least_one(self) -> None:
        reranker = CohereReranker(api_key="k", client=_FakeCohereClient())
        with pytest.raises(ValueError):
            await reranker.rerank("q", [_make_result("art:0001")], top_k=0)

    async def test_out_of_range_index_skipped(self) -> None:
        fake = _FakeCohereClient()
        fake.override_ranking = [
            _FakeRanked(index=99, relevance_score=0.1),
            _FakeRanked(index=0, relevance_score=0.9),
        ]
        reranker = CohereReranker(api_key="k", client=fake)
        out = await reranker.rerank(
            "q", [_make_result("art:0001"), _make_result("art:0002")], top_k=2
        )
        # Out-of-range index is skipped; the valid one still shows up
        assert any(r.chunk.chunk_id == "art:0001" for r in out)

    async def test_top_n_capped_to_input_len(self) -> None:
        fake = _FakeCohereClient()
        reranker = CohereReranker(api_key="k", client=fake)
        await reranker.rerank("q", [_make_result("art:0001"), _make_result("art:0002")], top_k=50)
        assert fake.calls[-1]["top_n"] == 2
