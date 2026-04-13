# W4 E-4 Fix Code Review

- Authoritative fix commit reviewed: `104658506075ccdc0e5c4eeeca8f8982ac6c3566`
- Parent reviewed: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Code truth source: clean detached checkout at `/tmp/keystone-w4-e4-fix-review-TqMScG`
- Dirty workspaces were not used as code truth.

## Scope Checked

- Read and anchored on the required authority docs, including the bug analysis, minimum-fix spec, regression-test spec, downstream rerun scope, prior `W4-1` audit, control-plane state, active handoff, retrospective review ledger, audit execution plan, and Batch 2+ launch prompts.
- Reviewed only the committed diff `65a612dc1400abbedcfbdda1f173cd72a3a90c06..104658506075ccdc0e5c4eeeca8f8982ac6c3566`.
- Exact changed file surface:
  - `graphify-out/GRAPH_REPORT.md`
  - `graphify-out/graph.json`
  - `src/keystone/pipeline/markdown_renderer.py`
  - `tests/unit/pipeline/test_markdown_renderer.py`
- Minimum allowed code/test surface check:
  - Runtime edits stayed inside `src/keystone/pipeline/markdown_renderer.py`, matching the approved runtime surface (`audit/remediation/w4-e4-fix/W4-E4-MINIMUM-FIX-SPEC.md:21-24`, `47-72`, `85-93`).
  - Test edits stayed inside `tests/unit/pipeline/test_markdown_renderer.py`, matching the approved test surface (`audit/remediation/w4-e4-fix/W4-E4-MINIMUM-FIX-SPEC.md:25-32`, `85-93`).
  - `tests/e2e/test_mock_pipeline.py` was rerun only, not edited, matching the proof surface (`audit/remediation/w4-e4-fix/W4-E4-REGRESSION-TEST-SPEC.md:29-49`).
  - No out-of-scope runtime/test files changed: `src/keystone/structuring/content_structuring.py`, structuring models, sample-schema files, control-plane files, and later-slice-owned files stayed untouched.
  - Total commit surface is broader than the literal two-file minimum because it also refreshes `graphify-out/`; that is generated collateral, not runtime/test semantic expansion, and it matches the lane guardrail to rebuild graphify after code-file changes (`audit/remediation/w4-e4-fix/IMPLEMENTATION-SESSION-PROMPT.md:13`, `127-130`).

## Evidence

- File-surface verification:
  - `git diff --name-only 65a612dc1400abbedcfbdda1f173cd72a3a90c06 104658506075ccdc0e5c4eeeca8f8982ac6c3566`
  - Result: only the four files listed above changed.
- Runtime fix behavior:
  - `src/keystone/pipeline/markdown_renderer.py:207-221` is the only runtime logic change.
  - The new implementation resolves each input id through `citation_numbers`, drops unknown ids, dedupes after resolution by building a set of resolved manifest numbers, sorts ascending, and renders the final label from that sorted numeric list.
  - `_citation_numbers()` remains unchanged at `src/keystone/pipeline/markdown_renderer.py:194-205`, so alias resolution still comes from the existing manifest-number map, as required by the minimum-fix spec (`audit/remediation/w4-e4-fix/W4-E4-MINIMUM-FIX-SPEC.md:49-59`, `63-72`) and the bug analysis (`audit/remediation/w4-e4-fix/W4-E4-BUG-ANALYSIS.md:43-61`).
  - `_render_sources()` and outline construction were untouched, so there is no observed broader semantic drift in source-list numbering, outline order, or item storage semantics.
- Regression proof quality:
  - `tests/unit/pipeline/test_markdown_renderer.py:257-260` adds a helper that creates the required reversed local citation order.
  - `tests/unit/pipeline/test_markdown_renderer.py:334-343` adds the focused regression required by the spec: the manifest stays `[CAN-001, CAN-002]`, the rendered item uses `["CAN-002", "CAN-001"]`, and the assertions require `Sources: [1, 2]` while forbidding `Sources: [2, 1]`.
  - That exactly matches the required regression shape (`audit/remediation/w4-e4-fix/W4-E4-REGRESSION-TEST-SPEC.md:5-17`) and closes the specific gap identified in the bug analysis (`audit/remediation/w4-e4-fix/W4-E4-BUG-ANALYSIS.md:63-73`).
- Proof runs executed against the detached snapshot:
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/pipeline/test_markdown_renderer.py`
  - Result: `6 passed in 0.24s`
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/e2e/test_mock_pipeline.py`
  - Result: `1 passed in 17.05s`
- Additional detached-snapshot alias/dedupe probe:
  - Ran a direct renderer probe with manifest citations `CAN-001`, `CAN-002`, alias `SRC-ALIAS -> CAN-001`, and target item citations `["CAN-002", "SRC-ALIAS", "CAN-001", "SRC-ALIAS"]`.
  - Observed target rendered line: `Sources: [1, 2]`.
  - This confirms the implementation normalizes after alias resolution and dedupes on the resolved numeric identity, not raw id spelling.
- Downstream rereview implications:
  - This snapshot is suitable for the narrow `W4-1` rerun the downstream scope doc calls for (`audit/remediation/w4-e4-fix/DOWNSTREAM-RERUN-SCOPE.md:5-18`).
  - `W4D-1` and `W3B-1` do not reopen because their protected surfaces remain untouched (`audit/remediation/w4-e4-fix/DOWNSTREAM-RERUN-SCOPE.md:21-39`).

## Findings

- No blocking findings.
- Non-blocking scope note: the total commit surface includes `graphify-out/` collateral, so the literal file manifest is wider than the strict two-file minimum. I do not consider that disqualifying here because the runtime/test surface stayed within the approved seam and the extra files are generated graph refresh output rather than behavioral scope creep.

## Final Verdict

`ACCEPTABLE`
