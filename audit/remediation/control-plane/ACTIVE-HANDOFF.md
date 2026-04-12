# Active Handoff

## Current Truth

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B is cleared at `2cdbfec`.
- Wave 3A seam freeze is committed in `65074ca`.
- Wave 3 is cleared at `4819527`.
- Wave 3B is cleared at `5cc9585`.
- Wave 4 is cleared at `6406e46`.
- Wave 4B is now cleared at `65a612d`.
- The main workspace remains controller/docs only.
- `WAVE-4B-SETUP.md` remains the frozen boundary for what Wave 4B was allowed to change.
- All required Wave 4B review packets now exist in the main workspace.
- The clean Wave 4B implementation lane stayed inside the approved content slices and did not reopen deferred capability work.
- Wave 5 calibration remains gated off.
- A hard stop is now active because the required next-wave authority artifact is missing.
- The controller is expected to continue **autonomously across checkpoints**, but hard stops still terminate forward motion.

## Authoritative Order

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md)
4. [candidate-65a612d-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md)
5. [WAVE-4B-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4B-SETUP.md)
6. [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md)
7. [WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md)
8. [WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md)
9. [WAVE-4-TEMPLATE-ROUTING-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md)
10. [WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md)
11. [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
12. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
13. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)

## Active State Tuple

- `active_wave`: `wave-4b`
- `active_state`: `cleared`
- `execution_baseline_commit`: `6406e46`
- `review_target_commit`: `65a612d`
- `docs_reconcile_commit`: `HEAD`
- `next_recovery_checkout`: `65a612d`

## Open Blockers

- Hard stop: required authority artifact missing for any post-Wave-4B lane. Do not start Wave 5, calibration, or any new capability work until a new committed setup checkpoint exists.

## Latest Review Packets

- [candidate-65a612d-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-adversarial-review.md)
- [candidate-65a612d-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-second-opinion.md)
- [candidate-65a612d-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md)
- [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md)

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Treat `65a612d` as the last cleared code commit.
3. Keep the main workspace docs-only.
4. Do **not** start Wave 5, calibration, or any deferred capability slice.
5. Stop until a controller-approved next-wave setup artifact is created and committed.

