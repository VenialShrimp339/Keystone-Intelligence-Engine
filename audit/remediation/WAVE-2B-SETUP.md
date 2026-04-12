# Wave 2B: Enforcement Model + Execution-Path Fixes

*Date: 2026-04-11 | Use this file only with `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`*

---

## What this file is for

This is the authoritative execution doc for the **next build session only**.

Use it together with:
1. `audit/remediation/WORKSTREAM-STATUS.md`
2. `CURRENT-STATE.md`
3. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
4. `audit/remediation/BUILD-PROCESS.md`
5. `audit/remediation/WAVE-2B-SETUP.md`

Do **not** use older `FINAL-DECISIONS.md`, `FINAL-DECISIONS-v2.md`, or `WAVE-2A-SETUP.md` to scope Wave 2B.

---

## Current starting point

- Wave 1 is complete.
- Wave 2A is complete and cleared in commit `16e0bc7`.
- The governing-doc reconciliation pass is complete before Wave 2B starts.
- Wave 2B is now the **expanded** Wave 2B from `FINAL-DECISIONS-v2.1.md`, not the earlier narrower governance-only version.

---

## Prerequisites already delivered by completed Wave 2A

Wave 2B may assume the following are already in place from commit `16e0bc7`:

1. Fresh canonical `CAN-*` citation IDs and alias rewriting.
2. Canonicalized findings flowing into Deliberation.
3. Provenance fields on aggregated claims / confidence claims plus `provenance_index`.
4. Orchestrator filtering of confidence / manifest by task provenance before rendering.
5. `metadata_hash` vs `content_hash` semantic split.
6. Post-synthesis verifier contract seam defined, but implementation still deferred.

Wave 2B must build on those prerequisites. It must **not** re-open Wave 2A scope except for true blockers found while implementing 2B.

Residual Wave 2A follow-ups that are **not** blockers for 2B:

1. Render-time corroboration now blocks failed-task leakage, but it may underreport legitimate multi-pass corroboration in shared-source cases. Treat this as later semantic cleanup unless 2B work directly depends on it.
2. `PostSynthesisVerifierContract` in `src/keystone/contracts.py` still drifts from the v2.1 governing-doc seam. Keep that in mind when touching adjacent enforcement surfaces.

---

## Wave 2B scope only

Wave 2B includes the full enforcement-model work from Decision B **plus** the accepted execution-path additions `E-1`, `E-9`, `E-10`, `E-6`, and `E-7`.

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

### Internal sequencing for Wave 2B

1. Land the governance core and profile-routing path.
2. Land `E-9` sprint-contract wiring.
3. Land `E-6` and `E-7` on top of the generated sprint contract path.
4. Land `E-1` if not already folded into the evaluator work earlier.
5. Run focused verification after each cluster, not just at the end.

`E-9` is a prerequisite for `E-6` and `E-7`.

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

1. Read `FINAL-DECISIONS-v2.1.md` and `BUILD-PROCESS.md` first.
2. Confirm the working baseline is the cleared Wave 2A checkpoint (`16e0bc7`) plus this doc-alignment pass.
3. Implement only the Wave 2B items listed above.
4. Keep edits tightly scoped to the enforcement and evaluator-routing surface.
5. Run tests after each logical cluster:
   - governance / policy wiring
   - evaluator profile routing + sprint-contract generation
   - rubric field consumption + epsilon fix
6. If a change seems to require Wave 3 or 3B work, stop and push it out instead of widening Wave 2B.

---

## After Wave 2B completes

1. Run adversarial review on the Wave 2B diff **before** starting the next wave.
2. Scope that review to the Wave 2B code diff, not the whole working tree.
3. Fix any review blockers.
4. Create a clean checkpoint commit for Wave 2B.
5. Update `CURRENT-STATE.md` and `SESSION-LOG.md`.
6. Only then start Wave 3 from the reconciled plan in `FINAL-DECISIONS-v2.1.md`.

Wave 3 does **not** start until Wave 2B implementation, Wave 2B adversarial review, and Wave 2B blocker cleanup are all complete.
