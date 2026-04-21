---
model: claude-opus-4-6
tuned: "2026-04"
---
For the following uncertain claim, identify the key assumptions that would have to be true for it to hold. List 2-5 specific, testable assumptions.

A testable assumption is one where you can describe what evidence would confirm or refute it. "The market will grow" is not testable; "the market will exceed $X by date Y as measured by source Z" is testable. Prefer assumptions that are both high-impact (if wrong, the claim collapses) and verifiable (a decision-maker could check them).

Rank assumptions by impact: list the assumption whose failure would most undermine the claim first.

Claim: {{claim_text}}
Current confidence: {{mean_confidence}}
Dissenting views: {{dissenting_views}}

Respond with JSON: {"assumptions": ["highest-impact assumption first", "second assumption", ...]}
