# Promotion Decision

Date: 2026-04-16
Controller mode: docs-only promotion reconcile rerun against repaired Lane E package state

## Record

- Reviewed package snapshot: `c9c7a1596d68171881023ce832412b74b2ee5c7c`
- Rerun controller snapshot: `f954edffa9d6b78e98bdbfedff78097539f425d5`
- Runtime truth anchor: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- Pre-promotion review persistence: `8e002a77e149aba86ef5f0520e16e58b5647a551`

## Verdict

- Final verdict: `PROMOTE`
- Safe to promote into the live control plane: `YES`

## Evidence Inputs

- `AUTHORITY-INDEX.md`
- `SESSION-STANDARD.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `FOUNDER-INTENT-DOCTRINE.md`
- `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
- `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
- `CURRENT-STATE.md`
- `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
- `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md`
- `audit/remediation/retrieval-parse/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-parse/NEW-LANE-SETUP-ARTIFACT.md`
- `audit/remediation/retrieval-parse/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-parse/REVIEW-AND-GATE-CHECKLIST.md`
- `audit/remediation/retrieval-parse/LANE-CHOICE-RATIONALE.md`
- `audit/remediation/retrieval-parse/SESSION-PROMPTS.md`
- `audit/remediation/runs/retrieval-parse/package-c9c7a15-review-index.md`
- `audit/remediation/runs/retrieval-parse/package-c9c7a15-scope-write-set-review.md`
- `audit/remediation/runs/retrieval-parse/package-c9c7a15-stale-doc-conflict-review.md`
- `audit/remediation/runs/retrieval-parse/package-c9c7a15-usefulness-review.md`

## What Verified Cleanly

- Lane H remains the cleared runtime truth anchor for governed article/PDF fetch at `93a5ca8`, and Lane E is rooted only in persisted Lane H outputs.
- `document_fetch` remains system-owned and non-task-assignable exactly as cleared in Lane H; Lane E does not reopen fetch authority.
- The promoted lane remains article/PDF only.
- The promoted lane remains deterministic parse plus evidence normalization only.
- The package keeps SEC / EDGAR, papers, Lane F, claim-scoped citation migration, UI, benchmark acceptance, and broader downstream integration out of scope.
- The package is explicit that one thin internal post-E bridge is later and separate from Lane E.
- The three tracked pre-promotion sidecars for package snapshot `c9c7a15` are present on disk, pinned to the correct reviewed snapshot, and all `CLEARED`.
- The fourth required pre-promotion review is this controller promotion review, which closes the package-review burden named in `REVIEW-AND-GATE-CHECKLIST.md`.

## Repaired Prior Defects

The earlier `DO_NOT_PROMOTE` concerns attached to the unrepaired package tree are now closed in the repaired current canon used for this rerun.

- The package no longer depends on missing tracked subordinate Retrieval MVP docs in its required open-path or live authority stack.
- Graphify is now explicitly optional if absent rather than a mandatory durable dependency.
- Those repairs are docs/provenance-only and do not widen Lane E beyond the already-reviewed narrow article/PDF parse and evidence-normalization boundary.

This promotion is therefore grounded in the tracked package snapshot `c9c7a15` as reviewed through the repaired current canon persisted at `f954edf`, not in the unrepaired `c9c7a15` tree viewed in isolation.

## Promotion Decision

- Promotion outcome: `PROMOTE`
- Lane to activate after control-plane updates: `Lane E - Article/PDF Deterministic Parse And Evidence Normalization`
- Next branch to open: `codex/retrieval-mvp-parse`
- Next worktree to open: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-parse`
- Runtime baseline to open from: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` at `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- Review packet root for the next lane: `audit/remediation/runs/retrieval-parse/`

## Residual Non-Blockers

- The evidence stack is still intentionally cross-worktree: Lane H runtime proof remains anchored in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`, and the Lane E pre-promotion sidecars remain a later persisted current-branch layer rather than part of the original `c9c7a15` tree itself.
- SEC / EDGAR venue work remains separate and later.
- Lane E alone still does not make the article/PDF retrieval layer usable end-to-end on the canonical research path because the later thin post-E bridge is still separate.
