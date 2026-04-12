# Candidate 2cdbfec File Manifest

- Candidate commit: `2cdbfec`
- Parent commit: `4ff7e90`
- Baseline commit: `16e0bc7`
- Purpose: record the actual committed Wave 2B remediation surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/deliberation/deliberation.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/governance/policy.py`
- `src/keystone/models/research.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`

### Tests

- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/governance/test_policy.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/test_research_models.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Mixed-Hunk Risk Files

These files remained mixed-hunk risk candidates during replay and should still be treated carefully in any follow-up blocked-remediation loop:

- `src/keystone/specification/spec_engine.py`
- `src/keystone/evaluator/evaluator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/evaluator/test_evaluator.py`

## Explicit Denylist

Do not treat these as part of candidate `2cdbfec` unless a later controller action explicitly widens scope:

- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/models/config.py`
- `tests/integration/test_pipeline_real.py`
- `schemas/citation.schema.json`
- any Wave 3, 3B, 4, 4B, or 5 setup docs
- `CURRENT-STATE.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `SESSION-LOG.md`

## Suspicious Dirty Files In Main Workspace

These remain quarantined in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` and were intentionally excluded from candidate `2cdbfec`:

- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/models/config.py`
- `tests/integration/test_pipeline_real.py`
- `schemas/citation.schema.json`
- broad archive / docs reorg churn outside the control-plane files

## Committed Diff Classification

### Expected

- `src/keystone/deliberation/deliberation.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/governance/policy.py`
- `src/keystone/models/research.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`
- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/governance/test_policy.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/test_research_models.py`

### Legitimate Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Classification Rule

Every touched file in candidate `2cdbfec` has been classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

Candidate `2cdbfec` contains no unresolved `scope creep` files.
