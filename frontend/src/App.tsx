import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { QueryClient as TanStackQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";

import { ChatPanel } from "./components/ChatPanel";
import { EventLog } from "./components/EventLog";
import { MarkdownResult } from "./components/MarkdownResult";
import { SessionSidebar } from "./components/SessionSidebar";
import { Button } from "./components/ui/button";
import { getRun, getRunEvents, listRuns, startRun, stopRun } from "./lib/api";
import { connectRunStream, type ConnectionStatus } from "./lib/ws";
import type {
  GetRunResponse,
  ListRunsResponse,
  PipelineEventEnvelope,
  RunSummary,
  StreamMessage,
} from "./types/api";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <KeystoneApp />
    </QueryClientProvider>
  );
}

function KeystoneApp() {
  const client = useQueryClient();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [hasAutoSelected, setHasAutoSelected] = useState(false);
  const [eventsByRun, setEventsByRun] = useState<Record<string, PipelineEventEnvelope[]>>({});
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("idle");

  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: listRuns,
    refetchInterval: 5000,
  });
  const runs = runsQuery.data?.runs ?? [];

  useEffect(() => {
    if (!hasAutoSelected && !selectedRunId && runs.length > 0) {
      setSelectedRunId(runs[0].id);
      setHasAutoSelected(true);
    }
  }, [hasAutoSelected, runs, selectedRunId]);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );
  const selectedStatus = selectedRun?.status ?? null;

  const runQuery = useQuery({
    queryKey: ["run", selectedRunId],
    queryFn: () => getRun(selectedRunId!),
    enabled: selectedRunId !== null,
  });

  const eventsQuery = useQuery({
    queryKey: ["events", selectedRunId],
    queryFn: () => getRunEvents(selectedRunId!),
    enabled: selectedRunId !== null,
  });

  useEffect(() => {
    if (selectedRunId && eventsQuery.data) {
      setEventsByRun((current) => ({
        ...current,
        [selectedRunId]: eventsQuery.data.events,
      }));
    }
  }, [eventsQuery.data, selectedRunId]);

  useEffect(() => {
    if (!selectedRunId || !selectedStatus || !isLive(selectedStatus)) {
      setConnectionStatus(selectedRunId ? "closed" : "idle");
      return;
    }

    const stream = connectRunStream(selectedRunId, {
      onStatus: setConnectionStatus,
      onMessage: (message) => handleStreamMessage(message, client, setEventsByRun),
    });
    return () => stream.close();
  }, [client, selectedRunId, selectedStatus]);

  const startMutation = useMutation({
    mutationFn: ({ question, clientContext }: { question: string; clientContext: string | null }) =>
      startRun({ question, client_context: clientContext }),
    onSuccess: (response) => {
      upsertRun(client, response.run);
      setEventsByRun((current) => ({ ...current, [response.run.id]: [] }));
      setSelectedRunId(response.run.id);
    },
  });

  const stopMutation = useMutation({
    mutationFn: (runId: string) => stopRun(runId),
    onSuccess: (response) => {
      upsertRun(client, response.run);
    },
  });

  const selectedEvents = selectedRunId ? eventsByRun[selectedRunId] ?? [] : [];
  const markdown = runQuery.data?.result?.markdown_output ?? null;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex h-[65px] items-center justify-between border-b bg-white px-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
            K
          </div>
          <div className="min-w-0">
            <div className="truncate text-base font-semibold">Keystone</div>
            <div className="truncate text-xs text-muted-foreground">Local research workspace</div>
          </div>
        </div>
        <Button variant="secondary" size="sm" onClick={() => runsQuery.refetch()}>
          <RefreshCw className="h-4 w-4" aria-hidden />
          Refresh
        </Button>
      </header>

      <div className="grid h-[calc(100vh-65px)] min-h-[640px] grid-cols-[320px_minmax(0,1fr)] max-lg:grid-cols-1 max-lg:grid-rows-[320px_minmax(0,1fr)]">
        <div className="min-h-0">
          <SessionSidebar
            runs={runs}
            selectedRunId={selectedRunId}
            connectionStatus={connectionStatus}
            onSelectRun={setSelectedRunId}
            onNewResearch={() => {
              setHasAutoSelected(true);
              setSelectedRunId(null);
            }}
          />
        </div>

        <main className="grid min-h-0 grid-cols-[minmax(0,1fr)_420px] max-xl:grid-cols-1">
          <div className="min-h-0 overflow-y-auto">
            <ChatPanel
              currentRun={selectedRun ?? runQuery.data?.run ?? null}
              isStarting={startMutation.isPending}
              onStartRun={(question, clientContext) =>
                startMutation.mutateAsync({ question, clientContext }).then(() => undefined)
              }
              onStopRun={() =>
                selectedRunId ? stopMutation.mutateAsync(selectedRunId).then(() => undefined) : Promise.resolve()
              }
            />
            <MarkdownResult markdown={markdown} />
          </div>
          <div className="max-xl:min-h-[420px]">
            <EventLog events={selectedEvents} />
          </div>
        </main>
      </div>
    </div>
  );
}

