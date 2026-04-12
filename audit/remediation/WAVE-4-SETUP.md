# Wave 4 Setup

*Date: 2026-04-12 | Status: active Wave 4 setup checkpoint | research stays in the main workspace docs lane; any code must run in a clean worktree*

---

## What This File Is For

This is the active setup doc for Wave 4.

Use it only after reading:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md`
4. `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `audit/remediation/WAVE-4-4B-PREWORK.md`
7. `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
8. `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
9. `graphify-out/GRAPH_REPORT.md`

This file turns cleared Wave 3B commit `5cc9585` into the Wave 4 research-and-polish runway.
It does not authorize Wave 4B content implementation, and it does not authorize Wave 5 calibration work.

## Wave Activation

- Wave 3B cleared candidate: `5cc9585`
- Wave 4 execution baseline: `5cc9585`
- Controller branch: `codex/remediation-program`
- Planned implementation branch: `codex/remediation-wave-4`
- Planned implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4`
- Main workspace policy: controller/docs only

## Current-Code Anchors

Wave 4 setup is based on the cleared `5cc9585` runtime, which now has these relevant properties:

1. `StructuredOutline` is real and load-bearing on the runtime path.
2. `MarkdownRenderer` already consumes the outline surface rather than pre-L2 finding structures.
3. The orchestrator is the only authoritative cross-task round controller.
4. Round-state persistence and continuity are real under `memory/rounds/`.
5. The accepted D-2 actionability memo already exists as a Wave 4 sidecar.
6. The remaining low-risk polish items are still unapplied:
   - `E-2`: Completeness classification fix
   - `E-4`: renderer zero-cost client-output cleanup
   - `E-5`: sample-schema sync

## Wave 4 Delivery Lanes

Wave 4 has two explicit lanes:

1. A docs-only research/design lane in the main workspace.
2. A narrow low-risk polish code lane that can open later only in a clean worktree rooted at `5cc9585`.

The docs lane comes first.
Wave 4B content implementation remains a separate later gate.

## Binding Scope In

Wave 4 includes only the post-3B work approved by `AUTONOMOUS-REMEDIATION-PLAN-v4.md`, `WAVE-4-4B-PREWORK.md`, and `FINAL-DECISIONS-v2.1.md`:

1. Docs-only research memos for:
   - core L1 / L1.5 prompt quality
   - sprint-contract / rubric content
   - template / routing content
   - evaluator-verification design
2. Carry-forward of the accepted D-2 actionability memo as the binding actionability sidecar.
3. Exact fix specs for Wave 4 polish items `E-2`, `E-4`, and `E-5`.
4. Run-folder scaffolding and candidate-manifest preparation for future Wave 4 polish candidates.
5. A later clean-worktree Wave 4 polish code lane limited to:
   - Completeness classification
   - client-render cleanup
   - sample-schema sync

## Binding Scope Out

The following remain explicitly out of scope for Wave 4:

1. Wave 4B implementation of prompt, rubric, template, or actionability memo content
2. Wave 5 calibration, scoring, threshold, or profile-weight finalization
3. Broad prompt-library rewrites in production code before the corresponding Wave 4 memo exists
4. Evaluator or routing capability expansion that qualifies as a `new capability` rather than content or seam-local code
5. Broad repo cleanup or main-workspace dirty-file cleanup
6. Reopening cleared Wave 3 or Wave 3B code without a true regression

## Wave 4 Control Rule

Wave 4 freezes the authority model as follows:

1. The main workspace remains controller/docs only.
2. Research/design sidecars run only in the main workspace.
3. Any code change, even low-risk polish, must run in a clean worktree rooted at `5cc9585`.
4. No Wave 4B content slice may start until the corresponding Wave 4 memo exists and the targeted seam is stable.
5. Every Wave 4 memo must declare whether the result is:
   - `content-only`
   - `existing-seam code`
   - `new capability`
6. If a memo implies `new capability`, it must be re-scoped out of Wave 4B and into a later capability wave.

## Execution Order

Wave 4 should be executed in this order unless a later controller checkpoint records a justified deviation:

1. Reconcile the Wave 3B cleared-state packet and freeze this Wave 4 setup doc.
2. Write the next missing Wave 4 research memo in the main workspace.
3. Write the exact Wave 4 polish fix specs for `E-2`, `E-4`, and `E-5`.
4. Finish the remaining Wave 4 memos in the main workspace.
5. Only then open a clean Wave 4 polish worktree from `5cc9585` if a narrow code slice is ready.

Rationale:

- Wave 4B content implementation must not outrun the research evidence.
- The low-risk polish slice is intentionally narrow and should not absorb content rewrites.
- Keeping the code lane closed until the docs lane is frozen preserves the controller/docs-only main workspace rule.

## Initial Allowed Write Set

### Docs-only setup / research lane

- `audit/remediation/WAVE-4-SETUP.md`
- `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
- `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
- `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
- `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
- `audit/remediation/WAVE-4-POLISH-SPECS.md`
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

### Generated Collateral Expected With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Initial Denylist

Do not treat these as in-scope for Wave 4 unless a later controller checkpoint explicitly widens scope:

- `src/keystone/evaluator/prompts/**`
- `src/keystone/specification/prompts/**`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/template_registry.py`
- Wave 4B or Wave 5 setup docs
- immutable historical review packets
- unrelated main-workspace dirty files outside the Wave 4 docs lane or the future narrow polish lane

## Required Structural Decisions For The Docs Lane

These are now frozen for Wave 4 setup work:

1. `WAVE-4-D2-ACTIONABILITY-RESEARCH.md` is already the accepted actionability sidecar.
2. Every remaining Wave 4 memo must include:
   - the exact observed problem and the source artifact that proves it
   - the accepted architectural boundary it must respect
   - the runtime consumer of the proposed change
   - at least one negative example
   - at least one regression test idea
   - a note on whether the change depends on Wave 2B, 3, or 3B having landed
3. Any output missing those elements is planning-only brainstorming, not implementation-ready design.
4. Wave 4 polish remains limited to `E-2`, `E-4`, and `E-5`.

## Required Docs Outputs

Before any Wave 4 code candidate may start, the main workspace must contain:

1. `WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
2. `WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
3. `WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
4. `WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
5. `WAVE-4-POLISH-SPECS.md`

The D-2 actionability memo already exists and does not need to be re-authored unless a later controller checkpoint says otherwise.

## Required Test Matrix

At minimum, a future Wave 4 polish candidate must run the real enforcing seams behind these suites:

1. `tests/unit/test_schemas.py`
2. `tests/unit/pipeline/test_markdown_renderer.py`
3. `tests/e2e/test_mock_pipeline.py`

## Required Runtime Probes

The future Wave 4 polish candidate artifact set must name probes for these invariants:

1. Completeness is classified as `EXPERT_CHECKABLE`, not `MACHINE_CHECKABLE`.
2. Client markdown no longer emits the internal Section 7 metrics block.
3. Client-facing references no longer expose raw `CIT-xxx` engineering IDs.
4. Sample engagements validate against the live production schema with the stale legacy fields removed.

## Worktree Bootstrap

When the docs lane is complete and the low-risk Wave 4 polish lane is ready, begin from the cleared baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/remediation-wave-4 ../Keystone-Intelligence-Engine-wave-4 5cc9585
```

Then work from:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4
```

If the clean worktree lacks its own virtual environment, reuse the shared repository venv by absolute path while keeping the workdir on the clean lane.

After any code-file changes in the worktree, rebuild graphify before ending the implementation session:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If default `python3` cannot import `graphify`, use the recorded fallback interpreter from `audit/remediation/control-plane/RECOVERY-RULES.md`.

## Candidate Artifact Requirements

Wave 4 candidate artifacts must live under `audit/remediation/runs/wave-4/` and include:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Use `candidate-TEMPLATE-file-manifest.md` in the run folder as the starting scaffold.

## Carried Follow-Up

- `W2B-R01` remains visible: parseable but under-specified sprint-contract JSON can still produce empty enforcement fields. Do not silently lose this follow-up while executing Wave 4.

## Reopen / Hard-Stop Triggers

Stop and return to the control plane if any of these happen:

1. A proposed Wave 4 change widens into Wave 4B content implementation or Wave 5 calibration.
2. The future Wave 4 polish lane needs to widen beyond the frozen `E-2` / `E-4` / `E-5` file surface without a committed controller update.
3. A Wave 4 memo implies `new capability` rather than content or seam-local code.
4. The clean Wave 4 worktree cannot be opened from `5cc9585` without colliding with unrelated state.
5. The controller cannot reconcile the dirty main workspace without risking unrelated user changes.
