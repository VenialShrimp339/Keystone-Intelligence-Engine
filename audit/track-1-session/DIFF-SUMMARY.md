# Track 1 Architecture Finalization: Diff Summary
*Audit date: 2026-04-05 | Documents all changes applied during Track 1 session*

---

## CAPSTONE-PLAN-v2.md Changes

### Section 3: Specification Engine

**§3.2 RESEARCH.md Template**
- Added Day-1 Hypothesis block (three fields: primary hypothesis, alternative hypothesis, prior confidence, evidence thresholds). Previously absent.

**§3.4 The 10-Step Specification Pipeline (new section, replaces prior 4-step verification phase)**
- Replaced prior 4-step flow (intent clarification, decomposition, verification, dispatch) with a fully specified 10-step pipeline:
  - Step 1: Problem Framing and Classification — 5-type engagement taxonomy, Observation Library CBR query hook (wired Phase 1, returns empty until Phase 2 library is populated)
  - Step 2: Intent Clarification and Hypothesis Formation — Decision-First CoT (5-step), Day-1 Hypothesis formation. TiCoder divergence detection tagged Phase 2
  - Step 3: Issue Tree Decomposition — 3-4 heterogeneous Sonnet agents (financial/operational/market lenses), shallow start (8-20 leaf nodes), Self-MoA aggregation by Opus meta-agent
  - Step 4: Decomposition Validation — discrete MECE verification with Opus, five dimensions, binary criteria, programmatic semantic similarity complement
  - Step 5: Priority Assignment — Phase 1: simplified heuristic `(decision_relevance x uncertainty)`; Phase 2: full VOI formula `(decision_relevance x current_uncertainty) / estimated_cost`
  - Step 6: Dynamic Agent Configuration — template registry query, 0.85 similarity threshold, custom AgentDefinition generation below threshold, tighten-only invariant
  - Step 7: Task Generation — DAG structure in research-tasks.json (new `depends_on` field), per-branch `end_product` specification
  - Step 8: Human Review Gate — non-negotiable, Phase 1 implementation via PostgreSQL state machine (3 tables, REST API, web UI)
  - Step 9: Research Execution (Scout Phase) — Day-1 Hypothesis anchors, 70/30 exploration-to-exploitation start
  - Step 10: Feedback Loop — completed tasks immutable, pending tasks modifiable, 3 replanning cycles max

**§3.6 Research-tasks.json (updated)**
- Added `"depends_on"` field to task schema for DAG dependency structure
- Added `"end_product"` field specifying exact deliverable format per task (chart type, table structure, conclusion format)
- Added `"priority_score"` as a computed field
- Design decisions #8 and #9 tagged `[BATCH 2 UPDATE]` explain both additions

**§3.8 Engagement Classification and Pipeline Profile Selection (new section)**
- Full 5-type analytical taxonomy (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) with definitions, signals, and examples
- Five classification signals enumerated
- Pipeline profile table: Light / Standard / Deep with agent counts, rounds, eval stack coverage
- Note on orthogonal domain taxonomy (10-category MBB framework) for Observation Library and framework selection

**§3.9 Intent Clarification: Decision-First Chain-of-Thought (new section)**
- Phase 1: 5-step Decision-First CoT (decision identification, evidence threshold, unstated constraints, surprise detection, scope boundary)
- Phase 2: TiCoder divergence detection — 2-3 competing research plans, divergence surface shown at Human Review Gate

---

### Section 4: Research & Analysis

**§4.1 Parallel Research Execution (updated)**
- Added point 5 "[BATCH 2 UPDATE]": artifact bypass pattern — 1,000-2,000 token Pydantic-schemaed condensed summary + full artifact written to `{engagement_id}/memory/raw/{agent_id}/`. Guards against 37% Factory.ai information retention failure mode.

**§4.2 Agent Specialization (updated)**
- "[BATCH 2 UPDATE] Template registry, not fixed types" — five agent types reframed as seed templates in registry, not enum dispatch. Template query at dispatch, custom AgentDefinition generation below threshold.
- "[BATCH 2 UPDATE] Tighten-only constraint invariant" — dynamic configurations can only restrict, never expand beyond parent template permissions. Tool assignment as primary behavioral governance (not system prompt).
- "[BATCH 2 UPDATE] Token budget as explicit agent configuration field" — token budget part of AgentDefinition schema, set at Spec Engine dispatch.

