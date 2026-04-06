# Audit Deepening: Closing the Gaps

Your initial orientation was strong. The project state map is correct, the cross-session integrity check was the right call, and the "Things to Watch" section identified the real risks. But the per-component audit was too shallow to actually serve its purpose, and there are a few concrete analytical gaps that need closing before we proceed.

This prompt explains what was inadequate, why it matters, and what to do about it. Internalize the reasoning here so you calibrate future audits correctly.

---

## What Was Inadequate and Why

### 1. The Per-Component Audit Was Summary, Not Audit

You gave each component a 2-3 sentence "SOLID" verdict. That's a summary of what each component does, not an audit of whether it does it correctly. An audit means: reading the implementation spec's acceptance criteria, reading the actual source code, and checking each criterion against the code. You didn't show this work for any component.

**Why this matters:** Jack has been running this project on autopilot through Cowork, which means nobody has actually verified that what was specified is what was built. The session logs say "all tests passing" but that only tells you the code doesn't crash, not that it implements the spec. You are the first set of eyes that can actually close this loop.

**The standard going forward:** When you audit a component, the output should be structured enough that Jack (or a future session) can look at it and see exactly which acceptance criteria passed, which are questionable, and which are untested. A blanket "SOLID" tells him nothing actionable.

### 2. The Spec Engine / Gateway Interface Was Not Verified

You noted that Component #5 (Spec Engine) depended on Component #4 (Gateway) and that #5 used a stub while #4 was built in parallel. But you didn't verify whether the stub matches the real interface. This was the highest-risk cross-session seam.

I've now checked: the Spec Engine's `task_generator.py` resolves tools via `_resolve_tools()` which uses string-based tool names (e.g., "exa_search", "brave_search"). The Gateway's `tool_registry.py` registers tools by string name. The template_registry.py hardcodes tool name strings in seed templates (e.g., "sec_filings", "financial_data_api", "exa_search"). The Gateway's `servers.py` registers 7 servers with specific tool names.

**What you need to verify:** Do the tool name strings used in the Spec Engine's seed templates and task generator actually match the tool name strings registered in the Gateway's server configs? If the Spec Engine assigns "sec_filings" but the Gateway registers it as "edgar_tools", the pipeline will silently fail at runtime (authorization check will reject the tool call). Read both files and cross-reference every tool name string.

### 3. L2 (Content Structuring) and L3 (Generation) Are Missing From Your Component Map

Your "NOT STARTED" list goes: #3a, #7, #8, #9, #10, #11. But the pipeline is L0 -> L1 -> CitProc -> L1.5 -> L2 -> L3 -> L4. Where are L2 and L3?

Read `audit/PHASE-1-IMPLEMENTATION-SPEC.md` carefully. The build order is: #1 through #4+HITL (parallel), then #5 -> #6 -> #7 -> #8 -> #9 -> #10 -> #11 (sequential). The MVP definition on lines 38-53 shows the minimal pipeline skips L2/L3 and goes straight from Deliberation to Evaluator to Markdown output. Component #11 (end-to-end pipeline test) produces "Markdown output" not formatted deliverables.

**What you need to determine:** Are L2/L3 explicitly deferred to Phase 2? Are they embedded within another component? Or are they a gap in the implementation spec? This matters because your recommended next steps assume a certain set of remaining work. If L2/L3 are Phase 2 deferrals, fine. If they're missing from the spec, that's a planning gap Jack needs to know about.

### 4. The datetime.utcnow() Issue Is More Than Cosmetic

You flagged 207 deprecation warnings and called it "trivial fix." The fix is trivial per-instance, but 207 warnings flooding the test output will mask real warnings and errors in future test runs as more components are built. This should be fixed before building #7, not deferred indefinitely. Include it in your recommended immediate actions.

### 5. docs/ARCHITECTURE.md Staleness Is a Handoff Risk

