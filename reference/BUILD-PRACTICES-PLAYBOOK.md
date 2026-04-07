# Build Practices Playbook: Lessons from the Keystone Intelligence Engine

*Extracted from 16+ sessions building a multi-agent AI system across Waves 1-3*
*For use as input to other Claude Code projects*

---

## 1. Project Documentation Architecture

The most important decision we made was establishing a clear document hierarchy BEFORE any code was written. Every new Claude session auto-loads CLAUDE.md, which points to the other files. This eliminates "what's going on?" cold-start time.

### The Four Essential Root Files

```
CLAUDE.md                    <- Auto-loaded. Project overview, reading order, working rules.
CURRENT-STATE.md             <- Living snapshot. Updated after EVERY session.
SESSION-LOG.md               <- Chronological history. Append-only.
[AUTHORITATIVE-DECISIONS].md <- Owner's design decisions. Not overrideable by any session.
```

**Why this works:** Claude Code sessions are stateless. They compact, they lose context, they get replaced. These files are the persistent memory. Without them, every session reinvents understanding from scratch.

**CLAUDE.md structure that worked:**
1. One-line project description
2. Project structure (directory map with descriptions)
3. Deployment context (platform, constraints, cost targets)
4. Architectural convictions (5-7 principles that shape ALL decisions)
5. System overview (pipeline/architecture reference)
6. Orientation section: "New session? Read these files first: [ordered list]"
7. Session handoff protocol (what to update before finishing)
8. Working rules (communication style, output standards)
9. Key terms (domain-specific vocabulary used precisely)

