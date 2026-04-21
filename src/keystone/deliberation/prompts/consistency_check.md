---
model: claude-opus-4-6
tuned: "2026-04"
---
Review these selected claims for logical contradictions:

{{summaries}}

Identify any pairs that directly contradict each other. A contradiction is when both claims cannot be simultaneously true. Analytical tension — where claims point in different directions but are compatible (e.g., "market is growing" and "margins are declining") — is NOT a contradiction. Only flag genuine logical incompatibilities.

Respond with JSON: {"contradictions": [{"claim_a": <index>, "claim_b": <index>, "issue": "..."}]}
