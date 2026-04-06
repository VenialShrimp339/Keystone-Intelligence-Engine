# Track 1: Architecture Document Finalization
## Claude Code Session Prompt

*This prompt drives the most sensitive step in the Keystone Intelligence Engine project: updating the two documents that become the single source of truth for every subsequent builder session. Errors here propagate to every downstream component.*

---

## PHASE 0: MANDATORY CONTEXT LOADING

**Before you write a single character of new content, you must read every file listed below in full.** These files contain the project's complete architectural history, settled decisions, and the specific changes to be made. Skipping or skimming any of these will produce errors that cascade through the entire build phase.

### Read in this exact order:

**Tier 1 — Project identity (read first, establishes the frame):**
1. `CLAUDE.md` — Project overview, architectural convictions, working rules, key terms
2. `CURRENT-STATE.md` — Where we are right now, what's complete, what's next
3. `JACK-ARCHITECTURAL-DIRECTIVES.md` — **THE HIGHEST AUTHORITY IN THIS PROJECT.** Jack's 14 design decisions. Every edit you make must comply with every directive. Pay extreme attention to Directive 13 (Phase 1 Depth Staging) — it contains the explicit Phase 1 vs. Phase 2 lists that govern what gets built now vs. later.

**Tier 2 — The files you will be editing:**
4. `CAPSTONE-PLAN-v2.md` — **READ IN FULL. ALL 1,294 LINES.** This is the master architecture document. You will be making 48 surgical edits across 6 sections. You need to understand the entire document's structure, prose style, and existing content before changing anything.
5. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — **READ IN FULL.** The component-level build spec. You will update this after CAPSTONE-PLAN is finalized.

**Tier 3 — The change specifications (what to change and why):**
6. `audit/batch-2-analysis/MASTER-SYNTHESIS.md` — **READ IN FULL, especially Section 9** (lines ~424-485: "Recommended Changes to CAPSTONE-PLAN-v2.md"). This contains the 48 specific changes organized by section. Also read Sections 1-8 for the evidence and reasoning behind each change.
7. `synthesis/UNIFIED-SYNTHESIS.md` — The Batch 1 synthesis that the current plan is based on. Needed to understand what `[SYNTHESIS UPDATE]` tags reference.

**Tier 4 — Additional context for cross-referencing:**
8. `PARALLEL-EXECUTION-PLAN.md` — Contains Phase 1/Phase 2 staging decisions and the overall build sequence. **WARNING:** Some staging classifications in this file conflict with Directive 13 in JACK-ARCHITECTURAL-DIRECTIVES.md. When they conflict, **Directive 13 always wins.**
9. `src/keystone/models/` — Read all files in this directory. These are the existing Pydantic models that define the data structures.
10. `src/keystone/contracts.py` — Existing Protocol interfaces. Changes must not break these.
11. `src/keystone/events.py` — Existing event types.

**DO NOT READ** the following files (they waste context and are not relevant to this task):
- `research-reports/` (any raw research reports)
- `reference/` (reference implementations)
- `nate-synthesis/` (superseded by UNIFIED-SYNTHESIS)
- `COWORK-SESSION-HISTORY-CONDENSED.md`
- Individual analysis files in `audit/batch-2-analysis/analysis-*.md` (the MASTER-SYNTHESIS already synthesizes these)

### After reading, confirm your understanding by writing a brief note to `audit/track-1-session/context-verification.md`:
- Number of directives in JACK-ARCHITECTURAL-DIRECTIVES.md
- Number of recommended changes in MASTER-SYNTHESIS Section 9
- The section headers of CAPSTONE-PLAN-v2.md with their line ranges
- Any conflicts you noticed between files (especially between PARALLEL-EXECUTION-PLAN.md and Directive 13)

This verification step catches context loading errors before they corrupt edits.

---

## PHASE 1: PARALLEL ANALYSIS (3 Opus Subagents)

### Architecture

You will spawn 3 parallel Opus 4.6 subagents. Each subagent deeply analyzes their assigned sections of CAPSTONE-PLAN-v2.md and produces a **Change Specification File** — a detailed document specifying exactly what text to change, the replacement text, and the rationale. **No subagent edits CAPSTONE-PLAN-v2.md directly.** All changes are applied by you (the orchestrator) in Phase 2 after reviewing all three specs for consistency.

### Why this architecture

- **Parallel analysis, serialized editing** prevents merge conflicts and cross-section inconsistencies
- Each subagent can focus deeply on ~2 sections rather than all 6, reducing the chance of attention fatigue
- The orchestrator catches cross-section inconsistencies before any edit is applied
- The change specification format is reviewable — Jack can inspect the plan before it's executed

### Subagent shared context

