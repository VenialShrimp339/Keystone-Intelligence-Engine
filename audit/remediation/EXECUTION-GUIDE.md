# Remediation Execution Guide

> Historical launcher only. Do **not** use this as the current entrypoint for remediation. If `audit/remediation/control-plane/` exists, follow `CONTROL-PLANE-STATE.yaml`, `ACTIVE-HANDOFF.md`, and `AUTONOMOUS-REMEDIATION-PLAN-v4.md` instead.

*The single document to follow. Replaces all prior instruction files.*
*Status: Phase 1C complete. Phase 1A + 1B ready to execute.*

---

## What's Already Done

| Step | Status | Output |
|------|--------|--------|
| Round 1: 5.4 Pro adversarial review (4 sessions) | Done | round-1/5.4-pro-outputs.md |
| Round 1: Opus validation (4 agents) | Done | round-1/opus-validation.md |
| Tier 1 code fixes (5 fixes) | Done (3 incomplete) | round-1/tier-1-fixes-applied.md |
| Codex adversarial review of Tier 1 fixes | Done | round-1/codex-adversarial-review.md |
| Claude Code deep audit of uncovered areas | Done | round-1/deep-audit-findings.md |
| Phase 1C: Opus agents (4 parallel) | Done | round-2/outputs/opus-agent-{1-4}*.md |
| Feynman comparative analysis | Done | .codex/research-comparisons/ + audit/feynman-analysis/ |

**Current issue count: ~65-70 unique issues after dedup.**

---

## What Happens Next

### Phase 1A: Two 5.4 Pro design sessions (you run these)
### Phase 1B: Two Codex tasks (you run these)
### Phase 1D: Consolidation into MASTER-ISSUE-LIST (Claude Code does this after 1A+1B)
### Phase 2: Architectural decisions (collaborative)
### Phase 3: Implementation (Claude Code)
### Phase 4: Final validation (all models)

This guide covers Phases 1A and 1B. When those complete, come back to Claude Code for the rest.

---

## STEP 1: Update the 5.4 Pro Project

### 1a. Remove these 10 files from the project

These served their purpose in round 1 (evidence methodology review, broad audit). The design sessions need code context, not documentation:

```
FRAMEWORKS.md
RESEARCH-PROMPTS-FINAL.md
evolution-timeline.md
PHASE-1-IMPLEMENTATION-SPEC.md
CAPSTONE-IMPLICATIONS.md
implementation-verification.md
UNIFIED-SYNTHESIS.md
MASTER-SYNTHESIS.md
PLAN-CHANGELOG.md
architecture-and-evolution.md
```

### 1b. Add these 10 files to the project

Upload from the repo:

**Context files (from audit/remediation/):**
```
audit/remediation/ROUND-2-CONTEXT.md
audit/remediation/MASTER-REMEDIATION-PLAN.md
```

**Code files (from src/keystone/):**
```
src/keystone/deliberation/aggregator.py
src/keystone/deliberation/confidence_builder.py
src/keystone/deliberation/analyst.py
src/keystone/research/error_recovery.py
src/keystone/research/finding_writer.py
src/keystone/specification/validator.py
src/keystone/specification/task_generator.py
src/keystone/specification/_prompts.py
```

### 1c. Replace FILE-INDEX.md

Remove the existing `FILE-INDEX.md` from the project and upload the new version from:
```
audit/remediation/round-2/FILE-INDEX-v2.md
```
Rename it to `FILE-INDEX.md` when uploading (or just upload as FILE-INDEX-v2.md -- the custom instructions will reference it).

### 1d. Update Custom Instructions

Replace the entire Project Instructions with:

```
# Project: Keystone Intelligence Engine - Remediation Design Phase

## What You're Working On
A multi-agent AI pipeline for automated consulting research. ~11,000 lines of production Python. 825 tests. 6-layer DPVI architecture.

This is a DESIGN phase, not a review. The bugs are found and cataloged. You are designing the architecture to fix them.

Current date: April 2026. Built April 3-9, 2026.

## What Has Already Happened
- Round 1: 4 adversarial review sessions found ~30 issues, validated by Opus agents
- Codex adversarial review found 3 issues with our Tier 1 fixes
- Claude Code deep audit found 20 more issues in uncovered areas
- 4 Opus agents audited LLM parsing (21 findings), cross-component contracts (20 findings), concurrency (17 findings), and test quality (10 missing tests)
- Feynman comparative analysis identified 3 new components/gaps
- Total: ~65-70 unique issues after dedup. 5 systemic root causes.

ROUND-2-CONTEXT.md has the complete synthesis. Read it FIRST.

## Your Role
You are designing architectures, not finding bugs. Produce implementable design documents with specific data structures, function signatures, and code change lists. Your output will be implemented by Claude Code (Opus 4.6) and verified by Codex.

## Output Standards
- Start with your design, not a summary of what you read
- For each decision: recommendation, rejected alternative with rationale, code changes needed, tests to verify
- Be concrete: "add a field X to model Y" not "the model should be extended"
- If my framing is wrong, say so and redesign it
- If there are interactions between your design and the other parallel session's design, flag them explicitly

## Key Files
- ROUND-2-CONTEXT.md -- ALL findings. Read first.
- MASTER-REMEDIATION-PLAN.md -- The plan, issue list, implementation order.
- JACK-ARCHITECTURAL-DIRECTIVES.md -- Product owner's constraints. Directive 11 (pipeline profiles) and Directive 5 (build philosophy: right interfaces, staged depth) are especially relevant.
- contracts.py -- The 9 handoff contracts.
- All .py files -- The code you're designing changes for.
```

**After these changes: 40 files in the project (10 removed, 10 added). Net effect: replaced round-1 documentation with relevant code files and comprehensive findings synthesis.**

---

## STEP 2: Run the 5.4 Pro Sessions

### Session 5: Data Identity & Provenance Architecture

Open a new conversation in the project. Select 5.4 Pro. Paste the prompt from:
```
audit/remediation/round-2/prompts/5.4-pro-session-5.md
```

