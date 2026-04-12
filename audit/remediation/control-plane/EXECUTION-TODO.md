# Remediation Execution Todo

*Created: 2026-04-12 | Purpose: drainable checklist for fresh autonomous sessions*

Use this only after reading:

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)

The control plane remains authoritative.  
This file is the operational checklist.

## Execution Mode

- [x] Continue autonomously across docs-only checkpoints
- [x] After each checkpoint commit, re-read the control plane and keep draining this list
- [x] Stop only on a hard stop condition from `CONTROL-PLANE-STATE.yaml`

## Current State

- Last cleared code commit: `4819527`
- Latest committed docs checkpoint before this setup state: `6eafc82`
- Active wave state: `wave-3b / setup`
- Next mandatory gate: `Wave 3B implementation lane`

## Now

- [x] Confirm the control-plane tuple now says:
  - `active_wave = wave-3b`
  - `active_state = setup`
  - `last_cleared_code_commit = 4819527`
  - `next_action = open a clean Wave 3B implementation worktree from 4819527`
- [x] Stay on `codex/remediation-program` in the main workspace
- [x] Do **not** start Wave 3B code in the main workspace

## Phase 1: Wave 3A Seam Freeze

- [x] Read:
  - [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md)
  - [WAVE-3-3B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-3B-PREWORK.md)
  - [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
- [x] Create [WAVE-3A-SEAM-FREEZE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3A-SEAM-FREEZE.md)
- [x] Freeze ownership of:
  - verifier module
  - provenance-sidecar emission point
  - round-state persistence location
  - deep vs shallow template/prompt wiring
  - inner-loop vs outer-loop authority
- [x] Add explicit “in scope / out of scope / owner / handoff contract / reopen trigger” sections for each seam
- [x] Commit the seam-freeze doc as a docs-only checkpoint

## Phase 2: Wave 3 Setup

- [x] Create [WAVE-3-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-SETUP.md) from the seam freeze plus final decisions
- [x] Create `audit/remediation/runs/wave-3/`
- [x] Create a Wave 3 candidate file-manifest template
- [x] Update control-plane files so `active_wave = wave-3` only after the seam-freeze commit lands

## Phase 3: Wave 3 Implementation

- [x] Open a new clean Wave 3 implementation worktree rooted at `2cdbfec`
- [x] Keep the main workspace controller/docs only
- [x] Implement only the Wave 3 scope approved by the seam freeze and setup docs
- [x] Write `candidate-<commit>-implementation.md`
- [x] Run focused Wave 3 tests and runtime probes
- [x] Create the candidate commit
- [x] Run adversarial review + second opinion on the committed snapshot
- [x] Write review synthesis and clearance artifacts for `4819527`

## Phase 4: Wave 3B Gate

- [x] Do **not** start Wave 3B until Wave 3 is cleared
- [x] Commit the Wave 3 cleared-state reconcile packet in the main workspace
- [x] Create `WAVE-3B-SETUP.md`
- [x] Update the control plane so Wave 3B setup becomes the active runway
- [x] Re-read the control plane after the Wave 3B setup checkpoint
- [ ] Preserve the single authoritative round-controller rule

## Phase 5: Wave 3B Implementation

- [ ] Open a new clean Wave 3B implementation worktree rooted at `4819527`
- [ ] Keep the main workspace controller/docs only
- [ ] Implement only the Wave 3B scope approved by `WAVE-3B-SETUP.md`
- [ ] Write `candidate-<commit>-implementation.md` under `audit/remediation/runs/wave-3b/`
- [ ] Run focused Wave 3B tests and runtime probes
- [ ] Create the candidate commit
- [ ] Run adversarial review + second opinion on the committed snapshot
- [ ] Write review synthesis and either blocked-checkpoint or clearance artifacts

## Carried Follow-Ups

- [ ] Keep `W2B-R01` visible as a non-blocking follow-up:
  - parseable but under-specified sprint-contract JSON can still produce empty enforcement fields
  - do not let it silently disappear from later planning

## Hard Rules

- [x] Never use the main workspace as the implementation lane
- [x] Never review a dirty tree as authoritative
- [x] Never overwrite immutable historical review packets
- [x] Never advance a wave without a committed clearance artifact
- [x] Always use GPT-5.4 with xhigh fast for spawned agents
