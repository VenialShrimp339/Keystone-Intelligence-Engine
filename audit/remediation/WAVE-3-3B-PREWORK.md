# Wave 3 / 3B Prework

## Scope

This is a planning-only decomposition for the accepted post-2B plan.

Inputs read per prompt:
- `graphify-out/GRAPH_REPORT.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `CURRENT-STATE.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/WAVE-2B-RECONCILIATION.md`
- `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
- `audit/remediation/round-3/PLANNING-ADDENDUM.md`
- `CAPSTONE-PLAN-v2.md`
- `JACK-ARCHITECTURAL-DIRECTIVES.md`
- `audit/remediation/WAVE-2B-SETUP.md`

Additional source inspection was limited to the current implementation and test surfaces needed to ground write sets and sequencing.

Graphify context matters here: `StructuredFinding`, `CitationManifest`, `ResearchTask`, `EngagementSpec`, and the MCP gateway are current cross-community bridge nodes. In practice that means the highest-conflict write sets are the models layer, `pipeline/orchestrator.py`, and the research/evaluation handoff seams.

## Current-Code Readout

The live codebase already contains some of the accepted architecture, but several Wave 3 / 3B seams are still only partial or entirely absent.

Confirmed already present:
- Claim/task provenance now exists in `ConfidenceMap` and tier claims.
- `PostSynthesisVerifierContract` exists in `src/keystone/contracts.py`, but only as a contract.
- Event types for L2 already exist in `src/keystone/events.py`.
- `ContextLoader`, `WikiBuilder`, and `INDEX.md` maintenance exist as reusable primitives.
- Some E2 concurrency hardening appears already landed: deliberation uses `asyncio.gather(..., return_exceptions=True)`, `llm_client.py` kills subprocesses in `finally`, and `gateway/circuit_breaker.py` holds the HALF_OPEN probe lock.

Confirmed still missing or still architecturally incomplete:
- No `DomainCategory`, `domain_category`, or `secondary_types` in the classification/runtime path.
- `PipelineProfile` still lives in `specification/engagement_classifier.py`, not the shared research models.
- `TemplateRegistry` still routes only on the 5-type axis plus `TaskCategory`/`custom_category` heuristics.
- `pipeline/orchestrator.py` does not execute task dependencies, does not batch by DAG depth, and does not reference `ResearchTask.dependencies`.
- No concrete post-synthesis verifier implementation module exists; filtering still lives as a helper inside `pipeline/orchestrator.py`.
- No provenance sidecar emission exists.
- No `structuring/` package, no `StructuredOutline`, and no real Pipeline-L2 implementation exist.
- `MarkdownRenderer` still renders directly from `ConfidenceMap` and raw findings.
- Orchestrator-level iterative round control does not exist.
- `ResearchAgent` already has its own per-agent round loop, which creates a real integration hazard for Wave 3B if the orchestrator gains a second, outer round loop without changing the L1 contract.
- `ContextLoader` exists but is not wired from the pipeline.
- `WikiBuilder` and `IndexMaintainer` exist but are not inserted into the live pipeline.

## 1. Delivery Map

### Wave 3

