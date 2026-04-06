# Keystone Intelligence Engine -- Cowork Session History (Condensed)

> **Purpose:** This document condenses ~60 pages of Cowork chat history into the essential context needed for agent handoffs. It covers every architectural decision, session output, and open item from the project's planning phase. Organized thematically, not chronologically, with chronological detail within sections where sequence matters.
>
> **Who this is for:** A new Claude Cowork or Claude Code session picking up this project. Read CLAUDE.md first (auto-loaded in Claude Code), then this document for full project history and state.

---

## 1. PROJECT OVERVIEW

**Keystone Intelligence Engine** is a multi-agent AI system that automates consulting research at Keystone Group (management consulting firm). Jack Riddle's capstone project at IU Kelley School of Business. Being built as a real product, not an academic exercise. ~6 weeks of discretion from Prof. Youle. Jack starts at Keystone Group in July 2026.

**Core thesis:** The harness matters more than the model. The same model scores 17% vs 92% depending on the harness (LangSmith/Claude Code empirical data). Value accrues to the specification layer, evaluation architecture, and accumulated institutional knowledge -- not to model access, which is a commodity.

**Architecture:** 6-layer DPVI (Decompose-Parallelize-Verify-Iterate) pipeline with a META self-improvement loop:

- **L0: Specification Engine** -- Vague question → intent clarification → RESEARCH.md spec → agent dispatch. This layer IS the system. Quality ceiling = specification quality.
- **L1: Parallel Research Agents** -- Fan-out across data sources, strict isolation, JIT context, anti-confirmatory framing. 4-5 agent types (Quantitative, Qualitative, Contrarian, Historical Analogy, Internal Document).
- **CitationProcessor** (added post-research) -- Discrete stage between L1 and L1.5. Deduplicates citations, scores cross-agent corroboration, verifies URL liveness, checks DOIs against CrossRef/Semantic Scholar.
- **L1.5: Deliberation** -- REDESIGNED from debate to independent parallel analysis + structured aggregation (see Section 3).
- **L2: Content Structuring** -- Receives claim-level intermediate representations (not raw agent output). Applies consulting analytical frameworks. Sprint contracts with Evaluator.
- **L3: Generation** -- Deliverable production (PowerPoint, Excel, briefs) in Keystone format. Every finding pre-tagged with deliverable destination.
- **L4: Evaluator** -- OVERHAULED to five-layer stack (see Section 3). The most important component in the system.
- **META: Self-Improvement** -- Observation Library (expanded from Rejection Library), Darwinian prompt evolution, trajectory storage, client calibration profiles.

**Deployment target:** Claude Max plan with minimal external APIs. Opus for L0/L4 judgment work, Sonnet for L1 throughput, Haiku for extraction. Prometheus 2 (7B, runs locally on Mac Mini) for rubric evaluation. Cost target: $12-$100/engagement.

---

## 2. CLAUDE.MD AND PROJECT FILE SETUP

### What happened

The project started with an OpenClaw-generated CLAUDE.md that was 146 lines of project brief prose -- thesis statements, evidence tables, bio section. This violated every published best practice from Boris Cherny (Claude Code creator) and Anthropic's docs.

### Key decisions made

1. **CLAUDE.md restructured to ~90 lines of behavioral rules only.** Removed: project brief content, 4-phase task description, verbose file guides, "About Jack" section. Kept: project structure map, architectural convictions, working rules, evidence standards, pipeline reference, empirical anchors, key terms.

2. **Skills and agents created:**
   - `.claude/skills/research-synthesis/SKILL.md` (74 lines) -- 4-phase methodology, thread map, output standards, evidence tiers. Loads on demand.
   - `.claude/skills/architecture/SKILL.md` (81 lines) -- 6-layer pipeline deep reference, handoff contracts, design principles. Loads on demand.
   - `.claude/agents/research-analyst.md` (50 lines) -- Opus-model thread analysis agent with restricted tools and defined workflow.
   - `.claude/agents/synthesis-lead.md` -- Single synthesis agent that reads all thread analyses, updates plan, writes changelog.