Copy ONLY the content inside the ``` code block (the prompt itself, not the metadata around it).

**What this session designs:** How citations should be identified, canonicalized, and traced through the pipeline. How task provenance should survive deliberation aggregation. How per-task citation sub-manifests should be built reliably. What invariants should hold end-to-end.

### Session 6: Enforcement Model & Error Recovery

Open a second conversation. Same model. Paste the prompt from:
```
audit/remediation/round-2/prompts/5.4-pro-session-6.md
```

**What this session designs:** How quality gates should behave on failure (per gate, per pipeline profile). The LLM output parsing standard. Error recovery design. HITL gate behavior. Directive 11 runtime wiring. Component instance lifecycle.

**Run both sessions in parallel.** They're independent design problems. Session 5 handles data flow; Session 6 handles enforcement and runtime behavior. Each prompt explicitly asks the model to flag interactions with the other session's design.

---

## STEP 3: Run the Codex Tasks

These can run in parallel with the 5.4 Pro sessions.

### Codex Task 1: Canary Test Suite

Paste the prompt from:
```
audit/remediation/round-2/prompts/codex-1-canary-suite.md
```

**What this produces:** A permanent test file (`tests/canary/test_architectural_guarantees.py`) with 8 tests that attack the architectural guarantees the system claims about itself. Some will xfail against current code (expected -- they're regression gates for fixes in progress).

### Codex Task 2: Static & Contract Compliance Audit

Paste the prompt from:
```
audit/remediation/round-2/prompts/codex-2-static-audit.md
```

**What this produces:** Structured findings from 6 analyses: protocol compliance, Pydantic model strictness, schema-model field drift, bare KeyError sites, string-boolean bugs, and mypy type checking.

---

## STEP 4: Save All Outputs

When each session completes, save the output to:

```
audit/remediation/round-2/outputs/session-5-data-identity.md
audit/remediation/round-2/outputs/session-6-enforcement-model.md
audit/remediation/round-2/outputs/codex-1-canary-suite-output.md
audit/remediation/round-2/outputs/codex-2-static-audit-output.md
```

The Opus agent outputs are already saved there:
```
audit/remediation/round-2/outputs/opus-agent-1-llm-robustness.md
audit/remediation/round-2/outputs/opus-agent-2-contracts.md
audit/remediation/round-2/outputs/opus-agent-3-concurrency.md
audit/remediation/round-2/outputs/opus-agent-4-test-quality.md
```

---

## STEP 5: Come Back to Claude Code

Once all 4 outputs (2 x 5.4 Pro + 2 x Codex) are saved, start a Claude Code session with:

```
Read all files in audit/remediation/round-2/outputs/. All Phase 1A and 1B tasks are complete. Execute Phase 1D: consolidate all findings into MASTER-ISSUE-LIST.md, then proceed to Phase 2 (architectural decisions). The MASTER-REMEDIATION-PLAN.md and ROUND-2-CONTEXT.md have the full context. EXECUTION-GUIDE.md describes the process.
```

Claude Code will:
1. **Phase 1D:** Merge all findings (round 1 + round 2 + Opus agents + Codex) into a deduplicated MASTER-ISSUE-LIST with every issue classified by type
2. **Phase 2:** Draft architectural decisions A-E based on the 5.4 Pro design outputs, get them reviewed, and finalize
3. **Phase 3:** Implement all fixes in dependency order with canary tests
4. **Phase 4:** Final validation

---

## What Each Tool Is Doing and Why

| Tool | Role | Why this tool |
|------|------|---------------|
| **5.4 Pro** (Sessions 5-6) | Design consultant -- produces target-state architectures for citation identity and enforcement model | Extended thinking on complex design problems. Can reason about tradeoffs across the full codebase. Works from files, can't execute code. |
| **Codex** (Tasks 1-2) | Executable verifier -- builds canary tests and runs static analysis | Can clone the repo, execute code, run mypy, trace code paths. Finds things file-based review misses. |
| **Claude Code** (Phase 1D onward) | Implementation engineer -- consolidates findings, makes decisions, writes code, runs tests | Full codebase access, conversation context, can make changes and verify them immediately. |
| **Opus agents** (Phase 1C, complete) | Parallel deep-read auditors -- examined LLM parsing, contracts, concurrency, test quality | Same codebase access as Claude Code but parallelizable. Already completed. |

---

## Timeline Expectations

| Phase | Effort | Wall clock |
|-------|--------|------------|
| Steps 1-3 (your setup + session launch) | 30-45 min of hands-on work | 30-45 min |
| 5.4 Pro sessions running | Passive (they run) | 30-90 min each |
| Codex tasks running | Passive | 15-45 min each |
| Step 4 (save outputs) | 10 min | 10 min |
| Step 5 onward (Claude Code) | Active collaboration | Several hours across multiple sessions |

All 4 external tasks (2 x 5.4 Pro + 2 x Codex) can run simultaneously. Total passive wait: ~90 min for the longest session.

---

## File Map After Setup

```
audit/remediation/
  README.md                              <- Process overview
  MASTER-REMEDIATION-PLAN.md             <- Full plan (updated)
  ROUND-2-CONTEXT.md                     <- ALL findings synthesis (updated, upload to 5.4 Pro)
  EXECUTION-GUIDE.md                     <- THIS FILE
  
  round-1/                               <- Completed artifacts
    5.4-pro-outputs.md
    opus-validation.md
    codex-adversarial-review.md
    deep-audit-findings.md
    tier-1-fixes-applied.md
  
  round-2/
    FILE-INDEX-v2.md                     <- Updated file index (upload to 5.4 Pro)
    prompts/
      5.4-pro-session-5.md              <- Data Identity design prompt
      5.4-pro-session-6.md              <- Enforcement Model design prompt
      codex-1-canary-suite.md           <- Canary test suite prompt
      codex-2-static-audit.md           <- Static analysis prompt
      opus-agents-phase-1c.md           <- Agent briefs (for documentation)
    outputs/
      opus-agent-1-llm-robustness.md    <- DONE
      opus-agent-2-contracts.md         <- DONE
      opus-agent-3-concurrency.md       <- DONE
      opus-agent-4-test-quality.md      <- DONE
      session-5-data-identity.md        <- Save here when complete
      session-6-enforcement-model.md    <- Save here when complete
      codex-1-canary-suite-output.md    <- Save here when complete
      codex-2-static-audit-output.md    <- Save here when complete
  
  decisions/                             <- Phase 2 (after all outputs collected)
  implementation/                        <- Phase 3
```
