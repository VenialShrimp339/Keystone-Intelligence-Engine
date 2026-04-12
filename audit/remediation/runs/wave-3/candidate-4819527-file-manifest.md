# Candidate 4819527 File Manifest

- Candidate commit: `4819527`
- Parent commit: `2cdbfec`
- Baseline commit: `2cdbfec`
- Wave: `wave-3`
- Purpose: record the exact committed Wave 3 candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/events.py`
- `src/keystone/governance/models.py`
- `src/keystone/models/research.py`
- `src/keystone/models/__init__.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/template_registry.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- `src/keystone/pipeline/provenance_sidecar.py`

### Tests

- `tests/canary/test_architectural_guarantees.py`
- `tests/integration/test_deep_research.py`
- `tests/unit/evaluator/test_rubric_config.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/test_research_models.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Exact-Surface Boundary

Any file not listed in `Allowed Write Set` or `Committed Diff Classification` is outside the exact committed surface of `4819527`.

## Suspicious Dirty Files In Main Workspace

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contained unrelated pre-existing dirty and untracked files, but none of them were staged for `4819527`.

## Committed Diff Classification

### Expected

- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/events.py`
- `src/keystone/governance/models.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/research.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- `src/keystone/pipeline/provenance_sidecar.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/specification/template_registry.py`
- `tests/canary/test_architectural_guarantees.py`
- `tests/integration/test_deep_research.py`
- `tests/unit/evaluator/test_rubric_config.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/test_research_models.py`

### Legitimate Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

### Scope Creep

- None

### Quarantined Unrelated

- all unrelated dirty and untracked files in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`
- `graphify-out/cache/` left untracked in the clean worktree and excluded from `4819527`

## Classification Rule

Every touched file in the candidate is classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No unresolved `scope creep` remains in `4819527`.
