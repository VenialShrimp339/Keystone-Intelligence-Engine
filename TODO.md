# TODO

## Active

- [ ] Orchestrator: pipe Lane E normalizer output into `AgentPool(evidence_provider=...)`
- [ ] Fix stale import in `tests/integration/test_evaluator_live.py` (`_parse_score_json` removed from `layer3_rubric.py`)

## Up Next

- [ ] Task-aware evidence selection (replace default "all records" with filter keyed off `ResearchTask.required_sources` / category / source_family)
- [ ] Deep-mode EV-ref enforcement (so deep-mode Citations keep Lane E SHA-256 + locator)
- [ ] Richer PDF backend (wrap `pdfminer.six` or `pypdf` behind `PDFTextBackend` protocol)
- [ ] Branch/worktree consolidation (cosmetic, not blocking)

## Done

- [x] **Lane E -> research bridge** — `evidence_context.py` (provider + Citation conversion), shallow-mode EV-NNN refs, deep-mode background block, AgentPool threading, 31 new unit tests, 913/913 total pass, zero new ruff/mypy errors
  - `src/keystone/research/evidence_context.py` (new)
  - `src/keystone/research/research_agent.py` (accept evidence_provider, resolve EV refs)
  - `src/keystone/research/agent_pool.py` (propagate evidence_provider)
  - `src/keystone/research/__init__.py` (exports)
  - `tests/unit/research/test_evidence_context.py` (new)
- [x] **Lane E: Article/PDF parse + evidence normalization** — 6 source files, 4 test files, 82 tests, mypy-strict clean
- [x] Core pipeline L0 → L4 → Render
- [x] Lane H: governed document fetch (commit `93a5ca8`, not in current branch)
- [x] Project scaffolding: CLAUDE.md, HANDOVER.md, venv, hooks
