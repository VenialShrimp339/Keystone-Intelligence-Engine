# Run State Contract

Authoritative runtime anchor: `65a612d`  
Docs workspace mode: docs-only  
Related docs:

- [RUN-INSPECTOR-AND-DEV-MODE.md](./RUN-INSPECTOR-AND-DEV-MODE.md)
- [REVIEWER-FLOW-SPEC.md](./REVIEWER-FLOW-SPEC.md)
- [../retrieval-mvp/CURRENT-RETRIEVAL-VS-TARGET.md](../retrieval-mvp/CURRENT-RETRIEVAL-VS-TARGET.md)

## Scope

This contract defines the exact UI-visible state model for the run inspector and reviewer flow without pretending the repo already has:

- a productized web runtime
- governed full-document retrieval
- a stable run-history API
- live L2/L3 product surfaces
- cross-engagement memory as a current analyst surface

The contract distinguishes three backing levels:

- `Backed now`: directly supported by current artifacts, models, or HITL endpoints
- `Derived now`: honest to compute from current runtime/artifact reality, but not persisted as a first-class field
- `Provisional`: acceptable for docs and future UI planning, but not yet backed strongly enough to present as settled product truth

## Pre-Run Sequence Contract

Freeze one authoritative pre-run sequence for every UI doc in this package:

`draft -> plan_ready -> needs_review -> running`

Branch rule:

- Use `draft -> plan_ready -> running` only when no `post_specification` gate is configured.

Meaning rules:

- `plan_ready` is the analyst confirmation state produced after plan preview. It is not a HITL gate.
- `needs_review` is the first real runtime pause when a `post_specification` gate exists.
- `running` begins only after that checkpoint is approved, or immediately after `plan_ready` when no pre-run gate exists.
- Do not merge analyst confirmation and reviewer decision into one UI step.

## Current Truth Inputs

| Surface | Current truth source | Status |
|---|---|---|
| Run spec and task plan | `engagement_spec.json`, `EngagementSpec`, `ResearchSpec`, `task_decomposition.tasks` | Backed now |
| Stage and activity updates | in-process `AnyPipelineEvent`; demo bundles may persist `event_log.json` | Backed now for same-process sessions; derived for saved bundles |
| Workstream findings | `findings.json`, `StructuredFinding`, `FindingClaim` | Backed now |
| Canonical sources | `citation_manifest.json`, `CitationManifest`, `CitationAlias`, `CorroborationPair` | Backed now |
| Confidence tiers and gaps | `confidence_map.json`, `ConfidenceMap` | Backed now |
| Quality review | `evaluation_results.json`, `EvaluationResult` | Backed now |
| Brief and bundle outputs | `deliverable.md` plus the output bundle directory | Backed now |
| Review checkpoints | `/api/hitl/gates`, `/api/hitl/gates/{engagement_id}`, `/api/hitl/gates/{gate_id}/detail`, `/api/hitl/gates/{gate_id}/decision` | Backed now |
| Gateway audit detail | `AuditLogger.get_entries()` and `get_dead_letters()` in-process only | Backed now for same-process dev mode only |
| Wiki/raw artifact storage | `engagements/{engagement_id}/memory/raw`, `compiled`, `INDEX.md` when present | Backed now |
| Governed full-document fetch lineage | Not present on the current canonical path | Provisional |
| Mixed governed/bypass run lineage | No stable run field in current bundle | Provisional |

## Run-Class Banner Contract

These banners are part of the state contract because they change how every other section should be interpreted.

| Banner | Exact meaning | Current backing |
|---|---|---|
| `Governed run` | The run used the default gateway-mediated research path. This does not mean full-document retrieval is available. | Derived now. Safe only when launch context or saved run metadata identifies the standard path. |
| `Experimental bypass` | The run used `DEEP_RESEARCH=1` or another provider-native bypass path outside gateway governance. | Derived now. Safe only when run launch context explicitly proves it. Do not infer from a generic artifact bundle. |
| `Lineage unknown` | The current bundle or context cannot prove whether the run stayed on one runtime path. | Derived now. Use when the UI cannot honestly classify a record as governed or bypass from current evidence. |
| `Docs / demo only` | The screen is showing a mock, a design doc, or a demo/test bundle rather than a productized runtime record. | Backed now by context, not by runtime code. |

Reserved future banner:

