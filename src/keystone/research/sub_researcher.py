"""SubResearcher: STANDARD-tier worker for the two-tier L1 pattern.

Receives a SubQuery from LeadResearcher, runs 1-2 rounds of tool
calls via MCPGateway, synthesizes a PartialFinding with sub_id
attribution. All tool calls go through the gateway (auth, rate
limit, circuit breaker preserved).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from keystone.events import (
    AnyPipelineEvent,
    CitationExtracted,
    SourceFound,
    SubAgentCompleted,
)
from keystone.gateway.mcp_gateway import ToolCall
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.citations import Citation, SourceType
from keystone.models.sub_research import PartialClaim, PartialFinding, SubQuery
from keystone.research._prompts import load_prompt

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from keystone.evaluator.retry import LLMCallable
    from keystone.gateway.mcp_gateway import MCPGateway
    from keystone.models.tasks import ModelTier, ResearchTask
    from keystone.research.error_recovery import ErrorRecovery
    from keystone.research.evidence_context import EvidenceContextProvider

logger = logging.getLogger(__name__)

SUB_RESEARCHER_ROUNDS = 2


def _make_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


def _make_citation_id(engagement_id: str, agent_id: str, seq: int) -> str:
    eng_short = engagement_id.replace("-", "").replace("_", "")[:8].upper()
    agt_prefix = agent_id.replace("-", "").replace("_", "")[:4].upper()
    agt_short = agt_prefix + uuid.uuid4().hex[:4].upper()
    return f"CIT-{eng_short}-{agt_short}-{seq:03d}"


class SubResearcher:
    """STANDARD-tier worker that executes one SubQuery.

    Runs 1-2 rounds of gateway tool calls, synthesizes findings
    into a PartialFinding with sub_id-attributed claims. Follows
    the same gateway/citation patterns as ResearchAgent shallow mode.
    """

    def __init__(
        self,
        llm: LLMCallable,
        gateway: MCPGateway,
        *,
        error_recovery: ErrorRecovery | None = None,
        evidence_provider: EvidenceContextProvider | None = None,
        current_tier: ModelTier | None = None,
        max_rounds: int = SUB_RESEARCHER_ROUNDS,
    ) -> None:
        from keystone.models.tasks import ModelTier
        from keystone.research.error_recovery import ErrorRecovery

        self._llm = llm
        self._gateway = gateway
        self._error_recovery = error_recovery or ErrorRecovery()
        self._evidence_provider = evidence_provider
        self._current_tier = current_tier or ModelTier.STANDARD
        self._max_rounds = max_rounds
        self._sources: list[dict] = []
        self._tokens_consumed: int = 0
        self._citation_counter: int = 0

    async def execute(
        self,
        sub_query: SubQuery,
        task: ResearchTask,
        *,
        engagement_id: str,
        client_id: str,
        agent_id: str,
    ) -> AsyncIterator[tuple[PartialFinding | None, list[AnyPipelineEvent]]]:
        """Run the sub-query and yield (result, events).

        Single-yield async generator so the caller gets both the
        PartialFinding and the observability events in one shot.
        """
        events: list[AnyPipelineEvent] = []
        all_claims: list[dict] = []

        for round_num in range(1, self._max_rounds + 1):
            round_cits: list[Citation] = []

            for tool_name in sub_query.allowed_tools:
                try:
                    result = await self._gateway.execute(
                        ToolCall(
                            agent_id=agent_id,
                            tool_name=tool_name,
                            parameters={
                                "query": sub_query.objective,
                                "round": round_num,
                            },
                            engagement_id=engagement_id,
                            client_id=client_id,
                            assigned_tools=sub_query.allowed_tools,
                        )
                    )
                    self._sources.append(
                        {"tool": tool_name, "round": round_num, "result": result.result}
                    )
                    self._tokens_consumed += result.tokens_used

                    events.append(
                        SourceFound(
                            event_id=_make_event_id(),
                            engagement_id=engagement_id,
                            client_id=client_id,
                            agent_id=agent_id,
                            url=f"tool://{tool_name}/sub_{sub_query.sub_id}/round_{round_num}",
                            source_type=tool_name,
                            quality_score=0.7,
                        )
                    )

                    for cit_dict in result.citations:
                        self._citation_counter += 1
                        citation = Citation(
                            citation_id=_make_citation_id(
                                engagement_id, agent_id, self._citation_counter
                            ),
                            engagement_id=engagement_id,
                            client_id=client_id,
                            url=cit_dict.get("url", f"tool://{tool_name}"),
                            title=cit_dict.get("title", tool_name),
                            content_snippet=cit_dict.get("text"),
                            access_date=datetime.now(UTC),
                            source_type=SourceType.REPORT,
                            quality_score=0.7,
                        )
                        round_cits.append(citation)

                        events.append(
                            CitationExtracted(
                                event_id=_make_event_id(),
                                engagement_id=engagement_id,
                                client_id=client_id,
                                agent_id=agent_id,
                                citation_id=citation.citation_id,
                                title=citation.title,
                            )
                        )

                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Tool %s failed in sub-researcher %s round %d: %s",
                        tool_name,
                        sub_query.sub_id,
                        round_num,
                        exc,
                    )

            citation_table = {f"SRC-{i + 1:03d}": cit for i, cit in enumerate(round_cits)}

            synthesis_prompt = self._build_synthesis_prompt(
                sub_query, task, round_num, citation_table
            )

            try:
                raw_response = await self._error_recovery.execute_with_recovery(
                    self._llm,
                    synthesis_prompt,
                    current_tier=self._current_tier,
                    description=f"sub_synthesis_{sub_query.sub_id}_round_{round_num}",
                )
                round_claims = self._parse_synthesis(raw_response)

                filtered = self._filter_claims_with_refs(round_claims, citation_table)
                all_claims.extend(filtered)
                self._tokens_consumed += len(synthesis_prompt) // 4

            except RuntimeError:
                logger.error(
                    "Synthesis failed for sub-researcher %s round %d",
                    sub_query.sub_id,
                    round_num,
                )

        partial_claims = [
            PartialClaim(
                text=c["text"],
                evidence=c.get("evidence", ""),
                citation_refs=c.get("citation_refs", []),
                confidence=c.get("confidence", 0.5),
                caveats=c.get("caveats", []),
                sub_id=sub_query.sub_id,
            )
            for c in all_claims
        ]

        finding = PartialFinding(
            sub_id=sub_query.sub_id,
            task_id=task.id,
            methodology=sub_query.methodology,
            claims=partial_claims,
            sources_consulted=len(self._sources),
            tokens_consumed=self._tokens_consumed,
        )

        events.append(
            SubAgentCompleted(
                event_id=_make_event_id(),
                engagement_id=engagement_id,
                client_id=client_id,
                task_id=task.id,
                sub_id=sub_query.sub_id,
                status="success",
                n_claims=len(partial_claims),
                sources_consulted=len(self._sources),
                tokens_consumed=self._tokens_consumed,
            )
        )

        yield finding, events

    def _build_synthesis_prompt(
        self,
        sub_query: SubQuery,
        task: ResearchTask,
        round_num: int,
        citation_table: dict[str, Citation],
    ) -> str:
        if citation_table:
            src_lines = "\n".join(
                f"- {ref} | {cit.title} | {cit.url}"
                + (f" | {cit.content_snippet[:120]}" if cit.content_snippet else "")
                for ref, cit in citation_table.items()
            )
            sources_section = f"Sources this round (use refs in citation_refs):\n{src_lines}"
        else:
            sources_text = json.dumps(
                [s for s in self._sources if s.get("round") == round_num],
                default=str,
            )
            sources_section = f"Sources this round:\n{sources_text}"

        return load_prompt(
            "sub_synthesis",
            task_description=task.description,
            sub_objective=sub_query.objective,
            methodology=sub_query.methodology,
            round_number=str(round_num),
            anti_confirmatory_framing=sub_query.anti_confirmatory_framing,
            output_focus=sub_query.output_focus,
            sources_section=sources_section,
            evidence_section="",
            ref_guidance="the SRC-NNN refs",
        )

    def _parse_synthesis(self, response: str) -> list[dict]:
        try:
            data = safe_llm_json(response, expect_list=True)
            return data
        except ParseError:
            pass
        try:
            data = safe_llm_json(response)
            if "claims" in data:
                return data["claims"]
            return [data]
        except ParseError:
            logger.warning("Could not parse sub-researcher synthesis as JSON")
            return []

    def _filter_claims_with_refs(
        self,
        raw_claims: list[dict],
        citation_table: dict[str, Citation],
    ) -> list[dict]:
        """Keep only claims with valid citation_refs."""
        result = []
        for claim in raw_claims:
            refs = claim.get("citation_refs", [])
            if not refs:
                logger.debug(
                    "Sub-researcher dropping claim (no citation_refs): %.80s",
                    claim.get("text", ""),
                )
                continue
            valid_refs = [r for r in refs if r in citation_table]
            if not valid_refs:
                logger.debug(
                    "Sub-researcher dropping claim (no valid refs): %.80s",
                    claim.get("text", ""),
                )
                continue
            claim["citation_refs"] = valid_refs
            result.append(claim)
        return result
