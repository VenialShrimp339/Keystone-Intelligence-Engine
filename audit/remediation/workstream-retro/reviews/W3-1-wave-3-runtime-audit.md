# W3-1 Wave 3 Runtime Audit

- Slice: `W3-1`
- Review date: `2026-04-12`
- Baseline commit: `2cdbfec84022f52e9dca6acec8f919e8e6de5c2c`
- Parent commit: `2cdbfec84022f52e9dca6acec8f919e8e6de5c2c`
- Target commit: `4819527ed12810e0a1c2996308525ec23a906cb3`
- Authority package snapshot used for retrospective docs/status: `63f8353a1ed78d70647f0d043e2b9478b1edadda`
- Code truth source: detached review checkout at `4819527ed12810e0a1c2996308525ec23a906cb3`
- Authority/docs source: detached review checkout at `63f8353a1ed78d70647f0d043e2b9478b1edadda`
- Dirty main workspace status: present and explicitly not trusted as code truth
- Subagents used: none

## Launch And Prerequisite Proof

Authoritative prerequisite layer: `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`

Current prerequisite status in that ledger:

- `CP-1`: `CLEARED`
- `CP-2`: `CLEARED`
- `RP-1`: `CLEARED`
- `W2B-1`: `CLEARED`
- `W3A-1`: `CLEARED`

That satisfies the Batch 3 launch gate for `W3-1`.

## Authority Docs Read

Read before deriving the retrospective joins or asserting prerequisite status:

1. `graphify-out/GRAPH_REPORT.md` from the detached `4819527` code checkout
2. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
3. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
4. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
5. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
6. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
7. `audit/remediation/WAVE-3-SETUP.md`
8. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
9. `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
10. `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`
11. `audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md`

Graphify status in the reviewed code snapshot:

- `graphify-out/GRAPH_REPORT.md` was present and read first.
- `graphify-out/wiki/index.md` was absent.

## Packet Integrity

Reviewed surface:

- full diff `2cdbfec84022f52e9dca6acec8f919e8e6de5c2c..4819527ed12810e0a1c2996308525ec23a906cb3`
- detached code checkout only
- later retrospective sidecars sourced from the detached `63f8353` authority checkout, not from the dirty main workspace

Packet-integrity result:

- The actual committed diff matches the candidate file-manifest surface and the manifest records `Scope Creep: None`.
- The historical `4819527` checkout does not contain the later retrospective authority docs named above; that is expected and non-blocking under the program rule that prerequisite authority comes from the current promoted review layer, not from the historical code snapshot.
- The recorded Wave 3 test matrix and runtime probes reproduced cleanly in the detached `4819527` checkout:
  - focused matrix: `163 passed, 2 xfailed in 6.84s`
  - completeness/gate matrix: `49 passed in 1.54s`
  - named runtime probes: `7 passed in 0.26s`

## Manifest / Scope Issues

One real historical packet defect exists, but it is now explicitly reconciled in the retrospective authority layer.

### Historical setup-contract incompleteness

The original `WAVE-3-SETUP.md` initial allowed write set did not include:

- `src/keystone/governance/models.py`
- `src/keystone/specification/spec_engine.py`
- `tests/unit/test_research_models.py`

The actual cleared `4819527` diff touched all three. That means the raw historical setup packet was incomplete as a contemporaneous write-surface contract.

However, the later `candidate-4819527-setup-contract-addendum.md` in the `63f8353` authority snapshot explicitly reconciles exactly those three omissions, narrows the historical E2 wording to verification-only carry-forward, and reconciles the probe contract to the actual mixed evidence model used by the cleared packet.

Assessment:

- as raw historical setup text alone: boundary packet was incomplete
- as current retrospective authority layer at `63f8353`: this defect is repaired and no longer blocks `W3-1`

No other manifest/scope defect was found:

- actual changed files stayed inside the candidate file manifest
- no unclassified code or test files landed outside that packet surface
- no packet-integrity contradiction was found between the diff and the candidate implementation/file-manifest pair

## Runtime Correctness

### 1. Taxonomy And Routing

The diff makes the dual-axis routing contract real on the runtime path:

- `ResearchSpec` persists `domain_category`, `secondary_types`, and the effective evaluation profile selection surface.
- `EngagementClassifier` emits `domain_category` and `secondary_types` with valid fallback behavior.
- `SpecificationEngine` persists the domain axis and resolves evaluator profile through the domain map before falling back to engagement-type mapping.
- `TemplateRegistry` and `TaskGenerator` both consume `domain_category`, so the secondary routing axis reaches template selection/tool assignment rather than staying packet-only.
- `rubric_config.py` adds the provisional `M_AND_A` and `RESTRUCTURING` evaluator profiles and weight vectors.

Runtime evidence:

- unit routing/profile tests passed
- the diff does not leave the domain axis as documentation-only metadata

Assessment: no runtime blocker found.

### 2. Deep-Research Formalization

The Wave 3 deep/shallow prompt and governance visibility contract is implemented on the real path:

- `ResearchAgent` emits `DeepResearchInvoked` before the deep path runs.
- `ResearchAgent` threads `agent.definition.system_prompt` into both `_build_deep_research_prompt()` and `_build_synthesis_prompt()`.
- `Pipeline.run_with_events()` marks `governance.gateway_bypassed = True` when that event is observed.

This is the correct Wave 3 behavior: the code does not pretend deep mode is gateway-governed; it makes the bypass visible instead.

Runtime evidence:

- `test_deep_research_emits_invocation_event`
- `test_template_prompt_wired_in_deep_mode`
- `test_template_prompt_wired_in_shallow_mode`
- `test_gateway_bypass_visible_in_governance`
- `test_pipeline_records_gateway_bypass_and_produces_sidecar`

Assessment: no runtime blocker found.

### 3. DAG Dispatch

The orchestrator now performs real dependency-depth batching rather than metadata-only ordering:

- `_build_dependency_batches()` computes topological depth, rejects cycles, and rejects missing dependency references.
- `_blocked_dependencies()` and `_mark_task_dependency_blocked()` stop downstream tasks from starting when required upstream tasks produced no output.
- The orchestrator still runs a single pass over the task DAG; it does not introduce a second engagement-level round controller.

Runtime evidence:

- `test_dependent_tasks_do_not_start_before_dependencies_complete`
- the full focused matrix including `tests/unit/specification/test_task_generator.py`, `tests/unit/specification/test_spec_engine.py`, and `tests/unit/pipeline/test_orchestrator.py`

Assessment: the Wave 3 DAG contract is real and does not pull forward Wave 3B control authority.

### 4. Concrete Verifier And Provenance Sidecar

The verifier and sidecar deliverables are present as concrete pipeline modules and are wired into the render path:

- `src/keystone/pipeline/post_synthesis_verifier.py` filters confidence-map claims and gaps to passed-task provenance only and updates corroboration counts accordingly.
- `src/keystone/pipeline/provenance_sidecar.py` produces consulted/rendered/rejected evidence sections plus rejection reasons.
- `Pipeline.run_with_events()` renders from `passed_findings`, a verifier-filtered confidence map, and a filtered manifest, then attaches `provenance_sidecar_path` and `provenance_sidecar_output` to `PipelineResult`.

Important nuance:

- the sidecar is emitted as a pipeline artifact in memory (`PipelineResult`) rather than being persisted to disk by the orchestrator itself
- that is still consistent with the current pipeline architecture, which already returns markdown deliverables in-memory rather than writing them directly

Runtime evidence:

- `test_shared_canonical_failed_claim_does_not_survive_filtering`
- `test_failed_task_gap_text_does_not_render`
- `test_provenance_sidecar_records_consulted_vs_rendered_vs_rejected_sources`
- integration probe `test_pipeline_records_gateway_bypass_and_produces_sidecar`

Assessment: no runtime blocker found.

## Boundary Compliance Against Wave 3B Deferrals

I found no illegal Wave 3B pull-forward in the actual `4819527` code diff.

What did **not** land:

- no `StructuredOutline`
- no `src/keystone/structuring/` surface
- no renderer migration to outline consumption
- no `src/keystone/research/round_state.py`
- no orchestrator-owned outer round loop
- no round `N+1` task refinement or novelty-exhaustion controller at orchestrator scope

What did land instead:

- single-pass DAG batching inside the orchestrator
- deep-mode visibility and prompt wiring
- concrete verifier extraction
- provenance sidecar generation

The live iterative loop remains in `ResearchAgent`, which is exactly what the seam freeze required for Wave 3. The orchestrator still does not become the authoritative cross-round controller. That keeps `4819527` on the Wave 3 side of the Wave 3 / 3B boundary.

Assessment: no later Wave 3B behavior appears to have been pulled forward illegally.

## Residual Risks

1. The original historical setup packet was not self-sufficient; future retrospective readers must use the setup-contract addendum with `WAVE-3-SETUP.md` rather than reading the historical setup text in isolation.
2. The provenance sidecar is surfaced as an in-memory pipeline artifact rather than directly written to disk by the orchestrator; that is non-blocking for this slice, but downstream persistence ownership still matters if later waves require on-disk artifact guarantees.
3. Deep mode still bypasses the MCP gateway by design. Wave 3 correctly makes that bypass visible, but it does not eliminate the architectural trade-off.

## Sub-Verdicts

- `routing and profile axis`: `CLEARED`
- `deep-research formalization`: `CLEARED`
- `DAG dispatch`: `CLEARED`
- `verifier and sidecar`: `CLEARED`
- `boundary compliance`: `CLEARED`

## Top-Line Verdict

`CLEARED`

Wave 3 runtime `4819527` is retrospectively clear on the real runtime path. The only material defect found is historical setup-contract incompleteness in the original Wave 3 packet, and the current retrospective authority layer at `63f8353a1ed78d70647f0d043e2b9478b1edadda` explicitly reconciles that defect without reopening scope. No local runtime blocker was found, and no Wave 3B control-path behavior was pulled forward illegally.
