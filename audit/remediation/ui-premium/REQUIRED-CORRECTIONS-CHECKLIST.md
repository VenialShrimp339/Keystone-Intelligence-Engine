# Required Corrections Checklist

Use this checklist before treating the UI Premium package as safe for controller handoff or implementation unlock.

- [x] Define one authoritative pre-run sequence that explicitly resolves `Preview plan` versus Gate 1 HITL review.
- [x] State whether the first pause is analyst confirmation, post-specification HITL review, or a single merged step.
- [x] Add exact user-facing source/evidence states for current reality, including discovered-only, cited-in-claim, URL-checked, snippet-only, and not-passage-anchored.
- [x] Keep discovery, citation existence, and claim support visibly separate in the copy contract.
- [x] Demote `Mixed / non-canonical` from required runtime labeling until lineage is artifact-backed, or add an explicit unknown-lineage fallback.
- [x] Remove or defer `Library` from primary navigation unless it is renamed and bounded to a currently backed surface.
- [x] Update the handoff package map and authority ordering so future sessions read the correct docs first.
- [x] Add an explicit unlock guard that says plan-preview semantics must be frozen before any runtime UI lane opens.

## Final Judgment

Yes. The package is now safe to use as a controller handoff.

Implementation remains blocked until retrieval seams lock, one canonical runtime surface is promoted, and a controller explicitly opens runtime UI work.
