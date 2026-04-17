# Worktree And Review-Gate Checklist

Status: historical/provenance packet material retained for lineage only.
This checklist records the older Retrieval MVP worktree/review gate expectations.
It is preserved for provenance, not as the live worktree-opening authority for the current repo.
Use the control plane and the promoted Lane E retrieval-parse packet for the current authorized path.

Date: 2026-04-13  
Purpose: define the required worktree provenance, review packet, and gate sequence for the first Retrieval MVP runtime lane

## 1. Worktree Provenance Requirements

Before any runtime work starts:

- [ ] work is opened in a dedicated clean worktree
- [ ] the worktree is rooted from `65a612d`
- [ ] the branch name is lane-specific
- [ ] the main workspace remains docs-only
- [ ] the worktree path is recorded in lane artifacts
- [ ] the worktree is clean before the first code edit

Recommended first-lane provenance values:

- [ ] branch: `codex/retrieval-mvp-fetch`
- [ ] worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
- [ ] parent anchor: `65a612d`

## 2. Runtime Truth Discipline

- [ ] every runtime truth claim is anchored to the sibling Wave 4B worktree or `git show 65a612d:...`
- [ ] no runtime truth claim is anchored to the dirty main workspace
- [ ] registered tool presence is not treated as backend reality
- [ ] `DEEP_RESEARCH=1` is not treated as canonical governed retrieval

## 3. Allowed Write Set Discipline

The lane must stay within the exact controller-approved write set from the future setup artifact.

Minimum rule:

- [ ] every touched file is either in the allowed write set or is graphify collateral explicitly permitted by the setup artifact
- [ ] any touched file outside the allowed write set triggers a stop back to the control plane

Recommended first-lane write set to enforce:

### Runtime code

- [ ] `src/keystone/gateway/audit_log.py`
- [ ] `src/keystone/gateway/mcp_gateway.py`
- [ ] `src/keystone/gateway/servers.py`
- [ ] `src/keystone/gateway/simple_client.py`
- [ ] `src/keystone/gateway/tool_registry.py`
- [ ] `src/keystone/models/research.py`

Required fences on those allowed files:

- [ ] `src/keystone/gateway/mcp_gateway.py` may not change authorization, rate-limiter use, circuit-breaker use, retry policy, dead-letter behavior, citation extraction sequencing, or HITL-adjacent control flow
- [ ] `src/keystone/models/research.py` may only receive an additive isolated retrieval block, with no changes to existing `ResearchSpec`, `EngagementSpec`, `PipelineProfile`, `StructuredFinding`, or `FindingClaim` semantics, fields, validators, defaults, or behavior
- [ ] `src/keystone/tool_names.py` is intentionally out of scope for Lane D
- [ ] any tool-assignment change through an allowed file counts as blocked L1 integration scope creep
- [ ] any shared research-model behavior change through an allowed file counts as broader runtime scope creep

### Tests

- [ ] `tests/unit/gateway/test_auth.py`
- [ ] `tests/unit/gateway/test_gateway.py`
- [ ] `tests/unit/gateway/test_tool_registry.py`
- [ ] `tests/unit/test_auth.py`
- [ ] `tests/unit/test_audit_log.py`
- [ ] `tests/unit/test_gateway.py`
- [ ] `tests/unit/test_research_models.py`
- [ ] `tests/unit/test_tool_registry.py`

### Generated collateral

- [ ] `graphify-out/GRAPH_REPORT.md`
- [ ] `graphify-out/graph.json`

## 4. Graphify Requirement

After any code-file change in the worktree:

- [ ] run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"`
- [ ] ensure graphify collateral is either committed as legitimate collateral or explicitly classified in the candidate file manifest

## 5. Candidate Review Packet Requirements

Each candidate must produce:

- [ ] `candidate-<commit>-implementation.md`
- [ ] `candidate-<commit>-file-manifest.md`
- [ ] `candidate-<commit>-backend-truth-matrix.md`
- [ ] `candidate-<commit>-live-fetch-review.md`
- [ ] `candidate-<commit>-adversarial-review.md`
- [ ] `candidate-<commit>-second-opinion.md`
- [ ] `candidate-<commit>-review-synthesis.md`
- [ ] `candidate-<commit>-clearance.md` or blocked checkpoint

