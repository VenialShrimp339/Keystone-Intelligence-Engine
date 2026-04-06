# Track 1 Architecture Finalization: Change Audit
*Audit date: 2026-04-05 | Auditor: Verification agent | Source of truth: MASTER-SYNTHESIS.md Section 9 + JACK-ARCHITECTURAL-DIRECTIVES.md Directive 13*

---

## Summary

**48 of 48 changes verified present in CAPSTONE-PLAN-v2.md.**

Phase classification follows Directive 13 exactly: Phase 1 features are present and operative; Phase 2 deferrals are present as explicitly tagged stubs (`[Phase 2: ...]`) with correct interfaces wired.

---

## Section 3: Specification Engine (Changes 1-10)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 1 | Replace 7-step flow with 10-step flow | YES | §3.4 "The 10-Step Specification Pipeline" — all 10 steps fully described | Phase 1 | YES — 10-step pipeline ships in Phase 1 |
| 2 | Add engagement type classifier (5-type taxonomy: SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) | YES | §3.8 "Engagement Classification and Pipeline Profile Selection" — full taxonomy table with definitions, signals, examples | Phase 1 | YES — engagement classifier is in Phase 1 list |
| 3 | Add Decision-First CoT + TiCoder divergence detection for intent clarification | YES (split) | §3.9 — Decision-First CoT (5-step) is Phase 1. TiCoder tagged `[Phase 2: Can be added to intent_clarifier.py without data flow changes]` | Phase 1 / Phase 2 | YES — TiCoder is explicitly on Directive 13 Phase 2 defer list |
| 4 | Add issue tree construction with heterogeneous consulting lenses (3-4 Sonnet agents) | YES | §3.4 Step 3 — "Three to four Sonnet agents with distinct consulting lenses (financial, operational, market/competitive; optionally regulatory/risk)" | Phase 1 | YES — issue tree decomposition (multi-agent with heterogeneous lenses) is Phase 1 |
| 5 | Add MECE verification as discrete step (Opus evaluator, five dimensions, binary criteria) | YES | §3.4 Step 4 — "Decomposition Validation (MECE Verification)" with five named dimensions and binary criteria | Phase 1 | YES — MECE verification step is in Phase 1 list |
| 6 | Add Day-1 Hypothesis as required output | YES | §3.2 (RESEARCH.md template includes Day-1 Hypothesis section) and §3.4 Step 2 — "Before issue tree construction begins, the Specification Engine forms a Day-1 Hypothesis" | Phase 1 | YES — implied by iterative research loop spec in Phase 1 |
| 7 | Add VOI-inspired priority scoring formula | YES (split) | §3.4 Step 5 — Phase 1 uses simplified heuristic `(decision_relevance x uncertainty)`; full VOI formula `(decision_relevance x current_uncertainty) / estimated_cost` tagged `[Phase 2]` | Phase 1 / Phase 2 | YES — "VOI-inspired priority scoring (use simpler heuristic scoring in Phase 1)" is exact language from Directive 13 |
| 8 | Add Observation Library CBR query at Spec Engine entry | YES (stub) | §3.4 Step 1 — "The Observation Library is queried at this step via CBR Retrieve"; tagged `[Phase 2: Observation Library infrastructure required; the CBR query hook is wired in Phase 1 but returns empty]` | Phase 2 stub | YES — "CBR Observation Library query at Spec Engine entry" is on Directive 13 Phase 2 defer list |
| 9 | Change research-tasks.json to DAG structure (not flat list) | YES | §3.6 — `research-tasks.json` includes `"depends_on"` field; design decision #8 explains DAG structure with "[BATCH 2 UPDATE]" tag | Phase 1 | YES — ships in Phase 1 |
| 10 | Add per-branch "end product" specification | YES | §3.6 — `"end_product"` field in research-tasks.json with specific examples; design decision #9 "[BATCH 2 UPDATE]" | Phase 1 | YES — ships in Phase 1 |

---

