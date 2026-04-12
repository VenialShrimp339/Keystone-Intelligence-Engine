# Active Handoff

## Current Truth

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B is cleared at `2cdbfec`.
- Wave 3A seam freeze is committed in `65074ca`.
- Wave 3 is cleared at `4819527`.
- Wave 3B is now cleared at `5cc9585`.
- Wave 4 is now the active wave in `setup` state.
- The main workspace remains controller/docs only.
- `WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md` now records the C-1 / C-2 / C-3 / C-4 / C-9 / C-12 / C-13 design contracts.
- `WAVE-4-POLISH-SPECS.md` now freezes the exact `E-2` / `E-4` / `E-5` polish slice.
- `WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md` now records the `C-5` / `C-7` design contracts and explicitly re-scopes persisted contradiction-taxonomy capability out of Wave 4B.
- The next required step is the next missing Wave 4 research memo, not a code lane.
- Wave 4B content implementation is not active, and Wave 5 calibration remains gated off.
- The controller is expected to continue **autonomously across checkpoints**. Docs-only checkpoints are not pause points.

## Authoritative Order

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [candidate-5cc9585-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md)
4. [candidate-5cc9585-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md)
5. [WAVE-4-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SETUP.md)
6. [WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md)
7. [WAVE-4-POLISH-SPECS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-POLISH-SPECS.md)
8. [WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md)
9. [WAVE-4-4B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-4B-PREWORK.md)
10. [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md)
11. [WAVE-3A-SEAM-FREEZE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3A-SEAM-FREEZE.md)
12. [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
13. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
14. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)

## Active State Tuple

- `active_wave`: `wave-4`
- `active_state`: `setup`
- `execution_baseline_commit`: `5cc9585`
- `review_target_commit`: `not yet created; any future Wave 4 polish candidate roots from 5cc9585`
- `docs_reconcile_commit`: `HEAD`
- `next_recovery_checkout`: `5cc9585`

## Open Blockers

- None.

## Latest Review Packets

- [candidate-5cc9585-adversarial-review.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-adversarial-review.md)
- [candidate-5cc9585-second-opinion.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-second-opinion.md)
- [candidate-5cc9585-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md)
- [candidate-5cc9585-clearance.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md)

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Treat `5cc9585` as the last cleared code commit for every future implementation lane.
3. Use [WAVE-4-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SETUP.md) as the binding Wave 4 scope boundary.
4. Author [WAVE-4-TEMPLATE-ROUTING-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md) next in the main workspace.
5. Keep the Wave 4 polish code lane unopened until the remaining Wave 4 memos exist and the file manifest stays narrow.
6. Do **not** start Wave 4B implementation until the required Wave 4 memos exist and the targeted seams are stable.
7. Use [EXECUTION-TODO.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/EXECUTION-TODO.md) as the operational checklist after reading this handoff.
8. After each checkpoint, re-read the control plane and continue automatically unless a hard stop condition is met.

## Exact Recovery Command

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
sed -n '1,240p' audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml
sed -n '1,260p' audit/remediation/control-plane/ACTIVE-HANDOFF.md
sed -n '1,260p' audit/remediation/WAVE-4-SETUP.md
```

## Allowed Write Set

### Active docs-only Wave 4 scope

- `audit/remediation/WAVE-4-SETUP.md`
- `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
- `audit/remediation/WAVE-4-POLISH-SPECS.md`
- `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
- `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
- `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/EXECUTION-TODO.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `CURRENT-STATE.md`
- `audit/remediation/runs/wave-4/candidate-TEMPLATE-file-manifest.md`

### Future Wave 4 polish code lane

- `src/keystone/models/evaluation.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `samples/auto_body_chain/RESEARCH.md.json`
- `samples/auto_body_chain/research-tasks.json`
- `samples/luminar_lidar/RESEARCH.md.json`
- `samples/luminar_lidar/research-tasks.json`
- `samples/specialty_chemicals_ma/RESEARCH.md.json`
- `samples/specialty_chemicals_ma/research-tasks.json`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/test_schemas.py`
- `tests/e2e/test_mock_pipeline.py`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Required Test Matrix

For the current docs-only setup state: none.

Before any Wave 4 polish candidate clears, run at minimum:

1. `tests/unit/test_schemas.py`
2. `tests/unit/pipeline/test_markdown_renderer.py`
3. `tests/e2e/test_mock_pipeline.py`

## Required Runtime Probes

Before any Wave 4 polish candidate clears, the artifact set must name probes for:

1. Completeness is classified as `EXPERT_CHECKABLE`, not `MACHINE_CHECKABLE`.
2. Client markdown no longer emits the internal Section 7 metrics block.
3. Client-facing references are rendered without raw `CIT-xxx` engineering IDs.
4. Sample engagements validate against the live production schema with legacy fields removed.

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WAVE-4-4B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-4B-PREWORK.md) — accepted Wave 4 / 4B planning decomposition
- [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md) — accepted D-2 scoring contract for later Wave 4B actionability work
- [WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md) — implementation-ready prompt-quality contract for C-1 / C-2 / C-3 / C-4 / C-9 / C-12 / C-13
- [WAVE-4-POLISH-SPECS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-POLISH-SPECS.md) — exact Wave 4 polish contract for `E-2`, `E-4`, and `E-5`
- [WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md) — implementation-ready sprint-contract contract for `C-5` plus an in-bounds contradiction taxonomy for `C-7`
- [CONTENT-SYNTHESIS-v2.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md) — source of the Wave 4 low-risk polish items `E-2`, `E-4`, and `E-5`
- [PLANNING-ADDENDUM.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/round-3/PLANNING-ADDENDUM.md) — planning overlay that keeps Bucket C work in Wave 4 research rather than sneaking it into code early

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
