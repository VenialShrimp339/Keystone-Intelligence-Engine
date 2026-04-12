# Autonomous Remediation Plan v3

*Created: 2026-04-12 | Status: hardened replacement for v2 after second deep adversarial review*

This version is the first autonomy plan that is intended to be safe to adopt.

It exists because the adversarial reviews converged on one conclusion:

**The roadmap is broadly right. The unsafe part is startup, authority, proof, and recovery.**

So v3 makes four changes that v2 still lacked:

1. an explicit **bootstrap phase**
2. a mandatory **clean implementation worktree**
3. a **proof-obligation contract** for blocker closure
4. a stricter **authority and review precedence model**

---

## 1. Current Truth

The controller must treat these as the current facts:

- Wave 2A is cleared at `16e0bc7`.
- Wave 2B implementation exists at `4ff7e90`.
- `4ff7e90` is **blocked**, not cleared.
- The active task is **Wave 2B blocked-snapshot remediation on top of `4ff7e90`**.
- The live docs currently do **not** consistently reflect that truth.

Therefore:
- no autonomous code lane may start from the current live docs as-is
- a bootstrap reconciliation commit is required first

---

## 2. Bootstrap Mode

Bootstrap mode exists because the future control-plane files do not exist yet.

### 2.1 Bootstrap authority order

Until the bootstrap adoption commit exists, use this temporary order:

1. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v3.md`
2. latest immutable Wave 2B review packets
3. `CURRENT-STATE.md`
4. `audit/remediation/WORKSTREAM-STATUS.md`
5. `audit/remediation/WAVE-2B-SETUP.md`
6. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
7. `SESSION-LOG.md`
8. all other docs as background only

Bootstrap mode ends only when the bootstrap adoption commit lands.

### 2.2 Bootstrap adoption commit

Before any new autonomous implementation work:

1. create the control-plane directory and files
2. reconcile the live docs to blocked-`4ff7e90` reality
3. patch or tombstone stale entrypoint docs
4. commit those changes together as one docs-only bootstrap commit

No code-writing lane may begin before that commit exists.

---

## 3. Authority, Lease, and State

### 3.1 Post-bootstrap authority order

After the adoption commit, the remediation authority order is:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. latest immutable review packet(s) for the active candidate
4. active blocker-remediation doc
5. `CURRENT-STATE.md`
6. `audit/remediation/WORKSTREAM-STATUS.md`
7. active wave setup doc
8. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
9. `SESSION-LOG.md`
10. `CLAUDE.md`, `EXECUTION-GUIDE.md`, `BUILD-PROCESS.md`, and other legacy docs as background only

Review truth must outrank status/setup docs.

### 3.2 Controller lease

There is exactly one controller at a time.

Only the controller may update:
- `CONTROL-PLANE-STATE.yaml`
- `ACTIVE-HANDOFF.md`
- `CURRENT-STATE.md`
- `WORKSTREAM-STATUS.md`
- active wave setup docs
- blocker-remediation docs

`CONTROL-PLANE-STATE.yaml` must contain:
- `controller_epoch`
- `lease_owner`
- `lease_acquired_at`
- `lease_heartbeat_at`
- `lease_expires_at`
- `lease_takeover_rule`
- `lease_stolen_by`
- `active_branch`
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

### 3.3 Lease rules

Lease semantics are mandatory:

- no state mutation is valid without an active lease
- the controller must heartbeat after every material stage transition
- if the lease expires, a new controller may take over only by:
  - incrementing `controller_epoch`
  - updating the lease fields
  - recording the takeover in `ACTIVE-HANDOFF.md`

### 3.4 Versioned authority rule

After bootstrap:
- no file in the authority stack may advance state unless it is committed
- pre-bootstrap review packets may be used as `bootstrap evidence`
- after bootstrap, every new authoritative artifact must be committed before it can change wave state

---

## 4. Required Control-Plane Artifacts

### 4.1 Mandatory control-plane files

Create and maintain:

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RECOVERY-RULES.md`

### 4.2 Required `ACTIVE-HANDOFF.md` schema

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

A sleeping user should be able to read only this file and know what to do next.

### 4.3 Active state tuple

The controller must serialize this tuple in both control-plane state and handoff:

- `active_wave`
- `active_state`: `planned | implementing | under_review | blocked | cleared`
- `execution_baseline_commit`
- `review_target_commit`
- `docs_reconcile_commit`
- `next_recovery_checkout`

### 4.4 Per-wave run folders

Every active wave gets a run folder:

- `audit/remediation/runs/wave-2b/`
- `audit/remediation/runs/wave-3/`
- `audit/remediation/runs/wave-3b/`
- `audit/remediation/runs/wave-4/`
- `audit/remediation/runs/wave-4b/`
- `audit/remediation/runs/wave-5/`