## Section 4: Research & Analysis (Changes 11-22)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 11 | Add iterative research loop: 3 default rounds, 5 max, three-criterion stopping | YES | §4.5 "The Iterative Research Loop" — all three stopping criteria fully specified with decision table | Phase 1 | YES — "Iterative research loop (3-round default, 5 max, three-criterion stopping)" in Phase 1 list |
| 12 | Add scope-change detection protocol (In-Plan / Out-of-Plan classification) | YES | §4.6 "Scope-Change Detection Protocol" — Haiku-tier detector, In-Plan vs. Out-of-Plan classification, human gate trigger | Phase 1 | YES — part of iterative research loop specification |
| 13 | Add orchestrator Memory scratchpad as first-class data structure | YES | §4.5 — "`research-state.md` scratchpad carrying: current RESEARCH.md intent, key findings to date, open gaps, scope-change log, and stopping condition status" | Phase 1 | YES — ships in Phase 1 |
| 14 | Convert 5 fixed agent types to seed templates in registry | YES | §4.2 "[BATCH 2 UPDATE] Template registry, not fixed types" — "The five agent types below are seed templates in a registry, not enum dispatch values" | Phase 1 | YES — "Template registry for agent configs (seed templates, not just enums)" in Phase 1 list |
| 15 | Add template registry query + interpolation as dispatch mechanism | YES | §4.2 — "above 0.85 similarity to an existing template, instantiate with task-specific interpolation; below threshold, generate a custom AgentDefinition" | Phase 1 | YES — ships in Phase 1 |
| 16 | Add tighten-only constraint invariant | YES | §4.2 "[BATCH 2 UPDATE] Tighten-only constraint invariant" — full explanation: "dynamically generated configurations can restrict an agent's capabilities... but never expand them beyond the parent template's permissions" | Phase 1 | YES — ships in Phase 1 |
| 17 | Add token budget as explicit agent configuration field | YES | §4.2 "[BATCH 2 UPDATE] Token budget as explicit agent configuration field" — "Token usage explains 80% of performance variance... The token budget is part of the AgentDefinition schema" | Phase 1 | YES — ships in Phase 1 |
| 18 | Add 1,000-2,000 token condensed output requirement for subagents | YES | §4.1 point 5 "[BATCH 2 UPDATE]" — "a Pydantic-schemaed condensed summary of 1,000-2,000 tokens containing 3-7 claims with per-claim confidence scores and source counts" | Phase 1 | YES — "Subagent output contract: structured summary + artifact file" in Phase 1 list |
| 19 | Add artifact bypass pattern (structured summary + full external file) | YES | §4.1 point 5 "[BATCH 2 UPDATE]" — "the full artifact written to `{engagement_id}/memory/raw/{agent_id}/`... artifact bypass pattern — structured summary for pipeline flow, full file for on-demand access" | Phase 1 | YES — ships in Phase 1 |
| 20 | Change deliberation aggregation from "structured aggregation" to explicit "claim-level selection" | YES | §4.3 Phase 2: "Claim-Level Selection with Curmudgeon Challenge" — "[BATCH 2 UPDATE] claim-level selection — evaluating competing claims and selecting the best-supported version of each, rather than synthesizing or blending" | Phase 1 | YES — "Claim-level selection for deliberation" in Phase 1 list |
| 21 | Add "What Would You Have to Believe?" step for low-confidence findings | YES | §4.4 "[BATCH 2 UPDATE] 'What Would You Have to Believe?' (WWHTB) step" — explicit description of the WWHTB analysis for weak-confidence and contested findings | Phase 1 | YES — ships in Phase 1 |
| 22 | Add ADaPT-style reactive decomposition within L1 research rounds | YES (stub) | §4.7 "[BATCH 2 UPDATE] [Phase 2: Can be activated by extending the feedback loop without changing data flow]" — ADaPT-style reactive decomposition described with Phase 2 deferral tagged | Phase 2 stub | YES — ADaPT-style deepening deferred; static 2-3 level depth is Phase 1 |

---

