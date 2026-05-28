# Skill Implications

## Required Additions

The skill should include a cleaving-frame selection stage before tree generation. This stage should propose candidate axes, identify what each would reveal, and choose the one that best exposes decision leverage.

The skill should output both tree maturity and tree type:

- component/factor map
- lever tree
- hypothesis tree
- decision tree
- uncertainty strategy tree
- solution/action tree

The skill should explicitly separate:

- full logical coverage tree
- pruned decision tree
- workplan/evidence tree
- communication/story tree

## Pruning Contract

Every pruned branch should explain:

- decision impact
- influenceability or controllability
- evidence cost
- uncertainty
- risk if the pruning decision is wrong

## KIE-Specific Implications

KIE should not dispatch research tasks from the full tree by default. It should dispatch from the pruned decision tree after operator approval. Full-tree branches can remain in the artifact as deferred coverage, monitoring items, or follow-up waves.

Leaf nodes should include:

- research question
- evidence required
- method or source type
- expected artifact
- what result would change the recommendation

## Evaluation Implications

Eval cases should penalize:

- one-cut trees on ambiguous prompts
- trees without pruning rationale
- generic framework substitution
- failure to distinguish full coverage from high-value work
- failure to update tree shape when a branch is a cross-cutting force

