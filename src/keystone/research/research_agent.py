"""Single research agent executor.

Takes a ResearchTask + EngagementSpec + AgentInstance. Runs an
iterative loop: call tools via gateway -> process results ->
synthesize via LLM -> repeat. Produces StructuredFinding.

Two execution modes:
  * **Shallow** (default): Iterative tool calls via MCPGateway + LLM
    synthesis rounds. Fast (~60s) but snippet-level depth.
  * **Deep** (when deep_llm provided): Single ``claude -p`` call with
    WebSearch + WebFetch tools. Multi-turn web research producing
    20+ claims with real source URLs. 5-10 minutes per task.

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
from keystone.llm.parsing import ParseError, safe_llm_json
from keystone.events import (
    AnyPipelineEvent,
    CitationExtracted,
    FindingSynthesized,
    ResearchComplete,
    ResearchStarted,
    SourceFound,
)
from keystone.gateway.mcp_gateway import MCPGateway, ToolCall
from keystone.models.agents import AgentInstance
from keystone.models.citations import Citation, SourceType
from keystone.models.research import EngagementSpec, StructuredFinding
from keystone.models.tasks import ResearchTask
from keystone.research.context_loader import ContextLoader
from keystone.research.error_recovery import ErrorRecovery
from keystone.research.evidence_context import (
    EvidenceContextProvider,
    evidence_to_citation,
)
from keystone.research.finding_writer import FindingWriter
from keystone.retrieval.parse_models import EvidencePrepRecord

logger = logging.getLogger(__name__)

# Source type inference from URL domain
_SOURCE_TYPE_PATTERNS: list[tuple[str, SourceType]] = [
    ("sec.gov", SourceType.FILING),
    ("edgar", SourceType.FILING),
    (".gov", SourceType.GOVERNMENT),
    ("arxiv.org", SourceType.ACADEMIC),
    ("scholar.google", SourceType.ACADEMIC),
    ("doi.org", SourceType.ACADEMIC),
    ("pubmed", SourceType.ACADEMIC),
    ("reuters", SourceType.NEWS),
    ("bloomberg", SourceType.NEWS),
    ("wsj.com", SourceType.NEWS),
    ("ft.com", SourceType.NEWS),
    ("cnbc.com", SourceType.NEWS),
    ("techcrunch", SourceType.NEWS),
]


def _infer_source_type(url: str) -> SourceType:
    """Infer SourceType from URL domain patterns."""
    lower = url.lower()
    for pattern, stype in _SOURCE_TYPE_PATTERNS:
        if pattern in lower:
            return stype
    return SourceType.REPORT


DEFAULT_ROUNDS = 3
MAX_ROUNDS = 5
QUALITY_THRESHOLD = 0.8


def _make_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


def _make_source_instance_id(engagement_id: str, agent_id: str, seq: int) -> str:
    """Generate engagement-unique source-instance citation ID.

    Format: CIT-{engagement_short}-{agent_uuid_prefix}-{seq:03d}
    Satisfies the CIT- validator. Unique across parallel agents because a
    per-agent uuid segment is embedded -- pure truncation collides for agents
    with common prefixes (e.g., agent_alpha_1 vs agent_alpha_2).
    """
    eng_short = engagement_id.replace("-", "").replace("_", "")[:8].upper()
    # First 4 chars of agent_id (stripped) + 4 uuid hex chars = collision-safe 8-char segment
    agt_prefix = agent_id.replace("-", "").replace("_", "")[:4].upper()
    agt_short = agt_prefix + uuid.uuid4().hex[:4].upper()
    return f"CIT-{eng_short}-{agt_short}-{seq:03d}"


class ResearchAgent:
    """Single research agent executor with iterative research loop.

    Two modes:
      * **Shallow** (deep_llm=None): Iterative gateway-based rounds.
      * **Deep** (deep_llm provided): Single claude -p call with web
        search tools. Produces 20+ claims with real source URLs.

    Shallow iterative loop (default 3 rounds, max 5):
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
        deep_llm: LLMCallable | None = None,
        finding_writer: FindingWriter | None = None,
        context_loader: ContextLoader | None = None,
        error_recovery: ErrorRecovery | None = None,
        evidence_provider: EvidenceContextProvider | None = None,
        max_rounds: int = DEFAULT_ROUNDS,
    ) -> None:
        self._llm = llm
        self._deep_llm = deep_llm
        self._gateway = gateway
        self._finding_writer = finding_writer or FindingWriter()
        self._context_loader = context_loader
        self._error_recovery = error_recovery or ErrorRecovery()
        self._evidence_provider = evidence_provider
        self._max_rounds = min(max_rounds, MAX_ROUNDS)
        self._finding: StructuredFinding | None = None
        # Per-round accumulators
        self._all_claims: list[dict] = []
        self._all_sources: list[dict] = []
        self._round_citations: dict[int, list[Citation]] = {}
        self._tokens_consumed: int = 0
        self._citation_counter: int = 0
        # Per-task evidence state (populated when evidence_provider is present)
        self._evidence_records: list[EvidencePrepRecord] = []
        self._evidence_table: dict[str, EvidencePrepRecord] = {}
        self._evidence_block: str = ""
        self._evidence_citations: dict[str, Citation] = {}

    async def execute(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Execute research. Yields L1 pipeline events.

        Dispatches to deep mode (multi-turn web research) when deep_llm
        is available. Falls back to shallow mode on deep research failure.
        """
        self._prepare_evidence_context(task)

        if self._deep_llm is not None:
            try:
                async for event in self._execute_deep(task, spec, agent):
                    yield event
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Deep research failed for agent %s on task %s: %s. "
                    "Falling back to shallow mode.",
                    agent.agent_id,
                    task.id,
                    exc,
                )
                # Reset state for shallow fallback
                self._all_claims = []
                self._all_sources = []
                self._round_citations = {}
                self._tokens_consumed = 0
                self._citation_counter = 0
                self._finding = None
                self._evidence_citations = {}

        async for event in self._execute_shallow(task, spec, agent):
            yield event

    def _prepare_evidence_context(self, task: ResearchTask) -> None:
        """Build the per-task EV-NNN table before any round runs.

        Noop when no evidence_provider was injected. Caches the rendered
        prompt block so each round reuses it without re-formatting.
        """

        self._evidence_records = []
        self._evidence_table = {}
        self._evidence_block = ""
        self._evidence_citations = {}

        if self._evidence_provider is None:
            return

        records = self._evidence_provider.records_for_task(task)
        if not records:
            return

        self._evidence_records = records
        self._evidence_table = self._evidence_provider.build_reference_table(records)
        self._evidence_block = self._evidence_provider.render_passages_for_prompt(
            self._evidence_table
        )

    async def _execute_deep(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Deep research mode: single multi-turn claude -p call with web tools.

        Builds a comprehensive prompt, runs one claude -p session that
        searches the web, reads pages, follows citations, and outputs
        structured JSON. Parses results through FindingWriter.

        ARCHITECTURE NOTE: Deep mode bypasses MCPGateway. The claude -p
        subprocess uses --allowedTools WebSearch,WebFetch directly, so
        gateway-level auth, rate limiting, circuit breaking, and audit
        logging do not apply. This is a known trade-off: deep mode gets
        multi-turn web research capability at the cost of gateway governance.
        Audit events (SourceFound, CitationExtracted) are still emitted
        from this path for observability. Full gateway integration for deep
        mode is a Phase 2 item -- requires wrapping provider-native tools
        in gateway-owned abstractions.
        """
        assert self._deep_llm is not None
        eid = agent.engagement_id
        cid = agent.client_id

        yield ResearchStarted(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            task_id=task.id,
        )

        # --- Build deep research prompt ---
        prompt = self._build_deep_research_prompt(task, spec, agent)
        logger.info(
            "Deep research: agent %s starting for task %s (prompt: %d chars)",
            agent.agent_id,
            task.id,
            len(prompt),
        )

        # --- Single deep call (5-10 minutes) ---
        raw_response = await self._deep_llm(prompt)
        logger.info(
            "Deep research: agent %s completed (response: %d chars)",
            agent.agent_id,
            len(raw_response),
        )

        # Rough token estimate for the deep session
        self._tokens_consumed = (len(prompt) + len(raw_response)) // 4

        # --- Parse structured output ---
        parsed = self._parse_deep_response(raw_response)
        claims_data = parsed.get("claims", [])
        absence_data = parsed.get("absence_report", [])

        if not claims_data:
            raise RuntimeError(f"Deep research for task {task.id} returned 0 claims")

        # --- Convert claims + sources -> Citation objects + raw_claims ---
        # Deep mode does NOT use the citation_refs pattern from shallow mode.
        # The LLM already returns per-claim `sources` arrays (structurally scoped),
        # so citations are built directly from each claim's sources and attached
        # to that claim. The citation_refs -> SRC-NNN indirection only exists in
        # shallow mode to fix round-broadcast (where all round citations were
        # broadcast to every claim regardless of actual reference).
        for claim_dict in claims_data:
            sources = claim_dict.pop("sources", [])
            citations: list[Citation] = []

            for src in sources:
                self._citation_counter += 1
                url = src.get("url", "")
                citation = Citation(
                    citation_id=_make_source_instance_id(
                        eid, agent.agent_id, self._citation_counter
                    ),
                    engagement_id=eid,
                    client_id=cid,
                    url=url,
                    title=src.get("title", "Web Source"),
                    content_snippet=src.get("content_snippet"),
                    access_date=datetime.now(UTC),
                    source_type=_infer_source_type(url),
                    quality_score=0.7,
                )
                citations.append(citation)
                self._all_sources.append(
                    {"tool": "deep_research", "url": url, "title": citation.title}
                )

                yield SourceFound(
                    event_id=_make_event_id(),
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=agent.agent_id,
                    url=url,
                    source_type="deep_research",
                    quality_score=0.7,
                )
                yield CitationExtracted(
                    event_id=_make_event_id(),
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=agent.agent_id,
                    citation_id=citation.citation_id,
                    title=citation.title,
                )

            claim_dict["citations"] = citations
            # Ensure required fields have defaults
            claim_dict.setdefault("evidence", claim_dict.get("text", ""))
            claim_dict.setdefault("confidence", 0.5)
            claim_dict.setdefault("caveats", [])
            self._all_claims.append(claim_dict)

        # --- Emit synthesis event ---
        conf_values = [c["confidence"] for c in self._all_claims if "confidence" in c]
        conf_range = f"{min(conf_values):.2f}-{max(conf_values):.2f}" if conf_values else "N/A"
        yield FindingSynthesized(
            event_id=_make_event_id(),
            engagement_id=eid,
            client_id=cid,
            agent_id=agent.agent_id,
            claim_count=len(self._all_claims),
            confidence_range=conf_range,
        )

        # --- Absence report ---
        if not absence_data:
            absence_data = await self._generate_absence_report(task, spec)

        # --- Build StructuredFinding ---
        agent_type = (
            agent.definition.research_type.value
            if agent.definition.research_type
            else agent.definition.role.value
        )

        self._finding = self._finding_writer.build_finding(
            task_id=task.id,
            agent_id=agent.agent_id,
            engagement_id=eid,
            client_id=cid,
            agent_type=agent_type,
            raw_claims=self._all_claims,
            absence_report=absence_data,
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
            absence_count=len(absence_data),
        )

    async def _execute_shallow(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Shallow research mode: iterative gateway-based rounds."""
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
                            citation_id=_make_source_instance_id(
                                eid, agent.agent_id, self._citation_counter
                            ),
                            engagement_id=eid,
                            client_id=cid,
                            url=cit_dict.get("url", f"tool://{tool_name}"),
                            title=cit_dict.get("title", tool_name),
                            content_snippet=cit_dict.get("text"),
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

            # Build citation table: SRC-001 -> Citation (for explicit ref attachment)
            round_citation_table = self._build_round_citation_table(round_cits)

            # --- LLM synthesis ---
            synthesis_prompt = self._build_synthesis_prompt(
                task, spec, agent, round_num, wiki_context, round_citation_table
            )
            newly_minted_ev: list[Citation] = []
            try:
                raw_response = await retry_llm_call(
                    self._llm,
                    synthesis_prompt,
                    max_retries=3,
                    base_delay=0.01,
                    description=f"synthesis_round_{round_num}",
                )
                round_claims = self._parse_synthesis(raw_response)

                # Attach only explicitly referenced citations -- no round-broadcast.
                # Resolves both SRC-NNN (tool results) and EV-NNN (parsed evidence).
                round_claims, newly_minted_ev = self._attach_citations_from_refs(
                    round_claims,
                    round_citation_table,
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=agent.agent_id,
                )

                self._all_claims.extend(round_claims)
                self._tokens_consumed += len(synthesis_prompt) // 4

            except RuntimeError:
                logger.error(
                    "Synthesis failed in round %d for agent %s",
                    round_num,
                    agent.agent_id,
                )

            # --- Emit events + source counts for newly-cited parsed evidence ---
            for ev_citation in newly_minted_ev:
                self._all_sources.append(
                    {
                        "tool": "lane_e_evidence",
                        "round": round_num,
                        "citation_id": ev_citation.citation_id,
                        "url": ev_citation.url,
                    }
                )
                yield SourceFound(
                    event_id=_make_event_id(),
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=agent.agent_id,
                    url=ev_citation.url,
                    source_type="lane_e_evidence",
                    quality_score=ev_citation.quality_score,
                )
                yield CitationExtracted(
                    event_id=_make_event_id(),
                    engagement_id=eid,
                    client_id=cid,
                    agent_id=agent.agent_id,
                    citation_id=ev_citation.citation_id,
                    title=ev_citation.title,
                )

            # --- Emit synthesis event ---
            new_claim_count = len(self._all_claims)
            conf_values = [c["confidence"] for c in self._all_claims if "confidence" in c]
            conf_range = f"{min(conf_values):.2f}-{max(conf_values):.2f}" if conf_values else "N/A"

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
    # Deep research prompt + parser
    # ------------------------------------------------------------------

    def _build_deep_research_prompt(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
    ) -> str:
        """Build a comprehensive prompt for deep multi-turn web research."""
        rs = spec.research_spec

        # Collect research questions for context
        questions = "\n".join(
            f"  - {'[PRIMARY] ' if q.is_primary else ''}{q.question}" for q in rs.questions
        )

        # Inject parsed evidence as background context. Deep mode still
        # expects `sources` arrays with URLs in the output JSON, so these
        # are read-only reference material -- no EV-NNN ref format.
        evidence_block = ""
        if self._evidence_block:
            evidence_block = (
                "\nPARSED EVIDENCE ALREADY FETCHED (use as background; "
                "cite via their URLs in your sources arrays when relevant):\n"
                f"{self._evidence_block}\n"
            )

        return f"""You are a senior research analyst conducting deep web research for a consulting engagement.

ENGAGEMENT CONTEXT:
- Title: {rs.title}
- Client Decision Context: {rs.decision_context}
- Quality Standard: {rs.quality_bar}

RESEARCH QUESTIONS:
{questions}

YOUR SPECIFIC TASK:
{task.description}

ACCEPTANCE CRITERIA:
{chr(10).join(f"  - {c}" for c in task.acceptance_criteria)}

ANTI-CONFIRMATORY FRAMING (you MUST find evidence both for AND against):
{task.anti_confirmatory_framing}

EXPECTED OUTPUT:
{task.end_product}
{evidence_block}
RESEARCH INSTRUCTIONS:
1. Search the web thoroughly for information related to this task.
2. For each promising result, read the full page to extract detailed information.
3. Follow citations and references to find primary sources.
4. Cross-reference claims across multiple sources.
5. Look for the most recent data available (2024-2026).
6. Seek out contrarian evidence and counterarguments.
7. Note what you searched for but could NOT find (absence is analytically significant).

After completing your research, output ONLY a JSON object in this exact format (no other text before or after):

```json
{{
  "claims": [
    {{
      "text": "Clear, specific factual claim statement",
      "evidence": "Summary of the evidence supporting this claim, including specific data points, dates, and figures",
      "confidence": 0.85,
      "caveats": ["Any limitations or qualifications"],
      "sources": [
        {{
          "url": "https://exact-source-url.com/page",
          "title": "Title of the source page or article",
          "content_snippet": "Relevant excerpt from the source (50-200 words)"
        }}
      ]
    }}
  ],
  "absence_report": [
    "Description of what was searched for but not found"
  ]
}}
```

REQUIREMENTS FOR YOUR OUTPUT:
- Produce at least 20 claims (more is better if the evidence supports it)
- Every claim MUST have at least one source with a real URL
- Include content_snippet for every source (actual text from the page)
- Confidence scores: 0.9+ = multiple corroborating sources with hard data; 0.7-0.89 = single strong source or multiple weak ones; 0.5-0.69 = limited or ambiguous evidence; below 0.5 = speculative or contested
- The absence_report MUST list at least 3 things you looked for but could not find
- Include evidence AGAINST the main thesis, not just supporting evidence
- Prefer primary sources (SEC filings, company reports, peer-reviewed papers) over secondary (news articles, blog posts)

OUTPUT THE JSON AND NOTHING ELSE."""

    def _parse_deep_response(self, response: str) -> dict:
        """Parse the JSON output from a deep research session."""
        try:
            data = safe_llm_json(response)
            # data is always a dict here (safe_llm_json default)
            if "claims" not in data:
                return {"claims": [], "absence_report": []}
            return data
        except ParseError:
            # Try list form (LLM returned array of claims directly)
            try:
                data = safe_llm_json(response, expect_list=True)
                return {"claims": data, "absence_report": []}
            except ParseError:
                logger.error(
                    "Failed to parse deep research JSON (%d chars). First 500 chars: %s",
                    len(response),
                    response[:500],
                )
                raise RuntimeError("Deep research output was not parseable JSON") from None

    # ------------------------------------------------------------------
    # Shallow mode prompt builders
    # ------------------------------------------------------------------

    def _build_synthesis_prompt(
        self,
        task: ResearchTask,
        spec: EngagementSpec,
        agent: AgentInstance,
        round_num: int,
        wiki_context: list[str],
        round_citation_table: dict[str, Citation] | None = None,
    ) -> str:
        ctx_section = ""
        if wiki_context:
            ctx_section = "\n\nPrior context:\n" + "\n---\n".join(wiki_context)

        # Enumerate citations as SRC-NNN refs for explicit per-claim attribution
        if round_citation_table:
            src_lines = "\n".join(
                f"- {ref} | {cit.title} | {cit.url}"
                + (f" | {cit.content_snippet[:120]}" if cit.content_snippet else "")
                for ref, cit in round_citation_table.items()
            )
            sources_section = f"Sources this round (use refs in citation_refs):\n{src_lines}"
        else:
            sources_text = json.dumps(
                [s for s in self._all_sources if s.get("round") == round_num],
                default=str,
            )
            sources_section = f"Sources this round:\n{sources_text}"

        evidence_section = ""
        ref_guidance = "the SRC-NNN refs"
        if self._evidence_block:
            evidence_section = "\n\n" + self._evidence_block
            ref_guidance = "SRC-NNN tool-search refs and EV-NNN parsed-passage refs"

        return (
            f"Task: {task.description}\n"
            f"Round: {round_num}\n"
            f"Anti-confirmatory framing: {task.anti_confirmatory_framing}\n"
            f"{sources_section}"
            f"{evidence_section}"
            f"{ctx_section}\n\n"
            "Synthesize findings as JSON array of claims. Each claim MUST include "
            f"citation_refs listing {ref_guidance} that support it:\n"
            '{"text": "...", "evidence": "...", "citation_refs": ["SRC-001", "EV-002"], '
            '"confidence": 0.0-1.0, "caveats": ["..."]}\n'
            "Claims without citation_refs will be dropped.\n"
        )

    def _build_round_citation_table(self, round_cits: list[Citation]) -> dict[str, Citation]:
        """Build SRC-NNN -> Citation table for explicit per-claim attribution."""
        return {f"SRC-{i + 1:03d}": cit for i, cit in enumerate(round_cits)}

    def _attach_citations_from_refs(
        self,
        raw_claims: list[dict],
        round_citation_table: dict[str, Citation],
        *,
        engagement_id: str,
        client_id: str,
        agent_id: str,
    ) -> tuple[list[dict], list[Citation]]:
        """Attach only explicitly referenced citations to each claim.

        Resolves both SRC-NNN refs (round tool-search citations) and
        EV-NNN refs (parsed-evidence passages). EV refs are lazily
        converted to ``Citation`` objects on first use and cached in
        ``self._evidence_citations`` so the same EV-NNN stays mapped to
        the same Citation for the rest of the task.

        Returns the filtered claim list plus the list of evidence-backed
        citations minted during this call, so the caller can emit
        ``CitationExtracted`` events and bump ``sources_consulted`` by
        the number of newly-resolved parsed passages.

        Claims with no valid citation_refs are dropped -- no
        round-broadcast fallback.
        """
        result: list[dict] = []
        newly_minted: list[Citation] = []
        for claim in raw_claims:
            refs = claim.get("citation_refs", [])
            if not refs:
                logger.debug("Dropping claim (no citation_refs): %.80s", claim.get("text", ""))
                continue

            resolved: list[Citation] = []
            for ref in refs:
                if ref in round_citation_table:
                    resolved.append(round_citation_table[ref])
                    continue
                if ref in self._evidence_citations:
                    resolved.append(self._evidence_citations[ref])
                    continue
                if ref in self._evidence_table:
                    self._citation_counter += 1
                    citation = evidence_to_citation(
                        self._evidence_table[ref],
                        citation_id=_make_source_instance_id(
                            engagement_id, agent_id, self._citation_counter
                        ),
                        engagement_id=engagement_id,
                        client_id=client_id,
                        agent_id=agent_id,
                    )
                    self._evidence_citations[ref] = citation
                    newly_minted.append(citation)
                    resolved.append(citation)

            if not resolved:
                logger.debug(
                    "Dropping claim (no valid citation_refs resolved): %.80s",
                    claim.get("text", ""),
                )
                continue
            claim["citations"] = resolved
            result.append(claim)
        return result, newly_minted

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
            result = self._parse_absence(response)
            # Structural enforcement: absence report must be non-empty
            if not result:
                return [f"No specific absences identified for task {task.id}"]
            return result
        except RuntimeError:
            return [f"Unable to generate absence report for task {task.id}"]

    # ------------------------------------------------------------------
    # Response parsers
    # ------------------------------------------------------------------

    def _parse_synthesis(self, response: str) -> list[dict]:
        """Parse LLM synthesis response into claim dicts."""
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
            logger.warning("Could not parse synthesis response as JSON")
            return []

    def _parse_absence(self, response: str) -> list[str]:
        """Parse LLM absence report response."""
        try:
            data = safe_llm_json(response, expect_list=True)
            return [str(item) for item in data]
        except ParseError:
            pass
        try:
            data = safe_llm_json(response)
            return [str(data)]
        except ParseError:
            return [response.strip()] if response.strip() else []
