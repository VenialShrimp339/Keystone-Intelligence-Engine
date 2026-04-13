# W2B-1 Wave 2B Lineage and Closure Audit

- Reviewed prompt snapshot: `df9f0445b7091b7fd0eb32d95bd5d2e1e433610f`
- Prompt-snapshot review checkout: `/tmp/kie-review-df9f044`
- Code review checkouts:
  - blocked candidate: `/tmp/kie-w2b-4ff7e90`
  - cleared candidate: `/tmp/kie-w2b-2cdbfec`
- Dirty main workspace: treated as non-authoritative for code truth
- Subagents: none
- Advisory graph context: `graphify-out/GRAPH_REPORT.md` is absent in the reviewed snapshot `df9f044`; absence recorded and review continued as instructed

## Launch Authority

- `BATCH-2-PLUS-PROMPTS.md:7-28` requires Batch 2 launch decisions to come from `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`, not from snapshot-local sidecars.
- `RETROSPECTIVE-REVIEW-LEDGER.yaml:7-10,14-55` records `CP-1`, `CP-2`, and `RP-1` as currently `CLEARED`, and marks `W2B-1` rerun-required specifically so it is re-evaluated against that authoritative ledger layer.
- This rerun therefore launches legitimately under the current prerequisite model.

## Pinned Commits

- Wave 2A cleared baseline: `16e0bc7`
- Blocked parent candidate: `4ff7e90`
- Blocked candidate parent commit: `c6eecbf`
- Cleared Wave 2B candidate: `2cdbfec`

## Scope and Method

- Read the required W2B-1 materials in the exact prompt order from detached checkout `/tmp/kie-review-df9f044`.
- Verified git lineage directly:
  - `16e0bc7 -> c6eecbf -> 4ff7e90 -> 2cdbfec`
  - `git show --name-only 4ff7e90`
  - `git diff --name-only 16e0bc7..4ff7e90`
  - `git diff --name-only 4ff7e90..2cdbfec`
  - `git diff --name-only 16e0bc7..2cdbfec`
