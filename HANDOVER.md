# Handover

Last updated: 2026-04-17
Session: Stream B — L2 Content Structuring (output quality)

## What Changed

- **Built L2 Content Structuring** between L1.5 Deliberation and L4 Evaluator. Previously the pipeline went L0 -> L1 -> CitProc -> L1.5 -> L4 -> Render; it now runs L0 -> L1 -> CitProc -> L1.5 -> **L2** -> L4 -> Render.
- New package `src/keystone/structuring/` (3 files, 738 lines): `ContentStructurer`, `filter_outline_by_passed_tasks`, `frameworks_for_engagement`, `primary_framework`, `render_task_section_text`.
- New model module `src/keystone/models/structuring.py` (171 lines): `StructuredOutline`, `StructuredSection`, `OutlineItem`, `AnalyticalFramework`, `FrameworkHint`, `OutlineSectionType`, `OutlineItemType`.
- Orchestrator now builds an `outline`, drafts per-task section text, and negotiates per-task sprint contracts through L2; the L4 eval loop consumes those artifacts directly.
- `MarkdownRenderer.render()` gained an optional `outline: StructuredOutline | None` parameter; when present it renders an "Analytical Framework" section derived from the engagement type.
- `ContentStructuringContract` Protocol in `contracts.py` updated to the real L2 signature; `test_protocol_contracts.py` now verifies `ContentStructurer` conforms.
- Tests: 31 new tests (27 L2 + 3 renderer outline + 1 Protocol conformance). 1004 / 1004 unit tests pass. Full suite ~7.7s.
- Overall ruff: 540 -> 531 (improved by 9). Mypy on touched files: 19 -> 19 (no regression).

## Components

| File | Role |
|---|---|
| `src/keystone/models/structuring.py` | Pydantic v2 models: `StructuredOutline`, `StructuredSection`, `OutlineItem`, `AnalyticalFramework`, `FrameworkHint`, `OutlineSectionType`, `OutlineItemType`. |
| `src/keystone/structuring/framework_selector.py` | `frameworks_for_engagement(engagement_type)` / `primary_framework(engagement_type)` map the 5 `EngagementType`s to consulting frameworks (Sizing->Estimation, Diagnostic->Root Cause, Evaluative->Porter + Value Chain, Exploratory->Landscape Mapping, Strategic->Scenario Planning + SWOT). |
| `src/keystone/structuring/section_text.py` | `render_task_section_text(task, finding, framework, ...)` assembles the per-task narrative the Evaluator scores: framework label, lede (confidence-aware phrasing), evidence chain with citations, analytical significance (cross-referenced against the ConfidenceMap), per-task gaps, absence report, acceptance criteria. |
| `src/keystone/structuring/content_structuring.py` | `ContentStructurer` (satisfies `ContentStructuringContract`). `structure()` emits `SectionDrafted` + `SprintContractNegotiated` per task then `OutlineGenerated` once. Getters: `get_outline`, `get_task_section_text`, `get_sprint_contract`, `get_sprint_contracts`. Also exports `filter_outline_by_passed_tasks` for post-evaluation render filtering. |
| `src/keystone/pipeline/orchestrator.py` | Adds `content_structurer: ContentStructurer` to `PipelineComponents`. Stage 5 is now L2 (between L1.5 and L4). Eval loop pulls `output_text` and `SprintContract` from L2 (falls back to `_finding_to_text` / `sprint_contract_generator.generate` defensively). Renderer call passes `filter_outline_by_passed_tasks(outline, passed_task_ids)` as a 6th positional arg. |
| `src/keystone/pipeline/markdown_renderer.py` | `render()` accepts `outline: StructuredOutline \| None = None`; renders an "Analytical Framework" section from `outline.frameworks` when provided, keeping all pre-existing positional args intact. |
| `src/keystone/contracts.py` | `ContentStructuringContract` Protocol updated to the real signature (takes `findings`, `tasks`, `engagement_id`, `client_id`; exposes `get_outline`, `get_task_section_text`, `get_sprint_contract`, `get_sprint_contracts`). |

## Design Choices

- **Deterministic structuring, delegated contract negotiation.** The outline and per-task section text are pure Python transformations of `ConfidenceMap` + `list[StructuredFinding]`. The only LLM call L2 makes is through the wired `SprintContractGenerator`, one call per renderable task.
- **Sprint contracts owned by L2.** Orchestrator no longer calls `sprint_contract_generator.generate(task, spec)` directly; L2 does, stashes the result, and the orchestrator pulls it via `get_sprint_contract(task.id)`. The `SprintContractNegotiated` event now has a real source. Existing tests that mock `c.sprint_contract_generator.generate` still pass (L2 calls the mocked instance).
- **Framework stamping without framework execution.** L2 *labels* a task's section with the primary framework and carries `FrameworkHint`s on the outline, but it does not generate SWOT boxes or Five-Forces diagrams. Framework execution is a Phase 2 expansion; Phase 1 just ensures the Evaluator (and the render) see the framework choice.
- **Text first, outline second.** Section text is rendered per task as the loop progresses (so `SectionDrafted` events are ordered by task). The full `StructuredOutline` is built once at the end from accumulated data.
- **Section ordering is convention-driven.** Enum `OutlineSectionType` lists sections in consulting-brief order: executive summary -> framework analysis -> branch sections -> moderate / weak / contested uncertainty -> gaps -> insufficient -> absence. `_build_outline` appends in that same order.
- **Outline filtering preserves provenance-free items.** `filter_outline_by_passed_tasks` keeps items with empty `task_ids` (framework notes, spec-level guidance) and narrows items with multi-task provenance to the surviving task IDs.
- **Defensive fallbacks.** If the sprint-contract generator raises, L2 falls back to a task-derived contract (acceptance criteria from `task.acceptance_criteria`). If L2 somehow produces empty text for a task, the orchestrator falls back to `_finding_to_text`. Neither path is expected in practice.