## Exact Recovery Command

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
sed -n '1,240p' audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml
sed -n '1,260p' audit/remediation/control-plane/ACTIVE-HANDOFF.md
sed -n '1,220p' audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md
```

## Allowed Write Set

### Active docs-only cleared scope

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/EXECUTION-TODO.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `CURRENT-STATE.md`

### No active code lane

Any future post-Wave-4B code lane requires a new controller-approved setup artifact first.

## Required Test Matrix

Wave 4B cleared with the following required matrix:

1. `tests/unit/deliberation/test_analyst.py`
2. `tests/unit/deliberation/test_aggregator.py`
3. `tests/unit/research/test_research_agent.py`
4. `tests/unit/specification/test_intent_clarifier.py`
5. `tests/unit/specification/test_task_generator.py`
6. `tests/unit/specification/test_template_registry.py`
7. `tests/unit/evaluator/test_layer1.py`
8. `tests/unit/evaluator/test_layer3.py`
9. `tests/unit/evaluator/test_sprint_contract.py`
10. `tests/unit/evaluator/test_evaluator.py`
11. `tests/e2e/test_mock_pipeline.py`

## Required Runtime Probes

Wave 4B cleared only after artifacts named probes for:

1. Actionability rewards decision-informing specificity and penalizes recommendation creep.
2. Differentiated analyst prompts still emit the shared `ScoredClaim` envelope.
3. Sprint-contract generation exposes all 10 dimensions and contradiction handling still fits the current boolean seam without a 10-claim cap.
4. Task-generation tool guidance stays inside the registered tool set and template enrichment stays inside the current envelope.
5. Thin or absent verification snippets are surfaced as `UNVERIFIABLE`-style evidence gaps rather than false `NOT_SUPPORTED`.

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WAVE-4B-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4B-SETUP.md) — frozen Wave 4B scope boundary and denylist
- [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md) — accepted D-2 scoring contract
- [WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md) — accepted prompt-quality contracts for the Wave 4B slice
- [WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md) — accepted sprint-contract and contradiction-boundary contract
- [WAVE-4-TEMPLATE-ROUTING-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md) — accepted routing and template-envelope contract
- [WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md) — accepted evaluator-verification boundary
- [candidate-65a612d-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md) — consensus review packet clearing the Wave 4B lane
- [candidate-65a612d-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md) — immutable cleared-state proof for the current last-cleared code commit

## Residual Follow-Ups

- `W2B-R01`: parse-invalid sprint-contract JSON now fails explicitly, but parseable under-specified JSON can still return empty Wave 2B enforcement fields.

## Controller Lease Events

- `2026-04-12T02:01:57-04:00` — controller takeover by `codex-gpt-5.4-xhigh-main-controller`.
  Reason: `lease_heartbeat_at` from the predecessor was older than 30 minutes (`2026-04-12T01:24:01-04:00`), so the takeover rule in the control plane fired before any new state mutation.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, `active_wave`/`active_state` still reconciled to `wave-2b` / `cleared`, `last_cleared_code_commit` was still `2cdbfec`, and `WAVE-3A-SEAM-FREEZE.md` was still absent.
- `2026-04-12T02:05:36-04:00` — seam-freeze checkpoint `65074ca` was reconciled into active Wave 3 setup state.
  Result: `WAVE-3-SETUP.md` became the active wave setup doc, `active_wave` advanced to `wave-3`, and the next action became opening the clean Wave 3 implementation lane from `2cdbfec`.
- `2026-04-12T02:31:29-04:00` — Wave 3 candidate `4819527` was reviewed and cleared.
  Result: Wave 3 advanced from `setup` to `cleared`, `4819527` became the last cleared code commit, and the next required gate became `WAVE-3B-SETUP.md`.
- `2026-04-12T02:50:02-04:00` — Wave 3B setup checkpoint was committed.
  Result: `WAVE-3B-SETUP.md` became the active setup doc, `active_wave` advanced to `wave-3b`, and the next action became opening the clean Wave 3B implementation lane from `4819527`.
- `2026-04-12T03:22:30-04:00` — controller lease takeover by `codex-gpt-5.4-xhigh-main-controller`.
  Reason: the previous lease heartbeat (`2026-04-12T02:50:02-04:00`) aged past the 30-minute limit before the next state mutation, so `controller_epoch` was incremented before reconciling Wave 3B clearance into Wave 4 setup.
  Repo-state verification completed before takeover: the main workspace was still on `codex/remediation-program`, the clean Wave 3B code lane had already produced cleared candidate `5cc9585`, the Wave 3B review packet set existed on disk, and the dirty main workspace still required controller/docs-only quarantine.
- `2026-04-12T03:43:19-04:00` — Wave 4 docs checkpoint added sprint-contract / rubric research.
  Result: `WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md` now records the `C-5` and `C-7` contracts, keeps persisted contradiction-taxonomy expansion out of Wave 4B, and advances the next required memo to `WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`.
- `2026-04-12T03:50:29-04:00` — Wave 4 docs checkpoint added template / routing research.
  Result: `WAVE-4-TEMPLATE-ROUTING-RESEARCH.md` now records the `C-6`, `C-8`, `C-10`, and `C-14` contracts, keeps dual-axis tiebreaking plus dynamic lens selection out of Wave 4B, and advances the next required memo to `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`.
- `2026-04-12T03:55:07-04:00` — Wave 4 docs checkpoint added evaluator-verification research.
  Result: `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md` now records the `C-11` and `C-15` boundary, the required Wave 4 memo set is complete, and the next required action becomes opening the clean Wave 4 polish lane from `5cc9585`.
- `2026-04-12T04:07:21-04:00` — Wave 4 candidate `6406e46` was reviewed and cleared.
  Result: Wave 4 advanced from `setup` to `cleared`, `6406e46` became the last cleared code commit, and the next required gate became `WAVE-4B-SETUP.md`.
- `2026-04-12T04:14:49-04:00` — Wave 4B setup checkpoint was committed.
  Result: `WAVE-4B-SETUP.md` became the active setup doc, `active_wave` advanced to `wave-4b`, and the next action became opening the clean Wave 4B implementation lane from `6406e46`.
- `2026-04-12T04:35:17-04:00` — Wave 4B candidate `65a612d` was reviewed and cleared.
  Result: Wave 4B advanced from `setup` to `cleared`, `65a612d` became the last cleared code commit, and a hard stop activated because no next-wave authority artifact is yet committed.
