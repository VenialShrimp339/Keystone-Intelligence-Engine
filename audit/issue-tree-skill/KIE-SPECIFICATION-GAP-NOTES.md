# KIE Specification Gap Notes

Date: 2026-05-28

## What Exists

The current L0 specification engine already preserves several strong architectural instincts:

- issue tree is treated as a first-class planning artifact
- decomposition is separated from validation
- selected analytical lenses can run in parallel and then be synthesized
- the lens catalog has moved beyond the original financial / operational / market trio
- ambiguous requests can trigger clarifying questions and approval
- leaf nodes later become research tasks with anti-confirmatory framing

## Core Gaps For This Skill

The existing decomposition contract is still too narrow for the owner vision:

- tree depth is capped in prompts at 2-3 levels, which blocks asymmetric deep branches
- the validator penalizes unbalanced trees, even though senior work often needs lopsided depth where the answer lives
- the tree has no explicit parent-child logic semantics such as AND, OR, diagnostic, constraint, weighted factor, sequence, or causal mechanism
- there is no distinction between a full coverage tree and a pruned decision tree
- pruning rationale is compressed into one synthesis paragraph instead of becoming an inspectable operator artifact
- the tree schema has no leaf-level resolution criteria, evidence requirements, artifact requirements, or branch prompt seeds
- lens selection is useful but can still substitute a catalog of lenses for the harder act of choosing a decomposition axis
- current prompts optimize for a research-task fanout count, not for the best consultant decomposition of the problem

## Design Consequence

The portable issue-tree skill should sit upstream of the current KIE `Decomposer`. Its first job is methodological quality:

1. frame the actual decision or question
2. generate candidate decomposition axes
3. produce 2-3 candidate top-level trees when the axis is ambiguous
4. select or merge the best tree
5. recursively decompose only where resolution requires it
6. label parent-child logic semantics
7. produce the full tree
8. produce a pruned decision tree with visible pruning rationale
9. attach leaf research questions, resolution criteria, and evidence/artifact requirements

The later KIE adapter can map this richer tree into the current `IssueTreeNode`, priority scorer, task generator, and HITL approval flow, but the skill should not inherit the current 2-3 level / 8-20 leaf limits as doctrine.

