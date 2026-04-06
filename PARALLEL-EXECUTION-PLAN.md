# Parallel Execution Plan: Tracks 1-3 + Phase 1 Build
*2026-04-05 | Produced in Cowork planning session*

---

## Execution Overview

Three parallel tracks converge into the Phase 1 build sequence. The dependency graph:

```
Track 3 (Casing books) ──────────────────────────────────────────────┐
  [Independent, start immediately]                                   │
                                                                     │
Track 1 (Doc updates) ──→ Track 2 (Fork evals) ──→ Build Phase 1A  │
  [Cowork, ~2-3 hrs]       [Claude Code, ~3 hrs]    [No fork deps]  │
                                                     │               │
                                                     ▼               │
                                                  Phase 1B ──────────┤
                                                  [Fork-conditional] │
                                                     │               │
                                                     ▼               │
                                                  Phase 1C ◄─────────┘
                                                  [Needs casing skill file]
                                                     │
                                                     ▼
                                                  Phase 1D → 1E
```

**Blockers to resolve before ANY build sessions:**
1. Python 3.11 or 3.12 environment (system has 3.14 only)
2. PostgreSQL instance with pgvector extension running
3. Exa API key (sign up at exa.ai)
4. Brave Search API key (sign up at brave.com/search/api)

---

## Track 1: Architecture Finalization
**Executor:** Cowork (me)
**Duration:** 2-3 hours
**Depends on:** Nothing
**Produces:** Updated CAPSTONE-PLAN-v2.md, PHASE-1-IMPLEMENTATION-SPEC.md, CURRENT-STATE.md, CLAUDE.md

### Approach

Surgical section-by-section edits to CAPSTONE-PLAN-v2.md incorporating all 48 recommended changes from MASTER-SYNTHESIS Section 9, filtered through Directive 13 (Phase 1 staging test: "Can this be added later by extending an interface without rewriting existing components?").

Every change marked inline as `[Phase 1]` or `[Phase 2+]` so the document becomes a living roadmap.

### Edit Plan by Section

**Section 3 (Specification Engine) — 10 changes:**
1. Replace 7-step flow with 10-step pipeline [Phase 1: all 10 steps, but Steps 1-2 simplified]
2. Add engagement classifier (5-type taxonomy) [Phase 1: implement classifier, 3-4 profiles]
3. Add Decision-First CoT + TiCoder [Phase 1: Decision-First CoT only. TiCoder Phase 2]
4. Add heterogeneous lenses for issue tree (3-4 Sonnet agents) [Phase 1]
5. Add MECE verification as discrete step [Phase 1]
6. Add Day-1 Hypothesis [Phase 1]
7. Add VOI-inspired priority scoring [Phase 1: simplified formula]
8. Add Observation Library CBR query at entry [Phase 2: stub the interface]
9. Change research-tasks.json to DAG structure [Phase 1]
10. Add per-branch end product specification [Phase 1]

**Section 4 (Research & Analysis) — 12 changes:**
11. Add iterative research loop: 3 default, 5 max, three-criterion stopping [Phase 1]
12. Add scope-change detection (In-Plan/Out-of-Plan) [Phase 1: simplified]
13. Add orchestrator Memory scratchpad [Phase 1]
14. Convert 5 fixed agent types to seed templates in registry [Phase 1: 5-10 templates]
15. Add template registry query + interpolation [Phase 1]
16. Add tighten-only constraint invariant [Phase 1]
17. Add token budget per agent [Phase 1]
18. Add 1,000-2,000 token condensed output [Phase 1]
19. Add artifact bypass pattern [Phase 1]
20. Change aggregation to claim-level selection [Phase 1]
21. Add WWHTB step [Phase 1]
22. Add ADaPT reactive decomposition [Phase 2: stub interface, Phase 1 uses static trees]

**Section 5 (Evaluator) — 7 changes:**
23. Add geometric mean aggregation [Phase 1]
24. Add Tier 1/Tier 2 rubric split [Phase 1]
25. Expand to 8-10 profiles [Phase 1: 3-4 profiles. Phase 2: expand to 8-10]
26. Add branch classification → weight generation [Phase 2: Phase 1 uses manual weights]
27. Sprint contract directionality [Phase 1]
28. Dimension-specific verification [Phase 1: programmatic for Quant Rigor. Phase 2: position-switching for Analytical Depth]
29. Graceful degradation principle [Phase 1: document principle]

