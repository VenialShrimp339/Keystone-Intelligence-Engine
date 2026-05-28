"""Browser-provider orchestration and ledger records.

The adapter coordinates a browser controller, the pure DOM completion
detectors, provider-specific export requirements, and report ingestion. It is
controller-agnostic so Chrome, Browser Use, Playwright, or a test fake can
drive the same control-plane truth.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from keystone.artifacts.models import (
    ArtifactStatus,
    ProviderJobArtifact,
    ProviderJobStatus,
    ProviderKind,
    ProviderSurface,
    SourceFormat,
    make_artifact_id,
)
from keystone.ingestion.manual_report import ManualUploadAdapter, ReportIngestionResult
from keystone.providers.browser_watch import (
    BrowserResearchState,
    ProviderCompletionSignal,
    detect_chatgpt_deep_research_state,
    detect_claude_research_state,
)


def _now() -> datetime:
    return datetime.now(UTC)


class ProviderIngestionState(str):
    """Simple string constants for export and ingestion state."""

    NOT_READY = "not_ready"
    READY_TO_INGEST = "ready_to_ingest"
    INGESTED = "ingested"
    REJECTED_INCOMPLETE = "rejected_incomplete"
    FAILED = "failed"


class BrowserTabClaim(BaseModel):
    """Result of opening or claiming a browser provider tab."""

    model_config = ConfigDict(extra="forbid")

    url: str
    tab_id: str | None = None
    claimed_existing: bool = False


class BrowserJobSubmission(BaseModel):
    """Result of submitting a provider research prompt."""

    model_config = ConfigDict(extra="forbid")

    url: str
    submitted_at: datetime = Field(default_factory=_now)
    provider_job_ref: str | None = None


class BrowserSnapshot(BaseModel):
    """Observed provider page state."""

    model_config = ConfigDict(extra="forbid")

    captured_at: datetime = Field(default_factory=_now)
    url: str
    dom_text: str
    screenshot_path: str | None = None


class BrowserProviderExportBundle(BaseModel):
    """Paths and source-recovery evidence exported from a provider job."""

    model_config = ConfigDict(extra="forbid")

    provider: ProviderKind
    report_path: str | None = None
    markdown_path: str | None = None
    docx_source_path: str | None = None
    artifact_path: str | None = None
    source_map_paths: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)
    exported_at: datetime = Field(default_factory=_now)
    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def primary_ingest_path(self) -> str | None:
        """Report path to ingest as the completed report body."""
        return self.markdown_path or self.report_path or self.artifact_path

    @property
    def export_paths(self) -> list[str]:
        paths = [
            self.report_path,
            self.markdown_path,
            self.docx_source_path,
            self.artifact_path,
            *self.source_map_paths,
        ]
        return [path for path in paths if path]


class ProviderSourceRecovery(BaseModel):
    """Source recovery route captured for a provider report."""

    model_config = ConfigDict(extra="forbid")

    route: str
    complete: bool
    source_urls: list[str] = Field(default_factory=list)
    source_paths: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProviderJobSnapshotRecord(BaseModel):
    """Ledger-friendly snapshot record."""

    model_config = ConfigDict(extra="forbid")

    captured_at: datetime
    url: str
    state: BrowserResearchState
    evidence: list[str] = Field(default_factory=list)
    report_title: str | None = None
    source_count: int | None = None
    export_available: bool = False
    screenshot_path: str | None = None


class ProviderJobRecord(BaseModel):
    """Control-plane ledger record for one provider job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    run_id: str
    provider: ProviderKind
    surface: ProviderSurface = ProviderSurface.WEB
    branch_id: str | None = None
    prompt: str
    job_url: str | None = None
    tab_id: str | None = None
    status: ProviderJobStatus = ProviderJobStatus.CREATED
    ingestion_state: str = ProviderIngestionState.NOT_READY
    created_at: datetime = Field(default_factory=_now)
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    exported_at: datetime | None = None
    ingested_at: datetime | None = None
    snapshots: list[ProviderJobSnapshotRecord] = Field(default_factory=list)
    export_paths: list[str] = Field(default_factory=list)
    source_recovery: ProviderSourceRecovery | None = None
    provider_artifact_id: str | None = None
    report_artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    @property
    def latest_signal(self) -> ProviderCompletionSignal | None:
        if not self.snapshots:
            return None
        snapshot = self.snapshots[-1]
        return ProviderCompletionSignal(
            provider=self.provider.value,
            state=snapshot.state,
            evidence=snapshot.evidence,
            report_title=snapshot.report_title,
            source_count=snapshot.source_count,
            export_available=snapshot.export_available,
        )

    def to_provider_artifact(self) -> ProviderJobArtifact:
        """Convert ledger record into the durable artifact contract."""
        return ProviderJobArtifact(
            artifact_id=self.provider_artifact_id
            or make_artifact_id("provider-job", self.run_id, self.job_id),
            run_id=self.run_id,
            status=_artifact_status(self.status, self.ingestion_state),
            provider=self.provider,
            surface=self.surface,
            provider_status=self.status,
            prompt=self.prompt,
            job_url=self.job_url,
            submitted_at=self.submitted_at,
            completed_at=self.completed_at,
            exported_at=self.exported_at,
            trace_paths=[
                snapshot.screenshot_path
                for snapshot in self.snapshots
                if snapshot.screenshot_path is not None
            ],
            export_paths=self.export_paths,
            metadata={
                "branch_id": self.branch_id or "",
                "ingestion_state": self.ingestion_state,
            },
        )


