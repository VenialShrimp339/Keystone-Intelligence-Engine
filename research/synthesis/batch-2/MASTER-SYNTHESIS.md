# Batch 2 Deep Research: Master Synthesis
*2026-04-05 | 10 reports analyzed | 16 architectural decisions resolved*

---

## 1. The Architecture That Emerges

The 10 Batch 2 reports, analyzed in parallel by independent Opus subagents, converge on an architecture that is more concrete, more principled, and in several places structurally different from what CAPSTONE-PLAN-v2.md describes today. The convergence is the headline: findings from reports that could not see each other arrive at the same conclusions through different evidence paths. Where they diverge, the divergences are resolvable. The result is a buildable system.

### The Specification Engine Flow (10 Steps, Not 7)

The Specification Engine is now fully specified as a 10-step pipeline. Reports 03, 05, and 10 independently converge on the same structural additions, each from a different angle (consulting methodology, AI planning research, and production system analysis). The complete flow:

1. **Problem Framing and Classification.** An engagement classifier routes incoming queries to one of five types (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC), using five signals: specificity of deliverable, presence of testable hypothesis, known analytical framework, scope boundedness, and decision type. The Observation Library is queried at this step via CBR Retrieve, seeding the hypothesis space with patterns from prior engagements. Intent clarification uses a Decision-First Chain-of-Thought (5-step structured prompt) because LLMs score only 25% on pragmatic inference (CEI benchmark, March 2026). TiCoder divergence detection (generate 2-3 candidate plans, surface where they disagree as clarifying questions) improves correctness from 40% to 84%.

2. **Hypothesis Generation.** A Day-1 Hypothesis is formed before decomposition begins, anchoring the entire research process to a testable claim rather than open-ended exploration. This prevents the AutoGPT infinite-loop failure mode. Multiple competing hypotheses are generated and ranked.

3. **Issue Tree Decomposition.** Three Sonnet agents with distinct consulting lenses (financial, operational, market/competitive) independently construct 2-3 level shallow issue trees, using hypothesis-driven branch framing, Plan-and-Solve + Skeleton-of-Thought prompting, and 2-3 curated MECE exemplars. Pydantic models enforce reasoning-first field ordering. The shallow start (8-20 leaf nodes) is deliberate: ADaPT-style adaptive deepening occurs during research, not upfront. This reduces human review burden and costs.

4. **Decomposition Validation.** A discrete MECE verification step using Opus as evaluator checks five dimensions (mutual exclusivity, collective exhaustiveness, tailoring, actionability, depth appropriateness) with atomic binary criteria. Programmatic semantic similarity checks complement the LLM judge. Trees failing verification are regenerated.

5. **Priority Assignment.** VOI-inspired scoring: `(decision_relevance x current_uncertainty) / estimated_cost`. Multi-signal branch prioritization (sampling consistency, feasibility estimation, structured rubric). Priority is a working hypothesis reprioritized each cycle, not a commitment.

6. **Dynamic Agent Configuration.** The engagement type drives a template registry query. Above 0.85 similarity: instantiate with task-specific interpolation. Below: generate a custom AgentDefinition constrained by structural validation and the tighten-only invariant. Token budget is set per agent (80% of performance variance is token usage, not config sophistication).

7. **Task Generation.** Research-tasks.json with DAG dependency structure (not flat list), anti-confirmatory framing, per-branch "end product" specification (specific chart type, table structure, conclusion format), and the priority score as a computed field.

