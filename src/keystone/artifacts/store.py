"""Local filesystem artifact store for first-slice pipeline runs."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from keystone.artifacts.models import ArtifactBase, ArtifactStatus, RunLedger

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T", bound=BaseModel)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class LocalArtifactStore:
    """Simple JSON-and-file store keyed by ``run_id`` and ``artifact_id``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def artifacts_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "artifacts"

    def files_dir(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "files"

    def ledger_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "run-ledger.json"

    def artifact_path(self, run_id: str, artifact_id: str) -> Path:
        return self.artifacts_dir(run_id) / f"{artifact_id}.json"

    def ensure_run(self, run_id: str) -> None:
        self.artifacts_dir(run_id).mkdir(parents=True, exist_ok=True)
        self.files_dir(run_id).mkdir(parents=True, exist_ok=True)

    def write_ledger(self, ledger: RunLedger) -> Path:
        self.ensure_run(ledger.run_id)
        path = self.ledger_path(ledger.run_id)
        data = ledger.model_dump(mode="json")
        data["updated_at"] = _utc_now_iso()
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def read_ledger(self, run_id: str) -> RunLedger:
        return RunLedger.model_validate_json(self.ledger_path(run_id).read_text(encoding="utf-8"))

    def create_ledger(
        self,
        *,
        run_id: str,
        root_request: str,
        status: ArtifactStatus = ArtifactStatus.CREATED,
        notes: Iterable[str] = (),
        metadata: dict | None = None,
    ) -> RunLedger:
        ledger = RunLedger(
            run_id=run_id,
            root_request=root_request,
            status=status,
            notes=list(notes),
            metadata=metadata or {},
        )
        self.write_ledger(ledger)
        return ledger

    def write_artifact(self, artifact: ArtifactBase, *, update_ledger: bool = True) -> Path:
        self.ensure_run(artifact.run_id)
        data = artifact.model_dump(mode="json")
        data["updated_at"] = _utc_now_iso()
        path = self.artifact_path(artifact.run_id, artifact.artifact_id)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if update_ledger and self.ledger_path(artifact.run_id).exists():
            self._attach_to_ledger(
                artifact.run_id,
                artifact.artifact_id,
                parent_ids=artifact.parent_artifact_ids,
            )
        return path

    def read_artifact(
        self,
        run_id: str,
        artifact_id: str,
        model_type: type[T] | None = None,
    ) -> T | dict:
        data = json.loads(self.artifact_path(run_id, artifact_id).read_text(encoding="utf-8"))
        if model_type is None:
            return data
        return model_type.model_validate(data)

    def list_artifacts(self, run_id: str, artifact_type: str | None = None) -> list[dict]:
        directory = self.artifacts_dir(run_id)
        if not directory.exists():
            return []
        artifacts: list[dict] = []
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if artifact_type is None or data.get("artifact_type") == artifact_type:
                artifacts.append(data)
        return artifacts

    def update_status(
        self,
        run_id: str,
        artifact_id: str,
        status: ArtifactStatus | str,
    ) -> dict:
        path = self.artifact_path(run_id, artifact_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = status.value if isinstance(status, ArtifactStatus) else str(status)
        data["updated_at"] = _utc_now_iso()
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data

    def write_text_file(self, run_id: str, relative_path: str, content: str) -> Path:
        self.ensure_run(run_id)
        path = self.files_dir(run_id) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def copy_file(self, run_id: str, source: str | Path, relative_path: str | None = None) -> Path:
        self.ensure_run(run_id)
        source_path = Path(source)
        target = self.files_dir(run_id) / (relative_path or source_path.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        return target

    def _attach_to_ledger(
        self,
        run_id: str,
        artifact_id: str,
        *,
        parent_ids: list[str],
    ) -> None:
        ledger = self.read_ledger(run_id)
        if artifact_id not in ledger.artifact_ids:
            ledger.artifact_ids.append(artifact_id)
        for parent_id in parent_ids:
            children = ledger.child_refs.setdefault(parent_id, [])
            if artifact_id not in children:
                children.append(artifact_id)
        self.write_ledger(ledger)
