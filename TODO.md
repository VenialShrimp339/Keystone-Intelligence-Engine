# TODO

## Active

- [ ] Wire `build_default_rate_limits()` into the production gateway init so EDGAR traffic is clamped at SEC's 10 req/sec without per-caller configuration
- [ ] Orchestrator: pipe Lane E normalizer output into `AgentPool(evidence_provider=...)`
- [ ] Fix stale import in `tests/integration/test_evaluator_live.py` (`_parse_score_json` removed from `layer3_rubric.py`)

## Up Next

- [ ] Real-MCP phase: FastMCP-based client replacing `MockMCPClient` so `edgartools-mcp` (and the other stdio servers) actually launch
- [ ] DoclingBackend integration smoke test against a real SEC filing PDF once docling is installed
- [ ] L2 Phase 2: LLM-augmented framework execution (Five Forces matrix, scenario shocks, Value Chain stage analysis)
- [ ] L2 Phase 2: bidirectional sprint-contract negotiation (Generator proposes, Evaluator counter-proposes) — schema already supports via `SprintContractProposed` event and negotiation-ready data structure
- [ ] Outline-driven rendering: let `StructuredOutline` drive section order + headers in the final deliverable (currently used only for the Analytical Framework section)
- [ ] Extend canary `test_pipeline_fresh_components_per_run` to assert `content_structurer` freshness across runs
- [ ] Task-aware evidence selection (replace default "all records" with filter keyed off `ResearchTask.required_sources` / category / source_family)
- [ ] Deep-mode EV-ref enforcement (so deep-mode Citations keep Lane E SHA-256 + locator)
- [ ] Pre-existing canary failures in `tests/canary/test_architectural_guarantees.py` (unrelated to L2 or Lane E)
- [ ] Branch/worktree consolidation (cosmetic, not blocking)

## Done

- [x] **Audit remediation (Streams A + B)** — 1027 / 1027 unit tests pass. Zero new ruff errors on touched files; mypy delta zero.
  - Renamed `SprintContractNegotiated` → `SprintContractProposed` across `events.py`, `contracts.py`, `content_structuring.py`, and both tests (`test_content_structuring.py`, `test_orchestrator.py`). Event name now matches the Phase-1 "unilateral proposal" semantics documented by `SprintContractGenerator`.
  - Added `override: list[FrameworkHint] | None` to `frameworks_for_engagement` + `primary_framework` and `frameworks_override` to `ContentStructurer.__init__`. Gives the Spec Engine a seam for novel engagements per Directive #1. Four new tests cover default/override/empty-override/mandatory-selection paths and structurer threading.
  - Moved `edgartools` and `docling` out of hard `dependencies` into optional `retrieval-edgar`, `retrieval-docling`, and combined `retrieval` extras. docling imports were already lazy inside `DoclingBackend._build_default_converter`; edgartools is only a subprocess command string. No code gating needed — graceful degradation already in place (`DOCLING_UNAVAILABLE` warning).
- [x] **Stream A: Retrieval Depth (EDGAR + deep research + Docling)** — 1023 / 1023 unit tests pass. Zero new ruff on touched files; mypy strict clean on new source.
  - EDGAR gateway: `src/keystone/gateway/servers.py` (three EDGAR tool entries under one server, `SERVER_RATE_LIMITS`, `build_default_rate_limits`, `EDGAR_IDENTITY_ENV`), `src/keystone/tool_names.py` (new `EDGAR_FINANCIALS`, `EDGAR_COMPANY_FACTS`, `EDGAR_TOOLS`)
  - Docling backend: `src/keystone/retrieval/docling_backend.py` (new), `src/keystone/retrieval/__init__.py` (exports)
  - Dependencies: `pyproject.toml` (edgartools + docling + mypy overrides)
  - Tests: `tests/unit/gateway/test_edgar_integration.py` (20 new), `tests/unit/research/test_research_agent_deep.py` (26 new), `tests/unit/test_llm_client_deep_research.py` (12 new), `tests/unit/retrieval/test_docling_backend.py` (19 new)
  - Test-count migration: `tests/unit/test_tool_registry.py`, `tests/unit/gateway/test_tool_registry.py` (9 tools, 7 unique servers)
- [x] **L2 Content Structuring (Stream B)** — `ContentStructurer` + framework selector + section-text renderer + outline filter; wired between L1.5 and L4; owns sprint-contract negotiation. 31 new unit tests.
  - `src/keystone/models/structuring.py` (new)
  - `src/keystone/structuring/__init__.py` (new), `framework_selector.py` (new), `section_text.py` (new), `content_structuring.py` (new)
  - `src/keystone/pipeline/orchestrator.py`, `markdown_renderer.py`, `contracts.py`
  - `tests/unit/structuring/test_content_structuring.py` (new, 27 tests) + renderer + orchestrator + protocol conformance updates
- [x] **Lane E -> research bridge** — `evidence_context.py` (provider + Citation conversion), shallow-mode EV-NNN refs, deep-mode background block, AgentPool threading, 31 unit tests, zero new ruff/mypy errors
  - `src/keystone/research/evidence_context.py` (new)
  - `src/keystone/research/research_agent.py` (accept evidence_provider, resolve EV refs)
  - `src/keystone/research/agent_pool.py` (propagate evidence_provider)
  - `src/keystone/research/__init__.py` (exports)
  - `tests/unit/research/test_evidence_context.py` (new)
- [x] **Lane E: Article/PDF parse + evidence normalization** — 6 source files, 4 test files, 82 tests, mypy-strict clean
- [x] Core pipeline L0 -> L4 -> Render
- [x] Lane H: governed document fetch (commit `93a5ca8`, not in current branch)
- [x] Project scaffolding: CLAUDE.md, HANDOVER.md, venv, hooks
