# W3B-1 Wave 3B Control-Path Audit

- Slice: `W3B-1`
- Top-line verdict: `CLEARED`
- Authority docs source for current review context: current controller authority stack in the main workspace rooted at `CONTROL-PLANE-STATE.yaml`, `ACTIVE-HANDOFF.md`, `RETROSPECTIVE-LINEAGE-MANIFEST.yaml`, and `RETROSPECTIVE-REVIEW-LEDGER.yaml`
- Code baseline: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Code parent: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- Code target: `8dd97bee1e9b5a13c0336890888259df72269149`
- Code truth source: detached review checkout at `/tmp/keystone-w3b1-fix-code-ciwj3o`
- Dirty main workspace status: present and explicitly not trusted as code truth
- Pre-rerun fix-review gate:
  - `audit/remediation/w3b-control-fix/W3B-FIX-CODE-REVIEW.md`: `ACCEPTABLE`
  - `audit/remediation/w3b-control-fix/W3B-FIX-BEHAVIOR-REVIEW.md`: `ACCEPTABLE`
- Graphify status in reviewed code snapshot `8dd97be`: `graphify-out/GRAPH_REPORT.md` present; `graphify-out/wiki/index.md` absent

## Prerequisite Proof

Authoritative prerequisite layer:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`

Current authoritative statuses read from that layer before launch:

- `CP-1`: `CLEARED`
- `CP-2`: `CLEARED`
- `RP-1`: `CLEARED`
- `W2B-1`: `CLEARED`
- `W3A-1`: `CLEARED`
- `W3-1`: `CLEARED`

Pre-rerun fix gate:

- code review: `ACCEPTABLE`
- behavior review: `ACCEPTABLE`

Result:

- `W3B-1` was launchable on the authoritative prerequisite layer, and the stop-law fix cleared the required pre-rerun review gate before this slice re-ran.

## Exact Authority Docs Read

From the current controller authority stack in the main workspace:

- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/w3b-control-fix/W3B-CONTROL-BUG-ANALYSIS.md`
- `audit/remediation/w3b-control-fix/W3B-MINIMUM-FIX-SPEC.md`
- `audit/remediation/w3b-control-fix/W3B-REGRESSION-TEST-SPEC.md`
- `audit/remediation/w3b-control-fix/DOWNSTREAM-RERUN-SCOPE.md`
- `audit/remediation/w3b-control-fix/W3B-FIX-CODE-REVIEW.md`
- `audit/remediation/w3b-control-fix/W3B-FIX-BEHAVIOR-REVIEW.md`
- `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
- `audit/remediation/WAVE-3B-SETUP.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-implementation.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-file-manifest.md`

From the detached `8dd97be` reviewed code snapshot:

- `graphify-out/GRAPH_REPORT.md`
- focused diffs for `src/keystone/pipeline/orchestrator.py` and `tests/unit/pipeline/test_orchestrator.py`
- spot checks for `src/keystone/models/structuring.py`, `src/keystone/structuring/content_structuring.py`, `src/keystone/pipeline/markdown_renderer.py`, `src/keystone/research/context_loader.py`, and `src/keystone/research/round_state.py`

## Packet Integrity

- The fix delta `65a612d..8dd97be` stays inside the approved minimum-remediation surface:
  - `src/keystone/pipeline/orchestrator.py`
  - `tests/unit/pipeline/test_orchestrator.py`
  - generated graphify collateral
- `src/keystone/pipeline/orchestrator.py` and `tests/unit/pipeline/test_orchestrator.py` are unchanged between historical blocked candidate `5cc9585` and pre-fix base `65a612d`, so the remediation lands directly on the exact control-path surface that `W3B-1` previously blocked.
- The detached review checkout was used as the sole code-truth surface. The dirty controller workspace remained docs-only and non-authoritative for code truth.

Historical proof-bundle status in the detached `8dd97be` checkout:

- full named Wave 3B bundle: `1 failed, 95 passed, 2 xfailed in 8.79s`
- only failure: `tests/canary/test_architectural_guarantees.py::test_evaluator_fallback_constructors_produce_valid_models`

Comparison against the detached pre-fix base `65a612d` checkout:

- the same full named bundle also fails there: `1 failed, 92 passed, 2 xfailed in 8.60s`
- the same failing test is the only failure there too

W3B-relevant rerun evidence:

- full Wave 3B bundle excluding that unrelated evaluator-fallback canary: `95 passed, 1 deselected, 2 xfailed in 2.48s`
- targeted stop-law regressions: `3 passed, 23 deselected in 0.30s`
- targeted canary probe on the pre-fix base:
  - `test_dependent_tasks_do_not_start_before_dependencies_complete`: `passed`
  - evaluator-fallback constructor check: `xfailed` when isolated

Packet-integrity verdict:

- no blocker

Reason:

- the only failing named test is pre-existing on the `65a612d` base and sits outside the Wave 3B control-path surface repaired here
- no packet or write-set drift was found in the remediation commit itself

## Scope And Boundary Conformity

- `StructuredOutline` remains a real typed model in `src/keystone/models/structuring.py`.
- `ContentStructurer` still emits `StructuredOutline` on the runtime path in `src/keystone/structuring/content_structuring.py`.
- `MarkdownRenderer` still consumes `StructuredOutline` rather than raw pre-L2 finding structures in `src/keystone/pipeline/markdown_renderer.py`.
- Persisted round-state continuity remains present under the `round_state` / `context_loader` surfaces.
- The orchestrator still instantiates `AgentPool(..., max_rounds=1)`, preserving Wave 3B's single-controller runtime contract.
- The fix delta does not touch `StructuredOutline`, renderer, round-state persistence, context reload, `ResearchAgent`, `AgentPool`, or any Wave 4 / 4B content surface.

Structural contract verdict:

- no packet or scope blocker

## Runtime Correctness

### Prior blocker 1 is closed: sufficiency no longer ignores open threads

Observed fixed logic in `src/keystone/pipeline/orchestrator.py`:

```python
if coverage_complete and has_high_confidence and not has_open_threads:
    return RoundStopSignal.SUFFICIENCY
