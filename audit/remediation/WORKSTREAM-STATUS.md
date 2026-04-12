# Workstream Status

*Created: 2026-04-11 | Purpose: stream separation and orientation*

If `audit/remediation/control-plane/` exists, that control plane outranks this file.  
This file is now an orientation layer, not the top authority.

---

## Current Snapshot

### Main remediation/build stream
- **Status:** Live blocked-remediation stream
- **Build status:** **Wave 1 complete**; **Wave 2A cleared**; **Wave 2B candidate `4ff7e90` blocked**
- **Current focus:** Reconcile and clear Wave 2B from a clean `4ff7e90` worktree, not from the dirty main workspace

### Round-3 content-audit stream
- **Status:** Parallel planning/research stream
- **Focus:** Prompt quality, rubric content, template logic, pipeline-content gaps, and later-wave planning changes
- **Important boundary:** This stream changes **later planning**; it does **not** directly re-scope Wave 2A

---

## Read This First

### For implementation sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. latest immutable review packet(s) for the active candidate
4. `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
5. `audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md`
6. `audit/remediation/WAVE-2B-SETUP.md`
7. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
8. `CURRENT-STATE.md`

### For planning sessions
Read in this order:
1. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
4. `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
5. `audit/remediation/round-3/PLANNING-ADDENDUM.md`
6. the relevant sidecar memo

### For review sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. the relevant run-folder artifact(s)
4. the relevant wave setup doc
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

---

## Stream 1: Main Remediation / Build

This is the **live execution stream**. It owns the actual implementation waves.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | Machine-readable live state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | Human-readable recovery and next action |
| latest immutable review packet(s) | Binding review truth for the active candidate |
| `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md` | Authoritative Wave 2B blocker ledger |
| `audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md` | Allowed write set for the active remediation loop |
| `CURRENT-STATE.md` | Live build summary |

### Current build status

| Wave | Status |
|------|--------|
| Wave 1A | Complete |
| Wave 1B | Complete |
| Wave 1C | Complete |
| Wave 2A | Cleared in `16e0bc7` |
| Wave 2B | Blocked candidate `4ff7e90` |

### What this means in practice

- Wave 2A is closed.
- Wave 2B is not “next”; it is a blocked checkpoint candidate that must be remediated.
- The authoritative implementation target is the blocked Wave 2B candidate plus the active blocker ledger.
- Do not reopen Wave 2A unless Wave 2B remediation surfaces a true regression.

---

## Stream 2: Round-3 Content Audit

This is a **parallel planning/research stream**. It is not the active implementation stream.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` | Canonical synthesis of round-3 content findings and bucket assignments |
| `audit/remediation/round-3/PLANNING-ADDENDUM.md` | Canonical resolution of round-3 direction calls and proposed later-wave changes |

### What this stream is for

- Identifying prompt, rubric, template, and pipeline-content issues
- Deciding what later waves need to change
- Surfacing governance and sequencing changes for Waves 2B and beyond
- Clarifying what must be added to governing docs later

### What this stream is **not** for

- It is **not** the current implementation scope for Wave 2A.
- It is **not** a signal to silently rewrite the live build plan mid-wave.
- It is **not** the current source of build status.

---

## How Round-3 Affects Planning Without Changing Wave 2A

Round-3 matters, but it matters **after** the current Wave 2A finish line.

### Direct effect

- The content audit and addendum change how later planning should be written.
- They introduce later-wave/planning changes such as dual-axis taxonomy work, thin Pipeline-L2, iterative research loop, additional Wave 2B/3/3B/4/4B/5 planning, and calibration sequencing.

### Non-effect on Wave 2A

- `PLANNING-ADDENDUM.md` explicitly says **Waves 1A through 2A are unchanged** and implementation can proceed immediately.
- `CONTENT-AUDIT-PLAN.md` explicitly frames the content audit as a **parallel, read-only** effort that should not conflict with ongoing implementation.
- Therefore: finish Wave 2A under the existing build docs. Apply round-3 planning changes when updating the governing documents for later waves.

---

## Authoritative Files vs. Historical / Stale Files

### Authoritative now

| File | Use it for |
|------|------------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | First-stop machine-readable state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | First-stop human-readable state |
| latest immutable review packet(s) | Binding blocked/cleared truth |
| `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md` | Active blocker ledger |
| `CURRENT-STATE.md` | Current build summary |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |
| `audit/remediation/WAVE-2B-SETUP.md` | Current Wave 2B blocked-remediation setup |
| `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` | Content-audit synthesis |
| `audit/remediation/round-3/PLANNING-ADDENDUM.md` | Later-planning direction calls |

### Historical or stale for current status

| File | Why it should not be treated as current status |
|------|-----------------------------------------------|
| `SESSION-LOG.md` | Historical record; use for rationale/history, not as the live status source |
| `audit/remediation/CONTENT-AUDIT-PLAN.md` | Audit launch/setup doc; superseded by the actual round-3 synthesis/addendum for current understanding |
| `audit/remediation/decisions/FINAL-DECISIONS.md` | Superseded |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.md` | Superseded by `FINAL-DECISIONS-v2.1.md` |

### Active docs with caveats

| File | Caveat |
|------|--------|
| `audit/remediation/BUILD-PROCESS.md` | Historical process discipline only; do not use as a launcher |
| `audit/remediation/WAVE-2A-SETUP.md` | Historical Wave 2A setup doc |
| `audit/remediation/WAVE-2B-SETUP.md` | Use only together with the control plane and blocker ledger |
| `CURRENT-STATE.md` | Summary only; review truth outranks it |

---

## Practical Rule Set for Future Sessions

1. If `audit/remediation/control-plane/` exists, read it before anything else.
2. If you are **implementing**, do it only from the clean implementation worktree, never the main workspace.
3. Do **not** use historical docs to infer current state when a newer review packet exists.
4. Do **not** let planning sidecars silently widen the active wave.
5. Do **not** advance Wave 2B until a committed candidate is reviewed and cleared.

---

## Next 5 Steps

1. Use the control-plane files as the first read in future remediation sessions.
2. Recover Wave 2B from the blocked `4ff7e90` snapshot, not from stale “Wave 2B next” assumptions.
3. Clear Wave 2B before opening Wave 3A or Wave 3.
4. Keep the round-3 planning overlay advisory until promoted by the controller.
5. Preserve the one-code-lane + sidecars pattern.
