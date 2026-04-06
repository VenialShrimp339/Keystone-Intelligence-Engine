# Analysis: Report 10 — Specification Engine as Problem Structurer
*Analyzed: 2026-04-05 | Priority: Tier 1 (HIGHEST) | Report quality: high*

---

## Executive Summary

Report 10 is the highest-quality report in the Batch 2 set. It directly targets the Specification Engine and produces a concrete 10-step pipeline with actionable, sourced additions to the existing plan. The four new steps — Problem Framing, Hypothesis Generation, Decomposition Validation, and Feedback Loop — are all independently validated by consulting methodology, production AI systems, and academic research, and all align tightly with Jack's architectural directives. The engagement-type taxonomy (5 types) and the four-phase issue tree deliberation pipeline (construct/analyze/evaluate/synthesize) are the two most implementation-ready contributions. The Observation Library CBR architecture (pgvector + compiled wiki + R4 cycle) is the third distinct contribution and resolves the previously underspecified knowledge management layer. The only area requiring caution is the Self-MoA claim and the EVPI formalism — the former is credible but not universally reproducible; the latter should be simplified for Phase 1.

---

## Key Findings (ranked by implementation impact)

### 1. Four missing pipeline steps that belong in Phase 1

- **What:** The report recommends expanding the existing 7-step Spec Engine flow to 10 steps by adding (1) Problem Framing and Classification before any decomposition, (2) Hypothesis Generation after framing but before tree construction, (3) Decomposition Validation after tree construction, and (4) a Feedback Loop connecting execution results back to planning.
- **Evidence basis:** McKinsey/BCG/Bain separation of problem definition from structuring (methodology documentation); AOP framework ICLR 2025 (arXiv 2410.02189) showing 15%+ decomposition issues even with detailed instructions; Anthropic engineering blog June 2025 confirming dynamic subagent spawning based on synthesized results; VeriMAP framework (arXiv 2510.17109) for verification-triggered replanning.
- **Evidence quality:** Verified — four independent source categories all converge on the same conclusion.
- **Temporal check:** AOP 2025, Anthropic blog June 2025, VeriMAP 2025 — all current.
- **Conflicts with existing project research?** No conflict. The existing CAPSTONE-PLAN-v2 plan describes 4-step verification but locates it after task generation, not as a structured validation gate after decomposition. This report adds granularity rather than contradiction.
- **Verdict:** ADOPT all four additions. Problem Framing (Step 1) is the single highest-leverage addition.
- **Justification:** Jack's Directive 2 explicitly requires a "casing phase" before decomposition — this maps directly to Steps 1-2 here. Directive 3 (iterative multi-round research) maps to Step 10. The report provides sourced implementation detail for both directives that the existing plan lacks.
- **Keystone impact:** Restructures the entire Spec Engine from a 7-step to a 10-step flow. Affects spec_engine.py, decomposer.py, and validator.py in PHASE-1-IMPLEMENTATION-SPEC.md. Also creates a new feedback_loop.py responsibility that does not currently have a home in the component map.
- **Contradicts:** Nothing in the settled decisions. Extends rather than replaces.

---

### 2. Five-type engagement taxonomy with type-specific routing

- **What:** Incoming queries should be classified into one of five types — SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC — each routing to a different pipeline configuration. Classification uses five signals: specificity of deliverable, presence of testable hypothesis, known analytical framework, scope boundedness, and decision type. EXPLORATORY needs sequential-with-reflection pipelines; EVALUATIVE benefits from parallel workstreams.
- **Evidence basis:** Adaptive-RAG (KAIST), FAIR-RAG four-tier routing, Perplexity hybrid model selection — all verified production systems. Consulting methodology classification also documented across multiple firms.
- **Evidence quality:** Verified for production AI routing; Credible for taxonomy labels (synthesized from consulting and AI sources, not a single authoritative source).
- **Temporal check:** All 2024-2025 sources, current.
- **Conflicts with existing project research?** The existing plan mentions "any consulting type" (Jack Directive 4) but does not define types or routing logic. This finding provides the missing implementation layer. No contradiction.
- **Verdict:** ADOPT the 5-type taxonomy and routing. INVESTIGATE hybrid classification for multi-type queries.
- **Justification:** Jack's Directive 4 requires support for any engagement type (auto shop chain, M&A, operations). Without classification and routing, the Spec Engine produces the same pipeline for a market sizing query and a strategic options analysis — which produces systematically weaker output. This is the mechanism that makes the engine generalist.
- **Keystone impact:** Adds a classifier module (likely part of spec_engine.py or a new engagement_classifier.py) that runs before issue tree construction. All downstream configuration — agent count, tool selection, research mode (sequential vs. parallel), task density — becomes a function of engagement type. This is architecturally significant: it means the agent config is a two-step process (type-classify first, then configure).
- **Contradicts:** Nothing. Enables Directive 1 (dynamic agent config) by providing the input the dynamic configurator needs.

