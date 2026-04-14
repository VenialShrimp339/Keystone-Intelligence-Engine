# Retrieval Tool-Surface Authority Expansion Setup Artifact

Date: 2026-04-13  
Status: controller-authored setup candidate for a fresh post-Lane-D authority-expansion lane

## What This File Is For

This file defines the setup for the next runtime lane that may reopen article/PDF canonical fetch honestly.

It exists because the old Lane D authority package was fetch-local and did not own cross-layer tool-contract expansion.

This artifact is subordinate to the live control plane. If any later promoted control-plane file conflicts with this document, the promoted control-plane file wins.

This artifact does not itself promote the lane. It defines what would need to be promoted.

## Read First

Before opening this lane, read:

1. `audit/remediation/retrieval-mvp/MVP-RETRIEVAL-REQUIREMENTS.md`
2. `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
3. `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`
4. `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md`
5. `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md`
6. `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
7. `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md`
8. `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
9. `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
10. `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
11. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md`
12. `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md`
13. `graphify-out/GRAPH_REPORT.md`

## Activation Block

- last cleared code anchor: `65a612dc1400abbedcfbdda1f173cd72a3a90c06`
- authoritative runtime baseline: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`
- planned implementation branch: `codex/retrieval-tool-surface`
- planned implementation worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
- planned review packet root: `audit/remediation/runs/retrieval-tool-surface/`
- main workspace policy: docs-only
- lane purpose: tool-surface authority expansion for article/PDF canonical fetch

## Current-Code Anchors

The new lane exists because the current runtime still has these properties:

1. `src/keystone/tool_names.py` treats tool names as a flat authoritative set.
2. `src/keystone/specification/prompts/task_generation.md` enumerates the exact seven assignable tools and forbids inventing others.
3. `src/keystone/specification/task_generator.py` filters LLM tool output against that flat registered set.
4. `src/keystone/models/tasks.py` enforces assigned-tool count but does not enforce membership in an explicit task-assignable subset.
5. `src/keystone/gateway/auth.py` plus registry behavior makes new registered surfaces authorization-significant.
6. Candidate `f1af7df` proved that a registry-only `document_fetch` addition creates cross-layer drift even before SEC enters the picture.

## Binding Scope In

This lane may own only the following slice:

1. Replace the flat tool-name contract with a richer canonical tool-definition contract.
2. Add `document_fetch` to that source of truth as a system-owned, non-task-assignable surface.
3. Limit `document_fetch` to article/PDF canonical fetch.
4. Define the request and response contract for `document_fetch`.
5. Update prompt, task-generator, task-model, registry, and auth surfaces so `document_fetch` cannot leak into `ResearchTask.assigned_tools`.
6. Register and implement governed article/PDF fetch through the new surface.
7. Extend audit and tests so task-surface leakage becomes a hard failure.
8. Produce a review packet that proves:
   - article fetch is real
   - PDF fetch is real
   - `document_fetch` is absent from task assignment surfaces
   - SEC was not silently reinterpreted

## Binding Scope Out

The following remain out of scope:

1. SEC venue troubleshooting or environment workarounds
2. changes to `edgar_filings` behavior beyond compatibility-preserving no-op adjustments
3. changes to `paper_search` or `doi_verify` semantics
4. research-agent, orchestrator, or broader L1 integration
5. parser lane work
6. evidence-bundle and citation-anchor schema work
7. benchmark acceptance claims
8. Retrieval MVP scope reduction
9. `DEEP_RESEARCH=1` equivalence claims
10. control-plane edits outside the later explicit promotion step

## Hard Contract Rule

This lane may not treat `document_fetch` as another ordinary task tool.

It must prove all of the following:

- task generation still assigns only the intended task-assignable tools
- `document_fetch` is callable only through a system-owned path
- registry presence alone does not imply task assignability
- a real article/PDF fetch backend can exist without silently widening L1 authority

## Hard Output Boundary

The only new runtime output surface this lane may create is canonical fetch output for article/PDF retrieval:

- canonical URL
- redirect chain
- MIME type
- content hash
- persisted raw artifact identity
- access timestamp
- coverage outcome
- gateway audit record

This lane must not introduce:

- parser output
- section anchors
- page passage ranking
- evidence bundles
- citation locators
- synthesis changes

## Exact Allowed Write Set

The future implementation lane is limited to [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md).

If any required change falls outside that file, stop and return to the controller.

## Required Test Matrix

At minimum, a future candidate must run:

1. `tests/unit/gateway/test_auth.py`
2. `tests/unit/gateway/test_gateway.py`
3. `tests/unit/gateway/test_tool_registry.py`
4. `tests/unit/specification/test_task_generator.py`
5. `tests/unit/test_auth.py`
6. `tests/unit/test_audit_log.py`
7. `tests/unit/test_gateway.py`
8. `tests/unit/test_research_models.py`
9. `tests/unit/test_tool_registry.py`

If `src/keystone/models/research.py` changes, add targeted model coverage for the new DTOs.

## Required Review Packet

The review packet under `audit/remediation/runs/retrieval-tool-surface/` must include at minimum:

- `candidate-<sha>-implementation.md`
- `candidate-<sha>-file-manifest.md`
- `candidate-<sha>-backend-truth-matrix.md`
- `candidate-<sha>-tool-contract-review.md`
- `candidate-<sha>-live-fetch-review.md`
- `candidate-<sha>-adversarial-review.md`
- `candidate-<sha>-second-opinion.md`
- `candidate-<sha>-review-synthesis.md`
- `candidate-<sha>-blocked-or-cleared-checkpoint.md`
- `live-probe-results.json`

## Clearance Standard

This lane is clearable only if:

- article and PDF fetch have real governed proof
- no system-only tool leaks into task assignment
- the review packet explicitly keeps SEC unclaimed or separately classified
- no reviewer has to infer the assignable versus system-owned distinction from scattered files