3. **settings.json configured:** Opus 4.6 default model, effortLevel: high, Haiku remapped to Sonnet, subagent default Sonnet (overridden to Opus in agent frontmatter). CLI fallback: `claude --model claude-opus-4-6` then `/effort high`.

4. **Custom instructions integrated into CLAUDE.md:** Lead with answer, take positions, steel-man before concluding, no em dashes/sycophantic openers/corporate filler, propose redesigns not hotfixes, try alternatives before reporting limitations. Mobile-dictation handling and chat tone preferences excluded (irrelevant for Claude Code).

5. **Boris Cherny's core principle adopted:** Error-driven iteration. Start minimal, run tasks, add corrections from actual failures. The CLAUDE.md is designed to grow from ~90 lines based on real error patterns, not speculative instructions.

6. **Verdict taxonomy standardized:** ADOPT / ADAPT / SKIP / INVESTIGATE (matching what all analysis files actually use). Earlier versions used BUILD/INTEGRATE/LEARN/SKIP -- this was updated for consistency.

7. **Deployment context added to CLAUDE.md:** Claude Max target, model mixing strategy, cost target, parallelism constraints.

### Current CLAUDE.md state
~90 lines. Includes: project structure, pipeline summary with CitationProcessor and claim-level handoffs, 5 empirical anchors (17%→92%, 96.5% SpreadsheetBench, 29-30% false claims, 68.8% AgentLeak leakage, 78% vs 42% harness comparison), key terms (including CitationProcessor and Observation Library), deployment context, communication/output rules, working rules.

---

## 3. THE 17 RESEARCH-BACKED PLAN CHANGES

### Research synthesis process

16 deep research reports were produced from prompts in RESEARCH-PROMPTS-FINAL.md, organized into 4 threads:
- **Thread A (Reports 1-5):** Open source landscape, evaluation frameworks, self-improvement, orchestration, deep research tooling
- **Thread B (Reports 6-9):** What senior consulting partners value, decision-useful research, quality of thought, AI failure modes
- **Thread C (Reports 10-13):** Specification-driven development, deliberation, report generation, data retrieval architecture
- **Thread D (Reports 14-16):** Best individual/small-team AI systems, academic papers, 10x ideas

Claude Code ran 4 parallel Opus subagents (one per thread) for analysis, then a single synthesis agent read all outputs and updated the plan. This hybrid approach was chosen because: (a) full parallel (16 agents, one per report) means no coordination and merge conflicts; (b) full sequential means context saturation by report 12. The hybrid parallelizes analysis (independent reads against immutable plan) while keeping synthesis atomic (one agent sees all patterns before touching the plan).

### The changes, grouped by pipeline area

#### Evaluator Overhaul (Changes 4, 5, 6, 7, 8) -- Largest cluster

**Original:** Single LLM judge with 8-dimension rubric.

**What research found:** SOS-Bench (ICLR 2025, 152K data points) proved single LLM judges systematically reward style over substance -- sarcasm causes 96% scoring loss while factual errors cause only 13% loss. "Play Favorites" (2025) identified the causal mechanism: models score their own outputs higher due to lower perplexity. Single LLM judge ceiling: 60-68% agreement with domain experts. Evaluation is ~65% dimensional and ~35% holistic "taste."

