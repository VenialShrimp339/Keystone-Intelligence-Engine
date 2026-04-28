# First Run Analysis: Synthesized Findings and Priorities

**Date:** 2026-04-23
**Sources:** 4 parallel analysis agents covering L0, L1, downstream layers, and codebase-wide one-size-fits-all audit. ~165KB of analysis across 1,843 lines.

---

## What works

The pipeline executes. Every layer ran with real LLM calls via `claude -p`. Deep-mode research found 46 real sources with real URLs. CitationProcessor verified URLs. Deliberation ran 4 independent analysts in parallel and aggregated them. The citation chain fix (B-1) held — no `ref://` placeholder URLs. The architecture is sound.

---

## The five structural gaps (ranked by impact on output quality)

### 1. Task specification depth (CRITICAL — highest leverage single fix)

**The gap:** L0 generates task descriptions of ~50-100 words. The benchmark prompts that produced MBB-grade research were ~800 words each, with named entities to investigate, per-entity sub-questions, quantitative benchmarks to seek, and focal synthesis questions.

**The evidence:** The L1 deep-mode agent produced 28 claims at 2-4 sentences each. The benchmark report produced 8 deep analyses at 1-2 paragraphs each with specific implementation recommendations. Both used the same model (Claude). The difference is entirely prompt quality.

**The fix:** Redesign `task_generation.md` to produce 150-300 word task descriptions with structured fields: `specific_entities` (named systems/papers/tools to investigate), `sub_questions` (3-5 targeted questions per entity), `focal_question` (the synthesis question that ties findings together), and `required_source_types` (what kinds of evidence to seek). This doesn't require architectural changes — just a better prompt and a richer ResearchTask schema.

**Impact:** This single change likely closes 50-60% of the quality gap between pipeline output and the benchmark.

---

### 2. Dynamic decomposition — lenses, categories, analyst types (CRITICAL)

**The gap:** 9 CRITICAL hardcoded defaults, 11 HIGH defaults, all encoding consulting-engagement assumptions. The financial/operational/market lenses, the consulting-scoped EngagementType and TaskCategory enums, the fixed deliberation analyst types, the mandatory Porter's Five Forces framework, the EDGAR tool in generalist templates — all produce nonsensical output for non-consulting questions.

**The evidence:** Applied to "design an agentic research system," the financial lens would produce branches about revenue models and unit economics. The correct lenses for this question would be technical architecture, existing systems landscape, and quality/evaluation methodology.

**The fix (multi-part):**
- **Lens selector:** New `LensSelector` pre-step that analyzes the question domain and selects 2-4 appropriate lenses from a larger menu. Replace hardcoded `_LENSES` list and the three hardcoded prompt files with a parameterized generic lens prompt.
- **EngagementType expansion:** Add DESIGN, TECHNICAL_EVALUATION, COMPARATIVE, LITERATURE_SYNTHESIS, PROCESS_ANALYSIS. Or make it an LLM-generated classification rather than a fixed enum.
- **TaskCategory expansion:** Add SYSTEMS_ARCHITECTURE, EVALUATION_DESIGN, PRIOR_ART_SURVEY, PROCESS_DESIGN, LITERATURE_REVIEW. Or use `custom_category` by default and let the LLM classify freely.
- **Deliberation analyst types:** Make the `analyst_types` parameter (which already exists on the Deliberation constructor) dynamic based on engagement domain. Technical → systems engineering, failure mode, comparative architecture. Business → current four types.
- **Template registry:** Add `technical_researcher` and `scientific_researcher` templates without EDGAR tools.

**Impact:** Unblocks the pipeline for any research question, not just consulting-company-analysis.

---

### 3. Interactive scoping / clarification (HIGH)

**The gap:** The intent clarifier returned `intent_clear=True` on a complex, multi-faceted question with at least 5 unresolved ambiguities. Even when `intent_clear=False`, the pipeline has no mechanism to actually ask the user questions and wait for answers. The pipeline takes a string and immediately decomposes it — there's no conversation.

**The evidence:** The original manual process involved extensive back-and-forth between Jack and his OpenClaw agent to scope the project, identify research areas, and refine the question. The pipeline skips all of this.

