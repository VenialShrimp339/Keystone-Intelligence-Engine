"""WebSocket route for live run event streams."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from keystone.server.models import HeartbeatMessage, StreamConnectedMessage

if TYPE_CHECKING:
    from keystone.server.run_store import RunStore

router = APIRouter(tags=["runs"])


@router.websocket("/api/runs/{run_id}/stream")
async def stream_run(websocket: WebSocket, run_id: str) -> None:
    store: RunStore = websocket.app.state.run_store
    queue = await store.subscribe(run_id)
    if queue is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    try:
        await websocket.send_json(
            StreamConnectedMessage(run_id=run_id, sent_at=_now()).model_dump(mode="json")
        )
        snapshot = await store.get_snapshot(run_id)
        if snapshot is not None:
            await websocket.send_json(snapshot.model_dump(mode="json"))

        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
            except TimeoutError:
                message = HeartbeatMessage(run_id=run_id, sent_at=_now())
            await websocket.send_json(message.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
    finally:
        await store.unsubscribe(run_id, queue)


def _now() -> datetime:
    return datetime.now(UTC)
