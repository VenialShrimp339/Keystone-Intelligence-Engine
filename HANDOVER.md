# Handover

Last updated: 2026-04-17
Session: Post-audit remediation (Streams A + B cleanup)

## What Changed (Audit remediation)

Three fixes from the Stream A + Stream B audit report landed in this pass.
Nothing else was touched.

- **`SprintContractNegotiated` → `SprintContractProposed`.** The event
  was misnamed: the underlying `SprintContractGenerator` is documented as
  "Phase 1 unilateral proposal," with bidirectional negotiation deferred
  to Phase 2 (Directive #13). Renamed across `events.py`, the L2
  contract docstring, `ContentStructurer`, and every test.
- **`frameworks_for_engagement` + `primary_framework` accept an override.**
  New optional `override: list[FrameworkHint] | None` parameter bypasses
  the default engagement-type → framework mapping. `ContentStructurer`
  constructor now takes `frameworks_override` and threads it through.
  This gives the Specification Engine a seam to inject custom frameworks
  for engagements that don't fit the five canonical types (Directive #1
  "predefined types are templates, not constraints"). An explicit empty
  list is respected — it signals "no framework applies," not "fall back
  to defaults."
- **`edgartools` and `docling` moved to optional extras.** Both are
  now under `[project.optional-dependencies]` as `retrieval-edgar`,
  `retrieval-docling`, and a combined `retrieval` extra. Minimal
  installs no longer pull torch + the 258M Granite-Docling model. Import
  gating was already in place: docling is imported lazily inside
  `DoclingBackend._build_default_converter` (the `ImportError` branch
  already returns a `DOCLING_UNAVAILABLE` warning), and edgartools is
  referenced only as a subprocess command string in `servers.py` — it is
  never imported by Keystone code.

Test delta: **1027 passed** (+4 new `TestFrameworkSelection` cases for
override, empty-override, mandatory-first selection, and structurer
threading). Zero new ruff errors on touched files. mypy strict delta is
zero (baseline error in `contracts.py:376` is pre-existing and
unrelated).

## Changed files (Audit remediation)

| File | Change |
|---|---|
| `src/keystone/events.py` | Renamed `SprintContractNegotiated` → `SprintContractProposed`; added docstring note about Phase 1/Phase 2 framing; updated `AnyPipelineEvent` union. |
| `src/keystone/contracts.py` | Updated `ContentStructuringContract.structure` docstring to reference the renamed event. |
| `src/keystone/structuring/framework_selector.py` | Added `override` parameter to `frameworks_for_engagement` and `primary_framework`. Module docstring cites Directive #1. |
| `src/keystone/structuring/content_structuring.py` | Renamed event import/yield; added `frameworks_override` constructor parameter; threaded override through `frameworks_for_engagement` and `primary_framework`. |
| `pyproject.toml` | Moved `edgartools` and `docling` out of `dependencies` into `[project.optional-dependencies]` (`retrieval-edgar`, `retrieval-docling`, `retrieval`). |
| `tests/unit/structuring/test_content_structuring.py` | Renamed event references; added 4 override tests. |
| `tests/unit/pipeline/test_orchestrator.py` | Renamed event references. |

## Install note

Runtime retrieval backends are now opt-in:

```bash
pip install -e ".[dev]"                  # tests + tooling, no retrieval extras
pip install -e ".[dev,retrieval]"        # add edgartools + docling
pip install -e ".[dev,retrieval-edgar]"  # EDGAR only
```

---

## Previous session: Stream A -- Retrieval Depth (EDGAR + deep research + Docling)

## What Changed (Stream A)

- Added `edgartools` MCP server integration in the gateway: three tool
  names (`edgar_filings`, `edgar_financials`, `edgar_company_facts`)
  share one upstream server (`edgartools-mcp`), declare the SEC
  `EDGAR_IDENTITY` User-Agent contract, and are rate-limited to SEC's
  10 req/sec cap through the new `SERVER_RATE_LIMITS` /
  `build_default_rate_limits` helpers.
- Wrote 20 new gateway tests covering EDGAR registration, SEC
  compliance config, shared-bucket rate limiting, authorization, tool
  discovery, description-budget headroom, and end-to-end MCPGateway
  dispatch.
- Added 26 unit tests for `ResearchAgent` deep mode (prompt
  construction, response parsing, event emission, shallow fallback,
  absence-report generation) and 12 unit tests for the underlying
  `_call_claude_cli_research` subprocess transport (argv, timeout,
  non-zero exit, concurrency cap, UTF-8 decode). None hit real
  `claude -p` or web traffic.
- Built the Docling PDF backend at
  `src/keystone/retrieval/docling_backend.py`. `DoclingBackend`
  implements the existing `PDFTextBackend` protocol, lazy-loads
  docling, captures errors as warning codes, and slots into
  `PDFParser(backend=DoclingBackend())`. 19 new tests drive it with an
  in-process fake converter -- the real docling library is never
  imported during tests.
