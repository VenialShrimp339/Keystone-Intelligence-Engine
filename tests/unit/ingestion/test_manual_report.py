from __future__ import annotations

from pathlib import Path

from keystone.artifacts import LocalArtifactStore
from keystone.ingestion import ManualUploadAdapter

FIXTURE = Path("tests/fixtures/ingestion/sample_public_deep_research_report.md")


def test_manual_upload_adapter_extracts_report_sources_claims_and_gaps(tmp_path):
    store = LocalArtifactStore(tmp_path)
    run_id = "manual-report-run"
    store.create_ledger(run_id=run_id, root_request="Research collision repair consolidation")

    result = ManualUploadAdapter(store).ingest_file(
        FIXTURE,
        run_id=run_id,
        provider_job_id="provider-chatgpt-test",
        issue_node_ids=["branch_1"],
    )

    assert result.report.title == "U.S. Auto Body Repair Industry Consolidation"
    assert result.report.raw_path is not None
    assert result.report.normalized_path is not None
    assert len(result.report.section_records) >= 3
    assert len(result.report.source_records) == 5
    assert len(result.report.candidate_claim_records) >= 6

    assert result.evidence_bundle.cited_claim_count >= 5
    assert result.evidence_bundle.uncited_claim_count >= 1
    assert "1_claims_missing_citations" in result.evidence_bundle.quality_flags

    loaded = store.read_artifact(
        run_id,
        result.evidence_bundle.artifact_id,
    )
    assert loaded["artifact_type"] == "evidence_bundle"
    assert loaded["source_bundle_artifact_id"] == result.source_bundle.artifact_id


def test_manual_upload_adapter_handles_html(tmp_path):
    html = tmp_path / "report.html"
    html.write_text(
        """
        <html><body>
          <h1>Compact Report</h1>
          <h2>Findings</h2>
          <p>One cited factual claim appears here with a source https://example.com/a.</p>
          <p>One uncited factual claim appears here and should be flagged by ingestion.</p>
        </body></html>
        """,
        encoding="utf-8",
    )

    result = ManualUploadAdapter().ingest_file(html, run_id="html-run")

    assert result.report.title == "Compact Report"
    assert len(result.report.source_records) == 1
    assert result.evidence_bundle.uncited_claim_count == 1
