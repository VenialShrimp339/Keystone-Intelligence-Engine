import { FileText, Plus, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import type { ConnectionStatus } from "../lib/ws";
import { cn } from "../lib/utils";
import type { RunPhase, RunStatus, RunSummary } from "../types/api";

interface SessionSidebarProps {
  runs: RunSummary[];
  selectedRunId: string | null;
  connectionStatus: ConnectionStatus;
  onSelectRun: (runId: string) => void;
  onNewResearch: () => void;
}

export function SessionSidebar({
  runs,
  selectedRunId,
  connectionStatus,
  onSelectRun,
  onNewResearch,
}: SessionSidebarProps) {
  const [query, setQuery] = useState("");
  const filteredRuns = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return runs;
    }
    return runs.filter(
      (run) =>
        run.title.toLowerCase().includes(needle) ||
        run.question.toLowerCase().includes(needle) ||
        run.phase.toLowerCase().includes(needle),
    );
  }, [query, runs]);

  const today = filteredRuns.filter((run) => isToday(run.created_at));
  const previous = filteredRuns.filter((run) => !isToday(run.created_at));

  return (
    <aside className="flex h-full min-h-0 flex-col border-r bg-white">
      <div className="border-b px-4 py-4">
        <Button className="w-full" onClick={onNewResearch}>
          <Plus className="h-4 w-4" aria-hidden />
          New Research
        </Button>
        <div className="mt-3 flex h-10 items-center gap-2 rounded-md border bg-background px-3">
          <Search className="h-4 w-4 text-muted-foreground" aria-hidden />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            placeholder="Search runs"
          />
        </div>
      </div>

      <div className="flex items-center justify-between border-b px-4 py-3 text-xs">
        <span className="font-medium text-muted-foreground">Stream</span>
        <Badge tone={connectionTone(connectionStatus)}>{connectionLabel(connectionStatus)}</Badge>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
        <RunGroup title="Today" runs={today} selectedRunId={selectedRunId} onSelectRun={onSelectRun} />
        <RunGroup
          title="Previous"
          runs={previous}
          selectedRunId={selectedRunId}
          onSelectRun={onSelectRun}
        />
        {filteredRuns.length === 0 ? (
          <div className="mt-8 flex flex-col items-center gap-3 text-center text-sm text-muted-foreground">
            <FileText className="h-8 w-8" aria-hidden />
            <span>No runs found.</span>
          </div>
        ) : null}
      </div>
    </aside>
  );
}

function RunGroup({
  title,
  runs,
  selectedRunId,
  onSelectRun,
}: {
  title: string;
  runs: RunSummary[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}) {
  if (runs.length === 0) {
    return null;
  }

  return (
    <section className="mb-5">
      <div className="mb-2 px-1 text-xs font-semibold uppercase text-muted-foreground">{title}</div>
      <div className="space-y-2">
        {runs.map((run) => (
          <button
            key={run.id}
            type="button"
            onClick={() => onSelectRun(run.id)}
            className={cn(
              "grid w-full gap-2 rounded-md border bg-white p-3 text-left shadow-panel transition-colors hover:border-primary/40 hover:bg-muted/40",
              selectedRunId === run.id && "border-primary bg-blue-50/60",
            )}
          >
            <div className="flex min-w-0 items-start justify-between gap-2">
              <div className="min-w-0 truncate text-sm font-semibold">{run.title}</div>
              <Badge tone={statusTone(run.status, run.error?.kind)} className="shrink-0">
                {phaseLabel(run.phase, run.status, run.error?.kind)}
              </Badge>
            </div>
            <div className="line-clamp-2 min-h-[2.25rem] text-xs leading-[1.125rem] text-muted-foreground">
              {run.question}
            </div>
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{formatElapsed(run.elapsed_ms)}</span>
              <span>{run.event_count} events</span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

export function phaseLabel(phase: RunPhase, status?: RunStatus, errorKind?: string): string {
  if (errorKind === "stopped") {
    return "Stopped";
  }
  if (status === "stopping") {
    return "Stopping";
  }
  const labels: Record<RunPhase, string> = {
    QUEUED: "Queued",
    SPEC: "Planning",
    RESEARCH: "Research",
    CITATION: "Evidence check",
    DELIBERATION: "Analyst review",
    STRUCTURING: "Structuring",
    EVALUATION: "Quality review",
    RENDERING: "Final brief",
    COMPLETE: "Complete",
    PAUSED: "Paused",
    FAILED: "Failed",
  };
  return labels[phase];
}

function statusTone(status: RunStatus, errorKind?: string) {
  if (status === "complete") {
    return "success";
  }
  if (status === "failed" && errorKind !== "stopped") {
    return "danger";
  }
  if (status === "paused" || status === "stopping") {
    return "warning";
  }
  if (status === "running") {
    return "active";
  }
  return "neutral";
}

function connectionTone(status: ConnectionStatus) {
  if (status === "open") {
    return "success";
  }
  if (status === "connecting" || status === "reconnecting") {
    return "warning";
  }
  if (status === "error") {
    return "danger";
  }
  return "neutral";
}

function connectionLabel(status: ConnectionStatus) {
  const labels: Record<ConnectionStatus, string> = {
    idle: "Idle",
    connecting: "Connecting",
    open: "Live",
    reconnecting: "Reconnecting",
    closed: "Closed",
    error: "Error",
  };
  return labels[status];
}

function isToday(value: string): boolean {
  const date = new Date(value);
  const now = new Date();
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  );
}

function formatElapsed(ms: number): string {
  if (ms < 1000) {
    return "0s";
  }
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}m ${rest}s`;
}

