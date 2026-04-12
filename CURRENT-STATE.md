# Current State
*Last updated: 2026-04-12 | Updated by: Wave 2B cleared-state reconcile checkpoint*

---

## Live status

- **Wave 1:** Complete.
- **Wave 2A:** Cleared in commit `16e0bc7` (`Wave 2A: fix final hash and corroboration leakage`).
- **Wave 2B:** Cleared in commit `2cdbfec` (`Wave 2B: remediate blocked candidate 4ff7e90`).
- **Round-3 overlay:** Accepted for Wave 2B and later. It did **not** reopen Waves 1A through 2A.

## What just happened

1. Blocked Wave 2B candidate `4ff7e90` was recovered from the captured dirty patch in a clean `4ff7e90` worktree.
2. The replayed result was committed as `2cdbfec`.
3. Independent adversarial review and second opinion both returned `CLEARED` for `16e0bc7..2cdbfec`.
4. Wave 2B is now cleared, with one residual non-blocking follow-up around parseable but under-specified sprint-contract JSON.
5. The repo now needs a committed Wave 3A seam-freeze doc before any Wave 3 code begins.

## What happens next

1. Read the control-plane files first:
   - `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
   - `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. Treat `2cdbfec` as the last cleared code commit.
3. Create and commit `WAVE-3A-SEAM-FREEZE.md`.
4. Only after the seam-freeze doc lands may a clean Wave 3A / Wave 3 implementation worktree be opened from `2cdbfec`.
5. Do **not** reopen Wave 2B unless a true regression is found against the cleared candidate.

## Reconciled wave plan

| Wave | Status | Scope |
|------|--------|-------|
| Wave 1 (1A + 1B + 1C) | **Complete** | Lifecycle isolation, parsing standard, citation-identity foundation |
| Wave 2A | **Cleared** (`16e0bc7`) | Citation identity completion and provenance gating |
| Wave 2B | **Cleared** (`2cdbfec`) | Enforcement model plus `E-1`, `E-9`, `E-10`, `E-6`, `E-7` |
| Wave 3A | Next required doc checkpoint | Seam freeze for verifier, provenance sidecar, round-state, and loop ownership |
| Wave 3 | Planned | Completeness work plus dual-axis taxonomy and related routing |
| Wave 3B | Planned | Thin Pipeline-L2 plus minimum viable live iterative loop |
| Wave 4 | Planned | Research/design plus explicit polish lane |
| Wave 4B | Planned | Content implementation from Wave 4 memos |
| Wave 5 | Planned | Calibration against frozen benchmark outputs |

## Authoritative docs for a fresh session

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
- `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`

## Non-authoritative but still useful

- `audit/remediation/runs/wave-2b/candidate-2cdbfec-implementation.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md`
- `SESSION-LOG.md` -- historical trail
- `audit/remediation/WAVE-3-3B-PREWORK.md`
- `audit/remediation/WAVE-4-4B-PREWORK.md`
- `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
