# Current State
*Last updated: 2026-04-12 | Updated by: Wave 3B setup checkpoint*

---

## Live status

- **Wave 1:** Complete.
- **Wave 2A:** Cleared in commit `16e0bc7` (`Wave 2A: fix final hash and corroboration leakage`).
- **Wave 2B:** Cleared in commit `2cdbfec` (`Wave 2B: remediate blocked candidate 4ff7e90`).
- **Wave 3A:** Complete in commit `65074ca` (`docs: freeze Wave 3A seams`).
- **Wave 3:** Cleared in commit `4819527` (`feat: implement wave 3 provenance and routing`).
- **Wave 3B:** Active in setup state from cleared Wave 3 baseline `4819527`.
- **Round-3 overlay:** Accepted for Wave 2B and later. It did **not** reopen Waves 1A through 2A.

## What just happened

1. Blocked Wave 2B candidate `4ff7e90` was recovered from the captured dirty patch in a clean `4ff7e90` worktree.
2. The replayed result was committed as `2cdbfec`.
3. Independent adversarial review and second opinion both returned `CLEARED` for `16e0bc7..2cdbfec`.
4. Wave 2B is now cleared, with one residual non-blocking follow-up around parseable but under-specified sprint-contract JSON.
5. Wave 3A seam ownership was frozen in `65074ca`.
6. Wave 3 implementation landed in clean worktree commit `4819527` and cleared review.
7. `WAVE-3B-SETUP.md` now defines the active Wave 3B implementation runway.
8. The next step is opening a clean Wave 3B worktree from `4819527`, not broad cleanup or any Wave 4 / 4B content work.

## What happens next

1. Read the control-plane files first:
   - `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
   - `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. Treat `4819527` as the last cleared code commit.
3. Use `audit/remediation/WAVE-3B-SETUP.md` as the binding Wave 3B scope boundary.
4. Root the next clean implementation lane from `4819527`.
5. Keep Wave 3B out of the main workspace; controller/docs only still applies.
6. Do **not** reopen Wave 3 or Wave 2B unless a true regression is found against a cleared candidate.

## Reconciled wave plan

| Wave | Status | Scope |
|------|--------|-------|
| Wave 1 (1A + 1B + 1C) | **Complete** | Lifecycle isolation, parsing standard, citation-identity foundation |
| Wave 2A | **Cleared** (`16e0bc7`) | Citation identity completion and provenance gating |
| Wave 2B | **Cleared** (`2cdbfec`) | Enforcement model plus `E-1`, `E-9`, `E-10`, `E-6`, `E-7` |
| Wave 3A | **Complete** (`65074ca`) | Seam freeze for verifier, provenance sidecar, round-state, and loop ownership |
| Wave 3 | **Cleared** (`4819527`) | Completeness work plus dual-axis taxonomy, auditable deep research, verifier, sidecar, and DAG batching |
| Wave 3B | **Active / setup** | Thin Pipeline-L2 plus minimum viable live iterative loop |
| Wave 4 | Planned | Research/design plus explicit polish lane |
| Wave 4B | Planned | Content implementation from Wave 4 memos |
| Wave 5 | Planned | Calibration against frozen benchmark outputs |

## Authoritative docs for a fresh session

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
- `audit/remediation/WAVE-3-SETUP.md`
- `audit/remediation/WAVE-3B-SETUP.md`
- `audit/remediation/runs/wave-3/candidate-4819527-adversarial-review.md`
- `audit/remediation/runs/wave-3/candidate-4819527-second-opinion.md`
- `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md`
- `audit/remediation/runs/wave-3/candidate-4819527-clearance.md`
- `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`

## Non-authoritative but still useful

- `audit/remediation/runs/wave-2b/candidate-2cdbfec-implementation.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md`
- `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
- `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`
- `SESSION-LOG.md` -- historical trail
- `audit/remediation/WAVE-3-3B-PREWORK.md`
- `audit/remediation/WAVE-4-4B-PREWORK.md`
- `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
