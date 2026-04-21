# Keystone UI Architecture

Date: 2026-04-21

This document defines the first browser-first UI architecture for the Keystone
Intelligence Engine. It is a planning document only. It does not require
changes to existing pipeline modules.

## Contract Notes

The serving layer lives in `src/keystone/server/` and imports the existing
pipeline package. It must not modify `src/keystone/pipeline/`,
`src/keystone/events.py`, or model code to make the UI work.

The frontend lives in `frontend/` as a standalone React app. It communicates
with the serving layer only through HTTP and WebSocket.

All durable state lives server-side: run summaries, event history, current run
phase, result payloads, uploaded source metadata, and config. The frontend keeps
only transient view state.

The live UI is WebSocket-first. `GET /api/runs/{id}/events` exists for reloads
and completed-run history, not for polling while a run is active.

The concrete source contract currently defines 40 event classes in
`src/keystone/events.py`, not 37. The three additional L3 events are
`DraftGenerated`, `CitationFormatted`, and `DeliverableAssembled`. The Atlas
notes say render emits no events today, so the UI should accept these events for
forward compatibility but not depend on them for current progress.

The product tone should be consultant-facing: default labels should say
"Planning", "Research", "Evidence check", "Analyst review", "Structuring",
"Quality review", and "Final brief". Raw event names belong in an expandable
diagnostic detail view.

## 1. Screen Inventory

### App Shell

Purpose: Own the persistent layout, selected run, WebSocket connection, and
global status affordances.

Wireframe:

```text
+-------------------------------------------------------------------+
| Keystone                                   Settings  Source Library |
+----------------------+--------------------------------------------+
| Session Sidebar      | Main Work Area                              |
|                      |                                            |
| Recent runs          | Chat / Results / Sources / Settings         |
| Search/filter        |                                            |
| Status chips         | Expandable observability panel on the right |
+----------------------+--------------------------------------------+
```

Consumes:

| Endpoint | Use |
|---|---|
| `GET /api/runs` | Initial sidebar hydration |
| `GET /api/config` | Show configured/unconfigured status |
| `GET /api/sources` | Show source library status badge |

Subscribes to WebSocket messages:

| Message | Effect |
|---|---|
| `run_state` | Update global phase/status |
| `pipeline_event` | Route event to active run store |
| `result_ready` | Switch active run to result-capable state |
| `error` | Show run-level failure banner |
| `heartbeat` | Keep connection status fresh |

### Session Sidebar

Purpose: Always-visible left panel for starting, selecting, and scanning local
research sessions.

Wireframe:

```text
[New Research]

Search runs...

Today
  Market entry question          Quality review   18m
  Sensor TAM estimate            Complete         21m

Previous
  Margin bridge research         Complete
  Supplier risk scan             Stopped
```

Consumes:

| Endpoint | Use |
|---|---|
| `GET /api/runs` | List all runs with phase, status, timestamps, token summary |
| `GET /api/runs/{id}` | Load selected run result if complete |
| `GET /api/runs/{id}/events` | Rehydrate selected run observability history |

Subscribes to WebSocket messages:

| Message/Event | Effect |
|---|---|
| `run_state` | Update selected run chip and elapsed time |
| `pipeline_event` | Increment event count and current phase metadata |
| `result_ready` | Mark run as complete |
| `error` | Mark run as failed/stopped |

### Chat / Submission Panel

Purpose: Main entry point for non-technical users to submit a research question
and watch the run begin.

Wireframe:

```text
Ask Keystone

+--------------------------------------------------------------+
| What strategic question should Keystone research?            |
|                                                              |
+--------------------------------------------------------------+

Client context (optional)
+--------------------------------------------------------------+
| Decision, geography, time horizon, constraints...            |
+--------------------------------------------------------------+

[Deep research] [Run]

Current run:
  Planning the engagement...
```

Consumes:

| Endpoint | Use |
|---|---|
| `POST /api/runs` | Start a run |
| `POST /api/runs/{id}/stop` | Request graceful stop |
| `GET /api/config` | Resolve default profile/model labels |

Subscribes to WebSocket messages:

| Message/Event | Effect |
|---|---|
| `run_state` | Replace input state with current phase copy |
| `SpecificationGenerated` | Show "Engagement plan drafted" |
| `TasksDecomposed` | Show task count and estimated breadth |
| `AgentDispatched`, `ResearchStarted` | Show research has begun |
| `ReviewGateCreated` | Open HITL modal and show paused state |
| `result_ready` | Switch primary panel to Results viewer |

