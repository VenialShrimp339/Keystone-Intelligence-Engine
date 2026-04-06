"""Tests for IndexMaintainer auto-maintenance of INDEX.md."""

from __future__ import annotations

from keystone.citation.hash import compute_content_hash
from keystone.knowledge.index_maintainer import IndexMaintainer
from keystone.knowledge.wiki_schema import WikiEntry


class FakeStore:
    """In-memory WikiStore for testing IndexMaintainer."""

    def __init__(self):
        self.entries: list[WikiEntry] = []
        self.index_content: str = ""

    async def list_compiled(self, engagement_id: str) -> list[WikiEntry]:
        return [e for e in self.entries if e.engagement_id == engagement_id]

    async def write_index(self, engagement_id: str, content: str) -> None:
        self.index_content = content


def _make_entry(
    topic: str, round_added: int, engagement_id: str = "ENG-001"
) -> WikiEntry:
    content = f"# {topic.replace('_', ' ').title()}\n\nFindings about {topic}."
    return WikiEntry(
        path=f"compiled/{topic}.md",
        engagement_id=engagement_id,
        client_id="CLIENT-001",
        content=content,
        content_hash=compute_content_hash(content),
        proposition_hashes=[],
        source_artifacts=[f"raw/1_agent1_{topic}.md"],
        round_added=round_added,
    )


class TestIndexMaintainer:
    async def test_generates_correct_format(self):
        store = FakeStore()
        store.entries = [_make_entry("market_analysis", 1)]
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        assert "# ENG-001 -- Research Wiki" in store.index_content
        assert "## Topics" in store.index_content
        assert "## Coverage" in store.index_content
        assert "Market Analysis" in store.index_content

    async def test_multiple_topics_listed_alphabetically(self):
        store = FakeStore()
        store.entries = [
            _make_entry("zebra_analysis", 1),
            _make_entry("alpha_research", 1),
            _make_entry("middle_topic", 2),
        ]
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        lines = store.index_content.splitlines()
        topic_lines = [l for l in lines if l.startswith("- [")]
        assert len(topic_lines) == 3
        # Alphabetical order by path
        assert "alpha_research" in topic_lines[0]
        assert "middle_topic" in topic_lines[1]
        assert "zebra_analysis" in topic_lines[2]

    async def test_round_numbers_tracked(self):
        store = FakeStore()
        store.entries = [
            _make_entry("topic_a", 1),
            _make_entry("topic_b", 3),
        ]
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        assert "(Round 1)" in store.index_content
        assert "(Round 3)" in store.index_content

    async def test_coverage_stats_accurate(self):
        store = FakeStore()
        store.entries = [
            _make_entry("topic_a", 1),
            _make_entry("topic_b", 1),
            _make_entry("topic_c", 2),
        ]
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        assert "Total topics: 3" in store.index_content
        assert "Rounds completed: 2" in store.index_content

    async def test_empty_entries(self):
        store = FakeStore()
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        assert "No compiled topics yet." in store.index_content
        assert "Total topics: 0" in store.index_content
        assert "Rounds completed: 0" in store.index_content

    async def test_last_updated_present(self):
        store = FakeStore()
        store.entries = [_make_entry("topic", 1)]
        maintainer = IndexMaintainer()

        await maintainer.update(store, "ENG-001")

        assert "Last updated:" in store.index_content
