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
- `48293d262714c59ee9d45b6f01213b887fade48d` (`48293d2`) is the exact authority-decision-pending control-plane snapshot the Lane H setup-promotion reconcile started from.
- `725a223e56dc5fd86fc135bd4bae940aed71db12` (`725a223`) is the exact docs snapshot this Lane H cleared-state reconcile started from.
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
- Candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` from branch `codex/retrieval-mvp-fetch` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch` remains frozen as `BLOCKED` superseded reference material.
- That superseded blocked candidate carries two separate historical blocker classes: a `document_fetch` authority / scope conflict first, and an EDGAR venue / access blocker second.
- Retrieval MVP Lane D may not continue coding from the current worktree or candidate.
- Lane H candidate `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` from branch `codex/retrieval-tool-surface` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` is now `CLEARED`.
- `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` is now the current runtime truth for governed article/PDF canonical fetch.
- Article/PDF canonical-fetch authority and implementation are now cleared separately from the later SEC venue review.
- No retrieval code lane is currently authorized to continue from the main control plane.
- The next controller-priority workstream is a docs-only `Professor-Demo Narrow Lane E Setup` rooted from cleared Lane H commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`.
- Parser Lane E, L1 integration Lane F, UI work, benchmark acceptance claims, Wave 5, and calibration remain blocked until later controller promotion.
- The controller is expected to continue **autonomously across checkpoints**. This reconcile advances live forward truth from Lane H setup to Lane H cleared state while preserving the distinction between retrospective completion, the blocked Lane D candidate, the cleared Lane H runtime, and the later SEC venue review.

## Authoritative Order

