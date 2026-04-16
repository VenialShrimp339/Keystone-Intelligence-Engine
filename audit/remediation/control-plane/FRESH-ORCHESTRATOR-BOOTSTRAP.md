# Fresh Orchestrator Bootstrap

## Purpose

Use this file when starting a brand-new controller/orchestrator session after thread compaction.
This file is not the live control plane.

If this file conflicts with either of these, they win:

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)

## What A Fresh Session Must Know

- Lane H is the cleared runtime truth anchor at commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Treat runtime truth as pinned commit plus worktree path, not as path alone.
- No retrieval code lane is currently authorized from the main control plane.
- The narrow Lane E setup package already exists at commit `c9c7a1596d68171881023ce832412b74b2ee5c7c`.
- Cleared pre-promotion reviews for that package are persisted on the current branch at `8e002a77e149aba86ef5f0520e16e58b5647a551`.
- The next controller-priority milestone is promotion reconcile / decision for the existing Lane E package, or an explicit blocker record.
- SEC / EDGAR remains explicitly separate and later.
- Browser Use remains sidecar research only.

## What A Fresh Session Must Read First

Read these in order:

1. [AUTHORITY-INDEX.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/AUTHORITY-INDEX.md)
2. [SESSION-STANDARD.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/SESSION-STANDARD.md)
3. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
4. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
5. [FOUNDER-INTENT-DOCTRINE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/FOUNDER-INTENT-DOCTRINE.md)
6. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
7. [MVP-REQUIRED-BUILDOUT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md)
8. [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-parse/WORKSTREAM-HANDOFF.md)
9. [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-parse/NEW-LANE-SETUP-ARTIFACT.md)
10. [REVIEW-AND-GATE-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-parse/REVIEW-AND-GATE-CHECKLIST.md)
11. [package-c9c7a15-review-index.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/retrieval-parse/package-c9c7a15-review-index.md)

## What A Fresh Session Should Ignore

- Do not trust stale remembered chat outputs.
- Do not trust old references that still say the next step is to create the Lane E package.
- Do not reopen Lane D.
- Do not reopen Lane H coding just because the runtime worktree exists.
- Do not start SEC / EDGAR work, Browser Use implementation, UI work, benchmark acceptance, Wave 5, or calibration.

## First Required Milestone

The first milestone for a fresh controller session is:

- promotion reconcile / decision for the existing Lane E package
- or an explicit blocker record that explains why promotion cannot safely happen

Do **not** recreate the Lane E package.

## Lease / Control-Plane Rule

If the lease in `CONTROL-PLANE-STATE.yaml` is stale, the fresh controller must follow the takeover rule there before mutating live state.

## Success Condition For The Fresh Session

A fresh orchestrator session is doing the right thing if it ends with one of these outcomes:

- a committed promotion decision for the existing Lane E package
- a committed explicit blocker record for that package
- or a committed control-plane reconcile that safely records the outcome
