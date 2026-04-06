# Next Wave: Claude Code Session Prompts

## Overview

Four sessions total. Track 2A/2B/2C are lightweight fork evaluations (all completed).
The Evaluator (Component #6) is a single long-running Claude Code session that builds
the full L4 evaluation stack.

**Dependency graph:**
```
Track 2A (SemanticCite)  ──┐
Track 2B (mcp-gateway)   ──┼── all completed
Track 2C (VectorChord)   ──┘

Evaluator Session (Component #6)  ──→  Phase 1D-1 (#7 Content Structuring)
         ~4-6 hrs
```

Track 2 results feed into future Phase 1B sessions (not the Evaluator).
The Evaluator session can launch immediately.

**Evaluator session file ownership (strict):**
- `src/keystone/evaluator/` (entire module: __init__.py, rubric_config.py, retry.py,
  layer1_deterministic.py, layer2_citation_gate.py, layer3_rubric.py, sprint_contract.py,
  evaluator.py, three_pass.py)
- `src/keystone/evaluator/prompts/` (entire directory: 14 prompt templates)
- `schemas/evaluation_result.schema.json`
- `tests/unit/evaluator/` (all test files)
- `tests/fixtures/evaluator/` (all fixture files)

**Read-only imports from:** `src/keystone/models/`, `src/keystone/contracts.py`,
`src/keystone/events.py`, `src/keystone/citation/url_check.py`, `src/keystone/citation/hash.py`

**DO NOT modify:** `src/keystone/hitl/`, `src/keystone/citation/`, `src/keystone/models/`,
`templates/`, `samples/`, `contracts.py`, `events.py`

**Append-only:** `SESSION-LOG.md`

---

## Track 2A: SemanticCite Fork Evaluation

**STATUS: COMPLETED.** Verdict: SKIP (0% overlap). Build from scratch using existing
citation/ utilities. See `audit/fork-evaluations/semanticcite-eval.md`.

### Prompt (historical reference):

````markdown
# Fork Evaluation: SemanticCite for CitationProcessor (Component #8)

## Your Task
Clone and evaluate the SemanticCite repository to determine whether it should be
forked as a starting point for Component #8 (CitationProcessor) of the Keystone
Intelligence Engine, or whether we should build from scratch.

## PHASE 0: CONTEXT LOADING (mandatory, do this first)

Read these files to understand what Component #8 needs to do:
1. `CLAUDE.md` — Project overview and trust hierarchy
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Design constraints (especially Directives 1, 9, 14)
3. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Find the Component #8 section, read it fully
4. `src/keystone/models/citations.py` — Existing citation data model (Citation, Claim,
   CorroborationPair, CitationManifest, WikiCompilationRecord). These are the types
   the CitationProcessor must consume and produce.
5. `src/keystone/contracts.py` — Read CitationProcessorContract. This is the interface
   any implementation must satisfy.
6. `src/keystone/citation/` — Read hash.py, dedup.py, url_check.py. These utilities
   already exist and the CitationProcessor must use them, not duplicate them.
7. `schemas/citation.schema.json`, `schemas/claim.schema.json`,
   `schemas/citation_manifest.schema.json` — Output schemas

Absorb all of this before touching SemanticCite. You need to know exactly what
"good" looks like for our system before you can evaluate a candidate.

## PHASE 1: CLONE AND MAP

```bash
mkdir -p audit/fork-evaluations
cd /tmp && git clone https://github.com/SciPhi-AI/SemanticCite.git
```

Then:
1. Map the full directory structure (`find . -type f | head -200`)
2. Read the README and any architectural documentation
3. Identify core modules and their responsibilities
4. Determine: language, framework, dependencies, license
5. Read the actual source code of the 3-5 most important modules (not just docs)

## PHASE 2: EVALUATE AGAINST OUR SPEC

For each requirement from our Component #8 spec, assess SemanticCite's coverage.
Be specific — don't guess. Read the actual code.

| Requirement | Our Spec | SemanticCite Coverage | Gap |
|-------------|----------|----------------------|-----|
| Citation extraction from agent outputs | Required | ? | ? |
| Cross-agent deduplication (URL/DOI match → merge) | Required | ? | ? |
| Corroboration scoring (2+ agents find same source independently) | Required | ? | ? |
| URL liveness verification (async, HEAD+GET fallback) | Required (already built in citation/) | ? | ? |
| Fabrication detection (non-existent DOIs via doi-mcp) | Required | ? | ? |
| Content-hash provenance (SHA-256 for Karpathy wiki pattern) | Required (already built in citation/) | ? | ? |
| Output conforming to citation_manifest.schema.json | Required | ? | ? |
| Pydantic v2 model compatibility | Required | ? | ? |
| Integration with our existing citation/ utilities | Required | ? | ? |
| ACH diagnosticity classification on claims | Required | ? | ? |
| Five-tier confidence mapping on claims | Required | ? | ? |

## PHASE 3: CODE QUALITY ASSESSMENT
- Code structure and maintainability (rate 1-5)
- Test coverage (% if measurable, qualitative assessment otherwise)
- Dependency footprint — any conflicts with our stack? (PydanticAI, Python 3.12,
  httpx, SQLAlchemy 2.0, FastAPI)
- Maintenance pulse: last commit date, open issues, contributor count, release cadence
- License compatibility with MIT/Apache-2.0

## PHASE 4: INTEGRATION EFFORT ESTIMATE

If we fork, classify every module:
- **KEEP:** usable as-is or with minor config changes
- **MODIFY:** substantial changes but core logic salvageable
- **GUT:** rewrite using their structure as skeleton
- **MISSING:** not present, must build from scratch

Then estimate:
- Fork + modify: X person-days
- Build from scratch (using our existing citation/ utilities): Y person-days
- Net savings: X - Y (negative = fork is MORE work due to integration overhead)

Be honest. Forking a repo that doesn't align with your data model often costs more
than building from scratch. The existing `citation/hash.py`, `citation/dedup.py`,
and `citation/url_check.py` already give us a head start on a from-scratch build.

## PHASE 5: PRODUCE VERDICT

Write to `audit/fork-evaluations/semanticcite-eval.md`:

```
## Verdict: FORK / EXTRACT / SKIP
## Overlap Percentage: X%
## Confidence: HIGH / MEDIUM / LOW

### Modules to Keep:
- [list with rationale]

### Modules to Modify:
- [list with what changes needed]

### Modules Missing (must build regardless):
- [list]

### Integration Risks:
- [list — especially data model mismatches, dependency conflicts]

### Effort Comparison:
- Fork + modify: estimated X days
- Build from scratch: estimated Y days
- Net savings: Z days

### Recommendation:
[Final recommendation with reasoning. Be decisive — "it depends" is not a verdict.]
```

FORK = use as starting point, modify to fit.
EXTRACT = don't fork the repo, but extract specific algorithms/patterns worth copying.
SKIP = build from scratch, nothing worth taking.

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
````

---

## Track 2B: mcp-gateway Fork Evaluation

**STATUS: COMPLETED.** Verdict: EXTRACT. See `audit/fork-evaluations/mcp-gateway-eval.md`.

### Prompt (historical reference):

````markdown
# Fork Evaluation: mcp-gateway for MCP Gateway (Component #4)

## Your Task
Clone and evaluate the vurgunhajiyev/mcp-gateway repository to determine whether it
should be forked as a starting point for Component #4 (MCP Gateway) of the Keystone
Intelligence Engine, or whether we should build from scratch using FastMCP.

## PHASE 0: CONTEXT LOADING (mandatory, do this first)

Read these files to understand what Component #4 needs to do:
1. `CLAUDE.md` — Project overview
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Especially Directives 9 (max retry + dead-letter),
   11 (configurable pipeline depth), 14 (quality standard)
3. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Find the Component #4 section, read it fully
4. `src/keystone/contracts.py` — There's no explicit MCP Gateway contract, but read how
   ResearchAgentContract references tool calls. The gateway is the central router all
   tool calls flow through.
5. `src/keystone/events.py` — Check for any tool-call-related events

Key requirements for our MCP Gateway:
- Central router for ALL MCP tool calls (Exa, Brave, EdgarTools, FRED, paper-search-mcp,
  doi-mcp, Finnhub, internal document retriever)
- Per-agent tool authorization: agents only access their assigned_tools (structural
  enforcement, not honor system)
- Redis-backed rate limiting per provider (respect API quotas)
- Per-provider circuit breakers (3 failures → open, 30s retry window)
- Audit logging: every tool call logged with agent_id, tool, input hash, output hash,
  latency, timestamp
- Tool registry with health checks
- Support for both stdio and HTTP MCP transports
- Citation extraction from tool outputs (hand off to CitationProcessor)
- Max retry count + dead-letter path on ALL loops (Directive 9)

## PHASE 1: CLONE AND MAP

```bash
mkdir -p audit/fork-evaluations
cd /tmp && git clone https://github.com/vurgunhajiyev/mcp-gateway.git
```

Then:
1. Map directory structure
2. Read README and architectural docs
3. Identify core modules and responsibilities
4. Determine: language, framework, dependencies, license
5. Read actual source code of core router, auth, and transport modules

## PHASE 2: EVALUATE AGAINST OUR SPEC

| Requirement | Our Spec | mcp-gateway Coverage | Gap |
|-------------|----------|---------------------|-----|
| Central router for all MCP tool calls | Required | ? | ? |
| Per-agent tool authorization (structural) | Required | ? | ? |
| Redis-backed rate limiting per provider | Required | ? | ? |
| Circuit breakers (3 failures → open, 30s retry) | Required | ? | ? |
| Audit logging (agent_id, tool, I/O, latency) | Required | ? | ? |
| Tool registry with health checks | Required | ? | ? |
| stdio + HTTP MCP transport support | Required | ? | ? |
| Citation extraction from tool outputs | Required | ? | ? |
| Max retry + dead-letter on all loops | Required (Directive 9) | ? | ? |
| Python / FastMCP compatibility | Required | ? | ? |

## PHASE 3: CODE QUALITY ASSESSMENT
Same criteria as Track 2A: structure, tests, dependencies, maintenance, license.

**Critical check:** Is this repo Python-based? Our stack is Python. If it's
TypeScript/Go, the fork value drops dramatically — we'd be extracting patterns
rather than code.

## PHASE 4: INTEGRATION EFFORT ESTIMATE

Classify modules: KEEP / MODIFY / GUT / MISSING.

Compare against building from scratch with FastMCP (our preferred MCP framework).
FastMCP already provides: tool definition, transport handling, basic routing.
What we'd need to ADD on top of FastMCP: auth, rate limiting, circuit breaking,
audit logging, tool registry. Estimate that effort too.

Three-way comparison:
- Fork mcp-gateway + modify: X days
- Build from scratch with FastMCP: Y days
- Build from scratch without FastMCP: Z days

## PHASE 5: PRODUCE VERDICT

Write to `audit/fork-evaluations/mcp-gateway-eval.md` with same structure as Track 2A.

Verdict options: FORK / EXTRACT / SKIP

**Note:** If the repo is not Python, the verdict is almost certainly EXTRACT or SKIP.
Be explicit about language mismatch if present.

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
````

---

## Track 2C: VectorChord Infrastructure Evaluation

**STATUS: COMPLETED.** Verdict: KEEP CURRENT STACK. VectorChord sits ON TOP of
pgvector (not a replacement). At 100K-1M vectors, pgvector HNSW is sufficient.
See `audit/fork-evaluations/vectorchord-eval.md`.

### Prompt (historical reference):

````markdown
# Infrastructure Evaluation: VectorChord + VectorChord-BM25 for Source Discovery

## Your Task
Evaluate VectorChord and VectorChord-BM25 as potential replacements for the
pgvector + ParadeDB stack in Component #3a (Source Discovery) of the Keystone
Intelligence Engine. This is an infrastructure evaluation, not a fork evaluation.
The question: should we use VectorChord instead of pgvector as our vector index,
and VectorChord-BM25 instead of ParadeDB for keyword search?

## PHASE 0: CONTEXT LOADING (mandatory, do this first)

Read these files:
1. `CLAUDE.md` — Project overview
2. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Find the Component #3a section. Note
   the retrieval architecture: dense vectors (Voyage-finance-2, 1024-dim) + BM25
   keyword search + RRF fusion + Cohere Rerank v3.5.
3. `CAPSTONE-PLAN-v2.md` — Read Section 6.2 (retrieval architecture) for the full
   picture of how vector search fits into the system.

Current baseline stack:
- **Vector search:** pgvector (HNSW index, 1024-dim, already installed and verified)
- **Keyword search:** ParadeDB pg_search (BM25 scoring in PostgreSQL)
- **Fusion:** Application-layer RRF (Reciprocal Rank Fusion)
- **Reranking:** Cohere Rerank v3.5 (API call, not in-database)

## PHASE 1: RESEARCH VECTORCHORD

```bash
cd /tmp
git clone https://github.com/tensorchord/VectorChord.git
git clone https://github.com/tensorchord/VectorChord-bm25.git
```

Read thoroughly:
1. README and architecture docs for both repos
2. Benchmark results (especially vs. pgvector)
3. PostgreSQL version compatibility
4. Docker deployment options
5. API surface — is it a drop-in replacement for pgvector or different syntax?

## PHASE 2: EVALUATE AGAINST OUR REQUIREMENTS

### Vector Search (replacing pgvector):

| Requirement | pgvector (baseline) | VectorChord | Winner |
|-------------|-------------------|-------------|--------|
| 1024-dim vectors (Voyage-finance-2) | Yes | ? | ? |
| HNSW index | Yes | ? | ? |
| Approximate + exact search | Yes | ? | ? |
| PostgreSQL 15/16/17 compatibility | Yes (verified PG17) | ? | ? |
| Maturity / production usage | High (widely adopted) | ? | ? |
| Performance on 100K-1M vectors | Baseline | ? | ? |
| Docker deployment | Yes | ? | ? |
| Drop-in pgvector syntax compatibility | N/A | ? | ? |

### BM25 Search (replacing ParadeDB):

| Requirement | ParadeDB pg_search | VectorChord-BM25 | Winner |
|-------------|-------------------|-------------------|--------|
| True BM25 scoring in PostgreSQL | Yes | ? | ? |
| Index maintenance overhead | Medium | ? | ? |
| Full-text search on financial docs | Yes | ? | ? |
| PostgreSQL native (no external service) | Yes | ? | ? |
| Maturity / production usage | Medium | ? | ? |

### Hybrid Search (the key question):

Can VectorChord + VectorChord-BM25 do dense + BM25 + RRF fusion NATIVELY within
PostgreSQL, eliminating the need for application-layer fusion code? This is the
primary potential advantage. If both are just "slightly faster pgvector" and
"slightly different ParadeDB," the switching cost isn't worth it.

## PHASE 3: DEPLOYMENT AND OPERATIONS
- Docker images available? Official or community?
- Managed hosting options (Neon, Supabase, etc.)?
- Backup/restore implications vs. standard pgvector?
- **Migration path:** Can we start with pgvector and migrate to VectorChord later
  with minimal code changes? (If yes, this lowers the stakes of the decision.)
- **Bus factor:** What happens if the VectorChord project goes unmaintained? pgvector
  is PostgreSQL ecosystem core. Is VectorChord?

## PHASE 4: PERFORMANCE TESTING (if feasible)

If time permits and Docker images are available:
1. Create a PostgreSQL instance with VectorChord extension
2. Index 1,000 sample documents with random 1024-dim vectors
3. Run 10 hybrid queries (dense + BM25 if VectorChord-BM25 supports it)
4. Compare latency to pgvector baseline

If not feasible, use published benchmark data and note the limitation.

## PHASE 5: PRODUCE VERDICT

Write to `audit/fork-evaluations/vectorchord-eval.md`:

```
## Verdict: REPLACE pgvector / REPLACE ParadeDB / KEEP CURRENT STACK
## Confidence: HIGH / MEDIUM / LOW

### Advantages over current stack:
- [list]

### Risks:
- [list]

### Migration path (pgvector → VectorChord):
- [description — is it a syntax-level migration or a rewrite?]

### Recommendation:
[Decision framework:
 - If VectorChord is clearly better AND mature: REPLACE now.
 - If comparable performance but riskier: KEEP pgvector, revisit in 60 days.
 - If immature/unmaintained: SKIP, pgvector is the safe default.

 Remember: pgvector is already installed and working. The switching cost must be
 justified by concrete, measurable advantages — not just benchmarks on different
 hardware.]
```

## SESSION COMPLETION
Write a brief entry to `SESSION-LOG.md`.
````

---

## Component #6: Evaluator Stack (Single Session)

**Scope:** The complete L4 Evaluator: configuration, all 3 evaluation layers,
14 prompt templates, orchestrator, three-pass architecture, test suite, and
first test scenario. This is the highest-leverage component in the system.

**Files to create (~37):**

Core modules (9):
- `src/keystone/evaluator/__init__.py`
- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/evaluator/retry.py`
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer2_citation_gate.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/three_pass.py`

Prompt templates (14):
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/prompts/numerical_consistency.md`
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/evaluator/prompts/intent_alignment.md`
- `src/keystone/evaluator/prompts/intellectual_honesty.md`
- `src/keystone/evaluator/prompts/completeness.md`
- `src/keystone/evaluator/prompts/narrative_coherence.md`
- `src/keystone/evaluator/prompts/analytical_depth.md`
- `src/keystone/evaluator/prompts/source_quality.md`
- `src/keystone/evaluator/prompts/quantitative_rigor.md`
- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/prompts/evaluative_surprise.md`
- `src/keystone/evaluator/prompts/calibrated_confidence.md`
- `src/keystone/evaluator/prompts/gestalt_overlay.md`

Schema (1):
- `schemas/evaluation_result.schema.json`

Tests (6):
- `tests/unit/evaluator/test_rubric_config.py`
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_layer2.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/evaluator/test_evaluator.py`

Fixtures (7):
- `tests/fixtures/evaluator/clean_output.txt`
- `tests/fixtures/evaluator/fabricated_citations.json`
- `tests/fixtures/evaluator/numerical_inconsistency.txt`
- `tests/fixtures/evaluator/trendslop_output.txt`
- `tests/fixtures/evaluator/mixed_quality.txt`
- `tests/fixtures/evaluator/sample_sprint_contract.json`
- `tests/fixtures/evaluator/sample_research_task.json`

### Prompt:

````markdown
# Component #6: Evaluator Stack (L4) — Full Build

## Identity

You are building the complete Evaluator (L4) for the Keystone Intelligence Engine,
a multi-agent AI system for automated consulting research. The Evaluator is the most
important component in the system: evaluation bounds output quality. Everything the
pipeline produces is only as good as the Evaluator's ability to catch failures and
score accurately.

This is a long-running session. You will build 9 core modules, 14 prompt templates,
1 JSON schema, 6 test files, and 7 test fixtures. The work is structured in 8 phases
with audit checkpoints between major sections.

## MANDATORY: CREATE A TODO LIST

**Before writing ANY code, create a comprehensive todo list using TodoWrite.**
Use this exact list as your starting point (you may add sub-items as needed):

```
1. PHASE 0: Context loading (read all required files)
2. PHASE 1: Build rubric_config.py + retry.py
3. AUDIT CHECKPOINT 1: Verify config weights sum to 1.0, profiles complete
4. PHASE 2: Build layer1_deterministic.py + prompts
5. PHASE 3: Build layer2_citation_gate.py
6. PHASE 4: Build sprint_contract.py + prompt
7. AUDIT CHECKPOINT 2: Run tests for Phases 1-4, verify all pass
8. PHASE 5: Build layer3_rubric.py + 11 prompt templates
9. AUDIT CHECKPOINT 3: Verify all prompts have 7 required sections, word counts 300-800
10. PHASE 6: Build evaluator.py + three_pass.py
11. PHASE 7: Build test fixtures + integration tests
12. AUDIT CHECKPOINT 4: Run ALL tests, verify contract compliance
13. PHASE 8: First test scenario from implementation spec
14. FINAL AUDIT: Full verification checklist
15. SESSION COMPLETION: Update SESSION-LOG.md
```

**Mark each item in_progress before starting and completed when done. Only one item
in_progress at a time.**

## PHASE 0: CONTEXT LOADING

Read ALL of these files before writing any code. Do not skip any.

**Architecture and directives:**
1. `CLAUDE.md` — Project overview, trust hierarchy, coding standards
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Focus on:
   - Directive 7: Geometric mean aggregation (HITL Gates section is #7, the rubric
     directive is in the Batch 2 additions to CAPSTONE-PLAN-v2.md)
   - Directive 8: Tier 1/Tier 2 rubric split (same)
   - Directive 9: Max retry + dead-letter on all loops
   - Directive 11: Configurable pipeline depth (Light/Standard/Deep)
   - Directive 13: Phase 1 depth staging (ship vs. defer lists)
   - Directive 14: Quality standard ("real product for real consulting firm")

**Models you MUST import and use (DO NOT recreate any of these):**
3. `src/keystone/models/evaluation.py` — READ THOROUGHLY. Contains:
   - `RubricDimension` (10 StrEnum values)
   - `RUBRIC_WEIGHTS` (canonical base weights, sum to 1.0)
   - `ESTIMATIVE_WEIGHT_OVERRIDES`, `CURRENT_WEIGHT_OVERRIDES`
   - `DimensionScore`, `Layer1Result`, `Layer2Result`, `Layer3Result`
   - `SprintContract`, `EvaluationResult`, `EvaluationIntensity`
   - `CalibrationSample`, `CalibrationReport`
4. `src/keystone/contracts.py` — Read `EvaluatorContract` Protocol. Your `Evaluator`
   class MUST satisfy this interface EXACTLY:
   ```python
   async def evaluate(self, output_text: str, contract: SprintContract,
       task: ResearchTask, manifest: CitationManifest, spec: EngagementSpec
   ) -> AsyncIterator[AnyPipelineEvent]
   async def get_result(self) -> EvaluationResult
   ```
5. `src/keystone/events.py` — Read ALL L4 events:
   - `DeterministicCheckPassed` (facts_verified, facts_failed, numerical_issues)
   - `CitationGateResult` (citations_checked, citations_verified, fabrications_found, gate_passed)
   - `RubricDimensionScored` (dimension, score, weight)
   - `EvaluationComplete` (task_id, passed, overall_score, layer2_gate_passed, feedback_length)
6. `src/keystone/models/citations.py` — `Citation`, `CitationManifest` (Layer 2 input)
7. `src/keystone/models/research.py` — `EngagementType` enum (5 values), `ResearchTask`
8. `src/keystone/models/observations.py` — `ObservationEntry` (Phase 2 stub reference)

**Existing utilities you MUST reuse (DO NOT reimplement):**
9. `src/keystone/citation/url_check.py` — `batch_check_urls` for URL liveness
10. `src/keystone/citation/hash.py` — Content hashing utilities (reference only)

**Specification (read relevant sections only):**
11. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Find Component #6 section. Read its
    acceptance criteria and first test scenario. These are your targets.
12. `CAPSTONE-PLAN-v2.md` — Read ONLY these sections:
    - Section 5.1-5.3: Evaluation philosophy, rubric definitions, Tier 1/Tier 2
    - Section 5.8: Anti-slop standard (6 detection signals)
    - Section 5.9: Five-layer evaluation stack
    - Section 5.10: Three-pass evaluation architecture
    - Section 5.12: Evaluation profiles (3 seed profiles with weight allocations)
    - Section 5.14: Dimension-specific verification (deferred to Phase 2)
    - Section 5.15: Graceful degradation principle
    Do NOT read all 1,500+ lines. Only these sections.

After reading, confirm to yourself: What types do I import? What types do I create?
What interfaces must I satisfy? This mental model prevents the #1 failure mode:
accidentally recreating types that already exist in models/evaluation.py.

---

## PHASE 1: BUILD rubric_config.py + retry.py

### rubric_config.py

This is the foundation everything else depends on. Get it right first.

```python
from enum import StrEnum
from keystone.models.evaluation import (
    RubricDimension, RUBRIC_WEIGHTS,
    ESTIMATIVE_WEIGHT_OVERRIDES, CURRENT_WEIGHT_OVERRIDES,
)
from keystone.models.research import EngagementType

class EvaluationProfile(StrEnum):
    DEFAULT = "default"
    ESTIMATIVE = "estimative"
    CURRENT = "current"
    STRATEGIC = "strategic"

# Tier 1 universal gate floor thresholds (0-100 scale)
# Below floor = immediate rejection, skip Tier 2
TIER_1_DIMENSIONS: set[RubricDimension] = {
    RubricDimension.INTENT_ALIGNMENT,
    RubricDimension.INTELLECTUAL_HONESTY,
    RubricDimension.COMPLETENESS,
    RubricDimension.NARRATIVE_COHERENCE,
}

TIER_1_FLOOR_THRESHOLDS: dict[RubricDimension, float] = {
    RubricDimension.INTENT_ALIGNMENT: 40.0,
    RubricDimension.INTELLECTUAL_HONESTY: 40.0,
    RubricDimension.COMPLETENESS: 30.0,
    RubricDimension.NARRATIVE_COHERENCE: 40.0,
}

TIER_2_DIMENSIONS: set[RubricDimension]  # the other 6

# Map EngagementType -> EvaluationProfile
ENGAGEMENT_PROFILE_MAP: dict[EngagementType, EvaluationProfile]

# Create STRATEGIC_WEIGHT_OVERRIDES (new, not in evaluation.py):
# Emphasize: Analytical Depth (15%), Actionability (18%), Evaluative Surprise (8%)
# De-emphasize: Quantitative Rigor (10%), Completeness (5%)
STRATEGIC_WEIGHT_OVERRIDES: dict[RubricDimension, float]
```

Implement these functions:
- `get_profile_weights(profile: EvaluationProfile) -> dict[RubricDimension, float]`
  Applies the appropriate overrides to base RUBRIC_WEIGHTS. Validates result sums to 1.0.
- `get_tier1_passed(scores: list[DimensionScore]) -> bool`
  Returns False if ANY Tier 1 dimension is below its floor threshold.
- `get_tier2_scores(scores: list[DimensionScore]) -> list[DimensionScore]`
  Filters to only Tier 2 dimension scores.

**Critical:** STRATEGIC_WEIGHT_OVERRIDES must still sum to 1.0 after application.
Use the same partial-override pattern as ESTIMATIVE and CURRENT: only specify
dimensions that differ from the base, redistribute the delta proportionally across
non-overridden dimensions.

### retry.py

Every LLM call in the Evaluator must be wrapped in a retry helper (Directive 9).

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

LLMCallable = Callable[[str], Awaitable[str]]

async def retry_llm_call(
    llm: LLMCallable,
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    description: str = "",
) -> str:
    """Retry with exponential backoff (1s, 2s, 4s).

    Raises RuntimeError after max_retries exhausted (dead-letter).
    Logs each retry attempt with the description for debugging.
    """
```

This is the shared utility. Layer 1, Layer 3, and sprint_contract all import it.
Tests inject mock LLMs that never fail, but the retry wrapper must still be in
the call path so it's tested in integration.

### test_rubric_config.py

Write tests immediately after building rubric_config.py:
- All 4 profiles have weights summing to 1.0 (within 1e-9)
- ENGAGEMENT_PROFILE_MAP covers all 5 EngagementType values
- TIER_1_FLOOR_THRESHOLDS covers all 4 Tier 1 dimensions
- TIER_2_DIMENSIONS has exactly 6 members, no overlap with TIER_1
- STRATEGIC profile emphasizes Analytical Depth and Actionability over DEFAULT
- get_tier1_passed returns False when one Tier 1 score is below floor
- get_tier1_passed returns True when all Tier 1 scores are at or above floor
- get_tier2_scores returns only non-Tier-1 dimensions
- Boundary case: score exactly at floor threshold passes

Run the tests: `pytest tests/unit/evaluator/test_rubric_config.py -v`

---

## AUDIT CHECKPOINT 1

Before proceeding, verify:
1. `from keystone.evaluator.rubric_config import EvaluationProfile, get_profile_weights` works
2. `from keystone.evaluator.retry import LLMCallable, retry_llm_call` works
3. All test_rubric_config.py tests pass
4. Print the weight table for each profile and visually confirm they look reasonable
5. Confirm STRATEGIC_WEIGHT_OVERRIDES values and document your rationale in a code comment

If anything fails, fix it before moving on.

---

## PHASE 2: BUILD layer1_deterministic.py

Deterministic verification layer. No LLM judgment in the verification step itself,
but uses LLM for initial decomposition.

**FActScore decomposition:**
- Use an LLM call (via retry_llm_call) to decompose output_text into atomic factual claims
- For each claim, check if it's supported by the provided citations
- Count verified vs. failed facts
- Create prompt template at `prompts/fact_decomposition.md`

**Numerical consistency:**
- Use an LLM call to extract numerical claims and their locations
- Cross-reference numbers within the document (e.g., "revenue grew 15%" in text
  vs. "12%" in a table = inconsistency)
- Create prompt template at `prompts/numerical_consistency.md`

**URL liveness:**
- `from keystone.citation.url_check import batch_check_urls` — use directly
- Extract URLs from citations in the manifest, run batch check
- Report dead URLs in Layer1Result

**Constructor pattern:**
```python
class Layer1Evaluator:
    def __init__(self, llm: LLMCallable): ...
    async def evaluate(self, output_text: str, manifest: CitationManifest) -> Layer1Result: ...
```

Returns: `Layer1Result` (imported from models/evaluation.py)

### test_layer1.py

- FActScore decomposition produces atomic claims (mock LLM returns JSON list)
- Numerical consistency catches contradictions (mock LLM extracts numbers)
- URL liveness integrates with batch_check_urls (mock the url_check function)
- Layer1Result correctly populated with all fields
- Empty output text handled gracefully (returns zeroed result, not crash)
- retry_llm_call is in the call path (verify via mock call count)

Run: `pytest tests/unit/evaluator/test_layer1.py -v`

---

## PHASE 3: BUILD layer2_citation_gate.py

Binary citation verification gate. Any fabrication = full rejection.

**DOI verification (Phase 1 approach):**
- For citations with DOIs: HTTP HEAD to `https://doi.org/{doi}` — 200/302 = exists,
  404 = fabricated
- Design as a pluggable interface for Phase 1B swap to MCP gateway:
  ```python
  class DOIVerifier(Protocol):
      async def verify(self, doi: str) -> bool: ...

  class HTTPDOIVerifier:  # Phase 1 default
      async def verify(self, doi: str) -> bool: ...

  # Phase 1B+: MCPDOIVerifier routes through MCP gateway to doi-mcp
  # Swap via config, not code change
  ```
- For citations with URLs but no DOI: reuse `batch_check_urls`
- For citations with neither: flag as UNVERIFIABLE (not fabricated)

**Fabrication classification:**
- DOI resolves to nothing → FABRICATED
- DOI resolves but title doesn't match citation title (fuzzy match, >0.8 threshold)
  → SUSPICIOUS (flag but don't reject in Phase 1)
- DOI resolves and title matches → VERIFIED

**Constructor pattern:**
```python
class Layer2CitationGate:
    def __init__(self, doi_verifier: DOIVerifier | None = None): ...
    async def evaluate(self, manifest: CitationManifest) -> Layer2Result: ...
```

Returns: `Layer2Result` (imported from models/evaluation.py)
- `gate_passed = len(citations_fabricated) == 0`

### test_layer2.py

- Citation with valid DOI -> gate passes (mock HTTP 302)
- Citation with fabricated DOI -> gate fails (mock HTTP 404)
- Citation with no DOI -> UNVERIFIABLE, gate still passes
- Mixed citations (one fabricated among valid) -> gate fails
- Layer2Result.gate_passed invariant enforced
- DOIVerifier Protocol works with mock implementation
- Empty manifest -> gate passes (nothing to check)

Run: `pytest tests/unit/evaluator/test_layer2.py -v`

---

## PHASE 4: BUILD sprint_contract.py

Sprint contract generator. Phase 1: Evaluator proposes criteria unilaterally.
Phase 2 will add bidirectional negotiation (data structure already supports it).

- Given a ResearchTask and EngagementSpec, use LLM (via retry_llm_call) to generate
  a SprintContract
- Create prompt template at `prompts/sprint_contract_generation.md`
- The prompt should produce task-specific acceptance criteria, mandatory elements,
  and anti-patterns based on task category, end_product format, and engagement type
- Preserve the dimension_emphasis field for Phase 2 bidirectional negotiation

**Constructor pattern:**
```python
class SprintContractGenerator:
    def __init__(self, llm: LLMCallable): ...
    async def generate(self, task: ResearchTask, spec: EngagementSpec) -> SprintContract: ...
```

### test_sprint_contract.py

- Generated SprintContract has non-empty acceptance_criteria (mock LLM)
- Generated SprintContract references correct task_id and engagement_id
- dimension_emphasis values are valid RubricDimension enum members
- anti_patterns list is non-empty (mock LLM includes them)

Run: `pytest tests/unit/evaluator/test_sprint_contract.py -v`

---

## AUDIT CHECKPOINT 2

Run ALL tests built so far:
```bash
pytest tests/unit/evaluator/ -v
```

**Every test must pass before proceeding.** The foundation is set. Fix any failures.

Also verify:
1. All imports from models/evaluation.py are correct (no recreated types)
2. LLMCallable + retry_llm_call pattern is consistent across Layer 1 and sprint_contract
3. DOIVerifier Protocol allows pluggable Phase 1B replacement
4. No files modified outside `src/keystone/evaluator/`, `schemas/`, `tests/`

Count the tests passing and note the number.

---

## PHASE 5: BUILD layer3_rubric.py + 11 PROMPT TEMPLATES

**This is the highest-leverage phase. Prompt quality directly determines evaluation
accuracy. Take your time here. Do not rush.**

### layer3_rubric.py

```python
class Layer3RubricScorer:
    def __init__(self, llm: LLMCallable, profile: EvaluationProfile):
        self.llm = llm
        self.weights = get_profile_weights(profile)

    async def score_all_dimensions(
        self,
        output_text: str,
        contract: SprintContract,
    ) -> Layer3Result:
        # 1. Score Tier 1 dimensions (4 parallel LLM calls via asyncio.gather)
        # 2. Check Tier 1 floors — if any fail, return early
        # 3. Score Tier 2 dimensions (6 parallel LLM calls via asyncio.gather)
        # 4. Compute geometric mean of ALL 10 dimensions
        # 5. Apply gestalt overlay (1 more LLM call)
        # 6. Return Layer3Result
        ...
```

**Scoring flow per dimension:**
1. Load the dimension's prompt template from `prompts/{dimension_name}.md`
2. Inject: output_text, SprintContract criteria, dimension definition
3. Call LLM via retry_llm_call with the assembled prompt
4. Parse structured JSON response: `{"score": N, "feedback": "...", "sub_criteria_notes": [...]}`
5. Return DimensionScore

**Tier 1 gate check (between step 2 and 3):**
- After scoring all 4 Tier 1 dimensions, call `get_tier1_passed(tier1_scores)`
- If any Tier 1 dimension is below its floor threshold: STOP
- Set Layer3Result with only Tier 1 scores, weighted_total=0, gestalt_adjustment=0,
  final_score=0
- The orchestrator (Phase 6) uses this to set passed=false

**Tier 2 scoring:**
- Score all 6 Tier 2 dimensions in parallel (asyncio.gather)
- Each dimension gets its own prompt template, called independently
- NO dimension prompt should reference other dimension scores (prevents contamination,
  per SOS-Bench finding)

**Geometric mean aggregation (Directive 7):**
```python
import math

def weighted_geometric_mean(scores: list[DimensionScore], weights: dict) -> float:
    """Weighted geometric mean prevents dimension compensation.

    A near-zero score on any dimension drags the composite toward zero.
    Standard formula: exp(sum(w_i * ln(x_i))) when weights sum to 1.
    When scoring only a subset (e.g., Tier 1 only), normalize by weight_sum.
    """
    log_sum = 0.0
    weight_sum = 0.0
    for s in scores:
        w = weights.get(s.dimension, 0.0)
        if w > 0:
            # Floor at 1.0 to avoid log(0); 1/100 is effectively zero
            log_sum += w * math.log(max(s.score, 1.0))
            weight_sum += w
    if weight_sum == 0:
        return 0.0
    return math.exp(log_sum / weight_sum) if weight_sum < 1.0 else math.exp(log_sum)
```

**IMPORTANT MATH VERIFICATION:** Test against known cases:
- Scores [80, 80, 80] with equal weights → 80.0 exactly
- Scores [100, 1, 100] with equal weights → ~21.5 (not 67 as arithmetic mean gives)
- Scores [100, 100, 100, ...] → 100.0

**Gestalt overlay (Pass 2):**
- After dimensional scoring, make one holistic LLM call using `prompts/gestalt_overlay.md`
- The prompt reads the full output and proposes a +-5 to +-10 point adjustment
- Clamp the adjustment to [-10, +10]
- Add to the geometric mean score, clamp final to [0, 100]

### PROMPT TEMPLATES (the critical deliverable)

Create 11 prompt template files in `src/keystone/evaluator/prompts/`.

**These prompts are the single biggest quality lever in the system.** Each prompt is
read by an LLM that scores a research output on one dimension. Generic prompts produce
generic scores. Specific prompts produce calibrated scores.

**REQUIRED structure for each dimension prompt (.md file):**

Every prompt MUST have all 7 of these sections:

1. **Role definition** (1-2 sentences): You are evaluating consulting research output
   on the {dimension} dimension.
2. **Dimension definition** (2-3 sentences): What this dimension measures and why
   it matters. Pull from CAPSTONE-PLAN Section 5.3.
3. **Scoring rubric with anchors:**
   - Score 0-20: [specific description of terrible performance on this dimension]
   - Score 21-40: [description of poor performance, with example signal]
   - Score 41-60: [description of adequate but unremarkable performance]
   - Score 61-80: [description of strong performance, with example signal]
   - Score 81-100: [description of exceptional performance, with example signal]
4. **Sub-criteria checks** (dimension-specific, pulled from Section 5.3):
   - Intent Alignment: counterfactual deletion test
   - Intellectual Honesty: steelmanning, uncertainty honesty
   - Completeness: absence detection, deletion test
   - Narrative Coherence: cross-finding synthesis
   - Analytical Depth: judgment ratio (analysis vs. aggregation)
   - Source Quality: signal depth (triangulated > press releases)
   - Quantitative Rigor: adversarial robustness, precision calibration
   - Actionability: Monday-morning actionability, trendslop detection
   - Evaluative Surprise: conscious-competence ceiling check
   - Calibrated Confidence: ICD 203 probability language calibration
5. **Anti-slop sub-check** (mapped to this dimension):
   - Actionability: trendslop ("In today's rapidly evolving...")
   - Intellectual Honesty: excessive hedging ("It could be argued...")
   - Analytical Depth: framework cramming
   - Narrative Coherence: listicle structure instead of narrative
   - Others: map slop signals to the dimension they most degrade
6. **Sprint contract context injection point:**
   - `{{sprint_contract_criteria}}` placeholder
   - `{{output_text}}` placeholder
   - "Grade against these SPECIFIC criteria in addition to the general rubric"
7. **Output format:**
   ```json
   {
     "score": <integer 0-100>,
     "feedback": "<2-3 sentences of specific, actionable feedback>",
     "sub_criteria_notes": ["<note per sub-criterion checked>"],
     "slop_detected": <boolean>,
     "slop_details": "<description if detected, null otherwise>"
   }
   ```

**Now create each prompt. For each one, think about what makes THIS dimension
uniquely hard to evaluate and what specific failure modes the prompt must catch:**

### Tier 1 Dimension Prompts (4):

- `intent_alignment.md` — The "answering the right question" check. The hardest
  failure to catch because outputs can be technically excellent but strategically
  irrelevant. Key test: counterfactual deletion. Key failure: the Klarna pattern
  (technically correct, strategically wrong).

- `intellectual_honesty.md` — The "intellectual integrity" check. Key tests:
  are limitations named? Is the opposing case steelmanned? Are uncertainty ranges
  honest? Key failure: artificially narrow confidence intervals that signal false
  precision.

- `completeness.md` — The "nothing important missing" check. Key tests: absence
  detection checklist, deletion test (remove section, is there a gap?). Key failure:
  impressive depth on covered topics masking blind spots.

- `narrative_coherence.md` — The "clear story" check. Key test: cross-finding
  synthesis (findings tell a story TOGETHER, not just sequentially). Key failure:
  disconnected sections that each read well but don't build an argument.

### Tier 2 Dimension Prompts (6):

- `analytical_depth.md` — Key metric: judgment ratio (% analytical judgment vs.
  information aggregation). Key failure: competent mediocrity (correct but obvious).

- `source_quality.md` — Key metric: signal depth (triangulated/hard-to-access sources
  vs. press releases and blog posts). Machine-checkable sub-criterion: source diversity
  across types.

- `quantitative_rigor.md` — Key tests: adversarial robustness (findings hold if
  assumptions shift +-20%?), precision calibration (numbers at appropriate precision?).
  Key failure: confident numbers from weak data.

- `actionability.md` — Key test: Monday-morning actionability (segmented by role,
  immediately executable). Key failure: trendslop (recommendations that apply to any
  company in any industry).

- `evaluative_surprise.md` — The conscious-competence ceiling detector. Key test:
  would the requester already know this? A perfectly rubric-compliant output with zero
  genuine insight caps at 95%. Key failure: competent mediocrity that satisfies every
  checklist item.

- `calibrated_confidence.md` — Key test: ICD 203 probability language calibration
  ("almost certainly" >95%, "highly likely" 80-95%, etc.). Key failure: uniform
  "moderate confidence" labels regardless of actual evidence quality.

### Gestalt Overlay Prompt (1):

- `gestalt_overlay.md` — Holistic Pass 2 prompt. Reads the full output and proposes
  a numeric adjustment (-10 to +10). Captures emergent quality signals: "does this
  change how I think about the problem?" Detects the 35% of quality that dimensional
  scoring misses (per Kahneman Noise framework). Output format:
  ```json
  {
    "adjustment": <integer -10 to +10>,
    "rationale": "<1-2 sentences explaining the adjustment>"
  }
  ```

**Each prompt must be 300-800 words.** Check with `wc -w` after writing.

### test_layer3.py

**Mathematical verification (no LLM mocking needed):**
- Geometric mean with equal scores [80, 80, 80] = 80.0
- Geometric mean with one low score [100, 1, 100] << arithmetic mean
- Geometric mean with all perfect [100, 100, ...] = 100.0
- Weights sum to 1.0 for all profiles
- Floor score (1.0) handling: score of 0 mapped to 1.0 in log computation

**Tier 1 gate logic (mock LLM):**
- All Tier 1 pass -> Tier 2 runs -> full Layer3Result
- One Tier 1 fails (below floor) -> Tier 2 skipped -> Layer3Result with only Tier 1
- Tier 1 boundary: score exactly at floor -> passes

**Scoring logic (mock LLM responses):**
- Profile ESTIMATIVE applies correct weight overrides
- Profile STRATEGIC applies correct weight overrides
- Gestalt adjustment clamped to [-10, +10]
- Final score clamped to [0, 100]
- Anti-slop detection reflected in sub_criteria_notes

**Prompt loading:**
- All 11 prompt templates load from disk
- Each template contains required placeholders ({{output_text}}, {{sprint_contract_criteria}})
- Templates parse successfully into valid prompt strings

Run: `pytest tests/unit/evaluator/test_layer3.py -v`

---

## AUDIT CHECKPOINT 3

Before proceeding to the orchestrator, verify:

1. All 14 prompt templates exist in `src/keystone/evaluator/prompts/`
2. Each dimension prompt has all 7 required sections (role, definition, rubric anchors,
   sub-criteria, anti-slop, sprint contract injection, output format)
3. Each prompt is 300-800 words (run `wc -w` on each)
4. All test_layer3.py tests pass
5. Geometric mean implementation verified against hand-calculated examples
6. Tier 1/Tier 2 split in Layer3RubricScorer matches rubric_config.py EXACTLY
7. Run full test suite: `pytest tests/unit/evaluator/ -v` — ALL tests must pass

Print a summary: number of prompt templates, word counts, test count, all passing.
Fix any failures before proceeding.

---

## PHASE 6: BUILD evaluator.py + three_pass.py

### evaluator.py

The main orchestrator. This class satisfies `EvaluatorContract` from contracts.py.

```python
class Evaluator:
    """L4 Evaluator: 3-layer quality gate (Phase 1).

    Implements EvaluatorContract Protocol.

    Usage:
        evaluator = Evaluator(llm=anthropic_client, profile=EvaluationProfile.DEFAULT)
        async for event in evaluator.evaluate(output_text, contract, task, manifest, spec):
            # Handle events (log, store in trajectory)
            pass
        result = await evaluator.get_result()
    """

    def __init__(
        self,
        llm: LLMCallable,
        profile: EvaluationProfile = EvaluationProfile.DEFAULT,
        doi_verifier: DOIVerifier | None = None,  # None = use HTTPDOIVerifier
        intensity: EvaluationIntensity = EvaluationIntensity.STANDARD,
    ): ...

    async def evaluate(
        self,
        output_text: str,
        contract: SprintContract,
        task: ResearchTask,
        manifest: CitationManifest,
        spec: EngagementSpec,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 3-layer evaluation stack.

        Yields events at each layer boundary. Implements early termination:
        - Layer 2 fabrication -> yield CitationGateResult(gate_passed=False), return
        - Tier 1 floor failure -> yield EvaluationComplete(passed=False), return
        """
        # 1. Run Layer 1 (deterministic)
        layer1_result = await self._run_layer1(output_text, manifest)
        yield DeterministicCheckPassed(
            event_id=..., engagement_id=..., client_id=..., layer="L4",
            facts_verified=layer1_result.facts_verified,
            facts_failed=layer1_result.facts_failed,
            numerical_issues=len(layer1_result.numerical_inconsistencies),
        )

        # 2. Run Layer 2 (citation gate)
        layer2_result = await self._run_layer2(manifest)
        yield CitationGateResult(
            ...,
            citations_checked=layer2_result.citations_checked,
            citations_verified=layer2_result.citations_verified,
            fabrications_found=len(layer2_result.citations_fabricated),
            gate_passed=layer2_result.gate_passed,
        )
        if not layer2_result.gate_passed:
            self._result = self._build_failed_result(
                layer1_result, layer2_result, reason="fabrication"
            )
            yield EvaluationComplete(passed=False, ...)
            return

        # 3. Run Layer 3 (rubric scoring) — skipped for LIGHT_TOUCH
        if self.intensity == EvaluationIntensity.LIGHT_TOUCH:
            self._result = self._build_light_result(layer1_result, layer2_result)
            yield EvaluationComplete(passed=True, ...)
            return

        layer3_result = await self._run_layer3(output_text, contract)
        for score in layer3_result.dimension_scores:
            yield RubricDimensionScored(
                ...,
                dimension=score.dimension,
                score=score.score,
                weight=self._weights.get(score.dimension, 0.0),
            )

        # 4. Determine pass/fail
        passed = layer3_result.final_score >= self._pass_threshold
        self._result = self._build_result(
            layer1_result, layer2_result, layer3_result, passed
        )
        yield EvaluationComplete(
            ...,
            passed=passed,
            overall_score=layer3_result.final_score,
            layer2_gate_passed=True,
            feedback_length=len(self._result.feedback),
        )

    async def get_result(self) -> EvaluationResult:
        if self._result is None:
            raise RuntimeError("evaluate() must be called before get_result()")
        return self._result
```

**Key design decisions:**
- `intensity` parameter controls depth (Directive 11):
  - LIGHT_TOUCH: Layer 1 + Layer 2 only, skip Layer 3
  - STANDARD: Full 3-layer stack
  - DEEP: Full stack + factorial probes (Phase 2 stub, same as STANDARD for now)
- `_build_result` generates specific, actionable feedback referencing specific dimension
  scores and failure reasons. Feedback must NOT be generic.
- Pass threshold is configurable (default 60/100)
- All event fields must match events.py field names EXACTLY

### three_pass.py

Three-pass evaluation orchestration wrapper.

```python
class ThreePassEvaluator:
    """Implements the three-pass evaluation architecture (Section 5.10)."""

    async def run(self, output_text: str, contract: SprintContract) -> Layer3Result:
        # Pass 1: Dimensional scoring (delegates to Layer3RubricScorer)
        dimensional_result = await self.scorer.score_all_dimensions(output_text, contract)

        # Pass 2: Gestalt overlay (already integrated in Layer3RubricScorer)
        # The gestalt adjustment is part of the Layer3Result from Pass 1

        # Pass 3: Observation Library scan (STUB for Phase 2)
        # In Phase 2, this queries ObservationLibrary for known patterns
        # matching the current output and adjusts scoring accordingly.
        # For now: no-op, returns the Pass 1+2 result unchanged.
        observation_scan = None  # Phase 2: ObservationLibraryContract.query()

        return dimensional_result
```

Document the Phase 2 interface for Pass 3 in a docstring.

### Build __init__.py

Export everything downstream sessions will need:
```python
from keystone.evaluator.rubric_config import (
    EvaluationProfile, get_profile_weights,
    TIER_1_DIMENSIONS, TIER_2_DIMENSIONS, TIER_1_FLOOR_THRESHOLDS,
    ENGAGEMENT_PROFILE_MAP,
    STRATEGIC_WEIGHT_OVERRIDES,
)
from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.evaluator.layer1_deterministic import Layer1Evaluator
from keystone.evaluator.layer2_citation_gate import Layer2CitationGate, DOIVerifier, HTTPDOIVerifier
from keystone.evaluator.layer3_rubric import Layer3RubricScorer, weighted_geometric_mean
from keystone.evaluator.sprint_contract import SprintContractGenerator
from keystone.evaluator.evaluator import Evaluator
from keystone.evaluator.three_pass import ThreePassEvaluator
```

---

## PHASE 7: TEST FIXTURES + INTEGRATION TESTS

### Test Fixtures

Create realistic fixtures in `tests/fixtures/evaluator/`:

**clean_output.txt:** A well-written 500-800 word research section about competitive
dynamics in the auto insurance telematics market. Include real-sounding analysis,
specific data points, a clear "so what," and proper source attribution. This should
score well (70-85) across most dimensions.

**fabricated_citations.json:** A CitationManifest JSON with 5 citations, where
citation #3 has a fabricated DOI (10.9999/fake.2024.0001). The others have valid-looking
DOIs and URLs. Must match the Citation schema from models/citations.py.

**numerical_inconsistency.txt:** Research output where the text says "revenue grew 15%
year-over-year" but a data table in the same section shows 12.3% growth. Make it
subtle enough that a human might miss it on first read.

**trendslop_output.txt:** A 400-600 word analysis that hits every surface-level checkbox
but contains zero genuine insight. Generic recommendations that could apply to any
company in any industry. "In today's rapidly evolving landscape..." style. This is
the archetype of what the Evaluator must catch.

**mixed_quality.txt:** A research section with one excellent analytical paragraph
(genuine insight, specific data, clear implications) followed by two paragraphs of
trendslop. Tests whether the evaluator can distinguish quality within a single output.

**sample_sprint_contract.json:** A valid SprintContract JSON for a competitive
analysis task. Includes acceptance_criteria, mandatory_elements, anti_patterns.
Must validate against the SprintContract Pydantic model.

**sample_research_task.json:** A valid ResearchTask JSON (competitive_landscape type,
3 tools, anti-confirmatory framing, dependencies, end_product). Must validate against
the ResearchTask Pydantic model.

**Each fixture must be valid against the relevant Pydantic model / JSON schema.**
After creating each fixture, load it into the Pydantic model and assert it validates.

### test_evaluator.py (Integration Tests)

**Full pipeline tests (mock ALL LLM calls with realistic responses):**
- Clean input -> passed=true, score 70-85, all layers run
- Fabricated citation -> passed=false, Layer 3 skipped, feedback mentions fabrication
- Tier 1 failure (Intent Alignment below floor) -> passed=false, Tier 2 skipped
- Events yielded in correct order: DeterministicCheckPassed -> CitationGateResult
  -> RubricDimensionScored (x10) -> EvaluationComplete

**Intensity tests:**
- LIGHT_TOUCH: only Layer 1 + Layer 2 run, no Layer 3, no RubricDimensionScored events
- STANDARD: full stack
- DEEP: same as STANDARD in Phase 1 (stub)

**Contract compliance:**
- `isinstance(evaluator, EvaluatorContract)` — Protocol satisfied at runtime
- evaluate() yields correct event types
- get_result() raises RuntimeError if called before evaluate()

**Feedback quality:**
- Feedback for failed output mentions the specific failure reason
- Feedback for passing output includes per-dimension strengths/weaknesses
- Feedback is non-empty and non-generic

**Profile variance:**
- Different EvaluationProfiles produce different weight distributions in scores
- ESTIMATIVE profile weights differ from DEFAULT on the overridden dimensions

Run: `pytest tests/unit/evaluator/test_evaluator.py -v`

---

## AUDIT CHECKPOINT 4

Run the COMPLETE test suite:
```bash
pytest tests/unit/evaluator/ -v --tb=short
```

**All tests must pass.** Count and report: X tests passing, 0 failing.

Then verify:
1. **Contract compliance:** `Evaluator` satisfies `EvaluatorContract` Protocol
2. **Event compliance:** All 4 L4 events yielded at correct points with correct fields
3. **Model compliance:** `EvaluationResult` matches `models/evaluation.py` types exactly
4. **Directive compliance:**
   - Directive 7: Geometric mean used (not arithmetic mean)
   - Directive 8: Tier 1/Tier 2 split enforced (Tier 1 failure = no Tier 2)
   - Directive 9: retry_llm_call wraps every LLM call, max retries + dead-letter
   - Directive 11: Light/Standard/Deep intensity operational
   - Directive 13: No Phase 2 features implemented:
     - NO Layers 4-5 (process trajectory, diverse judge ensemble)
     - NO Pass 3 (Observation Library scan) — stub only
     - NO sprint contract negotiation — unilateral only
     - NO dimension-specific verification strategies
     - NO more than 4 evaluation profiles
5. **No ownership violations:** Did NOT modify models/*.py, contracts.py, events.py,
   hitl/, citation/ (read-only import only), templates/, samples/
6. **Prompt completeness:** All 14 templates exist, 300-800 words each, all 7 sections

Fix any issues before proceeding.

---

## PHASE 8: FIRST TEST SCENARIO

Run the exact scenario from PHASE-1-IMPLEMENTATION-SPEC.md Component #6:

1. Create a deliberately flawed research output combining:
   - One fabricated citation (DOI that doesn't exist)
   - One numerical inconsistency ("revenue grew 15%" vs. table showing 12%)
   - One trendslop section
   - One genuinely good analytical section

2. Run through the evaluator with mocked LLM responses and verify:
   - **Scenario A:** Input with fabricated citation. Layer 2 catches it and rejects.
     Layer 3 is NOT run. Feedback mentions fabrication.
   - **Scenario B:** Clean input with numerical inconsistency (no fabricated citations).
     Layer 1 catches the numerical error. Layer 3 runs. Numerical issue reported in
     Layer1Result.numerical_inconsistencies.
   - **Scenario C:** Clean input with trendslop section. Layer 3 scores Actionability
     LOW (mock response has score < 40). Mock Intent Alignment below floor (35/100).
     Tier 1 failure triggers rejection BEFORE Tier 2 runs.
   - **Scenario D:** Clean input with the good analytical section. All layers pass.
     Analytical Depth scores HIGH (mock response has score > 75).
   - **Verify geometric mean:** Take the 10 mock dimension scores from Scenario D and
     compute the geometric mean BY HAND. Compare against the evaluator's weighted_total.
     They must match within 0.01.

Add these as test functions in test_evaluator.py if not already covered.

---

## FINAL AUDIT

Run one last comprehensive check:

```bash
# Full test suite
pytest tests/unit/evaluator/ -v --tb=long

# Import check
python -c "from keystone.evaluator import Evaluator, EvaluationProfile, LLMCallable"

# Prompt word counts
wc -w src/keystone/evaluator/prompts/*.md

# File count
find src/keystone/evaluator/ -type f | wc -l
find tests/unit/evaluator/ -type f | wc -l
find tests/fixtures/evaluator/ -type f | wc -l

# Line counts for core modules
wc -l src/keystone/evaluator/*.py
```

Print a final summary:
- Total files created
- Total lines of code
- Total tests passing
- Prompt template count and word count range
- Any Phase 2 stubs noted
- Any issues or concerns

---

## SESSION COMPLETION

Write entry to `SESSION-LOG.md` including:
- Date and session identifier
- All files created with line counts
- All test results (total count, all passing)
- Prompt template word counts per file
- Key design decisions: STRATEGIC_WEIGHT_OVERRIDES values, LLMCallable pattern,
  DOIVerifier Protocol, retry strategy
- Phase 2 deferred items: Layers 4-5, Pass 3, sprint negotiation,
  dimension-specific verification, 8-10 profiles
- Handoff to Component #10 (Calibration): "Evaluator is ready for calibration.
  Needs 10+ Jack-scored deliverables. Target: 0.80+ Spearman correlation."
````

---

## Execution Sequence

**Immediate (Evaluator session):**

| Session | Duration | Produces | Blocks |
|---------|----------|----------|--------|
| **Evaluator** (Component #6) | **4-6 hrs** | Full L4 eval stack (37 files) | Phase 1D-1 (#7) |

**After Evaluator completes:**

| Session | Depends On | Duration |
|---------|-----------|----------|
| Phase 1D-1 (#7 Content Structuring) | Evaluator | TBD |

**Parallel with Evaluator (using Track 2 results):**

| Session | Depends On | Duration |
|---------|-----------|----------|
| Phase 1B-1 (#3a Source Discovery) | Track 2C (done: KEEP pgvector) | 1-2 weeks |
| Phase 1B-2 (#4 MCP Gateway) | Track 2B (done: EXTRACT from mcp-gateway) | 1 week |

**Still blocked by Track 3 (casing books):**

| Session | Depends On |
|---------|-----------|
| Phase 1C-1 (#5 Spec Engine) | 1A-1, 1A-3, Track 3 |