Every subagent receives the same context block. Assemble this by concatenating:
1. The project overview from CLAUDE.md (first 50 lines)
2. JACK-ARCHITECTURAL-DIRECTIVES.md **in full** (every directive, especially 13)
3. MASTER-SYNTHESIS.md Section 1 (The Architecture That Emerges) — the narrative context
4. MASTER-SYNTHESIS.md Section 9 (the 48 changes) — the change spec
5. The Phase 1/Phase 2 explicit lists from Directive 13
6. The complete CAPSTONE-PLAN-v2.md — **every subagent reads the full file**, not just their sections

### Critical section-to-file mapping

The MASTER-SYNTHESIS Section 9 refers to sections by topic, not by the CAPSTONE-PLAN's numbering. Here is the exact mapping:

| MASTER-SYNTHESIS Reference | Actual CAPSTONE-PLAN Section | Line Range |
|---|---|---|
| "Section 3 (Specification Engine)" | ## 3. The Specification Engine (Layer 0) | Lines 126-306 |
| "Section 4 (Research & Analysis)" | ## 4. The Research & Analysis Engine | Lines 307-527 |
| "Section 5 (Evaluator)" | ## 5. The Evaluator: The Most Important Component | Lines 528-684 |
| "Section 6 (Retrieval)" | ## 6. Internal Document Integration, specifically §6.2 Unified Retrieval Architecture | Lines 685-758 (retrieval is 701-731) |
| "Section 7 (Observation Library)" | ## 7. The Self-Improvement Loop | Lines 759-924 |
| "Section 12 (Infrastructure)" | ## 12. Implementation Roadmap | Lines 1093-1187 |

**This mapping is critical.** "Section 6 (Retrieval)" in the MASTER-SYNTHESIS does NOT mean Section 6 of the CAPSTONE-PLAN as a whole — it means the Unified Retrieval Architecture subsection within Section 6.

---

### SUBAGENT A: Specification Engine + Research Engine
**Assigned sections:** §3 (lines 126-306) + §4 (lines 307-527)
**MASTER-SYNTHESIS changes:** #1-22 (22 changes)
**Coupling:** HIGH — these sections describe the tightly coupled L0→L1 pipeline

**Spawn this subagent with the following prompt:**

```
You are analyzing Sections 3 and 4 of CAPSTONE-PLAN-v2.md for the Keystone Intelligence Engine project and producing a Change Specification File.

## YOUR TASK
For each of the 22 changes assigned to you (MASTER-SYNTHESIS Section 9, Changes #1-22), produce a detailed change specification. You do NOT edit the file directly. You produce a specification that the orchestrator will review and apply.

## THE 22 CHANGES ASSIGNED TO YOU

### Section 3 (Specification Engine), Changes #1-10:
1. Replace 7-step flow with 10-step flow
2. Add engagement type classifier (5-type taxonomy)
3. Add Decision-First CoT + TiCoder divergence detection for intent clarification
4. Add issue tree construction with heterogeneous consulting lenses (3-4 Sonnet agents)
5. Add MECE verification as discrete step (Opus evaluator, five dimensions, binary criteria)
6. Add Day-1 Hypothesis as required output
7. Add VOI-inspired priority scoring formula
8. Add Observation Library CBR query at Spec Engine entry
9. Change research-tasks.json to DAG structure (not flat list)
10. Add per-branch "end product" specification

### Section 4 (Research & Analysis), Changes #11-22:
11. Add iterative research loop specification: 3 default rounds, 5 max, three-criterion stopping
12. Add scope-change detection protocol (In-Plan / Out-of-Plan classification)
13. Add orchestrator Memory scratchpad as first-class data structure
14. Convert 5 fixed agent types to seed templates in registry
15. Add template registry query + interpolation as dispatch mechanism
16. Add tighten-only constraint invariant
17. Add token budget as explicit agent configuration field
18. Add 1,000-2,000 token condensed output requirement for subagents
19. Add artifact bypass pattern (structured summary + full external file)
20. Change deliberation aggregation from ambiguous "structured aggregation" to explicit "claim-level selection"
21. Add "What Would You Have to Believe?" step for low-confidence findings
22. Add ADaPT-style reactive decomposition within L1 research rounds

## PHASE 1 vs PHASE 2 CLASSIFICATION

For EVERY change, you must classify it as [Phase 1] or [Phase 2+]. The authoritative source is Directive 13 in JACK-ARCHITECTURAL-DIRECTIVES.md. Here are the explicit lists:

**Ship in Phase 1 (from Directive 13):**
- Issue tree decomposition (multi-agent with heterogeneous lenses, shallow start)
- MECE verification step
- Engagement classifier (routes to pipeline profile)
- Human review gate (database state machine)
- Template registry for agent configs (seed templates, not just enums)
- Iterative research loop (3-round default, 5 max, three-criterion stopping)
- Claim-level selection for deliberation

**Defer to Phase 2 (from Directive 13):**
- TiCoder divergence detection in intent clarification
- VOI-inspired priority scoring (use simpler heuristic scoring in Phase 1)
- CBR Observation Library query at Spec Engine entry
- Sprint contract negotiation between Evaluator and Generator
- Dimension-specific verification strategies

**The Directive 13 test:** "Can this feature be added later by extending an interface or adding a module, WITHOUT changing the data flow or rewriting existing components? If yes, defer."

For changes NOT explicitly listed in Directive 13's Phase 1/Phase 2 lists, apply the test yourself and document your reasoning.

## HOW TO HANDLE PHASE 1 vs PHASE 2 IN THE DOCUMENT

CAPSTONE-PLAN-v2.md describes the COMPLETE architecture vision, not just Phase 1. ALL 48 changes should be incorporated. But phase-sensitive items need clear marking:

**Pattern 1: Feature exists at reduced depth in Phase 1.**
Example: Step 5 (Priority Assignment) ships in Phase 1 with heuristic scoring, but the full VOI-inspired scoring is Phase 2. In the document, describe the full VOI approach, then add: `[BATCH 2 UPDATE] Phase 1 implementation uses simplified heuristic scoring (decision_relevance × uncertainty). Full VOI-inspired scoring with estimated_cost denominator ships in Phase 2.`

**Pattern 2: Feature is entirely Phase 2.**
Example: Observation Library CBR query at Spec Engine entry. Describe it in the architecture, then mark: `[Phase 2: Observation Library infrastructure required]`

**Pattern 3: Feature is Phase 1 in full.**
Example: Iterative research loop with three-criterion stopping. Describe it fully, mark as `[BATCH 2 UPDATE]`. No phase caveat needed.

The goal: a reader of CAPSTONE-PLAN-v2.md sees the complete system design. A reader of PHASE-1-IMPLEMENTATION-SPEC.md sees exactly what to build now. The two documents are complementary, not redundant.

## OUTPUT FORMAT

Write your output to: `audit/track-1-session/change-spec-A.md`

For each change, use this exact format:

```markdown
## Change #{N}: {Title}
**MASTER-SYNTHESIS Reference:** Section 9, Change #{N}
**Phase Classification:** [Phase 1] / [Phase 2+]
**Phase Rationale:** {Why this classification, referencing Directive 13 or the deferral test}
**Location in CAPSTONE-PLAN-v2.md:** Section {X}, subsection {Y}, around line {Z}

