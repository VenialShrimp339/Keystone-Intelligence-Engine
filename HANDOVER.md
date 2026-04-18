# Handover

Last updated: 2026-04-17
Session: Evaluator Layer 4 — Process Trajectory Evaluation

## What Changed (Layer 4)

Added a fourth evaluation layer that scores the RESEARCH PROCESS, not
the output text. Layers 1-3 can be fooled by a lazy or narrow research
process that happens to produce plausible-sounding prose; Layer 4 reads
the agent's pipeline event trail and surfaces that pattern.

- **New package entry:** `src/keystone/evaluator/layer4_trajectory.py`
  holds the `Layer4Evaluator` class, a frozen `ProcessContext`
  dataclass, deterministic metric extraction (source count, unique
  domains, source-type diversity, tool utilization from `SourceFound`
  events, synthesis round count from `FindingSynthesized` events, issue
  tree sibling coverage, citation quality distribution from the task
  manifest), and deterministic flag computation.
- **New model:** `Layer4Result` in `src/keystone/models/evaluation.py`
  with deterministic metrics, LLM assessment (qualitative score +
  rationale + missed inquiries + skepticism assessment), a composite
  `process_quality_score` (0-100), and a `process_flags` list. Values
  come from the new `ProcessFlag` enum
  (`single_source_type`, `single_domain`, `low_domain_diversity`,
  `no_multi_round`, `low_tool_diversity`, `low_source_count`,
  `coverage_gap`, `no_high_confidence_citations`,
  `missing_anti_confirmatory_evidence`, `narrow_inquiry`).
- **Wire into the Evaluator:** `evaluate()` now accepts an optional
  `process_context`. When provided and Layers 1-3 pass, Layer 4 runs
  after Layer 3; the overall score becomes the weighted geometric mean
  of the L3 final score and the L4 process score (default 80% L3,
  20% L4, tunable via `Evaluator(layer3_weight=...)`). A L1/L2 failure
  or a Tier 1 rubric floor failure still short-circuits — Layer 4
  never lifts a failing content evaluation.
- **New event:** `ProcessTrajectoryScored` (layer `L4`) carries
  `process_quality_score`, `qualitative_score`, source / domain /
  round counts, tool utilization, and `flag_count` for observability.
- **New prompt:** `src/keystone/evaluator/prompts/process_trajectory.md`
  asks a senior research methodologist to assess strategy soundness,
  missed inquiries, anti-confirmatory framing, and source-quality
  appropriateness for the claim types. Output is a strict JSON schema
  with a `qualitative_score`, rationale, missed-inquiry list,
  skepticism assessment, and an `additional_flags` array.
- **Orchestrator plumbing:** `run_with_events` now accumulates each
  agent's event trail into `events_by_agent`, maps `task.id` → the
  `AgentInstance` that handled it, and builds a `ProcessContext` per
  task before calling `evaluator.evaluate(..., process_context=ctx)`.
  When an agent or events are missing, `process_context` is `None` and
  Layer 4 is skipped for that task.
- **Contract:** `EvaluatorContract.evaluate` in `contracts.py` gained
  the `process_context: ProcessContext | None = None` parameter.

Test delta: **1089 passed** (was 1058). 31 new Layer 4 unit tests cover
helpers (`_extract_domain`, `_find_sibling_branch_ids`,
`_blend_layer3_layer4`), deterministic metric extraction from event
trails, each flag rule (good process / narrow research / single-round /
single-domain / low tool diversity / coverage gap / no HIGH-confidence
citations), score blending (critical vs warning penalties, floors,
merge dedup), and the full `Layer4Evaluator` happy path + LLM failure
fallback + unknown-flag silencing. Zero new ruff errors on touched
files. mypy strict clean on `evaluator.py`, `layer4_trajectory.py`,
`events.py`, `models/evaluation.py`.

## New files (Layer 4)

| File | Purpose |
|---|---|
| `src/keystone/evaluator/layer4_trajectory.py` | `Layer4Evaluator`, `ProcessContext`, deterministic metric + flag extraction. |
| `src/keystone/evaluator/prompts/process_trajectory.md` | LLM prompt for strategy / missed inquiries / skepticism assessment. |
| `tests/unit/evaluator/test_layer4_trajectory.py` | 31 tests across helpers, metrics, flags, scoring, and the full evaluator. |

