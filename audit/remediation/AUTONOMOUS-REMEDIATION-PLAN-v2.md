# Autonomous Remediation Plan v2

*Created: 2026-04-12 | Status: proposed successor to the earlier autonomous remediation plan*

This plan replaces the earlier autonomy proposal with a stricter control plane.

It is designed to let one controller run the remediation program for a long time with:
- one active code lane
- multiple read-only/planning sidecars
- restart-safe recovery
- immutable review gates
- durable documentation after every material step

The key correction from the adversarial review is simple:

**The main risk is not roadmap quality. The main risk is control-plane drift.**

So this version is built around explicit state, commit-addressed review stages, and hard authority precedence.

---

## 1. Current Truth

The controller must treat these as the current facts:

- Wave 2A is cleared at commit `16e0bc7`.
- Wave 2B implementation exists in commit `4ff7e90`.
- `4ff7e90` is **not cleared**. It is explicitly blocked by:
  - `audit/remediation/WAVE-2B-ADVERSARIAL-REVIEW.md`
  - `audit/remediation/WAVE-2B-SECOND-OPINION.md`
- Therefore the active task is **Wave 2B blocked-snapshot remediation on top of `4ff7e90`**, not “start Wave 2B.”

This plan must not allow any fresh session to infer that Wave 2B is merely “next.”

---

## 2. Authority and State

### 2.1 Authority Order

For remediation control flow, the order of authority is:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `CURRENT-STATE.md`
4. `audit/remediation/WORKSTREAM-STATUS.md`
5. active wave setup doc
6. active blocker-remediation doc
7. latest immutable review packet(s) for the active wave
8. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
9. `SESSION-LOG.md`
10. `CLAUDE.md`, `EXECUTION-GUIDE.md`, `BUILD-PROCESS.md` as background only unless explicitly reconciled

If any higher-priority artifact disagrees with a lower-priority artifact, the lower-priority artifact is stale by definition and must not drive execution.

### 2.2 Controller Lease

There is exactly one controller at a time.

The controller is the only actor allowed to update:
- `CONTROL-PLANE-STATE.yaml`
- `ACTIVE-HANDOFF.md`
- `CURRENT-STATE.md`
- `WORKSTREAM-STATUS.md`
- active wave setup docs
- blocker-remediation docs

All other agents are advisory or implementation-only.

`CONTROL-PLANE-STATE.yaml` must include:
- `controller_epoch`
- `controller_owner`
- `active_branch`
- `active_wave`
- `last_cleared_code_commit`
- `current_candidate_commit`
- `last_docs_reconcile_commit`
- `required_review_stage`
- `accepted_overlays`
- `workspace_policy`
- `model_policy`
- `blocked_on`
- `next_action`
- `latest_review_packets`

### 2.3 Versioned Authority Rule

No file may be called authoritative if it is not committed.

If an “authoritative” doc is only present in the local worktree, the controller must either:
1. commit it, or
2. demote it immediately in `WORKSTREAM-STATUS.md`

---

## 3. Required Control-Plane Artifacts

### 3.1 Mandatory new files

Create and maintain these prospectively:

- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RECOVERY-RULES.md`

### 3.2 Per-wave run folder

Every active wave gets a run folder:

- `audit/remediation/runs/wave-2b/`
- `audit/remediation/runs/wave-3/`
- `audit/remediation/runs/wave-3b/`
- `audit/remediation/runs/wave-4/`
- `audit/remediation/runs/wave-4b/`
- `audit/remediation/runs/wave-5/`

Each candidate commit must generate immutable artifacts in its wave folder:

- `candidate-<commit>-implementation.md`
- `candidate-<commit>-adversarial-review.md`
- `candidate-<commit>-second-opinion.md`
- `candidate-<commit>-clearance.md`
- `candidate-<commit>-review-synthesis.md`
- `candidate-<commit>-fix-brief.md` if blocked

Only the `clearance` artifact may mark a candidate as cleared.

### 3.3 Blocker remediation document

For any blocked wave, create one authoritative blocker file:

- `audit/remediation/WAVE-<N>-BLOCKER-REMEDIATION.md`

For each blocker, record:
- `id`
- `source_review`
- `status`: `open`, `fixed_pending_review`, `fixed_and_reviewed`, `stale`
- `current_disposition`
- `files_to_touch`
- `tests_required`
- `runtime_probe_required`
- `acceptance_invariant`
- `reopen_criteria`

For the current wave, this means creating:
- `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`

before any more autonomous Wave 2B coding.

---

## 4. Review Model

### 4.1 Review stages

Every candidate commit passes through four distinct states:

1. `candidate`
2. `adversarial_reviewed`
3. `second_opinion_reviewed`
4. `cleared`

Only `cleared` may advance:
- `last_cleared_code_commit`
- the wave state
- the next-wave setup

### 4.2 Committed-snapshot-only rule

No dirty-tree review is binding.

Every review must:
- use a committed snapshot only
- run in a detached worktree or equivalent isolated snapshot
- name exact baseline and target commits

Every blocker fix must produce a new candidate commit.
Every new candidate commit must get new review artifacts keyed to that exact commit.

### 4.3 Mandatory contents of every review packet

Each review artifact must include:
- baseline commit
- target commit
- exact diff scope
- focused verification matrix
- runtime probes for the high-risk seams
- findings ordered by severity
- explicit stale-vs-open disposition for older blocker items
- verdict: `BLOCKED` or `CLEARED`

### 4.4 When second opinion is mandatory

Second opinion is mandatory whenever the commit touches any of:
- `src/keystone/pipeline/`
- `src/keystone/governance/`
- `src/keystone/evaluator/`
- `src/keystone/citation/`
- `src/keystone/contracts.py`
- live remediation control docs

Graphify is advisory only. Path-based triggers are mandatory; graph-centrality is not.

---

## 5. Restart and Recovery

### 5.1 Recovery source of truth

Never recover from dirty `HEAD`.

On restart:
1. Read `CONTROL-PLANE-STATE.yaml`
2. Read `ACTIVE-HANDOFF.md`
3. Read `CURRENT-STATE.md`
4. Read the active wave setup doc
5. Read the active blocker-remediation doc
6. Read the latest review artifacts for the active candidate
7. Read the relevant `SESSION-LOG.md` slice
8. Read `graphify-out/GRAPH_REPORT.md`

### 5.2 Fresh-worktree rule

Recovery must happen in a fresh worktree or equivalent clean checkout at one of:
- `last_cleared_code_commit`, or
- `current_candidate_commit`

The live dirty workspace is not an execution baseline.

### 5.3 Dirty-state quarantine

If the workspace is dirty on restart:
- classify all dirty content as `UNREVIEWED_WIP`
- snapshot it to a recovery patch or recovery branch
- do not treat it as the active baseline

The controller must explicitly decide whether to:
- discard it from the active lane
- promote part of it into the next candidate
- or preserve it as non-authoritative recovery material

### 5.4 Startup refusal checks

Before any coding begins, the controller must refuse to proceed if:
- `HEAD` disagrees with `CONTROL-PLANE-STATE.yaml`
- `CURRENT-STATE.md` disagrees with `WORKSTREAM-STATUS.md`
- the active wave differs across state files
- the candidate commit is missing its review artifacts
- a lower-priority doc still claims a superseded step is active

If any of these happen, reconcile docs first.

---

## 6. Model Policy

Use **GPT-5.4 with xhigh reasoning** for every spawned agent by default.

This applies to:
- implementation lane
- adversarial review
- second opinion
- clearance review
- blocker-fix sessions
- planning sidecars
- prework and research sidecars

If any session must use a different model or reasoning level, record that deviation in:
- `CONTROL-PLANE-STATE.yaml`
- the relevant run artifact

---

## 7. Execution Program

## Stage 0: Wave 2B blocked-snapshot remediation

This is the immediate next stage.

### 0A. Control-plane reconciliation before more code

Before any new Wave 2B code session:

1. Reconcile the live docs so they state:
   - Wave 2B implementation exists in `4ff7e90`
   - `4ff7e90` is blocked
   - next task is Wave 2B blocker remediation
2. Create `CONTROL-PLANE-STATE.yaml`
3. Create `ACTIVE-HANDOFF.md`
4. Create `WAVE-2B-BLOCKER-REMEDIATION.md`

This is a docs-only checkpoint.

### 0B. Wave 2B invariants

Wave 2B is only clear when these invariants are true in the runtime path:

1. LIGHT coverage cannot fail open on failed evaluated tasks.
2. `TaskImportance` and `priority` derive from Step-5 priority scores, not LLM list order.
3. `Evaluator` is constructed from the effective evaluation profile carried through `ResearchSpec`, not local remapping.
4. HITL gate decisions are policy-owned via `ProfileExecutionPolicy`, not hardcoded in leaf modules.
5. `SprintContractGenerator` is load-bearing and malformed output does not silently degrade to a bare contract.
6. `dimension_emphasis`, `mandatory_elements`, and `anti_patterns` affect the real evaluation path, not just stored metadata.

### 0C. Wave 2B loop

Loop:
1. implementation session against the open blockers only
2. candidate commit
3. adversarial review
4. second opinion
5. clearance review
6. if blocked, write `fix-brief` and repeat
7. if cleared, docs-only reconcile and create `WAVE-3-SETUP.md`

No Wave 3 coding starts before Wave 2B is cleared.

---

## Stage 1: Wave 3 stabilization

Wave 3 scope:
- dual-axis taxonomy
- domain-aware routing
- provisional M&A / Restructuring profile paths
- deep-research formalization
- DAG dispatch
- concrete post-synthesis verifier
- provenance sidecar
- remaining E2 concurrency/HITL hardening

### 1A. Wave 3 seam freeze

Before Wave 3B can begin, Wave 3 must freeze these decisions explicitly:
- verifier module ownership
- provenance-sidecar ownership point
- round-state persistence location
- inner-loop vs outer-loop authority

This is mandatory. No 3B implementation may begin without it.

### 1B. Parallelism rules

Safe sidecars:
- taxonomy/routing scope guard
- verifier/provenance prework
- deep-research formalization review
- Wave 3 review-prompt prep

Not safe in parallel:
- multiple writers to `pipeline/orchestrator.py`
- final sidecar/render-path insertion
- loop-control integration

### 1C. Wave 3 exit gate

Wave 3 is only clear when all of the following are true:

1. classifier -> template -> evaluator profile routing is load-bearing end-to-end
2. DAG dispatch timing/batching is proven on the runtime path
3. failed or unevaluated material cannot leak back through verifier or provenance sidecar
4. E2 non-regression canaries remain green
5. seam-freeze decisions are written into the active docs

---

## Stage 2: Wave 3B control-path convergence

Wave 3B scope:
- `StructuredOutline`
- thin real Pipeline-L2
- renderer consumes the outline
- persisted round-state continuity
- branch coverage between rounds
- sufficiency gate
- novelty exhaustion
- round `N+1` task refinement from uncovered branches, contradictions, and gaps

### 2A. Single-owner hotspot

The final orchestrator integration for Wave 3B has one owner.

No parallel code writers may simultaneously edit:
- `src/keystone/pipeline/orchestrator.py`
- the final round-control path
- final outline insertion points

### 2B. Wave 3B exit gate

Wave 3B is only clear when:

1. `StructuredOutline` preserves task, claim, branch, and citation provenance
2. renderer consumes the outline, not raw pre-L2 structures
3. there is exactly one authoritative round controller
4. branch-coverage and novelty rules are proven on real runtime paths
5. round `N+1` work is derived from prior findings, gaps, contradictions, and uncovered branches

---

## Stage 3: Wave 4 research program

Wave 4 remains planning/research only.

Required research lanes:
- D-2 actionability
- L1/L1.5 prompt quality
- sprint-contract / rubric content
- template / routing content
- evaluator-verification design

Each memo must include:
- observed problem
- architecture boundary
- runtime consumer
- positive/negative examples
- regression ideas
- prerequisite wave
- explicit statement whether the outcome is:
  - `content-only`
  - `existing-seam code`
  - `new capability`

This last field is critical for 4B scoping.

---

## Stage 4: Wave 4B content implementation

Only content work whose seams are already stable may be implemented here.

### 4A. 4B rescope rule

If a Wave 4 memo concludes the fix requires:
- a new evaluator capability
- a new verifier capability
- new fetch/retrieval behavior
- new pipeline stage behavior

then it does **not** stay in 4B automatically.
It must be re-scoped into a later architecture wave.

### 4B. Safe slices

Parallel slices are allowed only when write sets are disjoint:
- evaluator-content slice
- research-prompt slice
- sprint-contract/rubric slice
- routing/template slice
- verifier-content rules slice

Each slice must move:
- prompt/rubric/template content
- runtime consumer
- fixtures
- tests

together under one owner.

### 4C. Wave 4B exit gate

Wave 4B is only clear when:
- research-to-code conformity review passes
- no dead prompt/rubric branches remain
- recommendation creep is still rejected under D-2
- before/after fixtures improve for the intended reasons

---

## Stage 5: Wave 5 calibration

Wave 5 is empirical calibration only after the content/runtime stack is stable.

### 5A. Autonomous portion

Prepare:
- 5 to 10 representative outputs
- exact rubric/profile/version packet for each
- scoring packet for Jack
- calibration memo template in advance

### 5B. External dependency

Jack scoring is required to complete Wave 5.

### 5C. Wave 5 exit gate

Wave 5 is only clear when:
- thresholds/profile weights changed only from scored evidence
- provisional M&A / Restructuring weights are finalized or explicitly re-deferred
- calibration rationale is documented
- targeted regression evaluation passes

---

## 8. Parallelism Rules

### Allowed

- one active code lane
- multiple review sidecars
- multiple planning/research sidecars
- review-prompt generation
- test-matrix planning
- future-wave decomposition

### Not allowed

- multiple code writers on the active wave
- next-wave code before current-wave clearance
- dirty-tree review as a binding gate
- sidecar planning artifacts silently changing active-wave scope

---

## 9. Documentation Rules

Every material loop must leave durable evidence.

### After every implementation candidate

Update or create:
- candidate implementation artifact
- focused test results
- candidate commit

### After every review

Update or create:
- review artifact
- review synthesis
- blocker-remediation doc status
- control-plane state

### After every wave clearance

Update or create:
- `CURRENT-STATE.md`
- `WORKSTREAM-STATUS.md`
- active wave setup doc
- `SESSION-LOG.md`
- control-plane state
- next-wave setup doc

### Session log rule

`SESSION-LOG.md` is append-only history.
It is never the live source of truth.

---

## 10. Immediate Next Actions

Before any more autonomous coding:

1. Create `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. Create `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. Create `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
4. Reconcile `CURRENT-STATE.md`, `WORKSTREAM-STATUS.md`, and `WAVE-2B-SETUP.md` so they describe Wave 2B as:
   - implemented at `4ff7e90`
   - blocked
   - awaiting blocker remediation
5. Only then launch the next Wave 2B blocker-remediation code session

That is the correct starting point for safe autonomy.
