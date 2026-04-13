# Worktree Inventory

Date: 2026-04-13
Scope: read-only inventory; no worktrees removed

## Snapshot

- Total linked worktrees: `29`
- Named branch worktrees: `9`
- Detached temp worktrees: `20`
- The primary workspace is not `main`; it is `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` on `codex/remediation-program` at `b519f5491690`
- `main` is not checked out anywhere

## Preserve Now: Definitely Active or Branch-Backed

These should remain until a later explicit branch-retirement decision.

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` - `codex/remediation-program` - dirty main workspace
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-supervisor-control` - `codex/workflow-supervisor-control` - clean
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w3b-control-fix` - `codex/w3b-control-fix` - clean
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro` - `codex/remediation-w4-e4-post-retro` - has untracked `engagements/`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4b-c15-post-retro` - `codex/remediation-w4b-c15-post-retro` - has untracked `engagements/` and `graphify-out/cache/`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-2b` - `codex/remediation-wave-2b` - clean
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3` - `codex/remediation-wave-3` - only extra dirt is `graphify-out/cache/`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b` - `codex/remediation-wave-3b` - clean
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4` - `codex/remediation-wave-4` - clean
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` - `codex/remediation-wave-4b` - clean

## Probably Removable Later: Clean Detached Review / Checkpoint Trees

These are the safest later-removal candidates because they are detached, clean, and appear to duplicate named branches or review snapshots.

- `/private/tmp/keystone-review-d6c24c7`
- `/private/tmp/keystone-w3b1-review`
- `/private/tmp/kie-cp1-review-04fbc6c`
- `/private/tmp/kie-review-4ff7e90`
- `/private/tmp/kie-review-676be93-22bQ2W`
- `/private/tmp/kie-rp1-87xOeF`
- `/private/tmp/kie-rp1-review`
- `/private/tmp/kie-rp1-review-04fbc6c`
- `/private/tmp/kie-w4d1-review-04fbc6c`
- `/private/tmp/kie-retro-worktrees/w3a1-df9f0445`
- `/private/tmp/kie-wave2a-badba75-review` after checking whether its `.venv/` matters

## Probably Removable Later: Detached Duplicate Implementation Trees

These are duplicates of branch-backed worktrees and look removable only after artifact triage.

- `/private/tmp/keystone-w3b1-code` - duplicate of `...-wave-3b`
- `/private/tmp/keystone-W4B-1-65a612d` - duplicate of `...-wave-4b`
- `/private/tmp/keystone-w4b-c15-review-parent` - duplicate of `...-wave-4b`

## Preserve Until Artifact Triage: Detached Trees With Unique Local Output

These should not be removed until their local artifacts are intentionally kept, copied, or discarded.

- `/private/tmp/keystone-w4-1-jzvvQl` - duplicate commit of Wave 4, but has `engagements/eng_79f836f8124d`
- `/private/tmp/keystone-w4-e4-rerun-j0GXxp` - duplicate of active `...-w4-e4-post-retro`, but has `engagements/eng_c896be1e8bc0`
- `/private/tmp/keystone-w4b-c15-review-JeHOZe` - duplicate of active `...-w4b-c15-post-retro`, but has two unique engagement trees
- `/private/tmp/keystone-w4b2-CpI6OH` - duplicate of `...-wave-4b`, but has `engagements/eng_dab4e5ecae77`
- `/private/tmp/keystone-w4b2-rerun-ny4ASg` - duplicate of active `...-w4b-c15-post-retro`, but has `engagements/eng_96e3a36bfe11`

## Duplication Patterns

- Commit `65a612dc1400` appears in four worktrees
- Commit `4d8f647cab66` appears in three worktrees
- Commit `04fbc6c9bb1d` appears in three detached review worktrees
- Commit `104658506075` appears in two worktrees
- Commit `5cc95858213e` appears in two worktrees
- Commit `6406e4639a26` appears in two worktrees

Interpretation:

- There is more duplication than true branch diversity.
- No detached worktree inspected looked like the only reference keeping a commit alive.
- The main risk is local rerun output, not orphaned commits.

## Recommended Later Triage Order

1. Remove clean detached review/checkpoint worktrees first.
2. Triage `engagements/`, `.venv`, and worktree-local `graphify-out/cache/`.
3. Remove detached implementation duplicates after confirming no unique artifacts remain.
4. Keep named Desktop branch worktrees until the corresponding branches are explicitly retired.

## Exact Safe Commands for Later Use

Read-only inspection:

```bash
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree list --porcelain
git -C "/private/tmp/keystone-review-d6c24c7" status --short --branch
git -C "/private/tmp/keystone-w4-e4-rerun-j0GXxp" status --short --branch
find "/private/tmp/keystone-w4-e4-rerun-j0GXxp/engagements" -maxdepth 3 | head -n 40
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree prune --dry-run
```

Targeted later removals after verification:

```bash
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/keystone-review-d6c24c7"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/keystone-w3b1-review"
git -C /Users/jackriddle/Desktop/Keystone-Intelligence-Engine worktree remove "/private/tmp/kie-review-4ff7e90"
```

Do not jump straight to broad pruning or manual `rm -rf`.
