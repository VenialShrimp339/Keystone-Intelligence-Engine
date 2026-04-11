# Overnight Session Audit Results
*Date: 2026-04-06 | Auditor: Claude Code (Opus 4.6, Session 15)*

---

## Critical Finding: Tool Name Mismatch (FIXED)

9 of 11 tool name strings in `specification/template_registry.py` did not match `gateway/servers.py` registrations. Only `exa_search` and `brave_search` matched. Would have caused runtime auth failures when Component #7 routes tool calls through the gateway.

**Root cause:** Sessions 1A-4 (Gateway) and 1A-6 (Spec Engine) ran in parallel, independently choosing string identifiers for the same tools.

**Fix applied:** Created `src/keystone/tool_names.py` with a `ToolName` StrEnum as single source of truth. Both gateway and spec engine now import from it. 4 unregistered tool names (`news_search`, `industry_reports`, `patent_search`, `government_search`) removed from templates until MCP servers are available.

---

## L2/L3 Pipeline Layer Resolution

L2 (Content Structuring) and L3 (Deliverable Generation) are intentionally absent from Phase 1. The MVP pipeline routes L1.5 output directly to L4 for evaluation, then to Markdown. Contracts for both exist in `contracts.py` (Phase 2 hooks). This is consistent with Directive 5.

---

## Per-Component Acceptance Criteria Audit

### Component #4: MCP Gateway

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Structural tool authorization | MET | auth.py, test_auth.py (8 tests) |
| 2 | Rate limiter | MET | rate_limiter.py, test_rate_limiter.py (11 tests) |
| 3 | Circuit breaker (3 failures, 30s recovery) | MET | circuit_breaker.py, test_circuit_breaker.py (10 tests) |
| 4 | Audit log with full context | MET | audit_log.py, test_audit_log.py (11 tests) |
| 5 | 3+ MCP servers incl HTTP + stdio | UNTESTED | 7 configs exist, but MockMCPClient only |
| 6 | paper-search-mcp callable | PARTIALLY MET | Registered; not callable (mock) |
| 7 | Finnhub callable | PARTIALLY MET | Registered; not callable (mock) |
| 8 | transport_type + security_approved fields | MET | ToolEntry model, all 7 entries populated |
| 9 | Tool descriptions < 10K tokens | MET | get_description_budget(), tested |
| 10 | Retry + dead-letter on all loops | MET | MAX_RETRIES=3, DeadLetter, tested |

### Component #6: Evaluator Stack

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Layer 1 catches numerical inconsistencies | MET | layer1_deterministic.py, test_layer1.py |
| 2 | Layer 2 rejects fabricated DOI | MET | layer2_citation_gate.py, test_layer2.py |
| 3 | 10 dimensions scored independently | MET | 10 prompt files, test_layer3.py |
| 4 | Tier 1 floor gates enforced | MET | rubric_config.py, test_rubric_config.py |
| 5 | Geometric mean aggregation | MET | layer3_rubric.py, hand-verified math |
| 6 | 3-4 engagement-type profiles | MET | 4 profiles (DEFAULT, ESTIMATIVE, CURRENT, STRATEGIC) |
| 7 | Anti-slop sub-check | UNTESTED | Prompt templates contain anti-slop language; no dedicated test |
| 8 | Gestalt overlay +/-5-10% | MET | _gestalt_overlay(), clamped [-10, +10] |
| 9 | No dimension-specific verification (Phase 2) | MET | Correctly deferred |

### Component #3b: Knowledge Accumulation

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | raw/ receives unmodified artifacts | MET | write_raw(), test_engagement_store.py |
| 2 | compiled/ receives synthesized summaries | MET | _render_compiled(), test_wiki_builder.py |
| 3 | INDEX.md auto-updates | MET | index_maintainer.py, 6 tests |
| 4 | Content-hash provenance per proposition | MET | content_hasher.py, 8 tests |
| 5 | Storage-agnostic (no direct fs calls) | MET | WikiStore Protocol, no pathlib in wiki_builder.py |

### Component #5: Specification Engine

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | RESEARCH.md with all required fields | MET | _build_research_spec(), test_spec_engine.py |
| 2 | 10+ tasks with DAG, anti-confirmatory, end_product | MET | task_generator.py, Kahn's algorithm |
| 3 | Both estimative and current task types | UNTESTED | Mock LLM; no test for type diversity |
| 4 | 3-5 tools per task from gateway | MET (code) | _resolve_tools() works; tool names NOW aligned |
| 5 | Rejects underspecified questions | UNTESTED | intent_clear flag exists; no vague-input test |
| 6 | Issue tree with all fields | MET | EngagementSpec populated, verified |
| 7 | Template registry matches standard/custom | MET | 3-signal scoring, 9 tests |
| 8 | HITL gate blocks until approval | MET | _trigger_hitl_gate(), tested via mock |
| 9 | Schema validation catches malformed output | MET | DAG cycle detection, tested |

### Component #HITL

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Gate 1 blocks after EngagementSpec | MET | create_and_wait_for_gate(), tested |
| 2 | Gate 2 blocks after DeliberationResult | MET | Same function, different gate_type |
| 3 | Approve resumes with no changes | MET | test_gate.py |
| 4 | Modify resumes with modifications | MET | modifications_json preserved, tested |
| 5 | Reject halts pipeline | MET | GateRejectedError, tested |
| 6 | REST API < 100ms | MET | In-process FastAPI |
| 7 | Maps to Temporal Signals | MET | Only polling mechanism changes |
| 8 | Web UI displays artifacts | UNMET | Deliberately deferred to CLI/REST |

---

## Consolidated Test Coverage Gaps

These acceptance criteria are UNTESTED across all components:

1. **Real MCP server connectivity** (Component #4) -- All calls through MockMCPClient
2. **Anti-slop detection behavior** (Component #6) -- Prompts contain language; no test verifies low scores on trendslop
3. **Task type diversity** (Component #5) -- No test asserts both estimative and current types generated
4. **Underspecified question rejection** (Component #5) -- No test for vague inputs
5. **HITL Web UI** (Component #HITL) -- Deliberately deferred

---

## Other Fixes Applied

1. **datetime.utcnow() replaced with datetime.now(UTC)** in 4 source files and 5 test files. Test warnings dropped from 207 to 0.
2. **pyproject.toml trimmed** to only currently-imported dependencies. Unused packages documented as comments for when their components are built.
3. **docs/ARCHITECTURE.md regenerated** from actual codebase state.

---

## Cross-Session Integrity (Verified Clean)

- **contracts.py:** 9 Protocol classes, no duplicates, no conflicts
- **events.py:** 34 events, AnyPipelineEvent union complete, no duplicates
- **models/__init__.py:** Clean re-exports, no conflicts
- **pyproject.toml:** Not modified by unauthorized sessions
