# Autonomous Remediation Plan v4

*Created: 2026-04-12 | Status: final hardened autonomy plan after repeated adversarial review*

This is the first remediation-autonomy plan that should be trusted for execution.

It exists because the review teams converged on a consistent conclusion:

- the **wave roadmap is sound**
- the **unsafe parts were bootstrap, authority, proof, recovery, and workspace discipline**

This version hardens those areas directly.

## 1. What This Plan Is And Is Not

This document is:
- the bootstrap authority for adopting autonomous remediation
- the final design for controller behavior, review gates, and wave sequencing
- the source of truth for how future sessions should recover and continue

This document is **not**:
- itself a state transition
- permission to start coding immediately from the current dirty workspace
- permission to trust stale status docs over newer blocked review packets

No wave state changes because this file exists.  
Wave state changes only through committed control-plane artifacts plus committed review packets.

## 2. Current Truth

The controller must treat these facts as binding:

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B implementation exists at `4ff7e90`.
- `4ff7e90` is **blocked**, not cleared.
- The current active task is **Wave 2B blocked-snapshot remediation on top of `4ff7e90`**.
- The main workspace currently contains unreviewed dirty Wave 2B blocker-fix work.
- That dirty Wave 2B work is **recovery material**, not live truth, until it is replayed in a clean worktree, committed, and re-reviewed.
- The repo’s top-level status docs still contain stale “Wave 2B is next” language and therefore cannot currently be trusted as the active control plane.

Therefore:
- no new implementation lane may start from the main workspace
- no stale entrypoint doc may outrank the Wave 2B blocked review packets
- the first autonomous action must be a docs/bootstrap adoption commit plus a recovery-safe worktree setup

## 3. Core Operating Laws

### 3.1 One controller, one code lane

At any moment there may be:
- exactly one controller
- exactly one active code-writing lane
- any number of read-only or planning sidecars

No second code-writing lane is allowed for the active wave.

### 3.2 Committed snapshot only

No dirty-tree review is binding.

Every meaningful decision must be grounded in one of:
- a committed control-plane artifact
- a committed candidate code snapshot
- a committed review packet

### 3.3 Review truth outranks status docs

If a committed review packet says a candidate is blocked, no status doc may claim the wave is clear or “next.”

### 3.4 Recovery before progress

When the workspace is messy, autonomy must recover the state first.  
It may not treat “probably the latest edits” as good enough.

### 3.5 Every analysis leaves a trail

Every implementation, review, synthesis, planning, and recovery step must emit a versioned artifact on disk before the controller advances state.

## 4. Bootstrap Adoption

Autonomy is not considered adopted until a docs-only bootstrap commit lands.

### 4.1 Pre-bootstrap authority order

Until the bootstrap adoption commit exists, use this order:

1. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
2. latest immutable Wave 2B review packets
3. `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md` and the latest blocker-fix session artifact as recovery evidence only
4. `CURRENT-STATE.md`
5. `audit/remediation/WORKSTREAM-STATUS.md`
6. `audit/remediation/WAVE-2B-SETUP.md`
7. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
8. `SESSION-LOG.md`
9. `CLAUDE.md`, `audit/remediation/EXECUTION-GUIDE.md`, `audit/remediation/BUILD-PROCESS.md`, and other legacy docs as background only

### 4.2 Bootstrap adoption deliverables

Before any new code work:

1. create `audit/remediation/control-plane/`
2. create:
   - `CONTROL-PLANE-STATE.yaml`
   - `ACTIVE-HANDOFF.md`
   - `RECOVERY-RULES.md`
