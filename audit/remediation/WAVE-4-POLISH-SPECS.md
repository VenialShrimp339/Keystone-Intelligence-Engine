# Wave 4 Polish Specs

*Date: 2026-04-12 | Scope: E-2, E-4, E-5 | Purpose: freeze the exact low-risk Wave 4 polish slice before any code lane opens*

---

## Purpose

This memo turns the accepted Wave 4 polish items into exact implementation contracts.

These are existing-seam fixes only:

- `E-2`: Completeness classification fix
- `E-4`: renderer zero-cost client-output cleanup
- `E-5`: sample-schema sync

Nothing in this memo authorizes prompt redesign, rubric-policy redesign, or Wave 4B content implementation.

## Shared Boundary

- Baseline runtime: cleared Wave 3B commit `5cc9585`
- Scope source: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
- Code lane status: not yet opened
- Main workspace rule: controller/docs only

The future Wave 4 code lane must remain narrow and must not absorb extra prompt or evaluator work under the cover of "polish."

## Fix Summary

| Fix | Observed problem | Runtime consumer | Classification | Dependency |
|---|---|---|---|---|
| `E-2` | Completeness is labeled machine-checkable even though it is LLM-judged prose evaluation | `src/keystone/models/evaluation.py` | `existing-seam code` | None beyond Wave 3B clear |
| `E-4` | Client markdown leaks internal quality metrics and raw `CIT-xxx` engineering IDs | `src/keystone/pipeline/markdown_renderer.py` | `existing-seam code` | None beyond Wave 3B clear |
| `E-5` | Sample engagements still encode legacy fields and stale tool names | `samples/**`, `tests/unit/test_schemas.py` | `existing-seam code` | None beyond Wave 3B clear |

## E-2: Completeness Classification Fix

### Observed problem

- Source artifact: `CONTENT-SYNTHESIS-v2.md` `E-2`
- Live code seam: `src/keystone/models/evaluation.py`
- Current mapping:
  - `RubricDimension.COMPLETENESS -> EvalType.MACHINE_CHECKABLE`

That label is inconsistent with how Completeness is actually judged: it depends on LLM-evaluated narrative coverage, not a deterministic machine check.

### Implementation contract

- Change the Completeness mapping to `EvalType.EXPERT_CHECKABLE`.
- Do **not** change:
  - Completeness weight
  - Completeness floor
  - pass thresholds
  - any other rubric dimension type
- Treat this as metadata correction, not calibration work.

### Negative example

Bad implementation:

- changing Completeness weight or pass criteria in the same patch
- folding this change into broader evaluator policy cleanup

### Verification expectation

- Minimum runtime probe:
  - import the evaluation model surface and verify Completeness resolves to `EXPERT_CHECKABLE`
- Preferred regression:
  - add one focused assertion on the eval-type map in an existing evaluator-facing test seam if the controller later widens the frozen test manifest

## E-4: Renderer Zero-Cost Client Cleanup

### Observed problem

- Source artifact: `CONTENT-SYNTHESIS-v2.md` `E-4`
- Live code seam: `src/keystone/pipeline/markdown_renderer.py`

Current renderer behavior that should not reach client output:

- renders `## Quality Assessment`, including internal task-pass metrics
- emits raw `CIT-xxx` identifiers in the sources list and claim source labels

Those are engineering or governance artifacts, not client-facing citation formatting.

### Implementation contract

- Remove the Quality Assessment section from default client markdown output.
- Preserve the rest of the report structure:
  - Title
  - Executive Summary
  - Key Findings
  - Areas of Uncertainty
  - Research Gaps
  - Sources
- Replace raw citation IDs with stable numbered references derived from manifest order.
- Apply numbered references consistently:
  - in claim-level source labels
  - in the Sources section
- Keep manifest order stable rather than re-sorting by claim occurrence.

### Reference-format rule

Preferred client-facing rendering:

- claim/body reference style: `[1]`, `[2]`, `[1, 3]`
- source list style: `1. Author...`

The important invariant is that no raw `CIT-xxx` token remains in client markdown.

### Negative example

Bad implementation:

- stripping all source labels rather than formatting them
- reordering manifest citations per claim and producing unstable numbering
- removing internal quality data from the pipeline entirely instead of just from client markdown

### Verification expectation

- Required unit regressions in `tests/unit/pipeline/test_markdown_renderer.py`:
  - rendered markdown does not contain `## Quality Assessment`
  - rendered markdown does not contain `CIT-`
  - numbered references appear in the client-facing output
- Required e2e smoke in `tests/e2e/test_mock_pipeline.py`:
  - end-to-end markdown still renders through the mock pipeline

## E-5: Sample Schema Sync

### Observed problem

- Source artifact: `CONTENT-SYNTHESIS-v2.md` `E-5`
- Live consumer surfaces:
  - `samples/auto_body_chain/RESEARCH.md.json`
  - `samples/luminar_lidar/RESEARCH.md.json`
  - `samples/specialty_chemicals_ma/RESEARCH.md.json`
  - corresponding `research-tasks.json` files
  - `tests/unit/test_schemas.py`

Observed stale sample fields:

- `alternative_hypothesis`
- `prior_confidence`
- `max_rounds`

Observed stale sample tool names:

- `government_data_api`
- `news_search`

These fields and tool names do not reflect the live production model / registered tool surface, even if the current JSON schema still tolerates them.

### Implementation contract

- Remove the legacy fields from all sample `RESEARCH.md.json` files where they appear.
- Normalize sample task tool lists so every `assigned_tools` entry is drawn from the registered tool set in `src/keystone/tool_names.py`.
- Keep the samples realistic, but do **not** invent new placeholder tools to preserve realism.
- Maintain the 3-5 tools per task rule while normalizing.

### Test contract

Make the semantic alignment load-bearing in `tests/unit/test_schemas.py` by adding assertions that:

- sample `RESEARCH.md.json` fixtures do not contain the legacy fields above
- sample `research-tasks.json` fixtures use only registered tool names

Schema-valid but semantically stale samples should stop passing silently.

### Negative example

Bad implementation:

- only deleting fields from one sample directory
- replacing stale tool names with different unregistered names
- leaving the tests as pure JSON Schema validation with no semantic guardrails

### Verification expectation

- `tests/unit/test_schemas.py` must fail if a sample reintroduces a legacy field or an unregistered tool name.

## Recommended Stageable Files For The Future Code Lane

- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`
- `tests/e2e/test_mock_pipeline.py`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Minimum Future Test Command

When the Wave 4 polish code lane opens, the minimum proof command should be:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/test_schemas.py \
  tests/unit/pipeline/test_markdown_renderer.py \
  tests/e2e/test_mock_pipeline.py
```

## Final Classification

All three Wave 4 polish items are `existing-seam code`.

None of them requires a new capability.
None of them should be bundled with Wave 4B content work.
