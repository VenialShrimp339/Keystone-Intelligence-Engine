# Issue-Tree Skill Handoff

Date: 2026-05-28

Worktree: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization`

## Scope Completed

Built the first portable foundation for a world-class issue-tree/problem-decomposition skill that can run as:

1. a standalone consultant skill
2. a Codex/Claude local skill package
3. a future Keystone Intelligence Engine specification-stage adapter

The source books were analyzed into derived artifacts under `audit/issue-tree-skill/books/`. Raw extracted book text was not stored in the repository.

Extraction status:

- `Bulletproof Problem Solving`: orchestrator fallback from local EPUB text extraction after the book agent ran long.
- `The Pyramid Principle`: subagent-completed extraction from the PDF.
- `The McKinsey Mind`: orchestrator fallback from local PDF text extraction after the book agent ran long.

Graphify artifacts were not present at session start, so no graphify wiki context was available.

## What The Books Taught Us

The combined method is stronger than a generic MECE prompt:

- A senior-quality issue tree starts with the governing question, decision owner, R1/R2 gap, action implication, and evidence standard.
- MECE is a validation rule, not the whole method.
- The generative move is choosing the right decomposition axis before building the tree.
- A useful tree needs branch logic semantics: source logic, truth logic, evaluation logic, exclusivity, and exhaustiveness.
- Full coverage and execution focus are different artifacts. Build the full tree, then prune into the decision tree.
- Pruning should be visible and based on value of information, impact, uncertainty, evidence cost, influenceability, discriminating power, and dependency.
- Leaf nodes should become resolvable evidence questions or artifact requirements, not vague topics.
- Consulting archetypes are useful as exemplars and priors. They become harmful when used as canned templates.
- Some excellent decompositions are not symmetrical. The tree should get deeper where the answer lives.

## Main Artifacts

- Extraction plan: `audit/issue-tree-skill/EXTRACTION-PLAN.md`
- KIE specification gap notes: `audit/issue-tree-skill/KIE-SPECIFICATION-GAP-NOTES.md`
- Book-derived artifacts: `audit/issue-tree-skill/books/`
- Unified methodology pack: `audit/issue-tree-skill/methodology/UNIFIED-METHODOLOGY-PACK.md`
- Decomposition axis library: `audit/issue-tree-skill/methodology/DECOMPOSITION-AXIS-LIBRARY.md`
- Consulting archetypes: `audit/issue-tree-skill/methodology/CONSULTING-ARCHETYPES.md`
- Quality gates: `audit/issue-tree-skill/methodology/QUALITY-GATES.md`
- KIE adapter design: `audit/issue-tree-skill/methodology/KIE-INTEGRATION-ADAPTER.md`
- Portable skill: `.agents/skills/problem-decomposition/SKILL.md`
- Skill references: `.agents/skills/problem-decomposition/references/`
- Eval strategy: `audit/issue-tree-skill/evals/EVAL-STRATEGY.md`
- Book-derived eval manifest: `audit/issue-tree-skill/evals/book-derived/BOOK-DERIVED-EVAL-MANIFEST.yaml`
- Novel stress tests: `audit/issue-tree-skill/evals/novel-stress-tests/novel-stress-tests.yaml`
- First blind eval result: `audit/issue-tree-skill/evals/book-derived/sydney-comparison.md`

## What The Skill Now Does

The skill generates:

- problem frame
- clarifying questions or explicit assumptions
- candidate decomposition axes
- selected axis rationale
- full issue tree
- pruned decision tree
- branch/sibling logic semantics
- leaf resolution plan
- evidence and artifact requirements
- quality self-check
- optional KIE-oriented machine-readable package

The strict contract now uses:

- `nodes[]`
- `edges[]`
- `sibling_groups[]`
- `leaf_tasks[]`
- `pruning_decisions[]`
- `quality_gate_results[]`

This is materially better for KIE than the current runtime spec tree because logic lives on sibling groups and full/pruned tree states are explicit.

## Eval Results

First blind book-derived eval:

Case: Sydney Airport future passenger capacity.

Baseline agent: no skill.

Treatment agent: used `.agents/skills/problem-decomposition/SKILL.md`.

Scores:

| Dimension | Baseline | Skill |
|---|---:|---:|
| problem_frame | 4 | 5 |
| axis_selection | 3 | 5 |
| mece_and_branch_logic | 3 | 4 |
| expert_property_coverage | 4 | 5 |
| hypothesis_and_decision_relevance | 4 | 5 |
| asymmetric_depth_and_pruning | 3 | 5 |
| leaf_resolution_actionability | 4 | 5 |
| framework_misuse_penalty | -1 | 0 |

Result: skill output won, 34 after penalty versus baseline 24.

Why: the skill selected a supply/demand bottleneck axis, used a capacity equation, made peak-period bottlenecks explicit, and surfaced controllable runway/slot/gauge/peak-spreading levers.

Confidence: high for this single eval. Low to medium for general readiness until the recommended eval subset is run.

## Strengths

- Strong portable methodology spine.
- Clear separation between method, examples, output contract, evals, and KIE adapter.
- Better than baseline on the first hidden-rubric book-derived eval.
- Full-tree and pruned-tree distinction is explicit.
- Branch logic semantics are now machine-representable.
- Leaf tasks are close to KIE-ready research briefs.

## Weaknesses

- The initial blind eval weakness is now reduced: a 13-case baseline-vs-skill run completed on 2026-05-28 with 11 skill wins, 0 baseline wins, 2 ties, no catastrophic failures, and schema-compliant outputs.
- The skill is now wired into KIE prototype code through `IssueTreePackage` and approved-leaf task bridging, but the LLM package-builder prompt path and HITL approval view are still pending.
- Bulletproof and McKinsey extraction artifacts were orchestrator fallback artifacts, not completed independent book-agent deliverables.
- The contract is a target schema, not a validated Pydantic model.
- The skill still depends on the executor model following quality gates. More adversarial evals are needed to measure compliance.

## Readiness Recommendation

Ready for live-controller prototype integration.

Still not ready for direct production KIE integration until:

1. live multi-branch provider runs prove the package-to-provider path,
2. a package-builder prompt path invokes the skill and validates the Pydantic schema,
3. a HITL approval view exists for problem frame, axes, pruned leaves, and pruning decisions,
4. source reconciliation from live provider exports is robust enough for cited synthesis.

## Exact Next KIE Step

Replace the fixture controller with a live browser-provider controller, while keeping `IssueTreePackage` as the dispatch artifact.

Implementation sequence:

1. Add a prompt path that invokes the problem-decomposition skill/methodology to produce and validate `IssueTreePackage`.
2. Add a HITL approval view for the problem frame, candidate axes, full tree, pruned tree, pruning decisions, and leaf evidence plan.
3. Replace the fixture `BrowserProviderController` with a live Chrome/plugin controller.
4. Run a multi-branch provider prototype from approved `leaf_tasks[]`.
5. Keep the existing decomposer as fallback until live package-driven provider runs are stable.

This preserves KIE's current lens and task machinery while fixing the upstream issue-tree quality gap.