Each candidate commit gets immutable artifacts:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-clearance.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-fix-brief.md` if blocked
- `candidate-<commit>-file-manifest.md`

### 4.5 Blocker-remediation docs

Every blocked wave needs one authoritative blocker file:

- `audit/remediation/WAVE-<N>-BLOCKER-REMEDIATION.md`

Each blocker row must include:
- `blocker_id`
- `failure_family`
- `source_review`
- `blocked_candidate_commit`
- `status`: `open | fixed_pending_review | fixed_and_reviewed | stale | deferred_by_policy`
- `current_disposition`
- `files_to_touch`
- `stageable_files`
- `tests_required`
- `runtime_probe_required`
- `acceptance_invariant`
- `pre_fix_red_evidence`
- `post_fix_green_evidence`
- `verification_evidence`
- `review_packet_refs`
- `fix_commit`
- `reopen_criteria`
- `owner_prompt_ref`

For the immediate next step, create:
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`

---

## 5. Workspace and Branch Model

### 5.1 Main workspace rule

The main workspace becomes **controller/docs only**.

It must not be used as the active implementation lane.

### 5.2 Active implementation lane

The active code lane always runs in a **dedicated clean worktree** rooted at:
- the blocked candidate commit, or
- the last cleared baseline

For the immediate Stage 0 work, that means the code lane must run in a clean worktree rooted at `4ff7e90`.

### 5.3 Branch rules

Use:
- one dedicated remediation branch for the controller, e.g. `codex/remediation-program`
- one active wave integration branch, e.g. `codex/remediation-wave-2b`

`main` is read-only for remediation.

### 5.4 Worktree lifecycle

The controller must track:
- one controller/docs workspace
- one active implementation worktree
- zero or more detached review worktrees

Detached review worktrees must be pruned immediately after:
- clearance
- supersession by a newer candidate
- or explicit abandonment

### 5.5 Dirty WIP classification

Before a new implementation lane starts, current dirty state must be classified as:
- `candidate_delta`
- `quarantined_wip`
- `unrelated_user_change`
- `generated_artifact`

No dirty state may be promoted unless it is tied to:
- a parent candidate commit
- a recovery artifact path/hash
- an allowed write set

---

## 6. Review Model

### 6.1 Review stages

Each candidate commit passes through:

1. `candidate`
2. `adversarial_reviewed`
3. `second_opinion_reviewed`
4. `cleared`

Only `cleared` may advance:
- `last_cleared_code_commit`
- wave state
- next-wave setup

### 6.2 Review roles

- `adversarial review`: first independent read-only review
- `second opinion`: parallel independent review
- `clearance`: controller-produced synthesis artifact, not a free-form third review

If the first two reviews disagree materially, the candidate remains blocked until synthesis resolves the disagreement or a third targeted review is commissioned.

### 6.3 Committed-snapshot-only rule

No dirty-tree review is binding.

Every review must:
- use a committed snapshot only
- run in a detached worktree or equivalent isolated snapshot
- record exact baseline and target commits

Every blocker fix must produce a new candidate commit.
Every new candidate commit must receive new review artifacts.

### 6.4 Baseline rule

Every candidate is reviewed against:
- `wave_baseline_commit`
- and optionally `previous_candidate..current_candidate` for local diffs

But:
- the clearance verdict must always be grounded in the **full** `wave_baseline..candidate` scope

This prevents cumulative regression blindness.

### 6.5 Mandatory contents of every review packet

Each review artifact must include:
- `wave_baseline_commit`
- `candidate_parent_commit`
- baseline commit
- target commit
- exact diff scope
- focused verification matrix
- named runtime probes
- findings ordered by severity
- stale-vs-open blocker disposition
- verdict: `BLOCKED` or `CLEARED`

### 6.6 Proof-obligation rule

Every blocker must be closed by a proof-obligation table in both:
- the blocker-remediation doc
- the `candidate-<commit>-clearance.md`

Required columns:
- `blocker_id`
- `runtime_invariant`
- `owner_path`
- `named_tests`
- `named_runtime_probes`
- `pre_fix_red_evidence`
- `post_fix_green_evidence`
- `reviewer_disposition`

No candidate may clear with an incomplete row.

### 6.7 Non-vacuous proof rule

For each blocker:
- at least one test or probe must execute the **real enforcing seam**
- mocked-path tests may supplement but cannot substitute
- closure requires either:
  - red evidence on the blocked snapshot, or
  - red evidence under a deliberate bypass mutation

### 6.8 Mandatory second-opinion triggers

Second opinion is mandatory for any commit touching:
- `src/keystone/pipeline/`
- `src/keystone/governance/`
- `src/keystone/evaluator/`
- `src/keystone/citation/`
- `src/keystone/contracts.py`
- `src/keystone/models/`
- `src/keystone/specification/`
- `src/keystone/research/`
- `src/keystone/knowledge/`
- live remediation control docs

