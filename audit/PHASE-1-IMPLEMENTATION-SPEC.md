# Phase 1 Implementation Spec: Core Pipeline
*Produced: 2026-04-04 | Updated: 2026-04-05 (Batch 2 changes) | Derived from CAPSTONE-PLAN-v2.md + UNIFIED-SYNTHESIS.md + MASTER-SYNTHESIS.md*

---

## Build Order

```
#1  RESEARCH.md spec format (S+) ─────────────────────────┐
#2  Citation data model (S) ──────────────────────────────┤  All parallel,
#3a Source Discovery (L) ─────────────────────────────────┤  no dependencies
#3b Knowledge Accumulation (M) ──────────────────────────┤
#4  MCP gateway (M) ─────────────────────────────────────┤
#HITL PostgreSQL state machine (S) ──────────────────────┘
                                                          │
#5  Specification Engine L0 (XL) ◄────────────────────────┘
                                                          │
#6  Evaluator stack L4 Layers 1-3 (XL) ◄──────────────────┘
                                                          │
#7  Research Agent pipeline L1 (L+) ◄─────────────────────┘
                                                          │
#8  CitationProcessor (M) ◄──────────────────────────────┘
                                                          │
#9  Deliberation L1.5 (L+) ◄─────────────────────────────┘
                                                          │
#10 Evaluator calibration (M) ◄──────────────────────────┘
                                                          │
#11 End-to-end pipeline test (M) ◄───────────────────────┘
```

Items #1-#4 and #HITL can be built in parallel (no dependencies). Items #5-#11 are sequential with the dependencies shown. #3b (Knowledge Accumulation) can optionally be deferred until after #5 ships since it primarily serves cross-engagement knowledge. HITL must ship alongside #1-#4 because #5 and #9 depend on it.

---

## Minimum Viable Pipeline (MVP)

The smallest subset that produces a working end-to-end research flow:

```
User question
  → L0: RESEARCH.md generation + task decomposition (simplified: 3-5 tasks)
    → L1: 2-3 research agents (Sonnet, Exa + Brave only, strict isolation)
      → CitationProcessor (dedup + URL check only, skip corroboration scoring)
        → L1.5: Single aggregation pass (skip independent parallel analysis)
          → L4: Layers 1-2 only (deterministic verification + citation gate)
            → Markdown output
```

**MVP strips:** No Prometheus 2 rubric scoring (Layer 3). No deliberation diversity (single aggregator). No cross-model ensemble. No model mixing (all Sonnet). 2-3 agents instead of 15-50. Output is Markdown, not formatted deliverable.

**MVP proves:** The pipeline runs end-to-end. Data flows through all stages. Citations trace from source to output. The evaluator catches fabricated citations. Quality is measurable (even if only on Layers 1-2). Claim-level selection aggregation produces coherent findings. HITL gates block and resume execution correctly.

Build the MVP first, then add depth: Prometheus 2 rubric scoring, independent parallel analysis in deliberation, additional search APIs, model mixing, cross-model evaluation.

---

## Component Specifications

### #1: RESEARCH.md Specification Format

**What to build:**
- `templates/RESEARCH.md.template` -- the canonical engagement specification template
- `schemas/research_md.schema.json` -- JSON Schema for validating RESEARCH.md structure
- `schemas/research_tasks.schema.json` -- JSON Schema for research-tasks.json
- 3-5 sample RESEARCH.md files for test engagements

**Input/output contract:**
```
Input:  User question (natural language string)
Output: RESEARCH.md file conforming to schema
        research-tasks.json conforming to schema

RESEARCH.md template additions (Batch 2):
  - day_1_hypothesis: string  // testable claim anchoring the engagement
  - engagement_type: enum["SIZING", "DIAGNOSTIC", "EVALUATIVE", "EXPLORATORY", "STRATEGIC"]
  - max_rounds: integer | null  // override for default 3-round cap (null = use default)

research-tasks.json schema (key fields):
{
  "project": string,
  "research_md": "path/to/RESEARCH.md",
  "specification_version": integer,
  "tasks": [{
    "id": "task_NNN",
    "depends_on": string[]  // DAG structure: IDs of tasks that must complete first
    "category": enum["market_sizing", "competitive_landscape", "financial_analysis",
                      "technology_assessment", "regulatory", "strategic_positioning"],
    "type": enum["estimative", "current"],
    "target_decision_usefulness": integer(1-5),
    "description": string,
    "end_product": string,  // specific deliverable format (chart type, table structure, conclusion format)
    "required_sources": string[],
    "acceptance_criteria": string[],
    "deliverable_destination": string,
    "passes": boolean (default false, only Evaluator can set true),
    "priority": integer,
    "priority_score": number,  // computed field: (decision_relevance x current_uncertainty) / estimated_cost
    "anti_confirmatory_framing": string,
    "assigned_tools": string[] (3-5 tools per task),
    "assigned_model": enum["opus", "sonnet", "haiku"]
  }]
}
```

**Acceptance criteria:**
- Schema validates all 3-5 sample RESEARCH.md files
- research-tasks.json schema enforces: anti_confirmatory_framing required, passes default false, assigned_tools length 3-5, depends_on is a valid array (empty array = no dependencies), end_product required
- RESEARCH.md template includes day_1_hypothesis, engagement_type, and max_rounds fields
- Templates are usable by the Specification Engine agent without modification

**Dependencies:** None
**Scope:** S+ (2-3 days)
**First test:** Manually write a RESEARCH.md for "Evaluate the competitive position of Company X in the autonomous vehicle sensor market." Validate against schema. Decompose into research-tasks.json with DAG dependency structure. Validate against schema. Verify priority_score is computed and depends_on references are valid task IDs.

---

### #2: Citation Data Model

