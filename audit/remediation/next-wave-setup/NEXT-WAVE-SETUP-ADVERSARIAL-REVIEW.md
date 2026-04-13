# Next-Wave Setup Adversarial Review

Date: 2026-04-13  
Reviewer mode: hostile controller-grade promotion review  
Scope: current on-disk post-Wave-4B next-wave setup package for Retrieval MVP Lane D

## Final Verdict

Promotion verdict: **YES**

The current setup package is now safe to promote into live control-plane authority as a docs-only next-wave setup checkpoint.

That verdict is narrow:

- it means the package is controller-grade enough for a later control-plane reconcile
- it does not self-promote
- it does not authorize any runtime code lane in this session

The earlier `NO` review is now stale against current disk state.

## Fresh Disk-Verified Checks

### 1. The write surface is now narrow enough to resist the earlier false-unlock path

The current package no longer treats `src/keystone/tool_names.py` as an allowed Lane D edit surface.

Current disk state instead says:

- `src/keystone/tool_names.py` is explicitly out of scope and on the denylist
- `src/keystone/gateway/mcp_gateway.py` is fenced against auth, rate-limit, circuit-breaker, retry, dead-letter, citation-sequencing, and HITL-adjacent changes
- `src/keystone/models/research.py` is fenced to an additive isolated retrieval block only, with no shared-model semantic changes
- any tool-assignment change through an allowed file is blocked L1 integration scope creep
- any shared research-model behavior change through an allowed file is blocked broader runtime scope creep

Those controls are present in:

- `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- `audit/remediation/next-wave-setup/ALLOWED-WRITE-SET.md`

This closes the main factual error in the stale review.

### 2. The required pre-promotion gates now exist as real artifacts with verdicts

The package now includes all five required docs-only gate artifacts:

1. `BACKEND-REALITY-GATE.md`
2. `TOOL-CONTRACT-GATE.md`
3. `GOVERNANCE-GATE.md`
4. `RUN-CONTRACT-GATE.md`
5. `CONTROLLER-UNLOCK-WORKTREE-PROVENANCE-GATE.md`

Each one currently records:

- reviewer
- reviewed snapshot
- evidence inputs
- approved setup artifact path
- explicit `CLEARED` verdict

`REVIEW-AND-GATE-CHECKLIST.md` and `NEXT-WAVE-SETUP-ARTIFACT.md` both make promotion contingent on those artifacts existing and remaining `CLEARED`, so the package is no longer relying on narrative intent.

### 3. Backend-reality proof is now load-bearing rather than rhetorical

The exact candidate-packet requirements now include both:

- `candidate-<commit>-backend-truth-matrix.md`
- `candidate-<commit>-live-fetch-review.md`

Those exact filenames are present in the current disk contents of:

- `audit/remediation/retrieval-mvp/RUNTIME-LANE-UNLOCK-MEMO.md`
- `audit/remediation/retrieval-mvp/SETUP-ARTIFACT-CHECKLIST.md`
- `audit/remediation/retrieval-mvp/WORKTREE-AND-REVIEW-GATE-CHECKLIST.md`
- `audit/remediation/next-wave-setup/NEXT-WAVE-SETUP-ARTIFACT.md`
- `audit/remediation/next-wave-setup/REVIEW-AND-GATE-CHECKLIST.md`

The package also now requires:

- a closed backend truth matrix
- at least one live or provider-authenticated probe artifact per canonical fetch surface, or a blocked checkpoint
- explicit proof that successful canonical fetch claims did not use `MockMCPClient`
- explicit proof that successful canonical fetch claims did not use the `SimpleMCPClient` stub fallback

That matters because the current runtime on disk still shows:

- `src/keystone/gateway/simple_client.py` has real default backends only for Exa and Brave, with stub fallback for other tools
- `tests/unit/test_gateway.py` uses `MockMCPClient`

So the package is correctly treating unit green lights and registry presence as non-evidence.

### 4. Runtime provenance and invocation-contract requirements are now explicit

The current package pins:

- baseline `65a612d`
- candidate parent anchor `65a612d`
- worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch`
- branch `codex/retrieval-mvp-fetch`
- approved setup artifact path

It also requires every candidate packet to record:

- `candidate_commit`
- `candidate_parent_anchor`
- `approved_setup_artifact`
- `worktree_path`
- `worktree_clean`
- `branch`

And it requires the implementation note to pin the exact runtime invocation contract used for tests and probes.

That is sufficient for controller-grade reviewability of later candidate evidence.

### 5. The forward lane remains properly narrow

The current package still keeps:

- Retrieval Lane D as the only next forward lane
- parser Lane E blocked
- L1 integration Lane F blocked
- UI work blocked
- benchmark acceptance claims blocked
- Wave 5 and calibration blocked

That matches the current retrieval packet and the active control-plane hard-stop state.

## Remaining Boundaries

The package being safe to promote does not change these current truths:

- the main workspace remains docs-only
- no retrieval runtime lane is authorized now
- no code lane is authorized by this session
- a later controller reconcile must still promote this package into live control-plane authority before any runtime worktree may open

## Lane Decision

Retrieval Lane D is still the right next forward lane after promotion.

Why:

- it is the smallest honest gap-closer between current governed retrieval and the stated MVP target
- it keeps parser and L1 integration seams procedurally separate
- it preserves the distinction between governed canonical retrieval and bypass/deep-research behavior

## Promotion Decision

- Safe to promote now: **Yes**
- Setup package safe to promote: **Yes**
- Retrieval Lane D still the right next forward lane: **Yes**
- Any code lane authorized yet: **No**

