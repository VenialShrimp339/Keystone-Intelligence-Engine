# Workstream Status

*Created: 2026-04-11 | Updated: 2026-04-12 | Purpose: stream separation and orientation*

If `audit/remediation/control-plane/` exists, that control plane outranks this file.
This file is an orientation layer, not the top authority.

---

## Current Snapshot

### Main remediation/build stream
- **Status:** Wave 4 setup active from cleared Wave 3B baseline `5cc9585`
- **Build status:** **Wave 1 complete**; **Wave 2A cleared**; **Wave 2B cleared in `2cdbfec`**; **Wave 3 cleared in `4819527`**; **Wave 3B cleared in `5cc9585`**
- **Current focus:** Continue the remaining Wave 4 research memos in the main workspace; the narrow Wave 4 polish slice is now frozen on paper but still unopened in code

### Round-3 content-audit stream
- **Status:** Parallel planning/research stream feeding Wave 4 and later
- **Focus:** Prompt quality, rubric content, template logic, pipeline-content gaps, and later-wave planning changes
- **Important boundary:** This stream informs later planning. It does **not** silently reopen any cleared implementation wave

## Read This First

### For implementation sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. latest immutable review and clearance packet(s) for the cleared candidate
4. `audit/remediation/WAVE-4-SETUP.md`
5. `CURRENT-STATE.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

### For planning sessions
Read in this order:
1. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/WAVE-4-SETUP.md`
4. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
5. `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
6. `audit/remediation/round-3/PLANNING-ADDENDUM.md`
7. the relevant sidecar memo

### For review sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. the relevant run-folder artifact(s)
4. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

## Stream 1: Main Remediation / Build

This remains the live execution stream.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | Machine-readable live state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | Human-readable live state |
| `audit/remediation/runs/wave-3b/candidate-5cc9585-*.md` | Immutable Wave 3B candidate, review, synthesis, and clearance artifacts |
| `audit/remediation/WAVE-4-SETUP.md` | Active Wave 4 execution runway |
| `CURRENT-STATE.md` | Current build summary |

### Current build status

| Wave | Status |
|------|--------|
| Wave 1A | Complete |
| Wave 1B | Complete |
| Wave 1C | Complete |
| Wave 2A | Cleared in `16e0bc7` |
| Wave 2B | Cleared in `2cdbfec` |
| Wave 3A | Complete in `65074ca` |
| Wave 3 | Cleared in `4819527` |
| Wave 3B | Cleared in `5cc9585` |
| Wave 4 | Active in setup state |

### What this means in practice

- The active setup artifact is `WAVE-4-SETUP.md`.
- The next gate is **not** “start Wave 4B content implementation or broad cleanup.”
- The next code lane, when allowed, must root from the last cleared code commit `5cc9585`, not from dirty `HEAD`.
- Until that code lane is explicitly opened, the main workspace stays controller/docs only.

## Stream 2: Round-3 Content Audit

This remains a parallel planning/research stream.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` | Canonical synthesis of round-3 content findings and bucket assignments |
| `audit/remediation/round-3/PLANNING-ADDENDUM.md` | Canonical resolution of round-3 direction calls and proposed later-wave changes |
| `audit/remediation/WAVE-4-4B-PREWORK.md` | Accepted Wave 4 / 4B decomposition layer |
| `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md` | Accepted D-2 actionability sidecar |

### What this stream is for

- Identifying prompt, rubric, template, and pipeline-content issues
- Deciding what later waves need to change
- Surfacing governance and sequencing changes for Wave 4 and beyond

### What this stream is not for

- It is **not** permission to reopen cleared Wave 3B code.
- It is **not** permission to skip the Wave 4 setup boundary.
- It is **not** the live source of build status.

## Authoritative Files vs. Historical / Stale Files

### Authoritative now

| File | Use it for |
|------|------------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | First-stop machine-readable state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | First-stop human-readable state |
| `audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md` | Cleared-state proof for the current last-cleared code commit |
| `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md` | Wave 3B review consensus |
| `audit/remediation/WAVE-4-SETUP.md` | Active Wave 4 execution runway |
| `CURRENT-STATE.md` | Current build summary |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |

### Historical or stale for current status

| File | Why it should not be treated as current status |
|------|-----------------------------------------------|
| `SESSION-LOG.md` | Historical record; use for rationale/history, not as the live status source |
| `audit/remediation/WAVE-3B-SETUP.md` | Historical Wave 3B setup context, not the active runway |
| `audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md` | Historical blocked review packet for `4ff7e90`, not the cleared candidate |
| `audit/remediation/WAVE-2B-SECOND-OPINION.md` | Historical blocked second opinion for `4ff7e90`, not the cleared candidate |
| `audit/remediation/decisions/FINAL-DECISIONS.md` | Superseded |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.md` | Superseded by `FINAL-DECISIONS-v2.1.md` |

## Practical Rule Set for Future Sessions

1. If `audit/remediation/control-plane/` exists, read it before anything else.
2. Keep the main workspace controller/docs only.
3. Do not let Wave 4 setup silently widen into Wave 4B content implementation.
4. Root the next code work from `5cc9585`.
5. Do not let planning sidecars silently widen the active scope.

## Next 5 Steps

1. Use the control-plane files as the first read in future sessions.
2. Treat `5cc9585` as the last cleared code commit.
3. Use `WAVE-4-SETUP.md` plus the Wave 3B review packet set as the current boundary evidence.
4. Finish the remaining Wave 4 docs lane before opening the next clean implementation lane.
5. Preserve the one-code-lane + sidecars pattern.
