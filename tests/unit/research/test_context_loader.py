"""Tests for the JIT context loader (wiki compiled/ directory).

Validates: round 1 skip, round 2+ loading, INDEX.md parsing,
empty wiki handling, missing file graceful fallback.
"""

from __future__ import annotations

import pytest

from keystone.research.context_loader import ContextLoader


@pytest.fixture
def wiki_dir(tmp_path):
    """Create a wiki directory structure with compiled entries and INDEX.md."""
    compiled = tmp_path / "compiled"
    compiled.mkdir()

    # Two compiled wiki entries
    (compiled / "market_size.md").write_text("# Market Size\nTAM is $50B.")
    (compiled / "competitors.md").write_text("# Competitors\n3 major players.")

    # INDEX.md with links to both
    index = tmp_path / "INDEX.md"
    index.write_text(
        "# Wiki Index\n\n"
        "- [Market Size](compiled/market_size.md)\n"
        "- [Competitors](compiled/competitors.md)\n"
    )

    return tmp_path


@pytest.fixture
def empty_wiki_dir(tmp_path):
    """Wiki directory with no compiled entries and no INDEX.md."""
    compiled = tmp_path / "compiled"
    compiled.mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# Round 1 vs Round 2+
# ---------------------------------------------------------------------------


class TestRoundBehavior:
    @pytest.mark.asyncio
    async def test_round_1_returns_empty(self, wiki_dir) -> None:
        """Round 1 has no prior context -- should return empty list."""
        loader = ContextLoader(wiki_dir)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_round_0_returns_empty(self, wiki_dir) -> None:
        """Round 0 (edge case) also returns empty."""
        loader = ContextLoader(wiki_dir)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=0)
        assert result == []

    @pytest.mark.asyncio
    async def test_round_2_loads_context(self, wiki_dir) -> None:
        """Round 2+ loads all compiled wiki entries."""
        loader = ContextLoader(wiki_dir)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=2)
        assert len(result) == 2
        assert any("Market Size" in entry for entry in result)
        assert any("Competitors" in entry for entry in result)

    @pytest.mark.asyncio
    async def test_round_3_loads_context(self, wiki_dir) -> None:
        """Round 3 also loads context (not just round 2)."""
        loader = ContextLoader(wiki_dir)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=3)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# INDEX.md navigation
# ---------------------------------------------------------------------------


class TestIndexParsing:
    def test_parse_index_extracts_entries(self, wiki_dir) -> None:
        loader = ContextLoader(wiki_dir)
        entries = loader._parse_index()
        assert len(entries) == 2
        assert entries[0] == {"title": "Market Size", "path": "compiled/market_size.md"}
        assert entries[1] == {"title": "Competitors", "path": "compiled/competitors.md"}

    def test_parse_index_skips_non_link_lines(self, tmp_path) -> None:
        """Lines that aren't markdown links are ignored."""
        index = tmp_path / "INDEX.md"
        index.write_text(
            "# Index\n\nSome plain text\n- [Valid Link](file.md)\n- Not a link\n- [Broken\n"
        )
        loader = ContextLoader(tmp_path)
        entries = loader._parse_index()
        assert len(entries) == 1
        assert entries[0]["title"] == "Valid Link"

    def test_parse_index_missing_file_returns_empty(self, tmp_path) -> None:
        """No INDEX.md at all returns empty list."""
        loader = ContextLoader(tmp_path)
        entries = loader._parse_index()
        assert entries == []


# ---------------------------------------------------------------------------
# Empty wiki handling
# ---------------------------------------------------------------------------


class TestEmptyWiki:
    @pytest.mark.asyncio
    async def test_empty_wiki_round_2_returns_empty(self, empty_wiki_dir) -> None:
        """Round 2 with no INDEX.md gracefully returns empty."""
        loader = ContextLoader(empty_wiki_dir)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=2)
        assert result == []

    @pytest.mark.asyncio
    async def test_index_exists_but_no_entries(self, tmp_path) -> None:
        """INDEX.md exists but has no links."""
        compiled = tmp_path / "compiled"
        compiled.mkdir()
        index = tmp_path / "INDEX.md"
        index.write_text("# Wiki Index\n\nNo entries yet.\n")

        loader = ContextLoader(tmp_path)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=2)
        assert result == []


# ---------------------------------------------------------------------------
# File not found handling
# ---------------------------------------------------------------------------


class TestFileNotFound:
    @pytest.mark.asyncio
    async def test_missing_compiled_file_skipped(self, tmp_path) -> None:
        """INDEX.md references a file that doesn't exist -- skip it gracefully."""
        compiled = tmp_path / "compiled"
        compiled.mkdir()
        (compiled / "exists.md").write_text("# Exists\nReal content.")

        index = tmp_path / "INDEX.md"
        index.write_text("- [Exists](compiled/exists.md)\n- [Ghost](compiled/ghost.md)\n")

        loader = ContextLoader(tmp_path)
        result = await loader.load_context("ENG-001", "TASK-001", round_number=2)
        assert len(result) == 1
        assert "Real content" in result[0]

    def test_load_entry_checks_both_bases(self, tmp_path) -> None:
        """_load_entry checks wiki_dir and compiled/ for the path."""
        compiled = tmp_path / "compiled"
        compiled.mkdir()
        # File at wiki root (not in compiled/)
        (tmp_path / "root_file.md").write_text("Root content")

        loader = ContextLoader(tmp_path)
        result = loader._load_entry("root_file.md")
        assert result == "Root content"

    def test_load_entry_returns_none_for_missing(self, tmp_path) -> None:
        compiled = tmp_path / "compiled"
        compiled.mkdir()

        loader = ContextLoader(tmp_path)
        result = loader._load_entry("nonexistent.md")
        assert result is None