### Pipeline Observability Panel

Purpose: Expandable right panel that gives confidence in the 20-minute run
without exposing raw internals by default.

Wireframe:

```text
Run Progress

Planning          complete     23 tasks
Research          active       12/23 agents complete
Evidence check    waiting
Analyst review    waiting
Structuring       waiting
Quality review    waiting

Agent Roster
  Competitive scan        reading sources       9 sources
  Pricing analysis        synthesized finding   6 sources

Evidence Health
  Citations 38  Live URLs 37  Corroboration 12 pairs

[Show technical event log]
```

Consumes:

| Endpoint | Use |
|---|---|
| `GET /api/runs/{id}/events` | Rebuild progress after reload |
| `GET /api/runs/{id}` | Load final metrics when complete |

Subscribes to WebSocket messages:

| Event group | Effect |
|---|---|
| L0 events | Planning step, issue tree/task count, agent roster seed |
| L1 events | Agent progress, source counts, findings count |
| Retrieval events | Source-library ingest/search detail |
| CitationProcessor events | Citation health and corroboration |
| L1.5 events | Analyst methodology progress and confidence map |
| L2 events | Outline/section/sprint-contract progress |
| L4/L5 events | Quality review scores and veto warnings |
| HITL events | Pause/resume/reject state |
| META events | Detail log only |

### Results Viewer

Purpose: Present the consulting brief, quality scores, and citations after the
pipeline completes.

Wireframe:

```text
+-----------------------------+-------------------------------+
| Final Brief                 | Quality                        |
| Rendered markdown           | Overall scores by task         |
|                             | Rubric bars                    |
| Executive summary           | Citation gate                  |
| Analysis sections           | Process quality                |
| Sources                     |                               |
+-----------------------------+-------------------------------+
| Citation drawer: canonical source, URL status, corroboration |
+-------------------------------------------------------------+
```

Consumes:

| Endpoint | Use |
|---|---|
| `GET /api/runs/{id}` | Load `PipelineResult` after completion |
| `GET /api/runs/{id}/events` | Populate score timeline and event audit |

Subscribes to WebSocket messages:

| Message/Event | Effect |
|---|---|
| `EvaluationComplete` | Add task-level score as it arrives |
| `CitationGateResult` | Update citation gate status |
| `DissenterVetoTriggered` | Show prominent quality warning |
| `EnsembleEvaluationComplete` | Update ensemble quality panel |
| `result_ready` | Fetch/render final markdown and source list |

### Source Management

Purpose: Upload local evidence files and inspect the ingested corpus used as
institutional memory.

Wireframe:

```text
Source Library

[Upload files]

Ingested sources
  Title / filename     Type     Chunks     Parse quality     Added
  market-report.pdf    pdf      42         high              Apr 21
  filing.html          article  18         medium            Apr 21

Selected source
  Metadata
  Parse warnings
  Chunk preview
```

Consumes:

| Endpoint | Use |
|---|---|
| `POST /api/sources` | Upload and ingest files |
| `GET /api/sources` | List ingested artifacts/chunks |

Subscribes to WebSocket messages:

| Event | Effect |
|---|---|
| `ChunkIngested` | Update ingest summary when sources are wired into a run |
| `SearchCompleted` | Optional detail: show corpus search usage during research |

### Settings / Config Panel

Purpose: Configure local provider keys, model tiers, reasoning effort, and
quality thresholds without asking consultants to edit environment variables.

Wireframe:

```text
Settings

Provider
  OpenAI key       configured
  Exa key          missing
  Brave key        configured

Run defaults
  Research profile        Standard / Deep
  Max parallel agents     5
  Quality bar             60

Advanced
  Planning model tier
  Research model tier
  Analyst model tier
  Evaluator model tier
  Reasoning effort overrides
```

Consumes:

| Endpoint | Use |
|---|---|
| `GET /api/config` | Read sanitized app and pipeline config |
| `PUT /api/config` | Update local config |

Subscribes to WebSocket messages: none required. If the selected run is active,
the UI should mark config controls as affecting future runs only.

### HITL Gate Modal

Purpose: Interrupt the run when a human review gate fires, present artifacts,
and submit approve/modify/reject.

Wireframe:

```text
Review Required

Planning review / Analyst review

[Artifact tabs: Issue tree | Agents | Confidence map | Divergences]

Decision
  [Approve] [Request changes] [Reject]

Reasoning / modifications
+--------------------------------------------------------------+
| Optional notes or structured modification JSON               |
+--------------------------------------------------------------+

[Submit decision]
```

