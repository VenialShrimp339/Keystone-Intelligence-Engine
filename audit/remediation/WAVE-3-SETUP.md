# Wave 3 Setup

*Date: 2026-04-12 | Status: active Wave 3 setup checkpoint | Wave 3 code must run in a clean worktree*

---

## What This File Is For

This is the active setup doc for Wave 3.

Use it only after reading:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
4. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

This file turns the seam freeze into an implementation runway.  
It does not reopen Wave 2B, and it does not authorize any Wave 3B work.

## Wave Activation

- Seam-freeze checkpoint: `65074ca`
- Last cleared code commit: `2cdbfec`
- Wave 3 implementation baseline: `2cdbfec`
- Controller branch: `codex/remediation-program`
- Required implementation branch: `codex/remediation-wave-3`
- Required implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3`
- Main workspace policy: controller/docs only

## Binding Scope In

Wave 3 includes only the completeness work approved in `FINAL-DECISIONS-v2.1.md` and frozen by `WAVE-3A-SEAM-FREEZE.md`:

1. Deep research audit events and deep/shallow template prompt wiring
2. DAG topological batch dispatch in the orchestrator
3. Concrete post-synthesis verifier extraction and insertion
4. Provenance sidecar generation from filtered render surfaces
5. Dual-axis taxonomy and domain-aware routing
6. Provisional M&A / Restructuring profile expansion
7. Remaining E2 cleanup:
   - deliberation gather fallback
   - subprocess cleanup
   - circuit-breaker hardening
   - HITL polling cleanup

## Binding Scope Out

The following remain explicitly out of scope for Wave 3:

1. `StructuredOutline`
2. `src/keystone/structuring/`
3. renderer migration to outline consumption
4. orchestrator-owned outer round loop
5. persisted branch-coverage stop logic
6. round `N+1` task refinement
7. novelty-exhaustion authority at orchestrator scope
8. Wave 4 / 4B content-layer changes
9. Wave 5 calibration work
10. unrelated repo cleanup or main-workspace dirty-file cleanup

## Execution Slices

Wave 3 should be implemented in this order unless a later candidate artifact records a justified deviation:

1. Slice A: taxonomy / classification / routing
2. Slice B: deep-research formalization
3. Slice C: verifier + provenance-sidecar primitives
4. Slice G: remaining E2 cleanup
5. Slice H: orchestrator integration hotspot

Rationale:

- The setup keeps most work off `src/keystone/pipeline/orchestrator.py` until lower-level pieces are ready.
- The orchestrator remains the highest merge-risk file and should have a single owner in the code lane.
- Wave 3 must not introduce Wave 3B's outer-loop controller while landing these slices.

## Initial Allowed Write Set

### Code

- `src/keystone/events.py`
- `src/keystone/models/research.py`
- `src/keystone/models/__init__.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/template_registry.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/deliberation/deliberation.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- `src/keystone/pipeline/provenance_sidecar.py`
- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/hitl/service.py`
- `src/keystone/hitl/gate.py`
- `src/keystone/llm_client.py`
- `src/keystone/gateway/circuit_breaker.py`

### Tests

- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/evaluator/test_rubric_config.py`
- `tests/unit/hitl/test_service.py`
- `tests/unit/hitl/test_gate.py`
- `tests/integration/test_deep_research.py`
- `tests/canary/test_architectural_guarantees.py`

### Generated Collateral Expected With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Initial Denylist

Do not treat these as in-scope for Wave 3 unless a later controller checkpoint explicitly widens scope:

- `src/keystone/models/structuring.py`
- `src/keystone/structuring/**`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/research/round_state.py` if it starts to carry live outer-loop authority before Wave 3B setup
- `CURRENT-STATE.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- historical Wave 2B review packets
- unrelated main-workspace dirty files outside the Wave 3 code lane

## Required Test Matrix

At minimum, the Wave 3 candidate must run the real enforcing seams behind these suites:

1. `tests/unit/specification/test_engagement_classifier.py`
2. `tests/unit/specification/test_template_registry.py`
3. `tests/unit/specification/test_task_generator.py`
4. `tests/unit/research/test_research_agent.py`
5. `tests/unit/pipeline/test_orchestrator.py`
6. `tests/unit/evaluator/test_rubric_config.py`
7. `tests/unit/hitl/test_service.py`
8. `tests/unit/hitl/test_gate.py`
9. `tests/unit/deliberation/test_deliberation.py`
10. `tests/integration/test_deep_research.py`
11. `tests/canary/test_architectural_guarantees.py`

## Required Runtime Probes

The candidate artifact set must name probes for these invariants:

1. Deep mode emits audit-visible events and governance can see gateway bypass state.
2. Shallow mode consumes template prompt material in synthesis without reviving round-broadcast citations.
3. Dependent tasks do not start before declared dependencies complete.
4. Failed or unevaluated task provenance cannot leak through the verifier into the render surface.
5. The provenance sidecar distinguishes consulted, rendered, and rejected evidence.
6. Domain-aware routing can choose provisional M&A / Restructuring profile paths without falling back to a generic default.

## Worktree Bootstrap

The next code lane must begin from the cleared baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/remediation-wave-3 ../Keystone-Intelligence-Engine-wave-3 2cdbfec
```

Then work from:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3
```

If the clean worktree lacks its own virtual environment, reuse the shared repository venv by absolute path while keeping the workdir on the clean lane.

After any code-file changes in the worktree, rebuild graphify before ending the implementation session:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If default `python3` cannot import `graphify`, use the recorded fallback interpreter from `audit/remediation/control-plane/RECOVERY-RULES.md`.

## Candidate Artifact Requirements

Wave 3 candidate artifacts must live under `audit/remediation/runs/wave-3/` and include:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Use `candidate-TEMPLATE-file-manifest.md` in the run folder as the starting scaffold.

## Carried Follow-Up

- `W2B-R01` remains visible: parseable but under-specified sprint-contract JSON can still produce empty enforcement fields. Do not silently lose this follow-up while executing Wave 3.

## Reopen / Hard-Stop Triggers

Stop and return to the control plane if any of these happen:

1. A proposed Wave 3 change requires Wave 3B outer-loop authority or L2 outline/renderer work.
2. The clean Wave 3 worktree cannot be opened from `2cdbfec` without colliding with unrelated state.
3. The candidate write set needs to widen beyond this setup doc plus the seam freeze without a committed controller update.
4. A new architecture decision is needed that is not already settled in `FINAL-DECISIONS-v2.1.md`.