class ProviderLedger(BaseModel):
    """Provider job ledger for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    jobs: list[ProviderJobRecord] = Field(default_factory=list)

    def get(self, job_id: str) -> ProviderJobRecord:
        for job in self.jobs:
            if job.job_id == job_id:
                return job
        raise KeyError(job_id)

    def upsert(self, job: ProviderJobRecord) -> None:
        for index, existing in enumerate(self.jobs):
            if existing.job_id == job.job_id:
                self.jobs[index] = job
                self.updated_at = _now()
                return
        self.jobs.append(job)
        self.updated_at = _now()


class ProviderLedgerStore:
    """JSON store for provider ledgers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, run_id: str) -> ProviderLedger:
        if not self.path.exists():
            return ProviderLedger(run_id=run_id)
        return ProviderLedger.model_validate_json(self.path.read_text(encoding="utf-8"))

    def write(self, ledger: ProviderLedger) -> Path:
        data = ledger.model_dump(mode="json")
        data["updated_at"] = _now().isoformat()
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self.path

    def upsert_job(self, job: ProviderJobRecord) -> Path:
        ledger = self.load(job.run_id)
        ledger.upsert(job)
        return self.write(ledger)


class BrowserProviderController(Protocol):
    """Controller contract implemented by Chrome, Browser Use, or tests."""

    def open_or_claim_tab(self, record: ProviderJobRecord) -> BrowserTabClaim:
        """Open or claim a provider tab for the job."""

    def submit_research_job(self, record: ProviderJobRecord) -> BrowserJobSubmission:
        """Submit the branch-level prompt to provider research."""

    def snapshot(self, record: ProviderJobRecord) -> BrowserSnapshot:
        """Capture provider page text and URL for completion detection."""

    def export_completed_report(self, record: ProviderJobRecord) -> BrowserProviderExportBundle:
        """Export a completed report through the provider-native route."""


