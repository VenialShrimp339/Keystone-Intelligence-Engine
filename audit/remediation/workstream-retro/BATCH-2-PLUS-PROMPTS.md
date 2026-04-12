# Batch 2+ Prompts

*Date: 2026-04-12 | Scope: exact copy-paste prompts for Batches 2 through 7 of the retrospective audit program*

---

## Shared Launch Rule

Do not launch any prompt in this file unless all Batch 1 slices are already `CLEARED`.

Pinned context for all prompts:

- pre-planning docs anchor commit: `2e6d780`
- last cleared-state docs checkpoint: `91f97c2`
- last cleared code commit: `65a612d`
- code lineage:
  `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- controller/docs lineage:
  `35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2 -> 2e6d780`

## W2B-1 Prompt

```md
You are running slice `W2B-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W2B-1-wave-2b-lineage-and-closure-audit.md`

Rules:
- Review only. Do not fix code or rewrite historical packets.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review committed snapshots only. Do not trust dirty `HEAD` as code truth.

Pinned commits:
- Wave 2A cleared baseline: `16e0bc7`
- Blocked parent candidate: `4ff7e90`
- Cleared Wave 2B candidate: `2cdbfec`

Read first, in order:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
5. `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
6. `audit/remediation/WAVE-2B-SETUP.md`
7. `audit/remediation/runs/wave-2b/candidate-4ff7e90-review-synthesis.md`
8. `audit/remediation/runs/wave-2b/candidate-4ff7e90-blocked-checkpoint.md`
9. `audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md`
10. `audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch`
11. `audit/remediation/runs/wave-2b/candidate-2cdbfec-implementation.md`
12. `audit/remediation/runs/wave-2b/candidate-2cdbfec-file-manifest.md`
13. `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
14. `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
15. `audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md`
16. `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`

Review scope:
- blocked-parent lineage: `16e0bc7..4ff7e90` and the blocked packet set
- recovery delta: `4ff7e90..2cdbfec`
- clearance scope: full `16e0bc7..2cdbfec`

Your job is to answer two separate questions:
1. Was the blocked-parent and recovery lineage documented and constrained correctly?
2. Did `2cdbfec` actually close the Wave 2B blocker set on the real runtime path?

Required sub-verdicts:
- `blocked-parent lineage`
- `cleared runtime closure`

Required checks:
- blocker mapping `W2B-B01` through `W2B-B04`
- residual-risk handling for `W2B-R01`
- parent-delta boundary discipline
- recovery-patch and packet coherence
- full-baseline clearance truth vs local parent-delta truth

Output requirements:
- Distinguish packet/lineage defects from runtime-closure defects.
- End with:
  - sub-verdict 1
  - sub-verdict 2
  - top-line `BLOCKED | CLEARED | CONTINGENT`
- If the top-line verdict is not `CLEARED`, state exactly which later waves become untrustworthy.
```

## W3A-1 Prompt

```md
You are running slice `W3A-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W3A-1-wave-3a-seam-and-setup-audit.md`

Rules:
- Review only. Do not change seam docs or setup docs.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
5. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
6. `audit/remediation/WAVE-3-SETUP.md`
7. `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md`
8. `audit/remediation/runs/wave-3/candidate-4819527-clearance.md`
9. `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md`

Your job is to audit the Wave 3A seam-freeze and Wave 3 setup contracts as prerequisites for all later wave reviews.

Required checks:
1. seam ownership clarity
2. Wave 3 scope-in and scope-out clarity
3. Wave 3 vs Wave 3B boundary discipline
4. required test and runtime-probe adequacy
5. reopen and hard-stop trigger adequacy
6. whether later cleared packets appear to rely on a seam or scope that the docs did not actually freeze

Output requirements:
- Separate findings into:
  - seam-freeze defects
  - setup-contract defects
  - later-wave dependency risk
- End with one top-line `BLOCKED | CLEARED | CONTINGENT` verdict and a short statement on whether `W3-1` may launch.
```

## W4D-1 Prompt

```md
You are running slice `W4D-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W4D-1-wave-4-memo-boundary-audit.md`

Rules:
- Review only. Do not rewrite research memos or setup docs.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-4-SETUP.md`
5. `audit/remediation/WAVE-4-POLISH-SPECS.md`
6. `audit/remediation/WAVE-4B-SETUP.md`
7. `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
8. `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
9. `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
10. `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
11. `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`

Your job is to audit the Wave 4 memo boundary system itself and verify that `WAVE-4B-SETUP.md` transcribed it correctly.

Required per-memo checks:
- problem statement clarity
- accepted architectural boundary
- classification:
  - `content-only`
  - `existing-seam code`
  - `new capability`
