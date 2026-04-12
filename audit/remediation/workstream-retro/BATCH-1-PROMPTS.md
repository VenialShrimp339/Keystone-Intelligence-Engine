# Batch 1 Prompts

*Date: 2026-04-12 | Scope: exact copy-paste prompts for Batch 1 trust-gate review sessions*

---

## Batch 1 Overview

Batch 1 is the hard trust gate.

Do not launch any downstream retrospective audit session unless all three Batch 1 slices return `CLEARED`.

Pinned context for all three prompts:

- pre-planning docs anchor commit: `2e6d780`
- last cleared-state docs checkpoint: `91f97c2`
- current planning-package docs commit observed at the start of this reconcile: `c5dbd05`
- controller-promoted retrospective lineage manifest: `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- last cleared code commit: `65a612d`
- code lineage:
  `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- controller/docs lineage:
  `35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2 -> 2e6d780`

Interpretation note:

- `2e6d780` is a pre-planning anchor, not the literal current docs `HEAD`.
- `65074ca` lands `WAVE-3A-SEAM-FREEZE.md`, but that commit is internally stale because it still says to create that doc.
- `198ab92` is the later controller reconcile that first promotes the seam freeze into active `wave-3 / setup`.
- Historical symbolic `HEAD` references across `35a8a29 -> 2e6d780` are replaced for retrospective audit use by the exact git-derived pins in `RETROSPECTIVE-LINEAGE-MANIFEST.yaml`.

## CP-1 Prompt

```md
You are running slice `CP-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/CP-1-control-plane-authority-audit.md`

Rules:
- This is review-only. Do not fix code, do not advance Wave 5, and do not mutate controller authority files.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Treat the dirty main workspace as non-authoritative for code truth.
- Treat this report as a retrospective sidecar, not a controller-promoted authority artifact.

Pinned context:
- Pre-planning docs anchor commit: `2e6d780`
- Last cleared-state docs checkpoint: `91f97c2`
- Last cleared code commit: `65a612d`

Read first, in order:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
5. `CURRENT-STATE.md`
6. `audit/remediation/WORKSTREAM-STATUS.md`
7. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
8. `audit/remediation/workstream-retro/AUDIT-PROGRAM-HANDOFF.md`

Your job is to audit the control-plane authority model itself.

Challenge these questions:
1. Is the authority order consistent across the machine-readable control plane, the human handoff, the status docs, and the hardened autonomy plan?
2. Is the hard-stop state after Wave 4B coherent and accurately represented?
3. Are the lease, docs-only workspace rule, and dirty-tree quarantine rules stated consistently?
4. Is there any governance contradiction between the handoff's permission to write under `audit/remediation/workstream-retro/` and the active control-plane allowed write set?
5. Are any authority references still symbolic or ambiguous in a way that would make downstream retrospective review unsafe?

Required findings:
- authority-order drift
- hard-stop drift
- write-set or governance mismatch
- symbolic `HEAD` ambiguity
- any stale-doc contradiction that could mislead later audits

Output requirements:
- State exactly which files you treated as authoritative vs non-authoritative.
- Quote the exact current docs branch HEAD you observed.
- Distinguish `BLOCKED`, `CLEARED`, and `CONTINGENT` using the retrospective audit-program semantics:
  - `CLEARED`: inputs are authoritative and internally coherent
  - `BLOCKED`: contradictions or missing authority make downstream audits unsafe
  - `CONTINGENT`: mostly coherent, but a prerequisite trust slice still needs to confirm a dependency
- End with one top-line verdict and a short "downstream effect" section that says whether Batch 2 may launch.
```

## CP-2 Prompt

```md
You are running slice `CP-2` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/CP-2-controller-lineage-join-audit.md`

Rules:
- This is review-only. Do not change code, packets, or controller docs.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- Treat code truth and controller/docs truth as separate histories.
- Do not trust the dirty main workspace as code truth.