| Deliverable | Why it belongs to Wave 3 | Likely touched modules/files |
|---|---|---|
| Dual-axis taxonomy and domain-aware routing | Accepted overlay places `D-1` in Wave 3, after Wave 2B completes the load-bearing profile-routing path. | `src/keystone/models/research.py`, `src/keystone/models/__init__.py`, `src/keystone/specification/engagement_classifier.py`, `src/keystone/specification/prompts/classification.md`, `src/keystone/specification/template_registry.py`, `src/keystone/specification/task_generator.py`, `src/keystone/evaluator/rubric_config.py`, `tests/unit/specification/test_engagement_classifier.py`, `tests/unit/specification/test_template_registry.py`, `tests/unit/evaluator/test_rubric_config.py` |
| Provisional M&A / Restructuring evaluation profile expansion | The accepted plan explicitly adds provisional profile paths in Wave 3, with calibration still deferred to Wave 5. | `src/keystone/evaluator/rubric_config.py`, likely `src/keystone/evaluator/evaluator.py` only if Wave 2B profile routing still needs reinforcement, `tests/unit/evaluator/test_rubric_config.py`, `tests/unit/evaluator/test_evaluator.py`, `tests/unit/evaluator/test_layer3.py` |
| Deep research formalization and template-prompt wiring | Decision C says deep research remains experimental but must become auditable and consume template registry prompts in both deep and shallow modes. | `src/keystone/events.py`, `src/keystone/research/research_agent.py`, `src/keystone/pipeline/orchestrator.py`, `tests/unit/research/test_research_agent.py`, `tests/integration/test_deep_research.py`, `tests/unit/pipeline/test_orchestrator.py` |
| DAG topological batch dispatch | This is the accepted Wave 3 answer to B07 and is still absent from the runtime path. | `src/keystone/pipeline/orchestrator.py`, possibly `src/keystone/research/agent_pool.py`, possibly `src/keystone/models/tasks.py` only if new runtime status values are needed, `tests/unit/pipeline/test_orchestrator.py`, `tests/canary/test_architectural_guarantees.py`, `tests/integration/test_pipeline_real.py` |
| Concrete post-synthesis verifier | The contract exists already, but the accepted plan says the implementation lands in Wave 3. | Inference: new `src/keystone/pipeline/post_synthesis_verifier.py` is the cleanest landing spot because the current helper lives in the pipeline layer; also `src/keystone/pipeline/orchestrator.py`, `tests/unit/pipeline/test_orchestrator.py`, likely new `tests/unit/pipeline/test_post_synthesis_verifier.py` |
| Provenance sidecar generation | Accepted Wave 3 adjunct (`A14`) and depends on the now-available provenance/citation fields. | Inference: new `src/keystone/pipeline/provenance_sidecar.py` or similar, `src/keystone/pipeline/orchestrator.py`, `src/keystone/models/citations.py` only if output metadata needs expansion, `tests/unit/knowledge/*` or new pipeline-side tests |
| Remaining completeness hardening from E2 | Wave 3 still owns the concurrency-cleanup remainder, but current code suggests this is now mostly a hardening/cleanup pass rather than a greenfield feature. | `src/keystone/hitl/service.py`, `src/keystone/hitl/gate.py`, maybe small orchestrator glue changes, `tests/unit/hitl/test_service.py`, `tests/unit/hitl/test_gate.py`, canary regression coverage |

### Wave 3B

| Deliverable | Why it belongs to Wave 3B | Likely touched modules/files |
|---|---|---|
| `StructuredOutline` model | Accepted overlay places the thin real L2 in Wave 3B and requires a typed handoff instead of direct `ConfidenceMap -> renderer`. | Inference: new `src/keystone/models/structuring.py` or similar, `src/keystone/models/__init__.py`, possibly `src/keystone/contracts.py`, new unit tests for the model |
| Thin real Pipeline-L2 | Accepted overlay explicitly rejects skipping L2. | Inference: new `src/keystone/structuring/__init__.py`, new `src/keystone/structuring/content_structuring.py`, `src/keystone/contracts.py`, `tests/unit/test_protocol_contracts.py`, likely new `tests/unit/structuring/test_content_structuring.py` |
| Renderer migration to outline consumption | Accepted overlay requires the renderer to consume `StructuredOutline`, not raw `ConfidenceMap`. | `src/keystone/pipeline/markdown_renderer.py`, `tests/unit/pipeline/test_markdown_renderer.py`, `tests/e2e/test_mock_pipeline.py`, `tests/integration/test_pipeline_real.py` |
| Profile-driven round loop with persisted research-state continuity | Accepted overlay places the minimum viable live loop in Wave 3B, not in Wave 2B. | `src/keystone/pipeline/orchestrator.py`, inference: new `src/keystone/research/round_state.py` or `research_state.py`, `src/keystone/research/context_loader.py`, `src/keystone/knowledge/wiki_builder.py`, `src/keystone/knowledge/index_maintainer.py`, possibly `src/keystone/knowledge/engagement_store.py`, `tests/unit/research/test_context_loader.py`, `tests/unit/knowledge/test_wiki_builder.py`, `tests/unit/knowledge/test_index_maintainer.py` |
| Branch coverage computation between rounds | Accepted overlay says round N+1 work must come from uncovered branches, contradictions, and gaps. | `src/keystone/pipeline/orchestrator.py`, possibly new branch-coverage helper module under `src/keystone/specification/` or `src/keystone/research/`, `tests/unit/pipeline/test_orchestrator.py`, likely new branch-coverage unit tests |
| Lightweight sufficiency gate and novelty exhaustion at orchestrator scope | Accepted overlay requires a live stop surface at the round-controller level. | `src/keystone/pipeline/orchestrator.py`, possibly `src/keystone/deliberation/gap_detector.py` for reusable gap signals, likely new tests in `tests/unit/pipeline/` and `tests/integration/` |
| Round N+1 task refinement from prior findings/gaps/contradictions | Accepted overlay requires follow-on work generation, not raw replay. | `src/keystone/pipeline/orchestrator.py`, `src/keystone/specification/spec_engine.py`, possibly `src/keystone/specification/task_generator.py`, tests in `tests/unit/pipeline/test_orchestrator.py` and `tests/integration/test_pipeline_real.py` |