---

### 3. Decision-First Chain-of-Thought and TiCoder divergence detection for intent clarification

- **What:** Intent clarification should use a structured 5-step Decision-First CoT sequence: (1) What decision will this inform? (2) What is the client's current default position? (3) What evidence would change their mind? (4) What evidence would confirm? (5) What research questions must be answered? Separately, the TiCoder pattern — generate 2-3 candidate research plans, identify where they diverge, surface divergence points as clarifying questions — improves correctness from 40% to 84%.
- **Evidence basis:** McKinsey Problem Statement Worksheet (verified, extensively documented); RSA framework (Frank & Goodman 2012, published in Science); CEI benchmark (arXiv 2603.09993) showing LLMs at 25% on pragmatic inference vs 54% human majority; TiCoder (Lahiri et al., 2022) with measured 40→84% improvement; SAGE-Agent (OpenReview 2025) with 7-39% higher coverage.
- **Evidence quality:** Verified for McKinsey methodology and TiCoder improvement numbers. Verified for the CEI finding about LLM pragmatic inference weakness (this is the critical negative finding). Credible for SAGE-Agent.
- **Temporal check:** CEI benchmark March 2026 — directly current. RSA framework 2012 but foundational and actively extended through 2025.
- **Conflicts with existing project research?** The existing plan has intent_clarifier.py as a named component but does not specify its internal logic. This provides the logic. The finding that LLMs perform at 25% on pragmatic inference is a constraint the existing plan does not account for — it means intent_clarifier.py cannot rely on implicit inference and must use structured prompting.
- **Verdict:** ADOPT Decision-First CoT as the intent_clarifier.py prompting pattern. ADOPT TiCoder divergence detection for surfacing clarifying questions. INVESTIGATE EVPI-based question selection as Phase 2 enhancement.
- **Justification:** The 25% pragmatic inference finding is the most important negative constraint in this report. The Spec Engine is a Level 3 Intent Engineering system by design; if the LLM cannot reliably infer intent implicitly, the only alternative is making inference explicit through structure. Decision-First CoT is that structure. TiCoder's 40→84% improvement is a substantial, measured gain from a technique with low implementation cost.
- **Keystone impact:** Directly shapes intent_clarifier.py implementation. The 5-step CoT becomes the system prompt structure for that component. The TiCoder pattern adds a second pass — generate candidate plans before generating the final plan — which means intent_clarifier.py produces intermediate artifacts that feed into decomposer.py.
- **Contradicts:** Nothing.

---

### 4. Four-phase issue tree deliberation pipeline with Self-MoA pattern

