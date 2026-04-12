# Wave 2B: Cleared Historical Setup

*Date: 2026-04-12 | Updated after cleared candidate `2cdbfec` | Retained as historical Wave 2B execution context*

---

## What this file is for

Wave 2B is no longer active remediation work.

This file is retained to explain what Wave 2B covered and what was required to clear it, but the live authority for future sessions is now:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/runs/wave-2b/candidate-2cdbfec-clearance.md`
4. `audit/remediation/WAVE-2B-BLOCKER-REMEDIATION.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

Do **not** use this file as permission to continue Wave 2B coding.

## Cleared State

- Wave 1 is complete.
- Wave 2A is complete and cleared in commit `16e0bc7`.
- Blocked Wave 2B candidate `4ff7e90` was recovered and superseded.
- Wave 2B is cleared in commit `2cdbfec`.
- The next required step is a committed Wave 3A seam-freeze doc before any Wave 3 code begins.

## What Wave 2B Cleared

Wave 2B cleared the enforcement-model work from Decision B plus:

1. `E-1`: geometric-mean epsilon fix in `evaluator/layer3_rubric.py`
2. `E-9`: orchestrator calls `SprintContractGenerator.generate()`
3. `E-10`: effective evaluation profile carried through `ResearchSpec` into `Evaluator`
4. `E-6`: `dimension_emphasis` applied during rubric scoring
5. `E-7`: `mandatory_elements` and `anti_patterns` reach rubric prompts

The blocked-remediation loop closed these runtime invariants:

1. LIGHT coverage cannot fail open on failed evaluated tasks.
2. Task `priority` / `importance` derive from Step-5 scores, not LLM list order.
3. The effective evaluator profile is carried through `ResearchSpec` and used by `Evaluator`.
4. Gate 1 and Gate 2 consult `ProfileExecutionPolicy`.

## Residual Non-Blocking Follow-Up

- `W2B-R01`: parse-invalid sprint-contract JSON now fails explicitly, but parseable under-specified JSON can still collapse Wave 2B enforcement fields to empty values.

## Explicitly Out Of Scope After Clearance

Do **not** use Wave 2B follow-up work to silently start any of the following:

1. Wave 3A seam ownership changes without a seam-freeze doc
2. Wave 3 taxonomy, verifier, DAG, or provenance-sidecar implementation
3. Wave 3B iterative-loop or Pipeline-L2 implementation
4. Wave 4 / 4B content or polish work
5. Broad cleanup or unrelated dirty-file cleanup

## What Happens Next

1. Commit the cleared-state reconcile checkpoint.
2. Create and commit `WAVE-3A-SEAM-FREEZE.md`.
3. Only then open a clean Wave 3A / Wave 3 implementation lane rooted at `2cdbfec`.