Any summary doc or retrospective planning doc that offers a shortcut list must defer to this order.
Item 3 is the authoritative lineage layer for retrospective checkpoint-chain questions. Item 4 is the authoritative current review-status layer for retrospective audit prerequisites. Items 5-11 are the promoted Lane H authority stack. Items 12-20 are the cleared Lane H candidate packet. Items 21-24 preserve the blocked Lane D candidate state as superseded reference material. Items 25-26 are the historical setup-boundary docs the blocked candidate was reviewed against.

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
12. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-implementation.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-implementation.md)
13. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-file-manifest.md)
14. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-backend-truth-matrix.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-backend-truth-matrix.md)
15. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-tool-contract-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-tool-contract-review.md)
16. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-live-fetch-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-live-fetch-review.md)
17. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-adversarial-review.md)
18. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-second-opinion.md)
19. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md)
20. [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md)
21. [LANE-D-AUTHORITY-RESOLUTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md)
22. [NEXT-CONTROLLER-ACTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md)
23. [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md)
24. [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md)
25. [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md)
26. [NEXT-WAVE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md)
27. [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md)
28. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
29. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)
30. [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
31. [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md)
32. `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` outputs as retrospective sidecars only unless a later controller reconcile promotes them.

## Active State Tuple

- `active_wave`: `retrieval-tool-surface`
- `active_state`: `cleared`
- `execution_baseline_commit`: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- `review_target_commit`: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- `docs_reconcile_commit`: `725a223e56dc5fd86fc135bd4bae940aed71db12`
- `next_recovery_checkout`: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- `cleared_runtime_worktree`: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
- `implementation_lane`: `Lane H - Retrieval Tool-Surface Authority Expansion (cleared at 93a5ca8)`
- `next_setup_workstream`: `Professor-Demo Narrow Lane E Setup`
- `approved_write_set`: [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
- `superseded_blocked_reference`: `f1af7dfafa2e66b831810d70006ab8295411c61b` (`BLOCKED`; historical Lane D reference only)
- `sec_venue_review`: `deferred separate later step`

Interpret `docs_reconcile_commit` as the exact docs snapshot this controller reconcile started from. It is not symbolic `HEAD`; future controller docs checkpoints must repin it explicitly.

## Open Blockers

- No remaining blocker prevents using `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` as the cleared runtime truth for governed article/PDF fetch.
- No retrieval code lane is currently authorized beyond the cleared Lane H state because the next milestone is still a docs-only narrow Lane E setup package.
- Candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` remains frozen as blocked, superseded reference material and may not be patched forward or reopened as Retrieval MVP Lane D coding.
- SEC / EDGAR venue review remains deferred as a later separate step after the article/PDF path is integrated further.
- Still blocked: parser Lane E code, L1 integration Lane F, UI work, benchmark acceptance claims, Wave 5, calibration, and any write-set expansion beyond later controller-approved setup packages.

## Latest Review Packets

- [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md)
- [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md)
- [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md)
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
- [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md)
- [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md)
- [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-implementation.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-implementation.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-file-manifest.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-backend-truth-matrix.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-backend-truth-matrix.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-tool-contract-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-tool-contract-review.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-live-fetch-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-live-fetch-review.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-adversarial-review.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-second-opinion.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md)
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md)
- [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md)
- [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md)
- [MVP-REQUIRED-BUILDOUT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md)

## Retrospective Review Status

- Current authoritative prerequisite layer: [RETROSPECTIVE-REVIEW-LEDGER.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml)
- Batch 1 currently `CLEARED` there: `CP-1`, `CP-2`, `RP-1`
- `W2B-1`, `W3A-1`, `W3-1`, `W3B-1`, `W4D-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1` are currently `CLEARED`.
- The retrospective audit program is complete under the current authoritative review ledger.
- The ledger records current review authority only. It does not rewrite the historical original remediation clearances listed above or claim that the historical snapshot under review already contained later review sidecars.
- The retrospective audit completion remains prerequisite proof only. It does not authorize the frozen `f1af7df` reference candidate, reopen Retrieval MVP Lane D, or replace the cleared Lane H runtime truth.

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Treat `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` as the last cleared code commit and current runtime truth anchor.
3. Treat Lane H as cleared runtime truth; do **not** reopen Lane H coding unless a later controller action explicitly says so.
4. Treat `f1af7dfafa2e66b831810d70006ab8295411c61b` as superseded blocked reference material only; do **not** patch it forward or reopen Lane D coding.
5. Keep the main workspace docs-only.
6. In the next controller session, create a docs-only narrow Lane E setup package for deterministic parse and evidence normalization rooted from `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`.
7. Keep SEC / EDGAR venue review separate and later.
8. Do **not** start parser Lane E coding, L1 integration Lane F, UI work, benchmark acceptance, Wave 5, or calibration until a later control-plane promotion authorizes them.

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
sed -n '1,260p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md
sed -n '1,220p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md
sed -n '1,260p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md
sed -n '1,220p' /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md
sed -n '1,260p' audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md
```

## Allowed Write Set

### Active docs-only controller scope

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

Until a later controller session creates and promotes the next setup package, the live main-workspace write set remains these control-plane files only.

### Historical Lane H authority package

- `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
- `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
- `audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md`
- `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`

These remain the authority stack the cleared Lane H candidate was reviewed against. They are not current permission for additional code changes by themselves.

### Cleared Lane H runtime line

- The current runtime truth is the cleared Lane H worktree at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- The cleared runtime snapshot is `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`.
- No further coding is currently authorized there until a later control-plane action says so.

### Superseded Lane D reference package

- [NEXT-WAVE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md) and [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md) remain historical review-boundary evidence for the frozen `f1af7dfafa2e66b831810d70006ab8295411c61b` candidate only.
- They are not current live coding authority.

### Retrospective sidecars

- `audit/remediation/workstream-retro/`
- `audit/remediation/workstream-retro/reviews/`

Write here only for retrospective audit planning, docs/package reconciliation, or review-sidecar output. These paths do not outrank the live control plane unless a later controller reconcile promotes them.

## Cleared Lane H Historical Test Matrix

The cleared Lane H candidate was reviewed against this minimum matrix:

1. `tests/unit/gateway/test_auth.py`
2. `tests/unit/gateway/test_gateway.py`
3. `tests/unit/gateway/test_tool_registry.py`
4. `tests/unit/specification/test_task_generator.py`
5. `tests/unit/test_auth.py`
6. `tests/unit/test_audit_log.py`
7. `tests/unit/test_gateway.py`
8. `tests/unit/test_research_models.py`
9. `tests/unit/test_tool_registry.py`

No new code-lane test matrix is active yet because the next milestone is a docs-only Lane E setup package.

## Cleared Lane H Historical Review Packet

The cleared Lane H review packet under `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/` includes:

- `candidate-93a5ca8-implementation.md`
- `candidate-93a5ca8-file-manifest.md`
- `candidate-93a5ca8-backend-truth-matrix.md`
- `candidate-93a5ca8-tool-contract-review.md`
- `candidate-93a5ca8-live-fetch-review.md`
- `candidate-93a5ca8-adversarial-review.md`
- `candidate-93a5ca8-second-opinion.md`
- `candidate-93a5ca8-review-synthesis.md`
- `candidate-93a5ca8-blocked-or-cleared-checkpoint.md`
- `live-probe-results.json`

Lane H cleared because all of the following were explicit:

- article and PDF fetch had real governed proof
- `document_fetch` never leaked into task assignment surfaces
- SEC remained explicitly unclaimed and separate
- no reviewer had to infer the assignable versus system-owned distinction from scattered files

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md) — promoted Lane H handoff and boundary statement
- [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md) — promoted authority decision for the system-owned `document_fetch` contract shape
- [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md) — Lane H setup authority that governed the cleared candidate
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md) — exact approved write set and denylist Lane H was reviewed against
- [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md) — canonical tool-definition contract shape Lane H implemented
- [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md) — promotion preconditions and post-promotion rule set
- [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md) — docs-only promotion verdict clearing Lane H for live control-plane adoption
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md) — cleared candidate synthesis for the current runtime truth
- [/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md) — immutable cleared-state checkpoint for the current runtime truth
- [LANE-D-AUTHORITY-RESOLUTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md) — historical Lane D ruling that froze `f1af7df`
- [NEXT-CONTROLLER-ACTION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md) — historical bridge from the blocked Lane D state into the Lane H package
- [candidate-f1af7df-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md) — frozen blocked-candidate synthesis for reference only
- [candidate-f1af7df-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md) — immutable blocked-state checkpoint for the superseded Lane D candidate
- [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md) — immutable cleared-state proof for the Wave 4B baseline the retrieval lanes rooted from

