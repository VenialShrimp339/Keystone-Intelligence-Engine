# TODO

## Active

- [ ] Orchestrator: pipe Lane E normalizer output into `AgentPool(evidence_provider=...)`
- [ ] Fix stale import in `tests/integration/test_evaluator_live.py` (`_parse_score_json` removed from `layer3_rubric.py`)

## Up Next

- [ ] L2 Phase 2: LLM-augmented framework execution (Five Forces matrix, scenario shocks, Value Chain stage analysis)
- [ ] L2 Phase 2: bidirectional sprint-contract negotiation (Generator proposes, Evaluator counter-proposes)
- [ ] Outline-driven rendering: let `StructuredOutline` drive section order + headers in the final deliverable (currently used only for the Analytical Framework section)
- [ ] Extend canary `test_pipeline_fresh_components_per_run` to assert `content_structurer` freshness across runs
- [ ] Task-aware evidence selection (replace default "all records" with filter keyed off `ResearchTask.required_sources` / category / source_family)
- [ ] Deep-mode EV-ref enforcement (so deep-mode Citations keep Lane E SHA-256 + locator)
- [ ] Richer PDF backend (wrap `pdfminer.six` or `pypdf` behind `PDFTextBackend` protocol)
- [ ] Pre-existing canary failures in `tests/canary/test_architectural_guarantees.py` (unrelated to L2 or Lane E)
- [ ] Branch/worktree consolidation (cosmetic, not blocking)

## Done

- [x] **L2 Content Structuring (Stream B)** — `ContentStructurer` + framework selector + section-text renderer + outline filter; wired between L1.5 and L4; owns sprint-contract negotiation. 31 new unit tests, 1004 / 1004 unit tests pass, 540 -> 531 ruff overall, mypy stable.
  - `src/keystone/models/structuring.py` (new): StructuredOutline, StructuredSection, OutlineItem, AnalyticalFramework, FrameworkHint, OutlineSectionType, OutlineItemType
  - `src/keystone/structuring/__init__.py` (new), `framework_selector.py` (new), `section_text.py` (new), `content_structuring.py` (new)
  - `src/keystone/pipeline/orchestrator.py` (wire L2 into PipelineComponents and run_with_events)
  - `src/keystone/pipeline/markdown_renderer.py` (optional outline parameter, Analytical Framework section)
  - `src/keystone/contracts.py` (ContentStructuringContract signature updated to match real L2)
  - `tests/unit/structuring/test_content_structuring.py` (new, 27 tests)
  - `tests/unit/pipeline/test_markdown_renderer.py` (3 outline-integration tests added)
  - `tests/unit/pipeline/test_orchestrator.py` (event counts + stage order updated for L2)
  - `tests/unit/test_protocol_contracts.py` (ContentStructuringContract conformance test added)
- [x] **Lane E -> research bridge** — `evidence_context.py` (provider + Citation conversion), shallow-mode EV-NNN refs, deep-mode background block, AgentPool threading, 31 unit tests, zero new ruff/mypy errors
  - `src/keystone/research/evidence_context.py` (new)
  - `src/keystone/research/research_agent.py` (accept evidence_provider, resolve EV refs)
  - `src/keystone/research/agent_pool.py` (propagate evidence_provider)
  - `src/keystone/research/__init__.py` (exports)
  - `tests/unit/research/test_evidence_context.py` (new)
- [x] **Lane E: Article/PDF parse + evidence normalization** — 6 source files, 4 test files, 82 tests, mypy-strict clean
- [x] Core pipeline L0 → L4 → Render
- [x] Lane H: governed document fetch (commit `93a5ca8`, not in current branch)
- [x] Project scaffolding: CLAUDE.md, HANDOVER.md, venv, hooks
