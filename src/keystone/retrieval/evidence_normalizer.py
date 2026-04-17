"""Normalize parsed documents into evidence-prep records.

The normalizer is the single hand-off out of Lane E: one
``EvidencePrepRecord`` per emitted ``ParsedPassage``, carrying the full
provenance chain (artifact_id, canonical_url, content_hash, coverage,
source_family, parser identity, locator, parse confidence).

The normalizer does not re-score, re-chunk, or filter. That is by
design: the research pipeline's confidence logic is the single source of
truth for how to weight evidence, and Lane E must not silently drop
passages that downstream might have wanted to inspect (even LOW
confidence ones). If the caller wants filtering, it is applied on the
returned list.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from keystone.retrieval.parse_models import (
    EvidencePrepRecord,
    FetchedArtifact,
    ParsedDocument,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


class EvidenceNormalizer:
    """Turn (FetchedArtifact, ParsedDocument) pairs into evidence-prep records."""

    def normalize(
        self, artifact: FetchedArtifact, parsed: ParsedDocument
    ) -> list[EvidencePrepRecord]:
        """Produce one ``EvidencePrepRecord`` per passage in ``parsed``.

        Raises:
            ValueError: if ``parsed.artifact_id`` does not match
                ``artifact.artifact_id``. Downstream correctness depends
                on this identity so a mismatch is a hard error, not a
                silent drop.
        """

        if parsed.artifact_id != artifact.artifact_id:
            raise ValueError(
                "ParsedDocument.artifact_id "
                f"({parsed.artifact_id!r}) does not match FetchedArtifact.artifact_id "
                f"({artifact.artifact_id!r})"
            )

        canonical = artifact.canonical_url or artifact.url
        records: list[EvidencePrepRecord] = []
        for passage in parsed.passages:
            record_id = f"ev:{passage.passage_id}"
            records.append(
                EvidencePrepRecord(
                    record_id=record_id,
                    artifact_id=artifact.artifact_id,
                    canonical_url=canonical,
                    content_hash=artifact.content_hash,
                    coverage=artifact.coverage,
                    source_family=parsed.source_family,
                    parser=parsed.parser,
                    locator=passage.locator,
                    passage_kind=passage.kind,
                    text=passage.text,
                    parse_confidence=passage.parse_confidence,
                    fetched_at=artifact.fetched_at,
                    title=artifact.title,
                )
            )
        return records

    def normalize_many(
        self,
        pairs: Iterable[tuple[FetchedArtifact, ParsedDocument]],
    ) -> list[EvidencePrepRecord]:
        """Convenience: normalize a sequence of (artifact, parsed) pairs.

        Errors on individual pairs propagate -- Lane E cannot silently
        drop an evidence batch.
        """

        out: list[EvidencePrepRecord] = []
        for artifact, parsed in pairs:
            out.extend(self.normalize(artifact, parsed))
        return out