## Retrospective Audit Anchors

- Treat `91f97c2` as the last cleared-state docs checkpoint.
- Treat `2e6d780` as the first retro-planning handoff anchor, not as literal current `HEAD`.
- Treat `725a223e56dc5fd86fc135bd4bae940aed71db12` (`725a223`) as the exact control-plane snapshot this Lane H cleared-state reconcile started from.
- Treat `48293d262714c59ee9d45b6f01213b887fade48d` (`48293d2`) as the earlier Lane H setup-promotion control-plane snapshot, not as the current docs-reconcile pin.
- Treat `66f6178c1d710effe44cb5c278c5c729d5bcc216` (`66f6178`) as the earlier blocked-candidate control-plane snapshot, not as the current docs-reconcile pin.
- Treat `8bb00ab0298babd50d24fa3c07afae2ae7172ff6` (`8bb00ab`) as the earlier Lane D setup-promotion snapshot, not as the current docs-reconcile pin.
- Treat `c5dbd055d1b9d67c0d40a46f18b6b3a7f2b46468` (`c5dbd05`) as the earlier Batch 1 planning-package docs snapshot, not as the current docs-reconcile pin.
- Treat `RETROSPECTIVE-LINEAGE-MANIFEST.yaml` as the authoritative retrospective lineage layer for docs checkpoints `35a8a29` through `2e6d780`.
- Treat `RETROSPECTIVE-REVIEW-LEDGER.yaml` as the authoritative current review-status layer for retrospective audit prerequisites.
- Treat the manifest's exact git-derived pins as the replacement for the historical symbolic `HEAD` defect during retrospective audit use.
- Treat `65074ca` as the real seam-freeze artifact landing, but use `198ab92` as the first coherent live promotion of that artifact into active `wave-3 / setup`.
- The manifest repairs retrospective audit use of the older symbolic-`HEAD` defect without rewriting the historical checkpoint text itself.

## Controller Lease Events

- `2026-04-13T22:13:44.196852-04:00`: controller epoch advanced from `9` to `10` because the prior lease heartbeat (`2026-04-13T20:28:07-04:00`) was older than 30 minutes. This reconcile took over the stale lease before advancing the live control plane from Lane H setup to Lane H cleared state.

## Residual Follow-Ups

- `W2B-R01`: parse-invalid sprint-contract JSON now fails explicitly, but parseable under-specified JSON can still return empty Wave 2B enforcement fields.
