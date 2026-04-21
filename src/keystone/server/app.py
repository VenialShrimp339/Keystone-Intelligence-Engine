"""FastAPI application for the Keystone v0.1 browser UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from keystone.models.config import AppConfig
from keystone.server.pipeline_runner import PipelineRunner
from keystone.server.routes_runs import router as runs_router
from keystone.server.run_store import RunStore
from keystone.server.ws import router as ws_router

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    config = AppConfig()
    store = RunStore()
    runner = PipelineRunner(store, config)
    app.state.app_config = config
    app.state.run_store = store
    app.state.pipeline_runner = runner
    try:
        yield
    finally:
        await runner.shutdown()


app = FastAPI(title="Keystone Intelligence Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(ws_router)


@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
