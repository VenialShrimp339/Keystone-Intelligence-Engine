# Risk Register

| ID | Risk | Severity | Likelihood | Why it matters | Mitigation | Acceptance gate |
|---|---|---|---|---|---|---|
| R1 | Premium shell over unstable runtime truth | P0 | High | Makes the docs checkout look like the canonical product runtime | Keep runtime-anchor banners and authority-chain notes explicit | Controller review |
| R2 | Governed and bypass research collapse into one user concept | P0 | High | Hides the most important retrieval truth boundary | Label governed, experimental bypass, mixed, and docs/demo-only runs separately | Retrieval compliance review |
| R3 | Citation theater | P0 | High | Implies claim support when only citation existence/liveness is proven | Distinguish discovered, cited, live, anchored, and claim-supported states | Evidence-label review |
| R4 | Coverage theater | P1 | High | Tool registry breadth can look like real backend coverage | Avoid provider-badge and source-count vanity metrics | Backend reality review |
| R5 | Progress theater | P1 | High | Fake ETAs and fake completion bars create false trust | Use only real stage and wait states | Observability review |
| R6 | UI implementation starts before retrieval seams lock | P0 | Medium | Creates rework and misleading product assumptions | Keep implementation blocked until explicit unlock | Controller review |
| R7 | HITL reviewer flow overclaimed | P1 | Medium | Backend gates are real, polished reviewer UX is not | Scope only current gate item types and acknowledge modify/apply limits | HITL reality review |
| R8 | Evaluation confidence overclaimed | P1 | Medium | The evaluator is real but Phase 1 only | Label it as 3-layer Phase 1 and not human-calibrated | Quality-surface review |
| R9 | Run history implies repeatability the repo cannot yet prove | P2 | Medium | A beautiful history page can look like a stable product record | Keep history tied to artifact bundles and visible warnings | Run-history review |
| R10 | Advanced mode leaks developer jargon into analyst mode | P2 | Medium | Reduces usability for nontechnical analysts | Keep analyst language on top and raw internals below | UX language review |
| R11 | File upload and speech-to-text promise richer ingestion than exists | P2 | Medium | Users may assume indexing, meeting capture, or structured extraction | Limit MVP copy to attachments and dictation unless more is built | Input-surface review |
| R12 | Future docs drift from the accepted UI boundary | P2 | Medium | Later docs may silently re-inflate UI maturity | Queue authoritative doc updates only after controller approval | Documentation review |

## Non-Negotiable Gate

If any future session cannot clearly answer:

- what was governed
- what was experimental
- what evidence was actually available
- what was evaluated
- what was excluded

then the UI package is not ready for implementation unlock.
