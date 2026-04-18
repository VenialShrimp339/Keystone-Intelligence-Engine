"""Pydantic v2 models for the retrieval search sub-package.

Everything that flows between chunker -> embedder -> vector store -> BM25
-> hybrid search -> reranker -> caller is modelled here. Frozen where
the identity of the object matters (chunks, search queries, ingest
results); unfrozen where downstream components may want to re-sort or
annotate (retrieval results carry a mutable ``score`` while moving
through RRF and reranking).

A chunk is uniquely identified by ``chunk_id`` (``{artifact_id}:{seq}``).
Ingest is idempotent: calling ``upsert`` with the same chunk_id replaces
the existing row, preserving the referential stability of downstream
citations.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from keystone.retrieval.parse_models import (  # noqa: TC001 (Pydantic v2 needs runtime access)
    Locator,
    ParseConfidence,
    SourceFamily,
)

_CHUNK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-:.]{0,255}")
_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class RetrievalSource(StrEnum):
    """Where a retrieval result originated from in the hybrid pipeline."""

    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"
    RERANKED = "reranked"


class QueryClassification(StrEnum):
    """How the :class:`QueryRouter` routed a query.

    The classifier looks at the query text only; the caller decides
    which downstream pipeline to run. ``HYBRID`` means "run both
    structured and unstructured paths and merge results."
    """

    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    HYBRID = "hybrid"


class ChunkMetadata(BaseModel):
    """Provenance + quality metadata preserved from Lane E on every chunk.

    The metadata is frozen so downstream cannot silently rewrite the
    provenance chain. Serialization to the database flattens this into
    a JSONB column.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str = Field(min_length=1, description="Originating FetchedArtifact")
    canonical_url: str = Field(min_length=1, description="Canonical URL of the source")
    content_hash: str = Field(description="SHA-256 of the source artifact (lowercase hex)")
    source_family: SourceFamily = Field(description="Coarse origin family")
    locator: Locator = Field(description="Where the passage lives in the source")
    parse_confidence: ParseConfidence = Field(description="Per-passage parse quality")
    title: str | None = Field(default=None, description="Artifact title if known")
    fetched_at: datetime | None = Field(default=None, description="When Lane H completed the fetch")
    record_ids: list[str] = Field(
        default_factory=list,
        description=(
            "EvidencePrepRecord record_ids merged into this chunk. Multiple "
            "short passages may fold into one chunk; this preserves the "
            "upstream link."
        ),
    )
    engagement_id: str | None = Field(
        default=None,
        description=(
            "Engagement that ingested this chunk. When set, search callers "
            "can use SearchQuery.exclude_engagement_id to suppress current-"
            "engagement chunks from another agent's view (inter-agent "
            "isolation invariant). ``None`` means the chunk is institutional "
            "memory and is always visible."
        ),
    )

    @field_validator("content_hash")
    @classmethod
    def _content_hash_format(cls, v: str) -> str:
        if not _SHA256_HEX.fullmatch(v):
            raise ValueError("content_hash must be a 64-character lowercase hex string (SHA-256)")
        return v