## 6. File Manifest Requirements

The candidate file manifest must record:

- [ ] candidate commit
- [ ] candidate parent
- [ ] baseline commit
- [ ] wave or lane name
- [ ] exact allowed write set
- [ ] exact committed diff classification
- [ ] classification of each touched file as expected, legitimate collateral, scope creep, or quarantined unrelated
- [ ] an explicit statement that no unresolved scope creep remains

## 7. Review Packet Provenance Fields

The candidate packet must make the following fields explicit, matching the retrieval benchmark packet contracts:

- [ ] `candidate_commit`
- [ ] `candidate_parent_anchor`
- [ ] `approved_setup_artifact`
- [ ] `worktree_path`
- [ ] `worktree_clean`
- [ ] branch

These should later match the same provenance fields expected in benchmark `run.json` and `adapter_declaration.json`.

## 8. Mandatory Pre-Open Gates

Before the controller opens the worktree:

- [ ] Control-plane compliance review is complete
- [ ] Tool Contract Gate is complete
- [ ] Backend Reality Gate is complete
- [ ] Governance Gate is complete
- [ ] Run Contract Gate is complete
- [ ] Controller Unlock / Worktree Provenance Gate is complete

Interpretation:

- Control-plane compliance review confirms the lane is actually authorized by a new committed setup artifact.
- Tool Contract Gate confirms the lane is operating against the typed retrieval contract direction and not reusing the shallow query-shaped seam as final truth.
- Backend Reality Gate confirms the named fetch surfaces are real target backends, not registry descriptions or placeholder stubs.
- Governance Gate confirms the lane stays on gateway-owned retrieval and does not smuggle bypass behavior into canonical claims.
- Run Contract Gate confirms the candidate will record a pinned runtime invocation contract for tests and probes, and that mismatched execution surfaces count as a blocker.
- Controller Unlock / Worktree Provenance Gate confirms baseline, parent anchor, setup artifact, worktree, and branch are all pinned and reviewable.

## 9. Mandatory Review Gates Before Clearance

Before a candidate may clear the lane:

- [ ] adversarial review is complete
- [ ] second opinion is complete
- [ ] review synthesis is complete
- [ ] file manifest confirms no scope creep
- [ ] named test matrix passed on the candidate snapshot
- [ ] named runtime probes passed on the candidate snapshot

## 10. Mandatory Gates Before Benchmark Execution Or Publishability Claims

These do not need to clear before opening the fetch lane, but they must clear before benchmark evidence or publishability claims:

- [ ] Public Pack Exposure Gate
- [ ] Replay-vs-Production Equivalence Gate
- [ ] Mixed-Provenance Audit Gate
- [ ] Citation Support Gate
- [ ] Benchmark Anti-Gaming Review
- [ ] Acceptance Math Gate
- [ ] Deep-Research Publishability Gate

## 11. Benchmark-Artifact Provenance Requirements

When the lane eventually participates in frozen-corpus benchmark runs, the candidate artifacts must support:

- [ ] `run.json` recording baseline anchor, candidate commit, candidate parent anchor, approved setup artifact, worktree path, replay surface, and replay adapter
- [ ] `adapter_declaration.json` recording runtime anchor, worktree, replay surface, evidence policy, governance policy, and equivalence review
- [ ] provenance-mode reporting at run, source, and citation level
- [ ] clean replay-only pack-access proof

Important:

- these are benchmark run-start and benchmark-validity requirements
- they are not, by themselves, sufficient to authorize opening the runtime lane

## 12. Stop Conditions

Stop and return to the control plane if any of the following happens:

- [ ] the lane needs to modify files outside the approved write set
- [ ] the lane needs to widen into parser or L1 integration work
- [ ] the lane needs new persistent infrastructure outside the approved seam
- [ ] the lane relies on bypass retrieval for canonical claims
- [ ] the lane cannot keep the main workspace quarantined
- [ ] a review identifies unresolved scope creep
- [ ] a blocker cannot be resolved inside the approved lane

## 13. Authorization Verdict For This Session

Current verdict:

- [ ] retrieval runtime lane authorized now

Result:

- This box is intentionally unchecked.
- No retrieval runtime lane is authorized now.
- The control-plane hard stop remains active until a later controller-approved setup artifact is committed.
