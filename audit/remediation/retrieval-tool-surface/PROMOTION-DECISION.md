# Promotion Decision

Date: 2026-04-13  
Controller mode: docs-only promotion review rerun against current disk state

## Verdict

- Final verdict: `PROMOTE`
- Safe to promote into the live control plane: `YES`

## What Verified Cleanly

- The package still chooses the correct contract shape: a system-owned, non-task-assignable `document_fetch`, not a new ordinary task tool. See `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md:16-32,53-75`, `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md:26-34`, and `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md:17-39,71-107`.
- The package still keeps article/PDF authority separate from SEC venue classification. See `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md:116-144` and `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md:17-22,48-57,89-92`.
- The package still preserves `f1af7df` as superseded reference material rather than reclassifying it as environment-only blocked. See `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md:48-57` and `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md:124-132`.

## Previously Blocked Defects Now Closed

### 1. Promotion checklist now includes the required gate-checklist update set

- `audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md:30-46` now explicitly includes `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md` in the required external docs to update on promotion.
- That now matches the current controller authority stack in `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md:23-35`, `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md:29-43`, and `audit/remediation/control-plane/ACTIVE-HANDOFF.md:145-162`.
- Result: the promotion checklist now names the missing external controller document that governs the pre-promotion gate stack.

### 2. `src/keystone/models/research.py` is now fenced to additive-only DTO work

- `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md:90-104` now gives `src/keystone/models/research.py` its own explicit shared-surface fence.
- That fence limits the file to isolated additive request/response/identity/coverage/audit DTO blocks and expressly forbids changing existing semantics, fields, validators, defaults, or behavior for `ResearchSpec`, `EngagementSpec`, `PipelineProfile`, `StructuredFinding`, and `FindingClaim`.
- Result: the write set is now narrow and honest on the shared research-model surface.

### 3. Controller-grade proof requirements are restored

- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md:126-140` now requires `tests/unit/test_audit_log.py` in the mandatory unit matrix.
- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md:142-155` now requires both `candidate-<sha>-backend-truth-matrix.md` and `candidate-<sha>-review-synthesis.md` in the review packet.
- Those requirements now align again with `audit/remediation/control-plane/ACTIVE-HANDOFF.md:178-205` and the prior controller-grade packet discipline in `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md:49-60,77-128`.
- Result: the package no longer softens audit, backend-reality, or synthesis proof requirements.

## Promotion Decision

- Promotion outcome: `PROMOTE`
- Lane to activate after control-plane updates: `Lane H - Retrieval Tool-Surface Authority Expansion`
- Branch to record: `codex/retrieval-tool-surface`
- Worktree to record: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
- Run packet root to record: `audit/remediation/runs/retrieval-tool-surface/`
- Article/PDF MVP-critical status: unchanged
- SEC status: separate downstream venue review

## Remaining Blockers

- None in the current file contents of the reviewed retrieval-tool-surface package.
