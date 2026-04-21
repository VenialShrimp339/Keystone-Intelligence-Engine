import type { StreamMessage } from "../types/api";

export type ConnectionStatus = "idle" | "connecting" | "open" | "reconnecting" | "closed" | "error";

export interface RunStreamHandlers {
  onMessage: (message: StreamMessage) => void;
  onStatus: (status: ConnectionStatus) => void;
  onError?: (error: Event) => void;
}

export interface RunStreamClient {
  close: () => void;
}

export function connectRunStream(runId: string, handlers: RunStreamHandlers): RunStreamClient {
  let socket: WebSocket | null = null;
  let retryTimer: number | null = null;
  let retryCount = 0;
  let closed = false;

  const connect = (reconnecting = false) => {
    handlers.onStatus(reconnecting ? "reconnecting" : "connecting");
    socket = new WebSocket(websocketUrl(runId));

    socket.onopen = () => {
      retryCount = 0;
      handlers.onStatus("open");
    };

    socket.onmessage = (event) => {
      handlers.onMessage(JSON.parse(event.data as string) as StreamMessage);
    };

    socket.onerror = (event) => {
      handlers.onStatus("error");
      handlers.onError?.(event);
    };

    socket.onclose = () => {
      if (closed) {
        handlers.onStatus("closed");
        return;
      }
      const delay = Math.min(5000, 500 * 2 ** retryCount);
      retryCount += 1;
      handlers.onStatus("reconnecting");
      retryTimer = window.setTimeout(() => connect(true), delay);
    };
  };

  connect();

  return {
    close: () => {
      closed = true;
      if (retryTimer !== null) {
        window.clearTimeout(retryTimer);
      }
      socket?.close();
      handlers.onStatus("closed");
    },
  };
}

function websocketUrl(runId: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/runs/${runId}/stream`;
}

