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

<evaluation_contract>
You MUST produce a JSON array of objects. Every factual claim in the research output MUST appear as a separate entry. Each object MUST have ALL four fields:

```json
[
  {
    "claim": "The atomic factual claim extracted from the text",
    "status": "SUPPORTED",
    "citation_id": "CIT-001",
    "reasoning": "One sentence explaining why this claim is SUPPORTED/NOT_SUPPORTED/CONTRADICTED"
  }
]
```

Rules for each field:
- "claim": A single, verifiable assertion. Compound sentences MUST be split into separate claims.
- "status": Exactly one of "SUPPORTED", "NOT_SUPPORTED", "CONTRADICTED". No other values.
- "citation_id": The specific citation ID (e.g., "CIT-001") or null if NOT_SUPPORTED.
- "reasoning": Exactly one sentence. Reference the citation text or explain its absence.

Do NOT skip claims. Do NOT merge multiple claims into one entry.
Do NOT omit any field from any object.
Output only the JSON array. After the closing bracket, output nothing further.
</evaluation_contract>

<completeness_check>
Before outputting, verify:
[ ] Every factual assertion in the research output has a corresponding entry
[ ] Each entry has all 4 fields: claim, status, citation_id, reasoning
[ ] status is exactly one of: SUPPORTED, NOT_SUPPORTED, CONTRADICTED
[ ] citation_id is null only when status is NOT_SUPPORTED
[ ] No compound claims — each entry is a single atomic fact
</completeness_check>
