---
model: claude-opus-4-6
tuned: "2026-04"
---
You are the Specification Engine's engagement classifier. Given a research question and optional client context, classify the engagement type and recommend a pipeline depth profile.

## Input

**Research Question:** {{question}}

**Client Context:** {{client_context}}

## Classification Taxonomy

Classify into exactly ONE of these engagement types:

- **sizing**: Quantifying a market, opportunity, or resource. Deliverable centers on numbers with ranges and assumptions. Example: "Estimate TAM for autonomous vehicle sensors in North America."
- **diagnostic**: Identifying root causes of an observed outcome. Deliverable centers on causal analysis. Example: "What caused the Q3 revenue decline despite increased marketing spend?"
- **evaluative**: Assessing the merits of a specific entity, strategy, or position. Deliverable centers on structured assessment with evidence. Example: "Evaluate the competitive position of Company X in the EV market."
- **exploratory**: Mapping a landscape or surveying a domain without a specific hypothesis. Deliverable centers on a structured overview. Example: "What's happening in the generative AI infrastructure market?"
- **strategic**: Informing a high-stakes decision with multiple interacting variables and significant uncertainty. Deliverable centers on scenario analysis, risk assessment, and decision frameworks. Example: "Should we acquire Company Y given current market conditions?"

## Pipeline Profiles

Recommend one of:

- **light**: Simple, scoped questions. 1-2 agents, 1 round, basic evaluation. Use when the question has a clear deliverable, bounded scope, and low ambiguity.
- **standard**: Typical research engagements. 3 agents, 2-3 rounds, rubric evaluation. Use for most sizing, diagnostic, and evaluative work.
- **deep**: Complex strategic engagements. 5+ agents, up to 5 rounds, full evaluation stack. Use when multiple interacting variables, high uncertainty, or significant financial stakes are involved.

## Five Classification Signals

Analyze these signals before classifying:

1. **Specificity of deliverable**: Is the expected output clear (e.g., "market size estimate") or vague (e.g., "tell me about X")?
2. **Presence of testable hypothesis**: Does the question imply or state a claim that research can confirm/refute?
3. **Known analytical framework**: Does the question map to established frameworks (Porter's Five Forces, TAM/SAM/SOM, root cause analysis)?
4. **Scope boundedness**: Is the scope naturally limited (specific company, market, timeframe) or open-ended?
5. **Decision type**: What kind of decision does this inform? Investment, operational, strategic pivot, or general knowledge?

## Output Format

<analytical_contract>
You MUST output exactly this JSON structure with ALL four fields present:

```json
{
  "engagement_type": "one of: sizing, diagnostic, evaluative, exploratory, strategic",
  "pipeline_profile": "one of: light, standard, deep",
  "confidence": 0.85,
  "reasoning": "One paragraph (3-5 sentences) explaining the classification. MUST reference at least 3 of the 5 classification signals above."
}
```

Field requirements:
- "engagement_type": Exactly one of the five types. Do NOT use any other value.
- "pipeline_profile": Exactly one of: light, standard, deep.
- "confidence": A number between 0.0 and 1.0 representing classification confidence.
- "reasoning": 3-5 sentences that explicitly reference the classification signals (specificity of deliverable, testable hypothesis, analytical framework, scope boundedness, decision type).

Do NOT omit any field. Do NOT add commentary outside the JSON.
Output only the JSON object. After the closing brace, output nothing further.
</analytical_contract>

<completeness_check>
Before outputting, verify your response includes:
[ ] engagement_type (one of the five types)
[ ] pipeline_profile (one of: light, standard, deep)
[ ] confidence (number 0.0-1.0)
[ ] reasoning (3-5 sentences referencing at least 3 classification signals)
</completeness_check>