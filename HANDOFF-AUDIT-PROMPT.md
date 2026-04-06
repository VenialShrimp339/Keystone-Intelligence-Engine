# Claude Code Handoff: Overnight Session Audit

## Your Identity and Task

You are picking up the Keystone Intelligence Engine project after a Cowork planning session that ran for multiple days (with many context compactions). Five parallel Claude Code build sessions ran overnight. Your job: **audit every overnight session's output before the project moves forward.** Do not blindly trust any of it.

## PHASE 0: CONTEXT LOADING (mandatory, read in this order)

Read these files before doing anything else:

1. `CLAUDE.md` — Auto-loaded. Project overview, pipeline reference, working rules, communication standards.
2. `CURRENT-STATE.md` — Living snapshot. Components #1, #2, #3b, #4, #5, #6, and HITL are marked complete. Component #3a (Source Discovery) is the next build. Component #7 (Research Agents) is unblocked.
3. `JACK-ARCHITECTURAL-DIRECTIVES.md` — **AUTHORITATIVE.** 14 design decisions from Jack that are NOT in the plan docs. Every architectural choice must be cross-checked against these. Pay special attention to Directive 5 (correct architecture at reduced feature depth), Directive 13 (Phase 1/Phase 2 staging), and Directive 14 (Goldman-grade quality, real product not class project).
4. `SESSION-LOG.md` — Full chronological history. The overnight sessions are the last 4-5 entries. Each entry lists files created, files modified, key decisions, test results, and handoff notes.
5. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — The build spec each session was working from. Cross-reference what was built against what was specified.

For deeper architectural context (read sections as needed, not cover-to-cover):
- `CAPSTONE-PLAN-v2.md` — Source of truth for all architecture (175KB, 48 research-backed changes applied in Session 12)
- `OVERNIGHT-SESSIONS.md` — The exact prompts given to the overnight sessions
- `PHASE-1A-BUILDER-SESSIONS.md` — The exact prompts given to the earlier Phase 1A sessions
- `NEXT-WAVE-PROMPTS.md` — The evaluator session prompt

## CRITICAL CONTEXT NOT IN ANY FILE

These are things the Cowork session knows from its (compacted) context that aren't written down anywhere. Internalize these:

### 1. Cross-Session Interference Risk
The overnight sessions ran in parallel on the same codebase. Each session was told which files it "owned" and told not to modify files outside its scope. But there is NO guarantee they followed this perfectly. Specific risks:
- **contracts.py and events.py** were designated "append-only shared files." Multiple sessions may have modified them. Check for conflicts, duplicates, or incompatible changes.
- **pyproject.toml** — Only Session 1A-3 (HITL) was authorized to add dependencies. Check if other sessions modified it.
- **models/__init__.py** — Multiple sessions added re-exports. Check for conflicts.
- **Implicit interface assumptions** — Session 1A-6 (Spec Engine #5) depended on Session 1A-4 (Gateway #4) for the ToolRegistry, but #4 was built in parallel. The Spec Engine was told to use a stub. Verify the stub matches the real #4 interface.

### 2. Python Environment Trap
The sandbox system Python is 3.14. The project targets 3.11-3.12. This has caused problems in multiple sessions:
- Full `pip install -e ".[dev]"` fails on 3.14 due to dependency conflicts (brave-search requires httpx<0.26, pyproject.toml requires httpx>=0.27)
- Some sessions may have only tested with partial installs
- Do NOT trust "all tests passing" claims until you verify the test environment is sound

### 3. Known Unfixed Issues (from Session 9 and subsequent sessions)
- `ruff format` style differences across model files (cosmetic, pre-existing from Session 6)
- `agents.py` line 14 has a runtime import pattern without `# noqa: TC001` for consistency
- `pyproject.toml` dependency conflicts need resolution on Python 3.11/3.12 (brave-search httpx pin vs our httpx pin)
- Some sessions noted pre-existing test failures in other modules (e.g., Session 1A-2 noted TYPE_CHECKING failures in research.py, which Session 1A-1 later fixed — but order of completion is unknown)

### 4. Trust Calibration
Jack's standard: **detection over hope.** Do not assume outputs are correct because a session reported "all tests passing." Verify:
- Do the tests actually test the right things, or are they trivial?
- Do the implementations match the PHASE-1-IMPLEMENTATION-SPEC.md acceptance criteria?
- Are there code paths that look correct on the surface but fail under edge cases?
- Did any session take shortcuts that violate Directive 5 (correct architecture) or Directive 13 (Phase 1/Phase 2 staging)?
- Did any session gold-plate features that should be Phase 2?

### 5. The Evaluator Is the Most Important Component
CAPSTONE-PLAN-v2.md and Jack's directives both state: "Evaluation > Generation." The Evaluator (Component #6, built in Session 8) deserves the most thorough audit. It has 77 tests, 14 prompt templates, and 9 source modules. Verify the geometric mean math, the Tier 1/Tier 2 gating logic, and the weight normalization.

## PHASE 1: SEQUENTIAL AUDIT OF OVERNIGHT SESSIONS

Audit each session one at a time. For each, produce a structured verdict. Do NOT proceed to the next session until the current one is fully audited.

### Audit Template (use for each session):

```
## Session [X]: Component #[N] — [Name]
### 1. Spec Fidelity
- Read the relevant section of PHASE-1-IMPLEMENTATION-SPEC.md
- Compare acceptance criteria vs what was actually built
- Flag anything missing, anything extra (gold-plating), anything that diverges

### 2. Code Quality
- Read every source file the session created
- Check: Pydantic v2 patterns correct? Protocols used consistently? Error handling present?
- Check: Does the code follow the patterns established in the foundation models (src/keystone/models/)?
- Check: Are there any imports from modules the session wasn't supposed to touch?

### 3. Test Quality
- Read the test files
- Are tests testing behavior or just testing that code runs without crashing?
- Are edge cases covered?
- Run the tests if possible (note: Python 3.14 environment may cause issues)

### 4. Interface Compatibility
- Does this component's output match what downstream components expect?
- Does this component's input match what upstream components provide?
- Check contracts.py — does the component satisfy its Protocol?

### 5. Directive Compliance
- Cross-reference against JACK-ARCHITECTURAL-DIRECTIVES.md
- Especially: Directive 5 (correct architecture), Directive 9 (retry + dead-letter),
  Directive 11 (configurable depth), Directive 13 (Phase 1 staging), Directive 14 (quality)

### 6. Verdict
- SOLID / NEEDS FIXES / NEEDS REWORK
- If NEEDS FIXES: list specific issues with file paths and line numbers
- If NEEDS REWORK: explain why and what the correct approach is
```

### Audit Order (recommended):

1. **Component #4 (MCP Gateway)** — Session 1A-4. Other components depend on it. 7 source modules, 75 tests. Check the ToolRegistry interface that #5 stubs against.
2. **Component #6 (Evaluator)** — Session 8. Most critical component. 9 modules, 14 prompts, 77 tests. Verify math, gating logic, weight normalization.
3. **Component #3b (Knowledge Accumulation)** — Session 1A-5. Karpathy wiki pattern. 6 modules, 45 tests. Check WikiStore Protocol and filesystem operations.
4. **Component #5 (Specification Engine)** — Session 1A-6. 10 modules, 9 prompts, 58 tests. Check the 10-step pipeline, stub wiring to real #4, HITL gate integration.
5. **Component #HITL** — Session 14/1A-3. If this was part of the overnight batch. 7 modules, 42 tests. Check state machine correctness, API schema validation.

If Components #1 and #2 were part of the overnight batch rather than the earlier Phase 1A batch, audit those too:
- **Component #1 (RESEARCH.md Spec Format)** — Session 1A-1. DAG validation, schema samples, engagement types.
- **Component #2 (Citation Data Model)** — Session 1A-2. Content hashing, dedup, URL checking.

## PHASE 2: CROSS-SESSION INTEGRATION CHECK

After auditing each session individually, check for cross-cutting issues:

1. **contracts.py consistency** — Read the full file. Are all Protocols internally consistent? Do the components actually satisfy their Protocols?
2. **events.py consistency** — Read the full file. Are event types correctly in the AnyPipelineEvent union? Any duplicates?
3. **Import graph** — Check that no circular imports exist across the new modules.
4. **Shared model compatibility** — Components #5 and #1 both touch research.py/tasks.py. Components #2 and #3b both use citation hashing. Verify no conflicts.
5. **Test suite health** — Run `pytest tests/` and report the full results. If tests fail, categorize: (a) real bugs, (b) environment issues (3.14 vs 3.12), (c) cross-session conflicts.

## PHASE 3: SYNTHESIS AND NEXT STEPS

After both audit phases, produce:

1. **AUDIT-RESULTS.md** — One file with all session verdicts, cross-session issues, and an overall build health assessment.
2. **Updated CURRENT-STATE.md** — Reflect audit findings. If any components need rework, change their status.
3. **Updated SESSION-LOG.md** — Add this audit session's entry.
4. **Recommended next action** — Based on audit results:
   - If everything is SOLID: proceed to Component #3a (Source Discovery) or #7 (Research Agents)
   - If NEEDS FIXES: produce a fix session prompt
   - If NEEDS REWORK: flag to Jack before proceeding

## Working Standards

These are Jack's communication preferences. Follow them:
- Lead with the answer. Explanation follows only if needed.
- Take positions with explicit confidence levels. No passive hedging.
- When something doesn't work or isn't good enough, say so directly.
- No em dashes, sycophantic openers, corporate filler, meta-commentary, or emotional padding.
- When the approach is wrong, propose the redesign, not the hotfix.
- If a tool or method fails mid-task, try 2-3 alternatives before reporting a limitation.
- Verify outputs. Detection over hope.

## Key Terms (use precisely)

- **RESEARCH.md** — Engagement specification. Every agent reads it, every output validates against it.
- **Observation Library** — Captures all outcomes (successes + failures). Expanded from Rejection Library.
- **DPVI** — Decompose-Parallelize-Verify-Iterate.
- **Handoff Contracts** — Explicit I/O/quality definitions at every pipeline boundary (Protocol classes in contracts.py).
- **Goldman-grade** — "Would a domain expert call this solid on its own merits?"
- **Sprint Contracts** — Quality specs negotiated between generator and evaluator per section.
- **CitationProcessor** — Dedicated stage between L1 and L1.5.
- **FITFO** — Figure It The F*** Out. The system should handle novel problems without predefined skills.
- **Trendslop** — Generic, insight-free output that sounds professional but says nothing. The Evaluator's primary detection target.

## Session Handoff Protocol

Before finishing this session, you MUST:
1. Append a new entry to `SESSION-LOG.md` with: date, agent type, task summary, files created/modified, key decisions, what comes next.
2. Rewrite `CURRENT-STATE.md` to reflect the current project state after your work.
