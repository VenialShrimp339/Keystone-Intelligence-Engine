"""Unit tests for the BM25 index."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.bm25_index import InMemoryBM25Index, tokenize
from keystone.retrieval.search.chunker import SemanticChunker


class TestTokenize:
    def test_lowercases(self) -> None:
        assert tokenize("Hello WORLD") == ["hello", "world"]

    def test_splits_on_punctuation(self) -> None:
        assert tokenize("foo, bar. baz!") == ["foo", "bar", "baz"]

    def test_empty(self) -> None:
        assert tokenize("  ") == []


class TestInMemoryBM25Index:
    @pytest.fixture
    def chunker(self) -> SemanticChunker:
        return SemanticChunker(
            target_tokens=80,
            max_tokens=120,
            overlap_tokens=16,
            add_contextual_preamble=False,
        )

    @pytest.fixture
    def sample_chunks(
        self,
        make_record: Callable[..., EvidencePrepRecord],
        chunker: SemanticChunker,
    ):
        records = [
            make_record(
                artifact_id="art-A",
                paragraph_index=0,
                text="Microsoft reported strong cloud growth in fiscal 2024.",
            ),
            make_record(
                artifact_id="art-B",
                paragraph_index=0,
                text="Apple's iPhone sales decreased in the latest quarter.",
            ),
            make_record(
                artifact_id="art-C",
                paragraph_index=0,
                text="Oil prices rose on OPEC production cuts.",
            ),
        ]
        return chunker.chunk(records, engagement_id=None)

    async def test_index_and_search(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        results = await index.search("iphone sales", top_k=3)
        assert len(results) >= 1
        assert results[0].chunk.metadata.artifact_id == "art-B"
        assert results[0].source.value == "bm25"
        assert results[0].bm25_score is not None
        assert results[0].bm25_score > 0

    async def test_search_respects_top_k(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        results = await index.search("the", top_k=1)
        assert len(results) <= 1

    async def test_empty_index_returns_empty(self) -> None:
        index = InMemoryBM25Index()
        results = await index.search("anything", top_k=5)
        assert results == []

    async def test_zero_token_query_returns_empty(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        results = await index.search("   ", top_k=5)
        assert results == []

    async def test_zero_score_dropped(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        results = await index.search("zzzzzz", top_k=5)
        # No chunk contains 'zzzzzz' so BM25 returns no results
        assert results == []

    async def test_add_chunks_appends(
        self,
        make_record: Callable[..., EvidencePrepRecord],
        chunker: SemanticChunker,
    ) -> None:
        records_a = [make_record(artifact_id="art-A", paragraph_index=0, text="hello world")]
        records_b = [make_record(artifact_id="art-B", paragraph_index=0, text="foo bar baz")]
        index = InMemoryBM25Index()
        await index.index_chunks(chunker.chunk(records_a, engagement_id=None))
        assert len(index) == 1
        await index.add_chunks(chunker.chunk(records_b, engagement_id=None))
        assert len(index) == 2

    async def test_add_chunks_replaces_same_id(
        self,
        make_record: Callable[..., EvidencePrepRecord],
        chunker: SemanticChunker,
    ) -> None:
        first = chunker.chunk(
            [
                make_record(
                    artifact_id="art-A",
                    paragraph_index=0,
                    text="Microsoft reported cloud growth.",
                )
            ],
            engagement_id=None,
        )
        second = chunker.chunk(
            [
                make_record(
                    artifact_id="art-A",
                    paragraph_index=0,
                    text="Apple discussed iPhone sales.",
                )
            ],
            engagement_id=None,
        )
        # Padding corpus so BM25 IDF is positive (BM25 collapses to 0 for
        # single-doc matches on tiny corpora).
        padding = chunker.chunk(
            [
                make_record(
                    artifact_id=f"pad-{i}",
                    paragraph_index=0,
                    text=f"Background prose number {i} for corpus padding.",
                )
                for i in range(5)
            ],
            engagement_id=None,
        )
        assert first[0].chunk_id == second[0].chunk_id
        index = InMemoryBM25Index()
        await index.index_chunks(first + padding)
        await index.add_chunks(second)
        assert len(index) == 1 + len(padding)
        iphone = await index.search("iPhone", top_k=5)
        assert iphone and iphone[0].chunk.metadata.artifact_id == "art-A"
        # Searching for the replaced text ('Microsoft') must not surface art-A
        microsoft = await index.search("Microsoft", top_k=5)
        assert all(r.chunk.metadata.artifact_id != "art-A" for r in microsoft)

    async def test_delete_by_artifact_id(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        before = len(index)
        removed = await index.delete_by_artifact_id("art-B")
        assert removed >= 1
        assert len(index) == before - removed

    async def test_delete_rebuilds_state(self, sample_chunks: list) -> None:
        index = InMemoryBM25Index()
        await index.index_chunks(sample_chunks)
        await index.delete_by_artifact_id("art-A")
        results = await index.search("microsoft", top_k=3)
        # art-A was the only document mentioning Microsoft -> no results
        ids = {r.chunk.metadata.artifact_id for r in results}
        assert "art-A" not in ids