- dependency note correctness
- regression-test and negative-example sufficiency

Required setup-transcription checks:
- approved slice map
- write set
- denylist
- runtime probe bundle
- explicit deferral of `C-6`, `C-10`, `C-11`, deferred `C-14`, and deferred `C-7`

Required sub-verdicts:
- `D-2 memo`
- `core prompt memo`
- `sprint-contract / contradiction memo`
- `template / routing memo`
- `evaluator verification memo`
- `Wave 4B setup transcription`

Output requirements:
- Report memo defects separately from setup-transcription defects.
- End with all six sub-verdicts plus one top-line `BLOCKED | CLEARED | CONTINGENT`.
- State explicitly whether `W4B-1` and `W4B-2` may launch.
```

## W3-1 Prompt

```md
You are running slice `W3-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W3-1-wave-3-runtime-audit.md`

Rules:
- Review only. Do not fix code.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review only the committed snapshot for `4819527` in an isolated worktree or detached checkout. Do not trust dirty `HEAD` as code truth.

Pinned commits:
- baseline: `2cdbfec`
- parent: `2cdbfec`
- target: `4819527`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
5. `audit/remediation/WAVE-3-SETUP.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
7. `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
8. `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`

Review scope:
- full diff `2cdbfec..4819527`
- committed snapshot only

Challenge these deliverables separately:
1. taxonomy and routing
2. deep-research prompt wiring and governance visibility
3. DAG dispatch and dependency ordering
4. concrete verifier and provenance sidecar
5. Wave 3 boundary discipline against Wave 3B deferrals

Required sub-verdicts:
- `routing and profile axis`
- `deep-research formalization`
- `DAG dispatch`
- `verifier and sidecar`
- `boundary compliance`

Output requirements:
- Distinguish manifest/scope issues from runtime issues.
- State whether any later Wave 3B behavior appears to have been pulled forward illegally.
- End with all five sub-verdicts plus one top-line `BLOCKED | CLEARED | CONTINGENT`.
```

## W3B-1 Prompt

```md
You are running slice `W3B-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W3B-1-wave-3b-control-path-audit.md`

Rules:
- Review only. Do not fix code.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review only the committed snapshot for `5cc9585` in an isolated worktree or detached checkout. Do not trust dirty `HEAD` as code truth.

Pinned commits:
- baseline: `4819527`
- parent: `4819527`
- target: `5cc9585`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
5. `audit/remediation/WAVE-3B-SETUP.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
7. `audit/remediation/runs/wave-3b/candidate-5cc9585-implementation.md`
8. `audit/remediation/runs/wave-3b/candidate-5cc9585-file-manifest.md`

Review scope:
- full diff `4819527..5cc9585`
- committed snapshot only

Challenge these two risk surfaces separately:
1. `StructuredOutline`, renderer consumption, and persisted round-state continuity
2. single-controller iterative-loop authority at orchestrator scope

Required sub-verdicts:
- `outline-render-state contract`
- `single-controller iterative loop`

Required checks:
- provenance continuity across outline and renderer
- round-state persistence and reload
- branch coverage and novelty stop logic
- round `N+1` refinement
- demotion of `ResearchAgent` to a per-round primitive
- no nested dual-controller runtime

Output requirements:
- Distinguish structural contract defects from control-loop authority defects.
- End with both sub-verdicts plus one top-line `BLOCKED | CLEARED | CONTINGENT`.
```

## W4-1 Prompt

```md
You are running slice `W4-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W4-1-wave-4-polish-audit.md`

Rules:
- Review only. Do not fix code.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review only the committed snapshot for `6406e46` in an isolated worktree or detached checkout. Do not trust dirty `HEAD` as code truth.

Pinned commits:
- baseline: `5cc9585`
- parent: `5cc9585`
- target: `6406e46`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-4-SETUP.md`
5. `audit/remediation/WAVE-4-POLISH-SPECS.md`
6. `audit/remediation/runs/wave-4/candidate-6406e46-implementation.md`
7. `audit/remediation/runs/wave-4/candidate-6406e46-file-manifest.md`

Review scope:
- full diff `5cc9585..6406e46`
- committed snapshot only

Audit only the frozen Wave 4 polish slice:
- `E-2`
- `E-4`
- `E-5`

Do not retroactively widen the scope using later Wave 4B goals.

Required checks:
- manifest and denylist compliance
- completeness classification fix
- renderer cleanup
- sample-schema sync
- no prompt, rubric, template, or Wave 4B content leakage

Output requirements:
- separate findings by `E-2`, `E-4`, `E-5`, and scope discipline
- end with one top-line `BLOCKED | CLEARED | CONTINGENT`
```

## W4B-1 Prompt

```md
You are running slice `W4B-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W4B-1-wave-4b-conformity-audit.md`

