# Keystone Intelligence Engine

Multi-agent AI system for automated consulting research. Capstone project (IU Kelley, Prof. Youle). Real product for Keystone Group, not an academic exercise.

## Project Structure

```
CURRENT-STATE.md             <- WHERE WE ARE. Read this first after CLAUDE.md.
JACK-ARCHITECTURAL-DIRECTIVES.md <- Jack's design decisions from planning sessions. AUTHORITATIVE.
SESSION-LOG.md               <- Chronological log of every agent session.
CAPSTONE-PLAN-v2.md          <- Source of truth. 6-layer architecture (1294 lines, 17 research-backed changes).
src/keystone/                <- Production code: models, events, contracts, and 7 built components.
src/keystone/tool_names.py   <- Single source of truth for MCP tool name constants. Import from here.
docs/ARCHITECTURE.md         <- Code architecture, module map, dependency rules. Regenerated Session 15.
audit/                       <- Implementation spec, gap triage, plan audit, Batch 2 analysis.
audit/batch-2-analysis/      <- Per-report analyses + master synthesis from Batch 2 deep research.
audit/track-1-session/       <- Track 1 architecture finalization: change specs, verification, audit.
reference/analysis/          <- Repo analysis (00-09), Batch 1 deep research (01-10), LEAK-SYNTHESIS.md.
synthesis/                   <- UNIFIED-SYNTHESIS.md, PLAN-CHANGELOG.md, thread analyses/summaries.
research-reports/            <- 16 original deep research reports (Batch 1).
research-reports/batch-2/    <- 10 new deep research reports addressing open architectural questions.
reference/nano-claude-code/  <- Python reimplementation of Claude Code (11.8K lines, 56 files).
```

## Deployment Context

Target: Claude Max plan. Minimal external API dependencies.
Model mixing: Opus for L0/L4 (judgment), Sonnet for L1 (throughput), Haiku for extraction/classification.
Cost target: $12-$100 per engagement (validated in Gap #7).
Parallelism: Start with 3-5 agents, tier up organically (Gap #8).

## Architectural Convictions

These shape every recommendation and evaluation:

1. **Harness > model.** Same model: 17% vs 92% depending on harness (empirical). Value = orchestration + specification + accumulated knowledge.
2. **Specification layer IS the system.** The .md files defining methodology and quality criteria are the only irreplaceable component.
3. **Evaluation > Generation.** The Evaluator is more important than any generator.
4. **Structure over intent.** Quality enforced by architecture, not prompt compliance. Instructions drift ~40%.
5. **Capability expansion, not cost reduction.** "What research would you do if cost dropped 10x?"

## The Pipeline (reference only -- full detail in CAPSTONE-PLAN-v2.md)

```
META  -> Self-Improvement (Observation Library, prompt evolution, trajectory storage)
L0    -> Specification Engine (question -> RESEARCH.md spec -> dispatch)
L1    -> Parallel Research Agents (isolated, JIT context, anti-confirmatory)
       -> CitationProcessor (cross-agent dedup, corroboration scoring, URL verification)
L1.5  -> Deliberation (independent parallel analysis + structured aggregation, NOT debate)
L2    -> Content Structuring (consulting frameworks, sprint contracts, claim-level handoffs)
L3    -> Generation (deliverables, citations, format templates)
L4    -> Evaluator (10-dimension rubric, 5-layer eval stack, Observation Library)
```

## Orientation

New session? Read these files first:
1. This file (auto-loaded in Claude Code)
2. `CURRENT-STATE.md` -- Living snapshot of where we are, what's next, what's blocked
3. `JACK-ARCHITECTURAL-DIRECTIVES.md` -- Jack's authoritative design decisions (issue trees, dynamic agents, iterative research, engagement scope, build philosophy). Required reading for any architecture work.

For full project history: `SESSION-LOG.md`.

## Session Handoff Protocol

**Before finishing any session, do both:**
1. Append a new entry to `SESSION-LOG.md` with: date, agent type, task summary, files created/modified (full paths), key decisions, what comes next.
2. Rewrite `CURRENT-STATE.md` to reflect the current project state after your work.

## Working Rules

- **Read CAPSTONE-PLAN-v2.md before making architectural recommendations.** Read the relevant sections, not just the top.
- **Cross-reference RESEARCH-PROMPTS-FINAL.md** when analyzing any research report to understand what was asked.
- **Connect findings to specific pipeline layers.** Generic observations are useless.
- **Make verdicts, not inventories.** Every tool/framework/pattern -> ADOPT (use directly) / ADAPT (modify for our context, specify how) / SKIP (not applicable, say why) / INVESTIGATE (promising, needs more research) + one-sentence justification.
- **Flag contradictions between reports.** They were produced independently. Contradictions are signal.
- **Distinguish evidence quality:** Verified (empirical, reproduced) / Credible (active project, reputable source) / Claimed (blog/tweet, no evidence) / Stale (6+ months old, superseded)

## Communication & Output Rules

- Lead with the answer. Explanation follows only if needed.
- Take positions with explicit confidence levels. No passive hedging.
- When a finding has multiple defensible interpretations, steel-man each before concluding.
- If a task specification or architectural assumption seems wrong, flag it before executing.
- Verify outputs. Don't assume correctness. Detection over hope.
- No em dashes, sycophantic openers, corporate filler, meta-commentary, or emotional padding.
- When the approach is wrong, propose the redesign, not the hotfix.
- If a tool or method fails, try 2-3 alternatives before reporting a limitation.

## Key Terms

Use precisely when relevant:

- **RESEARCH.md** -- Engagement specification. Every agent reads it, every output validates against it.
- **Observation Library** -- Expanded from Rejection Library. Captures all outcomes (successes + failures) -> structured entries -> permanent constraints + reinforced patterns.
- **DPVI** -- Decompose-Parallelize-Verify-Iterate.
- **Handoff Contracts** -- Explicit I/O/quality definitions at every pipeline boundary.
- **Goldman-grade** -- "Would a domain expert call this solid on its own merits?"
- **Sprint Contracts** -- Quality specs negotiated between generator and evaluator per section.
- **CitationProcessor** -- Dedicated stage between L1 and L1.5. Cross-agent dedup, corroboration scoring, URL verification, citation manifest.

## Empirical Anchors

| Stat | Source | Proves |
|------|--------|--------|
| 17% -> 92% | Claude Code + LangSmith | Harness > model |
| 96.5% SpreadsheetBench | AutoAgent | Self-optimizing harness > hand-engineering |
| 29-30% false claims | Claude agentic | Evaluator catches ~1/3 of output |
| 78% vs 42% | Same model, Nate Mar 6 | Structure > capability |
| 68.8% leakage | AgentLeak benchmark | Isolation must be structural, not framework-level |
