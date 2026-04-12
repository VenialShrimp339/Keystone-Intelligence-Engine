# Candidate 6406e46 File Manifest

- Candidate commit: `6406e46`
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

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contains numerous unrelated pre-existing dirty and deleted files. Representative excluded entries:

- `.claude/settings.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `OPENAI-SWITCHOVER-HANDOFF.md`
- `audit/GAP-TRIAGE.md`
- `docs/PARALLEL-EXECUTION-PLAN.md`
- `reference/analysis/00-master-index.md`
- `research-reports/Deep_Research_Report_From_Prompt_1.md`
- `reference/nano-claude-code`

None of those controller-workspace dirty files were staged for `6406e46`.

## Committed Diff Classification

### Expected

- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`
- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`

### Legitimate Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

### Scope Creep

- None

### Quarantined Unrelated

- all unrelated dirty and deleted files already present in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`

## Classification Rule

Every touched file in the candidate is classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No unresolved `scope creep` remains in `6406e46`.
