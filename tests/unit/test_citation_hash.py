"""Tests for content hashing utilities.

Validates SHA-256 content hashing, proposition hashing,
and content verification for provenance tracking.
"""

from __future__ import annotations

from keystone.citation.hash import (
    compute_content_hash,
    compute_proposition_hash,
    verify_content_hash,
)


class TestComputeContentHash:
    def test_produces_64_char_hex(self):
        result = compute_content_hash("hello world")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_consistent_for_same_input(self):
        a = compute_content_hash("same content")
        b = compute_content_hash("same content")
        assert a == b

    def test_different_for_different_input(self):
        a = compute_content_hash("content A")
        b = compute_content_hash("content B")
        assert a != b

    def test_empty_string(self):
        result = compute_content_hash("")
        assert len(result) == 64

    def test_unicode_content(self):
        result = compute_content_hash("Acme's revenue grew 15% CAGR")
        assert len(result) == 64


class TestComputePropositionHash:
    def test_links_proposition_to_source(self):
        source_hash = compute_content_hash("source document text")
        prop_hash = compute_proposition_hash("market share is 23%", source_hash)
        assert len(prop_hash) == 64
        assert all(c in "0123456789abcdef" for c in prop_hash)

    def test_different_propositions_different_hashes(self):
        source_hash = compute_content_hash("source")
        h1 = compute_proposition_hash("claim A", source_hash)
        h2 = compute_proposition_hash("claim B", source_hash)
        assert h1 != h2

    def test_same_proposition_different_sources(self):
        src1 = compute_content_hash("source 1")
        src2 = compute_content_hash("source 2")
        h1 = compute_proposition_hash("same claim", src1)
        h2 = compute_proposition_hash("same claim", src2)
        assert h1 != h2

    def test_consistent(self):
        source_hash = compute_content_hash("source")
        a = compute_proposition_hash("claim", source_hash)
        b = compute_proposition_hash("claim", source_hash)
        assert a == b


class TestVerifyContentHash:
    def test_matching_content_returns_true(self):
        content = "the quick brown fox"
        h = compute_content_hash(content)
        assert verify_content_hash(content, h) is True

    def test_changed_content_returns_false(self):
        h = compute_content_hash("original content")
        assert verify_content_hash("modified content", h) is False

    def test_empty_content(self):
        h = compute_content_hash("")
        assert verify_content_hash("", h) is True
        assert verify_content_hash("non-empty", h) is False
