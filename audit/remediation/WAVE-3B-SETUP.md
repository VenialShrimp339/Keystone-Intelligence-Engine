# Wave 3B: Cleared Historical Setup

*Date: 2026-04-12 | Updated after cleared candidate `5cc9585` | Retained as historical Wave 3B execution context*

---

## What This File Is For

Wave 3B is no longer active remediation work.

This file is retained to explain what Wave 3B covered and what was required to clear it, but the live authority for future sessions is now:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md`
4. `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md`
5. `audit/remediation/WAVE-4-SETUP.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

Do **not** use this file as permission to continue Wave 3B coding.

## Cleared State

- Wave 3B implementation baseline: `4819527`
- Wave 3B cleared candidate: `5cc9585`
- Wave 3B implementation branch: `codex/remediation-wave-3b`
- Wave 3B implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b`
- Main workspace policy remained controller/docs only throughout execution.
- The next required step is a committed `WAVE-4-SETUP.md` checkpoint before any Wave 4 polish code or Wave 4B content implementation begins.

## Binding Scope In

Wave 3B included only the control-path convergence work approved in `FINAL-DECISIONS-v2.1.md` and staged by the Wave 3 seam freeze:

1. `StructuredOutline` as a typed model that preserves issue-tree branch, task, claim, and citation provenance
2. Thin real Pipeline-L2 implementation in `src/keystone/structuring/content_structuring.py`
3. Renderer migration so `MarkdownRenderer` consumes `StructuredOutline`
4. Persisted round-state continuity under `engagements/{engagement_id}/memory/rounds/`
5. Round-to-round branch coverage computation using issue-tree branch IDs
6. Lightweight sufficiency / quality gate at orchestrator scope between rounds
7. Novelty-exhaustion stop condition at orchestrator scope
8. Round `N+1` task refinement from uncovered branches, contradictions, open gaps, and prior findings
9. Single authoritative round controller at orchestrator scope
10. `ResearchAgent` demotion to a per-round shallow execution primitive under Wave 3B control

## Binding Scope Out

The following remained explicitly out of scope for Wave 3B:

1. Wave 4 / 4B prompt, rubric, actionability, or template content changes
2. Wave 5 calibration work
3. Prompt-library rewrites outside the minimum mechanical adaptation needed to keep tests truthful
4. Evaluator rubric-policy redesign or new calibration logic
5. Deep-research gateway unification beyond the existing Wave 3 audit / governance visibility
6. Citation-processor semantic redesign
7. Provenance-sidecar redesign as a new product surface
8. Broad repo cleanup or main-workspace dirty-file cleanup
9. Unrelated model migrations outside the L2 / round-state control path

## Historical Execution Order

Wave 3B was executed in this order:

1. `StructuredOutline` model plus content-structuring contract and thin L2 module
2. Round-state persistence plus continuity plumbing
3. Renderer migration to outline consumption
4. Final orchestrator convergence and authoritative round control

## Historical Allowed Write Set

### Code

- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/round_state.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/__init__.py`

### Tests

- `tests/unit/test_protocol_contracts.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/knowledge/test_wiki_builder.py`
- `tests/unit/knowledge/test_index_maintainer.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/canary/test_architectural_guarantees.py`

### Generated Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Historical Required Test Matrix

Wave 3B clearance required this minimum bundle:

1. `tests/unit/test_protocol_contracts.py`
2. `tests/unit/structuring/test_content_structuring.py`
3. `tests/unit/research/test_round_state.py`
4. `tests/unit/research/test_context_loader.py`
5. `tests/unit/research/test_research_agent.py`
6. `tests/unit/knowledge/test_wiki_builder.py`
7. `tests/unit/knowledge/test_index_maintainer.py`
8. `tests/unit/pipeline/test_markdown_renderer.py`
9. `tests/unit/pipeline/test_orchestrator.py`
10. `tests/e2e/test_mock_pipeline.py`
11. `tests/canary/test_architectural_guarantees.py`

## Historical Required Runtime Probes

Wave 3B clearance required proof that:

1. `StructuredOutline` preserves branch/task/claim/citation provenance end to end.
2. `MarkdownRenderer` consumes the outline surface, not raw `ConfidenceMap` / `StructuredFinding` inputs.
3. The runtime has exactly one authoritative round controller.
4. Branch coverage and novelty rules drive continuation on the real runtime path.
5. Round `N+1` tasks are derived from uncovered branches, contradictions, gaps, and prior findings rather than raw replay.
6. Context reload uses persisted `memory/rounds/` state plus compiled wiki artifacts from prior rounds.

## Historical Worktree Bootstrap

The Wave 3B code lane began from the cleared Wave 3 baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/remediation-wave-3b ../Keystone-Intelligence-Engine-wave-3b 4819527
```

Then work from:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b
```

If the clean worktree lacked its own virtual environment, the shared repository venv was reused by absolute path while keeping the workdir on the clean lane.

## Historical Candidate Artifact Requirements

Wave 3B candidate artifacts lived under `audit/remediation/runs/wave-3b/` and included:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

## Carried Follow-Up

- `W2B-R01` remains visible: parseable but under-specified sprint-contract JSON can still produce empty enforcement fields. Wave 3B did not close it.

## What Happens Next

1. Commit the Wave 3B cleared-state reconcile checkpoint.
2. Create and commit `WAVE-4-SETUP.md`.
3. Only then continue Wave 4 docs lanes and later open a clean Wave 4 polish lane rooted at `5cc9585` if a narrow code slice is frozen.

## Historical Reopen / Hard-Stop Triggers

During active Wave 3B execution, the controller was expected to stop and return to the control plane if any of these happened:

1. A proposed Wave 3B change requires Wave 4 / 4B content decisions or Wave 5 calibration decisions.
2. The clean Wave 3B worktree cannot be opened from `4819527` without colliding with unrelated state.
3. The candidate write set needed to widen beyond the setup doc without a committed controller update.
4. The runtime could not be reduced to one authoritative round controller without a new architecture decision not already settled in `FINAL-DECISIONS-v2.1.md`.
5. The outline contract could not preserve branch/task/claim/citation provenance without widening into a broader model redesign.
