# Candidate 4ff7e90 Blocked Checkpoint

- Candidate commit: `4ff7e90`
- Baseline commit: `16e0bc7`
- State: `BLOCKED`
- Checkpoint created by: bootstrap adoption pass on `codex/remediation-program`

## Why This Exists

Wave 2B was reviewed and blocked, but the live status docs were never updated to reflect that.  
This file makes the blocked state explicit and versioned so a fresh session does not accidentally treat Wave 2B as merely “next.”

## Blocking Findings

- `W2B-B01`: LIGHT coverage can fail open on failed evaluated tasks.
- `W2B-B02`: task priority and importance derive from LLM list order instead of Step-5 scores.
- `W2B-B03`: the effective evaluator profile is not truly carried through `ResearchSpec`.
- `W2B-B04`: HITL gate decisions are not fully policy-owned.

## Non-Blocking Follow-Ups

- `W2B-R01`: malformed sprint-contract JSON should not silently degrade to a bare contract.
- `W2B-R02`: rubric event weights should reflect actual `dimension_emphasis`.
- `W2B-R03`: add real-path gate regression coverage.

## Recovery Material

- [candidate-4ff7e90-recovery-dirty-wip.patch](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch)

## Next Action

Create a clean worktree at `4ff7e90`, replay only approved Wave 2B blocker-fix work, produce a new candidate commit, and review that committed snapshot.