Pinned context:
- Pre-planning docs anchor commit: `2e6d780`
- Last cleared-state docs checkpoint: `91f97c2`
- Last cleared code commit: `65a612d`
- Code lineage:
  `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- Controller/docs lineage:
  `35a8a29 -> 2c026cc -> f717507 -> a370963 -> 65074ca -> 198ab92 -> 6eafc82 -> cd8ad1f -> 5453fb9 -> 0df3596 -> b42d035 -> 456f29c -> 28ebe1a -> d16a40a -> d73c406 -> fabe847 -> 91f97c2 -> 2e6d780`

Read first, in order:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
5. `CURRENT-STATE.md`
6. `audit/remediation/WORKSTREAM-STATUS.md`
7. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
8. `audit/remediation/workstream-retro/AUDIT-PROGRAM-HANDOFF.md`
9. the relevant Wave 2B, 3, 3B, 4, and 4B clearance and review-synthesis artifacts

Also inspect git history directly.

Your job is to verify the controller/docs checkpoint chain and the controller-code-packet join.

For every controller/docs checkpoint from `35a8a29` through the pre-planning docs anchor `2e6d780`, verify:
1. the claimed wave/state transition
2. the exact code commit it refers to
3. the exact review packet set it relies on
4. the exact active setup or boundary doc it advances to
5. the exact next action it claims
6. whether that mapping is correct on disk and in git history

Required checks:
- stale-doc divergence
- wrong commit-to-packet mapping
- wrong packet-to-next-action mapping
- skipped or implicit state transitions
- use of symbolic `HEAD` where an exact commit should have been pinned
- explicit handling of the `65074ca` seam-freeze anomaly versus the later `198ab92` setup activation
- verify that `RETROSPECTIVE-LINEAGE-MANIFEST.yaml` is sufficient as the authoritative retrospective lineage layer without weakening the git-verification standard

Output requirements:
- Include a compact checkpoint table with columns:
  `docs_commit | claimed_state | code_commit | packets | boundary_doc | next_action | verdict`
- Separate local metadata mismatches from state-transition blockers.
- End with a top-line `BLOCKED | CLEARED | CONTINGENT` verdict and a short statement on whether downstream wave audits can trust the documented lineage.
```

## RP-1 Prompt

```md
You are running slice `RP-1` of the retrospective remediation-workstream audit program for the Keystone Intelligence Engine.

Write your report to:
`audit/remediation/workstream-retro/reviews/RP-1-review-packet-integrity-audit.md`

Rules:
- This is review-only. Do not modify packets or controller docs.
- If you need subagents, use GPT-5.4 with xhigh fast for every spawned subagent and record any deviation.
- This is a packet-integrity audit, not a code-quality audit.

Pinned context:
- pre-planning docs anchor commit: `2e6d780`
- last cleared-state docs checkpoint: `91f97c2`

Read first:
1. `graphify-out/GRAPH_REPORT.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
4. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
5. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
6. `audit/remediation/workstream-retro/AUDIT-PROGRAM-HANDOFF.md`
7. every file under:
   - `audit/remediation/runs/wave-2b/`
   - `audit/remediation/runs/wave-3/`
   - `audit/remediation/runs/wave-3b/`
   - `audit/remediation/runs/wave-4/`
   - `audit/remediation/runs/wave-4b/`

Your job is to validate the integrity of the run-folder packet system itself.

Required checks:
1. packet presence:
   - implementation
   - file manifest
   - adversarial review
   - second opinion
   - review synthesis
   - clearance or blocked checkpoint as appropriate
2. metadata alignment:
   - baseline commit
   - candidate parent
   - target commit
   - wave label
3. cross-link correctness
4. template scaffold correctness
5. corruption markers:
   - `*** Add File`
   - `*** Update File`
   - `*** End Patch`
   - copied content from another wave
6. cross-wave contamination or duplicate clearance content embedded in the wrong file

Do not stop at "all files exist."

You must explicitly scan for malformed packet content and scaffolding defects.

Output requirements:
- Report packet-integrity findings by wave.
- Distinguish:
  - missing packet
  - malformed packet
  - metadata mismatch
  - cross-wave contamination
  - template corruption
- State whether any defect is severe enough to invalidate downstream wave reviews.
- End with one top-line `BLOCKED | CLEARED | CONTINGENT` verdict and a short note on whether Batch 2 may launch.
```
