# Wave 3B Setup

*Date: 2026-04-12 | Status: active Wave 3B setup checkpoint | Wave 3B code must run in a clean worktree*

---

## What This File Is For

This is the active setup doc for Wave 3B.

Use it only after reading:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
4. `audit/remediation/WAVE-3-SETUP.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `audit/remediation/WAVE-3-3B-PREWORK.md`
7. `graphify-out/GRAPH_REPORT.md`

This file turns cleared Wave 3 commit `4819527` into the Wave 3B implementation runway.
It does not reopen Wave 3, and it does not authorize any Wave 4 / 4B content work.

## Wave Activation

- Wave 3 cleared candidate: `4819527`
- Wave 3B implementation baseline: `4819527`
- Controller branch: `codex/remediation-program`
- Required implementation branch: `codex/remediation-wave-3b`
- Required implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b`
- Main workspace policy: controller/docs only

## Current-Code Anchors

Wave 3B setup is based on the cleared `4819527` runtime, which currently has these relevant properties:

1. `src/keystone/events.py` already contains L2 event types (`OutlineGenerated`, `SectionDrafted`, `SprintContractNegotiated`) plus the Wave 3 deep-research visibility event.
2. `src/keystone/contracts.py` still has a placeholder `ContentStructuringContract`; there is no concrete L2 implementation yet.
3. `src/keystone/pipeline/markdown_renderer.py` still renders directly from `StructuredFinding` + `ConfidenceMap`, not from an outline model.
4. `src/keystone/research/research_agent.py` still owns the live shallow multi-round loop (`max_rounds`, novelty stop, quality stop).
5. `src/keystone/research/context_loader.py` reads compiled wiki entries from `memory/INDEX.md`, but has no persisted round-state awareness.
6. `src/keystone/knowledge/wiki_builder.py`, `src/keystone/knowledge/index_maintainer.py`, and `src/keystone/knowledge/engagement_store.py` already provide the compiled-wiki continuity seams that Wave 3B can build on.
7. `src/keystone/pipeline/orchestrator.py` now has real DAG dispatch, verifier insertion, and provenance sidecar wiring, but it does not yet own an outer research loop or any L2 outline handoff.

## Binding Scope In

Wave 3B includes only the control-path convergence work approved in `FINAL-DECISIONS-v2.1.md` and staged by the Wave 3 seam freeze:

1. `StructuredOutline` as a typed model that preserves:
   - `issue_tree_branch_id`
   - source `task_ids`
   - source `claim_ids`
   - source `citation_ids`
2. Thin real Pipeline-L2 implementation in `src/keystone/structuring/content_structuring.py`
3. Renderer migration so `MarkdownRenderer` consumes `StructuredOutline`, not raw pre-L2 structures
4. Persisted round-state continuity under `engagements/{engagement_id}/memory/rounds/`
5. Round-to-round branch coverage computation using issue-tree branch IDs
6. Lightweight sufficiency / quality gate at orchestrator scope between rounds
7. Novelty-exhaustion stop condition at orchestrator scope
8. Round `N+1` task refinement from uncovered branches, contradictions, open gaps, and prior findings
9. Single authoritative round controller at orchestrator scope
10. ResearchAgent demotion to a per-round shallow execution primitive under Wave 3B control

## Binding Scope Out

The following remain explicitly out of scope for Wave 3B:

1. Wave 4 / 4B prompt, rubric, actionability, or template content changes
2. Wave 5 calibration work
3. prompt-library rewrites outside the minimum mechanical adaptation needed to keep tests truthful
4. evaluator rubric-policy redesign or new calibration logic
5. deep-research gateway unification beyond the existing Wave 3 audit / governance visibility
6. citation-processor semantic redesign
7. provenance-sidecar redesign as a new product surface
8. broad repo cleanup or main-workspace dirty-file cleanup
9. unrelated model migrations outside the L2 / round-state control path

## Wave 3B Control Rule

Wave 3B freezes the runtime authority model as follows:

1. The orchestrator becomes the only authoritative cross-task round controller.
2. Shallow `ResearchAgent` execution must run exactly one orchestrator-directed round per dispatch in Wave 3B mode.
3. Deep research may remain a task-local single session, but it does not become a peer round controller.
4. `ContextLoader`, `WikiBuilder`, and `IndexMaintainer` are continuity helpers, not round controllers.
5. No Wave 3B candidate clears if the runtime can still double-iterate through both the orchestrator and the shallow `ResearchAgent`.

