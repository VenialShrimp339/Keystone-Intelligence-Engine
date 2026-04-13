# Lane Choice Rationale

Date: 2026-04-13

## Decision

The next forward code lane should be Retrieval MVP Lane D only, but only after the missing docs/setup checkpoint is promoted.

That means:

- the immediate next work item is the setup artifact in this package
- the first forward runtime lane after promotion is the retrieval fetch lane
- no broader runtime lane should open first

## Why This Is The Right First Lane

1. The control plane says the retrospective audit program is complete and the only remaining forward blocker is the missing post-Wave-4B authority/setup artifact.
2. The retrieval workstream already names Lane D as the first recommended runtime lane and keeps Lane E and Lane F procedurally blocked behind a narrow controller unlock.
3. Lane D closes the biggest honest gap between `65a612d` and the Retrieval MVP target:
   - governed discovery exists
   - governed full-document fetch does not
4. Lane D is the narrowest runtime slice that can improve retrieval truth without reopening the parser, L1, evaluator, or UI surfaces.
5. Graphify reinforces that shape:
   - `MCP Gateway` is a core god node
   - gateway audit and `SimpleMCPClient` form a bounded seam
   - nothing in the current graph suggests parser, evaluator, or orchestration work should be bundled into the first fetch unlock

## Why Another Docs Checkpoint Does Not Need To Come Before Lane D

The only remaining docs/setup checkpoint is the one created in this package.

The retrieval packet already contains the required contract, benchmark, scoring, provenance, and governance documents named by the retrieval unlock memo and checklist:

- `CURRENT-RETRIEVAL-VS-TARGET.md`
- `MVP-RETRIEVAL-REQUIREMENTS.md`
- `ARCHITECTURE-DECISIONS.md`
- `RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
- `RETRIEVAL-MVP-SEAM-CONTRACT.md`
- `RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`
- `BENCHMARK-TASK-PACK-SCHEMA.md`
- `REPLAY-ADAPTER-SPEC.md`
- `REPLAY-SERVICE-CONTRACT-NOTE.md`
- `ARTIFACT-SCHEMA-DELTA-MEMO.md`
- `MANUAL-DR-PARALLEL-PROMPTBOOK.md`
- `HUMAN-SCORING-WORKSHEET.md`
- `SCOREBOARD-SPEC.md`
- `PROVENANCE-AUDIT-SPEC.md`
- `ACCEPTANCE-MATH-ADDENDUM.md`
- `ACCEPTANCE-RUN-CHECKLIST.md`

What was missing was not another design memo. What was missing was the controller-grade packaging that freezes one exact forward lane.

## Why Not Wave 5, Parser, L1, Or UI

### Not Wave 5 or calibration

- The control plane explicitly says not to start Wave 5 or calibration.
- Naming this setup as Wave 5 would imply a broader advancement than current authority supports.

### Not parser Lane E

- Parser work widens the lane from fetch transport into deterministic document interpretation.
- The retrieval package itself treats Lane E as a later seam.

### Not L1 integration Lane F

- L1 integration would reopen research-agent, evidence-bundle, and citation-anchoring seams.
- That is materially broader than the minimum lane needed to close the fetch gap.

### Not UI implementation

- The UI handoff explicitly says UI runtime work stays blocked until retrieval seams lock.

## Naming Rationale

The control plane does not pin an authoritative filename for the missing setup checkpoint.

This package therefore uses:

- filename: `NEXT-WAVE-SETUP-ARTIFACT.md`
- title: `Post-Wave-4B Retrieval Fetch Setup Artifact`

That choice is deliberate:

- it is truthful to the control-plane wording
- it avoids prematurely implying a true Wave 5 authority state
- it makes the permitted lane explicit in the title itself

## Authority Nuance

This package makes the hard stop satisfiable in substance because the missing artifact now exists.

This package does not by itself make the lane formally open, because the core control-plane authority docs remain unchanged by instruction.

The required follow-on action is a narrow controller reconcile that promotes this package into the live control plane without broadening scope.

## Coherence Note

`audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md` still contains an older sentence referring to retrospective `W4-1` as `CONTINGENT`.

That sentence is stale relative to the current authoritative control plane and retrospective review ledger, but it does not change the lane decision because:

- the memo is explicitly subordinate to the control plane
- its forward recommendation still points to the same narrow fetch lane
- the current hard stop is about missing setup authority, not unresolved retrospective review

## Final Judgment

- Immediate next checkpoint: this docs-only setup artifact
- First forward lane after promotion: Retrieval MVP Lane D fetch
- Additional docs/setup checkpoint before Lane D: no, beyond promotion of this package itself
- Broader forward runtime lane before Lane D: no
