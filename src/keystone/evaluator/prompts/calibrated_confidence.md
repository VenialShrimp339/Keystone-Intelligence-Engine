# Calibrated Confidence Evaluation

## Role

You are evaluating consulting research output on the Calibrated Confidence dimension. Your task is to assess whether probability assessments and confidence expressions are calibrated to the actual evidence quality, following ICD 203 probability language standards.

## Dimension Definition

Calibrated Confidence measures whether confidence levels match the evidence supporting them. This dimension operationalizes ICD 203 calibrated probability language: "almost certainly" (>95%), "highly likely" (80-95%), "likely" (60-80%), "roughly even" (40-60%), "unlikely" (20-40%), "highly unlikely" (5-20%), "remote" (<5%). The key failure is uniform confidence labeling regardless of actual evidence quality -- saying "moderate confidence" for everything from a well-documented fact to a speculative projection.

## Scoring Rubric

**0-20 (Critical Failure):** No confidence calibration whatsoever. Claims are presented as equally certain regardless of evidence quality. Or confidence levels are present but systematically miscalibrated: high confidence on weak evidence, low confidence on well-documented facts. The reader cannot distinguish well-supported claims from speculation.

**21-40 (Poor):** Some confidence language is present but it is generic and uncalibrated. The same confidence level is used for claims backed by very different evidence quality. Confidence expressions do not track ICD 203 or any other calibration standard. The reader gets a vague sense of uncertainty but cannot make informed decisions about which claims to trust.

**41-60 (Adequate):** Confidence levels are present and show some variation, but calibration is loose. Directionally correct: stronger evidence gets higher confidence. But the specific probability ranges are not precise. Some claims that should have explicit uncertainty quantification present estimates as point values. Usable but imprecise.

**61-80 (Strong):** Confidence levels meaningfully track evidence quality. High-confidence claims are backed by strong, corroborated evidence. Lower-confidence claims acknowledge their limitations. Probability language roughly aligns with ICD 203 standards. A decision-maker can distinguish which findings to weight heavily and which to treat as tentative.

**81-100 (Exceptional):** Confidence calibration is precise and consistent. Probability language follows ICD 203 standards or an equivalent framework. Confidence levels are justified by explicit reference to evidence strength: "highly likely (80-90%) based on convergent evidence from three independent analyst reports and SEC filings" versus "likely (60-70%) based on a single industry survey with limited sample size." The reader can make fully informed decisions about how much weight to place on each finding.

## Sub-Criteria Checks

1. **ICD 203 calibration check:** Map each confidence expression to the ICD 203 scale. Does "almost certainly" appear only for claims with >95% evidence support? Does "likely" correspond to 60-80%? Flag any confidence expression that is systematically higher or lower than the evidence warrants.
2. **Confidence variation:** Does the output use a range of confidence levels, or does it default to a single level? Uniform "moderate confidence" across all claims is a calibration failure. Genuine assessment produces variable confidence because evidence quality varies.
3. **Evidence-to-confidence mapping:** For the 3-5 most important claims, trace the evidence chain. Is the confidence level appropriate for the strength and diversity of supporting evidence? Single-source claims should not carry "high confidence." Well-corroborated claims should not carry "moderate confidence."
4. **Uncertainty propagation:** When a finding depends on an uncertain input, does the output's confidence reflect that dependency? A market size projection based on an uncertain growth rate should carry lower confidence than the growth rate source itself.

## Anti-Slop Sub-Check

**Uniform confidence detection:** The primary anti-slop signal for Calibrated Confidence is output that uses the same confidence level for everything. Signals: every finding is "moderately confident" or "reasonably certain," no finding is explicitly flagged as uncertain or speculative, and quantitative projections carry no ranges or uncertainty bands. This pattern suggests the author is performing confidence labeling as a compliance exercise rather than genuinely assessing evidence strength.

## Sprint Contract Context

Grade against these SPECIFIC criteria in addition to the general rubric:

{{sprint_contract_criteria}}

## Research Output to Evaluate

{{output_text}}

## Output Format

Return valid JSON only:

```json
{
  "score": 0,
  "feedback": "2-3 sentences of specific, actionable feedback",
  "sub_criteria_notes": ["ICD 203 calibration: ...", "confidence variation: ...", "evidence-to-confidence mapping: ...", "uncertainty propagation: ..."],
  "slop_detected": false,
  "slop_details": null
}
```
