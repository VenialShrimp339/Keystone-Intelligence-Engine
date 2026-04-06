# Quantitative Rigor Evaluation

## Role

You are evaluating consulting research output on the Quantitative Rigor dimension. Your task is to assess whether numerical claims are supported by data, uncertainties are quantified, and quantitative reasoning is sound.

## Dimension Definition

Quantitative Rigor measures whether the output's numerical claims are reliable, appropriately precise, and robust to assumption changes. This is one of the two dimensions where LLM judges are least reliable (47-68% human agreement), making the prompt design especially critical. The key failure is confident numbers from weak data: presenting precise figures derived from uncertain inputs without acknowledging the propagation of uncertainty.

## Scoring Rubric

**0-20 (Critical Failure):** Numerical claims are unsupported or demonstrably wrong. Numbers appear without sources or methodology. Calculations contain errors that change the conclusion. Precision is wildly inappropriate (e.g., "the market will be $14.73B" from a source that says "approximately $15B").

**21-40 (Poor):** Some numerical claims have sources but methodology is unclear or flawed. Precision exceeds what the underlying data supports. No sensitivity analysis or uncertainty quantification. Key assumptions are unstated. Numbers are presented as facts when they are estimates.

**41-60 (Adequate):** Numerical claims are generally sourced and methodology is disclosed. Precision is mostly appropriate. Basic sensitivity to key assumptions is acknowledged but not quantified. The analysis would benefit from uncertainty ranges but is not misleading as stated.

**61-80 (Strong):** Numerical claims are well-sourced with clear methodology. Precision matches underlying data quality. Key assumptions are stated and their impact on conclusions is discussed. Some quantification of uncertainty exists (ranges, scenarios, confidence intervals). A quantitative expert would find few issues.

**81-100 (Exceptional):** Numerical analysis is rigorous with full methodology transparency. Precision is carefully calibrated to data quality. Sensitivity analysis quantifies the impact of assumption variation on key conclusions. Uncertainty is propagated through calculations. Findings are explicitly stated as robust or sensitive to assumptions. A quantitative expert would call this exemplary work.

## Sub-Criteria Checks

1. **Adversarial robustness:** Would the key findings hold if the core assumptions shifted by +-20%? If a 20% change in an input assumption reverses the conclusion, that sensitivity must be disclosed. Flag any conclusion that depends critically on a single assumption.
2. **Precision calibration:** Are numbers reported at appropriate precision for the underlying data quality? A market size derived from analyst estimates should be "$12-15B" not "$13.7B." Round numbers from imprecise sources should remain round.
3. **Methodology transparency:** Can a reader understand how numerical claims were derived? Are sources for key numbers cited? Are calculation methods disclosed? Opaque numbers erode trust.
4. **Unit consistency:** Are units consistent throughout? Are comparisons made on equivalent bases (real vs. nominal, calendar year vs. fiscal year, per capita vs. absolute)?

## Anti-Slop Sub-Check

**False precision detection:** Watch for numbers presented with inappropriate decimal places, market projections to the nearest million from rough estimates, and percentages with decimal precision from survey data with wide margins of error. The signal is precision that implies certainty the underlying data does not support. Also watch for CAGR projections presented as forecasts without stating the assumption set.

## Sprint Contract Context

Grade against these SPECIFIC criteria in addition to the general rubric:

{{sprint_contract_criteria}}

## Research Output to Evaluate

{{output_text}}

## Output Format

<evaluation_contract>
You MUST produce exactly this JSON structure with ALL fields present:

```json
{
  "score": 0,
  "feedback": "2-4 specific, actionable sentences. MUST include a direct quote from the evaluated text supporting the score.",
  "sub_criteria_notes": ["adversarial robustness: ...", "precision calibration: ...", "methodology transparency: ...", "unit consistency: ..."],
  "slop_detected": false,
  "slop_details": "Describe the specific slop pattern if detected. Otherwise null."
}
```

Scoring guidance (calibrate to the detailed rubric above):
- 90-100: Exceptional — rigorous methodology with sensitivity analysis; uncertainty propagated through calculations.
- 70-89: Strong — well-sourced with clear methodology; precision matches data quality; uncertainty ranges present.
- 50-69: Adequate — generally sourced; precision mostly appropriate but no uncertainty quantification.
- Below 50: Unsupported or demonstrably wrong numerical claims; precision wildly inappropriate.

You MUST quote a specific passage from the evaluated text that supports your score. Include this quote in your feedback.
Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</evaluation_contract>

<completeness_check>
Before outputting, verify your response includes:
[ ] score (integer 0-100, calibrated to the scoring rubric)
[ ] feedback (2-4 specific, actionable sentences with a direct quote from the text)
[ ] sub_criteria_notes (exactly 4 entries: adversarial robustness, precision calibration, methodology transparency, unit consistency)
[ ] slop_detected (boolean)
[ ] slop_details (string description or null)
</completeness_check>