## Changed files (Layer 4)

| File | Change |
|---|---|
| `src/keystone/models/evaluation.py` | Added `ProcessFlag` (StrEnum), `Layer4Result` (deterministic metrics + LLM assessment + `process_quality_score` + flags), and `layer4_results` on `EvaluationResult`. |
| `src/keystone/events.py` | Added `ProcessTrajectoryScored` and extended `AnyPipelineEvent` union. |
| `src/keystone/evaluator/evaluator.py` | Added `layer3_weight` constructor param + `DEFAULT_LAYER3_WEIGHT = 0.8`, optional `process_context` parameter on `evaluate`, Layer 4 step, `_blend_layer3_layer4`, composite score wiring through `_build_result` (new `l4` + `composite_score` args, L4-aware feedback string, emits `Layer4Result` into `EvaluationResult.layer4_results`). |
| `src/keystone/evaluator/__init__.py` | Exports `Layer4Evaluator` and `ProcessContext`. |
| `src/keystone/contracts.py` | `EvaluatorContract.evaluate` signature now includes `process_context: ProcessContext | None = None`. |
| `src/keystone/pipeline/orchestrator.py` | Accumulates per-agent event trail into `events_by_agent`, builds `agent_by_task`, calls `_build_process_context(task, agent_by_task, events_by_agent, spec)` before each evaluator invocation, and passes `process_context=...` through. |

## Design Choices (Layer 4)

- **Deterministic metrics + one LLM call.** Flag rules run entirely
  off event data and the citation manifest — no LLM judgment needed
  for `single_domain`, `no_multi_round`, `low_tool_diversity`, etc.
  The LLM contributes the qualitative score, the missed-inquiries
  list, and the skepticism assessment, each tied to the actual task
  and the sampled source list so the review is subject-specific. The
  prompt explicitly forbids restating the deterministic metrics.
- **Weighted geometric mean, not arithmetic.** `_blend_layer3_layer4`
  uses `exp(w_L3 * log(L3) + w_L4 * log(L4))` so a very weak L4
  drags the composite below the arithmetic mean. An L4 score near
  zero lowers a strong L3 into the 10-20 range — reviewers get a
  loud signal that the process was insufficient, even when the prose
  reads well.
- **L4 never lifts a failing L1/L2/L3.** The composite replaces the
  L3 final score only when Layer 4 actually ran. A Tier 1 floor
  failure returns final_score=0 before Layer 4 is touched, and L2
  fabrication short-circuits at Layer 2. The pass/fail threshold is
  still checked against the composite (default 60).
- **`ProcessContext` is frozen, narrow, and optional.** A dataclass
  bundling `agent_id`, the `ResearchTask`, the `AgentInstance`, the
  agent's events (pre-filtered by the orchestrator), and the
  engagement's issue tree. Frozen to keep Layer 4 from mutating
  shared state. `None` disables L4 rather than crashing, so tests
  and downstream callers can opt in gradually.
- **Tool utilization reads `SourceFound.source_type` first, then
  falls back to `tool://` URL hosts.** Deep-mode agents emit
  `source_type="deep_research"` (a non-tool label); shallow-mode
  agents emit the tool name as `source_type` and also encode it in
  the `tool://` URL scheme. The extractor handles both.
- **Issue-tree coverage is per-task by necessity.** The evaluator
  runs one task at a time, so `issue_tree_branches_covered` is
  simply `[task.issue_tree_branch_id]` if set and the sibling branch
  ids surface as `issue_tree_branches_missed` for the LLM to weigh.
  Engagement-level coverage enforcement stays in governance, not L4.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/ -q                                          # 1089 tests
pytest tests/unit/evaluator/test_layer4_trajectory.py -q       # 31 L4 tests
ruff check <new paths>                                         # clean
mypy src/keystone/evaluator/evaluator.py \
     src/keystone/evaluator/layer4_trajectory.py \
     src/keystone/models/evaluation.py \
     src/keystone/events.py                                    # clean
```

## Integration Shape (Layer 4)

```python
from keystone.evaluator import Evaluator, ProcessContext

# Build ProcessContext from the orchestrator's per-task event trail
context = ProcessContext(
    agent_id=agent.agent_id,
    task=task,
    agent=agent,
    events=events_by_agent[agent.agent_id],
    issue_tree=spec.issue_tree,
)

