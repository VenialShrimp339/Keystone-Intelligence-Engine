---
model: claude-opus-4-6
tuned: "2026-04"
---
Multiple analysts evaluated this claim with different conclusions.

Claim: {{claim_text}}
Evidence: {{claim_evidence}}

Analyst assessments:
{{assessments}}

Select the analyst whose assessment is best supported by the evidence. Do NOT blend or average. Pick one. After selecting, state in one sentence the strongest reason this selected assessment could be wrong.

Respond with JSON: {"selected_analyst": "<analyst_type>", "reasoning": "...", "curmudgeon": "strongest reason this could be wrong"}