- Registered `edgartools>=5.0.0` and `docling>=2.0.0` in
  `pyproject.toml`; added mypy overrides for `edgartools.*`,
  `edgar.*`, and `docling_core.*`.
- Full unit suite: **1023 passed** (was 1004 pre-session; +19 net
  after accounting for the adjusted `test_tool_registry` counts).
  `ruff check` clean on every new or touched file. `mypy --strict`
  clean on `servers.py`, `tool_names.py`, and `docling_backend.py`.

## New files (Stream A)

| File | Purpose |
|---|---|
| `src/keystone/retrieval/docling_backend.py` | `DoclingBackend` PDF text extractor using the Granite-Docling pipeline; lazy import + defensive error handling. |
| `tests/unit/gateway/test_edgar_integration.py` | 20 tests: EDGAR MCP registration, SEC User-Agent + rate-limit contract, shared-bucket behaviour, gateway dispatch. |
| `tests/unit/research/test_research_agent_deep.py` | 26 tests: deep-mode prompt construction, response parsing, events, fallback to shallow. |
| `tests/unit/test_llm_client_deep_research.py` | 12 tests: `_call_claude_cli_research` subprocess argv / timeout / exit handling + `get_deep_research_callable`. |
| `tests/unit/retrieval/test_docling_backend.py` | 19 tests: DoclingBackend happy path, failure modes, PDFParser integration. |

## Changed files (Stream A)

| File | Change |
|---|---|
| `src/keystone/tool_names.py` | Added `EDGAR_FINANCIALS`, `EDGAR_COMPANY_FACTS`, and the `EDGAR_TOOLS` grouping constant. |
| `src/keystone/gateway/servers.py` | Added `EDGAR_IDENTITY_ENV`, `EDGAR_MAX_REQ_PER_SEC`, `EDGAR_SERVER_NAME`; expanded EDGAR to three tool entries sharing one server; added `SERVER_RATE_LIMITS` + `build_default_rate_limits()`. |
| `src/keystone/retrieval/__init__.py` | Exports `DoclingBackend` + `DOCLING_PIPELINE_TAG`. |
| `pyproject.toml` | Added `edgartools`, `docling` deps; mypy overrides for `edgartools.*`, `edgar.*`, `docling_core.*`. |
| `tests/unit/test_tool_registry.py` & `tests/unit/gateway/test_tool_registry.py` | Updated tool-count assertions: `len(TOOL_CONFIGS) == 9`, `unique_server_count == 7`. |

## Design Choices (Stream A)

- **EDGAR = one server, three tool names.** All three EDGAR tool
  entries use `server_name="edgartools-mcp"` so the gateway's rate
  limiter, circuit breaker, and audit log aggregate per-agency.
  Agents can be authorized for a subset (e.g. financials-only) but
  can never collectively exceed SEC's 10 req/sec ceiling because the
  token bucket is shared at the server level.
- **SEC User-Agent via `EDGAR_IDENTITY`.** edgartools reads the
  identity string from that env var. Every EDGAR tool's
  `config.identity_env` points at it so deployment docs have a single
  source of truth. `rate_limit_per_second: 10` is recorded in the
  config dict as a documentation aid alongside the enforced bucket in
  `SERVER_RATE_LIMITS`.
- **DoclingBackend is lazy.** Docling is an expensive dependency
  (torch + the 258M Granite-Docling model). The backend stores an
  optional injected converter and only imports docling on the first
  `extract` when one was not supplied. Tests never touch the real
  library.
- **DoclingBackend never raises.** Empty bytes, non-PDF input, docling
  `ImportError`, conversion exceptions, encrypted PDFs, and non-SUCCESS
  status all degrade to empty pages + a warning code, matching the
  existing `BasicPDFTextBackend` vocabulary so downstream scoring
  logic stays uniform.
- **Deep-mode tests mock subprocess at the boundary.** The `_FakeProc`
  helper captures kill / wait / communicate calls without spawning a
  real process; `_patched_create` records argv so regression tests can
  pin `--allowedTools WebSearch,WebFetch`, `--no-session-persistence`,
  the 1200s default timeout, and Sonnet model selection.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/ -q                                    # 1023 tests
pytest tests/unit/gateway/test_edgar_integration.py -q   # 20 EDGAR tests
pytest tests/unit/research/test_research_agent_deep.py -q
pytest tests/unit/test_llm_client_deep_research.py -q
pytest tests/unit/retrieval/test_docling_backend.py -q
ruff check <new paths>                                   # clean
mypy src/keystone/gateway/servers.py \
     src/keystone/retrieval/docling_backend.py           # clean
