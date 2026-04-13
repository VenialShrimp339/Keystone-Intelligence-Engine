# Candidate 4819527 Setup Contract Addendum

- Baseline commit: `2cdbfec`
- Candidate parent: `2cdbfec`
- Candidate commit: `4819527`
- Status: docs-only retrospective contract reconcile for the cleared Wave 3 deliverable

## Purpose And Status

This addendum reconciles the historical Wave 3 setup contract to the actual cleared `4819527` deliverable.

It is not original contemporaneous authorization.

It is a retrospective contract reconcile required to describe the real cleared Wave 3 packet truthfully.

It does not reopen Wave 3 implementation scope, does not authorize new Wave 3 coding, and does not authorize Wave 3B work.

## Authority Inputs

This addendum is grounded in:

1. `audit/remediation/workstream-retro/reviews/W3A-1-wave-3a-seam-and-setup-audit.md`
2. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
3. `audit/remediation/WAVE-3-SETUP.md`
4. `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`
5. `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
6. `audit/remediation/runs/wave-3/candidate-4819527-clearance.md`
7. `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md`

## Retrospective Write-Surface Reconcile

The original Wave 3 setup omitted these files from its initial allowed write set:

- `src/keystone/governance/models.py`
- `src/keystone/specification/spec_engine.py`
- `tests/unit/test_research_models.py`

The actual cleared `4819527` deliverable touched all three, and the cleared candidate packet family already classified them as expected committed surface rather than scope creep.

The truthful retrospective interpretation is:

- the original setup contract was incomplete for the actual cleared deliverable
- these three files are recorded here as a retrospective contract reconcile required by the real `4819527` packet
- this addendum does not claim that the original setup contemporaneously authorized those files

## Retrospective E2 Interpretation

The original `WAVE-3-SETUP.md` wording made "Remaining E2 cleanup" look like reopened Wave 3 implementation scope and gave it its own execution slice.

The cleared `4819527` implementation packet is narrower. It states that the Wave 3 E2 hardening surfaces in `deliberation.py`, `llm_client.py`, `gateway/circuit_breaker.py`, `hitl/service.py`, and `hitl/gate.py` stayed unchanged because the cleared baseline already satisfied those invariants.

The truthful retrospective interpretation is therefore:

- the original E2 wording was broader than the cleared packet's actual work
- for `4819527`, those unchanged E2 surfaces are verification-only carry-forward from the cleared baseline
- this addendum does not recast those surfaces as reopened implementation scope in `4819527`

## Probe Contract Reconcile

The Wave 3 setup required named evidence for six runtime invariants. The actual cleared packet proves them through a mixed evidence model: some were named in the seven-probe runtime bundle, while others were carried by the clearance proof table or the focused matrix.

### Invariant 1

Deep mode emits audit-visible events and governance can see gateway bypass state.

- Named runtime-probe evidence:
  - `tests/unit/research/test_research_agent.py::test_deep_research_emits_invocation_event`
  - `tests/unit/pipeline/test_orchestrator.py::TestEventCollection::test_gateway_bypass_visible_in_governance`
  - `tests/integration/test_deep_research.py::test_pipeline_records_gateway_bypass_and_produces_sidecar`
- Proof-table / matrix evidence:
  - `candidate-4819527-clearance.md` proof row `C-deep-formalization`
- Reconcile note:
  - This invariant is directly supported by the named runtime bundle and remains explicit in the clearance packet.

### Invariant 2

Shallow mode consumes template prompt material in synthesis without reviving round-broadcast citations.

- Named runtime-probe evidence:
  - `tests/unit/research/test_research_agent.py::test_template_prompt_wired_in_shallow_mode`
- Proof-table / matrix evidence:
  - focused Wave 3 matrix coverage for `tests/unit/research/test_research_agent.py`
  - focused Wave 3 matrix coverage for `tests/integration/test_deep_research.py`
  - `candidate-4819527-clearance.md` proof row `C-deep-formalization`
- Reconcile note:
  - The named runtime bundle directly covers shallow prompt consumption.
  - The non-revival guardrail is carried by the proof-table / matrix evidence rather than by a standalone named runtime probe in the seven-probe bundle.

### Invariant 3

Dependent tasks do not start before declared dependencies complete.

- Named runtime-probe evidence:
  - `tests/canary/test_architectural_guarantees.py::test_dependent_tasks_do_not_start_before_dependencies_complete`
- Proof-table / matrix evidence:
  - `candidate-4819527-clearance.md` proof row `B07-dag-dispatch`
- Reconcile note:
  - This invariant is directly supported by the named runtime bundle and the clearance proof table.

### Invariant 4

Failed or unevaluated task provenance cannot leak through the verifier into the render surface.

- Named runtime-probe evidence:
  - none in the seven-probe runtime bundle
- Proof-table / matrix evidence:
  - `tests/unit/pipeline/test_orchestrator.py::TestConfidenceMapFiltering::test_shared_canonical_failed_claim_does_not_survive_filtering`
  - `tests/unit/pipeline/test_orchestrator.py::TestConfidenceMapFiltering::test_failed_task_gap_text_does_not_render`
  - `candidate-4819527-clearance.md` proof row `A13-concrete-verifier`
- Reconcile note:
  - This invariant is proven by the proof table and focused matrix, not by a separately named runtime probe in the seven-probe bundle.

### Invariant 5

The provenance sidecar distinguishes consulted, rendered, and rejected evidence.

- Named runtime-probe evidence:
  - `tests/unit/pipeline/test_orchestrator.py::TestConfidenceMapFiltering::test_provenance_sidecar_records_consulted_vs_rendered_vs_rejected_sources`
  - `tests/integration/test_deep_research.py::test_pipeline_records_gateway_bypass_and_produces_sidecar`
- Proof-table / matrix evidence:
  - `candidate-4819527-clearance.md` proof row `A14-provenance-sidecar`
- Reconcile note:
  - This invariant is directly supported by the named runtime bundle and remains explicit in the clearance packet.

### Invariant 6

Domain-aware routing can choose provisional M&A / Restructuring profile paths without falling back to a generic default.

- Named runtime-probe evidence:
  - none in the seven-probe runtime bundle
- Proof-table / matrix evidence:
  - focused Wave 3 matrix coverage for `tests/unit/specification/test_engagement_classifier.py`
  - focused Wave 3 matrix coverage for `tests/unit/specification/test_template_registry.py`
  - focused Wave 3 matrix coverage for `tests/unit/evaluator/test_rubric_config.py`
  - focused Wave 3 matrix coverage for `tests/unit/test_research_models.py`
  - `candidate-4819527-clearance.md` proof row `F1-taxonomy`
- Reconcile note:
  - The setup invariant was real, but the actual cleared packet carried it through proof-table / matrix evidence rather than through a standalone named runtime probe.

## Reconciled Boundary Statement

`4819527` stayed within the Wave 3 boundary only as retrospectively reconciled by this addendum.

That means:

- the omitted write-surface files are acknowledged as part of the actual cleared deliverable
- the unchanged E2 surfaces are treated as verification-only carry-forward from baseline rather than reopened implementation scope
- the setup probe contract is read through the actual mixed evidence model the cleared packet used

## Non-Effects

This addendum does not:

1. rewrite the original setup packet as if it had already contained these reconciliations
2. retroactively convert this reconcile into contemporaneous authorization
3. reopen Wave 3 implementation scope
4. authorize Wave 3B, Wave 4, or any later wave work