- **What:** Issue tree construction should run four phases: (1) Parallel Construction — three Sonnet agents with different personas (First Principles, Industry Framework, Creative Decomposer) each produce a full tree; (2) Structural Analysis — programmatic metric computation on tree structure (no LLM cost); (3) MECE Evaluation — Opus as judge using atomic binary criteria (pass/fail per criterion more reliable than numeric scoring); (4) Synthesis — Opus as meta-agent performing MoA-style generative aggregation across the three trees. Self-MoA (same-model multiple instances) outperforms Mixed-MoA by 6.6% because quality sensitivity penalizes model mixing.
- **Evidence basis:** MoA paper (Wang et al. 2024, arXiv 2406.04692) — SOTA on AlpacaEval 2.0 at 65.1% vs GPT-4 Omni 57.5%; Self-MoA follow-up (arXiv 2502.00674) with 6.6% improvement; AOP framework for atomic MECE validation; Delphi methodology for anonymity/structured feedback principles.
- **Evidence quality:** Verified for MoA paper results. Credible for Self-MoA 6.6% figure (recent but sourced). Credible for binary verdict reliability (pattern from DeepEval/ConfidentAI, not a controlled study). Verified for Delphi methodology principles.
- **Temporal check:** MoA 2024, Self-MoA 2025 — current. Delphi foundational.
- **Conflicts with existing project research?** Jack's Directive 2 already specifies MULTIPLE agents constructing MECE issue trees independently before deliberation — this finding provides the precise architecture for that directive. Settled Decision 2 (deliberation = independent parallel analysis + structured aggregation, not debate) is exactly the Self-MoA pattern. Perfect alignment.
- **Verdict:** ADOPT the four-phase pipeline structure. ADOPT Self-MoA with persona-diverse agents. ADOPT atomic binary criteria for MECE evaluation. ADAPT Delphi logic-convergence analysis for Phase 2. Note: the 6.6% Self-MoA figure is credible but the mechanism (quality sensitivity to model mixing) should be monitored in practice.
- **Justification:** The Phase 2 (structural analysis, programmatic) step is especially valuable: it provides useful signal at zero LLM cost, giving the Opus judge structured input rather than raw tree text. The binary verdict approach for MECE evaluation is consistent with the broader finding (from other batch-2 reports) that LLM judges are more reliable on binary determinations than numeric scales.
- **Keystone impact:** This is the implementation specification for Jack's Directive 2. It adds a structural_analyzer.py utility (programmatic, no model) between tree construction and Opus evaluation. The four phases map to: decomposer.py (Phase 1), new structural_analyzer.py (Phase 2), evaluator.py with modified prompting (Phase 3), and a new tree_synthesizer.py or extended meta_aggregator.py (Phase 4).
- **Contradicts:** Nothing. Fully implements Settled Decision 2.

---

### 5. Scout/strike with Day-1 hypothesis, VOI-inspired prioritization, and dual stopping criteria

- **What:** Scout phase should begin by forming a Day-1 best-guess answer (not neutral exploration). VOI-inspired task priority score: (decision_relevance × current_uncertainty) / estimated_cost. Dual stopping criteria: (1) sufficiency — has the working answer met quality thresholds? and (2) diminishing returns — is marginal information gain per token declining below threshold? Optimal exploration-exploitation ratio starts ~70/30 scout/strike, shifts to ~20/80 as knowledge accumulates.
- **Evidence basis:** PLOS ONE multidisciplinary framework on exploration-exploitation lifecycle (Verified); Anthropic engineering blog confirming "start wide, narrow progressively" as validated approach (Verified — they also note that early agent versions failed by being too specific too early); ISPOR VOI framework from health economics (Verified); Information Foraging Theory / Marginal Value Theorem (Verified — foundational).
- **Evidence quality:** Verified across all four source categories.
- **Temporal check:** PLOS ONE and Anthropic blog are current. IFT and MVT are foundational (pre-2000) but validated and actively applied.
- **Conflicts with existing project research?** The existing plan has scout/strike but does not specify the Day-1 hypothesis requirement, the VOI-based prioritization formula, or the stopping criteria. This fills the operational gaps. Jack's Directive 3 asks "Who decides new research? Max rounds? Stopping conditions?" — the dual stopping criteria answer that question.
- **Verdict:** ADOPT scout/strike with Day-1 hypothesis. ADAPT VOI formula (simplified, not formal EVPI analysis). ADOPT dual stopping criteria. INVESTIGATE MCTS/UCB-inspired branch selection for Phase 2.
- **Justification:** The Day-1 hypothesis requirement is a low-cost, high-value addition: it anchors the entire scout phase to a testable claim rather than open-ended exploration, which prevents the AutoGPT failure mode of infinite-loop exploration with no convergence. The VOI formula provides a principled basis for task prioritization that currently does not exist in the plan.
- **Keystone impact:** Modifies scout_strike.py. Adds a hypothesis_tracker.py responsibility (tracks Day-1 hypothesis, updates based on findings). The priority score formula should appear in research-tasks.json schema as a computed field. Stopping criteria logic belongs in scout_strike.py or a new stopping_evaluator.py.
- **Contradicts:** Nothing.

---

### 6. Observation Library as CBR system with pgvector + compiled wiki hybrid

