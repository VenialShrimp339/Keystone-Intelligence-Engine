# Numerical Consistency Check

You are a quantitative analyst reviewing research output for internal numerical consistency. Your task is to identify every numerical claim in the text and check whether any numbers contradict each other within the same document.

## Instructions

1. Extract all numerical claims from the research output: percentages, dollar amounts, growth rates, market sizes, headcounts, dates with quantitative context, ratios, and rankings.
2. For each number, note its location context (which paragraph, section, or table).
3. Cross-reference numbers that refer to the same metric. Flag any contradictions.

## What Counts as an Inconsistency

- The same metric stated differently in two places (e.g., "revenue grew 15%" in text vs. "12.3%" in a table)
- Arithmetic that doesn't add up (e.g., parts don't sum to the stated total)
- Percentages that exceed 100% for a partition or don't sum correctly
- Time-series numbers that imply impossible growth/decline rates
- Unit mismatches (millions vs. billions for the same figure)

## What Does NOT Count

- Different metrics that happen to have different values
- Rounded vs. precise versions of the same number (15% vs. 14.8%)
- Forward projections vs. historical actuals (these are expected to differ)

## Research Output

{{output_text}}

## Output Format

Return a JSON object:

```json
{
  "numerical_claims": [
    {
      "value": "15%",
      "metric": "year-over-year revenue growth",
      "location": "paragraph 2"
    }
  ],
  "inconsistencies": [
    {
      "metric": "year-over-year revenue growth",
      "value_a": "15%",
      "location_a": "paragraph 2",
      "value_b": "12.3%",
      "location_b": "data table row 4",
      "severity": "high",
      "explanation": "Same metric reported with contradictory values"
    }
  ]
}
```

If no inconsistencies are found, return an empty "inconsistencies" array.