3. create `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
4. create `audit/remediation/runs/wave-2b/`
5. reconcile live docs to blocked-`4ff7e90` reality:
   - `CURRENT-STATE.md`
   - `audit/remediation/WORKSTREAM-STATUS.md`
   - `audit/remediation/WAVE-2B-SETUP.md`
6. add explicit tombstone or redirect banners to stale launcher docs:
   - `CLAUDE.md`
   - `audit/remediation/EXECUTION-GUIDE.md`
   - `audit/remediation/BUILD-PROCESS.md`
   - any other doc that still presents itself as the current first entrypoint
7. append `SESSION-LOG.md` with the Wave 2B checkpoint and blocked-review chain
8. commit the above as one docs-only bootstrap adoption commit

Autonomy does not start until that commit exists.

### 4.3 Bootstrap adoption intent

The goal of the bootstrap commit is simple:

- a fresh session must not be able to accidentally start Wave 2B from stale docs
- a fresh session must be able to find the blocked state, current candidate lineage, and exact next action without reading chat history

## 5. Post-Bootstrap Authority Model

### 5.1 Authority order after bootstrap

After the bootstrap adoption commit, the remediation authority order is:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. latest immutable review packet(s) for the active candidate
4. latest immutable clearance or blocked-state synthesis artifact
5. active blocker-remediation doc
6. candidate file manifest for the active candidate
7. `CURRENT-STATE.md`
8. `audit/remediation/WORKSTREAM-STATUS.md`
9. active wave setup doc
10. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
11. `SESSION-LOG.md`
12. `CLAUDE.md`, `audit/remediation/EXECUTION-GUIDE.md`, `audit/remediation/BUILD-PROCESS.md`, and all other legacy docs as background only

### 5.2 Versioned authority rule

After bootstrap:
- no authoritative artifact may remain untracked
- no uncommitted artifact may advance state
- sidecar outputs are advisory until the controller triages and promotes them

When a live control plane exists, `ACTIVE-HANDOFF.md` may narrow items 3-9 above to the exact current packet family, boundary docs, and summary docs for the active wave or hard-stop checkpoint. `CURRENT-STATE.md` and `WORKSTREAM-STATUS.md` must mirror that narrowed order rather than invent a competing shortcut, and `audit/remediation/workstream-retro/` plus `audit/remediation/workstream-retro/reviews/` remain retrospective sidecar roots unless a later controller reconcile promotes them.

### 5.3 Review precedence rule

If review truth conflicts with status docs:
- review truth wins
- status docs must be patched at the next blocked-state or cleared-state checkpoint

## 6. Controller Lease

### 6.1 Lease principle

There is exactly one controller at a time.

Only the controller may mutate:
- `CONTROL-PLANE-STATE.yaml`
- `ACTIVE-HANDOFF.md`
- blocker-remediation docs
- `CURRENT-STATE.md`
- `WORKSTREAM-STATUS.md`
- active wave setup docs

### 6.2 Required lease fields

`CONTROL-PLANE-STATE.yaml` must contain at least:

- `controller_epoch`
- `lease_owner`
- `lease_acquired_at`
- `lease_heartbeat_at`
- `lease_expires_at`
- `lease_takeover_rule`
- `lease_stolen_by`
- `active_branch`
- `controller_workspace_path`
- `active_worktree_path`
- `review_worktrees`
- `active_wave`
- `active_state`
- `execution_baseline_commit`
- `last_cleared_code_commit`
- `current_candidate_commit`
- `candidate_parent_commit`
- `last_docs_reconcile_commit`
- `required_review_stage`
- `accepted_overlays`
- `workspace_policy`
- `model_policy`
- `blocked_on`
- `next_action`
- `latest_review_packets`
- `dirty_state_status`
- `recovery_patch_path`
- `recovery_patch_sha256`
- `recovery_branch`
- `wip_parent_candidate_commit`
- `wip_scope`

### 6.3 Lease rules

- no state mutation is valid without an active lease
- the controller must heartbeat after every material stage transition
- a takeover requires:
  - incrementing `controller_epoch`
  - rewriting the lease fields
  - appending the takeover event to `ACTIVE-HANDOFF.md`
- the new controller must first verify that the predecessor’s last claimed action matches the repo state before doing anything else

## 7. Workspace and Branch Discipline

### 7.1 Main workspace rule

The main workspace is **controller/docs only**.

It must not be the active implementation lane.

### 7.2 Active implementation lane

The active code lane always runs in a dedicated clean worktree rooted at:
- the blocked candidate commit, or
- the last cleared baseline

For the immediate next loop:
- the clean implementation worktree must be rooted at `4ff7e90`

### 7.3 Review worktrees

Every adversarial review, second opinion, and clearance check must run against:
- a detached worktree
- or an equivalent isolated snapshot

Review worktrees must be pruned after:
- candidate supersession
- explicit abandonment
- or clearance

### 7.4 Branch policy

Use:
- one controller branch, e.g. `codex/remediation-program`
- one active wave integration branch, e.g. `codex/remediation-wave-2b`

`main` is read-only for remediation.

### 7.5 Dirty-WIP rule

Before any new Wave 2B implementation:
- classify all dirty state
- snapshot all candidate-related WIP to a recovery artifact
- bind that recovery artifact to a parent candidate commit

Allowed dirty-state classes:
- `candidate_delta`
- `quarantined_wip`
- `unrelated_user_change`
- `generated_artifact`

No dirty state may be promoted without:
- a parent candidate commit
- a recovery artifact path and checksum
- explicit controller promotion into the clean worktree

## 8. Artifact Model

### 8.1 Control-plane files

Mandatory:
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RECOVERY-RULES.md`

