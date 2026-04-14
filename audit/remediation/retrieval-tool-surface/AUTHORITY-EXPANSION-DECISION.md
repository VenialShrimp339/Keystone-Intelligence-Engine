# Authority Expansion Decision

Date: 2026-04-13  
Controller mode: docs-only authority resolution for post-Lane-D fetch expansion

## Controller Verdict

- Recommended path: `OTHER_CANONICAL_TOOL_CONTRACT_SHAPE`
- Article/PDF canonical fetch remains MVP-critical: `YES`
- Recommended lane: `Lane H - Retrieval Tool-Surface Authority Expansion`
- `f1af7df` disposition: `SUPERSEDED_BY_FRESH_IMPLEMENTATION_LANE`
- SEC venue issue kept separate from this decision: `YES`

## Explicit Answers

### 1. Should the next lane authorize a new ordinary callable `document_fetch` surface the same way the current seven task tools are authorized?

No.

That exact shape recreates the problem that blocked `f1af7df`: it turns a fetch-seam addition into a task-assignment, prompt-contract, and authorization expansion all at once.

### 2. What should replace that shape?

Authorize a new canonical `document_fetch` surface only as a system-owned retrieval surface inside a richer tool-definition contract.

That means:

- `document_fetch` is real, governed, audited, and registered
- `document_fetch` is not a normal `ResearchTask.assigned_tools` member
- `document_fetch` is not available for LLM task generation to invent or assign
- `document_fetch` is callable only through retrieval control-plane logic after discovery normalization
- the request shape must be typed around promoted discovery output and canonical-fetch intent, not a loose raw URL string contract

### 3. Why is this the correct contract shape?

Because the Retrieval MVP docs already define a staged path:

`task -> discovery candidates -> governed fetch -> deterministic parse -> evidence bundle -> synthesis`

An ordinary task-callable tool surface weakens that seam in three ways:

- It invites the model to treat canonical fetch as another free-form research tool instead of a controlled promotion step.
- It forces `task_generation.md`, `task_generator.py`, `ResearchTask.assigned_tools`, and gateway auth to widen together.
- It obscures the difference between discovery-only tools and canonical evidence-acquisition tools.

The better design is a single source of truth with explicit metadata:

- task-assignable versus system-owned
- discovery-only versus canonical-fetch capable
- allowed source families
- authorization mode

## Recommended Contract Shape

### Canonical tool-definition model

The single source of truth should become richer than the current flat `ALL_TOOLS` list.

Minimum distinctions:

- `task_assignable`
- `system_owned`
- `discovery_only`
- `canonical_fetch_role`
- `allowed_source_families`

### `document_fetch`

Recommended role:

- system-owned: `true`
- task-assignable: `false`
- discovery-only: `false`
- canonical fetch role: `article_pdf_fetch`
- allowed source families: `article`, `pdf`

Recommended request boundary:

- promoted discovery provenance or equivalent controller-owned source identity
- requested canonical target URL
- expected source family
- task or run context for audit

Recommended output boundary:

- canonical URL
- redirect chain
- MIME type
- content hash
- persisted raw artifact identity
- access timestamp
- coverage outcome
- gateway audit metadata

### Existing tools that stay as they are for this decision

- `exa_search` and `brave_search`: task-assignable, discovery-only
- `edgar_filings`: separate SEC-specific surface; not re-litigated here
- `paper_search` and `doi_verify`: separate paper-specific path; not the current blocker
- `fred_data` and `finnhub_market`: unaffected by this lane

## What The New Lane Must Own

- `src/keystone/tool_names.py`
- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/task_generator.py`
- `src/keystone/models/tasks.py`
- `src/keystone/gateway/auth.py`
- `src/keystone/gateway/servers.py`
- `src/keystone/gateway/simple_client.py`
- `src/keystone/gateway/tool_registry.py`
- `src/keystone/gateway/mcp_gateway.py`
- minimal additive fetch DTOs if needed
- the dedicated review packet for article/PDF tool-surface proof

## What This Decision Explicitly Does Not Decide

- whether the current execution venue can satisfy SEC/EDGAR live-proof requirements
- whether `edgar_filings` should later become system-owned too
- parser design, evidence-bundle schema, or citation-locator migration
- research-agent or orchestrator integration
- any Retrieval MVP scope reduction

## `f1af7df` Reuse Decision

Chosen status: `SUPERSEDED_BY_FRESH_IMPLEMENTATION_LANE`

Operational meaning:

- freeze the commit as blocked
- do not cherry-pick it forward as the base of the new lane
- allow reference-only reuse of ideas and probe evidence after the new contract is in force

## Separation Rule For SEC

The SEC issue is downstream of this decision.

Ordering:

1. Clear the tool-surface authority model for article/PDF canonical fetch.
2. Open the fresh implementation lane under that authority.
3. Only then run a separate venue review for official SEC filing access.

No later session may describe the SEC `403` as evidence that article/PDF tool-surface expansion was the wrong contract choice.
