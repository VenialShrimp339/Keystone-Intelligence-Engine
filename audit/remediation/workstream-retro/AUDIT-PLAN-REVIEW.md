# Audit Plan Review

*Date: 2026-04-12 | Scope: retrospective audit-program critique for the autonomous remediation workstream*

---

## Executive Summary

The candidate audit-slice plan has the right spine, but it is not launch-ready as written.

It needs five corrections before the eventual review sessions start:

1. Batch 1 must become a hard trust gate.
2. `CP-2` must expand into a controller-code-packet join audit.
3. `RP-1` must explicitly check packet integrity, not just packet presence.
4. `W2B-1`, `W3B-1`, `W4D-1`, and `W4B-1` need mandatory sub-verdicts so they are not too coarse.
5. `W4B-2` cannot be treated as an unconditional peer-clearance review if `W4B-1` is unresolved.

The refined program below keeps the overall slice count efficient while tightening the trust boundaries enough to catch cascading invalidity.

## Freeze Notes

- The last cleared code commit remains `65a612d`.
- The last Wave 4B cleared-state docs checkpoint remains `91f97c2`.
- The pre-planning docs anchor commit is `2e6d780` (`Add handoff for retrospective audit-program planning`).
- Therefore the handoff's recorded `HEAD` of `91f97c2` is no longer the literal repo `HEAD`; it is the last cleared-state docs checkpoint, while `2e6d780` is the pre-planning anchor for this audit package.
- All outputs written under `audit/remediation/workstream-retro/` in this session should be treated as planning sidecars, not controller-promoted authority.

## What Is Correct In The Candidate Plan

- It correctly recognizes that the audit cannot be a monolithic review of current `codex/remediation-program`.
- It correctly separates code lineage from controller/docs lineage.
- It correctly identifies review-packet integrity as its own meta-audit surface.
- It correctly treats Wave 4B memo-to-code conformity as distinct from Wave 4B runtime review.
- It correctly places the cross-wave regression audit at the end.

## What Must Change

### 1. Batch 1 False Parallelism

The candidate Batch 1 groups trust-establishment slices with downstream boundary slices.

That is unsafe.

- `CP-1`, `CP-2`, and `RP-1` establish whether the rest of the inputs are trustworthy.
- `W2B-1`, `W3A-1`, and `W4D-1` consume those inputs.

If authority order, checkpoint mapping, or packet integrity is wrong, later reviews risk auditing the wrong baseline, the wrong packet set, or a stale boundary doc.

### 2. Missing Join Between Controller History And Code History

The candidate plan separates:

- control-plane authority
- controller checkpoint chain
- review-packet integrity

But it does not explicitly verify that each controller/docs checkpoint points at the right code commit, packet set, active boundary doc, and next action.

That join is required because the project has two intertwined histories:

- code lineage: `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- controller/docs lineage:
  `35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2 -> 2e6d780`

The refined plan therefore expands `CP-2` into a controller-checkpoint plus controller-code-packet join audit.

### 3. `RP-1` Must Be Stronger Than A Presence Check

`RP-1` is load-bearing.

It must check:

- missing packet types
- mismatched commit headers
- cross-link correctness
- packet metadata alignment
- template contamination
- patch markers embedded in artifacts
- cross-wave content bleed

This is not hypothetical.

`audit/remediation/runs/wave-4/candidate-TEMPLATE-file-manifest.md` currently contains an appended `*** Add File` hunk for `candidate-5cc9585-clearance.md`, which is a real packet-integrity defect.

### 4. `W2B-1` Is Too Broad Unless It Has Mandatory Sub-Verdicts

Wave 2B has two distinct retrospective questions:

1. Was the blocked `4ff7e90` lineage captured and recovered correctly?
2. Did `2cdbfec` really close the Wave 2B blocker set on the runtime path?

These should stay inside one launch slice for efficiency, but the prompt must require two explicit sub-verdicts:

- `blocked-parent lineage`
- `cleared runtime closure`

### 5. `W3B-1` Is Too Broad As A Single Undifferentiated Runtime Review

Wave 3B combines two different risk surfaces:

- `StructuredOutline` / renderer / round-state continuity
- single-controller iterative-loop authority

These can still live in one launch slice, but the prompt must force separate sub-verdicts for:

- structural contract and state continuity
- orchestrator-owned control-loop authority

### 6. `W4D-1` Is Underspecified

`W4D-1` should not return one coarse wave-level yes/no over all memos.

It needs to audit:

- each Wave 4 memo's scope classification
- each memo's dependency note
- whether `WAVE-4B-SETUP.md` transcribed those memo boundaries into the approved slice map, write set, denylist, and runtime-probe bundle

This is a memo-boundary plus setup-transcription audit, not just a memo-read audit.

### 7. `W4-1` Should Not Be Over-Coupled To The Full Memo Set

Wave 4 code at `6406e46` is a narrow polish slice.

It should be audited primarily against:

- `WAVE-4-SETUP.md`
- `WAVE-4-POLISH-SPECS.md`

It should not be retroactively widened by later Wave 4B content-memo expectations.

### 8. `W4B-2` Needs A Conformity Dependency

Wave 4B runtime success does not prove memo compliance.

A candidate can pass tests and probes while still smuggling deferred capability work such as:

- `C-6`
- `C-10`
- `C-11`
- deferred `C-14`
- deferred `C-7`

Therefore:

- `W4B-1` must remain the conformity audit
- `W4B-2` must either run after `W4B-1` or return `CONTINGENT` until `W4B-1` clears

### 9. Exact Commit Pinning Must Replace Symbolic `HEAD`

The eventual prompts must pin exact commits.

Do not rely on symbolic `HEAD` in retrospective review prompts because:

- the handoff itself advanced the docs lineage from `91f97c2` to the pre-planning anchor `2e6d780`
- `CONTROL-PLANE-STATE.yaml` and `ACTIVE-HANDOFF.md` still use symbolic `HEAD` for docs reconcile references

## Refined Slice Set

The candidate slice count stays efficient at 12 slices, but four slices get stronger internal structure.

| Slice | Status vs candidate | Why |
|---|---|---|
| `CP-1` Control-plane authority audit | keep | Needed to validate authority order, lease state, hard stop, and docs-only quarantine |
| `CP-2` Controller checkpoint-chain and controller-code-packet join audit | expand | Needed to map every controller/docs checkpoint to the right code commit, packet set, boundary doc, and next action |
| `RP-1` Review-packet integrity meta-audit | strengthen | Must detect corruption, header drift, and cross-wave contamination |
| `W2B-1` Wave 2B lineage and closure audit | refine | Keep as one slice, but require separate lineage and closure sub-verdicts |
| `W3A-1` Wave 3A seam-freeze and Wave 3 setup contract audit | refine | Must audit both seam freeze and actual setup contract, not seam freeze alone |
| `W4D-1` Wave 4 memo-boundary and Wave 4B setup-transcription audit | refine | Must be per-memo and setup-transcription aware |
| `W3-1` Wave 3 runtime audit | keep | Still coherent as one slice if the prompt forces deliverable-level sub-verdicts |
| `W3B-1` Wave 3B control-path audit | refine | Keep as one slice, but require structural-contract and control-loop sub-verdicts |
| `W4-1` Wave 4 polish/runtime audit | keep | Narrow and coherent |
| `W4B-1` Wave 4B memo-to-code conformity audit | keep and strengthen | Must return per-slice conformity results |
| `W4B-2` Wave 4B runtime audit | keep with dependency guard | Runtime review is valid only after, or contingent upon, `W4B-1` |
| `X-1` Cross-wave regression and cascading invalidation audit | keep | Final synthesis guardrail |

## Ordering Decision

The best execution model is hybrid:

- strict trust gate first
- strict batch order for all structural prerequisites
- limited contingent mode only for later wave-local slices when a launcher deliberately overlaps sister reviews

In practice that means:

1. Batch 1 is a hard trust gate.
2. Nothing downstream launches unless Batch 1 clears.
3. Batches 2 through 5 should run in strict order.
4. Batch 6 may overlap `W4B-1` and `W4B-2`, but `W4B-2` must cap at `CONTINGENT` until `W4B-1` clears.
5. `X-1` waits for every prior slice.

## Program Risks The Refined Plan Explicitly Covers

- stale-doc drift between `91f97c2` and the pre-planning docs anchor `2e6d780`
- symbolic `HEAD` ambiguity in authority artifacts
- packet contamination in review scaffolds
- false confidence from runtime-green but memo-illegal Wave 4B work
- retroactive widening of Wave 4 polish using later Wave 4B memo intent
- loss of the blocked-parent recovery story in Wave 2B
- collapse of Wave 3B's structural and controller questions into one overly broad pass

## Bottom Line

The candidate program is directionally right, but it needs:

- a hard trust gate
- a stronger `CP-2`
- a stronger `RP-1`
- structured sub-verdicts inside the broadest slices
- a guarded dependency from `W4B-1` to `W4B-2`

With those changes, the audit program becomes launchable without becoming over-fragmented.
