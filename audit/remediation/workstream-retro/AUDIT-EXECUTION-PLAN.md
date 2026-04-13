# Audit Execution Plan

*Date: 2026-04-12 | Scope: launch plan for the retrospective audit of the autonomous remediation workstream*

---

## Program Mode

Use a hybrid execution model:

- strict trust gate first
- strict batch order for structural prerequisites
- contingent mode only for later wave-local overlap, and only where explicitly allowed

Default launch mode is strict.

## Freeze Pins

- Pre-planning docs anchor commit: `2e6d780`
- Last cleared-state docs checkpoint: `91f97c2`
- Current planning-package docs commit at reconciliation start: `c5dbd05`
- Controller-promoted retrospective lineage manifest: `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- Controller-promoted retrospective review ledger: `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- Current planning-package lineage after the pre-planning anchor:
  `2e6d780 -> c5dbd05`
- Last cleared code commit: `65a612d`
- Code lineage:
  `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- Controller/docs lineage:
  `35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2 -> 2e6d780`

Historical interpretation note:

- `65074ca` lands `WAVE-3A-SEAM-FREEZE.md`, but that commit is internally stale because its live control-plane text still says to create that doc.
- `198ab92` is the later controller reconcile that first promotes the seam freeze into active `wave-3 / setup`.
- Historical symbolic `HEAD` references across `35a8a29 -> 2e6d780` are replaced for retrospective audit use by the exact git-derived pins recorded in `RETROSPECTIVE-LINEAGE-MANIFEST.yaml`.

## Program Rules

1. Review only. No implementation, no Wave 5 work, no controller-state mutation as part of the retrospective audits.
2. Review only committed snapshots. Do not trust dirty `HEAD` or the controller/docs branch as code truth.
3. Treat outputs under `audit/remediation/workstream-retro/` as planning or retrospective sidecars unless a later controller reconcile promotes them.
4. Use the controller-promoted retrospective review ledger to determine the current authoritative status of prior review slices for prerequisite checks.
5. Do not require the reviewed historical snapshot to contain later review sidecars when checking prerequisites.
6. Every review session must use GPT-5.4 with xhigh fast for any spawned subagent and record any deviation.
7. Every review session must return a top-line verdict: `BLOCKED`, `CLEARED`, or `CONTINGENT`.

## Verdict Semantics

### `CLEARED`

Use only when:

- the slice's inputs were authoritative and pinned
- all slice-specific checks passed
- all required upstream prerequisites were already `CLEARED` in the current authoritative review-status layer

### `BLOCKED`

Use when:

- the slice finds a real blocker
- a required authority artifact is missing
- authority inputs are contradictory
- packet integrity failure makes the slice untrustworthy

Any `BLOCKED` slice blocks every dependent slice.

### `CONTINGENT`

Use when:

- no local blocker was found
- but an upstream prerequisite is unresolved, untrusted, or was launched out of order

`CONTINGENT` is stop-equivalent, not go-equivalent.

Do not treat `CONTINGENT` as effective clearance.

## Output Root

Eventual retrospective review sessions should write reports under:

`audit/remediation/workstream-retro/reviews/`

These review reports are not controller authority artifacts by default.

They become current prerequisite authority only when a later controller reconcile promotes them into the retrospective review ledger or a later controller-approved successor layer.

## Batch Structure

### Batch 1: Trust Gate

Run in parallel:

1. `CP-1` Control-plane authority audit
2. `CP-2` Controller checkpoint-chain and controller-code-packet join audit
3. `RP-1` Review-packet integrity meta-audit

Stop rule:

- If any Batch 1 slice is `BLOCKED` or `CONTINGENT`, stop the entire program.

Rationale:

- Batch 1 decides whether downstream inputs are safe to trust.

### Batch 2: Boundary Foundations

Run in parallel, but only after `CP-1`, `CP-2`, and `RP-1` are currently `CLEARED` in the controller-promoted retrospective review ledger:

1. `W2B-1` Wave 2B lineage and closure audit
2. `W3A-1` Wave 3A seam-freeze and Wave 3 setup contract audit
3. `W4D-1` Wave 4 memo-boundary and Wave 4B setup-transcription audit

Stop rules:

- If `W2B-1` is `BLOCKED`, stop `W3-1`, `W3B-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1`.
- If `W3A-1` is `BLOCKED`, stop `W3-1`, `W3B-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1`.
- If `W4D-1` is `BLOCKED`, stop `W4B-1`, `W4B-2`, and `X-1`.

Notes:

- `W2B-1` must return two sub-verdicts:
  - `blocked-parent lineage`
  - `cleared runtime closure`
- `W4D-1` must return per-memo sub-verdicts plus one setup-transcription verdict.

### Batch 3: Wave 3 Runtime

Run only after `W2B-1` and `W3A-1` are currently `CLEARED`:

1. `W3-1` Wave 3 runtime audit

Stop rule:

- If `W3-1` is `BLOCKED`, stop `W3B-1`, `W4-1`, `W4B-1`, `W4B-2`, and `X-1`.

### Batch 4: Wave 3B Control Path

Run only after `W3-1` is currently `CLEARED`:

1. `W3B-1` Wave 3B control-path audit

Stop rule:

- If `W3B-1` is `BLOCKED`, stop `W4-1`, `W4B-1`, `W4B-2`, and `X-1`.

Notes:

- `W3B-1` must return two sub-verdicts:
  - `outline-render-state contract`
  - `single-controller iterative-loop authority`

### Batch 5: Wave 4 Polish

Run only after `W3B-1` is currently `CLEARED`:

1. `W4-1` Wave 4 polish/runtime audit

Stop rule:

- If `W4-1` is `BLOCKED`, stop `W4B-1`, `W4B-2`, and `X-1`.

### Batch 6: Wave 4B

Default order:

1. `W4B-1` Wave 4B memo-to-code conformity audit
2. `W4B-2` Wave 4B runtime audit

Prerequisites:

- `W4-1` must be currently `CLEARED`
- `W4D-1` must be currently `CLEARED`

Allowed contingent overlap:

- If a launcher deliberately runs `W4B-1` and `W4B-2` in parallel, `W4B-2` may not return `CLEARED` until `W4B-1` has already returned `CLEARED`.
- In that overlap mode, the maximum allowed top-line verdict for `W4B-2` is `CONTINGENT` until `W4B-1` clears.

Stop rules:

- If `W4B-1` is `BLOCKED`, stop `W4B-2` and `X-1`.
- If `W4B-2` is `BLOCKED`, stop `X-1`.

Notes:

- `W4B-1` must return per-slice conformity sub-verdicts for:
  - `D-2`
  - `core prompt quality`
  - `sprint-contract / contradiction`
  - `template / routing`
  - `C-15`

### Batch 7: Cross-Wave Synthesis Guard

Run only after every prior slice is currently `CLEARED`:

1. `X-1` Cross-wave regression and cascading invalidation audit

This is the final program-level review.

## Slice Table

| Slice | Batch | Direct prerequisites | Output path |
|---|---|---|---|
| `CP-1` | 1 | none | `audit/remediation/workstream-retro/reviews/CP-1-control-plane-authority-audit.md` |
| `CP-2` | 1 | none | `audit/remediation/workstream-retro/reviews/CP-2-controller-lineage-join-audit.md` |
| `RP-1` | 1 | none | `audit/remediation/workstream-retro/reviews/RP-1-review-packet-integrity-audit.md` |
| `W2B-1` | 2 | Batch 1 cleared in review ledger | `audit/remediation/workstream-retro/reviews/W2B-1-wave-2b-lineage-and-closure-audit.md` |
| `W3A-1` | 2 | Batch 1 cleared in review ledger | `audit/remediation/workstream-retro/reviews/W3A-1-wave-3a-seam-and-setup-audit.md` |
| `W4D-1` | 2 | Batch 1 cleared in review ledger | `audit/remediation/workstream-retro/reviews/W4D-1-wave-4-memo-boundary-audit.md` |
| `W3-1` | 3 | `W2B-1`, `W3A-1` currently cleared | `audit/remediation/workstream-retro/reviews/W3-1-wave-3-runtime-audit.md` |
| `W3B-1` | 4 | `W3-1` currently cleared | `audit/remediation/workstream-retro/reviews/W3B-1-wave-3b-control-path-audit.md` |
| `W4-1` | 5 | `W3B-1` currently cleared | `audit/remediation/workstream-retro/reviews/W4-1-wave-4-polish-audit.md` |
| `W4B-1` | 6 | `W4-1`, `W4D-1` currently cleared | `audit/remediation/workstream-retro/reviews/W4B-1-wave-4b-conformity-audit.md` |
| `W4B-2` | 6 | `W4-1`, `W4D-1` currently cleared; `W4B-1` currently cleared for unconditional `CLEARED` | `audit/remediation/workstream-retro/reviews/W4B-2-wave-4b-runtime-audit.md` |
| `X-1` | 7 | all prior slices currently cleared | `audit/remediation/workstream-retro/reviews/X-1-cross-wave-regression-audit.md` |

## Required Launch Discipline

Every eventual review session must:

1. read `graphify-out/GRAPH_REPORT.md` first if it exists in the reviewed commit snapshot; if absent, record the absence and continue
2. read `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml` before deriving any historical docs/code join from raw checkpoint text
3. read `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml` before asserting any prior review slice is currently `CLEARED`
4. do not require the reviewed historical snapshot to contain later review sidecars when checking prerequisites
5. pin the exact baseline, parent, and target commits in the report header
6. state whether code truth came from a clean worktree or detached review checkout
7. state that the dirty main workspace was not trusted as code truth
8. list the exact authority docs read
9. distinguish:
   - packet integrity
   - scope or boundary conformity
   - runtime correctness
10. end with an explicit top-line verdict plus residual risks

`graphify-out/GRAPH_REPORT.md` is advisory context only, not a required authority artifact. Its absence alone must not block `RP-1`.

## No-Go Conditions For The Program

The program stops immediately if any of the following are found:

- contradictory authority order
- unpinned or ambiguous baseline/target mapping
- corrupted or cross-contaminated packet artifacts
- stale-doc divergence that changes the apparent state transition
- a blocked earlier wave that invalidates a later baseline
- a memo-transcription failure that makes the Wave 4B legal boundary uncertain

## Bottom Line

Launch order should be:

1. trust gate
2. boundary foundations
3. Wave 3
4. Wave 3B
5. Wave 4
6. Wave 4B conformity, then Wave 4B runtime
7. cross-wave regression synthesis

That gives enough ordering to catch cascading invalidity while preserving limited late-stage overlap where it is safe.
