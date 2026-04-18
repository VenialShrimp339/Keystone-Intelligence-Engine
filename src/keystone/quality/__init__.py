"""Deterministic prose-quality filters.

The slop detector catches phrases LLMs over-use (filler, buzzwords, hedging
clusters, AI tells, "delve/tapestry/realm" tics) so the Evaluator grades the
cleaned text, not the sloppy version. No LLM calls — pure pattern matching.
"""

from __future__ import annotations

from keystone.quality.patterns import (
    DEFAULT_PATTERNS,
    Category,
    Severity,
    SlopPattern,
)
from keystone.quality.slop_detector import (
    SlopDetector,
    SlopMatch,
    SlopReport,
)

__all__ = [
    "DEFAULT_PATTERNS",
    "Category",
    "Severity",
    "SlopDetector",
    "SlopMatch",
    "SlopPattern",
    "SlopReport",
]
