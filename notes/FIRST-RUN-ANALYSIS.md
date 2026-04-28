# First Pipeline Run Analysis

**Date:** 2026-04-23
**Tests run:** L0 specification engine, L1 deep-mode research, downstream layers (CitProc + L1.5 + L4)
**Status:** L1 deep mode COMPLETE, downstream layers IN PROGRESS, L0 re-running after timeout fix

---

## 1. L1 Deep Mode vs Batch-1 Report 1: Side-by-Side

Both cover the same topic: "Multi-Agent Research & Analysis Systems."

### Quantitative Comparison

| Metric | Pipeline L1 (single deep-mode agent) | Batch-1 Report 1 (Claude deep research) |
|---|---|---|
| Total claims/assertions | 28 | ~50+ (narrative, not structured) |
| Sources cited | 46 | ~30-40 (inline citations) |
| Real URLs | 46/46 (100%) | N/A (narrative with inline refs) |
| Unique systems analyzed | ~15 | 8 deep + 3 shallow |
| Depth per system | 2-4 sentences each | 1-2 paragraphs each |
| Absence report items | 9 | 0 (no structured absence report) |
| Anti-confirmatory claims | 3 (claims 14, 15, 20) | Embedded throughout |
| Actionable verdicts | 3 (adopt/adapt/skip on last 3 claims) | Full USE/LEARN/SKIP matrix |
| Search infrastructure coverage | Mentioned briefly | Deep section with pricing, benchmarks |
| Benchmark data | DeepResearchGym + DeepResearch Bench mentioned | Full leaderboard table with RACE scores |
| Output structure | Flat JSON array of claims | Narrative with sections, tables, clear flow |
| Total length | ~3,500 words (structured JSON) | ~5,000 words (narrative markdown) |

### Qualitative Assessment

**Where the pipeline output is comparable or better:**
- **Citation quality:** Every claim has real, verifiable URLs. The batch-1 report has inline references but they're not structured or independently verifiable.
- **Absence report:** The pipeline's 9-item absence report is genuinely useful — "no evidence of MBB-grade validation," "no documentation on proprietary data handling," "no comparison of fractal vs scatter-gather architectures." Batch-1 has no equivalent.
- **Confidence calibration:** Each claim has a numeric confidence (0.77-0.93) with substantive caveats. Batch-1 uses informal evidence quality tags (Verified/Credible/Claimed/Stale) in the system prompt but doesn't apply them consistently per claim.
- **Recency:** Pipeline found April 2026 sources (Gemini Deep Research Max, arXiv:2604.02460). Batch-1 was run in March 2026 and reflects that cutoff.
- **Anti-confirmatory claims:** Claims 14-15 directly challenge the multi-agent thesis with peer-reviewed evidence. Batch-1 is more advocacy-oriented — it validates Keystone's architectural convictions rather than challenging them.

**Where the batch-1 report is significantly better:**
- **Analytical depth per system:** Batch-1 spends a full paragraph on GPT-Researcher's architecture, then a second paragraph on its weaknesses, then specific actionable recommendations. The pipeline produces 2-4 sentences per system.
- **Strategic synthesis:** Batch-1 ends with "compose the commodity, build the moat" — a genuine strategic insight that connects all the findings. The pipeline produces a flat list of claims without hierarchical reasoning.
- **Narrative structure:** Batch-1 flows logically from landscape survey → patterns worth stealing → search infrastructure → benchmarks → USE/LEARN/SKIP matrix → what must be built new. The pipeline output is an unstructured JSON array.
- **Cross-system pattern recognition:** Batch-1 identifies that "every system enforces quality through prompts, not architecture" — a meta-observation drawn across all 8 systems. The pipeline doesn't synthesize across claims.
- **Actionable specificity:** Batch-1's LEARN recommendations include specific implementation guidance ("steal the pattern from 199-Bio's Dynamic Outline Evolution Phase 4.5"). Pipeline's verdicts are one sentence each.
- **Benchmark interpretation:** Batch-1 extracts specific RACE scores, creates a leaderboard table, and draws strategic implications ("specialized multi-agent systems now beat all major commercial platforms by 8-10 RACE points"). Pipeline mentions the benchmarks exist but doesn't interpret them.

