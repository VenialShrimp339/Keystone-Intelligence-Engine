# Adversarial Findings

Date: 2026-04-13  
Scope: full review of `audit/remediation/ui-premium/` as a controller handoff package  
Runtime anchor checked: `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`

## Final Judgment

No.

The package is directionally honest, but it is not yet safe to use as a controller handoff until it resolves the pre-run/HITL lifecycle ambiguity and turns the discovery/evidence boundary into an actual UI contract instead of a stated principle.

## Findings Ordered By Severity

### 1. [P0] Canonical lifecycle hides the real pre-run HITL gate

Location:

- `audit/remediation/ui-premium/INFORMATION-ARCHITECTURE.md:48-57`

Problem:

The package's canonical sequence puts `Needs review` only after `Running`, but the authoritative runtime can create a real `post_specification` HITL gate before L1 research begins. Because this same package also makes `Preview plan` and `Plan ready` the mandatory pre-run flow, future implementation work has no controller-grade answer for whether the first pause is analyst confirmation, Gate 1 review, or both.

Why this is unsafe:

- It can duplicate review.
- It can collapse HITL into a simple start button.
- It leaves the controller handoff ambiguous on the first real pause boundary.

Runtime basis:

- `src/keystone/specification/spec_engine.py` creates Gate 1 before research when `db_session_factory` is present.
- `audit/remediation/ui-premium/SCREEN-SPECS.md` also defines `Plan ready` as a separate pre-run state.
- `audit/remediation/ui-premium/REVIEWER-FLOW-SPEC.md` treats the checkpoint as a real runtime pause.

### 2. [P1] Mixed-lineage banner is promoted before it is provable

Location:

- `audit/remediation/ui-premium/RUN-INSPECTOR-AND-DEV-MODE.md:117-129`

Problem:

This file elevates `Mixed / non-canonical` into the required runtime banner set even though the state contract says mixed lineage is still provisional and not artifact-backed.

Why this matters:

- It invites heuristic labeling from partial bundles.
- It creates false precision around governed versus bypass provenance.
- It weakens the package's own governance-truth boundary.

Required correction direction:

- Keep `Mixed / non-canonical` reserved until lineage is persisted.
- Or add an explicit unknown-lineage fallback instead.

### 3. [P1] Primary-nav `Library` smuggles future product depth

Location:

- `audit/remediation/ui-premium/SCREEN-SPECS.md:9-16`

Problem:

Putting `Library` in primary navigation introduces a product area that the rest of the package repeatedly says is not current analyst reality. In this repo, `Library` strongly implies cross-engagement memory or Observation Library depth, yet the handoff explicitly forbids presenting those surfaces as live product truth.

Why this matters:

- It makes the controller handoff easy to misread as approval for future-product chrome.
- It blurs current artifact reality versus future product ambition.
- It creates unnecessary pressure to invent a bounded meaning later.

### 4. [P1] Citation-theater risk is named but not operationalized

Location:

- `audit/remediation/ui-premium/COPY-GUARDRAILS.md:27-35`

Problem:

The package calls citation theater a P0 risk, but the required-copy table still omits exact user-facing labels for the critical interim source/evidence states. Without controller-grade copy for states like discovered-only, cited-in-claim, URL-checked, snippet-only, and not-passage-anchored, a later UI pass can still collapse discovery and evidence into one polished source row.

Why this matters:

- Discovery can still masquerade as evidence.
- Citation existence can still be mistaken for support.
- The risk register is stronger than the actual copy contract.

Required correction direction:

- Add exact interim labels and warnings for current source/evidence states.
- Keep those labels consistent with the provisional support taxonomy in the run-state contract.

### 5. [P2] Package map is stale for a controller handoff

Location:

- `audit/remediation/ui-premium/WORKSTREAM-HANDOFF.md:127-137`

Problem:

The package map omits `SCREEN-SPECS.md`, `COPY-GUARDRAILS.md`, `RUN-STATE-CONTRACT.md`, and `REVIEWER-FLOW-SPEC.md`, even though later prompts make those files authoritative deliverables.

Why this matters:

- A future session can read the wrong authority set.
- Already-settled boundaries can be reopened accidentally.
- The handoff package becomes harder to trust as an index.

## Controller Conclusion

This package should not be used as an implementation unlock or controller handoff yet.

Final judgment: No.