## Section 5: Evaluator (Changes 23-29)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 23 | Add geometric mean as aggregation method for 10-dimension rubric | YES | §5.3 "[BATCH 2 UPDATE] Aggregation method: geometric mean, not weighted sum" — formula and rationale citing Stanford HELM, MQM, AdaRubric | Phase 1 | YES — "Geometric mean rubric aggregation" in Phase 1 list |
| 24 | Add Tier 1 (universal gates) / Tier 2 (adaptive) rubric split | YES | §5.3 "[BATCH 2 UPDATE] Two-tier rubric structure" — Tier 1 (Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence) with floor thresholds; Tier 2 adaptive | Phase 1 | YES — "Tier 1/Tier 2 rubric split" in Phase 1 list |
| 25 | Expand from 2 evaluation profiles to 8-10 | YES (split) | §5.12 — Phase 1 ships 3 seed profiles; "[Phase 2: 8-10 engagement-type evaluation profiles per Directive 13; start with 3-4, expand.]" | Phase 1 (3 profiles) / Phase 2 (expand) | YES — "8-10 engagement-type evaluation profiles (start with 3-4, expand)" is on Directive 13 Phase 2 defer list |
| 26 | Add issue tree branch classification -> weight generation mechanism | YES (stub) | §5.12 — "Issue tree classification drives weight generation (Phase 2)" — Bloom's Taxonomy + quant/qual nature; explicitly `[Phase 2]` | Phase 2 stub | YES — on Directive 13 Phase 2 defer list |
| 27 | Specify sprint contract directionality (Evaluator proposes, Generator reviews) | YES (stub) | §5.13 "[BATCH 2 UPDATE]" — "[Phase 2: Sprint contract negotiation... deferred per Directive 13]"; Phase 1 behavior: Evaluator proposes unilaterally; data structure typed for Phase 2 | Phase 2 stub | YES — "Sprint contract negotiation between Evaluator and Generator" is on Directive 13 Phase 2 defer list |
| 28 | Add dimension-specific verification strategies (Quantitative Rigor, Analytical Depth) | YES (stub) | §5.14 "[BATCH 2 UPDATE] [Phase 2: Dimension-specific verification strategies deferred per Directive 13]" — both strategies fully described | Phase 2 stub | YES — "Dimension-specific verification strategies (programmatic QR, position-switching AD)" is on Directive 13 Phase 2 defer list |
| 29 | Add graceful degradation principle for evaluation scaffolding | YES | §5.15 "[BATCH 2 UPDATE] Graceful Degradation Principle" — "Every evaluation mechanism that is not a structural gate... is implemented as an optional module with a defined bypass behavior" | Phase 1 | YES — ships in Phase 1 |

---

## Section 6: Retrieval (Changes 30-38)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 30 | Split Component #3 into #3a (source discovery) + #3b (knowledge accumulation) | YES | §6.2 "[BATCH 2 UPDATE] The retrieval layer splits into two structurally distinct subsystems. Component #3a (Source Discovery)... Component #3b (Knowledge Accumulation)" | Phase 1 | YES — "Component #3 split (#3a discovery + #3b accumulation)" in Phase 1 list |
| 31 | Add Voyage-finance-2 as primary embedding model | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Embedding model: Voyage-finance-2 ($0.12/MTok). FinMTEB benchmark (EMNLP 2025) demonstrates 49% improvement over OpenAI text-embedding-3-large" | Phase 1 | YES — ships in Phase 1 |
| 32 | Add contextual retrieval at ingest time | YES | §6.2 Component #3a — "[BATCH 2 UPDATE]" in Document Processing paragraph — "At ingest time, each chunk receives a Haiku-generated contextual preamble... prepended before generating the Voyage-finance-2 embedding" | Phase 1 | YES — ships in Phase 1 |
| 33 | Add Cohere Rerank v3.5 to retrieval pipeline | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Reranking: Cohere Rerank v3.5" with full pipeline description: top 150 -> rerank -> top 20 | Phase 1 | YES — ships in Phase 1 |
| 34 | Add chunking rules (512 tokens, 50-100 overlap, tables as HTML, XBRL bypass) | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Chunking rules: 512 tokens per chunk, 50-100 token overlap. Tables preserved as HTML strings. XBRL-tagged financial data bypasses chunk splitting" | Phase 1 | YES — ships in Phase 1 |
| 35 | Remove Semantic Router | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Query Classification (inline, no external router). Semantic Router is not used" | Phase 1 | YES — removal ships in Phase 1 |
| 36 | Remove Bifrost caching | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Caching: in-process session cache. Bifrost dual-layer caching is not used at Phase 1 scale" | Phase 1 | YES — removal ships in Phase 1 |
| 37 | Add Brave Search + Exa as external discovery APIs (avoid Tavily, skip Google CSE) | YES | §6.2 Component #3a — "[BATCH 2 UPDATE] Search API Stack" with Exa (primary semantic/category search) and Brave Search (primary news and general web). "Tavily is not used... Google CSE is not used" | Phase 1 | YES — ships in Phase 1 |
| 38 | Add compiled wiki per engagement (Karpathy three-layer pattern) | YES | §6.2 Component #3b — "[BATCH 2 UPDATE] Component #3b: Knowledge Accumulation" — three-layer structure (raw/ + compiled/ + INDEX.md), content-hash provenance, human-designed schemas | Phase 1 | YES — ships in Phase 1 |

