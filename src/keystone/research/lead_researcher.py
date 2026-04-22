"""LeadResearcher: FLAGSHIP-tier orchestrator for the two-tier L1 pattern.

Decomposes a ResearchTask into 3 SubQuery objects with distinct
methodologies, dispatches SubResearcher workers in parallel via
asyncio.gather, and merges their PartialFinding outputs into one
StructuredFinding. The Lead never calls tools — FLAGSHIP tokens
stay on planning and synthesis only.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from keystone.events import (
    AnyPipelineEvent,
    FindingSynthesized,
    PartialFindingMerged,
    ResearchComplete,
    ResearchStarted,
    SubAgentCompleted,
    SubAgentDispatched,
)
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.models.sub_research import PartialFinding, SubQuery
from keystone.research._prompts import load_prompt
from keystone.research.sub_researcher import SubResearcher

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from keystone.evaluator.retry import LLMCallable
    from keystone.gateway.mcp_gateway import MCPGateway
    from keystone.models.agents import AgentInstance
    from keystone.models.citations import Citation
    from keystone.models.research import EngagementSpec, StructuredFinding
    from keystone.models.tasks import ModelTier, ResearchTask
    from keystone.research.error_recovery import ErrorRecovery
    from keystone.research.evidence_context import EvidenceContextProvider
    from keystone.research.finding_writer import FindingWriter

logger = logging.getLogger(__name__)

PHASE_1_N = 3


def _make_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


class LeadResearcher:
    """FLAGSHIP-tier orchestrator for hierarchical research dispatch.

    Three responsibilities, no tool access:
    1. Decompose task into N methodologically-distinct SubQuery objects
    2. Dispatch SubResearchers in parallel (asyncio.gather)
    3. Synthesize PartialFindings into one StructuredFinding

    Follows the execute() -> get_finding() contract so AgentPool
    can use it interchangeably with ResearchAgent.
    """

    def __init__(
        self,
        flagship_llm: LLMCallable,
        standard_llm: LLMCallable,
        gateway: MCPGateway,
        *,
        error_recovery: ErrorRecovery | None = None,
        evidence_provider: EvidenceContextProvider | None = None,
        finding_writer: FindingWriter | None = None,
        flagship_tier: ModelTier | None = None,
        standard_tier: ModelTier | None = None,
        max_sub_agents: int = PHASE_1_N,
        sub_agent_timeout_s: int = 300,
    ) -> None:
        from keystone.models.tasks import ModelTier
        from keystone.research.error_recovery import ErrorRecovery
        from keystone.research.finding_writer import FindingWriter

        self._flagship_llm = flagship_llm
        self._standard_llm = standard_llm
        self._gateway = gateway
        self._error_recovery = error_recovery or ErrorRecovery()
        self._evidence_provider = evidence_provider
        self._finding_writer = finding_writer or FindingWriter()
        self._flagship_tier = flagship_tier or ModelTier.FLAGSHIP
        self._standard_tier = standard_tier or ModelTier.STANDARD
        self._max_sub_agents = max_sub_agents
        self._sub_agent_timeout_s = sub_agent_timeout_s
        self._finding: StructuredFinding | None = None

    async def execute(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Execute hierarchical research. Yields L1 pipeline events."""
        eid = agent.engagement_id
        cid = agent.client_id

        yield ResearchStarted(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            task_id=task.id,
        )

        # Phase 1: Plan sub-queries (1 FLAGSHIP call)
        sub_queries = await self._plan_subqueries(task, spec)

        # Emit dispatch events
        for sq in sub_queries:
            yield SubAgentDispatched(
                event_id=_make_event_id(),
                engagement_id=eid,
                client_id=cid,
                task_id=task.id,
                sub_id=sq.sub_id,
                methodology=sq.methodology,
            )

        # Phase 2: Dispatch SubResearchers in parallel
        partials, sub_events = await self._dispatch_sub_researchers(sub_queries, task, spec, agent)

        # Yield all sub-agent events
        for event in sub_events:
            yield event

        # Phase 3: Synthesize (1 FLAGSHIP call) — or fallback
        if not partials:
            logger.warning(
                "All sub-agents failed for task %s — cannot synthesize",
                task.id,
            )
            raise _AllSubAgentsFailedError(task.id)

        self._finding = await self._synthesize(partials, task, spec, agent)

        total_sources = sum(p.sources_consulted for p in partials)
        total_tokens = sum(p.tokens_consumed for p in partials)

        conf_values = [c.confidence for c in self._finding.claims] if self._finding else []
        conf_range = f"{min(conf_values):.2f}-{max(conf_values):.2f}" if conf_values else "N/A"
        yield FindingSynthesized(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            claim_count=len(self._finding.claims) if self._finding else 0,
            confidence_range=conf_range,
        )

        n_contradictions = 0
        for claim in self._finding.claims if self._finding else []:
            if claim.caveats and any("contradict" in c.lower() for c in claim.caveats):
                n_contradictions += 1

        yield PartialFindingMerged(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            task_id=task.id,
            n_sub_findings=len(partials),
            n_total_claims=len(self._finding.claims) if self._finding else 0,
            n_contradictions=n_contradictions,
            n_unique_sources=total_sources,
        )

        yield ResearchComplete(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            task_id=task.id,
            sources_consulted=total_sources,
            tokens_consumed=total_tokens,
            absence_count=len(self._finding.absence_report) if self._finding else 0,
        )

    async def get_finding(self) -> StructuredFinding:
        if self._finding is None:
            msg = "No finding available. Call execute() first."
            raise RuntimeError(msg)
        return self._finding

    # ------------------------------------------------------------------
    # Phase 1: Plan sub-queries
    # ------------------------------------------------------------------

    async def _plan_subqueries(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
    ) -> list[SubQuery]:
        engagement_context = (
            f"Title: {spec.research_spec.title}\n"
            f"Decision Context: {spec.research_spec.decision_context}"
        )

        prompt = load_prompt(
            "plan_subqueries",
            task_description=task.description,
            engagement_context=engagement_context,
            anti_confirmatory_framing=task.anti_confirmatory_framing,
            available_tools=", ".join(task.assigned_tools),
        )

        raw = await self._error_recovery.execute_with_recovery(
            self._flagship_llm,
            prompt,
            current_tier=self._flagship_tier,
            description="plan_subqueries",
        )

        return self._parse_subqueries(raw, task)

    def _parse_subqueries(self, raw: str, task: ResearchTask) -> list[SubQuery]:
        try:
            data = safe_llm_json(raw, expect_list=True)
        except ParseError:
            try:
                wrapper = safe_llm_json(raw)
                data = wrapper.get("sub_queries", wrapper.get("subqueries", []))
            except ParseError:
                logger.error("Could not parse plan_subqueries response")
                raise

        n = self._max_sub_agents
        sub_queries = []
        for i, item in enumerate(data[:n]):
            sq = SubQuery(
                sub_id=item.get("sub_id", f"SUB-{i + 1:03d}"),
                objective=item["objective"],
                methodology=item.get("methodology", "market_intelligence"),
                allowed_tools=self._validate_tools(
                    item.get("allowed_tools", task.assigned_tools[:2]),
                    task.assigned_tools,
                ),
                anti_confirmatory_framing=item.get(
                    "anti_confirmatory_framing",
                    f"Evaluate the strength of evidence for and against: {item['objective']}",
                ),
                stop_criterion=item.get(
                    "stop_criterion",
                    "3+ independent sources corroborate or contradict",
                ),
                output_focus=item.get("output_focus", "specific factual claims with data"),
            )
            sub_queries.append(sq)

        if len(sub_queries) < n:
            logger.warning(
                "Plan produced %d sub-queries, expected %d. Padding with tool-split fallback.",
                len(sub_queries),
                n,
            )
            sub_queries = self._pad_subqueries(sub_queries, task)

        return sub_queries[:n]

    def _validate_tools(self, requested: list[str], available: list[str]) -> list[str]:
        """Ensure sub-query tools are a subset of the parent task's tools."""
        valid = [t for t in requested if t in available]
        if not valid:
            return available[:2]
        return valid

    def _pad_subqueries(self, existing: list[SubQuery], task: ResearchTask) -> list[SubQuery]:
        """Fill missing sub-queries by splitting tools across methodologies."""
        tools = task.assigned_tools
        n = self._max_sub_agents
        methodologies = ["financial_data", "market_intelligence", "academic_technical"]

        while len(existing) < n:
            idx = len(existing)
            method = methodologies[idx % len(methodologies)]
            tool_start = (idx * len(tools)) // n
            tool_end = ((idx + 1) * len(tools)) // n
            sub_tools = tools[tool_start:tool_end] or tools[:1]

            existing.append(
                SubQuery(
                    sub_id=f"SUB-{idx + 1:03d}",
                    objective=f"Investigate {task.description} through {method} lens",
                    methodology=method,
                    allowed_tools=sub_tools,
                    anti_confirmatory_framing=(
                        f"Evaluate the strength of evidence for and against "
                        f"the claims emerging from {method} analysis"
                    ),
                    stop_criterion="3+ independent sources corroborate or contradict",
                    output_focus="specific factual claims with data",
                )
            )
        return existing

    # ------------------------------------------------------------------
    # Phase 2: Dispatch sub-researchers
    # ------------------------------------------------------------------

    async def _dispatch_sub_researchers(
        self,
        sub_queries: list[SubQuery],
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> tuple[list[PartialFinding], list[AnyPipelineEvent]]:
        eid = agent.engagement_id
        cid = agent.client_id

        async def run_one(sq: SubQuery) -> tuple[PartialFinding | None, list[AnyPipelineEvent]]:
            sub_agent_id = f"{agent.agent_id}_sub_{sq.sub_id.lower().replace('-', '_')}"
            sub = SubResearcher(
                llm=self._standard_llm,
                gateway=self._gateway,
                error_recovery=self._error_recovery,
                evidence_provider=self._evidence_provider,
                current_tier=self._standard_tier,
            )
            try:
                async for finding, events in sub.execute(
                    sq,
                    task,
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=sub_agent_id,
                ):
                    return finding, events
                return None, []
            except Exception as exc:  # noqa: BLE001
                logger.error("SubResearcher %s failed: %s", sq.sub_id, exc)
                return None, [
                    SubAgentCompleted(
                        event_id=_make_event_id(),
                        engagement_id=eid,
                        client_id=cid,
                        task_id=task.id,
                        sub_id=sq.sub_id,
                        status="error",
                    )
                ]

        timeout = self._sub_agent_timeout_s

        async def run_with_timeout(
            sq: SubQuery,
        ) -> tuple[PartialFinding | None, list[AnyPipelineEvent]]:
            try:
                return await asyncio.wait_for(run_one(sq), timeout=timeout)
            except TimeoutError:
                logger.error("SubResearcher %s timed out after %ds", sq.sub_id, timeout)
                return None, [
                    SubAgentCompleted(
                        event_id=_make_event_id(),
                        engagement_id=eid,
                        client_id=cid,
                        task_id=task.id,
                        sub_id=sq.sub_id,
                        status="timeout",
                    )
                ]

        results = await asyncio.gather(
            *(run_with_timeout(sq) for sq in sub_queries),
            return_exceptions=True,
        )

        partials: list[PartialFinding] = []
        all_events: list[AnyPipelineEvent] = []

        for result in results:
            if isinstance(result, BaseException):
                logger.error("Sub-agent gather exception: %s", result)
                continue
            finding, events = result
            all_events.extend(events)
            if finding is not None and finding.claims:
                partials.append(finding)

        return partials, all_events

    # ------------------------------------------------------------------
    # Phase 3: Synthesize
    # ------------------------------------------------------------------

    async def _synthesize(
        self,
        partials: list[PartialFinding],
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> StructuredFinding:
        sub_findings_block, master_citations = self._render_partials_for_prompt(partials)

        engagement_context = (
            f"Title: {spec.research_spec.title}\n"
            f"Decision Context: {spec.research_spec.decision_context}"
        )

        prompt = load_prompt(
            "lead_synthesis",
            task_description=task.description,
            anti_confirmatory_framing=task.anti_confirmatory_framing,
            engagement_context=engagement_context,
            n_sub_agents=str(len(partials)),
            sub_findings_block=sub_findings_block,
        )

        raw = await self._error_recovery.execute_with_recovery(
            self._flagship_llm,
            prompt,
            current_tier=self._flagship_tier,
            description="lead_synthesis",
        )

        return self._build_finding_from_merge(raw, partials, task, agent, master_citations)

    def _render_partials_for_prompt(
        self, partials: list[PartialFinding]
    ) -> tuple[str, dict[str, Citation]]:
        """Render partials for the synthesis prompt.

        Re-numbers SRC-NNN refs globally across all sub-agents so the
        Lead's LLM sees a single flat namespace. Returns the rendered
        block and a master citation map for ref resolution at merge.
        """
        blocks: list[str] = []
        master_citations: dict[str, Citation] = {}
        global_counter = 0

        for p in partials:
            ref_remap: dict[str, str] = {}
            for old_ref, citation in p.citations.items():
                global_counter += 1
                new_ref = f"SRC-{global_counter:03d}"
                ref_remap[old_ref] = new_ref
                master_citations[new_ref] = citation

            claims_text = "\n".join(
                f"  - [{c.confidence:.2f}] {c.text} "
                f"(refs: {', '.join(ref_remap.get(r, r) for r in c.citation_refs)})"
                for c in p.claims
            )
            absence_text = "\n".join(f"  - {a}" for a in p.absence_items) or "  (none)"
            blocks.append(
                f"=== {p.sub_id} ({p.methodology}) — {len(p.claims)} claims, "
                f"{p.sources_consulted} sources ===\n"
                f"Claims:\n{claims_text}\n"
                f"Absence items:\n{absence_text}"
            )
        return "\n\n".join(blocks), master_citations

    def _build_finding_from_merge(
        self,
        raw: str,
        partials: list[PartialFinding],
        task: ResearchTask,
        agent: AgentInstance,
        master_citations: dict[str, Citation] | None = None,
    ) -> StructuredFinding:
        import re
        from datetime import UTC, datetime

        from keystone.models.citations import Citation, SourceType
        from keystone.models.research import FindingClaim, FindingStatus, StructuredFinding
        from keystone.research.finding_writer import _tier_from_confidence

        if master_citations is None:
            master_citations = {}
            for p in partials:
                master_citations.update(p.citations)

        try:
            data = safe_llm_json(raw)
        except ParseError:
            logger.error("Could not parse lead_synthesis response — falling back to raw collation")
            data = self._raw_collation_fallback(partials)

        raw_claims = data.get("claims", [])
        absence_report = data.get("absence_report", [])
        status_str = data.get("status", "complete")

        status_map = {
            "complete": FindingStatus.COMPLETE,
            "partial": FindingStatus.PARTIAL,
            "gap_found": FindingStatus.GAP_FOUND,
        }
        finding_status = status_map.get(status_str, FindingStatus.COMPLETE)

        agent_type = (
            agent.definition.research_type.value
            if agent.definition.research_type
            else agent.definition.role.value
        )

        sub_ref_pattern = re.compile(r"^SUB-\d{3}$")
        finding_claims: list[FindingClaim] = []
        dropped: list[dict] = []

        for i, rc in enumerate(raw_claims):
            refs = [r for r in rc.get("citation_refs", []) if not sub_ref_pattern.match(r)]
            if not refs:
                dropped.append({"index": i, "text": rc.get("text", ""), "reasons": ["no refs"]})
                continue

            resolved: list[Citation] = []
            for ref in refs:
                if ref in master_citations:
                    resolved.append(master_citations[ref])
                else:
                    resolved.append(
                        Citation(
                            citation_id=f"CIT-MERGE-{uuid.uuid4().hex[:8]}",
                            engagement_id=agent.engagement_id,
                            client_id=agent.client_id,
                            url=f"unresolved://{ref}",
                            title=ref,
                            access_date=datetime.now(UTC),
                            source_type=SourceType.REPORT,
                            quality_score=0.3,
                        )
                    )

            caveats = rc.get("caveats", [])
            contradiction_note = rc.get("contradiction_note")
            if contradiction_note:
                caveats.append(f"Contradiction: {contradiction_note}")

            confidence = rc.get("confidence", 0.5)

            finding_claims.append(
                FindingClaim(
                    text=rc["text"],
                    evidence=rc.get("evidence", ""),
                    citations=resolved,
                    confidence=confidence,
                    confidence_tier=_tier_from_confidence(confidence),
                    caveats=caveats,
                    claim_id=f"{agent.engagement_id}_{task.id}_{uuid.uuid4().hex[:8]}",
                    citation_ids=[c.citation_id for c in resolved],
                )
            )

        if not finding_claims:
            logger.warning("Lead synthesis produced 0 valid claims — using raw collation")
            return self._build_raw_collation_finding(partials, task, agent, master_citations)

        total_sources = sum(p.sources_consulted for p in partials)
        total_tokens = sum(p.tokens_consumed for p in partials)

        return StructuredFinding(
            task_id=task.id,
            agent_id=agent.agent_id,
            engagement_id=agent.engagement_id,
            client_id=agent.client_id,
            agent_type=agent_type,
            claims=finding_claims,
            status=finding_status,
            absence_report=absence_report or ["No absences identified across sub-agents"],
            sources_consulted=total_sources,
            tokens_consumed=total_tokens,
            dropped_claims=dropped,
        )

    def _raw_collation_fallback(self, partials: list[PartialFinding]) -> dict:
        """Fallback when LLM synthesis parse fails: collate claims directly."""
        claims = []
        absence = []
        for p in partials:
            for c in p.claims:
                claims.append(
                    {
                        "text": c.text,
                        "evidence": c.evidence,
                        "citation_refs": c.citation_refs,
                        "confidence": c.confidence,
                        "caveats": c.caveats,
                    }
                )
            absence.extend(p.absence_items)
        return {"claims": claims, "absence_report": absence, "status": "partial"}

    def _build_raw_collation_finding(
        self,
        partials: list[PartialFinding],
        task: ResearchTask,
        agent: AgentInstance,
        master_citations: dict[str, Citation] | None = None,
    ) -> StructuredFinding:
        """Emergency fallback: turn partials directly into a StructuredFinding."""
        data = self._raw_collation_fallback(partials)
        from datetime import UTC, datetime

        from keystone.models.citations import Citation, SourceType
        from keystone.models.research import FindingClaim, FindingStatus, StructuredFinding
        from keystone.research.finding_writer import _tier_from_confidence

        if master_citations is None:
            master_citations = {}
            for p in partials:
                master_citations.update(p.citations)

        agent_type = (
            agent.definition.research_type.value
            if agent.definition.research_type
            else agent.definition.role.value
        )

        claims = []
        for rc in data["claims"]:
            refs = rc.get("citation_refs", [])
            resolved: list[Citation] = []
            for ref in refs:
                if ref in master_citations:
                    resolved.append(master_citations[ref])
                else:
                    resolved.append(
                        Citation(
                            citation_id=f"CIT-RAW-{uuid.uuid4().hex[:8]}",
                            engagement_id=agent.engagement_id,
                            client_id=agent.client_id,
                            url=f"unresolved://{ref}",
                            title=ref,
                            access_date=datetime.now(UTC),
                            source_type=SourceType.REPORT,
                            quality_score=0.3,
                        )
                    )
            confidence = rc.get("confidence", 0.5)
            claims.append(
                FindingClaim(
                    text=rc["text"],
                    evidence=rc.get("evidence", ""),
                    citations=resolved,
                    confidence=confidence,
                    confidence_tier=_tier_from_confidence(confidence),
                    caveats=rc.get("caveats", []),
                    claim_id=f"{agent.engagement_id}_{task.id}_{uuid.uuid4().hex[:8]}",
                    citation_ids=[c.citation_id for c in resolved],
                )
            )

        return StructuredFinding(
            task_id=task.id,
            agent_id=agent.agent_id,
            engagement_id=agent.engagement_id,
            client_id=agent.client_id,
            agent_type=agent_type,
            claims=claims,
            status=FindingStatus.PARTIAL,
            absence_report=data.get(
                "absence_report", ["Raw collation fallback — absences unknown"]
            ),
            sources_consulted=sum(p.sources_consulted for p in partials),
            tokens_consumed=sum(p.tokens_consumed for p in partials),
        )


class _AllSubAgentsFailedError(Exception):
    """All sub-agents failed — caller should fall back to single-agent path."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"All sub-agents failed for task {task_id}")