# Optional: tune composite weighting (default 80/20)
evaluator = Evaluator(llm=flagship_llm, layer3_weight=0.8)

async for event in evaluator.evaluate(
    output_text, contract, task, manifest, spec, process_context=context,
):
    ...  # ProcessTrajectoryScored and EvaluationComplete now carry composite
result = await evaluator.get_result()
assert result.layer4_results is not None
assert result.overall_score <= result.layer3_results.final_score  # L4 lowers or equals
```

## Gotchas (Layer 4)

- **Layer 4 is skipped without a `ProcessContext`.** Backwards
  compatible: callers that don't supply `process_context` get the
  old L3-only composite. Tests that only care about Layers 1-3 need
  no changes.
- **`_blend_layer3_layer4` floors each side at 0.01 before
  logarithm.** A hard-zero L4 score produces a composite near
  `L3^0.8 * 0.01^0.2 ≈ L3^0.8 * 0.4`, not zero. This is intentional
  — the composite should be very low, not nonexistent.
- **Unknown flags from the LLM are dropped silently** (logged at
  debug). Expand `ProcessFlag` if the prompt's vocabulary grows.
- **Tool utilization penalizes more than mere underuse.** A task
  with 3 assigned tools but only 1 exercised scores ≤0.34 and
  triggers `low_tool_diversity`. Tune `_LOW_TOOL_UTILIZATION_MAX`
  if deep-mode agents with a single `deep_research` "tool" flag
  false-positive — in practice deep mode emits `source_type` that
  doesn't match any assigned tool name, so this is a genuine signal
  not a bug.
- **`passed` now keys off the composite.** Downstream code that
  keyed off `overall_score` is unchanged; code that keyed off
  `layer3_results.final_score` for "did the content pass?" should
  keep doing that.

## What Did Not Change (Layer 4)

- No changes to Layer 1 (deterministic), Layer 2 (citation gate), or
  Layer 3 (rubric scoring). All three remain byte-for-byte identical.
- No changes to the CitationProcessor, Deliberation, Content
  Structurer, Specification Engine, or Renderer.
- No changes to the HITL gate, governance policy, or tool registry.

---

## Previous session: Outline-driven rendering — L3 renderer consumes full StructuredOutline

## What Changed (Outline-driven rendering)

The renderer previously consumed only the `FRAMEWORK_ANALYSIS` facet of the
L2 outline and rebuilt every other section from the raw `ConfidenceMap` +
`StructuredFinding` inputs. L2 was paying to build 9 section types and the
renderer was throwing 8 of them away. `MarkdownRenderer` has been rewritten
to traverse `StructuredOutline.sections` end-to-end.

**Section layout (outline-driven path):**

1. Title + engagement metadata
2. **Executive Summary** — confidence distribution line, high-confidence
   headlines with `[HIGH]` badges and inline `[N]` citation refs,
   uncovered-branch caveat
3. **Analytical Framework** — renders from the `FRAMEWORK_ANALYSIS`
   section's items when L2 populated it; falls back to `outline.frameworks`
   for callers that construct outlines without running the full structurer
4. **Key Findings** — one `### subsection` per `BRANCH` section (titled
   by the issue-tree branch); each claim shows tier + confidence badge
   (`[HIGH, 85%]`), inline citations, `Evidence:`, `Caveats:`, and optional
   analytical `note`
5. **Areas of Uncertainty** — subsections for `MODERATE (60-80%)`,
   `WEAK (50-60%)`, `CONTESTED (<50%)`; each carries an italic preamble
   and stamps claims with the tier badge