### 8.2 Active handoff schema

`ACTIVE-HANDOFF.md` must contain these exact sections:

1. `Current Truth`
2. `Authoritative Order`
3. `Active State Tuple`
4. `Open Blockers`
5. `Latest Review Packets`
6. `Exact Next Action`
7. `Exact Recovery Command`
8. `Allowed Write Set`
9. `Required Test Matrix`
10. `Required Runtime Probes`
11. `Docs Explicitly Ignored As Stale`
12. `Active Sidecars`

### 8.3 Active state tuple

This tuple must appear in both control-plane files:

- `active_wave`
- `active_state`
- `execution_baseline_commit`
- `review_target_commit`
- `docs_reconcile_commit`
- `next_recovery_checkout`

### 8.4 Run folders

Every active wave gets a run folder:

- `audit/remediation/runs/wave-2b/`
- `audit/remediation/runs/wave-3/`
- `audit/remediation/runs/wave-3b/`
- `audit/remediation/runs/wave-4/`
- `audit/remediation/runs/wave-4b/`
- `audit/remediation/runs/wave-5/`

Each candidate commit gets immutable artifacts:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-file-manifest.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-clearance.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-blocked-checkpoint.md` if blocked
- `candidate-<commit>-fix-brief.md` if blocked

### 8.5 Blocker ledger

Every blocked wave must maintain a blocker ledger:

- `audit/remediation/WAVE-<N>-BLOCKER-REMEDIATION.md`

Each blocker row must include:

- `blocker_id`
- `failure_family`
- `family_status`
- `source_review`
- `blocked_candidate_commit`
- `first_seen_commit`
- `introduced_by`
- `last_verified_commit`
- `status`
- `current_disposition`
- `files_to_touch`
- `stageable_files`
- `tests_required`
- `runtime_probe_required`
- `required_regression_test`
- `required_regression_probe`
- `acceptance_invariant`
- `pre_fix_red_evidence`
- `post_fix_green_evidence`
- `verification_evidence`
- `review_packet_refs`
- `fix_commit`
- `reopen_criteria`
- `owner_prompt_ref`
- `supersedes`

The immediate next artifact must be:
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`

## 9. Review Model

### 9.1 Review stages

Each candidate commit moves through:

1. `candidate`
2. `adversarial_reviewed`
3. `second_opinion_reviewed`
4. `cleared`

Only `cleared` may advance:
- `last_cleared_code_commit`
- wave state
- next-wave setup

### 9.2 Review roles

