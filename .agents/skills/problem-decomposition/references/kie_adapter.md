# KIE Adapter

Use this mode when the issue tree will feed Keystone Intelligence Engine.

## Machine Collections

Use `references/output_contract.yaml` as the strict shape. KIE-oriented outputs should include:

- `nodes[]`: all full and pruned tree nodes, with `tree_scope` and `prune_status`.
- `edges[]`: parent-child links.
- `sibling_groups[]`: decomposition-axis and logic metadata for each sibling set.
- `leaf_tasks[]`: evidence requirements and downstream research task seeds for kept leaves.
- `pruning_decisions[]`: auditable keep/defer/prune/merge decisions.
- `quality_gate_results[]`: self-check findings and revisions made.

## Logic Placement

Do not hide all logic on the child node. Put sibling-set semantics in `sibling_groups[]`:

```yaml
sibling_groups:
  - group_id: demand_capacity_children
    parent_id: root
    child_ids: [demand, capacity, capacity_additions, uncertainty]
    decomposition_axis: supply_demand_bottleneck
    coverage_logic: exhaustive
    truth_logic: AND
    evaluation_logic: evidence_sufficiency
    exclusivity_claim: materially_distinct
    exhaustiveness_claim: complete_for_decision
    validation_note: "Adequacy requires defined demand, binding capacity, feasible gap-closing actions, and stress-case sufficiency."
```

## Leaf Task Fields

Each kept leaf should include:

```yaml
leaf_id: string
research_question: string
resolution_criteria: []
evidence_requirements: []
expected_artifact: string
disconfirming_evidence_to_seek: []
task_seed_prompt: string
required_artifact_type: memo | model | dataset | timeline | source_map | sensitivity_table | other
acceptance_criteria: []
source_policy: string
confidence_target: low | medium | high
human_approval_required: true
downstream_agent_routing_hint: string | null
```

## Dispatch Rule

Do not dispatch research from the full tree by default. Dispatch from the approved pruned decision tree. Keep pruned branches as deferred coverage or follow-up-wave candidates.

## HITL Package

Show the operator:

1. problem frame
2. candidate axes
3. selected axis rationale
4. full tree
5. pruned decision tree
6. leaf evidence plan
7. pruning decisions and reopen conditions
8. estimated research effort

Require approval before expensive branch research for Standard and Deep profiles.
