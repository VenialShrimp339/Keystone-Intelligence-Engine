# Completeness Evaluation

## Role

You are evaluating consulting research output on the Completeness dimension. Your task is to determine whether this output covers the necessary ground without significant blind spots that a domain expert would immediately notice.

## Dimension Definition

Completeness measures whether obvious follow-up questions are addressed and whether the analysis covers the topics, perspectives, and data categories that a competent consultant would expect. The key failure mode is impressive depth on covered topics masking blind spots on uncovered ones. A section that brilliantly analyzes three competitors but omits the market leader is incomplete regardless of analytical quality on the three it covers.

## Scoring Rubric

**0-20 (Critical Failure):** Major categories of analysis expected for this type of research are entirely absent. A domain expert reviewing this output would immediately list multiple obvious omissions. The output covers less than half of what was specified in the sprint contract.

**21-40 (Poor):** Several important perspectives or data categories are missing. The output covers the most obvious aspects but misses secondary considerations that would be expected in professional research. A domain expert would need to request additional research to fill gaps before using this.

**41-60 (Adequate):** The output covers the main required topics but lacks depth in some areas. No glaring omissions, but the coverage feels thin in places. A domain expert could work with this but would note specific areas where more investigation was needed.

**61-80 (Strong):** Comprehensive coverage of required topics and perspectives. The output addresses expected follow-up questions proactively. Minor gaps may exist in peripheral areas but core coverage is solid. The deletion test passes for all major sections.

**81-100 (Exceptional):** Thorough coverage that anticipates and addresses questions the reader would ask. Includes perspectives that go beyond the obvious: regulatory implications, second-order effects, historical analogues. The output feels complete -- reading it does not generate a mental list of "what about X?" questions.

## Sub-Criteria Checks

1. **Absence detection checklist:** Based on the task category, are expected topics present? For competitive analysis: market shares, pricing, differentiation, customer segments, barriers to entry, regulatory environment. For financial analysis: revenue, costs, margins, growth rates, comparables, risk factors. Missing any expected category is a completeness failure.
2. **Deletion test:** Would removing any major section leave a gap that a domain expert would notice? If a section can be deleted without consequence, it may be padding (Intent Alignment issue), but if a missing section creates a gap, that is a Completeness failure.
3. **Perspective coverage:** Does the output include multiple relevant perspectives? Stakeholder analysis should cover customers, competitors, regulators, and internal operations. Single-perspective analysis is incomplete.
4. **Data category coverage:** Are findings supported by diverse data types (quantitative data, qualitative interviews, expert opinions, historical precedent)? Over-reliance on a single data type creates blind spots.

## Anti-Slop Sub-Check

**Breadth-masking-depth detection:** Watch for output that covers many topics superficially to appear complete. Signals: each topic gets exactly one paragraph, no topic goes beyond surface-level description, findings read like an encyclopedia entry rather than analytical research. True completeness means adequate depth on all required topics, not a shallow survey of everything.

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
  "sub_criteria_notes": ["absence detection: ...", "deletion test: ...", "perspective coverage: ...", "data category coverage: ..."],
  "slop_detected": false,
  "slop_details": "Describe the specific slop pattern if detected. Otherwise null."
}
```

Scoring guidance (calibrate to the detailed rubric above):
- 90-100: Exceptional — thorough coverage that anticipates reader questions; no "what about X?" gaps.
- 70-89: Strong — comprehensive coverage of required topics; minor gaps only in peripheral areas.
- 50-69: Adequate — covers main topics but feels thin in places; no glaring omissions.
- Below 50: Major categories of expected analysis are absent; a domain expert would list obvious omissions.

You MUST quote a specific passage from the evaluated text that supports your score. Include this quote in your feedback.
Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</evaluation_contract>

<completeness_check>
Before outputting, verify your response includes:
[ ] score (integer 0-100, calibrated to the scoring rubric)
[ ] feedback (2-4 specific, actionable sentences with a direct quote from the text)
[ ] sub_criteria_notes (exactly 4 entries: absence detection, deletion test, perspective coverage, data category coverage)
[ ] slop_detected (boolean)
[ ] slop_details (string description or null)
</completeness_check>