- `Mixed / non-canonical`: provisional. Reserve until mixed lineage is explicitly recorded in one run record.

`Governed run` and `Experimental bypass` must stay visibly separate. `Lineage unknown` is the honest fallback when the current record cannot prove either class. `Governed run` should usually co-appear with `Retrieval constrained` on the current runtime because the governed path is still snippet/discovery-heavy rather than full-document anchored.

## Analysis Lifecycle Contract

Allowed analysis lifecycle values:

- `draft`
- `plan_ready`
- `needs_review`
- `running`
- `complete`
- `stopped`
- `failed`

| Lifecycle state | UI label | Entry rule | Exit rule | Backing level |
|---|---|---|---|---|
| `draft` | `Draft` | User has not launched a run yet | User requests a plan or starts execution | Provisional. UI shell state only. |
| `plan_ready` | `Plan ready` | A valid `EngagementSpec` and task plan exist before heavy execution continues | Run starts, review gate opens, or plan is discarded | Provisional. Current code can generate the spec, but there is no productized plan-preview endpoint or persisted plan-ready run record. |
| `needs_review` | `Needs review` | At least one HITL gate exists with `status == pending`, including `post_specification` before L1 research begins | Gate resolves to `approved`, `modified`, or `rejected` | Backed now by HITL endpoints. |
| `running` | `Running` | A run has started and is not terminal and not paused at a review gate | Review gate becomes pending, run completes, run stops, or run fails | Derived now from live events or a currently executing run context. |
| `complete` | `Complete` | Run finished and produced a resolved result record or output bundle | New run, archive, or manual deletion | Derived now from completed artifacts such as `deliverable.md`, `findings.json`, `citation_manifest.json`, `confidence_map.json`, and `evaluation_results.json`. |
| `stopped` | `Stopped` | Human intentionally stopped the run at a review checkpoint | Terminal | Derived now only for explicit review rejection or future user-stop wiring. Do not imply a generic stop endpoint exists. |
| `failed` | `Failed` | Run ended before usable results were ready | Terminal | Derived now from runtime exceptions, `run_errors.json`, or missing terminal artifacts. |

Notes:

- `needs_review` is the only lifecycle state with a directly modeled backend state machine today.
- `plan_ready` is a valid future UI label, but the current repo does not yet prove a standalone plan-preview surface.
- `needs_review` can be the first real runtime pause before any L1 activity when the specification gate opens.
- `stopped` must not be used as a synonym for any failure. In current code it is most honest when the reviewer rejected a gate.

## Stage Contract

Stage status values:

- `pending`
- `active`
- `complete`
- `blocked_review`
- `failed`
- `halted`
- `skipped`

Current analyst-visible stage keys and labels:

| Stage key | UI label | Runtime source now | Notes |
|---|---|---|---|
| `l0` | `Planning` | `L0` events: `SpecificationGenerated`, `TasksDecomposed`, `AgentDispatched` | Backed now |
| `l1` | `Researching` | `L1` events: `ResearchStarted`, `SourceFound`, `CitationExtracted`, `FindingSynthesized`, `ResearchComplete` | Backed now |
| `citation_processor` | `Source check` | `CitationProcessor` events: dedup, corroboration, URL verification, manifest production | Backed now |
| `l1_5` | `Confidence review` | `L1.5` events: analyst spawn/completion, aggregation, confidence map | Backed now |
| `l4` | `Quality review` | `L4` events plus `evaluation_results.json` | Backed now |
| `render` | `Rendering` | Final `markdown_output` / `deliverable.md` generation | Derived now. There is no authoritative render-stage event on the current path. |
| `hitl_wait` | `Waiting for review` | HITL gate `status == pending` via API | Backed now, but not unified into the main event stream. |

Rules:

- Do not show `L2` or `L3` as analyst-facing runtime stages in current-state UI. Event classes exist in `events.py`, but the authoritative runtime path does not emit them today.
- `render` can appear in a timeline, but only as a derived terminal stage. Do not present it as if a live render event feed exists.
- `hitl_wait` is a real pause state, but it is endpoint-backed rather than event-stream-backed on the current path.
- `hitl_wait` may occur immediately after `l0` and before `l1` when the `post_specification` gate opens.

## Workstream And Task Contract

