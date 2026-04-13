# Review And Gate Checklist

Date: 2026-04-13  
Applies to: post-Wave-4B Retrieval MVP Lane D fetch

## Gate Split

This checklist separates:

- what must clear before the lane opens
- what must clear before a candidate can be reviewed for clearance
- what remains out of scope until later benchmark or publishability work

Naming a gate here does not mean the gate is already cleared.

## Pre-Open Gates

All of these must clear before any runtime worktree is opened:

1. Control-plane compliance review
2. Tool Contract Gate
3. Backend Reality Gate
4. Governance Gate
5. Run Contract Gate
6. Controller Unlock / Worktree Provenance Gate

## Pre-Open Provenance Checklist

Before the first code edit:

1. Worktree path is exactly `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`.
2. Branch is exactly `codex/retrieval-mvp-fetch`.
3. Worktree root commit is exactly `65a612dc1400abbedcfbdda1f173cd72a3a90c06`.
4. The approved setup artifact path is recorded as `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`.
5. `git status --short` in the worktree is clean before the first code edit.
6. The main workspace remains docs-only.

## Candidate Review Packet

Each candidate must produce these files under `audit/remediation/runs/retrieval-mvp-fetch/`:

1. `candidate-<commit>-implementation.md`
2. `candidate-<commit>-file-manifest.md`
3. `candidate-<commit>-adversarial-review.md`
4. `candidate-<commit>-second-opinion.md`
5. `candidate-<commit>-review-synthesis.md`
6. `candidate-<commit>-clearance.md` or `candidate-<commit>-blocked-checkpoint.md`

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

## Required Runtime Probes

The candidate packet must name and report these probes:

1. Article fetch returns canonical URL, MIME, hash, and explicit coverage.
2. EDGAR fetch returns official filing content rather than stub text.
3. PDF fetch persists raw bytes with explicit coverage and hash.
4. Paper fetch returns full text when available, else explicit `abstract_only` or `metadata_only`.
5. Exa and Brave remain discovery-only on the canonical path.
6. Stubbed tool behavior cannot be misreported as canonical backend support.
7. Fetch activity is gateway-audited.

## Clearance Gates

Before a candidate may clear the lane, all of these must be true:

1. Adversarial review is complete.
2. Second opinion is complete.
3. Review synthesis is complete.
4. File manifest confirms no unresolved scope creep.
5. The exact named test matrix passed on the candidate snapshot.
6. The exact named runtime probes passed on the candidate snapshot.
7. Graphify collateral was rebuilt after code-file changes and is either committed or explicitly classified.

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

## Current Status

- Missing-artifact problem: satisfied by this package in substance
- Core control-plane promotion: still pending by instruction
- Retrieval runtime lane open now: no
