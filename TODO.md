# TODO

## Active

- [ ] **Lane E → pipeline bridge** (connect parse output to research path — Lane E itself is built)
- [ ] Fix stale import in `tests/integration/test_evaluator_live.py` (`_parse_score_json` removed from `layer3_rubric.py`)

## Up Next

- [ ] Richer PDF backend (wrap `pdfminer.six` or `pypdf` behind `PDFTextBackend` protocol)
- [ ] Branch/worktree consolidation (cosmetic, not blocking)

## Done

- [x] **Lane E: Article/PDF parse + evidence normalization** — 6 source files, 4 test files, 82 tests, mypy-strict clean, no regressions (882/882)
  - `src/keystone/retrieval/__init__.py`
  - `src/keystone/retrieval/parse_models.py`
  - `src/keystone/retrieval/artifact_loader.py`
  - `src/keystone/retrieval/article_parser.py` (stdlib html.parser)
  - `src/keystone/retrieval/pdf_parser.py` (stdlib, pluggable `PDFTextBackend`)
  - `src/keystone/retrieval/evidence_normalizer.py`
- [x] Core pipeline L0 → L4 → Render (800 unit tests pass, now 882 with Lane E)
- [x] Lane H: governed document fetch (commit `93a5ca8`, not in current branch)
- [x] Project scaffolding: CLAUDE.md, HANDOVER.md, venv, hooks
