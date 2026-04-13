# Lane Choice Rationale

Date: 2026-04-13

## Decision

The next forward code lane should be Retrieval MVP Lane D only, but only after the corrected setup package is later promoted through a control-plane reconcile.

That means:

- the immediate next work item in this session is the docs-only setup-package correction pass
- the first forward runtime lane after a later promotion session is the retrieval fetch lane
- no broader runtime lane should open first

## Why This Is The Right First Lane

1. The control plane says the retrospective audit program is complete and the only remaining forward blocker is the missing post-Wave-4B authority/setup artifact.
2. The retrieval workstream already names Lane D as the first recommended runtime lane and keeps Lane E and Lane F procedurally blocked behind a narrow controller unlock.
3. Lane D closes the biggest honest gap between `65a612d` and the Retrieval MVP target:
   - governed discovery exists
   - governed full-document fetch does not
4. Lane D is the narrowest runtime slice that can improve retrieval truth without reopening the parser, L1, evaluator, or UI surfaces.
5. Graphify reinforces that shape:
   - `MCP Gateway` is a core god node, so its write surface must be fenced tightly
   - shared research models are core abstractions, so any semantic changes there are too broad for Lane D
   - nothing in the current graph suggests parser, evaluator, or orchestration work should be bundled into the first fetch unlock

## Why Another Design Memo Does Not Need To Come Before Lane D

The retrieval packet already contains the contract, benchmark, scoring, provenance, and governance docs named by the retrieval unlock memo and checklist:

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

What was missing was not another design memo. What was missing was controller-grade packaging that:

- freezes one exact forward lane
- fences indirect scope creep through cross-cutting files
- turns narrative gates into explicit gate artifacts with verdicts
- makes backend-reality proof load-bearing instead of aspirational

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

## Authority And Staleness Fence

This package does not lift the hard stop by narrative intent. It only becomes promotable when its required gate artifacts exist and remain `CLEARED`, and a later controller reconcile explicitly adopts it into the live control plane.

Subordinate retrieval docs may still contain historical or stale status prose. Those lines are fenced here:

- they are non-authoritative for forward-lane promotion
- they may not be used as proof that the hard stop is lifted
- only `CONTROL-PLANE-STATE.yaml`, `ACTIVE-HANDOFF.md`, and the required next-wave gate artifacts in this package may be used as live authority for promotion decisions

## Final Judgment

- Immediate next checkpoint: this corrected docs-only setup package
- First forward lane after later promotion: Retrieval MVP Lane D fetch
- Additional broader runtime lane before Lane D: no
- Parser Lane E, L1 integration Lane F, UI work, benchmark acceptance, Wave 5, and calibration remain blocked
