# Session Standard

Status: mandatory shared operating standard for both Claude and Codex.
This standard applies immediately, including to the session that introduced it.

## Fresh-Session Read Order

1. `AUTHORITY-INDEX.md`
2. `SESSION-STANDARD.md`
3. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
4. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
5. `FOUNDER-INTENT-DOCTRINE.md`
6. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
7. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
8. `CURRENT-STATE.md`
9. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
10. the task-specific packet, package, or review index relevant to the current work
11. `SESSION-LOG.md` only if historical rationale is needed
12. generated support artifacts such as `graphify-out/GRAPH_REPORT.md` only if present

If the control-plane pair exists, do not start from `CURRENT-STATE.md` alone.

## Required End-Of-Session Updates

For any repo-mutating or decision-setting session, complete every required item before ending:

1. add a `SESSION-LOG.md` entry
2. update `CURRENT-STATE.md` if the onboarding summary changed
3. update the control-plane pair if live truth changed
4. create or update any required packet or checkpoint doc

Missing a required artifact makes the session noncompliant.

## Required Provenance Fields

Any session log entry, checkpoint, or handoff note created under this standard must record:

- timestamp with timezone
- agent/runtime identity
- worktree path
- branch
- start commit
- end commit, or explicit `no commit`
- files changed or reviewed
- authority docs read
- summary of work performed
- decisions or contradictions resolved
- tests or other evidence run
- blockers or residual risks
- exact next action

## When To Update `CURRENT-STATE.md`

Update `CURRENT-STATE.md` only when the onboarding summary changes:

- active workstream changes
- blocked, cleared, pending, or authorization state changes
- runtime truth anchor commit or worktree changes
- authoritative next action changes
- a contradiction resolution changes what a fresh session must believe

Do not use `CURRENT-STATE.md` as scratch space or as a complete chronology ledger.

## When To Update The Control Plane

Update `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` and `audit/remediation/control-plane/ACTIVE-HANDOFF.md` when live truth changes:

- lease takeover
- runtime truth anchor changes
- allowed write set changes
- active wave or controller-priority workstream changes
- setup, package, promotion, or blocker status changes
- authoritative next action changes
- docs-reconcile pin changes

`CURRENT-STATE.md` must never move ahead of the control plane.

## When A Packet Or Checkpoint Is Required

Create or update a packet/checkpoint doc for:

- a new setup package
- a pre-promotion review bundle
- a blocked or cleared candidate
- a promotion decision
- an explicit blocker record
- a no-commit handoff for repo-mutating work
- any material stop where a later session could confuse WIP with canon

Each packet or checkpoint must pin:

- snapshot commit
- worktree path
- write set
- evidence inputs
- verdict
- follow-on action

## No-Commit Rule

- Uncommitted work is not durable canon.
- If a session ends without a commit and files changed, leave a checkpoint or handoff note with the exact dirty file list and safe resume instructions.
- Do not repin the control plane or claim promotion or clearance to uncommitted state.

## Blocked / In-Progress Recording Rule

- Record blocked state conservatively.
- Distinguish confirmed primary evidence, likely inference, unresolved contradiction, founder doctrine, and provenance risk.
- Do not rewrite historical packet contents to smooth chronology.
- Do not destroy or silently normalize user work, packet families, archive contents, or external worktree evidence.

## Generated Support Artifacts

- Generated support artifacts such as `graphify-out/GRAPH_REPORT.md` are optional aids.
- If present, use them for architecture/codebase orientation.
- If absent, continue and note the absence.
- Do not make tracked entrypoints depend on generated or untracked artifacts as unconditional authority.
