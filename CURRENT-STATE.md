# Current State
*Last updated: 2026-04-12 | Updated by: bootstrap adoption pass for autonomous remediation*

---

## Live status

- **Wave 1:** Complete.
- **Wave 2A:** Cleared in commit `16e0bc7` (`Wave 2A: fix final hash and corroboration leakage`).
- **Wave 2B:** Checkpoint candidate `4ff7e90` exists and is **blocked**.
- **Round-3 overlay:** Accepted for Wave 2B and later. It does **not** reopen Waves 1A through 2A.

## What just happened

1. Wave 2B was implemented and checkpointed in commit `4ff7e90` (`Wave 2B: add enforcement model and profile-driven routing`).
2. Independent adversarial reviews of `16e0bc7..4ff7e90` both returned `BLOCKED`.
3. The blockers are now tracked explicitly in `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`.
4. Dirty Wave 2B blocker-fix work in the main workspace has been captured as recovery evidence only. It is not authoritative until replayed in a clean worktree, committed, and re-reviewed.
5. The repo now has a bootstrap control plane so a fresh session can recover from disk instead of chat history.

## What happens next

1. Read the control-plane files first:
   - `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
   - `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. Create a clean implementation worktree rooted at `4ff7e90`.
3. Replay only the approved Wave 2B blocker-fix work from the recovery patch.
4. Create the next Wave 2B candidate commit.
5. Review that committed snapshot against the full `16e0bc7..candidate` scope.
6. Do **not** start Wave 3 until Wave 2B is truly cleared.

## Reconciled wave plan

| Wave | Status | Scope |
|------|--------|-------|
| Wave 1 (1A + 1B + 1C) | **Complete** | Lifecycle isolation, parsing standard, citation-identity foundation |
| Wave 2A | **Cleared** (`16e0bc7`) | Citation identity completion and provenance gating |
| Wave 2B | **Blocked remediation in progress** (`4ff7e90` blocked) | Enforcement model plus `E-1`, `E-9`, `E-10`, `E-6`, `E-7` |
| Wave 3A | Planned | Seam freeze for verifier, provenance sidecar, round-state, and loop ownership |
| Wave 3 | Planned | Completeness work plus dual-axis taxonomy and related routing |
| Wave 3B | Planned | Thin Pipeline-L2 plus minimum viable live iterative loop |
| Wave 4 | Planned | Research/design plus explicit polish lane |
| Wave 4B | Planned | Content implementation from Wave 4 memos |
| Wave 5 | Planned | Calibration against frozen benchmark outputs |

## Authoritative docs for a fresh session

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
- `audit/remediation/runs/wave-2b/candidate-4ff7e90-review-synthesis.md`
- `audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md`
- `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`

## Non-authoritative but still useful

- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` -- still binding for design
- `SESSION-LOG.md` -- historical trail
- `audit/remediation/WAVE-3-3B-PREWORK.md`
- `audit/remediation/WAVE-4-4B-PREWORK.md`
- `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