It is also mandatory for any change touching:
- `StructuredFinding`
- `ResearchTask`
- `CitationManifest`
- `EngagementSpec`
- `ResearchSpec`
- `StructuredOutline`
- round-state persistence
- runtime enforcement decisions
- profile routing
- review gating

Docs-only reconcile commits are exempt from full second opinion, but they still require a controller consistency check.

---

## 7. Restart and Recovery

### 7.1 Recovery order

On restart:
1. read `CONTROL-PLANE-STATE.yaml`
2. read `ACTIVE-HANDOFF.md`
3. read latest immutable review packets
4. read the active blocker-remediation doc
5. read `CURRENT-STATE.md`
6. read `WORKSTREAM-STATUS.md`
7. read the active wave setup doc
8. read `FINAL-DECISIONS-v2.1.md`
9. read the relevant `SESSION-LOG.md` slice
10. read `graphify-out/GRAPH_REPORT.md`

### 7.2 Never recover from dirty `HEAD`

Recovery must happen in a fresh worktree at:
- `last_cleared_code_commit`, or
- `current_candidate_commit`

The live dirty workspace is never an execution baseline.

### 7.3 Startup refusal checks

Before any implementation work:
- verify the active wave matches across control-plane state and handoff
- verify review packet baseline equals `last_cleared_code_commit`
- verify review packet target equals `current_candidate_commit`
- verify candidate ancestry from the cleared baseline
- verify run-folder artifacts are keyed to the same commit pair
- verify authority docs are committed
- verify stale lower-priority docs are either reconciled or explicitly demoted

If any fail, autonomy must stop for reconciliation.

---

## 8. Sidecar Policy

Every sidecar must declare a manifest before it starts:
- objective
- read set
- write set
- output path
- authority level: always `advisory` unless explicitly promoted
- expiry condition
- whether it may touch live docs

No sidecar output may alter the active loop until the controller triages it.

Review sidecars may emit findings.
Fix sidecars may prepare patches against a candidate commit.
Only the single code lane may apply patches and create a new candidate.

---

## 9. Model Policy

Use **GPT-5.4 with xhigh reasoning** for every spawned agent by default.

This is an explicit user preference and overrides cost/latency objections.

If any session must deviate, record that deviation in:
- `CONTROL-PLANE-STATE.yaml`
- the relevant run artifact

---

## 10. Execution Program

## Stage -1: Bootstrap adoption

This stage must happen before any autonomous implementation.

Deliverables:
1. create `audit/remediation/control-plane/`
2. create `CONTROL-PLANE-STATE.yaml`
3. create `ACTIVE-HANDOFF.md`
4. create `RECOVERY-RULES.md`
5. reconcile:
   - `CURRENT-STATE.md`
   - `WORKSTREAM-STATUS.md`
   - `WAVE-2B-SETUP.md`
6. append a retroactive `SESSION-LOG.md` entry for the Wave 2B candidate `4ff7e90` and its blocked reviews
7. add top-of-file tombstone banners or redirects to:
   - `CLAUDE.md`
   - `EXECUTION-GUIDE.md`
   - `BUILD-PROCESS.md`
   - any other stale “single source” or “follow this first” docs
8. commit all of the above as one docs-only bootstrap adoption commit

No code lane starts before this commit exists.

## Stage 0: Wave 2B blocked-snapshot remediation

### 0A. Execution worktree creation

Create a clean implementation worktree rooted at `4ff7e90`.

The main workspace remains controller/docs only.

### 0B. Exact open-items table

Before more code:
- build `WAVE-2B-BLOCKER-REMEDIATION.md`
- enumerate every item from:
  - `WAVE-2B-ADVERSARIAL-REVIEW.md`
  - `WAVE-2B-SECOND-OPINION.md`

Each item must be classified as:
- `open blocker`
- `open non-blocker risk`
- `stale`
- `deferred by policy`

No implementation prompt may launch before this table exists.

### 0C. Candidate file manifest

Before editing:
- create `candidate-<commit>-file-manifest.md` for the active blocked candidate
- define:
  - allowed write set
  - allowed collateral files
  - explicit denylist
  - suspicious dirty files

Implementation sessions may only touch files on that manifest unless the controller amends it first.

### 0D. Wave 2B proof obligations

Wave 2B is only clear when these runtime invariants are proven with named tests/probes:

