# Candidate 5cc9585 Implementation

- Baseline commit: `4819527`
- Parent commit: `4819527`
- Target commit: `5cc9585`
- Implementation branch: `codex/remediation-wave-3b`
- Implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b`

## Summary

This candidate lands the approved Wave 3B control-path convergence scope on top of cleared Wave 3 baseline `4819527`.

Claimed closures in this candidate:

- `StructuredOutline` is now a real typed Pipeline-L2 handoff surface with task / branch / claim / citation provenance.
- The renderer now consumes the outline surface instead of raw `StructuredFinding` / `ConfidenceMap` inputs.
- The orchestrator now owns the only authoritative cross-task round loop on the real runtime path.
- Pipeline L1 dispatch is reduced to one shallow round per orchestrator-directed pass.
- Round-to-round state now persists under `engagements/{engagement_id}/memory/rounds/`.
- Context reload now includes prior round summaries in addition to compiled wiki continuity.
- Round continuation and follow-up work are driven by coverage, sufficiency, novelty, gaps, and contested threads at orchestrator scope.
- The approved Wave 3B contract and canary surfaces are now load-bearing instead of placeholder seams.

## Exact Files Changed

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/research/__init__.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/round_state.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/test_protocol_contracts.py`

## Exact Tests Run

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b` against committed `5cc9585`:

```bash
TMP_ENG=$(mktemp -d); KEYSTONE_ENGAGEMENTS_DIR="$TMP_ENG/engagements" PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/test_protocol_contracts.py \
  tests/unit/structuring/test_content_structuring.py \
  tests/unit/research/test_round_state.py \
  tests/unit/research/test_context_loader.py \
  tests/unit/research/test_research_agent.py \
  tests/unit/knowledge/test_wiki_builder.py \
  tests/unit/knowledge/test_index_maintainer.py \
  tests/unit/pipeline/test_markdown_renderer.py \
  tests/unit/pipeline/test_orchestrator.py \
  tests/e2e/test_mock_pipeline.py \
  tests/canary/test_architectural_guarantees.py
```

Result: `93 passed, 2 xfailed in 11.61s`

## Runtime Probe Mapping

- `tests/unit/structuring/test_content_structuring.py`
  Confirms the outline groups claims by issue-tree branch and preserves claim / task provenance.
- `tests/unit/pipeline/test_markdown_renderer.py`
  Confirms rendering consumes the outline surface and keeps provenance-bearing sections intact.
- `tests/unit/pipeline/test_orchestrator.py`
  Confirms L2 sits on the real runtime path before evaluation / rendering and that filtered render surfaces exclude failed or unevaluated task material.
- `tests/unit/research/test_round_state.py`
  Confirms round-state files persist under the `memory/rounds/` surface.
- `tests/unit/research/test_context_loader.py`
  Confirms prior round summaries reload for later rounds.
- `tests/canary/test_architectural_guarantees.py::test_dependent_tasks_do_not_start_before_dependencies_complete`
  Confirms real dependency batching still governs dispatch timing under the Wave 3B controller.
- `tests/e2e/test_mock_pipeline.py`
  Confirms the full mock pipeline completes through the new outline and round-control path.

## Graphify Rebuild

Default command failed with `ModuleNotFoundError: No module named 'graphify'`.

Fallback command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b`:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

Result:

- `[graphify watch] Rebuilt: 3255 nodes, 18400 edges, 47 communities`
- `[graphify watch] graph.json and GRAPH_REPORT.md updated in graphify-out`

## Exact Files Safe To Stage

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/research/__init__.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/round_state.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/test_protocol_contracts.py`
