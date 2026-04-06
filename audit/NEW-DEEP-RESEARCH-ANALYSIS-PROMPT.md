# Session Prompt: Batch 2 Deep Research Analysis

*Prompt for a Claude Code session to analyze the 10 new deep research reports (Batch 2) that address open architectural questions for the Keystone Intelligence Engine.*

---

## Before You Paste This Prompt

**Step 1: Save your 10 deep research reports.**

Create the folder `research-reports/batch-2/` inside the Keystone-Intelligence-Engine project directory. Drop all 10 reports into it as-is. **Do not rename them.** The files are saved in chronological download order, which matches the prompt order from DEEP-RESEARCH-BATCH-PLAN.md:

| Download order | Topic |
|---|---|
| 1st file saved | Report 01: Iterative Multi-Round Research |
| 2nd file saved | Report 02: Dynamic Agent Configuration |
| 3rd file saved | Report 03: MECE Issue Tree Decomposition |
| 4th file saved | Report 04: Retrieval Architecture & Knowledge Bases |
| 5th file saved | Report 05: Consulting Engagement Taxonomy |
| 6th file saved | Report 06: Context Management |
| 7th file saved | Report 07: Adaptive Evaluation |
| 8th file saved | Report 08: MCP Tool Ecosystem |
| 9th file saved | Report 09: Orchestration Patterns |
| 10th file saved | Report 10: Specification Engine |

**Step 2: Open a new Claude Code session** in the Keystone-Intelligence-Engine project directory (so CLAUDE.md auto-loads).

**Step 3: Paste the prompt below.**

---

## Prompt

```
# Session: Batch 2 Deep Research Report Analysis (Parallel Architecture)

You are the ORCHESTRATOR for analyzing 10 deep research reports that address the open architectural questions for the Keystone Intelligence Engine. This is the most architecturally consequential analysis session in the project. Quality over speed.

## Execution Architecture

You will execute in THREE PHASES:

**Phase 1 (you, the orchestrator):** Load shared context, identify reports, prepare shared context block.
**Phase 2 (10 parallel subagents):** Spawn 10 Opus subagents simultaneously — one per report. Each gets the full shared context plus its specific report. Each writes one analysis file.
**Phase 3 (you, the orchestrator):** After all 10 subagents complete, read all 10 analysis files and write the master synthesis.

This parallel architecture means each subagent gets the FULL context window dedicated to its one report — no degradation from processing other reports first.

---

## PHASE 1: Context Loading and Report Identification

### Step 1.1: Load shared context

Read these files IN THIS ORDER. Do not skip any.

1. **CLAUDE.md** (auto-loaded — verdict taxonomy, working rules, key terms)
2. **CURRENT-STATE.md** (~95 lines — where the project stands, settled decisions)
3. **JACK-ARCHITECTURAL-DIRECTIVES.md** (~150 lines — CRITICAL. Jack's design decisions from planning sessions. Authoritative. Read every line.)
4. **CAPSTONE-PLAN-v2.md Sections 2-5 only** (lines ~24-800 — architecture, specification engine, research agents, deliberation, evaluation)
5. **audit/PHASE-1-IMPLEMENTATION-SPEC.md** (~270 lines — the 11 components, I/O contracts, acceptance criteria)
6. **synthesis/UNIFIED-SYNTHESIS.md** (skim Section 6: verdict table — what's already decided)

### Step 1.2: Identify the 10 reports

Reports are in `research-reports/batch-2/`. If the files aren't there, STOP and tell the user.

The files may have arbitrary names from Claude's web UI. They are saved in chronological order matching the prompt order. List the directory sorted by creation/modification time (`ls -lt` or `ls -tr`) to establish the mapping:

| Chronological order | Report topic |
|---|---|
| 1st file | Report 01: Iterative Multi-Round Research |
| 2nd file | Report 02: Dynamic Agent Configuration |
| 3rd file | Report 03: MECE Issue Tree Decomposition |
| 4th file | Report 04: Retrieval Architecture & Knowledge Bases |
| 5th file | Report 05: Consulting Engagement Taxonomy |
| 6th file | Report 06: Context Management |
| 7th file | Report 07: Adaptive Evaluation |
| 8th file | Report 08: MCP Tool Ecosystem |
| 9th file | Report 09: Orchestration Patterns |
| 10th file | Report 10: Specification Engine |

Verify each mapping by reading the first ~10 lines of each file to confirm the topic matches. If the content doesn't match the expected order, use content to determine the correct mapping and note the discrepancy.

### Step 1.3: Create output directory

```bash
mkdir -p audit/batch-2-analysis
```

### Step 1.4: Prepare the shared context block

Before spawning subagents, you need to assemble the shared context they'll all receive. Construct a SHARED_CONTEXT string containing the full text of:
- CURRENT-STATE.md (the settled decisions section especially)
- JACK-ARCHITECTURAL-DIRECTIVES.md (full text)
- The key sections of CAPSTONE-PLAN-v2.md you read (Sections 2-5)
- The PHASE-1-IMPLEMENTATION-SPEC.md component list
- The UNIFIED-SYNTHESIS.md Section 6 verdict table

You will inject this into each subagent's prompt so they all have identical project context.

---

## PHASE 2: Spawn 10 Parallel Subagents

Spawn ALL 10 subagents in a SINGLE message using the Agent tool. Each subagent must be Opus (`model: "opus"`). Each gets the same shared context plus its unique report assignment.

Each subagent prompt must include ALL of the following sections. Do not abbreviate or omit any section from the subagent prompts.

### Subagent Prompt Template

For each subagent, construct a prompt with this structure:

---

**[SECTION A: IDENTITY AND TASK]**

```
You are analyzing ONE deep research report for the Keystone Intelligence Engine project. Your job: extract every implementation-relevant finding, apply critical judgment to each finding, and produce a structured analysis file. You are an analyst, not a transcriber. Exercise independent judgment throughout.

