# Wave 2B Blocker Remediation

*Created: 2026-04-12 | Updated: 2026-04-12 | Status: authoritative closure ledger for cleared candidate `2cdbfec`*

## Current Wave State

- Baseline commit: `16e0bc7`
- Previously blocked candidate commit: `4ff7e90`
- Cleared candidate commit: `2cdbfec`
- Current state: `cleared`
- Dirty Wave 2B recovery evidence at:
  - [candidate-4ff7e90-recovery-dirty-wip.patch](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/runs/wave-2b/candidate-4ff7e90-recovery-dirty-wip.patch)
- Rule: the dirty recovery evidence is now superseded by the replayed clean candidate `2cdbfec`

## Closed Blockers

### W2B-B01

- `blocker_id`: `W2B-B01`
- `failure_family`: `coverage_fail_open`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-ADVERSARIAL-REVIEW.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed by clean replay candidate 2cdbfec and cleared by both independent reviews.`
- `files_to_touch`:
  - `src/keystone/governance/policy.py`
  - `src/keystone/pipeline/orchestrator.py`
  - `tests/unit/governance/test_policy.py`
  - `tests/unit/pipeline/test_orchestrator.py`
- `stageable_files`:
  - `src/keystone/governance/policy.py`
  - `src/keystone/pipeline/orchestrator.py`
  - `tests/unit/governance/test_policy.py`
  - `tests/unit/pipeline/test_orchestrator.py`
- `tests_required`:
  - `tests/unit/governance/test_policy.py`
  - `tests/unit/pipeline/test_orchestrator.py`
- `runtime_probe_required`: `Probe that a LIGHT task with failed L4 output still halts coverage instead of disappearing from coverage.`
- `required_regression_test`: `A LIGHT task that is evaluated and fails must still trigger a halt.`
- `required_regression_probe`: `Direct object-level or pipeline-level probe with evaluation_status=failed after evaluation.`
- `acceptance_invariant`: `LIGHT coverage cannot fail open on failed evaluated tasks.`
- `pre_fix_red_evidence`: `Adversarial review finding 1 plus direct probe on 4ff7e90 returning coverage None after a failed LIGHT evaluation.`
- `post_fix_green_evidence`: candidate-2cdbfec-implementation.md records a green matrix plus targeted probe node tests for failed LIGHT coverage on both policy and orchestrator paths.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md, candidate-2cdbfec-second-opinion.md, and candidate-2cdbfec-clearance.md all confirm closure.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where a failed evaluated LIGHT task becomes non-renderable before coverage is enforced.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

### W2B-B02

- `blocker_id`: `W2B-B02`
- `failure_family`: `priority_misrouting`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-ADVERSARIAL-REVIEW.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed by clean replay candidate 2cdbfec and cleared by both independent reviews.`
- `files_to_touch`:
  - `src/keystone/specification/task_generator.py`
  - `tests/unit/specification/test_task_generator.py`
- `stageable_files`:
  - `src/keystone/specification/task_generator.py`
  - `tests/unit/specification/test_task_generator.py`
- `tests_required`:
  - `tests/unit/specification/test_task_generator.py`
- `runtime_probe_required`: `Probe that the highest Step-5-scored branch becomes PRIMARY even if it is listed second by the LLM.`
- `required_regression_test`: `Higher-scored branch returned second must still outrank the first-listed branch.`
- `required_regression_probe`: `Construct a mismatched order case and inspect resulting priority and importance.`
- `acceptance_invariant`: `Task priority and importance derive from Step-5 scores, not LLM list order.`
- `pre_fix_red_evidence`: `Adversarial review finding 2 plus direct probe on 4ff7e90 where a lower-scored first-listed branch became PRIMARY.`
- `post_fix_green_evidence`: candidate-2cdbfec-implementation.md records targeted probe coverage for a later-listed higher-scored branch winning PRIMARY priority.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md, candidate-2cdbfec-second-opinion.md, and candidate-2cdbfec-clearance.md all confirm closure.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where task importance or priority is still tied to raw generation order.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

### W2B-B03

- `blocker_id`: `W2B-B03`
- `failure_family`: `effective_profile_shadowing`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-ADVERSARIAL-REVIEW.md + WAVE-2B-SECOND-OPINION.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed by persisting the effective evaluation profile on ResearchSpec and routing Evaluator from that stored field in 2cdbfec.`
- `files_to_touch`:
  - `src/keystone/models/research.py`
  - `src/keystone/specification/spec_engine.py`
  - `src/keystone/pipeline/orchestrator.py`
  - `src/keystone/evaluator/evaluator.py`
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/pipeline/test_orchestrator.py`
  - `tests/unit/evaluator/test_evaluator.py`
  - `tests/unit/test_research_models.py`
