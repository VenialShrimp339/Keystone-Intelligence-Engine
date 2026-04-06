# Analysis: Report 01 — Iterative Multi-Round Research
*Analyzed: 2026-04-05 | Priority: Tier 1 (HIGHEST) | Report quality: high*

## Executive Summary

This report is the most directly actionable of the batch. It synthesizes production evidence from Anthropic, OpenAI, Google, Perplexity, Stanford STORM, and multiple academic systems to provide concrete mechanical specifications for iterative multi-round research — the single biggest architectural gap in the current plan. The core finding is that production systems converge on orchestrator-worker loops with model-judgment stopping supplemented by hard iteration caps (typically 3–5 rounds), quality gates, and diminishing-returns detection. Five specific mechanisms emerge: ADaPT-style failure-triggered decomposition, a three-criterion stopping combination, context isolation with structured handoffs, scope-change detection with hierarchical replanning, and model-capability-dependent harness design. These findings directly fill the gap identified in Jack's Directive 3 and provide the mechanical specification the plan currently lacks.

---

## Key Findings (ranked by implementation impact)

### 1. Three-Criterion Stopping Combination Is the Production Standard

- **What:** No production system uses a single stopping criterion. The convergent pattern is: (1) hard iteration cap (3–5 rounds), (2) quality-gate evaluator scoring research completeness against the original brief, and (3) semantic/novelty exhaustion detection measuring whether new rounds produce genuinely new information. These run in parallel; any one can terminate the loop.
- **Evidence basis:** Anthropic engineering blog (June 2025) — max 20 tool calls per subagent, ~100 sources hard limit. OpenAI Deep Research — 30–60 searches, 120–150 page fetches, 20–30 min wall clock. Google Gemini Deep Research — ~20 iterations maximum. Stanford STORM — fixed N×M budget. DBAutoDoc (2026) — median convergence in 2 iterations, diminishing returns after round 2. Self-Refine — `is_refinement_sufficient` scalar threshold.
- **Evidence quality:** Credible (Anthropic June 2025, well within temporal range). Credible (OpenAI production). Credible (Google production). Verified for DBAutoDoc (2026 publication with empirical results).
- **Temporal check:** All sources 2024–2026. Current.
- **Conflicts with existing project research?** No. The plan has no stopping mechanism specified at all — this fills a gap rather than contradicting anything.
- **Verdict:** ADOPT
- **Justification:** Three independent production systems arrived at the same combination independently; this is convergent evidence, not coincidence.
- **Keystone impact:** Component #7 (Research Agent pipeline L1), Component #9 (Basic Deliberation L1.5). Directly resolves Jack's Directive 3 (stopping conditions). The quality-gate criterion maps to L4 Evaluator, which the plan already has — the connection is making L4 operate mid-pipeline, not just at the end.
- **Contradicts:** None identified. Parallel analysis unknown.

---

### 2. ADaPT-Style Failure-Triggered Decomposition Outperforms Upfront Fixed Planning

- **What:** Systems that decompose tasks reactively — attempt synthesis first, decompose only when the executor fails a quality heuristic — outperform fixed-depth upfront plans by 27–28% on benchmark tasks. The key pattern: attempt execution, assess via self-generated success heuristic, decompose into sub-tasks with AND/OR logical operators only on failure, recurse with bounded depth.
- **Evidence basis:** ADaPT (NAACL 2024) — 28.3% improvement on ALFWorld, 27% on WebShop. DynTaskMAS (ICAPS 2025) — 21–33% reduction in execution time, 35.4% resource utilization improvement. AdaptOrch (2026) — "Performance Convergence Scaling Law" showing orchestration topology dominates model capability as models converge.
- **Evidence quality:** Verified (ADaPT: peer-reviewed, reproduced benchmarks). Credible (DynTaskMAS: 2025 conference). Credible (AdaptOrch: 2026, within range).
- **Temporal check:** ADaPT is 2024 — fast-moving area. However, the principle (reactive decomposition > upfront planning) is validated by multiple systems across 2024–2026 and aligns with consulting practice. Not stale.
- **Conflicts with existing project research?** Mild tension. The current plan (L0 Specification Engine) performs upfront decomposition via issue trees before any research begins. ADaPT suggests attempting execution before decomposing. These are not irreconcilable: upfront issue tree decomposition is appropriate at the engagement level (coarse), while failure-triggered decomposition should govern within each research round (fine-grained). Upfront issue tree + reactive sub-decomposition is additive.
- **Verdict:** ADAPT
- **Justification:** Pure ADaPT (no upfront plan) conflicts with Jack's Directive 2 (MECE issue tree casing phase); the correct adaptation is issue-tree decomposition at L0 + ADaPT-style reactive decomposition within L1 research rounds.
- **Keystone impact:** Component #5 (Specification Engine L0), Component #7 (Research Agent pipeline L1). The issue tree sets the research agenda; failure-triggered deepening governs whether individual research threads get additional subagents.
- **Contradicts:** Mild tension with Jack's Directive 2 (issue tree pre-planning). Reconcilable as described above.

