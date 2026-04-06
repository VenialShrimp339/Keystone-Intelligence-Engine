"""Tests for ContentHasher wiki-specific provenance logic."""

from __future__ import annotations

from keystone.citation.hash import compute_content_hash, compute_proposition_hash
from keystone.knowledge.content_hasher import ContentHasher
from keystone.knowledge.wiki_schema import WikiEntry


class TestContentHasher:
    def setup_method(self):
        self.hasher = ContentHasher()

    def test_proposition_hash_matches_citation_hash_output(self):
        source_hash = compute_content_hash("raw artifact text")
        expected = compute_proposition_hash("market share is 23%", source_hash)
        result = self.hasher.hash_proposition("market share is 23%", source_hash)
        assert result == expected

    def test_proposition_hash_is_64_char_hex(self):
        source_hash = compute_content_hash("source")
        result = self.hasher.hash_proposition("claim text", source_hash)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_content_hash_matches_citation_hash_output(self):
        text = "Some compiled markdown content"
        expected = compute_content_hash(text)
        result = self.hasher.hash_content(text)
        assert result == expected

    def test_content_hash_is_64_char_hex(self):
        result = self.hasher.hash_content("test content")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_provenance_valid_chain_passes(self):
        raw_text = "This is the raw research artifact with findings."
        content = "# Compiled\n\nSynthesized findings from research."
        content_hash = compute_content_hash(content)
        source_hash = compute_content_hash(raw_text)
        prop_hash = compute_proposition_hash("key finding", source_hash)

        entry = WikiEntry(
            path="compiled/test.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=content_hash,
            proposition_hashes=[prop_hash],
            source_artifacts=["raw/1_agent1_task1.md"],
            round_added=1,
        )
        assert self.hasher.verify_provenance(entry, [raw_text]) is True

    def test_provenance_broken_chain_wrong_content_hash(self):
        raw_text = "raw artifact"
        content = "# Compiled Topic\n\nSome content."
        # Deliberately use wrong content hash
        wrong_hash = compute_content_hash("different content entirely")

        entry = WikiEntry(
            path="compiled/test.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=wrong_hash,
            proposition_hashes=[],
            source_artifacts=["raw/1_agent1_task1.md"],
            round_added=1,
        )
        assert self.hasher.verify_provenance(entry, [raw_text]) is False

    def test_provenance_broken_chain_no_source_artifacts(self):
        content = "# Topic\n\nContent."
        entry = WikiEntry(
            path="compiled/test.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=compute_content_hash(content),
            proposition_hashes=[],
            source_artifacts=[],
            round_added=1,
        )
        assert self.hasher.verify_provenance(entry, ["raw text"]) is False

    def test_provenance_broken_chain_no_raw_artifacts(self):
        content = "# Topic\n\nContent."
        entry = WikiEntry(
            path="compiled/test.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=compute_content_hash(content),
            proposition_hashes=[],
            source_artifacts=["raw/1_a_t.md"],
            round_added=1,
        )
        assert self.hasher.verify_provenance(entry, []) is False
