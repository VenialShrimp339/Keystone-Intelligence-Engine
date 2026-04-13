# W4 E-4 Fix Behavior Review

- Reviewed commit: `104658506075ccdc0e5c4eeeca8f8982ac6c3566`
- Reviewed parent: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Review mode: committed snapshot only, inspected from clean authoritative worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro`

## Behavioral Checks

1. Exact inline multi-citation ordering bug is closed.
   - The only runtime behavior change is in `src/keystone/pipeline/markdown_renderer.py:207-221`, where `_format_citation_refs()` now resolves manifest numbers, drops unknown ids, dedupes by resolved numeric identity, sorts ascending, and renders the normalized list.
   - A detached parent-snapshot probe against `65a612dc1400abbedcfbdda1f173cd72a3a90c06` reproduced the known failure for manifest `[CAN-001, CAN-002]` plus item citations `["CAN-002", "CAN-001"]`: `Sources: [2, 1]`.
   - The same probe against `104658506075ccdc0e5c4eeeca8f8982ac6c3566` rendered `Sources: [1, 2]`.

2. The other W4 E-4 invariants are preserved.
   - Existing renderer assertions still require numbered client-facing sources, absence of `## Quality Assessment`, and absence of raw `CAN-` / `CIT-` labels in output (`tests/unit/pipeline/test_markdown_renderer.py:321-343`).
   - The new focused regression adds the exact required reversed-order case and asserts both `Sources: [1, 2]` present and `Sources: [2, 1]` absent (`tests/unit/pipeline/test_markdown_renderer.py:257-260`, `334-343`).
   - Direct post-fix probe output still showed inline `Sources: [1, 2]` while the `## Sources` block remained manifest-numbered as `1.` then `2.`, so the fix corrected only the item-local ordering defect and did not disturb source-list numbering.

3. Required regression and smoke proof are present and sufficient for this minimum lane.
   - Required load-bearing suite passed on the authoritative snapshot:
     - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/pipeline/test_markdown_renderer.py`
     - Result: `6 passed in 0.21s`
   - Required end-to-end smoke passed on the authoritative snapshot:
     - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/e2e/test_mock_pipeline.py`
     - Result: `1 passed in 58.68s`
   - `tests/e2e/test_mock_pipeline.py` was not edited in the fix diff, which matches the rerun-only smoke requirement in `W4-E4-REGRESSION-TEST-SPEC.md`.

4. Downstream launch assumptions are preserved.
   - The committed diff from `65a612dc1400abbedcfbdda1f173cd72a3a90c06..104658506075ccdc0e5c4eeeca8f8982ac6c3566` touches only:
     - `src/keystone/pipeline/markdown_renderer.py`
     - `tests/unit/pipeline/test_markdown_renderer.py`
     - `graphify-out/GRAPH_REPORT.md`
     - `graphify-out/graph.json`
   - No change widened into `src/keystone/structuring/content_structuring.py`, later-slice runtime surfaces, or the smoke test file, so the downstream rerun scope remains consistent with `DOWNSTREAM-RERUN-SCOPE.md`: rereview and promotion of repaired `W4-1` is the next required authority step before `W4B-1` / `W4B-2` may launch.

## Evidence

- Clean authoritative snapshot checks:
  - `git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro status --short --branch`
  - `git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro rev-parse HEAD HEAD^`
  - `git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro diff --name-only 104658506075ccdc0e5c4eeeca8f8982ac6c3566^ 104658506075ccdc0e5c4eeeca8f8982ac6c3566`
- Runtime behavior comparison:
  - Parent probe in detached worktree: reversed local citations rendered `Sources: [2, 1]`
  - Fix probe in authoritative worktree: reversed local citations rendered `Sources: [1, 2]`
- Code and test anchors:
  - Sorting logic: `src/keystone/pipeline/markdown_renderer.py:207-221`
  - Existing invariant coverage: `tests/unit/pipeline/test_markdown_renderer.py:321-343`
  - New regression fixture and assertion: `tests/unit/pipeline/test_markdown_renderer.py:257-260`, `334-343`

## Residual Risks

- No behavior blocker remains on the exact E-4 defect reviewed here.
- The commit includes regenerated `graphify-out/` artifacts because repo policy requires graph rebuild after code edits; those files do not change runtime behavior, but a separate scope-only review could note them if needed.
- This report supports fix acceptability for the committed snapshot only. It does not itself promote `W4-1` in the authoritative review ledger.

## Final Verdict

`ACCEPTABLE`
