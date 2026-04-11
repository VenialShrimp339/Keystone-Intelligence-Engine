"""Unified LLM output parsing utilities.

Single entry point for all JSON extraction from LLM responses.
Replaces the 6 ad-hoc extractors previously scattered across the codebase.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

# Matches ```json ... ``` or ``` ... ``` fences
_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL)
# Trailing commas before ] or } (common LLM output error)
_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


class ParseError(Exception):
    """Raised when LLM output cannot be parsed into valid JSON.

    Carries the raw text so callers can log or surface it as a QualityFlag.
    """

    def __init__(self, message: str, raw_text: str) -> None:
        super().__init__(message)
        self.message = message
        self.raw_text = raw_text


def safe_llm_json(
    text: str,
    *,
    required_keys: Sequence[str] = (),
    expect_list: bool = False,
    bool_keys: frozenset[str] = frozenset(),
) -> dict | list:
    """Single entry point for parsing LLM JSON output.

    Steps:
    1. Strip markdown code fences (```json ... ``` or ``` ... ```)
    2. Extract JSON via bracket-counting (handles nested structures)
    3. Parse with json.loads
    4. Validate type (dict or list based on expect_list)
    5. Check required_keys if provided
    6. Coerce bool_keys values using parse_llm_bool logic

    Raises ParseError on failure. Never returns None. Never silently defaults.
    """
    stripped = _strip_fences(text)
    candidate = _extract_json_candidate(stripped, expect_list=expect_list)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        # Try stripping trailing commas (common LLM output error)
        cleaned = _TRAILING_COMMA_RE.sub(r"\1", candidate)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ParseError(
                f"JSON parse failed: {exc}",
                raw_text=text,
            ) from exc

    if expect_list:
        if not isinstance(parsed, list):
            raise ParseError(
                f"Expected JSON array, got {type(parsed).__name__}",
                raw_text=text,
            )
    else:
        if not isinstance(parsed, dict):
            raise ParseError(
                f"Expected JSON object, got {type(parsed).__name__}",
                raw_text=text,
            )

    if required_keys and isinstance(parsed, dict):
        missing = [k for k in required_keys if k not in parsed]
        if missing:
            raise ParseError(
                f"Missing required keys: {missing}",
                raw_text=text,
            )

    if bool_keys and isinstance(parsed, dict):
        for key in bool_keys:
            if key in parsed:
                try:
                    parsed[key] = parse_llm_bool(parsed[key])
                except ValueError as exc:
                    raise ParseError(
                        f"Cannot coerce key '{key}' to bool: {exc}",
                        raw_text=text,
                    ) from exc

    return parsed


def parse_llm_bool(value: object) -> bool:
    """Coerce an LLM-produced value to bool.

    True values:  True, "true", "yes", 1
    False values: False, "false", "no", 0
    Anything else raises ValueError.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes"):
            return True
        if lowered in ("false", "no"):
            return False
    raise ValueError(
        f"Cannot interpret {value!r} as bool. "
        "Expected: True/False, 'true'/'false', 'yes'/'no', 1/0."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_fences(text: str) -> str:
    """Remove outermost markdown code fence if present."""
    text = text.strip()
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text


def _extract_json_candidate(text: str, *, expect_list: bool) -> str:
    """Extract the outermost JSON value using bracket-counting.

    Tries array first when expect_list=True, otherwise tries object first.
    Falls back to the other bracket type if the preferred one is not found.
    Raises ParseError if no bracket start is found at all.
    """
    # Try direct parse first (fastest path for clean JSON)
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    pairs = [("[", "]"), ("{", "}")] if expect_list else [("{", "}"), ("[", "]")]

    for start_char, end_char in pairs:
        result = _bracket_extract(text, start_char, end_char)
        if result is not None:
            return result

    raise ParseError(
        f"No JSON object or array found in text",
        raw_text=text,
    )


def _bracket_extract(text: str, start_char: str, end_char: str) -> str | None:
    """Find the outermost balanced bracket pair using character-by-character scan.

    Correctly handles nested structures and string literals (including escaped
    characters inside strings).
    """
    start = text.find(start_char)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == start_char:
            depth += 1
        elif c == end_char:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None
