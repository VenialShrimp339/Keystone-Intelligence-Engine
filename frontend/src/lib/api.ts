import type {
  GetRunEventsResponse,
  GetRunResponse,
  ListRunsResponse,
  StartRunRequest,
  StartRunResponse,
  StopRunResponse,
} from "../types/api";

const API_BASE = "/api";

export async function startRun(payload: StartRunRequest): Promise<StartRunResponse> {
  return request<StartRunResponse>("/runs", {
    method: "POST",
    body: JSON.stringify({
      client_id: "local",
      ...payload,
    }),
  });
}

export async function listRuns(): Promise<ListRunsResponse> {
  return request<ListRunsResponse>("/runs");
}

export async function getRun(runId: string): Promise<GetRunResponse> {
  return request<GetRunResponse>(`/runs/${runId}`);
}

export async function getRunEvents(runId: string): Promise<GetRunEventsResponse> {
  return request<GetRunEventsResponse>(`/runs/${runId}/events`);
}

export async function stopRun(runId: string): Promise<StopRunResponse> {
  return request<StopRunResponse>(`/runs/${runId}/stop`, { method: "POST" });
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP status message when the server did not return JSON.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

