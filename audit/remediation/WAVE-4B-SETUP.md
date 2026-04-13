# Wave 4B Setup

*Date: 2026-04-12 | Status: active Wave 4B setup checkpoint | main workspace stays controller/docs only; any code must run in a clean worktree rooted at cleared Wave 4 baseline `6406e46`*

---

## What This File Is For

This is the active setup doc for Wave 4B.

Use it only after reading:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/runs/wave-4/candidate-6406e46-clearance.md`
4. `audit/remediation/runs/wave-4/candidate-6406e46-review-synthesis.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `audit/remediation/WAVE-4-4B-PREWORK.md`
7. `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
8. `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
9. `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
10. `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
11. `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
12. `graphify-out/GRAPH_REPORT.md`

This file turns cleared Wave 4 commit `6406e46` into the Wave 4B content-implementation runway.
It does not authorize deferred capability work, and it does not authorize Wave 5 calibration.

## Wave Activation

- Wave 4 cleared candidate: `6406e46`
- Wave 4B execution baseline: `6406e46`
- Controller branch: `codex/remediation-program`
- Planned implementation branch: `codex/remediation-wave-4b`
- Planned implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`
- Main workspace policy: controller/docs only

## Current-Code Anchors

Wave 4B setup is based on cleared `6406e46`, which now has these relevant properties:

1. The post-3B outline/render path is stable and client markdown no longer leaks internal quality blocks or raw citation-engineering IDs.
2. The Completeness eval-type metadata fix is already landed and should not be reopened as part of Wave 4B.
3. The accepted D-2 actionability contract exists as a Wave 4 sidecar and should now be implemented only at the evaluator-content seam.
4. Sprint-contract generation, task generation, template registry, and intent-clarifier seams are real and available for in-bounds content work.
5. The evaluator-verification memo explicitly keeps `C-15` in-bounds and pushes true claim-support verification (`C-11`) out as a later capability lane.

## Binding Scope In

Wave 4B includes only the content-layer and existing-seam implementation slices approved by the Wave 4 memo set:

1. `D-2` actionability reset at the evaluator prompt/content seam:
   - decision-informing specificity
   - lever / implication / tradeoff / threshold framing
   - recommendation-creep penalties
2. Core prompt-quality slice:
   - `C-1`, `C-2`, `C-3`, `C-4`, `C-9`, `C-12`, `C-13`
   - only where the change stays inside existing prompt consumers and shared output envelopes
3. Sprint-contract / contradiction slice:
   - `C-5`
   - `C-7` only for tighter contradiction criteria plus removal of the 10-claim cap while preserving the current boolean consistency seam
4. Template / routing slice:
   - `C-8` task-generation tool-selection heuristics inside the registered tool set
   - `C-14` archetype enrichment inside the current template envelope
5. Evaluator verification slice:
   - `C-15` snippet-sufficiency guardrails inside Layer 1 / evaluator reporting without source fetching
6. Existing tests and fixtures that make those content seams load-bearing.

## Binding Scope Out

The following remain explicitly out of scope for Wave 4B:

1. `C-6` dual-axis classifier persistence or tiebreaking as a load-bearing runtime capability
2. `C-10` dynamic lens registry or selector
3. `C-11` true claim-support verification beyond citation existence
4. Any source-fetching verifier or new evaluator stage
5. `C-14` low-fit custom-template generation outside the current template envelope
6. Any persisted discrepancy / framing-disagreement taxonomy beyond the current boolean contradiction seam
7. Method-specific analyst output schemas or any other schema-expanding deliberation capability
8. Wave 5 calibration, threshold tuning, profile-weight finalization, or broad scoring-policy changes
9. Broad repo cleanup or main-workspace dirty-file cleanup

## Wave 4B Control Rule

Wave 4B freezes the authority model as follows:

1. The main workspace remains controller/docs only.
2. Any Wave 4B code change must run in a clean worktree rooted at `6406e46`.
3. The implementation lane must stay inside the existing prompt / evaluator / template seams enumerated below.
4. If any approved slice requires a new persisted field, a new runtime stage, dynamic registry infrastructure, or live source fetching, stop and return to the control plane.
5. Do not bundle Wave 5 calibration or deferred capability work under the label of "content cleanup."

## Approved Slice Map

### Slice A: D-2 Actionability

In scope:

- rewrite `actionability.md` around decision-informing specificity
- align Layer 3 tests/fixtures with the accepted D-2 contract

Out of scope:

- calibration changes beyond what is needed to make the new contract load-bearing
- recommendation or output-format redesign outside the evaluator seam

### Slice B: Core Prompt Quality

In scope:

- differentiated analyst prompts that still emit shared `ScoredClaim`
- shallow-synthesis quality bar rewrite
- deep-prompt materiality rewrite
- current fixed-lens prompt utilization guidance
- injection-safe delimiter text on the highest-risk prompt surfaces
- judge-selection criteria and valid-value guard
- intent-clarifier Step 4 schema recovery

Out of scope:

- typed method-specific analyst payloads
- dynamic lens selection or new prompt registries

Retrospective clarification for historical `65a612d` interpretation: the Slice B line `intent-clarifier Step 4 schema recovery` authorizes only seam-local preservation of Step 4 within `src/keystone/specification/prompts/intent_clarification.md` and `src/keystone/specification/intent_clarifier.py`. It does not retroactively widen the historical Wave 4B write surface to `src/keystone/specification/spec_engine.py`, `src/keystone/specification/task_generator.py`, or `src/keystone/models/research.py` for downstream structural propagation. See `audit/remediation/runs/wave-4b/candidate-65a612d-c13-contract-addendum.md`.

### Slice C: Sprint Contract / Contradiction

