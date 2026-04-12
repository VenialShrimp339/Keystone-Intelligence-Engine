# Workstream Status

*Created: 2026-04-11 | Updated: 2026-04-12 | Purpose: stream separation and orientation*

If `audit/remediation/control-plane/` exists, that control plane outranks this file.
This file is an orientation layer, not the top authority.
If any shortcut list here conflicts with `ACTIVE-HANDOFF.md`, the handoff wins.

---

## Current Snapshot

### Main remediation/build stream
- **Status:** Wave 4B cleared at `65a612d`
- **Build status:** **Wave 1 complete**; **Wave 2A cleared**; **Wave 2B cleared in `2cdbfec`**; **Wave 3 cleared in `4819527`**; **Wave 3B cleared in `5cc9585`**; **Wave 4 cleared in `6406e46`**; **Wave 4B cleared in `65a612d`**
- **Current focus:** Hard stop until a controller-approved post-Wave-4B setup artifact exists; the main workspace stays controller/docs only

### Round-3 content-audit stream
- **Status:** Parallel planning/research stream feeding Wave 4 and later
- **Focus:** Prompt quality, rubric content, template logic, pipeline-content gaps, and later-wave planning changes
- **Important boundary:** This stream informs later planning. It does **not** silently reopen any cleared implementation wave

## Read This First

### For implementation sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. the exact packet family, boundary docs, and summary docs named in `ACTIVE-HANDOFF.md`
4. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
5. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md` for controller-law background only

### For planning sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `CURRENT-STATE.md`
4. `audit/remediation/WORKSTREAM-STATUS.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
7. the relevant planning or sidecar memo set

### For review sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. the exact packet family and boundary docs named in `ACTIVE-HANDOFF.md`
4. `CURRENT-STATE.md`
5. `audit/remediation/WORKSTREAM-STATUS.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

## Stream 1: Main Remediation / Build

This remains the live execution stream.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | Machine-readable live state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | Human-readable live state |
| `audit/remediation/runs/wave-4b/candidate-65a612d-{adversarial-review,second-opinion,review-synthesis,clearance}.md` | Immutable Wave 4B review and clearance packet set |
| `audit/remediation/runs/wave-4b/candidate-65a612d-file-manifest.md` | Current candidate surface and scope boundary proof |
| `audit/remediation/WAVE-4B-SETUP.md` | Historical boundary for what Wave 4B was allowed to clear |
| `CURRENT-STATE.md` | Current build summary |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |

### Current build status

| Wave | Status |
|------|--------|
| Wave 1A | Complete |
| Wave 1B | Complete |
| Wave 1C | Complete |
| Wave 2A | Cleared in `16e0bc7` |
| Wave 2B | Cleared in `2cdbfec` |
| Wave 3A | Complete in `65074ca` (live setup promoted in `198ab92`) |
| Wave 3 | Cleared in `4819527` |
| Wave 3B | Cleared in `5cc9585` |
| Wave 4 | Cleared in `6406e46` |
| Wave 4B | Cleared in `65a612d` |

### What this means in practice

- The active cleared-state proof is the Wave 4B `65a612d` packet set.
- The next gate is **not** “start Wave 5 or deferred capability work.”
- Any future code lane, if later authorized, must root from the last cleared code commit `65a612d`, not from dirty `HEAD`.
- Until a new authority artifact is committed, the main workspace stays controller/docs only and the controller is hard-stopped.
- `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` are controller-authorized retrospective sidecar roots only, not live status authority by default.

## Stream 2: Round-3 Content Audit

This remains a parallel planning/research stream.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` | Canonical synthesis of round-3 content findings and bucket assignments |
| `audit/remediation/round-3/PLANNING-ADDENDUM.md` | Canonical resolution of round-3 direction calls and proposed later-wave changes |
| `audit/remediation/WAVE-4-4B-PREWORK.md` | Accepted Wave 4 / 4B decomposition layer |
| `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md` | Accepted D-2 actionability sidecar |
| `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md` | Accepted sprint-contract / contradiction-boundary sidecar for Wave 4B |
| `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md` | Accepted routing / template-enrichment sidecar for Wave 4B |
| `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md` | Accepted evaluator-verification sidecar for Wave 4B |

### What this stream is for

- Identifying prompt, rubric, template, and pipeline-content issues
- Deciding what later waves need to change
- Surfacing governance and sequencing changes for Wave 4 and beyond

### What this stream is not for

- It is **not** permission to reopen cleared Wave 4B code.
- It is **not** permission to skip the next setup gate once one exists.
- It is **not** the live source of build status.

## Authoritative Files vs. Historical / Stale Files

### Authoritative now

| File | Use it for |
|------|------------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | First-stop machine-readable state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | First-stop human-readable state |
| `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md` | Cleared-state proof for the current last-cleared code commit |
| `audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md` | Wave 4B review consensus |
| `audit/remediation/runs/wave-4b/candidate-65a612d-file-manifest.md` | Current candidate surface and scope boundary proof |
| `audit/remediation/WAVE-4B-SETUP.md` | Historical boundary for what Wave 4B was allowed to contain |
| `CURRENT-STATE.md` | Current build summary |
| `audit/remediation/WORKSTREAM-STATUS.md` | Orientation summary that must mirror the active handoff |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |
| `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md` | Controller-law and schema background, not live packet precedence |

### Historical or stale for current status

| File | Why it should not be treated as current status |
|------|-----------------------------------------------|
| `SESSION-LOG.md` | Historical record; use for rationale/history, not as the live status source |
| `audit/remediation/WAVE-4-SETUP.md` | Historical Wave 4 runway context now that Wave 4B is cleared |
| `audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md` | Historical blocked review packet for `4ff7e90`, not the cleared candidate |
| `audit/remediation/WAVE-2B-SECOND-OPINION.md` | Historical blocked second opinion for `4ff7e90`, not the cleared candidate |
| `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` outputs | Retrospective planning and review sidecars unless a later controller reconcile promotes them |
| `audit/remediation/decisions/FINAL-DECISIONS.md` | Superseded |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.md` | Superseded by `FINAL-DECISIONS-v2.1.md` |

## Practical Rule Set for Future Sessions

1. If `audit/remediation/control-plane/` exists, read it before anything else.
2. Keep the main workspace controller/docs only.
3. Do not let any post-Wave-4B work silently widen into Wave 5 or deferred capability implementation.
4. Treat `65a612d` as the current last cleared code commit.
5. Do not move again until a new committed authority artifact exists.

## Next 5 Steps

1. Use the control-plane files as the first read in future sessions.
2. Treat `65a612d` as the last cleared code commit.
3. Use the Wave 4B clearance packet set plus `WAVE-4B-SETUP.md` as the current boundary evidence.
4. Stop until a controller-approved next-wave setup artifact is committed.
5. Preserve the one-code-lane + sidecars pattern.
