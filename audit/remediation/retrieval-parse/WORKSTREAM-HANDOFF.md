# Retrieval Parse Workstream Handoff

Date: 2026-04-14
Controller mode: docs-only narrow Lane E packaging
Authoritative runtime anchor: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`

## Mission

Package the next forward lane that owns deterministic parse and evidence normalization for the cleared article/PDF fetch path without:

- reopening Lane H fetch authority
- weakening the system-owned `document_fetch` boundary
- pulling SEC / EDGAR back into scope
- widening into Lane F integration, UI, or benchmark acceptance

## Hard Guardrails

- Lane H is already `CLEARED` at `93a5ca8` and remains the current runtime truth for governed article/PDF fetch.
- `document_fetch` stays system-owned and non-task-assignable exactly as cleared in Lane H.
- Lane E consumes Lane H output through persisted raw artifacts and metadata such as `storage_path`, `canonical_url`, `content_hash`, `coverage`, and audit linkage.
- Lane E is article/PDF only.
- Lane E is deterministic parse plus evidence normalization only.
- Lane E does not own SEC / EDGAR, papers, citation-schema migration, research-agent integration, UI, or benchmark acceptance claims.
- The main workspace remains docs-only for this package.

## Executive Judgment

- The correct next runtime lane is a narrow `Lane E - Article/PDF Deterministic Parse And Evidence Normalization`.
- The lane should add parse-local modules and tests, not reopen gateway, task-assignment, or citation-manifest surfaces.
- Article parse should emit section/paragraph locators.
- PDF parse should emit page/paragraph locators and parse-confidence signals.
- Evidence normalization should preserve Lane H fetch truth such as artifact identity, canonical URL, content hash, and coverage.
- Claim-scoped anchored citation flow stays out of scope for this lane.
- One thin internal post-E bridge is still needed later before the article/PDF retrieval layer is usable end-to-end on the canonical research path.

## Authority Order

If any lower-order file conflicts with a higher-order file, the higher-order file wins.

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
4. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
5. `CURRENT-STATE.md`
6. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
7. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
8. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
9. `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
10. `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
11. `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
12. `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`
13. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md`
14. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md`
15. `audit/remediation/retrieval-parse/WORKSTREAM-HANDOFF.md`
16. `audit/remediation/retrieval-parse/NEW-LANE-SETUP-ARTIFACT.md`
17. `audit/remediation/retrieval-parse/ALLOWED-WRITE-SET.md`
18. `audit/remediation/retrieval-parse/REVIEW-AND-GATE-CHECKLIST.md`
19. `audit/remediation/retrieval-parse/LANE-CHOICE-RATIONALE.md`
20. `audit/remediation/retrieval-parse/SESSION-PROMPTS.md`
21. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
22. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
23. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`
24. `graphify-out/GRAPH_REPORT.md`

Items 15 through 20 are the live narrow Lane E package.
For live Lane E scope, boundary, and ownership questions, those package docs outrank items 21 through 24.
The three broader Retrieval MVP docs remain useful only as subordinate future-state design references and may not be used to widen live Lane E into filings, papers, `EvidenceBundle`, `AnchoredCitation`, retrieval-coordinator work, Lane F integration, SEC / EDGAR, or benchmark / acceptance scope.

## Staleness And Subordination Fence

These older or broader docs may be useful as historical or future-state context, but they are non-authoritative for live Lane E boundary decisions if they imply Lane H is still pending, Lane D fetch is still next, or broad Retrieval MVP scope is already authorized:

- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`

- `audit/remediation/WORKSTREAM-STATUS.md`
- `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md`
- `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
- `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`

Use the three Retrieval MVP design docs only for future-state design intent, never for live Lane E authority.
If they conflict with this narrow Lane E package on source-family scope, `document_fetch` ownership, retrieval-coordinator work, citation-schema migration, Lane F ownership, SEC / EDGAR, or benchmark / acceptance scope, this package wins.
Use the remaining stale docs only for historical intent, never for live lane authority.

## Package Map

- `WORKSTREAM-HANDOFF.md`: lane boundary, authority order, and stale-doc fence
- `NEW-LANE-SETUP-ARTIFACT.md`: exact narrow Lane E setup definition
- `ALLOWED-WRITE-SET.md`: exact future runtime write set and denylist
- `REVIEW-AND-GATE-CHECKLIST.md`: promotion checks, candidate packet, and stop conditions
- `LANE-CHOICE-RATIONALE.md`: why narrow Lane E is next and why it still needs a thin post-E bridge later
- `SESSION-PROMPTS.md`: exact next review, promotion, implementation, and follow-on prompts

## Notes For The Next Session

- Treat Lane H as closed and frozen for coding unless a later controller says otherwise.
- Treat claim-scoped citation anchors as Lane F work, not Lane E work.
- Treat evidence normalization in Lane E as parse-local normalized passages, not as final downstream citation schema.
- If Lane E requires a denied path, stop and return to the controller instead of stretching the lane.
