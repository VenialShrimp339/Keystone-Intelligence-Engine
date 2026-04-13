# Repo Hygiene Inventory

Date: 2026-04-13
Scope: docs-only inventory pass; no cleanup executed
Workspace: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`

## Snapshot

- Control-plane state says the main workspace is docs-only and hard-stopped for forward code work until a later authority artifact exists.
- Current working branch is `codex/remediation-program`.
- `git status --short` at inventory time was `24 M`, `120 D`, `93 ??`, and `1 m` (`reference/nano-claude-code`).
- `git ls-files --others --exclude-standard | wc -l` returned `717`, so the visible untracked set is much larger than the top-level `??` count suggests.
- Dominant pattern: unfinished docs/archive reorganization layered on top of real runtime/test/schema edits, generated artifacts, local tool state, and worktree sprawl.

## Category: Authoritative Docs / Control-Plane Material

These should stay in place and should not be part of any cleanup move or delete pass.

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- `audit/remediation/control-plane/EXECUTION-TODO.md`
- `CURRENT-STATE.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `audit/remediation/WAVE-4B-SETUP.md`
- `audit/remediation/runs/wave-4b/`
- Tracked retrospective review packets already in `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/`

Authority-adjacent docs that look live, not archival:

- `audit/remediation/README.md`
- `audit/remediation/CHECKPOINT-INSTRUCTIONS.md`
- `audit/remediation/MASTER-REMEDIATION-PLAN.md`
- `audit/remediation/workstream-retro/reviews/CP-FIX-authority-normalization-spec.md`
- `audit/remediation/workstream-retro/reviews/RP-FIX-packet-normalization-spec.md`

## Category: Active Workstream Docs

These look like active or recently active planning/workstream material and should stay until explicitly retired.

- `audit/remediation/retrieval-mvp/`
- `audit/remediation/w3b-control-fix/`
- `audit/remediation/w4-e4-fix/`
- `audit/remediation/w4b-c15-fix/`
- `audit/remediation/workflow-supervisor-preflight/`
- `audit/feynman-analysis/FEYNMAN-COMPARATIVE-ANALYSIS.md`
- `docs/system-diagram.md`
- `docs/roadmap/full-product-vision.md`
- `docs/architecture-and-evolution.md`
- `.claude/agents/kie-implementer.md`
- `.claude/agents/kie-planner.md`
- `.claude/agents/kie-reviewer.md`

## Category: Likely Archival Material

The large tracked deletion set mostly looks like relocation, not true removal. Treat these as file-by-file reconciliation candidates.

Representative relocation patterns:

- `audit/GAP-TRIAGE.md` -> `audit/archive/GAP-TRIAGE.md`
- `audit/NEW-DEEP-RESEARCH-ANALYSIS-PROMPT.md` -> `audit/archive/NEW-DEEP-RESEARCH-ANALYSIS-PROMPT.md`
- `audit/OVERNIGHT-AUDIT-RESULTS.md` -> `audit/archive/OVERNIGHT-AUDIT-RESULTS.md`
- `audit/PLAN-AUDIT.md` -> `audit/archive/PLAN-AUDIT.md`
- `audit/SESSION-HANDOFF-SCAFFOLDING.md` -> `audit/archive/SESSION-HANDOFF-SCAFFOLDING.md`
- `docs/PARALLEL-EXECUTION-PLAN.md` -> `docs/archive/PARALLEL-EXECUTION-PLAN.md`
- `reference/analysis/*` -> `research/codebase-analysis/nano-claude-code/*`
- `source-analysis/*` -> `research/external-sources/bookmarks/*`
- `nate-synthesis/*` -> `research/external-sources/nate-jones/*`
- `quality-audits/*` -> `research/quality-audits/*`
- `research-reports/*` -> `research/reports/*`
- `synthesis/*` -> `research/synthesis/*`
- `OPENAI-SWITCHOVER-*.md` -> `reference/openai-switchover/OPENAI-SWITCHOVER-*.md`
- `WAVE-*-SESSION-PROMPTS.md` and `WAVE-4B-PIPELINE-INTEGRATION-PROMPT.md` -> `reference/session-prompts/`