## Key Commands

```bash
source .venv/bin/activate
pytest tests/unit/structuring/ -q              # 27 new L2 tests
pytest tests/unit/pipeline/ -q                 # 51 pipeline tests (orchestrator + renderer)
pytest tests/unit/ -q                          # 1004 tests, ~7.7s
ruff check src/keystone/structuring/ src/keystone/models/structuring.py
mypy src/keystone/structuring/ src/keystone/models/structuring.py
```

## Integration Shape

L2 is wired automatically by `Pipeline._build_components()`. Nothing for downstream code to pass explicitly. Test-side, if a test wants to bypass L2:

```python
async def noop_gen(*a, **kw):
    return
    yield

c.content_structurer.structure = noop_gen
c.content_structurer.get_outline = AsyncMock(return_value=StructuredOutline(...))
c.content_structurer.get_task_section_text = AsyncMock(return_value="")
c.content_structurer.get_sprint_contract = AsyncMock(return_value=None)
```

The orchestrator's `get_sprint_contract` fallback falls through to `c.sprint_contract_generator.generate(task, spec)` when L2 returns `None`, so tests that mock the generator but skip L2 still work.

## Gotchas

- **Event count changed.** `Pipeline.run()` now emits 3 extra events per renderable task (SectionDrafted + SprintContractNegotiated + 1 terminal OutlineGenerated). Two pre-existing orchestrator tests (`test_pipeline_result_has_all_fields`, `test_events_collected_from_stages`) were updated to reflect this.
- **Stage order.** `test_stages_called_in_order` now expects `["L0", "L1", "CitProc", "L1.5", "L2", "L4"]`. Added L2 patch + getters in that test's fixture.
- **Renderer signature.** `MarkdownRenderer.render()` is now 6-argument. Positional args 1-5 are unchanged; the new `outline` is the 6th. `renderer.render.call_args.args[1..4]` in existing tests still point at the right slots.
- **Fresh-per-run contract.** `content_structurer` is instantiated in `_build_components()` alongside the other stage classes, so the existing canary `test_pipeline_fresh_components_per_run` (which only asserts freshness of the fields it names) still passes. Consider extending that canary later to also assert `content_structurer` is fresh.
- **`sprint_contract_generator` is now shared between orchestrator and L2.** `_build_components()` creates one instance and passes it into both `ContentStructurer(...)` and `PipelineComponents(sprint_contract_generator=...)`. Per-run freshness is preserved because each run builds new components.
- **Pre-existing canary failures (not introduced by this change).** `tests/canary/test_architectural_guarantees.py::test_failed_evaluation_blocks_rendering`, `test_pipeline_fresh_components_per_run`, and `test_spec_engine_no_agent_config_leak` failed both before and after this work (governance flag threshold). Out of scope here.

## Next Steps

- **LLM-augmented framework execution.** Phase 2 expansion: have L2 prompt the LLM to actually apply the selected framework (e.g. populate a Five-Forces matrix, synthesize scenarios with shocks). Currently L2 only labels sections with the framework.
- **Sprint contract feedback loop.** Phase 2 design calls for bidirectional negotiation (Generator proposes, Evaluator counter-proposes). Surface hooks exist; the LLM handshake does not.
- **Extend the canary test** (`test_pipeline_fresh_components_per_run`) to assert `content_structurer` freshness across runs.
- **Outline-driven rendering.** The renderer currently uses the outline only for the framework section. A follow-up could let the outline drive branch ordering and per-task section headers in the deliverable.
- Still open from prior sessions: fix stale import in `tests/integration/test_evaluator_live.py` (`_parse_score_json` removed from `layer3_rubric.py`). Not blocking unit tests.
- Still open from prior sessions: pre-existing canary failures noted above.

## What Did Not Change

- No modifications to L0 Spec Engine, L1 Research Agents, CitationProcessor, L1.5 Deliberation, L4 Evaluator, Governance, Gateway, or Lane E (`src/keystone/retrieval/`).
- No new runtime dependencies.
- `_finding_to_text` in the orchestrator is retained as a defensive fallback; no caller reaches it in the normal path.
- `SprintContractGenerator` is unchanged; L2 just owns when it is called.
