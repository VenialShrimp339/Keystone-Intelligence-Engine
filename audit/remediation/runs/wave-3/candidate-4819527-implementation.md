# Candidate 4819527 Implementation

- Baseline commit: `2cdbfec`
- Parent commit: `2cdbfec`
- Target commit: `4819527`
- Implementation branch: `codex/remediation-wave-3`
- Implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3`

## Summary

This candidate lands the approved Wave 3 completeness scope on top of the cleared Wave 2B baseline `2cdbfec`.

Claimed closures in this candidate:

- Dual-axis taxonomy and domain-aware routing are now load-bearing from classification through template matching and evaluator profile resolution.
- Provisional M&A / Restructuring evaluator profile paths now exist and route through the persisted `ResearchSpec` surface.
- Deep research is now auditable via `DeepResearchInvoked`, template prompt material is consumed in both deep and shallow paths, and governance can see gateway-bypass usage.
- The orchestrator now performs real dependency-depth batch dispatch and blocks dependents when upstream tasks produce no output.
- The post-synthesis verifier now exists as a concrete pipeline module instead of only an in-file helper.
- A provenance sidecar is now emitted from the post-evaluation, post-verifier render surface.
- Remaining Wave 3 E2 hardening surfaces (`deliberation.py`, `llm_client.py`, `circuit_breaker.py`, `hitl/service.py`, `hitl/gate.py`) stayed unchanged because the cleared baseline already satisfied those invariants; this candidate verified them rather than reopening them.

## Exact Files Changed

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
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

## Exact Tests Run

### Focused Wave 3 Matrix

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3` against committed `4819527`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/specification/test_engagement_classifier.py \
  tests/unit/specification/test_template_registry.py \
  tests/unit/specification/test_task_generator.py \
  tests/unit/specification/test_spec_engine.py \
  tests/unit/evaluator/test_rubric_config.py \
  tests/unit/test_research_models.py \
  tests/unit/research/test_research_agent.py \
  tests/unit/pipeline/test_orchestrator.py \
  tests/canary/test_architectural_guarantees.py
```

Result: `163 passed, 2 xfailed in 6.66s`

### Required Completeness / Gate Matrix

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3` against committed `4819527`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/deliberation/test_deliberation.py \
  tests/unit/hitl/test_service.py \
  tests/unit/hitl/test_gate.py \
  tests/integration/test_deep_research.py
```

Result: `49 passed in 1.55s`

## Exact Runtime Probes Run

Command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3` against committed `4819527`:

```bash
PYTHONPATH=src /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest -q \
  tests/unit/research/test_research_agent.py::test_deep_research_emits_invocation_event \
  tests/unit/research/test_research_agent.py::test_template_prompt_wired_in_deep_mode \
  tests/unit/research/test_research_agent.py::test_template_prompt_wired_in_shallow_mode \
  tests/unit/pipeline/test_orchestrator.py::TestEventCollection::test_gateway_bypass_visible_in_governance \
  tests/unit/pipeline/test_orchestrator.py::TestConfidenceMapFiltering::test_provenance_sidecar_records_consulted_vs_rendered_vs_rejected_sources \
  tests/canary/test_architectural_guarantees.py::test_dependent_tasks_do_not_start_before_dependencies_complete \
  tests/integration/test_deep_research.py::test_pipeline_records_gateway_bypass_and_produces_sidecar
```

Result: `7 passed in 0.26s`

Probe mapping:

- `test_deep_research_emits_invocation_event`
  Confirms deep mode emits an audit-visible invocation event.
- `test_template_prompt_wired_in_deep_mode`
  Confirms deep mode consumes template prompt material.
- `test_template_prompt_wired_in_shallow_mode`
  Confirms shallow synthesis consumes template prompt material.
- `test_gateway_bypass_visible_in_governance`
  Confirms pipeline governance captures deep-mode gateway bypass.
- `test_provenance_sidecar_records_consulted_vs_rendered_vs_rejected_sources`
  Confirms the sidecar distinguishes consulted, rendered, and rejected evidence.
- `test_dependent_tasks_do_not_start_before_dependencies_complete`
  Confirms dependency-depth batching is real, not metadata-only.
- `test_pipeline_records_gateway_bypass_and_produces_sidecar`
  Confirms the integration path preserves both governance visibility and sidecar emission.

## Graphify Rebuild

Default command failed with `ModuleNotFoundError: No module named 'graphify'`.

Fallback command run from `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3`:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

Result:

- `[graphify watch] Rebuilt: 3183 nodes, 18102 edges, 57 communities`
- `[graphify watch] graph.json and GRAPH_REPORT.md updated in graphify-out`

## Exact Files Safe To Stage

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
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