Interpretation:

- Many of the scary `D` entries are probably intended cleanup already.
- They still need verification before acceptance because provenance can be lost if a destination doc is only similar, not equivalent.

## Category: Likely Generated Material

These look generated or rerun-produced, but some of them still contain operationally useful artifacts.

- `graphify-out/` contains `398` files.
- `graphify-out/GRAPH_REPORT.md` is operationally used by repo instructions and should remain readable.
- `graphify-out/cache/` looks like a generated cache candidate.
- `src/keystone/graphify-out/` contains `144` files and looks like a second generated cache tree inside the source tree.
- `output/` contains `22` files across `first_real_run`, `deep_research_run`, and `claude_switchover_run`.
- Worktree-local `engagements/` directories and worktree-local `graphify-out/cache/` trees also look generated, but they need per-worktree triage before any removal.

## Category: Likely Safe-to-Ignore Material

These are the strongest ignore candidates later, after policy is explicitly chosen.

- `.codex/config.toml`
- `.codex/hooks.json`
- `.codex/research-comparisons/feynman-2026-04-11/`
- `.DS_Store` files under archive/output/research trees
- `reference/nano-claude-code/node-compile-cache/`
- Worktree-local `.venv` directories once confirmed non-authoritative

Not safe to throw into the ignore bucket yet:

- `AGENTS.md`
- `.graphifyignore`
- `.claude/settings.json`
- `graphify-out/GRAPH_REPORT.md`
- `output/` as a whole, until artifact retention policy is explicit

## Category: Dangerous-to-Delete Material

These should be treated as no-touch during cleanup planning.

- Runtime edits under `src/keystone/`
- Test edits under `tests/`
- `schemas/citation.schema.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `docs/architecture-and-evolution.md`
- `scripts/setup.sh`
- `scripts/run_demo.sh`
- `AGENTS.md`
- `.graphifyignore`
- `reference/nano-claude-code`

Why `reference/nano-claude-code` is especially dangerous:

- The parent repo tracks it as mode `160000` at commit `567e557286b760ce74cf61bd97787fed9e637b66`.
- `git submodule status` fails because there is no matching `.gitmodules` mapping.
- The nested repo itself is dirty (`README.md` modified; multiple untracked research docs; untracked `node-compile-cache/`).

## What Should Stay

- Control-plane and clearance material.
- Active remediation workstream docs.
- Live runtime, test, schema, README, env, and tool configuration changes.
- `docs/architecture-and-evolution.md`.
- `scripts/`.
- `AGENTS.md` and `.graphifyignore`.
- The embedded `reference/nano-claude-code` repo until it has its own explicit cleanup decision.

## What Should Move to Archive

After file-by-file verification, these are the strongest archive/reorg candidates.

- Top-level switchover docs now represented under `reference/openai-switchover/`
- Top-level session prompt docs now represented under `reference/session-prompts/`
- Legacy `audit/*` docs now represented under `audit/archive/`
- Legacy `docs/PARALLEL-EXECUTION-PLAN.md` now represented under `docs/archive/`
- Older research/synthesis/source-analysis trees now represented under `research/`

## What Should Become Ignored or Generated Later

After policy review, the strongest candidates are:

- `.codex/`
- `graphify-out/cache/`
- `src/keystone/graphify-out/`
- `output/`
- `.DS_Store`
- nested repo cache junk inside `reference/nano-claude-code`

## Bottom Line

This is not a generic dirty repo. It is a mixed authority/docs/runtime/generated state. Cleanup should be staged later and separated into:

1. relocation verification
2. generated/ignore policy
3. worktree retirement

Do not collapse those into one pass.
