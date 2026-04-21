"""Async task wrapper around ``Pipeline.run_with_events``."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from keystone.gateway.factory import build_mcp_gateway

if TYPE_CHECKING:
    from keystone.checkpoint.store import CheckpointStore
from keystone.llm_client import create_llm_factory
from keystone.models.config import AppConfig
from keystone.pipeline.orchestrator import Pipeline
from keystone.server.models import RunError, RunErrorKind, RunStatus, RunSummary, StartRunRequest
from keystone.server.run_store import RunStore, envelope_from_event

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Schedules and cancels single-process Keystone pipeline runs."""

    def __init__(
        self,
        store: RunStore,
        config: AppConfig | None = None,
        checkpoint_store: CheckpointStore | None = None,
    ) -> None:
        self._store = store
        self._config = config or AppConfig()
        self._checkpoint_store = checkpoint_store
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def start(self, request: StartRunRequest) -> RunSummary:
        run = await self._store.create_run(
            question=request.question,
            client_id=request.client_id,
            client_context=request.client_context,
        )
        task = asyncio.create_task(self._run_pipeline(run.id, request), name=f"keystone-{run.id}")
        self._tasks[run.id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run.id, None))
        return run

    async def stop(self, run_id: str) -> bool:
        run = await self._store.get_summary(run_id)
        if run is None or run.status in {RunStatus.COMPLETE, RunStatus.FAILED}:
            return False

        await self._store.mark_stopping(run_id)
        task = self._tasks.get(run_id)
        if task is None or task.done():
            return False
        task.cancel()
        return True

    async def resume(self, run_id: str, request: StartRunRequest) -> RunSummary | None:
        """Resume a failed/paused run from its last checkpoint."""
        run = await self._store.get_summary(run_id)
        if run is None:
            return None
        task = asyncio.create_task(
            self._resume_pipeline(run_id, request), name=f"keystone-resume-{run_id}"
        )
        self._tasks[run_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(run_id, None))
        return run

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_pipeline(self, run_id: str, request: StartRunRequest) -> None:
        pipeline = self._build_pipeline()
        await self._store.mark_started(run_id)
        event_count = 0
        try:
            async for event in pipeline.run_with_events(
                request.question,
                request.client_id,
                request.client_context,
            ):
                event_count += 1
                await self._store.append_event(run_id, envelope_from_event(event))

            await self._store.mark_rendering(run_id)
            result = await pipeline.get_result()
            result = result.model_copy(update={"total_events": event_count})
            await self._store.complete_run(run_id, result)
        except asyncio.CancelledError:
            await self._store.mark_stopped(run_id)
        except Exception as exc:  # noqa: BLE001 - server boundary must capture run failures.
            logger.exception("Pipeline run %s failed", run_id)
            await self._store.mark_failed(run_id, _error_from_exception(exc))

    async def _resume_pipeline(self, run_id: str, request: StartRunRequest) -> None:
        pipeline = self._build_pipeline()
        await self._store.mark_started(run_id)
        event_count = 0
        try:
            async for event in pipeline.resume_with_events(
                engagement_id=run_id,
                question=request.question,
                client_id=request.client_id,
                client_context=request.client_context,
            ):
                event_count += 1
                await self._store.append_event(run_id, envelope_from_event(event))

            await self._store.mark_rendering(run_id)
            result = await pipeline.get_result()
            result = result.model_copy(update={"total_events": event_count})
            await self._store.complete_run(run_id, result)
        except asyncio.CancelledError:
            await self._store.mark_stopped(run_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Pipeline resume %s failed", run_id)
            await self._store.mark_failed(run_id, _error_from_exception(exc))

    def _build_pipeline(self) -> Pipeline:
        llm_factory = create_llm_factory(self._config, self._config.pipeline)
        gateway = build_mcp_gateway()
        return Pipeline(
            llm_factory=llm_factory,
            gateway=gateway,
            db_session_factory=None,
            pipeline_config=self._config.pipeline,
            checkpoint_store=self._checkpoint_store,
        )


def _error_from_exception(exc: Exception) -> RunError:
    message = str(exc) or exc.__class__.__name__
    lower = message.lower()
    kind = (
        RunErrorKind.GOVERNANCE_HALT
        if "governance" in lower or "halt" in lower
        else RunErrorKind.EXCEPTION
    )
    return RunError(
        kind=kind,
        message=message,
        detail={"exception_type": exc.__class__.__name__},
    )
