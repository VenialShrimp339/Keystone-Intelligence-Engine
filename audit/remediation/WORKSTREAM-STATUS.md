# Workstream Status

*Created: 2026-04-11 | Purpose: canonical handoff/orientation doc for future sessions*

This file is the entry point for remediation work. Use it first to determine which stream you are in, which docs are authoritative, and which older docs are history only.

---

## Current Snapshot

### Main remediation/build stream
- **Status:** Live implementation stream
- **Build status:** **Wave 1 complete**; **Wave 2A cleared**; **Wave 2B next**
- **Current focus:** Start Wave 2B from the cleared Wave 2A baseline and reconciled governing docs

### Round-3 content-audit stream
- **Status:** Parallel planning/research stream
- **Focus:** Prompt quality, rubric content, template logic, pipeline-content gaps, and later-wave planning changes
- **Important boundary:** This stream changes **later planning**; it does **not** directly re-scope Wave 2A

---

## Read This First

### For implementation sessions
Read in this order:
1. `audit/remediation/WORKSTREAM-STATUS.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
4. `audit/remediation/BUILD-PROCESS.md`
5. `audit/remediation/WAVE-2B-SETUP.md` if you are starting Wave 2B
6. `SESSION-LOG.md` Sessions 19-22 only if you need rationale or exact prior decisions

### For planning sessions
Read in this order:
1. `audit/remediation/WORKSTREAM-STATUS.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
4. `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md`
5. `audit/remediation/round-3/PLANNING-ADDENDUM.md`
6. `SESSION-LOG.md` Sessions 19-20 if you need design/build history

### For review sessions
Read in this order:
1. `audit/remediation/WORKSTREAM-STATUS.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
4. `audit/remediation/BUILD-PROCESS.md`
5. The relevant wave setup doc
6. The relevant implementation session log entry or diff

---

## Stream 1: Main Remediation / Build

This is the **live execution stream**. It owns the actual implementation waves.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/WORKSTREAM-STATUS.md` | Canonical orientation and stream separation |
| `CURRENT-STATE.md` | Canonical live build status and next-wave summary |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding implementation design and wave order |
| `audit/remediation/BUILD-PROCESS.md` | Build discipline and checkpoint process |
| `audit/remediation/WAVE-2B-SETUP.md` | Current Wave 2B execution checklist and scope notes |

### Current build status

| Wave | Status |
|------|--------|
| Wave 1A | Complete |
| Wave 1B | Complete |
| Wave 1C | Complete |
| Wave 2A | Cleared in `16e0bc7` |
| Wave 2B | Next |

### What this means in practice

- Wave 2A is closed. The authoritative implementation target is now Wave 2B.
- Wave 2B scope comes from `FINAL-DECISIONS-v2.1.md`, `CURRENT-STATE.md`, and `WAVE-2B-SETUP.md`.
- Wave 2A review artifacts remain important background if Wave 2B touches adjacent provenance/rendering seams.
- Do not reopen Wave 2A unless Wave 2B implementation or review surfaces a true regression.

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
| `audit/remediation/WORKSTREAM-STATUS.md` | First-stop orientation |
| `CURRENT-STATE.md` | Current build status |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |
| `audit/remediation/BUILD-PROCESS.md` | Build/checkpoint discipline |
| `audit/remediation/WAVE-2B-SETUP.md` | Current Wave 2B execution setup |
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
| `audit/remediation/BUILD-PROCESS.md` | Treat it as authoritative for process discipline, but not for older `v2.md` references or any pre-Session-20 assumptions that conflict with the now-proven Wave 2A setup |
| `audit/remediation/WAVE-2A-SETUP.md` | Historical Wave 2A setup doc. Use only if you need to reconstruct the Wave 2A implementation/review arc. |
| `audit/remediation/WAVE-2B-SETUP.md` | Authoritative for the current implementation wave |
| `CURRENT-STATE.md` | Treat it as authoritative for live build status, but remember it has not yet been updated to absorb the round-3 planning changes for later waves |

---

## Practical Rule Set for Future Sessions

1. If you are **implementing**, stay in the main remediation/build stream.
2. If you are **replanning later waves**, read the round-3 docs alongside the live build docs.
3. Do **not** use historical docs to infer current status when a newer authoritative file exists.
4. Do **not** let round-3 planning findings silently expand Wave 2A scope.
5. Before Wave 2B starts, reconcile the live governing docs with the round-3 planning decisions so there is one clear plan again.

---

## Next 5 Steps

1. Use this file as the first read in future remediation sessions.
2. Start Wave 2B against `FINAL-DECISIONS-v2.1.md`, `CURRENT-STATE.md`, and `WAVE-2B-SETUP.md`.
3. Run the Wave 2B adversarial review and close any blockers before opening Wave 3.
4. Keep the round-3 planning overlay aligned with the main build docs as later waves land.
5. Preserve the one-code-lane + sidecars pattern: one active implementation wave, multiple review/planning lanes.
