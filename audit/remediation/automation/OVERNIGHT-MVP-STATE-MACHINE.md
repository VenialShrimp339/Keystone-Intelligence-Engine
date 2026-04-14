# Overnight MVP State Machine

## Rule Zero

One wake, one milestone.

Every wake starts from disk and re-determines the current stage.
Do not assume the previous wake finished what it intended.

## Stage 0: Reconcile Stale Lane H State

Enter this stage if:

- the Lane H review packet says candidate `93a5ca8` is `CLEARED`
- but the live control plane still says Lane H is only in `setup`

Allowed work:

- docs-only reconcile
- update control-plane files only

Required result:

- live control plane reflects the current Lane H candidate state truthfully

Stop after:

- one docs-only commit or one blocker note

## Stage 1: Narrow Professor-Demo Lane E Setup Package

Enter this stage if:

- Lane H is fully reconciled
- Lane E is still blocked / not yet authorized

Allowed work:

- docs-only narrow setup package for deterministic parse/evidence normalization

Required scope:

- article/PDF path only
- no SEC
- no advanced retrieval
- no extra UI commitments

Required result:

- a narrow Lane E setup artifact package that can be adversarially reviewed

Stop after:

- one docs-only package commit or one blocker note

## Stage 2: Lane E Package Review And Promotion Decision

Enter this stage if:

- a narrow Lane E setup package exists
- it is not yet promoted

Allowed work:

- docs-only adversarial review
- docs-only promotion decision

Required result:

- either `PROMOTE`
- or `DO_NOT_PROMOTE` with exact blockers

Stop after:

- one review/promotion decision commit or one blocker note

## Stage 3: Lane E Control-Plane Promotion

Enter this stage if:

- Lane E package is cleared for promotion
- the live control plane has not yet adopted it

Allowed work:

- docs-only reconcile

Required result:

- live control plane authorizes narrow Lane E

Stop after:

- one docs-only reconcile commit or one blocker note

## Stage 4: Lane E Implementation

Enter this stage if:

- Lane E is live and authorized
- no Lane E candidate exists yet

Allowed work:

- one runtime implementation candidate inside the approved Lane E write set

Required result:

- one candidate commit
- one run packet
- required test evidence

Stop after:

- one candidate commit or one blocker note

## Stage 5: Lane E Review Stack

Enter this stage if:

- a Lane E candidate exists
- final review synthesis has not yet cleared or blocked it

Allowed work:

- full review stack
- synthesis

Required result:

- `CLEARED` or `BLOCKED`

Stop after:

- one synthesis/clear-block commit or one blocker note

## Stage 6: Lane E Reconcile

Enter this stage if:

- Lane E synthesis is final
- live control plane is stale relative to that synthesis

Allowed work:

- docs-only reconcile

Required result:

- live control plane reflects Lane E outcome

Stop after:

- one docs-only reconcile commit or one blocker note

## Stage 7: Narrow Professor-Demo Lane F Setup Package

Enter this stage if:

- Lane E is cleared and reconciled
- Lane F remains unauthorized

Allowed work:

- docs-only narrow setup package for L1 integration and anchored citations

Required scope:

- integrate only the governed article/PDF path
- do not widen into SEC
- do not widen into full benchmark, UI, or advanced retrieval

Stop after:

- one docs-only package commit or one blocker note

## Stage 8: Lane F Package Review And Promotion Decision

Same pattern as Lane E package review.

Required result:

- `PROMOTE` or `DO_NOT_PROMOTE`

Stop after one milestone.

## Stage 9: Lane F Control-Plane Promotion

Same pattern as Lane E promotion.

Required result:

- live control plane authorizes narrow Lane F

Stop after one milestone.

## Stage 10: Lane F Implementation

Enter this stage if:

- Lane F is authorized
- no Lane F candidate exists yet

Allowed work:

- one runtime implementation candidate inside the approved Lane F write set

Required result:

- one candidate commit
- one run packet
- required tests

Stop after one milestone.

## Stage 11: Lane F Review Stack

Same pattern as Lane E review stack.

Required result:

- `CLEARED` or `BLOCKED`

Stop after one milestone.

## Stage 12: Lane F Reconcile

Same pattern as Lane E reconcile.

Required result:

- live control plane reflects Lane F outcome

Stop after one milestone.

## Stage 13: Thin Comparison/Demo Run

Enter this stage if:

- Lane H, Lane E, and Lane F are cleared and reconciled
- the reporting path is actually runnable

Allowed work:

- one thin comparison/demo package

Required result:

- one real report from the governed path
- one comparison against parallel ChatGPT/Claude deep research
- honest notes on strengths, weaknesses, and remaining omissions

Do not:

- broaden into the full benchmark program
- pretend this is a full acceptance campaign

Stop after one milestone.

## Stage 14: Professor Demo Handoff Package

Enter this stage if:

- the thin comparison/demo run exists

Allowed work:

- docs-only packaging

Required result:

- one concise handoff packet saying:
  - what to run
  - what is working
  - what is still not solved
  - what evidence supports the current claim

Stop after one milestone.

## Global Stage Rules

- If any stage ends `BLOCKED`, do not jump ahead.
- If the next stage is not yet authorized by the control plane, the only allowed milestone is the docs-only setup/promote path for that next stage.
- Do not combine setup, implementation, review, and reconcile into one wake.
- If a stage requires a new architecture decision not already settled on disk, stop and pause the automation.
