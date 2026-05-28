# Sydney Airport Capacity Eval: Baseline Output

Case: `bps_sydney_airport_capacity`

Executor condition: baseline agent, no skill package, no book artifacts, no external sources.

## Output Summary

The baseline framed the question as whether Sydney Airport will have enough effective passenger capacity over the future horizon under acceptable service standards after demand growth, operating constraints, planned investments, and diversion to alternatives such as Western Sydney Airport.

The full tree used five top branches:

1. demand
2. capacity
3. expansion and mitigation
4. feasibility
5. adequacy conclusion

The demand branch covered annual passenger demand, peak demand, aircraft movement demand, demand drivers, and demand diversion or substitution.

The capacity branch covered airfield capacity, regulatory operating capacity, terminal processing, gates/stands/apron, baggage, landside access, enabling infrastructure, and resilience.

The pruned decision tree kept:

1. define adequacy standard and horizon
2. forecast passenger demand by segment and peak period
3. identify the binding constraint
4. test committed capacity additions
5. test feasible additional interventions

The leaf evidence table was broad and operationally useful, including annual demand, peak profile, runway capacity, curfew and movement caps, gates, landside, Western Sydney diversion, committed projects, physical expansion, and policy changes.

## Strengths

- Strong treatment of bottleneck capacity versus annual totals.
- Good coverage of demand, supply, regulatory constraints, and mitigation options.
- Useful evidence table with airport-specific leaf requirements.
- Correctly recognized peak-period failure risk.

## Weaknesses

- Did not explicitly select and justify a capacity-equation decomposition axis.
- Spread depth across many airport-planning topics before isolating runway utilization.
- Treated Western Sydney and broader system relief as a prominent branch without bounding it relative to the core runway-capacity question.
- Branch logic was explained narratively rather than encoded as sibling-group semantics.