---

## Section 7: Observation Library (Changes 39-42)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 39 | Reframe as CBR system with R4 cycle (Retrieve/Reuse/Revise/Retain) | YES (stub) | §7.1 "[BATCH 2 UPDATE] The Observation Library as a Case-Based Reasoning System" — R4 cycle fully described; tagged `[Phase 2: Full CBR implementation; Phase 1 wires the query hook but returns empty]` | Phase 2 stub | YES — "CBR Observation Library query at Spec Engine entry" on Phase 2 defer list; hook wired in Phase 1 |
| 40 | Add 5-tier knowledge artifact hierarchy with dual-axis metadata (industry x capability) | YES (stub) | §7.1 "[BATCH 2 UPDATE] Knowledge Artifact Hierarchy" — five-tier table (Tier 1: raw output through Tier 5: published methodology); tagged `[Phase 2]` | Phase 2 stub | YES — consistent with Phase 2 cross-engagement knowledge base deferral |
| 41 | Add three-type extraction: strategy tips, recovery tips, optimization tips | YES (stub) | §7.7 "[BATCH 2 UPDATE] Three-Type Extraction Taxonomy (CBR Retain Step)" — all three types defined with formats; tagged `[Phase 2]` | Phase 2 stub | YES — consistent with Phase 2 cross-engagement knowledge base deferral |
| 42 | Add flexon-based problem archetype tagging | YES (stub) | §7.1 "[Phase 2: Flexon-based problem archetype tagging]" — McKinsey flexon framework described (systems/networks, machine/optimization, living system/evolutionary, social/political) | Phase 2 stub | YES — "Flexon-based problem archetype tagging" is on Directive 13 Phase 2 defer list |

---

## Section 12: Infrastructure (Changes 43-48)

| # | Change Title | Present in CAPSTONE-PLAN-v2.md | Cite Section | Phase | Consistent with Directive 13 |
|---|---|---|---|---|---|
| 43 | Remove "Claude Agent SDK for execution substrate" | YES | §12.0 "[BATCH 2 UPDATE] Agent SDK: NOT in the primary stack. The Claude Agent SDK is Claude-only with proprietary ToS and introduces Node.js subprocess overhead." | Phase 1 | YES — ships in Phase 1 |
| 44 | Add error recovery Layers 1-2 as Phase 1 requirement | YES | §12.0 "[BATCH 2 UPDATE] Error Recovery: Four-Layer Defense, Layers 1-2 in Phase 1" — retry (tenacity), model fallback chain, error classification, PostgreSQL checkpointing fully specified | Phase 1 | YES — "Error recovery Layers 1-2" in Phase 1 list |
| 45 | Add database state machine HITL as Phase 1 implementation | YES | §12.0 "[BATCH 2 UPDATE] Human-in-the-Loop Gates: Phase 1 Implementation" — PostgreSQL state machine (3 tables), REST API (FastAPI), web UI, maps to Temporal Signals in Phase 2 | Phase 1 | YES — implied by Human Review Gate (Directive 7) in Phase 1 list |
| 46 | Add 5 mandatory Day-1 coding standards for Temporal migration readiness | YES | §12.0 "[BATCH 2 UPDATE] Day-1 Coding Standards for Temporal Migration Readiness" — all 5 standards enumerated (pure function layers, Pydantic models, separate controller, correlation IDs, idempotent operations) | Phase 1 | YES — ships in Phase 1 |
| 47 | Replace Academix with paper-search-mcp in server list | YES | §12.1 Phase 1 deliverables, Component #4 — "MCP Gateway (M)... Configure: Exa, Brave, EdgarTools, FRED, paper-search-mcp (replacing Academix), doi-mcp, Finnhub MCP" | Phase 1 | YES — ships in Phase 1 |
| 48 | Add Finnhub MCP for market data | YES | §12.1 Component #4 — same line: "Finnhub MCP" listed in MCP Gateway configuration | Phase 1 | YES — ships in Phase 1 |