**Section 6 (Retrieval) — 9 changes:**
30. Split #3 into #3a + #3b [Phase 1]
31. Voyage-finance-2 embeddings [Phase 1]
32. Contextual retrieval at ingest [Phase 1]
33. Cohere Rerank v3.5 [Phase 1]
34. Chunking rules [Phase 1]
35. Remove Semantic Router [Phase 1]
36. Remove Bifrost caching [Phase 1]
37. Brave + Exa for external discovery [Phase 1]
38. Compiled wiki per engagement [Phase 1: basic structure. Phase 2: cross-engagement]

**Section 7 (Observation Library) — 4 changes:**
39. CBR R4 cycle [Phase 2: stub interface only]
40. 5-tier knowledge hierarchy [Phase 2]
41. Three-type extraction [Phase 2]
42. Flexon tagging [Phase 2]

**Section 12 (Infrastructure) — 6 changes:**
43. Remove Agent SDK [Phase 1]
44. Error recovery Layers 1-2 [Phase 1]
45. HITL database state machine [Phase 1]
46. Day-1 coding standards for Temporal [Phase 1]
47. paper-search-mcp replaces Academix [Phase 1]
48. Finnhub MCP [Phase 1]

### PHASE-1-IMPLEMENTATION-SPEC.md Updates

After CAPSTONE-PLAN-v2.md is updated, PHASE-1-IMPLEMENTATION-SPEC.md gets:
- Component #3 split into #3a and #3b with separate specs
- Component #4 updated: note mcp-gateway fork candidate (conditional on Track 2 eval)
- Component #5 expanded: 10-step pipeline, staged per Directive 13
- Component #6 updated: geometric mean, tier split, 3-4 profiles (not 8-10)
- Component #7 updated: error recovery, artifact bypass, template dispatch
- Component #8 updated: note SemanticCite fork candidate (conditional on Track 2 eval)
- Component #9 updated: claim-level selection, WWHTB
- New HITL component spec
- Component #3a: note VectorChord as conditional replacement (Track 2 eval)
- Updated build order reflecting fork-conditional branches
- Open source fork candidates integrated with FORK/BUILD markers

### Verification Step

After all edits:
1. Diff every change against MASTER-SYNTHESIS Section 9's 48 recommendations
2. Verify each was either incorporated or explicitly deferred with rationale
3. Check consistency between CAPSTONE-PLAN-v2.md and PHASE-1-IMPLEMENTATION-SPEC.md
4. Verify all 14 Jack directives are respected
5. Update CURRENT-STATE.md and CLAUDE.md to reference new state

---

## Track 2: Fork Candidate Deep-Eval Sessions
**Executor:** Jack (Claude Code sessions)
**Duration:** ~1-2 hours per session, 3 sessions
**Depends on:** Track 1 (updated component specs)
**Produces:** 3 verdict documents in audit/fork-evaluations/

### Session A: SemanticCite → Component #8 (CitationProcessor)

**Prompt:**