## Execution Slices

Wave 3B should be implemented in this order unless a later candidate artifact records a justified deviation:

1. Slice D: `StructuredOutline` model + content-structuring contract + thin L2 module
2. Slice F: round-state persistence + continuity plumbing
3. Slice E: renderer migration to outline consumption
4. Slice H: final orchestrator convergence and authoritative round control

Rationale:

- The outline contract must stabilize before the renderer depends on it.
- Round-state persistence and continuity helpers should exist before the orchestrator owns live round advancement.
- `src/keystone/pipeline/orchestrator.py` remains the highest-conflict hotspot and should be the final convergence slice with a single owner.

## Initial Allowed Write Set

### Code

- `src/keystone/events.py`
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
- `src/keystone/knowledge/wiki_builder.py`
- `src/keystone/knowledge/index_maintainer.py`
- `src/keystone/knowledge/engagement_store.py`

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

### Generated Collateral Expected With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Initial Denylist

Do not treat these as in-scope for Wave 3B unless a later controller checkpoint explicitly widens scope:

- `src/keystone/evaluator/prompts/**`
- `src/keystone/specification/prompts/**`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/template_registry.py`
- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/pipeline/provenance_sidecar.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- Wave 4, Wave 4B, or Wave 5 setup docs
- immutable historical review packets
- unrelated main-workspace dirty files outside the Wave 3B code lane

## Required Structural Decisions For The Code Lane

These are now frozen for Wave 3B implementation:

1. `StructuredOutline` is the canonical L2 handoff surface for rendering.
2. The outline must retain branch/task/claim/citation provenance as first-class fields, not only in generated text.
3. Round-state persistence lives under `memory/rounds/` with machine-readable artifacts owned by `research/round_state.py`.
4. `ContextLoader` loads prior round-state summaries plus compiled wiki context; it does not store controller truth.
5. Orchestrator round control uses existing issue-tree branch IDs and prior-round signals; it does not reopen L0 classification.
6. Shallow `ResearchAgent` execution in Wave 3B is per-round and subordinate to the orchestrator.

## Required Test Matrix

At minimum, the Wave 3B candidate must run the real enforcing seams behind these suites:

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

## Required Runtime Probes

The candidate artifact set must name probes for these invariants:

1. `StructuredOutline` preserves branch/task/claim/citation provenance end to end.
2. `MarkdownRenderer` consumes the outline surface, not raw `ConfidenceMap` / `StructuredFinding` inputs.
3. The runtime has exactly one authoritative round controller.
4. Branch coverage and novelty rules drive continuation on the real runtime path.
5. Round `N+1` tasks are derived from uncovered branches, contradictions, gaps, and prior findings rather than raw replay.
6. Context reload uses persisted `memory/rounds/` state plus compiled wiki artifacts from prior rounds.

## Worktree Bootstrap

The next code lane must begin from the cleared baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/remediation-wave-3b ../Keystone-Intelligence-Engine-wave-3b 4819527
```

Then work from:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b
```

If the clean worktree lacks its own virtual environment, reuse the shared repository venv by absolute path while keeping the workdir on the clean lane.

After any code-file changes in the worktree, rebuild graphify before ending the implementation session:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If default `python3` cannot import `graphify`, use the recorded fallback interpreter from `audit/remediation/control-plane/RECOVERY-RULES.md`.

## Candidate Artifact Requirements

Wave 3B candidate artifacts must live under `audit/remediation/runs/wave-3b/` and include:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Use `candidate-TEMPLATE-file-manifest.md` in the run folder as the starting scaffold.

## Carried Follow-Up

- `W2B-R01` remains visible: parseable but under-specified sprint-contract JSON can still produce empty enforcement fields. Do not silently lose this follow-up while executing Wave 3B.

## Reopen / Hard-Stop Triggers

Stop and return to the control plane if any of these happen:

1. A proposed Wave 3B change requires Wave 4 / 4B content decisions or Wave 5 calibration decisions.
2. The clean Wave 3B worktree cannot be opened from `4819527` without colliding with unrelated state.
3. The candidate write set needs to widen beyond this setup doc without a committed controller update.
4. The runtime cannot be reduced to one authoritative round controller without a new architecture decision not already settled in `FINAL-DECISIONS-v2.1.md`.
5. The outline contract cannot preserve branch/task/claim/citation provenance without widening into a broader model redesign.
