# Wave 2B Adversarial Review

- **Baseline commit:** `16e0bc7`
- **Candidate parent:** `4ff7e90`
- **Target commit:** `2cdbfec`
- **Reviewed snapshot:** `/private/tmp/kie-review-2cdbfec-adversarial`
- **Authority/context docs read from main workspace:** control plane, handoff, blocker ledger, final decisions, Wave 2B setup, adversarial prompt, candidate implementation/file manifest, and historical blocked review packets
- **Code review scope:** committed snapshot only; full diff `16e0bc7..2cdbfec`, with parent-delta `4ff7e90..2cdbfec` used to separate recovery changes from already-blocked Wave 2B surface

## Scope and Method

- Reviewed the committed code in the detached review worktree and ignored the dirty main workspace for implementation truth.
- Checked the full baseline diff, targeted `rg` probes for execution-path and policy wiring, and line-by-line review of the Wave 2B surfaces in `policy.py`, `orchestrator.py`, `spec_engine.py`, `task_generator.py`, `deliberation.py`, `sprint_contract.py`, `layer3_rubric.py`, and related tests.
- Ran the required verification matrix from the review worktree:

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

- **Result:** `151 passed in 1.81s`
- Ran one direct runtime probe against the committed `SprintContractGenerator.generate()` path to challenge bare-contract regression behavior.

## Findings

### 1. Parseable but under-specified sprint-contract JSON still degrades to a partially bare contract
- **Severity:** `DESIGN_CONCERN`
- **Area:** Sprint-contract robustness / bare-contract regression
- **File and line number:** `src/keystone/evaluator/sprint_contract.py:63-79`, `tests/unit/evaluator/test_sprint_contract.py:87-169`
- **What I found:** The candidate correctly hard-fails malformed JSON, but it still accepts parseable JSON objects that omit Wave 2B enforcement fields. `generate()` defaults `mandatory_elements` to `[]`, `anti_patterns` to `[]`, and `dimension_emphasis` to `{}` whenever those keys are absent. Direct probe on `2cdbfec`: returning `{"acceptance_criteria": ["keep the section concise"]}` produced a contract with `mandatory_elements=[]`, `anti_patterns=[]`, and `dimension_emphasis={}`.
- **Why it matters:** The main Wave 2B runtime path is fixed, but the older “bare / partially populated sprint contract” failure family is not fully gone. `E-6` and `E-7` are load-bearing only when the LLM returns those fields, so a parseable but thin response still weakens enforcement without an explicit failure.
- **What should change:** Validate the generated JSON as a complete Wave 2B contract, or apply an explicit non-empty fallback policy for `mandatory_elements` / `anti_patterns` / `dimension_emphasis`. Add a regression test for parseable but under-specified JSON, not just malformed JSON.

## Residual Positives

- `SprintContractGenerator.generate()` is on the real orchestrator path and the generated contract is what reaches `Evaluator` (`src/keystone/pipeline/orchestrator.py:275-289`, `tests/unit/pipeline/test_orchestrator.py:1480-1483`).
- The persisted evaluation profile is now carried on `ResearchSpec` and routed directly into `Evaluator` (`src/keystone/models/research.py:166-180`, `src/keystone/specification/spec_engine.py:353-357`, `src/keystone/pipeline/orchestrator.py:619-624`, `tests/unit/pipeline/test_orchestrator.py:1486-1545`).
- Step-5 priority routing is now load-bearing for `priority` and `importance` (`src/keystone/specification/task_generator.py:129-162,232-247`, `tests/unit/specification/test_task_generator.py:206-286`).
- Gate 1 and Gate 2 now consult `ProfileExecutionPolicy.should_run_hitl_gate()` on the committed runtime path (`src/keystone/specification/spec_engine.py:375-386`, `src/keystone/deliberation/deliberation.py:191-215`, `tests/unit/specification/test_spec_engine.py:286-335`, `tests/unit/deliberation/test_deliberation.py:324-390`).
- LIGHT coverage no longer fails open on failed evaluated tasks (`src/keystone/governance/policy.py:113-175,177-245`, `tests/unit/governance/test_policy.py:131-159`, `tests/unit/pipeline/test_orchestrator.py:1547-1575` and adjacent runtime-path coverage tests).
- The epsilon fix, prompt-context propagation, and adjusted-weight observability are real in the scoring path (`src/keystone/evaluator/layer3_rubric.py:34-111,135-166`, `src/keystone/evaluator/evaluator.py:179-191`, `tests/unit/evaluator/test_layer3.py:213-387`, `tests/unit/evaluator/test_evaluator.py:432-471`).
- I did not find Wave 3 / 3B implementation leakage in the reviewed `src/` and `tests/` surface. The broader `16e0bc7..2cdbfec` diff includes the already-blocked `4ff7e90` Wave 2B surface plus the recovery delta, which is consistent with the control-plane review scope.

## Verdict

`CLEARED`

The four active Wave 2B blockers from the control plane are closed on the committed runtime path in `2cdbfec`, and the required verification matrix passed in the review worktree. I do not have a blocker against clearing Wave 2B at this candidate.

Residual risk remains around parseable but under-specified sprint-contract JSON. That should be treated as a follow-up hardening item, not as a reason to keep `2cdbfec` blocked under the current Wave 2B blocker ledger.
