# Active Handoff

## Current Truth

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B is cleared at `2cdbfec`.
- Wave 3A seam-freeze artifact lands in `65074ca`, but the first coherent live promotion into `wave-3 / setup` is `198ab92`.
- Wave 3 is cleared at `4819527`.
- Wave 3B is cleared at `5cc9585`.
- Wave 4 is cleared at `6406e46`.
- Wave 4B is now cleared at `65a612d`.
- `91f97c2` remains the last cleared-state docs checkpoint.
- `2e6d780` is the pre-planning retro handoff anchor.
- `8bb00ab0298babd50d24fa3c07afae2ae7172ff6` (`8bb00ab`) is the exact cleared setup-package docs snapshot the earlier Lane D setup-promotion reconcile started from.
- `48293d262714c59ee9d45b6f01213b887fade48d` (`48293d2`) is the exact authority-decision-pending control-plane snapshot this reconcile started from.
- `RETROSPECTIVE-LINEAGE-MANIFEST.yaml` is now controller-promoted as the authoritative retrospective lineage layer for docs checkpoints `35a8a29` through `2e6d780`.
- `RETROSPECTIVE-REVIEW-LEDGER.yaml` is now controller-promoted as the authoritative current review-status layer for retrospective audit prerequisites.
- Batch 1 is durably `CLEARED` there for `CP-1`, `CP-2`, and `RP-1`.
- The Wave clearances above remain historical original remediation clearances for the live implementation lane; they are not retrospective review authority by themselves.
- `W2B-1`, `W3A-1`, `W3-1`, `W3B-1`, `W4D-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1` are now `CLEARED` in the authoritative retrospective review ledger.
- `X-1` is now current `CLEARED` in that ledger.
- The retrospective audit program is now complete under the authoritative review ledger.
- Those retrospective `CLEARED` statuses remain prerequisite proof only. They do not, by themselves, authorize a forward lane.
- The main workspace remains controller/docs only.
- `WAVE-4B-SETUP.md` remains the frozen boundary for what Wave 4B was allowed to change.
- All required Wave 4B review packets now exist in the main workspace.
- The clean Wave 4B implementation lane stayed inside the approved content slices and did not reopen deferred capability work.
- `NEXT-WAVE-SETUP-ARTIFACT.md` plus the cleared gate artifacts remain the historical setup authority candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` was reviewed against.
- Candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` from branch `codex/retrieval-mvp-fetch` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch` is now frozen as `BLOCKED` superseded reference material.
- That superseded blocked candidate carries two separate historical blocker classes: a `document_fetch` authority / scope conflict first, and an EDGAR venue / access blocker second.
- Retrieval MVP Lane D may not continue coding from the current worktree or candidate.
- The current forward authorization is now `Lane H - Retrieval Tool-Surface Authority Expansion`.
- The promoted Lane H setup is pinned to baseline `65a612d`, branch `codex/retrieval-tool-surface`, worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`, and the exact approved write set in `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`.
- Article/PDF canonical-fetch authority is now promoted separately from the later SEC venue review.
- Lane H may now launch from the promoted setup state.
- Parser Lane E, L1 integration Lane F, UI work, benchmark acceptance claims, Wave 5, and calibration remain blocked.
- The controller is expected to continue **autonomously across checkpoints**. This promotion changes the live forward-lane authority while preserving the distinction between retrospective completion, the blocked Lane D candidate, the promoted Lane H setup state, and the later SEC venue review.

## Authoritative Order

