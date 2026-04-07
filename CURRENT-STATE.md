# Current State
*Last updated: 2026-04-07 | Updated by: Session 4a-10 (Wave 4a Research Agent + MCP Gateway Pressure Test)*

---

## Where we are

**Phase:** Phase 1 build complete. All 10 components + pipeline orchestrator + LLM client built. Wave 4a pressure testing in progress (4 parallel sessions). Sessions 10 and 12 complete.

**Wave 4a status:** Sessions 10 (Research Agents) and 12 (Deliberation + CitationProcessor) complete. 43 integration tests pass with real GPT-5.4 + real search API calls. 4 bugs found and fixed total. Sessions 9 and 11 running in parallel.

**Next immediate step:** Merge Wave 4a results from all 4 sessions. Then Wave 4b (full pipeline end-to-end integration).

## What was completed (Session 4a-10 -- Research Agent + MCP Gateway Pressure Test)

First real LLM + real search API integration of L1 Research Agents and MCP Gateway:
- **16 integration tests written and passing** (6 baseline + 5 probing + 5 infrastructure)
- **~20 real GPT-5.4 LLM calls** + **~12 real Exa/Brave search API calls** via Codex OAuth
- **3 bugs found and fixed** in `research_agent.py`: JSON parser didn't handle markdown fences or trailing text, absence report could return empty list
- **SimpleMCPClient created** (`gateway/simple_client.py`): real HTTP calls to Exa and Brave Search APIs
- **Search APIs work well:** Both Exa and Brave return 5 relevant results per query for market sizing topics
- **Citation URL liveness: 62%** (8/13 live) -- dead URLs from market research 403s and truncated Exa snippets
- **Parallel agents work:** AgentPool runs 2 agents concurrently, both produce 20+ claims
- **Error recovery works:** Failed tools get dead-lettered, agent continues with remaining tools
- **Structural enforcement validated:** FindingWriter correctly rejects unsubstantiated claims (no citations)

## What was completed (Session 4a-12 -- Deliberation + CitationProcessor Pressure Test)

First real LLM integration test of L1.5 Deliberation and CitationProcessor:
- **27 integration tests written and passing** (13 citation, 14 deliberation)
- **12 real GPT-5.4 calls** via Codex OAuth (~3,136 prompt + ~4,736 response tokens)
- **1 bug fixed:** `citation/url_check.py` lacked User-Agent header; sites returned 403 for bare httpx requests
- **0 JSON parsing failures:** GPT-5.4 produces clean JSON for all analyst/judge/WWHTB prompts
- **Confidence map validated:** 2 high, 3 moderate, 4 contested claims across 9 total
- **WWHTB works:** 7 assumption-elicitation calls produced specific, testable assumptions
- **Gap detection works:** 4 gaps + 4 absence items correctly sourced from agent findings

## Known test coverage gaps

