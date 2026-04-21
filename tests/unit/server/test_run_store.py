from __future__ import annotations

import pytest

from keystone.events import ResearchStarted, TasksDecomposed
from keystone.server.models import RunPhase, RunStatus
from keystone.server.run_store import RunStore, envelope_from_event


@pytest.mark.asyncio
async def test_run_store_wraps_events_and_publishes_state() -> None:
    store = RunStore()
    run = await store.create_run(
        question="Estimate the market for autonomous warehouse robotics.",
        client_id="client-a",
        client_context=None,
    )
    queue = await store.subscribe(run.id)
    assert queue is not None

    await store.mark_started(run.id)
    started = await queue.get()
    assert started.type == "run_state"
    assert started.phase == RunPhase.SPEC
    assert started.status == RunStatus.RUNNING

    tasks_event = TasksDecomposed(
        event_id="evt-tasks",
        engagement_id="eng-1",
        client_id="client-a",
        task_count=3,
        categories=["market", "operations"],
        rationale="Split by market size and operating model.",
    )
    envelope = envelope_from_event(tasks_event)
    assert envelope.event_type == "TasksDecomposed"
    assert envelope.payload["task_count"] == 3
    assert "event_id" not in envelope.payload

    await store.append_event(run.id, envelope)
    event_message = await queue.get()
    assert event_message.type == "pipeline_event"
    assert event_message.event.event_id == "evt-tasks"

    research_event = ResearchStarted(
        event_id="evt-research",
        engagement_id="eng-1",
        client_id="client-a",
        agent_id="agent-1",
        task_id="task-1",
    )
    await store.append_event(run.id, envelope_from_event(research_event))

    research_message = await queue.get()
    state_message = await queue.get()
    assert research_message.type == "pipeline_event"
    assert state_message.type == "run_state"
    assert state_message.previous_phase == RunPhase.SPEC
    assert state_message.phase == RunPhase.RESEARCH

    detail = await store.get_detail(run.id)
    assert detail is not None
    assert detail.engagement_id == "eng-1"
    assert detail.event_count == 2
    assert detail.phase == RunPhase.RESEARCH


@pytest.mark.asyncio
async def test_run_store_records_stopped_runs() -> None:
    store = RunStore()
    run = await store.create_run(
        question="Map supplier risk.",
        client_id="client-a",
        client_context=None,
    )

    stopping = await store.mark_stopping(run.id)
    assert stopping.status == RunStatus.STOPPING

    await store.mark_stopped(run.id)
    detail = await store.get_detail(run.id)
    assert detail is not None
    assert detail.phase == RunPhase.FAILED
    assert detail.status == RunStatus.FAILED
    assert detail.error is not None
    assert detail.error.kind == "stopped"