## 2. Dependency Graph

### Must-land-first items

1. Wave 2B must complete first, especially `E-9`, `E-10`, `E-6`, `E-7`, and governance/profile-routing work.
2. Dual-axis taxonomy model changes must land before domain-aware template routing and before provisional M&A / Restructuring profile paths are treated as meaningful runtime behavior.
3. `StructuredOutline` schema must stabilize before renderer migration.
4. Research-state persistence and branch-coverage plumbing must exist before a real orchestrator round loop can be trusted.
5. Concrete post-synthesis verifier logic should exist before provenance sidecar emission is wired through the final render path.
6. The orchestrator integration hotspot should land after lower-level primitives are ready; too many accepted Wave 3 / 3B items converge on `src/keystone/pipeline/orchestrator.py` to treat it as an early parallel slice.

### Items that can run in parallel

- Taxonomy/classification work can proceed in parallel with deep-research formalization.
- Verifier implementation can proceed in parallel with provenance sidecar formatting if both avoid `pipeline/orchestrator.py` until integration.
- L2 model/module work can proceed in parallel with research-state persistence and wiki-continuity plumbing.
- HITL polling hardening can proceed independently of taxonomy, verifier, and L2 work.

### Items that look parallelizable but actually are not

- Domain-aware routing and profile expansion look separate, but both are only valuable once Wave 2B makes the profile-routing path load-bearing.
- Renderer migration looks separate from L2, but it should not start until the final `StructuredOutline` contract is settled.
- Orchestrator DAG dispatch and Wave 3B iterative-loop control look like different features, but both mutate the same scheduling core in `pipeline/orchestrator.py`.
- Orchestrator live-loop work and the current `ResearchAgent` inner round loop look independent, but they are tightly coupled. If both remain active, the system will nest loops and mis-measure coverage, novelty, and stopping criteria.

## 3. Safe Implementation Slices

The safest future worker plan is to keep most work off `pipeline/orchestrator.py` until the final integration pass.

### Slice A: Taxonomy / Classification / Routing

