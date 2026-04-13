# Copy Guardrails

Anchored to `65a612d` in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-wave-4b`

## Label Rules

- Use analyst-facing nouns on the main surface: `Analysis`, `Research Plan`, `Review checkpoint`, `Evidence`, `Sources`, `Outputs`, `Quality`.
- Use sentence case for labels, buttons, warnings, and helper text.
- Prefer plain-English state language over backend language. Keep `task_id`, model tiers, and audit terms out of default analyst mode.
- Lead with action or state, not provider or model branding.
- Keep discovery, citation existence, source liveness, content limits, and claim support visibly separate.

## Avoid These Labels

- `Deep Research` as the default path
- `Verified` without a stated verification boundary
- `Artifacts` as the primary noun on the analyst surface
- `Live reviewer workspace`
- `Meeting recording`
- `Full document coverage`

## Warning Rules

- Every warning should say what happened, why it matters, and what the user should assume next.
- Use explicit warnings for experimental paths, constrained retrieval, partial evaluation, missing renders, and docs/demo-only states.
- Do not use green-badge trust language, percentage-confidence theater, or copy that implies certainty beyond the current runtime.

## Required Warning Copy

| Situation | Exact copy |
|---|---|
| Experimental bypass | `Experimental path. Do not treat this analysis as canonical MVP evidence.` |
| Lineage unknown | `Keystone cannot prove this analysis stayed on one runtime path from the current record alone.` |
| Retrieval constrained | `Source support may be limited because governed retrieval did not fetch full documents.` |
| Evaluation partial | `Only part of this analysis completed quality review.` |
| Modified, not auto-applied | `Review comments were saved, but changes were not applied automatically.` |
| Docs / demo only | `This view describes the intended UI. It does not prove a productized runtime surface.` |

## Required Source And Evidence Labels

| State key | Exact user-facing label | What it means now | What it must not imply |
|---|---|---|---|
| `discovered_only` | `Discovered only` | Keystone found this source during research. | Claim support |
| `cited_in_claim` | `Cited in claim` | At least one claim references this source. | Claim support |
| `url_checked` | `URL checked` | Keystone checked that the citation URL responded. | Content support or passage anchoring |
| `snippet_only` | `Snippet only` | The current record includes only a snippet or claim-level excerpt. | Full-document review |
| `not_passage_anchored` | `Not passage anchored` | The current record does not prove an exact fetched passage. | Passage-level evidence |

Required shared warning:

`These source labels show discovery, citation presence, liveness, and content limits. They do not prove claim support.`

Claim support rule:

- Show support in the `Evidence` view with claim-level context or confidence tiers.
- Do not turn any source-row chip into a support verdict.

## Button Copy Rules

- Use direct verbs: `Preview plan`, `Start analysis`, `Continue to review`, `Approve and continue`, `Request changes`, `Download bundle`.
- Avoid vague action labels like `Run`, `Go`, `Continue anyway`, or `Trust`.
- Keep destructive or final actions literal: `Stop analysis`, not `Dismiss`.