### Root Cause of the Depth Gap

The depth gap is not a model capability issue — both use Claude. It's structural:

1. **Single pass vs iterative:** The pipeline ran ONE deep-mode session. Batch-1 was created through a multi-turn deep research session where the model could search → read → follow citations → search again → synthesize. The pipeline's deep mode does this internally within one `claude -p` call, but it's bounded by the prompt and timeout.

2. **No synthesis layer in L1:** The pipeline produces raw claims. There's no step that takes 28 claims and produces a narrative synthesis with cross-claim pattern recognition. The existing synthesis.md prompt handles per-round synthesis but doesn't do the meta-level "what does this all mean together" step.

3. **Structured JSON vs narrative:** The deep_research.md prompt asks for JSON output. This constrains the model to produce atomic claims rather than flowing analytical prose. A McKinsey analyst would never deliver a JSON array — they'd deliver a narrative with tables and recommendations.

4. **No specification input:** The pipeline agent received a task description and acceptance criteria, but not the kind of deep specification the batch-1 prompt had ("evaluate deeply: GPT-Researcher, STORM, 199-Bio, Cranot" with specific sub-questions for each). The prompt from RESEARCH-PROMPTS-FINAL.md was ~800 words of targeted guidance. The pipeline's task description was ~50 words.

---

## 2. L0 Specification Engine Observations

### What worked:
- Classification: `strategic / deep` — reasonable
- Intent clarification: completed (but see issues below)  
- Decomposition: 15 leaves, depth 2, MECE validation passed
- Priority scoring: 15 priorities scored

### Issues found:

**ISSUE L0-1: Hardcoded decomposition lenses (CRITICAL)**
`_LENSES = ["financial", "operational", "market"]` in `decomposer.py:56`.
For a question about building an agentic research system, financial and market lenses are nonsensical. The lenses should be dynamically selected based on the question domain. Already added to TODO.

**ISSUE L0-2: Intent clarifier doesn't ask clarifying questions**
`intent_clear=True` on a complex, multi-faceted question about building an entire system. A real analyst would ask: "What's the primary use case? What engagement types? What's the team size? What's the budget for API costs? Should this handle slide generation or just research?" The intent clarifier should have a lower threshold for asking questions on complex/ambiguous inputs.

**ISSUE L0-3: Timeout on task generation (300s → dead letter)**
The task generation step tries to produce structured JSON for all 15 tasks in one LLM call. This timed out 3/3 attempts at 300s. Fixed by increasing default to 600s, but the root cause is generating all tasks in one call. Should chunk into batches of 5.

**ISSUE L0-4: EngagementType taxonomy is consulting-scoped**
`EngagementType` enum: SIZING, DIAGNOSTIC, EVALUATIVE, STRATEGIC, EXPLORATORY. A question about building a software system doesn't cleanly map to any of these. Need either a broader taxonomy or dynamic category generation.

**ISSUE L0-5: TaskCategory enum too narrow**
`TaskCategory`: MARKET_SIZING, COMPETITIVE_LANDSCAPE, FINANCIAL_ANALYSIS, TECHNOLOGY_ASSESSMENT, REGULATORY, STRATEGIC_POSITIONING. No categories for "systems architecture," "evaluation design," "prior art survey," "process design," etc. The `custom_category` escape hatch exists but relies on the LLM knowing to use it.

**ISSUE L0-6: No process visibility / intermediate artifacts**
There's no way to inspect what the three lens decompositions produced, what the MECE validator checked, or what the priority scores were. All intermediate state is in-memory only. For debugging and quality assurance, each L0 step should write its intermediate output to a file.

---

## 3. Downstream Layers Observations (from Session 3)