1. LIGHT coverage cannot fail open on failed evaluated tasks.
2. `TaskImportance` and `priority` derive from Step-5 priority scores, not LLM list order.
3. `Evaluator` is constructed from the effective evaluation profile carried through `ResearchSpec`, not local remapping.
4. HITL gate decisions are policy-owned via `ProfileExecutionPolicy`, not hardcoded in leaf modules.
5. `SprintContractGenerator` is load-bearing and malformed output does not silently degrade to a bare contract.
6. `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` affect the real evaluation path, not just stored metadata.
7. observability reflects actual runtime behavior, not stale base metadata.

### 0E. Wave 2B loop

Loop:
1. implement only open blockers in the clean worktree
2. create candidate commit
3. run adversarial review
4. run second opinion
5. produce controller clearance artifact against the full `16e0bc7..candidate` scope
6. if blocked:
   - write fix brief
   - update blocker-remediation doc
   - do a blocked-state docs checkpoint
   - repeat
7. if cleared:
   - do a docs-only reconcile commit
   - create `WAVE-3-SETUP.md`

No Wave 3 code may begin before Wave 2B is cleared.

---

## Stage 1: Wave 3A seam freeze

Before substantive Wave 3 implementation, freeze:
- verifier module ownership
- provenance-sidecar ownership point
- round-state persistence location
- deep vs shallow template-prompt wiring ownership
- inner-loop vs outer-loop authority

This freeze is required before Wave 3 code touches those seams.

## Stage 2: Wave 3 implementation

Wave 3 scope:
- dual-axis taxonomy
- domain-aware routing
- provisional M&A / Restructuring profile paths
- deep-research formalization
- DAG dispatch
- concrete post-synthesis verifier
- provenance sidecar
- remaining E2 concurrency/HITL hardening

Wave 3 exit requires proof of:
1. classifier -> template -> evaluator profile routing is load-bearing
2. DAG dispatch timing/batching is proven on the runtime path
3. failed/unevaluated material cannot leak through verifier or sidecar
4. shallow and deep research both consume the intended template prompt path
5. deep-research bypass/governance visibility is real
6. E2 non-regression canaries remain green

Only after this can Wave 3B begin.

## Stage 3: Wave 3B control-path convergence

Wave 3B scope:
- `StructuredOutline`
- thin real Pipeline-L2
- renderer consumes the outline
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
5. round `N+1` work is derived from prior findings/gaps/contradictions and uncovered branches

---

## Stage 4: Wave 4 research and polish

Wave 4 has two explicit lanes:

### 4A. Research lanes
- D-2 actionability
- L1/L1.5 prompt quality
- sprint-contract / rubric content
- template / routing content
- evaluator-verification design

Every memo must declare whether the result is:
- `content-only`
- `existing-seam code`
- `new capability`

### 4B. Polish lane

Carry the binding low-risk Wave 4 polish work explicitly.

If any polish item is deferred, record the deferral explicitly in the active docs.

---

## Stage 5: Wave 4B content implementation

Dependency rules:
- sprint-contract/rubric content only after Wave 2B clears
- taxonomy/template content only after Wave 3 clears
- actionability/final-content-path work only after Wave 3B clears

Parallelism:
- evaluator-content work is **not** assumed disjoint
- sequence:
  1. sprint-contract/rubric content
  2. actionability content

Other slices may run in parallel only if write sets are actually disjoint and controller-approved.

Wave 4B exit requires:
- research-to-code conformity review
- no dead prompt/rubric branches
- D-2 recommendation-creep regressions still rejected
- before/after fixtures improve for the intended reasons

---

## Stage 6: Wave 5 calibration

Before Jack scoring, freeze a committed benchmark package:
- benchmark corpus
- replay harness
- prompt bundle version
- provider/model settings
- rubric/profile version
- scoring packet

Only then run Jack scoring and calibration.

Wave 5 exit requires:
- thresholds/profile weights changed only from scored evidence
- provisional profile weights finalized or explicitly re-deferred
- calibration rationale documented
- targeted regression evaluation passes

---

## 11. Documentation Rules

After every `BLOCKED` verdict:
- update `CONTROL-PLANE-STATE.yaml`
- update `ACTIVE-HANDOFF.md`
- update blocker-remediation doc
- append `SESSION-LOG.md`
- reconcile `CURRENT-STATE.md` / `WORKSTREAM-STATUS.md` enough that they no longer claim an outdated next step
- commit those docs as a docs-only blocked-state checkpoint

After every `CLEARED` verdict:
- same as above
- plus next-wave setup doc

`SESSION-LOG.md` remains append-only history only.

---

## 12. Immediate Next Actions

The next safe steps are:

1. Execute Stage `-1` bootstrap adoption.
2. Then create the Wave 2B clean implementation worktree from `4ff7e90`.
3. Then build the exact open-items table in `WAVE-2B-BLOCKER-REMEDIATION.md`.
4. Then launch the next Wave 2B blocker-remediation session from the clean worktree only.

That is the first point where safe autonomy begins.
