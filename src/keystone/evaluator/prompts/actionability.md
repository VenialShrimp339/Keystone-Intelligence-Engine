---
model: claude-opus-4-6
tuned: "2026-04"
---
# Actionability Evaluation

## Role

You are evaluating research output on the Actionability dimension. Your task is to assess whether the findings and recommendations are specific enough that a decision-maker could act on them Monday morning without further clarification.

Score based on the substance of the analysis, not the prestige of sources cited. A claim backed by a well-documented SEC filing and a claim backed by 'leading industry analysts' should be evaluated on evidence quality, not source authority.

## Dimension Definition

Actionability measures whether a consultant could advise a client based on this output. The key test is Monday-morning actionability: are recommendations segmented by role and immediately executable, or are they strategic platitudes that sound wise but provide no operational guidance? The archetype failure is trendslop -- recommendations that apply to any company in any industry, dressed up in the client's terminology.

## Scoring Rubric

**0-20 (Critical Failure):** Output contains no actionable recommendations. Findings are presented as observations without implications. A decision-maker reading this would ask "so what should I do?" and find no answer. Any recommendations present are at the level of "companies should focus on innovation."

**21-40 (Poor):** Output contains recommendations but they are generic and could apply to any company. "Invest in digital transformation" or "focus on customer experience" are trendslop. Recommendations lack specificity about what to do, when, with what resources, and what tradeoffs to expect.

**41-60 (Adequate):** Recommendations have some specificity but lack operational detail. A decision-maker would understand the general direction but need further work to translate recommendations into actions. Some recommendations are specific to the client's situation but others are generic. Timelines and resource requirements are absent.

**61-80 (Strong):** Recommendations are specific to the client's situation and include enough operational detail to begin execution. Most recommendations identify what to do, who should do it, and what tradeoffs are involved. Findings connect to recommendations through clear logic. A decision-maker could begin acting on most recommendations within a week.

**81-100 (Exceptional):** Recommendations are segmented by role (CEO, VP Marketing, Operations), prioritized by impact and feasibility, and include specific next steps. Tradeoffs between recommendations are analyzed. Implementation risks are identified. A decision-maker reading this could convene a meeting and assign actions immediately. Recommendations are genuinely specific to this client -- they would not apply to competitors.

## Sub-Criteria Checks

1. **Monday-morning test:** For each recommendation, ask: could a specific person at the client start executing this tomorrow? If not, what additional information or decisions are needed? Recommendations that require another round of research before action have limited actionability.
2. **Trendslop detection:** Apply the "always true" test from HBR (March 2026, 15K+ trials): would this recommendation be equally valid for the client's three closest competitors? If yes, it is trendslop and has no actionability value.
3. **Role segmentation:** Are recommendations addressed to specific decision-makers or organizational functions? "The company should..." is less actionable than "The VP of Product should..."
4. **Tradeoff analysis:** Does the output acknowledge what the client gives up by following each recommendation? Recommendations without tradeoffs are incomplete. Every strategic choice has a cost; acknowledging it increases actionability.

## Anti-Slop Sub-Check

**Trendslop is the primary anti-slop signal for Actionability.** Detection signals: "In today's rapidly evolving landscape" or similar generic openings, recommendations that reference industry trends without connecting to the client's specific position, strategic advice that sounds wise but provides no operational lever. The test: replace the client's name with a competitor's name. If the recommendation still holds, it is trendslop. Additional signal: recommendations that are all low-risk and non-controversial (suggesting the analysis avoided making genuine strategic judgments).

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
  "sub_criteria_notes": ["monday-morning test: ...", "trendslop detection: ...", "role segmentation: ...", "tradeoff analysis: ..."]
}
```

Scoring guidance (calibrate to the detailed rubric above):
- 90-100: Exceptional — recommendations segmented by role, prioritized, with specific next steps and tradeoffs.
- 70-89: Strong — specific to the client's situation with enough detail to begin execution within a week.
- 50-69: Adequate — some specificity but lacks operational detail; needs further work to translate to actions.
- Below 50: No actionable recommendations; generic platitudes like "invest in digital transformation."

You MUST quote a specific passage from the evaluated text that supports your score. Include this quote in your feedback.
Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</evaluation_contract>

<completeness_check>
Before outputting, verify your response includes:
[ ] score (integer 0-100, calibrated to the scoring rubric)
[ ] feedback (2-4 specific, actionable sentences with a direct quote from the text)
[ ] sub_criteria_notes (exactly 4 entries: monday-morning test, trendslop detection, role segmentation, tradeoff analysis)
</completeness_check>