"""Tests for the Lane H artifact loader."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from keystone.retrieval import (
    ArtifactLoader,
    ArtifactLoadError,
    ArtifactNotFoundError,
)
from keystone.retrieval.parse_models import (
    CoverageStatus,
    FetchedArtifact,
    SourceFamily,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _write_artifact(root: Path, artifact_id: str, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "artifact_id": artifact_id,
        "url": f"https://example.com/{artifact_id}",
        "canonical_url": f"https://example.com/{artifact_id}",
        "redirect_chain": [],
        "mime_type": "text/html",
        "content_hash": HASH_A,
        "title": "A title",
        "fetched_at": datetime(2026, 4, 17, 12, 0, tzinfo=UTC).isoformat(),
        "coverage": {"status": CoverageStatus.COMPLETE.value},
        "content_text": "<p>hi</p>",
        "source_family": SourceFamily.ARTICLE.value,
        "audit": {"fetcher": "lane-h/v1"},
    }
    payload.update(overrides)
    path = root / f"{artifact_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestArtifactLoader:
    def test_loads_single_artifact(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "art1")
        loader = ArtifactLoader(tmp_path)
        art = loader.load("art1")
        assert isinstance(art, FetchedArtifact)
        assert art.artifact_id == "art1"
        assert art.coverage.status is CoverageStatus.COMPLETE

    def test_missing_file_raises_not_found(self, tmp_path: Path) -> None:
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactNotFoundError):
            loader.load("does-not-exist")

    def test_malformed_json_raises_load_error(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("{ not valid json", encoding="utf-8")
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactLoadError) as excinfo:
            loader.load("bad")
        assert "not valid JSON" in str(excinfo.value)

    def test_top_level_must_be_object(self, tmp_path: Path) -> None:
        (tmp_path / "list.json").write_text("[]", encoding="utf-8")
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactLoadError):
            loader.load("list")

    def test_validation_failure_wrapped_as_load_error(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "invalid-hash", content_hash="short")
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactLoadError) as excinfo:
            loader.load("invalid-hash")
        assert "failed validation" in str(excinfo.value)

    def test_exists_tracks_disk_state(self, tmp_path: Path) -> None:
        loader = ArtifactLoader(tmp_path)
        assert not loader.exists("missing")
        _write_artifact(tmp_path, "ok")
        assert loader.exists("ok")

    def test_iter_all_skips_non_json_files(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "art1")
        _write_artifact(tmp_path, "art2", content_hash=HASH_B)
        (tmp_path / "readme.txt").write_text("not json", encoding="utf-8")
        (tmp_path / "subdir").mkdir()
        loader = ArtifactLoader(tmp_path)
        ids = sorted(a.artifact_id for a in loader.iter_all())
        assert ids == ["art1", "art2"]

    def test_iter_all_raises_for_bad_json(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("{", encoding="utf-8")
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactLoadError):
            list(loader.iter_all())

    def test_missing_root_dir_raises(self, tmp_path: Path) -> None:
        loader = ArtifactLoader(tmp_path / "nope")
        with pytest.raises(ArtifactLoadError):
            list(loader.iter_all())

    def test_not_utf8_encoding_raises(self, tmp_path: Path) -> None:
        (tmp_path / "latin.json").write_bytes(b"\xff\xfe\x00\x00")
        loader = ArtifactLoader(tmp_path)
        with pytest.raises(ArtifactLoadError):
            loader.load("latin")

    def test_path_for_and_root_expose_config(self, tmp_path: Path) -> None:
        loader = ArtifactLoader(tmp_path)
        assert loader.root == tmp_path
        assert loader.path_for("foo") == tmp_path / "foo.json"
