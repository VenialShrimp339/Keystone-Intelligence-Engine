"""Passage-aware semantic chunker.

Takes Lane E :class:`EvidencePrepRecord` and produces
:class:`DocumentChunk` instances ready for embedding + indexing. The
chunker respects Lane E's passage boundaries -- it never splits a single
passage mid-sentence across chunks unless the passage is larger than
``max_tokens``. Multiple short passages from the same artifact may fold
into one chunk when their combined token count stays below the target.

An optional contextual preamble (Anthropic's contextual retrieval
pattern) prepends a short line to each chunk's ``content`` describing
what document / section it came from. Research showed this single
change reduces retrieval failures by ~67% on RAG benchmarks. The raw
passage text stays in ``raw_text`` so downstream citations quote the
source verbatim without the preamble.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from keystone.retrieval.search.models import ChunkMetadata, DocumentChunk

if TYPE_CHECKING:
    from collections.abc import Iterable

    from keystone.retrieval.parse_models import EvidencePrepRecord

# Word-count proxy for tokens. Production pipelines would use the
# embedder's tokenizer, but for chunking the word proxy is within ~15%
# of Voyage's tokenizer output on English prose and doesn't require
# loading a 100MB tokenizer for every chunking operation.
_WORD_RE = re.compile(r"\S+")


def count_tokens(text: str) -> int:
    """Return the approximate token count for ``text`` (word-count proxy)."""

    return len(_WORD_RE.findall(text))


class SemanticChunker:
    """Chunk :class:`EvidencePrepRecord` sequences for embedding.

    Deterministic: same inputs always produce the same chunk_ids in the
    same order, so ingest is safely re-runnable. Chunk IDs encode the
    artifact + passage sequence so a downstream citation can be resolved
    back to a specific (artifact, passage-range) pair.
    """

    def __init__(
        self,
        *,
        target_tokens: int = 384,
        max_tokens: int = 512,
        min_tokens: int = 32,
        overlap_tokens: int = 64,
        add_contextual_preamble: bool = True,
    ) -> None:
        if max_tokens < target_tokens:
            raise ValueError(
                f"max_tokens ({max_tokens}) must be >= target_tokens ({target_tokens})"
            )
        if target_tokens < min_tokens:
            raise ValueError(
                f"target_tokens ({target_tokens}) must be >= min_tokens ({min_tokens})"
            )
        if overlap_tokens >= target_tokens:
            raise ValueError(
                f"overlap_tokens ({overlap_tokens}) must be < target_tokens ({target_tokens})"
            )
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens
        self.add_contextual_preamble = add_contextual_preamble

    def chunk(
        self,
        records: Iterable[EvidencePrepRecord],
        *,
        engagement_id: str | None,
    ) -> list[DocumentChunk]:
        """Chunk an iterable of evidence records, grouped by artifact.

        ``engagement_id`` is a required kwarg so the caller cannot
        silently produce untagged chunks (which the isolation filter
        treats as institutional memory and never hides). Pass a non-
        ``None`` string to tag the chunks to that engagement, or pass
        ``None`` explicitly for institutional-memory ingest that
        should remain visible across all engagements. The explicit
        kwarg makes the dangerous path (no tagging) deliberate.
        """

        grouped: dict[str, list[EvidencePrepRecord]] = {}
        for record in records:
            grouped.setdefault(record.artifact_id, []).append(record)

        out: list[DocumentChunk] = []
        for artifact_id, artifact_records in grouped.items():
            out.extend(
                self._chunk_artifact(artifact_id, artifact_records, engagement_id=engagement_id)
            )
        return out

    # --- Internal helpers -------------------------------------------------

    def _chunk_artifact(
        self,
        artifact_id: str,
        records: list[EvidencePrepRecord],
        *,
        engagement_id: str | None,
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        pending: list[EvidencePrepRecord] = []
        pending_tokens = 0

        for record in records:
            record_tokens = count_tokens(record.text)
            # Oversized passage: flush pending, then split this passage
            if record_tokens > self.max_tokens:
                if pending:
                    chunks.append(
                        self._build_chunk(
                            artifact_id,
                            len(chunks),
                            pending,
                            pending_tokens,
                            engagement_id=engagement_id,
                        )
                    )
                    pending = []
                    pending_tokens = 0
                chunks.extend(
                    self._split_oversized(
                        artifact_id, len(chunks), record, engagement_id=engagement_id
                    )
                )
                continue

            # Would exceed max_tokens: flush first, then start fresh
            if pending and pending_tokens + record_tokens > self.max_tokens:
                chunks.append(
                    self._build_chunk(
                        artifact_id,
                        len(chunks),
                        pending,
                        pending_tokens,
                        engagement_id=engagement_id,
                    )
                )
                pending = []
                pending_tokens = 0

            pending.append(record)
            pending_tokens += record_tokens

            # Target reached: flush
            if pending_tokens >= self.target_tokens:
                chunks.append(
                    self._build_chunk(
                        artifact_id,
                        len(chunks),
                        pending,
                        pending_tokens,
                        engagement_id=engagement_id,
                    )
                )
                pending = []
                pending_tokens = 0

        # Flush trailing fragment even if it's below min_tokens -- dropping
        # a tail passage loses evidence. Tests pin this behaviour.
        if pending:
            chunks.append(
                self._build_chunk(
                    artifact_id,
                    len(chunks),
                    pending,
                    pending_tokens,
                    engagement_id=engagement_id,
                )
            )
        return chunks

    def _build_chunk(
        self,
        artifact_id: str,
        seq: int,
        records: list[EvidencePrepRecord],
        token_count: int,
        *,
        engagement_id: str | None,
    ) -> DocumentChunk:
        anchor = records[0]
        raw_text = "\n\n".join(record.text for record in records)
        content = self._apply_preamble(raw_text, anchor)
        metadata = ChunkMetadata(
            artifact_id=artifact_id,
            canonical_url=anchor.canonical_url,
            content_hash=anchor.content_hash,
            source_family=anchor.source_family,
            locator=anchor.locator,
            parse_confidence=anchor.parse_confidence,
            title=anchor.title,
            fetched_at=anchor.fetched_at,
            record_ids=[record.record_id for record in records],
            engagement_id=engagement_id,
        )
        return DocumentChunk(
            chunk_id=_make_chunk_id(artifact_id, seq),
            content=content,
            raw_text=raw_text,
            metadata=metadata,
            token_count=max(token_count, 1),
        )

    def _split_oversized(
        self,
        artifact_id: str,
        start_seq: int,
        record: EvidencePrepRecord,
        *,
        engagement_id: str | None,
    ) -> list[DocumentChunk]:
        """Split a single oversize passage into multiple overlapping chunks."""

        words = _WORD_RE.findall(record.text)
        if not words:
            return []
        stride = max(1, self.target_tokens - self.overlap_tokens)
        pieces: list[str] = []
        start = 0
        while start < len(words):
            end = min(start + self.target_tokens, len(words))
            pieces.append(" ".join(words[start:end]))
            if end == len(words):
                break
            start += stride

        chunks: list[DocumentChunk] = []
        for offset, piece in enumerate(pieces):
            seq = start_seq + offset
            content = self._apply_preamble(piece, record)
            metadata = ChunkMetadata(
                artifact_id=artifact_id,
                canonical_url=record.canonical_url,
                content_hash=record.content_hash,
                source_family=record.source_family,
                locator=record.locator,
                parse_confidence=record.parse_confidence,
                title=record.title,
                fetched_at=record.fetched_at,
                record_ids=[record.record_id],
                engagement_id=engagement_id,
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=_make_chunk_id(artifact_id, seq),
                    content=content,
                    raw_text=piece,
                    metadata=metadata,
                    token_count=count_tokens(piece),
                )
            )
        return chunks

    def _apply_preamble(self, text: str, anchor: EvidencePrepRecord) -> str:
        if not self.add_contextual_preamble:
            return text
        preamble = _build_preamble(anchor)
        if not preamble:
            return text
        return f"{preamble}\n\n{text}"


def _build_preamble(record: EvidencePrepRecord) -> str:
    """Construct a short 'what-and-where' preamble for a chunk.

    Kept deterministic: identical inputs always produce the identical
    preamble. Empty strings are returned when no useful context exists
    (no title + no section path), so the chunk content is unchanged.
    """

    parts: list[str] = []
    title = (record.title or "").strip()
    if title:
        parts.append(f"Source: {title}")
    section_path = [segment for segment in record.locator.section_path if segment.strip()]
    if section_path:
        parts.append("Section: " + " > ".join(section_path))
    if record.locator.page_number is not None:
        parts.append(f"Page {record.locator.page_number}")
    if not parts:
        return ""
    return " | ".join(parts)


def _make_chunk_id(artifact_id: str, seq: int) -> str:
    return f"{artifact_id}:{seq:04d}"
