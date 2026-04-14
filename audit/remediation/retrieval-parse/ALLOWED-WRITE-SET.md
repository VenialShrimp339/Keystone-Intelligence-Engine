# Allowed Write Set

Date: 2026-04-14
Lane: `Lane E - Article/PDF Deterministic Parse And Evidence Normalization`
Baseline anchor: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`

## Rule

The future Lane E runtime work may touch only the paths listed here.

Any path not listed here is denied.

## Exact Allowed Paths

### Runtime code

- `src/keystone/retrieval/__init__.py`
- `src/keystone/retrieval/parse_models.py`
- `src/keystone/retrieval/artifact_loader.py`
- `src/keystone/retrieval/article_parser.py`
- `src/keystone/retrieval/pdf_parser.py`
- `src/keystone/retrieval/evidence_normalizer.py`

Allowed edit kinds inside those files are limited to:

- parse-local article/PDF models
- deterministic artifact loading from persisted Lane H outputs
- article section/paragraph parsing
- PDF page/paragraph parsing
- parse warnings and parse-confidence handling
- normalized evidence-prep records that preserve upstream artifact metadata

### Conditional-only runtime path

- `pyproject.toml`

This file may be changed only if the lane cannot stay dependency-free and needs one additive article/PDF parser dependency.
If touched, the candidate must record:

- why the dependency is required
- why the dependency is still narrow Lane E scope
- why no existing dependency was sufficient

### Tests

- `tests/unit/retrieval/test_parse_models.py`
- `tests/unit/retrieval/test_artifact_loader.py`
- `tests/unit/retrieval/test_article_parser.py`
- `tests/unit/retrieval/test_pdf_parser.py`
- `tests/unit/retrieval/test_evidence_normalizer.py`
- `tests/fixtures/retrieval/`

### Review collateral

- `audit/remediation/runs/retrieval-parse/`

### Generated collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Frozen Lane H Surfaces

The following surfaces are frozen because Lane H already cleared them:

- `src/keystone/tool_names.py`
- `src/keystone/gateway/**`
- `src/keystone/specification/**`
- `src/keystone/models/tasks.py`
- `src/keystone/models/research.py`

Lane E may not reopen:

- `document_fetch` ownership
- task-assignable versus system-owned tool semantics
- fetch request/response DTOs
- article/PDF fetch routing, audit, or task-surface leakage rules

## Frozen Lane F And Downstream Surfaces

The following surfaces are frozen because they belong to integration or citation migration, not narrow Lane E:

- `src/keystone/models/citations.py`
- `src/keystone/citation/**`
- `src/keystone/research/research_agent.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/deliberation/**`
- `src/keystone/evaluator/**`
- `src/keystone/knowledge/**`

Lane E may not:

- change the canonical citation schema
- add claim-scoped anchored-citation flow
- change the shallow research loop
- wire parse output directly into synthesis

## Explicitly Blocked

The allowed files above do not authorize:

- SEC / EDGAR work
- `edgar_filings`
- papers / DOI
- filing locators such as `item`
- `EvidenceBundle` as the new L1 contract
- `AnchoredCitation`
- UI work
- benchmark packs or acceptance artifacts
- `audit/remediation/control-plane/**`
- `audit/remediation/retrieval-tool-surface/**`
- `audit/remediation/retrieval-mvp/**`
- any new public tool or server surface

## Write-Set Expansion Rule

If a candidate requires touching a blocked path:

1. stop immediately
2. record the blocked path in the run packet
3. return to the controller for a lane-boundary decision

No small exception is pre-authorized.

## Review Expectation

The candidate file manifest must classify each touched file as one of:

- expected in-scope file
- expected generated collateral
- blocked scope creep
- unrelated dirty file left untouched

Lane clearance requires an explicit statement that:

- Lane H invariants remained unchanged
- `document_fetch` stayed system-owned and non-task-assignable
- no citation-schema or research-path integration changes were made
- the patch stayed inside this write set