- `adversarial review`: first independent read-only review
- `second opinion`: parallel independent read-only review
- `clearance`: controller-produced synthesis artifact tied to exact blocker IDs and proof rows

If the first two reviews disagree materially:
- the candidate remains blocked
- the controller either resolves the disagreement in synthesis or commissions one targeted tie-break review

### 9.3 Baseline rule

Every candidate may be locally inspected as:
- `previous_candidate..current_candidate`

But clearance must always be grounded in:
- the full `wave_baseline..candidate` scope

For Wave 2B:
- baseline remains `16e0bc7`

### 9.4 Mandatory review packet contents

Every review artifact must record:

- baseline commit
- candidate parent commit
- target commit
- full diff scope
- focused test matrix
- named runtime probes
- findings ordered by severity
- stale-vs-open blocker disposition
- explicit verdict: `BLOCKED` or `CLEARED`

### 9.5 Blocked-state checkpoint rule

After every `BLOCKED` verdict, before any further code work:

1. update `CONTROL-PLANE-STATE.yaml`
2. update `ACTIVE-HANDOFF.md`
3. update blocker ledger
4. append `SESSION-LOG.md`
5. patch `CURRENT-STATE.md` and `WORKSTREAM-STATUS.md` enough to stop them from lying
6. write `candidate-<commit>-blocked-checkpoint.md`
7. commit those docs as a docs-only blocked-state checkpoint

This is mandatory.  
Blocked state must be explicit and committed.

### 9.6 Cleared-state checkpoint rule

After every `CLEARED` verdict:

1. update the same control-plane docs
2. mark the wave cleared
3. reconcile the next-wave setup doc
4. write `candidate-<commit>-clearance.md`
5. commit those docs as a docs-only cleared-state reconcile checkpoint

### 9.7 Docs-only reconcile review rule

Docs-only reconcile commits do not require a full second-opinion ladder.

They do require:
- controller consistency check
- authority-order validation
- confirmation that no wave state is misrepresented

## 10. Proof Obligations

### 10.1 Proof table

Every blocker must be closed by a proof row in:
- the blocker ledger
- the clearance artifact

Required columns:

- `blocker_id`
- `failure_family`
- `runtime_invariant`
- `owner_path`
- `named_tests`
- `named_runtime_probes`
- `pre_fix_red_evidence`
- `post_fix_green_evidence`
- `reviewer_disposition`

### 10.2 Non-vacuous proof rule

For each blocker:
- at least one test or probe must hit the real enforcing seam
- mocks may supplement but cannot substitute
- closure requires either:
  - red evidence on the blocked snapshot, or
  - red evidence under a deliberate bypass mutation against the same seam

### 10.3 Candidate scope manifest

Every candidate must carry a file manifest that declares:

- allowed write set
- allowed collateral files
- explicit denylist
- suspicious dirty files
- files touched but not promoted

Reviews must classify every touched file as:
- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No candidate clears with unresolved scope-creep files.

## 11. Sidecar Policy

Every sidecar must declare a manifest before starting:

- objective
- read set
- write set
- output path
- authority level
- expiry condition
- whether it may touch live docs

Default authority is always `advisory`.

Sidecars may:
- analyze
- review
- plan
- prepare diffs

They may not:
- mutate live state
- advance wave state
- reopen or close blockers

Only the controller may promote sidecar output into the active loop.

## 12. Model Policy

Use **GPT-5.4 with xhigh reasoning** for every spawned agent by default.

If the tool or UI has a “fast mode” distinction, use the fast variant of that same model policy.

If any session must deviate, record the deviation in:
- `CONTROL-PLANE-STATE.yaml`
- the relevant run artifact

## 13. Execution Program

### Stage -1: Bootstrap adoption

This stage is mandatory and precedes all autonomous code work.

Deliverables:
- control-plane directory
- control-plane files
- Wave 2B blocker ledger
- corrected live docs
- tombstoned stale launchers
- retroactive Wave 2B blocked-state history in `SESSION-LOG.md`
- docs-only bootstrap adoption commit

