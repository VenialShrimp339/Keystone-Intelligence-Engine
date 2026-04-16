"""Canary test package bootstrap.

Bare `pytest` in this workspace does not automatically add `src/` to
`sys.path`, so make the package importable from the repo root.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "structlog" not in sys.modules:
    class _StructlogLogger:
        def info(self, *args, **kwargs) -> None:
            return None

        def error(self, *args, **kwargs) -> None:
            return None

    sys.modules["structlog"] = types.SimpleNamespace(
        get_logger=lambda *args, **kwargs: _StructlogLogger()
    )