You noted it's stale. The reason this matters: ARCHITECTURE.md is referenced in CLAUDE.md's orientation section ("Read `docs/ARCHITECTURE.md` for code architecture, module map, dependency rules, coherence check"). Every new Claude Code session reads it. If it describes files that don't exist and omits files that do, new sessions start with a wrong mental model. This should also be fixed before the next build session, not deferred.

---

## Tasks: Complete These Before Proceeding

### Task 1: Spec Engine / Gateway Tool Name Cross-Reference

Read these two files in full:
- `src/keystone/specification/template_registry.py` (all seed templates, every `tools=` field)
- `src/keystone/gateway/servers.py` (all registered server configs, every tool name)

Also check:
- `src/keystone/specification/task_generator.py` lines 155-190 (`_resolve_tools` fallback logic)

Produce a two-column table: tool names used by Spec Engine vs tool names registered in Gateway. Flag any mismatches. If there are mismatches, this is the highest-priority fix before building #7 (Research Agents), because #7 is the first component where tools are actually called through the gateway.

### Task 2: Per-Component Acceptance Criteria Audit

For each of the five overnight build components (#4, #6, #3b, #5, #HITL), do the following:

1. Read the component's section in `audit/PHASE-1-IMPLEMENTATION-SPEC.md` (acceptance criteria are listed explicitly for each)
2. Read the actual source code for the component
3. For each acceptance criterion, give one of three verdicts:
   - **MET**: Code implements this and tests verify it. Cite the specific test or code path.
   - **UNTESTED**: Code appears to implement this but no test verifies it.
   - **UNMET**: Code does not implement this, or implements it incorrectly.

This is the work the initial audit should have done. Don't need prose summaries of what each component does (you already gave those). Need the specific criterion-by-criterion check.

**Important:** Components #1 and #2 were from the earlier Phase 1A batch, not the overnight batch. If you have bandwidth, audit those too. If not, at minimum confirm that the TYPE_CHECKING bug that was found in both was actually fixed in both (Session 1A-1 and 1A-2 both noted this bug; confirm both fixes landed).

### Task 3: L2/L3 Pipeline Layer Resolution

Read:
- `audit/PHASE-1-IMPLEMENTATION-SPEC.md` (the full MVP definition, lines 38-53, and the "Done" Criteria section at the end)
- `CAPSTONE-PLAN-v2.md` Sections on L2 and L3 (search for "Content Structuring" and "Generation")

Answer: Are L2 and L3 explicitly scoped for Phase 1? Phase 2? Split across phases? Not addressed? This determines whether the remaining work is 5 components or 7.

### Task 4: Fix datetime.utcnow() Warnings

Search all source files under `src/keystone/` for `datetime.utcnow()` and `datetime.now()` without timezone. Replace with `datetime.now(UTC)` (import UTC from datetime). Run the test suite afterward and confirm the 207 warnings drop to near-zero.

### Task 5: Regenerate docs/ARCHITECTURE.md

Read the current `docs/ARCHITECTURE.md`. Then generate an accurate one from the actual codebase state. Should include:
- Actual directory tree (not the pre-build one)
- Module responsibilities for every module under src/keystone/
- The interface table (which Protocol each component satisfies)
- Dependency rules (what can import what)

This is a file that every future session reads on startup, so accuracy here has compounding value.

### Task 6: Record This Session's Work

After completing the above:
1. Produce `audit/OVERNIGHT-AUDIT-RESULTS.md` with all findings from Tasks 1-3
2. Update `CURRENT-STATE.md` to reflect any issues found
3. Append this session's entry to `SESSION-LOG.md`

---

## Calibration Note for Future Tasks

The initial orientation prioritized breadth over depth: you read many files and produced a correct high-level map. That was valuable and the right instinct for the first pass. But the specific task was an audit, and an audit requires depth on each item, not just breadth across items. The failure mode to watch for: compressing detailed verification work into summary judgments because it "looks right." The whole point of the audit is that things can look right and be wrong, especially when multiple independent agents built code in parallel without seeing each other's work.

Going forward: when a task requires verification, show the work. When a task requires orientation, the summary approach is fine. Match the methodology to the task type.
