# W3A-1 Wave 3A Seam and Setup Audit

- Top-line verdict: `CLEARED`
- Reviewed retrospective snapshot parent: `04fbc6c9bb1de88b5649beb3c0b4fd4c014cf41f`
- Reviewed retrospective snapshot target: `df9f0445b7091b7fd0eb32d95bd5d2e1e433610f`
- Historical seam-freeze artifact landing: `65074ca1cb7cf20fd0b8d733c8ab1505d4a7327c`
- Historical first coherent live Wave 3 setup promotion: `198ab92b299f63afb0532ff503241f8b28e14935`
- Wave 3 baseline / parent / target: `2cdbfec84022f52e9dca6acec8f919e8e6de5c2c` / `2cdbfec84022f52e9dca6acec8f919e8e6de5c2c` / `4819527ed12810e0a1c2996308525ec23a906cb3`
- Later dependency target checked: `5cc95858213e7ed817339fa910aaeaa85730c5a7`
- Code truth source: detached review checkout at `/tmp/kie-retro-worktrees/w3a1-df9f0445`
- Dirty main workspace status: not trusted as code truth
- Authoritative prerequisite layer: `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- Subagents: none
- Advisory graph context: `graphify-out/GRAPH_REPORT.md` is absent in the reviewed snapshot, recorded per program rule, and treated as non-blocking

## Prerequisite Gate

- `CP-1`, `CP-2`, and `RP-1` are currently `CLEARED` in the authoritative ledger (`audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml:15-61`), so the Batch 2 launch gate for this slice is satisfied.
- This rerun is specifically required because the current authoritative Wave 3 setup reading now includes `candidate-4819527-setup-contract-addendum.md` (`audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml:56-58`).

## Authority Docs Read

1. `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
2. `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
3. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
4. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
5. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
6. `audit/remediation/WAVE-3A-SEAM-FREEZE.md`
7. `audit/remediation/WAVE-3-SETUP.md`
8. `audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md`
9. `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md`
10. `audit/remediation/runs/wave-3/candidate-4819527-clearance.md`
11. `audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md`

Supporting evidence used for boundary sanity checks:

- `audit/remediation/WAVE-3B-SETUP.md`
- `audit/remediation/runs/wave-3/candidate-4819527-implementation.md`
- `audit/remediation/runs/wave-3/candidate-4819527-file-manifest.md`
- `audit/remediation/runs/wave-3b/candidate-5cc9585-file-manifest.md`
- `git diff --name-status 2cdbfec..4819527`
- `git diff --name-status 4819527..5cc9585`
- focused diffs for `src/keystone/pipeline/orchestrator.py`, `src/keystone/research/research_agent.py`, `src/keystone/governance/models.py`, `src/keystone/specification/spec_engine.py`, `src/keystone/specification/task_generator.py`, `src/keystone/pipeline/post_synthesis_verifier.py`, and `src/keystone/pipeline/provenance_sidecar.py`

## Packet Integrity

No packet-integrity blocker was found in the reviewed snapshot.

- `df9f044` is a docs-only reconcile commit, which is an allowed review mode so long as controller consistency, authority order, and wave-state truth are preserved (`audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md:449-456`).
- The lineage manifest preserves the key historical split between seam-freeze artifact landing `65074ca` and first coherent live promotion `198ab92` instead of collapsing them (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:42-49`, `136-181`).
- The reviewed snapshot does not contain `graphify-out/GRAPH_REPORT.md`; per the execution plan this is advisory only, so I recorded the absence and continued.

## Scope / Boundary Conformity

### Seam-freeze defects

No blocking seam-freeze defect remains.

- The seam-freeze doc cleanly freezes the five required seams and keeps Wave 3B control-path authority out of Wave 3 (`audit/remediation/WAVE-3A-SEAM-FREEZE.md:11-20`, `36-41`, `43-110`, `112-143`, `145-207`).
- The plan's Stage 1, Stage 2, and Stage 3 split matches that freeze: Wave 3 owns taxonomy/routing, deep-research formalization, DAG dispatch, concrete verifier, provenance sidecar, and E2 hardening, while Wave 3B owns `StructuredOutline`, renderer migration, persisted round-state continuity, branch coverage, sufficiency, novelty, and round `N+1` refinement (`audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md:636-693`).
- A direct diff sanity check of `2cdbfec..4819527` shows the orchestrator changes are confined to DAG dispatch, gateway-bypass visibility, verifier insertion, and sidecar emission; it does not introduce outline, round-state, sufficiency, novelty, or outer-loop surfaces.

### Setup-contract defects

No blocking setup-contract defect remains in the reviewed snapshot, but only because the current authority is the reconciled setup-plus-addendum packet, not the original setup doc in isolation.