- Confirmed `candidate-4ff7e90-recovery-dirty-wip.patch` applies cleanly to detached checkout `/tmp/kie-w2b-4ff7e90` with `git apply --check`.
- Confirmed the recovery patch file set is an exact match for the 16 code/test files in `git diff --name-only 4ff7e90..2cdbfec`, with only the generated graphify collateral landing outside the patch.
- Re-ran the full Wave 2B proof matrix in detached checkout `/tmp/kie-w2b-2cdbfec`:
  - `tests/unit/governance/test_policy.py`
  - `tests/unit/specification/test_task_generator.py`
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/pipeline/test_orchestrator.py`
  - `tests/unit/evaluator/test_layer3.py`
  - `tests/unit/evaluator/test_evaluator.py`
  - `tests/unit/evaluator/test_sprint_contract.py`
  - `tests/unit/hitl/test_gate.py`
  - `tests/unit/deliberation/test_deliberation.py`
  - `tests/unit/test_research_models.py`
- Result: `151 passed in 5.01s`
- Re-ran a direct runtime probe on `SprintContractGenerator.generate()` in detached checkout `/tmp/kie-w2b-2cdbfec`.
- Result: syntactically valid but under-specified JSON still produced `mandatory_elements=[]`, `anti_patterns=[]`, and `dimension_emphasis={}`.

## Packet / Lineage Findings

### 1. The blocked-parent lineage is documented correctly

- `candidate-4ff7e90-review-synthesis.md:3-18` correctly records:
  - baseline `16e0bc7`
  - candidate parent `c6eecbf`
  - blocked candidate `4ff7e90`
  - the distinction between later recovery-owner references and the exact committed candidate surface
- `candidate-4ff7e90-file-manifest.md:18-29,97-117` reinforces the same rule: the authoritative exact-surface layer comes from `git show --name-only 4ff7e90`, while later replay notes are informational only.
- Actual git agrees with that packet framing:
  - `git show --name-only 4ff7e90` matches the 22 code/test entries listed in `candidate-4ff7e90-file-manifest.md:30-56,60-83`
  - `git diff --name-only 16e0bc7..4ff7e90` adds only the separate docs reconcile at `c6eecbf`; the packets do not misrepresent those docs as part of the exact `4ff7e90` commit surface

### 2. Parent-delta boundary discipline is correct

- `candidate-2cdbfec-file-manifest.md:8-35,69-104` matches the real parent delta exactly:
  - 16 expected code/test files
  - plus legitimate collateral `graphify-out/GRAPH_REPORT.md` and `graphify-out/graph.json`
- The denylist and quarantined-dirty-file notes in `candidate-2cdbfec-file-manifest.md:46-67` exclude the unrelated dirty main-workspace files the controller was already treating as quarantined.
- I did not find Wave 3, 3B, 4, 4B, or 5 leakage in `git diff --name-only 4ff7e90..2cdbfec`.

### 3. Recovery-patch and packet coherence is strong

- `candidate-4ff7e90-review-synthesis.md:62-75` correctly treats the dirty patch as recovery evidence only until replayed in a clean worktree.
- The patch at `candidate-4ff7e90-recovery-dirty-wip.patch` applies cleanly to detached `4ff7e90`.
- Its file set is an exact match for the 16 code/test files in `git diff --name-only 4ff7e90..2cdbfec`.
- The only difference between patch file set and committed parent delta is the generated graphify collateral, which is explicitly classified as legitimate collateral in `candidate-2cdbfec-file-manifest.md:32-35,90-93`.

### 4. Full-baseline clearance truth vs local parent-delta truth is handled correctly

- `candidate-2cdbfec-adversarial-review.md:3-8` and `candidate-2cdbfec-second-opinion.md:3-8` both review the full clearance scope `16e0bc7..2cdbfec`.
- Both packets use `4ff7e90..2cdbfec` only to isolate the recovery delta, which is the correct retrospective distinction for this slice.
- `candidate-2cdbfec-clearance.md:8-16` then grounds clearance in the committed snapshot, full baseline scope, focused proof matrix, and both independent reviews.

### 5. One packet defect remains, but it is non-blocking

- `candidate-2cdbfec-implementation.md:13-20` lists `W2B-R01` among the candidate's claimed closures.
- Later, more authoritative artifacts correct that overstatement:
  - `WAVE-2B-BLOCKER-REMEDIATION.md:192-226`
  - `candidate-2cdbfec-adversarial-review.md:35-41`
  - `candidate-2cdbfec-second-opinion.md:32-39`
  - `candidate-2cdbfec-review-synthesis.md:52-56`
  - `candidate-2cdbfec-clearance.md:33-36`
- I treat this as a packet-coherence defect, not a lineage blocker, because the final review-and-clearance chain preserves the right residual-risk status before controller disposition.

## Runtime Closure Findings

### W2B-B01

- The blocked defect is real in `4ff7e90`: `src/keystone/governance/policy.py:113-118` only treated outcomes as uncovered while they remained `renderable`, so failed evaluated LIGHT output could disappear from coverage after evaluation.
- `2cdbfec` closes that path at `src/keystone/governance/policy.py:113-129` by routing LIGHT coverage through `_requires_light_pass()`.
- Regression proof exists in:
  - `tests/unit/governance/test_policy.py:141-162`
  - `tests/unit/pipeline/test_orchestrator.py:1591-1660`
- The full proof matrix re-run passed.

### W2B-B02

- The blocked defect is real in `4ff7e90`: `src/keystone/specification/task_generator.py:121-156` sets `priority_rank = i + 1` and returns tasks in raw LLM order.
- `2cdbfec` closes that path at `src/keystone/specification/task_generator.py:126-162,232-248` by building ranked branch order from Step-5 scores, deriving importance from that rank, and sorting by resolved priority.
- Regression proof exists in `tests/unit/specification/test_task_generator.py:206-286`.
- The full proof matrix re-run passed.

### W2B-B03

- The blocked defect is real in `4ff7e90`:
  - `src/keystone/specification/spec_engine.py:338-346` does not persist an evaluator-profile field on `ResearchSpec`
  - `src/keystone/pipeline/orchestrator.py:619-624` rebuilds evaluator profile from `engagement_type`
- `2cdbfec` closes that path by:
  - persisting `effective_evaluation_profile` in `src/keystone/models/research.py:170-177`
  - resolving it once in `src/keystone/specification/spec_engine.py:353-357,389-396`
  - routing evaluator construction from the stored field in `src/keystone/pipeline/orchestrator.py:619-624`
- Regression proof exists in:
  - `tests/unit/specification/test_spec_engine.py:280-284`
  - `tests/unit/pipeline/test_orchestrator.py:1486-1545`
  - `tests/unit/test_research_models.py:373-380`
- The full proof matrix re-run passed.

### W2B-B04

- The blocked defect is real in `4ff7e90`:
  - `src/keystone/specification/spec_engine.py:363-365`
  - `src/keystone/deliberation/deliberation.py:190-192`
  - both still inline LIGHT-specific gate behavior
- `2cdbfec` closes that path by routing Gate 1 and Gate 2 through `ProfileExecutionPolicy.should_run_hitl_gate()`:
  - `src/keystone/specification/spec_engine.py:375-386`
  - `src/keystone/deliberation/deliberation.py:190-214`
- Regression proof exists in:
  - `tests/unit/specification/test_spec_engine.py:286-335`
  - `tests/unit/deliberation/test_deliberation.py:351-393`
- A repo-wide `PipelineProfile.LIGHT|should_run_hitl_gate(` search in detached `2cdbfec` found no remaining gate-level LIGHT short-circuit outside policy ownership.

### W2B-R01

- `2cdbfec` does hard-fail parse-invalid JSON at `src/keystone/evaluator/sprint_contract.py:53-61`.
- That behavior is covered by `tests/unit/evaluator/test_sprint_contract.py:158-169`.
- But parseable under-specified JSON still collapses Wave 2B enforcement fields to empties via `src/keystone/evaluator/sprint_contract.py:63-79`.
- My direct detached-checkout probe reproduced that residual risk exactly:
  - `mandatory_elements []`
  - `anti_patterns []`
  - `dimension_emphasis {}`
- The blocker ledger therefore handles `W2B-R01` correctly as narrowed but still open, not as cleared.

### W2B-R02

- `2cdbfec` closes the observability drift by emitting effective adjusted weights from `src/keystone/evaluator/evaluator.py:179-191`.
- Regression proof exists in `tests/unit/evaluator/test_evaluator.py:432-471`.
- The full proof matrix re-run passed.

## Assessment

### Question 1. Was the blocked-parent and recovery lineage documented and constrained correctly?

Yes.

- The lineage pins are correct in git and in the packet family.
- The blocked packet set correctly distinguishes exact committed `4ff7e90` truth from later replay-only recovery context.
- The recovery patch is coherent with the real parent delta.
- The cleared packet set correctly distinguishes full-baseline clearance truth from local parent-delta truth.
- The only issue I found is a non-blocking overstatement around `W2B-R01` in the implementation packet, and the later authoritative review chain corrects it.

### Question 2. Did `2cdbfec` actually close the Wave 2B blocker set on the real runtime path?

Yes.

- I found no surviving blocker in `W2B-B01` through `W2B-B04`.
- The detached-checkout full proof matrix passed.
- The direct runtime probe I ran confirms the residual `W2B-R01` issue still exists in narrowed form, which matches the ledger and clearance packets.
- That residual does not reopen the blocker set and does not invalidate Wave 2B clearance under the documented blocker ledger.

## Verdict

- sub-verdict 1: `blocked-parent lineage` -> `CLEARED`
- sub-verdict 2: `cleared runtime closure` -> `CLEARED`
- top-line: `CLEARED`