Consumes:

| Endpoint | Use |
|---|---|
| `POST /api/runs/{id}/hitl/{gate_id}` | Submit gate decision |

Subscribes to WebSocket messages:

| Event | Effect |
|---|---|
| `ReviewGateCreated` | Open modal and set run phase to paused |
| `ReviewDecisionSubmitted` | Show submitted state |
| `ReviewGateApproved` | Close modal and resume |
| `ReviewGateModified` | Close modal only after backend confirms semantics |
| `ReviewGateRejected` | Close modal and mark run failed/rejected |

Note: current Atlas guidance says `MODIFIED` is a backend stub that halts rather
than applying changes. v0.4 should either disable "Request changes" until
GAP-17 lands or submit it with explicit copy that the run will halt for manual
follow-up.

## 2. API Contract

### API Design Rules

The server owns a `RunStore` that persists:

- run summary and lifecycle state
- append-only pipeline event history
- latest derived UI state
- final `PipelineResult`
- source metadata and ingest summaries
- sanitized config snapshots

Every serialized pipeline event is wrapped with an `event_type` discriminator
because the Pydantic event classes do not include a native type field.

### Shared TypeScript Types

```ts
export type ISODateTime = string;
export type JsonObject = Record<string, unknown>;

export type RunPhase =
  | "QUEUED"
  | "SPEC"
  | "RESEARCH"
  | "CITATION"
  | "DELIBERATION"
  | "STRUCTURING"
  | "EVALUATION"
  | "RENDERING"
  | "COMPLETE"
  | "PAUSED"
  | "FAILED";

export type RunStatus =
  | "queued"
  | "running"
  | "paused"
  | "stopping"
  | "complete"
  | "failed";

export type PipelineLayer =
  | "L0"
  | "L1"
  | "CitationProcessor"
  | "Retrieval"
  | "L1.5"
  | "L2"
  | "L3"
  | "L4"
  | "L5"
  | "HITL"
  | "META";

export type PipelineEventType =
  | "SpecificationGenerated"
  | "TasksDecomposed"
  | "AgentDispatched"
  | "ResearchStarted"
  | "SourceFound"
  | "CitationExtracted"
  | "FindingSynthesized"
  | "ResearchComplete"
  | "CitationDeduped"
  | "CorroborationScored"
  | "URLVerified"
  | "ManifestProduced"
  | "ChunkIngested"
  | "SearchCompleted"
  | "AnalystSpawned"
  | "IndependentAnalysisComplete"
  | "AggregationComplete"
  | "ConfidenceMapProduced"
  | "OutlineGenerated"
  | "SectionDrafted"
  | "SprintContractProposed"
  | "DraftGenerated"
  | "CitationFormatted"
  | "DeliverableAssembled"
  | "DeterministicCheckPassed"
  | "CitationGateResult"
  | "RubricDimensionScored"
  | "ProcessTrajectoryScored"
  | "EvaluationComplete"
  | "EnsembleJudgeScored"
  | "DissenterVetoTriggered"
  | "EnsembleEvaluationComplete"
  | "ObservationRecorded"
  | "PatternPromoted"
  | "ConstraintEncoded"
  | "ReviewGateCreated"
  | "ReviewDecisionSubmitted"
  | "ReviewGateApproved"
  | "ReviewGateModified"
  | "ReviewGateRejected";

export interface PipelineEventEnvelope {
  event_type: PipelineEventType;
  event_id: string;
  engagement_id: string;
  client_id: string;
  timestamp: ISODateTime;
  layer: PipelineLayer;
  payload: JsonObject;
}

export interface RunSummary {
  id: string;
  engagement_id: string | null;
  client_id: string;
  title: string;
  question: string;
  phase: RunPhase;
  status: RunStatus;
  created_at: ISODateTime;
  started_at: ISODateTime | null;
  completed_at: ISODateTime | null;
  elapsed_ms: number;
  event_count: number;
  total_tokens: number;
  tokens_by_layer: Record<string, number>;
  active_gate_id: string | null;
  error: RunError | null;
}

export interface RunError {
  kind: "exception" | "stopped" | "rejected" | "governance_halt";
  message: string;
  detail?: JsonObject;
}

export interface RunDetail extends RunSummary {
  spec: EngagementSpecDTO | null;
  result_available: boolean;
  markdown_preview: string | null;
}
```

### Result DTO Types

These DTOs intentionally mirror the Python model names while allowing nested
payloads to remain JSON until the frontend needs richer typed views.

