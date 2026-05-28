# Issue-Tree Skill Eval Report

Date: 2026-05-28

## Verdict

Integrate after targeted patch.

Confidence: high for integration gating, medium for absolute quality scoring. The run used schema-enforced executor outputs, hidden-rubric comparison, and a targeted rerun after patching the skill contract.

## Method

- Visible set: 7 recommended book-derived cases plus 6 novel stress tests.
- Baseline arm: same visible prompts, no access to the problem-decomposition skill or hidden rubrics.
- Skill arm: same visible prompts, access to `.agents/skills/problem-decomposition/` in `kie_integration` mode.
- Comparator: read baseline output, skill output, selected visible cases, eval strategy, hidden book-derived candidate rubrics, novel stress tests, and abstract rubric.
- Required dimensions: problem framing, axis selection, MECE/branch logic, expert-property coverage, decision relevance, asymmetric depth/pruning, leaf actionability, framework misuse, schema compliance, catastrophic failure.

## Aggregate Result

- Skill wins: 11 of 13.
- Baseline wins: 0 of 13.
- Ties: 2 of 13.
- Baseline average: 35.923 of 40.
- Skill average: 39.077 of 40.
- Average lift: +3.154 points.
- Catastrophic failures: none in either arm.
- Machine-readable schema compliance: true in both arms.

## Main Lift

The skill produced clearer decision frames, candidate-axis comparison, explicit sibling logic, visible pruning rationale, and more actionable leaf evidence requirements. The largest gains appeared in Sydney airport capacity, rooftop solar timing, sales growth diagnosis, Acme Thrum mat cost, public-company diligence, and technical architecture.

## Failure Clusters Before Patch

- The skill sometimes made the pruned tree a long KEEP/DEFER ledger rather than a compact decision tree.
- Some novel cases used concise frames without fully explicit decision maker, R1/R2, and constraints.
- HSDD remained too broad after pruning.
- No recurrent canned-framework misuse appeared.

## Patch Applied

Files patched:

- `.agents/skills/problem-decomposition/SKILL.md`
- `.agents/skills/problem-decomposition/references/methodology.md`
- `.agents/skills/problem-decomposition/references/output_contract.yaml`
- `.agents/skills/problem-decomposition/references/quality_gates.md`

Patch intent:

- Require explicit decision maker, R1, R2, and constraints in Keystone and machine-readable mode.
- Define the pruned tree as the retained executable spine.
- Move verbose KEEP/DEFER/PRUNE/MERGE rationale into `pruning_decisions[]`.
- Require a second pruning pass or broad-map label when more than 8 retained leaves survive.

## Targeted Rerun

Rerun cases:

- `mind_hsdd_market_sizing`
- `novel_policy_001`
- `novel_messy_prompt_001`

Targeted result:

- HSDD: 4 leaf tasks, 5 pruned-tree entries, 8 quality gates.
- Policy: 5 leaf tasks, 6 pruned-tree entries, 8 quality gates.
- Messy prompt: 5 leaf tasks, 6 pruned-tree entries, 8 quality gates.

The targeted rerun resolves the specific patch issues: retained trees are compact, frame assumptions are explicit, and pruning ledgers are separated from the tree body.

## Integration Decision

Proceed with integration. The skill demonstrates clear lift over baseline, no catastrophic failures, valid machine-readable output, and a patched contract for the observed failure clusters.
