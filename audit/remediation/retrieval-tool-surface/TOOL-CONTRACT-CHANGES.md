# Tool Contract Changes

Date: 2026-04-13

## Problem To Solve

The current tool contract collapses three different concepts into one flat set:

- task-assignable research tools
- registry-visible gateway surfaces
- system-owned retrieval actions

That flat model is why a local `document_fetch` registry addition in `f1af7df` widened authority across prompt generation, task validation, and gateway auth without ever being explicitly promoted.

## Recommended Contract

Keep one canonical source of truth for tool definitions, but make it metadata-rich instead of a flat list.

Each tool definition should make these distinctions explicit:

- tool name
- task-assignable or not
- system-owned or not
- discovery-only or canonical-fetch capable
- allowed source families
- authorization mode

## Recommended Role Table

| Surface | Task-assignable | System-owned | Role | Source families |
|---|---|---|---|---|
| `exa_search` | yes | no | discovery-only | web search |
| `brave_search` | yes | no | discovery-only | web search |
| `edgar_filings` | yes | no | filing-specific retrieval | SEC filings |
| `paper_search` | yes | no | paper discovery/retrieval | academic papers |
| `doi_verify` | yes | no | paper identity support | DOI metadata |
| `fred_data` | yes | no | structured macro data | time-series data |
| `finnhub_market` | yes | no | structured market data | market data |
| `document_fetch` | no | yes | canonical fetch | article, PDF |

## Why `document_fetch` Should Be System-Owned

`document_fetch` is not just another discovery tool.

It is the controlled seam between:

- discovery output
- governed artifact acquisition
- later deterministic parse and evidence selection

Making it task-assignable would:

- force every LLM task prompt to reason about canonical fetch mechanics
- blur discovery-only and final-evidence surfaces
- make `assigned_tools` a misleading authority boundary

Making it system-owned instead:

- preserves the intended staged retrieval architecture
- keeps the L1 task-tool list stable
- makes the authority expansion explicit and auditable

## Request Contract For `document_fetch`

The request should be typed around canonical fetch intent, not a loose ad hoc URL string.

Minimum fields:

- promoted source identity or equivalent discovery provenance
- target URL
- expected source family: `article` or `pdf`
- task or run context for audit
- optional canonicalization hints

The request should not imply:

- parser execution
- evidence ranking
- citation anchoring

## Response Contract For `document_fetch`

Minimum fields:

- canonical URL
- redirect chain
- MIME type
- content hash
- artifact identity or persistence location
- access timestamp
- coverage status
- gateway audit linkage

## Required Cross-Layer Changes

### `src/keystone/tool_names.py`

- move from flat-name authority to metadata-rich tool definitions
- add `document_fetch`
- expose a derived task-assignable subset for task generation and validation

### `src/keystone/specification/prompts/task_generation.md`

- keep the exact task-assignable list limited to the current seven tools
- explicitly say system-owned surfaces such as `document_fetch` are not assignable

### `src/keystone/specification/task_generator.py`

- filter LLM output against the task-assignable subset, not all registered surfaces
- fail closed if a system-owned surface appears in assigned tools

### `src/keystone/models/tasks.py`

- validate assigned-tool membership against the task-assignable subset
- keep `ResearchTask.assigned_tools` semantically about task authority, not general registry visibility

### `src/keystone/gateway/auth.py`

- distinguish task-authorized tool calls from system-owned internal calls
- reject any attempt to invoke `document_fetch` through ordinary task assignment

### `src/keystone/gateway/servers.py`, `tool_registry.py`, `simple_client.py`, and `mcp_gateway.py`

- register `document_fetch` as a real system surface
- preserve audit, rate-limit, retry, and governance behavior
- keep Exa and Brave discovery-only

## What This Lane Must Prove

- `document_fetch` is real
- article fetch is real
- PDF fetch is real
- `document_fetch` never appears in task prompts, `assigned_tools`, or task-tool validation as an allowed ordinary research tool

## What This Lane Must Not Smuggle

- SEC venue decisions
- parser contracts
- evidence-bundle contracts
- citation-locator schema work
- research-agent integration
- a quiet Retrieval MVP scope reduction

## Naming Decision

Do not split article and PDF into separate generic public tool names unless a later controller has a concrete reason.

One `document_fetch` surface with explicit source-family and MIME handling is the correct abstraction for this lane because the authority problem is not "too few names." The problem is "the wrong visibility and authorization semantics."
