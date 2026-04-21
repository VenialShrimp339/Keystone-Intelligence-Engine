---
model: claude-opus-4-6
tuned: "2026-04"
---
Task: {{task_description}}
Round: {{round_number}}
Anti-confirmatory framing: {{anti_confirmatory_framing}}
{{sources_section}}{{evidence_section}}{{ctx_section}}

SYNTHESIS INSTRUCTIONS:

Synthesize the evidence above into a JSON array of claims. Each claim must be a specific, falsifiable assertion supported by the cited evidence.

Evidence relevance: Only include claims that are directly relevant to the task description. Tangentially interesting findings that do not address the research question should be excluded. Ask yourself: would a decision-maker with the question above find this claim useful?

Anti-confirmatory reasoning: You MUST include claims that challenge or qualify the emerging thesis. If all evidence points in one direction, explicitly note this uniformity as a caveat — consensus among sources may reflect herding rather than independent confirmation. Actively seek and synthesize counter-evidence from the sources above.

Confidence calibration: Assign confidence aligned to these tiers:
- >0.8: Multiple independent, high-quality sources with corroborating hard data
- 0.6-0.8: Strong single source or multiple sources with partial corroboration
- 0.5-0.6: Limited evidence, single source, or conflicting signals
- <0.5: Speculative, contested, or based on weak/ambiguous evidence

Round-over-round synthesis: In rounds after the first, integrate new evidence with prior claims. Strengthen claims that gain corroboration, weaken claims contradicted by new evidence, and add new claims only when genuinely new information emerges. Do not simply append — synthesize.

Each claim MUST include citation_refs listing {{ref_guidance}} that support it:
{"text": "...", "evidence": "...", "citation_refs": ["SRC-001", "EV-002"], "confidence": 0.0-1.0, "caveats": ["..."]}
Claims without citation_refs will be dropped.