```ts
export interface EngagementSpecDTO {
  research_spec: {
    engagement_id: string;
    client_id: string;
    title: string;
    created_at: ISODateTime;
    specification_version: number;
    decision_context: string;
    surprising_finding: string;
    questions: Array<{
      question: string;
      is_primary: boolean;
      parent_question: string | null;
    }>;
    engagement_type: string;
    effective_pipeline_profile: "light" | "standard" | "deep";
    effective_evaluation_profile: string;
    quality_bar: string;
    non_goals: string[];
  };
  task_decomposition: {
    project: string;
    engagement_id: string;
    client_id: string;
    specification_version: number;
    decomposition_rationale: string;
    tasks: ResearchTaskDTO[];
  };
  validation_report: {
    intent_clear: boolean;
    scope_valid: boolean;
    within_frontier: boolean;
    quality_threshold_met: boolean;
    issues: string[];
  };
  issue_tree: JsonObject | null;
}

export interface ResearchTaskDTO {
  id: string;
  category: string;
  type: "estimative" | "current";
  description: string;
  required_sources: string[];
  acceptance_criteria: string[];
  deliverable_destination: string;
  priority: number;
  importance: "primary" | "critical" | "supporting" | "optional";
  status: string;
  assigned_agent_id: string | null;
  dependencies: string[];
  issue_tree_branch_id: string | null;
}

export interface CitationManifestDTO {
  manifest_id: string;
  engagement_id: string;
  client_id: string;
  citations: CitationDTO[];
  corroboration_pairs: Array<{
    citation_a: string;
    citation_b: string;
    overlap_score: number;
  }>;
  dead_urls: string[];
  fabrication_flags: string[];
  aliases: JsonObject[];
}

export interface CitationDTO {
  citation_id: string;
  url: string;
  doi: string | null;
  title: string;
  authors: string[];
  publication: string;
  date_published: string | null;
  access_date: ISODateTime;
  source_type: "academic" | "news" | "filing" | "report" | "government" | "internal";
  quality_score: number;
  url_live: boolean | null;
  found_by_agents: string[];
  merged_from_ids: string[];
}

export interface EvaluationResultDTO {
  evaluation_id: string;
  engagement_id: string;
  client_id: string;
  task_id: string;
  evaluated_at: ISODateTime;
  intensity: "light_touch" | "standard" | "deep";
  passed: boolean;
  overall_score: number;
  layer1_results: JsonObject;
  layer2_results: JsonObject;
  layer3_results: JsonObject | null;
  layer4_results: JsonObject | null;
  layer5_results: JsonObject | null;
  feedback: string;
}

export interface PipelineResultDTO {
  engagement_id: string;
  client_id: string;
  spec: EngagementSpecDTO;
  findings: JsonObject[];
  manifest: CitationManifestDTO;
  confidence_map: JsonObject;
  evaluation_results: EvaluationResultDTO[];
  markdown_output: string;
  total_tokens: number;
  total_events: number;
  tokens_by_layer: Record<string, number>;
}
```

### Endpoint Schemas

```ts
export interface StartRunRequest {
  question: string;
  client_id?: string;
  client_context?: string | null;
  pipeline_profile?: "light" | "standard" | "deep" | null;
  source_ids?: string[];
}

export interface StartRunResponse {
  run: RunSummary;
  websocket_url: string;
}

export interface ListRunsResponse {
  runs: RunSummary[];
}

export interface GetRunResponse {
  run: RunDetail;
  result: PipelineResultDTO | null;
}

export interface GetRunEventsResponse {
  run_id: string;
  events: PipelineEventEnvelope[];
}

export interface StopRunResponse {
  run: RunSummary;
  accepted: boolean;
}

export interface HitlDecisionRequest {
  decision: "approve" | "modify" | "reject";
  decided_by?: string;
  modifications?: JsonObject | null;
  reasoning?: string | null;
}

export interface HitlDecisionResponse {
  gate: GateDTO;
  run: RunSummary;
}

export interface GateDTO {
  id: string;
  engagement_id: string;
  client_id: string;
  gate_type: "post_specification" | "post_deliberation";
  status: "pending" | "approved" | "modified" | "rejected";
  created_at: ISODateTime;
  resolved_at: ISODateTime | null;
  resolved_by: string | null;
  items: Array<{
    id: string;
    item_type:
      | "issue_tree"
      | "agent_config"
      | "confidence_map"
      | "divergence_points"
      | "sprint_contract";
    content: JsonObject;
    display_order: number;
  }>;
}
```

