"""Tests for src/keystone/llm/parsing.py"""

from __future__ import annotations

import pytest

from keystone.llm.parsing import ParseError, parse_llm_bool, safe_llm_json


# ---------------------------------------------------------------------------
# safe_llm_json: fence stripping
# ---------------------------------------------------------------------------


def test_safe_llm_json_strips_fences():
    text = '```json\n{"key": "value"}\n```'
    result = safe_llm_json(text)
    assert result == {"key": "value"}


def test_safe_llm_json_strips_bare_fences():
    text = '```\n{"key": "value"}\n```'
    result = safe_llm_json(text)
    assert result == {"key": "value"}


def test_safe_llm_json_strips_fences_with_braces_in_string_value():
    # Fence-wrapped JSON where a string value contains curly braces.
    # This exercises the fence-strip path, not the bracket-counting path
    # (the bracket-counter is covered by test_safe_llm_json_handles_deeply_nested).
    text = '```json\n{"template": "{nested} structure", "score": 42}\n```'
    result = safe_llm_json(text)
    assert result["score"] == 42


# ---------------------------------------------------------------------------
# safe_llm_json: array extraction
# ---------------------------------------------------------------------------


def test_safe_llm_json_extracts_array():
    text = '[{"index": 0, "confidence": 0.9}]'
    result = safe_llm_json(text, expect_list=True)
    assert isinstance(result, list)
    assert result[0]["index"] == 0


def test_safe_llm_json_extracts_array_from_prose():
    text = "Here are the results:\n[1, 2, 3]\nEnd of output."
    result = safe_llm_json(text, expect_list=True)
    assert result == [1, 2, 3]


def test_safe_llm_json_raises_when_expecting_list_but_gets_dict():
    text = '{"key": "value"}'
    with pytest.raises(ParseError, match="Expected JSON array"):
        safe_llm_json(text, expect_list=True)


# ---------------------------------------------------------------------------
# safe_llm_json: required_keys validation
# ---------------------------------------------------------------------------


def test_safe_llm_json_validates_required_keys():
    text = '{"score": 85}'
    with pytest.raises(ParseError, match="Missing required keys"):
        safe_llm_json(text, required_keys=("score", "feedback"))


def test_safe_llm_json_passes_when_all_required_keys_present():
    text = '{"score": 85, "feedback": "good"}'
    result = safe_llm_json(text, required_keys=("score", "feedback"))
    assert result["score"] == 85


# ---------------------------------------------------------------------------
# safe_llm_json: bool_keys coercion
# ---------------------------------------------------------------------------


def test_safe_llm_json_coerces_bool_keys():
    text = '{"intent_clear": "true", "other": "value"}'
    result = safe_llm_json(text, bool_keys=frozenset(["intent_clear"]))
    assert result["intent_clear"] is True


def test_safe_llm_json_coerces_bool_keys_false():
    text = '{"intent_clear": "false"}'
    result = safe_llm_json(text, bool_keys=frozenset(["intent_clear"]))
    assert result["intent_clear"] is False


def test_safe_llm_json_coerces_bool_keys_yes_no():
    text = '{"flag_a": "yes", "flag_b": "no"}'
    result = safe_llm_json(text, bool_keys=frozenset(["flag_a", "flag_b"]))
    assert result["flag_a"] is True
    assert result["flag_b"] is False


def test_safe_llm_json_raises_on_uncoercible_bool_key():
    text = '{"intent_clear": "maybe"}'
    with pytest.raises(ParseError, match="Cannot coerce key"):
        safe_llm_json(text, bool_keys=frozenset(["intent_clear"]))


# ---------------------------------------------------------------------------
# safe_llm_json: prose rejection
# ---------------------------------------------------------------------------


def test_safe_llm_json_rejects_prose_as_json():
    text = "This is a sentence with no JSON in it at all."
    with pytest.raises(ParseError):
        safe_llm_json(text)


def test_safe_llm_json_rejects_empty_string():
    with pytest.raises(ParseError):
        safe_llm_json("")


# ---------------------------------------------------------------------------
# safe_llm_json: trailing comma tolerance
# ---------------------------------------------------------------------------


