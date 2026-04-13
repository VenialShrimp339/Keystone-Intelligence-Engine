# X-1 Cross-Wave Regression Audit

- Slice: `X-1`
- Date: `2026-04-13`
- Scope: program-level retrospective check for cross-wave regression, baseline invalidation, hidden dependency failure, and drift in clearance meaning
- Code truth basis: committed snapshots and direct git inspection only; dirty main workspace not trusted as code truth
- Required prereq layer: `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- Subagents: none

## Launch Gate

`X-1` was launchable on the current authoritative review layer. The controller-promoted retrospective review ledger marks every prior slice through `W4B-2` as currently `CLEARED` (`audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml:52-143`).

## Authority And Read Set

Read first and used directly:

- `graphify-out/GRAPH_REPORT.md`
- all Batch 1-6 retrospective review reports under `audit/remediation/workstream-retro/reviews/`
- the final cleared packet families for Waves `2B`, `3`, `3B`, `4`, and `4B`
- `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
- `audit/remediation/workstream-retro/AUDIT-EXECUTION-PLAN.md`
- `audit/remediation/workstream-retro/AUDIT-SYNTHESIS-PLAN.md`
- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`

Direct git checks performed for this synthesis:

- historical lineage: `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d`
- repair deltas:
  - `65a612d..8dd97be`
  - `65a612d..1046585`
  - `65a612d..4d8f647`

## Program-Level Answer

No new cross-wave regression, downstream baseline invalidation, or hidden dependency failure was found beyond the local defects already discovered and explicitly repaired by the Batch 2-6 reruns.

The workstream still describes a valid bounded-wave historical sequence, but only under the retrospective authority model now encoded in the manifest and review ledger:

- the historical code lineage remains `4ff7e90 -> 2cdbfec -> 4819527 -> 5cc9585 -> 6406e46 -> 65a612d` (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:9-18`)
- the retrospective rerun clearances are slice-scoped authority overlays, not a rewritten cumulative release branch (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:17-18`; `audit/remediation/workstream-retro/reviews/W4-1-wave-4-polish-audit.md:18-19`; `audit/remediation/workstream-retro/reviews/W4B-2-wave-4b-runtime-audit.md:18-19`)

## Baseline Inheritance Validity

Baseline inheritance remains valid across the full wave lineage.

- The promoted lineage manifest preserves the exact code chain and documents anomalies as annotations instead of flattening them away, especially the `65074ca -> 198ab92` seam-freeze transition (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:17-18,42-48`).
- The later wave checkpoints continue to point at the expected prior cleared baselines:
  - Wave 3 from `2cdbfec`
  - Wave 3B from `4819527`
  - Wave 4 from `5cc9585`
  - Wave 4B from `6406e46`
  (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:184-199,254-370,378-448`)
- No Batch 3-6 packet family or rerun report requires reconstructing lineage from stale symbolic `HEAD`; all prerequisite reasoning is now ledger- and manifest-backed, which is exactly what `CP-2` and the execution plan require.

## Local Findings Already Handled Correctly

### 1. Wave 2B residual overclaim did not propagate illegally

`candidate-2cdbfec-implementation.md` overclaimed `W2B-R01` as closed, but the authoritative Wave 2B review chain corrected that before controller disposition. Both the synthesis and clearance preserved `W2B-R01` as non-blocking follow-up (`audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md:52-64`; `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md:33-35`). Later cleared packets for Waves 3, 3B, 4, and 4B all continued to carry `W2B-R01` forward as historical residual rather than silently assuming closure.

### 2. Wave 3 setup-contract incompleteness was repaired at the authority layer, not buried

The original Wave 3 setup packet was incomplete, but the later addendum explicitly narrowed the meaning of the Wave 3 clearance instead of pretending the original setup had always been sufficient (`audit/remediation/runs/wave-3/candidate-4819527-setup-contract-addendum.md:24-56,142-156`; `audit/remediation/runs/wave-3/candidate-4819527-clearance.md:16-31`). `W3A-1` and `W3-1` both relied on that reconciled reading, so later slices are no longer resting on the earlier incomplete setup packet.

### 3. Wave 4B C-13 overbreadth was repaired at the authority layer, not propagated downstream

The C-13 memo originally blended seam-local Step 4 recovery with later downstream propagation. The addendum now constrains the historical `65a612d` clearance to `C-13A` and explicitly excludes `C-13B` from the cleared code surface (`audit/remediation/runs/wave-4b/candidate-65a612d-c13-contract-addendum.md:22-54`; `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md:17-18,26,38-44`). `W4D-1`, `W4B-1`, and `W4B-2` all use that narrowed reading, so no later slice still depends on the earlier broader assumption.

### 4. The historical W3B, W4, and W4B runtime defects were local and were rerun on isolated repair seams

Direct git inspection confirms that the historical `65a612d` snapshot still contained the three later-rerun defects on their own local seams:

- `65a612d:src/keystone/pipeline/orchestrator.py:869-878` still allowed `SUFFICIENCY` before novelty/open-thread handling
- `65a612d:src/keystone/pipeline/markdown_renderer.py:269-272` still rendered `## Quality Assessment`
- `65a612d:src/keystone/evaluator/layer1_deterministic.py:32-44` still required sentence-like evidence snippets to meet the extra `>= 12` word floor

Those defects were then repaired in disjoint, narrow deltas:

- `65a612d..8dd97be` touched only `src/keystone/pipeline/orchestrator.py` and `tests/unit/pipeline/test_orchestrator.py`
- `65a612d..1046585` touched only `src/keystone/pipeline/markdown_renderer.py` and `tests/unit/pipeline/test_markdown_renderer.py`
- `65a612d..4d8f647` touched only `src/keystone/evaluator/layer1_deterministic.py` and `tests/unit/evaluator/test_layer1.py`

That isolation matters: the reruns corrected real local defects without introducing a new hidden cross-wave overlap. The rerun reports also explicitly frame those clearances as slice-local retrospective authority, not historical rewrite (`audit/remediation/workstream-retro/reviews/W3B-1-wave-3b-control-path-audit.md:72,99,186-199`; `audit/remediation/workstream-retro/reviews/W4-1-wave-4-polish-audit.md:18-19,76,153-167`; `audit/remediation/workstream-retro/reviews/W4B-2-wave-4b-runtime-audit.md:18-19,80,195-205`).

## Newly Discovered Cross-Wave Invalidations

None.

I did not find a later currently-`CLEARED` slice that still depends on:

- the raw pre-reconcile Wave 3 setup packet instead of the addendum-backed reading
- the overbroad historical C-13 reading instead of the addendum-backed `C-13A` reading
- silent closure of `W2B-R01`
- a hidden overlap among the `W3B-1`, `W4-1`, and `W4B-2` repair deltas
- any packet or docs contradiction strong enough to reclassify a prior residual as a downstream blocker

## Historical Residuals That Remain Non-Blocking

### 1. `W2B-R01` is still open, but it never became a hidden prerequisite

`W2B-R01` remains partially open for parseable but under-specified sprint-contract JSON (`audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md:35`; `audit/remediation/runs/wave-2b/candidate-2cdbfec-review-synthesis.md:54-64`). That residual should continue to be described as historical hardening debt, not as cleared functionality. But it does not invalidate later wave clearances because later packet families consistently preserved it as non-blocking rather than relying on it as solved state.

### 2. The retrospective program clears slices, not one cumulative repaired descendant commit

There is still no single post-hoc commit that combines `8dd97be`, `1046585`, and `4d8f647` into a new linearized release branch. That is a description constraint, not a blocker. The manifest and rerun reports already say the retrospective authority layer augments slice truth without rewriting historical commits (`audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml:17-18`; `audit/remediation/workstream-retro/reviews/W4-1-wave-4-polish-audit.md:19`; `audit/remediation/workstream-retro/reviews/W4B-2-wave-4b-runtime-audit.md:19`).

### 3. The unrelated evaluator-fallback canary failure remains suite-health debt, not a wave-lineage failure

`W3B-1` explicitly records that its only remaining named-suite failure was already present on base `65a612d` and sat outside the repaired control-path surface (`audit/remediation/workstream-retro/reviews/W3B-1-wave-3b-control-path-audit.md:99,199`). Nothing in the later Wave 4 or Wave 4B reruns used that canary as prerequisite clearance authority, so it remains non-blocking program debt rather than cross-wave invalidation.

## Sequence Validity

The workstream can still be described as a valid sequence of bounded waves, with the following exact reading:

1. The historical implementation sequence remains the bounded code lineage recorded in the promoted manifest.
2. The historical packet meanings that proved incomplete or overbroad were corrected by explicit retrospective authority artifacts, not by silent reinterpretation.
3. The later rerun clearances repaired local slice defects on isolated seams and did not create any new downstream dependency failure.

Under that reading, the trust gate, baseline inheritance, boundary deferrals, and final hard-stop semantics remain coherent at program scope.

## Verdict

CLEARED
