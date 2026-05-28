"""Pydantic artifact contracts for durable first-slice pipeline state.

These models intentionally describe handoff artifacts rather than database
tables. The first implementation uses a local JSON store so each pipeline
boundary can be inspected, replayed, and tested without running the full
research engine.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(UTC)


def _slug(value: str, *, limit: int = 32) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not slug:
        slug = "artifact"
    return slug[:limit].strip("-") or "artifact"


def make_artifact_id(prefix: str, *parts: object) -> str:
    """Create a stable, human-readable artifact id from semantic parts."""
    joined = "\n".join(str(part) for part in parts if part is not None)
    digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:10]
    seed = _slug(joined, limit=28) if joined else "artifact"
    return f"{_slug(prefix, limit=20)}-{seed}-{digest}"


class ArtifactStatus(StrEnum):
    """Lifecycle state shared by durable artifacts."""

    CREATED = "created"
    PENDING_APPROVAL = "pending_approval"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"
    SUPERSEDED = "superseded"


class ApprovalStatus(StrEnum):
    """Human review state for artifacts that should not silently launch work."""

    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    APPROVED = "approved"
    REJECTED = "rejected"


class ProviderKind(StrEnum):
    """Research-capable model provider."""

    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    CODEX = "codex"
    LOCAL = "local"
    OTHER = "other"


class ProviderSurface(StrEnum):
    """How a provider job was accessed."""

    WEB = "web"
    CLI = "cli"
    API = "api"
    MANUAL_UPLOAD = "manual_upload"
    LOCAL_FIXTURE = "local_fixture"


class ProviderJobStatus(StrEnum):
    """Observed provider lifecycle state."""

    CREATED = "created"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    EXPORTED = "exported"
    FAILED = "failed"
    BLOCKED = "blocked"


class SourceFormat(StrEnum):
    """Input format for uploaded or exported research reports."""

    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    UNKNOWN = "unknown"


class DeliverableType(StrEnum):
    """First-slice deliverable target."""

    MARKDOWN_BRIEF = "markdown_brief"
    PDF = "pdf"
    SLIDE_DECK = "slide_deck"
    SPREADSHEET = "spreadsheet"
    OTHER = "other"


class ArtifactBase(BaseModel):
    """Shared metadata for all durable pipeline artifacts."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    run_id: str
    artifact_type: str
    status: ArtifactStatus = ArtifactStatus.CREATED
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    parent_artifact_ids: list[str] = Field(default_factory=list)
    child_artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunLedger(BaseModel):
    """Top-level manifest for a repeatable local pipeline run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    root_request: str
    status: ArtifactStatus = ArtifactStatus.CREATED
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    artifact_ids: list[str] = Field(default_factory=list)
    child_refs: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Parent artifact id -> child artifact ids.",
    )
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SpecificationArtifact(ArtifactBase):
    """Human-reviewable L0 research specification and plan."""

    artifact_type: str = "specification"
    question: str
    engagement_type: str | None = None
    domain: str | None = None
    decision_context: str | None = None
    day_1_hypothesis: str | None = None
    output_target: str | None = None
    selected_lenses: list[dict[str, Any]] = Field(default_factory=list)
    clarifying_questions: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.REQUIRED


class IssueTreeNodeArtifact(ArtifactBase):
    """Durable representation of a researchable issue-tree node."""

    artifact_type: str = "issue_tree_node"
    node_id: str
    name: str
    description: str
    parent_node_id: str | None = None
    child_node_ids: list[str] = Field(default_factory=list)
    lens_annotations: dict[str, str] = Field(default_factory=dict)
    research_questions: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.REQUIRED


class IssueTreePackageArtifact(ArtifactBase):
    """Durable specification-stage issue-tree package."""

    artifact_type: str = "issue_tree_package"
    package: dict[str, Any]
    approval_status: ApprovalStatus = ApprovalStatus.REQUIRED


class ProviderJobArtifact(ArtifactBase):
    """Provider/browser/CLI job lifecycle proof."""

    artifact_type: str = "provider_job"
    provider: ProviderKind = ProviderKind.OTHER
    surface: ProviderSurface = ProviderSurface.WEB
    provider_status: ProviderJobStatus = ProviderJobStatus.CREATED
    model_name: str | None = None
    tool_name: str | None = None
    prompt: str
    selected_model_evidence: str | None = None
    job_url: str | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    exported_at: datetime | None = None
    trace_paths: list[str] = Field(default_factory=list)
    export_paths: list[str] = Field(default_factory=list)
    block_reason: str | None = None


class SourceBundleArtifact(ArtifactBase):
    """Normalized source inventory extracted from one or more reports."""

    artifact_type: str = "source_bundle"
    report_artifact_ids: list[str] = Field(default_factory=list)
    source_records: list[dict[str, Any]] = Field(default_factory=list)
    extraction_method: str = "manual_report_adapter"

    @property
    def source_count(self) -> int:
        return len(self.source_records)


class ResearchReportArtifact(ArtifactBase):
    """Normalized imported research report."""

    artifact_type: str = "research_report"
    provider_job_id: str | None = None
    title: str
    source_format: SourceFormat = SourceFormat.UNKNOWN
    issue_node_ids: list[str] = Field(default_factory=list)
    raw_path: str | None = None
    normalized_path: str | None = None
    section_records: list[dict[str, Any]] = Field(default_factory=list)
    source_records: list[dict[str, Any]] = Field(default_factory=list)
    candidate_claim_records: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)


class EvidenceBundleArtifact(ArtifactBase):
    """Claims, citations, and quality gaps ready for synthesis/evaluation."""

    artifact_type: str = "evidence_bundle"
    report_artifact_ids: list[str] = Field(default_factory=list)
    source_bundle_artifact_id: str | None = None
    claim_records: list[dict[str, Any]] = Field(default_factory=list)
    source_records: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)

    @property
    def cited_claim_count(self) -> int:
        return sum(1 for claim in self.claim_records if claim.get("citation_ids"))

    @property
    def uncited_claim_count(self) -> int:
        return sum(1 for claim in self.claim_records if not claim.get("citation_ids"))


class SynthesisArtifact(ArtifactBase):
    """Minimal synthesis layer output for the first vertical slice."""

    artifact_type: str = "synthesis"
    input_artifact_ids: list[str] = Field(default_factory=list)
    thesis: str
    branch_summaries: list[dict[str, Any]] = Field(default_factory=list)
    evidence_map: dict[str, list[str]] = Field(default_factory=dict)
    gap_questions: list[str] = Field(default_factory=list)
    markdown_path: str | None = None


class EvaluationArtifact(ArtifactBase):
    """Deterministic checks against a target artifact."""

    artifact_type: str = "evaluation"
    target_artifact_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class DeliverableArtifact(ArtifactBase):
    """Pointer to a generated final or interim deliverable."""

    artifact_type: str = "deliverable"
    deliverable_type: DeliverableType = DeliverableType.MARKDOWN_BRIEF
    title: str
    path: str
    input_artifact_ids: list[str] = Field(default_factory=list)
    quality_gate_artifact_ids: list[str] = Field(default_factory=list)