Rules:
- Review only. Do not fix code.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review only the committed snapshot for `65a612d` in an isolated worktree or detached checkout. Do not trust dirty `HEAD` as code truth.

Pinned commits:
- baseline: `6406e46`
- parent: `6406e46`
- target: `65a612d`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-4B-SETUP.md`
5. `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
6. `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
7. `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
8. `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
9. `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
10. `audit/remediation/runs/wave-4b/candidate-65a612d-implementation.md`
11. `audit/remediation/runs/wave-4b/candidate-65a612d-file-manifest.md`

Review scope:
- full diff `6406e46..65a612d`
- legality and conformity, not runtime correctness

Your job is to verify that the code changes stay inside the legal memo boundaries for Wave 4B.

Required sub-verdicts:
- `D-2 actionability`
- `core prompt quality`
- `sprint-contract / contradiction`
- `template / routing`
- `C-15 snippet sufficiency`

Required checks:
- touched-files to memo-contract mapping
- touched-files to tests/probes mapping
- no deferred capability leakage:
  - `C-6`
  - `C-10`
  - `C-11`
  - deferred `C-14`
  - deferred `C-7`
- no new runtime stage, registry, persisted field, or live source-fetch path introduced under a "content" label

Output requirements:
- report each of the five sub-verdicts explicitly
- identify any touched file that is memo-unsupported
- end with one top-line `BLOCKED | CLEARED | CONTINGENT`
- state whether `W4B-2` may return an unconditional `CLEARED` verdict
```

## W4B-2 Prompt

```md
You are running slice `W4B-2` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/W4B-2-wave-4b-runtime-audit.md`

Rules:
- Review only. Do not fix code.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Review only the committed snapshot for `65a612d` in an isolated worktree or detached checkout. Do not trust dirty `HEAD` as code truth.
- If `W4B-1` is not already `CLEARED`, your maximum allowed top-line verdict is `CONTINGENT`.

Pinned commits:
- baseline: `6406e46`
- parent: `6406e46`
- target: `65a612d`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/WAVE-4B-SETUP.md`
5. `audit/remediation/runs/wave-4b/candidate-65a612d-implementation.md`
6. `audit/remediation/runs/wave-4b/candidate-65a612d-file-manifest.md`
7. `audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md`
8. `audit/remediation/workstream-retro/reviews/W4B-1-wave-4b-conformity-audit.md` if it already exists

Review scope:
- full diff `6406e46..65a612d`
- committed snapshot only
- runtime correctness and load-bearing proof

Required checks:
1. D-2 actionability runtime behavior
2. shared `ScoredClaim` envelope preservation
3. sprint-contract 10-dimension exposure and contradiction handling without the 10-claim cap
4. tool-selection and template-enrichment runtime behavior inside the existing envelope
5. `UNVERIFIABLE` handling for thin or absent snippets
6. manifest compliance and denylist compliance

Output requirements:
- distinguish runtime failures from memo-conformity uncertainty
- if `W4B-1` is unresolved, explicitly say why your verdict is `CONTINGENT`
- otherwise end with one top-line `BLOCKED | CLEARED`
```

## X-1 Prompt

```md
You are running slice `X-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/X-1-cross-wave-regression-audit.md`

Rules:
- Review only. Do not fix code or rewrite historical artifacts.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Do not launch this slice unless every prior slice is already `CLEARED`.

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. all Batch 1, 2, 3, 4, 5, and 6 retrospective review reports
3. the final cleared packets for Waves 2B, 3, 3B, 4, and 4B
4. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
5. `audit/remediation/workstream-retro/AUDIT-EXECUTION-PLAN.md`
6. `audit/remediation/workstream-retro/AUDIT-SYNTHESIS-PLAN.md`

Your job is to answer the program-level question:

Assuming the trust gate and all wave-local audits have cleared, is there any cross-wave regression, baseline invalidation, or hidden dependency failure that the local slices missed?

Required checks:
- baseline inheritance validity across the whole code lineage
- whether any local "residual risk" should actually have propagated as a blocker
- whether any later clearance implicitly depended on an earlier illegal assumption
- whether packet or docs drift changes the apparent meaning of any local clearance
- whether the workstream as a whole can still be described as a valid sequence of bounded waves

Output requirements:
- distinguish:
  - local findings already handled correctly
  - newly discovered cross-wave invalidations
  - historical residuals that remain non-blocking
- end with one top-line `BLOCKED | CLEARED`
- if `BLOCKED`, state exactly which earlier wave must be considered invalidated downstream
```
