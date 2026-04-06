"""Single research agent executor.

Takes a ResearchTask + EngagementSpec + AgentInstance. Runs an
iterative loop: call tools via gateway -> process results ->
synthesize via LLM -> repeat. Produces StructuredFinding.

Uses LLMCallable for all LLM calls. Tool calls go through MCPGateway.
Satisfies ResearchAgentContract from contracts.py.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.events import (
    AnyPipelineEvent,
    CitationExtracted,
    FindingSynthesized,
    ResearchComplete,
    ResearchStarted,
    SourceFound,
)
from keystone.gateway.mcp_gateway import MCPGateway, ToolCall, ToolResult
from keystone.models.agents import AgentInstance
from keystone.models.citations import Citation, SourceType
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ResearchTask
from keystone.research.context_loader import ContextLoader
from keystone.research.error_recovery import ErrorRecovery
from keystone.research.finding_writer import FindingWriter

logger = logging.getLogger(__name__)

DEFAULT_ROUNDS = 3
MAX_ROUNDS = 5
QUALITY_THRESHOLD = 0.8


def _make_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


class ResearchAgent:
    """Single research agent executor with iterative research loop.

    Iterative loop (default 3 rounds, max 5):
      1. Load JIT context from compiled wiki (round 2+)
      2. Call assigned tools via MCPGateway
      3. Synthesize round findings via LLM
      4. Check stopping criteria

    Stopping criteria (any one terminates):
      - Hard round cap reached
      - Quality threshold met (all confidences >= 0.8)
      - Semantic novelty exhaustion (no new claims in last round)
    """

    def __init__(
        self,
        llm: LLMCallable,
        gateway: MCPGateway,
        *,
        finding_writer: FindingWriter | None = None,
        context_loader: ContextLoader | None = None,
        error_recovery: ErrorRecovery | None = None,
        max_rounds: int = DEFAULT_ROUNDS,
    ) -> None:
        self._llm = llm
        self._gateway = gateway
        self._finding_writer = finding_writer or FindingWriter()
        self._context_loader = context_loader
        self._error_recovery = error_recovery or ErrorRecovery()
        self._max_rounds = min(max_rounds, MAX_ROUNDS)
        self._finding: StructuredFinding | None = None
        # Per-round accumulators
        self._all_claims: list[dict] = []
        self._all_sources: list[dict] = []
        self._round_citations: dict[int, list[Citation]] = {}
        self._tokens_consumed: int = 0
        self._citation_counter: int = 0

    async def execute(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Execute research. Yields L1 pipeline events."""
        eid = agent.engagement_id
        cid = agent.client_id

        yield ResearchStarted(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            task_id=task.id,
        )

        prev_claim_count = 0

        for round_num in range(1, self._max_rounds + 1):
            # --- JIT context loading (round 2+) ---
            wiki_context: list[str] = []
            if self._context_loader and round_num > 1:
                wiki_context = await self._context_loader.load_context(
                    engagement_id=eid,
                    task_id=task.id,
                    round_number=round_num,
                )

            # --- Tool execution ---
            round_cits: list[Citation] = []
            for tool_name in task.assigned_tools:
                try:
                    result = await self._gateway.execute(
                        ToolCall(
                            agent_id=agent.agent_id,
                            tool_name=tool_name,
                            parameters={"query": task.description, "round": round_num},
                            engagement_id=eid,
                            client_id=cid,
                            assigned_tools=task.assigned_tools,
                        )
                    )

                    self._all_sources.append(
                        {"tool": tool_name, "round": round_num, "result": result.result}
                    )
                    self._tokens_consumed += result.tokens_used

                    yield SourceFound(
                        event_id=_make_event_id(),
                        engagement_id=eid,
                        client_id=cid,
                        agent_id=agent.agent_id,
                        url=f"tool://{tool_name}/round_{round_num}",
                        source_type=tool_name,
                        quality_score=0.7,
                    )

                    # Build Citation objects from tool result citations
                    for cit_dict in result.citations:
                        self._citation_counter += 1
                        citation = Citation(
                            citation_id=f"CIT-{self._citation_counter:03d}",
                            engagement_id=eid,
                            client_id=cid,
                            url=cit_dict.get("url", f"tool://{tool_name}"),
                            title=cit_dict.get("title", tool_name),
                            access_date=datetime.now(UTC),
                            source_type=SourceType.REPORT,
                            quality_score=0.7,
                        )
                        round_cits.append(citation)

                        yield CitationExtracted(
                            event_id=_make_event_id(),
                            engagement_id=eid,
                            client_id=cid,
                            agent_id=agent.agent_id,
                            citation_id=citation.citation_id,
                            title=citation.title,
                        )

                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Tool %s failed in round %d for agent %s: %s",
                        tool_name,
                        round_num,
                        agent.agent_id,
                        exc,
                    )

            self._round_citations[round_num] = round_cits

            # --- LLM synthesis ---
            synthesis_prompt = self._build_synthesis_prompt(
                task, spec, agent, round_num, wiki_context
            )
            try:
                raw_response = await retry_llm_call(
                    self._llm,
                    synthesis_prompt,
                    max_retries=3,
                    base_delay=0.01,
                    description=f"synthesis_round_{round_num}",
                )
                round_claims = self._parse_synthesis(raw_response)

                # Attach round citations to each claim
                for claim in round_claims:
                    claim["citations"] = round_cits

                self._all_claims.extend(round_claims)
                self._tokens_consumed += len(synthesis_prompt) // 4

            except RuntimeError:
                logger.error(
                    "Synthesis failed in round %d for agent %s",
                    round_num,
                    agent.agent_id,
                )

            # --- Emit synthesis event ---
            new_claim_count = len(self._all_claims)
            conf_values = [
                c["confidence"] for c in self._all_claims if "confidence" in c
            ]
            conf_range = (
                f"{min(conf_values):.2f}-{max(conf_values):.2f}"
                if conf_values
                else "N/A"
            )

            yield FindingSynthesized(
                event_id=_make_event_id(),
                engagement_id=eid,
                client_id=cid,
                agent_id=agent.agent_id,
                claim_count=new_claim_count,
                confidence_range=conf_range,
            )

            # --- Stopping criteria ---
            if conf_values and min(conf_values) >= QUALITY_THRESHOLD:
                logger.info("Quality threshold met in round %d", round_num)
                break

            if round_num > 1 and new_claim_count == prev_claim_count:
                logger.info("No new claims in round %d, stopping", round_num)
                break

            prev_claim_count = new_claim_count

        # --- Absence report via LLM ---
        absence_report = await self._generate_absence_report(task, spec)

        # --- Build final StructuredFinding ---
        agent_type = (
            agent.definition.research_type.value
            if agent.definition.research_type
            else agent.definition.role.value
        )

        if not self._all_claims:
            msg = (
                f"Agent {agent.agent_id} produced 0 claims for task {task.id} "
                f"after {self._max_rounds} rounds"
            )
            raise RuntimeError(msg)

        self._finding = self._finding_writer.build_finding(
            task_id=task.id,
            agent_id=agent.agent_id,
            engagement_id=eid,
            client_id=cid,
            agent_type=agent_type,
            raw_claims=self._all_claims,
            absence_report=absence_report,
            sources_consulted=len(self._all_sources),
            tokens_consumed=self._tokens_consumed,
        )

        yield ResearchComplete(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            task_id=task.id,
            sources_consulted=len(self._all_sources),
            tokens_consumed=self._tokens_consumed,
            absence_count=len(absence_report),
        )

    async def get_finding(self) -> StructuredFinding:
        """Return the structured finding. Must call execute() first."""
        if self._finding is None:
            msg = "No finding available. Call execute() first."
            raise RuntimeError(msg)
        return self._finding

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_synthesis_prompt(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
        round_num: int,
        wiki_context: list[str],
    ) -> str:
        ctx_section = ""
        if wiki_context:
            ctx_section = "\n\nPrior context:\n" + "\n---\n".join(wiki_context)

        sources_text = json.dumps(
            [s for s in self._all_sources if s["round"] == round_num],
            default=str,
        )

        return (
            f"Task: {task.description}\n"
            f"Round: {round_num}\n"
            f"Anti-confirmatory framing: {task.anti_confirmatory_framing}\n"
            f"Sources this round:\n{sources_text}"
            f"{ctx_section}\n\n"
            "Synthesize findings as JSON array of claims. Each claim:\n"
            '{"text": "...", "evidence": "...", "confidence": 0.0-1.0, '
            '"caveats": ["..."]}\n'
        )

    async def _generate_absence_report(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
    ) -> list[str]:
        prompt = (
            f"Task: {task.description}\n"
            f"Sources consulted: {len(self._all_sources)}\n"
            f"Claims found: {len(self._all_claims)}\n\n"
            "List what was looked for but NOT found. "
            "Return a JSON array of strings.\n"
        )
        try:
            response = await retry_llm_call(
                self._llm,
                prompt,
                max_retries=2,
                base_delay=0.01,
                description="absence_report",
            )
            return self._parse_absence(response)
        except RuntimeError:
            return [f"Unable to generate absence report for task {task.id}"]

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    def _parse_synthesis(self, response: str) -> list[dict]:
        """Parse LLM synthesis response into claim dicts."""
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "claims" in data:
                return data["claims"]
            return [data]
        except json.JSONDecodeError:
            logger.warning("Could not parse synthesis response as JSON")
            return []

    def _parse_absence(self, response: str) -> list[str]:
        """Parse LLM absence report response."""
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return [str(item) for item in data]
            return [str(data)]
        except json.JSONDecodeError:
            return [response.strip()] if response.strip() else []
