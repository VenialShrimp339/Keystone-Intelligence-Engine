# Implementation Lanes

## Lane Principles

- The main workspace stays docs-only for this lane.
- No UI runtime work starts until retrieval seams lock, plan-preview semantics are frozen, and a controller unlocks implementation.
- Parallelize by seam, not by vague theme.
- Require adversarial review before accepting any lane.
- Keep analyst mode, advanced mode, and dev mode responsibilities separate.

## Docs-Only Lanes Open Now

| Lane | Purpose | Can run now | Procedural status | Suggested branch | Ownership |
|---|---|---|---|---|---|
| Lane A | Analyst IA and chat-surface contract | Yes | Open now | `codex/ui-premium-surface` | Surface-spec lane |
| Lane B | Run inspector, reviewer-flow, and dev-mode state contract | Yes | Open now | `codex/ui-premium-inspector` | Observability lane |
| Lane C | Honest-copy, status taxonomy, and adversarial review | Yes | Open now | `codex/ui-premium-truth` | Adversarial lane |

## Runtime Lanes That Can Start Later In Parallel

| Lane | Purpose | Can run now | Procedural status | Suggested worktree | Suggested branch | Ownership |
|---|---|---|---|---|---|---|
| Lane D | Frontend shell, nav, and base layouts | No | Wait for unlock | `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-ui-shell` | `codex/ui-shell` | Frontend shell |
| Lane E | Run history, stage timeline, and artifact browser | No | Wait for unlock | `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-ui-history` | `codex/ui-history` | History lane |
| Lane F | Run inspector and evidence panels | No | Wait for unlock | `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-ui-inspector` | `codex/ui-inspector` | Inspector lane |
| Lane G | HITL reviewer surface | No | Wait for unlock | `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-ui-review` | `codex/ui-review` | Reviewer lane |

## Recommended Parallel Workstreams Right Now

- Lane A: refine IA, labels, and screen-level surface decisions.
- Lane B: lock run-status, gate-status, evidence-status, and dev-mode contracts.
- Lane C: adversarially review the package for false trust, overclaim risk, and retrieval/evaluator drift.

## Runtime Work That Is Parallel Once Unlocked

- Lane D and Lane E can run in parallel because shell/navigation and history/artifact browsing are separable.
- Lane F can run in parallel with Lane D if the state contract is frozen first.
- Lane G should start only after gate-state semantics, reviewer scope, and pre-run plan/review semantics are frozen.

## What Must Wait For Retrieval Architecture Lock

- Final source drawer design.
- Final depth and source-scope controls.
- Passage-level provenance UI.
- Coverage metrics and evidence-status taxonomy.
- Any polished copy around governed research breadth.

## Mandatory Acceptance Reviews By Lane

### Lane A

- Familiarity-without-copy review.
- Analyst-language review.
- Overclaim review.

### Lane B

- Backend reality review.
- Degraded-state review.
- Retrieval-lock dependency review.

### Lane C

- Adversarial truth review.
- False-green-flag review.
- Authority-chain compliance review.

### Lane D-G

- Retrieval-contract compliance review.
- Control-plane compliance review.
- Adversarial UX review.
- Reviewer-flow reality review for any HITL-facing lane.

## Unlock Condition

No UI implementation lane should open until all of the following are true:

- plan-preview semantics are frozen:
  - `Plan ready` means analyst confirmation
  - `Needs review` is the first real runtime pause when `post_specification` is enabled
  - `Running` starts only after approval or when no pre-run checkpoint exists
- one canonical runtime surface is promoted
- retrieval seams are locked
- governed versus bypass behavior is artifact-backed
- honest source and evidence labels are agreed
- controller approval explicitly opens runtime UI work
