# Current State
*Last updated: 2026-04-11 | Updated by: post-Wave-2A final-clearance reconciliation pass*

---

## Live status

- **Wave 1:** Complete.
- **Wave 2A:** Cleared and checkpointed in commit `16e0bc7` (`Wave 2A: fix final hash and corroboration leakage`).
- **Wave 2B:** Next implementation wave. Wave 2A's final deep review gate is now closed.
- **Round-3 overlay:** The content-audit planning overlay is accepted for Wave 2B and later. It does **not** reopen Waves 1A through 2A.

## What just happened

1. Wave 2A's initial checkpoint candidate `badba75` turned out to be incomplete. Successive deep reviews surfaced additional render-side provenance leaks and one DOI-dedup hash bug.
2. Narrow Wave 2A blocker-fix commits landed in sequence: `d6c24c7`, `bc80475`, `676be93`, and finally `16e0bc7`.
3. The final deep review of `33695a7..16e0bc7` returned `WAVE 2A CLEARED`.
4. This pass reconciles the control-plane docs so Wave 2B starts from the real cleared Wave 2A baseline.

## What happens next

1. Treat the updated docs below as authoritative.
2. Start Wave 2B using `audit/remediation/WAVE-2B-SETUP.md` plus `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`.
3. Run adversarial review on the Wave 2B diff and clear blockers before opening Wave 3.
4. Continue through the reconciled post-2B plan: Wave 3, Wave 3B, Wave 4, Wave 4B, then Wave 5.

## Reconciled wave plan

| Wave | Status | Scope |
|------|--------|-------|
| Wave 1 (1A + 1B + 1C) | **Complete** | Lifecycle isolation, parsing standard, citation-identity foundation |
| Wave 2A | **Complete** (`16e0bc7`) | Citation identity completion and provenance gating |
| Wave 2B | **Next** | Enforcement model plus `E-1`, `E-9`, `E-10`, `E-6`, `E-7` |
| Wave 3 | Planned | Completeness work plus dual-axis taxonomy and related profile/template routing |
| Wave 3B | Planned | Thin Pipeline-L2 plus minimum viable live iterative loop |
| Wave 4 | Planned | Polish plus content-layer research/design work |
| Wave 4B | Planned | Implementation of Wave 4 content designs |
| Wave 5 | Planned | Calibration against real outputs |

## Accepted 2B+ overlay

- **D-1:** Dual-axis taxonomy is in scope and stays in the plan. It lands in Wave 3, not as a narrowed substitute architecture.
- **D-8:** Pipeline-L2 remains Phase 1 scope as a thin real layer, not a stub. It lands in Wave 3B.
- **D-9:** Iterative research remains Phase 1 scope as a minimum viable live loop. It lands in Wave 3B.
- **D-2:** Phase 1 output is **decision-informing analysis**, not stakeholder-specific recommendation framing.
- **Calibration sequencing:** all calibration-policy changes remain deferred to Wave 5 except `E-1` (geometric-mean epsilon fix), which belongs in Wave 2B.
- **Profile weights:** M&A and Restructuring profile weights are provisional until Wave 5 calibration against real scored outputs.

## Known active gaps

| Gap | Next wave |
|-----|-----------|
| Enforcement model still mostly advisory | 2B |
| `SprintContractGenerator` / profile routing / rubric field consumption not fully wired (`E-9`, `E-10`, `E-6`, `E-7`) | 2B |
| Dual-axis taxonomy and domain-aware template/profile routing not built | 3 |
| Thin Pipeline-L2 not built | 3B |
| Minimum viable live iterative loop not built | 3B |
| Actionability/content-layer alignment still reflects pre-D-2 assumptions | 4 |
| Calibration unresolved beyond the epsilon bug | 5 |

## Residual non-blocking Wave 2A follow-ups

- Render-time `corroboration_count` is now leak-free, but it may underreport legitimate multi-pass corroboration in shared-source cases. Treat this as a later design follow-up, not a Wave 2A blocker.
- `PostSynthesisVerifierContract` in `src/keystone/contracts.py` still differs from the v2.1 governing-doc seam. Reconcile that before the real verifier implementation lands.

## Authoritative docs for the next session

- `audit/remediation/WORKSTREAM-STATUS.md` -- stream separation and orientation
- `CURRENT-STATE.md` -- live status and next-wave summary
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` -- binding implementation design and reconciled wave order
- `audit/remediation/BUILD-PROCESS.md` -- build discipline and checkpoint process
- `audit/remediation/WAVE-2B-SETUP.md` -- authoritative Wave 2B execution doc
- `SESSION-LOG.md` -- use Sessions 19-22 for recent remediation rationale and checkpoints
