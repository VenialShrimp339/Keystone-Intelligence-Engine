"""Deterministic slop detector for consulting-brief prose.

Runs a curated database of regex patterns against a block of text and reports
every match with offset, severity, category, and a suggested replacement when
available. A companion ``clean()`` method applies replacements in one pass so
the Evaluator scores the cleaned version rather than the sloppy original.

Design properties:

- Case-insensitive matching with word-boundary awareness (no false positives
  inside legitimate words — "paradigm" inside "paradigmatic" does not match).
- Overlapping matches resolved longest-first so "it is important to note that"
  wins over "important" on the same span.
- ``clean()`` never introduces new words; it either deletes a slop phrase or
  substitutes a configured replacement, then tidies the resulting whitespace
  and capitalization.
- No LLM calls. Pure pattern matching, sub-millisecond on a ten-kilobyte
  brief.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from keystone.quality.patterns import (
    DEFAULT_PATTERNS,
    Category,
    Severity,
    SlopPattern,
)

_SEVERITY_RANK: dict[Severity, int] = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
}


@dataclass(frozen=True)
class SlopMatch:
    """One matched instance of a slop pattern."""

    phrase: str
    matched_text: str
    start: int
    end: int
    line: int
    col: int
    category: Category
    severity: Severity
    suggested_replacement: str | None
    note: str | None


@dataclass(frozen=True)
class SlopReport:
    """Result of ``SlopDetector.detect``."""

    matches: tuple[SlopMatch, ...]
    counts_by_severity: dict[Severity, int] = field(default_factory=dict)
    counts_by_category: dict[Category, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.matches)

    @property
    def high_count(self) -> int:
        return self.counts_by_severity.get(Severity.HIGH, 0)

    @property
    def medium_count(self) -> int:
        return self.counts_by_severity.get(Severity.MEDIUM, 0)

    @property
    def low_count(self) -> int:
        return self.counts_by_severity.get(Severity.LOW, 0)

    def at_or_above(self, severity: Severity) -> tuple[SlopMatch, ...]:
        """Matches whose severity is ``>=`` the supplied threshold."""
        threshold = _SEVERITY_RANK[severity]
        return tuple(m for m in self.matches if _SEVERITY_RANK[m.severity] >= threshold)


class SlopDetector:
    """Regex-based slop filter.

    Usage::

        detector = SlopDetector()
        report = detector.detect(section_text)
        cleaned = detector.clean(section_text)
    """

    def __init__(
        self,
        patterns: tuple[SlopPattern, ...] | list[SlopPattern] | None = None,
    ) -> None:
        self._patterns: tuple[SlopPattern, ...] = tuple(
            patterns if patterns is not None else DEFAULT_PATTERNS
        )
        # Compile once. The key is the pattern's regex string so the caller
        # can swap out the pattern list for tests without paying the
        # recompile cost at every call.
        self._compiled: list[tuple[SlopPattern, re.Pattern[str]]] = [
            (pattern, re.compile(pattern.regex, re.IGNORECASE)) for pattern in self._patterns
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def patterns(self) -> tuple[SlopPattern, ...]:
        return self._patterns

    def detect(
        self,
        text: str,
        *,
        min_severity: Severity = Severity.LOW,
    ) -> SlopReport:
        """Scan ``text`` and return every pattern match.

        Args:
            text: The text to scan. Empty input returns an empty report.
            min_severity: Only matches with severity ``>=`` this threshold
                are included. Default includes LOW.
        """
        if not text:
            return SlopReport(matches=(), counts_by_severity={}, counts_by_category={})

        threshold = _SEVERITY_RANK[min_severity]
        raw_matches: list[SlopMatch] = []
        for pattern, compiled in self._compiled:
            if _SEVERITY_RANK[pattern.severity] < threshold:
                continue
            for found in compiled.finditer(text):
                start, end = found.span()
                if start == end:
                    continue
                line, col = _line_col(text, start)
                raw_matches.append(
                    SlopMatch(
                        phrase=pattern.phrase,
                        matched_text=found.group(0),
                        start=start,
                        end=end,
                        line=line,
                        col=col,
                        category=pattern.category,
                        severity=pattern.severity,
                        suggested_replacement=pattern.replacement,
                        note=pattern.note,
                    )
                )

        resolved = _resolve_overlaps(raw_matches)
        # Stable order: by start offset, then by severity (HIGH first).
        resolved.sort(key=lambda m: (m.start, -_SEVERITY_RANK[m.severity]))

        sev_counts = Counter(m.severity for m in resolved)
        cat_counts = Counter(m.category for m in resolved)

        return SlopReport(
            matches=tuple(resolved),
            counts_by_severity=dict(sev_counts),
            counts_by_category=dict(cat_counts),
        )

    def clean(self, text: str) -> str:
        """Apply replacements for every pattern that has one configured.

        Policy:
            - HIGH and MEDIUM matches whose ``replacement`` is non-``None``
              are substituted in place.
            - Patterns with ``replacement=None`` are left unchanged.
            - LOW matches are never auto-edited, even if a replacement is
              configured (defense against aggressive edits).

        After substitution the result is de-whitespaced and sentence-
        capitalized so deletions do not leave "  the market grew" artifacts.
        """
        if not text:
            return text

        matches_to_apply: list[SlopMatch] = []
        for pattern, compiled in self._compiled:
            if pattern.replacement is None:
                continue
            if pattern.severity == Severity.LOW:
                continue
            for found in compiled.finditer(text):
                start, end = found.span()
                if start == end:
                    continue
                line, col = _line_col(text, start)
                matches_to_apply.append(
                    SlopMatch(
                        phrase=pattern.phrase,
                        matched_text=found.group(0),
                        start=start,
                        end=end,
                        line=line,
                        col=col,
                        category=pattern.category,
                        severity=pattern.severity,
                        suggested_replacement=pattern.replacement,
                        note=pattern.note,
                    )
                )

        if not matches_to_apply:
            return text

        resolved = _resolve_overlaps(matches_to_apply)
        # Apply right-to-left so earlier offsets stay valid as we splice.
        resolved.sort(key=lambda m: m.start, reverse=True)

        buffer = text
        for match in resolved:
            replacement = match.suggested_replacement
            assert replacement is not None  # filtered above
            buffer = buffer[: match.start] + replacement + buffer[match.end :]

        return _tidy(buffer)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _line_col(text: str, offset: int) -> tuple[int, int]:
    """Return (line, col) 1-indexed for the given character offset."""
    if offset <= 0:
        return 1, 1
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    last_newline = prefix.rfind("\n")
    col = offset - (last_newline + 1) + 1
    return line, col


def _resolve_overlaps(matches: list[SlopMatch]) -> list[SlopMatch]:
    """Drop shorter matches that are wholly contained in a longer match.

    Consulting example: "it is important to note that" and "important"
    both match. We keep the longer phrase. Pure ordering; no scoring.
    """
    if not matches:
        return []
    # Longest span first so we always compare against the current "winner".
    ordered = sorted(
        matches,
        key=lambda m: (-(m.end - m.start), m.start),
    )
    kept: list[SlopMatch] = []
    for candidate in ordered:
        overlaps_winner = any(
            not (candidate.end <= winner.start or candidate.start >= winner.end) for winner in kept
        )
        if overlaps_winner:
            continue
        kept.append(candidate)
    return kept


_SPACE_RUN = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([,.!?;:])")
_LEADING_WHITESPACE_AT_TEXT_START = re.compile(r"\A[ \t]+")
_BLANK_LINE_RUN = re.compile(r"\n[ \t]*\n[ \t]*\n+")
_LEADING_LOWER = re.compile(r"^(\s*)([a-z])")
_POST_TERMINATOR_LOWER = re.compile(r"([.!?]\s+)([a-z])")
_LIST_MARKER_LOWER = re.compile(r"(?m)^([-*+]\s+|\d+[.)]\s+)([a-z])")


def _tidy(text: str) -> str:
    """Collapse whitespace artifacts and re-capitalize sentence starts.

    Deletions can leave ``"text.  the next sentence"`` or ``"text ,"`` style
    wrinkles. This pass fixes them without touching the semantic content.
    Markdown list markers are preserved because the regex only fires on
    runs at the start of a line that precede non-whitespace text; list
    indentation already has a marker character at the start.
    """
    out = text
    out = _SPACE_RUN.sub(" ", out)
    out = _SPACE_BEFORE_PUNCT.sub(r"\1", out)
    out = _BLANK_LINE_RUN.sub("\n\n", out)
    out = _LEADING_WHITESPACE_AT_TEXT_START.sub("", out)
    out = _LEADING_LOWER.sub(
        lambda m: m.group(1) + m.group(2).upper(),
        out,
        count=1,
    )
    out = _POST_TERMINATOR_LOWER.sub(
        lambda m: m.group(1) + m.group(2).upper(),
        out,
    )
    out = _LIST_MARKER_LOWER.sub(
        lambda m: m.group(1) + m.group(2).upper(),
        out,
    )
    return out
