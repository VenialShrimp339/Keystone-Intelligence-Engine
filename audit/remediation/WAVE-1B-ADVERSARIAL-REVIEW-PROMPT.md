# Wave 1B Adversarial Review Prompt

Give this entire document to Codex (or another external reviewer) for adversarial review.

---

## Context

This is the Keystone Intelligence Engine, a multi-agent AI system for automated consulting research. We are implementing a remediation plan from `audit/remediation/decisions/FINAL-DECISIONS-v2.md`.

**Wave 1B implements Decision D: LLM Output Parsing Standard.**

The goal: replace 6 ad-hoc JSON extraction implementations scattered across the codebase with a single `safe_llm_json()` utility. Add `parse_llm_bool()` for boolean coercion. Add `ParseError` for explicit failure signaling. Eliminate all silent fallbacks.

**Deployment context:** We use `claude -p` (Claude CLI with Max subscription) as our LLM transport, NOT OpenAI APIs. The OpenAI/Codex OAuth paths in `llm_client.py` are legacy code.

**Prior wave:** Wave 1A (commit `9893a4d`) moved Pipeline component construction to per-run isolation, added per-analyst exception handling, subprocess cleanup, and circuit breaker fixes.

---

## The Approved Design (Decision D from FINAL-DECISIONS-v2.md)

### Recommendation

Single `safe_llm_json()` utility replaces ALL existing JSON extraction. `parse_llm_bool()` for boolean coercion. `ParseError` exception for failures. Every caller either recovers explicitly or surfaces a `QualityFlag`. No silent fallbacks.

### Six existing JSON extraction implementations being replaced:

1. `specification/_prompts.py:34-58` -- regex, dict only, greedy `{.*}` with DOTALL
2. `research_agent.py` -- bracket-counting `_extract_json_text`, most robust
3. `evaluator/layer1_deterministic.py:116-157` -- rfind-based
4. `evaluator/layer3_rubric.py:186-208` -- separate extractor
5. `evaluator/sprint_contract.py:75-88` -- find/rfind braces, returns `{}` on failure
6. `deliberation/analyst.py, aggregator.py, wwhtb.py` -- bare `json.loads`, no fence handling

### New file: `src/keystone/llm/parsing.py`

```python
class ParseError(Exception):
    def __init__(self, message: str, raw_text: str): ...

def safe_llm_json(
    text: str,
    *,
    required_keys: Sequence[str] = (),
    expect_list: bool = False,
    bool_keys: frozenset[str] = frozenset(),
) -> dict | list:
    """Single entry point for parsing LLM JSON output.
    Raises ParseError on failure. Never returns None. Never silently defaults."""

def parse_llm_bool(value: object) -> bool:
    """True: True, "true", "yes", 1. False: False, "false", "no", 0.
    Anything else: raise ValueError."""
```

### Required tests (11):

- `test_safe_llm_json_strips_fences`
- `test_safe_llm_json_handles_nested_fences`
- `test_safe_llm_json_extracts_array`
- `test_safe_llm_json_validates_required_keys`
- `test_safe_llm_json_coerces_bool_keys`
- `test_safe_llm_json_rejects_prose_as_json`
- `test_parse_llm_bool_string_false_is_false`
- `test_parse_llm_bool_rejects_unknown_values`
- `test_mece_validator_string_false_fails_dimension`
- `test_aggregator_judge_fenced_json`
- `test_parse_failure_does_not_fabricate_score`

---

## What Was Changed (18 files, 934 insertions, 239 deletions)

### New files (4):
- `src/keystone/llm/__init__.py` -- package init
- `src/keystone/llm/parsing.py` -- `ParseError`, `safe_llm_json`, `parse_llm_bool`, internal helpers (`_strip_fences`, `_extract_json_substring`)
- `tests/unit/llm/__init__.py` -- package init
- `tests/unit/llm/test_parsing.py` -- 23 tests covering all 11 required tests plus extras

