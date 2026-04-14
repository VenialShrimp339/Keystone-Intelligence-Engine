# Fresh Orchestrator Bootstrap

## Purpose

Use this file when starting a brand-new controller/orchestrator session after heavy thread compaction.

This file is not the live control plane.
It exists to help a fresh session take over from disk without needing prior chat history.

If this file conflicts with either of these, they win:

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)

## What A Fresh Session Must Know

- The project is no longer in the retrospective-audit phase. That phase is complete and only serves as prerequisite proof now.
- The old Retrieval MVP Lane D candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` is frozen as blocked superseded reference material only.
- Lane H is not merely "setup-promoted" anymore. It is fully cleared at `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`.
- The current real runtime truth for governed article/PDF fetch lives in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- No retrieval code lane is currently authorized from the main control plane.
- The next controller-priority milestone is docs-only: `Professor-Demo Narrow Lane E Setup`.
- SEC / EDGAR remains explicitly separate and later.
- Browser Use remains sidecar research only, classified `FALLBACK_ONLY`.

## What A Fresh Session Must Read First

Read these in order:

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
4. [MVP-REQUIRED-BUILDOUT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md)

Then read the active Lane H authority + cleared packet:

5. [WORKSTREAM-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md)
6. [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md)
7. [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md)
8. [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
9. [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md)
10. [PROMOTION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md)
11. [candidate-93a5ca8-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md)
12. [candidate-93a5ca8-blocked-or-cleared-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md)

Only after that should the fresh controller decide what to spawn.

## What The Fresh Session Should Ignore

- Do not trust stale remembered chat outputs.
- Do not trust old references that still talk about "Lane H setup" unless they are explicitly historical.
- Do not reopen the paused automation/heartbeat as the first action.
- Do not reopen Lane D.
- Do not reopen Lane H coding just because the runtime worktree exists.
- Do not touch the large unrelated dirty repo state outside controller-approved docs unless the active lane explicitly requires it.
- Do not start SEC / EDGAR, Browser Use implementation, UI work, benchmark acceptance, Wave 5, or calibration.

## First Required Milestone

The first milestone for a fresh orchestrator session should be:

- create a docs-only narrow Lane E setup package rooted from `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`

That setup package should stay narrow:

- article/PDF deterministic parse only
- evidence normalization only
- no SEC / EDGAR
- no Lane F integration yet
- no UI
- no benchmark acceptance claims

## Recommended Session/Wave Pattern

For the next controller cycle, use this sequence:

1. one docs-only setup-package worker for narrow Lane E
2. parallel docs-only reviewers:
   - authority/write-set/scope
   - stale-doc/conflict/omission
   - MVP usefulness
3. one promotion-decision synthesis worker
4. one docs-only control-plane promotion reconcile if the package clears

Only after that should any Lane E code session exist.

## Lease / Control-Plane Rule

If the lease in `CONTROL-PLANE-STATE.yaml` is stale, the fresh controller must follow the takeover rule there before mutating live state.

## Success Condition For The Fresh Session

A fresh orchestrator session is doing the right thing if it ends with one of these outcomes:

- a committed narrow Lane E setup package ready for review
- a committed promotion decision on that package
- a committed control-plane promotion for Lane E
- or a precise blocker note that explains why the above cannot safely happen

If it starts doing more than one of those in a single uncontrolled chain, it is drifting.