### CitationProcessor: WORKING
- 7 citations processed, URL liveness checks ran
- 2 dead URLs correctly flagged (1 intentionally fake, 1 actual 404)
- Completed in 10.7s
- No issues observed

### L1.5 Deliberation: WORKING (with observations)
- 4 analysts spawned (ACH, quantitative, adversarial, historical_analogy)
- All 4 completed independently in ~2.5 minutes
- Aggregation completed, confidence map produced
- 3 convergent findings, 3 genuine disagreements, 3 blind spots, 3 gaps
- Completed in 326.3s (~5.5 minutes)

Observation: The 4 methodology types (ACH, quantitative, adversarial, historical_analogy) are fixed. For a technical architecture question, more appropriate methodologies might include "systems engineering assessment," "failure mode analysis," "comparative architecture review." Same one-size-fits-all issue as the L0 lenses.

### L4 Evaluator: IN PROGRESS
- Running the 3-layer evaluation (deterministic checks, citation gate, rubric scoring)
- Results pending

---

## 4. Pipeline-Wide Issues

### No iterative research capability
The pipeline runs L1 once and moves on. There's no mechanism for:
- Gap identification → spawn additional research to fill gaps
- Cross-agent contradiction detection → targeted research to resolve
- Depth assessment → "this topic needs more research" → additional rounds
This is the single biggest gap between the pipeline and the manual process that produced CAPSTONE-PLAN-v2.md.

### No clarification / scoping conversation
The pipeline takes a question string and immediately decomposes it. There's no interactive phase where the system helps the user refine their question, scope the engagement, or identify what's most important. This was flagged as critical by Jack — messy, dictated input is the normal case, and the system needs to handle it.

### No intermediate visibility
There's no way to inspect what each layer produced without reading the code and adding print statements. Each layer should write its output to a structured file:
- L0: `output/{engagement_id}/l0_spec.json`, `l0_issue_tree.json`, `l0_tasks.json`
- L1: `output/{engagement_id}/l1_findings/task_{id}.json` per task
- CitProc: `output/{engagement_id}/citation_manifest.json`
- L1.5: `output/{engagement_id}/l15_confidence_map.json`
- L4: `output/{engagement_id}/l4_evaluation.json`
- Render: `output/{engagement_id}/final_brief.md`

### Output format is JSON, not narrative
The pipeline produces StructuredFinding (JSON with claims array), not a narrative analytical brief. The MarkdownRenderer exists but it renders from the structured data — it doesn't produce the kind of flowing analytical prose that a McKinsey analyst would write. The gap between "28 JSON claims" and "a 15-page analytical brief" is significant.

### One-size-fits-all defaults pervade the system
- L0 lenses: financial/operational/market (hardcoded)
- L0 engagement types: consulting-scoped enum
- L0 task categories: consulting-scoped enum  
- L1.5 analyst methodologies: ACH/quantitative/adversarial/historical_analogy (fixed)
- Tool assignment: BASELINE_AGENT_TOOLS includes edgar_filings regardless of topic
- Default methodology: Porter's Five Forces for evaluative engagements

All of these should be dynamically selected based on the question domain.

---

## 5. Verdict

**The pipeline works.** All layers execute with real LLM calls and produce valid output. Deep-mode research finds real sources with real URLs. The citation chain is intact. Deliberation produces independent analyst assessments. The architecture is sound.

**The pipeline doesn't match the manual research quality yet.** The gap is not model capability — it's structural. The key missing pieces are:
1. Dynamic decomposition (lenses, categories, analyst types selected per question)
2. Iterative research (gap-fill, contradiction-resolve, depth-assess cycles)
3. Interactive scoping (clarifying questions before decomposition)
4. Narrative synthesis (flowing analytical prose, not JSON claims)
5. Process visibility (intermediate artifacts for debugging and quality assurance)
6. Task specification depth (50-word task descriptions vs 800-word research prompts)

These are all buildable. Items 1 and 6 are the highest leverage — they directly determine whether the research agents find the right things at sufficient depth.