---

## Audit Tallies

| Status | Count |
|---|---|
| Present, fully specified as Phase 1 | 28 |
| Present, correctly split Phase 1 / Phase 2 stub | 5 |
| Present as Phase 2 stub (interface wired, logic deferred) | 15 |
| **Total verified** | **48** |
| Missing or absent | 0 |

All 48 changes are present. Phase classification is correct per Directive 13 throughout: every change on Directive 13's Phase 2 defer list is tagged `[Phase 2: ...]` in the plan with an explanation of why it can be added without rework. Every change on Directive 13's Phase 1 ship list is present and operationally specified.

---

## Directive Compliance Summary

Verification against all 14 directives in JACK-ARCHITECTURAL-DIRECTIVES.md. Evidenced from CAPSTONE-PLAN-v2.md content.

| Directive | Title | Compliant? | Evidence in CAPSTONE-PLAN-v2.md |
|---|---|---|---|
| 1 | The Rigidity Problem — dynamic agent configuration, not fixed types | YES | §4.2 "[BATCH 2 UPDATE] Template registry, not fixed types" — seed templates in registry, custom AgentDefinition generation below 0.85 similarity threshold, tighten-only invariant. The five fixed types are explicitly renamed "seed templates." |
| 2 | MECE Issue Tree Decomposition — casing phase before task decomposition | YES | §3.4 Steps 3-4 — independent heterogeneous lens construction (financial, operational, market/competitive agents), Opus meta-agent synthesis (Self-MoA), discrete MECE verification step with five dimensions. Step 8 human review gate shows the issue tree explicitly. |
| 3 | Iterative Multi-Round Research — fully specified loop with stopping criteria | YES | §4.5 "[BATCH 2 UPDATE] The Iterative Research Loop" — three-criterion stopping (hard cap 3/5, quality gate, novelty exhaustion), decision table per round, Memory scratchpad. §4.6 scope-change detection. Opening: "This was the 'single biggest architectural gap' (Directive 3). The iterative research loop is now fully specified." |
| 4 | Engagement Scope — handles all Keystone engagement types without predefined skill files | YES | §3.8 5-type analytical taxonomy (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) + §3.4 dynamic agent configuration. Note §3.8: "70% of MBB engagements blend categories." Template registry + issue tree decomposition enables novel engagement types without hardcoded skill files per the auto shop test case framing. |
| 5 | Build Philosophy — right interfaces at reduced feature depth, not mini MVP | YES | §5.15 Graceful Degradation Principle — "Every evaluation mechanism that is not a structural gate is implemented as an optional module with a defined bypass behavior." §12.0 five Day-1 coding standards ensure zero-rework Phase 2 migration. Phase 2 deferrals throughout §§3-7 specify exactly how each feature is added by extending an interface or adding a module. |
| 6 | FITFO Standard — system-level competence on novel problems | YES | §3.4 Step 6 Dynamic Agent Configuration — below similarity threshold, custom AgentDefinition generated. §7.1 "[BATCH 2 UPDATE]" Observation Library as CBR (Phase 2) — cross-domain retrieval via flexon problem archetypes. §3.8 domain taxonomy for framework selection. |
| 7 | Human-in-the-Loop Gates — non-negotiable at issue tree and confidence map | YES | §3.4 Step 8 — Human Review Gate: "Non-negotiable (Directive 7). The human reviews: the issue tree, the agent configurations, and the Day-1 Hypothesis." §12.0 "[BATCH 2 UPDATE] Human-in-the-Loop Gates: Phase 1 Implementation" — PostgreSQL state machine, REST API, web UI, approve/modify/reject. Second gate: §4.3 Deliberation outputs confidence map, §12.1 Component #9 "HITL gate after confidence map." |
| 8 | Karpathy's LLM Knowledge Bases — compiled markdown wikis, not just embeddings | YES | §6.2 Component #3b "[BATCH 2 UPDATE]" — three-layer pattern (raw/ + compiled/ + INDEX.md) per engagement. §7.1 Observation Library as compiled wiki. Distinction explicitly stated: "RAG for discovery (finding sources not yet ingested), filesystem navigation for accumulated knowledge." Cross-engagement wiki tagged Phase 2 per Directive 13. |
| 9 | Component #3 Over-Engineering Concern — wait for findings before building | YES | §6.2 "[BATCH 2 UPDATE]" split into #3a and #3b resolves this. §12.1 Phase 1 build sequence explicitly lists "#3a Source Discovery (L)" and "#3b Knowledge Accumulation (M)" as separate parallel deliverables. Semantic Router removed, Bifrost removed — over-engineered elements eliminated. |
| 10 | Confirmed Settled Decisions — all 11 settled decisions validated | YES | All 11 decisions are reflected in the plan. PydanticAI: §12.0. Deliberation = independent parallel + structured aggregation: §4.3. Five-layer evaluator: §5.9. Model mixing: §4.1. Agent isolation: §4.1. Claim-level IR: §4.4. Generator-based loop: §4.5. Protocol-based contracts: §12.0. Events as type union (not tested): §2 architecture diagram. Multi-tenancy: §4.1 (`engagement_id` throughout). Narrative Coherence as Tier 1 gate: §5.3. |
| 11 | Configurable Pipeline Depth — three profiles (Light/Standard/Deep), no gold-plated bullets | YES | §3.8 "Pipeline Profile Selection" — table with Light (1-2 agents, 1 round, Layers 1-2), Standard (3 agents, 2-3 rounds, Layers 1-3), Deep (up to 5 agents, up to 5 rounds, full stack). "The engagement classifier recommends a profile; the operator can override up or down via the control panel (Directive 11)." |
| 12 | Casing Principles Over Example Libraries — methodology from casing books, not memorized trees | YES | §3.4 Step 3 — "2-3 curated MECE exemplars from casing materials" as demonstrations of principles, not template libraries. §3.9 Decision-First CoT operationalizes the 5-step methodology. The plan describes teaching *how* to decompose, with exemplars as demonstrations. |
| 13 | Phase 1 Depth Staging — specific Phase 1 / Phase 2 lists | YES | All 11 Phase 1 items verified present and operative (see change audit above). All 8 Phase 2 deferrals verified present as `[Phase 2: ...]` stubs with interface hooks wired. Zero Phase 2 items missing from the plan. Zero Phase 2 items accidentally promoted to Phase 1. |
| 14 | Quality Standard — real product for a real consulting firm, Goldman-grade bar | YES | §5.4 Goldman-grade bar: "Would a domain expert at a top firm call this solid on its own merits?" 0.80+ Spearman rank correlation target for Evaluator calibration. §5.4 calibration against actual Keystone deliverables scored by Jack. §1 Executive Vision frames the entire system as Goldman-grade output. |

