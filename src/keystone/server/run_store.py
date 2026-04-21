"""In-memory run store for the v0.1 single-user serving layer."""

from __future__ import annotations

import asyncio
import contextlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from keystone.server.models import (
    PipelineEventEnvelope,
    PipelineEventMessage,
    PipelineResultDTO,
    ResultReadyMessage,
    ResultReadySummary,
    RunDetail,
    RunError,
    RunErrorKind,
    RunPhase,
    RunProgress,
    RunSnapshotMessage,
    RunStateMessage,
    RunStatus,
    RunSummary,
    StreamErrorMessage,
    StreamMessage,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

    from keystone.pipeline.orchestrator import PipelineResult

BASE_EVENT_FIELDS = {"event_id", "engagement_id", "client_id", "timestamp", "layer"}


@dataclass
class _RunRecord:
    id: str
    question: str
    client_id: str
    client_context: str | None
    title: str
    created_at: datetime
    phase: RunPhase = RunPhase.QUEUED
    status: RunStatus = RunStatus.QUEUED
    engagement_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    events: list[PipelineEventEnvelope] = field(default_factory=list)
    result: PipelineResult | None = None
    total_tokens: int = 0
    tokens_by_layer: dict[str, int] = field(default_factory=dict)
    active_gate_id: str | None = None
    error: RunError | None = None
    progress: RunProgress = field(default_factory=RunProgress)


class RunStore:
    """Thread-local, asyncio-safe storage for run state and event history."""

    def __init__(self) -> None:
        self._runs: dict[str, _RunRecord] = {}
        self._subscribers: dict[str, list[asyncio.Queue[StreamMessage]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def create_run(
        self,
        *,
        question: str,
        client_id: str,
        client_context: str | None,
    ) -> RunSummary:
        run_id = f"run_{uuid4().hex[:12]}"
        title = _title_from_question(question)
        now = _now()
        record = _RunRecord(
            id=run_id,
            question=question,
            client_id=client_id,
            client_context=client_context,
            title=title,
            created_at=now,
        )
        async with self._lock:
            self._runs[run_id] = record
            return self._summary(record, now=now)

    async def exists(self, run_id: str) -> bool:
        async with self._lock:
            return run_id in self._runs

    async def list_runs(self) -> list[RunSummary]:
        async with self._lock:
            now = _now()
            records = sorted(self._runs.values(), key=lambda run: run.created_at, reverse=True)
            return [self._summary(record, now=now) for record in records]

    async def get_summary(self, run_id: str) -> RunSummary | None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return None
            return self._summary(record)

    async def get_detail(self, run_id: str) -> RunDetail | None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return None
            return self._detail(record)

    async def get_result(self, run_id: str) -> PipelineResultDTO | None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record is None or record.result is None:
                return None
            return _result_to_dto(record.result)

    async def get_events(self, run_id: str) -> list[PipelineEventEnvelope] | None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return None
            return list(record.events)

    async def get_snapshot(
        self,
        run_id: str,
        *,
        recent_limit: int = 200,
    ) -> RunSnapshotMessage | None:
        async with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return None
            return RunSnapshotMessage(
                run=self._summary(record),
                recent_events=record.events[-recent_limit:],
                active_gate=None,
            )

    async def subscribe(self, run_id: str) -> asyncio.Queue[StreamMessage] | None:
        async with self._lock:
            if run_id not in self._runs:
                return None
            queue: asyncio.Queue[StreamMessage] = asyncio.Queue(maxsize=1000)
            self._subscribers[run_id].append(queue)
            return queue

    async def unsubscribe(self, run_id: str, queue: asyncio.Queue[StreamMessage]) -> None:
        async with self._lock:
            queues = self._subscribers.get(run_id)
            if queues is None:
                return
            with contextlib.suppress(ValueError):
                queues.remove(queue)
            if not queues:
                self._subscribers.pop(run_id, None)

    async def mark_started(self, run_id: str) -> None:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            now = _now()
            record.started_at = record.started_at or now
            record.status = RunStatus.RUNNING
            record.phase = RunPhase.SPEC
            record.error = None
            self._publish_state(record, previous, "Planning the engagement...", now)

    async def append_event(self, run_id: str, envelope: PipelineEventEnvelope) -> None:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            record.events.append(envelope)
            record.engagement_id = envelope.engagement_id or record.engagement_id
            record.client_id = envelope.client_id or record.client_id
            self._apply_event_progress(record, envelope)
            self._apply_event_state(record, envelope)
            self._publish(
                run_id,
                PipelineEventMessage(run_id=run_id, event=envelope),
            )
            if record.phase != previous or envelope.event_type == "ReviewGateCreated":
                self._publish_state(record, previous, _state_message(record.phase))

    async def mark_rendering(self, run_id: str) -> None:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            if record.status not in {RunStatus.STOPPING, RunStatus.FAILED}:
                record.status = RunStatus.RUNNING
            record.phase = RunPhase.RENDERING
            self._publish_state(record, previous, "Assembling the final brief...")

    async def complete_run(self, run_id: str, result: PipelineResult) -> None:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            record.result = result
            record.engagement_id = result.engagement_id
            record.client_id = result.client_id
            record.total_tokens = result.total_tokens
            record.tokens_by_layer = dict(result.tokens_by_layer)
            record.completed_at = _now()
            record.phase = RunPhase.COMPLETE
            record.status = RunStatus.COMPLETE
            record.error = None
            self._publish_state(record, previous, "Final brief ready.", record.completed_at)
            evaluations = result.evaluation_results
            self._publish(
                run_id,
                ResultReadyMessage(
                    run_id=run_id,
                    result_url=f"/api/runs/{run_id}",
                    summary=ResultReadySummary(
                        markdown_chars=len(result.markdown_output),
                        total_tokens=result.total_tokens,
                        total_events=result.total_events,
                        passed_evaluations=sum(
                            1 for evaluation in evaluations if evaluation.passed
                        ),
                        total_evaluations=len(evaluations),
                    ),
                ),
            )

    async def mark_stopping(self, run_id: str) -> RunSummary:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            if record.status not in {RunStatus.COMPLETE, RunStatus.FAILED}:
                record.status = RunStatus.STOPPING
                self._publish_state(record, previous, "Stopping the run...")
            return self._summary(record)

    async def mark_stopped(self, run_id: str) -> None:
        await self.mark_failed(
            run_id,
            RunError(
                kind=RunErrorKind.STOPPED,
                message="Run stopped by user request.",
            ),
        )

    async def mark_failed(self, run_id: str, error: RunError) -> None:
        async with self._lock:
            record = self._require(run_id)
            previous = record.phase
            record.completed_at = record.completed_at or _now()
            record.phase = RunPhase.FAILED
            record.status = RunStatus.FAILED
            record.error = error
            self._publish_state(record, previous, error.message, record.completed_at)
            self._publish(
                run_id,
                StreamErrorMessage(run_id=run_id, error=error, sent_at=record.completed_at),
            )

    def _require(self, run_id: str) -> _RunRecord:
        record = self._runs.get(run_id)
        if record is None:
            raise KeyError(run_id)
        return record

    def _summary(self, record: _RunRecord, *, now: datetime | None = None) -> RunSummary:
        now = now or _now()
        return RunSummary(
            id=record.id,
            engagement_id=record.engagement_id,
            client_id=record.client_id,
            title=record.title,
            question=record.question,
            phase=record.phase,
            status=record.status,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            elapsed_ms=_elapsed_ms(record, now),
            event_count=len(record.events),
            total_tokens=record.total_tokens,
            tokens_by_layer=record.tokens_by_layer,
            active_gate_id=record.active_gate_id,
            error=record.error,
        )

    def _detail(self, record: _RunRecord) -> RunDetail:
        summary = self._summary(record)
        markdown = record.result.markdown_output if record.result is not None else None
        spec = _model_to_json(record.result.spec) if record.result is not None else None
        return RunDetail(
            **summary.model_dump(mode="python"),
            spec=spec,
            result_available=record.result is not None,
            markdown_preview=_markdown_preview(markdown),
        )

    def _publish_state(
        self,
        record: _RunRecord,
        previous_phase: RunPhase | None,
        message: str,
        sent_at: datetime | None = None,
    ) -> None:
        self._publish(
            record.id,
            RunStateMessage(
                run_id=record.id,
                previous_phase=previous_phase,
                phase=record.phase,
                status=record.status,
                message=message,
                progress=record.progress,
                sent_at=sent_at or _now(),
            ),
        )

    def _publish(self, run_id: str, message: StreamMessage) -> None:
        for queue in self._subscribers.get(run_id, []):
            if queue.full():
                with contextlib.suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(message)

    def _apply_event_progress(
        self,
        record: _RunRecord,
        envelope: PipelineEventEnvelope,
    ) -> None:
        payload = envelope.payload
        progress = record.progress.model_copy()
        if envelope.event_type == "TasksDecomposed":
            progress.total_tasks = _int_payload(payload, "task_count", progress.total_tasks)
            progress.total_agents = max(progress.total_agents, progress.total_tasks)
        elif envelope.event_type == "AgentDispatched":
            if progress.total_tasks == 0:
                progress.total_agents += 1
        elif envelope.event_type == "ResearchComplete":
            progress.completed_agents += 1
        elif envelope.event_type == "ManifestProduced":
            progress.citations_total = _int_payload(
                payload,
                "total_citations",
                progress.citations_total,
            )
        elif envelope.event_type == "EvaluationComplete":
            progress.evaluations_complete += 1
            progress.completed_tasks += 1
        record.progress = progress

    def _apply_event_state(
        self,
        record: _RunRecord,
        envelope: PipelineEventEnvelope,
    ) -> None:
        if record.status in {RunStatus.COMPLETE, RunStatus.FAILED}:
            return

        if envelope.event_type == "ReviewGateCreated":
            record.phase = RunPhase.PAUSED
            record.status = RunStatus.PAUSED
            gate_id = envelope.payload.get("gate_id")
            record.active_gate_id = gate_id if isinstance(gate_id, str) else None
            return

        if envelope.event_type == "ReviewGateRejected":
            record.phase = RunPhase.FAILED
            record.status = RunStatus.FAILED
            record.active_gate_id = None
            record.error = RunError(
                kind=RunErrorKind.REJECTED,
                message="Run rejected at human review gate.",
            )
            return

        if envelope.event_type in {"ReviewGateApproved", "ReviewGateModified"}:
            record.active_gate_id = None

        if record.status != RunStatus.STOPPING:
            record.status = RunStatus.RUNNING
        record.phase = _phase_for_layer(envelope.layer)


def envelope_from_event(event: BaseModel) -> PipelineEventEnvelope:
    """Wrap a typed pipeline event with the UI discriminator contract."""

    data = event.model_dump(mode="json")
    payload = {key: value for key, value in data.items() if key not in BASE_EVENT_FIELDS}
    return PipelineEventEnvelope(
        event_type=event.__class__.__name__,
        event_id=data["event_id"],
        engagement_id=data["engagement_id"],
        client_id=data["client_id"],
        timestamp=data["timestamp"],
        layer=data["layer"],
        payload=payload,
    )


def _phase_for_layer(layer: str) -> RunPhase:
    return {
        "L0": RunPhase.SPEC,
        "L1": RunPhase.RESEARCH,
        "Retrieval": RunPhase.RESEARCH,
        "CitationProcessor": RunPhase.CITATION,
        "L1.5": RunPhase.DELIBERATION,
        "L2": RunPhase.STRUCTURING,
        "L3": RunPhase.RENDERING,
        "L4": RunPhase.EVALUATION,
        "L5": RunPhase.EVALUATION,
        "HITL": RunPhase.PAUSED,
        "META": RunPhase.EVALUATION,
    }.get(layer, RunPhase.RESEARCH)


def _state_message(phase: RunPhase) -> str:
    return {
        RunPhase.QUEUED: "Queued.",
        RunPhase.SPEC: "Planning the engagement...",
        RunPhase.RESEARCH: "Research agents are gathering evidence...",
        RunPhase.CITATION: "Checking evidence and citations...",
        RunPhase.DELIBERATION: "Analysts are reviewing findings...",
        RunPhase.STRUCTURING: "Structuring the brief...",
        RunPhase.EVALUATION: "Quality review is running...",
        RunPhase.RENDERING: "Assembling the final brief...",
        RunPhase.COMPLETE: "Final brief ready.",
        RunPhase.PAUSED: "Waiting for review.",
        RunPhase.FAILED: "Run failed.",
    }[phase]


def _result_to_dto(result: PipelineResult) -> PipelineResultDTO:
    data = result.model_dump(mode="json")
    return PipelineResultDTO(**data)


def _model_to_json(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _title_from_question(question: str) -> str:
    compact = " ".join(question.strip().split())
    return compact[:77] + "..." if len(compact) > 80 else compact


def _markdown_preview(markdown: str | None) -> str | None:
    if not markdown:
        return None
    compact = markdown.strip()
    return compact[:497] + "..." if len(compact) > 500 else compact


def _elapsed_ms(record: _RunRecord, now: datetime) -> int:
    start = record.started_at or record.created_at
    end = record.completed_at or now
    return max(0, int((end - start).total_seconds() * 1000))


def _int_payload(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key)
    return value if isinstance(value, int) else default


def _now() -> datetime:
    return datetime.now(UTC)
