# Workstream Retro Audit Program Handoff

*Date: 2026-04-12 | Purpose: single-session handoff for designing the adversarial audit program for the long-running autonomous remediation workstream*

## What this session is for

This handoff is for a **new Codex session** that should take over from the long-running orchestration thread.

Its job is **not** to continue implementation.

Its job is to:

1. audit the proposed audit strategy itself
2. refine or replace that strategy if needed
3. produce the exact copy-paste prompts for the adversarial review sessions

This session should act as the **audit-program architect**, not as an implementation lane.

## Freeze Rule

Treat the current repo state as frozen for the purpose of this planning session.

- Current controller/docs branch: `codex/remediation-program`
- Last cleared-state docs checkpoint: `91f97c2` (`docs: clear wave 4b candidate`)
- Pre-planning retro handoff anchor: `2e6d780` (`Add handoff for retrospective audit-program planning`)
- Current planning-package docs commit at the start of this reconcile: `c5dbd055d1b9d67c0d40a46f18b6b3a7f2b46468` (`c5dbd05`, `docs: finalize workstream retro audit launch package`)
- Current planning-package lineage after Wave 4B clearance: `2e6d780 -> c5dbd05`
- Current last cleared code commit: `65a612d`

Do **not**:

- continue autonomous implementation
- create Wave 5 setup
- modify runtime code
- launch actual adversarial review sessions yet

This session may:

- read any relevant docs and run-folder artifacts
- use parallel read-only explorers or subagents
- write planning docs under `audit/remediation/workstream-retro/`
- write retrospective review sidecars under `audit/remediation/workstream-retro/reviews/`
- treat both paths as retrospective sidecars unless a later controller reconcile promotes them

## Why this handoff exists

The long-running autonomous session appears to have progressed through:

- Wave 2B clearance at `2cdbfec`
- Wave 3A seam-freeze artifact landing at `65074ca`, later promoted into live Wave 3 setup at `198ab92`
- Wave 3 clearance at `4819527`
- Wave 3B clearance at `5cc9585`
- Wave 4 clearance at `6406e46`
- Wave 4B clearance at `65a612d`

But because that session covered a very large scope across multiple waves, we want a **retrospective adversarial audit of the entire workstream**, not just of the final outputs.

The audit program itself therefore needs to be designed carefully:

- enough parallelism to be efficient
- enough dependency ordering to catch cascading invalidity
- enough scope precision that each review produces actionable results

## Current authoritative state to read first

Read these first, in order:

