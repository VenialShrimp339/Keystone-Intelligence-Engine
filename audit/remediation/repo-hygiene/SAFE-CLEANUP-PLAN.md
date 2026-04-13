# Safe Cleanup Plan

Date: 2026-04-13
Recommendation: cleanup should happen later, not now

## Why Later

The repo is in a mixed state:

- live runtime/test/schema changes are present in the same working tree
- a docs/archive reorganization is already partially in progress
- generated artifacts are mixed with operationally useful graph and output files
- an embedded git repo is dirty
- worktree sprawl includes both obvious duplicates and temp trees with unique local artifacts

Trying to clean all of that in one pass would make it too easy to lose provenance or accidentally bundle runtime changes into hygiene commits.

## Staged Plan

### Stage 0: Reconfirm the Control Plane

Do this before any later cleanup session.

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
sed -n '1,220p' audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml
sed -n '1,260p' audit/remediation/control-plane/ACTIVE-HANDOFF.md
git status --short --branch
git worktree list --porcelain
```

Goal:

- Reconfirm that the workspace is still docs-only.
- Reconfirm the pinned authority commits before deciding what is stale.

### Stage 1: Separate Cleanup From Runtime WIP

Do not start cleanup until the runtime lane is either committed elsewhere or explicitly left untouched.

Read-only commands:

```bash
git diff --name-only -- src tests schemas
git diff --name-only -- .env.example .gitignore README.md
git ls-files --others --exclude-standard | sed -n '1,200p'
```

Decision rule:

- If `src/`, `tests/`, or `schemas/` are still dirty, cleanup must stay scoped to docs-only files.
- Do not use `git add -A`.

### Stage 2: Verify Relocation Pairs Before Accepting Deletions

Treat every tracked deletion as "pending verification," not "ready to remove."

Exact safe comparison commands:

```bash
git diff --no-index -- audit/GAP-TRIAGE.md audit/archive/GAP-TRIAGE.md
git diff --no-index -- docs/PARALLEL-EXECUTION-PLAN.md docs/archive/PARALLEL-EXECUTION-PLAN.md
git diff --no-index -- OPENAI-SWITCHOVER-HANDOFF.md reference/openai-switchover/OPENAI-SWITCHOVER-HANDOFF.md
git diff --no-index -- WAVE-1-SESSION-PROMPTS.md reference/session-prompts/WAVE-1-SESSION-PROMPTS.md
git diff --no-index -- source-analysis/BOOKMARK-ARCHITECTURE-INSIGHTS.md research/external-sources/bookmarks/BOOKMARK-ARCHITECTURE-INSIGHTS.md
git diff --no-index -- research-reports/Deep_Research_Report_From_Prompt_1.md research/reports/batch-1/Deep_Research_Report_From_Prompt_1.md
git diff --no-index -- synthesis/UNIFIED-SYNTHESIS.md research/synthesis/UNIFIED-SYNTHESIS.md
```

Only after equivalence is confirmed should a later cleanup commit stage specific source deletions.

Example targeted staging commands for later:

```bash
git add audit/GAP-TRIAGE.md
git add docs/PARALLEL-EXECUTION-PLAN.md
git add OPENAI-SWITCHOVER-HANDOFF.md OPENAI-SWITCHOVER-PLAN.md OPENAI-SWITCHOVER-RESEARCH-PROMPTS.md
git add WAVE-1-SESSION-PROMPTS.md WAVE-2-SESSION-PROMPTS.md WAVE-3-SESSION-PROMPTS.md WAVE-4-PRESSURE-TEST-PROMPTS.md WAVE-4B-PIPELINE-INTEGRATION-PROMPT.md
```

Notes:

- Stage by exact path, not by directory glob.
- Keep archive reconciliation separate from generated/ignore changes.

### Stage 3: Set an Explicit Generated / Ignore Policy

Do this after relocation verification, not before.

Read-only sizing commands:

```bash
find graphify-out -type f | wc -l
find src/keystone/graphify-out -type f | wc -l
find output -type f | wc -l
git -C reference/nano-claude-code status --short --branch
```

Recommended later policy:

- Keep `graphify-out/GRAPH_REPORT.md` readable.
- Treat `graphify-out/cache/` as a generated-cache candidate.
- Treat `src/keystone/graphify-out/` as a generated-cache candidate.
- Treat `.codex/` as local tooling state.
- Treat `output/` as generated unless a retention rule says specific runs are evidence.
- Treat nested repo cache junk separately from the parent repo.

If ignore rules are later approved, add narrow rules first. Do not ignore whole trees until the report/evidence question is settled.

### Stage 4: Triage the Embedded Repo Separately

`reference/nano-claude-code` is not normal parent-repo dirt.

Read-only commands:

```bash
git ls-tree HEAD reference/nano-claude-code
git -C reference/nano-claude-code status --short --branch
find reference/nano-claude-code/node-compile-cache -maxdepth 2 | head -n 40
```

Decision rule:

- Do not fold nested-repo cleanup into the parent cleanup commit.
- Decide separately whether this stays as an embedded standalone repo, becomes a real submodule, or is frozen as reference material.

### Stage 5: Remove Worktrees in Safe Order

Worktree cleanup should happen last.

Read-only commands:

```bash
git worktree list --porcelain
git -C "/private/tmp/keystone-review-d6c24c7" status --short --branch
git -C "/private/tmp/keystone-w4b-c15-review-JeHOZe" status --short --branch
find "/private/tmp/keystone-w4b-c15-review-JeHOZe/engagements" -maxdepth 3 | head -n 40
git worktree prune --dry-run
```

Recommended later removal order:

1. clean detached review/checkpoint trees
2. detached duplicates with no unique artifacts
3. only then any broader pruning

Exact removal commands for the safest first wave:

```bash
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/keystone-review-d6c24c7"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/keystone-w3b1-review"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/kie-review-4ff7e90"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/kie-rp1-review"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/kie-w4d1-review-04fbc6c"
```

Preserve for now:

- the main root worktree
- all named Desktop branch worktrees
- any temp worktree with unique `engagements/`, `.venv`, or cache output that has not been triaged

## What Should Stay

- Control-plane and clearance docs
- active remediation workstream docs
- runtime/test/schema edits
- `docs/architecture-and-evolution.md`
- `scripts/`
- `AGENTS.md`
- `.graphifyignore`
- the embedded `reference/nano-claude-code` repo until separately decided

## What Should Move to Archive Later

- root switchover docs after pair verification
- root session prompt docs after pair verification
- legacy `audit/*` docs already represented under `audit/archive/`
- legacy research/synthesis/source-analysis material already represented under `research/`

## What Should Become Ignored / Generated Later

- `.codex/`
- `.DS_Store`
- `graphify-out/cache/`
- `src/keystone/graphify-out/`
- `output/`
- nested repo cache junk

## Commands to Avoid

Do not use these in a future cleanup pass unless there is a separate explicit approval.

```bash
git add -A
git clean -fd
git clean -fdx
git worktree prune
rm -rf /private/tmp/keystone-*
git reset --hard
git checkout --
```

## Bottom Line

The safe cleanup path is:

1. verify authority
2. isolate runtime WIP
3. reconcile relocation pairs
4. define generated/ignore policy
5. remove worktrees last

Anything faster is riskier than the mess itself.
