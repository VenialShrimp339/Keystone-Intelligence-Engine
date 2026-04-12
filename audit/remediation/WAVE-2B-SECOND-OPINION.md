# Wave 2B Second Opinion

*Date: 2026-04-11 | Baseline commit: `16e0bc7` | Target commit: `4ff7e90`*

---

## Scope and Method

- Reviewed the committed snapshot only, using a detached worktree at `/tmp/kie-review-4ff7e90`
- Compared `16e0bc7..4ff7e90`, with the code-review focus kept on `src/` and `tests/`
- Read `graphify-out/GRAPH_REPORT.md`, `audit/remediation/WORKSTREAM-STATUS.md`, `CURRENT-STATE.md`, and `audit/remediation/WAVE-2B-SETUP.md` from the target snapshot where available
- Note: the prompt referenced `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` and `audit/remediation/BUILD-PROCESS.md`, but those files are not present in `4ff7e90`
- Used parallel sub-reviewers for execution path, enforcement policy, rubric/runtime consumption, and test-integrity checks

---

## Verification Matrix

```bash
/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/.venv/bin/pytest \
  tests/unit/pipeline/test_orchestrator.py \
  tests/unit/governance/test_policy.py \
  tests/unit/evaluator/test_layer3.py \
  tests/unit/deliberation/test_deliberation.py \
  tests/unit/hitl/test_gate.py \
  tests/unit/specification/test_spec_engine.py \
  tests/unit/specification/test_task_generator.py \
  tests/unit/test_research_models.py
```

Result: `128 passed in 1.45s`

---

## Executive Summary

Wave 2B does land real progress: the orchestrator now calls `SprintContractGenerator.generate()`, `dimension_emphasis` affects the live geometric-mean score, `mandatory_elements` / `anti_patterns` do reach rubric prompts on the happy path, the epsilon fix is real in the scoring path, and `task_outcomes` are updated and used for evaluation/render gating.

I do not think this snapshot clears Wave 2B yet. Two intended Wave 2B guarantees are still not true in the committed runtime path: L0/HITL enforcement is still hardcoded instead of policy-owned, and the evaluator profile is still recomputed at the last moment instead of being carried through `ResearchSpec` as the wave setup requires. There are also robustness and test-integrity gaps that make the new behavior easier to silently regress than it should be.

---

## Findings

### Finding 1

- **Severity:** `BLOCKER`
- **Area:** Enforcement model correctness
- **File and line number:** `src/keystone/specification/spec_engine.py:363-365`, `src/keystone/deliberation/deliberation.py:190-192`, `src/keystone/governance/policy.py:39-40`
- **What I found:** Wave 2B adds `ProfileExecutionPolicy.should_run_hitl_gate()`, but neither Gate 1 nor Gate 2 actually consult it. `SpecificationEngine` and `Deliberation` both inline their own `PipelineProfile.LIGHT` short-circuit instead.
- **Why it matters:** One of the explicit Wave 2B review targets was that spec-engine/L0 enforcement become profile-owned rather than ad hoc. In this snapshot, the central policy object exists but the HITL gating decision is still duplicated in leaf modules, so the enforcement surface is not actually centralized.
- **What should change:** Route HITL gate decisions through `ProfileExecutionPolicy` instead of hardcoded profile checks, and add runtime-path tests that prove LIGHT skips and non-LIGHT blocks by consulting the shared policy.

### Finding 2

- **Severity:** `BLOCKER`
- **Area:** Execution-path truth
- **File and line number:** `src/keystone/pipeline/orchestrator.py:282-285`, `src/keystone/pipeline/orchestrator.py:619-623`, `src/keystone/models/research.py:157-168`
- **What I found:** The evaluator profile still does not come from `ResearchSpec`. `ResearchSpec` now stores pipeline-profile fields, but no resolved evaluation-profile field. At runtime the orchestrator rebuilds the evaluator profile from `spec.research_spec.engagement_type` via `_resolve_evaluation_profile(spec)` immediately before constructing `Evaluator`.
- **Why it matters:** Wave 2B setup item `E-10` was to pass the effective evaluation profile from `ResearchSpec` into `Evaluator`. This snapshot only re-derives a profile locally. That means any spec-time override, blend, or future profile-generation logic would be silently discarded before evaluation.
- **What should change:** Persist the resolved evaluation profile on `ResearchSpec` and pass that field directly into `Evaluator`, with a runtime-path test that fails if the code goes back to local remapping.

