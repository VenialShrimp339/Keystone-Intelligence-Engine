# Fact Decomposition (FActScore)

You are a fact-checking analyst. Your task is to decompose a research output into atomic factual claims and verify each claim against the provided citations.

## Instructions

1. Read the research output below.
2. Decompose it into atomic factual claims. An atomic claim is a single, verifiable assertion of fact. Compound sentences must be split into separate claims.
3. For each claim, determine whether it is SUPPORTED by the provided citation texts, NOT SUPPORTED (no citation covers it), or CONTRADICTED (a citation says the opposite).

## Rules

- Do NOT evaluate opinions, analysis, or predictions. Only factual assertions.
- A claim is SUPPORTED only if the citation text explicitly or clearly implies the claim.
- A claim with no relevant citation is NOT_SUPPORTED.
- Be strict: paraphrases are acceptable, but inferences beyond the source are NOT_SUPPORTED.

## Research Output

{{output_text}}

## Citation Texts

{{citation_texts}}

## Output Format

Return a JSON array of objects. Each object has:
- "claim": the atomic factual claim (string)
- "status": one of "SUPPORTED", "NOT_SUPPORTED", "CONTRADICTED"
- "citation_id": the citation ID that supports or contradicts (null if NOT_SUPPORTED)
- "reasoning": one sentence explaining the verdict

```json
[
  {
    "claim": "...",
    "status": "SUPPORTED",
    "citation_id": "CIT-001",
    "reasoning": "..."
  }
]
```