In scope:

- expand sprint-contract generation guidance to all 10 dimensions
- add section-local emphasis guidance inside the current sprint-contract seam
- tighten contradiction criteria
- remove the 10-claim cap while preserving the current boolean `consistency_passed` seam

Out of scope:

- persisted discrepancy or framing-disagreement classes
- contradiction graphs, chunked contradiction search, or auto confidence downgrades

### Slice D: Template / Routing

In scope:

- task-generation tool-selection heuristics inside the registered tool set
- archetype enrichment with frameworks, output expectations, and failure-mode language inside the current template envelope

Out of scope:

- dual-axis classification rollout
- dynamic lens registry / selector
- low-fit custom-template generation outside the current envelope

### Slice E: Evaluator Verification Guardrails

In scope:

- Layer 1 snippet-sufficiency policy
- `UNVERIFIABLE` style handling for thin or absent evidence text if that stays inside the current evaluator/result seam

Out of scope:

- claim-support verification beyond citation existence
- live source fetching
- new verifier stages or stage-boundary reshaping

## Initial Allowed Write Set

### Docs-only setup lane

- `audit/remediation/WAVE-4B-SETUP.md`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/EXECUTION-TODO.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `CURRENT-STATE.md`
- `audit/remediation/templates/run-packets/wave-4b/candidate-TEMPLATE-file-manifest.md`

### Future Wave 4B implementation lane

- `src/keystone/evaluator/prompts/actionability.md`
- `src/keystone/evaluator/prompts/sprint_contract_generation.md`
- `src/keystone/evaluator/prompts/fact_decomposition.md`
- `src/keystone/evaluator/layer1_deterministic.py`
- `src/keystone/evaluator/layer3_rubric.py`
- `src/keystone/evaluator/sprint_contract.py`
- `src/keystone/evaluator/evaluator.py`
- `src/keystone/models/evaluation.py`
- `src/keystone/deliberation/analyst.py`
- `src/keystone/deliberation/aggregator.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/specification/prompts/intent_clarification.md`
- `src/keystone/specification/prompts/decompose_financial_lens.md`
- `src/keystone/specification/prompts/decompose_market_lens.md`
- `src/keystone/specification/prompts/decompose_operational_lens.md`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/intent_clarifier.py`
- `src/keystone/specification/template_registry.py`
- `tests/unit/deliberation/test_analyst.py`
- `tests/unit/deliberation/test_aggregator.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/specification/test_intent_clarifier.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/specification/test_template_registry.py`
- `tests/unit/evaluator/test_layer1.py`
- `tests/unit/evaluator/test_layer3.py`
- `tests/unit/evaluator/test_sprint_contract.py`
- `tests/unit/evaluator/test_evaluator.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/fixtures/evaluator/**`

### Generated collateral expected with code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Initial Denylist

Do not treat these as in-scope for Wave 4B unless a later controller checkpoint explicitly widens scope:

- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/decomposer.py`
- `src/keystone/evaluator/layer2_citation_gate.py`
- future claim-support verifier modules
- future lens-registry / selector surfaces
- any new template-generator or custom-template-expansion surface
- Wave 5 setup or calibration docs
- immutable historical review packets
- unrelated main-workspace dirty files outside the Wave 4B docs lane or the future implementation lane

## Required Test Matrix

At minimum, a future Wave 4B candidate must run the real enforcing seams behind these suites:

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

The future Wave 4B candidate artifact set must name probes for these invariants:

1. Actionability rewards decision-informing specificity and penalizes recommendation creep.
2. Differentiated analyst prompts still emit the shared `ScoredClaim` envelope.
3. Sprint-contract generation exposes all 10 dimensions and contradiction handling still fits the current boolean seam without a 10-claim cap.
4. Task-generation tool guidance stays inside the registered tool set and template enrichment stays inside the current envelope.
5. Thin or absent verification snippets are surfaced as `UNVERIFIABLE`-style evidence gaps rather than false `NOT_SUPPORTED`.

## Worktree Bootstrap

When the setup checkpoint is committed and the Wave 4B code lane is ready, begin from the cleared baseline:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
git worktree add -b codex/remediation-wave-4b ../Keystone-Intelligence-Engine-wave-4b 6406e46
```

Then work from:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b
```

If the clean worktree lacks its own virtual environment, reuse the shared repository venv by absolute path while keeping the workdir on the clean lane.

After any code-file changes in the worktree, rebuild graphify before ending the implementation session:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If default `python3` cannot import `graphify`, use the recorded fallback interpreter from `audit/remediation/control-plane/RECOVERY-RULES.md`.

## Candidate Artifact Requirements

Wave 4B candidate artifacts must live under `audit/remediation/runs/wave-4b/` and include:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Use `audit/remediation/templates/run-packets/wave-4b/candidate-TEMPLATE-file-manifest.md` as the starting scaffold if it exists; otherwise create it there before the first Wave 4B candidate is reviewed.

## Carried Follow-Up

- `W2B-R01` remains visible: parseable but under-specified sprint-contract JSON can still produce empty enforcement fields. Do not silently lose this follow-up while executing Wave 4B.

## Reopen / Hard-Stop Triggers

Stop and return to the control plane if any of these happen:

1. A proposed Wave 4B change widens into any deferred `new capability` item (`C-6`, `C-10`, `C-11`, deferred `C-14`, or deferred `C-7`).
2. The implementation needs a new persisted field, runtime stage, registry, or live source-fetch path that is not already inside the approved seams above.
3. The future Wave 4B code lane needs to widen beyond the frozen write surface without a committed controller update.
4. A review finds a blocker that cannot be resolved inside the approved Wave 4B slice.
