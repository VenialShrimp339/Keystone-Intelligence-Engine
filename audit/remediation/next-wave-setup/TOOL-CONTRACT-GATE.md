# Tool Contract Gate

Date: 2026-04-13  
Gate scope: docs-only promotion review of the corrected next-wave setup package

## Record

- Reviewer: `codex-gpt-5.4-xhigh-main-controller`
- Reviewed snapshot: corrected `audit/remediation/next-wave-setup/` working-tree snapshot dated `2026-04-13`, anchored to runtime truth `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`
- Approved setup artifact path: `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- Verdict: `CLEARED`

## Evidence Inputs

- `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-mvp/MVP-RETRIEVAL-REQUIREMENTS.md`
- `audit/remediation/retrieval-mvp/ARCHITECTURE-DECISIONS.md`
- `audit/remediation/retrieval-mvp/RETRIEVAL-MVP-SEAM-CONTRACT.md`
- `audit/remediation/retrieval-mvp/IMPLEMENTATION-LANES.md`

## Judgment

This corrected package now keeps the tool contract honest:

- Exa and Brave remain discovery-only on the canonical path
- canonical evidence must come from fetch surfaces, not search snippets
- tool-assignment changes through allowed files are explicitly classified as blocked L1 integration scope creep
- `src/keystone/tool_names.py` is fenced out of Lane D so the lane cannot quietly rewrite shared tool grouping or default assignment behavior
- parser and L1 integration work remain blocked rather than being smuggled through fetch-labeled changes

This gate clearing does not claim the runtime already satisfies the typed retrieval contract. It means the setup package now preserves the contract boundary a later implementation lane must honor.

## Reopen Rule

Reopen this gate if the setup artifact or allowed-write-set doc starts allowing tool-assignment changes, shared group rewrites, or snippet-as-evidence behavior.
