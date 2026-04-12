# Wave 2B: Blocked-Snapshot Remediation

*Date: 2026-04-12 | Use this file only with the control plane and `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`*

---

## What this file is for

This is the execution doc for **remediating the blocked Wave 2B candidate**.  
It is no longer a “start Wave 2B from scratch” launcher.

Use it together with:
1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
4. `audit/remediation/runs/wave-2b/candidate-4ff7e90-file-manifest.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

Do **not** use older `FINAL-DECISIONS.md`, `FINAL-DECISIONS-v2.md`, or `WAVE-2A-SETUP.md` to scope Wave 2B.

---

## Current starting point

- Wave 1 is complete.
- Wave 2A is complete and cleared in commit `16e0bc7`.
- Wave 2B checkpoint candidate `4ff7e90` exists and is **blocked**.
- Two committed review packets and one synthesis packet define the active Wave 2B blockers.
- Dirty Wave 2B blocker-fix work exists in the main workspace, but it is recovery evidence only until replayed in a clean `4ff7e90` worktree.

---

## Prerequisites already delivered by completed Wave 2A

Wave 2B may assume the following are already in place from commit `16e0bc7`:

1. Fresh canonical `CAN-*` citation IDs and alias rewriting.
2. Canonicalized findings flowing into Deliberation.
3. Provenance fields on aggregated claims / confidence claims plus `provenance_index`.
4. Orchestrator filtering of confidence / manifest by task provenance before rendering.
5. `metadata_hash` vs `content_hash` semantic split.
6. Post-synthesis verifier contract seam defined, but implementation still deferred.

Wave 2B remediation must build on those prerequisites. It must **not** re-open Wave 2A scope except for true regressions found while clearing 2B.

Residual Wave 2A follow-ups that are **not** blockers for 2B:

1. Render-time corroboration now blocks failed-task leakage, but it may underreport legitimate multi-pass corroboration in shared-source cases. Treat this as later semantic cleanup unless 2B work directly depends on it.
2. `PostSynthesisVerifierContract` in `src/keystone/contracts.py` still drifts from the v2.1 governing-doc seam. Keep that in mind when touching adjacent enforcement surfaces.

---

## Wave 2B remediation scope only

The Wave 2B target remains the same: the full enforcement-model work from Decision B **plus** `E-1`, `E-9`, `E-10`, `E-6`, and `E-7`.

The active remediation loop is narrower:

1. close the blocked runtime invariants in `4ff7e90`
2. keep fixes inside the approved file manifest
3. prove closure on the real runtime path
4. create a new candidate commit and review that committed snapshot only

### Core enforcement deliverables

1. `ProfileExecutionPolicy` with enforcement lookup.
2. Profile-owned L0 enforcement in `spec_engine.py`.
3. Task-scope governance in the orchestrator.
4. Coverage-policy computation.
5. `GateResolution` with `patch_applied` blocking.
6. Evaluator updates `task_outcomes`.
7. Task generator sets `importance`.

### Added Wave 2B deliverables

1. **`E-1`**: geometric-mean epsilon fix in `evaluator/layer3_rubric.py` (`0.01`, not `1.0`).
2. **`E-9`**: orchestrator must call `SprintContractGenerator.generate()` instead of building a bare sprint contract.
3. **`E-10`**: pass the effective evaluation profile from `ResearchSpec` into `Evaluator`.
4. **`E-6`**: apply `dimension_emphasis` multipliers during rubric scoring.
5. **`E-7`**: inject `mandatory_elements` and `anti_patterns` into rubric prompts.

### Active blocked-remediation targets

1. LIGHT coverage cannot fail open on failed evaluated tasks.
2. Task `priority` / `importance` must derive from Step-5 priority scores, not generation order.
3. The effective evaluator profile must be carried through `ResearchSpec` and used by `Evaluator`.
4. Gate 1 and Gate 2 must consult `ProfileExecutionPolicy`.
5. If possible while in scope, keep sprint-contract parse failure and rubric observability from silently degrading the new enforcement path.

---

## Explicitly out of scope for Wave 2B

Do **not** pull any of the following into this wave:

1. Dual-axis taxonomy (`DomainCategory`, `secondary_types`, domain-aware template routing, provisional M&A / Restructuring profile expansion) -- **Wave 3**.
2. Deep-research formalization and remaining concurrency cleanup from Decision C / E2 beyond what is already required by current code -- **Wave 3**.
3. Thin Pipeline-L2 (`StructuredOutline`, `content_structuring.py`, renderer migration to structured outline) -- **Wave 3B**.
4. Minimum viable live iterative loop (round-state continuity, branch coverage between rounds, refined round `N+1` task generation, novelty exhaustion loop control) -- **Wave 3B**.
5. Actionability / recommendation-framing prompt rewrite for decision-informing analysis -- **Wave 4 / 4B**.
6. Calibration-policy changes beyond `E-1` -- **Wave 5**.
7. Post-synthesis verifier implementation (the contract already exists; implementation is later) -- **Wave 3**.
8. Broad cleanup, unrelated dirty-file cleanup, or archival work.

---

## Suggested execution checklist

1. Read the control-plane files first.
2. Create a clean implementation worktree rooted at `4ff7e90`.
3. Replay or re-implement only the files listed in the candidate file manifest.
4. Keep edits tightly scoped to the blocked runtime invariants.
5. Run the focused Wave 2B proof matrix.
6. If a change seems to require Wave 3 or 3B work, stop and push it out instead of widening Wave 2B.

---

## After Wave 2B clears

1. Commit a docs-only cleared-state reconcile checkpoint.
2. Update the control plane to mark Wave 2B cleared.
3. Create the Wave 3A seam-freeze setup doc.
4. Only then begin Wave 3A / Wave 3.

Wave 3 does **not** start until a new Wave 2B candidate is reviewed and cleared against the full `16e0bc7..candidate` scope.
