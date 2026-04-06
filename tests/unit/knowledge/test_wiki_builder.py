"""Tests for WikiBuilder compilation logic."""

from __future__ import annotations

from datetime import date, datetime, timezone

from keystone.citation.hash import compute_content_hash, compute_proposition_hash
from keystone.knowledge.content_hasher import ContentHasher
from keystone.knowledge.wiki_builder import WikiBuilder
from keystone.knowledge.wiki_schema import WikiEntry
from keystone.models.citations import (
    Citation,
    ConfidenceTier,
    SourceType,
    WikiCompilationRecord,
)
from keystone.models.research import FindingClaim, StructuredFinding


# -- In-memory WikiStore for testing --


class InMemoryWikiStore:
    """Minimal in-memory WikiStore satisfying the Protocol."""

    def __init__(self):
        self.raw_artifacts: dict[str, str] = {}  # path -> content
        self.compiled_entries: dict[str, WikiEntry] = {}  # path -> entry
        self.index_content: str = ""

    async def write_raw(
        self,
        engagement_id: str,
        round_number: int,
        agent_id: str,
        task_id: str,
        artifact: str,
    ) -> str:
        path = f"raw/{round_number}_{agent_id}_{task_id}.md"
        self.raw_artifacts[path] = artifact
        return path

    async def write_compiled(self, entry: WikiEntry) -> None:
        self.compiled_entries[entry.path] = entry

    async def read_compiled(self, engagement_id: str, path: str) -> WikiEntry | None:
        return self.compiled_entries.get(path)

    async def list_compiled(self, engagement_id: str) -> list[WikiEntry]:
        return [e for e in self.compiled_entries.values() if e.engagement_id == engagement_id]

    async def read_index(self, engagement_id: str) -> str:
        return self.index_content

    async def write_index(self, engagement_id: str, content: str) -> None:
        self.index_content = content


# -- Test fixtures --


def _make_citation(citation_id: str = "CIT-001") -> Citation:
    return Citation(
        citation_id=citation_id,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        url="https://example.com/source",
        title="Market Report 2026",
        source_type=SourceType.REPORT,
        quality_score=0.85,
        access_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
        date_published=date(2026, 3, 15),
    )


def _make_claim(
    text: str = "Market share is 23%",
    evidence: str = "Based on Q4 2025 earnings reports",
    citation_id: str = "CIT-001",
) -> FindingClaim:
    return FindingClaim(
        text=text,
        evidence=evidence,
        citations=[_make_citation(citation_id)],
        confidence=0.82,
        confidence_tier=ConfidenceTier.HIGH,
        caveats=["Regional data only"],
    )


def _make_finding(
    task_id: str = "market_sizing",
    agent_id: str = "agent_quant_1",
    claims: list[FindingClaim] | None = None,
) -> StructuredFinding:
    return StructuredFinding(
        task_id=task_id,
        agent_id=agent_id,
        engagement_id="ENG-001",
        client_id="CLIENT-001",
        agent_type="quantitative",
        claims=claims or [_make_claim()],
        absence_report=["No data found for Southeast Asian markets"],
        sources_consulted=12,
        tokens_consumed=5000,
    )


# -- Tests --


class TestWikiBuilderCompileRound:
    def _make_builder(self) -> tuple[WikiBuilder, InMemoryWikiStore]:
        store = InMemoryWikiStore()
        hasher = ContentHasher()
        builder = WikiBuilder(store, hasher)
        return builder, store

    async def test_single_finding_compiles(self):
        builder, store = self._make_builder()
        finding = _make_finding()

        entries, records = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[finding],
        )

        assert len(entries) == 1
        entry = entries[0]
        assert entry.engagement_id == "ENG-001"
        assert entry.client_id == "CLIENT-001"
        assert entry.round_added == 1
        assert "Market Sizing" in entry.content
        assert "Market share is 23%" in entry.content

    async def test_compiled_format_has_required_sections(self):
        builder, store = self._make_builder()
        entries, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[_make_finding()],
        )

        content = entries[0].content
        assert "# Market Sizing" in content
        assert "## Key Findings" in content
        assert "## Evidence" in content
        assert "## Confidence Assessment" in content
        assert "[Source: CIT-001]" in content
        assert "Compiled from round 1 by agent agent_quant_1" in content

    async def test_multiple_findings_grouped_correctly(self):
        builder, store = self._make_builder()
        findings = [
            _make_finding(task_id="market_sizing", agent_id="agent_1"),
            _make_finding(task_id="competitor_analysis", agent_id="agent_2"),
        ]

        entries, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=findings,
        )

        assert len(entries) == 2
        paths = {e.path for e in entries}
        assert "compiled/market_sizing.md" in paths
        assert "compiled/competitor_analysis.md" in paths

    async def test_proposition_hashes_generated_for_each_claim(self):
        builder, store = self._make_builder()
        claims = [
            _make_claim(text="Claim A", citation_id="CIT-001"),
            _make_claim(text="Claim B", citation_id="CIT-002"),
        ]
        finding = _make_finding(claims=claims)

        entries, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[finding],
        )

        entry = entries[0]
        assert len(entry.proposition_hashes) == 2
        for h in entry.proposition_hashes:
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    async def test_content_hash_matches_recomputed(self):
        builder, store = self._make_builder()
        entries, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[_make_finding()],
        )

        entry = entries[0]
        recomputed = compute_content_hash(entry.content)
        assert entry.content_hash == recomputed

    async def test_raw_artifacts_written_to_flat_paths(self):
        builder, store = self._make_builder()
        finding = _make_finding(task_id="market_sizing", agent_id="agent_1")

        entries, _ = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[finding],
        )

        assert "raw/1_agent_1_market_sizing.md" in store.raw_artifacts
        entry = entries[0]
        assert entry.source_artifacts == ["raw/1_agent_1_market_sizing.md"]

    async def test_wiki_compilation_records_produced(self):
        builder, store = self._make_builder()
        claims = [
            _make_claim(text="Claim A", citation_id="CIT-001"),
            _make_claim(text="Claim B", citation_id="CIT-002"),
        ]
        finding = _make_finding(claims=claims)

        _, records = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[finding],
        )

        assert len(records) == 2
        for rec in records:
            assert isinstance(rec, WikiCompilationRecord)
            assert rec.engagement_id == "ENG-001"
            assert rec.raw_path.startswith("raw/")
            assert rec.compiled_path.startswith("compiled/")
            assert rec.compiled_at is not None
            assert len(rec.content_hash) == 64

        citation_ids = {r.citation_id for r in records}
        assert citation_ids == {"CIT-001", "CIT-002"}

    async def test_empty_findings_handled(self):
        builder, store = self._make_builder()
        entries, records = await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[],
        )

        assert entries == []
        assert records == []

    async def test_index_updated_after_compile(self):
        builder, store = self._make_builder()
        await builder.compile_round(
            engagement_id="ENG-001",
            client_id="CLIENT-001",
            round_number=1,
            findings=[_make_finding()],
        )

        assert store.index_content != ""
        assert "ENG-001 -- Research Wiki" in store.index_content
        assert "Market Sizing" in store.index_content
