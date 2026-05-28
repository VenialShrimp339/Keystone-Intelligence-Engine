# Current State

*Last updated: 2026-05-28 | Updated by: Codex artifact-centered autonomous slice*

> Summary-only current-truth layer. For live authority, start with `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair.

## Live Status

- The active product direction is now the artifact-centered, subscription-first Keystone research rebuild captured in `notes/OWNER-VISION-2026-05-24.md`, `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`, `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`, and `audit/roadmap/JULY-27-EXECUTION-PLAN.md`.
- Keystone remains a spec-driven, issue-tree-based consulting research system. The DPVI spine is preserved: decompose, parallelize, verify, iterate.
- The prior April remediation control plane that pointed at Lane E retrieval-parse is historical provenance only for current planning. It no longer describes the active next action for this worktree.
- The old Claude CLI-first runtime doctrine is stale. The target runtime is subscription-first provider routing: Codex CLI for structured local calls, ChatGPT web Deep Research as primary hosted research, Claude web Research as secondary/cross-check research, manual upload as fallback, deterministic public-source connectors where precision matters, and API only as fallback/control.
- The issue-tree/problem-decomposition skill has now passed the recommended baseline-vs-skill eval gate. It won 11 of 13 cases, tied 2, had no catastrophic failures, and was patched for compact pruning plus explicit decision maker/R1/R2/constraints.
- A Pydantic `IssueTreePackage` now exists upstream of the legacy `Decomposer` in `src/keystone/specification/issue_tree_package.py`. Approved `leaf_tasks[]` bridge deterministically into existing `ResearchTask` records through `TaskGenerator.generate_from_issue_tree_package`.
- First-slice artifact/report ingestion, provider completion detection, provider ledgering, browser-provider orchestration, and artifact-centered slice execution exist under `src/keystone/artifacts/`, `src/keystone/ingestion/`, and `src/keystone/providers/`.
- The first realistic artifact-centered vertical slice ran on a public Permira/Squarespace PE diligence prompt. It produced an approved issue-tree package, branch prompts, fixture-backed provider jobs, provider ledger, two ingested reports, combined evidence bundle, evaluation, and cited Markdown deliverable.
- Claude web Research full lifecycle is proven for the public auto-body consolidation probe and was ingested into durable artifacts.
- ChatGPT web Deep Research full lifecycle is now proven for the same public probe: completed report capture, Markdown export, Word export, source-link recovery, normalized report creation, and provider-neutral ingestion all succeeded.
- ChatGPT export nuance: native Markdown preserved opaque citation markers, while native Word exposed the actual source URLs. The near-term browser adapter should treat ChatGPT as a body-plus-source export workflow when citation fidelity matters.
- External presentation drafts (`keystone-class-presentation.md`, `keystone-class-presentation.pptx`) exist in the worktree but are locally excluded from Git status. Preserve them; they are unrelated to the KIE source checkpoint.

## What Happens Next

1. Replace the fixture controller in the vertical slice with a live Chrome controller or plugin-backed controller that can submit and export ChatGPT/Claude jobs under logged-in browser sessions.
2. Harden provider export handlers around real ChatGPT Markdown+DOCX downloads and Claude artifact/report export, including source URL reconciliation.
3. Promote the artifact-centered slice from local harness to orchestrated multi-branch prototype with provider-job scheduling, completion monitoring, branch evidence mapping, gap detection, and next-wave recommendation.
4. Add a UI or review artifact for approving `IssueTreePackage` leaves before expensive provider dispatch.
5. Decide whether the legacy `Decomposer` remains a fallback path, is wrapped by the skill package builder, or is retired for artifact-centered flows.

## Current Key Artifacts

- Owner vision: `notes/OWNER-VISION-2026-05-24.md`
- Repo baseline: `audit/mega-goal/00-repo-baseline.md`
- Architecture preservation audit: `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`
- Provider feasibility: `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`
- Artifact contracts: `audit/contracts/ARTIFACT-CONTRACTS.md`
- July plan: `audit/roadmap/JULY-27-EXECUTION-PLAN.md`
- First vertical slice: `audit/roadmap/first-vertical-slice-spec.md`
- Issue-tree skill handoff: `audit/issue-tree-skill/handoff/HANDOFF.md`
- Issue-tree eval report: `audit/issue-tree-skill/evals/runs/2026-05-28-autonomous-slice/EVAL-REPORT.md`
- IssueTreePackage schema: `src/keystone/specification/issue_tree_package.py`
- Browser provider adapter: `src/keystone/providers/browser_provider.py`
- First artifact-centered vertical slice run: `audit/vertical-slices/2026-05-28-artifact-centered/run/result.json`
- First artifact-centered cited deliverable: `audit/vertical-slices/2026-05-28-artifact-centered/run/artifact-store/sqsp-permira-artifact-slice/files/deliverables/synthesis-evidence-combined-sqsp-permi-ef1d530508.md`
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
