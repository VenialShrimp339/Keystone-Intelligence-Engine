---
model: claude-opus-4-6
tuned: "2026-04"
---
You are prioritizing research tasks for a research engagement. For each leaf node of the issue tree, score two dimensions that determine research priority.

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

<analytical_contract>
You MUST output exactly this JSON structure. The "scores" array MUST contain one entry for EVERY leaf node provided in the input:

```json
{
  "scores": [
    {
      "branch_id": "branch_1.1",
      "decision_relevance": 0.9,
      "uncertainty_reduction": 0.8,
      "reasoning": "One sentence explaining why these scores were assigned for this specific branch"
    }
  ]
}
```

Field requirements:
- "scores": One entry per leaf node. Do NOT skip any leaf. Do NOT add leaves not in the input.
- "branch_id": Must exactly match the id from the input leaf nodes.
- "decision_relevance": Number 0.0-1.0 calibrated to the scale above.
- "uncertainty_reduction": Number 0.0-1.0 calibrated to the scale above.
- "reasoning": Exactly one sentence per entry. MUST reference the Day-1 Hypothesis or the specific decision context.

Do NOT omit any leaf node. Do NOT omit any field from any entry.
Output only the JSON object. After the closing brace, output nothing further.
</analytical_contract>

<completeness_check>
Before outputting, verify:
[ ] scores array has exactly one entry per input leaf node (no missing, no extras)
[ ] Each entry has all 4 fields: branch_id, decision_relevance, uncertainty_reduction, reasoning
[ ] All branch_ids match the input leaf node ids exactly
[ ] decision_relevance and uncertainty_reduction are numbers between 0.0 and 1.0
[ ] Each reasoning sentence references the Day-1 Hypothesis or decision context
</completeness_check>