```ts
export interface ConfigResponse {
  app: {
    llm_provider: "claude_cli" | "api_key" | "codex_oauth";
    flagship_model: string;
    standard_model: string;
    fast_model: string;
    api_keys: {
      openai: { configured: boolean };
      exa: { configured: boolean };
      brave: { configured: boolean };
      voyage: { configured: boolean };
      cohere: { configured: boolean };
    };
  };
  pipeline: {
    model_mixing: Record<string, string>;
    layer_effort_overrides: Record<string, "low" | "medium" | "high" | "xhigh">;
    research_default_rounds: number;
    research_max_rounds: number;
    research_quality_threshold: number;
    claude_cli_concurrency: number;
    research_concurrency: number;
    deep_research_timeout_s: number;
    evaluator_pass_threshold: number;
    evaluator_layer3_weight: number;
    dispute_variance_threshold: number;
    wwhtb_confidence_threshold: number;
    l5_low_agreement_threshold: number;
    research_token_ceiling_per_task: number;
  };
}

export interface ConfigUpdateRequest {
  app?: {
    llm_provider?: "claude_cli" | "api_key" | "codex_oauth";
    flagship_model?: string;
    standard_model?: string;
    fast_model?: string;
    openai_api_key?: string;
    exa_api_key?: string;
    brave_search_api_key?: string;
    voyage_api_key?: string;
    cohere_api_key?: string;
  };
  pipeline?: Partial<ConfigResponse["pipeline"]>;
}

export interface ConfigUpdateResponse {
  config: ConfigResponse;
  restart_required: boolean;
}
```

```ts
export interface SourceRecordDTO {
  source_id: string;
  artifact_id: string;
  filename: string;
  title: string | null;
  source_family: "article" | "pdf" | "report" | "unknown";
  canonical_url: string | null;
  content_hash: string;
  uploaded_at: ISODateTime;
  fetched_at: ISODateTime | null;
  artifact_count: number;
  chunk_count: number;
  chunks_created: number;
  chunks_updated: number;
  chunks_skipped: number;
  parse_confidence: {
    score: number;
    tier: "high" | "medium" | "low";
    reasons: string[];
  } | null;
  warnings: Array<{ code: string; message: string }>;
}

export interface UploadSourceRequest {
  file: File;
  title?: string;
  canonical_url?: string;
  source_family?: "article" | "pdf" | "report" | "unknown";
}

export interface UploadSourceResponse {
  source: SourceRecordDTO;
}

export interface ListSourcesResponse {
  sources: SourceRecordDTO[];
}
```

### REST Endpoints

| Method + path | Request | Response | Pipeline component wrapped |
|---|---|---|---|
| `POST /api/runs` | `StartRunRequest` | `StartRunResponse` | Constructs `Pipeline` with current `AppConfig`/`PipelineConfig`, schedules `Pipeline.run_with_events(...)`, creates server-side run record |
| `GET /api/runs` | none | `ListRunsResponse` | `RunStore` summaries for sidebar |
| `GET /api/runs/{id}` | none | `GetRunResponse` | `PipelineResult` persisted after iterator exhaustion |
| `GET /api/runs/{id}/events` | none | `GetRunEventsResponse` | Append-only event history produced by `run_with_events` |
| `WS /api/runs/{id}/stream` | WebSocket upgrade | `StreamMessage` frames | Live wrapper around `run_with_events` event yield and server-derived state |
| `POST /api/runs/{id}/stop` | none | `StopRunResponse` | Server task cancellation / graceful stop flag; does not require pipeline code changes in v0.1 |
| `POST /api/runs/{id}/hitl/{gate_id}` | `HitlDecisionRequest` | `HitlDecisionResponse` | Run-scoped facade over `keystone.hitl.service.HITLService.submit_decision` |
| `GET /api/config` | none | `ConfigResponse` | `AppConfig` and nested `PipelineConfig`, sanitized secrets |
| `PUT /api/config` | `ConfigUpdateRequest` | `ConfigUpdateResponse` | Server config store; future runs receive updated config |
| `POST /api/sources` | `UploadSourceRequest` as `multipart/form-data` | `UploadSourceResponse` | `FetchedArtifact` -> parser -> `EvidencePrepRecord` -> `RetrievalService.ingest_institutional` |
| `GET /api/sources` | none | `ListSourcesResponse` | Source metadata store plus retrieval ingest summaries |

### WebSocket Messages

