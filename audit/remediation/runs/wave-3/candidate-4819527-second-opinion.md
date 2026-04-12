# Wave 3 Second Opinion

- **Baseline commit:** `2cdbfec`
- **Target commit:** `4819527`
- **Candidate parent:** `2cdbfec`
- **Reviewed snapshot:** `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3`
- **Commit surface reviewed:** `git show --stat --summary 4819527`, `git diff --name-only 2cdbfec..4819527`, targeted source inspection, the required Wave 3 pytest matrix, and the focused seven-probe bundle
- **Scoping note:** code truth came only from the clean Wave 3 worktree; control-plane and review-authority docs were read from the main workspace

## Authority and Method

I read these authority/context documents before reviewing the candidate:

- `graphify-out/GRAPH_REPORT.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
- `audit/remediation/WAVE-3-SETUP.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/WAVE-3-3B-PREWORK.md`
- `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
- `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`

I focused on three questions:

1. Are the new Wave 3 invariants actually load-bearing on the runtime path?
2. Did the candidate stay inside the frozen Wave 3 seam and denylist boundary?
3. Did the candidate avoid falsely reopening E2 surfaces that were already good in `2cdbfec`?

## Findings

No blocker was identified in `4819527`.

## Boundary Check

- The committed diff stayed within the approved Wave 3 surface plus the expected graphify collateral.
- New files are limited to the approved verifier module, provenance sidecar module, and deep-research integration test.
- No `StructuredOutline`, renderer migration, outer-loop round controller, or persisted Wave 3B control path landed in this candidate.

## Runtime Check

- Deep research is now audit-visible and governance-visible.
- Template prompt material is consumed in both deep and shallow research paths.
- Dependency batching is real and no longer metadata-only.
- Failed or unevaluated material is filtered by the concrete verifier before render/sidecar assembly.
- The sidecar records consulted, rendered, and rejected evidence separately.
- The M&A / Restructuring path is now represented in the classifier and evaluator profile map.

## Residual Notes

- The candidate intentionally leaves the already-stable E2 cleanup code untouched in `deliberation.py`, `llm_client.py`, `circuit_breaker.py`, `hitl/service.py`, and `hitl/gate.py`; the verification matrix still covered those surfaces.
- The worktree still has untracked `graphify-out/cache/` output after the rebuild. That is not part of the candidate.

## Verdict

`CLEARED`

My second-pass opinion is that `4819527` clears Wave 3 against the active control-plane scope and should advance the controller to the Wave 3B setup gate.