The default analyst surface should collapse task and agent into one `Workstream` row because the current runtime is still effectively near one task to one agent. Advanced and dev modes may break that row open.

The workstream row should expose three separate state chips instead of one overloaded state:

- `research_state`
- `quality_state`
- `output_state`

### `research_state`

Allowed values:

- `planned`
- `running`
- `complete`
- `partial`
- `failed_no_output`

| `research_state` | Rule | Current backing |
|---|---|---|
| `planned` | Task exists in `task_decomposition.tasks`, but no L1 start/finish signal has been observed yet | Derived now |
| `running` | `ResearchStarted` seen and terminal L1 outcome not yet seen | Derived now from live events |
| `complete` | `findings.json` contains a finding for the task with `status == "complete"` | Backed now |
| `partial` | `findings.json` contains a finding with `status == "partial"` or `status == "gap_found"` | Backed now |
| `failed_no_output` | Task exists but no finding survived for it by run end | Derived now |

### `quality_state`

Allowed values:

- `not_started`
- `passed`
- `failed`
- `not_evaluated`

| `quality_state` | Rule | Current backing |
|---|---|---|
| `not_started` | L4 has not begun for the task during a live run | Derived now from live events |
| `passed` | `evaluation_results.json` has an entry for the task with `passed == true` | Backed now |
| `failed` | `evaluation_results.json` has an entry for the task with `passed == false` | Backed now |
| `not_evaluated` | No evaluation result exists for the task by run end | Backed now as a missing-record derivation |

### `output_state`

Allowed values:

- `included`
- `excluded_failed_quality`
- `excluded_not_evaluated`
- `unknown`

| `output_state` | Rule | Current backing |
|---|---|---|
| `included` | Task passed quality and therefore survived the current render gate | Derived now from orchestrator render rules and `evaluation_results.json` |
| `excluded_failed_quality` | Task has a failing evaluation result and is excluded from render | Derived now |
| `excluded_not_evaluated` | Task produced findings but never received a passing evaluation result | Derived now |
| `unknown` | Pre-terminal or insufficient run context | Derived now |

Important honesty rule:

- The repo does not currently persist `GovernanceState` in the standard run bundle. UI exclusion states are therefore honest derived states, not first-class stored run fields.

## Review Checkpoint Contract

Checkpoint types:

- `post_specification`
- `post_deliberation`

Checkpoint status values:

- `pending`
- `approved`
- `modified`
- `rejected`

Decision values:

- `approve`
- `modify`
- `reject`

| Checkpoint status | UI meaning | Backend meaning now | Backing |
|---|---|---|---|
| `pending` | Waiting for a reviewer decision | `GateStatus.PENDING` | Backed now |
| `approved` | Reviewer approved the checkpoint and the pipeline may continue | `GateStatus.APPROVED` | Backed now |
| `modified` | Reviewer requested changes | `GateStatus.MODIFIED` | Backed now |
| `rejected` | Reviewer stopped the run at this checkpoint | `GateStatus.REJECTED` | Backed now |

Current runtime consequences:

- `approved`: pipeline resumes
- `modified`: current helper wraps this as `patch_applied = false` and raises because modifications are not auto-applied in this phase
- `rejected`: pipeline halts

Current checkpoint materials:

| Gate type | Required materials now | Optional materials now |
|---|---|---|
| `post_specification` | `issue_tree`, `agent_config` | `sprint_contract` |
| `post_deliberation` | `confidence_map` | `divergence_points` |

Important honesty rules:

- `ReviewDecisionSubmitted` exists as an event class but is not emitted on the current runtime path. Do not design the live timeline as if decision events are already streaming.
- The current repo proves review gates and decisions. It does not yet prove a separate polished reviewer app or a stable multi-user review inbox.

## Evidence Contract

Evidence item types:

- `finding_claim`
- `aggregated_claim`
- `gap`
- `absence`
- `dropped_claim`

### Evidence tier states

Allowed tier values:

- `high`
- `moderate`
- `weak`
- `contested`
- `insufficient`
- `unaggregated`

| Tier state | Current source |
|---|---|
| `high` | `confidence_map.high_confidence_above_80pct` |
| `moderate` | `confidence_map.moderate_confidence_60_80pct` |
| `weak` | `confidence_map.weak_confidence_50_60pct` |
| `contested` | `confidence_map.contested_below_50pct` |
| `insufficient` | `confidence_map.insufficient_evidence` |
| `unaggregated` | `findings.json` claim exists but the UI is reading the L1 finding layer rather than the confidence map |

