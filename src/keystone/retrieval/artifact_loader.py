"""Load Lane H persisted fetch artifacts from disk.

Lane H writes one JSON file per fetched document to a configurable
directory (``<root>/<artifact_id>.json``). This loader reads those files,
validates them into FetchedArtifact instances, and surfaces precise
errors for the two failure modes downstream needs to handle distinctly:

- the artifact file does not exist (ArtifactNotFoundError)
- the artifact file exists but is malformed or invalid (ArtifactLoadError)

The loader is intentionally synchronous: it is called at pipeline-setup
time or from within already-async parse stages, and doing I/O in a thread
is cheaper than the overhead of spawning tasks for small JSON reads.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from keystone.retrieval.parse_models import FetchedArtifact

if TYPE_CHECKING:
    from collections.abc import Iterator


class ArtifactLoadError(Exception):
    """An artifact file exists but could not be loaded into a FetchedArtifact.

    Raised for malformed JSON, validation failures, permission issues,
    or encoding errors. The original exception is chained via ``__cause__``.
    """


class ArtifactNotFoundError(ArtifactLoadError):
    """No artifact file exists for the requested identifier."""


class ArtifactLoader:
    """Read persisted Lane H fetch artifacts from a directory.

    The directory is treated as flat: one ``<artifact_id>.json`` per
    artifact. Subdirectories are ignored. Files without the ``.json``
    suffix are ignored by ``iter_all``.
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        """The directory this loader reads from."""

        return self._root

    def path_for(self, artifact_id: str) -> Path:
        """Return the expected path for an artifact id."""

        return self._root / f"{artifact_id}.json"

    def exists(self, artifact_id: str) -> bool:
        """Cheap membership check -- does the artifact file exist on disk?"""

        return self.path_for(artifact_id).is_file()

    def load(self, artifact_id: str) -> FetchedArtifact:
        """Load and validate a single artifact by id.

        Raises:
            ArtifactNotFoundError: No file at ``<root>/<artifact_id>.json``.
            ArtifactLoadError: The file exists but cannot be validated.
        """

        path = self.path_for(artifact_id)
        if not path.is_file():
            raise ArtifactNotFoundError(f"No artifact for id {artifact_id!r} at {path}")
        return self._load_path(path)

    def iter_all(self) -> Iterator[FetchedArtifact]:
        """Iterate every valid artifact in ``root``.

        Files that fail to load are skipped silently only when they are
        not ``.json`` files. Malformed ``.json`` files raise
        ArtifactLoadError immediately -- silently dropping them would
        hide data-loss bugs.
        """

        if not self._root.is_dir():
            raise ArtifactLoadError(
                f"Artifact root directory does not exist or is not a directory: {self._root}"
            )
        for entry in sorted(self._root.iterdir()):
            if not entry.is_file() or entry.suffix != ".json":
                continue
            yield self._load_path(entry)

    def _load_path(self, path: Path) -> FetchedArtifact:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ArtifactLoadError(f"Could not read artifact at {path}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise ArtifactLoadError(f"Artifact at {path} is not valid UTF-8: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ArtifactLoadError(
                f"Artifact at {path} is not valid JSON: {exc.msg} (line {exc.lineno})"
            ) from exc

        if not isinstance(payload, dict):
            raise ArtifactLoadError(
                f"Artifact at {path} must be a JSON object, got {type(payload).__name__}"
            )

        try:
            return FetchedArtifact.model_validate(payload)
        except ValidationError as exc:
            raise ArtifactLoadError(f"Artifact at {path} failed validation: {exc}") from exc