**The fix:** Two parts:
- **Lower the intent_clear threshold:** Add a 5th clarity condition: "success criteria are specific enough that two analysts would agree whether research succeeded."
- **Build a clarification loop:** When `intent_clear=False`, the pipeline should emit a `ClarificationNeeded` event with specific questions, pause, and wait for user input before proceeding. This requires a new event type and a HITL-like gate in the orchestrator.

**Impact:** Prevents the pipeline from confidently decomposing ambiguous questions into wrong tasks. Essential for messy, dictated input.

---

### 4. Iterative research with gap-filling (HIGH)

**The gap:** The pipeline runs L1 once and moves on. There's no mechanism for: gap identification → spawn additional research, cross-agent contradiction detection → targeted resolution, depth assessment → "this topic needs more" → additional rounds. The manual process that produced CAPSTONE-PLAN-v2.md involved multiple rounds of research, synthesis, gap identification, and additional research.

**The evidence:** The L1 output identified 9 absence items but took no action on them. In the manual process, each gap would have spawned additional deep research.

**The fix:** Add a post-L1 gap analysis step:
1. After L1 completes, run a gap-analysis LLM call on the collected findings
2. If gaps are significant, generate additional tasks targeting the gaps
3. Run a second L1 pass on the gap-fill tasks only
4. Merge gap-fill findings into the original findings
5. Cap at 2-3 iterations to prevent runaway cost

**Impact:** This is the capability that transforms the pipeline from "one-shot research" to "iterative analyst workflow." It's the difference between producing a survey and producing an analysis.

---

### 5. Narrative synthesis layer (MEDIUM — but affects perceived quality most)

**The gap:** The pipeline produces a flat JSON array of 28 atomic claims. The benchmark produces a 5,000-word analytical brief with sections, tables, strategic insights, and a USE/LEARN/SKIP decision matrix. The JSON-to-narrative gap is where "technically correct" fails to become "partner-ready."

**The evidence:** The benchmark's most valuable insight — "every system enforces quality through prompts, not architecture" — is a synthetic observation that cannot be expressed as a single JSON claim with a single citation. It emerges from cross-system pattern recognition.

**The fix:** Add a synthesis step between L1 findings and L1.5 deliberation:
1. Take the collected StructuredFindings from all tasks
2. Run a FLAGSHIP LLM call that produces cross-cutting themes, contradictions, and strategic implications
3. Generate a narrative synthesis with hierarchical structure
4. Feed this richer input to deliberation

**Impact:** Transforms output from "useful data" to "useful analysis." Without this, the pipeline produces research material, not a deliverable.

---

## Infrastructure fixes (required but lower priority than structural gaps)

| Fix | Description | Effort |
|---|---|---|
| **Timeout increase** | `claude -p` timeout from 300s to 600s (done). Background task timeout needs to match. | Done |
| **Task generation chunking** | Generate tasks in batches of 5 instead of all 15-50 in one call | 1 hour |
| **Fact decomposition chunking** | L4 evaluator should chunk claims into batches of 5-8 for fact extraction | 1 hour |
| **Process visibility** | Each layer writes intermediate output to `output/{engagement_id}/` | 2 hours |
| **5th analyst** | Deliberation should use 5 analysts (fixes bimodal confidence distribution from 4-analyst panel) | 30 min |
| **URL retry** | CitationProcessor's URL checker should retry on transient HTTP errors, not immediately mark as dead | 30 min |
| **Source quality scores** | Replace uniform `quality_score: 0.7` with actual source quality differentiation (arxiv > medium blog) | 2 hours |

---

## Recommended execution order

**Phase A — Unblock the first real run (1-2 sessions):**
1. Task generation chunking (prevents timeout crash)
2. Fact decomposition chunking (same)
3. Process visibility (write intermediate outputs)
4. Increase background task timeouts

**Phase B — Close the quality gap (2-3 sessions):**
5. Task specification depth redesign (highest leverage)
6. Dynamic lens selection (replace hardcoded financial/operational/market)
7. TaskCategory and EngagementType expansion
8. Template registry expansion (technical/scientific researcher templates)

**Phase C — Match the manual workflow (2-3 sessions):**
9. Interactive clarification loop
10. Iterative research with gap-filling
11. Dynamic deliberation analyst types
12. Narrative synthesis layer

**Phase D — Polish (1-2 sessions):**
13. 5th deliberation analyst
14. Source quality differentiation
15. URL retry logic
16. Remaining one-size-fits-all fixes from audit
