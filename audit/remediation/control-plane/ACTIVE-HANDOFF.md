# Active Handoff

## Current Truth

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B is now cleared at `2cdbfec`.
- The blocked `4ff7e90` snapshot has been recovered in a clean worktree, replayed, committed, and independently re-reviewed.
- The main workspace remains controller/docs only.
- The next required step is **Wave 3A seam freeze**, not more Wave 2B remediation and not direct Wave 3 code.
- The authoritative bootstrap plan remains [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md).

## Authoritative Order

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [candidate-2cdbfec-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md)
4. [candidate-2cdbfec-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md)
5. [candidate-2cdbfec-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md)
6. [candidate-2cdbfec-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md)
7. [WAVE-2B-BLOCKER-REMEDIATION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md)
8. [candidate-2cdbfec-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md)
9. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
10. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)
11. [WAVE-2B-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SETUP.md)

## Active State Tuple

- `active_wave`: `wave-2b`
- `active_state`: `cleared`
- `execution_baseline_commit`: `16e0bc7`
- `review_target_commit`: `2cdbfec`
- `docs_reconcile_commit`: `HEAD`
- `next_recovery_checkout`: `2cdbfec`

## Closed Blockers

- `W2B-B01`: LIGHT coverage fail-open is closed in `2cdbfec`.
- `W2B-B02`: task `priority` / `importance` misrouting is closed in `2cdbfec`.
- `W2B-B03`: effective evaluator profile shadowing is closed in `2cdbfec`.
- `W2B-B04`: HITL gate policy-ownership drift is closed in `2cdbfec`.

## Residual Follow-Ups

- `W2B-R01`: parse-invalid sprint-contract JSON now fails explicitly, but parseable under-specified JSON can still return empty Wave 2B enforcement fields.

## Latest Review Packets

- [candidate-2cdbfec-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md)
- [candidate-2cdbfec-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md)
- [candidate-2cdbfec-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md)
- [candidate-2cdbfec-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md)

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Treat `2cdbfec` as the last cleared code commit for future implementation lanes.
3. Create and commit `WAVE-3A-SEAM-FREEZE.md` before any Wave 3 code begins.
4. Only after the seam-freeze doc lands may a new clean Wave 3A / Wave 3 worktree be opened from `2cdbfec`.

## Cleared Candidate Artifacts

- [candidate-2cdbfec-implementation.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-implementation.md)
- [candidate-2cdbfec-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md)
- [candidate-2cdbfec-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md)
- [candidate-2cdbfec-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md)
- [candidate-2cdbfec-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md)
- [candidate-2cdbfec-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md)

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WAVE-3-3B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-3B-PREWORK.md) — advisory only until Wave 3A seam freeze lands
- [WAVE-4-4B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-4B-PREWORK.md) — advisory only
- [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md) — advisory only