Exit condition:
- a fresh session can recover the blocked Wave 2B state from disk without chat history

### Stage 0: Wave 2B blocked-snapshot remediation

#### 0A. Recovery capture

Before touching code:
- snapshot the current dirty Wave 2B blocker-fix WIP to a recovery patch or recovery branch
- record its checksum and parent candidate in control-plane state

That WIP is recovery evidence only until it is replayed in the clean worktree.

#### 0B. Clean worktree

Create a clean implementation worktree rooted at `4ff7e90`.

The main workspace stays controller/docs only.

#### 0C. Exact open-items table

Before new edits:
- build `WAVE-2B-BLOCKER-REMEDIATION.md`
- enumerate every item from:
  - `WAVE-2B-ADVERSARIAL-REVIEW.md`
  - `WAVE-2B-SECOND-OPINION.md`

Each item must be classified as:
- `open blocker`
- `open non-blocker risk`
- `stale`
- `deferred by policy`

#### 0D. Candidate file manifest

Before editing:
- create `candidate-4ff7e90-file-manifest.md`
- define:
  - allowed write set
  - allowed collateral files
  - denylist
  - suspicious dirty files

Implementation may only touch files on the manifest unless the controller amends it first.

#### 0E. Wave 2B runtime invariants

Wave 2B is only clear when these are proven on the runtime path:

1. LIGHT coverage cannot fail open on failed evaluated tasks.
2. `TaskImportance` and `priority` derive from Step-5 priority scores, not LLM list order.
3. `Evaluator` is built from the effective evaluation profile carried through `ResearchSpec`, not from local remapping.
4. HITL gate decisions are policy-owned via `ProfileExecutionPolicy`, not hardcoded in leaf modules.
5. Sprint-contract generation is load-bearing and malformed output does not silently degrade.
6. `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` affect the real evaluation path, not just stored metadata.
7. emitted observability matches the real runtime weights and decisions.

#### 0F. Wave 2B loop

Loop:

1. replay or re-implement only the open blockers in the clean worktree
2. run the focused proof matrix
3. create candidate commit
4. write implementation artifact
5. run adversarial review
6. run second opinion
7. write clearance synthesis against full `16e0bc7..candidate`
8. if blocked:
   - write fix brief
   - update blocker ledger
   - commit a blocked-state docs checkpoint
   - repeat
9. if cleared:
   - commit a cleared-state reconcile checkpoint
   - create `WAVE-3A-SEAM-FREEZE.md`

No Wave 3 code may begin before Wave 2B is cleared.

### Stage 1: Wave 3A seam freeze

Before substantive Wave 3 implementation, freeze ownership of:

- verifier module
- provenance-sidecar emission point
- round-state persistence location
- deep vs shallow template/prompt wiring
- inner-loop vs outer-loop authority

This seam freeze must be committed before Wave 3 code touches those seams.

### Stage 2: Wave 3 implementation

Wave 3 scope:

- dual-axis taxonomy
- domain-aware routing
- provisional M&A / Restructuring profile paths
- deep-research formalization
- DAG dispatch
- concrete post-synthesis verifier
- provenance sidecar
- remaining E2 concurrency/HITL hardening

Wave 3 exit requires proof that:

1. classifier -> template -> evaluator profile routing is load-bearing
2. DAG dispatch timing and batching are real
3. failed or unevaluated material cannot leak through verifier or sidecar
4. shallow and deep research consume the intended prompt/template path
5. deep-research bypass and governance visibility are real
6. E2 non-regression canaries remain green

### Stage 3: Wave 3B control-path convergence

Wave 3B scope:

- `StructuredOutline`
- thin real Pipeline-L2
- renderer consumes outline
- persisted round-state continuity
- branch coverage between rounds
- sufficiency gate
- novelty exhaustion
- round `N+1` task refinement from uncovered branches, contradictions, and gaps

