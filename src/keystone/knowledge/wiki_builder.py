"""Compiles raw research artifacts into structured wiki entries.

The WikiBuilder is the core compilation engine for Component #3b.
It processes StructuredFindings from L1 research agents into compiled
wiki entries with full content-hash provenance, and produces
WikiCompilationRecords to maintain the citation provenance chain.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from keystone.knowledge.content_hasher import ContentHasher
from keystone.knowledge.index_maintainer import IndexMaintainer
from keystone.knowledge.wiki_schema import WikiEntry, WikiStore
from keystone.models.citations import WikiCompilationRecord
from keystone.models.research import FindingClaim, StructuredFinding


class WikiBuilder:
    """Compiles raw research artifacts into structured wiki entries.

    Also produces WikiCompilationRecords (from models/citations.py) to maintain
    the citation provenance chain: each record links citation_id -> raw_path -> compiled_path.
    """

    def __init__(self, store: WikiStore, hasher: ContentHasher) -> None:
        self._store = store
        self._hasher = hasher
        self._index_maintainer = IndexMaintainer()

    async def compile_round(
        self,
        engagement_id: str,
        client_id: str,
        round_number: int,
        findings: list[StructuredFinding],
    ) -> tuple[list[WikiEntry], list[WikiCompilationRecord]]:
        """Process one research round's findings into compiled wiki entries.

        Returns:
            Tuple of (wiki_entries, compilation_records).
        """
        if not findings:
            return [], []

        entries: list[WikiEntry] = []
        records: list[WikiCompilationRecord] = []

        for finding in findings:
            # 1. Build raw artifact text from the structured finding
            raw_text = self._render_raw_artifact(finding)

            # 2. Write raw artifact (flat naming: {round}_{agent_id}_{task_id}.md)
            raw_path = await self._store.write_raw(
                engagement_id=engagement_id,
                round_number=round_number,
                agent_id=finding.agent_id,
                task_id=finding.task_id,
                artifact=raw_text,
            )

            # 3. Compute source content hash for provenance
            source_hash = self._hasher.hash_content(raw_text)

            # 4. Extract propositions and hash each one
            proposition_hashes: list[str] = []
            for claim in finding.claims:
                prop_hash = self._hasher.hash_proposition(claim.text, source_hash)
                proposition_hashes.append(prop_hash)

            # 5. Compile into structured markdown
            topic_slug = self._make_topic_slug(finding.task_id)
            compiled_path = f"compiled/{topic_slug}.md"
            compiled_content = self._render_compiled(finding, round_number, source_hash)

            # 6. Hash the compiled content
            content_hash = self._hasher.hash_content(compiled_content)

            # 7. Create WikiEntry
            entry = WikiEntry(
                path=compiled_path,
                engagement_id=engagement_id,
                client_id=client_id,
                content=compiled_content,
                content_hash=content_hash,
                proposition_hashes=proposition_hashes,
                source_artifacts=[raw_path],
                round_added=round_number,
                indexed=False,
            )

            # 8. Write compiled entry
            await self._store.write_compiled(entry)
            entries.append(entry)

            # 9. Create WikiCompilationRecords for each citation
            now = datetime.now(timezone.utc)
            for claim in finding.claims:
                for citation in claim.citations:
                    record = WikiCompilationRecord(
                        citation_id=citation.citation_id,
                        engagement_id=engagement_id,
                        raw_path=raw_path,
                        compiled_path=compiled_path,
                        content_hash=source_hash,
                        compiled_at=now,
                    )
                    records.append(record)

        # 10. Update INDEX.md
        await self._index_maintainer.update(self._store, engagement_id)

        return entries, records

    def _render_raw_artifact(self, finding: StructuredFinding) -> str:
        """Render a StructuredFinding as raw markdown for storage."""
        lines: list[str] = []
        lines.append(f"# Research Finding: {finding.task_id}")
        lines.append(f"Agent: {finding.agent_id} ({finding.agent_type})")
        lines.append(f"Sources consulted: {finding.sources_consulted}")
        lines.append("")

        for i, claim in enumerate(finding.claims, 1):
            lines.append(f"## Claim {i}")
            lines.append(claim.text)
            lines.append(f"**Evidence:** {claim.evidence}")
            lines.append(f"**Confidence:** {claim.confidence} ({claim.confidence_tier})")
            if claim.caveats:
                lines.append(f"**Caveats:** {'; '.join(claim.caveats)}")
            citation_ids = [c.citation_id for c in claim.citations]
            lines.append(f"**Citations:** {', '.join(citation_ids)}")
            lines.append("")

        if finding.absence_report:
            lines.append("## Absence Report")
            for item in finding.absence_report:
                lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    def _render_compiled(
        self,
        finding: StructuredFinding,
        round_number: int,
        source_hash: str,
    ) -> str:
        """Render a compiled wiki entry from a StructuredFinding."""
        lines: list[str] = []
        topic_title = self._make_topic_title(finding.task_id)
        lines.append(f"# {topic_title}")
        lines.append("")

        # Key Findings section
        lines.append("## Key Findings")
        for claim in finding.claims:
            citation_refs = ", ".join(c.citation_id for c in claim.citations)
            lines.append(f"- {claim.text} [Source: {citation_refs}]")
        lines.append("")

        # Evidence section
        lines.append("## Evidence")
        for claim in finding.claims:
            lines.append(f"**{claim.text}**")
            lines.append(claim.evidence)
            if claim.caveats:
                lines.append(f"*Caveats: {'; '.join(claim.caveats)}*")
            lines.append("")

        # Confidence Assessment
        lines.append("## Confidence Assessment")
        if finding.claims:
            avg_conf = sum(c.confidence for c in finding.claims) / len(finding.claims)
            tier = finding.claims[0].confidence_tier
            lines.append(
                f"Average confidence: {avg_conf:.2f} ({tier}). "
                f"Based on {finding.sources_consulted} sources consulted."
            )
        else:
            lines.append("No claims produced.")

        if finding.absence_report:
            lines.append("")
            lines.append("**Gaps identified:**")
            for gap in finding.absence_report:
                lines.append(f"- {gap}")

        lines.append("")
        lines.append("---")
        lines.append(f"*Compiled from round {round_number} by agent {finding.agent_id}*")
        lines.append(f"*Content hash: {source_hash}*")
        lines.append("")

        return "\n".join(lines)

    def _make_topic_slug(self, task_id: str) -> str:
        """Convert a task_id into a filesystem-safe topic slug."""
        slug = task_id.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        slug = slug.strip("_")
        return slug or "unnamed"

    def _make_topic_title(self, task_id: str) -> str:
        """Convert a task_id into a human-readable title."""
        title = task_id.replace("_", " ").replace("-", " ")
        return title.title()