```
# Fork Evaluation: SemanticCite for CitationProcessor (Component #8)

## Your Task
Clone and evaluate the SemanticCite repository to determine whether it should be
forked as a starting point for Component #8 (CitationProcessor) of the Keystone
Intelligence Engine, or whether we should build from scratch.

## Step 1: Load Context
Read these files to understand what Component #8 needs to do:
- CLAUDE.md (project overview)
- JACK-ARCHITECTURAL-DIRECTIVES.md (design constraints)
- audit/PHASE-1-IMPLEMENTATION-SPEC.md → Component #8 section
- src/keystone/models/citations.py (existing citation data model)
- src/keystone/contracts.py (Protocol interfaces)

## Step 2: Clone and Map
Clone the SemanticCite repository. Then:
1. Map the directory structure
2. Read the README and any architectural docs
3. Identify the core modules and their responsibilities
4. Determine: language, framework, dependencies, license

## Step 3: Evaluate Against Our Spec
For each requirement in our Component #8 spec, assess whether SemanticCite covers it:

| Requirement | Our Spec | SemanticCite Coverage | Gap |
|-------------|----------|----------------------|-----|
| Citation extraction from agent outputs | Required | ? | ? |
| Cross-agent deduplication (same URL/DOI → merge) | Required | ? | ? |
| Corroboration scoring (independent discovery by 2+ agents) | Required | ? | ? |
| URL liveness verification | Required | ? | ? |
| Fabrication detection (non-existent DOIs) | Required | ? | ? |
| Content-hash provenance for wiki compilation | Required | ? | ? |
| Output conforming to citation_manifest.schema.json | Required | ? | ? |
| Integration with Pydantic v2 models | Required | ? | ? |

## Step 4: Code Quality Assessment
- Is the code well-structured and maintainable?
- Are there tests? What's the coverage?
- What's the dependency footprint? Any conflicts with our stack (PydanticAI, Python 3.11/3.12)?
- Is the code actively maintained? Last commit date? Open issues?
- License compatibility with our project?

## Step 5: Integration Effort Estimate
If we fork:
- What modules would we keep as-is?
- What modules would we modify?
- What modules would we gut/rewrite?
- What modules are missing and must be built?
- Estimated effort to integrate vs. building from scratch

## Step 6: Produce Verdict
Write your evaluation to audit/fork-evaluations/semanticcite-eval.md with this structure:

### Verdict: FORK / EXTRACT / SKIP
### Overlap Percentage: X%
### Confidence: HIGH / MEDIUM / LOW

### Modules to Keep:
- [list with rationale]

### Modules to Modify:
- [list with what changes needed]

### Modules Missing (must build):
- [list]

### Integration Risks:
- [list]

### Effort Comparison:
- Fork + modify: estimated X days
- Build from scratch: estimated Y days
- Net savings: Z days

### Recommendation:
[Final recommendation with reasoning]
```

### Session B: vurgunhajiyev/mcp-gateway → Component #4 (MCP Gateway)

**Prompt:**

```
# Fork Evaluation: mcp-gateway for MCP Gateway (Component #4)

## Your Task
Clone and evaluate the vurgunhajiyev/mcp-gateway repository to determine whether
it should be forked as a starting point for Component #4 (MCP Gateway) of the
Keystone Intelligence Engine, or whether we should build from scratch.

## Step 1: Load Context
Read these files to understand what Component #4 needs to do:
- CLAUDE.md (project overview)
- JACK-ARCHITECTURAL-DIRECTIVES.md (design constraints)
- audit/PHASE-1-IMPLEMENTATION-SPEC.md → Component #4 section
- src/keystone/contracts.py (Protocol interfaces)

## Step 2: Clone and Map
Clone vurgunhajiyev/mcp-gateway. Then:
1. Map the directory structure
2. Read the README and any architectural docs
3. Identify the core modules and their responsibilities
4. Determine: language, framework, dependencies, license

## Step 3: Evaluate Against Our Spec
For each requirement in our Component #4 spec, assess coverage:

| Requirement | Our Spec | mcp-gateway Coverage | Gap |
|-------------|----------|---------------------|-----|
| Central router for all MCP tool calls | Required | ? | ? |
| Per-agent tool authorization (only assigned tools) | Required (structural enforcement) | ? | ? |
| Redis-backed rate limiting per provider | Required | ? | ? |
| Per-provider circuit breakers (3 failures → open, 30s retry) | Required | ? | ? |
| Audit logging (agent_id, tool, input, output, timestamp) | Required | ? | ? |
| Tool registry with health checks | Required | ? | ? |
| Tool Search deferred loading (stub descriptions first) | Required | ? | ? |
| Support for both stdio and HTTP MCP transports | Required | ? | ? |
| Citation extraction from tool outputs | Required | ? | ? |
| Max retry count + dead-letter path on all loops | Required | ? | ? |

## Step 4: Code Quality Assessment
- Code structure and maintainability
- Test coverage
- Dependency footprint and stack compatibility
- Maintenance status (last commit, issues, contributors)
- License compatibility

## Step 5: Integration Effort Estimate
Same structure as Session A: keep/modify/gut/missing modules, effort comparison.

## Step 6: Produce Verdict
Write to audit/fork-evaluations/mcp-gateway-eval.md with the same verdict structure
as Session A.
```

