# Methodology

## Core Model

A good issue tree answers a governing question. The process is:

1. frame the problem
2. choose candidate cleaving axes
3. select the axis that exposes decision leverage
4. build a full tree
5. validate sibling logic and MECE
6. prune into a decision tree
7. attach evidence requirements to leaves
8. synthesize a current best answer

## Problem Frame

Define:

- decision maker or audience
- decision to make or question to answer
- Situation: known baseline
- Complication: event, discrepancy, proposed solution, or uncertainty
- R1: current or likely undesired result
- R2: desired result
- solution stance: no solution, proposed solution, accepted solution, failed solution, known alternatives, unclear R2, or uncertain R1
- boundaries, time frame, accuracy needed, constraints, and expected action

For machine-readable or Keystone outputs, decision maker, R1, R2, and constraints must be explicit. When they are unknown, write the assumption in the field and add a blocking unknown or objective-definition branch instead of omitting the field.

## Tree Type Router

- No solution known: diagnostic causes, then solution options.
- Solution proposed: criteria-based proof/disproof.
- Solution accepted: implementation steps, dependencies, risks.
- Prior solution failed: failure diagnosis and revised options.
- Known alternatives: option-selection tree.
- R2 unclear: objective-definition tree.
- R1 uncertain: evidence tree to validate whether a problem exists.

## Branch Logic Types

- `AND`: all children must hold.
- `OR`: one child can explain or satisfy the parent.
- `weighted_factor`: children trade off by weight.
- `diagnostic_candidates`: possible causes to test.
- `constraint_gate`: failure can kill the recommendation.
- `sequence`: steps or dependencies in order.
- `causal_chain`: mechanism from cause to outcome.
- `portfolio`: multiple moves can coexist.
- `evidence_sufficiency`: independent evidence paths.
- `custom`: explicitly define the relationship.

## MECE Validation

Validate by source logic:

- sequence: do the steps together produce the parent outcome?
- structure: do the parts cover the whole without overlap?
- class: do siblings share a common attribute and include obvious members?
- diagnostic: are causes distinct enough to test?
- criteria: do criteria cover R2 without double-counting?

Sibling groups should not mix causes, actions, risks, metrics, and stakeholders at the same level.

## Pruning

Retain branches with high decision impact, high uncertainty, high discriminating power, low-cost quick evidence, or strong disconfirming value.

Defer or prune branches that are low impact, already known, not influenceable, too costly for the decision, or dominated by another branch.

Show:

- action: keep, prune, defer, merge
- rationale
- risk if wrong
- evidence that would reopen the branch

Separate the retained pruned tree from the pruning ledger. The pruned tree should be the compact executable spine, usually 3-8 retained leaves, plus only the dependencies needed to understand those leaves. The pruning ledger can be verbose and should carry the KEEP/DEFER/PRUNE/MERGE rationale. If more than 8 retained leaves survive, run a second pass or label the result as a broad research map.

## Leaf Resolution

Every leaf should include:

- research question
- resolution criteria
- evidence required
- expected artifact
- disconfirming evidence
- likely sources or methods
- required accuracy
