# W4-1 Wave 4 Polish Audit

- Slice: `W4-1`
- Baseline / parent: `5cc9585`
- Target: `6406e46`
- Review mode: committed snapshot only, audited from detached worktree `/tmp/keystone-w4-1-jzvvQl`
- Subagents: none

## Authority Note

The prompt-required controller docs under `audit/remediation/control-plane/` plus the Wave 4 run-packet sidecars are not present inside commit `6406e46`. I used the current-workspace copies of those docs as audit instructions only, but all code and diff evidence below comes from the detached `6406e46` snapshot and the committed diff `5cc9585..6406e46`.

## Verification

- Re-ran the candidate proof suite against the detached snapshot:
  - `PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q tests/unit/test_schemas.py tests/unit/pipeline/test_markdown_renderer.py tests/e2e/test_mock_pipeline.py`
  - Result: `32 passed in 1.28s`
- Re-ran the E-2 runtime probe:
  - `RUBRIC_EVAL_TYPES[RubricDimension.COMPLETENESS] == EvalType.EXPERT_CHECKABLE`
  - Result: `expert_checkable`
- Added one detached-snapshot reproduction probe for E-4:
  - Manifest order `CAN-001`, `CAN-002` plus item citations `["CAN-002", "CAN-001"]`
  - Rendered output: `Sources: [2, 1]`

## E-2

No formal finding.

Evidence:

- `src/keystone/models/evaluation.py:80-90` now maps `RubricDimension.COMPLETENESS` to `EvalType.EXPERT_CHECKABLE`.
- The detached runtime probe returned `expert_checkable`.
- No extra evaluator-policy drift landed with the change; weights, thresholds, and other rubric-dimension eval types remain untouched in the committed diff.

## E-4

### Finding: inline numbered references are still ordered by claim citation order, not manifest order

The frozen Wave 4 spec requires client references to be numbered from manifest order and to keep that manifest order stable rather than reordering per claim occurrence. `src/keystone/pipeline/markdown_renderer.py:207-222` numbers citations from the manifest, but it emits inline references by iterating the incoming `citation_ids` list in whatever order the claim/outline already has. Upstream, that input order is not normalized to manifest order: branch items can preserve raw claim citation order at `src/keystone/structuring/content_structuring.py:121-127`, and confidence-derived items are sorted lexicographically by citation id at `src/keystone/structuring/content_structuring.py:479-489`, not by manifest position.

That mismatch is observable in the committed snapshot: with manifest citations `[CAN-001, CAN-002]` and an outline item carrying `["CAN-002", "CAN-001"]`, the renderer outputs `Sources: [2, 1]`. The current regression coverage misses this because `tests/unit/pipeline/test_markdown_renderer.py:299-326` only asserts single-reference cases and never exercises a multi-citation item whose local order disagrees with manifest order. This means E-4 is only partially landed: raw ids are hidden and the quality block is gone, but the manifest-stable numbering contract is still violated.

## E-5

No formal finding.

Evidence:

- The three frozen sample `RESEARCH.md.json` fixtures no longer carry `alternative_hypothesis`, `prior_confidence`, or `max_rounds`.
- The committed sample task files no longer contain the stale unregistered tool names called out by the Wave 4 spec.
- `tests/unit/test_schemas.py:20-22` and `:65-91` now make both invariants load-bearing by failing on reintroduced legacy fields or unregistered tools.

Residual note, not escalated to a formal finding:

- Two regulatory tasks now use `fred_data` as the third tool (`samples/luminar_lidar/research-tasks.json:186-192` and `samples/specialty_chemicals_ma/research-tasks.json:78-84`). That keeps enum validity, but it is the main place where sample realism feels thinnest if this slice is reopened.

## Scope Discipline

No formal finding.

Evidence:

- The committed diff touches 13 files, and that set matches the candidate manifest exactly:
  - `src/keystone/models/evaluation.py`
  - `src/keystone/pipeline/markdown_renderer.py`
  - the three sample `RESEARCH.md.json` files
  - the three sample `research-tasks.json` files
  - `tests/unit/pipeline/test_markdown_renderer.py`
  - `tests/unit/test_schemas.py`
  - `tests/e2e/test_mock_pipeline.py`
  - `graphify-out/GRAPH_REPORT.md`
  - `graphify-out/graph.json`
- No denylisted prompt, rubric, template, routing, evaluator-policy, or Wave 4B files were touched in `5cc9585..6406e46`.
- I found no evidence of prompt, rubric, template, or Wave 4B content leakage in the committed file surface.

## Top-Line

`CONTINGENT` — the snapshot stays inside the frozen Wave 4 polish lane and lands E-2 plus the mechanical parts of E-5, but E-4 still misses the manifest-order reference invariant required by the Wave 4 polish spec.
