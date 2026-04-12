# Wave 2B Adversarial Review

- **Baseline commit:** `16e0bc7`
- **Target commit:** `4ff7e90`
- **Reviewed snapshot:** detached worktree at `4ff7e90` only
- **Commit surface reviewed:** `git show --stat --oneline 4ff7e90`, `git diff --name-only 16e0bc7..4ff7e90 -- src/ tests/`, `git diff 16e0bc7..4ff7e90 -- src/ tests/`, targeted `rg` probes, focused pytest matrix, and tiny runtime probes
- **Scoping note:** `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` and `audit/remediation/BUILD-PROCESS.md` are present on disk but not in git history at `4ff7e90`; I used them as launcher/scoping context only, not as reviewed code artifacts

## Findings

### 1. LIGHT evaluation failures are invisible to the coverage gate
- **Severity:** `BLOCKER`
- **Area:** Enforcement model / coverage policy
- **File and line number:** `src/keystone/governance/policy.py:113-118,183-184`
- **What you found:** `record_evaluation_outcome()` clears `renderable` on any failed L4 result, but the LIGHT branch in `evaluate_coverage()` only halts on tasks that remain renderable. A LIGHT task that is evaluated and fails therefore disappears from coverage entirely. Direct probe on `4ff7e90`: after a failed LIGHT evaluation the task ended as `evaluation_status='failed', renderable=False`, and `evaluate_coverage()` returned `None`.
- **Why it matters:** Wave 2B's LIGHT policy is supposed to require that every renderable task be evaluated and passed. In the committed snapshot, a failed LIGHT task can fall out of coverage and let the pipeline continue instead of halting. That makes the coverage policy non-load-bearing for exactly the failure mode it was added to enforce.
- **What should change:** Compute LIGHT coverage from evaluation status rather than the post-failure `renderable` bit, or preserve enough state to distinguish "failed after evaluation" from "never renderable." Add a runtime-path test for "evaluated but failed" LIGHT tasks.

### 2. Task importance is keyed off LLM output order, not scored priorities
- **Severity:** `BLOCKER`
- **Area:** Task-scope governance / coverage inputs
- **File and line number:** `src/keystone/specification/task_generator.py:121-145,204-229`
- **What you found:** `TaskGenerator` computes `priority_entry = priority_map.get(...)` and then ignores it. Instead, both `priority` and `importance` are derived from `i + 1`, i.e. raw list order. Direct probe on `4ff7e90`: a lower-priority branch listed first became `task_low branch_low 1 primary`, while the higher-scored branch listed second became `task_high branch_high 2 supporting`.
- **Why it matters:** Wave 2B enforcement depends on `PRIMARY` and `CRITICAL` being assigned to the right tasks. If those labels are derived from arbitrary LLM ordering instead of Step-5 priority scores, governance can halt, degrade, or render against the wrong tasks even when the rest of the orchestration path is wired correctly.
- **What should change:** Derive `priority` and `importance` from the scored priority data / branch mapping instead of list order. Add a test where the higher-scored branch is returned second and must still become `PRIMARY`/`CRITICAL`.

### 3. The effective profile still does not drive evaluator weights
- **Severity:** `BLOCKER`
- **Area:** Execution-path truth / evaluator routing
- **File and line number:** `src/keystone/pipeline/orchestrator.py:619-634`
- **What you found:** `_resolve_evaluation_profile()` ignores `research_spec.effective_pipeline_profile` and routes evaluator weights only from `engagement_type`; only `_resolve_evaluation_intensity()` reads the effective pipeline profile. Direct probe on `4ff7e90`: an `EVALUATIVE` spec with `effective_pipeline_profile=LIGHT` produced `profile=default intensity=light_touch`; changing only the effective profile to `DEEP` still produced `profile=default intensity=deep`.
- **Why it matters:** This does not satisfy the Wave 2B requirement that the effective profile from `ResearchSpec` reaches `Evaluator` and becomes load-bearing. It also leaves the historical "default profile instead of the effective one" regression partially alive. The new test only covers the aligned `STRATEGIC + DEEP` case, so it would stay green even if effective-profile routing were broken.
- **What should change:** Route evaluator profile from an effective field on `ResearchSpec`, or from a deterministic mapping keyed off `effective_pipeline_profile`, and add a mismatched-profile runtime test such as `EVALUATIVE + DEEP` or `EXPLORATORY + STANDARD`.

### 4. The new sprint-contract path can still silently collapse back to a bare contract
- **Severity:** `DESIGN_CONCERN`
- **Area:** Sprint-contract wiring / bare-contract regression
- **File and line number:** `src/keystone/evaluator/sprint_contract.py:53-57,66-75`
- **What you found:** `Pipeline` now calls `SprintContractGenerator.generate()`, but when contract JSON parsing fails the generator logs a warning and falls back to `task.acceptance_criteria` with empty `mandatory_elements` and `anti_patterns`. Direct probe on `4ff7e90` with malformed LLM output returned the original criteria and both optional lists empty.
- **Why it matters:** This reopens the same failure class Wave 2B was meant to close: the runtime can still evaluate against a bare / partially populated contract, and `mandatory_elements` / `anti_patterns` stop being load-bearing exactly when the LLM response is malformed.
- **What should change:** Fail closed or retry on malformed sprint-contract JSON instead of silently degrading to the pre-2B bare-contract behavior. Add a malformed-response test proving the runtime does not continue with an empty contract.