function handleStreamMessage(
  message: StreamMessage,
  client: TanStackQueryClient,
  setEventsByRun: Dispatch<SetStateAction<Record<string, PipelineEventEnvelope[]>>>,
) {
  if (message.type === "run_snapshot") {
    upsertRun(client, message.run);
    setEventsByRun((current) => ({
      ...current,
      [message.run.id]: dedupeEvents(message.recent_events),
    }));
    return;
  }

  if (message.type === "pipeline_event") {
    setEventsByRun((current) => {
      const currentEvents = current[message.run_id] ?? [];
      if (currentEvents.some((event) => event.event_id === message.event.event_id)) {
        return current;
      }
      return {
        ...current,
        [message.run_id]: [...currentEvents, message.event],
      };
    });
    client.setQueryData<ListRunsResponse>(["runs"], (current) =>
      current
        ? {
            runs: current.runs.map((run) =>
              run.id === message.run_id ? { ...run, event_count: run.event_count + 1 } : run,
            ),
          }
        : current,
    );
    return;
  }

  if (message.type === "run_state") {
    client.setQueryData<ListRunsResponse>(["runs"], (current) =>
      current
        ? {
            runs: current.runs.map((run) =>
              run.id === message.run_id
                ? { ...run, phase: message.phase, status: message.status }
                : run,
            ),
          }
        : current,
    );
    return;
  }

  if (message.type === "result_ready") {
    client.invalidateQueries({ queryKey: ["runs"] });
    client.invalidateQueries({ queryKey: ["run", message.run_id] });
    client.invalidateQueries({ queryKey: ["events", message.run_id] });
    return;
  }

  if (message.type === "error") {
    client.invalidateQueries({ queryKey: ["runs"] });
    client.invalidateQueries({ queryKey: ["run", message.run_id] });
  }
}

function upsertRun(client: TanStackQueryClient, run: RunSummary) {
  client.setQueryData<ListRunsResponse>(["runs"], (current) => {
    const runs = current?.runs ?? [];
    const exists = runs.some((item) => item.id === run.id);
    return {
      runs: exists
        ? runs.map((item) => (item.id === run.id ? run : item))
        : [run, ...runs],
    };
  });

  client.setQueryData<GetRunResponse>(["run", run.id], (current) =>
    current ? { ...current, run: { ...current.run, ...run } } : current,
  );
}

function dedupeEvents(events: PipelineEventEnvelope[]) {
  const seen = new Set<string>();
  return events.filter((event) => {
    if (seen.has(event.event_id)) {
      return false;
    }
    seen.add(event.event_id);
    return true;
  });
}

function isLive(status: RunSummary["status"]): boolean {
  return status === "queued" || status === "running" || status === "paused" || status === "stopping";
}