**§4.3 The Deliberation Phase (updated)**
- "[BATCH 2 UPDATE]" Phase 2 header: claim-level selection (not synthesis/blending). 81% vs. 51.2% win rate evidence. Aggregator runs claim-level selection: convergent findings, genuine disagreements, methodological blind spots, curmudgeon challenge.
- Confidence map `wyhtb_analysis` field added under `insufficient_evidence` tier: "What Would You Have to Believe?" analysis.

**§4.4 Content Structuring via Sprint Contracts (updated)**
- "[BATCH 2 UPDATE] 'What Would You Have to Believe?' (WWHTB) step" — for weak-confidence and contested findings, forces transparent reasoning about required assumptions. Appears in confidence map alongside each contested or weak-confidence finding.

**§4.5 The Iterative Research Loop (new section)**
- "[BATCH 2 UPDATE]" — fully specified loop addressing Directive 3 ("single biggest architectural gap"):
  - Three-criterion stopping: hard iteration cap (3 default, 5 max), quality gate (L4 Evaluator mid-pipeline), semantic novelty exhaustion
  - Decision table: 5 signals x decision (spawn broader, go deeper, stop, stop with log, hierarchical replan)
  - Between-round continuity: `research-state.md` scratchpad, Opus compaction safe within round, file persist between rounds, `compiled/` update, `INDEX.md` update, JIT context for next round

**§4.6 Scope-Change Detection Protocol (new section)**
- "[BATCH 2 UPDATE]" — Haiku-tier detector, In-Plan vs. Out-of-Plan classification, cost ~$0.001 per check. Out-of-Plan triggers human gate per Directive 7. False negative safety net: human gate after Deliberation.

**§4.7 ADaPT-Style Reactive Decomposition (new section)**
- "[BATCH 2 UPDATE] [Phase 2]" — ADaPT +28.3% over static planning. Phase 1 uses static 2-3 level depth. Phase 2 activation extends feedback loop with branch-level depth triggers based on agent-reported complexity signals. No data flow changes required.

---

### Section 5: Evaluator

**§5.3 The Ten-Dimension Judgment Rubric (updated)**
- "[BATCH 2 UPDATE] Two-tier rubric structure" — Tier 1 Universal Gates (Intent Alignment >= 5/10, Intellectual Honesty >= 5/10, Completeness >= 4/10, Narrative Coherence >= 5/10) with explicit floor thresholds. Failure on any Tier 1 = rejection before geometric mean.
- "[BATCH 2 UPDATE] Aggregation method: geometric mean, not weighted sum" — `composite_score = product(score_i ^ weight_i)`. Prevents dimension compensation. Cites Stanford HELM, MQM, AdaRubric.

**§5.9 Five-Layer Evaluation Stack (updated)**
- Layer 3 "[BATCH 2 UPDATE]": "Tier 1 gate dimensions are checked before Tier 2 scoring begins." Phase 2 extension for dimension-specific verification strategies tagged.