### Modified source files (13):
1. `src/keystone/specification/_prompts.py` -- `extract_json` now delegates to `safe_llm_json`
2. `src/keystone/specification/engagement_classifier.py` -- bare `data["engagement_type"]` replaced with `safe_llm_json` + `.get()`
3. `src/keystone/specification/intent_clarifier.py` -- 4 bare key accesses replaced
4. `src/keystone/specification/priority_scorer.py` -- bare key accesses replaced
5. `src/keystone/specification/task_generator.py` -- bare key accesses replaced
6. `src/keystone/specification/validator.py` -- `bool()` replaced with `parse_llm_bool()`
7. `src/keystone/research/research_agent.py` -- `_extract_json_text` replaced with `safe_llm_json`
8. `src/keystone/deliberation/analyst.py` -- `json.loads` replaced with `safe_llm_json`
9. `src/keystone/deliberation/aggregator.py` -- both `json.loads` calls replaced
10. `src/keystone/deliberation/wwhtb.py` -- `json.loads` replaced
11. `src/keystone/evaluator/layer1_deterministic.py` -- `_parse_json_array` replaced with `safe_llm_json(expect_list=True)`
12. `src/keystone/evaluator/layer3_rubric.py` -- score extraction replaced; `ParseError` instead of silent score-50 default
13. `src/keystone/evaluator/sprint_contract.py` -- `_parse_contract_json` replaced with `safe_llm_json`

### Modified test files (1):
14. `tests/unit/specification/test_validator.py` -- added `test_mece_validator_string_false_fails_dimension`

### Key correctness fixes:
- **`validator.py`**: `bool("false")` was returning `True` (Python truthiness). Now uses `parse_llm_bool("false")` which correctly returns `False`.
- **`layer3_rubric.py`**: On JSON parse failure, score was silently set to 50. Now raises `ParseError` so the caller handles it explicitly.

### Test results:
750 passed, 1 pre-existing failure (`test_claim_level_citations_are_narrower_than_round_level` -- strict subset assertion, not related to Wave 1B), 2 xfailed, 1 xpassed.

---

## Adversarial Review Instructions

You are an adversarial reviewer. Your job is NOT to confirm the changes look good. Your job is to find where the implementation is wrong, incomplete, or could fail under real conditions.

### Files to read and review:

Read these files in the actual codebase:

1. `src/keystone/llm/parsing.py` -- the core new utility
2. `tests/unit/llm/test_parsing.py` -- its tests
3. All 13 modified source files listed above
4. `tests/unit/specification/test_validator.py` -- the new regression test
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.md` Decision D (lines 356-429) -- the approved design

### What to challenge:

1. **Does `safe_llm_json` actually handle all the edge cases the 6 old extractors handled?** Read each old extractor's logic and verify the new function covers it. Specifically:
   - Does it handle the greedy `{.*}` DOTALL regex pattern from `_prompts.py`?
   - Does it handle the bracket-counting from `research_agent.py`?
   - Does it handle the rfind-based extraction from `layer1_deterministic.py`?
   - Does it handle nested JSON within markdown fences?
   - Does it handle arrays (`[...]`) correctly when `expect_list=True`?
   - What happens with empty input? Whitespace-only input? Valid JSON with no fences?

2. **Are there any remaining silent fallbacks?** The design says "Never returns None. Never silently defaults." Check every call site:
   - Does any caller catch `ParseError` and silently return a default without logging?
   - Does `layer3_rubric.py` still fabricate scores anywhere?
   - Does `sprint_contract.py` still return `{}` on failure?

3. **Is the `bool_keys` feature correctly wired?** Check that `validator.py` actually passes bool keys through and that the coercion happens at the right level (inside `safe_llm_json`, not at the caller).

4. **Are old extractors fully removed?** Grep for:
   - `_extract_json_text`
   - `_parse_json_array`
   - `_parse_contract_json`
   - `_parse_score_json`
   - `json.loads` (should not appear in any of the 13 modified files)
   - `json.JSONDecodeError` (same)
   - The old regex pattern from `_prompts.py`

5. **Test coverage gaps:**
   - Do the tests actually test failure modes, or only happy paths?
   - Is `test_parse_failure_does_not_fabricate_score` testing the right thing (layer3_rubric, not just the parsing utility)?
   - Are there edge cases in the LLM output format that no test covers?

6. **Error propagation correctness:**
   - When `safe_llm_json` raises `ParseError`, does it propagate correctly through the retry mechanism (`retry_llm_call`)?
   - Could a `ParseError` in one component crash the entire pipeline instead of being caught at the right level?

7. **API contract:**
   - Does `safe_llm_json` match the spec exactly? Check parameter names, types, return types.
   - Is `ParseError` a proper exception with `message` and `raw_text` attributes?

### Output format:

For each finding:
- **Severity:** BLOCKER (must fix before proceeding) / DESIGN_CONCERN (architectural issue) / WARNING (non-blocking issue) / NOTE (observation)
- **File and line number**
- **What you found** (specific, with evidence from the code)
- **Why it matters** (what breaks or degrades)
- **What should change** (one sentence)

Do NOT fix anything. Report only.