class BrowserProviderAdapter:
    """Control-plane adapter for browser-backed research providers."""

    def __init__(
        self,
        *,
        controller: BrowserProviderController,
        ledger_store: ProviderLedgerStore,
        artifact_store=None,
    ) -> None:
        self._controller = controller
        self._ledger_store = ledger_store
        self._artifact_store = artifact_store

    def start_job(
        self,
        *,
        run_id: str,
        provider: ProviderKind,
        prompt: str,
        branch_id: str | None = None,
        surface: ProviderSurface = ProviderSurface.WEB,
    ) -> ProviderJobRecord:
        """Open or claim a tab, submit a research prompt, and ledger the job."""
        job = ProviderJobRecord(
            job_id=make_artifact_id("provider-job", run_id, provider.value, branch_id, prompt),
            run_id=run_id,
            provider=provider,
            surface=surface,
            branch_id=branch_id,
            prompt=prompt,
        )
        claim = self._controller.open_or_claim_tab(job)
        job.job_url = claim.url
        job.tab_id = claim.tab_id
        submission = self._controller.submit_research_job(job)
        job.job_url = submission.url
        job.submitted_at = submission.submitted_at
        job.status = ProviderJobStatus.SUBMITTED
        job.metadata["provider_job_ref"] = submission.provider_job_ref or ""
        self._persist(job)
        return job

    def poll_once(self, run_id: str, job_id: str) -> ProviderJobRecord:
        """Poll one provider job and update its ledger state."""
        job = self._load_job(run_id, job_id)
        snapshot = self._controller.snapshot(job)
        signal = _detect_signal(job.provider, snapshot.dom_text)
        job.job_url = snapshot.url
        job.snapshots.append(
            ProviderJobSnapshotRecord(
                captured_at=snapshot.captured_at,
                url=snapshot.url,
                state=signal.state,
                evidence=signal.evidence,
                report_title=signal.report_title,
                source_count=signal.source_count,
                export_available=signal.export_available,
                screenshot_path=snapshot.screenshot_path,
            )
        )
        job.status = _status_from_signal(signal)
        if signal.state == BrowserResearchState.EXPORT_READY and job.completed_at is None:
            job.completed_at = snapshot.captured_at
            job.ingestion_state = ProviderIngestionState.READY_TO_INGEST
        elif signal.state in {BrowserResearchState.BLOCKED, BrowserResearchState.FAILED}:
            job.ingestion_state = ProviderIngestionState.FAILED
        self._persist(job)
        return job

    def watch_until_terminal(
        self,
        *,
        run_id: str,
        job_ids: list[str],
        max_polls: int = 120,
        poll_interval_seconds: float = 5.0,
    ) -> list[ProviderJobRecord]:
        """Interleave polling across multiple provider jobs until terminal."""
        pending = set(job_ids)
        latest: dict[str, ProviderJobRecord] = {}
        polls = 0
        while pending and polls < max_polls:
            polls += 1
            for job_id in list(pending):
                job = self.poll_once(run_id, job_id)
                latest[job_id] = job
                if job.status in {
                    ProviderJobStatus.COMPLETED,
                    ProviderJobStatus.FAILED,
                    ProviderJobStatus.BLOCKED,
                }:
                    pending.remove(job_id)
            if pending and poll_interval_seconds > 0:
                time.sleep(poll_interval_seconds)
        return [latest.get(job_id, self._load_job(run_id, job_id)) for job_id in job_ids]

    def export_and_ingest(self, run_id: str, job_id: str) -> ReportIngestionResult | None:
        """Export and ingest a completed provider report if the watcher allows it."""
        job = self._load_job(run_id, job_id)
        signal = job.latest_signal
        if signal is None or not signal.should_ingest:
            job.ingestion_state = ProviderIngestionState.REJECTED_INCOMPLETE
            self._persist(job)
            return None

        bundle = self._controller.export_completed_report(job)
        recovery = _source_recovery(bundle)
        job.source_recovery = recovery
        job.export_paths = bundle.export_paths
        job.exported_at = bundle.exported_at
        job.status = ProviderJobStatus.EXPORTED

        validation_error = _validate_export_bundle(job.provider, bundle)
        if validation_error is not None:
            job.ingestion_state = ProviderIngestionState.REJECTED_INCOMPLETE
            job.metadata["export_rejection"] = validation_error
            self._persist(job)
            return None

        ingest_path = bundle.primary_ingest_path
        if ingest_path is None:
            job.ingestion_state = ProviderIngestionState.REJECTED_INCOMPLETE
            job.metadata["export_rejection"] = "no primary report path"
            self._persist(job)
            return None

        result: ReportIngestionResult | None = None
        if self._artifact_store is not None:
            result = ManualUploadAdapter(self._artifact_store).ingest_file(
                ingest_path,
                run_id=run_id,
                provider_job_id=job.to_provider_artifact().artifact_id,
                issue_node_ids=[job.branch_id] if job.branch_id else [],
                source_format=SourceFormat.MARKDOWN
                if Path(ingest_path).suffix.lower() in {".md", ".markdown"}
                else None,
            )
            job.report_artifact_ids.append(result.report.artifact_id)
            job.ingested_at = _now()
            job.ingestion_state = ProviderIngestionState.INGESTED
        else:
            job.ingestion_state = ProviderIngestionState.READY_TO_INGEST

        self._persist(job)
        return result

    def _load_job(self, run_id: str, job_id: str) -> ProviderJobRecord:
        ledger = self._ledger_store.load(run_id)
        return ledger.get(job_id)

    def _persist(self, job: ProviderJobRecord) -> None:
        artifact = job.to_provider_artifact()
        job.provider_artifact_id = artifact.artifact_id
        if self._artifact_store is not None:
            self._artifact_store.write_artifact(artifact)
        self._ledger_store.upsert_job(job)


