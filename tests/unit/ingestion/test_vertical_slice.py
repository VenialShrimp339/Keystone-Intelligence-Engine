from __future__ import annotations

from pathlib import Path

from keystone.artifacts import LocalArtifactStore
from keystone.ingestion.vertical_slice import run_manual_first_slice

FIXTURE = Path("tests/fixtures/ingestion/sample_public_deep_research_report.md")


def test_manual_first_slice_writes_traceable_artifacts(tmp_path):
    store = LocalArtifactStore(tmp_path)

    result = run_manual_first_slice(
        store=store,
        run_id="slice-run",
        root_request="Research U.S. auto body repair consolidation",
        report_path=FIXTURE,
        domain="business_strategy",
        output_target="markdown brief",
    )

    ledger = store.read_ledger("slice-run")
    assert result["report_artifact_id"] in ledger.artifact_ids
    assert result["evidence_bundle_artifact_id"] in ledger.artifact_ids
    assert result["deliverable_artifact_id"] in ledger.artifact_ids

    deliverable_path = Path(result["deliverable_path"])
    assert deliverable_path.exists()
    deliverable_text = deliverable_path.read_text(encoding="utf-8")
    assert "## Traceable Claims" in deliverable_text
    assert "SRC-001" in deliverable_text

    evaluation = store.read_artifact("slice-run", result["evaluation_artifact_id"])
    assert evaluation["passed"] is True
