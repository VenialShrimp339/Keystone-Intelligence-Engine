# Audit Synthesis Plan

*Date: 2026-04-12 | Scope: how to merge the eventual retrospective review-session outputs into one final program judgment*

---

## Purpose

The retrospective audit will produce many local slice reports.

Those reports should not be merged by simple majority or by raw finding count.

They need to be synthesized according to dependency order and invalidation scope.

This plan defines:

- what counts as a local finding
- what counts as a cascading invalidation
- the order in which the slice outputs should be merged
- what final outputs should be written after the review sessions finish

## Synthesis Order

Merge results in this order:

1. Batch 1 trust gate
2. Batch 2 boundary foundations
3. Wave 3
4. Wave 3B
5. Wave 4
6. Wave 4B conformity
7. Wave 4B runtime
8. cross-wave regression

Never synthesize later wave-local findings as if they outrank an earlier trust failure.

## Finding Types

### Local Finding

A local finding affects only the slice that discovered it.

Examples:

- a missing probe in `W4-1`
- a weak negative example in one Wave 4 memo
- an under-tested prompt change inside an otherwise legal Wave 4B slice

Default handling:

- keep the finding local
- do not automatically invalidate downstream waves
- downstream waves may still be `CLEARED` if the finding does not break their prerequisites

### Cascading Invalidation

A cascading invalidation is a finding that breaks trust in later slices because it corrupts a prerequisite.

Examples:

- a controller/docs checkpoint points at the wrong code commit
- a review packet is corrupted or cross-contaminated
- a Wave 3A seam contract was never actually frozen the way later wave audits assumed
- Wave 4B legality depends on a memo boundary that was mistranscribed into `WAVE-4B-SETUP.md`

Default handling:

- mark all dependent slices invalidated or at least untrustworthy
- do not bury the issue as a local note
- downstream synthesis must treat later `CLEARED` reports as superseded

## Cascade Rules

### Batch 1 Failures

If any of these slices are `BLOCKED` or `CONTINGENT`:

- `CP-1`
- `CP-2`
- `RP-1`

Then:

- do not trust any downstream slice result
- do not produce a final workstream clearance summary
- the program-level outcome is blocked at the trust layer

### Boundary Foundation Failures

If `W2B-1` fails:

- treat Waves 3, 3B, 4, and 4B as downstream-invalidated until re-reviewed against a repaired baseline story

If `W3A-1` fails:

- treat `W3-1`, `W3B-1`, `W4-1`, `W4B-1`, and `W4B-2` as invalidated because their legal boundary is untrusted

If `W4D-1` fails:

- treat `W4B-1` and `W4B-2` as invalidated
- do not retroactively invalidate `W4-1` unless the memo defect also proves `WAVE-4-SETUP.md` or `WAVE-4-POLISH-SPECS.md` were untrustworthy

### Wave Failures

If `W3-1` fails:

- `W3B-1`, `W4-1`, `W4B-1`, and `W4B-2` become invalidated downstream

If `W3B-1` fails:

- `W4-1`, `W4B-1`, and `W4B-2` become invalidated downstream

If `W4-1` fails:

- `W4B-1` and `W4B-2` become invalidated downstream

If `W4B-1` fails:

- `W4B-2` cannot clear

If `W4B-2` fails:

- only Wave 4B and the final cross-wave judgment are blocked

## Reconciliation Rules

### When Reviews Disagree

If two slice reports disagree materially:

1. trust the earlier prerequisite slice first
2. check whether the disagreement is actually a scope mismatch
3. classify the disagreement as one of:
   - metadata disagreement
   - boundary disagreement
   - runtime disagreement
4. resolve in synthesis without rewriting history

Do not erase a local finding just because a later slice did not rediscover it.

### When A Later Slice Clears On A Broken Premise

If a later slice returns `CLEARED`, but synthesis later determines its prerequisite was broken:

- keep the later slice report unchanged as a historical artifact
- mark it `superseded by prerequisite invalidation` in the synthesis outputs
- do not reinterpret it as true clearance

### When A Finding Is Real But Narrow

If a finding is real but does not break a prerequisite:

- record it in the master ledger
- leave downstream slices intact
- carry it forward as a residual risk, not a cascading invalidation

## Recommended Synthesis Outputs

After the eventual review sessions finish, write these files:

1. `audit/remediation/workstream-retro/synthesis/RETRO-AUDIT-MASTER-LEDGER.md`
2. `audit/remediation/workstream-retro/synthesis/RETRO-AUDIT-CASCADING-INVALIDATIONS.md`
3. `audit/remediation/workstream-retro/synthesis/RETRO-AUDIT-FINAL-SUMMARY.md`

## Master Ledger Schema

Each row in the master ledger should contain:

- `slice_id`
- `finding_id`
- `finding_type`
  - `local`
  - `cascading`
  - `residual`
- `artifact_family`
  - `authority`
  - `packet`
  - `boundary`
  - `runtime`
  - `cross-wave`
- `severity`
- `upstream_dependency`
- `downstream_impact`
- `evidence_paths`
- `synthesis_disposition`

## Final Summary Structure

The final summary should be written in this order:

1. program-level verdict
2. trust-gate outcome
3. boundary-foundation outcome
4. wave-local outcomes
5. cascading invalidations
6. residual non-blocking risks
7. exact list of slices that are trustworthy vs superseded

## Final Verdict Rule

The workstream may be described as retrospectively sound only if:

- every Batch 1 slice is `CLEARED`
- every prerequisite boundary slice is `CLEARED`
- every wave-local slice is `CLEARED`
- `X-1` is `CLEARED`

If any prerequisite slice is `BLOCKED` or `CONTINGENT`, the final summary must not describe the workstream as cleared.

## Bottom Line

The synthesis step is not a vote.

It is a dependency-aware merge that must let:

- trust failures override later local clears
- boundary failures invalidate dependent runtime claims
- narrow local findings remain local when they do not break prerequisites

That is the only way to preserve the logic of the original wave-by-wave remediation program while auditing it retrospectively.