- `stageable_files`:
  - `src/keystone/models/research.py`
  - `src/keystone/specification/spec_engine.py`
  - `src/keystone/pipeline/orchestrator.py`
  - `src/keystone/evaluator/evaluator.py`
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/pipeline/test_orchestrator.py`
  - `tests/unit/evaluator/test_evaluator.py`
  - `tests/unit/test_research_models.py`
- `tests_required`:
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/pipeline/test_orchestrator.py`
  - `tests/unit/evaluator/test_evaluator.py`
  - `tests/unit/test_research_models.py`
- `runtime_probe_required`: `Probe a mismatched engagement/effective-profile case and confirm Evaluator uses the effective profile from ResearchSpec, not a local remap.`
- `required_regression_test`: `A case like EVALUATIVE + DEEP must fail if local profile remapping is reintroduced.`
- `required_regression_probe`: `Inspect the evaluator construction path and the emitted profile in runtime data.`
- `acceptance_invariant`: `Evaluator is built from the effective evaluation profile carried through ResearchSpec.`
- `pre_fix_red_evidence`: `Adversarial review finding 3 plus second-opinion finding 2; direct probe on 4ff7e90 produced default profile with varying intensity only.`
- `post_fix_green_evidence`: candidate-2cdbfec-implementation.md records targeted probe coverage for the persisted evaluation-profile path plus the full focused matrix.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md, candidate-2cdbfec-second-opinion.md, and candidate-2cdbfec-clearance.md all confirm closure.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where evaluator profile is re-derived from engagement type or local mapping instead of ResearchSpec.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

### W2B-B04

- `blocker_id`: `W2B-B04`
- `failure_family`: `policy_ownership_duplication`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-SECOND-OPINION.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed by routing Gate 1 and Gate 2 through ProfileExecutionPolicy.should_run_hitl_gate() in 2cdbfec.`
- `files_to_touch`:
  - `src/keystone/governance/policy.py`
  - `src/keystone/specification/spec_engine.py`
  - `src/keystone/deliberation/deliberation.py`
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
- `stageable_files`:
  - `src/keystone/governance/policy.py`
  - `src/keystone/specification/spec_engine.py`
  - `src/keystone/deliberation/deliberation.py`
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
- `tests_required`:
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
  - `tests/unit/governance/test_policy.py`
  - `tests/unit/hitl/test_gate.py`
- `runtime_probe_required`: `Probe that Gate 1 and Gate 2 both consult ProfileExecutionPolicy on the real runtime path.`
- `required_regression_test`: `LIGHT skip and non-LIGHT block behavior must be asserted against the shared policy path.`
- `required_regression_probe`: `Inspect Gate 1 and Gate 2 behavior under policy changes without leaf-level special casing.`
- `acceptance_invariant`: `HITL gate decisions are policy-owned through ProfileExecutionPolicy, not duplicated in leaf modules.`
- `pre_fix_red_evidence`: `Second-opinion finding 1 showing Gate 1 and Gate 2 both inlined LIGHT short-circuits instead of consulting policy.`
- `post_fix_green_evidence`: candidate-2cdbfec-implementation.md records targeted probe coverage for both Gate 1 and Gate 2 policy-owned paths.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md, candidate-2cdbfec-second-opinion.md, and candidate-2cdbfec-clearance.md all confirm closure.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where gate ownership drifts back into spec_engine.py or deliberation.py.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

## Residual Non-Blocking Risks

### W2B-R01

- `blocker_id`: `W2B-R01`
- `failure_family`: `contract_fail_open`
- `family_status`: `open`
- `source_review`: `WAVE-2B-ADVERSARIAL-REVIEW.md + WAVE-2B-SECOND-OPINION.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `open`
- `current_disposition`: `Narrowed but not fully closed. Parse-invalid JSON now fails explicitly in 2cdbfec, but both clearance reviews found that parseable under-specified JSON can still produce empty Wave 2B enforcement fields.`
- `files_to_touch`:
  - `src/keystone/evaluator/sprint_contract.py`
  - `tests/unit/evaluator/test_sprint_contract.py`
- `stageable_files`:
  - `src/keystone/evaluator/sprint_contract.py`
  - `tests/unit/evaluator/test_sprint_contract.py`
- `tests_required`:
  - `tests/unit/evaluator/test_sprint_contract.py`