Your assigned report: Report NN — [Topic]
Report file: [full path to the specific report file]
Output file: audit/batch-2-analysis/analysis-NN-[short-topic].md

Priority tier: [Tier 1/2/3]
[Insert the report-specific focus instructions from the REPORT ASSIGNMENTS section below]
```

**[SECTION B: SHARED PROJECT CONTEXT]**

```
[Paste the full SHARED_CONTEXT block you assembled in Phase 1 here — settled decisions, Jack's directives, CAPSTONE-PLAN sections, component specs, existing verdicts]
```

**[SECTION C: TRUST HIERARCHY]**

```
These reports are an INPUT to your analysis, not the source of truth. Apply this trust hierarchy when findings conflict:

1. Jack's architectural directives (provided above) — highest authority. Owner's design intent.
2. The 11 settled decisions (provided above) — validated through multiple research rounds.
3. Existing project research already validated (UNIFIED-SYNTHESIS verdicts, findings in CAPSTONE-PLAN-v2.md) — produced by earlier sessions and cross-checked.
4. Your own knowledge of the current state of AI/ML as of 2026 — you have training data through early 2025 and are running in April 2026. If the report cites a 2023 paper as justification for an architectural choice and you know the field has moved significantly since then, say so. Your independent judgment is MORE valuable than an uncritical summary.
5. The deep research report itself — valuable for novel insights and synthesis, but NOT authoritative on its own. It was produced by an AI session that may have surfaced outdated papers, hallucinated citations, or presented superseded techniques as current.
```

**[SECTION D: TEMPORAL SKEPTICISM]**

```
AI agent architectures, LLM capabilities, embedding models, and orchestration patterns evolve on ~6-month cycles. Apply this filter:

- Pre-2024 citations in fast-moving areas (agent architectures, prompting techniques, embedding models, orchestration frameworks): STALE by default. Cross-check against what you know. Flag and assess whether the conclusion still holds given 2025-2026 developments.
- 2024-2025 citations: Credible but verify. A lot changed between mid-2024 and early 2026 (Claude 4.6, Agent SDK, new embedding models, MCP maturation).
- 2025-2026 citations and Anthropic engineering posts: Highest credibility for our stack.
- Timeless findings (consulting methodology, MECE frameworks, evaluation theory, IR fundamentals): Date matters less.

When a report presents an outdated finding alongside a valid architectural insight, salvage the insight but flag the evidence basis.

The project already has 17 research-backed changes in CAPSTONE-PLAN-v2.md and a validated synthesis from 16 prior reports. If this report contradicts something already settled, the bar for overriding is HIGH: new evidence must be (a) more recent, (b) more credible, and (c) directly applicable. Otherwise, note the disagreement but maintain the existing decision.

Conversely, when the report surfaces something genuinely novel, lean in. The value is in what's NEW.
```

**[SECTION E: ANALYSIS STANDARDS]**

```
- Make verdicts, not inventories. Every finding: ADOPT / ADAPT / SKIP / INVESTIGATE + one-sentence justification. If the report lists 15 options, pick the best one and say why.
- Jack's directives are authoritative. If research contradicts a directive, present it as "research suggests X, which conflicts with Jack's directive Y" — not as an override.
- Distinguish evidence quality: Verified (empirical, reproduced) / Credible (active project, reputable) / Claimed (blog/tweet, no evidence) / Stale (6+ months, superseded). When marking Stale, state what changed.
- Exercise independent judgment. If something doesn't pass your smell test — weak logic, thin evidence, poor fit — say so directly.
- Connect everything to the 11 Phase 1 components. If a finding doesn't affect any component, note it briefly and move on.
- Quantify where possible: token counts, latency, cost, round-trips.
- Do NOT read any files other than your assigned report. All project context is provided in this prompt.
```

**[SECTION F: OUTPUT FORMAT]**

```
Write your output to: audit/batch-2-analysis/analysis-NN-[short-topic].md

Use this exact structure:

# Analysis: Report NN — [Topic]
*Analyzed: [date] | Priority: [tier] | Report quality: [high/medium/low]*

## Executive Summary
3-5 sentences. What did this report find? How does it change our architecture?

## Key Findings (ranked by implementation impact)

### [N]. [Finding title]
- **What:** [1-2 sentence description]
- **Evidence basis:** [What source(s) does the report cite? Include dates.]
- **Evidence quality:** Verified / Credible / Claimed / Stale
- **Temporal check:** [Is this current as of 2026? If pre-2024 in a fast-moving area, has the field moved past it?]
- **Conflicts with existing project research?** [Yes/No. If yes, which finding, and which is more credible?]
- **Verdict:** ADOPT / ADAPT / SKIP / INVESTIGATE
- **Justification:** [one sentence]
- **Keystone impact:** [which components, which architectural decisions]
- **Contradicts:** [any known findings from other reports, or "none" / "unknown — parallel analysis"]

## Architectural Decisions This Enables
- Specific decisions that can now be made, with recommended choice and evidence basis.

## Changes to Existing Plan
- Changes needed to CAPSTONE-PLAN-v2.md (cite section)
- Changes needed to PHASE-1-IMPLEMENTATION-SPEC.md (cite component)
- Whether findings validate or challenge Jack's directives

## Open Questions Remaining
- What this report did NOT resolve
```

---

### Report Assignments (inject the correct one into each subagent)

**Report 01: Iterative Multi-Round Research** — Tier 1, HIGHEST priority
- This is the single biggest architectural gap. The plan has concepts but no mechanical specification.
- Focus on: Decision criteria for "spawn new research" vs. "go deeper" vs. "stop." Stopping conditions. Mid-research scope expansion. Recommended max rounds.
- Cross-report connections: Feeds into Reports 06 (context management), 09 (orchestration), 10 (spec engine).

**Report 02: Dynamic Agent Configuration** — Tier 2, HIGH priority
- Focus on: Architecture for agent configuration (templates vs. generated). How the Spec Engine decides between template and custom. Quality control for dynamic agents.
- Cross-report connections: Feeds into Reports 07 (adaptive eval), 10 (spec engine). Informed by Report 05 (engagement taxonomy).

**Report 03: MECE Issue Tree Decomposition** — Tier 1, HIGHEST priority
- New architectural concept proposed by Jack. Not in the original plan at all.
- Focus on: Whether multi-agent decomposition outperforms single-agent. How to evaluate tree quality. How the tree evolves during research. Prompting strategies.
- Cross-report connections: Feeds into Reports 02 (dynamic agents), 10 (spec engine).

**Report 04: Retrieval Architecture and Knowledge Accumulation** — Tier 2, HIGH priority
- Evaluates the Karpathy "LLM Knowledge Bases" pattern (compiled markdown wikis vs. traditional RAG/embeddings).
- Focus on: Where compiled wikis beat embeddings, where they don't. Whether our claim-level IR is already this pattern. Impact on Component #3 scope. Citation integrity in compiled wikis. Embedding model recommendation if embeddings still needed.
- Cross-report connections: Determines Component #3 scope. Feeds into Reports 06 (context mgmt), 08 (MCP tools), 10 (spec engine / Observation Library).

**Report 05: Consulting Engagement Taxonomy** — Tier 3, MEDIUM priority
- More inventory/survey than architecture.
- Focus on: Engagement type taxonomy, framework library mapping, knowledge management patterns from top firms.
- Cross-report connections: Informs Reports 02, 03, 07.

**Report 06: Context Management** — Tier 2, HIGH priority
- Focus on: LeadResearcher context strategy across rounds. External memory implementation. Source management for 50-200 sources. Finding revision across rounds.
- Cross-report connections: Informed by Report 01 (iterative research). Feeds into Report 09 (orchestration).

**Report 07: Adaptive Evaluation** — Tier 3, MEDIUM priority
- Focus on: Predefined profiles vs. dynamic evaluation criteria. Which rubric dimensions are universal vs. engagement-specific. Sprint contracts at engagement level.
- Cross-report connections: Informed by Report 05 (engagement taxonomy). Feeds into Report 10 (spec engine).

**Report 08: MCP Tool Ecosystem** — Tier 3, LOWER priority
- Inventory work.
- Focus on: MVP server selection (which 3-6 to start with). Gateway architecture best practices. Reliability handling.
- Cross-report connections: Informed by Report 04 (retrieval). Affects Component #4 scope.

**Report 09: Orchestration Patterns** — Tier 3, MEDIUM priority
- Focus on: PydanticAI vs. Agent SDK comparison. Whether deferring Temporal is correct. Error recovery. Human-in-the-loop gate implementation.
- Cross-report connections: Validates or challenges settled decision #1 (custom orchestration with PydanticAI). Informed by Reports 01 (iterative research), 06 (context management).

**Report 10: Specification Engine as Problem Structurer** — Tier 1, HIGHEST priority
- Integration point synthesizing across many other reports.
- Focus on: The complete Specification Engine flow, intent engineering, how the Observation Library informs specification, handling well-scoped vs. open-ended research.
- Cross-report connections: Informed by Reports 01, 02, 03, 05, 07. This is the keystone component — its analysis should note where it needs input from other reports.

---

## PHASE 3: Master Synthesis

After ALL 10 subagents have completed, read ALL 10 analysis files from `audit/batch-2-analysis/`.

Then write: `audit/batch-2-analysis/MASTER-SYNTHESIS.md`

This is the most important output of the entire session. You (the orchestrator) have the unique advantage of seeing all 10 analyses together. The subagents could not cross-reference each other because they ran in parallel. YOUR job is to find the connections, contradictions, and emergent architecture across all 10.

Use this structure:

```markdown
# Batch 2 Deep Research: Master Synthesis
*[date] | 10 reports analyzed | [X] architectural decisions resolved*

## 1. The Architecture That Emerges

Narrative description (not bullet points) of the Keystone architecture as it should be built, incorporating all 10 reports' findings. This should read as a coherent architectural vision, not a patchwork. Cover:

- The Specification Engine flow (with issue tree decomposition)
- The iterative research loop (with stopping conditions)
- Agent configuration strategy
- Retrieval and knowledge accumulation architecture
- Evaluation framework
- Context management approach
- Orchestration pattern

## 2. Contradiction Resolution

For each contradiction found ACROSS reports (the subagents flagged what they could, but they couldn't see each other's reports):
- Reports involved
- What they disagree on
- Which position is better supported (with evidence)
- Resolution for Keystone

## 3. Convergent Findings (appeared in 3+ reports)
High-confidence findings that multiple independent reports agree on.

## 4. The 11 Settled Decisions: Validated or Challenged?
For each of the 11 settled architectural decisions in CURRENT-STATE.md, synthesize across all 10 analyses: does the new research validate, challenge, or add nuance? If challenged, flag for Jack's review.

## 5. Jack's Directives: Validated or Challenged?
For each directive in JACK-ARCHITECTURAL-DIRECTIVES.md, synthesize: does the research support it, challenge it, or add nuance? Jack's directives are authoritative — if research conflicts, flag it but don't override.

## 6. New Architectural Decisions (Ready to Settle)
Decisions that can now be made. For each:
- The decision
- The recommendation
- The evidence basis (cite which report analyses support it)
- Confidence level
- What it affects (components, timeline)

## 7. Decisions Still Open
What the research did NOT resolve. What additional investigation is needed.

## 8. Updated Component Impact Map
For each of the 11 Phase 1 components: how do findings affect its design, scope, or priority?

## 9. Recommended Changes to CAPSTONE-PLAN-v2.md
Consolidated list of every warranted plan change. Organized by plan section. Each with evidence citation.

## 10. Updated Build Sequence
Does the research change the build order? Should any component move earlier or later? Should Component #3 scope change based on Karpathy findings?

## 11. Risk Register Update
New risks identified. Changes to existing risk severity.

## 12. Stale/Outdated Findings Flagged
Consolidate all findings that subagents flagged as Stale or temporally suspect. Group by topic. For each, note whether the underlying insight is still valid even if the cited evidence is outdated.
```

---

## PHASE 4: Session Handoff

After writing the master synthesis:

1. Update CURRENT-STATE.md:
   - Phase: "Batch 2 deep research analyzed. Architecture decisions pending Jack review."
   - Add Batch 2 analysis to the "What's complete" table
   - Update "What's next" based on findings
   - Update "Key architectural decisions" if any new decisions are settled

2. Append to SESSION-LOG.md:
   - Date, session type, files created, key decisions, what comes next

---

## DO NOT READ (context waste — applies to both orchestrator and subagents):

- `research-reports/Deep_Research_Report_From_Prompt_*.md` (OLD Batch 1 reports — different topic)
- `reference/analysis/deep-research-*.md` (old leak analysis reports)
- `reference/nano-claude-code/` (source code reference — not relevant)
- `synthesis/thread-*-analysis.md` (planning phase thread analyses — already synthesized)
- `quality-audits/` (audit of old prompts)
- `source-analysis/` (bookmark analysis)
- `SESSION-LOG.md`, `COWORK-SESSION-HISTORY-CONDENSED.md` (historical)
- `nate-synthesis/` (already incorporated into plan)
- `calibration/` (not relevant yet)
```

---

## Notes for Jack

- **Execution model:** The orchestrator loads context, then spawns 10 parallel Opus subagents simultaneously. Each subagent dedicates its full context window to ONE report. The orchestrator then synthesizes all 10 analyses.
- **Expected output:** 10 per-report analysis files + 1 master synthesis = 11 new files in `audit/batch-2-analysis/`
- **Expected duration:** 15-30 minutes (parallel execution is much faster than sequential)
- **Quality advantage:** Each subagent gets the full shared context PLUS its entire context budget for its one report. No degradation from processing other reports. The orchestrator then has the cross-report view that no individual subagent had.
- **After this session completes:** Bring the master synthesis back to the Cowork session. We'll review findings together, settle the open decisions, and update the build plan.
- **The JACK-ARCHITECTURAL-DIRECTIVES.md file is new.** It was created in today's Cowork session to capture everything you told me about rigidity, issue trees, iterative research, engagement scope, build philosophy, the Karpathy concept, and the "FITFO" standard. Read it before running the session to make sure I captured your intent correctly.

### What this session does NOT do:

- It does not update CAPSTONE-PLAN-v2.md (that requires Jack's review of findings first)
- It does not update PHASE-1-IMPLEMENTATION-SPEC.md (same reason)
- It does not write code (this is analysis only)
- It does not re-run or extend the deep research (it analyzes what was already produced)