**§5.12 Evaluation Profiles (new section)**
- "[BATCH 2 UPDATE]" — Phase 1: 3 seed profiles (General Consulting, M&A/Due Diligence, Market Sizing/Estimative) with weight tables. Phase 2: expand to 8-10 profiles, minimum 5 Jack-scored deliverables per profile before activation.
- Issue tree classification -> weight generation (Bloom's Taxonomy + quant/qual) tagged Phase 2.

**§5.13 Sprint Contract Protocol (updated)**
- "[BATCH 2 UPDATE]" — Sprint contract directionality specified: Evaluator proposes, Generator reviews, both commit. Phase 2 deferral with Phase 1 fallback: Evaluator proposes unilaterally. Data structure typed for Phase 2 bidirectional use without rework. Graceful degradation note.

**§5.14 Dimension-Specific Verification Strategies (new section)**
- "[BATCH 2 UPDATE] [Phase 2]" — Quantitative Rigor: programmatic calculation audit (extract arithmetic chains, verify vs. source, flag >+-5% discrepancies). Analytical Depth: position-switching protocol (same output presented twice, conclusion buried in second presentation; consistency = genuine depth). Phase 1 behavior: both scored by Prometheus 2 without complement.

**§5.15 Graceful Degradation Principle (new section)**
- "[BATCH 2 UPDATE]" — All non-gate evaluation mechanisms are optional modules with bypass behavior. Phase 1 and Phase 2 share identical data flow. Phase 2 additions flip configuration flags, not pipeline rewrites.

---

### Section 6: Retrieval / Internal Document Integration

**§6.2 Unified Retrieval Architecture (updated)**
- "[BATCH 2 UPDATE]" header paragraph — retrieval layer split into #3a (Source Discovery) and #3b (Knowledge Accumulation). King's College London citation added.

**§6.2 Component #3a Source Discovery (updated)**
- "[BATCH 2 UPDATE] Embedding model: Voyage-finance-2" — FinMTEB 49% improvement evidence, TigerData independent validation
- "[BATCH 2 UPDATE] Reranking: Cohere Rerank v3.5" — top 150 -> rerank -> top 20 pipeline
- "[BATCH 2 UPDATE] Query Classification (inline, no external router)" — Semantic Router removed; Haiku inline classification (<200ms)
- "[BATCH 2 UPDATE] Search API Stack" — Exa (primary semantic/category), Brave Search (primary news, post-Bing shutdown), Firecrawl (JS-rendered content). Tavily removed (Nebius acquisition). Google CSE removed (sunsetting Jan 2027).
- "[BATCH 2 UPDATE]" in Document Processing paragraph — contextual retrieval at ingest: Haiku preamble per chunk, 67% retrieval failure reduction
- "[BATCH 2 UPDATE] Chunking rules" — 512 tokens, 50-100 overlap, tables as HTML, XBRL bypass to structured data objects
- "[BATCH 2 UPDATE] Caching: in-process session cache" — Bifrost removed; Python `lru_cache`, per-source TTLs, Redis-compatible interface
- Source list updated: Semantic Scholar + OpenAlex now via "paper-search-mcp" (Academix replaced)

**§6.2 Component #3b Knowledge Accumulation (new section)**
- "[BATCH 2 UPDATE]" — Karpathy three-layer pattern per engagement: `raw/` (full subagent artifacts, immutable), `compiled/` (orchestrator-synthesized round summaries, claim sets), `INDEX.md` (auto-maintained by orchestrator)
- Content-hash provenance: `sha256(claim_text + source_url + access_timestamp)` per compiled claim
- Human-designed schemas (ETH Zurich: +4% vs. LLM-generated -2%)
- Cross-engagement knowledge base and wiki promotion rules tagged Phase 2

---

### Section 7: Self-Improvement Loop

**§7.1 Observation Library (updated)**
- "[BATCH 2 UPDATE]" paragraph added: "An active retrieval system (CBR), not a passive log" — Specification Engine queries at engagement start; retrieved cases seed hypothesis generation and agent configuration
- "[BATCH 2 UPDATE] The Observation Library as a Case-Based Reasoning System" — R4 cycle (Retrieve/Reuse/Revise/Retain) with Aamodt & Plaza citation. Phase 1 wires hook, Phase 2 populates library.
- "[BATCH 2 UPDATE] Knowledge Artifact Hierarchy" — 5-tier table (Tier 1: raw output through Tier 5: published methodology) with dual-axis metadata (industry vertical + functional capability). Phase 2 tagged.
- "[Phase 2: Flexon-based problem archetype tagging]" — McKinsey flexon framework (systems/networks, machine/optimization, living system/evolutionary, social/political) for cross-domain retrieval enabling FITFO Standard.

**§7.7 The Instinct -> Skill Evolution Pipeline (updated)**
- "[BATCH 2 UPDATE] Three-Type Extraction Taxonomy (CBR Retain Step)" — strategy tips (`{problem_type} -> {approach} -> {outcome}`), recovery tips (`{failure_signal} -> {root_cause} -> {correction}`), optimization tips (`{task_type} -> {optimization} -> {quality_impact}`). Phase 2 tagged.

---

### Section 12: Implementation Roadmap

**§12.0 Orchestration Architecture (updated)**
- "[BATCH 2 UPDATE] Agent SDK: NOT in the primary stack" — PydanticAI calling Claude API directly is the primary path. Agent SDK reserved for future computer-use nodes. Replaces prior "Claude Agent SDK for execution substrate" framing.
- "[BATCH 2 UPDATE] Custom async orchestration (Phase 1) / Temporal (Phase 2)" — Phase 1 uses asyncio.gather() + PostgreSQL state machine. Temporal deferred with five Day-1 standards ensuring zero-rework migration.
- "[BATCH 2 UPDATE] Error Recovery: Four-Layer Defense, Layers 1-2 in Phase 1" — Layer 1 (tenacity retry: 1s base, 60s cap, full jitter, 5 max attempts, retry 429/500/529/timeout). Layer 2 (model fallback chain: Opus -> Sonnet -> Haiku -> cached/template). Layer 3 (error classification). Layer 4 (PostgreSQL checkpointing). Partial-result continuation: 3 of 5 succeed -> combine + retry failures.
- "[BATCH 2 UPDATE] Human-in-the-Loop Gates: Phase 1 Implementation" — PostgreSQL state machine (3 tables: review_gates, review_items, review_decisions), FastAPI REST, web UI with approve/modify/reject. Maps to Temporal Signals Phase 2 with no agent code changes.
- "[BATCH 2 UPDATE] Day-1 Coding Standards for Temporal Migration Readiness" — 5 standards: (1) pure function layers, (2) Pydantic inter-layer models, (3) separate controller from workflow logic, (4) correlation IDs on all operations, (5) idempotent operations.

**§12.1 Phase 1 Build Order (updated)**
- Added separate Component #3b (Knowledge Accumulation, M) to parallel block
- Added HITL component (PostgreSQL state machine, S) to parallel block
- MCP Gateway configuration updated: paper-search-mcp (replacing Academix), Finnhub MCP added
- Component #5 updated to "10-step pipeline with engagement classifier, issue tree decomposition (heterogeneous lenses), MECE verification, template registry, iterative research loop, HITL gate integration"
- Component #6 updated to "geometric mean aggregation, Tier 1/Tier 2 split, 3-4 evaluation profiles"
- Component #7 updated to "error recovery (retry + fallback chain), artifact bypass pattern (structured summary + full file), template dispatch, 1,000-2,000 token condensed output"
- Component #9 updated to "claim-level selection aggregation (not synthesis), WWHTB step, HITL gate after confidence map"

---

## CURRENT-STATE.md Changes

*Requires separate verification against CURRENT-STATE.md. Not audited here — change-audit.md covers CAPSTONE-PLAN-v2.md changes per task scope.*

---

## CLAUDE.md Changes

*CLAUDE.md was not listed as a target file for Track 1 Architecture Finalization changes. No changes expected or verified against it in this audit.*

---

## Summary of Change Density by Section

| Section | Changes Applied | Scope Change |
|---|---|---|
| §3 Specification Engine | 10 changes | Major expansion: 4-step -> 10-step pipeline; new §§3.8, 3.9 |
| §4 Research & Analysis | 12 changes | Major expansion: iterative loop (§4.5), scope-change detection (§4.6), ADaPT (§4.7) all new |
| §5 Evaluator | 7 changes | Significant upgrade: Tier 1/2 split, geometric mean, 3 seed profiles, 3 new sections |
| §6 Retrieval | 9 changes | Major restructure: #3 split into #3a + #3b; Semantic Router and Bifrost removed; 6 new components in #3a |
| §7 Observation Library | 4 changes | Extension: CBR framing, 5-tier hierarchy, 3-type extraction, flexon tagging (all Phase 2 stubs) |
| §12 Infrastructure | 6 changes | Agent SDK removal; error recovery spec; HITL implementation; Day-1 coding standards; MCP server updates |
| **Total** | **48 changes** | |