### Evidence visibility states

Allowed visibility values:

- `shown`
- `excluded_failed_quality`
- `excluded_not_evaluated`

Current backing:

- `shown`: claim or evidence item survives the current artifact view
- `excluded_failed_quality`: source task failed evaluation
- `excluded_not_evaluated`: source task never received a passing evaluation result

Current evidence fields the UI may rely on now:

- `FindingClaim.text`
- `FindingClaim.evidence`
- `FindingClaim.citations`
- `FindingClaim.citation_ids`
- `FindingClaim.confidence`
- `FindingClaim.confidence_tier`
- `FindingClaim.caveats`
- `StructuredFinding.absence_report`
- `StructuredFinding.dropped_claims`
- `ConfidenceMap.* tier lists`
- `ConfidenceMap.gaps_identified`
- `ConfidenceMap.provenance_index`

What must remain provisional:

- exact fetched-passage support
- source-section anchoring
- normalized evidence-bundle viewers
- final support taxonomy such as discovered vs fetched vs parsed vs anchored vs claim-supported

## Source Versus Evidence Label Contract

These labels describe different things and must not be collapsed into one trust state.

| Lane | State key | Exact user-facing label | Meaning now | Must not imply |
|---|---|---|---|---|
| Discovery | `discovered_only` | `Discovered only` | The source was found during research. | Claim support |
| Citation existence | `cited_in_claim` | `Cited in claim` | At least one claim references the source. | Claim support |
| Source liveness | `url_checked` | `URL checked` | The citation URL responded when checked. | Content support |
| Content limit | `snippet_only` | `Snippet only` | Only a snippet or claim-level excerpt is available in the current record. | Full-document review |
| Anchoring limit | `not_passage_anchored` | `Not passage anchored` | The current record does not prove an exact fetched passage. | Passage-level evidence |

Shared warning copy:

`These source labels show discovery, citation presence, liveness, and content limits. They do not prove claim support.`

Claim support rule:

- Show claim support in the evidence layer through claim context and confidence tiers.
- Do not use any source-row chip as a support verdict.

## Citation Contract

Citation record types:

- `source_instance`
- `canonical`

| Citation type | ID shape | Current source of truth | Default UI usage |
|---|---|---|---|
| `source_instance` | `CIT-*` | claim-local citations in `findings.json` | Evidence drill-down |
| `canonical` | `CAN-*` | `citation_manifest.json` citations plus aliases | Sources tab |

### Citation verification states

Allowed verification values:

- `unchecked`
- `live`
- `dead`
- `fabrication_flagged`

| Verification state | Rule | Current backing |
|---|---|---|
| `unchecked` | `url_live is null` | Backed now |
| `live` | `url_live is true` | Backed now |
| `dead` | `url_live is false` or citation ID appears in `dead_urls` | Backed now |
| `fabrication_flagged` | citation ID appears in `fabrication_flags` or L4 citation gate rejects it | Backed now, but the manifest-side field is not the only enforcement path |

### Citation linkage states

Allowed linkage values:

- `canonicalized`
- `unmerged`
- `alias_available`
- `no_alias`

| Linkage state | Rule | Current backing |
|---|---|---|
| `canonicalized` | `CIT-*` source instance maps to a `CAN-*` entry through `aliases` | Backed now |
| `unmerged` | Canonical citation has no merged aliases beyond itself | Derived now |
| `alias_available` | `aliases` or `merged_from_ids` exist | Backed now |
| `no_alias` | no alias/backreference exists | Derived now |

### Citation content states

Allowed content values:

- `snippet_available`
- `no_snippet`
- `anchored_passage`

| Content state | Rule | Current backing |
|---|---|---|
| `snippet_available` | `content_snippet` exists on the source-instance citation | Backed now |
| `no_snippet` | `content_snippet` is missing | Backed now |
| `anchored_passage` | exact fetched location exists | Provisional until retrieval seams lock |

Important honesty rules:

- Do not collapse claim-local `CIT-*` citations and canonical `CAN-*` citations into one opaque object in default analyst mode.
- Current canonical source support is not passage-level proof. It is current citation, dedup, liveness, and alias reality.
- `Discovered only`, `Cited in claim`, `URL checked`, `Snippet only`, and `Not passage anchored` are source-state labels, not support verdicts.

