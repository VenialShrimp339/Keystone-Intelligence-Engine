# Review Stack Standard

## Why This Exists

The old failure mode was not just coding mistakes.
It was stale authority, under-reviewed scope changes, and state drift between code, docs, and review packets.

This standard defines the minimum review depth the overnight controller must use before it treats a milestone as real.

## For Runtime Candidates

Every runtime candidate must get:

1. contract/governance review
2. granular code/invariant review
3. backend-reality/live-probe review
4. product/e2e usefulness review
5. final synthesis review

These may be parallelized except for the final synthesis.

The generic stack is necessary but not sufficient.
Lane-specific checks below are also mandatory when those lanes exist.

## Runtime Review Questions

### Contract/Governance Review

- Did the change stay inside the approved write set?
- Did the change widen authority or semantics outside the lane?
- Did any system-owned surface leak into ordinary task assignment?
- Did the packet overclaim what was actually cleared?

### Granular Code/Invariant Review

- Do the code paths match the claimed contract?
- Are there hidden invariant breaks, bypasses, or caller-forged control paths?
- Did shared models change semantics when only additive changes were allowed?
- Are the tests actually load-bearing for the claimed behavior?

### Backend-Reality/Live-Probe Review

- Was the claimed backend behavior actually exercised live?
- Did the path use real transport rather than mocks or stub fallback?
- Are coverage/content-hash/artifact claims real?
- Did the packet keep source classes separate instead of silently conflating them?

### Product/E2E Usefulness Review

- Does this candidate actually move the project toward a usable MVP?
- Does the new capability reach the reporting path, or only a buried subsystem?
- Is the claimed gain meaningful for the professor-demo target?
- What still blocks end-to-end usefulness after this lane?

### Final Synthesis Review

- Are all prior reviews mutually consistent?
- Is the verdict `CLEARED` or `BLOCKED`?
- Does the control plane now need a reconcile?

## For Docs-Only Setup Packages

Every setup package must get:

1. authority/write-set/scope review
2. stale-doc/conflict/omission review
3. promotion decision review

If the package changes the near-term MVP path, also add:

4. MVP usefulness review

## Docs-Only Review Questions

### Authority/Write-Set/Scope Review

- Is the write set narrow and honest?
- Are denylist holes closed?
- Does the package accidentally reopen later lanes?
- Are all mandatory artifacts and tests named explicitly?

### Stale-Doc/Conflict/Omission Review

- Do any upstream or sibling docs still define a weaker contract?
- Are stale authority-adjacent statements still present?
- Could a later session cherry-pick a weaker packet definition?

### Promotion Decision Review

- Is the package safe to promote into the live control plane?
- If not, what exact defects remain?

### MVP Usefulness Review

- Does this lane actually help the shortest professor-demo path?
- Is the package over-designed relative to the overnight goal?

## Required Runtime Packet Depth

The review stack is incomplete unless the current lane's required packet set exists on disk and is internally coherent.

At minimum, any runtime candidate must have:

- implementation note
- file manifest
- backend truth matrix
- live-fetch or live-behavior review where applicable
- adversarial review
- second opinion
- review synthesis
- blocked-or-cleared checkpoint

Lane-specific packet requirements from the active setup artifact still win.

## Clearance Rule

A runtime candidate is not clearable unless:

- all required reviews exist
- no blocking review remains unresolved
- the synthesis pass says `CLEARED`
- the live control plane can absorb that clearance without contradiction

## Automation-Specific Rule

The controller may use subagents aggressively for review breadth, but it may not use review breadth as an excuse to skip synthesis.

The final state mutation still requires one controller synthesis pass that reads the actual review artifacts on disk.

## Lane-Specific Mandatory Reviews

### Lane H

Lane H is not clearable unless the reviews explicitly show:

- article fetch is real on the governed path
- PDF fetch is real on the governed path
- `document_fetch` stays system-owned and non-task-assignable
- SEC remains separate and unclaimed

### Lane E

Lane E is not clearable unless the reviews explicitly show:

- deterministic parse behavior for the approved source classes
- source-shaped locators are present and reviewable
- evidence-bundle normalization is explicit and stable

The minimum Lane E review set must include:

- deterministic parse review
- citation-locator review
- evidence-bundle schema review

### Lane F

Lane F is not clearable unless the reviews explicitly show:

- the reporting path actually consumes the approved Lane E bundles
- citations are anchored to fetched/parsed evidence
- mixed-governance boundaries remain intact

The minimum Lane F review set must include:

- integration regression review
- mixed-governance review
- citation-support spot-check review
