# Candidate 2cdbfec Implementation

- Baseline commit: `16e0bc7`
- Parent commit: `4ff7e90`
- Target commit: `2cdbfec`
- Implementation branch: `codex/remediation-wave-2b`
- Recovery source: `candidate-4ff7e90-recovery-dirty-wip.patch`

## Summary

This candidate replays the captured Wave 2B blocker-remediation patch into a clean worktree rooted at `4ff7e90`, verifies it inside the blocked manifest allowlist, rebuilds graphify, and commits the result as the next Wave 2B candidate.

Claimed closures in this candidate:

- `W2B-B01`: LIGHT coverage halts failed evaluated tasks.
- `W2B-B02`: task `priority` / `importance` derive from Step-5 scores, not LLM list order.
- `W2B-B03`: `Evaluator` uses the persisted effective evaluation profile from `ResearchSpec`.
- `W2B-B04`: Gate 1 and Gate 2 consult `ProfileExecutionPolicy.should_run_hitl_gate()`.
- `W2B-R01`: malformed sprint-contract JSON now fails explicitly.
- `W2B-R02`: emitted rubric weights reflect effective `dimension_emphasis`.

## Exact Files Changed

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
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

## Exact Tests Run

### Focused Wave 2B Proof Matrix

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-2b`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/governance/test_policy.py \
  tests/unit/specification/test_task_generator.py \
  tests/unit/specification/test_spec_engine.py \
  tests/unit/pipeline/test_orchestrator.py \
  tests/unit/evaluator/test_layer3.py \
  tests/unit/evaluator/test_evaluator.py \
  tests/unit/evaluator/test_sprint_contract.py \
  tests/unit/hitl/test_gate.py \
  tests/unit/deliberation/test_deliberation.py \
  tests/unit/test_research_models.py
```

Result: `151 passed in 4.87s`

Note: the clean `4ff7e90` worktree did not contain its own `.venv`, so the shared repository venv was used via absolute path while keeping the workdir on the replayed candidate lane.

## Exact Runtime Probes Run

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-2b`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/governance/test_policy.py::TestProfileExecutionPolicy::test_light_coverage_halts_on_failed_evaluated_output \
  tests/unit/specification/test_task_generator.py::TestTaskGenerator::test_uses_priority_scores_when_highest_scored_branch_is_listed_second \
  tests/unit/pipeline/test_orchestrator.py::TestWave2BWiring::test_orchestrator_uses_persisted_evaluation_profile \
  tests/unit/specification/test_spec_engine.py::TestSpecificationEngine::test_light_profile_skips_hitl_gate_via_shared_policy \
  tests/unit/deliberation/test_deliberation.py::TestHITLGate::test_non_light_gate_two_uses_shared_policy_path \
  tests/unit/evaluator/test_sprint_contract.py::TestSprintContractGeneration::test_malformed_json_raises_explicit_error \
  tests/unit/evaluator/test_evaluator.py::TestProfileVariance::test_rubric_events_emit_adjusted_weights
```

Result: `7 passed in 3.51s`

Probe mapping:

- `test_light_coverage_halts_on_failed_evaluated_output`
  Confirms failed LIGHT evaluations still halt coverage.
- `test_uses_priority_scores_when_highest_scored_branch_is_listed_second`
  Confirms later-listed higher Step-5 scores still win `priority` and `PRIMARY` importance.
- `test_orchestrator_uses_persisted_evaluation_profile`
  Confirms `Evaluator` uses the stored effective profile instead of local remapping.
- `test_light_profile_skips_hitl_gate_via_shared_policy`
  Confirms Gate 1 flows through shared policy ownership.
- `test_non_light_gate_two_uses_shared_policy_path`
  Confirms Gate 2 flows through shared policy ownership.
- `test_malformed_json_raises_explicit_error`
  Confirms malformed sprint-contract output fails explicitly.
- `test_rubric_events_emit_adjusted_weights`
  Confirms emitted rubric weights reflect effective `dimension_emphasis`.

## Graphify Rebuild

Default command failed with `ModuleNotFoundError: No module named 'graphify'`.

Fallback command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-2b`:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

Result:

- `[graphify watch] Rebuilt: 3129 nodes, 17568 edges, 51 communities`
- `[graphify watch] graph.json and GRAPH_REPORT.md updated in graphify-out`

## Exact Files Safe To Stage

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
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
