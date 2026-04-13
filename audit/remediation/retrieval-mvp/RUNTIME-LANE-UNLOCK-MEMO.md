# Runtime-Lane Unlock Memo

Date: 2026-04-13  
Session mode: controller-only planning  
Runtime truth anchor: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at commit `65a612d`

## Purpose

Define the exact controller-grade prerequisites for opening the first Retrieval MVP runtime lane without reopening runtime implementation in the main workspace, violating the current hard stop, or confusing docs readiness with runtime authorization.

This memo is subordinate to the active control plane:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`

If this memo conflicts with those files, the control plane wins.

## Current Authority State

As of this memo:

- `65a612d` is the last cleared code commit.
- The main workspace remains controller/docs only.
- The retrospective audit program is complete under the current authoritative review ledger.
- Forward runtime work remains hard-stopped until a later controller-approved next-wave setup artifact is both committed and promoted into the live control plane.

Therefore:

- No retrieval runtime lane is authorized by the current repo state.
- The retrieval-mvp package is a planning and benchmark packet, not a runtime-lane authorization artifact by itself.

## First Runtime Lane Recommendation

Inference from the retrieval-mvp package and the current repo layout:

- The first runtime lane should be the fetch lane only.
- Open Lane D from `IMPLEMENTATION-LANES.md` first:
  - purpose: gateway backends for article, filing, PDF, and paper fetch
  - worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
  - branch: `codex/retrieval-mvp-fetch`

Do not open parser Lane E or L1 integration Lane F in the same controller unlock.

Reason:

- Lane D is the narrowest lane that closes the largest current gap between `65a612d` and the stated Retrieval MVP target.
- Lane E and Lane F widen the surface into deterministic parsing and research-path integration, which should remain gated behind a later seam freeze or follow-on setup checkpoint.

## Controller-Grade Unlock Prerequisites

All of the following must be true before the first retrieval runtime lane may open.

### 1. Control-plane prerequisite

- A new controller-approved setup artifact must be committed after Wave 4B clearance.
- The hard stop in the control plane must no longer be unresolved for that lane.
- The setup artifact must explicitly authorize a retrieval runtime lane and must name the exact baseline, worktree, branch, scope, write set, tests, and review packet requirements.

This is the non-negotiable unlock condition. Without it, runtime work remains unauthorized even if the docs packet is strong.

### 2. Docs-only contract packet must be complete first

The following docs must already exist and be mutually consistent:

- `CURRENT-RETRIEVAL-VS-TARGET.md`
- `MVP-RETRIEVAL-REQUIREMENTS.md`
- `ARCHITECTURE-DECISIONS.md`
- `RETRIEVAL-MVP-ARCHITECTURE-MEMO.md`
- `RETRIEVAL-MVP-SEAM-CONTRACT.md`
- `RETRIEVAL-MVP-MIGRATION-CHECKLIST.md`
- `WORKSTREAM-HANDOFF.md`
- `IMPLEMENTATION-LANES.md`
- `RISK-REGISTER.md`

Minimum contract proof required from those docs:

- Exa and Brave are discovery-only on the canonical MVP path.
- The governed canonical path is `task -> discovery -> fetch -> parse -> evidence bundle -> synthesis -> anchored citation`.
- `DEEP_RESEARCH=1` remains a bypass lane and does not satisfy MVP acceptance.
- Runtime truth claims are anchored to `65a612d`.
- The first runtime lane is procedurally separate from later parser, L1 integration, semantic retrieval, and claim-support-verification work.

### 3. Docs-only benchmark packet must be complete first

The benchmark and replay packet should be complete before the lane opens, even though no acceptance run starts yet.

Required docs:

- `BENCHMARK-TASK-PACK-SCHEMA.md`
- `REPLAY-ADAPTER-SPEC.md`
- `REPLAY-SERVICE-CONTRACT-NOTE.md`
- `ARTIFACT-SCHEMA-DELTA-MEMO.md`
- `MANUAL-DR-PARALLEL-PROMPTBOOK.md`
- `HUMAN-SCORING-WORKSHEET.md`
- `SCOREBOARD-SPEC.md`
- `PROVENANCE-AUDIT-SPEC.md`
- `ACCEPTANCE-MATH-ADDENDUM.md`
- `ACCEPTANCE-RUN-CHECKLIST.md`

Minimum benchmark proof required from those docs:

- the candidate must beat `Manual-DR-Parallel`, not only `Keystone-Shallow-65a612d`
- replay-only source access is mandatory for binding benchmark runs
- provenance audit remains separate from claim-support judgment
- shadow bypass arms are non-canonical
- run artifacts must record candidate commit, parent anchor, approved setup artifact, and worktree provenance

### 4. Docs-only adversarial review must be complete first

Before opening the lane, the controller should have a docs-only adversarial pass over the retrieval-mvp packet that confirms:

- no overclaim that registered tools are real backends
- no collapse of governed retrieval into bypass retrieval
- no benchmark-softening through ties, double-fails, or weak baselines
- no ambiguity about provenance or replay-only rules
- no confusion between citation existence and claim support

At minimum, the review stack must clear the mandatory gates already named in `RISK-REGISTER.md` and the next-wave setup package:

- Backend Reality Gate
- Tool Contract Gate
- Governance Gate
- Run Contract Gate
- Controller Unlock / Worktree Provenance Gate

Those gates are not satisfied merely by being named in a checklist. Before a later promotion session may authorize the lane, each gate should exist as a docs-only artifact with:

- reviewer
- reviewed snapshot
- evidence inputs
- approved setup artifact path
- explicit `CLEARED` or `BLOCKED` verdict

### 5. Runtime-lane scope must be narrow and seam-specific

The first lane may open only if its scope is explicitly limited to fetch-layer work:

- gateway-owned article fetch
- gateway-owned EDGAR filing fetch
- gateway-owned PDF fetch and persistence
- gateway-owned paper metadata plus full-text or authoritative-abstract fetch
- minimal typed retrieval model additions required for fetch identity, coverage, and audit

The first lane must not include:

- deterministic parser lane work as its main responsibility
- research-agent integration
- benchmark execution
- semantic retrieval
- internal or cross-engagement retrieval
- claim-support verification
- UI work

## Required Next-Wave Setup Artifact Contents

The next-wave setup artifact must include, at minimum:

- authoritative read order
- activation block
- current-code anchor at `65a612d`
- explicit statement that the main workspace remains docs-only
- exact planned worktree path and branch
- exact lane purpose
- binding scope in
- binding scope out
- exact allowed write set
- exact denylist
- required test matrix
- required runtime probes
- candidate artifact requirements
- reopen and hard-stop triggers

The setup artifact should behave like `WAVE-4B-SETUP.md`, but for the first retrieval runtime lane.

See `SETUP-ARTIFACT-CHECKLIST.md` for the detailed content checklist.

## Worktree Provenance And Review Requirements

The first retrieval runtime lane must be opened only in a dedicated clean worktree rooted at `65a612d`.

Required provenance fields for later review and benchmark packets:

- `candidate_commit`
- `candidate_parent_anchor`
- `approved_setup_artifact`
- `worktree_path`
- `worktree_clean`
- branch name

Required candidate review packet set:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-backend-truth-matrix.md`
- `candidate-<commit>-live-fetch-review.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-clearance.md` or blocked checkpoint