### Session C: VectorChord + VectorChord-BM25 → Component #3a (Source Discovery)

**Prompt:**

```
# Fork Evaluation: VectorChord + VectorChord-BM25 for Source Discovery (Component #3a)

## Your Task
Evaluate VectorChord and VectorChord-BM25 as a potential replacement for the
pgvector + ParadeDB stack in Component #3a (Source Discovery) of the Keystone
Intelligence Engine. This is NOT a fork evaluation (we wouldn't fork a database
extension) but an infrastructure evaluation: should we use VectorChord instead
of pgvector as our vector index, and VectorChord-BM25 instead of ParadeDB for
keyword search?

## Step 1: Load Context
Read these files:
- CLAUDE.md (project overview)
- audit/PHASE-1-IMPLEMENTATION-SPEC.md → Component #3 section
- The retrieval architecture section of CAPSTONE-PLAN-v2.md

## Step 2: Research VectorChord
1. Clone the VectorChord repository (tensorchord/VectorChord on GitHub)
2. Clone VectorChord-BM25 (tensorchord/VectorChord-BM25)
3. Read READMEs, architecture docs, benchmarks
4. Check: PostgreSQL extension? What versions supported? Docker deployment?

## Step 3: Evaluate Against Our Requirements

### Vector Search (replacing pgvector):
| Requirement | pgvector | VectorChord | Winner |
|-------------|----------|-------------|--------|
| 1024-dim vectors (Voyage-finance-2) | Yes | ? | ? |
| HNSW index | Yes | ? | ? |
| Approximate + exact search | Yes | ? | ? |
| PostgreSQL 15/16 compatibility | Yes | ? | ? |
| Maturity / production usage | High | ? | ? |
| Performance on 100K-1M vectors | Baseline | ? | ? |
| Docker deployment | Yes | ? | ? |

### BM25 Search (replacing ParadeDB):
| Requirement | ParadeDB | VectorChord-BM25 | Winner |
|-------------|----------|-------------------|--------|
| True BM25 scoring in PostgreSQL | Yes (via pg_search) | ? | ? |
| RRF fusion with vector search | Manual (application layer) | ? | ? |
| Index maintenance overhead | ? | ? | ? |
| Full-text search on financial docs | Yes | ? | ? |
| PostgreSQL native (no external service) | Yes | ? | ? |
| Maturity / production usage | Medium | ? | ? |

### Hybrid Search (the key question):
Can VectorChord + VectorChord-BM25 do dense + BM25 + RRF fusion NATIVELY
within PostgreSQL, eliminating the need for application-layer fusion code?
This is the primary value proposition.

## Step 4: Deployment and Operations
- Docker images available?
- Managed hosting options?
- Backup/restore implications?
- Can we migrate from pgvector to VectorChord later if we start with pgvector?
- What happens if VectorChord project goes unmaintained?

## Step 5: Performance Testing (if feasible)
If time permits, set up a quick benchmark:
- Create a PostgreSQL instance with VectorChord
- Index 1000 sample documents with 1024-dim vectors
- Run 10 hybrid queries (dense + BM25)
- Compare latency to pgvector + ParadeDB baseline

## Step 6: Produce Verdict
Write to audit/fork-evaluations/vectorchord-eval.md:

### Verdict: REPLACE pgvector / REPLACE ParadeDB / KEEP CURRENT STACK
### Confidence: HIGH / MEDIUM / LOW

### Advantages over current stack:
- [list]

### Risks:
- [list]

### Migration path if we start with pgvector:
- [description]

### Recommendation:
[If VectorChord is clearly better: switch now.
 If comparable but riskier: start with pgvector, migrate later.
 If immature: skip, revisit in 60 days.]
```

---

## Track 3: Casing Book Analysis
**Executor:** Jack (Opus 1M context chat, NOT Claude Code)
**Duration:** ~1-2 hours
**Depends on:** Jack having digital casing books available to upload
**Produces:** MECE decomposition skill files for Component #5

### Prompt:

