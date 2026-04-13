# Docs Contradictions and Source of Truth

## Precedence used

When docs disagreed, this order won:

1. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
2. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
3. `CURRENT-STATE.md`
4. cleared implementation code and tests at `65a612d`
5. Wave 4B clearance packet and `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `CAPSTONE-PLAN-v2.md` and `JACK-ARCHITECTURAL-DIRECTIVES.md` for intended architecture
7. local modified or untracked docs only as unreconciled signal

## Dangerous contradictions

| contradiction | files in conflict | current winner | why dangerous | reconciliation |
|---|---|---|---|---|
| Project current state vs current branch contents | `CURRENT-STATE.md`; control-plane docs; actual branch/worktree topology from `git worktree list` and `git merge-base HEAD 65a612d` | Control-plane docs for project status, plus git topology for branch reality | A reader can think the current branch already contains the cleared Wave 3-4B runtime when it does not. | Treat `65a612d` as project implementation truth, but never say it lives on `codex/remediation-program`. |
| Local README/product framing vs hard-stop control plane | local modified `README.md` vs `audit/remediation/control-plane/ACTIVE-HANDOFF.md` and `CONTROL-PLANE-STATE.yaml` | Control-plane docs | The README can make the repo look like a ready MVP product entrypoint even though the live authority says hard stop and docs-only main workspace. | Rewrite or clearly label the README so it cannot silently outrank the control plane. |
| `AUTONOMOUS-REMEDIATION-PLAN-v4.md` still shows Wave 2B-era status | `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md` vs `CURRENT-STATE.md` and control-plane docs | `ACTIVE-HANDOFF.md` and `CONTROL-PLANE-STATE.yaml` | A stale remediation-plan header can pull readers back to `4ff7e90` and hide later cleared waves. | Keep v4 as historical process guidance only, not state truth. |
| Retrieval stack appears broader in docs than in runtime | `CAPSTONE-PLAN-v2.md`; local-only `docs/architecture-and-evolution.md`; local-only roadmap docs vs `src/keystone/gateway/simple_client.py` | Code at `65a612d` for current state; `CAPSTONE-PLAN-v2.md` for long-term intent | Registered tools and big retrieval language can be mistaken for live governed full-document retrieval. | Describe today as Exa/Brave snippet retrieval plus an experimental deep-research bypass lane; reserve full retrieval stack for the full version. |
| Evaluator completeness and calibration | local-only `docs/architecture-and-evolution.md`; `CAPSTONE-PLAN-v2.md`; `docs/ARCHITECTURE.md`; `src/keystone/evaluator/evaluator.py`; control-plane docs | `evaluator.py` plus Wave 5 defer in control-plane docs | The repo can read like it has a live five-layer calibrated evaluator when the committed runtime is a three-layer stack and Wave 5 is blocked. | Say “Layers 1-3 are real; calibration and Layers 4-5 are deferred by policy.” |
| Observation Library vs filesystem wiki foundation | local-only `docs/architecture-and-evolution.md`; local-only roadmap docs; `docs/ARCHITECTURE.md`; `src/keystone/models/observations.py`; `src/keystone/knowledge/*` | Code at `65a612d` | The project can sound self-improving already when only the engagement wiki is operational. | Separate “engagement wiki exists now” from “Observation Library learning system is still partial/future.” |
| Thin Pipeline-L2 ownership | `docs/ARCHITECTURE.md`; local-only `docs/system-diagram.md`; local-only roadmap docs vs `FINAL-DECISIONS-v2.1.md`, `CURRENT-STATE.md`, and `src/keystone/structuring/content_structuring.py` | `FINAL-DECISIONS-v2.1.md`, `CURRENT-STATE.md`, and code | If L2 is described as future, readers miss that the current markdown path already depends on a real thin outline layer. | Reconcile to: thin L2 is built now; rich L2 remains future. |
| HITL UI status | `CAPSTONE-PLAN-v2.md`; local-only roadmap docs; committed code under `src/keystone/hitl/` | Code at `65a612d` for current state | Phase 1 can sound like it includes a practical reviewer app when the committed repo only proves backend/API gates. | Reconcile to: HITL backend is real; reviewer UI is not a committed built surface. |
| Deep research completion vs in-progress upgrade language | `CURRENT-STATE.md`; `SESSION-LOG.md`; local-only `docs/architecture-and-evolution.md`; `src/keystone/research/research_agent.py` | Code plus control-plane docs | The project can claim “deep research built” without surfacing that the current implementation bypasses gateway controls and is not the settled full-version design. | Reconcile to: auditable deep-research seam exists; full governed deep-research architecture does not. |
| `docs/ARCHITECTURE.md` calls itself source of truth while under-describing later cleared code | `docs/ARCHITECTURE.md` vs `65a612d` code/tests and later control-plane docs | Cleared code/tests plus control plane | Readers can believe research/deliberation/structuring pieces are still absent because this older architecture map predates later waves. | Keep it only as an older scaffold map unless it is refreshed against the cleared runtime. |

## Harmless contradictions

| contradiction | files in conflict | current winner | why harmless |
|---|---|---|---|
| Snapshot counts drift, like total test count | local modified `README.md` vs local-only `docs/architecture-and-evolution.md` | none | This affects polish, not capability sequencing. |

## Current source-of-truth rule set

1. If the question is “what is cleared and allowed to count as built,” use the control plane plus `65a612d`.
2. If the question is “what is on the current branch,” use `HEAD` plus git topology.
3. If the question is “what was intended for the fuller product,” use `CAPSTONE-PLAN-v2.md`, `JACK-ARCHITECTURAL-DIRECTIVES.md`, and the local-only roadmap/architecture docs as intent signal.
4. If a local modified or untracked doc contradicts cleared code, it loses.

## Bottom line

The repo currently suffers from both overstatement and understatement.

- Overstatement:
  local README/product docs, retrieval language, self-improvement language, evaluator-completeness language.
- Understatement:
  the current branch and older committed architecture docs make the project look less built than the cleared Wave 3-4B implementation actually is.

The most dangerous problem is not one bad sentence. It is the absence of one obvious place where a newcomer can tell which story is authoritative.
