# Candidate 4ff7e90 File Manifest

- Candidate commit: `4ff7e90`
- Baseline commit: `16e0bc7`
- Purpose: close the known Wave 2B blockers without widening scope

## Allowed Write Set

### Code

- `src/keystone/governance/policy.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/models/research.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/deliberation/deliberation.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/evaluator/sprint_contract.py`

### Tests

- `tests/unit/governance/test_policy.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/test_research_models.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/hitl/test_gate.py`

### Generated collateral allowed only if code changes land

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Mixed-Hunk Risk Files

These files are allowed, but must be staged by hunk if unrelated dirty changes reappear:

- `src/keystone/specification/spec_engine.py`
- `src/keystone/evaluator/evaluator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/evaluator/test_evaluator.py`

## Explicit Denylist

Do not touch these during Wave 2B blocker remediation unless the controller explicitly amends this manifest:

- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/models/config.py`
- `tests/integration/test_pipeline_real.py`
- `schemas/citation.schema.json`
- any Wave 3, 3B, 4, 4B, or 5 setup docs
- `CURRENT-STATE.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `SESSION-LOG.md`

## Suspicious Dirty Files In Main Workspace

These are quarantined and must not be swept into the Wave 2B candidate:

- `src/keystone/gateway/mcp_gateway.py`
- `src/keystone/models/config.py`
- `tests/integration/test_pipeline_real.py`
- `schemas/citation.schema.json`
- broad archive / docs reorg churn outside the control-plane files

## Classification Rule

Every touched file in the next candidate must be classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No candidate clears with unresolved `scope creep` files.
