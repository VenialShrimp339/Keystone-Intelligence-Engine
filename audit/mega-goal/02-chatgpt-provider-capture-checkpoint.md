# ChatGPT Provider Capture Checkpoint

Timestamp: 2026-05-28T14:23:35-0500
Agent/runtime: Codex GPT-5
Worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization`
Branch: `codex/owner-triage-normalization`
Start commit: `48544b131d18f2a3c145db7cb0839313e5d2724b`

## Scope

Finish the live ChatGPT Deep Research lifecycle probe that had been left completed in Chrome but not durably captured. Preserve completion evidence, export the report, recover source URLs, and ingest the completed report through the same provider-neutral artifact path used for Claude.

## Evidence Inputs

- Conversation URL: `https://chatgpt.com/c/6a137bbc-82d0-83ea-a457-fbfa6d56e3de`
- Prompt: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-submitted-prompt.txt`
- Completion screenshot: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-completed-report-fullpage.png`
- Native Markdown export: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-completed-report.md`
- Native Word export: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-completed-report.docx`
- Normalized ingestion report: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-completed-report-normalized-with-sources.md`
- Source-link extraction: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/chatgpt-live-completed-report-source-links.json`
- Ingested ledger: `audit/provider-feasibility/artifacts/live-probe-2026-05-24/ingested-artifacts/live-provider-probe-2026-05-24-chatgpt/run-ledger.json`

## Observed Provider Behavior

- ChatGPT completed the report with the banner `Research completed in 17m · 10 citations · 246 searches`.
- The report export menu exposed `Copy contents`, `Export to Markdown`, `Export to Word`, and `Export to PDF`.
- Markdown export succeeded and preserved the report body.
- Markdown export did not expose actual source URLs. It preserved opaque ChatGPT citation markers.
- Word export succeeded and exposed ten actual source URLs in the DOCX relationship/document XML.
- Copy controls returned an empty clipboard through the current browser automation path and should not be treated as the primary export route.

## Ingestion Result

Run id: `live-provider-probe-2026-05-24-chatgpt`

Artifacts created:

- `ProviderJobArtifact`: `provider-job-live-provider-probe-2026-05-cd935ef776`
- `ResearchReportArtifact`: `report-live-provider-probe-2026-05-c0589cac5e`
- `SourceBundleArtifact`: `sources-report-live-provider-probe-2-26d5c838ef`
- `EvidenceBundleArtifact`: `evidence-report-live-provider-probe-2-26d5c838ef`
- `SynthesisArtifact`: `synthesis-report-live-provider-probe-2-26d5c838ef`
- `EvaluationArtifact`: `evaluation-evidence-report-live-provide-c25563318d`
- `DeliverableArtifact`: `deliverable-live-provider-probe-2026-05-33e175c221`

Counts:

- Sources: 10
- Candidate claims: 24
- Cited claims: 11
- Citation-gap flags: 13
- Local deterministic evaluation: 4/4 checks passed, score `1.0`

## Verdict

ChatGPT web Deep Research is now proven through full lifecycle: submit, run, complete, export, source-link recovery, normalization, and local provider-neutral ingestion.

The adapter design should encode a ChatGPT-specific export policy: use Markdown for body structure and DOCX for source URL recovery unless a future export route exposes source URLs directly in Markdown.

## Follow-On Action

Run the issue-tree skill eval subset, implement `IssueTreePackage` upstream of `Decomposer`, then build the browser provider adapter and first artifact-centered vertical slice.