- **What:** The Observation Library should be implemented as a Case-Based Reasoning (CBR) system using the classic R4 cycle — Retrieve/Reuse/Revise/Retain. Technical architecture: Layer 1 is PostgreSQL + pgvector with HNSW indexing for semantic retrieval; Layer 2 is a compiled Karpathy-pattern wiki stored in PostgreSQL (not filesystem) for synthesis; Layer 3 is a PydanticAI CBR engine executing the R4 cycle. After each engagement, extract three types of guidance: strategy tips (from successes), recovery tips (from failures), and optimization tips (from inefficient-but-successful paths). Trajectory-Informed Memory paper (arXiv 2603.10600) achieved 14.3 percentage point improvement on AppWorld.
- **Evidence basis:** CBR R4 cycle (Aamodt & Plaza 1994 — foundational and validated); McKinsey knowledge management verified (StrategyU firsthand + HBS Case Study 396357); Karpathy wiki pattern (April 2026 — directly current); Trajectory-Informed Memory (March 2026, arXiv 2603.10600); pgvector + HNSW is a verified production pattern.
- **Evidence quality:** Verified for CBR paradigm and McKinsey practice. Credible for Trajectory-Informed Memory improvement numbers (recent, benchmarked, but single paper). Verified for Karpathy wiki pattern (primary source, April 2026).
- **Temporal check:** Karpathy post is April 2026 — the most current source in the batch. Trajectory-Informed Memory is March 2026. Both directly relevant.
- **Conflicts with existing project research?** Jack's Directive 8 specifies Karpathy compiled markdown wikis. This report aligns exactly with that directive and extends it with the CBR framing and pgvector layer. The existing plan's Observation Library definition ("captures all outcomes -> structured entries -> permanent constraints + reinforced patterns") maps directly to the CBR R4 cycle.
- **Verdict:** ADOPT CBR R4 as the foundational paradigm. ADOPT pgvector + structured metadata as retrieval layer. ADAPT Karpathy wiki as compiled synthesis layer in PostgreSQL. ADOPT trajectory-informed extraction (strategy/recovery/optimization tips). SKIP Neo4j knowledge graphs (premature complexity). SKIP fine-tuning on observations (insufficient data volume; RAG superior).
- **Justification:** The CBR framing is the key clarifying contribution: it reframes the Observation Library from a passive log into an active retrieval system. The distinction matters architecturally — a log is queried by lookup; a CBR system is queried by similarity and actively adapts retrieved content to new context. The Retrieve step must run at engagement start (not just at end for storage), which means the Spec Engine needs to query the library as one of its first actions.
- **Keystone impact:** Adds a library query step to the Spec Engine flow — before hypothesis generation, check for similar past engagements and seed the hypothesis list with past patterns. The existing plan does not specify when or how the Spec Engine consults the Observation Library. This finding mandates an explicit integration point at Step 1 (Problem Framing) and Step 2 (Hypothesis Generation).
- **Contradicts:** Nothing. Directly implements Directive 8.

---

### 7. Production system patterns: orchestrator-worker with iterative revision, hybrid static/dynamic workflows, and AutoGPT failure modes

