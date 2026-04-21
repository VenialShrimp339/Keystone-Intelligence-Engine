"""Pydantic API models for the Keystone v0.1 serving layer."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic resolves postponed model fields.
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

JsonObject = dict[str, Any]


class APIModel(BaseModel):
    """Base model with JSON-friendly enum serialization."""

    model_config = ConfigDict(use_enum_values=True)


class RunPhase(StrEnum):
    QUEUED = "QUEUED"
    SPEC = "SPEC"
    RESEARCH = "RESEARCH"
    CITATION = "CITATION"
    DELIBERATION = "DELIBERATION"
    STRUCTURING = "STRUCTURING"
    EVALUATION = "EVALUATION"
    RENDERING = "RENDERING"
    COMPLETE = "COMPLETE"
    PAUSED = "PAUSED"
    FAILED = "FAILED"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    COMPLETE = "complete"
    FAILED = "failed"


class RunErrorKind(StrEnum):
    EXCEPTION = "exception"
    STOPPED = "stopped"
    REJECTED = "rejected"
    GOVERNANCE_HALT = "governance_halt"


PipelineLayer = Literal[
    "L0",
    "L1",
    "CitationProcessor",
    "Retrieval",
    "L1.5",
    "L2",
    "L3",
    "L4",
    "L5",
    "HITL",
    "META",
]

PipelineEventType = Literal[
    "SpecificationGenerated",
    "TasksDecomposed",
    "AgentDispatched",
    "ResearchStarted",
    "SourceFound",
    "CitationExtracted",
    "FindingSynthesized",
    "ResearchComplete",
    "CitationDeduped",
    "CorroborationScored",
    "URLVerified",
    "ManifestProduced",
    "ChunkIngested",
    "SearchCompleted",
    "AnalystSpawned",
    "IndependentAnalysisComplete",
    "AggregationComplete",
    "ConfidenceMapProduced",
    "OutlineGenerated",
    "SectionDrafted",
    "SprintContractProposed",
    "DraftGenerated",
    "CitationFormatted",
    "DeliverableAssembled",
    "DeterministicCheckPassed",
    "CitationGateResult",
    "RubricDimensionScored",
    "ProcessTrajectoryScored",
    "EvaluationComplete",
    "EnsembleJudgeScored",
    "DissenterVetoTriggered",
    "EnsembleEvaluationComplete",
    "ObservationRecorded",
    "PatternPromoted",
    "ConstraintEncoded",
    "ReviewGateCreated",
    "ReviewDecisionSubmitted",
    "ReviewGateApproved",
    "ReviewGateModified",
    "ReviewGateRejected",
]


class PipelineEventEnvelope(APIModel):
    event_type: PipelineEventType
    event_id: str
    engagement_id: str
    client_id: str
    timestamp: datetime
    layer: PipelineLayer
    payload: JsonObject


class RunError(APIModel):
    kind: RunErrorKind
    message: str
    detail: JsonObject | None = None


class RunProgress(APIModel):
    completed_tasks: int = 0
    total_tasks: int = 0
    completed_agents: int = 0
    total_agents: int = 0
    citations_total: int = 0
    evaluations_complete: int = 0


class RunSummary(APIModel):
    id: str
    engagement_id: str | None
    client_id: str
    title: str
    question: str
    phase: RunPhase
    status: RunStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    elapsed_ms: int
    event_count: int
    total_tokens: int
    tokens_by_layer: dict[str, int]
    active_gate_id: str | None
    error: RunError | None


class RunDetail(RunSummary):
    spec: JsonObject | None
    result_available: bool
    markdown_preview: str | None


class PipelineResultDTO(APIModel):
    engagement_id: str
    client_id: str
    spec: JsonObject
    findings: list[JsonObject]
    manifest: JsonObject
    confidence_map: JsonObject
    evaluation_results: list[JsonObject]
    markdown_output: str
    total_tokens: int
    total_events: int
    tokens_by_layer: dict[str, int]


class StartRunRequest(APIModel):
    question: str = Field(min_length=1)
    client_id: str = "local"
    client_context: str | None = None
    pipeline_profile: Literal["light", "standard", "deep"] | None = None
    source_ids: list[str] = Field(default_factory=list)


class StartRunResponse(APIModel):
    run: RunSummary
    websocket_url: str


class ListRunsResponse(APIModel):
    runs: list[RunSummary]


class GetRunResponse(APIModel):
    run: RunDetail
    result: PipelineResultDTO | None


class GetRunEventsResponse(APIModel):
    run_id: str
    events: list[PipelineEventEnvelope]


class StopRunResponse(APIModel):
    run: RunSummary
    accepted: bool


class StreamConnectedMessage(APIModel):
    type: Literal["connected"] = "connected"
    run_id: str
    sent_at: datetime


class RunSnapshotMessage(APIModel):
    type: Literal["run_snapshot"] = "run_snapshot"
    run: RunSummary
    recent_events: list[PipelineEventEnvelope]
    active_gate: JsonObject | None = None


class RunStateMessage(APIModel):
    type: Literal["run_state"] = "run_state"
    run_id: str
    previous_phase: RunPhase | None
    phase: RunPhase
    status: RunStatus
    message: str
    progress: RunProgress
    sent_at: datetime


class PipelineEventMessage(APIModel):
    type: Literal["pipeline_event"] = "pipeline_event"
    run_id: str
    event: PipelineEventEnvelope


class ResultReadySummary(APIModel):
    markdown_chars: int
    total_tokens: int
    total_events: int
    passed_evaluations: int
    total_evaluations: int


class ResultReadyMessage(APIModel):
    type: Literal["result_ready"] = "result_ready"
    run_id: str
    result_url: str
    summary: ResultReadySummary


class StreamErrorMessage(APIModel):
    type: Literal["error"] = "error"
    run_id: str
    error: RunError
    sent_at: datetime


class HeartbeatMessage(APIModel):
    type: Literal["heartbeat"] = "heartbeat"
    run_id: str
    sent_at: datetime


StreamMessage = (
    StreamConnectedMessage
    | RunSnapshotMessage
    | RunStateMessage
    | PipelineEventMessage
    | ResultReadyMessage
    | StreamErrorMessage
    | HeartbeatMessage
)
