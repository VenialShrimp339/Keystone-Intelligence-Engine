"""Citation and claim data models for the Keystone Intelligence Engine.

Based on Component #2 schemas in PHASE-1-IMPLEMENTATION-SPEC.md.
Citations are the atomic unit of evidence provenance. Claims are the
intermediate representation at the L1.5->L2 handoff boundary.
"""

from __future__ import annotations

import re
from datetime import date, datetime  # noqa: TC003 (Pydantic v2 needs runtime access)
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    """Classification of a citation's source origin."""

    ACADEMIC = "academic"
    NEWS = "news"
    FILING = "filing"
    REPORT = "report"
    GOVERNMENT = "government"
    INTERNAL = "internal"


class ConfidenceTier(StrEnum):
    """Five-tier confidence taxonomy grounded in DiscoUQ (Section 4.3).

    The weak tier (50-60%) is where simple voting fails and computational
    confidence features provide the largest improvement over naive agreement.
    """

    HIGH = "high_above_80"
    MODERATE = "moderate_60_80"
    WEAK = "weak_50_60"
    CONTESTED = "contested_below_50"
    INSUFFICIENT = "insufficient_evidence"


class ACHDiagnosticity(StrEnum):
    """How well a piece of evidence discriminates between competing hypotheses."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    """A single source reference with verification metadata.

    Every claim in the pipeline traces back to one or more Citations.
    The quality_score uses Admiralty Code composite scoring (source
    reliability x information credibility).
    """

    model_config = ConfigDict(frozen=True)

    citation_id: str = Field(description="Unique identifier, format CIT-NNN")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing (Gap #2)")
    url: str = Field(description="Source URL")
    doi: str | None = Field(default=None, description="Digital Object Identifier if available")
    title: str = Field(description="Title of the source document")
    authors: list[str] = Field(default_factory=list, description="Author names")
    publication: str = Field(default="", description="Publication or outlet name")
    date_published: date | None = Field(
        default=None, description="Publication date (ISO 8601)"
    )
    access_date: datetime = Field(description="When this source was accessed")
    source_type: SourceType = Field(description="Classification of source origin")
    quality_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Admiralty Code composite: reliability x credibility, 0-1 scale",
    )
    url_live: bool | None = Field(
        default=None, description="Whether URL was reachable at verification time"
    )
    crossref_verified: bool | None = Field(
        default=None, description="Whether citation exists in CrossRef/Semantic Scholar/OpenAlex"
    )
    found_by_agents: list[str] = Field(
        default_factory=list,
        description="Agent IDs that independently discovered this source",
    )
    content_hash: str | None = Field(
        default=None,
        description="SHA-256 hash of the source content at access time. "
        "Enables provenance tracking in compiled wiki (Karpathy pattern). "
        "None for citations not yet hash-verified.",
    )

    @field_validator("citation_id")
    @classmethod
    def validate_citation_id(cls, v: str) -> str:
        if not v.startswith("CIT-"):
            raise ValueError("citation_id must start with 'CIT-'")
        return v

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", v):
                raise ValueError(
                    "content_hash must be a 64-character lowercase hex string (SHA-256)"
                )
        return v


class Claim(BaseModel):
    """A synthesized analytical claim with full provenance chain.

    Claims are the intermediate representation at the L1.5->L2 handoff.
    Each claim traces to specific source chunks and citations, carries
    a confidence assessment, and records how many agents independently
    corroborated it.
    """

    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(description="Unique identifier, format CLM-NNN")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    text: str = Field(description="The claim statement")
    source_chunk_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source text chunks supporting this claim",
    )
    citation_ids: list[str] = Field(
        description="References to Citation entities backing this claim"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Numerical confidence score"
    )
    corroboration_count: int = Field(
        ge=0,
        description="Number of agents that independently found supporting evidence",
    )
    provenance_chain: str = Field(
        description="Trace from claim -> citations -> source documents"
    )
    confidence_tier: ConfidenceTier = Field(
        description="Discrete confidence tier derived from numerical confidence"
    )
    ach_diagnosticity: ACHDiagnosticity | None = Field(
        default=None,
        description="How well this evidence discriminates between hypotheses",
    )
    proposition_hashes: list[str] = Field(
        default_factory=list,
        description="Content hashes of the specific propositions supporting this claim. "
        "Enables fine-grained provenance from claim -> proposition -> source.",
    )

    @field_validator("claim_id")
    @classmethod
    def validate_claim_id(cls, v: str) -> str:
        if not v.startswith("CLM-"):
            raise ValueError("claim_id must start with 'CLM-'")
        return v


class CorroborationPair(BaseModel):
    """Records when two citations independently support the same finding."""

    citation_a: str = Field(description="First citation ID")
    citation_b: str = Field(description="Second citation ID")
    overlap_score: float = Field(
        ge=0.0, le=1.0, description="Degree of evidentiary overlap"
    )


class CitationManifest(BaseModel):
    """Output of the CitationProcessor: deduplicated, verified citation inventory.

    This is the single source of truth for all citations in an engagement.
    The Evaluator's Layer 2 citation gate checks against this manifest.
    """

    manifest_id: str = Field(description="Unique manifest identifier")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    citations: list[Citation] = Field(
        default_factory=list, description="All deduplicated citations"
    )
    corroboration_pairs: list[CorroborationPair] = Field(
        default_factory=list,
        description="Pairs of citations with overlapping evidence",
    )
    dead_urls: list[str] = Field(
        default_factory=list, description="Citation IDs with unreachable URLs"
    )
    fabrication_flags: list[str] = Field(
        default_factory=list,
        description="Citation IDs flagged as potentially fabricated",
    )


class WikiCompilationRecord(BaseModel):
    """Tracks how a citation's content was compiled into the engagement wiki.

    Part of the Karpathy three-layer pattern (raw/compiled/INDEX.md).
    Content-hash provenance links compiled propositions back to raw
    source artifacts for full traceability.
    """

    citation_id: str = Field(description="Citation this record tracks")
    engagement_id: str = Field(description="Parent engagement")
    raw_path: str = Field(description="Path in raw/ directory")
    compiled_path: str | None = Field(
        default=None, description="Path in compiled/ directory (None if not yet compiled)"
    )
    content_hash: str = Field(description="SHA-256 of source content")
    compiled_at: datetime | None = Field(default=None, description="When compilation occurred")
