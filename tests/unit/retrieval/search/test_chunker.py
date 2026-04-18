"""Unit tests for the semantic chunker."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from keystone.retrieval.parse_models import EvidencePrepRecord
from keystone.retrieval.search.chunker import (
    SemanticChunker,
    count_tokens,
)


def _words(n: int, seed: str = "w") -> str:
    return " ".join(f"{seed}{i}" for i in range(n))


class TestCountTokens:
    def test_simple(self) -> None:
        assert count_tokens("hello world foo") == 3

    def test_whitespace_only(self) -> None:
        assert count_tokens("    ") == 0


class TestSemanticChunkerConstruction:
    def test_invalid_target_vs_max_rejected(self) -> None:
        with pytest.raises(ValueError):
            SemanticChunker(target_tokens=400, max_tokens=300)

    def test_overlap_must_be_less_than_target(self) -> None:
        with pytest.raises(ValueError):
            SemanticChunker(target_tokens=100, max_tokens=200, overlap_tokens=100)


class TestSemanticChunker:
    def test_respects_passage_boundaries(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(paragraph_index=0, text=_words(50)),
            make_record(paragraph_index=1, text=_words(50)),
            make_record(paragraph_index=2, text=_words(60)),
        ]
        chunker = SemanticChunker(target_tokens=100, max_tokens=200)
        chunks = chunker.chunk(records, engagement_id=None)
        # 50 + 50 = 100 hits target -> chunk 1; 60 alone -> chunk 2
        assert len(chunks) == 2
        assert chunks[0].metadata.record_ids == [records[0].record_id, records[1].record_id]
        assert chunks[1].metadata.record_ids == [records[2].record_id]

    def test_does_not_overflow_max_tokens(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(paragraph_index=0, text=_words(80)),
            make_record(paragraph_index=1, text=_words(80)),
        ]
        chunker = SemanticChunker(target_tokens=100, max_tokens=120)
        chunks = chunker.chunk(records, engagement_id=None)
        # 80 + 80 = 160 > 120 max; first passage flushes alone
        assert len(chunks) == 2

    def test_oversize_passage_is_split_with_overlap(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(paragraph_index=0, text=_words(900)),
        ]
        chunker = SemanticChunker(target_tokens=200, max_tokens=250, overlap_tokens=40)
        chunks = chunker.chunk(records, engagement_id=None)
        assert len(chunks) >= 5
        # First and second chunks share some words via overlap
        first_tail = chunks[0].raw_text.split()[-40:]
        second_head = chunks[1].raw_text.split()[:40]
        assert first_tail == second_head

    def test_contextual_preamble_is_added(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(
                paragraph_index=0,
                text="The revenue grew.",
                section_path=["Part I", "Item 1 Business"],
                page_number=3,
                title="Acme 10-K",
            )
        ]
        chunker = SemanticChunker(target_tokens=100, max_tokens=200, add_contextual_preamble=True)
        chunks = chunker.chunk(records, engagement_id=None)
        assert len(chunks) == 1
        assert "Acme 10-K" in chunks[0].content
        assert "Part I > Item 1 Business" in chunks[0].content
        assert "Page 3" in chunks[0].content
        assert chunks[0].raw_text == "The revenue grew."

    def test_preamble_off(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        records = [make_record(text="The revenue grew.", title="Acme")]
        chunker = SemanticChunker(add_contextual_preamble=False)
        chunks = chunker.chunk(records, engagement_id=None)
        assert chunks[0].content == "The revenue grew."

    def test_preamble_skipped_when_no_context(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        # Record with no title and no section path -> preamble is empty
        records = [
            make_record(
                text="Fact without context.",
                title=None,
                section_path=[],
            )
        ]
        chunker = SemanticChunker()
        chunks = chunker.chunk(records, engagement_id=None)
        assert chunks[0].content == "Fact without context."

    def test_tail_below_min_is_preserved(
        self, make_record: Callable[..., EvidencePrepRecord]
    ) -> None:
        records = [
            make_record(paragraph_index=0, text=_words(50)),
            make_record(paragraph_index=1, text=_words(5)),
        ]
        chunker = SemanticChunker(target_tokens=100, max_tokens=200, min_tokens=20)
        chunks = chunker.chunk(records, engagement_id=None)
        # One chunk (50+5=55) below target, kept because we won't drop evidence
        assert len(chunks) == 1
        assert chunks[0].token_count == 55

    def test_multi_artifact_grouping(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        records = [
            make_record(artifact_id="art-A", paragraph_index=0, text=_words(50)),
            make_record(artifact_id="art-B", paragraph_index=0, text=_words(50)),
        ]
        chunker = SemanticChunker(target_tokens=100, max_tokens=200)
        chunks = chunker.chunk(records, engagement_id=None)
        ids = {c.metadata.artifact_id for c in chunks}
        assert ids == {"art-A", "art-B"}
        for chunk in chunks:
            assert chunk.chunk_id.startswith(f"{chunk.metadata.artifact_id}:")

    def test_deterministic_chunk_ids(self, make_record: Callable[..., EvidencePrepRecord]) -> None:
        records = [make_record(paragraph_index=i, text=_words(50)) for i in range(3)]
        chunker = SemanticChunker(target_tokens=100, max_tokens=200)
        first = [c.chunk_id for c in chunker.chunk(records, engagement_id=None)]
        second = [c.chunk_id for c in chunker.chunk(records, engagement_id=None)]
        assert first == second
