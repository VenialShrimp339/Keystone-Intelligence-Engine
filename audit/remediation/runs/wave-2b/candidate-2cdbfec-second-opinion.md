# Wave 2B Second Opinion

- **Baseline commit:** `16e0bc7`
- **Target commit:** `2cdbfec`
- **Candidate parent:** `4ff7e90`
- **Reviewed snapshot:** detached worktree at `/private/tmp/kie-review-2cdbfec-second`
- **Commit surface reviewed:** `git show --stat --oneline 2cdbfec`, `git diff --name-only 16e0bc7..2cdbfec`, `git diff --name-only 4ff7e90..2cdbfec`, targeted `rg`/source inspection, the required pytest matrix, and direct runtime probes
- **Scoping note:** code truth came only from `/private/tmp/kie-review-2cdbfec-second`; control-plane and review-authority docs were read from the main workspace

## Authority and Method

I read these authority/context documents before reviewing code:

- `graphify-out/GRAPH_REPORT.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/WAVE-2B-SETUP.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-implementation.md`
- `audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md`
- historical blocked packets for `4ff7e90`

I focused on three questions:

1. Are `W2B-B01` through `W2B-B04` actually closed on the real runtime path?
2. Does any historical failure family still survive in a less obvious form?
3. Did the recovery delta stay inside the approved Wave 2B boundary?

## Findings

### 1. Sprint-contract generation still accepts syntactically valid but underspecified JSON and silently collapses Wave 2B fields to empty values

- **Severity:** `DESIGN_CONCERN`
- **Area:** Optional hardening / contract fail-open family
- **File and line number:** `src/keystone/evaluator/sprint_contract.py:53-79`
- **What I found:** The invalid-JSON path is now fixed correctly: `safe_llm_json()` failures raise a `RuntimeError` instead of falling back to a bare contract. But the generator still accepts syntactically valid JSON that omits Wave 2B fields and returns `mandatory_elements=[]`, `anti_patterns=[]`, and `dimension_emphasis={}` without complaint. Direct probe on `2cdbfec`: returning `{"acceptance_criteria": ["Only criteria returned"]}` produced exactly those empty Wave 2B enforcement fields.
- **Why it matters:** This does not reopen any of the four active Wave 2B blockers, but it means the broader `W2B-R01` failure family is only partially closed. The candidate implementation note claims `W2B-R01` is closed; I do not think that claim is fully true unless “malformed” is restricted to parse-invalid JSON only.
- **What should change:** If the controller wants `W2B-R01` actually closed rather than merely improved, validate required contract structure after parsing and fail closed when Wave 2B fields are absent or malformed.

## Blocker Ledger Closure Check

I did **not** find a remaining blocker in `W2B-B01` through `W2B-B04`.

- `W2B-B01` appears closed. `ProfileExecutionPolicy.evaluate_coverage()` now treats failed evaluated LIGHT tasks as uncovered via `_requires_light_pass()` even after `record_evaluation_outcome()` clears `renderable` in `src/keystone/governance/policy.py:108-185`.
- `W2B-B02` appears closed. `TaskGenerator` now derives `priority` from Step-5 ranks and derives `importance` from the resolved `priority_rank`, not raw LLM list order, in `src/keystone/specification/task_generator.py:126-248`.
- `W2B-B03` appears closed. `ResearchSpec` persists `effective_evaluation_profile`, `SpecificationEngine` writes it once at spec construction, and orchestrator routing reads that stored field in `src/keystone/models/research.py:166-178`, `src/keystone/specification/spec_engine.py:351-358`, and `src/keystone/pipeline/orchestrator.py:619-634`.
- `W2B-B04` appears closed. Gate 1 and Gate 2 now consult `ProfileExecutionPolicy.should_run_hitl_gate()` in `src/keystone/specification/spec_engine.py:375-386` and `src/keystone/deliberation/deliberation.py:191-207`. A repo-wide search for `PipelineProfile.LIGHT` only found policy-owned checks plus evaluator-intensity routing.

## Verification Matrix

Command run from `/private/tmp/kie-review-2cdbfec-second`:

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

Result: `151 passed in 1.80s`

## Direct Runtime Probes

- **Persisted evaluator profile probe:** constructing an `EVALUATIVE` spec with `effective_evaluation_profile=STRATEGIC` and `effective_pipeline_profile=DEEP` produced `profile strategic` and `intensity deep`, confirming evaluator routing now reads stored spec state rather than re-deriving profile from `engagement_type`.
- **Sprint-contract partial-shape probe:** returning syntactically valid JSON with only `acceptance_criteria` yielded `mandatory_elements=[]`, `anti_patterns=[]`, and `dimension_emphasis={}`, confirming the optional `W2B-R01` family still survives in a narrower form.
- **Static gate-ownership probe:** repo-wide `PipelineProfile.LIGHT` search showed no remaining Gate 1 / Gate 2 leaf-level LIGHT short-circuits outside `ProfileExecutionPolicy`.

## Wave Boundary Check

The recovery delta stayed Wave-2B-bounded.

- `git diff --name-only 4ff7e90..2cdbfec` touched exactly the 16 expected code/test files plus `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json`.
- That matches `audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md:8-35,69-104`.
- I did not find new Wave 3 / 3B / 4 / 4B / 5 code leakage in the parent delta.

## Verdict

`CLEARED`

My second opinion is that `2cdbfec` clears Wave 2B against the active blocker ledger. The four blocking runtime invariants are now load-bearing on the committed path, the required matrix passes, and the recovery delta stayed within the approved Wave 2B boundary. I would carry forward the sprint-contract shape issue as a non-blocking residual concern rather than keep Wave 2B blocked over it.
