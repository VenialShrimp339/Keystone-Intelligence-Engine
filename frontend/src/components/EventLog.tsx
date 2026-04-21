import { Activity, Clock } from "lucide-react";

import { Badge } from "./ui/badge";
import { phaseLabel } from "./SessionSidebar";
import type { PipelineEventEnvelope } from "../types/api";

interface EventLogProps {
  events: PipelineEventEnvelope[];
}

export function EventLog({ events }: EventLogProps) {
  return (
    <aside className="flex h-full min-h-0 flex-col border-l bg-white">
      <div className="flex h-[65px] items-center justify-between border-b px-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" aria-hidden />
          <h2 className="text-sm font-semibold">Event Log</h2>
        </div>
        <Badge>{events.length}</Badge>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        {events.length === 0 ? (
          <div className="mt-12 flex flex-col items-center gap-3 text-center text-sm text-muted-foreground">
            <Clock className="h-8 w-8" aria-hidden />
            <span>No events yet.</span>
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <article key={event.event_id} className="rounded-md border bg-background p-3">
                <div className="flex min-w-0 items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold">{describeEvent(event)}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  <Badge className="shrink-0">{layerLabel(event.layer)}</Badge>
                </div>
                <details className="mt-2">
                  <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                    {event.event_type}
                  </summary>
                  <pre className="mt-2 max-h-64 overflow-auto rounded-sm bg-white p-2 text-[11px] leading-4 text-muted-foreground">
                    {JSON.stringify(event.payload, null, 2)}
                  </pre>
                </details>
              </article>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function describeEvent(event: PipelineEventEnvelope): string {
  const payload = event.payload;
  switch (event.event_type) {
    case "SpecificationGenerated":
      return "Engagement plan drafted";
    case "TasksDecomposed":
      return `Tasks decomposed${numberSuffix(payload.task_count, " task")}`;
    case "AgentDispatched":
      return `Agent dispatched${stringSuffix(payload.agent_type)}`;
    case "ResearchStarted":
      return `Research started${stringSuffix(payload.task_id)}`;
    case "SourceFound":
      return `Source found${stringSuffix(payload.source_type)}`;
    case "CitationExtracted":
      return `Citation extracted${stringSuffix(payload.title)}`;
    case "FindingSynthesized":
      return `Finding synthesized${numberSuffix(payload.claim_count, " claim")}`;
    case "ResearchComplete":
      return `Research complete${numberSuffix(payload.sources_consulted, " source")}`;
    case "ManifestProduced":
      return `Citation manifest produced${numberSuffix(payload.total_citations, " citation")}`;
    case "AnalystSpawned":
      return `Analyst spawned${stringSuffix(payload.analyst_type)}`;
    case "IndependentAnalysisComplete":
      return `Independent analysis complete${stringSuffix(payload.analyst_type)}`;
    case "AggregationComplete":
      return "Analyst aggregation complete";
    case "ConfidenceMapProduced":
      return `Confidence map produced${numberSuffix(payload.total_claims, " claim")}`;
    case "OutlineGenerated":
      return `Outline generated${numberSuffix(payload.section_count, " section")}`;
    case "SectionDrafted":
      return `Section drafted${stringSuffix(payload.section_title)}`;
    case "SprintContractProposed":
      return `Sprint contract proposed${numberSuffix(payload.criteria_count, " criterion")}`;
    case "EvaluationComplete":
      return `Evaluation complete${scoreSuffix(payload.overall_score)}`;
    case "EnsembleEvaluationComplete":
      return `Ensemble review complete${scoreSuffix(payload.aggregated_score)}`;
    case "ReviewGateCreated":
      return "Human review gate created";
    default:
      return event.event_type.replace(/([a-z])([A-Z])/g, "$1 $2");
  }
}

function layerLabel(layer: PipelineEventEnvelope["layer"]): string {
  if (layer === "L0") {
    return phaseLabel("SPEC");
  }
  if (layer === "L1" || layer === "Retrieval") {
    return phaseLabel("RESEARCH");
  }
  if (layer === "CitationProcessor") {
    return phaseLabel("CITATION");
  }
  if (layer === "L1.5") {
    return phaseLabel("DELIBERATION");
  }
  if (layer === "L2") {
    return phaseLabel("STRUCTURING");
  }
  if (layer === "L4" || layer === "L5") {
    return phaseLabel("EVALUATION");
  }
  return layer;
}

function stringSuffix(value: unknown): string {
  return typeof value === "string" && value.length > 0 ? `: ${value}` : "";
}

function numberSuffix(value: unknown, noun: string): string {
  if (typeof value !== "number") {
    return "";
  }
  return `: ${value}${noun}${value === 1 ? "" : "s"}`;
}

function scoreSuffix(value: unknown): string {
  if (typeof value !== "number") {
    return "";
  }
  return `: ${Math.round(value)} score`;
}

