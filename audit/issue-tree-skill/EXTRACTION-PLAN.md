# Issue-Tree Skill Extraction Plan

Date: 2026-05-28

## Objective

Build a portable issue-tree and problem-decomposition skill that improves LLM performance on ambiguous consulting and non-consulting problems. The extraction target is derived methodology, judgment, examples, evaluation standards, and failure modes from the three source books. The final package must help a model generate both a full tree and a visibly pruned decision tree with branch logic, leaf resolution criteria, and evidence requirements.

## Source Agents

Each book agent reads with the same mission: identify anything that would make an LLM better at senior-consultant-quality decomposition. Expected themes include problem framing, MECE logic, issue/hypothesis trees, decomposition axes, prioritization, pruning, branch depth, worked examples, and bad patterns, but agents must record useful surprises outside that taxonomy.

Each agent produces the same seven derived artifacts:

1. `book-brief.md`: concise thesis of what the book teaches the skill.
2. `methodology-primitives.yaml`: reusable rules, concepts, moves, checks, and decision criteria.
3. `worked-examples.md`: paraphrased worked examples with concise trees or logic structures.
4. `eval-candidates.yaml`: candidate blind evals with visible problem prompt and hidden grading properties.
5. `surprise-register.md`: unexpected insights relevant to the skill.
6. `anti-patterns.md`: failure modes the book helps detect or avoid.
7. `skill-implications.md`: concrete changes the final skill should make because of this source.

## Worked Example Handling

Worked examples should be transformed into a reusable evaluation shape:

- visible executor prompt: the problem only, cleaned of answer leakage
- hidden reference logic: concise paraphrase of the expert decomposition
- hidden property rubric: what a good answer must cover, why the branch logic matters, expected depth/asymmetry, and common traps
- grading rule: score properties, not exact tree similarity

Do not copy long passages. Keep example descriptions short and paraphrased. Use quoted fragments only when a precise term is essential, and keep them brief.

## Methodology vs. Copyrighted Text

The final artifacts should contain derived methods and compact examples. Source text is used for private analysis only and is not stored in the repo as raw book dumps. Rubrics should encode expert properties in our own wording, not reproduce book prose.

## Blind Eval Candidate Criteria

An example is suitable for a book-derived blind eval when:

- the problem can be stated without revealing the answer
- the source gives enough expert reasoning to derive a hidden rubric
- there are load-bearing properties that multiple valid trees could satisfy
- the case exposes at least one failure mode, such as wrong axis, shallow MECE, lazy parallelism, or poor pruning
- the grading can be done on properties instead of matching exact branch labels

Novel stress tests should cover ambiguous domains with no answer key: public company diligence, technical architecture, policy, scientific evidence, operations, and messy client prompts.

## Portability Constraint

The portable skill should live as a lean `SKILL.md` plus references loaded only when useful. It must not assume Claude-only, Codex-only, or Keystone-only runtime behavior.

The skill will support two modes:

- `standalone_consultant`: human-readable issue-tree package for a consultant.
- `kie_integration`: same tree plus machine-readable fields suitable for KIE L0 specification, HITL approval, and downstream branch research.

The KIE adapter should remain a reference layer, not a hard dependency inside the core method.