```ts
export type StreamMessage =
  | StreamConnectedMessage
  | RunSnapshotMessage
  | RunStateMessage
  | PipelineEventMessage
  | HitlGateMessage
  | ResultReadyMessage
  | StreamErrorMessage
  | HeartbeatMessage;

export interface StreamConnectedMessage {
  type: "connected";
  run_id: string;
  sent_at: ISODateTime;
}

export interface RunSnapshotMessage {
  type: "run_snapshot";
  run: RunSummary;
  recent_events: PipelineEventEnvelope[];
  active_gate: GateDTO | null;
}

export interface RunStateMessage {
  type: "run_state";
  run_id: string;
  previous_phase: RunPhase | null;
  phase: RunPhase;
  status: RunStatus;
  message: string;
  progress: {
    completed_tasks: number;
    total_tasks: number;
    completed_agents: number;
    total_agents: number;
    citations_total: number;
    evaluations_complete: number;
  };
  sent_at: ISODateTime;
}

export interface PipelineEventMessage {
  type: "pipeline_event";
  run_id: string;
  event: PipelineEventEnvelope;
}

export interface HitlGateMessage {
  type: "hitl_gate";
  run_id: string;
  gate: GateDTO;
}

export interface ResultReadyMessage {
  type: "result_ready";
  run_id: string;
  result_url: string;
  summary: {
    markdown_chars: number;
    total_tokens: number;
    total_events: number;
    passed_evaluations: number;
    total_evaluations: number;
  };
}

export interface StreamErrorMessage {
  type: "error";
  run_id: string;
  error: RunError;
  sent_at: ISODateTime;
}

export interface HeartbeatMessage {
  type: "heartbeat";
  run_id: string;
  sent_at: ISODateTime;
}
```

## 3. Event-to-UI Mapping

Priority definitions:

- Critical: visible in the default UI because the user must understand or act.
- Status: visible in progress summaries, not necessarily as a full row.
- Informational: hidden behind the technical detail/event log by default.

| Event | Panel updates | User sees | Priority |
|---|---|---|---|
| `SpecificationGenerated` | Chat, observability, sidebar | Planning complete; spec version, question count, validation status | Critical |
| `TasksDecomposed` | Chat, observability | Research plan expanded into N tasks by category | Critical |
| `AgentDispatched` | Observability | Agent/task appears in roster with model tier and tool count | Status |
| `ResearchStarted` | Observability, sidebar | Agent status changes to active research | Status |
| `SourceFound` | Observability, result citation drawer | Source count increments; high-quality source may appear in evidence detail | Informational |
| `CitationExtracted` | Observability, citation detail | Citation count increments with title | Informational |
| `FindingSynthesized` | Observability | Agent has synthesized claims; confidence range updates | Status |
| `ResearchComplete` | Observability, sidebar | Agent row completes with source/token/absence counts | Status |
| `CitationDeduped` | Observability, result citation drawer | Duplicate source merged; canonical citation count stabilizes | Informational |
| `CorroborationScored` | Observability, result citation drawer | Corroboration pair added; evidence strength indicator updates | Informational |
| `URLVerified` | Observability, result citation drawer | URL marked live/dead; dead URL becomes a warning | Status |
| `ManifestProduced` | Observability, results | Evidence check complete with total citations, dead URLs, flags, corroboration | Critical |
| `ChunkIngested` | Source management, observability | Uploaded/source corpus ingested with artifact and chunk counts | Status |
| `SearchCompleted` | Observability detail | Retrieval search logged with result count and latency | Informational |
| `AnalystSpawned` | Observability | Analyst methodology appears in analyst review roster | Status |
| `IndependentAnalysisComplete` | Observability | Analyst methodology completes with claim count | Status |
| `AggregationComplete` | Observability | Consensus/disagreement/blind-spot summary appears | Critical |
| `ConfidenceMapProduced` | Observability, results | Confidence distribution fills across high/moderate/weak/contested/gaps | Critical |
| `OutlineGenerated` | Observability | Brief outline created with section count | Status |
| `SectionDrafted` | Observability | Section row appears with title and claim count | Status |
| `SprintContractProposed` | Observability detail | Section quality criteria count appears in advanced detail | Informational |
| `DraftGenerated` | Observability | Future-compatible: draft section generated with word count | Status |
| `CitationFormatted` | Observability, results | Future-compatible: citations formatted for a section | Informational |
| `DeliverableAssembled` | Results, sidebar | Future-compatible: final deliverable assembled | Critical |
| `DeterministicCheckPassed` | Observability, results quality | Fact/numerical check counts update; failures become warnings | Status |
| `CitationGateResult` | Results quality, observability | Citation gate pass/fail; fabrication count is prominent | Critical |
| `RubricDimensionScored` | Results quality | Rubric bar for one dimension updates | Status |
| `ProcessTrajectoryScored` | Results quality, observability | Process quality score and flags update for a task | Status |
| `EvaluationComplete` | Results quality, sidebar | Task score and pass/fail status appear | Critical |
| `EnsembleJudgeScored` | Results quality detail | Individual judge score in advanced ensemble detail | Informational |
| `DissenterVetoTriggered` | Results quality, observability | Prominent "review needed" quality warning | Critical |
| `EnsembleEvaluationComplete` | Results quality | Ensemble score, agreement, veto count update | Critical |
| `ObservationRecorded` | Observability detail | Observation-library entry recorded | Informational |
| `PatternPromoted` | Observability detail | Internal pattern promoted; no default user-facing alert | Informational |
| `ConstraintEncoded` | Observability detail | Internal constraint encoded; no default user-facing alert | Informational |
| `ReviewGateCreated` | HITL modal, sidebar, chat | Run pauses and review modal opens | Critical |
| `ReviewDecisionSubmitted` | HITL modal | Submitted decision state appears | Critical |
| `ReviewGateApproved` | HITL modal, sidebar | Modal closes; run resumes | Critical |
| `ReviewGateModified` | HITL modal, sidebar | Modification accepted or halted per backend GAP-17 semantics | Critical |
| `ReviewGateRejected` | HITL modal, sidebar | Run halts as rejected with reviewer reasoning | Critical |

