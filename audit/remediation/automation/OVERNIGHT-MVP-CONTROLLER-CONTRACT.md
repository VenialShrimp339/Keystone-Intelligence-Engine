# Overnight MVP Controller Contract

## Purpose

This contract governs any unattended Codex heartbeat that tries to move Keystone toward a professor-usable MVP.

The automation is allowed to make progress.
It is not allowed to improvise authority, skip review depth, or silently widen scope.

This document is not live authority by itself.
Live authority still comes from:

1. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md`

If this contract conflicts with the live control plane, the control plane wins.

## Overnight Goal

The overnight goal is the shortest honest path from the current state to a professor-usable MVP demo.

That means:

- governed article/PDF retrieval on the real path
- deterministic parse/evidence preparation for the article/PDF path
- retrieval integration so the reporting path can use fetched evidence
- one thin comparison/demo run against parallel deep-research control

That does not mean:

- full SEC/EDGAR coverage
- full benchmark program
- full UI
- advanced retrieval stack
- Browser Use on the canonical path
- Wave 5 or calibration

The strongest terminal claim this automation should make on its own is:

- `professor_demo_ready_on_article_pdf_path`

It must not claim:

- `full_mvp_cleared`

unless SEC/EDGAR, canonical runtime promotion, and the remaining MVP blockers have actually been cleared in the control plane.

## Current Assumptions

The automation must never trust these assumptions blindly.
It must re-verify them from disk at the start of every wake.

- The main workspace is docs-only controller space.
- The last cleared code baseline is `65a612d`.
- The old Retrieval MVP Lane D candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` is frozen as blocked superseded reference material only.
- `Lane H - Retrieval Tool-Surface Authority Expansion` is the active forward retrieval lane.
- `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` is the current Lane H candidate under review/clearance reconciliation pressure.

## Non-Negotiable Safety Rules

1. Read the live control plane and active handoff at the start of every wake.
2. Treat the automation prompt as advisory only. Treat disk state as truth.
3. If the lease is stale under the takeover rule, perform the required takeover before mutating state.
4. Do not depend on chat history, Jack-as-clipboard behavior, or stale pasted outputs.
5. Keep the main workspace docs-only unless the live control plane explicitly says otherwise.
6. Allow runtime edits only in the controller-approved clean worktree for the currently authorized lane.
7. Never run overlapping code-writing lanes.
8. Never patch forward the frozen Lane D candidate.
9. Never start Lane E, Lane F, UI, SEC work, Wave 5, calibration, Browser Use implementation, or advanced retrieval work unless the control plane explicitly promotes that lane.
10. Stop immediately on any authority gap, unresolved blocker, or write-set conflict.

## Atomic Wake Rule

Each heartbeat wake may complete at most one milestone.

A milestone is one of:

- one docs-only reconcile/promotion
- one docs-only setup package
- one docs-only package review
- one runtime implementation candidate
- one runtime review stack plus synthesis
- one thin comparison/demo package

After completing one milestone, the automation must stop and wait for the next wake.

Why this rule exists:

- it prevents long chains of stale assumptions
- it keeps review and promotion boundaries explicit
- it reduces overlapping state mutations
- it keeps context windows from turning into silent workflow engines

## Allowed Subagent Pattern

The safe subagent pattern is:

- one controller
- zero or one code-writing implementer
- multiple read-only reviewers

Do not use multiple overlapping code-writing implementers on the same lane unless the write sets are explicitly disjoint and controller-promoted. The current overnight MVP path does not justify that complexity.

### Preferred Review Team For Runtime Candidates

Run these in parallel where useful:

1. contract/governance review
2. granular code/invariant review
3. backend-reality/live-probe review
4. product/e2e usefulness review

Then run one synthesis pass that decides `CLEARED` or `BLOCKED`.

### Preferred Review Team For Docs-Only Setup Packages

Run at least:

1. authority/write-set/scope review
2. stale-doc/conflict/omission review
3. MVP usefulness review if the package changes the professor-demo path

Then run one promotion decision pass.

## Required Evidence Before Continuing

The controller may continue automatically only when all three agree:

1. the live control plane
2. the active handoff
3. the current lane packet / current review packet

If they do not agree, the next milestone must be a docs-only reconcile or blocker stop.

## Hard Stops

The automation must stop and not improvise if:

- the control plane does not authorize the next lane
- a required artifact is missing or contradictory
- a code diff escapes the approved write set
- a review finds a blocker outside the active lane scope
- a new architecture decision is needed
- an external dependency requires human judgment
- SEC/EDGAR becomes entangled with the article/PDF path before the control plane says it may
- Browser Use starts to look like a canonical-path substitute rather than sidecar research

## Blocker Behavior

If a hard stop is hit:

1. do not keep coding
2. write a concise blocker note under `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/automation/OVERNIGHT-BLOCKER.md`
3. include:
   - the exact blocker
   - why it is blocked
   - what file(s) established the block
   - the exact next controller prompt needed
4. pause the automation rather than waking repeatedly into the same blocker

## MVP-Critical Path For This Automation

The overnight controller is allowed to chase only this narrow path:

1. reconcile Lane H clearance into the live control plane if stale
2. create and promote a narrow professor-demo Lane E setup package
3. implement Lane E
4. review and reconcile Lane E
5. create and promote a narrow professor-demo Lane F setup package
6. implement Lane F
7. review and reconcile Lane F
8. run one thin comparison/demo package

Anything else is either later or sidecar.

## Explicit Defers

These are not part of the overnight MVP critical path:

- SEC/EDGAR venue resolution
- Browser Use implementation
- embeddings / `pgvector` / BM25 / RRF / rerank
- full benchmark suite
- full UI implementation
- repo cleanup
- Wave 5
- calibration

## Definition Of Overnight Success

The overnight controller succeeds only if it leaves behind:

- truthful control-plane state
- truthful handoff state
- reviewed code only in promoted lanes
- one working narrow article/PDF-based reporting path
- one comparison/demo package that is honest about what is and is not solved

If it cannot do that safely, it should stop early with a clean blocker instead of bluffing progress.
