# Remediation Execution Todo

*Created: 2026-04-12 | Purpose: drainable checklist for fresh autonomous sessions*

Use this only after reading:

1. [CONTROL-PLANE-STATE.yaml](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml)
2. [ACTIVE-HANDOFF.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/ACTIVE-HANDOFF.md)

The control plane remains authoritative.  
This file is the operational checklist.

## Current State

- Last cleared code commit: `2cdbfec`
- Last docs reconcile commit: `2c026cc`
- Active wave state: `wave-2b / cleared`
- Next mandatory gate: `Wave 3A seam freeze`

## Now

- [ ] Confirm the control-plane tuple still says:
  - `active_wave = wave-2b`
  - `active_state = cleared`
  - `last_cleared_code_commit = 2cdbfec`
  - `next_action = create and commit WAVE-3A-SEAM-FREEZE.md`
- [ ] Stay on `codex/remediation-program` in the main workspace
- [ ] Do **not** start Wave 3 code yet

## Phase 1: Wave 3A Seam Freeze

- [ ] Read:
  - [AUTONOMOUS-REMEDIATION-PLAN-v4.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md)
  - [WAVE-3-3B-PREWORK.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-3B-PREWORK.md)
  - [FINAL-DECISIONS-v2.1.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/decisions/FINAL-DECISIONS-v2.1.md)
- [ ] Create [WAVE-3A-SEAM-FREEZE.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3A-SEAM-FREEZE.md)
- [ ] Freeze ownership of:
  - verifier module
  - provenance-sidecar emission point
  - round-state persistence location
  - deep vs shallow template/prompt wiring
  - inner-loop vs outer-loop authority
- [ ] Add explicit “in scope / out of scope / owner / handoff contract / reopen trigger” sections for each seam
- [ ] Commit the seam-freeze doc as a docs-only checkpoint

## Phase 2: Wave 3 Setup

- [ ] Create [WAVE-3-SETUP.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/WAVE-3-SETUP.md) from the seam freeze plus final decisions
- [ ] Create `audit/remediation/runs/wave-3/`
- [ ] Create a Wave 3 candidate file-manifest template
- [ ] Update control-plane files so `active_wave = wave-3` only after the seam-freeze commit lands

## Phase 3: Wave 3 Implementation

- [ ] Open a new clean Wave 3 implementation worktree rooted at `2cdbfec`
- [ ] Keep the main workspace controller/docs only
- [ ] Implement only the Wave 3 scope approved by the seam freeze and setup docs
- [ ] Write `candidate-<commit>-implementation.md`
- [ ] Run focused Wave 3 tests and runtime probes
- [ ] Create the candidate commit
- [ ] Run adversarial review + second opinion on the committed snapshot
- [ ] Write review synthesis and either blocked-checkpoint or clearance artifacts

## Phase 4: Wave 3B Gate

- [ ] Do **not** start Wave 3B until Wave 3 is cleared
- [ ] After Wave 3 clears, create `WAVE-3B-SETUP.md`
- [ ] Preserve the single authoritative round-controller rule

## Carried Follow-Ups

- [ ] Keep `W2B-R01` visible as a non-blocking follow-up:
  - parseable but under-specified sprint-contract JSON can still produce empty enforcement fields
  - do not let it silently disappear from later planning

## Hard Rules

- [ ] Never use the main workspace as the implementation lane
- [ ] Never review a dirty tree as authoritative
- [ ] Never overwrite immutable historical review packets
- [ ] Never advance a wave without a committed clearance artifact
- [ ] Always use GPT-5.4 with xhigh fast for spawned agents
