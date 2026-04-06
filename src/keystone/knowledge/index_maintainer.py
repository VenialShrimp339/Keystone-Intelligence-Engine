"""Auto-maintains INDEX.md as the navigation layer for the engagement wiki.

INDEX.md is updated atomically after each research round completes.
It lists all compiled topics with one-line summaries, organized
alphabetically, with coverage statistics.
"""

from __future__ import annotations

from datetime import datetime, timezone

from keystone.knowledge.wiki_schema import WikiEntry, WikiStore


class IndexMaintainer:
    """Maintains INDEX.md as the navigation layer for the wiki.

    Rebuilds INDEX.md from all compiled entries after each round.
    Entries are listed alphabetically by topic path.
    """

    async def update(self, store: WikiStore, engagement_id: str) -> None:
        """Rebuild INDEX.md from all compiled entries.

        Reads all compiled entries, generates the index content,
        writes it back, and marks all entries as indexed.
        """
        entries = await store.list_compiled(engagement_id)
        content = self._render_index(entries, engagement_id)
        await store.write_index(engagement_id, content)

    def _render_index(self, entries: list[WikiEntry], engagement_id: str) -> str:
        """Render INDEX.md content from compiled entries."""
        sorted_entries = sorted(entries, key=lambda e: e.path)

        lines: list[str] = []
        lines.append(f"# {engagement_id} -- Research Wiki")
        lines.append("")
        lines.append("## Topics")

        if not sorted_entries:
            lines.append("*No compiled topics yet.*")
        else:
            for entry in sorted_entries:
                topic_name = self._extract_topic_name(entry)
                summary = self._extract_summary(entry)
                lines.append(
                    f"- [{topic_name}]({entry.path}) -- {summary} (Round {entry.round_added})"
                )

        lines.append("")
        lines.append("## Coverage")

        rounds = {e.round_added for e in sorted_entries}
        lines.append(f"- Total topics: {len(sorted_entries)}")
        lines.append(f"- Rounds completed: {len(rounds)}")
        lines.append(f"- Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        lines.append("")

        return "\n".join(lines)

    def _extract_topic_name(self, entry: WikiEntry) -> str:
        """Extract a human-readable topic name from the entry.

        Tries the first H1 heading in content, falls back to path.
        """
        for line in entry.content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        # Fallback: derive from path (compiled/market_analysis.md -> Market Analysis)
        filename = entry.path.rsplit("/", maxsplit=1)[-1]
        name = filename.removesuffix(".md").replace("_", " ")
        return name.title()

    def _extract_summary(self, entry: WikiEntry) -> str:
        """Extract a one-line summary from the entry.

        Uses the first non-heading, non-empty line after the title.
        """
        past_title = False
        for line in entry.content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not past_title:
                past_title = True
                continue
            if past_title and stripped and not stripped.startswith("#"):
                # Truncate to reasonable length
                if len(stripped) > 80:
                    return stripped[:77] + "..."
                return stripped
        return "No summary available"
