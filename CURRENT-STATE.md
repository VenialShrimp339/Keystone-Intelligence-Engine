# Current State

*Last updated: 2026-05-28 | Updated by: Codex repo-cleanup pass*

> Summary-only current-truth layer. For live authority, start with `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair.

## Live Status

- The active product direction is now the artifact-centered, subscription-first Keystone research rebuild captured in `notes/OWNER-VISION-2026-05-24.md`, `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`, `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`, and `audit/roadmap/JULY-27-EXECUTION-PLAN.md`.
- Keystone remains a spec-driven, issue-tree-based consulting research system. The DPVI spine is preserved: decompose, parallelize, verify, iterate.
- The prior April remediation control plane that pointed at Lane E retrieval-parse is historical provenance only for current planning. It no longer describes the active next action for this worktree.
- The old Claude CLI-first runtime doctrine is stale. The target runtime is subscription-first provider routing: Codex CLI for structured local calls, ChatGPT web Deep Research as primary hosted research, Claude web Research as secondary/cross-check research, manual upload as fallback, deterministic public-source connectors where precision matters, and API only as fallback/control.
- The issue-tree/problem-decomposition skill has a prototype package at `.agents/skills/problem-decomposition/`, with derived methodology, references, output contract, eval strategy, and KIE adapter notes under `audit/issue-tree-skill/`.
- The issue-tree skill is prototype-ready for further eval. Direct KIE runtime integration should wait until the recommended book-derived and novel stress-test eval subset passes and a Pydantic `IssueTreePackage` is implemented.
- First-slice artifact/report ingestion and provider completion detection exist under `src/keystone/artifacts/`, `src/keystone/ingestion/`, and `src/keystone/providers/`.
- Claude web Research full lifecycle is proven for the public auto-body consolidation probe and was ingested into durable artifacts.
- ChatGPT web Deep Research full lifecycle is now proven for the same public probe: completed report capture, Markdown export, Word export, source-link recovery, normalized report creation, and provider-neutral ingestion all succeeded.
- ChatGPT export nuance: native Markdown preserved opaque citation markers, while native Word exposed the actual source URLs. The near-term browser adapter should treat ChatGPT as a body-plus-source export workflow when citation fidelity matters.
- External presentation drafts (`keystone-class-presentation.md`, `keystone-class-presentation.pptx`) exist in the worktree but are locally excluded from Git status. Preserve them; they are unrelated to the KIE source checkpoint.

## What Happens Next

1. Evaluate the problem-decomposition skill on the recommended book-derived and novel stress-test subset.
2. Implement a Pydantic `IssueTreePackage` upstream of the current `Decomposer`, then map approved `leaf_tasks[]` into the existing task generator.
3. Build the browser provider adapter around the proven lifecycle: tab registry, export-ready detection, ChatGPT Markdown+DOCX export, Claude artifact export, provider ledger, blocked-state pause, and per-provider concurrency controls.
4. Build the first artifact-centered vertical slice: messy request, problem frame, issue tree, approval artifact, provider reports, evidence bundle, synthesis brief, light evaluation, cited brief.
5. Only after that slice works, build the multi-branch provider prototype with branch-level ChatGPT/Claude/manual jobs, completion monitoring, evidence-to-branch mapping, gap detection, and next-wave recommendation.

## Current Key Artifacts

- Owner vision: `notes/OWNER-VISION-2026-05-24.md`
- Repo baseline: `audit/mega-goal/00-repo-baseline.md`
- Architecture preservation audit: `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`
- Provider feasibility: `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`
- Artifact contracts: `audit/contracts/ARTIFACT-CONTRACTS.md`
- July plan: `audit/roadmap/JULY-27-EXECUTION-PLAN.md`
- First vertical slice: `audit/roadmap/first-vertical-slice-spec.md`
- Issue-tree skill handoff: `audit/issue-tree-skill/handoff/HANDOFF.md`
- Portable issue-tree skill: `.agents/skills/problem-decomposition/SKILL.md`

## Fresh-Session Read Order

1. `AUTHORITY-INDEX.md`
2. `SESSION-STANDARD.md`
3. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
4. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
5. `FOUNDER-INTENT-DOCTRINE.md`
6. `CURRENT-STATE.md`
7. `notes/OWNER-VISION-2026-05-24.md`
8. `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`
9. `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`
10. `audit/issue-tree-skill/handoff/HANDOFF.md`
11. `audit/roadmap/JULY-27-EXECUTION-PLAN.md`
12. `SESSION-LOG.md` only if historical rationale is needed

## Historical Notes

- Historical implementation remains cleared through Wave 4B at `65a612d`.
- Lane H commit `93a5ca8406dc0c46c96f0c6285f56ec0ab6601ea` remains useful as the prior governed article/PDF retrieval anchor, but it is not the active next action.
- Lane E retrieval-parse package promotion remains provenance for the old remediation path, not the current product-rebuild priority.
- `SESSION-LOG.md` is provenance-only history, not the complete live chronology.
