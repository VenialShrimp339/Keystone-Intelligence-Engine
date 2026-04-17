"""Pydantic v2 models for Lane E parse output and evidence-prep records.

The schema chain:
    FetchedArtifact (Lane H output, persisted JSON)
        -> ParsedDocument (article or PDF parse result)
            -> passages: list[ParsedPassage]
            -> warnings: list[ParseWarning]
        -> normalize() -> list[EvidencePrepRecord]

Every record downstream of Lane E must be traceable back to its
FetchedArtifact via (artifact_id, content_hash) and to its location in
the source via Locator.

Models are frozen and strictly validated: a malformed record cannot be
constructed, which means Lane E cannot silently emit garbage.
"""

from __future__ import annotations

import re
from datetime import datetime  # noqa: TC003 (Pydantic v2 needs runtime access)
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")
_ARTIFACT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-:.]{0,127}")
_PASSAGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-:.]{0,255}")


class SourceFamily(StrEnum):
    """Coarse classification of a fetched artifact's origin family.

    Drives parser dispatch and downstream weighting. Kept intentionally
    narrow for Lane E -- richer typing lives in models.citations.SourceType.
    """

    ARTICLE = "article"
    PDF = "pdf"
    REPORT = "report"
    UNKNOWN = "unknown"


class CoverageStatus(StrEnum):
    """How complete Lane H's fetch was."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    TRUNCATED = "truncated"
    ERROR = "error"


class PassageKind(StrEnum):
    """Structural role of a parsed passage inside its document."""

    SECTION_HEADING = "section_heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    BLOCK_QUOTE = "block_quote"
    CODE = "code"
    TABLE = "table"
    CAPTION = "caption"


class ParseConfidenceTier(StrEnum):
    """Discrete bucket derived from ParseConfidence.score.

    Downstream layers should branch on tier, not on raw score.
    Cutoffs: HIGH >= 0.85, MEDIUM >= 0.55, LOW otherwise.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ParserIdentity(BaseModel):
    """Identifies which parser implementation produced a ParsedDocument.

    Two parses of the same artifact with different parsers are not
    interchangeable -- the identity is part of the provenance chain.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(
        min_length=1, description="Stable parser identifier, e.g. 'keystone.article.v1'"
    )
    version: str = Field(min_length=1, description="Parser implementation version")


class Coverage(BaseModel):
    """Lane H's fetch coverage record.

    Carries forward so downstream can attenuate confidence on truncated
    or partial fetches without re-querying Lane H.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: CoverageStatus = Field(description="Fetch completeness status")
    bytes_fetched: int | None = Field(default=None, ge=0, description="Bytes actually retrieved")
    bytes_expected: int | None = Field(
        default=None, ge=0, description="Bytes expected (e.g. Content-Length)"
    )
    notes: str | None = Field(default=None, description="Free-form coverage notes")

    @model_validator(mode="after")
    def _bytes_are_consistent(self) -> Coverage:
        if (
            self.bytes_fetched is not None
            and self.bytes_expected is not None
            and self.bytes_fetched > self.bytes_expected
        ):
            raise ValueError(
                "bytes_fetched cannot exceed bytes_expected; "
                f"got {self.bytes_fetched} > {self.bytes_expected}"
            )
        return self


class Locator(BaseModel):
    """Where a passage lives inside its source document.

    Article: section_path is the heading chain leading to this passage,
    paragraph_index is the ordinal within the enclosing section.
    PDF: page_number is set, section_path is empty or holds detected
    headings, paragraph_index is the ordinal within the page.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    section_path: list[str] = Field(
        default_factory=list,
        description="Heading chain from document root to this passage",
    )
    paragraph_index: int = Field(
        ge=0, description="Zero-based ordinal within the enclosing container"
    )
    page_number: int | None = Field(
        default=None, ge=1, description="One-based PDF page number, if applicable"
    )
    char_start: int | None = Field(
        default=None, ge=0, description="Character offset from the start of the source text"
    )
    char_end: int | None = Field(
        default=None, ge=0, description="Character offset one past the last char"
    )

    @model_validator(mode="after")
    def _char_range_valid(self) -> Locator:
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError(
                f"char_end ({self.char_end}) cannot be less than char_start ({self.char_start})"
            )
        return self

    @field_validator("section_path")
    @classmethod
    def _section_segments_nonempty(cls, v: list[str]) -> list[str]:
        for segment in v:
            if not segment or segment != segment.strip():
                raise ValueError("section_path segments must be non-empty and trimmed")
        return v


class ParseConfidence(BaseModel):
    """Deterministic confidence signal for a parse result.

    No LLM involved -- the score is computed from structural signals:
    was the document well-formed, did a decompressor succeed, were
    heading boundaries recoverable, was text non-empty, etc.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float = Field(ge=0.0, le=1.0, description="Confidence on [0, 1]")
    tier: ParseConfidenceTier = Field(description="Bucket derived from score")
    reasons: list[str] = Field(
        default_factory=list,
        description="Short machine-readable reason codes contributing to the score",
    )

    @model_validator(mode="after")
    def _tier_matches_score(self) -> ParseConfidence:
        expected = tier_for_score(self.score)
        if expected is not self.tier:
            raise ValueError(
                f"tier {self.tier.value!r} does not match score {self.score}; "
                f"expected {expected.value!r}"
            )
        return self


