# Current State
*Last updated: 2026-04-13 | Updated by: docs-only Lane H promotion reconcile*

---

## Live status

- **Wave 1:** Complete.
- **Wave 2A:** Cleared in commit `16e0bc7` (`Wave 2A: fix final hash and corroboration leakage`).
- **Wave 2B:** Cleared in commit `2cdbfec` (`Wave 2B: remediate blocked candidate 4ff7e90`).
- **Wave 3A:** Seam-freeze artifact landed in `65074ca` (`docs: freeze Wave 3A seams`); the first coherent live setup promotion is `198ab92`.
- **Wave 3:** Cleared in commit `4819527` (`feat: implement wave 3 provenance and routing`).
- **Wave 3B:** Cleared in commit `5cc9585` (`feat: implement wave 3b round control`).
- **Wave 4:** Cleared in commit `6406e46` (`fix: implement wave 4 polish slice`).
- **Wave 4B:** Cleared in commit `65a612d` (`feat: implement wave 4b content slice`).
- **Retrospective audit program:** Complete under `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`, but that completion remains prerequisite proof only.
- **Retrieval MVP Lane D:** Candidate `f1af7dfafa2e66b831810d70006ab8295411c61b` is frozen as `BLOCKED` superseded reference material only.
- **Current forward authorization:** `Lane H - Retrieval Tool-Surface Authority Expansion` is promoted in setup state.
- **Current retrieval code authorization:** `Lane H` may launch only in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` on `codex/retrieval-tool-surface`.
- **Browser Use research:** Classified as `FALLBACK_ONLY` with a secondary `BENCHMARK_OR_CONTROL_ARM_ONLY` role. It is not on the critical path for the current governed retrieval build.

## What just happened

1. The old Retrieval MVP Lane D fetch candidate (`f1af7df`) proved real article/PDF/paper fetch progress, but it was blocked on two separate issues:
   - a `document_fetch` authority / scope conflict
   - a separate SEC / EDGAR venue blocker
2. The controller then rejected `document_fetch` for the old Lane D boundary and froze `f1af7df` as blocked reference material only.
3. A new docs-only authority package was created, adversarially reviewed, corrected, and promoted as `Lane H - Retrieval Tool-Surface Authority Expansion`.
4. The live control plane now points to:
   - baseline `65a612d`
   - branch `codex/retrieval-tool-surface`
   - worktree `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface`
   - approved write set `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
5. A separate Browser Use audit concluded that Browser Use is valuable as fallback/browser-native acquisition research, but not as the canonical retrieval path or current critical-path replacement.

## What happens next

1. Read the control-plane files first:
   - `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
   - `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. Treat `65a612d` as the last cleared code commit.
3. Treat `f1af7dfafa2e66b831810d70006ab8295411c61b` as superseded blocked reference material, not as a promotable recovery stop.
4. Keep the main workspace controller/docs only.
5. Launch only `Lane H` coding in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` if you are doing runtime work.
6. After Lane H implementation, run Lane H adversarial review before any SEC / EDGAR venue retry.
7. Keep parser Lane E, L1 integration Lane F, UI runtime work, benchmark acceptance claims, Wave 5, and calibration blocked until the control plane explicitly reauthorizes them.
8. Use [audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md](/Users/jackriddle/Desktop/Keystone-Intelligence-Engine/audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md) for the full gap picture from current state -> MVP -> longer-horizon product.

## Reconciled wave plan

| Wave | Status | Scope |
|------|--------|-------|
| Wave 1 (1A + 1B + 1C) | **Complete** | Lifecycle isolation, parsing standard, citation-identity foundation |
| Wave 2A | **Cleared** (`16e0bc7`) | Citation identity completion and provenance gating |
| Wave 2B | **Cleared** (`2cdbfec`) | Enforcement model plus `E-1`, `E-9`, `E-10`, `E-6`, `E-7` |
| Wave 3A | **Complete** (`65074ca`; live setup promoted in `198ab92`) | Seam freeze for verifier, provenance sidecar, round-state, and loop ownership |
| Wave 3 | **Cleared** (`4819527`) | Completeness work plus dual-axis taxonomy, auditable deep research, verifier, sidecar, and DAG batching |
| Wave 3B | **Cleared** (`5cc9585`) | Thin Pipeline-L2 plus minimum viable live iterative loop |
| Wave 4 | **Cleared** (`6406e46`) | Low-risk polish slice `E-2`, `E-4`, `E-5` |
| Wave 4B | **Cleared** (`65a612d`) | Frozen content implementation from the Wave 4 memo set |
| Retrieval MVP Lane D | **Blocked / superseded** (`f1af7df`) | Candidate proved fetch progress but is not promotable under old authority |
| Lane H | **Setup promoted; implementation authorized** | Owns article/PDF tool-surface authority expansion and governed article/PDF fetch |

## Authoritative docs for a fresh session

- For exact precedence, use `audit/remediation/control-plane/ACTIVE-HANDOFF.md`. This file is a summary layer and does not override the handoff's authoritative order.
- `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
- `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
- `audit/remediation/control-plane/RETROSPECTIVE-LINEAGE-MANIFEST.yaml`
- `audit/remediation/control-plane/RETROSPECTIVE-REVIEW-LEDGER.yaml`
- `audit/remediation/retrieval-tool-surface/WORKSTREAM-HANDOFF.md`
- `audit/remediation/retrieval-tool-surface/AUTHORITY-EXPANSION-DECISION.md`
- `audit/remediation/retrieval-tool-surface/NEW-LANE-SETUP-ARTIFACT.md`
- `audit/remediation/retrieval-tool-surface/ALLOWED-WRITE-SET.md`
- `audit/remediation/retrieval-tool-surface/TOOL-CONTRACT-CHANGES.md`
- `audit/remediation/retrieval-tool-surface/PROMOTION-DECISION.md`
- `audit/remediation/retrieval-mvp/LANE-D-AUTHORITY-RESOLUTION.md`
- `audit/remediation/retrieval-mvp/NEXT-CONTROLLER-ACTION.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-review-synthesis.md`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-fetch/audit/remediation/runs/retrieval-mvp-fetch/candidate-f1af7df-blocked-checkpoint.md`
- `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md`
- `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md`
- `audit/remediation/WORKSTREAM-STATUS.md`
- `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`

## Non-authoritative but still useful

- `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
- `audit/remediation/runs/wave-4b/candidate-65a612d-review-synthesis.md`
- `audit/remediation/runs/wave-4b/candidate-65a612d-clearance.md`
- `audit/remediation/WAVE-4-4B-PREWORK.md`
- `audit/remediation/WAVE-4-D2-ACTIONABILITY-RESEARCH.md`
- `audit/remediation/WAVE-4-CORE-PROMPT-QUALITY-RESEARCH.md`
- `audit/remediation/WAVE-4-SPRINT-CONTRACT-RUBRIC-RESEARCH.md`
- `audit/remediation/WAVE-4-TEMPLATE-ROUTING-RESEARCH.md`
- `audit/remediation/WAVE-4-EVALUATOR-VERIFICATION-RESEARCH.md`
- `audit/remediation/external-research/browser-use/RECOMMENDATION.md`
- `audit/remediation/external-research/browser-use/INTEGRATION-BOUNDARY.md`
- `SESSION-LOG.md` -- historical trail
