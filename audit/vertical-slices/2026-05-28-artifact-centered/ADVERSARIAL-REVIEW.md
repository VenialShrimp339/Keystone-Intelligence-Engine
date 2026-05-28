# Adversarial Review

Date: 2026-05-28

## Reviewed Surface

- Issue-tree skill eval and patch.
- `IssueTreePackage` schema and task bridge.
- Browser provider ledger/watcher/export adapter.
- Fixture-backed Permira/Squarespace artifact-centered vertical slice.

## Keep

- Keep `IssueTreePackage` as the specification-stage artifact. It captures the missing state the legacy `IssueTree` could not represent: frame, candidate axes, selected-axis rationale, full/pruned trees, sibling logic, pruning decisions, approval, quality gates, and executable leaves.
- Keep the deterministic approved-leaf bridge into `ResearchTask.issue_tree_branch_id`. This is the right contract boundary: issue-tree approval controls research dispatch, while the existing task machinery remains useful.
- Keep the provider ledger separate from report ingestion. Provider truth and evidence ingestion are different state machines, and the ledger preserves URLs, DOM signals, export paths, and ingestion state.
- Keep ChatGPT's Markdown plus DOCX source-link route until a live Markdown export includes real source URLs.
- Keep Claude's artifact/report export route.
- Keep the fixture controller harness. It gives repeatable tests for provider state transitions without spending live provider runs.

## Change

- Replace the fixture controller with a live Chrome/plugin-backed `BrowserProviderController`. The current adapter is real control-plane code, but the vertical slice did not drive the logged-in provider UI.
- Add provider preflight handling. ChatGPT Deep Research can ask clarifying questions or source-scope confirmations before launching, and those need HITL or pre-approved defaults.
- Move source URL reconciliation from provider ledger metadata into the combined evidence bundle. The current ingestion recovers Markdown URLs; live ChatGPT should reconcile DOCX-derived URLs against opaque Markdown citations.
- Add branch-aware synthesis. The current deliverable is traceable and passes deterministic checks, but it is a thin evidence brief rather than a consultant-grade synthesis by branch.
- Add approval artifact rendering for `IssueTreePackage`. The package exists as JSON, but operators need a reviewable issue-tree approval view before dispatch.

## Defer

- Full replacement of the legacy `Decomposer`. Keep it as a fallback until live multi-branch provider runs prove the package-builder path.
- Provider ledger UI. The JSON ledger is enough for the first slice; UI becomes useful once live jobs run for minutes across multiple branches.
- Exact DOCX source-link parsing in core adapter. The live probe proved the route, but this slice used a placeholder DOCX path plus Markdown URLs. The parser should be added when the live controller exports real files.
- Cost and quota policy. Needed before broad waves, not needed for the first deterministic slice.

## Delete Or Avoid

- Avoid dispatching research directly from the full tree. Only approved pruned `leaf_tasks[]` should launch expensive provider jobs.
- Avoid treating provider-native notifications as truth. They remain UX only; the Keystone watcher and ledger own truth.
- Avoid claiming live autonomous provider operation from this slice. This run used a fixture controller and completed local reports; live Chrome automation is the next hardening step.

## Verification

- Focused changed-surface tests: 32 passed.
- Touched-file ruff check: passed.
- Vertical slice evaluation: passed, score 1.0, with 22 extracted claims, 8 sources, and 14 traceable evidence-map entries.
- Full pytest: first failure is `tests/e2e/test_mock_pipeline.py::test_mock_pipeline_end_to_end`; governance halts because mock research agents produce zero claims for primary tasks. The full run was also long-running until killed once, then rerun with `-x` to capture this failure. This is outside the artifact-centered slice surface but remains a broader repo risk.
- Graphify rebuild: attempted with repo venv and host Python; both failed because `graphify` is not importable in this environment.
