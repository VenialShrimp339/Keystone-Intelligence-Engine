# Current State
*Last updated: 2026-04-06 | Updated by: Session 15 (Overnight Audit + Cleanup)*

---

## Where we are

**Phase:** Phase 1 build in progress. Components #1, #2, #3b, #4, #5, #6, and #HITL are complete and audited. Overnight session audit completed with all fixes applied.

**Audit completed:** Full acceptance criteria audit of all 7 built components. One critical cross-session integration bug found and fixed (tool name mismatch between Spec Engine and Gateway). datetime deprecation warnings eliminated. Dependencies trimmed. docs/ARCHITECTURE.md regenerated.

**Next immediate step:** Component #7 (Research Agent Pipeline). Unblocked by Components #4 and #5.

## What was completed (Session 15 -- Overnight Audit + Cleanup)

Audit and fixes:
- **Tool name mismatch fixed:** Created `src/keystone/tool_names.py` as single source of truth. 9 of 11 tool names in Spec Engine templates were mismatched with Gateway registrations. Both now import from shared ToolName enum. 4 unregistered tools removed from templates.
- **datetime.utcnow() fixed:** Replaced with datetime.now(UTC) in 4 source files and 5 test files. Test warnings: 207 -> 0.
- **pyproject.toml trimmed:** Removed 11 unused dependencies. Documented as comments for when components need them.
- **docs/ARCHITECTURE.md regenerated:** Now reflects actual codebase state (was stale since Session 6).
- **Per-component acceptance criteria audit:** MET/UNTESTED/UNMET tables in audit/OVERNIGHT-AUDIT-RESULTS.md.
- **L2/L3 resolved:** Confirmed as Phase 2 deferrals, not a gap. MVP pipeline: L0 -> L1 -> CitProc -> L1.5 -> L4 -> Markdown.

## Known test coverage gaps

These acceptance criteria are UNTESTED (code appears correct, but no test verifies the behavior):
1. Real MCP server connectivity (Component #4) -- all calls through MockMCPClient
2. Anti-slop detection scoring (Component #6) -- prompts contain language, no behavioral test
3. Task type diversity (Component #5) -- no test asserts both estimative and current types
4. Underspecified question rejection (Component #5) -- no vague-input test
5. HITL Web UI -- deliberately deferred to CLI/REST

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

## What's blocked

| Blocker | Needed for | Action |
|---------|-----------|--------|
| API keys: Exa, Brave Search | Component #7 | Jack signs up. Both have free tiers. |
| PostgreSQL + pgvector infrastructure | Component #3a | Defer; use MCP search for MVP. |
| Jack provides 10+ scored deliverables | Component #10 | Not until pipeline produces output. |
| Exemplar library (casing books) | Component #5 quality improvement | Content investment by Jack + team |

## Key architectural decisions (all settled)

1-27: See previous CURRENT-STATE.md entries (all validated, unchanged).

28. **Shared tool name constants** (Session 15): `tool_names.py` ToolName StrEnum is the single source of truth for all MCP tool identifiers. Both Gateway and Spec Engine import from it.
29. **L2/L3 are Phase 2** (Session 15): MVP pipeline goes L0 -> L1 -> CitProc -> L1.5 -> L4 -> Markdown. ContentStructuringContract and GenerationContract exist as Phase 2 hooks.