```

That now matches the minimum-fix contract:

- coverage must be complete
- at least one high-confidence claim must exist
- no open gaps / contested claims / insufficient-evidence threads may remain

Runtime proof:

- `TestWave3BControlStopLaw.test_open_gap_blocks_sufficiency_and_refines_follow_up_task`
- result: the real orchestrator path now returns `CONTINUE`, keeps `generated_task_ids == ["task_gap"]`, and carries the expected round-2 refinement text

### Prior blocker 2 is closed: novelty now outranks stale continue paths

Observed fixed ordering in `src/keystone/pipeline/orchestrator.py`:

```python
if round_number >= round_limit:
    return RoundStopSignal.MAX_ROUNDS
if previous_outline is not None and _outline_signature(previous_outline) == _outline_signature(outline):
    return RoundStopSignal.NOVELTY
return RoundStopSignal.CONTINUE
```

This removes the stale pre-novelty `CONTINUE` branches that previously masked novelty on:

- persistent open-thread loops
- persistent uncovered-branch loops

Runtime proof:

- `TestWave3BControlStopLaw.test_stagnant_open_gap_stops_on_novelty_not_continue`
- `TestWave3BControlStopLaw.test_stagnant_uncovered_branch_stops_on_novelty_not_continue`

Result:

- unchanged unresolved rounds now stop on `NOVELTY`, not `CONTINUE`

### No local orchestrator regression surfaced on the reviewed control path

- `tests/unit/pipeline/test_orchestrator.py` passes cleanly in the authoritative fix snapshot.
- The Wave 3B-relevant proof bundle continues to pass once the unrelated pre-existing evaluator canary is excluded.
- No new regression signal surfaced in the stop-law, follow-up refinement, outline-render, round-state continuity, or single-controller runtime surfaces.

## Slice Assessment

### `outline-render-state contract`

Verdict: `CLEARED`

Basis:

- provenance-bearing outline, renderer consumption, and persisted round-state continuity remain intact in the reviewed snapshot
- the remediation commit does not disturb those previously-cleared Wave 3B structural surfaces

### `single-controller iterative loop`

Verdict: `CLEARED`

Basis:

- the previously blocked stop-law precedence defect is repaired on the authoritative runtime path
- the new regressions are load-bearing on `Pipeline.run()` and `result.round_states[...]`
- the real control path now blocks false sufficiency on open threads and fires novelty before stale continuation

## Top-Line Verdict

`CLEARED`

Why:

- packet integrity passed
- scope and boundary conformity passed
- the previously blocked runtime-control finding is repaired on the authoritative path
- the only failing named proof-bundle test is pre-existing on the `65a612d` base and is not attributable to the Wave 3B control-path fix

## Later-Wave Trust Impact

Because `W3B-1` is now `CLEARED` on slice merits:

- `W4-1` may now launch once this rerun is promoted into the authoritative review ledger
- `W4B-1`, `W4B-2`, and `X-1` remain sequence-gated behind `W4-1` and the existing Batch 6 / Batch 7 prerequisites

## Residual Risks

- `tests/canary/test_architectural_guarantees.py::test_evaluator_fallback_constructors_produce_valid_models` still fails in the full named bundle on both `65a612d` and `8dd97be`; it is not attributed to this W3B fix, but it remains a separate suite-health issue.
- `_outline_signature()` still defines novelty only from rendered-outline structure. That matches the minimum-fix scope and is not a blocker for this lane, but broader novelty semantics remain out of scope here.
- Downstream trust restoration still requires `W4-1`, `W4B-1`, `W4B-2`, and `X-1` to run in order after promotion.
