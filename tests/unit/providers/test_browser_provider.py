from __future__ import annotations

from typing import TYPE_CHECKING

from keystone.artifacts import LocalArtifactStore, ProviderKind
from keystone.providers import (
    BrowserJobSubmission,
    BrowserProviderAdapter,
    BrowserProviderExportBundle,
    BrowserSnapshot,
    BrowserTabClaim,
    ProviderIngestionState,
    ProviderLedgerStore,
)

if TYPE_CHECKING:
    from pathlib import Path

    from keystone.providers.browser_provider import ProviderJobRecord


class FakeController:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.snapshots: dict[str, list[str]] = {}
        self.exports: dict[str, BrowserProviderExportBundle] = {}

    def open_or_claim_tab(self, record: ProviderJobRecord) -> BrowserTabClaim:
        return BrowserTabClaim(
            url=f"https://example.test/{record.provider.value}/{record.branch_id}",
            tab_id=f"tab-{record.branch_id}",
        )

    def submit_research_job(self, record: ProviderJobRecord) -> BrowserJobSubmission:
        return BrowserJobSubmission(
            url=f"https://example.test/{record.provider.value}/{record.branch_id}/job",
            provider_job_ref=f"remote-{record.branch_id}",
        )

    def snapshot(self, record: ProviderJobRecord) -> BrowserSnapshot:
        queue = self.snapshots[record.job_id]
        dom_text = (
            queue.pop(0) if queue else "Research complete download markdown word sources used"
        )
        return BrowserSnapshot(url=record.job_url or "https://example.test/job", dom_text=dom_text)

    def export_completed_report(self, record: ProviderJobRecord) -> BrowserProviderExportBundle:
        return self.exports[record.job_id]


def _report(path: Path, title: str) -> Path:
    path.write_text(
        f"""# {title}

## Findings
- The target market has enough reachable demand to justify deeper diligence [SRC1].
- Margin pressure depends on pricing, support cost, and customer mix [SRC2].
- Retention evidence should be segmented before a go/no-go decision [SRC3].
- The provider route preserved traceable source URLs for ingestion [SRC4].
- The next pass should test disconfirming evidence before synthesis [SRC5].

[SRC1]: https://example.com/source-1
[SRC2]: https://example.com/source-2
[SRC3]: https://example.com/source-3
[SRC4]: https://example.com/source-4
[SRC5]: https://example.com/source-5
""",
        encoding="utf-8",
    )
    return path


def test_browser_provider_watches_exports_and_ingests_parallel_jobs(tmp_path):
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    artifact_store.create_ledger(
        run_id="run-provider",
        root_request="Run provider jobs",
    )
    controller = FakeController(tmp_path)
    adapter = BrowserProviderAdapter(
        controller=controller,
        ledger_store=ProviderLedgerStore(tmp_path / "provider-ledger.json"),
        artifact_store=artifact_store,
    )

    chatgpt_job = adapter.start_job(
        run_id="run-provider",
        provider=ProviderKind.CHATGPT,
        prompt="Research demand.",
        branch_id="demand",
    )
    claude_job = adapter.start_job(
        run_id="run-provider",
        provider=ProviderKind.CLAUDE,
        prompt="Research margins.",
        branch_id="margin",
    )

    controller.snapshots[chatgpt_job.job_id] = [
        "Thinking. Stop answering.",
        "Download Markdown Word Sources used",
    ]
    controller.snapshots[claude_job.job_id] = [
        "Research complete. Artifact panel: Margin Diligence. 42 sources.",
    ]
    chatgpt_md = _report(tmp_path / "chatgpt-report.md", "ChatGPT Demand Report")
    chatgpt_docx = tmp_path / "chatgpt-sources.docx"
    chatgpt_docx.write_text("source links placeholder", encoding="utf-8")
    claude_report = _report(tmp_path / "claude-report.md", "Claude Margin Report")
    controller.exports[chatgpt_job.job_id] = BrowserProviderExportBundle(
        provider=ProviderKind.CHATGPT,
        markdown_path=str(chatgpt_md),
        docx_source_path=str(chatgpt_docx),
        source_urls=["https://example.com/source-1"],
    )
    controller.exports[claude_job.job_id] = BrowserProviderExportBundle(
        provider=ProviderKind.CLAUDE,
        report_path=str(claude_report),
        source_urls=["https://example.com/source-2"],
    )

    watched = adapter.watch_until_terminal(
        run_id="run-provider",
        job_ids=[chatgpt_job.job_id, claude_job.job_id],
        max_polls=4,
        poll_interval_seconds=0,
    )

    assert {job.status.value for job in watched} == {"completed"}
    chatgpt_ingestion = adapter.export_and_ingest("run-provider", chatgpt_job.job_id)
    claude_ingestion = adapter.export_and_ingest("run-provider", claude_job.job_id)

    assert chatgpt_ingestion is not None
    assert claude_ingestion is not None
    ledger = ProviderLedgerStore(tmp_path / "provider-ledger.json").load("run-provider")
    states = {job.branch_id: job.ingestion_state for job in ledger.jobs}
    assert states == {
        "demand": ProviderIngestionState.INGESTED,
        "margin": ProviderIngestionState.INGESTED,
    }
    assert "chatgpt-sources.docx" in ledger.get(chatgpt_job.job_id).source_recovery.source_paths[0]


def test_chatgpt_export_without_docx_source_route_is_rejected(tmp_path):
    artifact_store = LocalArtifactStore(tmp_path / "artifacts")
    artifact_store.create_ledger(run_id="run-provider", root_request="Run provider jobs")
    controller = FakeController(tmp_path)
    adapter = BrowserProviderAdapter(
        controller=controller,
        ledger_store=ProviderLedgerStore(tmp_path / "provider-ledger.json"),
        artifact_store=artifact_store,
    )
    job = adapter.start_job(
        run_id="run-provider",
        provider=ProviderKind.CHATGPT,
        prompt="Research demand.",
        branch_id="demand",
    )
    controller.snapshots[job.job_id] = ["Download Markdown Word Sources used"]
    adapter.poll_once("run-provider", job.job_id)
    controller.exports[job.job_id] = BrowserProviderExportBundle(
        provider=ProviderKind.CHATGPT,
        markdown_path=str(_report(tmp_path / "chatgpt-report.md", "ChatGPT Demand Report")),
    )

    result = adapter.export_and_ingest("run-provider", job.job_id)

    assert result is None
    stored_job = ProviderLedgerStore(tmp_path / "provider-ledger.json").load("run-provider").get(
        job.job_id
    )
    assert stored_job.ingestion_state == ProviderIngestionState.REJECTED_INCOMPLETE
    assert "DOCX source-link" in stored_job.metadata["export_rejection"]
