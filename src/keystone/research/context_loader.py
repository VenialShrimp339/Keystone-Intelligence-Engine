"""JIT context loading from the compiled wiki for research round N+1.

Reads INDEX.md from the wiki's compiled/ directory to navigate
to relevant entries. Loads content for the next research round
based on task topics and prior findings.

Part of the Karpathy three-layer pattern (raw/compiled/INDEX.md).
"""

from __future__ import annotations

from pathlib import Path


class ContextLoader:
    """Loads compiled wiki context for iterative research rounds."""

    def __init__(self, wiki_base_dir: Path) -> None:
        self._wiki_dir = wiki_base_dir
        self._compiled_dir = wiki_base_dir / "compiled"
        self._index_path = wiki_base_dir / "INDEX.md"

    async def load_context(
        self,
        engagement_id: str,
        task_id: str,
        round_number: int,
    ) -> list[str]:
        """Load relevant wiki context for round N+1.

        Round 1 has no prior context. Subsequent rounds load
        all compiled entries (Phase 1 simplification; future
        phases add semantic relevance scoring).
        """
        if round_number < 2:
            return []

        entries: list[str] = []
        index_entries = self._parse_index()

        for entry in index_entries:
            content = self._load_entry(entry["path"])
            if content is not None:
                entries.append(content)

        return entries

    def _parse_index(self) -> list[dict[str, str]]:
        """Parse INDEX.md to extract entry paths and titles."""
        if not self._index_path.exists():
            return []

        content = self._index_path.read_text()
        entries: list[dict[str, str]] = []

        for line in content.splitlines():
            line = line.strip()
            if not (line.startswith("- [") and "](" in line):
                continue
            try:
                title = line[line.index("[") + 1 : line.index("]")]
                path = line[line.index("(") + 1 : line.index(")")]
                entries.append({"title": title, "path": path})
            except ValueError:
                continue

        return entries

    def _load_entry(self, relative_path: str) -> str | None:
        """Load a compiled wiki entry by relative path."""
        for base in (self._wiki_dir, self._compiled_dir):
            full_path = base / relative_path
            if full_path.exists():
                return full_path.read_text()
        return None
