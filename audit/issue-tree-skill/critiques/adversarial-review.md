# Adversarial Review

Reviewer scope:

- `audit/issue-tree-skill/methodology/UNIFIED-METHODOLOGY-PACK.md`
- `audit/issue-tree-skill/methodology/QUALITY-GATES.md`
- `audit/issue-tree-skill/methodology/DECOMPOSITION-AXIS-LIBRARY.md`
- `.agents/skills/problem-decomposition/SKILL.md`
- `.agents/skills/problem-decomposition/references/methodology.md`
- `.agents/skills/problem-decomposition/references/output_contract.yaml`

## Judgment

The method is strong conceptually, but the first draft was not yet KIE-grade portable. It could guide a good human or strong model, but the skill and schema left too much quality to self-discipline.

## Findings

1. High: the output contract was too weak for KIE integration. It defined singular node, leaf, and pruning shapes but no explicit `nodes[]`, `edges[]`, `sibling_groups[]`, `full_tree`, or `pruned_tree` collections.

2. High: branch logic semantics were conflated. The method mixed truth logic, grouping logic, process logic, diagnostic logic, and evaluation logic in one label set.

3. High: the gates were mostly self-attestation, so shallow generic trees could still pass.

4. Medium: ambiguity handling was too permissive for portable generation.

5. Medium: pruning lacked quantitative discipline.

6. Medium: eval leakage risk was unaddressed.

7. Low: overengineering risk was real for small tasks.

## Fixes Applied

1. Replaced the strict contract with explicit `nodes[]`, `edges[]`, `sibling_groups[]`, `leaf_tasks[]`, `pruning_decisions[]`, and `quality_gate_results[]`.

2. Moved logic semantics to sibling groups, separating source logic, coverage logic, truth logic, evaluation logic, exclusivity, exhaustiveness, and validation note.

3. Added anti-genericity gates requiring named mechanisms, measurable variables or observable proxies, decision consequences, and disconfirming tests.

4. Added ambiguity escalation rules for unknown decision maker, R1/R2 gap, horizon, action implication, and evidence standard.

5. Added auditable pruning fields: impact, uncertainty, evidence cost, discriminating power, influenceability, dependencies, value of information, risk if wrong, and reopen condition.

6. Added eval hygiene requirements to separate archetype examples from benchmark cases.

7. Added lightweight mode guidance for low-stakes prompts.

## Residual Risk

The patched contract is suitable as a first portable schema, but it has not yet been implemented inside KIE runtime code or validated across the full book-derived eval set. The next gate should run at least the recommended seven-case subset before treating the skill as ready for direct KIE integration.
