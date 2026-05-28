# Sydney Airport Capacity Eval: Skill Output

Case: `bps_sydney_airport_capacity`

Executor condition: treatment agent using `.agents/skills/problem-decomposition/SKILL.md` and its references only. The executor did not inspect `audit/issue-tree-skill`, book artifacts, eval manifests, or hidden rubrics.

## Output Summary

The skill framed the governing question as whether Sydney Airport will have enough passenger capacity over the planning horizon to meet future demand at acceptable service, resilience, and regulatory standards.

It made the decision owner, R1/R2 gap, and provisional hypothesis explicit. The provisional hypothesis was that the decisive tests are peak-period bottlenecks, enforceable aircraft-movement constraints, and the amount of demand shifting to alternatives such as Western Sydney Airport.

The executor produced three candidate axes:

1. supply/demand capacity equation
2. passenger journey process tree
3. scenario and uncertainty tree

It selected a merged supply/demand bottleneck axis:

```text
Future passenger load requiring Sydney Airport <= effective capacity of the binding bottleneck, by time period and scenario
```

The full tree used six top branches:

1. define adequate capacity in decision terms
2. estimate future passenger demand that Sydney Airport must absorb
3. determine effective passenger capacity before interventions
4. test whether Sydney Airport can expand or unlock capacity in time
5. stress-test the demand-capacity balance
6. classify the decision outcome

The pruned tree kept five analyses:

1. adequacy standard
2. net Sydney Airport demand
3. binding capacity bottleneck by period
4. committed and feasible capacity additions
5. high-demand, low-diversion, peak-hour, and disruption stress cases

It pruned or deferred detailed retail/lounge analysis, granular catchment modeling, full airline profitability modeling, and standalone environmental/community assessment unless they become binding constraints.

The leaf resolution plan included resolution criteria, evidence, expected artifact, disconfirming evidence, and method for each kept leaf.

## Strengths

- Matched the hidden reference logic by turning the problem into a supply/demand capacity equation.
- Explicitly distinguished annual capacity from peak-period bottlenecks.
- Named controllable airfield levers: runway movements, sequencing, curfew/slot rules, taxiway congestion, aircraft gauge, delay recovery, pricing, slots, peak spreading, and gauge incentives.
- Produced a visible full tree and pruned decision tree.
- Attached disconfirming evidence and expected artifacts to leaves.

## Weaknesses

- The original schema did not fully capture the richer output, especially sibling groups and full/pruned tree distinction. This was patched after adversarial review.
- The output still treated runway utilization as one key bottleneck among several rather than forcing deeper runway-utilization decomposition by default.