- Historical write-surface defect, now reconciled:
  `audit/remediation/WAVE-3-SETUP.md:83-118` omitted `src/keystone/governance/models.py`, `src/keystone/specification/spec_engine.py`, and `tests/unit/test_research_models.py`.
  The addendum now records those files explicitly as retrospective write-surface reconcile for the real `4819527` packet (`audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md:30-45`), and both the Wave 3 clearance and review synthesis now ground their boundary reading on that addendum (`audit/remediation/runs/wave-3/candidate-4819527-clearance.md:20-31`, `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md:15-23`).
- I spot-checked the omitted surfaces against the actual diff. They are Wave-3-shaped, not hidden Wave 3B scope:
  `src/keystone/governance/models.py` only adds `gateway_bypassed`;
  `src/keystone/specification/spec_engine.py` and `src/keystone/specification/task_generator.py` extend the domain-routing / evaluator-profile path;
  `tests/unit/test_research_models.py` covers the new `ResearchSpec` defaults.
  That matches the addendum's claim that the original setup was incomplete while the cleared packet still stayed inside Wave 3 substance.
- Historical E2/probe-contract defect, now reconciled:
  the original setup made "Remaining E2 cleanup" look like reopened implementation scope and required named probes for all six invariants (`audit/remediation/WAVE-3-SETUP.md:46-50`, `154-163`).
  The addendum now narrows those unchanged E2 surfaces to verification-only carry-forward and maps the six invariants to a mixed evidence model: named runtime probes where present, proof-table / matrix evidence where not (`audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md:46-148`).
  The clearance packet adopts that interpretation explicitly (`audit/remediation/runs/wave-3/candidate-4819527-clearance.md:20-31`).
- That mixed evidence model is adequate for this slice.
  The implementation packet still carries a focused Wave 3 matrix, a required completeness/gate matrix, and a seven-probe runtime bundle that hit real enforcing seams (`audit/remediation/runs/wave-3/candidate-4819527-implementation.md:50-117`), which is sufficient under the plan's non-vacuous proof rule (`audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md:478-485`).

### Later-wave dependency risk

No current later-wave dependency blocker was found.

- The reconciled Wave 3 boundary now truthfully explains why `4819527` cleared (`audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md:140-148`, `audit/remediation/runs/wave-3/candidate-4819527-clearance.md:22-31`, `audit/remediation/runs/wave-3/candidate-4819527-review-synthesis.md:15-23`).
- The later Wave 3B setup keeps `StructuredOutline`, renderer consumption, persisted `memory/rounds/` state, round-to-round coverage, novelty, sufficiency, round `N+1` task refinement, and single-controller authority in Wave 3B, not Wave 3 (`audit/remediation/WAVE-3B-SETUP.md:31-45`, `69-130`).
- The Wave 3B review synthesis says `5cc9585` stayed inside that approved Wave 3B boundary and made those control-path surfaces real on the committed runtime path (`audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md:15-47`).
  That is consistent with the Wave 3 scope-out list (`audit/remediation/WAVE-3-SETUP.md:52-65`) and the seam freeze's inner-loop vs outer-loop contract (`audit/remediation/WAVE-3A-SEAM-FREEZE.md:179-207`).

## Runtime Correctness

This slice did not find a new runtime contradiction in the later cleared packets.

- `4819527`'s runtime claims align with the reconciled Wave 3 boundary: routing/taxonomy, deep-research formalization, DAG dispatch, concrete verifier, and provenance sidecar are the real runtime closures (`audit/remediation/runs/wave-3/candidate-4819527-clearance.md:33-41`).
- `5cc9585`'s runtime claims align with the Wave 3B boundary: thin L2, outline-based rendering, persisted round-state continuity, and single-controller authority land there, not earlier (`audit/remediation/runs/wave-3b/candidate-5cc9585-review-synthesis.md:21-47`).
- The result is a clearance on boundary fidelity plus runtime consistency, not a claim that the original contemporaneous Wave 3 setup doc was already complete.

## Residual Risks

- The reviewed snapshot does not contain `graphify-out/GRAPH_REPORT.md`, so this slice had no advisory god-node/community context.
- This clearance depends on the docs-only retrospective reconcile in `df9f044`, especially `candidate-4819527-setup-contract-addendum.md`; it is not a claim that the original `198ab92` Wave 3 setup packet was complete on its own.
- This report is a retrospective sidecar until a later controller reconcile promotes it, and `W2B-1` is still `RERUN_REQUIRED` in the current authoritative ledger.

## Verdict

`CLEARED`

`W3-1` may not launch yet on the current authoritative layer.

This slice finds no remaining local Wave 3A blocker in `df9f044`, but `W2B-1` is still not currently `CLEARED` in the authoritative ledger and this rerun report is not controller-promoted authority by itself.