def tier_for_score(score: float) -> ParseConfidenceTier:
    """Canonical mapping from a [0,1] score to a discrete tier.

    Kept as a free function so parsers and normalizers produce consistent
    tiers without duplicating the cutoffs.
    """

    if score >= 0.85:
        return ParseConfidenceTier.HIGH
    if score >= 0.55:
        return ParseConfidenceTier.MEDIUM
    return ParseConfidenceTier.LOW


def confidence(score: float, reasons: list[str] | None = None) -> ParseConfidence:
    """Construct a ParseConfidence from a score, with tier derived automatically."""

    clamped = max(0.0, min(1.0, score))
    return ParseConfidence(
        score=clamped,
        tier=tier_for_score(clamped),
        reasons=list(reasons or []),
    )


class ParseWarning(BaseModel):
    """A non-fatal parse issue worth preserving for downstream review."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(
        min_length=1,
        description="Stable machine-readable code, e.g. 'EMPTY_PAGE', 'DECODE_FAILURE'",
    )
    message: str = Field(min_length=1, description="Human-readable description")
    locator: Locator | None = Field(
        default=None, description="Where in the source this warning applies, if local"
    )

    @field_validator("code")
    @classmethod
    def _code_is_upper_snake(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", v):
            raise ValueError(f"ParseWarning.code must be UPPER_SNAKE_CASE; got {v!r}")
        return v


class ParsedPassage(BaseModel):
    """A single structured passage extracted from a document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    passage_id: str = Field(description="Document-unique passage identifier")
    artifact_id: str = Field(description="FetchedArtifact this passage was parsed from")
    kind: PassageKind = Field(description="Structural role of this passage")
    text: str = Field(min_length=1, description="Cleaned passage text")
    locator: Locator = Field(description="Where the passage lives in the source")
    parse_confidence: ParseConfidence = Field(description="Per-passage parse quality signal")

    @field_validator("passage_id")
    @classmethod
    def _passage_id_format(cls, v: str) -> str:
        if not _PASSAGE_ID.fullmatch(v):
            raise ValueError(f"passage_id has invalid format: {v!r}")
        return v

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id_format(cls, v: str) -> str:
        if not _ARTIFACT_ID.fullmatch(v):
            raise ValueError(f"artifact_id has invalid format: {v!r}")
        return v

    @field_validator("text")
    @classmethod
    def _text_is_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("passage text cannot be whitespace-only")
        return v


