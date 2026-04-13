# W4B C-15 Fix Behavior Review

- Fix commit: `4d8f647cab66541ca63ec1494dc31ad957786bbf`
- Base commit: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Code-truth source: clean detached checkout at `/tmp/keystone-w4b-c15-review-JeHOZe` with `HEAD` pinned to `4d8f647cab66541ca63ec1494dc31ad957786bbf`
- Dirty authoritative fix worktree inspected but not trusted as code truth: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4b-c15-post-retro` at the same commit, with untracked `engagements/` and `graphify-out/cache/`
- Main verification commands run:
  - `git -C /tmp/keystone-w4b-c15-review-JeHOZe status --short --branch`
  - `git -C /tmp/keystone-w4b-c15-review-JeHOZe rev-parse HEAD HEAD^`
  - `git -C /tmp/keystone-w4b-c15-review-JeHOZe show --stat --summary --oneline 4d8f647cab66541ca63ec1494dc31ad957786bbf`
  - `git -C /tmp/keystone-w4b-c15-review-JeHOZe diff --unified=80 65a612dc1400abbedcfbdda1f173cd72a3a90c06 4d8f647cab66541ca63ec1494dc31ad957786bbf -- src/keystone/evaluator/layer1_deterministic.py tests/unit/evaluator/test_layer1.py`
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/evaluator/test_layer1.py tests/unit/evaluator/test_evaluator.py`
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/e2e/test_mock_pipeline.py`
  - direct prompt-capture probe on the clean fix checkout with exact snippet `Revenue reached $50M in 2025.`
  - same direct prompt-capture probe on a detached parent checkout at `/tmp/keystone-w4b-c15-review-parent`
  - targeted non-widening probe on the clean fix checkout for repeated-title and true-thin fragment cases

## Behavior Checks

1. The exact short full-sentence regression is closed on the real Layer 1 path.
   `src/keystone/evaluator/layer1_deterministic.py:32-44` makes the minimum helper-only change required by the fix spec: the empty-snippet check, title-equality rejection, and `>= 40` word rule are preserved, while the extra `>= 12` word floor is removed from the sentence-like branch.
   The new focused regression at `tests/unit/evaluator/test_layer1.py:243-285` matches the required shape exactly: one citation with `content_snippet="Revenue reached $50M in 2025."`, a captured fact-decomposition prompt, `SUPPORTED` only when the real sentence is present, and assertions for usable-evidence prompt text plus `facts_verified == 1`, `facts_failed == 0`, `facts_unverifiable == 0`.
   The required direct probe on the clean fix checkout produced the expected result:
   `facts_verified 1`
   `facts_failed 0`
   `facts_unverifiable 0`
   `Snippet status: usable evidence text`
   `Content: Revenue reached $50M in 2025.`

2. Parent-versus-fix behavior matches the authoritative bug statement exactly.
   The same direct probe against detached parent snapshot `65a612dc1400abbedcfbdda1f173cd72a3a90c06` still reproduced the blocked behavior:
   `facts_verified 0`
   `facts_failed 0`
   `facts_unverifiable 1`
   `Snippet status: metadata only or snippet-thin`
   `Content: No usable evidence text available for verification.`
   That isolates the behavioral change to the intended helper seam instead of any broader evaluator rewrite.

3. Title-only and true-thin behavior remain `UNVERIFIABLE`-oriented and were not widened incorrectly.
   Existing committed invariants still passed in `tests/unit/evaluator/test_layer1.py:177-205` and `tests/unit/evaluator/test_layer1.py:208-241`: title-only citations remain `UNVERIFIABLE`, and long substantive snippets remain usable evidence text.
   Existing evaluator feedback invariants also stayed green in `tests/unit/evaluator/test_evaluator.py:345-380` and `tests/unit/evaluator/test_evaluator.py:449-480`, so light-touch and standard feedback still surface unverifiable claims.
   The targeted non-widening probe on the clean fix checkout confirmed the two load-bearing negative cases that matter for this lane:
   repeated-title snippet -> `facts_unverifiable 1`, `Snippet status: metadata only or snippet-thin`
   true-thin fragment `Revenue growth 2025` -> `facts_unverifiable 1`, `Snippet status: metadata only or snippet-thin`
   I found no evidence that the fix converts metadata-only or genuinely thin non-sentence text into false `SUPPORTED` handling.

4. Required regression and smoke proof are present and sufficient.
   `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/evaluator/test_layer1.py tests/unit/evaluator/test_evaluator.py`
   Result: `23 passed in 0.64s`
   `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/e2e/test_mock_pipeline.py`
   Result: `1 passed in 1.26s`
   `tests/e2e/test_mock_pipeline.py` was not edited in the fix diff, which matches the rerun-only smoke requirement in `W4B-C15-REGRESSION-TEST-SPEC.md`.

5. The committed surface stays inside the approved minimum, so the downstream rereview assumption remains narrow.
   `git diff --name-only 65a612dc1400abbedcfbdda1f173cd72a3a90c06 4d8f647cab66541ca63ec1494dc31ad957786bbf` touches only:
   `src/keystone/evaluator/layer1_deterministic.py`
   `tests/unit/evaluator/test_layer1.py`
   `graphify-out/GRAPH_REPORT.md`
   `graphify-out/graph.json`
   No change widened into `src/keystone/evaluator/prompts/fact_decomposition.md`, `src/keystone/evaluator/evaluator.py`, `src/keystone/models/evaluation.py`, `src/keystone/evaluator/layer2_citation_gate.py`, or any other later-slice runtime surface. That matches `W4B-C15-MINIMUM-FIX-SPEC.md` and preserves the narrow downstream assumption in `DOWNSTREAM-RERUN-SCOPE.md`: rereview `W4B-2` only, with no broader reopen forced by this fix surface.

## Outcomes

- Exact required short-sentence behavior now works on the live `Layer1Evaluator.evaluate(...)` path.
- Parent snapshot still fails in the previously-blocked way, so the proof is discriminating rather than tautological.
- Title-only, repeated-title, and true-thin fragment cases remain `UNVERIFIABLE`-oriented.
- Required unit/evaluator and e2e smoke proof commands passed on the clean fix snapshot.
- Downstream rereview scope remains narrow: repaired `W4B-2` rerun only.

## Residual Risks

- The fix intentionally preserves the existing lightweight sentence heuristic instead of redesigning snippet-quality detection. That is the approved minimum for `C-15`, not a blocker for this review.
- The commit includes regenerated `graphify-out/` artifacts because repo policy requires graph rebuild after code edits; those files do not change runtime behavior.
- This report supports acceptability of the committed fix snapshot only. It does not itself promote the repaired `W4B-2` result in the authoritative review ledger.

ACCEPTABLE