### Finding 3

- **Severity:** `DESIGN_CONCERN`
- **Area:** Rubric/runtime consumption
- **File and line number:** `src/keystone/pipeline/orchestrator.py:275`, `src/keystone/evaluator/sprint_contract.py:53-75`
- **What I found:** The new live path now depends on `SprintContractGenerator.generate()`, but any contract parse failure silently falls back to task defaults and clears `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` to empty values.
- **Why it matters:** On the happy path, the Wave 2B rubric fields are load-bearing. On the parse-failure path, the run silently degrades back toward pre-Wave-2B behavior without failing closed. That makes `E-6` / `E-7` only conditionally true.
- **What should change:** Make sprint-contract parse failure explicit in enforcement, or preserve non-empty fallback behavior for the Wave 2B fields, and add a regression test for the parse-failure path.

### Finding 4

- **Severity:** `WARNING`
- **Area:** Test quality
- **File and line number:** `tests/unit/deliberation/test_deliberation.py:274-311`, `src/keystone/hitl/gate.py:207-208`, `tests/unit/specification/test_spec_engine.py:238-260`
- **What I found:** The new modified-gate deliberation test does not exercise the real runtime path. It mocks `create_and_wait_for_gate()` to return `GateResolution(status=MODIFIED, patch_applied=False)` and expects `Deliberation` to raise, but the real helper raises `GateModificationRequiredError` before returning that state. Separately, the spec-engine tests only verify profile fields are populated; they do not prove that LIGHT actually skips Gate 1 at runtime.
- **Why it matters:** These tests can stay green while the real gate behavior changes underneath them. That is exactly the kind of constructor-level or mocked-path coverage the Wave 2B review brief told us to challenge.
- **What should change:** Add runtime-path tests around the real modified-gate helper semantics and add a spec-engine test that proves LIGHT profile actually suppresses Gate 1.

### Finding 5

- **Severity:** `WARNING`
- **Area:** Runtime observability
- **File and line number:** `src/keystone/evaluator/layer3_rubric.py:135-166`, `src/keystone/evaluator/evaluator.py:178-186`
- **What I found:** `dimension_emphasis` does change the actual `weighted_total`, but the emitted `RubricDimensionScored.weight` values still come from the base profile weights stored on `Evaluator`, not the adjusted weights used during scoring.
- **Why it matters:** The live score is correct, but the event stream explaining that score is wrong whenever a sprint contract emphasizes or de-emphasizes dimensions. That weakens auditability and makes downstream consumers misread the scoring path.
- **What should change:** Emit the effective adjusted weights alongside dimension-score events, or otherwise align the runtime event payload with the weights actually used for scoring.

---

## Residual Positives

- `SprintContractGenerator.generate()` is genuinely used in the live orchestrator path.
- `task_outcomes` are initialized, updated after L1/L4, and then used for coverage and render gating.
- `mandatory_elements` and `anti_patterns` do reach rubric prompts on the successful contract-generation path.
- `dimension_emphasis` changes live scoring behavior.
- The geometric-mean epsilon is `0.01` in the real scoring path, and the targeted test would fail if it reverted.
- I did not find code-level Wave 3 / 3B leakage in the `src/` and `tests/` surface reviewed here.

---

## Verdict

`BLOCKED`

Wave 2B should not be cleared from `16e0bc7` to `4ff7e90` yet. The main reasons are that profile-owned L0 enforcement is still not actually policy-owned in runtime code, and `E-10` is still implemented as last-minute remapping rather than carrying an effective evaluation profile through `ResearchSpec`.
