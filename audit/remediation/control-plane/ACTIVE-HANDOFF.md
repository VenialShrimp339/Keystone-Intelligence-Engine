# Active Handoff

## Current Truth

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B checkpoint candidate `4ff7e90` is blocked.
- The current active task is **Wave 2B blocked-snapshot remediation**, not “start Wave 2B.”
- The main workspace contains dirty Wave 2B blocker-fix work, but that work is only recovery evidence until it is replayed in a clean worktree and committed.
- The authoritative bootstrap plan is [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md).

## Authoritative Order

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)
3. [WAVE-2B-ADVERSARIAL-REVIEW.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md)
4. [WAVE-2B-SECOND-OPINION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SECOND-OPINION.md)
5. [candidate-4ff7e90-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-review-synthesis.md)
6. [WAVE-2B-BLOCKER-REMEDIATION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md)
7. [candidate-4ff7e90-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md)
8. [CURRENT-STATE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CURRENT-STATE.md)
9. [WORKSTREAM-STATUS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WORKSTREAM-STATUS.md)
10. [WAVE-2B-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SETUP.md)

## Active State Tuple

- `active_wave`: `wave-2b`
- `active_state`: `blocked`
- `execution_baseline_commit`: `16e0bc7`
- `review_target_commit`: `4ff7e90`
- `docs_reconcile_commit`: `HEAD`
- `next_recovery_checkout`: `4ff7e90`

## Open Blockers

- `W2B-B01`: LIGHT coverage can fail open on failed evaluated tasks.
- `W2B-B02`: task `priority` / `importance` derive from LLM list order instead of Step-5 scores.
- `W2B-B03`: the effective evaluator profile is not carried through `ResearchSpec` and into `Evaluator`.
- `W2B-B04`: HITL Gate 1 / Gate 2 decisions are not truly policy-owned through `ProfileExecutionPolicy`.

## Latest Review Packets

- [WAVE-2B-ADVERSARIAL-REVIEW.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md)
- [WAVE-2B-SECOND-OPINION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-SECOND-OPINION.md)
- [candidate-4ff7e90-review-synthesis.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-review-synthesis.md)
- [candidate-4ff7e90-blocked-checkpoint.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-blocked-checkpoint.md)

## Exact Next Action

1. Stay on `codex/remediation-program` in the main workspace.
2. Verify the recovery patch checksum.
3. Create a clean Wave 2B worktree rooted at `4ff7e90`.
4. Replay the recovery patch into that worktree with `--3way`.
5. Compare the replayed result against the blocker ledger and file manifest before staging anything.
6. Run the focused Wave 2B proof matrix.
7. Create the next Wave 2B candidate commit.
8. Run adversarial review, second opinion, and controller clearance against `16e0bc7..<new_candidate>`.

## Exact Recovery Command

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git checkout codex/remediation-program
shasum -a 256 audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch
git worktree add -b codex/remediation-wave-2b ../Keystone-Intelligence-Engine-wave-2b 4ff7e90
cd ../Keystone-Intelligence-Engine-wave-2b
git apply --3way /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch
```

Expected checksum:

```text
f9cf1925c31d5836024bfdf32fd5a5ee8cbfe8d4b1e46dc0983630b128b36234
```

## Allowed Write Set

Only files from [candidate-4ff7e90-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md) may be touched until the controller amends the manifest.

## Required Test Matrix

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

## Required Runtime Probes

- Probe that a LIGHT task with failed L4 output still halts coverage.
- Probe that the higher Step-5-scored branch becomes `PRIMARY` even if listed second.
- Probe that `Evaluator` receives the effective evaluation profile from `ResearchSpec`, not a local remap.
- Probe that Gate 1 and Gate 2 consult `ProfileExecutionPolicy` rather than leaf-level `PipelineProfile.LIGHT` checks.
- Probe that malformed sprint-contract output does not silently degrade to a bare contract.
- Probe that emitted rubric weights reflect `dimension_emphasis`.

## Docs Explicitly Ignored As Stale

- [CLAUDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/CLAUDE.md) below its remediation banner
- [EXECUTION-GUIDE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/EXECUTION-GUIDE.md) below its tombstone banner
- [BUILD-PROCESS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/BUILD-PROCESS.md) below its tombstone banner

## Active Sidecars

- [WAVE-3-3B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-3B-PREWORK.md) — advisory only
- [WAVE-4-4B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-4B-PREWORK.md) — advisory only
- [WAVE-4-D2-ACTIONABILITY-RESEARCH.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md) — advisory only