### 5. `dimension_emphasis` is consumed in scoring, but runtime events still report stale base weights
- **Severity:** `WARNING`
- **Area:** Rubric/runtime observability
- **File and line number:** `src/keystone/evaluator/evaluator.py:179-186`
- **What you found:** Layer 3 scoring correctly applies `dimension_emphasis`, but emitted `RubricDimensionScored.weight` values still come from `self._weights`, i.e. the base profile weights. Runtime telemetry therefore reports stale weights even when the score was computed with adjusted weights.
- **Why it matters:** The scoring path is correct, but observability is misleading. That makes it harder to prove in production that `dimension_emphasis` was truly consumed, and it weakens debugging for exactly the rubric-load-bearing path this wave targeted.
- **What should change:** Emit adjusted per-contract weights with the score events, and add an evaluator-level test that asserts event weights change when `dimension_emphasis` changes.

### 6. The commit stayed code-bounded, but not perfectly commit-bounded
- **Severity:** `NOTE`
- **Area:** Wave-boundary discipline
- **File and line number:** `audit/remediation/WAVE-2A-FINAL-DEEP-REVIEW-16e0bc7.md:1`
- **What you found:** I found no Wave 3 / 3B / 4 / 5 implementation leakage in changed `src/` or `tests/` code. The commit does, however, include Wave 2A archival/docs churn (`CURRENT-STATE.md`, `WORKSTREAM-STATUS.md`, `SESSION-LOG.md`, and the final Wave 2A review artifact) alongside the Wave 2B implementation.
- **Why it matters:** This does not change runtime behavior, but it weakens the one-wave-one-commit review boundary that the build docs call for.
- **What should change:** Keep archival/doc reconciliations in a separate commit from wave code whenever possible.

## Focused Verification Matrix

No dedicated Wave 2B verification-matrix file was present in the target snapshot, so I built a focused matrix from the changed files and the explicit Wave 2B requirements:

1. **Spec / policy / HITL / task-importance slice**
   - `tests/unit/specification/test_spec_engine.py::TestSpecificationEngine::test_research_spec_fields`
   - `tests/unit/governance/test_policy.py`
   - `tests/unit/hitl/test_gate.py::TestCreateAndWaitForGate::test_modified_gate_halts_until_patch_is_applied`
   - `tests/unit/hitl/test_gate.py::TestHITLEventEmission::test_modify_emits_created_and_modified_events`
   - `tests/unit/deliberation/test_deliberation.py::TestHITLGate::test_gate_modified_without_applied_patch_halts`
   - `tests/unit/deliberation/test_deliberation.py::TestHITLGate::test_light_profile_skips_gate_two`
   - `tests/unit/specification/test_task_generator.py::TestTaskGenerator::test_sets_primary_importance_for_first_task`
   - `tests/unit/test_research_models.py::TestResearchSpecBatch2::test_pipeline_profile_defaults`
   - **Result:** `11 passed in 0.47s`

2. **Evaluator / rubric / orchestrator runtime-path slice**
   - `tests/unit/evaluator/test_sprint_contract.py`
   - `tests/unit/evaluator/test_layer3.py`
   - `tests/unit/pipeline/test_orchestrator.py::TestWave2BWiring`
   - `tests/unit/pipeline/test_orchestrator.py::TestPartialPipeline::test_empty_findings_halt_under_standard_coverage`
   - `tests/unit/pipeline/test_orchestrator.py::TestRendererGating::test_renderer_drops_claims_from_failed_tasks`
   - `tests/unit/pipeline/test_orchestrator.py::TestRendererGating::test_renderer_drops_claims_from_unevaluated_tasks`
   - `tests/unit/pipeline/test_orchestrator.py::TestRendererGating::test_renderer_drops_failed_task_feedback_and_shared_alias_rows`
   - **Result:** `33 passed in 0.28s`

3. **Tiny runtime probes used to challenge disputed paths**
   - LIGHT failed evaluation coverage: `light_outcome failed False` and `light_coverage_flag None`
   - Effective-profile routing: `light evaluative -> profile default intensity light_touch`; `deep evaluative -> profile default intensity deep`
   - Task-importance routing: `task_low branch_low 1 primary`; `task_high branch_high 2 supporting`
   - Sprint-contract fallback: malformed contract JSON returned task defaults with empty `mandatory_elements` / `anti_patterns`

## Residual Test Gaps

- There is still no runtime-path test for LIGHT-profile Gate 1 skip in `SpecificationEngine`; the changed spec-engine coverage stops at field population.
- The task-importance tests prove "first task becomes PRIMARY," not that scored priorities survive into governance.
- `test_orchestrator_passes_profile_to_evaluator` uses the aligned `STRATEGIC + DEEP` case, so it does not fail when `effective_pipeline_profile` is ignored for evaluator profile selection.
- Helper-level `GateResolution.patch_applied` blocking is covered, but downstream deliberation coverage still relies on a synthetic mocked return that the real helper never emits because it raises first.

## Verdict

`BLOCKED`

Wave 2B is not clear to checkpoint from `16e0bc7..4ff7e90`. The committed snapshot successfully adds most of the intended surfaces, and the focused matrix passes, but three execution-path blockers remain: LIGHT failed evaluations can evade coverage halting, task importance is assigned from LLM list order instead of scored priorities, and the effective profile still does not drive evaluator weights. Until those are fixed, the enforcement model is still not trustworthy enough to clear.
