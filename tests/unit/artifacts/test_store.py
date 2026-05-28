from __future__ import annotations

from keystone.artifacts import (
    ApprovalStatus,
    ArtifactStatus,
    IssueTreeNodeArtifact,
    LocalArtifactStore,
    SpecificationArtifact,
    make_artifact_id,
)


def test_artifact_store_roundtrip_status_and_ledger_children(tmp_path):
    store = LocalArtifactStore(tmp_path)
    run_id = "run-test"
    store.create_ledger(run_id=run_id, root_request="Research auto body consolidation")

    spec = SpecificationArtifact(
        artifact_id=make_artifact_id("spec", run_id, "auto body"),
        run_id=run_id,
        question="Research auto body consolidation",
        selected_lenses=[{"lens_id": "market_competitive"}],
        approval_status=ApprovalStatus.REQUIRED,
    )
    store.write_artifact(spec)

    node = IssueTreeNodeArtifact(
        artifact_id=make_artifact_id("node", run_id, "market structure"),
        run_id=run_id,
        parent_artifact_ids=[spec.artifact_id],
        node_id="branch_1",
        name="Market structure",
        description="Research market structure and consolidation.",
    )
    store.write_artifact(node)

    loaded = store.read_artifact(run_id, spec.artifact_id, SpecificationArtifact)
    assert loaded.question == spec.question

    updated = store.update_status(run_id, node.artifact_id, ArtifactStatus.READY)
    assert updated["status"] == "ready"

    artifacts = store.list_artifacts(run_id)
    assert {artifact["artifact_id"] for artifact in artifacts} == {
        spec.artifact_id,
        node.artifact_id,
    }

    ledger = store.read_ledger(run_id)
    assert spec.artifact_id in ledger.artifact_ids
    assert node.artifact_id in ledger.artifact_ids
    assert ledger.child_refs[spec.artifact_id] == [node.artifact_id]
