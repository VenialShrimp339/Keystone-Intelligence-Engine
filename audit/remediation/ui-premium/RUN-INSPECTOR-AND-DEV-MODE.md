# Run Inspector And Dev Mode

## Purpose

The run inspector is the truth surface beneath the chat launcher. It should let analysts trust what happened without overwhelming them, and let developers inspect raw state without pretending that raw state belongs in the default UX.

## Analyst-Mode Inspector

### Default sections

- `Overview`
- `Workstream`
- `Evidence`
- `Sources`
- `Quality`
- `Outputs`

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

### Evidence should show

- claims
- evidence summary
- caveats
- absence report
- task link
- linked citations

### Sources should show

- canonical citation view
- alias/backreference availability
- URL liveness
- fabrication flags
- corroboration count

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
- `Mixed / non-canonical`
- `Docs / demo only`

## Required Degraded-State Badges

- `Waiting for human`
- `Modified, not auto-applied`
- `Retrieval constrained`
- `Evaluation partial`
- `Fabrication halt`
- `Not rendered`
- `Deep research bypassed governance`

Use explicit badges, not generic warning dots.

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
- durable tool-level audit storage for end-user history
- accurate prompt lineage and llm-call accounting
- fully unified gate events inside the main event stream

## Anti-Patterns

- defaulting to an event firehose
- showing pseudo URLs as if they were user-meaningful sources
- collapsing canonical and raw citations into one opaque object
- hiding dropped claims, excluded tasks, or absence reports
- presenting `run_metrics.json` as if it were a product-grade source of truth
