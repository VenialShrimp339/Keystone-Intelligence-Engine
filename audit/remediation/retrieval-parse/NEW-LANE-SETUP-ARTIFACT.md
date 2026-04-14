# Retrieval Parse Setup Artifact

Date: 2026-04-14
Status: controller-authored setup candidate for narrow post-Lane-H parser work

## What This File Is For

This file defines the setup for the next runtime lane that may reopen article/PDF retrieval work honestly after Lane H.

Lane H already cleared governed article/PDF fetch and the `document_fetch` authority boundary.
This artifact does not re-decide that work.
It defines the narrow parser lane that may start from that cleared seam.

This artifact is subordinate to the live control plane.
If a later promoted control-plane file conflicts with this document, the promoted control-plane file wins.
For live Lane E boundary questions, this setup artifact and the rest of the narrow retrieval-parse package outrank the broader Retrieval MVP design docs.
Those broader docs remain future-state design references only and may not widen Lane E into filings, papers, `EvidenceBundle`, `AnchoredCitation`, retrieval-coordinator work, Lane F, SEC / EDGAR, or benchmark acceptance.

## Read First

Before opening this lane, read:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-BOOTSTRAP.md`
4. `audit/remediation/control-plane/FRESH-ORCHESTRATOR-SESSION-PROMPT.md`
5. `CURRENT-STATE.md`
6. `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
7. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
8. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
9. `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
10. `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`
11. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-review-synthesis.md`
12. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface/audit/remediation/runs/retrieval-tool-surface/candidate-93a5ca8-blocked-or-cleared-checkpoint.md`
13. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
14. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
15. `graphify-out/GRAPH_REPORT.md`

## Activation Block

- last cleared code anchor: `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea`
- authoritative runtime baseline: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` at `93a5ca8`
- planned implementation branch: `codex/retrieval-mvp-parse`
- planned implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-parse`
- planned review packet root: `audit/remediation/runs/retrieval-parse/`
- main workspace policy: docs-only
- lane purpose: deterministic parse and evidence normalization for article/PDF only

## Current-Code Anchors

The new lane exists because the cleared runtime now has these properties:

1. Lane H proved real governed article/PDF fetch through system-owned `document_fetch`.
2. The cleared fetch seam already records persisted raw artifact identity, canonical URL, redirect chain, MIME type, content hash, coverage, and audit metadata.
3. The cleared Lane H proof still stops at raw fetched artifacts and reports `citation_count=0`.
4. The current research path remains query-shaped and snippet-shaped downstream, which is explicitly not what Lane E is allowed to change.
5. The current citation stack remains document-scoped, so claim-scoped anchored citations are still a later schema migration risk.

## Binding Scope In

This lane may own only the following slice:

1. Load persisted Lane H article/PDF artifacts from the frozen fetch seam.
2. Add parse-local models for deterministic article/PDF parse output.
3. Parse article HTML into reproducible section/paragraph passages.
4. Parse PDFs into reproducible page/paragraph passages with parse-confidence signals.
5. Emit explicit parse warnings and degraded outcomes rather than inventing unsupported text.
6. Normalize parsed passages into a source-shaped evidence-prep output that preserves:
   - `artifact_id`
   - `canonical_url`
   - `content_hash`
   - `coverage`
   - `source_family`
   - parser identity
   - locator
   - parse confidence when available
7. Produce a review packet that proves article/PDF parse is deterministic, source-shaped, and still downstream of Lane H.

## Binding Scope Out

The following remain out of scope:

1. SEC / EDGAR
2. papers / DOI
3. any change to `document_fetch` ownership, request shape, response shape, or task-assignability rules
4. any change to gateway, auth, registry, task-generation, or task-validation semantics
5. any change to claim-scoped citation schema, `CitationManifest`, or canonical citation dedup flow
6. any change to `ResearchAgent`, orchestrator, renderer, deliberation, evaluator, or knowledge surfaces
7. any public tool surface for parse
8. UI work
9. benchmark acceptance claims
10. control-plane edits outside a later explicit promotion step

## Hard Contract Rule

This lane may not:

- reopen Lane H fetch authority
- change `document_fetch` into an assignable tool
- require task-generation or gateway changes
- treat parse-local locators as the final anchored-citation contract
- sneak `EvidenceBundle`, `AnchoredCitation`, or downstream synthesis changes into the parser lane

Lane E must prove all of the following:

- it parses only from cleared Lane H artifact inputs
- it keeps article/PDF parse deterministic and reproducible without LLM help
- it preserves source-shaped metadata from the fetched artifact
- it leaves Lane H and Lane F boundaries intact

## Hard Output Boundary

The only new runtime output surfaces this lane may create are parse-local article/PDF outputs and normalized evidence-prep records.

Required output characteristics:

- article passages carry section/paragraph locators
- PDF passages carry page/paragraph locators
- PDF outputs retain parse-confidence signals
- every normalized passage retains upstream artifact identity and canonical URL
- warnings and degraded coverage remain explicit

This lane must not introduce:

- filing locators
- paper abstract/body workflows
- `EvidenceBundle` as the downstream L1 contract
- `AnchoredCitation`
- `CitationManifest` changes
- claim-level citation rewrites

## Exact Allowed Write Set

The future implementation lane is limited to `audit/remediation/retrieval-parse/ALLOWED-WRITE-SET.md`.

If any required change falls outside that file, stop and return to the controller.

## Required Test Matrix

At minimum, a future candidate must run:

1. `tests/unit/retrieval/test_parse_models.py`
2. `tests/unit/retrieval/test_artifact_loader.py`
3. `tests/unit/retrieval/test_article_parser.py`
4. `tests/unit/retrieval/test_pdf_parser.py`
5. `tests/unit/retrieval/test_evidence_normalizer.py`

If `pyproject.toml` changes to add a parser dependency, include targeted dependency-load coverage and record the exact reason in the run packet.

## Required Review Packet

The review packet under `audit/remediation/runs/retrieval-parse/` must include at minimum:

- `candidate-<sha>-implementation.md`
- `candidate-<sha>-file-manifest.md`
- `candidate-<sha>-parse-truth-matrix.md`
- `candidate-<sha>-deterministic-parse-review.md`
- `candidate-<sha>-evidence-normalization-review.md`
- `candidate-<sha>-adversarial-review.md`
- `candidate-<sha>-second-opinion.md`
- `candidate-<sha>-review-synthesis.md`
- `candidate-<sha>-blocked-or-cleared-checkpoint.md`
- `parse-probe-results.json`

## Clearance Standard

This lane is clearable only if:

- article parse is real and deterministic from persisted artifacts
- PDF parse is real and deterministic from persisted artifacts
- source-shaped locators are explicit and reproducible
- parse confidence is explicit where parse quality is uncertain
- normalized outputs preserve Lane H artifact truth
- no reviewer has to infer whether Lane H or Lane F was reopened

## Bridge Note

Even a cleared Lane E does not by itself authorize a claim that the full article/PDF retrieval layer is usable end-to-end on the canonical research path.
A later thin internal bridge is still needed to connect cleared fetch plus parse outputs into a usable selected-passage handoff without opening full Lane F.
