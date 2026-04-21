Task: {{task_description}}
Round: {{round_number}}
Anti-confirmatory framing: {{anti_confirmatory_framing}}
{{sources_section}}{{evidence_section}}{{ctx_section}}

Synthesize findings as JSON array of claims. Each claim MUST include citation_refs listing {{ref_guidance}} that support it:
{"text": "...", "evidence": "...", "citation_refs": ["SRC-001", "EV-002"], "confidence": 0.0-1.0, "caveats": ["..."]}
Claims without citation_refs will be dropped.