Any summary doc or retrospective planning doc that offers a shortcut list must defer to this order.
Item 3 is the authoritative lineage layer for retrospective checkpoint-chain questions. Item 4 is the authoritative current review-status layer for retrospective audit prerequisites. Items 5-11 are the promoted Lane H authority stack. Items 12-15 preserve the blocked Lane D candidate state as superseded reference material. Items 16-18 are the historical setup-boundary docs the blocked candidate was reviewed against.

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [RETROSPECTIVE-LINEAGE-MANIFEST.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml)
4. [RETROSPECTIVE-REVIEW-LEDGER.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml)
5. [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md)
6. [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md)
7. [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md)
8. [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
9. [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md)
10. [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md)
11. [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md)
12. [LANE-D-AUTHORITY-RESOLUTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md)
13. [NEXT-CONTROLLER-ACTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md)
14. [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md)
15. [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md)
16. [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md)
17. [NEXT-WAVE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md)
18. [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md)
19. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
20. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)
21. [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
22. [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md)
23. `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` outputs as retrospective sidecars only unless a later controller reconcile promotes them.

## Active State Tuple

- `active_wave`: `retrieval-tool-surface`
- `active_state`: `setup`
- `execution_baseline_commit`: `65a612d`
- `review_target_commit`: `not yet created; Lane H roots from 65a612d`
- `docs_reconcile_commit`: `48293d262714c59ee9d45b6f01213b887fade48d`
- `next_recovery_checkout`: `65a612d`
- `implementation_lane`: `Lane H - Retrieval Tool-Surface Authority Expansion`
- `implementation_branch`: `codex/retrieval-tool-surface`
- `implementation_worktree`: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
- `approved_write_set`: [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
- `superseded_blocked_reference`: `f1af7dfafa2e66b831810d70006ab8295411c61b` (`BLOCKED`; historical Lane D reference only)
- `sec_venue_review`: `deferred separate later step`

Interpret `docs_reconcile_commit` as the exact docs snapshot this controller reconcile started from. It is not symbolic `HEAD`; future controller docs checkpoints must repin it explicitly.

## Open Blockers

- No remaining blocker prevents opening Lane H from the promoted setup state.
- Candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` remains frozen as blocked, superseded reference material and may not be patched forward or reopened as Retrieval MVP Lane D coding.
- SEC / EDGAR venue review remains deferred as a later separate step after Lane H implements and proves the promoted article/PDF authority contract.
- Still blocked: parser Lane E, L1 integration Lane F, UI work, benchmark acceptance claims, Wave 5, calibration, and any write-set expansion beyond [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md).

## Latest Review Packets

- [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md)
- [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md)
- [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md)
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
- [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md)
- [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md)
- [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md)
- [LANE-D-AUTHORITY-RESOLUTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md)
- [NEXT-CONTROLLER-ACTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md)
- [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md)
- [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md)
- [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md)

## Retrospective Review Status

- Current authoritative prerequisite layer: [RETROSPECTIVE-REVIEW-LEDGER.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml)
- Batch 1 currently `CLEARED` there: `CP-1`, `CP-2`, `RP-1`
- `W2B-1`, `W3A-1`, `W3-1`, `W3B-1`, `W4D-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1` are currently `CLEARED`.
- The retrospective audit program is complete under the current authoritative review ledger.
- The ledger records current review authority only. It does not rewrite the historical original remediation clearances listed above or claim that the historical snapshot under review already contained later review sidecars.
- The retrospective audit completion remains prerequisite proof only. It does not authorize the frozen `f1af7df` reference candidate, reopen Retrieval MVP Lane D, or replace the promoted Lane H setup authority.

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Treat `65a612d` as the last cleared code commit and start any Lane H runtime work from that baseline only.
3. Treat `f1af7dfafa2e66b831810d70006ab8295411c61b` as a frozen `BLOCKED` Lane D reference candidate only; do **not** patch it forward or reopen Lane D coding.
4. Treat the promoted retrieval-tool-surface package as the live forward authority stack for Lane H.
5. Keep the main workspace docs-only.
6. In the next runtime session, open `codex/retrieval-tool-surface` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` and implement only the exact write set in [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md).
7. Keep article/PDF canonical-fetch authority separate from the later SEC / EDGAR venue review.
8. Only after a Lane H candidate exists under the promoted contract may a separate SEC venue review be considered.
9. Do **not** start parser Lane E, L1 integration Lane F, UI work, benchmark acceptance, Wave 5, or calibration.

## Exact Recovery Command

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
sed -n '1,240p' audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml
sed -n '1,360p' audit/remediation/control-plane/ACTIVE-HANDOFF.md
sed -n '1,240p' audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml
sed -n '1,240p' audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md
sed -n '1,240p' audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md
sed -n '1,260p' audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md
sed -n '1,240p' audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md
sed -n '1,240p' audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md
sed -n '1,220p' audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md
sed -n '1,260p' audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md
sed -n '1,220p' audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md
sed -n '1,260p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md
sed -n '1,220p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md
sed -n '1,260p' audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md
```

## Allowed Write Set

### Active docs-only controller scope

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

### Promoted Lane H authority package

- `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
- `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
- `audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md`
- `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`

### Lane H implementation lane

- The exact write-set authority is [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md).
- The approved runtime surface is only the path set named there, rooted from baseline `65a612d` on branch `codex/retrieval-tool-surface` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Do **not** reopen Retrieval MVP Lane D or patch `f1af7dfafa2e66b831810d70006ab8295411c61b` forward under the historical `next-wave-setup` package.

### Superseded Lane D reference package

- [NEXT-WAVE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md) and [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md) remain historical review-boundary evidence for the frozen `f1af7dfafa2e66b831810d70006ab8295411c61b` candidate only.
- They are not current live coding authority.

### Retrospective sidecars

- `audit/remediation/workstream-retro/`
- `audit/remediation/workstream-retro/reviews/`

Write here only for retrospective audit planning, docs/package reconciliation, or review-sidecar output. These paths do not outrank the live control plane unless a later controller reconcile promotes them.

## Required Test Matrix

Before any Lane H candidate may clear, run at minimum:

1. `tests/unit/gateway/test_auth.py`
2. `tests/unit/gateway/test_gateway.py`
3. `tests/unit/gateway/test_tool_registry.py`
4. `tests/unit/specification/test_task_generator.py`
5. `tests/unit/test_auth.py`
6. `tests/unit/test_audit_log.py`
7. `tests/unit/test_gateway.py`
8. `tests/unit/test_research_models.py`
9. `tests/unit/test_tool_registry.py`

If `src/keystone/models/research.py` changes, add targeted model coverage for the new DTOs.

## Required Review Packet

Before any Lane H candidate may clear, the review packet under `audit/remediation/runs/retrieval-tool-surface/` must include at minimum:

- `candidate-<sha>-implementation.md`
- `candidate-<sha>-file-manifest.md`
- `candidate-<sha>-backend-truth-matrix.md`
- `candidate-<sha>-tool-contract-review.md`
- `candidate-<sha>-live-fetch-review.md`
- `candidate-<sha>-adversarial-review.md`
- `candidate-<sha>-second-opinion.md`
- `candidate-<sha>-review-synthesis.md`
- `candidate-<sha>-blocked-or-cleared-checkpoint.md`
- `live-probe-results.json`

Lane H clears only if all of the following are explicit:

- article and PDF fetch have real governed proof
- `document_fetch` never leaks into task assignment surfaces
- SEC remains explicitly unclaimed or separately classified
- no reviewer has to infer the assignable versus system-owned distinction from scattered files

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md) — promoted Lane H handoff and boundary statement
- [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md) — promoted authority decision for the system-owned `document_fetch` contract shape
- [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md) — active Lane H setup authority
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md) — exact approved write set and denylist for Lane H
- [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md) — canonical tool-definition contract shape Lane H must implement
- [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md) — promotion preconditions and post-promotion rule set
- [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md) — docs-only promotion verdict clearing Lane H for live control-plane adoption
- [LANE-D-AUTHORITY-RESOLUTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md) — historical Lane D ruling that froze `f1af7df`
- [NEXT-CONTROLLER-ACTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md) — historical bridge from the blocked Lane D state into the Lane H package
- [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md) — frozen blocked-candidate synthesis for reference only
- [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md) — immutable blocked-state checkpoint for the superseded Lane D candidate
- [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md) — immutable cleared-state proof for the runtime baseline any later retrieval lane must still root from
- [NEXT-WAVE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md) — historical Lane D setup boundary the blocked candidate was reviewed against
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md) — historical Lane D write-set boundary the blocked candidate was reviewed against

## Retrospective Audit Anchors

- Treat `91f97c2` as the last cleared-state docs checkpoint.
- Treat `2e6d780` as the first retro-planning handoff anchor, not as literal current `HEAD`.
- Treat `48293d262714c59ee9d45b6f01213b887fade48d` (`48293d2`) as the exact authority-decision-pending control-plane snapshot this Lane H promotion reconcile started from.
- Treat `66f6178c1d710effe44cb5c278c5c729d5bcc216` (`66f6178`) as the earlier blocked-candidate control-plane snapshot, not as the current docs-reconcile pin.
- Treat `8bb00ab0298babd50d24fa3c07afae2ae7172ff6` (`8bb00ab`) as the earlier Lane D setup-promotion snapshot, not as the current docs-reconcile pin.
- Treat `c5dbd055d1b9d67c0d40a46f18b6b3a7f2b46468` (`c5dbd05`) as the earlier Batch 1 planning-package docs snapshot, not as the current docs-reconcile pin.
- Treat `RETROSPECTIVE-LINEAGE-MANIFEST.yaml` as the authoritative retrospective lineage layer for docs checkpoints `35a8a29` through `2e6d780`.
- Treat `RETROSPECTIVE-REVIEW-LEDGER.yaml` as the authoritative current review-status layer for retrospective audit prerequisites.
- Treat the manifest's exact git-derived pins as the replacement for the historical symbolic `HEAD` defect during retrospective audit use.
- Treat `65074ca` as the real seam-freeze artifact landing, but use `198ab92` as the first coherent live promotion of that artifact into active `wave-3 / setup`.
- The manifest repairs retrospective audit use of the older symbolic-`HEAD` defect without rewriting the historical checkpoint text itself.

## Residual Follow-Ups

- `W2B-R01`: parse-invalid sprint-contract JSON now fails explicitly, but parseable under-specified JSON can still return empty Wave 2B enforcement fields.

## Controller Lease Events

- `2026-04-12T02:01:57-04:00` — controller takeover by `codex-gpt-5.4-xhigh-main-controller`.
  Reason: `lease_heartbeat_at` from the predecessor was older than 30 minutes (`2026-04-12T01:24:01-04:00`), so the takeover rule in the control plane fired before any new state mutation.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `wave-2b` / `cleared`, `last_cleared_code_commit` was still `2cdbfec`, and `WAVE-3A-SEAM-FREEZE.md` was still absent.
- `2026-04-12T02:05:36-04:00` — seam-freeze artifact commit `65074ca` landed.
  Result: `WAVE-3A-SEAM-FREEZE.md` was committed, but the same commit still left the live control-plane text stale and still said to create that doc. Treat `65074ca` as the real seam-freeze artifact landing, not as a self-contained live-state transition.
- `2026-04-12T02:10:00-04:00` — controller reconcile commit `198ab92` promoted the seam freeze into active Wave 3 setup.
  Result: `WAVE-3-SETUP.md` became the active wave setup doc, `active_wave` advanced to `wave-3`, and the next action became opening the clean Wave 3 implementation lane from `2cdbfec`.
- `2026-04-12T02:31:29-04:00` — Wave 3 candidate `4819527` was reviewed and cleared.
  Result: Wave 3 advanced from `setup` to `cleared`, `4819527` became the last cleared code commit, and the next required gate became `WAVE-3B-SETUP.md`.
- `2026-04-12T02:50:02-04:00` — Wave 3B setup checkpoint was committed.
  Result: `WAVE-3B-SETUP.md` became the active setup doc, `active_wave` advanced to `wave-3b`, and the next action became opening the clean Wave 3B implementation lane from `4819527`.
- `2026-04-12T03:22:30-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller`.
  Reason: the previous lease heartbeat (`2026-04-12T02:50:02-04:00`) aged past the 30-minute limit before the next state mutation, so `controller_epoch` was incremented before reconciling Wave 3B clearance into Wave 4 setup.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, the clean Wave 3B code lane had already produced cleared candidate `5cc9585`, the Wave 3B review packet set existed on disk, and the dirty main workspace still required controller/docs-only quarantine.
- `2026-04-12T03:43:19-04:00` — Wave 4 docs checkpoint added sprint-contract / rubric research.
  Result: `WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md` now records the `C-5` and `C-7` contracts, keeps persisted contradiction-taxonomy expansion out of Wave 4B, and advances the next required memo to `WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`.
- `2026-04-12T03:50:29-04:00` — Wave 4 docs checkpoint added template / routing research.
  Result: `WAVE-4-TEMPLATE-ROUTING-RESEARCH.md` now records the `C-6`, `C-8`, `C-10`, and `C-14` contracts, keeps dual-axis tiebreaking plus dynamic lens selection out of Wave 4B, and advances the next required memo to `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`.
- `2026-04-12T03:55:07-04:00` — Wave 4 docs checkpoint added evaluator-verification research.
  Result: `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md` now records the `C-11` and `C-15` boundary, the required Wave 4 memo set is complete, and the next required action becomes opening the clean Wave 4 polish lane from `5cc9585`.
- `2026-04-12T04:07:21-04:00` — Wave 4 candidate `6406e46` was reviewed and cleared.
  Result: Wave 4 advanced from `setup` to `cleared`, `6406e46` became the last cleared code commit, and the next required gate became `WAVE-4B-SETUP.md`.
- `2026-04-12T04:14:49-04:00` — Wave 4B setup checkpoint was committed.
  Result: `WAVE-4B-SETUP.md` became the active setup doc, `active_wave` advanced to `wave-4b`, and the next action became opening the clean Wave 4B implementation lane from `6406e46`.
- `2026-04-12T04:35:17-04:00` — Wave 4B candidate `65a612d` was reviewed and cleared.
  Result: Wave 4B advanced from `setup` to `cleared`, `65a612d` became the last cleared code commit, and a hard stop activated because no next-wave authority artifact is yet committed.
- `2026-04-12T13:33:33-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for Batch 1 docs/package reconciliation.
  Reason: the previous lease heartbeat (`2026-04-12T04:35:17-04:00`) had aged out long before the next authority mutation, so `controller_epoch` was incremented before repinning docs-commit semantics and normalizing the retrospective packet sidecars.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `wave-4b` / `cleared`, `last_cleared_code_commit` was still `65a612d`, the retro planning-package lineage already extended through `c5dbd055d1b9d67c0d40a46f18b6b3a7f2b46468` (`c5dbd05`), and the remaining work was docs-only reconciliation rather than runtime implementation.
- `2026-04-12T22:46:41-04:00` — Wave 3B fix review-and-promotion reconcile recorded `W3B-1` as current `CLEARED`.
  Result: authoritative fix snapshot `8dd97be` cleared both independent fix reviews and the rerun `W3B-1` sidecar, `RETROSPECTIVE-REVIEW-LEDGER.yaml` now records `W3B-1` as current `CLEARED`, and `W4-1` may now launch from the current retrospective review ledger while the forward Wave 5 / new-capability hard stop remains in place.
- `2026-04-13T11:06:14-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for retrospective `W4-1` reconcile.
  Reason: the previous lease heartbeat (`2026-04-12T22:46:41-04:00`) had aged out long before the next authority mutation, so `controller_epoch` was incremented before promoting the next retrospective review status.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `wave-4b` / `cleared`, `last_cleared_code_commit` was still `65a612d`, the `W4-1` review sidecar was present under `audit/remediation/workstream-retro/reviews/`, and the remaining work stayed inside the controller-authorized docs-only write set.
- `2026-04-13T11:06:14-04:00` — Wave 4 review-and-promotion reconcile recorded `W4-1` as current `CONTINGENT`.
  Result: historical Wave 4 runtime clearance at `6406e46` remains the original remediation-lane clearance, but the authoritative retrospective review ledger now records `W4-1` as current `CONTINGENT`, making `W4-1` the current retrospective stop sign and preventing `W4B-1`, `W4B-2`, and `X-1` from launching from the current review ledger.
- `2026-04-13T11:50:01-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for retrospective `W4-1` fix-rerun promotion.
  Reason: the previous lease heartbeat (`2026-04-13T11:06:14-04:00`) had aged past the 30-minute limit before the next authority mutation, so `controller_epoch` was incremented before promoting the repaired `W4-1` status.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `wave-4b` / `cleared`, `last_cleared_code_commit` was still `65a612d`, the `W4 E-4` fix-review sidecars and repaired `W4-1` rerun sidecar were present under the controller-authorized sidecar roots, and the remaining work stayed inside the docs-only write set.
- `2026-04-13T11:50:01-04:00` — Wave 4 fix review-and-promotion reconcile recorded `W4-1` as current `CLEARED`.
  Result: authoritative fix snapshot `1046585` cleared both independent `W4 E-4` fix reviews and the rerun `W4-1` sidecar, `RETROSPECTIVE-REVIEW-LEDGER.yaml` now records `W4-1` as current `CLEARED`, and `W4B-1` may now launch from the current retrospective review ledger while the forward Wave 5 / new-capability hard stop remains in place.
- `2026-04-13T12:04:35-04:00` — Wave 4B memo-conformity review-and-promotion reconcile recorded `W4B-1` as current `CLEARED`.
  Result: historical Wave 4B remediation clearance at `65a612d` remains the original implementation-lane clearance, while the authoritative retrospective review ledger now records `W4B-1` as current `CLEARED`; `W4B-2` may now launch from the current retrospective review ledger, and `X-1` remains gated until `W4B-2` is current `CLEARED`.
- `2026-04-13T12:24:08-04:00` — Wave 4B runtime review-and-promotion reconcile recorded `W4B-2` as current `BLOCKED`.
  Result: historical Wave 4B remediation clearance at `65a612d` remains the original implementation-lane clearance, `W4B-1` remains current `CLEARED` as the separate memo-conformity authority, and the authoritative retrospective review ledger now records `W4B-2` as current `BLOCKED`; `W4B-2` becomes the current retrospective stop sign and `X-1` may not launch until a later controller reconcile promotes `W4B-2` to current `CLEARED`.
- `2026-04-13T12:45:11-04:00` — Wave 4B fix review-and-promotion reconcile recorded `W4B-2` as current `CLEARED`.
  Result: historical Wave 4B remediation clearance at `65a612d` remains the original implementation-lane clearance, `W4B-1` remains current `CLEARED` as the separate memo-conformity authority, authoritative fix snapshot `4d8f647` cleared both independent `W4B C-15` fix reviews and the rerun `W4B-2` sidecar, and `X-1` may now launch from the current retrospective review ledger while the forward Wave 5 / new-capability hard stop remains in place.
- `2026-04-13T13:13:30-04:00` — Cross-wave synthesis reconcile recorded `X-1` as current `CLEARED`.
  Result: historical Wave 2A through Wave 4B clearances remain the original remediation-lane clearances, the authoritative retrospective review ledger now records `X-1` as current `CLEARED`, the retrospective audit program is complete under that current review authority layer, and the forward Wave 5 / new-capability hard stop remains in place until a controller-approved next-wave setup artifact is committed.
- `2026-04-13T14:58:17-04:00` — cleared setup-package commit `8bb00ab` landed.
  Result: the corrected `audit/remediation/next-wave-setup/` package was committed with the required docs-only gate artifacts on disk, but the live control plane still remained on the old missing-artifact hard stop until a later controller reconcile promoted that package.
- `2026-04-13T15:16:20-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for Retrieval MVP Lane D setup promotion.
  Reason: the previous lease heartbeat (`2026-04-13T13:13:30-04:00`) had aged past the 30-minute limit before the next authority mutation, so `controller_epoch` was incremented before promoting the next-wave setup state.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `HEAD` was the cleared setup-package commit `8bb00ab`, `active_wave`/`active_state` still reconciled to `wave-4b` / `cleared`, `last_cleared_code_commit` was still `65a612d`, and all five required next-wave gate artifacts plus `NEXT-WAVE-SETUP-ARTIFACT.md` were present on disk and `CLEARED` for the reviewed snapshot.
- `2026-04-13T15:16:20-04:00` — Retrieval MVP Lane D setup promotion reconcile replaced the missing-artifact hard stop with live fetch-lane setup authority.
  Result: the live control plane advanced from `wave-4b / cleared` hard-stop state to `retrieval-mvp-fetch / setup`, pinned the forward lane to baseline `65a612d`, branch `codex/retrieval-mvp-fetch`, worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`, and the exact approved write set in `ALLOWED-WRITE-SET.md`, while preserving retrospective audit completion as prerequisite proof only rather than forward-lane authority by itself.
- `2026-04-13T19:55:07-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for Retrieval MVP Lane D blocked-state reconcile.
  Reason: the previous lease heartbeat (`2026-04-13T15:16:20-04:00`) had aged past the 30-minute limit before the next authority mutation, so `controller_epoch` was incremented before reconciling the blocked candidate into the live control plane.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `retrieval-mvp-fetch` / `setup`, `last_cleared_code_commit` was still `65a612d`, the blocked-candidate review synthesis plus blocked checkpoint were present in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`, and the remaining work was docs-only controller reconcile rather than runtime implementation.
- `2026-04-13T19:55:07-04:00` — Retrieval MVP Lane D blocked-state reconcile froze the fetch lane and promoted the docs-only authority-expansion decision as the next controller priority.
  Result: the live control plane advanced from `retrieval-mvp-fetch / setup` to `retrieval-mvp-authority-expansion / setup`, recorded candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` as `BLOCKED`, withdrew authorization for more coding in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`, and set the next controller-priority workstream to a docs-only article/PDF canonical-fetch authority decision while preserving retrospective audit completion as prerequisite proof only and keeping `65a612d` as the last cleared code commit.
- `2026-04-13T20:28:07-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller` for Lane H promotion reconcile.
  Reason: the previous lease heartbeat (`2026-04-13T19:55:07-04:00`) had aged past the 30-minute limit before the next authority mutation, so `controller_epoch` was incremented before promoting Lane H setup into the live control plane.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `retrieval-mvp-authority-expansion` / `setup`, `last_cleared_code_commit` was still `65a612d`, the retrieval-tool-surface package plus its promotion decision were present on disk, and the remaining work stayed inside the docs-only controller reconcile scope.
- `2026-04-13T20:28:07-04:00` — Lane H promotion reconcile replaced the authority-decision-pending state with live Retrieval Tool-Surface setup authority.
  Result: the live control plane advanced from `retrieval-mvp-authority-expansion / setup` to `retrieval-tool-surface / setup`, pinned the forward lane to exact Lane H authority docs, baseline `65a612d`, branch `codex/retrieval-tool-surface`, worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`, and the approved write set in `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`; froze `f1af7dfafa2e66b831810d70006ab8295411c61b` as superseded blocked reference material, preserved retrospective audit completion as prerequisite proof only, and kept SEC venue review as a later separate step.
