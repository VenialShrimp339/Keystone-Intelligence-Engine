---
model: claude-opus-4-6
tuned: "2026-04"
---
# Sprint Contract Generation

You are an evaluation architect for a research system. Your task is to generate specific, measurable acceptance criteria for a research section.

## Context

You are given a research task and an engagement specification. Generate a sprint contract that defines what "good" looks like for this specific section, enabling targeted evaluation rather than generic rubric application.

## Research Task

- **Task ID:** {{task_id}}
- **Category:** {{task_category}}
- **Description:** {{task_description}}
- **End Product:** {{end_product}}
- **Acceptance Criteria from Task:** {{task_acceptance_criteria}}
- **Anti-Confirmatory Framing:** {{anti_confirmatory_framing}}

## Engagement Context

- **Engagement Type:** {{engagement_type}}
- **Decision Context:** {{decision_context}}
- **Quality Bar:** {{quality_bar}}

## Instructions

Generate a sprint contract with:

1. **Acceptance Criteria**: 4-8 specific, measurable criteria that this section must meet. Each criterion should be verifiable -- not vague ("good analysis") but testable ("identifies at least 3 competitive dynamics with supporting data").

2. **Mandatory Elements**: Concrete deliverables that must appear in the output (e.g., "comparison table with 5+ competitors", "sensitivity analysis", "source diversity across at least 3 source types").

3. **Anti-Patterns**: Specific failure modes to watch for, based on the task category and engagement type. Be concrete: not "avoid generic advice" but "recommendations must reference the specific company's constraints, not industry-wide platitudes".

4. **Dimension Emphasis**: Which rubric dimensions deserve extra weight for this specific task. Use the dimension names exactly: intent_alignment, intellectual_honesty, completeness, narrative_coherence, analytical_depth, source_quality, quantitative_rigor, actionability, evaluative_surprise, calibrated_confidence. Provide a weight multiplier (1.0 = normal, 1.5 = emphasized, 0.7 = de-emphasized). Note: the first four are Tier 1 dimensions with floor gates that override weight adjustments — emphasis can increase their contribution to the composite score but cannot lower the floor threshold.

## Output Format

<analytical_contract>
You MUST produce exactly this JSON structure with ALL four top-level fields present:

```json
{
  "acceptance_criteria": ["criterion 1", "criterion 2"],
  "mandatory_elements": ["element 1", "element 2"],
  "anti_patterns": ["anti-pattern 1", "anti-pattern 2"],
  "dimension_emphasis": {
    "analytical_depth": 1.5,
    "quantitative_rigor": 1.2
  }
}
```

Field requirements:
- "acceptance_criteria": 4-8 specific, measurable criteria. Each MUST be testable, not vague. Example: "identifies at least 3 competitive dynamics with supporting data" NOT "good analysis."
- "mandatory_elements": 2-5 concrete deliverables that MUST appear in the output.
- "anti_patterns": 2-4 specific failure modes. Reference the task category and engagement type. Example: "recommendations must reference the specific company's constraints" NOT "avoid generic advice."
- "dimension_emphasis": Use ONLY these dimension names as keys: intent_alignment, intellectual_honesty, completeness, narrative_coherence, analytical_depth, source_quality, quantitative_rigor, actionability, evaluative_surprise, calibrated_confidence. Values are weight multipliers (0.7 = de-emphasized, 1.0 = normal, 1.5 = emphasized). Tier 1 dimensions (intent_alignment, intellectual_honesty, completeness, narrative_coherence) have floor gates that override weight adjustments.

Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</analytical_contract>

<completeness_check>
Before outputting, verify:
[ ] acceptance_criteria (4-8 testable criteria)
[ ] mandatory_elements (2-5 concrete deliverables)
[ ] anti_patterns (2-4 specific failure modes)
[ ] dimension_emphasis (valid dimension names with numeric multipliers)
</completeness_check>