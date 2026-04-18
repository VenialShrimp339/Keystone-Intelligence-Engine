"""Unit tests for retrieval/search/models.py."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from keystone.retrieval.parse_models import (
    Locator,
    ParseConfidenceTier,
    SourceFamily,
    confidence,
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


def _meta(**overrides: object) -> ChunkMetadata:
    defaults: dict[str, object] = {
        "artifact_id": "art-1",
        "canonical_url": "https://example.com/doc",
        "content_hash": "a" * 64,
        "source_family": SourceFamily.ARTICLE,
        "locator": Locator(paragraph_index=0),
        "parse_confidence": confidence(0.9),
    }
    defaults.update(overrides)
    return ChunkMetadata(**defaults)  # type: ignore[arg-type]


class TestChunkMetadata:
    def test_happy_path(self) -> None:
        meta = _meta(title="Doc Title")
        assert meta.title == "Doc Title"
        assert meta.parse_confidence.tier is ParseConfidenceTier.HIGH

    def test_bad_content_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _meta(content_hash="not-a-hex")

    def test_frozen(self) -> None:
        meta = _meta()
        with pytest.raises(ValidationError):
            meta.artifact_id = "other"  # type: ignore[misc]


class TestDocumentChunk:
    def test_happy_path(self) -> None:
        chunk = DocumentChunk(
            chunk_id="art-1:0000",
            content="hello",
            raw_text="hello",
            metadata=_meta(),
            token_count=5,
        )
        assert chunk.embedding is None

    def test_chunk_id_format_enforced(self) -> None:
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id="",
                content="hello",
                raw_text="hello",
                metadata=_meta(),
                token_count=1,
            )

    def test_rejects_whitespace_text(self) -> None:
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id="art-1:0000",
                content="   ",
                raw_text="hello",
                metadata=_meta(),
                token_count=1,
            )

    def test_rejects_non_finite_embedding(self) -> None:
        with pytest.raises(ValidationError):
            DocumentChunk(
                chunk_id="art-1:0000",
                content="hello",
                raw_text="hello",
                metadata=_meta(),
                token_count=1,
                embedding=[1.0, math.inf, 0.5],
            )

    def test_with_embedding_returns_new_instance(self) -> None:
        chunk = DocumentChunk(
            chunk_id="art-1:0000",
            content="hello",
            raw_text="hello",
            metadata=_meta(),
            token_count=1,
        )
        embedded = chunk.with_embedding([0.1, 0.2, 0.3])
        assert embedded.embedding == [0.1, 0.2, 0.3]
        assert chunk.embedding is None
        assert embedded is not chunk


class TestSearchQuery:
    def test_defaults(self) -> None:
        q = SearchQuery(text="hello")
        assert q.top_k == 20
        assert q.candidate_pool == 150

    def test_candidate_pool_must_ge_top_k(self) -> None:
        with pytest.raises(ValidationError):
            SearchQuery(text="hello", top_k=50, candidate_pool=10)

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            SearchQuery(text="   ")


class TestRetrievalResult:
    def test_hybrid_score_round_trip(self) -> None:
        chunk = DocumentChunk(
            chunk_id="art-1:0000",
            content="hello",
            raw_text="hello",
            metadata=_meta(),
            token_count=1,
        )
        res = RetrievalResult(
            chunk=chunk,
            score=0.9,
            vector_score=0.8,
            bm25_score=2.5,
            rrf_score=0.9,
            source=RetrievalSource.HYBRID,
            rank=1,
        )
        assert res.source is RetrievalSource.HYBRID
        assert res.score == 0.9
        assert res.bm25_score == 2.5


class TestQueryRoute:
    def test_happy_path(self) -> None:
        r = QueryRoute(
            classification=QueryClassification.HYBRID,
            confidence=0.9,
            reason="mixed",
            signals=["percent", "explanatory"],
        )
        assert r.classification is QueryClassification.HYBRID

    def test_confidence_bounds(self) -> None:
        with pytest.raises(ValidationError):
            QueryRoute(
                classification=QueryClassification.QUALITATIVE,
                confidence=2.0,
                reason="too high",
            )


class TestIngestResult:
    def test_negative_counts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IngestResult(
                artifacts_ingested=-1,
                chunks_created=0,
                chunks_updated=0,
                chunks_skipped=0,
            )

    def test_happy_path(self) -> None:
        r = IngestResult(
            artifacts_ingested=3,
            chunks_created=10,
            chunks_updated=2,
            chunks_skipped=1,
        )
        assert r.chunks_created == 10
