Read these first, in order:
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/graphify-out/GRAPH_REPORT.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/SESSION-LOG.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SETUP.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SCOPE-GUARD.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SECOND-OPINION.md`

Important context:
- Wave 2A is fully cleared in commit `16e0bc7`.
- Wave 2B checkpoint candidate `4ff7e90` is blocked.
- Work only on Wave 2B blockers. Do not start Wave 3, 3B, 4, or doc reconciliation.
- The working tree is noisy. Be careful with mixed files, especially:
  - `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/specification/spec_engine.py`
  - `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/evaluator/evaluator.py`
- Do not sweep in unrelated dirty hunks.

What the two reviews agree on:
- Wave 2B made real progress.
- The remaining failures cluster around one theme:
  enforcement truth is still partly decorative rather than fully policy-owned and execution-path load-bearing.

Task:
Patch the confirmed Wave 2B blockers only.

Required fixes:

1. Fix LIGHT coverage so failed evaluated tasks cannot disappear from enforcement.
   - In `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/governance/policy.py`, make the LIGHT coverage check load-bearing for tasks that were evaluated and failed.
   - Do not key LIGHT coverage purely off `renderable`.
   - The policy must still halt when a LIGHT task produced output, was evaluated, and did not pass.
   - Add a runtime-path regression that proves a failed LIGHT evaluation triggers coverage halt.

2. Make task `priority` and `importance` derive from Step-5 scored priorities, not raw LLM list order.
   - In `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/specification/task_generator.py`, use the actual `PriorityScore` mapping / branch score data.
   - A higher-scored branch returned later in the LLM list must still become the higher-priority / more important task.
   - Add a regression test where the highest-scored branch is listed second and must still become `PRIMARY` or `CRITICAL` as appropriate.

3. Make `E-10` real by carrying an effective evaluation profile through `ResearchSpec` and routing `Evaluator` from that field.
   - Do not recompute the evaluator profile at the last minute from `engagement_type`.
   - Persist the resolved effective evaluation profile on `ResearchSpec`.
   - Route the live evaluator path from that persisted field.
   - Add a runtime-path regression that would fail if profile selection falls back to local remapping. Use a mismatched case, not an aligned one.

4. Centralize HITL gate ownership on `ProfileExecutionPolicy`.
   - The shared policy already has `should_run_hitl_gate()`.
   - `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/specification/spec_engine.py` and `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/deliberation/deliberation.py` should not each hardcode their own LIGHT skip logic.
   - Make the runtime path consult the shared policy helper instead.
   - Add tests that prove LIGHT skips and non-LIGHT blocks through the shared policy path.

Strongly recommended if cheap while you are already in scope:

5. Fix the observability mismatch where emitted rubric weights do not reflect `dimension_emphasis`.
   - If you touch `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/src/keystone/evaluator/evaluator.py`, do it carefully because the file already has unrelated dirty hunks.
   - If this cannot be done cleanly without sweeping unrelated changes, explicitly leave it out and say so.

6. Tighten the sprint-contract malformed-response path if it is cheap and clean.
   - If malformed contract JSON still silently degrades to a bare contract, either make that failure explicit or add a focused TODO / risk note in your summary.
   - Do not widen scope if this turns into a bigger design question.

Suggested verification matrix:
```bash
PYTHONPATH=src .venv/bin/pytest -q \
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

Stop after:
- the confirmed blockers are fixed
- the focused matrix is green
- graphify is rebuilt if code changed
- you summarize:
  - exact files changed
  - exact tests run
  - exact results
  - exact files safe to stage for the next Wave 2B checkpoint candidate

Do not do doc reconciliation in this session.
