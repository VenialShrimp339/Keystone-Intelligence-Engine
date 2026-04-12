# Candidate 6406e46 Implementation

- Baseline commit: `5cc9585`
- Parent commit: `5cc9585`
- Target commit: `6406e46`
- Implementation branch: `codex/remediation-wave-4`
- Implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4`

## Summary

This candidate lands the frozen Wave 4 polish slice on top of cleared Wave 3B baseline `5cc9585`.

Claimed closures in this candidate:

- `E-2`: Completeness is reclassified as `EXPERT_CHECKABLE` instead of `MACHINE_CHECKABLE`.
- `E-4`: Client markdown no longer emits the internal quality block and no longer exposes raw citation-engineering IDs as source labels.
- `E-5`: Sample engagements are synced to the live schema surface by removing legacy fields, normalizing tool names to the registered enum, and making that semantic check load-bearing in tests.

The candidate stays inside the approved Wave 4 polish write set and does not reopen Wave 4B content work.

## Exact Files Changed

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`
- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`

## Exact Tests Run

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4` against committed `6406e46`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/test_schemas.py \
  tests/unit/pipeline/test_markdown_renderer.py \
  tests/e2e/test_mock_pipeline.py
```

Result: `32 passed in 2.05s`

## Runtime Probe Mapping

- Completeness classification probe
  Command:

  ```bash
  PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/python -c "from keystone.models.evaluation import RUBRIC_EVAL_TYPES, EvalType, RubricDimension; value = RUBRIC_EVAL_TYPES[RubricDimension.COMPLETENESS]; print(value); raise SystemExit(0 if value == EvalType.EXPERT_CHECKABLE else 1)"
  ```

  Result: `expert_checkable`

- `tests/unit/pipeline/test_markdown_renderer.py`
  Confirms client markdown renders numbered manifest-order references, omits `## Quality Assessment`, and hides raw `CIT-` / `CAN-` source-label IDs.

- `tests/e2e/test_mock_pipeline.py`
  Confirms the full mock pipeline still renders markdown end to end while preserving `## Sources`, omitting the internal quality block, and keeping raw engineering citation IDs out of client output.

- `tests/unit/test_schemas.py`
  Confirms the sample engagements still validate against the live schemas and now fail if legacy `RESEARCH.md` fields or unregistered tool aliases reappear.

## Graphify Rebuild

Default command failed with `ModuleNotFoundError: No module named 'graphify'`.

Fallback command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4`:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

Result:

- `[graphify watch] Rebuilt: 3259 nodes, 18411 edges, 52 communities`
- `[graphify watch] graph.json and GRAPH_REPORT.md updated in graphify-out`

## Exact Files Safe To Stage

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`
- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`
