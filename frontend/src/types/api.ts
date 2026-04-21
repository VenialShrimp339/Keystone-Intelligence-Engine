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

export type RunStatus = "queued" | "running" | "paused" | "stopping" | "complete" | "failed";

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
  detail?: JsonObject | null;
}

export interface RunDetail extends RunSummary {
  spec: JsonObject | null;
  result_available: boolean;
  markdown_preview: string | null;
}

export interface PipelineResultDTO {
  engagement_id: string;
  client_id: string;
  spec: JsonObject;
  findings: JsonObject[];
  manifest: JsonObject;
  confidence_map: JsonObject;
  evaluation_results: JsonObject[];
  markdown_output: string;
  total_tokens: number;
  total_events: number;
  tokens_by_layer: Record<string, number>;
}

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

export interface RunProgress {
  completed_tasks: number;
  total_tasks: number;
  completed_agents: number;
  total_agents: number;
  citations_total: number;
  evaluations_complete: number;
}

export type StreamMessage =
  | { type: "connected"; run_id: string; sent_at: ISODateTime }
  | {
      type: "run_snapshot";
      run: RunSummary;
      recent_events: PipelineEventEnvelope[];
      active_gate: JsonObject | null;
    }
  | {
      type: "run_state";
      run_id: string;
      previous_phase: RunPhase | null;
      phase: RunPhase;
      status: RunStatus;
      message: string;
      progress: RunProgress;
      sent_at: ISODateTime;
    }
  | { type: "pipeline_event"; run_id: string; event: PipelineEventEnvelope }
  | {
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
  | { type: "error"; run_id: string; error: RunError; sent_at: ISODateTime }
  | { type: "heartbeat"; run_id: string; sent_at: ISODateTime };