Single-owner hotspot:
- final orchestrator integration

Wave 3B exit requires proof that:

1. `StructuredOutline` preserves branch/task/claim/citation provenance
2. renderer consumes outline, not raw pre-L2 structures
3. there is exactly one authoritative round controller
4. branch coverage and novelty rules are real on runtime paths
5. round `N+1` work is derived from prior findings, gaps, contradictions, and uncovered branches

### Stage 4: Wave 4 research and polish

Wave 4 has two explicit lanes.

#### 4A. Research lanes

- D-2 actionability
- L1/L1.5 prompt quality
- sprint-contract / rubric content
- template / routing content
- evaluator-verification design

Every memo must declare whether the result is:
- `content-only`
- `existing-seam code`
- `new capability`

If a memo implies new capability rather than content or seam-local code:
- it must be re-scoped out of 4B and into a future capability wave

#### 4B. Polish lane

Carry the binding low-risk Wave 4 polish work explicitly.  
If any polish item is deferred, record the deferral in the active docs.

### Stage 5: Wave 4B content implementation

Dependency rules:

- sprint-contract/rubric content only after Wave 2B clears
- taxonomy/template content only after Wave 3 clears
- actionability/final-content-path work only after Wave 3B clears

Parallelism rules:

- evaluator-content work is **not** presumed disjoint
- sequence:
  1. sprint-contract/rubric content
  2. actionability content
- other slices may run in parallel only if the controller-approved file manifests are truly disjoint

Wave 4B exit requires:

- research-to-code conformity review
- no dead prompt or rubric branches
- D-2 recommendation-creep regressions remain rejected
- before/after fixtures improve for the intended reasons

### Stage 6: Wave 5 calibration

Before Jack scoring, freeze a committed benchmark package containing:

- benchmark corpus
- replay harness
- prompt bundle version
- provider/model settings
- rubric/profile version
- scoring packet

Only then run Jack scoring and calibration.

Wave 5 exit requires:

- thresholds and profile weights changed only from scored evidence
- provisional profile weights finalized or explicitly re-deferred
- calibration rationale documented
- targeted regression evaluation passes

## 14. Restart and Refusal Rules

### 14.1 Recovery order

On restart:

1. read `CONTROL-PLANE-STATE.yaml`
2. read `ACTIVE-HANDOFF.md`
3. read latest immutable review packets
4. read latest immutable synthesis artifact
5. read blocker ledger
6. read `CURRENT-STATE.md`
7. read `WORKSTREAM-STATUS.md`
8. read active wave setup doc
9. read `FINAL-DECISIONS-v2.1.md`
10. read relevant `SESSION-LOG.md` slice
11. read `graphify-out/GRAPH_REPORT.md`

### 14.2 Never recover from dirty HEAD

Recovery must happen in a fresh worktree at:
- `last_cleared_code_commit`, or
- `current_candidate_commit`

The dirty workspace is never an execution baseline.

### 14.3 Startup refusal checks

Before any implementation work, verify:

- active wave matches across control-plane state and handoff
- review packet baseline equals `last_cleared_code_commit`
- review packet target equals `current_candidate_commit`
- candidate ancestry is valid from the cleared baseline
- run-folder artifacts match the same commit pair
- authoritative docs are committed
- stale docs are explicitly demoted
- the active worktree is clean
- the candidate file manifest exists
- the blocker ledger exists

If any check fails, autonomy must stop and reconcile before coding.

## 15. Immediate Next Actions

The next safe actions are:

1. adopt this plan by executing Stage `-1`
2. create the Wave 2B blocker ledger
3. capture the current dirty Wave 2B WIP as recovery evidence
4. create the clean Wave 2B worktree at `4ff7e90`
5. replay only approved blocker-fix work into that worktree
6. create the next Wave 2B candidate commit
7. run adversarial review, second opinion, and controller clearance

That is the first point where safe autonomy begins.