## 4. Pipeline State Machine

The UI should maintain two concepts:

- `phase`: user-visible pipeline location, using the listed state names.
- `status`: lifecycle condition such as running, paused, stopping, complete, or
  failed.

This keeps the requested visible state machine intact while allowing the stop
button to show "Stopping..." without inventing a new pipeline phase.

### State Transitions

| From | Trigger | To | UI behavior |
|---|---|---|---|
| none | `POST /api/runs` accepted | `QUEUED` | Sidebar row appears; chat input locks to active run |
| `QUEUED` | runner task starts, or first L0 event | `SPEC` | Show "Planning the engagement" |
| `SPEC` | first `ResearchStarted` | `RESEARCH` | Agent roster becomes primary progress element |
| `RESEARCH` | first CitationProcessor event | `CITATION` | Evidence health panel becomes active |
| `CITATION` | `AnalystSpawned` | `DELIBERATION` | Analyst methodology panel becomes active |
| `DELIBERATION` | first L2 event | `STRUCTURING` | Brief outline/section progress becomes active |
| `STRUCTURING` | first L4 or L5 event | `EVALUATION` | Quality review panel becomes active |
| `EVALUATION` | async iterator exhausts, before result persistence | `RENDERING` | Show "Preparing final brief"; do not wait for an event that does not exist today |
| `RENDERING` | `PipelineResult` saved and `result_ready` sent | `COMPLETE` | Results viewer becomes primary panel |
| any running phase | `ReviewGateCreated` | `PAUSED` | Open HITL modal; remember `resume_phase` server-side |
| `PAUSED` | `ReviewGateApproved` | `resume_phase` or next emitted-event phase | Close modal and resume progress |
| `PAUSED` | `ReviewGateModified` | `FAILED` in current backend, resumable after GAP-17 | Explain modification halt; keep artifacts visible |
| `PAUSED` | `ReviewGateRejected` | `FAILED` | Mark rejected and show reviewer reasoning |
| any running phase | server exception or governance halt | `FAILED` | Show failure banner and event history |
| any running phase | stop requested | same phase, `status="stopping"` | Disable stop button; show graceful-stop message |
| stopping | task cancellation confirmed without result | `FAILED` with `error.kind="stopped"` | Label as "Stopped" in UI, keep event history |

### UI By State

| State | Default visible UI |
|---|---|
| `QUEUED` | Sidebar row and pending state in chat |
| `SPEC` | Planning status, eventual task count and validation result |
| `RESEARCH` | Agent roster, source counts, completed-agent count |
| `CITATION` | Citation health, URL liveness, corroboration summary |
| `DELIBERATION` | Analyst methods, consensus/disagreement/blind-spot counts |
| `STRUCTURING` | Outline and section drafting progress |
| `EVALUATION` | Quality score cards, rubric bars, citation gate state |
| `RENDERING` | Final brief preparation indicator |
| `COMPLETE` | Results viewer with markdown, scores, citations |
| `PAUSED` | HITL modal blocks run controls except stop |
| `FAILED` | Failure/rejection/stopped banner plus event audit |

