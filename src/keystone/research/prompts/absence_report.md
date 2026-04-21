---
model: claude-opus-4-6
tuned: "2026-04"
---
Task: {{task_description}}
Sources consulted: {{sources_count}}
Claims found: {{claims_count}}

List what was looked for but NOT found. Focus on evidence that would have been decision-relevant if it existed — data points, comparisons, or perspectives whose absence materially affects the quality of conclusions drawn. Do not list trivially missing items; prioritize gaps that a decision-maker would want to know about.

Return a JSON array of strings.