### What exists now:
{Quote the current text that will be replaced or augmented. Include enough surrounding context (2-3 lines before/after) to make the location unambiguous.}

### What it should say:
{The new or modified text. Match the existing document's prose style — this is a well-written document with clear narrative flow. Do not introduce bullet-point-heavy formatting where the original uses prose. Do not change the authorial voice.}

### Preservations:
{List any existing content in this area that must NOT be changed. Common failure: overwriting a good paragraph when only one sentence needs updating.}

### Cross-section references:
{Does this change affect or reference content in sections NOT assigned to you? If so, list the specific sections and what the other subagent needs to know.}

### Directive compliance:
{Which of Jack's 14 directives are relevant to this change, and confirmation that the change complies. Minimum: check against Directives 1, 5, 11, 13.}
```

## STYLE GUIDANCE

CAPSTONE-PLAN-v2.md is a well-written document with a distinctive voice. Your replacement text must:
- Match the existing prose style (analytical, evidence-backed, citation-heavy)
- Use the same citation format: (Jones, "Article Title," Date)
- Maintain `[SYNTHESIS UPDATE]` tags for content that was added in previous synthesis passes
- Add `[BATCH 2 UPDATE]` tags for new content from this update (so future readers know what changed when)
- Preserve section numbering (do NOT renumber sections)
- Preserve the document's table/code-block formatting conventions

## IMPORTANT CONSTRAINTS

1. Do NOT rewrite sections wholesale. Make surgical additions and modifications. The existing prose is good — add to it, don't replace it.
2. The 10-step Specification Engine flow (Change #1) is the biggest change. It replaces the current 4-step verification phase (§3.4) and 2-step scout/strike model (§3.5) with a unified 10-step pipeline. This requires careful integration, not a cut-and-paste.
3. The iterative research loop (Change #11) needs its own subsection in Section 4. It's currently implicit in the scout/strike model but needs explicit mechanical specification.
4. For the deliberation aggregation change (#20): the current text in §4.3 already describes "structured aggregation" — update it to explicitly say "claim-level selection" with the 81% vs 51.2% evidence.
5. Preserve ALL existing citations and source attributions. Never remove a citation.
```

---

### SUBAGENT B: Evaluator + Retrieval Architecture
**Assigned sections:** §5 (lines 528-684) + §6 (lines 685-758, especially §6.2)
**MASTER-SYNTHESIS changes:** #23-38 (16 changes)
**Coupling:** MODERATE — the evaluator grades retrieval quality; retrieval provides sources for evaluation

**Spawn this subagent with the following prompt:**

```
You are analyzing Sections 5 and 6 of CAPSTONE-PLAN-v2.md for the Keystone Intelligence Engine project and producing a Change Specification File.

## YOUR TASK
For each of the 16 changes assigned to you (MASTER-SYNTHESIS Section 9, Changes #23-38), produce a detailed change specification. You do NOT edit the file directly.

## THE 16 CHANGES ASSIGNED TO YOU

### Section 5 (Evaluator), Changes #23-29:
23. Add geometric mean as aggregation method for 10-dimension rubric
24. Add Tier 1 (universal gates) / Tier 2 (adaptive) rubric split
25. Expand from 2 evaluation profiles to 8-10
26. Add issue tree branch classification → weight generation mechanism
27. Specify sprint contract directionality (Evaluator proposes, Generator reviews)
28. Add dimension-specific verification strategies (Quantitative Rigor, Analytical Depth)
29. Add graceful degradation principle for evaluation scaffolding

### Section 6 (Retrieval), Changes #30-38:
CRITICAL MAPPING: "Section 6 (Retrieval)" in MASTER-SYNTHESIS maps to §6.2 "Unified Retrieval Architecture" in CAPSTONE-PLAN (lines 701-731), NOT to all of Section 6.

30. Split Component #3 into #3a (source discovery) + #3b (knowledge accumulation)
31. Add Voyage-finance-2 as primary embedding model
32. Add contextual retrieval at ingest time
33. Add Cohere Rerank v3.5 to retrieval pipeline
34. Add chunking rules (512 tokens, 50-100 overlap, tables as HTML, XBRL bypass)
35. Remove Semantic Router
36. Remove Bifrost caching
37. Add Brave Search + Exa as external discovery APIs (avoid Tavily dependency, skip Google CSE)
38. Add compiled wiki per engagement (Karpathy three-layer pattern)

## PHASE 1 vs PHASE 2 CLASSIFICATION

**Ship in Phase 1 (from Directive 13):**
- Geometric mean rubric aggregation
- Tier 1/Tier 2 rubric split
- Component #3 split (#3a discovery + #3b accumulation)
- Error recovery Layers 1-2

**Defer to Phase 2 (from Directive 13):**
- 8-10 engagement-type evaluation profiles (start with 3-4, expand)
- Sprint contract negotiation between Evaluator and Generator
- Dimension-specific verification strategies (programmatic QR, position-switching AD)
- Cross-engagement knowledge base / wiki promotion rules

**For changes NOT in the explicit lists:** Apply the Directive 13 test: "Can this be added later by extending an interface without rewriting existing components?"

## SPECIAL INSTRUCTIONS FOR RETRIEVAL CHANGES (#30-38)

The retrieval section (§6.2) currently describes:
- pgvector + pgvectorscale
- Hybrid search (dense + BM25 + RRF)
- Semantic Router for query routing
- Exa, Brave, Firecrawl, Tavily as search APIs
- Docling for PDF parsing
- Bifrost dual-layer caching
- Admiralty Code source quality scoring

The changes require:
- REMOVING Semantic Router (Change #35) — replace with simpler query classification or remove entirely
- REMOVING Bifrost caching (Change #36) — simplify caching
- REMOVING Tavily dependency (Change #37) — Exa + Brave cover the same function
- ADDING Voyage-finance-2 (Change #31) — specific embedding model, not generic
- ADDING contextual retrieval (Change #32) — Haiku-generated preamble per chunk
- ADDING Cohere Rerank v3.5 (Change #33) — top 150 → rerank → top 20
- ADDING chunking rules (Change #34) — specific parameters
- ADDING compiled wiki / Karpathy pattern (Change #38) — new subsection for knowledge accumulation
- SPLITTING #3 (Change #30) — the retrieval section now describes TWO distinct subsystems

This is the most structurally significant set of changes in the retrieval section. The existing §6.2 needs substantial rewriting, not just patching. But §6.1, §6.3, §6.4, and §6.5 should be largely preserved.

## OUTPUT FORMAT

Write to: `audit/track-1-session/change-spec-B.md`

Use the same format as Subagent A (see the template in the orchestrator's Phase 1 instructions).

## STYLE GUIDANCE

Same as Subagent A: match existing prose style, use existing citation format, add `[BATCH 2 UPDATE]` tags for new content, preserve section numbering.

## IMPORTANT CONSTRAINTS

1. The evaluator rubric table (§5.3) is a large, carefully structured table. Updating it for the Tier 1/Tier 2 split (#24) requires restructuring the table, not just adding text. The current table has 10 dimensions with weights totaling 100%. The new structure has 4 universal gates (Tier 1) + 6 adaptive dimensions (Tier 2). Design this carefully.
2. The geometric mean change (#23) affects how scores are described throughout Section 5. Currently the document implies weighted summation. All references to score aggregation need updating.
3. For the retrieval split (#30): this creates a clear architectural distinction between "finding new sources" (RAG, embeddings, APIs) and "navigating accumulated knowledge" (Karpathy pattern, compiled wikis). Frame this as two distinct subsystems with different access patterns, not one system doing two things.
4. Preserve ALL existing citations. The Prendergast hallucination tax analysis, Jones citations, and ICD 203 references are all still valid.
```

---

### SUBAGENT C: Self-Improvement + Infrastructure
**Assigned sections:** §7 (lines 759-924) + §12 (lines 1093-1187)
**MASTER-SYNTHESIS changes:** #39-48 (10 changes)
**Coupling:** LOW — these sections are the most independent of each other

**Spawn this subagent with the following prompt:**

```
You are analyzing Sections 7 and 12 of CAPSTONE-PLAN-v2.md for the Keystone Intelligence Engine project and producing a Change Specification File.

## YOUR TASK
For each of the 10 changes assigned to you (MASTER-SYNTHESIS Section 9, Changes #39-48), produce a detailed change specification. You do NOT edit the file directly.

## THE 10 CHANGES ASSIGNED TO YOU

### Section 7 (Observation Library / Self-Improvement), Changes #39-42:
39. Reframe Observation Library as CBR system with R4 cycle (Retrieve/Reuse/Revise/Retain)
40. Add 5-tier knowledge artifact hierarchy with dual-axis metadata (industry × capability)
41. Add three-type extraction: strategy tips, recovery tips, optimization tips
42. Add flexon-based problem archetype tagging

### Section 12 (Infrastructure / Implementation Roadmap), Changes #43-48:
43. Remove "Claude Agent SDK for execution substrate"
44. Add error recovery Layers 1-2 as Phase 1 requirement
45. Add database state machine HITL as Phase 1 implementation
46. Add 5 mandatory Day-1 coding standards for Temporal migration readiness
47. Replace Academix with paper-search-mcp in server list
48. Add Finnhub MCP for market data

## PHASE 1 vs PHASE 2 CLASSIFICATION

**Nearly all Section 7 changes (39-42) are Phase 2.** The Observation Library is a Phase 2 feature per the existing Implementation Roadmap (§12.2, item 9). However, the INTERFACES to the Observation Library should be defined in Phase 1 (Directive 5: "build the architecture correctly but stage feature depth").

So the approach for §7: describe the full CBR vision, R4 cycle, hierarchy, etc. — but tag them as `[Phase 2]`. The builder sessions will see these descriptions and know to define interfaces but not implement.

**Section 12 changes (43-48) are all Phase 1.** These are infrastructure updates that must be in the roadmap now:
- Error recovery ships Phase 1 (Claude API: 62 incidents in 90 days)
- HITL state machine ships Phase 1 (enables Components #5 and #9)
- Day-1 coding standards ship Phase 1 (Temporal readiness)
- paper-search-mcp replaces Academix (tool ecosystem update)
- Finnhub MCP adds market data capability

## SPECIAL INSTRUCTIONS FOR SECTION 12

Section 12 currently has a specific build order (§12.1) that needs updating:

Current order: RESEARCH.md → Spec Engine → Evaluator → Research Agents → CitationProcessor → Deliberation → Retrieval → E2E test

New order (from MASTER-SYNTHESIS Section 10):
```
Parallel block (no dependencies):
  #1 RESEARCH.md spec format (S+)
  #2 Citation data model (S)
  #3a Source Discovery (L)
  #3b Knowledge Accumulation (M)
  #4 MCP Gateway (M)
  #HITL PostgreSQL state machine (S)
Sequential:
  #5 Specification Engine (XL)
  #6 Evaluator stack Layers 1-3 (XL)
  #7 Research Agent pipeline (L+)
  #8 CitationProcessor (M)
  #9 Deliberation (L+)
  #10 Evaluator calibration (M)
  #11 E2E pipeline test (M)
```

Also update §12.0 (Orchestration Architecture):
- Remove Agent SDK references
- Add error recovery as Phase 1 requirement
- Add HITL state machine description
- Add Day-1 coding standards list

And update §12.1 (Phase 1 deliverables) to match the new build order.

## OUTPUT FORMAT

Write to: `audit/track-1-session/change-spec-C.md`

Use the same format as Subagent A (see the orchestrator's Phase 1 instructions).

## IMPORTANT CONSTRAINTS

1. Section 7 is well-written and the Observation Library concept is already described. Most changes here are ADDITIONS (adding CBR framing, adding hierarchy details) not replacements.
2. The Instinct → Skill Evolution Pipeline (§7.7) is still valid — it becomes part of the CBR R4 cycle. Don't delete it; reframe it.
3. Section 12's build order change is significant. The current document describes a different sequence than what MASTER-SYNTHESIS recommends. Make sure the new order matches MASTER-SYNTHESIS Section 10 exactly.
4. When removing Agent SDK references (Change #43), also check §12.0 for any language about it being part of the orchestration stack. It currently says "Claude Agent SDK for execution substrate" somewhere — this should be removed or replaced with a note that Agent SDK is reserved for future computer-use nodes only.
5. The Day-1 coding standards (#46) should be presented as non-negotiable requirements, not suggestions. They enable Temporal migration in Phase 2.
```

---

## PHASE 2: ORCHESTRATOR REVIEW AND INTEGRATION

After all 3 subagents complete, you (the orchestrator) have three Change Specification Files:
- `audit/track-1-session/change-spec-A.md` (22 changes for §3, §4)
- `audit/track-1-session/change-spec-B.md` (16 changes for §5, §6)
- `audit/track-1-session/change-spec-C.md` (10 changes for §7, §12)

### Step 2.1: Completeness Check

Read all three files. Verify:
- [ ] All 48 changes from MASTER-SYNTHESIS Section 9 are accounted for (none dropped)
- [ ] Each change has a Phase 1/Phase 2 classification
- [ ] Each classification is consistent with Directive 13

If any changes are missing, produce them yourself before proceeding.

### Step 2.2: Cross-Section Consistency Check

Look for conflicts between the three specs:
- Does Agent A's template registry description match Agent C's infrastructure description?
- Does Agent A's claim-level selection description match Agent B's evaluator rubric changes?
- Does Agent B's retrieval split description match Agent C's build order?
- Are there any terms defined differently by different agents?
- Are there any Phase 1/Phase 2 classifications that conflict?

Document any conflicts found and resolve them. Resolution priority: Directive 13 > MASTER-SYNTHESIS > PARALLEL-EXECUTION-PLAN > individual subagent judgment.

### Step 2.3: Prose Style Consistency Check

Verify that replacement text from all three agents:
- Uses the same citation format
- Uses `[BATCH 2 UPDATE]` tags consistently
- Matches the existing document's voice and tone
- Doesn't introduce formatting inconsistencies (e.g., one agent uses bold headers, another doesn't)

---

## PHASE 3: APPLY CHANGES TO CAPSTONE-PLAN-v2.md

### FIRST: Create a backup
```bash
cp CAPSTONE-PLAN-v2.md CAPSTONE-PLAN-v2.md.backup
```
This backup allows recovery if the editing process goes wrong. Do not delete it until Phase 6 verification passes.

### Editing strategy: bottom-up within each section
Within each section, apply changes starting from the HIGHEST line number and working BACKWARD. This prevents earlier edits from shifting the line positions of later changes. Between sections, work in document order (§3, §4, §5, §6, §7, §12) since sections don't overlap.

Now apply all 48 changes to CAPSTONE-PLAN-v2.md. Work section by section in document order (§3, §4, §5, §6, §7, §12). For each change:

1. Locate the exact text identified in the change specification
2. Verify the surrounding context matches (guard against line-number drift from earlier edits)
3. Apply the change
4. After each section is complete, re-read the section to verify it flows naturally

### Critical editing rules:

- **NEVER delete content that isn't explicitly being replaced.** The existing document is well-written. If a change says "add X after paragraph Y," ADD it — don't rewrite the whole subsection.
- **Preserve all existing citations.** Every (Jones, "...", Date) reference must survive.
- **Preserve all `[SYNTHESIS UPDATE]` tags.** These mark content from the Batch 1 synthesis and are still valid.
- **Add `[BATCH 2 UPDATE]` tags** to all new content so future readers can trace when changes were made.
- **Do NOT renumber sections.** The current numbering (§1-§13 + Appendices) is stable and referenced by other files.
- **Maintain the document's narrative structure.** Sections tell a story. New content should extend the story, not interrupt it.

### After all changes are applied:

Read the COMPLETE updated CAPSTONE-PLAN-v2.md from start to finish. Check for:
- Narrative flow (does the document still read as a coherent design document?)
- Internal consistency (does Section 3's description of the pipeline match Section 12's build order?)
- No orphaned references (if you changed a term in §3, is it updated everywhere else it appears?)
- No duplicate content (did two changes add the same information in different places?)

---

## PHASE 4: UPDATE PHASE-1-IMPLEMENTATION-SPEC.md

With CAPSTONE-PLAN-v2.md now finalized, update `audit/PHASE-1-IMPLEMENTATION-SPEC.md` to reflect:

### 4.1: Component scope changes
- **Component #3:** Split into #3a (Source Discovery) and #3b (Knowledge Accumulation) with separate specs. #3a gets: Voyage-finance-2, contextual retrieval, Cohere Rerank, chunking rules, Brave + Exa. Remove Semantic Router and Bifrost. Note VectorChord as conditional replacement pending Track 2 evaluation. #3b gets: Karpathy three-layer pattern (raw/ + compiled/ + INDEX.md), content-hash provenance, human-designed schemas.
- **Component #4:** Add note that vurgunhajiyev/mcp-gateway is being evaluated as fork candidate. Replace Academix with paper-search-mcp. Add Finnhub MCP. Add transport_type and security_approved to tool registry schema.
- **Component #5:** Expand to 10-step pipeline. Apply Directive 13 staging: ALL 10 steps exist in Phase 1, but some at reduced depth:
  - Step 1 (Problem Framing): Engagement classifier with 3-4 types. Decision-First CoT. NO TiCoder (Phase 2).
  - Step 2 (Hypothesis Generation): Day-1 Hypothesis. Full implementation.
  - Step 3 (Issue Tree): 3 Sonnet agents with heterogeneous lenses, shallow 2-3 level trees. Full implementation.
  - Step 4 (Validation): MECE verification with Opus, binary criteria. Full implementation.
  - Step 5 (Priority Assignment): SIMPLIFIED heuristic scoring (NOT VOI, which is Phase 2 per Directive 13).
  - Step 6 (Agent Config): Template registry with 5-10 seed templates. No promotion loop (Phase 2).
  - Step 7 (Task Generation): DAG structure, anti-confirmatory framing, per-branch end products. Full implementation.
  - Step 8 (Human Review): HITL database state machine. Full implementation.
  - Step 9 (Research Execution): Scout phase with Day-1 Hypothesis. Full implementation.
  - Step 10 (Feedback Loop): 3-cycle max. Full implementation.
  - NO CBR Observation Library query (Phase 2 — Observation Library doesn't exist in Phase 1)
- **Component #6:** Add geometric mean aggregation. Add Tier 1/Tier 2 rubric split. Change from 2 to 3-4 profiles (Phase 1), with note about expanding to 8-10 in Phase 2. NO sprint contract negotiation (Phase 2 per Directive 13). NO dimension-specific verification strategies (Phase 2 per Directive 13).
- **Component #7:** Add error recovery (retry + model fallback chain). Add artifact bypass pattern (structured summary ~1,500 tokens + full artifact file). Add template dispatch from registry. Add 1,000-2,000 token condensed output requirement.
- **Component #8:** Add note that SemanticCite is being evaluated as fork candidate. Add content-hash provenance for wiki compilation.
- **Component #9:** Change aggregation to claim-level selection (81% vs 51.2% evidence). Add WWHTB step for low-confidence findings. Add per-claim confidence scores in subagent output.
- **New: HITL Infrastructure** — Add full component spec:
  ```
  What to build:
  - PostgreSQL tables: review_gates, review_items, review_decisions
  - review_gates: gate_id, engagement_id, gate_type (post_spec/post_deliberation), status (pending/approved/modified/rejected), created_at, resolved_at, resolved_by
  - review_items: item_id, gate_id, item_type (issue_tree/agent_config/confidence_map), content_json, display_order
  - review_decisions: decision_id, gate_id, decision (approve/modify/reject), modifications_json, reasoning, decided_by, decided_at
  - REST API (FastAPI): GET/POST /gates, GET/POST /decisions
  - Basic web UI: display issue tree/agent configs/confidence map, approve/modify/reject buttons, modification text fields, agent reasoning panel
  - Scope: S (2-3 days)
  - Dependencies: None (parallel with #1-#4)
  - First test: Create a gate, add review items, submit an approval. Verify state transitions work correctly.
  ```

### 4.2: Build order update
Update the build order diagram to match MASTER-SYNTHESIS Section 10:
- Parallel block: #1, #2, #3a, #3b, #4, HITL
- Sequential: #5 → #6 → #7 → #8 → #9 → #10 → #11

### 4.3: Fork candidate integration
For components with fork candidates, add a conditional note:
```
**Fork candidate:** {repo name} (evaluation pending, see audit/fork-evaluations/)
If FORK verdict: start from forked codebase, modify to match this spec.
If SKIP verdict: build from scratch per this spec.
```

### 4.4: Input/output contract updates
Update any schemas that changed (especially research-tasks.json for DAG structure, citation schemas for content-hash provenance, evaluator output for geometric mean).

---

## PHASE 5: UPDATE AUXILIARY FILES

### 5.1: CURRENT-STATE.md
Update to reflect:
- Phase: "Architecture finalization complete. Ready for fork evaluations (Track 2) and build phase."
- What's complete: Add "Track 1: CAPSTONE-PLAN-v2.md and PHASE-1-IMPLEMENTATION-SPEC.md updated with all Batch 2 findings"
- What's next: Fork evaluation sessions (Track 2), casing book analysis (Track 3), Phase 1A builder sessions
- Settled decisions: Add all 16 new decisions from MASTER-SYNTHESIS Section 6

### 5.2: CLAUDE.md
- Update the project structure section if any new directories were created
- Verify orientation file list is current
- Add reference to `audit/track-1-session/` for this session's artifacts

---

## PHASE 6: FINAL VERIFICATION

This is the most important phase. Every error caught here prevents a cascade through the build phase.

### 6.1: 48-Change Audit
Create `audit/track-1-session/change-audit.md`:

For every one of the 48 changes from MASTER-SYNTHESIS Section 9, verify:
```
Change #{N}: {title}
- Present in CAPSTONE-PLAN-v2.md: YES/NO (cite section and approximate line)
- Phase classification: [Phase 1] / [Phase 2+]
- Consistent with Directive 13: YES/NO
- Reflected in PHASE-1-IMPLEMENTATION-SPEC.md (if Phase 1): YES/NO
```

If any change is missing, add it now.

### 6.2: Directive Compliance Audit
For each of Jack's 14 directives, verify the updated documents comply:

| Directive | Compliant? | Evidence |
|-----------|-----------|----------|
| 1. The Rigidity Problem | ? | Templates, not enums. Where in updated docs? |
| 2. MECE Issue Tree | ? | Multi-agent construction. Where? |
| 3. Iterative Research | ? | Mechanical specification. Where? |
| 4. Engagement Scope | ? | Any domain handled. Where? |
| 5. Build Philosophy | ? | Correct architecture, staged depth. Where? |
| 6. FITFO Standard | ? | Novel problem handling. Where? |
| 7. HITL Gates | ? | Two gates. Where? |
| 8. Karpathy Knowledge Bases | ? | Discovery vs. accumulation. Where? |
| 9. Component #3 Concern | ? | Split into #3a + #3b. Where? |
| 10. Settled Decisions | ? | All 11 validated. Where? |
| 11. Configurable Pipeline | ? | Light/Standard/Deep. Where? |
| 12. Casing Principles | ? | Principles, not templates. Where? |
| 13. Phase 1 Staging | ? | Explicit lists respected. Where? |
| 14. Quality Standard | ? | Real product quality. Where? |

### 6.3: Cross-Document Consistency Check
Verify that CAPSTONE-PLAN-v2.md and PHASE-1-IMPLEMENTATION-SPEC.md agree on:
- [ ] The 10-step Specification Engine pipeline
- [ ] The component build order
- [ ] The retrieval split (#3a + #3b)
- [ ] The evaluator Tier 1/Tier 2 structure
- [ ] The deliberation aggregation method (claim-level selection)
- [ ] The iterative research loop specification
- [ ] The template registry approach
- [ ] Error recovery as Phase 1
- [ ] HITL infrastructure
- [ ] All Phase 1/Phase 2 classifications match

### 6.4: Diff Summary
Create `audit/track-1-session/DIFF-SUMMARY.md`:

A human-readable summary of every change made, organized by file:
```
## CAPSTONE-PLAN-v2.md Changes
### Section 3: Specification Engine
- {change description}
- {change description}
...

### Section 4: Research & Analysis
...

## PHASE-1-IMPLEMENTATION-SPEC.md Changes
...

## CURRENT-STATE.md Changes
...

## CLAUDE.md Changes
...
```

This is what Jack reviews to verify the session produced correct results.

---

## CONTEXT MANAGEMENT

This session involves reading ~3,000+ lines of source material and editing ~1,800 lines across two files. If you feel context pressure:

1. **Do NOT skip verification phases.** Phase 6 is the most important phase. Cut elsewhere if needed.
2. **If you must split the work:** Complete Phases 0-3 (CAPSTONE-PLAN edits + verification) as the minimum viable session. Write a handoff document to `audit/track-1-session/HANDOFF.md` with: what was completed, what remains, and the current state of each file. Phase 4 (IMPLEMENTATION-SPEC) can be continued in a follow-up session.
3. **The change specification files from Phase 1 are your safety net.** They exist as permanent artifacts. If the session fails partway through Phase 3, a new session can read the change specs and resume.

---

## SESSION COMPLETION

When all phases are complete, write a final entry to `SESSION-LOG.md`:
```
## Track 1: Architecture Finalization
**Date:** {date}
**Session type:** Claude Code with 3 parallel Opus subagents
**Files modified:** CAPSTONE-PLAN-v2.md, audit/PHASE-1-IMPLEMENTATION-SPEC.md, CURRENT-STATE.md, CLAUDE.md
**Files created:** audit/track-1-session/change-spec-{A,B,C}.md, audit/track-1-session/change-audit.md, audit/track-1-session/context-verification.md, audit/track-1-session/DIFF-SUMMARY.md
**Changes applied:** 48 from MASTER-SYNTHESIS, filtered through Directive 13
**Key decisions:** {any judgment calls made during the session}
**Known issues:** {anything that couldn't be resolved}
```