6. **Evidence Gaps** — `GAPS` (what we looked for but couldn't find),
   `INSUFFICIENT` (evidence too sparse to assess, `[INSUFFICIENT]` badge),
   plus an `Uncovered Issue-Tree Branches` subsection when
   `outline.uncovered_branch_ids` is non-empty
7. **Absence Report** — `ABSENCE` items; the section is omitted entirely
   when no absence items exist
8. **Evaluation Summary** — summary table (tasks, pass rate, avg score)
   plus a per-dimension average table when any `Layer3Result` is present;
   then per-task PASS/FAIL line (renamed from "Quality Assessment")
9. **Sources** — numbered list; number 1. in Sources == `[1]` inline

**Legacy (`outline=None`) path preserved.** Every pre-existing renderer
test keeps passing with the original output format; only the outline path
switches to the new structure.

**Inline citations.** `MarkdownRenderer._build_citation_index(manifest)`
assigns each citation a 1-based index in manifest order.
`_format_inline_citations([...], index)` emits `[1][2]`-style refs,
falling back to the raw citation ID when an ID is absent from the manifest.

**Dimension scores.** New helper `_dimension_score_table(results)` rolls
up `EvaluationResult.layer3_results.dimension_scores` across tasks,
averaging per `RubricDimension`. Silent no-op when no results carry
Layer 3 data.

## Test delta

- **1058 passed** (was 1027). +31 new renderer tests split into 10
  section-focused classes: `TestOutlineDrivenStructure`,
  `TestOutlineExecutiveSummary`, `TestOutlineAnalyticalFramework`,
  `TestOutlineKeyFindings`, `TestOutlineUncertainty`,
  `TestOutlineEvidenceGaps`, `TestOutlineAbsenceReport`,
  `TestOutlineEvaluationSummary`, `TestOutlineInlineCitations`,
  `TestOutlineEmpty`. Each covers the renderable section + a
  "section empty" fallback path.
- Zero new ruff errors on touched files; pre-existing errors on both
  files cleared incidentally (`pytest` unused import, I001 sort). Final
  state: `ruff check` clean on `markdown_renderer.py` and
  `test_markdown_renderer.py`.
- mypy strict delta: −1 error (baseline 9, now 8 — a function now has an
  explicit `claim: FindingClaim` annotation in the legacy helper). All
  remaining errors are pre-existing in the legacy path.
- Pre-existing unrelated test failure in the untracked work-in-progress
  `tests/unit/evaluator/test_layer4_trajectory.py` (ImportError on
  `DEFAULT_LAYER3_WEIGHT`) — failing on baseline too, not in scope.

## Changed files

| File | Change |
|---|---|
| `src/keystone/pipeline/markdown_renderer.py` | Rewritten. Outline-driven path with 8 section renderers plus shared citation-index / sources / title helpers. Legacy path retained verbatim for `outline=None`. Module-level `_TIER_LABELS`, `_sections_of_type`, `_confidence_counts`, `_section_type_to_tier`, `_dimension_score_table` helpers. |
| `tests/unit/pipeline/test_markdown_renderer.py` | Added outline fixtures (`_full_outline`, `_exec_item`, `_branch_item`, `_moderate_item`, `_weak_item`, `_contested_item`, `_gap_item`, `_insufficient_item`, `_absence_item`, `_eval_result_with_layer3`) and 10 new test classes (31 tests). Removed unused `pytest` import; fixed I001 sort. |
| `TODO.md` | Moved "Outline-driven rendering" from `Up Next` to `Done`. |

## Orchestrator

No change required. `orchestrator.py` already passes the filtered
`StructuredOutline` to `c.renderer.render(...)` at `pipeline/orchestrator.py:377`.
The outline-driven path is automatically active in production wiring.

## Gotchas

- `uncovered_branch_ids` now surfaces in two places: the Executive
  Summary caveat line (count only) and the Evidence Gaps subsection
  (IDs listed). Both are derived from the same field — changing the
  field's semantics would require updating both.
- The legacy-path helpers (`_render_executive_summary`, `_render_key_findings`,
  `_render_uncertainty`, `_render_gaps`, `_render_quality`,
  `_render_framework`) are still reachable when `outline=None`. They
  keep the old section names ("Research Gaps", "Quality Assessment") for
  backwards-compatible behavior; those names do not appear in the
  outline-driven path.
- `_format_inline_citations` preserves caller-provided ordering of
  citation IDs. That means a claim with `citation_ids=["CIT-002",
  "CIT-001"]` renders as `[2][1]`, not `[1][2]` — L2 controls the order.
- `MarkdownRenderer._format_claim_item` is a `@staticmethod` because
  branch items carry every piece of their own presentation context
  (`evidence`, `caveats`, `confidence_tier`, `confidence`, `note`).
  Calling `self._format_inline_citations` through the class name inside
  a static method is intentional.

---

## Previous session: Post-audit remediation (Streams A + B cleanup)

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
