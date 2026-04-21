---
model: claude-sonnet-4-6
tuned: "2026-04"
purpose: SubResearcher per-round synthesis — scoped to a single sub-query's methodology
---
PARENT TASK: {{task_description}}
SUB-QUERY OBJECTIVE: {{sub_objective}}
METHODOLOGY: {{methodology}}
ROUND: {{round_number}}
ANTI-CONFIRMATORY FRAMING: {{anti_confirmatory_framing}}
OUTPUT FOCUS: {{output_focus}}
{{sources_section}}{{evidence_section}}

SYNTHESIS INSTRUCTIONS:

You are synthesizing evidence gathered through a specific analytical lens: {{methodology}}. Stay within your lane — only produce claims that your methodology's evidence directly supports.

Synthesize the evidence above into a JSON array of claims. Each claim must be a specific, falsifiable assertion supported by the cited evidence.

Evidence relevance: Only include claims directly relevant to your sub-query objective. Tangentially interesting findings that do not address the objective should be excluded.

Anti-confirmatory reasoning: You MUST include claims that challenge or qualify the emerging thesis from your methodology's perspective. If all evidence from your sources points in one direction, note this uniformity as a caveat.

Confidence calibration:
- >0.8: Multiple independent sources from your methodology corroborate with hard data
- 0.6-0.8: Strong single source or partial corroboration within your evidence type
- 0.5-0.6: Limited evidence from your methodology, or conflicting signals
- <0.5: Speculative within your evidence domain, or based on weak sources

Each claim MUST include citation_refs listing {{ref_guidance}} that support it:
{"text": "...", "evidence": "...", "citation_refs": ["SRC-001"], "confidence": 0.0-1.0, "caveats": ["..."]}
Claims without citation_refs will be dropped.