class DocumentChunk(BaseModel):
    """A searchable chunk of a document.

    The chunk ``content`` is what gets embedded and searched -- it may
    include a contextual preamble that is not literally present in the
    source (see :class:`SemanticChunker`). The ``raw_text`` field holds
    the unprefixed passage text so downstream can cite it verbatim.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    chunk_id: str = Field(description="Document-unique identifier, '{artifact}:{seq}'")
    content: str = Field(min_length=1, description="Embedded/indexed text (may include preamble)")
    raw_text: str = Field(min_length=1, description="Original passage text without preamble")
    metadata: ChunkMetadata = Field(description="Provenance + quality metadata")
    embedding: list[float] | None = Field(
        default=None,
        description="Dense embedding vector. None until the embedder runs.",
    )
    token_count: int = Field(ge=1, description="Word-count proxy for token length")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this chunk record was produced",
    )

    @field_validator("chunk_id")
    @classmethod
    def _chunk_id_format(cls, v: str) -> str:
        if not _CHUNK_ID.fullmatch(v):
            raise ValueError(f"chunk_id has invalid format: {v!r}")
        return v

    @field_validator("content", "raw_text")
    @classmethod
    def _text_is_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("chunk text cannot be whitespace-only")
        return v

    @field_validator("embedding")
    @classmethod
    def _embedding_values_are_finite(cls, v: list[float] | None) -> list[float] | None:
        if v is None:
            return None
        import math

        for i, value in enumerate(v):
            if not math.isfinite(value):
                raise ValueError(f"embedding[{i}] is not finite: {value!r}")
        return v

    def with_embedding(self, embedding: list[float]) -> DocumentChunk:
        """Return a copy of this chunk with ``embedding`` set."""

        return self.model_copy(update={"embedding": embedding})


class SearchQuery(BaseModel):
    """User- or agent-supplied search request.

    Frozen so downstream pipeline steps cannot silently rewrite query
    semantics. Filters are opaque key/value pairs whose interpretation
    is up to the vector store implementation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(min_length=1, description="Natural-language query")
    top_k: int = Field(default=20, ge=1, le=500, description="How many results to return")
    candidate_pool: int = Field(
        default=150,
        ge=1,
        le=2000,
        description=(
            "How many candidates each retriever (vector, BM25) should "
            "produce before fusion + reranking."
        ),
    )
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Optional metadata filters applied during vector search. "
            "Supported keys: artifact_id, source_family."
        ),
    )
    exclude_engagement_id: str | None = Field(
        default=None,
        description=(
            "When set, suppresses chunks tagged with this engagement_id "
            "from the result set. Used by research agents during an "
            "active engagement so they cannot see other agents' "
            "intermediate ingest from the same engagement (inter-agent "
            "isolation invariant). Chunks with engagement_id=None "
            "(institutional memory) and chunks from OTHER engagements "
            "remain visible. Isolation is applied automatically when "
            "the enclosing RetrievalService was constructed with an "
            "``engagement_context`` and the caller made a string-form "
            "search call. A raw SearchQuery instance is honored "
            "literally: ``exclude_engagement_id=None`` on such a "
            "query is read as 'the caller is explicitly opting out of "
            "isolation', and the service-level context is not "
            "substituted. Callers that build their own query object "
            "are trusted to name their intent."
        ),
    )

    @field_validator("text")
    @classmethod
    def _text_is_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query text cannot be whitespace-only")
        return v

    @model_validator(mode="after")
    def _candidate_pool_ge_top_k(self) -> SearchQuery:
        if self.candidate_pool < self.top_k:
            raise ValueError(
                f"candidate_pool ({self.candidate_pool}) must be >= top_k ({self.top_k})"
            )
        return self


class RetrievalResult(BaseModel):
    """A scored chunk returned by a retriever, fusion step, or reranker.

    Unfrozen because the hybrid path annotates results in place as they
    progress through the pipeline (assigning ``rrf_score``, then
    ``rerank_score`` without allocating new model instances per step).
    """

    model_config = ConfigDict(extra="forbid")

    chunk: DocumentChunk = Field(description="The matched chunk")
    score: float = Field(
        description="Current best score (vector, RRF, or rerank, depending on source)"
    )
    source: RetrievalSource = Field(description="Which retrieval path produced the current score")
    rank: int = Field(ge=1, description="One-based rank at the time of scoring")
    vector_score: float | None = Field(
        default=None, description="Cosine similarity from vector search if present"
    )
    bm25_score: float | None = Field(default=None, description="Raw BM25 score if present")
    rrf_score: float | None = Field(default=None, description="RRF fusion score if hybrid was run")
    rerank_score: float | None = Field(
        default=None, description="Cohere rerank score if reranking was applied"
    )


class IngestResult(BaseModel):
    """Summary of a single ingest call."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifacts_ingested: int = Field(ge=0, description="Distinct artifacts seen in this batch")
    chunks_created: int = Field(ge=0, description="New chunks written to the store")
    chunks_updated: int = Field(ge=0, description="Existing chunks overwritten via upsert")
    chunks_skipped: int = Field(
        ge=0,
        description=(
            "Chunks skipped because they were empty, duplicate, or failed "
            "validation (counted but not raised, so the caller still sees a batch result)."
        ),
    )


class QueryRoute(BaseModel):
    """Classifier decision from :class:`QueryRouter`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    classification: QueryClassification = Field(description="Assigned class")
    confidence: float = Field(ge=0.0, le=1.0, description="Classifier confidence on [0,1]")
    reason: str = Field(
        min_length=1,
        description="Short explanation ('matched ratio/percent pattern', 'LLM judgement', ...)",
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Triggering tokens or rule IDs useful for debugging",
    )