See `WORKTREE-AND-REVIEW-GATE-CHECKLIST.md` for the exact checklist.

## Docs-Only Tasks That Should Be Complete First

The following docs-only tasks should be complete before the runtime lane opens:

1. Retrieval contract freeze:
   - requirements, architecture memo, seam contract, migration checklist, architecture decisions
2. Benchmark freeze:
   - task-pack schema, replay adapter spec, replay-service contract note, artifact-schema delta memo
3. Scoring and acceptance freeze:
   - manual control promptbook, worksheet, scoreboard spec, provenance audit spec, acceptance math, acceptance checklist
4. Governance hardening:
   - implementation lanes, workstream handoff, risk register, docs-only adversarial review

Important clarification:

- `replay_service_manifest.json`
- shallow `adapter_declaration.json`
- candidate `adapter_declaration.json`
- full suite task-pack hashes

are benchmark run-start artifacts, not runtime-lane-open prerequisites by themselves.

## Controller Decision Rule

The first retrieval runtime lane may open only when:

1. a new controller-approved setup artifact is committed after Wave 4B clearance
2. the setup artifact explicitly authorizes the first retrieval lane
3. the lane is rooted from `65a612d` in a clean dedicated worktree
4. the lane has an exact write set, denylist, test matrix, runtime probes, and review packet requirements
5. the docs-only contract, benchmark, and governance packet is complete enough to keep the lane honest about what it is and is not proving

If any one of those is missing, the lane remains unauthorized.

## Current Verdict

Current verdict for this session: no retrieval runtime lane is authorized now.

Reason:

- the required next-wave controller authority artifact does not yet exist as a committed setup checkpoint
- the control-plane hard stop remains active for forward runtime work
