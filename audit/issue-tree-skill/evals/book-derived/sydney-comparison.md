# Sydney Airport Capacity Eval: Baseline vs Skill

Case: `bps_sydney_airport_capacity`

Hidden rubric basis: book-derived properties from the Sydney Airport capacity worked example. The executor agents did not see the hidden rubric.

## Scores

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

Baseline total before penalty: 25 / 35

Skill total before penalty: 34 / 35

Baseline total after penalty: 24

Skill total after penalty: 34

## Result

Winner: skill output.

The skill output was stronger because it framed the case as a capacity equation: future passenger load requiring Sydney Airport versus effective capacity of the binding bottleneck. That directly matched the hidden reference logic.

It also handled the key expert property better: runway utilization and controllable airfield levers. It named runway movements, sequencing, curfew and slot rules, taxiway congestion, aircraft gauge, delay recovery, pricing, slots, peak spreading, and gauge incentives.

The baseline was solid and broad, but it spread depth across terminals, landside, feasibility, resilience, and Western Sydney relief before isolating the capacity bottleneck. The baseline partially risked broad transport-operations coverage before the highest-leverage runway-capacity analysis.

Confidence: high.
