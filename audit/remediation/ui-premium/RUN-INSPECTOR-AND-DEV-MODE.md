# Run Inspector And Dev Mode

Runtime anchor: `65a612d`  
Companion contracts:

- [RUN-STATE-CONTRACT.md](./RUN-STATE-CONTRACT.md)
- [REVIEWER-FLOW-SPEC.md](./REVIEWER-FLOW-SPEC.md)

## Purpose

The run inspector is the truth surface beneath the chat launcher. It should let analysts trust what happened without overwhelming them, and let developers inspect raw state without pretending that raw state belongs in the default UX.

It must stay honest about four different realities:

- current governed runs
- current bypass runs such as `DEEP_RESEARCH=1`
- current records with unknown lineage
- docs/demo views

Reserve mixed/non-canonical labeling until one run record can explicitly prove mixed lineage.

## Analyst-Mode Inspector

### Default sections

- `Overview`
- `Workstream`
- `Evidence`
- `Sources`
- `Quality`
- `Outputs`

### What backs each section now

| Section | Backing now | Notes |
|---|---|---|
| `Overview` | `engagement_spec.json`, live/in-bundle events, `run_errors.json`, `run_metrics.json` as secondary summary only | `run_metrics.json` is not the primary source of truth |
| `Workstream` | `task_decomposition.tasks`, `findings.json`, `evaluation_results.json`, live/in-bundle events | collapse task and agent into one default row |
| `Evidence` | `findings.json`, `confidence_map.json` | honest about claim summaries, gaps, caveats, and linked citations; not passage proof |
| `Sources` | `citation_manifest.json` plus claim-local citations in `findings.json` | keep canonical and source-instance citations visibly separate |
| `Quality` | `evaluation_results.json`, L4 events | current Phase 1 three-layer evaluator only |
| `Outputs` | `deliverable.md`, bundle file list, wiki/raw artifact storage when present | do not imply rich exports beyond what exists |
| `Review checkpoint` | HITL endpoints under `/api/hitl/...` | endpoint-backed, not event-stream-backed |
| `Dev mode` | raw events, raw gate payloads, in-process gateway audit data, artifact paths | gateway audit is not yet durable end-user history |

### Overview should show

- analysis status
- question
- chosen depth
- runtime mode banner
- elapsed time
- tasks produced vs tasks evaluated
- citation totals
- confidence-tier distribution
- deliverable availability

### Workstream should show

Actual current-stage order only:

- `L0`
- `L1`
- `CitationProcessor`
- `L1.5`
- `L4`
- `Render`

Do not surface empty L2/L3 stages by default in current-state UI.

The default workstream row should carry three separate states:

- research state: `planned`, `running`, `complete`, `partial`, or `failed_no_output`
- quality state: `not_started`, `passed`, `failed`, or `not_evaluated`
- output state: `included`, `excluded_failed_quality`, `excluded_not_evaluated`, or `unknown`

### Evidence should show

- claims
- evidence summary
- caveats
- absence report
- task link
- linked citations

### Sources should show

- canonical citation view
- separate source-state chips for `Discovered only`, `Cited in claim`, `URL checked`, `Snippet only`, and `Not passage anchored`
- alias/backreference availability
- URL liveness
- fabrication flags
- corroboration count

Claim support should stay in `Evidence`, not in the source row.

### Quality should show

- pass/fail by task
- evaluator-layer summary
- explicit note that this is a Phase 1 three-layer evaluator
- what was not evaluated

### Outputs should show

- rendered brief
- output bundle files
- exclusions from failed or unevaluated tasks

## Drill-Down Hierarchy

Primary path:

`analysis -> stage -> task/workstream -> finding -> claim -> citation -> artifact`

Secondary path:

`analysis -> evidence strength -> aggregated claim -> source task_ids -> source claims -> citations`

Because the current orchestrator is near one-task/one-agent, the default UI should collapse task and agent into one user-facing workstream row.

## Required Runtime Banners

- `Governed run`
- `Experimental bypass`
- `Lineage unknown`
- `Docs / demo only`

Reserved future banner:

- `Mixed / non-canonical`

Trigger rules:

- `Governed run` means the standard gateway-mediated path, not full-document retrieval.
- `Experimental bypass` means `DEEP_RESEARCH=1` or another provider-native bypass lane.
- `Lineage unknown` means the current record cannot honestly prove governed versus bypass lineage.
- `Mixed / non-canonical` should stay reserved until one run record can explicitly prove mixed lineage.
- `Docs / demo only` applies to mocked examples, design screens, and demo bundles.

## Required Degraded-State Badges

- `Waiting for human`
- `Modified, not auto-applied`
- `Retrieval constrained`
- `Evaluation partial`
- `Fabrication halt`
- `Not rendered`
- `Deep research bypassed governance`

Use explicit badges, not generic warning dots.

Trigger rules:

- `Waiting for human`: gate status is `pending`.
- `Modified, not auto-applied`: gate status is `modified`; current helper semantics do not auto-apply reviewer edits.
- `Retrieval constrained`: current governed path is still snippet/discovery-heavy rather than governed full-document retrieval.
- `Evaluation partial`: visible run output reflects incomplete or non-universal L4 coverage.
- `Fabrication halt`: an L4 citation gate failed.
- `Not rendered`: no brief was produced.
- `Deep research bypassed governance`: only when run context explicitly proves a bypass lane; do not infer from a generic bundle.

## Dev Mode

Dev mode should expose:

- raw event stream and event JSON
- gateway audit data
- retries and dead letters
- tool latency
- model tier and fallback chain
- deep/shallow execution mode
- `CIT-* -> CAN-*` alias mappings
- dropped-claim reasons
- gate polling internals
- artifact file paths

Dev mode should not expose secrets or credentials.

Current-state limit:

- gateway audit data exists through `AuditLogger`, but it is same-process debug data, not yet a durable product history surface
- HITL gate payloads are endpoint-backed, but gate events are not fully unified into the main event stream
- there is no stable websocket bridge for replaying live event history

## What Normal Analyst Mode Should Hide

- raw IDs
- event JSON
- token counts
- prompt/response payloads
- audit-log semantics
- provenance hashes
- internal branch or environment details

## Can Be Designed Now

- full post-run inspector from current artifact bundle
- stage/task/evidence/citation/evaluation/gate pages
- run-status taxonomy
- deliverable exclusion view
- gate-review UI for current gate item types

## Must Wait For Retrieval Architecture Lock

- true query-to-fetch-to-passage provenance graph
- stable source-support taxonomy
- unified governed-versus-bypass observability
- final source drawer semantics for fetched documents and anchors
- evidence-bundle viewers that imply full-document support
- durable tool-level audit storage for end-user history
- accurate prompt lineage and llm-call accounting
- fully unified gate events inside the main event stream

## Anti-Patterns

- defaulting to an event firehose
- showing pseudo URLs as if they were user-meaningful sources
- collapsing canonical and raw citations into one opaque object
- hiding dropped claims, excluded tasks, or absence reports
- treating `DEEP_RESEARCH=1` as governed retrieval
- presenting fetched-passage proof where the current run only has snippets or claim summaries
- presenting `run_metrics.json` as if it were a product-grade source of truth
