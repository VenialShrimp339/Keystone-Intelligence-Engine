"""Canary test: every prompt .md file must carry model-version frontmatter.

Fails loudly on model upgrades to trigger a prompt review. When upgrading
the flagship model (e.g. claude-opus-4-6 → claude-opus-4-7), update
CURRENT_MODEL below and re-run — any prompt still pinned to the old
version will fail, signaling it needs review for compensating-complexity
decay.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "keystone"

CURRENT_MODEL = "claude-opus-4-6"

_FRONTMATTER_RE = re.compile(
    r"^---\n(.*?)\n---\n",
    re.DOTALL,
)
_MODEL_RE = re.compile(r"^model:\s*(.+)$", re.MULTILINE)


def _discover_prompt_files() -> list[Path]:
    return sorted(SRC_ROOT.rglob("prompts/*.md"))


def _parse_model(path: Path) -> str | None:
    text = path.read_text()
    fm = _FRONTMATTER_RE.match(text)
    if not fm:
        return None
    m = _MODEL_RE.search(fm.group(1))
    return m.group(1).strip() if m else None


def _model_version_tuple(model_str: str) -> tuple[int, ...]:
    """Extract numeric version parts from a model string like 'claude-opus-4-6'."""
    parts = re.findall(r"\d+", model_str)
    return tuple(int(p) for p in parts)


class TestPromptFreshness:
    def test_all_prompt_files_have_frontmatter(self) -> None:
        missing = []
        for path in _discover_prompt_files():
            if _parse_model(path) is None:
                missing.append(str(path.relative_to(SRC_ROOT)))
        assert not missing, f"Prompt files missing model frontmatter: {missing}"

    def test_no_prompt_more_than_one_version_behind(self) -> None:
        current = _model_version_tuple(CURRENT_MODEL)
        stale = []
        for path in _discover_prompt_files():
            model = _parse_model(path)
            if model is None:
                continue
            version = _model_version_tuple(model)
            if len(version) >= 2 and len(current) >= 2 and version[-1] < current[-1] - 1:
                stale.append(f"{path.relative_to(SRC_ROOT)}: {model} (current: {CURRENT_MODEL})")
        assert not stale, "Prompts more than 1 version behind:\n" + "\n".join(stale)

    def test_prompt_files_discovered(self) -> None:
        files = _discover_prompt_files()
        assert len(files) >= 25, f"Expected ≥25 prompt files, found {len(files)}"
