# Current State

*Last updated: 2026-04-16 | Updated by: docs/provenance canonization pass*

> Summary-only current-truth layer. For live authority, start with `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair.

## Live Status

- Historical implementation remains cleared through Wave 4B at `65a612d`.
- The current cleared runtime truth anchor is Lane H commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` in worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
- Treat runtime truth as pinned commit plus worktree path. The worktree's current `HEAD` may be newer docs-only state and does not replace the pin.
- No retrieval code lane is currently authorized from the main control plane.
- The tracked narrow Lane E setup package exists at `c9c7a1596d68171881023ce832412b74b2ee5c7c`.
- Cleared pre-promotion Lane E reviews are persisted on the current branch at `8e002a77e149aba86ef5f0520e16e58b5647a551`.
- Live control-plane promotion of that package is still pending.
- Retrieval MVP Lane D candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` remains blocked, frozen, and superseded reference material only.
- The main workspace is authorized for docs/provenance work only in this session. That is an authorization policy, not a cleanliness claim.
- Browser Use remains `FALLBACK_ONLY` with a secondary `BENCHMARK_OR_CONTROL_ARM_ONLY` role.

## What Happens Next

1. Start from `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair.
2. Treat Lane H as the cleared runtime truth anchor, not as an active execution lane.
3. Use the existing Lane E package and review index as the next controller input:
   - `audit/remediation/retrieval-parse/WORKSTREAM-HANDOFF.md`
   - `audit/remediation/runs/retrieval-parse/package-c9c7a15-review-index.md`
4. The next controller-priority milestone is promotion reconcile / decision for the existing Lane E package, or an explicit blocker record.
5. Do **not** reopen Lane H coding, Lane D coding, SEC / EDGAR, Lane F, UI work, benchmark acceptance claims, Wave 5, or calibration unless the control plane is explicitly updated again.

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
10. the task-specific package and review index
11. `SESSION-LOG.md` only if historical rationale is needed

## Non-Authoritative But Useful

- `SESSION-LOG.md` is provenance-only history, not the complete live chronology.
- `docs/ARCHITECTURE.md` is an older scaffold/code-structure snapshot.
- `docs/architecture-and-evolution.md` is a derived historical/professor narrative, not current-state truth.
- `audit/remediation/README.md` is historical remediation-process narrative.
