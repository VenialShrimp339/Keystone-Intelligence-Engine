"""Parallel agent manager for L1 research.

Spawns N research agents concurrently. Collects results.
Handles partial-result continuation: if K of N agents succeed,
combines their results and retries failures.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from keystone.evaluator.retry import LLMCallable
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.models.agents import AgentInstance
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ResearchTask
from keystone.research.context_loader import ContextLoader
from keystone.research.error_recovery import ErrorRecovery
from keystone.research.finding_writer import FindingWriter
from keystone.research.research_agent import ResearchAgent

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from a single agent execution."""

    agent_id: str
    task_id: str
    finding: StructuredFinding | None = None
    error: Exception | None = None
    events: list = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.finding is not None and self.error is None


class AgentPool:
    """Parallel agent manager with partial-result continuation.

    Spawns N research agents concurrently. On mixed results
    (K of N succeed), combines successful findings and retries
    failures up to max_retries times.
    """

    def __init__(
        self,
        llm: LLMCallable,
        gateway: MCPGateway,
        *,
        finding_writer: FindingWriter | None = None,
        context_loader: ContextLoader | None = None,
        error_recovery: ErrorRecovery | None = None,
        max_retries: int = 1,
    ) -> None:
        self._llm = llm
        self._gateway = gateway
        self._finding_writer = finding_writer or FindingWriter()
        self._context_loader = context_loader
        self._error_recovery = error_recovery
        self._max_retries = max_retries

    async def execute_all(
        self,
        assignments: list[tuple[ResearchTask, EngagementSpec, AgentInstance]],
    ) -> list[AgentResult]:
        """Execute all agent assignments concurrently.

        Returns AgentResult for each assignment. Retries failures
        up to max_retries times while preserving successful results.
        """
        results = await self._run_batch(assignments)

        for retry_num in range(self._max_retries):
            failed = [
                (i, assignments[i])
                for i, r in enumerate(results)
                if not r.success
            ]
            if not failed:
                break

            logger.info(
                "Retrying %d failed agents (attempt %d/%d)",
                len(failed),
                retry_num + 1,
                self._max_retries,
            )

            retry_assignments = [a for _, a in failed]
            retry_results = await self._run_batch(retry_assignments)

            for (orig_idx, _), retry_result in zip(failed, retry_results):
                if retry_result.success:
                    results[orig_idx] = retry_result

        return results

    async def _run_batch(
        self,
        assignments: list[tuple[ResearchTask, EngagementSpec, AgentInstance]],
    ) -> list[AgentResult]:
        """Run a batch of agent assignments concurrently."""
        coros = [
            self._run_single(task, spec, agent)
            for task, spec, agent in assignments
        ]
        return list(await asyncio.gather(*coros))

    async def _run_single(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AgentResult:
        """Run a single agent, catching any exceptions."""
        research_agent = ResearchAgent(
            llm=self._llm,
            gateway=self._gateway,
            finding_writer=self._finding_writer,
            context_loader=self._context_loader,
            error_recovery=self._error_recovery,
        )

        events: list = []
        try:
            async for event in research_agent.execute(task, spec, agent):
                events.append(event)

            finding = await research_agent.get_finding()
            return AgentResult(
                agent_id=agent.agent_id,
                task_id=task.id,
                finding=finding,
                events=events,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Agent %s failed on task %s: %s",
                agent.agent_id,
                task.id,
                exc,
            )
            return AgentResult(
                agent_id=agent.agent_id,
                task_id=task.id,
                error=exc,
                events=events,
            )

    def get_successful_findings(
        self, results: list[AgentResult]
    ) -> list[StructuredFinding]:
        """Extract findings from successful results."""
        return [r.finding for r in results if r.success and r.finding is not None]

    def get_failed_agents(self, results: list[AgentResult]) -> list[AgentResult]:
        """Get agents that failed all attempts."""
        return [r for r in results if not r.success]
