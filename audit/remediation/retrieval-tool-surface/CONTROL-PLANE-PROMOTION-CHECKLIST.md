# Control-Plane Promotion Checklist

Date: 2026-04-13

## Purpose

Use this checklist before promoting the retrieval-tool-surface package into the live controller authority stack.

This checklist exists to prevent the new lane from becoming another implicit registry change that only looks authorized after the fact.

## Required Evidence Inputs

- `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
- `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
- `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md`
- `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md`

## Promotion Preconditions

- Confirm article/PDF canonical fetch is still Retrieval MVP-critical.
- Confirm the package does not narrow MVP by omission.
- Confirm the chosen shape is system-owned `document_fetch`, not a new ordinary task-assigned tool.
- Confirm the SEC issue is still explicitly separated and deferred.
- Confirm `f1af7df` remains frozen as superseded reference material, not the promoted base.

## Required External Docs To Update On Promotion

If the controller promotes this package, update at minimum:

1. `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`
2. `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
3. `audit/remediation/retrieval-mvp/WORKTREE-AND-REVIEW-GATE-CHECKLIST.md`
4. `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md` or a successor setup artifact
5. `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md` or a successor write-set file
6. `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md` or a successor gate-checklist file
7. `audit/remediation/next-wave-setup/TOOL-CONTRACT-GATE.md`
8. `audit/remediation/next-wave-setup/GOVERNANCE-GATE.md`
9. `audit/remediation/next-wave-setup/RUN-CONTRACT-GATE.md`
10. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
11. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

Do not mark Lane H as active until those updates exist.

## Required Review Verdicts

The promotion packet needs explicit verdicts for:

- tool-contract safety
- governance safety
- run-contract safety
- backend reality for article/PDF
- SEC separation hygiene

Minimum expected findings each reviewer must answer:

- Can `document_fetch` leak into `ResearchTask.assigned_tools`?
- Can registry membership still be mistaken for task assignability?
- Is article/PDF fetch proof being conflated with SEC clearance?
- Is any later session being set up to smuggle an MVP scope cut?

## No-Promotion Conditions

Do not promote if any of the following are true:

- the docs imply `document_fetch` can be assigned by the task generator
- the docs leave `ALL_TOOLS` semantics ambiguous
- the write set allows research-agent or orchestrator edits
- the package quietly reclassifies SEC as part of the same decision
- the package treats `f1af7df` as environment-only blocked

## Promotion Outcome

If promoted, the controller should record all of the following explicitly:

- lane name: `Lane H - Retrieval Tool-Surface Authority Expansion`
- branch: `codex/retrieval-tool-surface`
- worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
- run packet root: `audit/remediation/runs/retrieval-tool-surface/`
- article/PDF MVP-critical status: unchanged
- SEC status: separate downstream venue review

## Post-Promotion Rule

Once promoted, the next coding session should start from the session prompt in [SESSION-PROMPTS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/SESSION-PROMPTS.md), not from the old Lane D prompt family.
