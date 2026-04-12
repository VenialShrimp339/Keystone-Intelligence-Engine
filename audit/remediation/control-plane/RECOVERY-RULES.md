# Recovery Rules

## Purpose

This file defines how a fresh Codex session resumes the remediation program without relying on chat history.

## Recovery Order

1. Read [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml).
2. Read [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md).
3. Read the latest immutable review packets for the active candidate.
4. Read the active blocker ledger.
5. Only then read `CURRENT-STATE.md`, `WORKSTREAM-STATUS.md`, and the active wave setup doc.

## Hard Recovery Rules

- Never recover from dirty `HEAD`.
- Never use the main workspace as the implementation lane.
- Never review a dirty tree as if it were authoritative.
- Never advance a wave without a committed clearance artifact.
- Never trust stale status docs over a newer blocked review packet.

## Wave 2B Immediate Recovery Procedure

1. Start from branch `codex/remediation-program` in the main workspace.
2. Verify the recovery patch checksum:

```bash
cd /Users/jackriddle/Desktop/Keystone-Intelligence-Engine
shasum -a 256 audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch
```

Expected:

```text
f9cf1925c31d5836024bfdf32fd5a5ee8cbfe8d4b1e46dc0983630b128b36234
```

3. Create the clean Wave 2B worktree:

```bash
git worktree add -b codex/remediation-wave-2b ../Keystone-Intelligence-Engine-wave-2b 4ff7e90
```

4. Replay the captured Wave 2B blocker-fix WIP:

```bash
cd ../Keystone-Intelligence-Engine-wave-2b
git apply --3way /Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch
```

5. Compare the replayed result against:
   - [WAVE-2B-BLOCKER-REMEDIATION.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md)
   - [candidate-4ff7e90-file-manifest.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md)

6. Run the focused proof matrix from [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md).
7. Create the next candidate commit.
8. Review the committed snapshot only.

## If The Patch Does Not Apply Cleanly

- Do **not** fall back to coding in the main workspace.
- Do **not** widen the write set.
- Inspect only the files listed in the candidate file manifest.
- Reapply the intended hunks manually in the clean worktree.
- Update the blocker ledger with what changed before creating the candidate commit.

## Graphify Rule

If the active worktree changes code files, rebuild graphify before ending the implementation session.

Default command:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If default `python3` cannot import `graphify`, use the recorded interpreter:

```bash
/opt/homebrew/opt/python@3.12/bin/python3.12 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```