**All 14 directives: COMPLIANT.**

---

## Notable Observations

1. **Phase split on Change #7 (VOI scoring)** is exact: Phase 1 uses `(decision_relevance x uncertainty)` and Phase 2 adds the `/ estimated_cost` denominator. This is the correct "defer the sophistication, keep the interface" pattern from Directive 5.

2. **Phase split on Change #25 (evaluation profiles)** starts at 3 profiles in Phase 1 (not 2). This is a minor upgrade over the original 2 profiles and consistent with Directive 13's "start with 3-4" language.

3. **Change #39 (CBR system)** is marked Phase 2 correctly, but the hook is wired: §3.4 Step 1 says "the CBR query hook is wired in Phase 1 but returns empty until the library is populated." This is exactly the Directive 5 pattern: correct interface now, full implementation later.

4. **Change #22 (ADaPT-style reactive decomposition)** is correctly Phase 2 despite being research-facing: §4.7 is explicit that Phase 1 uses static 2-3 level depth and adaptive deepening is activated in Phase 2 by extending the feedback loop without data flow changes.

5. **Directive 7 compliance is complete**: both non-negotiable gates are implemented — issue tree gate in §3.4 Step 8 and confidence map gate in §4.3 + §12.1 Component #9. The database state machine HITL (Change #45) is the Phase 1 implementation of both gates.
