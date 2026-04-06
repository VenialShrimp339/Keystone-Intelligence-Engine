"""Tests for WikiEntry model and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from keystone.citation.hash import compute_content_hash
from keystone.knowledge.wiki_schema import WikiEntry


class TestWikiEntry:
    def _make_entry(self, **overrides) -> WikiEntry:
        content = overrides.pop("content", "# Test Topic\n\nSome content here.")
        defaults = {
            "path": "compiled/test_topic.md",
            "engagement_id": "ENG-001",
            "client_id": "CLIENT-001",
            "content": content,
            "content_hash": compute_content_hash(content),
            "proposition_hashes": [],
            "source_artifacts": ["raw/1_agent1_task1.md"],
            "round_added": 1,
            "indexed": False,
        }
        defaults.update(overrides)
        return WikiEntry(**defaults)

    def test_validates_with_all_required_fields(self):
        entry = self._make_entry()
        assert entry.engagement_id == "ENG-001"
        assert entry.client_id == "CLIENT-001"
        assert entry.path == "compiled/test_topic.md"
        assert entry.round_added == 1
        assert entry.indexed is False

    def test_content_hash_is_64_char_hex(self):
        entry = self._make_entry()
        assert len(entry.content_hash) == 64
        assert all(c in "0123456789abcdef" for c in entry.content_hash)

    def test_content_hash_matches_content(self):
        content = "# Market Analysis\n\nKey findings about the market."
        entry = self._make_entry(content=content)
        assert entry.content_hash == compute_content_hash(content)

    def test_rejects_invalid_content_hash(self):
        with pytest.raises(ValidationError, match="content_hash"):
            self._make_entry(content_hash="not-a-valid-hash")

    def test_rejects_short_content_hash(self):
        with pytest.raises(ValidationError, match="content_hash"):
            self._make_entry(content_hash="abcdef1234")

    def test_proposition_hashes_validated(self):
        source_hash = compute_content_hash("raw artifact text")
        from keystone.citation.hash import compute_proposition_hash

        prop_hash = compute_proposition_hash("market share is 23%", source_hash)
        entry = self._make_entry(proposition_hashes=[prop_hash])
        assert len(entry.proposition_hashes) == 1
        assert len(entry.proposition_hashes[0]) == 64

    def test_rejects_invalid_proposition_hash(self):
        with pytest.raises(ValidationError, match="proposition hash"):
            self._make_entry(proposition_hashes=["bad-hash"])

    def test_multiple_proposition_hashes(self):
        from keystone.citation.hash import compute_proposition_hash

        source_hash = compute_content_hash("source")
        hashes = [
            compute_proposition_hash("claim A", source_hash),
            compute_proposition_hash("claim B", source_hash),
        ]
        entry = self._make_entry(proposition_hashes=hashes)
        assert len(entry.proposition_hashes) == 2

    def test_empty_proposition_hashes_allowed(self):
        entry = self._make_entry(proposition_hashes=[])
        assert entry.proposition_hashes == []

    def test_frozen_model(self):
        entry = self._make_entry()
        with pytest.raises(ValidationError):
            entry.content = "modified"

    def test_source_artifacts_list(self):
        entry = self._make_entry(
            source_artifacts=["raw/1_agent1_task1.md", "raw/1_agent2_task2.md"]
        )
        assert len(entry.source_artifacts) == 2
