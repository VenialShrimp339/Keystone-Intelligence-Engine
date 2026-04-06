You are prioritizing research tasks for a consulting engagement. For each leaf node of the issue tree, score two dimensions that determine research priority.

## Input

**Day-1 Hypothesis:** {{day_1_hypothesis}}
**Engagement Type:** {{engagement_type}}

### Leaf Nodes to Score
{{leaves}}

## Scoring Dimensions

### Decision Relevance (0.0 - 1.0)
How directly does this branch's answer affect the decision the client needs to make?
- 1.0: The decision cannot be made without this answer
- 0.7-0.9: Important input but the decision could proceed without it
- 0.4-0.6: Useful context but not decision-critical
- 0.1-0.3: Nice to have, does not change the decision

### Uncertainty Reduction (0.0 - 1.0)
How much does researching this branch reduce uncertainty about the Day-1 Hypothesis?
- 1.0: This branch directly tests the hypothesis and could confirm or refute it
- 0.7-0.9: Provides strong evidence for or against the hypothesis
- 0.4-0.6: Provides moderate evidence or context for the hypothesis
- 0.1-0.3: Tangentially related, low information gain

## Priority Formula

priority_score = decision_relevance x uncertainty_reduction

Higher scores indicate branches that should be researched first (they matter most to the decision AND reduce the most uncertainty).

## Output Format

Respond with ONLY a JSON object:

```json
{
  "scores": [
    {
      "branch_id": "branch_1.1",
      "decision_relevance": 0.9,
      "uncertainty_reduction": 0.8,
      "reasoning": "One sentence explaining the scores"
    }
  ]
}
```
