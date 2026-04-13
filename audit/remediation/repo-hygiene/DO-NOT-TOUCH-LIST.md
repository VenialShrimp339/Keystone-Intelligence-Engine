# Do Not Touch List

Date: 2026-04-13
Purpose: files, directories, and cleanup actions that should be excluded from later repo-hygiene work unless explicitly re-authorized

## Hard No-Touch Files

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- `CURRENT-STATE.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `audit/remediation/WAVE-4B-SETUP.md`
- `audit/remediation/runs/wave-4b/`
- tracked retrospective audits under `audit/remediation/workstream-retro/` and `audit/remediation/workstream-retro/reviews/`

Reason:

- These are control-plane, clearance, or controller-authorized review artifacts.

## Hard No-Touch Runtime / Test / Schema Paths

- `src/keystone/`
- `tests/`
- `schemas/citation.schema.json`

Reason:

- These are live runtime/test changes, not hygiene clutter.

## Hard No-Touch Mixed-Intent Project Files

- `.env.example`
- `.gitignore`
- `README.md`
- `docs/architecture-and-evolution.md`
- `scripts/`
- `AGENTS.md`
- `.graphifyignore`
- `.claude/settings.json`

Reason:

- These are active project-definition or developer-workflow files and should not be swept into archive cleanup.

## Hard No-Touch Embedded Repo

- `reference/nano-claude-code`

Reason:

- It is tracked as a gitlink, not a normal directory.
- The nested repo has its own dirty state.
- `git submodule status` does not map it cleanly through `.gitmodules`.

## Hard No-Touch Worktrees For Now

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-supervisor-control`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w3b-control-fix`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4-e4-post-retro`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-w4b-c15-post-retro`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-2b`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-3b`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`
- temp worktrees with unique `engagements/`, `.venv`, or local cache output

Reason:

- These either hold active branch history or local artifacts that have not been triaged yet.

## Graph / Output Exceptions

Do not treat these as bulk junk without file-level policy.

- `graphify-out/GRAPH_REPORT.md`
- any graph artifact directly referenced by repo instructions
- `output/` runs that may still be evidence

Reason:

- Some files in generated-looking trees are still operationally or historically useful.

## Highest-Risk Cleanup Mistakes To Avoid

1. Treating authority docs as ordinary stale docs and moving or deleting them.
2. Mixing runtime/test/schema changes into a cleanup commit.
3. Accepting tracked deletions without verifying the replacement file is actually equivalent.
4. Removing temp worktrees before checking for unique `engagements/`, `.venv`, or cache artifacts.
5. Treating the embedded `reference/nano-claude-code` repo like a normal folder.

## Commands That Should Stay Off Limits

```bash
git add -A
git clean -fd
git clean -fdx
git worktree prune
rm -rf /private/tmp/keystone-*
git reset --hard
git checkout --
```

Use targeted inspection and targeted staging/removal only.
