# Review And Gate Checklist

Date: 2026-04-13  
Applies to: post-Wave-4B Retrieval MVP Lane D fetch

## Gate Split

This checklist separates:

- what must clear before the setup package may be promoted
- what must clear before any runtime worktree is opened
- what must clear before a candidate can be reviewed for clearance
- what remains out of scope until later benchmark or publishability work

Naming a gate here does not mean the gate is already cleared. A gate counts only when its required artifact exists for the reviewed snapshot and records an explicit verdict.

## Mandatory Pre-Promotion Gate Artifacts

Later controller promotion of the setup package is blocked unless all of the following docs-only gate artifacts exist under `audit/remediation/next-wave-setup/` and say `CLEARED`:

1. `BACKEND-REALITY-GATE.md`
2. `TOOL-CONTRACT-GATE.md`
3. `GOVERNANCE-GATE.md`
4. `RUN-CONTRACT-GATE.md`
5. `CONTROLLER-UNLOCK-WORKTREE-PROVENANCE-GATE.md`

Every required gate artifact must record:

1. reviewer
2. reviewed snapshot
3. evidence inputs
4. approved setup artifact path
5. unambiguous verdict

Control-plane compliance review is captured here through the artifact subordination rule plus the Controller Unlock / Worktree Provenance Gate.

## Pre-Open Provenance Checklist

Before the first code edit:

1. Worktree path is exactly `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`.
2. Branch is exactly `codex/retrieval-mvp-fetch`.
3. Worktree root commit is exactly `65a612dc1400abbedcfbdda1f173cd72a3a90c06`.
4. Runtime truth is anchored to `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`.
5. The approved setup artifact path is recorded as `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`.
6. `git status --short` in the worktree is clean before the first code edit.
7. The main workspace remains docs-only.

## Candidate Review Packet

Each candidate must produce these files under `audit/remediation/runs/retrieval-mvp-fetch/`:

1. `candidate-<commit>-implementation.md`
2. `candidate-<commit>-file-manifest.md`
3. `candidate-<commit>-backend-truth-matrix.md`
4. `candidate-<commit>-live-fetch-review.md`
5. `candidate-<commit>-adversarial-review.md`
6. `candidate-<commit>-second-opinion.md`
7. `candidate-<commit>-review-synthesis.md`
8. `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

Each candidate packet must include these provenance fields:

1. `candidate_commit`
2. `candidate_parent_anchor`
3. `approved_setup_artifact`
4. `worktree_path`
5. `worktree_clean`
6. `branch`

The candidate implementation note must also pin the exact runtime invocation contract used for tests and probes so provenance, entrypoint, and execution surface are reviewable.

## Required Test Matrix

These suites are mandatory and may not be substituted away:

1. `tests/unit/gateway/test_auth.py`
2. `tests/unit/gateway/test_gateway.py`
3. `tests/unit/gateway/test_tool_registry.py`
4. `tests/unit/test_auth.py`
5. `tests/unit/test_audit_log.py`
6. `tests/unit/test_gateway.py`
7. `tests/unit/test_research_models.py`
8. `tests/unit/test_tool_registry.py`

Important: this unit matrix is not sufficient backend-reality evidence on its own. It can pass against `MockMCPClient` or stub fallback and therefore cannot clear backend reality without the additional artifacts below.

## Required Backend-Reality Artifacts

The candidate packet must include:

1. A closed backend truth matrix conforming to `BACKEND-TRUTH-MATRIX-SPEC.md`.
2. A live-fetch review conforming to `LIVE-PROBE-EVIDENCE-SCHEMA.md`.

The backend truth matrix must classify every relevant surface as one of:

- live/provider-authenticated canonical fetch
- discovery-only
- stub fallback
- mock-only
- bypass-only
- blocked/missing canonical backend

Registry presence and tool descriptions are explicitly non-evidence.

## Required Runtime Probes

The candidate packet must name and report these probes:

1. Article fetch returns canonical URL, MIME, hash, and explicit coverage.
2. EDGAR fetch returns official filing content rather than stub text.
3. PDF fetch persists raw bytes with explicit coverage and hash.
4. Paper fetch returns full text when available, else explicit `abstract_only` or `metadata_only`.
5. Exa and Brave remain discovery-only on the canonical path.
6. Stubbed tool behavior cannot be misreported as canonical backend support.
7. Fetch activity is gateway-audited.

At least one live or provider-authenticated probe artifact must exist for each fetch surface, or the candidate must stop in a blocked checkpoint instead of clearing.

Each successful probe record must include:

1. invocation surface
2. tool name
3. backend/server
4. canonical URL
5. content hash
6. coverage status
7. persisted artifact location or byte count
8. candidate commit
9. candidate parent anchor
10. approved setup artifact
11. worktree path
12. whether the run used live provider access or replay

## Clearance Gates

Before a candidate may clear the lane, all of these must be true:

1. Adversarial review is complete.
2. Second opinion is complete.
3. Review synthesis is complete.
4. File manifest confirms no unresolved scope creep.
5. The exact named test matrix passed on the candidate snapshot.
6. The exact named runtime probes passed on the candidate snapshot.
7. The backend truth matrix is closed and reviewed.
8. The live-fetch review on the authoritative worktree is complete.
9. Successful fetch claims are proven not to use `MockMCPClient` or the `SimpleMCPClient` stub fallback.
10. Graphify collateral was rebuilt after code-file changes and is either committed or explicitly classified.

## Later Gates That Stay Out Of Scope For Lane Open

These do not need to clear before the fetch lane opens, but they must clear before benchmark evidence or publishability claims:

1. Public Pack Exposure Gate
2. Replay-vs-Production Equivalence Gate
3. Mixed-Provenance Audit Gate
4. Citation Support Gate
5. Benchmark Anti-Gaming Review
6. Acceptance Math Gate
7. Deep-Research Publishability Gate

## Stop Conditions

Stop and return to the control plane if any of these happen:

1. A touched path falls outside the approved write set.
2. The lane starts widening into parser or L1 integration work.
3. The lane needs new persistent infrastructure outside the fetch seam.
4. The lane relies on bypass retrieval for canonical claims.
5. Repo state becomes unsafe to reconcile.
6. A review identifies a blocker that cannot be resolved inside the approved lane.
7. The runtime invocation contract is ambiguous, unpinned, or differs across the claimed evidence set.
8. The backend truth matrix is open, contradictory, or unsupported by probe evidence.

## Current Status

- Core control-plane promotion: still pending by instruction
- Retrieval runtime lane open now: no
- Later promotion eligibility rule: only if the required gate artifacts in this package exist, remain current, and are `CLEARED`
