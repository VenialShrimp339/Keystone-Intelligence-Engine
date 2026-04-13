# Required Corrections Checklist

Date: 2026-04-13  
Applies to: promotion of the post-Wave-4B Retrieval MVP Lane D setup package

This file is now a closure checklist.

All previously required corrections were re-verified directly from current disk state in the fresh adversarial pass dated `2026-04-13`.

## Promotion Gate

- [x] Do not promote unless the package is controller-grade on current disk.
- [x] Current disk state now satisfies that bar.

## 1. Narrow Or Hard-Fence The Write Set

- [x] `src/keystone/tool_names.py` is no longer in the allowed write set and is explicitly denied.
- [x] `src/keystone/models/research.py` is fenced to additive isolated retrieval metadata only, with no changes to existing shared-model semantics.
- [x] `src/keystone/gateway/mcp_gateway.py` is fenced against auth, rate-limiter, circuit-breaker, retry, dead-letter, citation-sequencing, and HITL-adjacent behavior changes.
- [x] The package explicitly says tool-assignment changes through allowed files are blocked L1 integration scope creep.
- [x] The package explicitly says shared research-model behavior changes through allowed files are blocked broader runtime scope creep.

## 2. Turn Named Gates Into Required Gate Artifacts

- [x] `Backend Reality Gate` artifact exists with explicit `CLEARED` verdict.
- [x] `Tool Contract Gate` artifact exists with explicit `CLEARED` verdict.
- [x] `Governance Gate` artifact exists with explicit `CLEARED` verdict.
- [x] `Run Contract Gate` artifact exists with explicit `CLEARED` verdict.
- [x] `Controller Unlock / Worktree Provenance Gate` artifact exists with explicit `CLEARED` verdict.
- [x] Every required pre-open gate artifact records reviewer, reviewed snapshot, evidence inputs, approved setup artifact path, and explicit verdict.
- [x] Promotion is contingent on those gate artifacts existing and remaining `CLEARED`, not merely being named.

## 3. Strengthen Backend-Reality Proof

- [x] The package requires a closed backend truth matrix.
- [x] The package requires the candidate packet to prove successful fetch claims did not use `MockMCPClient` or stub fallback.
- [x] The package requires at least one live or provider-authenticated probe artifact per fetch surface, or a blocked checkpoint.
- [x] The package requires each successful probe to record invocation surface, tool name, backend/server, canonical URL, content hash, coverage status, and persisted artifact location or byte count.
- [x] The package requires each successful probe to record candidate commit, candidate parent anchor, approved setup artifact, worktree path, and live-vs-replay mode.
- [x] The package explicitly treats registry presence and tool descriptions as non-evidence.
- [x] The exact required candidate filenames now include `candidate-<commit>-backend-truth-matrix.md`.
- [x] The exact required candidate filenames now include `candidate-<commit>-live-fetch-review.md`.

## 4. Bring The Artifact Into Conformance With Its Own Upstream Checklist

- [x] The setup artifact explicitly says it is subordinate to `CONTROL-PLANE-STATE.yaml` and `ACTIVE-HANDOFF.md`, and that the control plane wins on conflict.
- [x] The setup artifact names the exact runtime-truth anchor path as `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b` at `65a612d`.
- [x] The setup artifact's required reading order includes the retrieval contract, architecture, migration, benchmark, and gate docs required by the upstream checklist.
- [x] Gate names are now consistent across the package.
- [x] The package no longer relies on "satisfied in substance" language as promotion proof.
- [x] Stale subordinate authority-adjacent prose is fenced and may not override live control-plane authority.

## 5. Strengthen The Clearance Bar

- [x] The unit matrix is kept and is explicitly declared insufficient on its own for backend-reality proof.
- [x] A mandatory live-fetch review requirement is present in the setup artifact and checklists.
- [x] The candidate implementation note must pin the exact runtime invocation contract for tests and probes.
- [x] The file manifest must explicitly call out any shared-runtime behavior change outside raw fetch transport, fetch identity, fetch coverage, or fetch audit.

## 6. Keep The Forward Lane Narrow

- [x] Retrieval Lane D remains the only next forward lane.
- [x] Parser Lane E remains blocked.
- [x] L1 integration Lane F remains blocked.
- [x] UI implementation remains blocked.
- [x] Benchmark acceptance claims remain blocked.
- [x] Wave 5 and calibration remain blocked.

## Final Decision Rule

- [x] Safe to promote now: **Yes**
- [x] Safe to promote after current-disk verification: **Yes**
- [x] Retrieval Lane D remains the right next forward lane: **Yes**
- [x] Any code lane authorized yet: **No**