- `runtime_probe_required`: `Probe malformed sprint-contract output and confirm the run fails explicitly or preserves non-empty enforcement fields.`
- `required_regression_test`: `Malformed sprint-contract JSON must not silently degrade to a bare contract.`
- `required_regression_probe`: `Direct malformed-response probe on the real generator path.`
- `acceptance_invariant`: `Malformed sprint-contract output cannot silently erase Wave 2B enforcement fields.`
- `pre_fix_red_evidence`: `Adversarial review design concern 4 and second-opinion design concern 3.`
- `post_fix_green_evidence`: test_malformed_json_raises_explicit_error now passes on the committed candidate.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md and candidate-2cdbfec-second-opinion.md both record the narrower parseable-under-specified residual risk.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where malformed or under-specified contract generation silently produces empty enforcement fields.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

### W2B-R02

- `blocker_id`: `W2B-R02`
- `failure_family`: `observability_drift`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-ADVERSARIAL-REVIEW.md + WAVE-2B-SECOND-OPINION.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed in 2cdbfec. Emitted rubric event weights now match the effective adjusted weights used in scoring.`
- `files_to_touch`:
  - `src/keystone/evaluator/evaluator.py`
  - `tests/unit/evaluator/test_evaluator.py`
- `stageable_files`:
  - `src/keystone/evaluator/evaluator.py`
  - `tests/unit/evaluator/test_evaluator.py`
- `tests_required`:
  - `tests/unit/evaluator/test_evaluator.py`
- `runtime_probe_required`: `Probe rubric event emission and confirm the reported weights match the effective adjusted weights.`
- `required_regression_test`: `Runtime event weights must change when dimension_emphasis changes.`
- `required_regression_probe`: `Event-stream inspection under non-default dimension emphasis.`
- `acceptance_invariant`: `Emitted rubric-weight observability must match actual runtime scoring weights.`
- `pre_fix_red_evidence`: `Adversarial review warning 5 and second-opinion warning 5.`
- `post_fix_green_evidence`: candidate-2cdbfec-implementation.md records targeted probe coverage for adjusted rubric-weight emission.
- `verification_evidence`: candidate-2cdbfec-adversarial-review.md, candidate-2cdbfec-second-opinion.md, and candidate-2cdbfec-clearance.md all treat this risk as closed.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where event weights drift from the weights actually used in scoring.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`

### W2B-R03

- `blocker_id`: `W2B-R03`
- `failure_family`: `mocked_path_gap`
- `family_status`: `closed`
- `source_review`: `WAVE-2B-SECOND-OPINION.md`
- `blocked_candidate_commit`: `4ff7e90`
- `first_seen_commit`: `4ff7e90`
- `introduced_by`: `Wave 2B checkpoint candidate`
- `last_verified_commit`: `2cdbfec`
- `status`: `closed`
- `current_disposition`: `Closed as a Wave 2B residual risk. The cleared candidate adds real runtime-path policy-gate coverage and the required matrix, including tests/unit/hitl/test_gate.py, passed without reviewer objections.`
- `files_to_touch`:
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
  - `tests/unit/hitl/test_gate.py`
- `stageable_files`:
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
  - `tests/unit/hitl/test_gate.py`
- `tests_required`:
  - `tests/unit/specification/test_spec_engine.py`
  - `tests/unit/deliberation/test_deliberation.py`
  - `tests/unit/hitl/test_gate.py`
- `runtime_probe_required`: `At least one real-path Gate 1 LIGHT skip probe and one real-path modified gate halt probe.`
- `required_regression_test`: `Mock-only gate tests are insufficient; at least one real helper path must be exercised.`
- `required_regression_probe`: `Real helper and real gating path under modified gate and LIGHT profile.`
- `acceptance_invariant`: `Wave 2B gate behavior must be proven on real runtime paths, not only mocked helper returns.`
- `pre_fix_red_evidence`: `Second-opinion warning 4.`
- `post_fix_green_evidence`: Focused matrix for 2cdbfec passed, including tests/unit/hitl/test_gate.py alongside the new Gate 1 / Gate 2 policy-path tests.
- `verification_evidence`: Neither clearing review found a remaining blocker or warning in the real gate-helper coverage surface.
- `review_packet_refs`:
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-adversarial-review.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-second-opinion.md`
  - `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
- `fix_commit`: `2cdbfec`
- `reopen_criteria`: `Any future candidate where the real gate helper semantics are no longer covered.`
- `owner_prompt_ref`: `audit/remediation/WAVE-2B-BLOCKER-FIX-PROMPT.md`
- `supersedes`: `none`
