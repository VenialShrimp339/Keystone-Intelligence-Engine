import { Play, Square } from "lucide-react";
import { FormEvent, useState } from "react";

import { phaseLabel } from "./SessionSidebar";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import type { RunSummary } from "../types/api";

interface ChatPanelProps {
  currentRun: RunSummary | null;
  isStarting: boolean;
  onStartRun: (question: string, clientContext: string | null) => Promise<void>;
  onStopRun: () => Promise<void>;
}

export function ChatPanel({ currentRun, isStarting, onStartRun, onStopRun }: ChatPanelProps) {
  const [question, setQuestion] = useState("");
  const [clientContext, setClientContext] = useState("");
  const canStop =
    currentRun?.status === "running" ||
    currentRun?.status === "queued" ||
    currentRun?.status === "paused" ||
    currentRun?.status === "stopping";

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isStarting) {
      return;
    }
    await onStartRun(trimmed, clientContext.trim() || null);
    setQuestion("");
    setClientContext("");
  };

  return (
    <section className="border-b bg-white px-5 py-5">
      <form className="grid gap-4" onSubmit={submit}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">Ask Keystone</h1>
            {currentRun ? (
              <p className="mt-1 text-sm text-muted-foreground">
                {phaseLabel(currentRun.phase, currentRun.status, currentRun.error?.kind)}
                {currentRun.error ? `: ${currentRun.error.message}` : ""}
              </p>
            ) : null}
          </div>
          <div className="flex h-10 items-center gap-2">
            <Button type="submit" disabled={!question.trim() || isStarting}>
              <Play className="h-4 w-4" aria-hidden />
              Run
            </Button>
            <Button type="button" variant="secondary" disabled={!canStop} onClick={onStopRun}>
              <Square className="h-4 w-4" aria-hidden />
              Stop
            </Button>
          </div>
        </div>

        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What strategic question should Keystone research?"
          className="min-h-[130px]"
        />

        <Textarea
          value={clientContext}
          onChange={(event) => setClientContext(event.target.value)}
          placeholder="Client context, decision, geography, time horizon, constraints"
          className="min-h-[84px]"
        />
      </form>
    </section>
  );
}

