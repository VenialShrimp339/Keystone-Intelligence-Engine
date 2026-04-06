---
name: research-synthesis
description: Methodology for analyzing the 16 deep research reports and synthesizing findings into architecture decisions. Use when analyzing reports, cross-referencing findings, producing BUILD/INTEGRATE/LEARN/SKIP verdicts, or updating the capstone plan.
---

# Research Synthesis Methodology

You are synthesizing 16 deep research reports into actionable architecture decisions for the Keystone Intelligence Engine.

## Phase 1: Report-by-Report Analysis

For each of the 16 reports (cross-reference with `RESEARCH-PROMPTS-FINAL.md` to understand what was asked):

1. **Top 3-5 findings** that change or validate architectural decisions in CAPSTONE-PLAN-v2.md
2. **Tool/framework verdicts**: Every tool mentioned gets one of:
   - **BUILD** — We should build this ourselves (explain why existing options fail)
   - **INTEGRATE** — Use this directly as a component (specify version, maturity, integration point)
   - **LEARN** — Steal the pattern/approach but build our own implementation (explain the pattern)
   - **SKIP** — Exists but not relevant (one sentence why)
3. **Contradictions** with CAPSTONE-PLAN-v2.md (what the plan says vs what the evidence shows)
4. **Cross-report contradictions** (flag for resolution in Phase 2)

### Report Thread Map
- **A1-A5** (Reports 1-5): Open source landscape, evaluation frameworks, self-improvement, orchestration, deep research tooling
- **B1-B4** (Reports 6-9): What partners value, decision-useful research, quality of thought, AI failure modes
- **C1-C4** (Reports 10-13): Specification-driven dev, deliberation, report generation, data retrieval
- **D1-D3** (Reports 14-16): Best small-team AI systems, academic papers, 10x ideas

## Phase 2: Cross-Report Synthesis

After all 16 reports are analyzed:

1. **Unified verdict matrix** — All tools/frameworks with BUILD/INTEGRATE/LEARN/SKIP, organized by pipeline layer
2. **Contradiction resolution** — When reports disagree, analyze WHY (different evidence, different assumptions, different scope) and recommend
3. **Convergent findings** — Insights that appear across 3+ reports independently (highest confidence)
4. **Remaining gaps** — What questions are still unanswered after all 16 reports?

## Phase 3: Architecture Update Specification

Produce specific, implementable updates to CAPSTONE-PLAN-v2.md:

- New tool integrations per component
- Architectural decision changes backed by evidence
- Evaluator rubric updates (from B1-B4 quality research)
- Self-improvement mechanisms (from A3)
- Deliberation layer changes (from C2)

Every update must cite the report(s) and specific finding(s) that justify it.

## Phase 4: Implementation Priority

- **Phase 1 (build first):** Core pipeline — what must exist for anything to work
- **Phase 2 (build next):** Quality compounding — what makes the system get better over time
- **Phase 3 (defer):** Extensions that add capability but aren't load-bearing

For each item: recommended tools, estimated complexity (S/M/L/XL), dependencies on other items.

## Output Standards

- **Specificity over breadth.** "Use PydanticAI for agent definition because it enforces type-safe handoff contracts (Report A4, p.12)" > "Several frameworks could work."
- **Honest assessment.** "This exists and is better than what we planned" is more valuable than diplomacy.
- **Contradictions are signal.** Don't smooth them over. Analyze why they exist and pick a side.
- **Trace to architecture.** Every finding maps to a specific layer in the pipeline. If it doesn't map, it probably doesn't matter.

## Evidence Quality Tiers

Apply consistently across all analysis:

- ✅ **Verified**: Empirically validated, reproduced, or from authoritative primary source
- 🟡 **Credible**: Well-reasoned with supporting evidence, from reputable practitioner
- ⚠️ **Claimed**: Single source, not independently verified, anecdotal
- ❌ **Stale**: Tool deprecated, framework abandoned, information outdated

When a finding carries a ⚠️ or ❌ rating, say so explicitly. Don't bury uncertainty.
