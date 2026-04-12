# Build Process: How to Build Without Repeating Our Mistakes

> Historical process guidance only. Do **not** use this file as the live remediation launcher. The active remediation process now comes from the control plane plus `AUTONOMOUS-REMEDIATION-PLAN-v4.md`.

*Created: 2026-04-11 | Status: Active*

---

## The Problem We're Solving

Every planning error in this project had the same root cause: proposing changes to code without reading the code first. Plans that "look right" fail at implementation when they conflict with frozen models, missing fields, incomplete file lists, or wrong wave ordering. External reviews (5.4 Pro, Codex) consistently caught these errors because they forced verification that the planning sessions skipped.

This document defines how we build from here.

---

## Immediate Next Steps

### Step 1: Current Phase 1D session revises FINAL-DECISIONS.md

The session has REVIEW-SYNTHESIS.md with 17 confirmed blockers and 6 revision sets. Tell it:

```
Revise FINAL-DECISIONS.md incorporating all 6 revision sets from REVIEW-SYNTHESIS.md. For each revision, READ THE ACTUAL CODE FILES before writing the change. Specifically:

1. Read models/research.py and confirm ResearchSpec is frozen before proposing how to handle pipeline_profile.
2. Read models/citations.py and confirm Citation is frozen before proposing how to handle merged_from_ids and content_hash rename.
3. Grep for "content_hash" across the entire codebase and list every file that references it.
4. Read confidence_builder.py and confirm how tier claims are constructed before proposing aggregated_claim_id changes.
5. Read finding_writer.py and confirm how claims are built before proposing claim_id changes.

For the enforcement matrix: fix the 5 contradictory cells identified in the Codex review. Add the "not applicable" vs "enforcement skip" distinction.

For the wave ordering: adopt the corrected order from REVIEW-SYNTHESIS.md (E before B).

Make new fields Optional with None defaults until producers are implemented. Do not make anything required before the code that populates it exists.

After revising, save as FINAL-DECISIONS-v2.md (not overwriting v1 for the audit trail).
```

### Step 2: Codex adversarial review of v2

After the revision, run `/codex:adversarial-review` in the same session, focused on:
- Frozen model handling
- Wave ordering dependencies
- Enforcement matrix consistency
- Field optionality

If clean on BLOCKERs: proceed to implementation.
If new BLOCKERs: revise again and re-review.

### Step 3: Implementation begins (fresh sessions)

Do NOT implement in the Phase 1D session. Its context is heavy with analysis artifacts. Start fresh sessions using the agent definitions.

---

## Build Process (Waves 1-4)

### Per-Wave Process

Each wave follows this exact process:

1. **Start a fresh Claude Code session** using the kie-implementer agent:
   ```
   cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine && claude --agent kie-implementer
   ```

2. **Give it a focused prompt** scoping to exactly one wave:
   ```
   Read audit/remediation/decisions/FINAL-DECISIONS-v2.md. Implement Wave [N] only.
   Read the specific decision sections for this wave before writing any code.
   Stop after the wave is complete and all tests pass.
   ```

3. **After the wave completes**, run Codex adversarial review in the SAME session:
   ```
   /codex:adversarial-review Focus on the Wave [N] changes. Check whether the implementation matches the approved design and whether any proposed invariants are actually enforced.
   ```

4. **Fix any Codex-identified issues** in the same session.

5. **Commit the wave.** Clean stopping point.

6. **Start a new session for the next wave.**

### Wave-Specific Details

**Wave 1A: Instance Lifecycle (Decision E)**
Must come first -- Decisions A and B depend on single-use components.
- Move component construction from Pipeline.__init__ to run_with_events()
- Add deliberation gather fallback
- Add subprocess cleanup try/finally
- Fix circuit breaker HALF_OPEN
- Scope: orchestrator.py, deliberation.py, llm_client.py, circuit_breaker.py

**Wave 1B: LLM Parsing Standard (Decision D)**
Can proceed after 1A or in parallel (no shared files except research_agent.py).
- Create src/keystone/llm/parsing.py with safe_llm_json and parse_llm_bool
- Replace all 12+ call sites
- Scope: new file + 12 modified files

**Wave 1C: Citation Identity Foundation (Decision A, part 1)**
Depends on 1A (single-use components) for clean per-run state.
- Engagement-unique citation IDs
- claim_id on FindingClaim (Optional until populated)
- CitationProcessorResult with canonicalized findings
- Alias map
- Scope: citations.py, research.py, research_agent.py, finding_writer.py, processor.py

**Wave 2A: Citation Identity Completion (Decision A, part 2)**
Depends on 1C.
- Provenance fields on aggregator and confidence map
- Deliberation consumes canonicalized findings + manifest
- Orchestrator filters confidence_map by task provenance
- Scope: aggregator.py, confidence_builder.py, deliberation.py, orchestrator.py, confidence.py

**Wave 2B: Enforcement Model (Decision B)**
Depends on 1A (single-use), 1C (canonical IDs), 2A (provenance filtering).
- GovernanceState and ProfileExecutionPolicy
- Pipeline profile persistence (set in SpecificationEngine, not orchestrator)
- Enforcement matrix implementation
- Task outcomes and renderability
- Scope: new governance/ package, orchestrator.py, spec_engine.py, evaluator.py

**Wave 3: Completeness (Decisions C + remaining items)**
Independent items. Agent teams could parallelize here.
- Deep research audit events (C)
- DAG execution scheduling
- Post-synthesis verification pass
- Provenance sidecar generation
- Research prompt wiring
- Scope: research_agent.py, orchestrator.py, new files

**Wave 4: Polish**
- Documentation fixes
- Schema alignment
- Dead code cleanup
- e2e test `or True` fix
- Research prompt integrity commandments
- Scope: .md files, test files, minor code cleanup

### Agent Teams for Wave 3

Wave 3 has genuinely independent items that can parallelize. Use agent teams:

```
Create an agent team for Wave 3. Spawn 3 teammates:
- Deep Research: implement Decision C audit events in research_agent.py and events.py
- Pipeline Completeness: implement DAG scheduling and post-synthesis verification in orchestrator.py
- Provenance: implement provenance sidecar writer and research prompt wiring

Have them coordinate through the shared task list. Each teammate runs tests after their changes.
```

Waves 1-2 should NOT use agent teams -- the files overlap too much and the changes depend on each other.

---

## Codex Integration Points

| When | What | Why |
|------|------|-----|
| After FINAL-DECISIONS-v2.md | `/codex:adversarial-review` focused on blockers | Catch remaining design errors before building |
| After each Wave | `/codex:adversarial-review` on the wave diff | Catch implementation errors before next wave |
| After Wave 4 (final) | `/codex:adversarial-review` full diff | Comprehensive final check |

## 5.4 Pro Integration Points

| When | What | Why |
|------|------|-----|
| Only if Wave 2B enforcement matrix changes significantly | Upload revised matrix for review | The matrix is the highest-risk design artifact |
| After Wave 4 | Optional final architecture review | Confirm the remediation achieved its goals |

---

## What NOT to Do

1. **Do not implement in the planning session.** Planning sessions accumulate analysis context that degrades implementation focus.
2. **Do not implement multiple waves in one session.** Each wave is a clean stopping point with external review.
3. **Do not skip Codex adversarial review between waves.** This is the enforcement mechanism. It's not optional.
4. **Do not redesign during implementation.** If the plan is wrong, stop and flag it. Return to a planner session.
5. **Do not batch test runs.** Test after EVERY individual change, not after the whole wave.