class ParsedDocument(BaseModel):
    """Result of parsing a single FetchedArtifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str = Field(description="FetchedArtifact this parse derived from")
    source_family: SourceFamily = Field(description="Coarse origin family")
    parser: ParserIdentity = Field(description="Parser that produced this result")
    passages: list[ParsedPassage] = Field(
        default_factory=list, description="Structured passages in document order"
    )
    warnings: list[ParseWarning] = Field(default_factory=list, description="Non-fatal parse issues")
    overall_confidence: ParseConfidence = Field(description="Document-level confidence signal")

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id_format(cls, v: str) -> str:
        if not _ARTIFACT_ID.fullmatch(v):
            raise ValueError(f"artifact_id has invalid format: {v!r}")
        return v

    @model_validator(mode="after")
    def _passages_reference_this_artifact(self) -> ParsedDocument:
        for passage in self.passages:
            if passage.artifact_id != self.artifact_id:
                raise ValueError(
                    f"passage {passage.passage_id!r} has artifact_id "
                    f"{passage.artifact_id!r}, expected {self.artifact_id!r}"
                )
        seen: set[str] = set()
        for passage in self.passages:
            if passage.passage_id in seen:
                raise ValueError(f"duplicate passage_id in document: {passage.passage_id!r}")
            seen.add(passage.passage_id)
        return self


class FetchedArtifact(BaseModel):
    """What Lane H persists to disk for each fetched document.

    Lane H's document_fetch tool writes one JSON file per artifact to a
    configurable directory. This model is the in-memory representation of
    that file. Content is stored in one of two fields depending on the
    MIME type and Lane H's extraction policy:

    - ``content_text``: the primary textual representation (HTML body or
      pre-extracted PDF text).
    - ``content_bytes_b64``: base64-encoded raw bytes, preserved when Lane H
      was unable or unwilling to extract text (e.g. binary-only PDFs).

    At least one of these must be present.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    artifact_id: str = Field(description="Stable identifier assigned by Lane H")
    url: str = Field(min_length=1, description="Requested URL")
    canonical_url: str | None = Field(
        default=None, description="Canonical form of the URL after redirects/normalization"
    )
    redirect_chain: list[str] = Field(
        default_factory=list,
        description="URLs traversed during the fetch (excluding the final URL)",
    )
    mime_type: str = Field(
        default="application/octet-stream",
        min_length=1,
        description="Content MIME type as reported by the fetcher",
    )
    content_hash: str = Field(
        description="SHA-256 of the canonical content bytes (64-char lowercase hex)"
    )
    title: str | None = Field(default=None, description="Document title if known")
    fetched_at: datetime = Field(description="When Lane H completed the fetch")
    coverage: Coverage = Field(description="Fetch coverage/completeness record")
    content_text: str | None = Field(default=None, description="Extracted or provided text content")
    content_bytes_b64: str | None = Field(
        default=None, description="Base64 of raw bytes when text is not available"
    )
    snippet: str | None = Field(
        default=None, description="Short preview string (e.g. search-result snippet)"
    )
    source_family: SourceFamily = Field(
        default=SourceFamily.UNKNOWN,
        description="Coarse origin family inferred by Lane H, if any",
    )
    audit: dict[str, Any] = Field(
        default_factory=dict,
        description="Lane H audit metadata (opaque; carried forward unchanged)",
    )

    @field_validator("artifact_id")
    @classmethod
    def _artifact_id_format(cls, v: str) -> str:
        if not _ARTIFACT_ID.fullmatch(v):
            raise ValueError(f"artifact_id has invalid format: {v!r}")
        return v

    @field_validator("content_hash")
    @classmethod
    def _content_hash_format(cls, v: str) -> str:
        if not _SHA256_HEX.fullmatch(v):
            raise ValueError("content_hash must be a 64-character lowercase hex string (SHA-256)")
        return v

    @model_validator(mode="after")
    def _has_content_payload(self) -> FetchedArtifact:
        if self.content_text is None and self.content_bytes_b64 is None:
            raise ValueError(
                "FetchedArtifact must carry at least one of content_text or content_bytes_b64"
            )
        return self


class EvidencePrepRecord(BaseModel):
    """Per-passage normalized record handed to the research pipeline.

    This is the single hand-off type out of Lane E. It preserves the full
    provenance chain (artifact_id, canonical_url, content_hash, coverage,
    source_family, parser identity, locator, parse confidence) so nothing
    downstream needs to re-read Lane H artifacts to reason about quality.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str = Field(description="Lane E-unique record identifier")
    artifact_id: str = Field(description="Originating FetchedArtifact")
    canonical_url: str = Field(
        min_length=1,
        description="Canonical URL -- falls back to the fetched URL when no canonical was recorded",
    )
    content_hash: str = Field(description="SHA-256 of the source artifact's canonical bytes")
    coverage: Coverage = Field(description="Lane H coverage, carried forward unchanged")
    source_family: SourceFamily = Field(description="Origin family, carried forward")
    parser: ParserIdentity = Field(description="Parser that produced the underlying passage")
    locator: Locator = Field(description="Where this passage lives in the source")
    passage_kind: PassageKind = Field(description="Structural role of the passage")
    text: str = Field(min_length=1, description="Passage text")
    parse_confidence: ParseConfidence = Field(description="Per-passage parse quality signal")
    fetched_at: datetime = Field(description="When Lane H completed the source fetch")
    title: str | None = Field(default=None, description="Artifact title if known")

    @field_validator("record_id", "artifact_id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        if not _PASSAGE_ID.fullmatch(v):
            raise ValueError(f"identifier has invalid format: {v!r}")
        return v

    @field_validator("content_hash")
    @classmethod
    def _content_hash_format(cls, v: str) -> str:
        if not _SHA256_HEX.fullmatch(v):
            raise ValueError("content_hash must be a 64-character lowercase hex string (SHA-256)")
        return v

    @field_validator("text")
    @classmethod
    def _text_is_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("evidence text cannot be whitespace-only")
        return v