**CURRENT-STATE.md structure that worked:**
1. "Where we are" (one paragraph)
2. "What was completed" (last session's work, with file paths)
3. "Known gaps" (honest about what's untested/missing)
4. "What's next" (prioritized, with dependencies and blockers)
5. "What's complete" (cumulative table of all work)
6. "What's blocked" (with specific actions needed to unblock)
7. "Key decisions" (settled, not relitigated)

**The Handoff Protocol:** Every session MUST do both:
1. Append to SESSION-LOG.md (date, task, files modified, decisions, what's next)
2. Rewrite CURRENT-STATE.md to reflect the new state

This protocol was frequently violated by sessions that forgot or ran out of context. Having it in CLAUDE.md helps but doesn't guarantee compliance. The planning/orchestrator session should verify handoff was done and fix it if not.

### The Owner's Directives File

We had JACK-ARCHITECTURAL-DIRECTIVES.md -- design decisions made by the project owner during planning sessions. These are AUTHORITATIVE and not overrideable by any Claude session. This prevents architectural drift when sessions make "improvements" that conflict with the owner's intent.

Key pattern: when a session questions an architectural decision, it checks the directives file FIRST. If the decision is there, it's settled. If it's not, the session flags it as an open question rather than making a unilateral call.

---

## 2. The Planning Session Pattern

One Claude Code session acts as the **orchestrator/planner**. It does NOT write production code. It:
- Reads the entire codebase and builds comprehensive understanding
- Identifies dependencies, risks, gaps
- Writes detailed prompts for parallel execution sessions
- Audits execution session outputs
- Maintains documentation
- Makes architectural decisions that affect multiple sessions

This is the most valuable pattern we discovered. The planning session has context that no individual execution session has, because it reads everything and persists across multiple waves.

**What the planning session does well:**
- Dependency analysis (which sessions can run in parallel)
- File overlap detection (preventing merge conflicts)
- Cross-component consistency checking
- Writing prompts with the right level of specificity
- Catching things execution sessions miss (we found 5 files missing from a session's scope during pre-launch audit)

**What the planning session should NOT do:**
- Write large amounts of production code (use execution sessions for that)
- Update documentation while execution sessions are running (stale immediately)
- Make unilateral architectural decisions without checking the owner's directives

---

## 3. Parallel Session Management

### The Wave Structure

Group independent work into "waves." Sessions within a wave run in parallel. Waves run sequentially.

```
Wave 1: [Session A] [Session B] [Session C]  <- all parallel, zero file overlap
         ↓ merge + audit ↓
Wave 2: [Session D] [Session E]              <- depend on Wave 1 outputs
         ↓ merge + audit ↓
Wave 3: [Session F] [Session G] [Session H]  <- depend on Wave 2 outputs
```

### How to Determine Parallelism

Before launching any wave, the planning session must verify:

1. **File overlap analysis**: List every file each session will create or modify. If two sessions touch the same file, they CANNOT run in parallel. Move the overlapping file to one session's scope and add "DO NOT TOUCH [file]" to the other.

2. **Interface contracts**: If Session A creates a function that Session B will call, they CAN run in parallel IF you specify the exact function signature in both prompts. We used `LLMFactory = Callable[[ModelTier], LLMCallable]` as a shared interface between the LLM client session and the pipeline session.

3. **Dependency direction**: If B needs A's output to even start, they're sequential. If B needs A's interface but can mock it, they're parallel.

### The Session Prompt Template

Every execution session prompt should include:

```
1. FILES TO READ FIRST (ordered, specific paths + line numbers)
2. YOUR TASK (clear scope statement)
3. FILES TO CREATE (exact paths, module structure)
4. FILES TO MODIFY (with specific changes)
5. CRITICAL PATTERNS TO FOLLOW (code examples from existing codebase)
6. SCOPE -- BUILD NOW (what's in scope)
7. SCOPE -- DO NOT BUILD (what to defer)
8. DO NOT (files to avoid, anti-patterns)
9. WHEN COMPLETE (verification steps, what to report)
```

The "DO NOT" section is critical for parallel sessions. Example:
```
DO NOT:
- Touch any files in evaluator/, specification/, citation/
- Modify SESSION-LOG.md or CURRENT-STATE.md (planning session handles handoff)
- Add dependencies to pyproject.toml (another session owns it)
```

### The Part 1 / Self-Audit / Part 2 Pattern

For longer-running autonomous sessions:

```
PART 1: Build the thing
  - Create files, write tests

SELF-AUDIT: Verify your own work
  - Run tests, check for regressions
  - Report count and any issues

PART 2: Validate or extend
  - Run integration tests
  - Do the thing that proves Part 1 actually works
```

This catches issues within the session before the external audit. Our sessions consistently found and fixed their own bugs during the self-audit step.

---

## 4. Quality Control Layers

We used four layers of verification, each catching different types of problems:

### Layer 1: Session Self-Audit
The session runs its own tests after building. Catches: syntax errors, import failures, basic logic bugs. ~60% of issues caught here.

### Layer 2: Automated Post-Session Audit
The planning session launches Opus-tier audit agents (one per execution session, in parallel) that:
- Read the session's output files
- Verify against the original task spec
- Grep for stragglers (e.g., old variable names that should have been renamed)
- Run the full test suite
- Check for scope violations (files modified that shouldn't have been)

This caught: 2 straggler docstring references, a checklist typo, missing files in a rename operation. ~30% of issues caught here.

### Layer 3: Planning Session Integration Review
The planning session verifies cross-session compatibility:
- Do the outputs from Session A work with Session B's expectations?
- Are the shared interfaces correct?
- Does the full test suite pass after merging all sessions?

This caught: the StructuredFinding model drift from the implementation spec (fields in the spec but not the model).

### Layer 4: Pre-Wave Structural Audit
Before launching a new wave, audit the entire pyramid:
- Trace data types through every pipeline boundary
- Verify Protocol contracts match actual implementations
- Check that test fixtures use realistic data shapes
- Identify any "spent" assumptions from earlier sessions

This caught: the tool name mismatch (9 of 11 tool names in the Spec Engine didn't match Gateway registrations -- would have caused runtime failures), and 5 files missing from a session prompt.

### Key Insight: Audit Depth Matters

Our first audit gave blanket "SOLID" verdicts for all components. A review of that audit identified 5 specific inadequacies. The deepened audit, mapping each acceptance criterion to specific code paths and tests (MET/UNTESTED/UNMET tables), found the critical tool name bug. **Never accept blanket quality verdicts. Always check against specific acceptance criteria.**

---

## 5. The Mock-First Build Pattern

Every component was built and tested with mock dependencies before any real integration.

```
Phase 1 (autonomous, parallelizable):
  Build component with mock LLM, mock APIs, mock database
  → Tests verify: data flow, type safety, error handling, event emission

Phase 2 (requires human judgment):
  Swap mocks for real services
  → Tests verify: actual integration works
  → Human verifies: output quality is acceptable
```

**Why this works:** Phase 1 can be done entirely by Claude sessions in parallel. The architecture gets validated structurally. Phase 2 requires the project owner in the loop because quality judgment can't be automated without calibration data.

**The trap:** It's tempting to declare the project "working" after Phase 1. It's not. Mock tests verify plumbing. Real quality verification requires real data and human judgment. We were explicit about this distinction throughout.

**The LLMCallable abstraction:**
```python
LLMCallable = Callable[[str], Awaitable[str]]
```
Every component takes this as a constructor parameter. In tests: `async def mock_llm(prompt): return '{"key": "value"}'`. In production: a real API client. This one type alias enabled the entire mock-first pattern.

---

## 6. Git as a Parallel Session Safety Net

**Initialize git BEFORE launching any parallel sessions.** We made this mistake -- the project had no git repo when we started running parallel sessions. One of the first things the planning session did was `git init && git add -A && git commit -m "baseline"`.

**Commit patterns:**
- Commit baseline BEFORE each wave
- Commit each wave's merged output AFTER audit
- Use selective staging (`git add [specific files]`) when parallel sessions are modifying the codebase simultaneously -- don't `git add -A` or you'll capture in-progress work from other sessions
- Never commit `.env` (gitignore it)

---

## 7. Research-Before-Build Pattern

Before building anything, we ran deep research:
- 16 deep research reports on architecture patterns (Batch 1)
- 10 deep research reports on specific open questions (Batch 2)
- Per-report analyses mapping findings to specific components
- Master synthesis documents resolving contradictions between reports

Then: implementation spec derived from research, gap analysis, pre-build audit, THEN code.

This front-loading means architectural decisions are evidence-based rather than vibes-based. When a session needs to make a design choice, there's usually a research report with a specific finding to reference.

**The research prompt pattern:**
```
Context: [what we're building, what decisions depend on this]
Specific questions: [numbered, precise, answerable]
For every claim: cite the specific source
If specific numbers aren't documented: say so explicitly
```

---

## 8. Handling Provider Migrations / Major Pivots

We experienced a forced migration from Anthropic to OpenAI mid-build. The approach:

1. **Research first**: 4 targeted research reports on the new provider
2. **Switchover plan**: Written document resolving architecture decisions with evidence
3. **Tier 1/2/3/4 classification**: Every affected file categorized by urgency
4. **Provider-agnostic abstractions**: Renamed provider-specific identifiers (ModelTier: OPUS/SONNET/HAIKU → FLAGSHIP/STANDARD/FAST/LIGHT) so the codebase doesn't embed provider assumptions
5. **The rename wave**: Pure refactoring session, no behavioral changes, all tests must still pass
6. **Config-driven model IDs**: Actual model strings live in `.env`, not in code

**Key lesson:** If your abstraction layer is right, a provider migration is a config change + prompt tuning, not an architecture rewrite. Our Protocol contracts and LLMCallable abstraction meant zero interface changes across 9 pipeline boundaries.

---

## 9. What Went Wrong (Lessons Learned the Hard Way)

### Cross-Session String Drift
Two parallel sessions independently chose different string identifiers for the same tools. 9 of 11 tool names didn't match. Fix: created a single source-of-truth constants file (`tool_names.py`) and had both sessions import from it. **Lesson: shared identifiers need a shared constants file created BEFORE parallel sessions that use them.**

### Shallow Audits
First audit gave "SOLID" verdicts without checking specific acceptance criteria. The deepening pass found a critical bug. **Lesson: always audit against specific acceptance criteria, not general impressions.**

### Model Drift from Spec
The implementation spec defined StructuredFinding with fields that were never added to the Pydantic model. Different sessions built against different versions of the truth. **Lesson: the code model is the source of truth, not the spec document. When they diverge, update the model before building components that produce or consume it.**

### Session Prompt Gaps
The planning session wrote a session prompt listing 12 files to rename, but missed 5 additional files (JSON schemas, sample data, templates) that contained the same strings. The pre-launch audit caught this. **Lesson: after writing a session prompt, grep the entire codebase for the strings being changed and verify the prompt covers all occurrences.**

### Empty Scaffolding Confusion
Early sessions created empty directory structures (calibration/, scripts/, etc.) that were never populated. Later sessions and auditors had to investigate whether these were intentional placeholders or abandoned work. **Lesson: don't create directories until you have files to put in them.**

### Stale Documentation
CURRENT-STATE.md, ARCHITECTURE.md, and CLAUDE.md all became stale as sessions modified the codebase without updating docs. The planning session had to periodically regenerate them. **Lesson: documentation refresh should happen after each wave, not continuously. Trying to keep docs updated during parallel sessions is futile.**

---

## 10. Communication Style That Works with Claude Code

### In CLAUDE.md:
- "Lead with the answer. Explanation follows only if needed."
- "Make verdicts, not inventories." (ADOPT/ADAPT/SKIP/INVESTIGATE)
- "No em dashes, sycophantic openers, corporate filler, meta-commentary"
- "When the approach is wrong, propose the redesign, not the hotfix"
- "Verify outputs. Don't assume correctness. Detection over hope."

### In Session Prompts:
- Be specific about file paths and line numbers
- Include code examples showing the EXACT pattern to follow
- Say "DO NOT" clearly (sessions will drift without explicit boundaries)
- "When complete, report: [exact deliverables]" forces structured output
- Give the session enough context to make judgment calls, not just follow instructions

### From the Owner:
Jack's most effective interventions were:
- "I don't trust this. Dig deeper." (forced the shallow audit to become thorough)
- "Determine if the Cowork session's analysis was valid -- don't treat it as automatically correct" (prevented blind acceptance of another AI's critique)
- "I'm worried about cascading failures" (triggered the pre-Wave structural audit that found real issues)
- Direct edits to the switchover plan's reasoning_effort table (owner judgment overriding AI defaults)

The owner doesn't need to write code or even understand the implementation details. They need to:
1. Set architectural direction (directives file)
2. Push back when quality seems shallow
3. Make judgment calls the AI can't (quality standards, business priorities)
4. Provide domain-specific inputs (test cases, calibration data, quality scoring)

---

## 11. The CLAUDE.md Template

Here's a minimal starting template that captures the patterns that worked:

```markdown
# [Project Name]

[One sentence: what this is and why it matters]

## Project Structure
[Directory tree with descriptions]

## Orientation
New session? Read these files first:
1. This file (auto-loaded)
2. CURRENT-STATE.md -- where we are, what's next
3. [OWNER-DIRECTIVES].md -- authoritative design decisions

## Session Handoff Protocol
Before finishing any session:
1. Append to SESSION-LOG.md: date, task, files modified, decisions, next steps
2. Rewrite CURRENT-STATE.md to reflect current state

## Working Rules
- [Project-specific rules that prevent recurring mistakes]
- Read [source-of-truth doc] before making architectural recommendations
- Flag contradictions rather than silently resolving them
- Verify outputs. Detection over hope.

## Communication Rules
- Lead with the answer
- Make verdicts, not inventories
- No filler, no hedging, no meta-commentary
```

---

## 12. Anti-Patterns to Avoid

1. **Don't let sessions update shared docs in parallel.** SESSION-LOG.md and CURRENT-STATE.md should only be updated by one session (the planning session, or the last session in a wave).

2. **Don't trust "all tests pass" as proof of quality.** Mock tests verify plumbing. Quality verification requires real data and human judgment.

3. **Don't create empty scaffolding "for later."** It creates confusion about what's built vs what's planned.

4. **Don't conflate the implementation spec with the code model.** When they diverge, update the code model. The spec is a plan; the model is the contract.

5. **Don't run quality calibration autonomously.** AI grading AI with synthetic data is a closed loop. The human must be in the loop for quality judgment.

6. **Don't launch parallel sessions without file overlap analysis.** Even one shared file causes merge pain.

7. **Don't write session prompts from memory.** Read the actual code first. Grep for the actual strings. Verify the actual constructors. Session prompts written from memory miss things.