These acceptance criteria are UNTESTED (code appears correct, but no test verifies the behavior):
1. ~~Real MCP server connectivity (Component #4)~~ -- **RESOLVED Session 10**: SimpleMCPClient makes real Exa/Brave calls
2. Anti-slop detection scoring (Component #6) -- prompts contain language, no behavioral test (Session 11 may address)
3. Task type diversity (Component #5) -- no test asserts both estimative and current types (Session 9 may address)
4. Underspecified question rejection (Component #5) -- no vague-input test (Session 9 may address)
5. HITL Web UI -- deliberately deferred to CLI/REST
6. SEC.gov URL liveness -- returns 403 for all automated access regardless of User-Agent. Not a code bug but limits citation verification for SEC filings.

## What's next

### Immediate: Component #7 (Research Agent Pipeline)
The single highest-value next step. First real LLM integration. First real tool calls through the gateway.

Build order:
1. Single-agent, single-round implementation with real MCP calls
2. Filesystem isolation per agent
3. Multi-agent parallel execution
4. Iterative research loop (3-round default, 5 max)
5. Error recovery with model fallback chain

### Prerequisites for Component #7
- API keys: Exa and Brave Search (both have free tiers)
- Python 3.12 environment (pyenv 3.12.13 installed)

### After Component #7
- **#8 CitationProcessor** (~60% utilities already built in citation/)
- **#9 Deliberation** (independent analysts + aggregation + HITL Gate 2)
- **#11 End-to-end pipeline test** (minimal: L0 -> L1 -> L4 -> Markdown)

### Can defer
- **#3a Source Discovery** -- MCP search tools (Exa, Brave) provide source discovery without local vector store
- **#10 Evaluator Calibration** -- blocked on Jack providing 10+ scored deliverables

## What's complete

| Item | Session | Key files |
|------|---------|-----------|
| 16 deep research reports analyzed and synthesized | 1 | synthesis/UNIFIED-SYNTHESIS.md, PLAN-CHANGELOG.md |
| CAPSTONE-PLAN-v2.md updated with 17 research-backed changes | 1 | CAPSTONE-PLAN-v2.md (1,294 lines) |
| Plan audited, gaps triaged, implementation spec produced | 2 | audit/PHASE-1-IMPLEMENTATION-SPEC.md, GAP-TRIAGE.md |
| nano-claude-code fully analyzed (56 files, 11.8K lines) | 4 | reference/analysis/00 through 09 |
| 10 deep research reports on Claude Code leak | 5 | reference/analysis/deep-research-01 through 10 |
| Leak research synthesized (~60-65% complete) | 6 | reference/analysis/LEAK-SYNTHESIS.md (45KB) |
| Foundational Pydantic v2 models (8 model files, 50+ classes) | 6 | src/keystone/models/*.py |
| Event type hierarchy (34 events across all layers + HITL) | 6, 14 | src/keystone/events.py |
| Handoff contract interfaces (9 Protocol classes incl. HITL) | 6, 14 | src/keystone/contracts.py |
| Project scaffolding | 6 | pyproject.toml, Makefile, .env.example |
| Code architecture document with coherence check | 6, **15** | docs/ARCHITECTURE.md (**regenerated**) |
| Pre-build audits (gap analysis, code audit, readiness) | 8A/B/C | audit/pre-build/01 through 05 |
| Day 0 fixes: all audit findings resolved | 9 | 7 files modified, 1 deleted |
| Batch 2 deep research prompts designed and audited | 10 | DEEP-RESEARCH-BATCH-PLAN.md |
| Batch 2: 10 deep research reports completed | 10 | research-reports/batch-2/ |
| Batch 2: 10 per-report analyses + master synthesis | 11 | audit/batch-2-analysis/ |
| **Track 1: Architecture finalization (48 changes)** | **12** | **CAPSTONE-PLAN-v2.md, PHASE-1-IMPLEMENTATION-SPEC.md** |
| **Component #1: RESEARCH.md spec format + task DAG** | **1A-1** | **models/{tasks,research}.py, schemas/, templates/, samples/** |
| **Component #2: Citation data model + pipeline utils** | **1A-2** | **models/citations.py, citation/, schemas/** |
| **Component #HITL: Human-in-the-Loop infrastructure** | **14** | **hitl/ (7 files), tests/unit/hitl/ (42 tests)** |
| **Component #6: Evaluator Stack (L4)** | **8** | **evaluator/ (9 modules, 14 prompts, 77 tests)** |
| **Component #4: MCP Gateway** | **1A-4** | **gateway/ (7 modules, 75 tests)** |
| **Component #3b: Knowledge Accumulation** | **1A-5** | **knowledge/ (6 modules, 45 tests)** |
| **Component #5: Specification Engine (L0)** | **1A-6** | **specification/ (10 modules, 9 prompts, 58 tests)** |
| **Overnight audit + cleanup** | **15** | **tool_names.py, OVERNIGHT-AUDIT-RESULTS.md, ARCHITECTURE.md** |
| **Wave 4a: Delib+CitProc pressure test (12 real LLM calls)** | **4a-12** | **tests/integration/test_deliberation_live.py, test_citation_processor_live.py, citation/url_check.py** |
| **Wave 4a: Research Agent+Gateway pressure test (20 LLM + 12 search)** | **4a-10** | **gateway/simple_client.py, tests/integration/test_research_agent_live.py, research/research_agent.py** |

## What's blocked

| Blocker | Needed for | Action |
|---------|-----------|--------|
| ~~API keys: Exa, Brave Search~~ | ~~Component #7~~ | **RESOLVED**: Both keys configured, tested in Session 4a-10 |
| PostgreSQL + pgvector infrastructure | Component #3a | Defer; use MCP search for MVP. |
| Jack provides 10+ scored deliverables | Component #10 | Not until pipeline produces output. |
| Exemplar library (casing books) | Component #5 quality improvement | Content investment by Jack + team |

## Key architectural decisions (all settled)

1-27: See previous CURRENT-STATE.md entries (all validated, unchanged).

28. **Shared tool name constants** (Session 15): `tool_names.py` ToolName StrEnum is the single source of truth for all MCP tool identifiers. Both Gateway and Spec Engine import from it.
29. **L2/L3 are Phase 2** (Session 15): MVP pipeline goes L0 -> L1 -> CitProc -> L1.5 -> L4 -> Markdown. ContentStructuringContract and GenerationContract exist as Phase 2 hooks.
