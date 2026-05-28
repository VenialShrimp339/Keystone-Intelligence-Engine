---
name: problem-decomposition
description: Generate senior-consultant-quality issue trees and problem decompositions for ambiguous problems, including consulting cases, diligence, market sizing, technical architecture, policy, scientific evidence, operations, and messy client prompts. Use when a user asks to structure a problem, build an issue tree, decompose research, choose a framework, define branches for analysis, or create full and pruned decision trees with evidence requirements.
---

# Problem Decomposition

Use this skill to turn an ambiguous question into a decision-ready issue tree. The goal is not a neat hierarchy. The goal is an executable thinking artifact: a full logical tree, a pruned decision tree, branch logic semantics, and leaf evidence requirements.

## Load References

Load only what the task needs:

- `references/methodology.md`: core workflow and validation rules.
- `references/decomposition_axes.md`: axis library for unusual or ambiguous problems.
- `references/archetypes.md`: consulting and non-consulting examples as priors.
- `references/output_contract.yaml`: machine-readable structure for strict outputs.
- `references/kie_adapter.md`: Keystone integration mode.
- `references/quality_gates.md`: deeper self-check and critique rubric.

## Modes

Use `standalone_consultant` by default. Use `kie_integration` when the user mentions Keystone, KIE, specification engine, downstream research agents, artifact requirements, branch prompts, or machine-readable output.

## Workflow

1. Frame the problem before decomposing.
   - decision maker or audience
   - decision/question
   - situation, complication, governing question
   - R1 undesired result and R2 desired result
   - constraints, time frame, accuracy needed, and expected action

2. Ask clarifying questions only when missing information would materially change the tree or research budget. Otherwise state assumptions and proceed.
   - If the decision maker, R1/R2 gap, time horizon, decision action, or evidence standard is unknown and would change the tree, either ask a blocking question or create an explicit objective-definition/evidence-validation branch.

3. Generate candidate decomposition axes.
   - For ambiguous problems, produce 2-3 top-level axis candidates.
   - State what each axis reveals, hides, and risks.
   - Select or merge the best axis before building the main tree.

4. Build the full issue tree.
   - Logic belongs to sibling groups, not only individual nodes.
   - For each material sibling group, label source logic, truth logic, and evaluation logic when relevant.
   - Use labels such as `AND`, `OR`, `weighted_factor`, `diagnostic_candidates`, `constraint_gate`, `minimum_bottleneck`, `sequence`, `causal_chain`, `portfolio`, `evidence_sufficiency`, or `custom`.
   - Parent nodes should state the insight implied by children, not generic labels.
   - Use asymmetric depth where branch value demands it.
   - Kept top-level branches should include at least one named mechanism, measurable variable or observable proxy, decision consequence, and disconfirming test.

5. Validate MECE by source logic.
   - Sequence: steps produce the parent outcome.
   - Structure: parts cover the whole.
   - Class: siblings share one attribute and obvious members are not missing.
   - Diagnostic: causes are distinct enough to test.
   - Criteria: decision criteria cover R2 without double-counting.

6. Produce a pruned decision tree.
   - Keep branches that can change the answer.
   - Defer or prune low-impact, already-known, low-influence, or high-cost branches.
   - Show pruning rationale, risk if wrong, value of information, and reopen condition.

7. Attach leaf resolution plans.
   - research question or resolution criterion
   - evidence required
   - expected artifact
   - disconfirming evidence to seek
   - likely sources or methods

8. Run a quality self-check and revise once if the tree fails a material gate.

## Output Shape

For normal use, return:

1. `Problem Frame`
2. `Clarifying Questions Or Assumptions`
3. `Candidate Axes`
4. `Selected Axis Rationale`
5. `Full Issue Tree`
6. `Pruned Decision Tree`
7. `Leaf Resolution Plan`
8. `Quality Check`

For `kie_integration`, also include a compact YAML or JSON block with node IDs, parent IDs, branch logic, priority, evidence requirements, expected artifact, and prune status. Use `references/output_contract.yaml` for strict schema needs.
Use `nodes[]`, `edges[]`, `sibling_groups[]`, `leaf_tasks[]`, `pruning_decisions[]`, and `quality_gate_results[]` when strict machine readability matters.

## Guardrails

- Do not use SWOT, 4Ps, Porter, 3C, market/customer/company/competition, or any familiar framework unless it clearly fits the problem frame. If used, explain why the frame matches the R1/R2 gap.
- Do not make every branch the same depth for visual symmetry.
- Do not convert the full tree directly into a research plan. Prune first.
- Do not bury uncertainty. Show what would change the tree.
- Do not present raw hidden reasoning. Provide structured rationale, assumptions, and branch logic.
- Keep examples and archetypes out of benchmark prompts. If an example materially resembles the task, disclose the overlap in eval hygiene notes.
- For low-stakes or narrow prompts, use a lightweight output: frame, selected axis, compact tree, top evidence tests, and quality check.
