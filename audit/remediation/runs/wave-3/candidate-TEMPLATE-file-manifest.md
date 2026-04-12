# Candidate TEMPLATE File Manifest

- Candidate commit: `TEMPLATE`
- Parent commit: `2cdbfec`
- Baseline commit: `2cdbfec`
- Wave: `wave-3`
- Purpose: record the exact committed Wave 3 candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/events.py`
- `src/keystone/models/research.py`
- `src/keystone/models/__init__.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/template_registry.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/deliberation/deliberation.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- `src/keystone/pipeline/provenance_sidecar.py`
- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/hitl/service.py`
- `src/keystone/hitl/gate.py`
- `src/keystone/llm_client.py`
- `src/keystone/gateway/circuit_breaker.py`

### Tests

- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/evaluator/test_rubric_config.py`
- `tests/unit/hitl/test_service.py`
- `tests/unit/hitl/test_gate.py`
- `tests/integration/test_deep_research.py`
- `tests/canary/test_architectural_guarantees.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Explicit Denylist

Do not treat these as part of the Wave 3 candidate unless a later controller action explicitly widens scope:

- `src/keystone/models/structuring.py`
- `src/keystone/structuring/**`
- `src/keystone/pipeline/markdown_renderer.py`
- Wave 3B, Wave 4, Wave 4B, or Wave 5 setup docs
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
