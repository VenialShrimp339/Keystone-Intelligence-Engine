"""Sketch of Keystone artifact contract models.

This is a non-runtime sketch for the architecture audit. It is intentionally
small and should be replaced by production Pydantic models during implementation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ArtifactStatus = Literal[
    "draft",
    "awaiting_user",
    "running",
    "failed",
    "complete",
    "superseded",
]


class ArtifactBase(BaseModel):
    artifact_id: str
    artifact_type: str
    schema_version: int = 1
    run_id: str
    created_at: datetime
    updated_at: datetime
    status: ArtifactStatus
    parent_artifact_ids: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ProviderJobArtifact(ArtifactBase):
    artifact_type: Literal["ProviderJobArtifact"] = "ProviderJobArtifact"
    provider: Literal[
        "codex_exec",
        "chatgpt_web",
        "claude_web",
        "openai_api",
        "anthropic_api",
        "manual_upload",
        "deterministic_source",
    ]
    surface: str
    prompt: str
    input_artifact_ids: list[str]
    state_snapshots: list[dict[str, str]] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)


class ResearchReportArtifact(ArtifactBase):
    artifact_type: Literal["ResearchReportArtifact"] = "ResearchReportArtifact"
    report_id: str
    provider_job_id: str
    source_format: Literal["markdown", "html", "pdf", "copied_dom", "text", "json"]
    raw_path: str
    normalized_markdown_path: str
    title: str
    summary: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)


class EvidenceBundleArtifact(ArtifactBase):
    artifact_type: Literal["EvidenceBundleArtifact"] = "EvidenceBundleArtifact"
    evidence_id: str
    issue_node_ids: list[str]
    claim_records: list[dict[str, Any]]
    source_records: list[dict[str, Any]]
    absence_records: list[dict[str, Any]] = Field(default_factory=list)
    coverage_map: dict[str, Any] = Field(default_factory=dict)
    conflict_map: dict[str, Any] = Field(default_factory=dict)

