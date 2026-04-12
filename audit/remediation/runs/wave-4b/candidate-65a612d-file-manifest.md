# Candidate 65a612d File Manifest

- Candidate commit: `65a612d`
- Parent commit: `6406e46`
- Baseline commit: `6406e46`
- Wave: `wave-4b`
- Purpose: record the exact committed Wave 4B candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/models/evaluation.py`
- `src/keystone/deliberation/analyst.py`
- `src/keystone/deliberation/aggregator.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/prompts/intent_clarification.md`
- `src/keystone/specification/prompts/decompose_financial_lens.md`
- `src/keystone/specification/prompts/decompose_market_lens.md`
- `src/keystone/specification/prompts/decompose_operational_lens.md`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/intent_clarifier.py`
- `src/keystone/specification/template_registry.py`

### Tests and Fixtures

- `tests/unit/deliberation/test_analyst.py`
- `tests/unit/deliberation/test_aggregator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/specification/test_intent_clarifier.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/fixtures/evaluator/**`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Explicit Denylist

Do not treat these as part of the Wave 4B candidate unless a later controller action explicitly widens scope:

- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/decomposer.py`
- `src/keystone/evaluator/layer2_citation_gate.py`
- future claim-support verifier modules
- future lens-registry / selector surfaces
- future custom-template generation surfaces outside the current template envelope
- Wave 5 setup or calibration docs
- immutable historical review packets
- unrelated main-workspace dirty files

## Suspicious Dirty Files In Main Workspace

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contains numerous unrelated pre-existing dirty, deleted, and untracked files. Representative excluded entries:

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

None of those controller-workspace dirty files were staged for `65a612d`.

## Committed Diff Classification

### Expected

- `src/keystone/deliberation/aggregator.py`
- `src/keystone/deliberation/analyst.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/models/evaluation.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/intent_clarifier.py`
- `src/keystone/specification/prompts/decompose_financial_lens.md`
- `src/keystone/specification/prompts/decompose_market_lens.md`
- `src/keystone/specification/prompts/decompose_operational_lens.md`
- `src/keystone/specification/prompts/intent_clarification.md`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/template_registry.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/unit/deliberation/test_aggregator.py`
- `tests/unit/deliberation/test_analyst.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/specification/test_intent_clarifier.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/specification/test_template_registry.py`

### Legitimate Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

### Scope Creep

- None

### Quarantined Unrelated

- all unrelated dirty, deleted, and untracked files already present in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`

## Classification Rule

Every touched file in the candidate is classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No unresolved `scope creep` remains in `65a612d`.
