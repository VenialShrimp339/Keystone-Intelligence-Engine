# Retrieval Tool-Surface Workstream Handoff

Date: 2026-04-13  
Controller mode: docs-only authority-expansion design  
Authoritative anchors: `65a612d` retrieval MVP docs, `candidate-f1af7df` review packet, and `LANE-D-AUTHORITY-RESOLUTION.md`

## Mission

Authorize the missing lane that owns article/PDF canonical fetch tool-surface expansion without:

- pretending the blocked Lane D packet already had that authority
- silently shrinking Retrieval MVP
- entangling the separate SEC venue problem with the tool-surface decision

## Hard Guardrails

- Article/PDF canonical fetch remains Retrieval MVP-critical.
- The current Lane D answer on a registry-only callable `document_fetch` is still `NO`.
- Do not reopen Retrieval Lane D coding from candidate `f1af7df` in this session.
- Keep the SEC `403` venue issue separate from article/PDF tool-surface authority.
- The main workspace remains docs-only for this controller packet.
- `f1af7df` is evidence and reference material, not a promotable base candidate.

## Executive Judgment

- The blocked Lane D packet proved a real gap in the authority stack, not a reason to narrow MVP.
- The correct next move is a fresh controller-approved lane that owns cross-layer tool-contract expansion.
- The recommended shape is not "make `document_fetch` another ordinary task-assigned tool."
- The recommended shape is a richer canonical tool-definition contract in which:
  - `exa_search` and `brave_search` stay task-assignable and discovery-only
  - `document_fetch` becomes a system-owned canonical fetch surface for article/PDF retrieval
  - `document_fetch` is registered and audited, but not valid inside `ResearchTask.assigned_tools`
  - `edgar_filings` remains the SEC-specific surface and the SEC venue issue remains a later separate review
  - `paper_search` and `doi_verify` remain the paper-specific path and are not the blocker this lane is solving

## Why This Must Be A New Lane

The current blocked state is cross-layer, not fetch-local:

- `src/keystone/tool_names.py` is the single source of truth for tool identifiers.
- `src/keystone/specification/prompts/task_generation.md` hardcodes the exact assignable tool list.
- `src/keystone/specification/task_generator.py` filters LLM output against the registered tool set.
- `src/keystone/models/tasks.py` currently enforces tool count but not membership semantics.
- `src/keystone/gateway/auth.py` and registry behavior make registry changes authorization-significant.

That means article/PDF fetch authority cannot be reopened honestly inside the old Lane D write set.

## Status Of `f1af7df`

Official disposition: `SUPERSEDED_BY_FRESH_IMPLEMENTATION_LANE`

Implications:

- Freeze `f1af7df` as a blocked checkpoint.
- Do not patch it forward under the old Lane D authority.
- It may be consulted as reference-only evidence for article/PDF fetch mechanics after the new lane is cleared.
- Its SEC probe outcome stays recorded, but that venue question is not the design driver for this package.

## Recommended New Lane

Recommended name: `Lane H - Retrieval Tool-Surface Authority Expansion`

Lane H owns:

- the canonical tool-definition contract for task-assignable versus system-owned surfaces
- the new system-owned `document_fetch` contract for article/PDF canonical fetch
- the prompt, task-generator, task-model, registry, and auth changes required to prevent task-surface leakage
- the clean worktree and review packet needed to prove article/PDF fetch without re-litigating SEC in the same decision

Lane H does not own:

- SEC venue remediation
- parser lane work
- L1 integration and evidence-bundle migration
- citation anchoring migration
- Retrieval MVP scope reduction

## Package Map

- [AUTHORITY-EXPANSION-DECISION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md)
- [NEW-LANE-SETUP-ARTIFACT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md)
- [ALLOWED-WRITE-SET.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md)
- [TOOL-CONTRACT-CHANGES.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md)
- [CONTROL-PLANE-PROMOTION-CHECKLIST.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/CONTROL-PLANE-PROMOTION-CHECKLIST.md)
- [SESSION-PROMPTS.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/retrieval-tool-surface/SESSION-PROMPTS.md)

## Controller Notes For The Next Session

- Treat article/PDF canonical fetch as still required for Retrieval MVP.
- Treat `document_fetch` as a contract-design question first, not a local registry patch.
- Require proof that system-owned surfaces cannot leak into task assignment.
- Keep every SEC statement explicitly labeled as venue-specific and not evidence for or against the article/PDF contract shape.
