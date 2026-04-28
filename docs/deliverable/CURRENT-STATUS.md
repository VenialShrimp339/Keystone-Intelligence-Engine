# Current Status

**Last updated:** April 28, 2026

---

## The Headline

The pipeline architecture is complete and all layers execute with real LLM calls. The first run produced impressive Specification Engine and Research output — particularly the MECE issue tree and Day-1 Hypothesis. The system has not yet completed a full end-to-end run: L0 and L1 completed, but downstream layers (deliberation, evaluation, rendering) have not yet finished a successful pass on real data due to timeout issues that are being actively fixed.

---

## What's Built

| Component | Tests | Status |
|-----------|-------|--------|
| Specification Engine (L0) | 99+ | Built, runs on real data successfully |
| Research Agents (L1) | 92+ | Built, deep research mode produces real findings |
| Citation Processor | 28+ | Built, URL verification working |
| Deliberation (L1.5) | 93+ | Built, times out on real data (being fixed) |
| Content Structuring (L2) | 31+ | Built, not yet tested on real data |
| Evaluator (L4, 5-layer stack) | 93+ | Built, not yet tested on real data |
| Cross-Model Ensemble (L5) | 99+ | Built, unit tested only |
| MCP Gateway | 145+ | Built (auth, rate limiting, circuit breaker) |
| HITL Infrastructure | 42+ | Built, database state machine |
| Retrieval Stack | 123+ | Built (pgvector + Voyage + BM25 + Cohere rerank) |
| Pipeline Orchestrator | 13+ | Built, end-to-end wiring with checkpointing |
| Markdown Renderer | 31+ | Built, outline-driven section rendering |
| **Total** | **1,584** | All passing (~57 seconds) |

The codebase spans 129 Python source files across `src/keystone/`. The pipeline is driven by 38 `.md` prompt files and 8 inline Python prompt templates (46 total).

A systematic prompt audit found: 15 prompts are fully domain-neutral, 12 are partially biased toward consulting language, and 11 are consulting-specific. The evaluator rubric headers have been de-biased. The deliberation layer (8 prompts) is fully domain-neutral. The remaining consulting-specific prompts are known and tracked for remediation.

---

## Pipeline Run Results

### Test Question

> *"Evaluate the competitive landscape of the US auto body repair industry across the top 10 metropolitan areas by population. Identify the largest chains, their market share, and whether the market is consolidating or fragmenting. What would a new entrant need to know?"*

This was chosen as the second test question because it's a consulting-style business question that fits the system's current strengths. An earlier run (~April 22-23) against a software architecture question exposed that the hardcoded financial/operational/market analytical lenses produce nonsensical branches for non-business questions — financial analysis of a software architecture problem, for instance. That earlier run was the catalyst for the domain classification work described below.

### L0: Specification Engine (Completed Successfully)

**Dual-axis classification:**
- Analytical mode: evaluative
- Pipeline profile: standard

**Day-1 Hypothesis** (generated before any research):

> "The US auto body repair industry in the top 10 MSAs is in mid-stage PE-driven consolidation, with the top 4 chains (led by Caliber Collision) collectively controlling 20-30% of metro-level collision repair revenue but facing a durable independent-shop majority sustained by insurer DRP breadth requirements and rising OEM certification specialization — making acquisition-based entry viable but at elevated multiples (10-14x EBITDA) while de novo entry is prohibitively capital-intensive for any single metro."

This hypothesis is notable because it was generated entirely from the question with no prior research. The system inferred three specific, testable claims: (1) PE consolidation at a specific share level, (2) DRP breadth requirements as a structural protection mechanism, and (3) a specific EBITDA multiple range. The L1 research agents subsequently found real evidence bearing on all three claims.

**Surprising Finding** (also generated pre-research):

> Despite a decade of PE-backed roll-up activity, the top-5 chain share has plateaued near 20-25% because the three largest auto insurers actively counter-consolidated their DRP networks — expanding preferred-shop panels to include more independents as a check on chain pricing leverage — while OEM-certified independents captured disproportionate share of the EV and ADAS repair segments, bifurcating the market into a commodity tier (chains) and a premium tier (specialized independents).

**Issue Tree:** The decomposer ran three lenses (financial, operational, market) in parallel, then a FLAGSHIP-tier synthesis model merged them into a unified tree:

| Branch | Topic | Leaves |
|--------|-------|--------|
| 1 | Market Size, Segmentation & Competitive Concentration | 2 |
| 2 | Demand Routing: Insurer & OEM Intermediary Power | 2 |
| 3 | Shop-Level Unit Economics & Scale Advantages | 2 |
| 4 | Workforce Constraints & Operational Barriers | 2 |
| 5 | Entry Economics, Valuation & Roll-Up Execution | 3 |
| 6 | Revenue Growth & Technology Disruption Vectors | 2 |

The synthesis rationale (preserved in the JSON metadata) documents six specific cross-lens merges, three hypothesis-critical node promotions, and the reasoning for folding environmental compliance into workforce rather than giving it a standalone branch. This is the system's "casing phase" — analogous to how McKinsey consultants structure novel problems before doing research.

**Task Generation:** 13 research tasks, each containing:
- Description (~80-120 words) with named entities and specific data points to seek
- 5-6 acceptance criteria with falsifiability conditions
- Anti-confirmatory framing specifying what evidence would *disprove* the Day-1 Hypothesis
- Named source requirements (e.g., "CCC Crash Course annual reports," "Boyd Group SEC filings (TSX: BYD)")
- Tool assignments (exa_search, brave_search, edgar_filings, etc.)
- Issue tree branch mapping and priority ranking

### L1: Deep Research (6 of 13 Agents Completed)

The auto body repair run used deep research mode (`DEEP_RESEARCH=1`), where each agent runs a single `claude -p` session with WebSearch and WebFetch capabilities. Six of thirteen agents completed before the Claude Max daily usage limit was reached. The remaining seven agents never started.

| Task | Topic | Claims | Confidence Range |
|------|-------|--------|-----------------|
| task_004 | Entry capital requirements (acquisition vs greenfield) | 27 | 0.45 – 0.85 |
| task_005 | OEM certification as competitive moat | 25 | 0.65 – 0.88 |
| task_006 | Shop-level unit economics | 26 | 0.70 – 0.95 |
| task_008 | Claim frequency & repair complexity trends | 24 | 0.52 – 0.88 |
| task_012 | Training infrastructure & workforce development | 28 | 0.68 – 0.93 |
| task_013 | ADAS/EV impact on competitive structure | 25 | 0.75 – 0.95 |

**Aggregate research output:**
- 155 structured claims, each with confidence score, tier classification, and explicit caveats
- Overall confidence range: **0.45 – 0.95**
- 173 real URLs from 107 unique domains
- 16 dead URLs correctly detected by the Citation Processor
- 0 fabricated citations flagged
- Sources include SEC filings (Boyd Group, Driven Brands), industry trade publications (CCC, Repairer Driven News, BodyShop Business), Fortune, Focus Advisors M&A reports, state regulatory databases (California BAR, Philadelphia L&I), academic research, and EPA archives

**Example finding** (from task_006, unit economics):

> "Chain-operated collision repair shops (Big Five) generate approximately $4.0–4.2M in annual revenue per location, roughly 3x the $1.2–1.25M average for smaller independent or dealer-owned body shops."
>
> Cited from Focus Advisors 2024 data ("scaled MSO shops averaging $3.85M revenue per 12,000 sq ft"), Boyd Group annual reports, and Crash Champions Fortune profile ("more than 650 locations and $2.75 billion in revenue"). Confidence: 0.82. Caveats: per-location figures are derived by dividing aggregate disclosures by shop count; significant variance exists within the independent category.

### Downstream Layers (Not Yet Completed on Real Data)

**Citation Processor: Completed.** Processed 173 citations, deduplication via union-find on URLs, flagged 16 dead URLs. No `ref://` placeholder contamination (a prior bug, fixed in commit `4a0dc33`).

**Deliberation (L1.5): Timed out.** All four analyst agents (ACH, quantitative, adversarial, historical analogy) exhausted 3 retry attempts each, timing out at 600 seconds per attempt. Root cause: 155 claims across 6 task findings is more data than the analysts can process in the configured timeout window. The most recent commit (`38c5e87`) raised regular call timeouts from 600s to 1200s. The next run should get past this bottleneck.

**L2, L4, Renderer: Blocked** by the deliberation timeout. These components are built, unit-tested, and waiting.

---

## What Changed Since April 9

The previous document Prof. Youle received (April 9) described the architecture and 825 unit tests. Since then:

**Test count:** 825 → 1,584 (+759 tests, +92%)

**Major capabilities built since April 9:**

