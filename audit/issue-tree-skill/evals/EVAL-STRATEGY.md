# Issue-Tree Skill Eval Strategy

Date: 2026-05-28

## Principle

Grade the properties that make an issue tree useful, not whether the output matches a single reference tree. Multiple high-quality decompositions can be valid when the axis choice is defensible and the resulting leaves resolve the decision.

## Track 1: Book-Derived Blind Evals

Executor sees:

- problem statement
- any minimal context needed to make the problem fair
- the issue-tree skill if this is the treatment arm

Executor does not see:

- source book
- reference decomposition
- hidden rubric
- evaluation properties

Grader sees:

- problem statement
- executor output
- hidden property rubric derived from the book example
- concise reference logic in paraphrased form

Grader should score:

- whether the output chooses a defensible top-level axis
- whether load-bearing branches from the expert example are covered
- whether sibling sets are MECE for the chosen axis
- whether branch depth follows decision value instead of uniform formatting
- whether the leaves are resolvable by evidence or analysis
- whether pruning rationale is visible and defensible
- whether the output avoids a generic framework where the example required custom reasoning

The grader should not require exact label matching or exact tree topology.

## Track 2: Novel Stress Tests

Novel cases have no book answer key. They test abstract quality across domains:

- public company diligence
- market sizing
- technical architecture
- policy design
- scientific evidence review
- operations/root-cause diagnostics
- messy client prompt with missing context

Grader should score 1-5 on:

- problem framing precision
- axis selection
- MECE discipline at every sibling set
- parent-child logic semantics
- decision relevance
- hypothesis density
- asymmetric depth discipline
- pruning discipline
- leaf actionability and evidence requirements
- handling of ambiguity and clarifying questions

## Baseline vs. Skill Comparison

Run the same prompt in two arms:

- baseline: executor gets only the problem and a generic request to create a high-quality issue tree
- skill: executor gets the problem plus the portable problem-decomposition skill

Comparator should report:

- winner by case
- largest quality deltas
- failure clusters in the skill arm
- whether the skill is causing over-structure or framework misuse

## Framework Misuse Penalty

Do not add a heavy penalty at first. Apply a simple penalty only when the output uses a named framework or canned branch set without showing why it fits the problem. If early evals show recurrent misuse, split this into a stricter rubric dimension.