```
# MECE Issue Tree Decomposition: Principles Extraction from Casing Literature

## Your Task
You are analyzing consulting case interview methodology books to extract the
PRINCIPLES of how expert consultants decompose problems into MECE (Mutually
Exclusive, Collectively Exhaustive) issue trees. The output will become a set
of skill files that teach AI agents how to perform this decomposition.

CRITICAL DISTINCTION: You are extracting PRINCIPLES and DECISION RULES, not
example frameworks or templates. The goal is NOT "here's the profitability
framework" but rather "here's how an expert decides WHERE to cut a problem,
HOW DEEP to go, and WHEN a decomposition is complete."

## What to Extract

### 1. Decomposition Decision Rules
- How do experts decide the first cut? (By what dimension do they split the root?)
- What signals indicate horizontal expansion (more branches) vs. vertical deepening (more levels)?
- How do they determine the right granularity for leaf nodes?
- When is 2 levels enough? When do you need 4-5?
- How do they handle cross-cutting concerns that don't fit cleanly into branches?

### 2. MECE Verification Methodology
- How do you test for mutual exclusivity? (What specific checks?)
- How do you test for collective exhaustiveness? (What specific checks?)
- What are the most common MECE violations and how are they detected?
- How do you handle the "residual bucket" problem (where a catch-all "Other" branch masks incomplete decomposition)?

### 3. Consulting Lenses
- What are the standard analytical lenses (financial, operational, market, regulatory, organizational, etc.)?
- When does each lens apply?
- How do different lenses produce different tree structures for the same problem?
- What makes a "heterogeneous lens" approach (multiple lenses simultaneously) better than a single-lens approach?

### 4. Hypothesis-Driven Decomposition
- How does a Day-1 Hypothesis shape the tree structure?
- How do you decompose toward testability (each leaf should be testable)?
- How do you prevent the hypothesis from biasing the decomposition?

### 5. Anti-Patterns
- What makes a BAD issue tree?
- Common failure modes: too broad (laundry list), too deep (analysis paralysis), non-MECE (overlapping branches), non-actionable (can't research the leaves)
- How do you recognize a tree that looks MECE but isn't actually useful?

### 6. Adaptation During Research
- How should a tree evolve as new information comes in?
- When do you add branches vs. restructure?
- How do you maintain MECE properties during evolution?

## Output Format

Produce these files (output each as a clearly labeled section):

### File 1: skills/mece-decomposition/SKILL.md
The core methodology file. This is what a Sonnet-class AI agent reads before
attempting decomposition. It must be:
- Concrete and operational (not abstract)
- Written as instructions the agent follows
- Include decision rules with IF/THEN structure where possible
- 2,000-4,000 words

### File 2: skills/mece-decomposition/principles.md
The deeper theoretical grounding. Why the decision rules work. The expert
reasoning behind each principle. Opus-class agents read this for deeper
understanding. 1,000-3,000 words.

### File 3: skills/mece-decomposition/gotchas.md
Common decomposition failures with specific detection criteria and fixes.
Format: Problem → How to Detect → How to Fix. 1,000-2,000 words.

### File 4: skills/mece-decomposition/validation.md
A step-by-step checklist for validating whether a given issue tree is
actually MECE, well-structured, and useful. This is what the MECE
Verification step (Step 4 in our Specification Engine) will use.
500-1,000 words.

### File 5: skills/mece-decomposition/lens-library.md
The consulting lenses catalog. Each lens: what it is, when to apply it,
how it shapes decomposition, what it tends to miss. 1,000-2,000 words.

## Quality Standard
After producing these files, self-evaluate:
1. Could a Sonnet-class agent produce a meaningfully better issue tree
   using SKILL.md than without it?
2. Are the decision rules specific enough to be actionable, or are they
   just restating "be MECE"?
3. Do the gotchas describe SPECIFIC failure modes, not generic warnings?
4. Would an experienced consultant recognize these principles as accurate?

If any answer is "no," revise before finalizing.
```

### Note on Book Availability
Jack: do you have your casing books in digital format (PDF, EPUB, etc.)? If they're
physical books, we have two alternatives:
1. Upload photos of key chapters and use Opus's vision capabilities
2. Use Opus's existing training knowledge of casing methodology (Case in Point,
   Case Interview Secrets, etc.) combined with a more targeted extraction prompt