Expected write set:
- `src/keystone/models/research.py`
- `src/keystone/models/__init__.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/template_registry.py`
- `src/keystone/specification/task_generator.py`
- `src/keystone/evaluator/rubric_config.py`
- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/evaluator/test_rubric_config.py`

Why this is safe:
- It is mostly self-contained in models/specification/evaluator mapping.
- It avoids the orchestrator hotspot.
- It resolves the current `custom_category` collapse path before more content work accumulates on the wrong routing axis.

### Slice B: Deep-Research Formalization

Expected write set:
- `src/keystone/events.py`
- `src/keystone/research/research_agent.py`
- `tests/unit/research/test_research_agent.py`
- `tests/integration/test_deep_research.py`

Why this is safe:
- It is isolated to L1 runtime behavior plus event emission.
- It can prepare the deep/shallow prompt path without fighting renderer or L2 work.

Planning note:
- The `orchestrator.py` governance-visibility hook for gateway bypass should be deferred to the orchestrator integration slice to keep write sets disjoint.

### Slice C: Verifier + Provenance Sidecar Primitives

Expected write set:
- Inference: new `src/keystone/pipeline/post_synthesis_verifier.py`
- Inference: new `src/keystone/pipeline/provenance_sidecar.py`
- `tests/unit/pipeline/test_orchestrator.py` or a new verifier-focused unit file
- New focused tests for sidecar generation

Why this is safe:
- It builds the concrete implementations behind already-accepted contracts and data fields.
- It can be developed and unit-tested before pipeline insertion.

### Slice D: Thin Pipeline-L2 Core

Expected write set:
- Inference: new `src/keystone/models/structuring.py`
- `src/keystone/models/__init__.py`
- Inference: new `src/keystone/structuring/__init__.py`
- Inference: new `src/keystone/structuring/content_structuring.py`
- `tests/unit/test_protocol_contracts.py`
- New `tests/unit/structuring/test_content_structuring.py`

Why this is safe:
- It creates the typed L2 seam without immediately rewriting the render path.
- It is mostly additive.

### Slice E: Renderer Migration

Expected write set:
- `src/keystone/pipeline/markdown_renderer.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/e2e/test_mock_pipeline.py`

Why this is safe:
- It depends on Slice D's finalized outline contract but does not need orchestrator control-flow changes.

### Slice F: Research-State Continuity / Wiki Plumbing

Expected write set:
- Inference: new `src/keystone/research/round_state.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/knowledge/wiki_builder.py`
- `src/keystone/knowledge/index_maintainer.py`
- Possibly `src/keystone/knowledge/engagement_store.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/knowledge/test_wiki_builder.py`
- `tests/unit/knowledge/test_index_maintainer.py`
- New tests for round-state persistence and branch coverage inputs

Why this is safe:
- It prepares the persistence and continuity layer the live loop needs.
- It stays out of the classifier/evaluator write sets.

### Slice G: HITL Polling Hardening

Expected write set:
- `src/keystone/hitl/service.py`
- `src/keystone/hitl/gate.py`
- `tests/unit/hitl/test_service.py`
- `tests/unit/hitl/test_gate.py`

Why this is safe:
- It is disjoint from taxonomy, L2, and research-state work.
- It closes the residual E2 hardening path without colliding with the orchestrator hotspot.

### Slice H: Orchestrator Integration Hotspot

Expected write set:
- `src/keystone/pipeline/orchestrator.py`
- Possibly `src/keystone/research/agent_pool.py`
- Possibly `src/keystone/specification/spec_engine.py`
- Possibly `src/keystone/specification/task_generator.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/integration/test_pipeline_real.py`
- `tests/canary/test_architectural_guarantees.py`

Responsibilities:
- DAG topological batch dispatch
- deep-research governance visibility
- concrete post-synthesis verifier insertion
- L2 insertion between deliberation and evaluation/rendering
- profile-driven outer round loop
- branch coverage use
- sufficiency/novelty stop logic
- round N+1 task refinement

Why this should have a single owner:
- It is the highest merge-conflict area in the entire Wave 3 / 3B plan.
- It is where false-green tests are most likely if multiple workers independently mock different subpaths.

## 4. Test Plan

### Baseline tests that should stay green before Wave 3 / 3B work starts

- `tests/unit/specification/test_engagement_classifier.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/knowledge/test_wiki_builder.py`
- `tests/unit/knowledge/test_index_maintainer.py`
- `tests/unit/deliberation/test_confidence_builder.py`
- `tests/canary/test_architectural_guarantees.py`

### Slice-by-slice additions

| Slice | Tests that should exist before | Tests that should exist after |
|---|---|---|
| A | existing classifier/registry/rubric-config tests | `test_classifier_emits_domain_category_and_secondary_types`, `test_template_registry_routes_on_domain_category`, `test_profile_map_supports_ma_and_restructuring` |
| B | existing `test_research_agent.py`, `test_deep_research.py` | `test_deep_research_emits_invocation_event`, `test_template_prompt_wired_in_deep_mode`, `test_template_prompt_wired_in_shallow_mode` |
| C | existing provenance filtering assertions in `test_orchestrator.py` and provenance tests in `test_confidence_builder.py` | `test_post_synthesis_verifier_filters_failed_and_unevaluated_claims`, `test_post_synthesis_verifier_rebuilds_gap_provenance`, `test_provenance_sidecar_records_consulted_vs_rendered_vs_rejected_sources` |
| D | current protocol-contract tests skip L2 | enable `ContentStructuringContract` conformance test; add `test_content_structurer_groups_claims_by_issue_tree_branch`, `test_structured_outline_preserves_claim_and_task_provenance` |
| E | current renderer tests | `test_renderer_consumes_structured_outline`, `test_renderer_does_not_drop_outline_provenance`, `test_renderer_keeps_weak_and_contested_sections_separate` |
| F | current context-loader/wiki/index tests | `test_round_state_persists_findings_gaps_and_stop_flags`, `test_context_loader_loads_only_prior_round_state`, `test_branch_coverage_computation_uses_issue_tree_branch_ids` |
| G | current HITL unit tests | `test_wait_for_decision_uses_short_lived_reads`, `test_duplicate_decision_submission_is_idempotent`, `test_polling_cleanup_does_not_hold_stale_state` |
| H | current orchestrator tests plus canary dependency test | unxfail and pass `test_dependent_tasks_do_not_start_before_dependencies_complete`; add `test_orchestrator_inserts_l2_before_evaluation`, `test_iterative_loop_stops_on_cap_quality_or_novelty`, `test_round_n_plus_1_tasks_use_prior_findings_and_open_gaps`, `test_nested_l1_and_l0_round_loops_do_not_double_iterate` |

### End-to-end and adversarial surfaces

- A full pipeline test where a dependency-root task fails and downstream tasks are marked `NOT_RUN` rather than silently executing.
- A multi-round test where round 2 has high overlap but one uncovered issue-tree branch; the loop must continue for coverage instead of stopping on naive "no new text" heuristics.
- A deep-research task in which gateway bypass is used; governance/audit visibility must surface that fact.
- An M&A or Restructuring engagement where classification, template routing, and evaluation profile selection all agree on the same domain path.
- A render path test proving failed or unevaluated task claims cannot leak back in through the L2 outline or sidecar path.

### False-positive / vacuous-test traps

- Do not test domain taxonomy only at classifier output; test the full path into template/profile routing.
- Do not treat "outline has N sections" as proof of L2 correctness; the test must verify claim-to-section assignment and provenance retention.
- Do not treat an empty second round as sufficient evidence of novelty exhaustion; test that uncovered branches and explicit gaps still force continuation.
- Do not test DAG execution only through sorted metadata; verify actual dispatch timing/batching behavior.
- Do not test the verifier only on high-confidence claims; weak, contested, insufficient, and gap provenance must also survive or be filtered correctly.

## 5. Likely Adversarial-Review Pressure Points

1. `pipeline/orchestrator.py` is now the central correctness hotspot. A superficially green implementation can still be architecturally false if verifier insertion, DAG batching, L2 insertion, and round control are not all running on the real path.
2. The current `ResearchAgent` already owns an inner iterative loop. Wave 3B must not simply add an outer orchestrator loop on top of it. That would create nested rounds, inflated cost, broken novelty signals, and misleading branch-coverage behavior.
3. Dual-axis taxonomy can be undermined by the surviving `custom_category` / fallback path in task generation and template matching. A partial implementation could appear correct at classification time while still silently routing strategic defaults downstream.
4. `StructuredOutline` can easily become a lossy abstraction if it strips claim IDs, task IDs, branch IDs, or citation provenance. If that happens, the verifier and provenance sidecar become decorative rather than load-bearing.
5. Some Wave 3 concurrency work already appears partially landed. A future worker could accidentally "reimplement" or regress those fixes while chasing doc language from `FINAL-DECISIONS-v2.1.md`. The plan should treat the live code and canary suite as the starting truth, not the older wave prose alone.

## 6. Open Questions

These are implementation-shape questions, not architecture re-decisions.

1. Where should the concrete post-synthesis verifier live: a new `pipeline/post_synthesis_verifier.py` beside the current helper, or a dedicated verification package? The contract exists; only the concrete home is unresolved.
2. How should Wave 3B reconcile the current per-agent inner round loop with the accepted orchestrator-level live loop? One of them must become subordinate, or the runtime will double-iterate.
3. Where should round-state persistence live: wiki store sidecar, engagement-store artifact, or a dedicated research-state file under engagement memory? The accepted plan requires persistence, but the storage home is still open.
4. Should provenance sidecar generation happen at pipeline render time or as part of the knowledge-store compilation path? Both are compatible with the accepted architecture, but ownership is still unresolved.

## Proposed Future Parallelization Plan for Wave 3 / 3B

Recommended worker split:

1. Worker A: Slice A (taxonomy / classification / routing)
2. Worker B: Slice B (deep-research formalization)
3. Worker C: Slice C (verifier + provenance sidecar primitives)
4. Worker D: Slice D (thin Pipeline-L2 core)
5. Worker E: Slice F (research-state continuity / wiki plumbing)
6. Worker F: Slice G (HITL polling hardening)
7. Final integrator: Slice E, then Slice H

This keeps five substantial slices off the orchestrator hotspot, then reserves the orchestrator and renderer convergence work for the end when upstream contracts are already stable.

## Recommended Order of Implementation Slices

1. Finish Wave 2B and confirm the profile-routing/sprint-contract path is genuinely load-bearing.
2. Slice A: taxonomy / classification / routing.
3. In parallel: Slice B, Slice C, Slice D, Slice F, Slice G.
4. Slice E once `StructuredOutline` is stable.
5. Slice H as the final convergence slice.
6. End-to-end integration and canary hardening after Slice H.

## Top 5 Risks Most Likely to Force Rework If Ignored

1. Leaving both the current L1 inner round loop and the future orchestrator loop active at the same time.
2. Implementing dual-axis taxonomy only at classification time while leaving downstream fallback routing untouched.
3. Allowing `StructuredOutline` to drop provenance-bearing identifiers.
4. Splitting `pipeline/orchestrator.py` across multiple workers before lower-level contracts stabilize.
5. Writing vacuous tests that validate mocked control flow instead of the real runtime path.