1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `CURRENT-STATE.md`
5. `audit/remediation/WORKSTREAM-STATUS.md`
6. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`

Then read these workstream artifacts:

7. `audit/remediation/runs/wave-2b/`
8. `audit/remediation/runs/wave-3/`
9. `audit/remediation/runs/wave-3b/`
10. `audit/remediation/runs/wave-4/`
11. `audit/remediation/runs/wave-4b/`

Then read the setup/seam/research docs relevant to boundary review:

12. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
13. `audit/remediation/WAVE-3-SETUP.md`
14. `audit/remediation/WAVE-3B-SETUP.md`
15. `audit/remediation/WAVE-4-SETUP.md`
16. `audit/remediation/WAVE-4B-SETUP.md`
17. `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
18. `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
19. `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
20. `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
21. `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`

## Important structural fact

There are **two intertwined histories** to audit:

### 1. Code lineage

`4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`

These cleared code snapshots live on clean worktree branches, not on `codex/remediation-program`.

### 2. Controller/docs lineage

Cleared-state lineage through Wave 4B:

`35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2`

Later planning-package lineage:

`2e6d780 -> c5dbd05`

These checkpoints live on `codex/remediation-program`.

Important historical note:

- `65074ca` is the real seam-freeze artifact landing because it creates `WAVE-3A-SEAM-FREEZE.md`.
- That same commit is internally stale because its live control-plane and handoff text still instruct the controller to create that doc.
- `198ab92` is the later controller reconcile that first promotes the seam freeze into active `wave-3 / setup`.

This means a monolithic audit of the current branch is **not sufficient**.

## Candidate audit-slice plan to pressure-test

Treat the following as a **candidate plan**, not as settled truth.

The new session’s first job is to audit whether this slicing is correct.

### Batch 1 candidate slices

1. `CP-1` Control-plane authority audit
2. `CP-2` Controller checkpoint-chain audit
3. `RP-1` Review-packet integrity meta-audit
4. `W2B-1` Wave 2B blocked-remediation audit
5. `W3A-1` Wave 3A seam-freeze contract audit
6. `W4D-1` Wave 4 memo-boundary audit

### Batch 2 candidate slice

7. `W3-1` Wave 3 runtime audit

### Batch 3 candidate slice

8. `W3B-1` Wave 3B runtime audit

### Batch 4 candidate slice

9. `W4-1` Wave 4 polish/runtime audit

### Batch 5 candidate slices

10. `W4B-1` Wave 4B memo-to-code conformity audit
11. `W4B-2` Wave 4B runtime audit

### Batch 6 candidate slice

12. `X-1` Cross-wave regression audit

## Candidate dependency ordering to pressure-test

Strict order currently believed safest:

1. Batch 1 all in parallel
2. `W3-1` only after `W2B-1` and `W3A-1`
3. `W3B-1` only after `W3-1`
4. `W4-1` only after `W3B-1` and `W4D-1`
5. `W4B-1` and `W4B-2` only after `W4-1` and `W4D-1`
6. `X-1` only after all prior code-wave audits

The new session should challenge this.  
If a better dependency graph exists, replace it.

## What the new session should deliver

It should write all outputs under:

`audit/remediation/workstream-retro/`

At minimum:

1. `AUDIT-PLAN-REVIEW.md`
   - a critique of the candidate audit-slice plan
   - findings on over-fragmentation, under-fragmentation, missing slices, wrong dependencies, false parallelism, or trust gaps

2. `AUDIT-EXECUTION-PLAN.md`
   - the final batch structure
   - exact slice ordering
   - stop/go rules
   - whether strict order or contingent mode is better

3. `BATCH-1-PROMPTS.md`
   - exact copy-paste prompts for every Batch 1 review session

4. `BATCH-2-PLUS-PROMPTS.md`
   - exact copy-paste prompts for later batches
   - clearly labeled prerequisites for each

5. `AUDIT-SYNTHESIS-PLAN.md`
   - how the results from all review sessions should later be merged
   - what counts as a local finding vs a cascading invalidation

## Requirements for the new session

### Scope discipline

- Do not conduct the adversarial reviews themselves.
- Do not fix code.
- Do not continue Wave 5 or later work.
- Stay inside planning/docs for the audit program.

### Method

- It may use parallel 5.4 xhigh explorers/subagents to analyze the audit plan and repo structure.
- It should challenge whether the candidate slices are the right boundaries.
- It should explicitly identify any slice that must be split or merged.
- It should identify where a later review depends on trusting an earlier stage.

### Output style

The outputs should optimize for launchability:

- exact output paths
- exact prompt text
- exact baseline/target commit guidance where relevant
- clear “do not trust dirty tree” instructions
- explicit `BLOCKED | CLEARED | CONTINGENT` verdict requirements for the eventual review sessions

## Launch prompt for the new session

Use this exact prompt in the new Codex session:

```md
Read `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/workstream-retro/AUDIT-PROGRAM-HANDOFF.md` and execute it exactly.

Important:
- This is a planning/docs session only.
- Do not continue implementation or Wave 5 work.
- Do not run the adversarial audit sessions yet.
- Your job is to audit the audit strategy itself, refine it, and write the exact copy-paste prompts for the eventual review sessions.
- Use GPT-5.4 with xhigh fast for every spawned agent.
```
