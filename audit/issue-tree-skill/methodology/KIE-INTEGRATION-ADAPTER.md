# KIE Integration Adapter

## Recommended Integration Point

Integrate the portable problem-decomposition skill upstream of KIE's current `Decomposer`. Use it to produce a richer issue-tree package for human review, then map the approved pruned tree into KIE tasks.

## Why Upstream

The current KIE decomposition code is valuable but currently optimized around lens fanout and 8-20 research leaves. The new skill should not inherit that limit. It should first produce consultant-grade framing, full/pruned trees, and leaf evidence contracts.

## Mapping

Portable skill package:

```yaml
nodes:
  - node_id: branch_2.1
    parent_id: branch_2
    tree_scope: both
    statement: string
    question_or_hypothesis: string
    decomposition_axis: causal_driver
    source_logic: diagnostic
    priority: high
    decision_relevance: high
    measurable_variable_or_proxy: string
    named_mechanism: string
    decision_consequence: string
    disconfirming_test: string
    prune_status: keep
sibling_groups:
  - group_id: group_2_children
    parent_id: branch_2
    child_ids: [branch_2.1, branch_2.2]
    decomposition_axis: causal_driver
    coverage_logic: exhaustive
    truth_logic: OR
    evaluation_logic: diagnostic_candidates
    validation_note: string
leaf_tasks:
  - leaf_id: branch_2.1
    research_question: string
    resolution_criteria: [string]
    evidence_requirements: [string]
    expected_artifact: string
    disconfirming_evidence_to_seek: [string]
    task_seed_prompt: string
    acceptance_criteria: [string]
pruning_decisions:
  - node_id: branch_2.1
    action: keep
    impact_score: 5
    uncertainty_score: 4
    evidence_cost_score: 2
    discriminating_power_score: 5
    influenceability_score: 3
    value_of_information_note: string
```

KIE mapping:

- `IssueTreeNode.id` <- `node_id`
- `IssueTreeNode.name` <- short statement
- `IssueTreeNode.description` <- question/hypothesis plus sibling-group validation note
- `lens_annotations` <- decomposition axis, source logic, truth logic, evaluation logic, prune status, decision relevance
- `PriorityScore` inputs <- decision relevance, uncertainty, evidence cost, impact
- `ResearchTask.description` <- leaf research question plus disconfirming evidence
- `ResearchTask.acceptance_criteria` <- resolution criteria
- `ResearchTask.end_product` <- expected artifact

## HITL Gate

For Standard and Deep profiles:

1. show problem frame
2. show candidate axes and selected axis
3. show full tree
4. show pruned decision tree
5. show leaf research plan and estimated provider budget
6. require approval before launching branch research

## First Implementation Recommendation

Do not rewrite KIE's runtime decomposer immediately. First add the portable skill package and use it as a reference-backed prompt for a new `IssueTreePackage` artifact. After baseline-vs-skill evals, add an adapter that down-converts approved pruned leaves into the existing task generator.
