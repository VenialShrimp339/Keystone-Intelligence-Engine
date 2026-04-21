"""REST routes for Keystone run lifecycle operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request, status

from keystone.server.models import (
    GetRunEventsResponse,
    GetRunResponse,
    ListRunsResponse,
    StartRunRequest,
    StartRunResponse,
    StopRunResponse,
)

if TYPE_CHECKING:
    from keystone.server.pipeline_runner import PipelineRunner
    from keystone.server.run_store import RunStore

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=StartRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_run(request_body: StartRunRequest, request: Request) -> StartRunResponse:
    runner = _runner(request)
    run = await runner.start(request_body)
    return StartRunResponse(run=run, websocket_url=f"/api/runs/{run.id}/stream")


@router.get("", response_model=ListRunsResponse)
async def list_runs(request: Request) -> ListRunsResponse:
    return ListRunsResponse(runs=await _store(request).list_runs())


@router.get("/{run_id}", response_model=GetRunResponse)
async def get_run(run_id: str, request: Request) -> GetRunResponse:
    store = _store(request)
    run = await store.get_detail(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return GetRunResponse(run=run, result=await store.get_result(run_id))


@router.get("/{run_id}/events", response_model=GetRunEventsResponse)
async def get_run_events(run_id: str, request: Request) -> GetRunEventsResponse:
    events = await _store(request).get_events(run_id)
    if events is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return GetRunEventsResponse(run_id=run_id, events=events)


@router.post("/{run_id}/stop", response_model=StopRunResponse)
async def stop_run(run_id: str, request: Request) -> StopRunResponse:
    store = _store(request)
    if not await store.exists(run_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    accepted = await _runner(request).stop(run_id)
    run = await store.get_summary(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return StopRunResponse(run=run, accepted=accepted)


def _store(request: Request) -> RunStore:
    return request.app.state.run_store


def _runner(request: Request) -> PipelineRunner:
    return request.app.state.pipeline_runner
