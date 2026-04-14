# Workstream Status

*Created: 2026-04-11 | Updated: 2026-04-13 | Purpose: stream separation and orientation*

If `audit/remediation/control-plane/` exists, that control plane outranks this file.
This file is an orientation layer, not the top authority.
If any shortcut list here conflicts with `ACTIVE-HANDOFF.md`, the handoff wins.

---

## Current Snapshot

### Main remediation/build stream
- **Status:** Wave 4B remains the last cleared implementation wave at `65a612d`; Retrieval MVP Lane D candidate `f1af7df` is frozen as blocked reference material; `Lane H` is now the live forward setup authority
- **Build status:** **Wave 1 complete**; **Wave 2A cleared**; **Wave 2B cleared in `2cdbfec`**; **Wave 3 cleared in `4819527`**; **Wave 3B cleared in `5cc9585`**; **Wave 4 cleared in `6406e46`**; **Wave 4B cleared in `65a612d`**
- **Current focus:** Lane H implementation for system-owned article/PDF canonical fetch authority expansion

### Round-3 content-audit stream
- **Status:** Parallel planning/research stream feeding Wave 4 and later
- **Focus:** Prompt quality, rubric content, template logic, pipeline-content gaps, and later-wave planning changes
- **Important boundary:** This stream informs later planning. It does **not** silently reopen any cleared implementation wave

## Read This First

### For implementation sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
4. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
5. `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
6. `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
5. the exact packet family and boundary docs named in `ACTIVE-HANDOFF.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

Do **not** treat `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch` as currently authorized for more coding.
Do treat `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` as the only currently authorized retrieval runtime worktree.

### For planning sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
4. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
5. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
6. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
7. `CURRENT-STATE.md`
8. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
9. `audit/remediation/WORKSTREAM-STATUS.md`
10. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

### For review sessions
Read in this order:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
4. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
5. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
6. `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
7. `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
8. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md`
9. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md`

## Stream 1: Main Remediation / Build

This remains the live execution stream. The current step is no longer docs-only controller work; it is the newly authorized `Lane H` retrieval authority-expansion implementation lane.

### What is authoritative now

| File | Role now |
|------|----------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | Machine-readable live state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | Human-readable live state |
| `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml` | Controller-promoted retrospective lineage layer for docs checkpoints `35a8a29` through `2e6d780` |
| `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml` | Controller-promoted current retrospective prerequisite layer |
| `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md` | Active human-readable Lane H boundary and mission |
| `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md` | Active authority ruling for system-owned `document_fetch` |
| `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md` | Active Lane H setup authority |
| `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md` | Exact approved Lane H write set and denylist |
| `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md` | Canonical contract shape Lane H must implement |
| `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md` | Promotion verdict clearing Lane H package for live control-plane use |
| `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md` | Active authority ruling for the blocked Retrieval MVP Lane D candidate |
| `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md` | Active controller-priority follow-up lane definition |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md` | Latest blocked candidate synthesis |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md` | Immutable blocked-state checkpoint for the latest retrieval candidate |
| `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md` | Cleared-state proof for the current last-cleared code commit |
| `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md` | Historical Lane D setup boundary the blocked candidate was reviewed against |
| `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md` | Historical Lane D write-set boundary the blocked candidate was reviewed against |
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
| Retrieval MVP Lane D | Blocked at candidate `f1af7df` and frozen as superseded reference only |
| Lane H | Setup promoted; implementation may now launch from `65a612d` |

### What this means in practice

- The active cleared-state proof is still the Wave 4B `65a612d` packet set.
- The latest Retrieval MVP Lane D candidate is blocked and may not be patched forward inside the old Lane D authority.
- The currently authorized forward code lane is `Lane H`, which must still root from the last cleared code commit `65a612d`, not from dirty `HEAD`.
- SEC / EDGAR venue review remains a later separate step after Lane H review.
- Browser Use research exists as sidecar material only. It is classified as fallback/browser-native acquisition research, not the canonical retrieval path.
- `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` remain retrospective sidecar roots only, not live status authority by default.

## Stream 2: Round-3 Content Audit

This remains a parallel planning/research stream.

### What this stream is for

- Identifying prompt, rubric, template, and pipeline-content issues
- Deciding what later waves need to change
- Surfacing governance and sequencing changes for Wave 4 and beyond

### What this stream is not for

- It is **not** permission to reopen cleared Wave 4B code.
- It is **not** permission to reopen blocked Retrieval MVP Lane D coding.
- It is **not** permission to bypass Lane H and wire Browser Use into the canonical path early.
- It is **not** the live source of build status.

## Authoritative Files vs. Historical / Stale Files

### Authoritative now

| File | Use it for |
|------|------------|
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | First-stop machine-readable state |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | First-stop human-readable state |
| `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml` | Exact retrospective docs/code/packet/boundary lineage pins replacing the historical symbolic-`HEAD` defect for audit use |
| `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml` | Exact current retrospective prerequisite status |
| `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md` | Active Lane H handoff |
| `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md` | Active Lane H authority ruling |
| `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md` | Live Lane H setup boundary |
| `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md` | Live Lane H write-set boundary |
| `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md` | Docs-only promotion verdict for Lane H |
| `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md` | Authority ruling for the blocked Retrieval MVP Lane D candidate |
| `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md` | Current controller-priority lane definition |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md` | Latest blocked-candidate synthesis |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md` | Latest blocked-candidate checkpoint |
| `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md` | Cleared-state proof for the current last-cleared code commit |
| `CURRENT-STATE.md` | Current build summary |
| `audit/remediation/WORKSTREAM-STATUS.md` | Orientation summary that must mirror the active handoff |
| `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md` | Current gap map from audited state -> MVP -> fuller product |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md` | Binding remediation design |

### Historical or stale for current status

| File | Why it should not be treated as current status |
|------|-----------------------------------------------|
| `SESSION-LOG.md` | Historical record; use for rationale/history, not as the live status source |
| `audit/remediation/WAVE-4-SETUP.md` | Historical Wave 4 runway context now that Wave 4B is cleared |
| `audit/remediation/WAVE-4B-SETUP.md` | Historical boundary for what Wave 4B was allowed to clear, not the current active lane |
| `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/` outputs | Retrospective planning and review sidecars unless a later controller reconcile promotes them |
| `audit/remediation/decisions/FINAL-DECISIONS.md` | Superseded |
| `audit/remediation/decisions/FINAL-DECISIONS-v2.md` | Superseded by `FINAL-DECISIONS-v2.1.md` |

## Practical Rule Set for Future Sessions

1. If `audit/remediation/control-plane/` exists, read it before anything else.
2. Keep the main workspace controller/docs only.
3. Do not authorize more coding in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch` from the blocked `f1af7df` candidate.
4. Treat `65a612d` as the current last cleared code commit.
5. Treat the retrospective audit program as complete prerequisite proof only, not as forward implementation authority by itself.
6. Treat `Lane H` as the current live forward setup authority for article/PDF canonical fetch.
7. Keep SEC / EDGAR venue review separate from Lane H.
8. Treat Browser Use as sidecar fallback/control-arm research only unless a later controller lane explicitly promotes it.

## Next 5 Steps

1. Use the control-plane files as the first read in future sessions.
2. Treat `65a612d` as the last cleared code commit.
3. Treat `f1af7df` as blocked and non-promotable under the old Lane D authority.
4. Run Lane H implementation in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`.
5. Preserve the one-code-lane + sidecars pattern for Lane H review and any later SEC venue retry.