```

## Integration Shape (Stream A)

```python
# EDGAR: agents request any of three tool names; gateway aggregates
# traffic through the same edgartools-mcp server under one rate bucket.
from keystone.gateway.servers import build_default_rate_limits, register_all_tools
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.tool_registry import ToolRegistry

limiter = InMemoryRateLimiter(build_default_rate_limits())
registry = ToolRegistry()
register_all_tools(registry)  # edgar_filings + edgar_financials + edgar_company_facts

# Docling: swap the PDF backend at construction time. Pure stdlib
# BasicPDFTextBackend still works for simple PDFs; DoclingBackend
# handles complex layouts and tables.
from keystone.retrieval import DoclingBackend, PDFParser

parser = PDFParser(backend=DoclingBackend())
parsed = parser.parse(fetched_artifact)
```

## Gotchas (Stream A)

- DoclingBackend ships without docling installed; the first `extract`
  call on a system without docling returns warning code
  `DOCLING_UNAVAILABLE` (empty pages). `pyproject.toml` declares docling
  as an optional extra under `retrieval-docling` (post-audit) — install
  with `pip install -e ".[retrieval]"` when you need it.
- `SERVER_RATE_LIMITS` is a declarative default. Existing call sites
  still build ad-hoc limiters (e.g. `test_research_agent.py`). The
  helper exists for production wiring and tests that want
  SEC-accurate throttling.
- Changing the number of registered MCP tools requires updating
  `tests/unit/test_tool_registry.py::TestServerConfigs` and
  `tests/unit/gateway/test_tool_registry.py::TestServerConfigs`
  (they now assert `len(TOOL_CONFIGS) == 9` and
  `unique_server_count == 7`).

## Next Steps (Stream A)

- Wire `build_default_rate_limits()` into the production gateway
  initialization so EDGAR traffic is clamped at 10 req/sec without
  per-caller configuration.
- Real-MCP phase: plug a FastMCP-based client into the gateway so the
  `edgartools-mcp` stdio server is actually spawned; the current
  `MockMCPClient` only validates registry + routing wiring.
- DoclingBackend: once docling is installed, add an integration smoke
  test that parses a real SEC filing PDF and verifies table-extraction
  quality.

## What Did Not Change (Stream A)

- No modifications to orchestrator, deliberation, evaluator, citation
  processor, spec engine, content structurer, or renderer.
- No modifications to Lane E parsers (`article_parser.py`,
  `pdf_parser.py`, `evidence_normalizer.py`) -- DoclingBackend is a
  new drop-in backend; `PDFParser` itself is unchanged.
- No changes to the deep-research prompt or parsing logic in
  `research_agent.py`. The 26 new tests only observe existing
  behaviour.

---

## Prior session: Stream B -- L2 Content Structuring (output quality)

- **Built L2 Content Structuring** between L1.5 Deliberation and L4
  Evaluator. Previously the pipeline went
  L0 -> L1 -> CitProc -> L1.5 -> L4 -> Render; it now runs
  L0 -> L1 -> CitProc -> L1.5 -> **L2** -> L4 -> Render.
- New package `src/keystone/structuring/` (3 files, 738 lines):
  `ContentStructurer`, `filter_outline_by_passed_tasks`,
  `frameworks_for_engagement`, `primary_framework`,
  `render_task_section_text`.
- New model module `src/keystone/models/structuring.py` (171 lines):
  `StructuredOutline`, `StructuredSection`, `OutlineItem`,
  `AnalyticalFramework`, `FrameworkHint`, `OutlineSectionType`,
  `OutlineItemType`.
- Orchestrator now builds an `outline`, drafts per-task section text,
  and negotiates per-task sprint contracts through L2; the L4 eval
  loop consumes those artifacts directly.
- `MarkdownRenderer.render()` gained an optional
  `outline: StructuredOutline | None` parameter; when present it
  renders an "Analytical Framework" section derived from the
  engagement type.
- `ContentStructuringContract` Protocol in `contracts.py` updated to
  the real L2 signature; `test_protocol_contracts.py` now verifies
  `ContentStructurer` conforms.
- Stream B tests: 31 new (27 L2 + 3 renderer outline + 1 Protocol
  conformance). End of Stream B: 1004 / 1004 unit tests pass.

(Design notes, integration shape, and gotchas for Stream B were
recorded at session end; see commit history for the detailed log.)

## Still open

- Fix stale import in `tests/integration/test_evaluator_live.py`
  (`_parse_score_json` removed from `layer3_rubric.py`). Not blocking
  unit tests.
- Pre-existing canary failures noted by Stream B
  (`tests/canary/test_architectural_guarantees.py` governance flag
  threshold).
- Bidirectional sprint-contract negotiation between
  `SprintContractGenerator` and the Evaluator (Phase 2).
- LLM-augmented framework execution in L2 (currently only labels
  sections; does not populate framework artifacts).
