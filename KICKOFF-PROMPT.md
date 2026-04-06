# Kickoff Prompts for Claude Code Sessions

## Session 1 (COMPLETED): Research Synthesis
Analyzed 16 research reports across 4 parallel threads, produced unified synthesis, updated CAPSTONE-PLAN-v2.md with 17 changes (1051 → 1294 lines), wrote changelog.

---

## Session 2: Plan Audit + Implementation Spec

Copy everything below the line into your Claude Code session.

---

The previous session analyzed 16 deep research reports and made 17 changes to CAPSTONE-PLAN-v2.md (documented in synthesis/PLAN-CHANGELOG.md). Before we build anything, we need to verify the plan is solid and produce an implementation spec.

Read CAPSTONE-PLAN-v2.md fully. Read synthesis/PLAN-CHANGELOG.md and synthesis/UNIFIED-SYNTHESIS.md. Read the skills in .claude/skills/ for methodology context.

Execute the following phases sequentially. Do not stop for input unless you encounter a genuine ambiguity that would change the direction of work. Keep going until all phases are complete.

## Phase 1: Internal Consistency Audit

The plan grew by 243 lines across 17 changes. Verify it's internally consistent:

1. **Cross-reference scan.** Find every reference to concepts that changed: "eight-dimension" should now be "ten-dimension" everywhere. "Rejection Library" should be "Observation Library" everywhere. "Structured debate" in L1.5 should reflect the redesign to independent parallel analysis + structured aggregation. The architecture diagram should match the prose. All section numbers should still be correct. All handoff contract tables should reflect the new CitationProcessor stage.

2. **Evidence spot-check.** For the 5 highest-impact changes (deliberation redesign, 5-layer evaluator stack, Observation Library expansion, agent isolation strengthening, orchestration architecture), go back to the actual research reports cited and verify the synthesis accurately represents what those reports found. If a synthesis claim overstates or misrepresents a report finding, flag it.

3. **Architectural coherence.** Do the 17 changes work together as a system? Does the CitationProcessor stage interact correctly with the redesigned Deliberation phase? Does the 5-layer evaluator stack account for the expanded 10-dimension rubric? Does the Observation Library design account for the saturation-breaking mechanisms?

Write `audit/PLAN-AUDIT.md` with findings: issues found, corrections needed, and a pass/fail verdict on whether the plan is build-ready. Make all necessary corrections directly to CAPSTONE-PLAN-v2.md.

## Phase 2: Gap Triage

synthesis/UNIFIED-SYNTHESIS.md identifies 8 remaining gaps. For each gap:
- **Blocks Phase 1?** Can we start building core pipeline components without resolving this?
- **Time-sensitive?** Does this have an external deadline?
- **Resolvable now?** Can we answer this with available information, or does it require external input (e.g., actual Keystone deliverables, API access negotiations)?

For any gap that blocks Phase 1 and is resolvable now, resolve it and update the plan. For gaps requiring external input, document exactly what's needed and from whom.

Write the triage results to `audit/GAP-TRIAGE.md`.

## Phase 3: Phase 1 Implementation Spec

Using the implementation priority table from synthesis/UNIFIED-SYNTHESIS.md (items #1-#11), produce a technical implementation spec for Phase 1 only. For each component:

1. **What to build:** Concrete deliverables (files, directories, schemas, configs)
2. **Input/output contracts:** What data flows in, what comes out, in what format (actual schema sketches, not prose descriptions)
3. **Acceptance criteria:** How we know it works. Specific, testable conditions.
4. **Dependencies:** What must exist before this component can be built. Map the build order.
5. **Estimated scope:** S/M/L/XL with brief justification
6. **First test:** The simplest possible end-to-end test that proves the component works

Also produce:
- **Minimum viable pipeline definition:** The smallest subset of Phase 1 components that produces a working end-to-end research flow (even if low quality). This is what we build and test first.
- **Build order:** The exact sequence of components to implement, accounting for dependencies
- **"Done" criteria for Phase 1:** What does it mean for Phase 1 to be complete?

Write to `audit/PHASE-1-IMPLEMENTATION-SPEC.md`.

## Phase 4: Session Context Document

Write `audit/SESSION-CONTEXT.md` -- a concise document (under 100 lines) that any future Claude Code session can read to understand: what's been done, what decisions were made and why, what's ready to build, and what the build order is. This replaces reading the full synthesis for future sessions. Think of it as the "briefing doc" for the build phase.

Keep going through all 4 phases without stopping.
