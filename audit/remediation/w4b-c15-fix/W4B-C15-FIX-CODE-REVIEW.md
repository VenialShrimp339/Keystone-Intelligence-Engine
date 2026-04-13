# W4B C-15 Fix Code Review

- Authoritative fix commit reviewed: `4d8f647cab66541ca63ec1494dc31ad957786bbf`
- Parent reviewed: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Code truth source: clean detached checkout at `/tmp/keystone-w4b-c15-review-JeHOZe`
- Dirty authoritative fix worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4b-c15-post-retro` was not used as code truth.
- Main workspace docs were used only for authority and fix-spec material, not as code truth.

## Scope Checked

- Read the required authority docs first, including `graphify-out/GRAPH_REPORT.md`, the `W4B-C15` bug/fix/test/rerun specs, the prior `W4B-2` runtime audit, control-plane state, active handoff, retrospective review ledger, audit execution plan, Batch 2+ prompts, and `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`.
- Reviewed only the committed diff `65a612dc1400abbedcfbdda1f173cd72a3a90c06..4d8f647cab66541ca63ec1494dc31ad957786bbf` from the clean detached checkout.
- Verified `4d8f647cab66541ca63ec1494dc31ad957786bbf` is a direct child of `65a612dc1400abbedcfbdda1f173cd72a3a90c06`.
- Exact changed file surface:
  - `graphify-out/GRAPH_REPORT.md`
  - `graphify-out/graph.json`
  - `src/keystone/evaluator/layer1_deterministic.py`
  - `tests/unit/evaluator/test_layer1.py`
- Minimum allowed surface check:
  - Runtime edits stayed inside `src/keystone/evaluator/layer1_deterministic.py`, matching the approved runtime seam (`audit/remediation/w4b-c15-fix/W4B-C15-MINIMUM-FIX-SPEC.md:19-27`, `49-67`, `91-99`).
  - Test edits stayed inside `tests/unit/evaluator/test_layer1.py`, matching the approved regression surface (`audit/remediation/w4b-c15-fix/W4B-C15-MINIMUM-FIX-SPEC.md:19-33`, `91-99`; `audit/remediation/w4b-c15-fix/W4B-C15-REGRESSION-TEST-SPEC.md:3-22`).
  - `tests/unit/evaluator/test_evaluator.py` and `tests/e2e/test_mock_pipeline.py` were rerun only, not edited, matching the approved proof surface (`audit/remediation/w4b-c15-fix/W4B-C15-MINIMUM-FIX-SPEC.md:29-33`; `audit/remediation/w4b-c15-fix/W4B-C15-REGRESSION-TEST-SPEC.md:34-55`).
  - No scope creep landed in prompt, result-shape, fetch, stage, specification, pipeline, or control-plane surfaces; the diff does not touch `fact_decomposition.md`, `evaluator.py`, `models/evaluation.py`, `layer2_citation_gate.py`, or any control-plane file (`audit/remediation/w4b-c15-fix/W4B-C15-MINIMUM-FIX-SPEC.md:35-47`, `69-79`; `audit/remediation/w4b-c15-fix/DOWNSTREAM-RERUN-SCOPE.md:65-77`).

## Evidence

- Lineage and file-surface verification:
  - `git cat-file -p 4d8f647cab66541ca63ec1494dc31ad957786bbf` shows `parent 65a612dc1400abbedcfbdda1f173cd72a3a90c06`.
  - `git diff --name-only 65a612dc1400abbedcfbdda1f173cd72a3a90c06 4d8f647cab66541ca63ec1494dc31ad957786bbf` returned only the four files listed above.
- Runtime fix behavior:
  - `src/keystone/evaluator/layer1_deterministic.py:32-44` is the only runtime logic hunk.
  - The patch changes `has_sentence_like_text` from `any(mark in snippet for mark in ".!?") and len(snippet_words) >= 12` to `any(mark in snippet for mark in ".!?")`.
  - Empty-snippet rejection at `src/keystone/evaluator/layer1_deterministic.py:33-35`, title-equality rejection at `:38-41`, the `>= 40` word rule at `:44`, and the existing lightweight punctuation-based sentence heuristic all remain in place.
  - `_format_citation_for_prompt()` is unchanged at `src/keystone/evaluator/layer1_deterministic.py:47-59`, so the output contract changes only because the helper now returns `True` for the short full-sentence case.
  - No fetch behavior, stage boundary, `facts_unverifiable` counting, or evaluator feedback plumbing changed; `Layer1Evaluator.evaluate()` and downstream counting are untouched at `src/keystone/evaluator/layer1_deterministic.py:74-160`.
- Regression proof quality:
  - `tests/unit/evaluator/test_layer1.py:244-285` adds the required load-bearing regression.
  - The new test uses the exact snippet `Revenue reached $50M in 2025.`, captures the fact-decomposition prompt, and uses a mock LLM that returns `SUPPORTED` only when `Content: Revenue reached $50M in 2025.` is actually present in the prompt, else `UNVERIFIABLE`.
  - The assertions match the spec exactly: `facts_verified == 1`, `facts_failed == 0`, `facts_unverifiable == 0`, prompt contains `Snippet status: usable evidence text`, prompt contains `Content: Revenue reached $50M in 2025.`, and prompt does not contain `Snippet status: metadata only or snippet-thin` (`audit/remediation/w4b-c15-fix/W4B-C15-REGRESSION-TEST-SPEC.md:7-22`).
  - The retained invariants remain covered in the same file: title-only stays `UNVERIFIABLE` at `tests/unit/evaluator/test_layer1.py:177-206`, and long substantive snippets remain usable at `:208-241`, matching the frozen contract (`audit/remediation/w4b-c15-fix/W4B-C15-REGRESSION-TEST-SPEC.md:24-32`; `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md:145-156`).
- Detached proof runs:
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/evaluator/test_layer1.py tests/unit/evaluator/test_evaluator.py`
  - Result: `23 passed in 0.58s`
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/e2e/test_mock_pipeline.py`
  - Result: `1 passed in 1.18s`
- Detached runtime probes:
  - Exact prompt-capture probe on `Layer1Evaluator.evaluate()` with snippet `Revenue reached $50M in 2025.` produced:
    - `facts_verified 1`
    - `facts_failed 0`
    - `facts_unverifiable 0`
    - `Snippet status: usable evidence text`
    - `Content: Revenue reached $50M in 2025.`
  - Additional helper probe confirmed the approved edge behavior:
    - `empty False`
    - `title_only_exact False`
    - `short_sentence True`
    - `long_snippet True`
- Graphify collateral:
  - The only non-runtime/test files in the commit are `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json`.
  - I do not treat that as semantic scope creep because generated graphify collateral is part of the approved proof surface after code edits (`audit/remediation/w4b-c15-fix/W4B-C15-MINIMUM-FIX-SPEC.md:29-33`).
  - The inspected `graph.json` diff includes new extracted test node/edges for `test_short_full_sentence_snippet_is_usable_evidence_text`, which is consistent with the added regression rather than unauthorized runtime expansion.

## Findings

- No blocking findings.
- Non-blocking scope note: the literal commit surface is four files rather than the strict two-file runtime/test minimum because it includes regenerated `graphify-out/` collateral. That is acceptable here because the only semantic code and test edits stay inside the approved `C-15` seam.
- This snapshot is suitable for the narrow `W4B-2` rerun described in `audit/remediation/w4b-c15-fix/DOWNSTREAM-RERUN-SCOPE.md:5-21`; it does not reopen `W4-1`, `W4B-1`, or `W4D-1` because their owned surfaces remain untouched (`audit/remediation/w4b-c15-fix/DOWNSTREAM-RERUN-SCOPE.md:23-84`).

ACCEPTABLE
