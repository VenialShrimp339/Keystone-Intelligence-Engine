# Candidate TEMPLATE File Manifest

- Candidate commit: `TEMPLATE`
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
*** Add File: audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md
# Candidate 5cc9585 Clearance

- Baseline commit: `4819527`
- Candidate parent: `4819527`
- Cleared candidate commit: `5cc9585`
- Clearance verdict: `CLEARED`

## Clearance Basis

This clearance is grounded in:

- the committed code snapshot at `5cc9585`
- the full review scope `4819527..5cc9585`
- the focused Wave 3B proof matrix
- the focused Wave 3B runtime and test bundle
- the candidate implementation packet and file manifest
- the adversarial review and second-opinion packet

## Proof Table

| wave3b_item | runtime_invariant | owner_path | named_tests | result |
|---|---|---|---|---|
| `D-structured-outline` | `StructuredOutline` preserves issue-tree branch, task, claim, and citation provenance end to end | `src/keystone/models/structuring.py`, `src/keystone/structuring/content_structuring.py`, `src/keystone/contracts.py` | `tests/unit/structuring/test_content_structuring.py`; `tests/unit/test_protocol_contracts.py` | `closed in 5cc9585` |
| `E-outline-renderer` | `MarkdownRenderer` consumes the outline surface rather than raw pre-L2 finding structures | `src/keystone/pipeline/markdown_renderer.py`, `src/keystone/pipeline/orchestrator.py` | `tests/unit/pipeline/test_markdown_renderer.py`; `tests/unit/pipeline/test_orchestrator.py`; `tests/e2e/test_mock_pipeline.py` | `closed in 5cc9585` |
| `F-round-state` | Round state persists under `memory/rounds/` and continuity reloads prior round summaries | `src/keystone/research/round_state.py`, `src/keystone/research/context_loader.py` | `tests/unit/research/test_round_state.py`; `tests/unit/research/test_context_loader.py` | `closed in 5cc9585` |
| `H-single-controller` | The orchestrator is the only authoritative cross-task round controller on the runtime path | `src/keystone/pipeline/orchestrator.py`, `src/keystone/research/agent_pool.py`, `src/keystone/research/research_agent.py` | `tests/unit/pipeline/test_orchestrator.py::TestPipelineStageOrder::test_stages_called_in_order`; `tests/unit/pipeline/test_orchestrator.py::TestPipelineStageOrder::test_pipeline_result_has_all_fields`; `tests/e2e/test_mock_pipeline.py` | `closed in 5cc9585` |
| `H-coverage-and-refinement` | Branch coverage, novelty, sufficiency, and prior-round findings drive continuation and follow-up task generation | `src/keystone/pipeline/orchestrator.py`, `src/keystone/research/context_loader.py`, `src/keystone/research/round_state.py` | `tests/unit/pipeline/test_orchestrator.py`; `tests/canary/test_architectural_guarantees.py::test_dependent_tasks_do_not_start_before_dependencies_complete` | `closed in 5cc9585` |

## Review Packet Verdicts

- [candidate-5cc9585-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-adversarial-review.md): `CLEARED`
- [candidate-5cc9585-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-second-opinion.md): `CLEARED`
- [candidate-5cc9585-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md): `CLEARED`

## Residual Risks

- Wave 4 / 4B content and rubric work is still pending and intentionally outside this clearance.
- The main workspace remains dirty from unrelated user changes and must stay quarantined from code truth.
- `W2B-R01` remains a non-blocking historical follow-up.

## Controller Decision

Wave 3B is cleared at `5cc9585`.

The next required step is a docs-only Wave 4 setup checkpoint before any Wave 4 polish code or Wave 4B content implementation begins.
