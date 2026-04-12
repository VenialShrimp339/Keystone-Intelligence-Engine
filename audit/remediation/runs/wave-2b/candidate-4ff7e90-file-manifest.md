# Candidate 4ff7e90 File Manifest

- Candidate commit: `4ff7e90`
- Parent commit: `c6eecbf`
- Baseline commit: `16e0bc7`
- Wave: `wave-2b`
- Purpose: retrospectively normalize the blocked Wave 2B candidate by recording the exact committed diff surface of `4ff7e90` without treating later recovery planning as contemporaneous packet truth

## Packet Inventory

- [candidate-4ff7e90-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-adversarial-review.md)
- [candidate-4ff7e90-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-second-opinion.md)
- [candidate-4ff7e90-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-review-synthesis.md)
- [candidate-4ff7e90-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-blocked-checkpoint.md)
- [candidate-4ff7e90-implementation.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-implementation.md)
- [candidate-4ff7e90-recovery-dirty-wip.patch](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch)

## Packet Provenance Note

The blocked `4ff7e90` review texts were originally authored as top-level Wave 2B review docs during the bootstrap adoption commit `35a8a29`. The in-folder review wrappers listed above were added later to make the `runs/wave-2b/` packet chain self-contained without pretending those review files originally lived under this run folder.

This file is also a later normalization artifact. It was not the contemporaneous pre-commit allowlist for `4ff7e90`.

Direct git evidence for the exact-surface sections below: `git show --name-only 4ff7e90`

## Allowed Write Set

For this retrospective packet, the `Allowed Write Set` is the literal committed file surface of `4ff7e90`. It is not a contemporaneous pre-commit allowlist, and it does not include later replay-only owner files.

### Code

- `src/keystone/contracts.py`
- `src/keystone/deliberation/deliberation.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/governance/__init__.py`
- `src/keystone/governance/models.py`
- `src/keystone/governance/policy.py`
- `src/keystone/hitl/gate.py`
- `src/keystone/hitl/schemas.py`
- `src/keystone/models/research.py`
- `src/keystone/models/tasks.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`

### Tests

- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/governance/test_policy.py`
- `tests/unit/hitl/test_gate.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/test_research_models.py`

## Committed Diff Classification

### Expected

- `src/keystone/contracts.py`
- `src/keystone/deliberation/deliberation.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/governance/__init__.py`
- `src/keystone/governance/models.py`
- `src/keystone/governance/policy.py`
- `src/keystone/hitl/gate.py`
- `src/keystone/hitl/schemas.py`
- `src/keystone/models/research.py`
- `src/keystone/models/tasks.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/spec_engine.py`
- `src/keystone/specification/task_generator.py`
- `tests/unit/deliberation/test_deliberation.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/governance/test_policy.py`
- `tests/unit/hitl/test_gate.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/test_research_models.py`

### Legitimate Collateral

- None

### Scope Creep

- None

### Quarantined Unrelated

- None inside the exact committed diff surface of `4ff7e90`

## Later Recovery / Replay Context

The items below are preserved as later blocked-state recovery context only. They do not redefine the exact committed diff surface above.

### Recovery Owner / Risk Files

These files remained likely replay touchpoints or mixed-hunk risk during later recovery planning:

- `src/keystone/specification/spec_engine.py`
- `src/keystone/evaluator/evaluator.py`
- `tests/unit/specification/test_spec_engine.py`
- `tests/unit/evaluator/test_evaluator.py`

### Recovery Evidence Boundary

- [candidate-4ff7e90-recovery-dirty-wip.patch](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch) captures later uncommitted recovery WIP only.
- That patch is not part of candidate `4ff7e90` and does not change the exact committed diff surface listed above.

## Classification Rule

Treat the `Committed Diff Classification` section above as the authoritative packet-truth layer for candidate `4ff7e90`. Later recovery / replay notes in this file are informational only.