def _detect_signal(provider: ProviderKind, dom_text: str) -> ProviderCompletionSignal:
    if provider == ProviderKind.CHATGPT:
        return detect_chatgpt_deep_research_state(dom_text)
    if provider == ProviderKind.CLAUDE:
        return detect_claude_research_state(dom_text)
    return ProviderCompletionSignal(provider=provider.value, state=BrowserResearchState.UNKNOWN)


def _status_from_signal(signal: ProviderCompletionSignal) -> ProviderJobStatus:
    if signal.state == BrowserResearchState.EXPORT_READY:
        return ProviderJobStatus.COMPLETED
    if signal.state == BrowserResearchState.COMPLETED:
        return ProviderJobStatus.COMPLETED
    if signal.state == BrowserResearchState.RUNNING:
        return ProviderJobStatus.RUNNING
    if signal.state == BrowserResearchState.BLOCKED:
        return ProviderJobStatus.BLOCKED
    if signal.state == BrowserResearchState.FAILED:
        return ProviderJobStatus.FAILED
    return ProviderJobStatus.RUNNING


def _validate_export_bundle(
    provider: ProviderKind,
    bundle: BrowserProviderExportBundle,
) -> str | None:
    if provider == ProviderKind.CHATGPT:
        if not bundle.markdown_path:
            return "ChatGPT export missing Markdown body path"
        if not bundle.docx_source_path:
            return "ChatGPT export missing DOCX source-link path"
    if provider == ProviderKind.CLAUDE and not (bundle.artifact_path or bundle.report_path):
        return "Claude export missing artifact/report path"
    primary = bundle.primary_ingest_path
    if primary is None or not Path(primary).exists():
        return "primary report path does not exist"
    return None


def _source_recovery(bundle: BrowserProviderExportBundle) -> ProviderSourceRecovery:
    if bundle.provider == ProviderKind.CHATGPT:
        route = "markdown_body_plus_docx_source_links"
        complete = bool(bundle.markdown_path and bundle.docx_source_path)
    elif bundle.provider == ProviderKind.CLAUDE:
        route = "artifact_report_export"
        complete = bool(bundle.artifact_path or bundle.report_path)
    else:
        route = "browser_export"
        complete = bundle.primary_ingest_path is not None
    return ProviderSourceRecovery(
        route=route,
        complete=complete,
        source_urls=bundle.source_urls,
        source_paths=[path for path in [bundle.docx_source_path, *bundle.source_map_paths] if path],
    )


def _artifact_status(status: ProviderJobStatus, ingestion_state: str) -> ArtifactStatus:
    if ingestion_state == ProviderIngestionState.INGESTED:
        return ArtifactStatus.READY
    if status in {ProviderJobStatus.FAILED, ProviderJobStatus.BLOCKED}:
        return ArtifactStatus.FAILED
    if status in {ProviderJobStatus.COMPLETED, ProviderJobStatus.EXPORTED}:
        return ArtifactStatus.PARTIAL
    return ArtifactStatus.CREATED
