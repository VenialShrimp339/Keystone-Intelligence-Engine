# Active Handoff

## Current Truth

- `AUTHORITY-INDEX.md` remains the mandatory front door and `SESSION-STANDARD.md` remains the shared operating standard.
- Live current truth now begins with this control-plane pair in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization`.
- The active branch is `codex/owner-triage-normalization`. Remote README-only commits were rebased into the local branch on 2026-05-28, preserving the artifact-centered rebuild commits on top.
- The active product direction is the artifact-centered, subscription-first Keystone research rebuild, not the old April Lane E retrieval-parse next action.
- Keystone's DPVI / issue-tree architecture is preserved. The execution boundaries are changing: expensive provider research must produce durable artifacts that can be inspected, resumed, reprocessed, and evaluated without rerunning upstream work.
- The old Claude CLI-first runtime doctrine is stale. Preferred routing is now Codex CLI for structured local calls, ChatGPT web Deep Research for primary hosted research, Claude web Research for secondary/cross-check research, manual upload as fallback, deterministic public-source connectors for precision workflows, and API only as fallback/control.
- The issue-tree/problem-decomposition skill is prototype-ready at `.agents/skills/problem-decomposition/`. It is not production-integrated into KIE yet.
- The next KIE specification step is to implement a Pydantic `IssueTreePackage` upstream of the current `Decomposer`, after running the recommended issue-tree skill eval subset.
- Claude web Research full lifecycle is proven and ingested for the public auto-body consolidation probe.
- ChatGPT web Deep Research full lifecycle is now proven and ingested for the same public probe.
- ChatGPT export nuance: the Markdown export preserved opaque citation markers, while the Word export exposed the actual source URLs. The browser adapter should preserve both body and source-link exports for ChatGPT until a cleaner export route is proven.
- The worktree contains external presentation draft files that are unrelated to KIE source. They were locally excluded through the Git worktree exclude file rather than deleted or moved.

## Fresh-Session Read Order

1. [AUTHORITY-INDEX.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/AUTHORITY-INDEX.md)
2. [SESSION-STANDARD.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/SESSION-STANDARD.md)
3. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
4. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
5. [FOUNDER-INTENT-DOCTRINE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/FOUNDER-INTENT-DOCTRINE.md)
6. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/CURRENT-STATE.md)
7. [OWNER-VISION-2026-05-24.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/notes/OWNER-VISION-2026-05-24.md)
8. [ARCHITECTURE-PRESERVATION-AUDIT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md)
9. [PROVIDER-FEASIBILITY-REPORT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md)
10. [HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/issue-tree-skill/handoff/HANDOFF.md)
11. [JULY-27-EXECUTION-PLAN.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/roadmap/JULY-27-EXECUTION-PLAN.md)
12. [SESSION-LOG.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/SESSION-LOG.md) only if historical rationale is needed.

## Live Authority Order

Any lower-order file that conflicts with a higher-order item below loses for live current-truth questions.

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/CURRENT-STATE.md)
4. [FOUNDER-INTENT-DOCTRINE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/FOUNDER-INTENT-DOCTRINE.md) for product doctrine only
5. [OWNER-VISION-2026-05-24.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/notes/OWNER-VISION-2026-05-24.md)
6. [ARCHITECTURE-PRESERVATION-AUDIT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md)
7. [PROVIDER-FEASIBILITY-REPORT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md)
8. [Issue-tree skill handoff](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/issue-tree-skill/handoff/HANDOFF.md)
9. [JULY-27-EXECUTION-PLAN.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization/audit/roadmap/JULY-27-EXECUTION-PLAN.md)
10. Historical remediation packets and `SESSION-LOG.md` as provenance only

## Active State Tuple

- `active_branch`: `codex/owner-triage-normalization`
- `active_worktree_path`: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization`
- `active_state`: `artifact_centered_research_rebuild_active`
- `controller_priority_workstream`: `Repository cleanup and fresh-goal launch readiness`
- `stage_b_checkpoint_after_rebase`: `5be732d`
- `stage_b_doc_checkpoint_after_rebase`: `fa1f92e`
- `chatgpt_provider_capture_after_rebase`: `a3fd5984c526401535d1e26e829f53cc1e76d6c2`
- `worktree_state`: clean after local excludes; cleanup doc commit and push are the only remaining prep steps
- `issue_tree_skill_status`: prototype-ready for more eval
- `claude_provider_probe`: completed and ingested
- `chatgpt_provider_probe`: completed, exported, source links recovered, and ingested

## Exact Next Action

1. Commit and push the cleanup/current-truth docs so GitHub matches local state.
2. In a fresh Codex session, run the recommended issue-tree skill eval subset.
3. Implement `IssueTreePackage` upstream of the current `Decomposer`.
4. Build the browser provider adapter from the proven lifecycle:
   - tab registry
   - export-ready detection
   - ChatGPT Markdown plus DOCX export
   - Claude artifact export
   - provider ledger
   - blocked-state pause
   - per-provider concurrency controls
5. Build the first artifact-centered vertical slice.
6. Expand to a multi-branch provider prototype only after the vertical slice is stable.

## Historical Remediation Notes

- Historical implementation remains cleared through Wave 4B at `65a612d`.
- Lane H commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` remains a useful prior governed article/PDF retrieval anchor.
- Lane E package `c9c7a1596d68171881023ce832412b74b2ee5c7c` and its promotion are preserved as old remediation provenance.
- Retrieval MVP Lane D candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` remains blocked, frozen, and superseded reference material.
- SEC / EDGAR venue review remains deferred as a separate deterministic-source workflow.

## Controller Lease Events

- `2026-04-13T22:13:44.196852-04:00`: controller epoch advanced from `9` to `10` and advanced the live control plane from Lane H setup to Lane H cleared state.
- `2026-04-16T16:51:40-0400`: controller epoch advanced from `10` to `11` for Lane E promotion reconcile.
- `2026-04-16T18:32:49-0400`: controller epoch advanced from `11` to `12` for Lane E promotion rerun.
- `2026-05-28T14:08:49-0500`: controller epoch advanced from `12` to `13`; live next action changed from old Lane E retrieval-parse work to the artifact-centered, subscription-first research rebuild after owner direction, provider feasibility work, and issue-tree skill prototype completion.
- `2026-05-28T14:23:35-0500`: controller epoch advanced from `13` to `14`; ChatGPT Deep Research moved from completed-in-browser/pending-capture to completed/exported/source-links-recovered/ingested.
- `2026-05-28T14:51:06-0500`: controller epoch advanced from `14` to `15`; remote README-only commits were rebased into local branch, local presentation drafts were excluded from Git status without moving/deleting them, and the branch was prepared for push before the fresh autonomous goal.