def test_safe_llm_json_tolerates_trailing_commas():
    text = '{"key": "value",}'
    result = safe_llm_json(text)
    assert result["key"] == "value"


# ---------------------------------------------------------------------------
# safe_llm_json: nested structures
# ---------------------------------------------------------------------------


def test_safe_llm_json_handles_deeply_nested():
    text = '{"outer": {"inner": {"deep": [1, 2, 3]}}}'
    result = safe_llm_json(text)
    assert result["outer"]["inner"]["deep"] == [1, 2, 3]


def test_safe_llm_json_handles_json_preceded_by_commentary():
    text = 'Here is the result:\n\n{"score": 72, "feedback": "needs work"}'
    result = safe_llm_json(text)
    assert result["score"] == 72


# ---------------------------------------------------------------------------
# parse_llm_bool
# ---------------------------------------------------------------------------


def test_parse_llm_bool_true_values():
    assert parse_llm_bool(True) is True
    assert parse_llm_bool("true") is True
    assert parse_llm_bool("True") is True
    assert parse_llm_bool("yes") is True
    assert parse_llm_bool("YES") is True
    assert parse_llm_bool(1) is True


def test_parse_llm_bool_string_false_is_false():
    assert parse_llm_bool("false") is False
    assert parse_llm_bool("False") is False
    assert parse_llm_bool("no") is False
    assert parse_llm_bool("NO") is False
    assert parse_llm_bool(False) is False
    assert parse_llm_bool(0) is False


def test_parse_llm_bool_rejects_unknown_values():
    with pytest.raises(ValueError):
        parse_llm_bool("maybe")

    with pytest.raises(ValueError):
        parse_llm_bool("1.0")

    with pytest.raises(ValueError):
        parse_llm_bool(None)

    with pytest.raises(ValueError):
        parse_llm_bool(2)


# ---------------------------------------------------------------------------
# Integration-style tests required by FINAL-DECISIONS-v2.1
# ---------------------------------------------------------------------------


def test_mece_validator_string_false_fails_dimension():
    """The bug: bool("false") == True. parse_llm_bool("false") must be False.

    MECEValidator uses parse_llm_bool on each dimension value from the LLM.
    If the LLM returns the string "false", the dimension must be False (fail),
    not True (pass). This test pins the fix so it cannot regress.
    """
    # Simulate what MECEValidator does for each dimension value
    assert parse_llm_bool("false") is False
    assert parse_llm_bool("False") is False
    assert parse_llm_bool("FALSE") is False

    # Verify the old behaviour would have been wrong
    assert bool("false") is True  # this is the bug being fixed


def test_aggregator_judge_fenced_json():
    """Aggregator._judge_select receives LLM output that may be fence-wrapped.

    The judge prompt asks for: {"selected_analyst": "...", "reasoning": "..."}
    The LLM may wrap that in ```json ... ```. safe_llm_json must handle it.
    """
    fenced = '```json\n{"selected_analyst": "ach", "reasoning": "ACH best supported"}\n```'
    result = safe_llm_json(fenced, required_keys=("selected_analyst", "reasoning"))
    assert result["selected_analyst"] == "ach"
    assert result["reasoning"] == "ACH best supported"

    # Also works without fences (clean JSON)
    clean = '{"selected_analyst": "quantitative", "reasoning": "Data-backed"}'
    result2 = safe_llm_json(clean, required_keys=("selected_analyst", "reasoning"))
    assert result2["selected_analyst"] == "quantitative"


def test_parse_failure_does_not_fabricate_score():
    """Parse failure must raise ParseError, never silently return a default score.

    The old layer3_rubric.py returned {"score": 50} on parse failure.
    safe_llm_json must raise ParseError so callers cannot accidentally use
    fabricated mid-range scores as real evaluation results.
    """
    malformed_responses = [
        "I was unable to evaluate this dimension.",
        "Score: 72",
        "```json\nnot valid json\n```",
        "",
        "{}[]",
    ]
    for response in malformed_responses:
        with pytest.raises(ParseError):
            safe_llm_json(response, required_keys=("score",))