**What to build:**
- `schemas/citation.schema.json` -- citation entity model
- `schemas/claim.schema.json` -- claim-level intermediate representation
- `schemas/citation_manifest.schema.json` -- CitationProcessor output

**Input/output contract:**
```
Citation entity:
{
  "citation_id": "CIT-NNN",
  "url": string,
  "doi": string | null,
  "title": string,
  "authors": string[],
  "publication": string,
  "date": string (ISO 8601),
  "access_date": string (ISO 8601),
  "source_type": enum["academic", "news", "filing", "report", "government", "internal"],
  "quality_score": number(0-1),  // Admiralty Code composite
  "url_live": boolean | null,
  "crossref_verified": boolean | null,
  "found_by_agents": string[]  // agent IDs that independently found this source
}

Claim entity (L1.5 → L2 handoff):
{
  "claim_id": "CLM-NNN",
  "text": string,
  "source_chunk_ids": string[],
  "citation_ids": string[],  // references citation entities
  "confidence": number(0-1),
  "corroboration_count": integer,
  "provenance_chain": string,
  "confidence_tier": enum["high_above_80", "moderate_60_80", "weak_50_60",
                          "contested_below_50", "insufficient_evidence"],
  "ach_diagnosticity": enum["high", "medium", "low"] | null
}

Citation manifest (CitationProcessor output):
{
  "manifest_id": string,
  "engagement_id": string,
  "citations": Citation[],
  "corroboration_pairs": [{ "citation_a": string, "citation_b": string, "overlap_score": number }],
  "dead_urls": string[],
  "fabrication_flags": string[]
}
```

**Acceptance criteria:**
- All schemas validate with standard JSON Schema validators
- Citation entity supports all source types in the retrieval architecture
- Claim entity supports the full confidence map taxonomy
- Schemas are referenced by CitationProcessor and Deliberation components

**Dependencies:** None (design in parallel with everything)
**Scope:** S (1-2 days)
**First test:** Create a mock citation manifest with 10 citations, 5 claims. Validate against schemas. Verify provenance chain traces from claim → citation → source.

---

### #3a: Source Discovery

**What to build:**
- PostgreSQL database with pgvector + ParadeDB extensions (BM25 + RRF fusion)
- `src/retrieval/` module with:
  - `vector_store.py` -- pgvector CRUD operations, embedding storage/query
  - `hybrid_search.py` -- dense + BM25 + RRF fusion (ParadeDB)
  - `document_processor.py` -- Docling integration for structure-aware PDF parsing (97.9% table accuracy)
  - `source_scorer.py` -- Admiralty Code quality scoring
  - `contextual_retrieval.py` -- Haiku-generated preamble per chunk at ingest time (67% failure reduction combined with reranking; zero cost on Claude Max)
  - `reranker.py` -- Cohere Rerank v3.5 (top 150 -> top 20)
- Embedding model: Voyage-finance-2 ($0.12/MTok, 49% improvement over OpenAI on ConvFinQA, third-party validated via FinMTEB EMNLP 2025)
- Chunking rules: 512 tokens, 50-100 token overlap, tables stored as HTML, XBRL data bypasses chunker
- External search APIs: Exa, Brave Search (Firecrawl for content extraction). Tavily REMOVED (acquired by Nebius Feb 2026, pricing uncertain). Semantic Router REMOVED. Bifrost caching REMOVED (replaced by in-process lru_cache).
- Future enhancement: VectorChord (vchordrq/vchordg indexes) as pgvector index upgrade when vector count exceeds 10M. Zero-migration-cost addition since VectorChord sits on pgvector. Evaluated 2026-04-05, verdict: KEEP pgvector for Phase 1. See `audit/fork-evaluations/vectorchord-eval.md`.

**Input/output contract:**
```
Input:  SearchQuery {
  query: string,
  source_types: string[],  // ["academic", "news", "filing", ...]
  max_results: integer,
  engagement_id: string (for caching scope)
}

Output: SearchResults {
  results: [{
    content: string,
    metadata: { source_type, url, date, authority_score, chunk_context, ... },
    relevance_score: number,
    retrieval_method: enum["dense", "bm25", "hybrid"]
  }],
  cache_hit: boolean
}
```

**Acceptance criteria:**
- Hybrid search (dense + BM25 + RRF) returns results for financial document queries
- Voyage-finance-2 embeddings in use (not OpenAI or generic models)
- Contextual retrieval: Haiku generates preamble per chunk at ingest time
- Reranker reduces top-150 results to top-20 before returning to agents
- Docling parses an SEC 10-K filing and preserves table structure (tables as HTML in metadata)
- XBRL data bypasses chunker and is stored as structured records
- In-process lru_cache returns identical results on repeat queries within TTL
- Source quality scoring produces Admiralty Code two-axis scores