- **What:** Universal cross-system patterns: (1) orchestrator-worker with iterative plan revision (Anthropic 90.2% improvement over single-agent on internal evals); (2) query fan-out to 8-12 sub-queries is universal; (3) hybrid static/dynamic workflows outperform pure dynamic (predefined phases + dynamic LLM planning within each phase); (4) context window management is the critical bottleneck — multi-agent systems use ~15x more tokens than chat. AutoGPT failures (infinite looping, hallucinated task completion, cascading errors from early mistakes) are the precise failure modes to guard against.
- **Evidence basis:** Anthropic engineering blog June 2025 (Verified); Perplexity DRACO benchmark (Verified); HuggingFace survey Sep 2025 (Credible); OpenAI system card (Verified).
- **Evidence quality:** Verified for the 90.2% figure and 15x token multiplier. Credible for hybrid workflow superiority (survey-based).
- **Temporal check:** All 2025 sources, current.
- **Conflicts with existing project research?** The 15x token multiplier is a constraint the existing cost estimates (Gap #7: $12-100 per engagement) need to be checked against. The existing plan references Settled Decision 7 (generator-based agent loop as orchestration primitive) which implements the orchestrator-worker pattern correctly.
- **Verdict:** ADOPT hybrid static/dynamic workflow framing. The specific AutoGPT failure modes should be added to the Observation Library's initial seed entries as known failure patterns.
- **Justification:** The 15x token multiplier combined with the 90.2% internal eval improvement quantifies the core tradeoff: multi-agent costs more but produces dramatically better output. This empirical grounding supports Jack's Directive 5 (capability expansion, not cost reduction). The AutoGPT failures are canonical; encoding them as early Observation Library entries protects the system from day-one failures.
- **Keystone impact:** The 15x multiplier should be input to the VOI priority scoring — token cost is the denominator in the priority formula. The hybrid static/dynamic framing validates the scout/strike architecture (predefined phases) plus dynamic task generation within each phase.
- **Contradicts:** Nothing.

---

## Architectural Decisions This Enables

**A. The 10-step Spec Engine flow is now fully specified.**
The existing plan had a 7-step flow with gaps at problem framing and feedback. This report closes both gaps with sourced implementations. The complete sequence:
1. Problem Framing + Classification (new — engagement type classifier)
2. Hypothesis Generation (new — Day-1 hypothesis, multiple competing hypotheses)
3. Issue Tree Decomposition (existing — now with 3 Sonnet agents + persona diversity)
4. Decomposition Validation (new — AOP solvability/completeness/non-redundancy)
5. Priority Assignment (existing — now with VOI-inspired scoring)
6. Dynamic Agent Configuration (existing — now routing from engagement type)
7. Task Generation (existing — now with success criteria per task + anti-confirmatory framing)
8. Human Review Gate (existing — now informed by TiCoder divergence points)
9. Research Execution, Scout Phase (existing — now with Day-1 hypothesis anchor)
10. Feedback Loop (new — findings -> issue tree refinement -> task reprioritization)

**B. Engagement type taxonomy unblocks dynamic agent configuration.**
Jack's Directive 1 requires the Spec Engine to generate custom configs dynamically instead of using fixed templates. The 5-type taxonomy is the input signal that makes dynamic configuration deterministic rather than unconstrained: type determines pipeline mode (sequential vs. parallel), which determines agent count, tool selection, and task density.

**C. CBR framing mandates an Observation Library query at Spec Engine entry, not just exit.**
The R4 cycle Retrieve step means the library must be queried before hypothesis generation. This establishes a hard integration dependency between Component #5 (Spec Engine) and the Observation Library that is currently unspecified in PHASE-1-IMPLEMENTATION-SPEC.md.

**D. The four-phase issue tree pipeline is now the implementation specification for Settled Decision 2.**
Settled Decision 2 defines deliberation as independent parallel analysis + structured aggregation. This report gives that definition a concrete 4-phase implementation with specified agents, personas, evaluation criteria, and synthesis method.

**E. Human review gate content is now defined.**
The existing plan specifies that human review gates exist but not what the human sees. TiCoder divergence detection provides the answer: present the divergence points between candidate plans — not just a single plan — so the human can review where the system is uncertain.

---

## Changes to Existing Plan

**Change 1 — CAPSTONE-PLAN-v2.md Section 3: Replace 7-step flow with 10-step flow.**
Add Steps 1 (Problem Framing), 2 (Hypothesis Generation), 4 (Decomposition Validation), 10 (Feedback Loop) as described above. Rename the former Step 4 (verification) as the decomposition validation gate.

**Change 2 — PHASE-1-IMPLEMENTATION-SPEC.md Component #5: Add three new sub-components.**
Current sub-components: spec_engine.py, intent_clarifier.py, decomposer.py, validator.py, scout_strike.py.
New sub-components to add: engagement_classifier.py (5-type taxonomy routing), structural_analyzer.py (programmatic tree metrics), tree_synthesizer.py (MoA meta-aggregation), feedback_loop.py (execution results -> spec revision). The CBR library query should be integrated into spec_engine.py entry logic.

**Change 3 — research-tasks.json schema: Add priority score field.**
Add `priority_score: float` computed as `(decision_relevance * current_uncertainty) / estimated_cost` where decision_relevance maps to the existing target_decision_usefulness field. This makes priority computationally derived rather than manually assigned.

**Change 4 — Observation Library spec: Reframe as CBR system with Layer 1 (pgvector) + Layer 2 (compiled wiki).**
Currently the plan describes the Observation Library as a capture mechanism. It should be redefined as an active CBR retrieval system that the Spec Engine queries at startup. Add the three-type extraction taxonomy (strategy/recovery/optimization tips) to the post-engagement retention process.

**Change 5 — intent_clarifier.py implementation: Specify Decision-First CoT + TiCoder pattern.**
Add the 5-step Decision-First CoT as the system prompt structure. Add a TiCoder pass (generate 2-3 candidate research plans, identify divergence, surface as questions) before returning the final clarified intent.

**Change 6 — Engagement scope acceptance criteria.**
The existing acceptance criteria (Component #5) specify "rejects underspecified questions." This should be refined: the system uses TiCoder divergence detection to surface clarifying questions rather than hard-rejecting. Rejection should be reserved for queries with no identifiable decision context even after clarification.

---

## Open Questions Remaining

**OQ-1 (Cross-report dependency — Report 01): Iterative research rounds.**
This report specifies the Feedback Loop (Step 10) at the level of "findings -> issue tree refinement -> task reprioritization" but does not specify the mechanism for mid-research scope expansion. Jack's Directive 3 asks: "Who decides new research? Max rounds? Stopping conditions?" The dual stopping criteria (sufficiency + diminishing returns) partially answer this, but the governance question — which component has authority to spawn new research tasks mid-engagement — is not resolved. Report 01 (iterative research) is the primary reference; its analysis should be checked for this.

**OQ-2 (Cross-report dependency — Report 02): Dynamic agent configuration schema.**
The 5-type taxonomy determines routing, but the schema of the resulting agent configuration is not defined here. What fields does a type-STRATEGIC configuration have that a type-SIZING configuration does not? Report 02 (dynamic agents) is the primary reference for this.

**OQ-3 (Cross-report dependency — Report 05): Engagement taxonomy overlap.**
Report 05 covers engagement taxonomy independently. The 5-type taxonomy here (SIZING/DIAGNOSTIC/EVALUATIVE/EXPLORATORY/STRATEGIC) may differ from Report 05's classification. The master synthesis must reconcile these. Until reconciled, this taxonomy should be treated as Credible-pending-reconciliation, not Verified.

**OQ-4 (Cross-report dependency — Report 07): Adaptive evaluation per engagement type.**
If the Spec Engine produces type-specific pipelines, the Evaluator (Component #6) must evaluate against type-specific criteria. A SIZING engagement should be evaluated on calculation accuracy; a STRATEGIC engagement on scenario completeness. Report 07 (adaptive eval) is the primary reference for whether the evaluator already handles this.

**OQ-5 (Cost validation): 15x token multiplier against engagement cost targets.**
The $12-100 per engagement cost target (Gap #7) was validated before the 15x multiplier was surfaced. With a multi-agent system consuming ~15x more tokens than single-agent chat, this target needs re-verification. The 10-step pipeline with 3 Sonnet agents for tree construction + 1 Opus meta-agent + parallel L1 research agents will be significantly more expensive than the original estimates assumed. This is a budget-critical validation gap.

**OQ-6 (Implementation sequence): When does the Observation Library CBR query run?**
The R4 Retrieve step should run at Spec Engine entry, but the Observation Library does not yet exist in Phase 1 (it is a Phase 2 component in the current plan). Phase 1 must either (a) initialize the library with seed entries (AutoGPT failure modes, known good patterns) before the first engagement, or (b) make the CBR query optional/bypass-able when the library is empty. This decision affects Component #5 acceptance criteria.

**OQ-7 (Self-MoA reproducibility): Model and context sensitivity.**
The 6.6% Self-MoA improvement over Mixed-MoA is from a single follow-up paper. The claim that "MoA performance is sensitive to quality and model mixing lowers average quality" is a mechanism claim, not a universal law. In practice, whether three Sonnet instances outperform a Sonnet + Haiku + Sonnet mix depends on the task. This should be treated as a reasonable default but tested empirically in Phase 1 evaluation.

**OQ-8 (Observation Library storage): PostgreSQL vs. filesystem for Karpathy wiki.**
The report recommends storing the compiled wiki in PostgreSQL rather than filesystem (adapting Karpathy's original pattern). This is a defensible choice for a production system, but Karpathy's original recommendation is filesystem-based markdown — which is simpler and Git-trackable. Jack's Directive 8 specifies "compiled markdown wikis," which implies filesystem. This is a concrete technical decision that needs resolution before implementation.

---

*Cross-report dependencies confirmed: Reports 01 (OQ-1), 02 (OQ-2), 03 (issue tree — fully resolved here), 05 (OQ-3), 07 (OQ-4). This report is self-sufficient for the Spec Engine core flow; it requires reconciliation with 01, 02, 05, 07 before the master architecture is finalized.*
