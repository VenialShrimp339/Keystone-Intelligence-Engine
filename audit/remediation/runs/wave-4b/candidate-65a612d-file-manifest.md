# Candidate 65a612d File Manifest

- Candidate commit: `65a612d`
- Parent commit: `6406e46`
- Baseline commit: `6406e46`
- Wave: `wave-4b`
- Purpose: record the exact committed Wave 4B candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/deliberation/analyst.py`
- `src/keystone/deliberation/aggregator.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/models/evaluation.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/intent_clarifier.py`
- `src/keystone/specification/prompts/intent_clarification.md`
- `src/keystone/specification/prompts/decompose_financial_lens.md`
- `src/keystone/specification/prompts/decompose_market_lens.md`
- `src/keystone/specification/prompts/decompose_operational_lens.md`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/template_registry.py`

### Tests

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

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Exact-Surface Boundary

Any file not listed in `Allowed Write Set` or `Committed Diff Classification` is outside the exact committed surface of `65a612d`.

## Suspicious Dirty Files In Main Workspace

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contained unrelated pre-existing dirty, deleted, and untracked files, but none of them were staged for `65a612d`.

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