8. **Human Review Gate.** Non-negotiable (Jack's Directive 7). The human sees: the issue tree, divergence points from TiCoder, the sprint contract proposed by the Evaluator, and the agent configurations. Implemented as a database state machine in Phase 1 with approve/modify/reject flows.

9. **Research Execution (Scout Phase).** Day-1 Hypothesis anchors the scout phase. Exploration-exploitation ratio starts ~70/30 scout/strike, shifts to ~20/80 as knowledge accumulates.

10. **Feedback Loop.** Findings feed back into issue tree refinement and task reprioritization. Completed tasks are immutable; only pending tasks can be modified. Three replanning cycles maximum.

### The Iterative Research Loop (Fully Specified)

This was Jack's identified "single biggest architectural gap." Reports 01, 06, and 10 together resolve it completely:

**Stopping criteria (three-criterion combination, any can terminate):**
- Hard iteration cap: 3 default, 5 max, never exceed 5 without logged justification
- Quality gate: L4 Evaluator applied mid-pipeline, scoring research completeness against RESEARCH.md
- Semantic novelty exhaustion: no new claims in the latest round

**Decision logic per round:**

| Signal | Decision |
|--------|----------|
| Quality gate score < threshold AND round < max | Spawn new research (broader coverage) |
| Score < threshold on specific dimension AND novelty exhaustion on that dimension | Go deeper (targeted subagents on gap) |
| Quality gate score >= threshold | Stop |
| Round cap reached | Stop (log reasoning) |
| Scope-change detected | Hierarchical replan |

**Scope-change protocol:** A lightweight Haiku-tier scope-change detector classifies findings as In-Plan (minor adjustment to scratchpad) or Out-of-Plan (triggers human gate per Directive 7).

**Between-round continuity:** The orchestrator (Opus) maintains a persistent Memory scratchpad (`research-state.md`) carrying: current RESEARCH.md intent, key findings to date, open gaps, scope-change log, and stopping condition status. Opus 4.6 does not suffer context anxiety, so compaction within a round is safe. Between rounds, persist to file and read at round start.

### Agent Configuration Strategy

The five fixed research agent types and five fixed deliberation analyst types become seed templates in a registry, not enum dispatch values. The Specification Engine queries the registry first; below the similarity threshold, it generates custom AgentDefinitions. The 10 seed templates (5 research + 5 deliberation) are the starting population; successful custom configs are promoted to the registry via a Phase 3 promotion loop.

Key constraints: tools[] assignment is the primary behavioral governance mechanism (not system prompt); the tighten-only invariant prevents privilege escalation in dynamic hierarchies; complexity-scaled spawning (1 agent for simple fact-finding, 2-4 for comparisons, up to 5 for complex research in Phase 1); token budget per agent is set by the Spec Engine and dominates quality outcomes.

### Retrieval and Knowledge Accumulation Architecture

Component #3 splits into two focused deliverables:

**#3a Source Discovery:** pgvector + ParadeDB (BM25 + RRF fusion), Voyage-finance-2 embeddings ($0.12/MTok, 49% improvement over OpenAI on financial QA), contextual retrieval at ingest (Haiku-generated preamble per chunk, 67% failure reduction combined with reranking, zero cost on Claude Max), Cohere Rerank v3.5 (top 150 -> rerank -> top 20), Docling for structure-aware parsing (97.9% table accuracy), Brave Search + Exa for external discovery. Semantic Router and Bifrost caching are removed.

**#3b Knowledge Accumulation:** Compiled markdown wiki per engagement following Karpathy's three-layer pattern (`raw/` for full subagent artifacts, `compiled/` for orchestrator-synthesized findings, `INDEX.md` auto-maintained). Citation provenance via content-hash per proposition. Human-designed schemas (ETH Zurich: human-written +4%, LLM-generated -2%). This layer feeds the Observation Library and cross-engagement knowledge base.

The principle: RAG for discovery (finding sources not yet ingested), filesystem navigation for accumulated knowledge (Karpathy pattern). King's College London (February 2026) confirms structure-driven retrieval outperforms similarity-driven for agent memory.

### Evaluation Framework

**Aggregation:** Geometric mean replaces implicit weighted sum. Prevents dimension compensation (a high Narrative Coherence score cannot mask failing Intellectual Honesty).

**Two-tier rubric structure:**
- **Tier 1 Universal Gates** (floor thresholds, failure = rejection regardless of Tier 2): Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence
- **Tier 2 Adaptive Dimensions** (weights flex by engagement type): Analytical Depth, Source Quality, Quantitative Rigor, Actionability, Evaluative Surprise, Calibrated Confidence

**8-10 engagement-type evaluation profiles** replace the current two-profile (estimative/current) system, covering the actual Keystone consulting portfolio. Issue tree branch classification (Bloom's Taxonomy cognitive level + quantitative/qualitative nature) drives weight generation.

**Sprint contract directionality:** Evaluator proposes criteria (from classified issue tree), Generator reviews and negotiates, both commit before research begins. Designed as optional scaffold that degrades gracefully as models improve.

**Dimension-specific verification:** Quantitative Rigor and Analytical Depth are precisely where LLM judges are least reliable (47-68% agreement). Quantitative Rigor gets programmatic verification complement. Analytical Depth gets mandatory position-switching.

### Context Management Approach

**Orchestrator (Opus 4.6):** Compaction within a round is safe (context anxiety eliminated). Between rounds, persist to `research-state.md`. Hard ceiling: 140-160K tokens (70-80% of 200K). Research plan at context start, most recent findings at context end.

**Subagents (Sonnet):** Clean context window per task. Ceiling: 100K tokens. Output: Pydantic-schemaed structured summary (~1,500 tokens with 3-7 claims, per-claim confidence scores, source counts) AND full artifact written to `{engagement_id}/memory/raw/`. The 37% information retention figure from Factory.ai is the failure mode to guard against.

**Between-round:** Orchestrator compiles round N findings into `compiled/`, updates `INDEX.md`. Subagents in round N+1 receive selected excerpts from `compiled/` via JIT context loading.

### Orchestration Pattern

**Confirmed stack:** PydanticAI (v1.0+, production-stable) for typed agents with structured outputs. Custom async orchestration for Phase 1. Temporal deferred to Phase 2 with five Day-1 coding standards enforced: pure function layers, Pydantic inter-layer data, separate controller, correlation IDs, idempotency. MCP for tool integration. Agent SDK removed from primary stack (Claude-only, proprietary ToS).

**Error recovery ships in Phase 1:** Retry with exponential backoff (tenacity), model fallback chains (Opus -> Sonnet -> Haiku -> cached), error classification, PostgreSQL checkpointing. Claude API has 62 incidents in 90 days.

**HITL implementation for Phase 1:** Database state machine (3 PostgreSQL tables, REST API, web UI). Approve/modify/reject flows. Maps to Temporal Signals in Phase 2 with no agent code changes.

---

## 2. Contradiction Resolution

### 2.1 Observation Library Storage: PostgreSQL vs. Filesystem

**Reports involved:** Report 04 (filesystem Karpathy pattern), Report 06 (filesystem three-layer), Report 10 (PostgreSQL + pgvector)
**What they disagree on:** Whether the compiled wiki lives on the filesystem (Karpathy's original pattern) or in PostgreSQL.
**Resolution:** Filesystem for Phase 1, PostgreSQL for Phase 2. Jack's Directive 8 says "compiled markdown wikis," implying filesystem. The Karpathy pattern is filesystem-native and Git-trackable. For a single-user Claude Max deployment, filesystem is simpler and sufficient. When cross-engagement knowledge accumulates to thousands of articles requiring concurrent access and semantic search, migrate to PostgreSQL. Design the wiki schema to be storage-agnostic from Day 1.

### 2.2 Self-MoA (Same Model) vs. Cross-Provider Diversity

**Reports involved:** Report 10 (Self-MoA +6.6% for issue trees), Settled Decision (cross-provider diversity required for deliberation)
**What they disagree on:** Whether to use the same model family or cross-provider models for parallel analysis.
**Resolution:** Both are correct at different pipeline stages. Self-MoA for issue tree construction (L0) because quality sensitivity penalizes model mixing during creative decomposition. Cross-provider diversity for deliberation (L1.5) and evaluation (L4) because bias mitigation matters more than quality sensitivity when assessing evidence. The Self-MoA finding applies to generation tasks; the cross-provider finding applies to judgment tasks. No change to settled decisions needed.

### 2.3 Engagement Taxonomy: 5-Type (Report 10) vs. 10-Category (Report 05)

**Reports involved:** Report 05 (10 MBB engagement categories), Report 10 (5 pipeline routing types)
**What they disagree on:** The granularity and purpose of engagement classification.
**Resolution:** These are different taxonomies serving different purposes. Report 05's 10 categories (Corporate Strategy, Operations, M&A, etc.) describe the *domain* of the engagement. Report 10's 5 types (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) describe the *analytical mode* of the pipeline. A single engagement can be "M&A" (domain) and "EVALUATIVE + SIZING" (analytical mode). The Spec Engine uses the 5-type taxonomy for pipeline routing. The 10-category taxonomy feeds into the Observation Library retrieval (similar past engagements) and framework selection. Both should be implemented; they are orthogonal, not competing.

### 2.4 Sprint Contract Directionality

**Reports involved:** Report 07 (Evaluator proposes, Generator reviews), Existing plan (says "negotiated" without direction)
**Resolution:** Report 07 is correct and more specific. The Evaluator proposes criteria derived from the classified issue tree, the Generator reviews and confirms achievability, both commit. This is a clarification of the existing plan, not a contradiction.

### 2.5 Rubric Aggregation Method

**Reports involved:** Report 07 (geometric mean), Existing plan (implicit weighted sum)
**Resolution:** Adopt geometric mean. The existing plan never explicitly specified weighted sum; it was the implicit default. Three independent frameworks (Stanford HELM, MQM, AdaRubric) use geometric mean specifically because it prevents dimension compensation. This is an unambiguous improvement.

### 2.6 Claude Agent SDK Role

**Reports involved:** Report 09 (disqualify as primary), CAPSTONE-PLAN-v2.md Section 12.0 ("execution substrate")
**Resolution:** Report 09 is correct. The Agent SDK is Claude-only with proprietary ToS and Node.js subprocess overhead. Standard research agents should use PydanticAI calling Claude API directly. Agent SDK is reserved for future nodes requiring full Claude Code runtime (computer use, code execution). Update the plan.

---

## 3. Convergent Findings (Appeared in 3+ Reports)

### 3.1 Token Usage Dominates Performance (Reports 01, 02, 09, 10)
Token usage explains 80% of performance variance in Anthropic's multi-agent system. Multi-agent uses ~15x more tokens than single chat. The Specification Engine's effort calibration (how many agents, what token budgets) is the primary quality and cost lever. Architectural sophistication of agent configs is secondary.

### 3.2 4-Agent Coordination Plateau (Reports 02, 03, 06)
Google DeepMind (180 configurations): coordination gains plateau beyond 4 agents, with up to 70% degradation on sequential tasks and 17.2x error amplification in poorly structured networks. Validates the 3-5 agent default. For issue tree generation: 3-4 agents maximum.

### 3.3 Structured Handoffs + Isolation > Context Accumulation (Reports 01, 06, 09)
Context resets for Sonnet subagents with structured handoff artifacts (1,000-2,000 token summaries + full external files) consistently outperform context accumulation. Opus 4.6 orchestrator can use compaction. The "artifact bypass" pattern (structured summary + full file) is mandatory, not optional.

### 3.4 Dynamic Config from Templates, Not Enums (Reports 01, 02, 03, 05, 10)
Every major production framework has converged on `Agent = (system_prompt, tools[], output_schema, constraints)` as a declarative configuration. Five fixed types become seed templates in a registry. Anthropic's own system dynamically spawns subagents with per-task configs.

### 3.5 Karpathy Pattern Confirmed for Accumulated Knowledge (Reports 04, 06, 10)
Compiled markdown wikis with three-layer structure (raw/, compiled/, INDEX.md) are the correct mechanism for within-engagement and cross-engagement knowledge. File-based memory (74%) outperforms specialized tools like Mem0 (68.5%). RAG for discovery, filesystem navigation for accumulated knowledge.

### 3.6 Tool Assignment as Hard Behavioral Constraint (Reports 02, 08, 09)
Tool restriction is a hard behavioral constraint; prompt instruction is soft guidance that models may ignore. The tools[] assignment in AgentDefinition is the primary enforcement mechanism. The MCP gateway becomes the enforcement point.

### 3.7 Selection Over Synthesis for Aggregation (Reports 03, 06)
Judge-based claim selection achieves 81% win rate; synthesis-based blending scores 51.2% (near chance). Deliberation aggregation must be selection-based with per-claim confidence scores and source counts. Synthesis "introduces incoherence, conflicting perspectives, and diluted arguments."

### 3.8 Issue Tree as Living Document with Shallow Start (Reports 03, 05, 10)
ADaPT shallow-then-adaptive decomposition (+28.3%) is superior to deep upfront planning. Start with 2-3 levels, deepen when research agents report complexity. Three replanning cycles maximum. Completed tasks immutable.

---

## 4. The 11 Settled Decisions: Validated or Challenged?

| # | Decision | Status | Evidence |
|---|----------|--------|----------|
| 1 | Custom orchestration (PydanticAI + Temporal + MCP) | **VALIDATED** | PydanticAI v1.0 production-stable (R09). Temporal deferral correct with 5 Day-1 requirements (R09). MCP ecosystem mature (R08). |
| 2 | Deliberation = independent parallel + structured aggregation | **VALIDATED + SHARPENED** | Selection over synthesis (R06: 81% vs 51.2%). Four-phase issue tree deliberation specified (R10). Self-MoA for generation, cross-provider for judgment. |
| 3 | Five-layer evaluator stack | **VALIDATED + EXTENDED** | Two-tier rubric split (R07). Geometric mean aggregation (R07). Dimension-specific verification strategies (R07). 8-10 engagement profiles (R07). |
| 4 | Opus L0/L4, Sonnet L1, Haiku extraction | **VALIDATED** | Opus context anxiety eliminated (R06). Capability-dependent harness design (R01). Haiku for contextual retrieval preambles (R04). |
| 5 | Agent isolation: filesystem-based, 3-5 tools | **VALIDATED + STRENGTHENED** | Tools as hard behavioral constraint (R02). 4-handoff failure ceiling (R06). Artifact bypass pattern (R06). |
| 6 | Claim-level IR at L1->L2 | **VALIDATED** | Already more rigorous than Karpathy default (R04). Content-hash provenance extends it (R04). Selection-based aggregation depends on it (R06). |
| 7 | Generator-based agent loop | **VALIDATED** | DAG backbone + L1 supervisor confirmed (R09). 90.2% improvement over single-agent (R09). |
| 8 | Protocol-based contracts (structural typing) | **VALIDATED** | Agent-as-declarative-config convergence (R02). Tighten-only invariant as schema constraint (R02). |
| 9 | Events as type union | **NOT TESTED** | No report addressed event dispatch architecture. Remains settled by prior analysis. |
| 10 | Multi-tenancy (engagement_id + client_id) | **NOT TESTED** | No report addressed multi-tenancy. Remains settled. |
| 11 | Narrative Coherence 5% | **VALIDATED + EXTENDED** | Now designated as Tier 1 universal gate with floor threshold (R07), even though its adaptive weight is low. |

**No settled decisions challenged.** Two (9, 10) were not tested. The remainder are all validated with additional specificity.

---

## 5. Jack's Directives: Validated or Challenged?

| Directive | Status | Evidence |
|-----------|--------|----------|
| 1. Rigidity Problem | **FULLY RESOLVED** | Template registry pattern with 3-phase implementation (R02). Heterogeneous lenses (R03). 5-type engagement taxonomy (R10). Dynamic config from templates, not enums. |
| 2. MECE Issue Tree | **FULLY RESOLVED** | Four-phase deliberation (construct/analyze/evaluate/synthesize) (R10). Heterogeneous consulting lenses (R03). Five MECE evaluation dimensions (R03). Shallow-then-adaptive (R03). Living document with 3-cycle cap (R03). |
| 3. Iterative Research | **FULLY RESOLVED** | Three-criterion stopping (R01). Max 3-5 rounds (R01). Scope-change detection (R01). Between-round continuity via scratchpad (R01, R06). Dual stopping criteria (sufficiency + diminishing returns) (R10). |
| 4. Engagement Scope | **VALIDATED** | 70% of MBB engagements blend categories (R05). 5-type analytical taxonomy enables routing (R10). Auto shop test case analyzable without specialized skill files (R05). |
| 5. Build Philosophy | **VALIDATED** | Model-capability-dependent harness design (R01). Graceful degradation principle (R07). Phase 1 at reduced depth with correct interfaces. |
| 6. FITFO Standard | **VALIDATED + OPERATIONALIZED** | Flexon-based problem archetypes (R05). CBR-based Observation Library feeds forward (R10). Cross-domain analogy step in Spec Engine (R05). |
| 7. Human-in-the-Loop | **IMPLEMENTATION SPECIFIED** | Database state machine for Phase 1 (R09). Approve/modify/reject flows (R09). Scope-change triggers additional gate (R01). TiCoder divergence shown at review (R10). |
| 8. Karpathy KBs | **CONFIRMED + IMPLEMENTED** | Three-layer pattern (raw/compiled/INDEX.md) (R04, R06). Observation Library as compiled wiki (R10). Content-hash provenance (R04). Discovery vs. accumulation distinction confirmed exactly (R04). |
| 9. Component #3 Concern | **RESOLVED** | Split into #3a (source discovery) + #3b (knowledge accumulation) (R04). Semantic Router and Bifrost removed (R04). Voyage-finance-2 selected (R04). Build unblocked. |
| 10. Confirmed Decisions | **ALL VALIDATED** | See Section 4 above. |
| 11. Quality Standard | **VALIDATED** | MBB quality rubrics mapped to Keystone dimensions (R07). Explicit rubric exceeds MBB practice (R07). Goldman-grade bar maintained. |

**No directives challenged by any report.** All are either validated as-is or resolved with concrete implementation specifications.

---

## 6. New Architectural Decisions (Ready to Settle)

### Decision 1: Spec Engine is a 10-step pipeline
**Recommendation:** Adopt the 10-step flow replacing the current 7-step. Add Problem Framing, Hypothesis Generation, Decomposition Validation, and Feedback Loop.
**Evidence:** Reports 03, 05, 10 (independent convergence from consulting methodology, AI planning research, production systems).
**Confidence:** High. Three independent evidence paths.
**Affects:** Component #5 scope upgrade from L to XL. CAPSTONE-PLAN-v2.md Section 3.

### Decision 2: Issue tree uses heterogeneous consulting lenses
**Recommendation:** 3-4 Sonnet agents with distinct lens assignments (financial, operational, market/competitive, optionally regulatory/risk for complex engagements).
**Evidence:** Reports 03, 10 (4-6% accuracy gain, 30% fewer factual errors over homogeneous generation).
**Confidence:** High. Peer-reviewed 2025.
**Affects:** Component #5 implementation.

### Decision 3: Shallow initial tree (2-3 levels), adaptive deepening
**Recommendation:** Start with 8-20 leaf nodes. Deeper decomposition triggered by research agent reports.
**Evidence:** ADaPT +28.3% (R03). Reduces human review burden. Cost-effective.
**Confidence:** High.
**Affects:** Component #5, human review gate scope.

### Decision 4: Three-criterion stopping with 3-5 round cap
**Recommendation:** Hard cap (3 default, 5 max) + quality gate + novelty exhaustion. Any can terminate.
**Evidence:** Convergent across Anthropic, OpenAI, Google, DBAutoDoc (R01).
**Confidence:** High.
**Affects:** Component #7 research loop, Component #5 orchestration.

### Decision 5: Subagent output contract: structured summary + artifact file
**Recommendation:** Pydantic schema ~1,500 tokens (3-7 claims, per-claim confidence, source counts) + full artifact to external file.
**Evidence:** Factory.ai 37% retention failure mode (R06). Anthropic 1,000-2,000 token target (R01, R09).
**Confidence:** High.
**Affects:** Component #7 output spec, L1->L1.5 handoff contract.

### Decision 6: Deliberation aggregation is claim-level selection
**Recommendation:** Judge-based selection (evaluate competing claims, pick best-supported), not synthesis/blending.
**Evidence:** 81% vs 51.2% win rate (R06). Near-chance performance from blending.
**Confidence:** High.
**Affects:** Component #9 aggregation logic.

### Decision 7: Component #3 splits into #3a (discovery) + #3b (accumulation)
**Recommendation:** #3a: pgvector + BM25 + Voyage-finance-2 + contextual retrieval + Cohere Rerank + Docling + Brave/Exa. #3b: compiled wiki per engagement (Karpathy pattern).
**Evidence:** Report 04 (convergent evidence from Karpathy pattern, FinanceBench, production retrieval).
**Confidence:** High.
**Affects:** Component #3 scope, build sequence. Semantic Router and Bifrost removed.

### Decision 8: Voyage-finance-2 as primary embedding model
**Recommendation:** 49% improvement over OpenAI on ConvFinQA. $0.12/MTok. Domain specialization matters.
**Evidence:** FinMTEB (EMNLP 2025), TigerData independent validation (R04).
**Confidence:** High. Third-party validated.
**Affects:** Component #3a.

### Decision 9: paper-search-mcp replaces Academix
**Recommendation:** 21+ sources vs. Academix's 5. Free-first full-text fallback.
**Evidence:** Report 08.
**Confidence:** Medium-high. Beta maturity.
**Affects:** Component #4 server list.

### Decision 10: Error recovery Layers 1-2 ship in Phase 1
**Recommendation:** Retry (tenacity) + model fallback chain. Claude API has 62 incidents in 90 days.
**Evidence:** Report 09. StatusGator monitoring data.
**Confidence:** High. Operational necessity.
**Affects:** Components #5, #7, #9.

### Decision 11: Database state machine HITL for Phase 1
**Recommendation:** PostgreSQL state machine (3 tables, REST API, web UI). Approve/modify/reject. 2-3 days implementation.
**Evidence:** Report 09 (standard pattern, maps to Temporal Signals in Phase 2).
**Confidence:** High.
**Affects:** Components #5, #9, Jack's Directive 7.

### Decision 12: Geometric mean for rubric aggregation
**Recommendation:** Replace implicit weighted sum. Prevents dimension compensation.
**Evidence:** Stanford HELM, MQM, AdaRubric (R07).
**Confidence:** High.
**Affects:** Component #6 Layer 3.

### Decision 13: Four universal gates + six adaptive dimensions
**Recommendation:** Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence as Tier 1 gates with floor thresholds. Remaining six flex by engagement type.
**Evidence:** Report 07 (synthesized from AdaRubric, OECD DAC, Bloom's, MQM, consulting practice).
**Confidence:** Medium-high.
**Affects:** Component #6.

### Decision 14: 8-10 engagement-type evaluation profiles
**Recommendation:** Expand from 2 profiles (estimative/current) to 8-10 covering the Keystone portfolio.
**Evidence:** Report 07 (Anthropic March 2026, consulting engagement diversity).
**Confidence:** Medium-high. Profiles need calibration.
**Affects:** Components #5, #6.

### Decision 15: Agent SDK removed from primary orchestration stack
**Recommendation:** Standard agents use PydanticAI calling Claude API. Agent SDK reserved for future computer-use nodes.
**Evidence:** Report 09 (Claude-only, proprietary ToS, Node.js overhead).
**Confidence:** High.
**Affects:** CAPSTONE-PLAN-v2.md Section 12.0.

### Decision 16: IBM ContextForge as gateway starting point (evaluate, don't commit)
**Recommendation:** Evaluate ContextForge in first 2 days of Component #4 build. If authorization model compatible, adapt. If not, build custom.
**Evidence:** Report 08 (circuit breakers, rate limiting, Redis federation already built).
**Confidence:** Medium. Requires compatibility assessment.
**Affects:** Component #4 scope.

---

## 7. Decisions Still Open

### 7.1 Quality Gate Threshold Values
What scores on which dimensions constitute "sufficient" for each engagement type? Requires calibration against actual Keystone deliverables (Jack's scoring, planned Week 6+). Provisional placeholder: Tier 1 minimum 6/10, rejection at < 4/10.

### 7.2 Orchestrator Model for Mid-Round Synthesis
Running Opus for every synthesis-and-decide step across 3-5 rounds may strain the $12-$100 cost target. Can Sonnet handle synthesis with Opus reserved for stopping decisions? Not addressed by any report.

### 7.3 Template Similarity Threshold Calibration
The 0.85 threshold for template matching vs. dynamic generation is uncalibrated for consulting research. Requires empirical measurement from first engagements.

### 7.4 Exemplar Library Bootstrap
The 140-163% few-shot improvement for MECE trees requires curated gold-standard examples before L0 is production-ready. This is a content investment, not engineering. Who produces it, by what quality bar?

### 7.5 Framework Retrieval Sequencing
The Spec Engine (L0) needs framework awareness during work plan generation, but the Skills Library lives in L2 (downstream). Does L0 get direct framework library access? Unresolved interface question.

### 7.6 Cross-Engagement Wiki Contamination
When the compiled wiki accumulates across engagements, circular reasoning and client data contamination are risks. Scoping rules (engagement-scoped raw/ + wiki/, separate promotion to cross-engagement) need explicit design.

### 7.7 Cost Validation: 15x Token Multiplier
The $12-$100 cost target was validated before the 15x multiplier was surfaced. The 10-step pipeline with 3 Sonnet tree agents + Opus meta-agent + parallel L1 research agents needs budget re-verification.

### 7.8 RESEARCH.md Versioning Across Rounds
When scope changes trigger spec updates, how do downstream layers know which version to validate against? Version tracking mechanism not specified.

---

## 8. Updated Component Impact Map

### Component #1: RESEARCH.md Spec Format (S -> S+)
- Add Day-1 Hypothesis field, per-branch "end product" specification
- Add engagement type (5-type taxonomy), max_rounds override, scope-change sensitivity
- Add priority_score as computed field in research-tasks.json
- Encode DAG dependency structure (not flat task list)

### Component #2: Citation Data Model (S -> S)
- No scope change. Confirmed correct.
- Content-hash provenance field should be added for wiki compilation integrity

### Component #3: Retrieval -> Split into #3a + #3b
- **#3a Source Discovery (L):** pgvector + ParadeDB + Voyage-finance-2 + contextual retrieval + Cohere Rerank + Docling + Brave/Exa. Semantic Router REMOVED. Bifrost REMOVED.
- **#3b Knowledge Accumulation (M, new):** Compiled wiki per engagement. raw/ + compiled/ + INDEX.md. Content-hash provenance. Human-designed schemas.
- Net scope: roughly unchanged total, better divided

### Component #4: MCP Gateway (M -> M)
- Evaluate IBM ContextForge first (2-day assessment)
- Replace Academix with paper-search-mcp
- Add Finnhub MCP for market data
- Add circuit breaker parameters from MCP Reliability Playbook
- Add transport_type and security_approved to tool registry schema
- Tool Search deferred loading is required, not optional

### Component #5: Specification Engine (L -> XL)
- **Major scope increase.** Now a 10-step pipeline with:
  - engagement_classifier.py (5-type taxonomy)
  - intent_clarifier.py (Decision-First CoT + TiCoder)
  - decomposer.py (heterogeneous lenses, shallow tree, MECE exemplars)
  - structural_analyzer.py (programmatic tree metrics, zero LLM cost)
  - tree_synthesizer.py (Self-MoA aggregation)
  - validator.py (MECE verification with Opus, binary criteria)
  - scout_strike.py (Day-1 hypothesis, VOI scoring, dual stopping)
  - feedback_loop.py (findings -> tree refinement -> reprioritization)
  - Observation Library CBR query at entry
  - Template registry for agent configs
- Estimated: 2-3 weeks

### Component #6: Evaluator Stack (XL -> XL)
- Geometric mean aggregation in Layer 3
- Tier 1/Tier 2 rubric split with floor thresholds
- 8-10 engagement-type profiles (expand from 2)
- Issue tree classification drives weight generation (Bloom's + quant/qual)
- Sprint contract: Evaluator proposes, Generator reviews
- Dimension-specific verification (programmatic for Quantitative Rigor, position-switching for Analytical Depth)

### Component #7: Research Agent Pipeline (L -> L+)
- Error recovery Layers 1-2 in Phase 1 (retry + fallback)
- Subagent output contract: structured summary + artifact file
- 1,000-2,000 token output budget enforced
- Partial-result continuation (3 of 5 succeed -> combine + retry failures)
- Template registry replaces enum dispatch
- Condensed summary schema: claims[], status, gaps, artifact_path

### Component #8: CitationProcessor (M -> M)
- Content-hash provenance for wiki compilation
- Consider second citation pass after L3 generation (Phase 2)
- No major scope change

### Component #9: Deliberation (L -> L+)
- Aggregation redesigned: claim-level selection, not synthesis
- Per-claim confidence scores and source counts required from subagents
- "What Would You Have to Believe?" step for low-confidence findings
- Self-MoA for issue tree generation, cross-provider for evidence assessment
- Post-selection consistency check (incoherent selected claims)

### Component #10: Evaluator Calibration (M -> M)
- 8-10 profiles to calibrate instead of 2
- MBB-to-rubric mapping as calibration anchors
- Per-dimension bias detection (especially Quantitative Rigor, Analytical Depth)

### Component #11: E2E Pipeline Test (M -> M)
- Test must cover iterative research loop (multi-round)
- Test must exercise HITL gates (approve/modify/reject)
- Must validate 37% retention doesn't occur (information fidelity check)

### New Component: HITL Infrastructure
- PostgreSQL state machine (3 tables)
- REST API
- Web UI with artifact display + agent reasoning panel
- 2-3 days estimated
- Ships alongside Components #5 and #9

---

## 9. Recommended Changes to CAPSTONE-PLAN-v2.md

### Section 3 (Specification Engine)
1. Replace 7-step flow with 10-step flow (see Section 1 above)
2. Add engagement type classifier (5-type taxonomy: SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC)
3. Add Decision-First CoT + TiCoder divergence detection for intent clarification
4. Add issue tree construction with heterogeneous consulting lenses (3-4 Sonnet agents)
5. Add MECE verification as discrete step (Opus evaluator, five dimensions, binary criteria)
6. Add Day-1 Hypothesis as required output
7. Add VOI-inspired priority scoring formula
8. Add Observation Library CBR query at Spec Engine entry
9. Change research-tasks.json to DAG structure (not flat list)
10. Add per-branch "end product" specification

### Section 4 (Research & Analysis)
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

### Section 5 (Evaluator)
23. Add geometric mean as aggregation method for 10-dimension rubric
24. Add Tier 1 (universal gates) / Tier 2 (adaptive) rubric split
25. Expand from 2 evaluation profiles to 8-10
26. Add issue tree branch classification -> weight generation mechanism
27. Specify sprint contract directionality (Evaluator proposes, Generator reviews)
28. Add dimension-specific verification strategies (Quantitative Rigor, Analytical Depth)
29. Add graceful degradation principle for evaluation scaffolding

### Section 6 (Retrieval)
30. Split Component #3 into #3a (source discovery) + #3b (knowledge accumulation)
31. Add Voyage-finance-2 as primary embedding model
32. Add contextual retrieval at ingest time
33. Add Cohere Rerank v3.5 to retrieval pipeline
34. Add chunking rules (512 tokens, 50-100 overlap, tables as HTML, XBRL bypass)
35. Remove Semantic Router
36. Remove Bifrost caching
37. Add Brave Search + Exa as external discovery APIs (avoid Tavily dependency, skip Google CSE)
38. Add compiled wiki per engagement (Karpathy three-layer pattern)

### Section 7 (Observation Library)
39. Reframe as CBR system with R4 cycle (Retrieve/Reuse/Revise/Retain)
40. Add 5-tier knowledge artifact hierarchy with dual-axis metadata (industry x capability)
41. Add three-type extraction: strategy tips, recovery tips, optimization tips
42. Add flexon-based problem archetype tagging

### Section 12 (Infrastructure)
43. Remove "Claude Agent SDK for execution substrate"
44. Add error recovery Layers 1-2 as Phase 1 requirement
45. Add database state machine HITL as Phase 1 implementation
46. Add 5 mandatory Day-1 coding standards for Temporal migration readiness
47. Replace Academix with paper-search-mcp in server list
48. Add Finnhub MCP for market data

---

## 10. Updated Build Sequence

The core build order is preserved with these modifications:

```
#1  RESEARCH.md spec format (S+, 2-3 days) ─────────────────┐
#2  Citation data model (S, 1-2 days) ───────────────────────┤
#3a Source Discovery (L, 1-2 weeks) ─────────────────────────┤  All parallel,
#3b Knowledge Accumulation (M, 3-5 days) ────────────────────┤  no dependencies
#4  MCP gateway (M, 1 week) ─────────────────────────────────┤
#HITL PostgreSQL state machine (S, 2-3 days) ────────────────┘
                                                              │
#5  Specification Engine L0 (XL, 2-3 weeks) ◄─────────────────┘
    [Now includes 10-step pipeline, template registry,
     engagement classifier, MECE verification]
                                                              │
#6  Evaluator stack L4 Layers 1-3 (XL, 2-3 weeks) ◄──────────┘
    [Now includes geometric mean, tier split, 8-10 profiles]
                                                              │
#7  Research Agent pipeline L1 (L+, 1-2 weeks) ◄─────────────┘
    [Now includes error recovery, artifact bypass, template dispatch]
                                                              │
#8  CitationProcessor (M, 3-5 days) ◄────────────────────────┘
                                                              │
#9  Deliberation L1.5 (L+, 1-2 weeks) ◄──────────────────────┘
    [Now includes selection-based aggregation, WWHTB]
                                                              │
#10 Evaluator calibration (M, 1 week) ◄──────────────────────┘
                                                              │
#11 End-to-end pipeline test (M, 3-5 days) ◄─────────────────┘
```

**Key changes:**
- HITL infrastructure added as a new parallel item (no dependencies, 2-3 days)
- Component #3 split into #3a + #3b (both still parallel, no dependency change)
- Component #5 upgraded from L to XL (was 1-2 weeks, now 2-3 weeks)
- #3b can start before or after #3a (independent)
- Error recovery baked into #7 (no separate component)

**Should any component move earlier?**
- #3b (Knowledge Accumulation) can be deferred until after #5 ships, since it primarily serves cross-engagement knowledge (not needed for first engagement). Build #3a first.
- HITL infrastructure should be built alongside #1-#4 since Components #5 and #9 depend on it.

---

## 11. Risk Register Update

### New Risks Identified

| Risk | Severity | Source | Mitigation |
|------|----------|--------|------------|
| 15x token multiplier may exceed $12-$100 cost target | HIGH | R01, R02, R09, R10 | Model explicitly with 10-step pipeline + 3-5 agents x 3-5 rounds. Claude Max absorbs most cost. |
| Exemplar library not available for L0 production readiness | MEDIUM | R03 | Content investment needed. Jack + team curate 5-10 gold-standard issue trees before L0 ships. |
| Tavily acquired by Nebius (Feb 2026), pricing uncertain | MEDIUM | R04, R08 | Do not make Tavily architecturally required. Exa + Firecrawl covers same function. |
| Google Custom Search sunsetting Jan 2027 | LOW | R04 | Already mitigated: Brave is primary. Don't build on CSE. |
| paper-search-mcp is Beta maturity | MEDIUM | R08 | Load test before relying as sole academic server. Fallback: Academix. |
| Branch prioritization F1 = 0.68-0.79 (~1 in 4-5 wrong) | MEDIUM | R03 | Design for reprioritization each cycle. Human gate catches major errors. |
| Claude API: 62 incidents in 90 days | HIGH | R09 | Error recovery Layers 1-2 in Phase 1. Retry + fallback chain. |
| LLM judges unreliable on Quantitative Rigor (low) and Analytical Depth (very low) | MEDIUM | R07 | Programmatic complement for QR. Position-switching for AD. |

### Changes to Existing Risk Severity

| Risk | Previous | New | Reason |
|------|----------|-----|--------|
| PydanticAI experimental/unstable | MEDIUM | **ELIMINATED** | v1.0 shipped Sep 2025, production-stable |
| Component #3 over-engineering | HIGH | **RESOLVED** | Split into #3a + #3b, clear scope |
| Iterative research unspecified | CRITICAL | **RESOLVED** | Full mechanical specification from R01, R06, R10 |
| HITL gates unimplemented (Temporal deferred) | HIGH | **RESOLVED** | Database state machine for Phase 1 |
| Agent configuration too rigid | HIGH | **RESOLVED** | Template registry pattern with 3-phase roadmap |

---

## 12. Stale/Outdated Findings Flagged

### Agent Architectures (fast-moving area)
- **G-Eval (EMNLP 2023)** cited in R03 for tree evaluation. The pattern (LLM-as-judge with structured prompts) is still valid, but the specific implementation has been superseded by DeepEval and Prometheus 2 in 2024-2025. **Insight valid, implementation stale.**
- **LLMCompiler (2023)** cited in R03 for DAG execution. The DAG pattern is valid; the specific LangChain integration should use PydanticAI Graph API instead. **Pattern valid, implementation stale.**
- **DyLAN (ICLR 2024)** cited in R02 for dynamic agent accuracy. The +25% finding on MMLU is directionally valid but the stronger Anthropic 90.2% finding supersedes it as evidence. **Redundant, not stale.**
- **Karpathy's P(IK) paper (2022)** cited in R03 for LLM overconfidence. The overconfidence finding has only been strengthened by subsequent work (2023-2025). **Finding timeless.**

### Consulting Methodology (timeless)
All consulting methodology citations (McKinsey Staff Paper 66, Pyramid Principle, ICD 203, Bulletproof Problem Solving) are foundational and not subject to temporal decay. No concerns.

### Embedding Models / Retrieval (moderate-speed area)
- **Voyage-finance-2** is current as of April 2026. No V4 financial variant exists yet. Monitor.
- **Cohere Embed v4** and **Gemini Embedding 2** are flagged for Phase 2 investigation. Both are too immature for Phase 1 production.

### MCP Ecosystem (fast-moving area)
- Karpathy wiki implementations (CRATE, llm-wiki-compiler) are all 72 hours old as of reports. **Build custom minimal implementation.** Revisit ecosystem in 60 days.
- Tool Search API is beta and Claude-exclusive. Acceptance criterion depends on it. **Monitor production timeline.**

---

*This synthesis represents the combined findings of 10 deep research reports, each analyzed by an independent Opus subagent with full project context. The orchestrator (this document) is the only entity that saw all 10 analyses together. Every recommendation traces to specific report analyses with documented evidence quality. The 16 new architectural decisions are ready for Jack's review.*