## 5. Phased Build Plan

### v0.1: Serving Layer + Basic Chat

Complexity: Medium.

Backend files:

- `src/keystone/server/__init__.py`
- `src/keystone/server/app.py`
- `src/keystone/server/models.py`
- `src/keystone/server/run_store.py`
- `src/keystone/server/pipeline_runner.py`
- `src/keystone/server/routes_runs.py`
- `src/keystone/server/ws.py`

Frontend files:

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/ws.ts`
- `frontend/src/types/api.ts`
- `frontend/src/components/SessionSidebar.tsx`
- `frontend/src/components/ChatPanel.tsx`
- `frontend/src/components/EventLog.tsx`
- `frontend/src/components/MarkdownResult.tsx`

What the user can do:

- Start a local research run from a question.
- Watch raw streamed events as text.
- Stop a run best-effort.
- See the final rendered markdown when the run completes.
- Reload completed run history from server state.

Implementation notes:

- Wrap `Pipeline.run_with_events(...)` directly.
- Persist every event envelope as it is yielded.
- Set `RENDERING` when the iterator exhausts and before saving result.
- No custom observability UI yet beyond a readable event stream.

### v0.2: Pipeline Observability + Session Management

Complexity: Medium-high.

Backend files:

- `src/keystone/server/state_machine.py`
- `src/keystone/server/event_projection.py`
- `src/keystone/server/routes_events.py`

Frontend files:

- `frontend/src/components/PipelineTimeline.tsx`
- `frontend/src/components/AgentRoster.tsx`
- `frontend/src/components/EvidenceHealth.tsx`
- `frontend/src/components/QualityReviewPanel.tsx`
- `frontend/src/components/RunHeader.tsx`
- `frontend/src/hooks/useRunStream.ts`
- `frontend/src/hooks/useRunProjection.ts`

What the user can do:

- See consultant-friendly live progress instead of raw event names.
- Switch between prior runs in the sidebar.
- Inspect agents, evidence health, analyst review, and quality review.
- Open a technical event log when debugging.

Implementation notes:

- Build projections from events server-side and send `run_state` messages.
- Keep frontend projection logic thin and replaceable.
- L3 events must be accepted but not required for render progress.

### v0.3: Source Management + Config Panel

Complexity: High.

Backend files:

- `src/keystone/server/routes_sources.py`
- `src/keystone/server/source_store.py`
- `src/keystone/server/source_ingest.py`
- `src/keystone/server/routes_config.py`
- `src/keystone/server/config_store.py`

Frontend files:

- `frontend/src/components/SourceLibrary.tsx`
- `frontend/src/components/SourceUploadDropzone.tsx`
- `frontend/src/components/SourceDetail.tsx`
- `frontend/src/components/SettingsPanel.tsx`
- `frontend/src/components/ModelTierControls.tsx`
- `frontend/src/components/ThresholdControls.tsx`

What the user can do:

- Upload local PDFs/articles/reports into the source library.
- Inspect parse quality, warnings, and chunk counts.
- Configure provider keys and model defaults locally.
- Adjust advanced pipeline thresholds for future runs.

Implementation notes:

- Source upload should produce `FetchedArtifact`, parse to
  `EvidencePrepRecord`, then ingest through `RetrievalService`.
- `GET /api/config` must not return raw secret values.
- `PUT /api/config` should reject changes that cannot affect an already-active
  run and clearly mark them as future-run defaults.

### v0.4: HITL Interaction + Pause/Resume

Complexity: High, depends on backend GAP-17.

Backend files:

- `src/keystone/server/routes_hitl.py`
- `src/keystone/server/hitl_bridge.py`
- `src/keystone/server/resume_controller.py`

Frontend files:

- `frontend/src/components/HitlGateModal.tsx`
- `frontend/src/components/GateArtifactTabs.tsx`
- `frontend/src/components/GateDecisionForm.tsx`
- `frontend/src/components/PauseResumeBanner.tsx`

What the user can do:

- Review post-specification and post-deliberation gates in-app.
- Approve a gate and let the run resume.
- Reject a gate and preserve a clear audit trail.
- Modify artifacts only after backend GAP-17 applies changes back into the
  issue tree/task list/confidence map and resumes from the correct boundary.

Implementation notes:

- The run-scoped endpoint wraps existing HITL service semantics.
- Before GAP-17, "modify" should be hidden or clearly terminal because current
  backend behavior halts on modification.
- Pause/resume should remain server-side; the frontend only submits decisions
  and renders the active gate.