---

## Phase 1 Build Sequence

### Prerequisites (before any builder session)
- [ ] Python 3.11/3.12 environment setup (pyenv or conda)
- [ ] PostgreSQL running with pgvector extension
- [ ] Exa API key obtained
- [ ] Brave Search API key obtained
- [ ] Track 1 complete (updated docs)

### Phase 1A: Foundation (parallel, no dependencies)

Three parallel Claude Code sessions:

**Session 1A-1: Component #1 (RESEARCH.md Spec Format)**
```
Estimated: 2-3 days | Scope: S+
```
- Templates and JSON schemas
- Sample RESEARCH.md files for test engagements
- research-tasks.json schema with DAG structure
- No external dependencies needed

**Session 1A-2: Component #2 (Citation Data Model)**
```
Estimated: 1-2 days | Scope: S
```
- Citation, Claim, and CitationManifest schemas
- Pydantic v2 models (updating existing src/keystone/models/citations.py)
- Content-hash provenance utilities
- No external dependencies needed

**Session 1A-3: HITL Infrastructure**
```
Estimated: 2-3 days | Scope: S
```
- PostgreSQL state machine (3 tables: review_gates, review_items, review_decisions)
- REST API (FastAPI)
- Basic web UI showing: issue tree, agent configs, divergence points
- Approve/modify/reject flows

**Quality gate for 1A:** All schemas validate. HITL API responds to approve/modify/reject. Sample RESEARCH.md passes schema validation.

### Phase 1B: Infrastructure (parallel, depends on 1A + Track 2 results)

Two parallel sessions:

**Session 1B-1: Component #3a (Source Discovery)**
```
Estimated: 1-2 weeks | Scope: L
Conditional: If VectorChord eval (Track 2C) says REPLACE → use VectorChord
             If KEEP CURRENT → use pgvector + ParadeDB
```
- Vector store with hybrid search (dense + BM25 + RRF)
- Voyage-finance-2 embedding integration
- Contextual retrieval at ingest
- Cohere Rerank v3.5
- Docling for PDF parsing
- Brave Search + Exa integration

**Session 1B-2: Component #4 (MCP Gateway)**
```
Estimated: 1 week | Scope: M
Conditional: If mcp-gateway eval (Track 2B) says FORK → fork and modify
             If SKIP → build from scratch
```
- Central router, auth, rate limiting, circuit breaking
- Audit logging
- Tool registry with health checks
- Tool Search deferred loading
- Configure: Exa, Brave, EdgarTools, FRED, paper-search-mcp, doi-mcp, Finnhub

**Quality gate for 1B:** Hybrid search returns results for financial queries. MCP gateway enforces per-agent tool authorization. Circuit breaker activates after 3 failures.

### Phase 1C: Core Engines (can partially parallelize)

**Session 1C-1: Component #5 (Specification Engine)**
```
Estimated: 2-3 weeks | Scope: XL
Depends on: #1, #4, HITL, Track 3 (casing skill file)
```

The biggest component. 10-step pipeline, staged per Directive 13:

**Build (Phase 1):**
- Step 1: Problem Framing + Engagement Classifier (3-4 types initially)
- Step 2: Hypothesis Generation (Day-1 Hypothesis)
- Step 3: Issue Tree Decomposition (3 Sonnet agents with heterogeneous lenses, using casing skill file)
- Step 4: MECE Verification (Opus evaluator, binary criteria)
- Step 5: Priority Assignment (simplified VOI formula)
- Step 6: Agent Configuration (template registry with 5-10 seed templates)
- Step 7: Task Generation (DAG structure, anti-confirmatory framing)
- Step 8: Human Review Gate (via HITL infrastructure)
- Step 9: Research Execution entry point (scout phase)
- Step 10: Feedback Loop (3-cycle max)

**Stub (interface only, implement Phase 2):**
- TiCoder divergence detection (Step 1)
- Observation Library CBR query (Step 1)
- ADaPT adaptive deepening (Step 3)
- Template promotion loop (Step 6)

**Session 1C-2: Component #6 (Evaluator Stack Layers 1-3)**
```
Estimated: 2-3 weeks | Scope: XL
Depends on: #1, #2
```

