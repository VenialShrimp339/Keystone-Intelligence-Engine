# Candidate TEMPLATE File Manifest

- Candidate commit: `TEMPLATE`
- Parent commit: `5cc9585`
- Baseline commit: `5cc9585`
- Wave: `wave-4`
- Purpose: record the exact committed Wave 4 polish candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`

### Tests

- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`
- `tests/e2e/test_mock_pipeline.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Explicit Denylist

Do not treat these as part of the Wave 4 candidate unless a later controller action explicitly widens scope:

- `src/keystone/evaluator/prompts/**`
- `src/keystone/specification/prompts/**`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/template_registry.py`
- Wave 4B or Wave 5 setup docs
- immutable historical review packets
- unrelated main-workspace dirty files

## Suspicious Dirty Files In Main Workspace

List any dirty files still present in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` that were intentionally excluded from the candidate.

## Committed Diff Classification

### Expected

- Fill with every in-scope file actually changed in the candidate

### Legitimate Collateral

- Fill with generated or mechanically related collateral that landed with the candidate

### Scope Creep

- Fill with any touched files that fell outside the approved write set

### Quarantined Unrelated

- Fill with files observed but intentionally excluded from the candidate

## Classification Rule

Every touched file in the candidate must be classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No candidate clears with unresolved `scope creep`.
