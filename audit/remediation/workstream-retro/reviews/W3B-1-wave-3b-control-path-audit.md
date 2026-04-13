# W3B-1 Wave 3B Control-Path Audit

- Slice: `W3B-1`
- Top-line verdict: `BLOCKED`
- Authority docs snapshot used for review context: `7e9bf3423cb05fcc66407a0c3bae24b1816cda0a`
- Code baseline: `4819527ed12810e0a1c2996308525ec23a906cb3`
- Code parent: `4819527ed12810e0a1c2996308525ec23a906cb3`
- Code target: `5cc95858213e7ed817339fa910aaeaa85730c5a7`
- Code truth source: detached review checkout at `/tmp/keystone-w3b1-code`
- Authority-docs source: detached review checkout at `/tmp/keystone-w3b1-review`
- Dirty main workspace status: present and explicitly not trusted as code truth
- Subagents: none
- Graphify status in reviewed code snapshot `5cc9585`: `graphify-out/GRAPH_REPORT.md` present; `graphify-out/wiki/index.md` absent

## Prerequisite Proof

Authoritative prerequisite layer:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`

Current authoritative statuses read from that layer before launch:

- `CP-1`: `CLEARED`
- `CP-2`: `CLEARED`
- `RP-1`: `CLEARED`
- `W2B-1`: `CLEARED`
- `W3A-1`: `CLEARED`
- `W3-1`: `CLEARED`

Result: `W3B-1` was launchable on the authoritative prerequisite layer and does not need to rely on later sidecars being present in the historical code snapshot.

## Exact Authority Docs Read

From the detached `7e9bf34` authority snapshot:

- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
- `audit/remediation/WAVE-3B-SETUP.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-implementation.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-file-manifest.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-clearance.md`

From the detached `5cc9585` reviewed code snapshot:

- `graphify-out/GRAPH_REPORT.md`
- full diff `4819527..5cc9585`
- touched runtime files under `src/keystone/models/structuring.py`, `src/keystone/structuring/content_structuring.py`, `src/keystone/pipeline/markdown_renderer.py`, `src/keystone/pipeline/orchestrator.py`, `src/keystone/research/round_state.py`, `src/keystone/research/context_loader.py`, `src/keystone/research/research_agent.py`, `src/keystone/research/agent_pool.py`, and `src/keystone/contracts.py`

## Packet Integrity

- The committed diff in `5cc9585` matches the Wave 3B file manifest and stays inside the approved write set.
- No scope-creep file surfaced in the `4819527..5cc9585` committed diff.
- The review was performed against detached committed snapshots rather than the dirty controller workspace.

Packet-integrity verdict: no blocker.

## Scope And Boundary Conformity

- `StructuredOutline` is real and typed in `src/keystone/models/structuring.py`.
- `ContentStructurer` is on the runtime path and emits outline events before rendering.
- `MarkdownRenderer` now consumes `StructuredOutline` rather than raw `ConfidenceMap` / `StructuredFinding` input.
- Persisted round state lands under `engagements/{engagement_id}/memory/rounds/`, and `ContextLoader` reloads prior round summaries from that surface.
- The orchestrator instantiates `AgentPool(..., max_rounds=1)`, so the production pipeline path demotes `ResearchAgent` to one orchestrator-directed shallow pass per pipeline round.
- No nested dual-controller runtime was found on the committed pipeline path itself.

Independent rerun of the declared Wave 3B proof bundle in the detached `5cc9585` checkout completed successfully:

- `93 passed, 2 xfailed in 8.74s`

Structural contract verdict: no packet or scope blocker.

## Runtime Correctness Findings

### Finding 1: sufficiency can fire while open Wave 3B threads still exist

File:

- `src/keystone/pipeline/orchestrator.py:869-870`

Observed logic:

```python
if coverage_complete and has_high_confidence:
    return RoundStopSignal.SUFFICIENCY
```

This branch ignores `gaps_identified`, `contested_below_50pct`, and `insufficient_evidence`, even though Wave 3B's frozen contract says continuation and round `N+1` refinement must be driven by uncovered branches, contradictions, open gaps, and prior findings. A synthetic check against the committed code returned:

```text
case1 sufficiency
```

for a coverage-complete outline that still had an open gap plus at least one high-confidence claim.

Impact:

- the orchestrator can terminate before unresolved gaps or contested threads trigger the intended follow-up planning path
- the claimed "lightweight sufficiency / quality gate" becomes over-permissive on the committed runtime path

### Finding 2: novelty is not first-class once open threads remain

File:

- `src/keystone/pipeline/orchestrator.py:875-878`

Observed logic:

```python
if has_open_threads and not has_high_confidence:
    return RoundStopSignal.CONTINUE
if previous_outline is not None and _outline_signature(previous_outline) == _outline_signature(outline):
    return RoundStopSignal.NOVELTY
```

Because `CONTINUE` is returned before the novelty comparison, an unchanged round with persistent open gaps cannot stop on novelty exhaustion until the hard round cap is reached. A synthetic check against the committed code returned:

```text
case2 continue
```

for an unchanged outline with an open gap and no high-confidence claims.

Impact:

- novelty exhaustion is not actually a first-class stop signal in the very state where it matters most
- the committed controller can loop until `MAX_ROUNDS` instead of stopping on unchanged evidence surfaces
- this directly weakens the required Wave 3B check for branch-coverage and novelty-driven continuation

## Slice Assessment

### `outline-render-state contract`

Verdict: `CLEARED`

Basis:

- provenance-bearing outline model is present
- renderer consumes the outline surface
- round-state persistence and round-summary reload are implemented on the committed path
- packet and manifest boundaries stayed coherent

### `single-controller iterative loop`

Verdict: `BLOCKED`

Basis:

- the runtime does reduce `ResearchAgent` to a per-round primitive on the production pipeline path
- however, the orchestrator's authoritative round-stop law is materially wrong in the committed code
- the stop precedence can both stop too early on unresolved threads and fail to stop on novelty exhaustion when those threads stagnate
- that defect sits exactly on the Wave 3B control-path authority surface, so the slice cannot be cleared

## Top-Line Verdict

`BLOCKED`

Why:

- packet integrity passed
- scope and boundary conformity passed
- runtime correctness failed on the orchestrator's core continuation law

## Later-Wave Trust Impact

Because `W3B-1` is `BLOCKED`, the following later slices are not trustworthy to launch or treat as cleared on this retrospective lane:

- `W4-1`
- `W4B-1`
- `W4B-2`
- `X-1`

## Residual Risks

- The rerun proof bundle passes, but the current tests do not exercise the open-thread stop-precedence combinations above.
- `graphify-out/GRAPH_REPORT.md` was advisory context only and did not affect prerequisite authority.
- `W2B-R01` remains a carried historical residual risk and is unaffected by this slice's blocker.