**Changes applied:**
- **Change 4: Five-layer evaluator stack.** Layer 1: deterministic checks (FActScore, URL liveness, numerical consistency). Layer 2: citation validation binary gate (fabricated citation = immediate rejection). Layer 3: multi-rubric scoring via Prometheus 2, one prompt per dimension. Layer 4 (Phase 2): process trajectory evaluation. Layer 5 (Phase 2): cross-model ensemble with minority-veto.
- **Change 5: 10-dimension rubric.** Added Evaluative Surprise (5%) and Calibrated Confidence (5%). Rebalanced weights away from where LLMs naturally excel (coherent prose, coverage) toward where they underperform (analytical novelty, quantitative rigor, actionable insight). Added sub-criteria: trendslop detection in Actionability, deletion test in Completeness.
- **Change 6: Calibration target.** 0.80+ Spearman rank correlation on 100-200 expert-scored samples as binary production gate. Anthropic's own standard.
- **Change 7: Three-pass evaluation.** Pass 1: dimensional rubric scoring. Pass 2: holistic gestalt overlay (+-5-10%). Pass 3: Observation Library negative-space scan (inactive until Phase 2 -- Evaluator Pass 3 depends on a populated Observation Library which doesn't exist yet).
- **Change 8: Cross-model evaluation requirement.** Prometheus 2 (local 7B) provides cross-model diversity without external APIs. Layer 5 ensemble deferred or simplified to single external model call per engagement.

**Assessment from Cowork session:** Well-grounded changes. Five-layer stack is ambitious for Phase 1 but impl spec correctly defers Layers 4-5. Evaluative Surprise is the most subjective dimension -- watch for signal vs noise in practice.

**Evidence caveats from audit (none change architecture but worth knowing):**
- The martingale claim about debate is the empirical finding, not the mathematical theorem itself (acceptable framing)
- SOS-Bench doesn't directly test decomposed evaluation -- the inference that decomposition fixes the bias is sound but is interpretation, not proof
- The 60-68% expert agreement figure is Credible tier, not Verified (single source flags it as unverified)
- Goodhart 19.3% is a sampling frequency from the research, not a general rate
- "50 tools vs 5 tools" quote correctly traces to Report A5, not A4 (changelog attribution was wrong)
- DMAD attribution in the changelog was wrong (D2, not C2) -- changelog-only issue, plan is correct

#### Deliberation Redesign (Changes 2, 3) -- Most controversial change

**Original:** Structured multi-perspective debate with bull/bear/contrarian/consensus personas debating through multiple rounds.

**What research found:** NeurIPS 2025 Spotlight paper *formally proved* (mathematical proof, not empirical) that multi-agent debate forms a martingale -- expected value doesn't improve with additional rounds. Majority voting alone (0.7691) outperformed best debate variant (0.7377). Wu et al.: majority pressure suppresses independent correction below 5%. Google DeepMind (180 configurations): unstructured multi-agent networks amplify errors 17.2x. DMAD (ICLR 2025): methodological diversity consistently outperforms persona diversity.

**Changes applied:**
- **Change 2: Two-phase deliberation.** Phase 1: independent parallel analysis -- 3-5 new analyst agents each apply a fundamentally different analytical methodology (ACH, Quantitative, Adversarial, Historical Analogy, Scenario Planning) with zero inter-agent communication. Agent identifiers stripped from findings. Phase 2: single Opus aggregator reads all independent analyses simultaneously, identifies convergent findings, genuine disagreements, methodological blind spots. One curmudgeon challenge per high-confidence finding. No iterative debate rounds.
- **Change 3: Five-tier confidence map.** Based on DiscoUQ (0.802 AUROC for disagreement detection). Tiers: >80%, 60-80%, 50-60%, <50%, Insufficient Evidence. ACH matrix as structural backbone.

**Assessment:** Evidence is strong (NeurIPS Spotlight with formal proof). Original debate design would have degraded quality with every iteration. Cross-provider model diversity (Claude + GPT + Gemini) was originally required for deliberation but Jack decided to remove it -- wants Claude Max with minimal external APIs. Methodological diversity alone should be sufficient; validate empirically.

#### Data Pipeline (Changes 1, 12, 17)

- **Change 1: CitationProcessor** added between L1 and L1.5. Deduplicates citations, scores cross-agent corroboration, verifies URL liveness, checks DOIs. Based on Anthropic's own production pattern (90.2% improvement). PROV-AGENT W3C data model.
- **Change 12: Full retrieval architecture.** pgvector + pgvectorscale, hybrid search (dense + BM25 + RRF), Semantic Router (<5ms query classification), Docling for structure-aware PDF parsing (87.7% accuracy), Bifrost dual-layer caching. Search API stack: Exa, Brave Search, Firecrawl, Tavily.
- **Change 17: Claim-level handoffs.** L1→L2 handoff operates at claim level. Each claim is structured JSON with source_chunk_ids, confidence score, corroboration count, provenance chain. Based on Microsoft Research ICLR 2026 finding that deep research quality depends on claim-level intermediate representations, not report length. Systems that separate claim synthesis from report generation produce higher-quality output.

**Assessment:** All solid. Retrieval architecture is detailed but aggressive -- MVP should be Exa + Brave + pgvector, add rest incrementally.

#### Agent Architecture & Orchestration (Changes 10, 11)

- **Change 10: Isolation strengthened.** AgentLeak benchmark (4,979 traces): 68.8% inter-agent data leakage in standard frameworks, 46.7% from shared memory. Per-agent working directories with advisory file locks, write-ahead logging, 3-5 domain-specific tools per agent, model mixing strategy.
- **Change 11: Custom orchestration.** PydanticAI for type-safe agent contracts, Temporal for durable execution with crash recovery, MCP for tool integration via gateway, AG-UI for output streaming. No existing framework meets the combination of strict isolation + reject/regenerate + handoff contracts + filesystem-as-state.

#### Meta-Layer & Supporting Changes (Changes 9, 13, 14, 15, 16)

- **Change 9: Rejection Library → Observation Library.** Captures successes AND failures. Three-category taxonomy (structural, analytical, judgment). Five saturation-breaking mechanisms to prevent plateau after 2-3 iterations.
- **Change 13: Task-type field.** Estimative vs current tasks get different evaluator weight profiles. Based on ICD 203 intelligence standards.
- **Change 14: Causal inference as Phase 2 capability.** CausalAgent (ACM IUI 2026) + DoWhy library. L2 designed in Phase 1 to accept causal analysis as input type.
- **Change 15: Anti-slop enforcement.** Antislop Sampler (8K+ pattern library, 90% slop reduction). Triggers Redraft Specialist subagent. Detection: generic openings, listicle structures, excessive hedging, buzzwords.
- **Change 16: Cost model validated.** $12-$100/engagement fully loaded. Verification consumes 72% of tokens. 0.3-3% of engagement revenue.

### Smell test results (Cowork assessment)

**Clearly right:** Five-layer evaluator, citation binary gate, deliberation redesign (formal proof), cross-model evaluation, claim-level handoffs, Observation Library, custom orchestration, agent isolation.

**Sound but aggressive for 6-week build:** Full retrieval architecture (4 providers + 2 embedding models + 2 rerankers), Evaluative Surprise dimension, full three-pass evaluation.

**Missing from the plan:** No explicit latency budgets. Implementation spec says "<30 minutes for 10-task engagement" but the plan doesn't frame latency as a design constraint.

---

## 4. SESSION OUTPUTS AND FILE MAP

### Claude Code Session 1: Research Synthesis
**Task:** Analyze 16 research reports, synthesize findings, update plan.
**Outputs:**
- `synthesis/` directory with per-report analyses (A1-analysis.md through D3-analysis.md)
- `synthesis/thread-a-summary.md` through `thread-d-summary.md`
- `synthesis/UNIFIED-SYNTHESIS.md` -- Cross-thread findings, ~80 tool verdicts, 6 contradiction resolutions, 8 gaps, implementation priority
- `synthesis/PLAN-CHANGELOG.md` -- 17 documented changes with section/what/why/evidence/confidence/enables
- `CAPSTONE-PLAN-v2.md` -- Updated with all 17 changes. Grew from 1,051 to 1,294 lines. 31 [SYNTHESIS UPDATE] tags for traceability.

### Claude Code Session 2: Audit + Implementation Spec
**Task:** Verify plan consistency, triage gaps, produce implementation spec, create session context.
**Outputs:**
- 3 stale references fixed in CAPSTONE-PLAN-v2.md (deliberation terminology, rubric dimension count)
- 6 evidence caveats documented (none change architecture)
- `audit/GAP-TRIAGE.md` -- 8 gaps triaged. No Phase 1 blockers. 2 resolved in-place (canary set for drift detection, updated cost model). External dependency: Jack provides 10+ past deliverables with quality scores for evaluator calibration.
- `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- 11 components specified with schemas, acceptance criteria, build order. MVP: 2-3 agents, 2 search APIs, single aggregation, Layers 1-2 eval, Markdown output.
- `audit/SESSION-CONTEXT.md` -- 66-line briefing doc (NOW STALE -- predates overnight analysis and scaffolding sessions).

### Claude Code Overnight Session: nano-claude-code Analysis
**Task:** Methodically analyze entire nano-claude-code Python reimplementation (56 files, 11,833 lines) against Keystone's architecture.
**Outputs (in `reference/analysis/`):**
- `00-master-index.md` (108 lines) -- Quick-reference tables, top 5 findings, component mapping
- `01-core-architecture.md` (262 lines) -- Agent loop, compaction, config, DPVI mapping
- `02-tool-system.md` (314 lines) -- ToolDef registry, per-agent subsetting, output truncation
- `03-multi-agent.md` (529 lines) -- HIGHEST VALUE: isolation, spawning, coordination, security analysis
- `04-task-management.md` (234 lines) -- Dependency graph, thread safety, research-tasks mapping
- `05-memory-context.md` (455 lines) -- HIGHEST VALUE: Observation Library mapping, JIT loading, compaction
- `06-mcp-implementation.md` (488 lines) -- Complete MCP client reference for Component #4
- `07-skills-plugins.md` (192 lines) -- Consulting methodology skill definitions
- `08-emergent-patterns.md` (213 lines) -- 10 cross-cutting patterns, anti-patterns
- `09-implementation-recommendations.md` (269 lines) -- All 11 components mapped, architecture validated

**Top 5 findings:**
1. Generator-based agent loop (175 lines) is the right orchestration primitive -- ADOPT for all pipeline stages
2. Thread-level isolation is INSUFFICIENT -- must use process-level isolation (validates AgentLeak findings)
3. MCP gateway is fully tractable (~850 lines working client) -- direct reference for Component #4
4. Two-layer compaction handles long research sessions (rule-based snipping first, LLM summarization second)
5. AgentDefinition from markdown with YAML frontmatter enables rapid agent specialization

**Architecture verdict:** No plan changes needed. Codebase validates all existing decisions. Concrete implementation patterns for Components #4, #5, #7, #9, #11.

### Deep Research Reports (10 parallel agents)
**Task:** Research community discoveries from the full 512K-line Claude Code TypeScript leak.
**Outputs:** 10 reports in `reference/analysis/` with opaque `compass_artifact_*` filenames (~1,385 lines total). **These have NOT been renamed or synthesized yet.**

**Topics covered:**
1. Agent Teams architecture (coordination, isolation, execution models: Fork/Teammate/Worktree)
2. Context engineering and compaction (MicroCompact/AutoCompact/Full Compact, 93.5% trigger threshold)
3. Tool system design patterns
4. Harness architecture (system prompt + orchestration loop, 785KB main.tsx)
5. Evaluation, quality gates, hooks system
6. MCP implementation and gateway patterns
7. Self-improvement, KAIROS/autoDream, knowledge accumulation
8. Cost optimization (prompt caching, model mixing, token economics)
9. Community analysis landscape (claw-code, nano-claude-code, all rewrites)
10. Official Anthropic Agent SDK and production patterns

### Claude Code Scaffolding Session
**Task:** Synthesize deep research reports against repo analysis, design code architecture, produce foundational Pydantic models and project scaffolding.
**Status: UNCLEAR -- contradictory signals in chat history.** The Cowork session initially stated "The synthesis session never ran" and that the prompt was ready but not executed. Later messages reference Claude Code having "wrapped up" and discuss its output. The prompt exists at `SYNTHESIS-AND-SCAFFOLDING-PROMPT.md` (audited, 17 issues found and fixed). **Verify actual state by checking whether `src/` contains scaffolding, whether `LEAK-SYNTHESIS.md` exists, and whether `SESSION-HANDOFF-SCAFFOLDING.md` was produced.**

### Key files created by Cowork session (not Claude Code)
- `KICKOFF-PROMPT.md` -- Session 1 and 2 prompts
- `reference/OVERNIGHT-ANALYSIS-PROMPT.md` -- 10-phase autonomous analysis prompt (audited, 14 issues found and fixed)
- `reference/DEEP-RESEARCH-PROMPTS.md` -- 10 parallel deep research prompts with project file references
- `reference/PROJECT-CUSTOM-INSTRUCTIONS.md` -- Custom instructions for deep research project
- `SYNTHESIS-AND-SCAFFOLDING-PROMPT.md` -- Scaffolding session prompt (audited, 17 issues found and fixed)

---

## 5. CLAUDE CODE SOURCE LEAK -- KEY FINDINGS FOR KEYSTONE

### State of the leak
March 31, 2026: Anthropic shipped 59.8MB source map (`cli.js.map`) in npm v2.1.88. Missing `.npmignore` entry. 512K+ lines of TypeScript across ~1,900 files. Anthropic issued DMCA takedowns (overshot to 8,100+ repos, retracted most). Primary rewrite: **claw-code** by Sigrid Jin (Python + Rust, 100K+ stars). **nano-claude-code** (~5,000 lines Python, analyzed overnight).

### Architecturally significant discoveries mapped to Keystone

**Agent Teams (applicable to L1 parallel research agents):**
- Three execution models: Fork (inherits parent context, prompt caching makes 5 agents cost ~1), Teammate (independent context, parallel, JSON inbox messaging), Worktree (isolated git worktree).
- Coordination: shared task list with dependency tracking, file locking for race conditions, automatic unblocking on dependency completion.

**Context Management (applicable to JIT context loading):**
- Three-layer compression: MicroCompact (local edits, zero API cost), AutoCompact (triggers at ~93.5% context utilization), Full Compact (complete compression with selective file re-injection).

**Tool System (validates per-agent tool specialization):**
- 50+ tools with isolated input schemas, permission levels, execution logic. Validates 3-5 tools per agent approach.

**KAIROS feature (applicable to META/Observation Library):**
- 150+ feature flag references. Always-on autonomous daemon with "autoDream" for memory consolidation while idle. Merges disparate observations, removes logical contradictions, converts vague insights to absolute facts. Directly relevant to Observation Library design.

---

## 6. IMPLEMENTATION SPEC SUMMARY (Phase 1)

11 components, build order with dependency graph:

**Foundations (parallel, no dependencies):**
- #1: RESEARCH.md specification format (templates, JSON schemas, 3-5 sample specs) -- Size: S
- #2: Citation data model (citation, claim, manifest JSON schemas) -- Size: S
- #3: pgvector + hybrid search retrieval module (`src/retrieval/`) -- Size: L (needs API keys: Exa, Brave, EdgarTools, FRED, Academix)
- #4: MCP gateway (`src/gateway/`) -- Size: M (needs API keys)

**Sequential chain (after foundations):**
- #5: Specification Engine (depends on #1, #4) -- Size: L
- #6: Research Agent Framework (depends on #2, #3, #4) -- Size: XL
- #7: CitationProcessor (depends on #2, #6) -- Size: M
- #8: Deliberation module (depends on #7) -- Size: XL
- #9: Content Structuring (depends on #8) -- Size: L
- #10: Generation (depends on #9) -- Size: M
- #11: Evaluator Layers 1-3 (depends on #2) -- Size: XL (2-3 weeks, includes Prometheus 2 local deployment)

**MVP definition:** 2-3 agents, 2 search APIs, single aggregation pass, Layers 1-2 eval, Markdown output. MVP is a waypoint -- full L1.5 deliberation must be tested before Phase 1 is declared done.

**External dependency on critical path:** Jack provides 10+ past deliverables with quality scores for evaluator calibration (0.80+ Spearman target).

**API keys needed for Components #3-4:** Exa, Brave Search, EdgarTools, FRED, Academix. PostgreSQL + pgvector infrastructure also required.

---

## 7. HANDOFF PROTOCOL (Designed but NOT yet implemented)

The Cowork session designed a three-document handoff system that was never fully deployed:

**CLAUDE.md** (exists, updated) -- Permanent project context. What the project IS. Auto-loaded by Claude Code.

**SESSION-LOG.md** (NOT YET CREATED) -- Chronological log of every agent session. Date, agent type, task, key outputs (file paths), key decisions, what it set up for next session.

**CURRENT-STATE.md** (NOT YET CREATED, would replace stale audit/SESSION-CONTEXT.md) -- Living snapshot. Current phase, what's complete, what's in progress, what's next, what's blocked, what files to read for deeper context.

**Working rule to add to CLAUDE.md:** "Before finishing any session, update SESSION-LOG.md with a new entry for this session, and rewrite CURRENT-STATE.md to reflect the current project state."

**Handoff prompt template for Claude Code** (designed, never deployed):
```
Create SESSION-HANDOFF-[TASKNAME].md with:
1. Task you were given (1-2 sentences)
2. Files created or modified (full paths + 1-sentence descriptions)
3. Files you read for context
4. Key decisions you made (what and why)
5. Deviations from the prompt (what and why)
6. What you didn't finish
7. What should happen next
8. Surprises or findings
Keep under 300 lines. This is for an agent that already knows the project.
```

---

## 8. OPEN ITEMS AND DECISIONS

### Unresolved from the Cowork session

1. **Deep research reports not synthesized.** The 10 compass_artifact files have not been renamed or cross-referenced against the repo analysis or plan changes. The scaffolding session may have done this -- check SESSION-HANDOFF-SCAFFOLDING.md if it exists.

2. **Scaffolding session output unverified.** The Cowork session never analyzed the scaffolding session's actual output (Pydantic models, project scaffolding, code architecture doc). Need to verify what was produced and its quality.

3. **Handoff protocol not implemented.** SESSION-LOG.md and CURRENT-STATE.md don't exist yet. CLAUDE.md doesn't have the handoff working rule.

4. **Latency budget not set.** No design constraint on end-to-end time. "<30 minutes for 10-task engagement" in impl spec but not in the plan as a hard constraint.

5. **Evaluative Surprise dimension untested.** Most subjective of 10 rubric dimensions. May need tuning or removal based on actual results.

6. **Retrieval architecture scope.** Full spec is 4 search providers + 2 embedding models + 2 rerankers. Jack acknowledged complexity is fine even if it complicates MVP, but MVP should start with Exa + Brave + pgvector.

### Jack's settled decisions

- **Claude Max as deployment target** with minimal external APIs
- **No cross-provider model diversity for deliberation** (Claude-only with methodological diversity; validate empirically)
- **Cross-model evaluation via Prometheus 2 locally** (provides diversity without external API calls)
- **Complexity is acceptable** even if it complicates MVP -- wants to build it right
- **Custom orchestration over framework adoption** (validated by AgentLeak 68.8% leakage finding)

### External dependencies

- Jack provides 10+ past deliverables with quality scores (evaluator calibration)
- API keys: Exa, Brave Search, EdgarTools, FRED, Academix
- PostgreSQL + pgvector infrastructure
- Mac Mini for Prometheus 2 local deployment

---

## 9. KEY EMPIRICAL EVIDENCE (Referenced throughout)

| Stat | Source | Implication |
|------|--------|-------------|
| 17% → 92% | Claude Code + LangSmith Skills | Harness > model, quantified |
| 96.5% SpreadsheetBench | AutoAgent (autonomous) | Self-optimizing harness beats hand-engineering |
| 29-30% false claims | Claude Code agentic (Capybara v8) | Evaluator catches ~1/3 of all output |
| 68.8% leakage | AgentLeak benchmark (4,979 traces) | Agent isolation requires structural enforcement |
| 78% vs 42% | Same model, different harness (Nate Mar 6) | Structure determines outcomes > capability |
| 60-68% expert agreement | Single LLM judge ceiling | Justifies multi-layer evaluation |
| 96% vs 13% scoring loss | SOS-Bench (ICLR 2025) | Style-over-substance bias in LLM judges |
| 17.2x error amplification | Google DeepMind (180 configs) | Unstructured multi-agent networks amplify errors |
| $12-$100/engagement | Validated cost model | 0.3-3% of engagement revenue |

---

## 10. PROJECT FILE STRUCTURE (As of last known state)

```
Keystone-Intelligence-Engine/
├── CLAUDE.md                          # ~90 lines, behavioral rules, auto-loaded
├── CAPSTONE-PLAN-v2.md                # 1,294 lines, source of truth (post-17 changes)
├── RESEARCH-PROMPTS-FINAL.md          # Maps prompt numbers to topics for 16 reports
├── KICKOFF-PROMPT.md                  # Session prompts (Sessions 1 and 2)
├── SYNTHESIS-AND-SCAFFOLDING-PROMPT.md # Scaffolding session prompt (audited)
├── README.md                          # Updated to reflect .claude/ structure
├── .claude/
│   ├── settings.json                  # Opus 4.6 default, high effort, Haiku→Sonnet
│   ├── agents/
│   │   ├── research-analyst.md        # Thread analysis agent (parallel, analysis-only)
│   │   └── synthesis-lead.md          # Reads all analyses, updates plan, writes changelog
│   └── skills/
│       ├── research-synthesis/SKILL.md # 4-phase methodology, evidence tiers
│       └── architecture/SKILL.md      # Pipeline layers, handoff contracts, design principles
├── research-reports/                  # 16 original deep research reports (A1-D3)
├── nate-synthesis/                    # 91-article synthesis, frameworks, capstone implications
├── source-analysis/                   # X/Twitter bookmarks analysis, external sources
├── quality-audits/                    # Prompt audits, system prompt analysis
├── synthesis/
│   ├── UNIFIED-SYNTHESIS.md           # Cross-thread findings, ~80 tool verdicts
│   ├── PLAN-CHANGELOG.md             # 17 changes with evidence and rationale
│   ├── thread-a-summary.md through thread-d-summary.md
│   └── [per-report analyses]
├── audit/
│   ├── PHASE-1-IMPLEMENTATION-SPEC.md # 11 components, schemas, acceptance criteria
│   ├── GAP-TRIAGE.md                 # 8 gaps, none block Phase 1
│   └── SESSION-CONTEXT.md            # 66 lines (STALE -- predates overnight + scaffolding)
├── reference/
│   ├── nano-claude-code/             # Full repo, 56 Python files, 11,833 lines
│   ├── OVERNIGHT-ANALYSIS-PROMPT.md  # 10-phase autonomous analysis prompt
│   ├── DEEP-RESEARCH-PROMPTS.md      # 10 parallel deep research prompts
│   ├── PROJECT-CUSTOM-INSTRUCTIONS.md
│   └── analysis/
│       ├── 00-master-index.md through 09-implementation-recommendations.md
│       └── compass_artifact_*.md     # 10 deep research reports (NOT YET RENAMED)
└── src/                              # May contain scaffolding from latest session (UNVERIFIED)
```