---

### 3. Context Resets with Structured Handoffs Outperform Context Compaction for Iterative Research

- **What:** For long-running iterative tasks, giving each round's agents a fresh context window and communicating through structured handoff artifacts (files, memory scratchpads) outperforms trying to compress a growing context. Anthropic's March 2026 post documents "context anxiety" — models prematurely wrapping up work as they approach perceived context limits. Optimal strategy is model-capability-dependent: resets were essential for Sonnet 4.5, optional for Opus 4.5, unnecessary for Opus 4.6.
- **Evidence basis:** Anthropic engineering blog "Harness design for long-running application development" (March 2026). JetBrains Research (2025) — hybrid observation masking + LLM summarization reduces costs 7–11% while improving SWE-bench success ~2.6pp. NoLiMa benchmark — 11/12 frontier models drop below 50% performance past 32K tokens.
- **Evidence quality:** Verified (Anthropic, March 2026 — highest credibility for our stack). Credible (JetBrains Research 2025). Credible (NoLiMa benchmark).
- **Temporal check:** March 2026 Anthropic post is the most current possible source. The "Opus 4.6 doesn't need resets" finding is directly relevant since we're targeting Claude Max with Opus for L0/L4. The capability-dependent framing is explicitly forward-looking.
- **Conflicts with existing project research?** Validates and extends the existing plan. The plan already specifies JIT context loading and per-agent isolated working directories (Settled Decision #5). This finding tells us *why* that architecture is right and adds the orchestrator memory scratchpad requirement.
- **Verdict:** ADOPT
- **Justification:** March 2026 Anthropic source directly validates our model stack; the scratchpad pattern for orchestrator persistence between rounds is a concrete mechanical spec we currently lack.
- **Keystone impact:** Component #7 (Research Agent pipeline L1). Adds a required architectural element: the LeadResearcher/orchestrator must maintain a persistent Memory scratchpad that survives context resets and carries: current research plan, key findings to date, identified gaps, and active research questions. Subagents return 1,000–2,000 token condensed summaries, not full context.
- **Contradicts:** None. Extends existing plan.

---

### 4. Scope-Change Detection with Hierarchical Replanning

- **What:** When subagent findings reveal research-plan-invalidating discoveries, the correct response is hierarchical replanning (not full restart). A lightweight LLM judge evaluates each subagent's output against the original research plan. Scope-changing findings trigger: cancel/deprioritize irrelevant in-flight subagents, update the shared scratchpad, spawn new subagents for the revised direction. AdaPlanner distinguishes In-Plan Refiners (minor adjustments) from Out-of-Plan Refiners (fundamental reframing).
- **Evidence basis:** AdaPlanner (cited, no publication date given in report). LangGraph's LLMCompiler pattern (production). Reflexion architecture (episodic memory + verbal lessons learned). CostBench (2025) — benchmark with four disruption types.
- **Evidence quality:** Credible (LangGraph production). Claimed (AdaPlanner — no date, no benchmark result cited in this report). Credible (Reflexion — well-established).
- **Temporal check:** LangGraph LLMCompiler is production-current. AdaPlanner date unknown — treat as Credible pending verification.
- **Conflicts with existing project research?** The plan has no scope-change mechanism at all. This is a gap, not a contradiction. Aligns with Jack's Directive 3 (handling mid-research scope expansion).
- **Verdict:** ADOPT
- **Justification:** Mid-research scope expansion is explicitly flagged as a missing mechanism in Jack's Directive 3; the In-Plan / Out-of-Plan distinction gives us a two-tier response that avoids costly full restarts.
- **Keystone impact:** Component #5 (Specification Engine L0 — the scope-change detector validates against the original RESEARCH.md), Component #7 (Research Agent pipeline L1 — orchestrator receives scope-change signal and acts). Requires: a scope-change detector agent (lightweight, Haiku-tier) as part of the orchestrator synthesis step between rounds.
- **Contradicts:** None. Gap fill.

---

### 5. Anthropic Production Architecture: Three-Tier LeadResearcher → Subagents → CitationAgent

- **What:** Anthropic's own production multi-agent research system uses exactly the architecture the Keystone plan is building: LeadResearcher (Opus 4) with extended thinking + memory scratchpad, spawns Subagents (Sonnet 4) with isolated contexts and OODA loops, which return condensed findings, then a CitationAgent handles source attribution. Multi-agent outperforms single-agent Opus 4 baseline by 90.2% on internal evaluations. Token usage explains 80% of performance variance on BrowseComp.
- **Evidence basis:** Anthropic engineering blog "How we built our multi-agent research system" (June 2025). Open-source prompts in Anthropic Cookbook repository.
- **Evidence quality:** Verified (Anthropic first-party, June 2025, open-source prompts available for inspection).
- **Temporal check:** June 2025. Current. Open-source prompts are inspectable.
- **Conflicts with existing project research?** Validates the plan's architecture. The 90.2% improvement over single-agent Opus confirms the multi-agent approach is not just theoretically sound. The token-usage-explains-80%-of-variance finding is important: it implies the primary cost lever is controlling token volume, not model selection within a tier.
- **Verdict:** ADOPT
- **Justification:** This is first-party empirical validation of the exact architecture we are building; the open-source Cookbook prompts should be reviewed directly for the subagent OODA prompt design.
- **Keystone impact:** Validates Component #7 (Research Agent pipeline L1) architecture. The specific numbers — max 20 tool calls per subagent, ~100 sources per subagent, 15× token multiplier vs. standard chat — are now our baseline cost/scope estimates. The Cookbook prompts are a direct implementation reference.
- **Contradicts:** None. Validates.

---

### 6. STORM's Perspective-Driven Decomposition as Research Thread Generation Model

- **What:** STORM (NAACL 2024) uses perspective discovery before research: given a topic, retrieve related article structures, prompt LLM to identify N diverse perspectives (default 5), then run M-round simulated conversations per perspective (default 5). Full 5×5 grid discovers ~99.83 unique references vs. 54.36 without perspectives. Co-STORM adds a Moderator agent surfacing "unknown unknowns" and a discourse manager forcing moderator intervention after L consecutive expert responses to prevent stagnation.
- **Evidence basis:** STORM (NAACL 2024). Co-STORM (EMNLP 2024). Both peer-reviewed.
- **Evidence quality:** Verified (peer-reviewed, published benchmarks, replicable methodology).
- **Temporal check:** 2024 — in fast-moving area. However, the perspective-driven decomposition is a methodological insight, not a model-capability claim. Still valid in 2026.
- **Conflicts with existing project research?** The Keystone plan's 5 fixed research agent types (Quantitative, Qualitative, Contrarian, Historical Analogy, Internal Document) are analogous to STORM's perspectives but hardcoded. Jack's Directive 1 explicitly says these should be templates/defaults, not constraints — STORM validates this direction. The Moderator agent surfacing unknown unknowns maps to the Contrarian agent role but suggests it should be architecture-enforced (after L consecutive non-challenge responses), not prompt-level.
- **Verdict:** ADAPT
- **Justification:** STORM's perspective generation mechanism should inform how the Specification Engine (L0) dynamically selects research agent types — pulling from templates rather than always using all 5 — and the Co-STORM moderator forcing intervention maps to structural anti-confirmation bias enforcement.
- **Keystone impact:** Component #5 (Specification Engine L0 — perspective/agent-type selection), Component #7 (Research Agent pipeline L1 — discourse manager equivalent). The fixed-N×M stopping criterion (simple budget) is too rigid for consulting; adapt with the three-criterion combination from Finding #1.
- **Contradicts:** Mild tension with current plan's 5 fixed agent types. Jack's Directive 1 resolves this in STORM's favor.

---

### 7. Semantic Stability Detection as Formal Stopping Criterion

- **What:** Tacheny (2025) formalizes agentic loops as discrete dynamical systems in semantic embedding space. Stopping is detected via geometric indicators: local drift (step-to-step similarity), dispersion (spread of recent outputs), and cluster persistence. Convergence = drift approaching maximum similarity + dispersion decreasing monotonically. Critical: prompt design controls the dynamical regime — iterative paraphrasing produces contractive (convergent) dynamics, while negation-framing produces exploratory (divergent) dynamics.
- **Evidence basis:** Tacheny (2025) — cited as "most rigorous theoretical treatment."
- **Evidence quality:** Credible (2025, described as rigorous theoretical treatment, but no benchmark results quoted).
- **Temporal check:** 2025. Current. The theoretical framework is model-agnostic.
- **Conflicts with existing project research?** No. Adds precision to the diminishing-returns detection component of stopping criteria.
- **Verdict:** INVESTIGATE
- **Justification:** The theoretical framework is compelling and the prompt-regime insight (paraphrasing vs. negation framing) directly affects how we write research prompts, but embedding-space computation adds operational complexity; needs feasibility assessment before adoption.
- **Keystone impact:** Component #7 (Research Agent pipeline L1 — stopping criterion). If adopted, adds an embedding computation step in the orchestrator between rounds. The prompt-design implication (anti-confirmatory framing = exploratory dynamics) validates the existing plan's anti-confirmatory framing requirement and gives it a theoretical basis.
- **Contradicts:** None. Novel addition.

---

### 8. Max Round Empirical Baseline: 3–5 Rounds Across Production Systems

- **What:** Across all production and open-source systems surveyed, 3–5 research rounds is the empirical sweet spot. OpenAI's novelty-exhaustion detection implies diminishing returns after initial rounds. DBAutoDoc shows median convergence in 2 iterations with sharp diminishing returns after round 2. Open-source implementations (dzhng/deep-research) default to depth 1–5. Sinha et al. (2025) warns that marginal single-step gains compound exponentially for longer tasks — a counterpoint to premature stopping.
- **Evidence basis:** DBAutoDoc (2026), dzhng/deep-research (open-source defaults), OpenAI Deep Research production behavior, Sinha et al. (2025).
- **Evidence quality:** Verified (DBAutoDoc empirical). Credible (OpenAI production). Claimed (dzhng defaults — open-source heuristic, not empirically validated). Credible (Sinha et al. 2025).
- **Temporal check:** 2025–2026. Current.
- **Conflicts with existing project research?** The plan specifies no round count. This provides the missing baseline.
- **Verdict:** ADOPT
- **Justification:** Convergent evidence across system types; 3–5 rounds should be our default hard cap, configurable per engagement complexity.
- **Keystone impact:** Component #7 (Research Agent pipeline L1). Concrete implementation spec: default max_rounds = 3, configurable to 5, never exceed 5 without explicit orchestrator justification logged to scratchpad. Simpler queries may terminate in 1–2 rounds via quality gate.
- **Contradicts:** None.

---

### 9. Context Engineering Four-Strategy Framework

- **What:** LangChain's Harrison Chase codifies four context strategies: Write (scratchpads/memory outside window), Select (RAG retrieval), Compress (summarization + observation masking), Isolate (subagents with separate windows). JetBrains Research (2025) finds hybrid observation masking + LLM summarization reduces costs 7–11% while improving SWE-bench success ~2.6pp. Letta/MemGPT paradigm: structured memory blocks (core always in-context, archival searchable, recall for history) with self-editing memory tools.
- **Evidence basis:** LangChain (Harrison Chase, cited without date). JetBrains Research (2025). Letta/MemGPT (ongoing project). NoLiMa benchmark (cited without date).
- **Evidence quality:** Credible (JetBrains 2025). Credible (Letta/MemGPT active project). Claimed (LangChain taxonomy — useful framing, not empirical).
- **Temporal check:** Mixed. JetBrains 2025 is current. NoLiMa benchmark — pre-2025 if undated, but the "lost in middle" effect has been consistently replicated. The 32K token performance cliff is likely conservative given 2026 model improvements, but the qualitative finding holds.
- **Conflicts with existing project research?** No. The four-strategy framework provides organizational clarity for what the plan already does (Isolate via per-agent directories, Write via memory scratchpad). Adds Compress as a cost optimization option and Select as the retrieval strategy.
- **Verdict:** ADOPT
- **Justification:** The four-strategy taxonomy gives the team a shared vocabulary for context engineering decisions; the JetBrains hybrid finding is directly applicable to cost optimization within our budget constraint.
- **Keystone impact:** Component #7 (Research Agent pipeline L1), Component #6 (Evaluator stack L4 Layers 1–3 — observation masking for tool output compression). The $12–$100 cost target makes the 7–11% cost reduction from observation masking worth implementing.
- **Contradicts:** None.

---

### 10. Model-Capability-Dependent Harness Design

- **What:** Context resets were essential for Sonnet 4.5 (severe context anxiety), optional for Opus 4.5, unnecessary for Opus 4.6 (coherent for 2+ hours without decomposition). Implication: every harness component encodes an assumption about model limitations. Those assumptions should be documented, periodically stress-tested, and the harness should be designed to make components pluggable as model capabilities improve.
- **Evidence basis:** Anthropic engineering blog "Harness design for long-running application development" (March 2026).
- **Evidence quality:** Verified (Anthropic first-party, March 2026).
- **Temporal check:** March 2026. Directly relevant.
- **Conflicts with existing project research?** Validates Jack's Build Philosophy (Directive 5): "build the architecture correctly with right interfaces and abstractions." Pluggable components are the architectural answer.
- **Verdict:** ADOPT
- **Justification:** This is a design principle with immediate practical impact: we are building with Opus 4 for L0/L4 (which per Anthropic may not need context resets) and Sonnet for L1 (which likely still benefits from isolation) — harness design should reflect this asymmetry.
- **Keystone impact:** Affects all 11 Phase 1 components as a design constraint. Concretely: Opus-tier orchestrator (L0, L4) can be designed without mandatory context resets; Sonnet-tier research agents (L1) should maintain context isolation as a structural guarantee, not an optional optimization.
- **Contradicts:** None. Extends Settled Decision #5 (filesystem-based isolation) with model-tier specificity.

---

## Architectural Decisions This Enables

### Decision 1: Iterative Research Round Structure (Previously Undefined)

**Recommended architecture:**
- Default max rounds: 3. Configurable to 5. Hard ceiling: 5.
- Stopping triggers any of: (a) quality gate pass (L4 Evaluator applied mid-pipeline), (b) semantic novelty exhaustion (no new claims in latest round), (c) hard round cap reached.
- Orchestrator maintains a Memory scratchpad (file-based, persists across rounds) containing: original RESEARCH.md requirements, key findings to date, open gaps, scope-change log.
- Each round: spawn N subagents (Sonnet-tier) with isolated contexts, collect 1,000–2,000 token condensed summaries, synthesize, evaluate, decide: iterate / go deeper on specific thread / stop.

**Evidence basis:** Anthropic June 2025, OpenAI production, DBAutoDoc 2026, STORM NAACL 2024.

### Decision 2: "Spawn New Research" vs. "Go Deeper" vs. "Stop" Criteria

This was explicitly unspecified in the plan. Recommended decision logic:

| Signal | Decision |
|--------|----------|
| Quality gate: overall score < threshold AND round < max | Spawn new research (new subagents, broader coverage) |
| Quality gate: score < threshold on specific dimension AND novelty exhaustion on that dimension | Go deeper (targeted subagents on specific gap) |
| Quality gate: score >= threshold | Stop |
| Round cap reached | Stop (log reasoning) |
| Scope-change detector fires | Hierarchical replan (not stop, not simple iterate) |

**Evidence basis:** Three-criterion stopping (Finding #1), ADaPT failure-triggered decomposition (Finding #2), scope-change detection (Finding #4).

### Decision 3: Scope-Change Protocol

Implement a lightweight Haiku-tier scope-change detector as a post-synthesis step within the orchestrator. Inputs: original RESEARCH.md, current round's synthesized findings. Output: binary (in-scope / scope-changing) + if scope-changing, In-Plan (minor adjustment) vs. Out-of-Plan (fundamental reframe). In-Plan: update scratchpad, adjust next round's task parameters. Out-of-Plan: trigger human-in-the-loop gate (Jack's Directive 7 — humans review before generation), present revised framing for approval before continuing.

**Evidence basis:** AdaPlanner, LangGraph LLMCompiler (Finding #4).

### Decision 4: Orchestrator Memory Scratchpad as First-Class Data Structure

The scratchpad is not optional state — it is the primary continuity mechanism between rounds and survives context resets. Required fields: engagement_id, client_id (multi-tenancy, Settled Decision #10), research_plan (current version of RESEARCH.md intent), rounds_completed, findings_by_round (condensed), open_gaps, scope_change_log, stopping_reason (populated when loop exits).

---

## Changes to Existing Plan

### Changes to CAPSTONE-PLAN-v2.md

1. **L1 Research Agent section** currently lacks any iterative loop specification. Add: max_rounds (3 default, 5 max), three-criterion stopping, orchestrator scratchpad as persistent state, condensed summary format for subagent returns (1,000–2,000 tokens).

2. **L1 stopping conditions section** (currently absent): add the decision table from Decision 2 above.

3. **Mid-research scope expansion** (currently absent): add scope-change detector as a named architectural component between synthesis and next-round decision.

4. **Research Agent types section**: add note that the 5 fixed types are templates/defaults; L0 Specification Engine selects appropriate types dynamically per Jack's Directive 1. STORM's perspective-discovery mechanism is the model for this selection.

5. **Cost estimates**: update with Anthropic's 15× token multiplier vs. standard chat. At current Opus/Sonnet pricing, 3–5 rounds with 3–5 subagents per round is the regime where $12–$100 target is achievable. This should be explicitly modeled.

### Changes to PHASE-1-IMPLEMENTATION-SPEC.md

1. **Component #7 (Research Agent pipeline L1)**: add orchestrator scratchpad data structure as a required deliverable. Add stopping logic as a required interface (not optional future work).

2. **Component #5 (Specification Engine L0)**: add scope-change detector as a component that belongs here (or as a sub-component of L1 orchestrator — to be decided, but must be specified).

3. **Component #1 (RESEARCH.md spec format)**: add fields required by the iterative loop: max_rounds override, quality threshold per dimension (for mid-pipeline L4 application), scope-change sensitivity level.

### Validation vs. Jack's Directives

| Directive | Finding | Status |
|-----------|---------|--------|
| Directive 3 (stopping conditions) | Findings 1, 2, 4, 8 provide full mechanical spec | RESOLVES |
| Directive 3 (max rounds) | Finding 8: 3 default, 5 max | RESOLVES |
| Directive 3 (mid-research scope expansion) | Finding 4: scope-change detector + hierarchical replan | RESOLVES |
| Directive 3 (round N informs round N+1) | Finding 3: orchestrator scratchpad as continuity mechanism | RESOLVES |
| Directive 1 (dynamic agent types) | Finding 6: STORM perspective discovery validates this | VALIDATES |
| Directive 5 (pluggable architecture) | Finding 10: model-capability-dependent harness design | VALIDATES |
| Directive 7 (human gates) | Finding 4: Out-of-Plan scope change triggers human gate | EXTENDS — adds a new trigger point for Directive 7 gates |
| Directive 2 (issue tree pre-planning) | Finding 2: ADaPT prefers reactive decomposition | TENSION — resolved by treating issue tree as engagement-level and ADaPT as within-round |

---

## Open Questions Remaining

1. **Quality gate threshold values**: the report establishes that quality-gate stopping exists and works, but provides no specific threshold numbers for consulting research quality. What score on which dimensions constitutes "sufficient" for a given engagement type? This is not addressable from this report alone — requires calibration against actual consulting output (L4 Evaluator calibration, Component #10).

2. **Orchestrator model tier for the iterative decision step**: the report validates Opus for orchestration (Anthropic's LeadResearcher is Opus 4) but at $12–$100 cost target, running Opus for every mid-round synthesis-and-decide step may be prohibitive across 3–5 rounds. Can Sonnet handle the synthesis step with Opus reserved for the stopping decision? Not addressed.

3. **Scope-change detector sensitivity calibration**: what constitutes a genuine Out-of-Plan discovery vs. a normal finding that updates the research picture? The detector will have false positives (unnecessary human interruptions) and false negatives (missed pivots). Calibration methodology not addressed in this report.

4. **Parallelism within rounds**: the report notes Anthropic's system has synchronous execution (lead agent waits for each batch before deciding next steps). The plan targets 3–5 parallel agents. The interaction between within-round parallelism and between-round iteration is not fully specified — specifically, whether all subagents in a round complete before the stopping decision, or whether early-finishing subagents can trigger early round termination.

5. **Integration with the CitationProcessor**: the report describes Anthropic's CitationAgent as a terminal step after all research rounds complete. The Keystone plan has CitationProcessor between L1 and L1.5. Whether the CitationProcessor runs once per round or once at the end affects both deduplication logic and corroboration scoring (more rounds = more opportunities to corroborate). Not resolved.

6. **RESEARCH.md versioning across rounds**: when a scope change triggers an In-Plan update to the research agenda, does the RESEARCH.md spec get versioned? How do downstream layers (L1.5 Deliberation, L2, L4) know which version of the spec to validate against? Not addressed.
