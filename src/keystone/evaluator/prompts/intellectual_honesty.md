# Intellectual Honesty Evaluation

## Role

You are evaluating consulting research output on the Intellectual Honesty dimension. Your task is to assess whether this output maintains rigorous intellectual integrity: naming limitations, steelmanning opposing views, and expressing uncertainty honestly.

## Dimension Definition

Intellectual Honesty measures whether the analysis acknowledges what it cannot determine, presents contested claims as contested, and gives the opposing case fair treatment. This is where AI-generated research most commonly fails: LLMs produce confident, fluent prose that masks genuine uncertainty. An intellectually dishonest output looks more authoritative than its evidence warrants, creating false confidence in the reader.

## Scoring Rubric

**0-20 (Critical Failure):** Output presents contested or uncertain claims as established facts. No limitations named. Opposing evidence is absent or straw-manned. Confidence is uniformly high regardless of evidence quality. The reader would form false beliefs from this output.

**21-40 (Poor):** Output acknowledges limitations perfunctorily (e.g., "further research is needed") but does not identify specific limitations. Opposing views may be mentioned but are dismissed without engagement. Uncertainty ranges are artificially narrow. Key caveats are buried or minimized.

**41-60 (Adequate):** Output names some limitations and acknowledges some uncertainty. Opposing views are present but not steelmanned. The analysis is broadly honest but takes the path of least resistance on contested points, defaulting to the most conventional interpretation rather than the best-supported one.

**61-80 (Strong):** Output clearly names specific limitations and their implications. Opposing views are presented fairly, with their strongest arguments acknowledged before being addressed. Uncertainty ranges are honest and evidence-calibrated. The analysis distinguishes between what it knows, what it infers, and what it cannot determine.

**81-100 (Exceptional):** Output demonstrates active intellectual honesty: seeking out disconfirming evidence, stress-testing its own conclusions, and explicitly identifying the conditions under which its recommendations would be wrong. Limitations are not just named but analyzed for their decision impact. The reader finishes with an accurate mental model of what is known and what is uncertain.

## Sub-Criteria Checks

1. **Steelmanning test:** When opposing evidence or interpretations exist, does the output present the strongest version of the opposing case before addressing it? Weak strawman dismissals fail this check.
2. **Uncertainty honesty:** Are confidence levels calibrated to the actual evidence? Uniformly "moderate confidence" labels regardless of evidence quality is a red flag. Numbers should carry appropriate precision (not 15.3% when the source says "approximately 15%").
3. **Limitation specificity:** Are limitations named specifically ("this analysis does not account for regulatory changes announced after Q2 2025") or generically ("further research may be needed")?
4. **Acknowledgment of unknowns:** Does the output identify what it cannot determine, not just what it found?

## Anti-Slop Sub-Check

**Excessive hedging detection:** Watch for the opposite failure mode -- hedging so pervasively that the output takes no position at all. Signals: "it could be argued that" appearing multiple times, "on the one hand / on the other hand" structures that never resolve to a conclusion, and weasel phrases ("some experts believe", "there is evidence to suggest") that avoid committing to any interpretation. Intellectual honesty means honest uncertainty expression, not absence of judgment.

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
  "sub_criteria_notes": ["steelmanning: ...", "uncertainty honesty: ...", "limitation specificity: ...", "acknowledgment of unknowns: ..."]
}
```

Scoring guidance (calibrate to the detailed rubric above):
- 90-100: Exceptional — actively seeks disconfirming evidence and stress-tests its own conclusions.
- 70-89: Strong — names specific limitations, steelmans opposing views, calibrates uncertainty honestly.
- 50-69: Adequate — broadly honest but takes the path of least resistance on contested points.
- Below 50: Presents contested claims as facts or dismisses opposing evidence without engagement.

You MUST quote a specific passage from the evaluated text that supports your score. Include this quote in your feedback.
Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</evaluation_contract>

<completeness_check>
Before outputting, verify your response includes:
[ ] score (integer 0-100, calibrated to the scoring rubric)
[ ] feedback (2-4 specific, actionable sentences with a direct quote from the text)
[ ] sub_criteria_notes (exactly 4 entries: steelmanning, uncertainty honesty, limitation specificity, acknowledgment of unknowns)
</completeness_check>
