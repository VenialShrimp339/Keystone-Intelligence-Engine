"""Filesystem implementation of WikiStore for Phase 1.

Directory structure:
  {base_path}/{engagement_id}/
      memory/
          raw/{round}_{agent_id}_{task_id}.md    # Flat naming, immutable after write
          compiled/{topic}.md
          INDEX.md

Uses asyncio.to_thread for non-blocking filesystem I/O.
Phase 2 replaces this with a PostgreSQL backend; the WikiStore
Protocol interface does not change.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from keystone.knowledge.wiki_schema import WikiEntry


class FilesystemWikiStore:
    """Filesystem implementation of WikiStore. Phase 1 backend.

    All operations go through asyncio.to_thread to avoid blocking
    the event loop on filesystem I/O.
    """

    def __init__(self, base_path: str = "engagements") -> None:
        self._base = Path(base_path)

    def _memory_path(self, engagement_id: str) -> Path:
        return self._base / engagement_id / "memory"

    def _raw_dir(self, engagement_id: str) -> Path:
        return self._memory_path(engagement_id) / "raw"

    def _compiled_dir(self, engagement_id: str) -> Path:
        return self._memory_path(engagement_id) / "compiled"

    def _index_path(self, engagement_id: str) -> Path:
        return self._memory_path(engagement_id) / "INDEX.md"

    def _meta_path(self, engagement_id: str, compiled_path: str) -> Path:
        """Path to the JSON metadata sidecar for a compiled entry."""
        return self._compiled_dir(engagement_id) / (Path(compiled_path).stem + ".meta.json")

    async def write_raw(
        self,
        engagement_id: str,
        round_number: int,
        agent_id: str,
        task_id: str,
        artifact: str,
    ) -> str:
        """Write a raw subagent artifact. Returns the relative path.

        Flat naming convention: {round}_{agent_id}_{task_id}.md
        Raw artifacts are immutable after write.
        """
        filename = f"{round_number}_{agent_id}_{task_id}.md"
        raw_dir = self._raw_dir(engagement_id)

        def _write() -> None:
            raw_dir.mkdir(parents=True, exist_ok=True)
            filepath = raw_dir / filename
            filepath.write_text(artifact, encoding="utf-8")

        await asyncio.to_thread(_write)
        return f"raw/{filename}"

    async def write_compiled(self, entry: WikiEntry) -> None:
        """Write or overwrite a compiled wiki entry.

        Writes both the markdown content and a JSON metadata sidecar
        containing the WikiEntry fields needed for reconstruction.
        """
        compiled_dir = self._compiled_dir(entry.engagement_id)
        # entry.path is like "compiled/topic.md" -- extract just the filename
        filename = entry.path.split("/")[-1]

        meta = {
            "path": entry.path,
            "engagement_id": entry.engagement_id,
            "client_id": entry.client_id,
            "content_hash": entry.content_hash,
            "proposition_hashes": list(entry.proposition_hashes),
            "source_artifacts": list(entry.source_artifacts),
            "round_added": entry.round_added,
            "indexed": entry.indexed,
        }

        def _write() -> None:
            compiled_dir.mkdir(parents=True, exist_ok=True)
            (compiled_dir / filename).write_text(entry.content, encoding="utf-8")
            meta_file = compiled_dir / (Path(filename).stem + ".meta.json")
            meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        await asyncio.to_thread(_write)

    async def read_compiled(self, engagement_id: str, path: str) -> WikiEntry | None:
        """Read a compiled entry by path. Returns None if not found."""
        compiled_dir = self._compiled_dir(engagement_id)
        filename = path.split("/")[-1]
        md_path = compiled_dir / filename
        meta_path = compiled_dir / (Path(filename).stem + ".meta.json")

        def _read() -> WikiEntry | None:
            if not md_path.exists() or not meta_path.exists():
                return None
            content = md_path.read_text(encoding="utf-8")
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            return WikiEntry(
                path=meta["path"],
                engagement_id=meta["engagement_id"],
                client_id=meta["client_id"],
                content=content,
                content_hash=meta["content_hash"],
                proposition_hashes=meta["proposition_hashes"],
                source_artifacts=meta["source_artifacts"],
                round_added=meta["round_added"],
                indexed=meta["indexed"],
            )

        return await asyncio.to_thread(_read)

    async def list_compiled(self, engagement_id: str) -> list[WikiEntry]:
        """List all compiled entries for an engagement."""
        compiled_dir = self._compiled_dir(engagement_id)

        def _list() -> list[WikiEntry]:
            if not compiled_dir.exists():
                return []
            entries = []
            for meta_file in sorted(compiled_dir.glob("*.meta.json")):
                md_file = meta_file.with_suffix("").with_suffix(".md")
                if not md_file.exists():
                    continue
                content = md_file.read_text(encoding="utf-8")
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                entries.append(
                    WikiEntry(
                        path=meta["path"],
                        engagement_id=meta["engagement_id"],
                        client_id=meta["client_id"],
                        content=content,
                        content_hash=meta["content_hash"],
                        proposition_hashes=meta["proposition_hashes"],
                        source_artifacts=meta["source_artifacts"],
                        round_added=meta["round_added"],
                        indexed=meta["indexed"],
                    )
                )
            return entries

        return await asyncio.to_thread(_list)

    async def read_index(self, engagement_id: str) -> str:
        """Read INDEX.md content. Returns empty string if not found."""
        index_path = self._index_path(engagement_id)

        def _read() -> str:
            if not index_path.exists():
                return ""
            return index_path.read_text(encoding="utf-8")

        return await asyncio.to_thread(_read)

    async def write_index(self, engagement_id: str, content: str) -> None:
        """Write INDEX.md content."""
        memory_dir = self._memory_path(engagement_id)

        def _write() -> None:
            memory_dir.mkdir(parents=True, exist_ok=True)
            (memory_dir / "INDEX.md").write_text(content, encoding="utf-8")

        await asyncio.to_thread(_write)
