# Skill Implications for Portable Issue-Tree Generation

## Core Design Choice

The final skill should not begin with "make it MECE." It should begin with "make the decision question explicit." MECE becomes useful only after the problem frame determines the universe to divide.

## Required Output Contract

The skill should produce:

1. Problem frame: situation, complication, governing question, provisional answer if known.
2. R1/R2 gap: current undesired result, desired result, disturbing event, and solution stance.
3. Full issue tree: exhaustive enough to show the logical universe.
4. Pruned decision tree: retained branches, deferred branches, and pruning rationale.
5. Leaf resolution criteria: yes/no tests, metrics, evidence requirements, and likely sources.
6. Branch logic audit: source logic for every sibling group.
7. Anti-pattern audit: specific failures checked and corrected.

## Prompting Moves to Add

Ask the model to identify the reader's current solution stance:

- No solution known.
- Proposed solution needs validation.
- Accepted solution needs implementation.
- Prior solution failed.
- Alternatives are already live.
- Desired result is underspecified.
- Current gap is uncertain.

Ask the model to label each branch set as one of:

- Sequence.
- Structure.
- Class.
- Deductive chain.
- Criteria comparison.
- Evidence test set.

Ask the model to rewrite every weak parent label into an insight. Example transformation: replace "cost issues" with "unit cost is rising because labor hours per output unit and input prices are both worsening."

Ask the model to distinguish diagnostic and solution branches. If both are needed, produce two trees.

Ask the model to convert concerns into yes/no issues. Example: "customer churn" becomes "Is churn concentrated in segments where onboarding time exceeds target?"

## KIE Integration Fields

For `kie_integration` mode, each node should carry machine-readable fields:

```yaml
node_id: string
parent_id: string | null
claim: string
node_type: root | frame | diagnostic_branch | solution_branch | criterion | evidence_test | action | risk | constraint
branch_logic: sequence | structure | class | deductive | criteria | test_set
question_answered: string
resolution_criterion: string | null
evidence_required:
  - metric_or_fact: string
    source_type: string
    expected_discriminator: string
decision_impact: high | medium | low
evidence_cost: high | medium | low
prune_status: retain | defer | reject
prune_rationale: string
confidence: high | medium | low
```

## Standalone Consultant Mode

For `standalone_consultant`, the model should write in a concise consultant package:

- One-line answer.
- Situation and complication.
- Full tree.
- Pruned tree.
- Workplan by evidence test.
- Risks and open questions.
- Final recommendation logic.

## Evaluation Guidance

Eval rubrics should grade properties, not exact tree labels:

- Did the answer find the real governing question?
- Did it define R1 and R2?
- Did it route to the right tree type?
- Are sibling branches governed by one source logic?
- Are parent nodes real insights?
- Are leaves testable?
- Does pruning preserve decision-changing branches?
- Does the answer avoid inventing straw alternatives?
- Does it separate diagnosis from recommendation?

## Implementation Guardrails

The skill should actively reject generic framework substitution. A SWOT, 3C, 4P, value-chain, or financial-driver tree is acceptable only if the answer explains why that framework matches the problem's opening scene and R1/R2 gap.

The skill should force a "no more than necessary" standard for branch depth. Go deep where a branch is high-impact, uncertain, and testable. Keep shallow branches that are low-impact, already known, or only constraints.

The skill should require pruning commentary. A senior-quality issue tree shows what was excluded and why.

The skill should use Minto's logic as a validation layer after generation:

1. Does each parent raise the question answered by its children?
2. Do siblings share one logic mode?
3. Does the grouping source determine order?
4. Does the parent summarize the children without overclaiming?
5. Do leaves resolve through evidence or action?

## Skill Drafting Recommendation

The final portable `SKILL.md` should be lean. Put the full methodology in references. The core runtime instruction should be a short loop:

1. Frame.
2. Route.
3. Generate.
4. Validate.
5. Prune.
6. Attach evidence.
7. Audit failure modes.

Minto should supply the validation and pruning spine, while other sources can add richer decomposition axes and modern decision-quality scoring.