**Dependencies:** None (parallel with #1-#2)
**Scope:** L (1-2 weeks)
**First test:** Index 5 SEC filings via Docling. Run a hybrid search for "revenue growth rate." Verify table data is preserved as HTML and retrievable. Verify BM25 catches exact financial terms that dense search misses. Verify reranker reduces result set to top 20. Verify Voyage-finance-2 is the embedding model (not a fallback).

---

### #3b: Knowledge Accumulation

**What to build:**
- `src/knowledge/` module with:
  - `wiki_builder.py` -- compiles raw subagent artifacts into structured markdown wiki
  - `index_maintainer.py` -- auto-maintains INDEX.md per engagement
  - `content_hasher.py` -- content-hash provenance per proposition (for wiki compilation integrity)
- Per-engagement directory structure:
  ```
  {engagement_id}/
    memory/
      raw/          # full subagent artifacts (unmodified)
      compiled/     # orchestrator-synthesized findings
      INDEX.md      # auto-maintained navigation index
  ```
- Human-designed schemas for compiled/ entries (ETH Zurich: human-written +4%, LLM-generated -2%)
- Storage: filesystem for Phase 1 (Git-trackable, Claude Max single-user sufficient). PostgreSQL migration in Phase 2.
- Design wiki schema to be storage-agnostic from Day 1 (interface, not direct filesystem calls)

**Input/output contract:**
```
Input:  SubagentArtifact {
  engagement_id: string,
  round: integer,
  agent_id: string,
  artifact_text: string,
  claims: Claim[]  // for content-hash provenance
}

Output: WikiEntry {
  path: string,  // compiled/{topic}.md
  content_hash: string,  // per-proposition hash for provenance
  indexed: boolean,  // appears in INDEX.md
  round_added: integer
}
```

**Acceptance criteria:**
- raw/ receives unmodified subagent artifacts after each round
- compiled/ receives orchestrator-synthesized summaries after each round
- INDEX.md updates automatically when new compiled/ entries are added
- Each proposition in compiled/ has a content-hash traceable to the source artifact in raw/
- Schema is storage-agnostic (no direct filesystem calls in the interface layer)

**Dependencies:** None (parallel with #1-#2, #3a). Can optionally be deferred until after #5 ships.
**Scope:** M (3-5 days)
**First test:** Run one mock research round. Write 3 subagent artifacts to raw/. Run wiki_builder. Verify compiled/ has synthesized summaries. Verify INDEX.md is updated. Verify each compiled proposition has a content-hash that traces back to the originating raw/ artifact.

---

### #4: MCP Gateway

**What to build:**
- `src/gateway/` module with:
  - `mcp_gateway.py` -- central router for all MCP tool calls
  - `auth.py` -- per-agent tool authorization (only assigned tools accessible)
  - `rate_limiter.py` -- Redis-backed rate limiting per provider
  - `circuit_breaker.py` -- per-provider circuit breakers
  - `audit_log.py` -- all tool calls logged with agent_id, tool, input, output, timestamp
  - `tool_registry.py` -- registry of available MCP servers with health checks; tool entries include transport_type (enum["http", "stdio", "docker"]) and security_approved (boolean)
  - `tool_loader.py` -- progressive Tool Search loading (stub descriptions first, full schemas on demand)
- Configure integrations to existing MCP servers (not building servers from scratch):
  - Exa (`exa-labs/exa-mcp-server`, hosted HTTP)
  - Brave Search (`brave/brave-search-mcp-server`, hosted HTTP)
  - EdgarTools (`dgunning/edgartools` built-in MCP, stdio+HTTP)
  - FRED (`stefanoamorelli/fred-mcp-server`, stdio+Docker)
  - paper-search-mcp (replaces Academix: 21+ sources vs. 5, free-first full-text fallback; Beta maturity -- load test before relying as sole academic server, fallback: Academix)
  - Finnhub MCP -- market data (real-time quotes, financials, earnings)
  - doi-mcp (`tfscharff/doi-mcp`, stdio) -- for Layer 2 citation verification `[LEAK-SYNTHESIS UPDATE]`
- Fork candidate: IBM ContextForge as gateway starting point. Evaluate in first 2 days of build (circuit breakers, rate limiting, Redis federation already built). If authorization model is incompatible, build custom.
- Add transport_type and security_approved fields to tool registry schema

**Input/output contract:**
```
Input:  ToolCall {
  agent_id: string,
  tool_name: string,
  parameters: object,
  engagement_id: string
}

Output: ToolResult {
  result: object,
  citations: Citation[],  // extracted from tool output
  tokens_used: integer,
  latency_ms: integer,
  cache_hit: boolean
}

Authorization check:
  agent_id → assigned_tools[] (from research-tasks.json)
  Reject if tool_name not in assigned_tools
```

**Acceptance criteria:**
- Agent can only call tools assigned to it (structural enforcement, not prompt-based)
- Rate limiter prevents exceeding provider limits (configurable per provider)
- Circuit breaker opens after 3 consecutive failures, retries after 30s
- Audit log captures every tool call with full context
- At least 3 MCP servers (Exa, Brave, EdgarTools) operational including at least one HTTP and one stdio transport
- paper-search-mcp registered and callable for academic source queries
- Finnhub MCP registered and callable for market data queries
- Tool registry entries include transport_type and security_approved fields
- Tool Search: with 8+ MCP servers connected, tool descriptions total under 10,000 tokens in context `[LEAK-SYNTHESIS UPDATE]`
- All retry loops have a maximum attempt count and dead-letter path `[LEAK-SYNTHESIS UPDATE]`

**Dependencies:** None (parallel with #1-#3)
**Scope:** M (1 week)
**First test:** Create an agent with assigned_tools=["exa_search", "brave_search"]. Verify it can call Exa and Brave. Verify it gets rejected when calling EdgarTools. Check audit log. Verify paper-search-mcp returns results from 3+ distinct academic sources. Verify tool registry entries have transport_type and security_approved populated.

---

### #HITL: Human-in-the-Loop Infrastructure

**What to build:**
- PostgreSQL tables (3):
  - `review_gates` -- tracks gate state (pending/approved/modified/rejected) per engagement and gate type
  - `review_items` -- the artifacts presented for review (issue tree JSON, agent configs, confidence map)
  - `review_decisions` -- the human decision record (decision type, modifications, timestamp, reviewer)
- REST API (`src/hitl/api.py`, FastAPI):
  - `GET /gates/{engagement_id}` -- list all gates and their current state for an engagement
  - `POST /gates/{engagement_id}` -- create a new review gate (called by pipeline on trigger)
  - `GET /decisions/{gate_id}` -- retrieve decision for a specific gate
  - `POST /decisions/{gate_id}` -- submit a decision (approve/modify/reject) with optional payload
- Web UI (`src/hitl/ui/`):
  - Displays issue tree visualization, agent configurations, and confidence map for Gate 1
  - Displays confidence map and deliberation outputs for Gate 2
  - Approve / Modify / Reject controls with modification input form
  - No framework requirement: minimal HTML/JS sufficient for Phase 1
- Pipeline integration: `hitl_gate.py` (used by both #5 and #9) polls the database state machine; resumes when gate state == "approved" or "modified"; halts when state == "rejected"
- Maps to Temporal Signals in Phase 2 with no agent code changes (design requirement)

**Input/output contract:**
```
Gate 1 (post-Spec Engine): presents issue_tree_json + agent configs + sprint contract draft
Gate 2 (post-Deliberation): presents confidence_map + deliberation_result summary

Decision payload (POST /decisions/{gate_id}):
{
  "decision": enum["approve", "modify", "reject"],
  "modifications": object | null,  // e.g., modified issue tree or agent config overrides
  "reviewer": string,
  "notes": string | null
}
```

**Acceptance criteria:**
- Gate 1 blocks pipeline after EngagementSpec is produced; pipeline does not dispatch agents until gate is approved
- Gate 2 blocks pipeline after DeliberationResult is produced; pipeline does not advance to content generation until gate is approved
- Approve flow: pipeline resumes with no changes
- Modify flow: pipeline resumes with human modifications applied to the relevant artifact
- Reject flow: pipeline halts; logs rejection with reviewer notes
- Web UI displays all gate artifacts clearly enough for Jack to make an informed decision
- REST API is callable from pipeline code with < 100ms overhead (local or same-host deployment)
- Maps to Temporal Signals API in Phase 2 without agent code changes

**Dependencies:** None (parallel with #1-#4)
**Scope:** S (2-3 days)
**First test:** Trigger Gate 1 from a test Specification Engine run. Verify gate appears in the web UI. Submit an approve decision. Verify pipeline receives the approval and continues. Then trigger Gate 1 again and submit a reject decision. Verify pipeline halts with logged rejection.

---

### #5: Specification Engine (L0)

**What to build:**
- `src/specification/` module with:
  - `spec_engine.py` -- main orchestrator (Opus model)
  - `engagement_classifier.py` -- routes to 5-type taxonomy (SIZING/DIAGNOSTIC/EVALUATIVE/EXPLORATORY/STRATEGIC) using five signals: specificity of deliverable, presence of testable hypothesis, known analytical framework, scope boundedness, decision type. Also routes to pipeline profile (Light/Standard/Deep per Directive 11).
  - `intent_clarifier.py` -- Decision-First CoT (5-step structured prompt). NO TiCoder divergence detection (Phase 2).
  - `decomposer.py` -- question → shallow issue tree (2-3 levels, 8-20 leaf nodes) using 3 Sonnet agents with heterogeneous consulting lenses (financial, operational, market/competitive). Self-MoA for tree construction. Uses 2-3 curated MECE exemplars. Pydantic models enforce reasoning-first field ordering. Day-1 Hypothesis formed before decomposition begins.
  - `validator.py` -- MECE verification with Opus (five dimensions: mutual exclusivity, collective exhaustiveness, tailoring, actionability, depth appropriateness). Binary criteria per dimension. Programmatic semantic similarity checks complement the LLM judge. Trees failing verification are regenerated.
  - `priority_scorer.py` -- SIMPLIFIED heuristic scoring (NOT VOI formula). Phase 1: human-readable priority_score derived from decision_relevance x uncertainty heuristics. VOI-inspired formula deferred to Phase 2 (Directive 13).
  - `template_registry.py` -- registry of 5-10 seed AgentDefinition templates. Queries registry on engagement_type; above 0.85 similarity instantiates with task-specific interpolation; below generates custom AgentDefinition constrained by structural validation. NO template promotion loop (Phase 2).
  - `task_generator.py` -- research-tasks.json with DAG dependency structure, anti-confirmatory framing, per-branch end_product specification
  - `scout_strike.py` -- Day-1 Hypothesis anchors scout phase. Exploration-exploitation ratio starts ~70/30 scout/strike, shifts as knowledge accumulates.
  - `feedback_loop.py` -- findings feed back into issue tree refinement and task reprioritization. Completed tasks immutable; only pending tasks modified. 3-cycle maximum.
  - `hitl_gate.py` -- triggers HITL database state machine review after task list generation (Directive 7 Gate 1). NO CBR Observation Library query (Phase 2 -- Observation Library doesn't exist in Phase 1).
- Agent definition: `.claude/agents/specification-engine.md`
- PydanticAI models for RESEARCH.md, research-tasks.json, and AgentDefinition types

**10-step pipeline (all steps exist in Phase 1, some at reduced depth per Directive 13):**
1. Problem Framing + Classification (engagement classifier, 3-4 types in Phase 1, 5 in Phase 2; Decision-First CoT; NO TiCoder)
2. Day-1 Hypothesis (full implementation)
3. Issue Tree Decomposition (3 Sonnet agents, heterogeneous lenses, shallow 2-3 level trees; full implementation)
4. Decomposition Validation (MECE verification with Opus, binary criteria; full implementation)
5. Priority Assignment (SIMPLIFIED heuristic scoring, NOT VOI; Phase 2 per Directive 13)
6. Dynamic Agent Configuration (template registry, 5-10 seed templates; NO promotion loop, Phase 2)
7. Task Generation (DAG structure, anti-confirmatory framing, per-branch end products; full implementation)
8. Human Review Gate (HITL database state machine; full implementation)
9. Scout Phase (Day-1 Hypothesis, 70/30 exploration-exploitation; full implementation)
10. Feedback Loop (3-cycle max, completed tasks immutable; full implementation)

**Input/output contract:**
```
Input:  UserQuestion {
  question: string,
  client_context: string | null,
  constraints: string[] | null
}

Output: EngagementSpec {
  research_md: RESEARCH.md (validated against schema),
  tasks: research-tasks.json (validated against schema, DAG structure),
  specification_version: integer,
  engagement_type: enum["SIZING", "DIAGNOSTIC", "EVALUATIVE", "EXPLORATORY", "STRATEGIC"],
  day_1_hypothesis: string,
  issue_tree_json: object,  // the structured issue tree for HITL display and living-document updates
  validation_report: {
    intent_clear: boolean,
    scope_valid: boolean,
    within_frontier: boolean,
    quality_threshold_met: boolean
  }
}

Quality gate: All four validation checks must pass before HITL gate triggers.
HITL gate: System pauses after EngagementSpec is produced. Resumes only on human approval.
```

**Acceptance criteria:**
- Given "Evaluate competitive position of Company X in AV sensor market," produces a RESEARCH.md with: decision context, engagement_type, day_1_hypothesis, 3+ research questions, methodology requirements, source requirements, output format, non-goals
- Decomposes into 10+ tasks with anti_confirmatory_framing on each, DAG depends_on structure, end_product per task
- Tasks include both estimative and current types with appropriate decision_usefulness targets
- Assigns 3-5 tools per task from the MCP gateway registry
- Validation rejects underspecified questions (e.g., "Tell me about AI")
- Issue tree output includes engagement_type, day_1_hypothesis, and issue_tree_json
- Template registry returns a matching template for standard engagement types; generates custom AgentDefinition for novel types
- HITL gate blocks execution until approval received from database state machine
- PydanticAI schema validation catches malformed outputs

**Dependencies:** #1 (schemas), #4 (MCP gateway for tool registry), #HITL (database state machine)
**Scope:** XL (2-3 weeks)
**First test:** Feed "Evaluate the competitive position of Luminar Technologies in the autonomous vehicle lidar market" to the Specification Engine. Verify it produces a valid RESEARCH.md with day_1_hypothesis and engagement_type set. Verify research-tasks.json has DAG depends_on structure and end_product per task. Verify anti-confirmatory framing is present. Verify tool assignments are sensible (financial tasks get EdgarTools, academic tasks get paper-search-mcp). Verify pipeline pauses at HITL gate waiting for approval.

---

### #6: Evaluator Stack (L4) -- Layers 1-3

**What to build:**
- `src/evaluator/` module with:
  - `layer1_deterministic.py` -- FActScore atomic fact decomposition, numerical consistency, URL liveness
  - `layer2_citation_gate.py` -- Citation verification via MCP gateway to doi-mcp (9-database parallel check). Binary gate: any fabrication = full rejection `[LEAK-SYNTHESIS UPDATE: routes through MCP gateway to doi-mcp instead of direct CrossRef/Semantic Scholar API calls]`
  - `layer3_rubric.py` -- 10-dimension rubric scoring via Prometheus 2. One prompt per dimension. Separate evaluation prompts with dimension-specific criteria. Geometric mean aggregation (replaces implicit weighted sum; prevents dimension compensation). Tier 1/Tier 2 structure enforced.
  - `three_pass.py` -- Pass 1 (dimensional) + Pass 2 (holistic gestalt +-5-10%). Pass 3 (Observation Library scan) is INACTIVE until Phase 2
  - `rubric_config.py` -- dimension definitions, weights, engagement-type-specific weight profiles (3-4 profiles in Phase 1, expanding to 8-10 in Phase 2). Tier 1 universal gates: Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence (floor thresholds; failure = rejection regardless of Tier 2). Tier 2 adaptive dimensions: Analytical Depth, Source Quality, Quantitative Rigor, Actionability, Evaluative Surprise, Calibrated Confidence (weights flex by engagement type).
  - `sprint_contract.py` -- per-section quality criteria loader. NO sprint contract negotiation between Evaluator and Generator (Phase 2 per Directive 13).
- Prometheus 2 local deployment (7B variant for Mac Mini)
- Calibration data: 10+ scored sample outputs

**Input/output contract:**
```
Input:  EvaluationRequest {
  output_text: string,
  sprint_contract: SprintContract,
  task: ResearchTask,  // includes type (estimative/current)
  engagement_type: enum["SIZING", "DIAGNOSTIC", "EVALUATIVE", "EXPLORATORY", "STRATEGIC"],
  citations: Citation[],
  research_md: RESEARCH.md reference
}

Output: EvaluationResult {
  passed: boolean,
  overall_score: number(0-100),
  layer1_results: {
    facts_verified: integer,
    facts_failed: integer,
    numerical_inconsistencies: string[],
    dead_urls: string[]
  },
  layer2_results: {
    citations_checked: integer,
    citations_verified: integer,
    citations_fabricated: string[],  // if non-empty, passed=false immediately
    gate_passed: boolean
  },
  layer3_results: {
    tier1_gate_results: {  // Tier 1 universal gates
      intent_alignment: { score: number(0-100), passed: boolean, feedback: string },
      intellectual_honesty: { score: number(0-100), passed: boolean, feedback: string },
      completeness: { score: number(0-100), passed: boolean, feedback: string },
      narrative_coherence: { score: number(0-100), passed: boolean, feedback: string }
    },
    tier2_dimension_scores: {  // Tier 2 adaptive dimensions
      [dimension_name]: {
        score: number(0-100),
        feedback: string,
        sub_criteria_notes: string[]
      }
    },
    aggregation_method: "geometric_mean",
    weighted_total: number(0-100),  // geometric mean of all passing dimensions
    gestalt_adjustment: number(-10 to +10),
    final_score: number(0-100)
  },
  feedback: string,  // specific, actionable feedback for regeneration
  observation_entry: ObservationEntry | null  // for Observation Library (Phase 2)
}

Pre-rubric gate: layer2_results.citations_fabricated.length > 0 → passed=false, skip Layer 3.
Tier 1 gate: any tier1_gate_results[dimension].passed == false → passed=false, skip Tier 2 aggregation.
```

**Acceptance criteria:**
- Layer 1: Catches numerical inconsistencies (e.g., "revenue grew 15%" contradicted by table showing 12%)
- Layer 2: Rejects output with a fabricated DOI. Passes output with all real citations
- Layer 3: Scores each dimension independently (10 separate prompts). Produces actionable feedback per dimension
- Tier 1 gates enforced: a failing Tier 1 dimension (floor threshold not met) causes immediate rejection regardless of Tier 2 scores
- Geometric mean aggregation: high Narrative Coherence cannot mask failing Intellectual Honesty
- 3-4 engagement-type profiles operational in Phase 1 (not just estimative vs. current); profiles expand to 8-10 in Phase 2
- Anti-slop sub-check: flags generic openings, trendslop, excessive hedging
- Gestalt overlay: adjusts +-5-10% for emergent quality signals
- NO dimension-specific verification strategies (programmatic QR, position-switching AD) in Phase 1 (Phase 2 per Directive 13)

**Dependencies:** #1 (schemas for sprint contracts), #2 (citation data model)
**Scope:** XL (2-3 weeks)
**First test:** Create a deliberately flawed research output with: one fabricated citation, one numerical inconsistency, one section of trendslop, and one genuinely good analytical section. Run through the evaluator. Verify: Layer 2 catches the fabricated citation and rejects. On a separate clean input: Layer 1 catches the numerical error. Layer 3 scores the trendslop section low on Actionability. A Tier 1 failure (e.g., fabricated framing failing Intent Alignment) causes rejection before Tier 2 runs. The good section scores well on Analytical Depth. Verify geometric mean is used for aggregation.

---

### #7: Research Agent Pipeline (L1)

**What to build:**
- `src/agents/` module with:
  - `research_agent.py` -- base research agent (Sonnet model). Agent configs loaded from template registry (template-based dispatch, NOT fixed enum dispatch).
  - `agent_types/` -- seed templates: Quantitative, Qualitative, Contrarian, Historical Analogy, Internal Document. These are templates in the registry, not hard-coded types.
  - `isolation.py` -- filesystem-based isolation (per-agent working directory, advisory file locks, WAL)
  - `finding_writer.py` -- structured finding output (claim + evidence + citations + per-claim confidence + caveats + absence). Output enforces 1,000-2,000 token condensed summary + full artifact written to `{engagement_id}/memory/raw/` (artifact bypass pattern).
  - `task_claimer.py` -- lock-file-based task claiming
  - `context_loader.py` -- JIT context loading from compiled/ wiki via INDEX.md navigation
  - `error_recovery.py` -- retry with exponential backoff (tenacity), model fallback chain (Opus -> Sonnet -> Haiku -> cached), error classification. Partial-result continuation: if 3 of 5 agents succeed, combine results + retry failures separately.
  - `fork_manager.py` -- byte-identical prefix construction and launch staggering for fork-mode cache sharing `[LEAK-SYNTHESIS UPDATE]`
  - `micro_compact.py` -- zero-API-cost cache_edits compaction (keep 5 most recent tool results) `[LEAK-SYNTHESIS UPDATE]`
  - `auto_compact.py` -- circuit-broken LLM summarization (3-failure limit, 50% context threshold) `[LEAK-SYNTHESIS UPDATE]`
- Agent definitions: `.claude/agents/research-agent-*.md` (one per seed template type; custom agents generated from template_registry.py)
- Soul prompts per agent template
- Agent config: `MAX_THINKING_TOKENS = 10000` for Sonnet agents (down from 31,999 default) `[LEAK-SYNTHESIS UPDATE]`
- Iterative research loop: 3-round default, 5 max. Three-criterion stopping: hard cap OR quality gate score >= threshold OR semantic novelty exhaustion. Any criterion can terminate.

**Input/output contract:**
```
Input:  AgentAssignment {
  task: ResearchTask (from research-tasks.json),
  research_md: RESEARCH.md,
  assigned_tools: string[],
  template_id: string,  // from template registry (replaces fixed agent_type enum)
  model: "sonnet",
  working_dir: string (isolated per-agent),
  wiki_excerpts: string[] | null,  // JIT-loaded from compiled/ for round N+1+
  round: integer
}

Output: StructuredFinding {
  task_id: string,
  agent_id: string,
  agent_type: string,  // template-based, not fixed enum
  condensed_summary: {  // 1,000-2,000 tokens enforced
    claims: [{
      text: string,
      evidence: string,
      citation_ids: string[],
      confidence: number(0-1),  // per-claim confidence score required
      caveats: string[]
    }],
    status: enum["complete", "partial", "gap_found"],
    gaps: string[],
    artifact_path: string  // path to full artifact in raw/
  },
  absence_report: string[],  // what was looked for but not found
  sources_consulted: integer,
  tokens_consumed: integer
}
```

**Acceptance criteria:**
- Agents operate in isolated working directories (cannot read each other's files)
- Each agent uses only its assigned 3-5 tools (enforced by MCP gateway)
- Findings include citations as required fields (structurally enforced, not prompt-based)
- Per-claim confidence scores are present on every claim (required for deliberation)
- Anti-confirmatory framing in task prompts produces balanced evidence
- Absence report is non-empty (agent reports what it looked for but didn't find)
- Condensed output is 1,000-2,000 tokens per agent (not raw data dumps); full artifact written to raw/
- Agent configs loaded from template registry, not from a fixed enum (custom templates generate correctly)
- Error recovery: if an agent fails, retry with exponential backoff; if retry fails, fall back down model chain; if 3 of 5 agents succeed, pipeline continues with partial results
- Iterative loop runs at least 2 rounds on a test engagement, stopping when quality gate met or cap reached

**Dependencies:** #1 (task schemas), #3b (wiki structure for JIT loading), #4 (MCP gateway), #5 (Specification Engine for task dispatch and template registry)
**Scope:** L+ (1-2 weeks)
**First test:** Dispatch 3 agents (Quantitative, Qualitative, Contrarian) on "Estimate TAM for L4+ AV sensor market." Verify isolation (agents can't see each other's work). Verify citations present on every claim with per-claim confidence scores. Verify Contrarian agent produces disconfirming evidence. Verify absence reports are non-empty. Verify condensed_summary is under 2,000 tokens and artifact_path points to a valid file in raw/. Simulate one agent failure; verify retry logic fires and partial-result continuation runs.

---

### #8: CitationProcessor

**What to build:**
- `src/citation/` module with:
  - `citation_processor.py` -- main processor
  - `deduplicator.py` -- merge citations referring to the same source across agents
  - `corroboration_scorer.py` -- score claims found independently by 2+ agents
  - `url_checker.py` -- URL liveness verification
  - `manifest_builder.py` -- produce citation manifest

**Input/output contract:**
```
Input:  AgentFindings[] (all StructuredFinding outputs from L1 agents)
Output: CitationManifest (per citation_manifest.schema.json)
        CorroboratedFindings[] {
          original_findings: StructuredFinding[],
          citations: Citation[] (deduplicated, verified),
          corroboration_pairs: [{ finding_a, finding_b, overlap_score }],
          dead_urls: string[],
          fabrication_flags: string[]
        }
```

**Acceptance criteria:**
- Deduplicates citations: same URL or DOI → merged, found_by_agents includes all agents
- Corroboration scoring: findings independently discovered by 2+ agents get elevated confidence
- URL liveness: checks all citation URLs, flags dead links
- Fabrication detection: flags citations with non-existent DOIs
- Content-hash provenance: each citation entry includes a content-hash for wiki compilation integrity (feeds #3b)
- Output conforms to citation_manifest.schema.json
- Fork candidate: SemanticCite evaluated as alternative to custom deduplication logic

**Dependencies:** #2 (citation data model), #7 (research agent outputs)
**Scope:** M (3-5 days)
**First test:** Feed 3 agents' findings (from #7 test). Two agents cite the same SEC filing (different URLs, same content). Verify deduplication merges them. One agent's citation has a dead URL. Verify it's flagged. Two agents independently found the same market size figure. Verify corroboration score is elevated. Verify content-hash is present on each citation entry.

---

### #9: Deliberation (L1.5)

**What to build:**
- `src/deliberation/` module with:
  - `deliberation.py` -- orchestrator for two-phase deliberation
  - `independent_analysts/` -- ACH, Quantitative, Adversarial, Historical Analogy (each a separate agent; each must produce per-claim confidence scores and source counts in output)
  - `aggregator.py` -- claim-level SELECTION aggregation (NOT synthesis/blending). Judge-based: evaluate competing claims, pick best-supported. 81% win rate vs. 51.2% for synthesis-based blending. Post-selection consistency check for incoherent selected claims. Opus model.
  - `wwhtb.py` -- "What Would You Have to Believe?" step for low-confidence findings (findings below confidence threshold trigger structured assumption elicitation)
  - `confidence_map.py` -- DiscoUQ-grounded five-tier confidence map builder
  - `gap_detector.py` -- identifies missing evidence, triggers additional research
  - `hitl_gate.py` -- triggers HITL database state machine review after confidence map is produced (Directive 7 Gate 2). System pauses; resumes on human approval.

**Input/output contract:**
```
Input:  CorroboratedFindings (from CitationProcessor)
        Each claim from L1 agents must include per-claim confidence score and source count.
Output: DeliberationResult {
  confidence_map: ConfidenceMap (five-tier JSON per Section 4.3),
  claims: Claim[] (per claim.schema.json; aggregated via claim-level selection),
  gap_report: string[],
  absence_report: string[],
  analyst_outputs: { [analyst_type]: AnalystOutput },
  wwhtb_outputs: [{ claim_id: string, assumptions: string[] }]  // for low-confidence findings
}

ConfidenceMap structure matches Section 4.3 JSON exactly.
Aggregation method: claim-level selection (judge picks best-supported claim for each disputed finding).
```

**Acceptance criteria:**
- 3-5 independent analysts produce assessments with no inter-agent communication
- Each analyst outputs per-claim confidence scores and source counts (required for selection aggregation)
- Aggregator uses claim-level selection, not synthesis/blending: for each disputed finding, the judge selects the best-supported claim rather than blending
- Post-selection consistency check: selected claims are screened for incoherence before output
- WWHTB step fires for any claim with confidence below 0.6 (low-confidence threshold)
- Curmudgeon challenge: every high-confidence finding has a non-trivial counter-argument
- Five-tier confidence map produced with all tiers populated
- At least one analyst runs on a different model family (cross-provider diversity)
- Claims output conforms to claim.schema.json with provenance chains
- HITL gate blocks execution after confidence map is produced; resumes on human approval

**Dependencies:** #8 (CitationProcessor output), #2 (claim schema), #HITL (database state machine)
**Scope:** L+ (1-2 weeks)
**First test:** Feed corroborated findings about AV sensor market. Verify: ACH analyst produces hypothesis matrix with per-claim confidence scores. Adversarial analyst surfaces disconfirming evidence. Aggregator uses selection (not synthesis) to resolve disputed findings -- log which source claim was selected and why. One low-confidence finding triggers WWHTB output. Confidence map has claims in 3+ tiers. Curmudgeon challenge is non-trivial for high-confidence claims. Pipeline pauses at HITL gate waiting for approval.

---

### #10: Evaluator Calibration

**What to build:**
- `calibration/` directory with:
  - `scoring_worksheet.md` -- 10-dimension scoring rubric for human evaluation (1-5 per dimension)
  - `calibration_samples/` -- 10+ scored sample outputs (Jack's scoring)
  - `canary_set/` -- 20-30 pre-scored samples for drift detection
  - `calibration_runner.py` -- compute Spearman correlation + Cohen's Kappa between human and automated scores
  - `per_dimension_calibration.py` -- identify systematic over/under-scoring per dimension

**Input/output contract:**
```
Input:  HumanScoredSamples[] {
  output_text: string,
  human_scores: { [dimension]: number(1-5) },
  human_overall: number(1-100)
}

Output: CalibrationReport {
  spearman_correlation: number,  // target: 0.80+
  cohens_kappa: number,  // target: 0.60+
  per_dimension_bias: { [dimension]: number },  // positive = overscoring
  calibration_ready: boolean  // true if spearman >= 0.80
}
```

**Acceptance criteria:**
- Spearman correlation >= 0.80 between automated and human scores on calibration set
- Cohen's Kappa >= 0.60
- Per-dimension bias identified and correction factors computed
- Canary set established for ongoing drift detection

**Dependencies:** #6 (evaluator stack), sample outputs from #7-#9 pipeline runs
**Scope:** M (1 week, but depends on Jack's scoring time)
**First test:** Score 10 pipeline outputs on the 10-dimension rubric. Run automated evaluator on same outputs. Compute Spearman correlation. If below 0.80, adjust Prometheus 2 prompts and re-run.

---

### #11: End-to-End Pipeline Test

**What to build:**
- `tests/e2e/` directory with:
  - `test_pipeline.py` -- full pipeline execution test
  - `test_questions/` -- 3-5 test research questions with expected quality characteristics
  - `quality_report.py` -- generates quality report from evaluator output

**Input/output contract:**
```
Input:  Research question (string)
Output: PipelineResult {
  research_md: RESEARCH.md,
  tasks: research-tasks.json,
  findings: StructuredFinding[],
  citation_manifest: CitationManifest,
  deliberation_result: DeliberationResult,
  evaluation_result: EvaluationResult,
  final_output: string (Markdown),
  pipeline_metrics: {
    total_time_seconds: number,
    total_tokens: number,
    total_cost_usd: number,
    agents_dispatched: number,
    citations_total: number,
    citations_verified: number,
    citations_fabricated: number,
    evaluator_score: number
  }
}
```

**Acceptance criteria:**
- Pipeline runs end-to-end without manual intervention (except HITL gate approvals)
- Iterative research loop runs at least 2 rounds on the test engagement (multi-round coverage required)
- HITL gates exercised: both Gate 1 (post-Spec Engine) and Gate 2 (post-Deliberation) fire, accept approve/modify/reject input, and resume/halt pipeline correctly
- Information fidelity check: 37% retention failure does not occur. Validate by tracing at least 5 key claims from final output back to source artifacts in raw/ -- all 5 must be traceable with content preserved.
- Output scores >= 60/100 on the 10-dimension rubric (baseline -- improvement expected with calibration)
- Zero fabricated citations (binary gate holds)
- All claims trace to citations
- Pipeline completes in < 30 minutes for a 10-task engagement
- Cost per run is within the $12-$100 validated range

**Dependencies:** All above (#1-#10)
**Scope:** M (3-5 days)
**First test:** "Evaluate the competitive position of Luminar Technologies in the autonomous vehicle lidar market." Full pipeline. Score the output. Generate the quality report. Verify the pipeline ran at least 2 research rounds. Manually approve both HITL gates. Verify information fidelity on 5 sampled claims.

---

## "Done" Criteria for Phase 1

Phase 1 is complete when ALL of the following are true:

1. **Pipeline runs end-to-end:** A research question enters and a scored Markdown output exits, with no manual intervention except HITL gate approvals
2. **Citation integrity holds:** Zero fabricated citations in 5 consecutive test runs (Layer 2 binary gate enforced)
3. **Evaluator is calibrated:** 0.80+ Spearman correlation on a calibration set of 20+ human-scored outputs
4. **Isolation is structural:** Research agents demonstrably cannot access each other's findings (tested via intentional cross-read attempt)
5. **Quality is measurable:** Every output has a 10-dimension score (Tier 1 + Tier 2), per-dimension feedback, and actionable regeneration guidance
6. **Handoff contracts enforced:** PydanticAI schema validation rejects malformed data at every pipeline boundary
7. **Cost is viable:** Average engagement cost is within the $12-$100 range
8. **The existence proof works:** At least one test engagement produces output that Jack rates as "approaching Keystone quality" (>= 70/100 on his manual scoring)
9. **HITL gates function correctly:** Both Gate 1 (post-Spec Engine) and Gate 2 (post-Deliberation) correctly block, resume on approval, apply modifications on modify, and halt on reject -- tested end-to-end
10. **Iterative research loop runs:** At least one test engagement completes a 2+ round iterative research loop, with round 2 producing demonstrably different/expanded findings than round 1

Phase 1 is NOT complete if:
- The evaluator approves outputs with fabricated citations (binary gate failure)
- Agents can access each other's intermediate work (isolation failure)
- The pipeline requires manual intervention beyond HITL gate decisions (automation failure)
- Evaluator scores don't correlate with Jack's human scoring (calibration failure)
- HITL gates cannot block and resume pipeline execution (HITL failure)
- The pipeline only runs one research round on multi-round-eligible engagements (iterative loop failure)