- **L5 cross-model ensemble evaluation** — 2-3 independent judges score in parallel, median aggregation, minority dissenter veto on Tier 1 dimensions
- **L4 process trajectory assessment** — evaluates how agents worked (tool utilization, source diversity, round count, issue tree coverage), not just what they found. Blended with L3 rubric scoring at 80/20 weighted geometric mean.
- **Full retrieval stack** — PostgreSQL 17 + pgvector 0.8.2, Voyage Finance embeddings (1024-dim), BM25 index, hybrid search with reciprocal rank fusion, Cohere rerank-v3.5. Per-engagement inter-agent isolation.
- **L2 content structuring** — framework selection, sprint contract generation, per-task section text drafting, outline construction
- **EDGAR gateway** — SEC filing access (company facts, financials, filings search)
- **Docling backend** — PDF and article parsing for evidence normalization
- **Pipeline configuration system** — per-layer model tiers, per-layer reasoning effort levels (L0 spec at xhigh, L4 evaluator at high, extraction at low), research concurrency, quality thresholds
- **Dual-axis domain classification** — engagement type + subject domain, with downstream adaptation of methodology, source requirements, non-goals, and analytical frameworks
- **Checkpoint/resume** — 5 stage boundaries persisted to SQLite, resume from any checkpoint after crash
- **Intermediate artifact output** — each pipeline layer writes results to `output/{engagement_id}/`
- **Prompt audit** — systematic review of all 38 prompt files, de-biased 15 consulting-specific headers, expanded deliberation analyst prompts from 2-3 sentences to 15-30 sentences with genuine analytical procedures
- **Two real pipeline runs** — one against a software architecture question (exposed domain mismatch), one against auto body repair (produced the output in SAMPLE-OUTPUT/)

---

## Quality Gap: Pipeline Output vs. Benchmark

The honest assessment: the pipeline's L0 specification output is genuinely impressive. The L1 research output finds real data with real sources. But the quality gap between pipeline output and the benchmark (MBB-grade analysis produced by manual Claude deep research sessions) is significant, and the root causes are well understood.

**What the benchmark produces:**
- A synthesizing thesis that organizes all findings ("every open-source system enforces quality through prompts, not architecture")
- Deep per-entity analysis at 1-2 paragraphs each with strategic implications
- Cross-entity pattern recognition
- Specific implementation guidance (USE/LEARN/SKIP decision matrices)
- 5,000-word narrative briefs with Situation-Complication-Resolution structure

**What the pipeline currently produces:**
- 155 flat structured claims at 2-4 sentences each
- No synthesizing thesis
- No cross-claim pattern recognition (each agent works in isolation)
- Rendered markdown from structured data, not flowing analytical prose

**The gap is structural, not a model capability problem.** Both use Claude. The three root causes:

1. **Task description depth** (highest leverage) — L0 generates ~80-120 word task descriptions. The benchmark research prompts that produced MBB-grade output were ~800 words each, with named entities to investigate, per-entity sub-questions, quantitative benchmarks to seek, and focal synthesis questions. This single gap accounts for an estimated 50-60% of the quality difference.

2. **No narrative synthesis layer** — there is no component between L1 and L1.5 that takes flat claims and produces a cross-cutting thesis, hierarchical claim structure, or analytical argument. This is why the pipeline produces "155 JSON claims" rather than "one analytical brief."

3. **Hardcoded analytical lenses** — the three lenses (financial, operational, market) are consulting-domain defaults. They worked for the auto body repair question but produce nonsensical decompositions for non-business questions. A dynamic lens selection system is designed but not yet built.

These are all fixable within the existing architecture. The handoff contracts and pipeline structure were designed to accommodate these improvements without requiring rework — that was an explicit design goal.

---

## What's Next

In priority order:

1. **Complete a full end-to-end run** — the 1200s timeout fix should unblock deliberation. This is the immediate goal.
2. **Task specification depth** — richer task descriptions with named entities, sub-questions, and focal synthesis questions. Highest-leverage quality improvement.
3. **Dynamic lens selection** — replace hardcoded financial/operational/market with domain-appropriate lens selection.
4. **Narrative synthesis layer** — convert flat claims into analytical hierarchy before deliberation.
5. **Interactive clarification loop** — ask clarifying questions before decomposition for ambiguous input.
6. **Iterative research** — gap-fill cycles after L1 completes, so unresolved questions spawn additional research.
