# Unified Issue-Tree Methodology Pack

Date: 2026-05-28

## Core Thesis

A senior-quality issue tree is an executable model of a problem. It is built to answer a decision question, expose the right causal or decision structure, test the hypotheses that matter, and convert leaves into evidence-producing work. MECE is a necessary quality property, but the harder skill is choosing the cleaving axis that makes the answer visible.

The derived method combines:

- Conn/McLean: problem definition, multiple cleaving frames, iteration, prioritization, and pruning
- Minto: reader-question anchoring, R1/R2 gap framing, vertical question-answer logic, horizontal grouping logic, and diagnostic versus solution tree separation
- Rasiel/Friga: hypothesis-first issue trees, quick assumption tests, key-driver focus, workplan linkage, and communication validation

## Process

### 1. Frame The Problem

Create a compact frame before decomposition:

- decision maker or audience
- decision to make or question to answer
- Situation: known baseline
- Complication: event, discrepancy, proposed solution, or uncertainty creating the need for analysis
- R1: current or likely undesired result
- R2: desired result
- solution stance: no solution, proposed solution, accepted solution, failed solution, known alternatives, unclear R2, or uncertain R1
- scope boundaries, time frame, accuracy required, constraints, and action expected after resolution

If R2 is unclear, create an objective-definition branch before diagnosis.

### 2. Generate Candidate Cleaving Axes

For ambiguous problems, generate 2-3 candidate top-level cuts. For each axis, state what it reveals, what it hides, and when it would be wrong.

Common candidates:

- component/factor
- causal driver
- lever/intervention
- supply/demand
- incidence/severity
- stakeholder/incentive
- process/value chain
- funnel or conversion path
- financial equation
- criteria/option selection
- uncertainty strategy
- system feedback/externality
- evidence sufficiency

Select or merge the axis that best exposes decision leverage, produces non-overlapping top-level branches, and yields resolvable leaves.

### 3. Choose Tree Type

Route by solution stance:

- diagnostic tree: explains why R1 exists
- hypothesis tree: tests what must be true for a provisional answer
- option tree: compares known alternatives against criteria
- lever tree: identifies actions that can move R2
- decision tree: sequences threshold tests and actions
- implementation tree: turns accepted solution into steps, dependencies, and risks
- uncertainty tree: maps information buys, hedges, options, no-regrets moves, and bets
- communication pyramid: turns evidence into a concise recommendation story

Diagnostic and solution trees should be separated unless the diagnosis is already sufficiently proven.

### 4. Build The Full Tree

The full tree shows the logical universe before pruning. It should:

- answer the governing question
- label each sibling group by source logic
- avoid cross-cutting forces as naive sibling branches
- use asymmetric depth where the problem requires it
- rewrite generic parent labels into insight-bearing claims
- push leaves to researchable questions, evidence tests, or resolution criteria

### 5. Label Parent-Child Logic

Every parent node should declare how its children relate:

- `AND`: all conditions must hold
- `OR`: any one condition could explain or satisfy
- `weighted_factor`: criteria trade off by weight
- `diagnostic_candidates`: mutually exclusive or overlapping possible causes to test
- `constraint_gate`: a failing child can kill the recommendation
- `sequence`: steps or dependencies in order
- `causal_chain`: one mechanism leads to another
- `portfolio`: multiple moves can coexist
- `evidence_sufficiency`: children are independent evidence paths
- `custom`: explicitly define the relationship

This avoids the common error of treating every tree as if all branches must be true.

### 6. Validate MECE By Source Logic

MECE is tested differently depending on the grouping:

- sequence: do the steps together produce the stated end product, in the right order?
- structure: do the parts cover the whole without overlap?
- class: do all items share one common attribute, and are obvious members missing?
- deductive chain: does the implication follow from the premises?
- criteria set: do the criteria cover what R2 means without double-counting?
- diagnostic set: are causes distinct enough to test, and are major cause families missing?

Sibling groups must use one logic mode at a time. If a level mixes causes, actions, risks, and metrics, rebuild it.

### 7. Prune Into A Decision Tree

Pruning is visible and separate from full coverage. Retain branches that have high decision impact, high uncertainty, high discriminating power, or low-cost quick-win evidence. Defer or prune branches that are low impact, already known, not influenceable, too costly for the decision, or dominated by another branch.

Each pruning decision records:

- keep, prune, defer, or merge
- rationale
- risk if wrong
- what evidence would reopen the branch

### 8. Attach Leaf Resolution Plans

Each leaf should answer:

- what question does this resolve?
- why does it matter to the decision?
- what evidence would answer it?
- what artifact should be produced?
- what result would confirm, disconfirm, or change priority?
- what disconfirming evidence should be sought?

For KIE, these leaf plans become branch research prompts or task seeds after human approval.

### 9. Synthesize

The tree is a workplan, not the final story. After evidence arrives, synthesize findings across branches and build a communication pyramid:

- governing answer
- 2-4 support points
- evidence or exhibits under each point
- residual risks and next decisions

If the answer cannot pass a short executive-summary test, revisit the tree.

## Full Tree Guidance

Use the full tree to show coverage, hidden assumptions, and branch universe. It can be broad and somewhat larger than the research plan, but it should not be a generic topic taxonomy. Every branch needs a logic role.

The full tree should include cross-cutting influences explicitly. Policy, regulation, technology, incentives, and data availability often affect multiple branches and should be modeled as constraints, annotations, or repeated mechanism-specific tests rather than as one catch-all sibling.

## Pruned Decision-Tree Guidance

Use the pruned tree for execution. It should usually be smaller, more asymmetric, and more testable than the full tree.

Pruned trees should prioritize:

- dominant questions that can eliminate downstream work
- high-impact/high-uncertainty branches
- branches where simple evidence can settle a large part of the decision
- key drivers or bottlenecks
- disconfirming tests for the favored hypothesis

## Non-Consulting Generalization

The method works outside consulting by changing the cleaving axis and evidence standard:

- scientific questions: evidence hierarchy, mechanism, study quality, reproducibility, external validity, and value of information
- technical architecture: problem diagnosis, constraints, trade-offs, failure modes, migration path, operating capability
- policy: objectives, mechanisms, affected groups, fiscal cost, administrative feasibility, legal constraints, political feasibility, externalities
- operations: demand, throughput, bottlenecks, process variation, staffing/capability, measurement artifacts
- personal decisions: weighted criteria, constraints, options, sensitivity, uncertainty, and reversibility
- wicked problems: actors, incentives, externalities, feedback loops, intervention points, least-bad trade-offs

## Failure Modes

- topic inventory disguised as an issue tree
- generic framework substitution
- mixed sibling logic
- full tree used as research plan without pruning
- premature solution tree before diagnosis
- uniform depth
- parent labels with no insight
- yes/no issues replaced by vague topics
- high-powered analysis before framing
- cross-cutting forces placed as standalone branches
- false precision
- no disconfirming evidence path

