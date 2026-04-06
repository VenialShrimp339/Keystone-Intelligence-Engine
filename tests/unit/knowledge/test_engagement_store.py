"""Integration tests for FilesystemWikiStore.

Full round: write raw -> compile -> write compiled -> update index -> read back.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from keystone.citation.hash import compute_content_hash
from keystone.knowledge.content_hasher import ContentHasher
from keystone.knowledge.engagement_store import FilesystemWikiStore
from keystone.knowledge.wiki_builder import WikiBuilder
from keystone.knowledge.wiki_schema import WikiEntry
from keystone.models.citations import (
    Citation,
    ConfidenceTier,
    SourceType,
)
from keystone.models.research import FindingClaim, StructuredFinding


# -- Fixtures --


def _make_citation(cid: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=cid,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        url="https://example.com/source",
        title="Source Report",
        source_type=SourceType.REPORT,
        quality_score=0.8,
        access_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
        date_published=date(2026, 3, 1),
    )


def _make_finding(task_id: str, agent_id: str, claim_text: str) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=agent_id,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        agent_type="quantitative",
        claims=[
            FindingClaim(
                text=claim_text,
                evidence="Empirical data from multiple sources",
                citations=[_make_citation()],
                confidence=0.85,
                confidence_tier=ConfidenceTier.HIGH,
            )
        ],
        absence_report=[],
        sources_consulted=8,
        tokens_consumed=3000,
    )


# -- Tests --


class TestFilesystemWikiStoreRoundTrip:
    @pytest.fixture
    def store(self, tmp_path: Path) -> FilesystemWikiStore:
        return FilesystemWikiStore(base_path=str(tmp_path))

    async def test_write_raw_creates_file(self, store: FilesystemWikiStore, tmp_path: Path):
        path = await store.write_raw("ENG-001", 1, "agent1", "task1", "Raw artifact text")
        assert path == "raw/1_agent1_task1.md"
        file_path = tmp_path / "ENG-001" / "memory" / "raw" / "1_agent1_task1.md"
        assert file_path.exists()
        assert file_path.read_text() == "Raw artifact text"

    async def test_write_compiled_creates_files(self, store: FilesystemWikiStore, tmp_path: Path):
        content = "# Topic\n\nCompiled findings."
        entry = WikiEntry(
            path="compiled/topic.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=compute_content_hash(content),
            proposition_hashes=[],
            source_artifacts=["raw/1_agent1_task1.md"],
            round_added=1,
        )
        await store.write_compiled(entry)

        md_path = tmp_path / "ENG-001" / "memory" / "compiled" / "topic.md"
        meta_path = tmp_path / "ENG-001" / "memory" / "compiled" / "topic.meta.json"
        assert md_path.exists()
        assert meta_path.exists()
        assert md_path.read_text() == content

    async def test_read_compiled_round_trip(self, store: FilesystemWikiStore):
        content = "# Market\n\nAnalysis content."
        entry = WikiEntry(
            path="compiled/market.md",
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            content=content,
            content_hash=compute_content_hash(content),
            proposition_hashes=["a" * 64, "b" * 64],
            source_artifacts=["raw/1_a1_t1.md"],
            round_added=2,
        )
        await store.write_compiled(entry)

        result = await store.read_compiled("ENG-001", "compiled/market.md")
        assert result is not None
        assert result.content == content
        assert result.content_hash == entry.content_hash
        assert result.proposition_hashes == ["a" * 64, "b" * 64]
        assert result.round_added == 2

    async def test_read_compiled_not_found(self, store: FilesystemWikiStore):
        result = await store.read_compiled("ENG-001", "compiled/nonexistent.md")
        assert result is None

    async def test_list_compiled(self, store: FilesystemWikiStore):
        for topic in ["alpha", "beta", "gamma"]:
            content = f"# {topic}\n\nContent for {topic}."
            entry = WikiEntry(
                path=f"compiled/{topic}.md",
                engagement_id="ENG-001",
                client_id="CLIENT-001",
                content=content,
                content_hash=compute_content_hash(content),
                proposition_hashes=[],
                source_artifacts=[f"raw/1_a_{topic}.md"],
                round_added=1,
            )
            await store.write_compiled(entry)

        entries = await store.list_compiled("ENG-001")
        assert len(entries) == 3
        paths = {e.path for e in entries}
        assert paths == {"compiled/alpha.md", "compiled/beta.md", "compiled/gamma.md"}

    async def test_list_compiled_empty(self, store: FilesystemWikiStore):
        entries = await store.list_compiled("ENG-001")
        assert entries == []

    async def test_index_round_trip(self, store: FilesystemWikiStore):
        await store.write_index("ENG-001", "# Index\n\nContent here.")
        result = await store.read_index("ENG-001")
        assert result == "# Index\n\nContent here."

    async def test_read_index_not_found(self, store: FilesystemWikiStore):
        result = await store.read_index("ENG-NOPE")
        assert result == ""


class TestFullRoundIntegration:
    """Full round: write raw -> compile -> write compiled -> update index -> read back."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> FilesystemWikiStore:
        return FilesystemWikiStore(base_path=str(tmp_path))

    async def test_full_round(self, store: FilesystemWikiStore):
        hasher = ContentHasher()
        builder = WikiBuilder(store, hasher)

        findings = [
            _make_finding("market_sizing", "agent_1", "TAM is $4.2B"),
            _make_finding("competitor_landscape", "agent_2", "Top 3 hold 60% share"),
            _make_finding("customer_segments", "agent_3", "B2B is primary channel"),
        ]

        entries, records = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=findings,
        )

        # Verify entries
        assert len(entries) == 3
        for entry in entries:
            assert entry.engagement_id == "ENG-001"
            assert entry.content_hash == compute_content_hash(entry.content)
            assert len(entry.source_artifacts) == 1

        # Verify records
        assert len(records) == 3  # One citation per finding

        # Verify index was written
        index = await store.read_index("ENG-001")
        assert "Research Wiki" in index
        assert "Total topics: 3" in index

        # Verify read-back
        for entry in entries:
            read_back = await store.read_compiled("ENG-001", entry.path)
            assert read_back is not None
            assert read_back.content == entry.content
            assert read_back.content_hash == entry.content_hash

    async def test_multiple_rounds_accumulate(self, store: FilesystemWikiStore):
        hasher = ContentHasher()
        builder = WikiBuilder(store, hasher)

        # Round 1
        entries_r1, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[_make_finding("market_sizing", "agent_1", "TAM is $4.2B")],
        )

        # Round 2
        entries_r2, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=2,
            findings=[_make_finding("pricing_analysis", "agent_2", "Average price is $50")],
        )

        all_entries = await store.list_compiled("ENG-001")
        assert len(all_entries) == 2

        index = await store.read_index("ENG-001")
        assert "Total topics: 2" in index
        assert "Rounds completed: 2" in index

    async def test_provenance_chain_traceable(self, store: FilesystemWikiStore):
        hasher = ContentHasher()
        builder = WikiBuilder(store, hasher)

        finding = _make_finding("analysis", "agent_1", "Key insight here")
        entries, records = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[finding],
        )

        entry = entries[0]
        # Content hash is valid
        assert entry.content_hash == compute_content_hash(entry.content)
        # Proposition hashes exist
        assert len(entry.proposition_hashes) == 1
        # Source artifact is tracked
        assert len(entry.source_artifacts) == 1
        raw_path = entry.source_artifacts[0]
        assert raw_path.startswith("raw/")
        # Compilation record links citation -> raw -> compiled
        assert len(records) == 1
        assert records[0].raw_path == raw_path
        assert records[0].compiled_path == entry.path