## Degraded-Mode Badge Contract

| Badge | Exact trigger now | Backing level |
|---|---|---|
| `Waiting for human` | Any gate for the run has `status == pending` | Backed now |
| `Modified, not auto-applied` | Gate detail shows `status == modified`; current helper semantics make `patch_applied` false in this phase | Derived now from API plus current runtime rule |
| `Retrieval constrained` | The run is on the current governed path, which is still snippet/discovery-heavy rather than governed full-document retrieval | Backed now by retrieval docs plus current runtime truth |
| `Evaluation partial` | Some task rows have `quality_state == not_evaluated`, or the visible run clearly includes only partial L4 coverage | Backed now |
| `Fabrication halt` | Any task fails the L4 citation gate (`layer2_results.gate_passed == false`) | Backed now |
| `Not rendered` | No `deliverable.md` exists or `markdown_output` is empty/missing | Backed now |
| `Deep research bypassed governance` | Run context explicitly proves `DEEP_RESEARCH=1` or equivalent bypass mode | Derived now. Do not infer from generic artifacts. |

## Analyst, Advanced, And Dev Mode Contract

| Mode | Default audience | Allowed data now | Must stay hidden by default |
|---|---|---|---|
| `Analyst mode` | Nontechnical analyst | overview, workstream rows, evidence summaries, canonical sources, quality summary, outputs, review state | raw IDs, raw JSON, provenance hashes, token counts, audit semantics, prompt payloads |
| `Advanced mode` | Power analyst | plan detail, task criteria, exclusion reasons, caveats, dropped claims, alias/corroboration summaries, full checkpoint material summaries | raw event JSON, audit entry hashes, full prompt/response payloads, secrets |
| `Dev mode` | Internal debugging | raw event stream / `event_log.json`, raw HITL gate payloads, artifact file paths, alias maps, provenance indices, gateway audit entries, dead letters, model tiers, latency | secrets, credentials, any hidden auth material |

Important current-state limits:

- Dev-mode gateway audit data is same-process only unless a future session explicitly persists it.
- Dev mode may show internal file paths and IDs, but analyst mode should not.
- Advanced mode can expose exclusion logic and checkpoint detail without becoming an event firehose.

## Inspector Section Backing Matrix

| Inspector section | Backing now | Keep provisional until retrieval seams lock |
|---|---|---|
| `Overview` | `engagement_spec.json`, live/in-bundle events, `run_errors.json`, `run_metrics.json` as secondary summary only | final run-history API semantics |
| `Workstream` | `task_decomposition.tasks`, `findings.json`, `evaluation_results.json`, live/in-bundle events | durable publishability/governance fields as first-class run data |
| `Evidence` | `findings.json`, `confidence_map.json` | passage viewer, anchored support graph, fetched evidence bundle viewer |
| `Sources` | `citation_manifest.json`, claim-local citations in `findings.json` | fetched full-document viewer, source-scope picker, final support taxonomy |
| `Quality` | `evaluation_results.json`, L4 events | calibrated long-horizon trust semantics beyond current Phase 1 evaluator reality |
| `Outputs` | `deliverable.md`, bundle file list, wiki/raw artifact storage when present | rich export taxonomy and document-package claims |
| `Review checkpoint` | HITL endpoints and gate-item schemas | polished reviewer inbox, unified event-stream replay |
| `Timeline` | same-process events, demo `event_log.json` | websocket bridge, stable live history, full gate events in the same stream |
| `Governance/bypass lineage` | contextual labels only, including `Lineage unknown` when the record cannot prove path class | stable run-level `gateway_bypassed`, mixed lineage, governed-vs-bypass history semantics |

## Non-Negotiable Honesty Rules

- Do not present `run_metrics.json` as a product-grade source of truth.
- Do not present current source rows as if they prove fetched-passage support.
- Do not infer `Mixed / non-canonical` from partial artifacts. Use `Lineage unknown` unless mixed lineage is explicitly recorded.
- Do not surface L2, L3, or cross-engagement memory as active product reality.
- Do not label `DEEP_RESEARCH=1` as equivalent to governed retrieval.
- Do not claim a unified review-plus-event timeline until the actual stream contains both.