**Build (Phase 1):**
- Layer 1: Deterministic verification (FActScore, numerical consistency)
- Layer 2: Citation gate (doi-mcp via MCP gateway, binary fabrication check)
- Layer 3: Rubric scoring (geometric mean, Tier 1/Tier 2 split)
- 3-4 engagement-type evaluation profiles
- Sprint contract: Evaluator proposes, Generator reviews
- Programmatic verification complement for Quantitative Rigor

**Stub (Phase 2):**
- Position-switching for Analytical Depth
- 8-10 profiles (expand from 3-4)
- Branch classification → automatic weight generation
- Layer 4: Cross-model ensemble
- Layer 5: Process trajectory

**Quality gate for 1C:** Spec Engine produces valid RESEARCH.md + research-tasks.json from a test question. Evaluator catches fabricated citations, flags numerical inconsistencies, scores with geometric mean.

### Phase 1D: Pipeline Assembly

**Session 1D-1: Component #7 (Research Agent Pipeline)**
```
Estimated: 1-2 weeks | Scope: L+
Depends on: #4, #5, #6
```
- Base research agent (Sonnet)
- 5 agent types as seed templates
- Filesystem isolation
- Error recovery (retry + fallback chain)
- Artifact bypass (structured summary + full file)
- Template dispatch from registry

**Session 1D-2: Component #8 (CitationProcessor)**
```
Estimated: 3-5 days | Scope: M
Depends on: #2, #7
Conditional: SemanticCite eval (Track 2A)
```

**Session 1D-3: Component #9 (Deliberation)**
```
Estimated: 1-2 weeks | Scope: L+
Depends on: #8, HITL
```
- Independent parallel analysis (3-4 analysts, methodological diversity)
- Claim-level selection aggregation
- WWHTB step for low-confidence findings
- Confidence map builder
- Human Review Gate after confidence map

**Session 1D-4: Component #3b (Knowledge Accumulation)**
```
Estimated: 3-5 days | Scope: M
Depends on: #3a
```
- Compiled wiki per engagement (raw/ + compiled/ + INDEX.md)
- Content-hash provenance
- INDEX.md auto-maintenance

### Phase 1E: Calibration and Integration

**Session 1E-1: Component #10 (Evaluator Calibration)**
```
Estimated: 1 week | Scope: M
Depends on: #6
```
- 3-4 profile calibration (using Jack-scored sample outputs)
- Per-dimension bias detection
- 0.80+ Spearman rank correlation target

**Session 1E-2: Component #11 (End-to-End Pipeline Test)**
```
Estimated: 3-5 days | Scope: M
Depends on: everything
```
- Full pipeline run: user question → RESEARCH.md → agents → citations → deliberation → evaluation → output
- Iterative research loop (multi-round)
- HITL gates exercised
- Information fidelity check (37% retention test)
- Cost measurement (verify 15x multiplier against budget)

---

## Builder Session Prompt Template

Every Phase 1 builder session uses this prompt skeleton:

```
# Build Session: Component #{N} — {Component Name}

## Identity
You are building Component #{N} of the Keystone Intelligence Engine, a multi-agent
AI system for automated consulting research. This is a real product for Keystone
Group, not an academic exercise.

## Context Loading (read these files first, in order)
1. CLAUDE.md — project overview, architectural convictions, working rules
2. JACK-ARCHITECTURAL-DIRECTIVES.md — Jack's 14 design decisions (authoritative)
3. CAPSTONE-PLAN-v2.md Section {X} — architectural context for this component
4. audit/PHASE-1-IMPLEMENTATION-SPEC.md Component #{N} — your build spec
5. src/keystone/models/ — existing Pydantic models (build on these, don't duplicate)
6. src/keystone/contracts.py — Protocol interfaces (implement these)
7. src/keystone/events.py — event types (add new types if needed)
{8. audit/fork-evaluations/{repo}-eval.md — if this component has a fork candidate}

## Phase 1 Staging (Directive 13)
BUILD now:
{list of features to implement in this session}

STUB (interface only, no implementation):
{list of features to define interfaces for but defer}

DO NOT BUILD:
{list of features explicitly excluded from Phase 1}

## Build Protocol
1. Read all context files before writing any code
2. Implement/update Protocol interfaces in contracts.py for this component
3. Write acceptance tests based on the spec's acceptance criteria
4. Implement the component in src/keystone/{module}/
5. Run tests, fix failures
6. Write integration smoke test:
   - Mock the upstream component's output
   - Feed it through your component
   - Verify the output matches the downstream component's expected input format
7. Self-review: re-read your code looking for:
   - Hardcoded values that should be configurable
   - Missing error handling
   - Protocol violations
   - Tighten-only invariant violations
   - Any retry loop missing a max attempt count

## Day-1 Coding Standards (for Temporal migration readiness)
1. Pure function layers (business logic separate from I/O)
2. Pydantic models for all inter-layer data
3. Separate controller from workflow logic
4. Correlation IDs on all operations
5. Idempotent operations where possible

## Output Requirements
- Working code in src/keystone/{module}/
- Tests in tests/{module}/
- Updated contracts.py if new protocols needed
- Updated events.py if new event types needed
- Entry in SESSION-LOG.md: date, what was built, key decisions made, known issues

## If You Run Out of Context
Write a handoff document to audit/session-handoffs/{component}-handoff.md:
- What was completed
- What remains
- Key decisions made during the session
- Any deviations from the spec and why
- The exact command/test to verify current state
```

---

## Quality Assurance Framework

### Per-Session Quality
1. **Tests first:** Every session writes acceptance tests before implementation
2. **Interface compliance:** Every component implements its Protocol from contracts.py
3. **Integration smoke test:** Each session's final step tests upstream→component→downstream
4. **37% retention check:** Any data-transforming component (especially #8, #9) must prove information fidelity
5. **Self-review pass:** Final step before session ends

### Cross-Session Quality
After each build phase (1A, 1B, 1C, 1D, 1E):
- Run all existing tests (not just the new component's tests)
- Verify no contract violations between components
- Check that shared models (citations, claims, research tasks) are used consistently

### Final Integration Quality (Phase 1E)
- Full end-to-end pipeline test with a real research question
- Cost measurement against budget target
- Information fidelity across the full pipeline
- HITL gates function correctly
- Evaluator catches known defects in test outputs

---

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| Track 2 reveals all fork candidates are unusable | Phase 1B specs are designed as "build from scratch" with fork as optimization. No architectural dependency on forks. |
| Track 3 casing books unavailable digitally | Fall back to Opus's training knowledge + targeted extraction prompt. Lower quality but unblocked. |
| Python 3.14 incompatibility with dependencies | Use pyenv to install 3.11.x alongside 3.14. Most dependencies target 3.11+. |
| Component #5 (Spec Engine) takes longer than 2-3 weeks | This is the critical path. If it slips, #7/#8/#9 can't start. Mitigation: start with a simplified 5-step version (Steps 1,3,7,8,9) and add remaining steps iteratively. |
| Cross-session model/schema drift | Every session reads contracts.py and models/ first. Changes to shared schemas require updating all affected tests. |
| Claude API instability during builds | Error recovery (Component #7) ships in Phase 1. For the build sessions themselves: save frequently, use session handoff protocol. |

---

## Immediate Next Actions

1. **Jack:** Start Track 3 (casing book analysis). This has zero dependencies and the longest lead time to where its output is needed (Phase 1C).
2. **Jack:** Get API keys for Exa and Brave Search. Set up Python 3.11/3.12 environment. Set up PostgreSQL.
3. **Cowork (me):** Execute Track 1. Update all architecture docs.
4. **After Track 1:** Jack runs Track 2 sessions (3 parallel Claude Code sessions).
5. **After Track 1 + prerequisites:** Start Phase 1A (3 parallel builder sessions for #1, #2, HITL).
6. **After Phase 1A + Track 2 results:** Start Phase 1B.

The critical path is: Track 1 → Phase 1A → Phase 1B → Phase 1C (blocked on Track 3) → Phase 1D → Phase 1E.

Track 3 runs completely in parallel and must complete before Phase 1C starts.
Track 2 runs after Track 1 and must complete before Phase 1B starts.
