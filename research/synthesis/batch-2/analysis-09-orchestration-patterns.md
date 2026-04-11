# Analysis: Report 09 — Orchestration Patterns
*Analyzed: 2026-04-05 | Priority: Tier 3 (MEDIUM) | Report quality: high*

---

## Executive Summary

This report directly validates Settled Decision #1 (custom orchestration with PydanticAI + Temporal + MCP gateway) with high-quality, current evidence, and provides implementation-ready specifications for several components the current plan describes but does not mechanize. The main architectural decision — PydanticAI for typed agents, Temporal deferred to Phase 2, hierarchical DAG + supervisor hybrid pattern — is confirmed. Three findings upgrade from informational to actionable: the four-layer error recovery architecture should be treated as a Phase 1 requirement rather than Phase 2, not a deferral; the Anthropic Agent SDK is formally disqualified as primary but designated as a legitimate complementary node for specific use cases; and the database state machine HITL pattern provides a concrete 2-3 day implementation path that maps directly to Jack's two non-negotiable gates. The report's quality is high: evidence is current (PydanticAI v1.0 September 2025, Anthropic Agent SDK September 2025, Temporal Series D 2025), production-backed (OpenAI Codex on Temporal, Replit Agent 3 migration, Retool Agents), and well-sourced. One finding — LangGraph's superiority for HITL over PydanticAI — creates a mild tension with the settled decision that requires a clear resolution. The tension is resolvable in favor of PydanticAI given Phase 2 Temporal integration, but the team must commit to shipping the database-state-machine HITL in Phase 1 rather than treating HITL as deferred.

---

## Key Findings (ranked by implementation impact)

### 1. Four-Layer Error Recovery Must Ship in Phase 1, Not Phase 2

- **What:** A structured four-layer defense (retry with exponential backoff → model fallback chains → error classification and routing → checkpointing) drops unrecoverable failures from 23% to under 2% in documented production systems. The report quantifies: retry with exponential backoff via `tenacity` takes a few hours to implement and prevents the majority of failures. Layer 4 (checkpointing) is where Temporal pays off most — but a PostgreSQL-based interim implementation is explicitly specified as viable for Phase 1.
- **Evidence basis:** Claude API StatusGator data — 62 incidents in 90 days, median 1 hour 19 minutes duration. AWS research — exponential backoff with jitter reduces retry storms 60-80%. One production system (unnamed, credible framing) — layered patterns dropped unrecoverable failures from 23% to under 2%.
- **Evidence quality:** Verified (StatusGator is an independent monitoring service with public data). Credible (AWS research is well-established). Claimed (23% → 2% figure — no specific source named, though the pattern itself is well-established). Credible (retry header handling is documented Claude API behavior).
- **Temporal check:** StatusGator data is ongoing; Claude API SLA behavior is current. Retry patterns are well-established and not fast-moving. No stale concerns.
- **Conflicts with existing project research?** The current plan lists error recovery as a general Phase 2 concern with no specific implementation. The PHASE-1-IMPLEMENTATION-SPEC.md (per CURRENT-STATE.md) does not call out retry/fallback/checkpointing as required Phase 1 components. This finding argues they should be.
- **Verdict:** ADOPT — immediately, for Phase 1
- **Justification:** Layer 1 (retry with tenacity) takes hours, not days, and prevents the dominant failure class. Claude API's 62 incidents in 90 days is not an edge case — it's operating reality. Shipping research agents that collapse on any API rate-limit is a quality failure, not a Phase 2 concern.
- **Keystone impact:** All pipeline components, especially Component #7 (Research Agent pipeline L1) and Component #4 (MCP Gateway). The four layers map cleanly to Phase 1 implementation: Layers 1-2 (retry + fallback) ship with the first research agent; Layer 3 (error classification) ships with the pipeline controller; Layer 4 (PostgreSQL checkpointing) ships with the HITL gate infrastructure.
- **Specific retry policy (ADOPT verbatim):** `tenacity` with 1-second base, 60-second cap, full jitter, 5 max attempts. Retry on 429, 500, 529, connection timeout. Never retry 400, 401, 413. Honor `Retry-After` and `X-RateLimit-*` headers.
- **Specific fallback chain (ADOPT):** Opus 4.6 → Sonnet 4.6 → Haiku 4.5 → cached/template response. Match the existing model tiers from Settled Decision #4. Retry primary 2-3 times before falling back — don't fail over immediately.
- **Specific partial-result handling (ADOPT):** If 3 of 5 research agents complete but 2 fail, combine available results with reduced-coverage notice; retry failed agents independently before proceeding. Every agent must return a structured success/failure status field — orchestrator must always know what it has.
- **Circuit breaker level:** Agent-cluster, not individual connection. Trip if more than 50% of L1 agents fail within 60 seconds. Add semantic quality checks alongside technical failure checks — hallucinations don't produce HTTP errors.
- **Contradicts:** Contradicts the implicit Phase 2 deferral of error recovery in the current plan. No contradiction with settled architectural decisions.

---

### 2. PydanticAI v1.0+ Is Production-Stable and the Correct Primary Framework

- **What:** PydanticAI v1.0 shipped September 4, 2025, with an explicit no-breaking-changes commitment until v2 (April 2026 earliest). Current version v1.77.0 with 16,100 GitHub stars, 414+ contributors, PyPI "Production/Stable" classifier. The framework provides three validated capabilities relevant to Keystone: (1) automatic retry on schema validation failure (malformed outputs self-correct without custom error handling), (2) native MCP integration (MCPServerStdio, SSE, Streamable HTTP), and (3) a beta Graph API with parallel execution, joins, reducers, and conditional branching. HITL is first-class: tools can be flagged `approval_required`, pausing execution for human review.
- **Evidence basis:** PydanticAI official changelog, GitHub metrics, PyPI classifier — all verifiable directly.
- **Evidence quality:** Verified (first-party framework documentation with verifiable metrics).
- **Temporal check:** v1.77.0 is current as of report date. No stale concerns.
- **Conflicts with existing project research?** Directly confirms Settled Decision #1. The main prior concern was that PydanticAI was pre-production; that concern is resolved.
- **Verdict:** ADOPT (confirms existing decision)
- **Justification:** The "experimental choice" risk that existed when this decision was first made is now eliminated. v1.0 stability and the `approval_required` HITL primitive are both production-confirmed.
- **Keystone impact:** Removes the "framework stability" risk from the risk register. The `approval_required` tool flag is the correct PydanticAI-native HITL primitive for Phase 1 — it pairs with the database state machine described in Finding #4. The automatic schema validation retry is a zero-cost reliability improvement — use `output_type` Pydantic models on every agent, every stage.
- **Note on Graph API:** The beta Graph API is promising for the L1 parallel research fan-out pattern but carries API churn risk while in beta. Recommendation: use `asyncio.gather()` for L1 parallelism in Phase 1 (proven, stable), evaluate the Graph API for Phase 2 when it exits beta. The beta label is a real constraint, not a minor caveat.
- **Contradicts:** None.

---

### 3. Temporal Deferral Is Correct, But "Architect for It Now" Has Concrete Requirements

- **What:** Temporal Python SDK v1.24.0 is fully GA with native PydanticAI integration via `TemporalAgent`. Production validation is strong: OpenAI uses it for Codex (millions of requests), Replit migrated Agent 3 to it for reliability, Retool built Agents on it. The deferral is correct for Phase 1 because the inflection point is SLA-required crash recovery — which MVP validation doesn't require. However, the report specifies five concrete architectural requirements that make Phase 2 migration smooth rather than a rewrite. The async alternative (building without Temporal) costs 500-1,000 lines of custom orchestration code: state machine, PostgreSQL checkpointing, tenacity retry, asyncio.Semaphore concurrency, structured correlation-ID logging.
- **Evidence basis:** Temporal PyPI download data (~25 million monthly). OpenAI Codex, Replit Agent 3, Retool Agents — all documented production migrations. Temporal Series D at $5B valuation in 2025. Self-host complexity confirmed by community reports ("several days" cryptic debugging, PostgreSQL spikes at modest scale).
- **Evidence quality:** Credible (download data verifiable via PyPI). Credible (OpenAI/Replit/Retool — named production systems). Verified (Temporal Series D is public information).
- **Temporal check:** All evidence 2025. Current.
- **Conflicts with existing project research?** Confirms the existing Temporal deferral decision and adds the "design for it now" requirements, which the current plan acknowledges but does not specify concretely.
- **Verdict:** ADOPT (deferral confirmed) + ADOPT (five migration requirements, enforced from Day 1)
- **Justification:** The migration requirements are low-cost to implement upfront and prevent expensive rearchitecting in Phase 2. They are pure software discipline, not extra features.
- **Keystone impact:** Component #5 (Specification Engine), Component #7 (Research Agent pipeline), Component #9 (Deliberation). The five requirements become mandatory coding standards for all pipeline layers:
  1. Each pipeline layer must be a pure function: `async def run_layer(input: LayerInput) -> LayerOutput`
  2. All inter-layer data must use Pydantic models (already true for Settled Decision #8 — reinforce)
  3. The pipeline controller must be separate from agent code (no controller logic inside agents)
  4. Log with correlation IDs per pipeline run from Day 1 (these become Temporal workflow IDs later)
  5. All layers must be idempotent (same input, same output — required for Temporal event history replay)
- **Phase 2 transition:** When Temporal arrives, wrap agents with `TemporalAgent`, move orchestration logic into `@workflow.defn` classes, deploy Temporal Cloud (~$100/month with $1,000 free credits for new users). Do not self-host — the operational complexity is significant.
- **Contradicts:** None. Confirms and specifies existing plan.

---

### 4. Database State Machine HITL Pattern Provides the Correct Phase 1 Gate Implementation

- **What:** The minimum viable HITL pattern for Phase 1 is a PostgreSQL state machine with three tables, a REST API, and a web UI. The pipeline writes an artifact (a Pydantic model), sets status to `AWAITING_REVIEW`, and returns. The UI polls for pending reviews, presents the artifact with agent reasoning, and posts the decision back. Three review flows from day one: approve (pipeline continues), modify (human edits artifact inline with schema validation, pipeline continues with modification), reject (regeneration with human feedback as context). Default timeouts: 1 hour for low-stakes (L0 spec approval), 24 hours for high-stakes (L1 research output). Estimated implementation: 2-3 days.
- **Evidence basis:** Report's own synthesis; referenced against PydanticAI's `approval_required` tool flag and Temporal Signals pattern (Phase 2 upgrade path). No specific production case study cited for the database state machine pattern itself — this is a standard architectural pattern.
- **Evidence quality:** Credible (standard pattern, well-understood tradeoffs). The 2-3 day estimate is plausible for the schema + REST API; the UI depends on complexity.
- **Temporal check:** State machine patterns are timeless. The Temporal Signals upgrade path is confirmed by the Temporal v1.24.0 GA status.
- **Conflicts with existing project research?** Jack's Directive #7 specifies exactly two non-negotiable HITL gates: (1) after the Specification Engine produces the issue tree/task list, (2) after Deliberation produces the confidence map. This pattern implements both with a single shared infrastructure. The current plan lists Temporal as the HITL mechanism — but Temporal is deferred, leaving a gap. This finding fills that gap.
- **Verdict:** ADOPT — this is the Phase 1 HITL implementation
- **Justification:** Jack's Directive #7 is non-negotiable and Temporal is deferred. The database state machine is the only viable Phase 1 path that satisfies both constraints. It maps cleanly to Temporal Signals in Phase 2 with no agent code changes — only the orchestration layer migrates.
- **Keystone impact:** CRITICAL. This affects the implementation spec for Component #5 (Specification Engine — Gate 1) and Component #9 (Deliberation — Gate 2). Both must write artifacts to `review_gates` and check status before proceeding. The orchestrator polls or uses asyncio event notification (avoid busy-wait polling in production code). The three table schema (`pipeline_runs`, `review_gates`, `agent_results`) should be the standard from Day 1, not added later.
- **UI requirement:** Show artifact prominently alongside collapsible "Agent Reasoning" panel (sources consulted, key decisions, confidence levels, token usage). The reasoning panel is not cosmetic — it's the mechanism by which the human reviewer can make an informed approve/modify/reject decision. Without it, the gate becomes a rubber stamp.
- **Contradicts:** Mild tension. CAPSTONE-PLAN-v2.md Section 12.0 lists Temporal as the mechanism for human-in-the-loop gates without specifying an interim implementation. This finding resolves the gap — the plan assumed Temporal would be Phase 1; it is Phase 2. The database state machine is the required bridge.

---

### 5. Anthropic Agent SDK Is Complementary, Not Competitive — and Formally Disqualified as Primary

- **What:** Anthropic renamed the Claude Code SDK to "Claude Agent SDK" on September 29, 2025. It is architecturally a runtime harness (wraps the full Claude Code agent loop, 14+ built-in tools, spawns a Node.js subprocess). Three factors disqualify it as primary framework: (1) Claude-only with no provider flexibility, (2) Anthropic Commercial Terms of Service (not MIT), creating ownership risk, (3) Node.js subprocess adds deployment complexity vs. pure Python. The right use case is nodes requiring Claude Code's full runtime: complex file operations, code execution sandboxes, computer use.
- **Evidence basis:** Anthropic SDK changelog (v0.1.48). GitHub stars (5,500). License terms are verifiable via Anthropic ToS.
- **Evidence quality:** Verified (first-party Anthropic documentation; license terms are public).
- **Temporal check:** September 2025 rename. Current.
- **Conflicts with existing project research?** CAPSTONE-PLAN-v2.md Section 12.0 lists "Claude Agent SDK for execution substrate" as part of the orchestration stack without specifying which roles it fills. This finding clarifies: it is NOT the execution substrate for standard research agents. Standard research agents should use PydanticAI calling Claude directly. Agent SDK is reserved for future nodes requiring computer-use or code-execution capabilities.
- **Verdict:** SKIP (as primary framework) / INVESTIGATE (for specific future nodes)
- **Justification:** Provider lock-in and proprietary licensing are structural disqualifiers for a production system targeting long-term commercial use. The token overhead argument (simpler and cheaper with PydanticAI direct) is secondary but real.
- **Keystone impact:** Clarifies the orchestration stack description in CAPSTONE-PLAN-v2.md. Remove "Claude Agent SDK for execution substrate" as a primary stack component. Add as a conditional future option for specific node types requiring full runtime capabilities. No Phase 1 dependency.
- **Contradicts:** Mild tension with CAPSTONE-PLAN-v2.md Section 12.0 language. The plan should be updated to clarify the Agent SDK's role.

---

### 6. DAG Backbone + L1 Supervisor Is the Validated Production Orchestration Pattern

- **What:** The correct macro pattern for Keystone is a deterministic DAG controller for the 6-layer pipeline (L0 → L1 → L1.5 → L2 → L3 → L4) with conditional edges for evaluation loops, plus a supervisor pattern embedded only inside L1 for parallel research. The LLM must not decide pipeline flow — the pipeline controller decides based on structured outputs. Anthropic's own multi-agent research system (June 2025 engineering blog) runs exactly this architecture: LeadResearcher (Opus 4) spawns subagents (Sonnet 4), each exploring tens of thousands of tokens but returning only 1,000-2,000 tokens of condensed findings. Outcome: multi-agent outperformed single-agent Opus 4 by 90.2%, with token usage explaining 80% of performance variance.
- **Evidence basis:** Anthropic engineering blog, June 2025 (first-party, highest credibility). The 90.2% improvement figure is from the same source.
- **Evidence quality:** Verified (Anthropic first-party production documentation, June 2025).
- **Temporal check:** June 2025. Current.
- **Conflicts with existing project research?** Confirms the existing generator-based agent loop decision (Settled Decision #7). Adds the explicit constraint that the LLM must not decide macro pipeline flow — the system decides based on typed outputs. This is not new to the plan but is now empirically grounded with production evidence.
- **Verdict:** ADOPT (confirms existing direction with added precision)
- **Justification:** Anthropic's own production evidence is the highest credibility available for a Claude-based system.
- **Keystone impact:** Component #7 (Research Agent pipeline L1). The condensed output constraint (1,000-2,000 tokens from each subagent to the orchestrator) is a new concrete specification. Each research agent should have an explicit token budget for its summary, not an open-ended handoff. The 80% token-usage-variance finding also validates prioritizing the Specification Engine's task decomposition quality — the Spec Engine controls how much research each agent is budgeted, which dominates quality outcomes.
- **Contradicts:** None. Confirms Settled Decision #7.

---

### 7. LangGraph's HITL Superiority Is Real but Not a Reason to Reconsider PydanticAI

- **What:** LangGraph has the most mature HITL pattern in the current ecosystem: native `interrupt()` at any node, persistent checkpointing with automatic crash recovery, and time-travel debugging. These features are genuinely superior to PydanticAI's `approval_required` tool flag + database state machine. LangGraph is production-validated (Klarna, Replit, Elastic). However, it carries LangChain abstraction weight, steeper learning curve, and more boilerplate for simple cases. The report's conclusion: LangGraph warrants serious consideration only if orchestration complexity becomes extreme.
- **Evidence basis:** LangGraph v1.0 (October 2025). Production deployments at Klarna, Replit, Elastic are named.
- **Evidence quality:** Credible (named production systems). The LangGraph v1.0 release in October 2025 is verifiable.
- **Temporal check:** October 2025 LangGraph v1.0. Current. Note: the three CVEs and licensing concerns cited in the existing project research (from the original Batch 1 analysis) are pre-v1.0 findings. Need to assess whether they apply to v1.0.
- **Conflicts with existing project research?** The current plan explicitly says: "LangGraph: LEARN patterns only (3 CVEs, licensing concerns — decided SKIP for direct dependency)." The report's LangGraph framing is less negative than the existing settled position. However, the settled position pre-dates LangGraph v1.0. The CVE and licensing concerns should be re-evaluated against v1.0 before permanently closing this option.
- **Verdict:** SKIP (for Phase 1, consistent with existing plan) / INVESTIGATE (v1.0 CVE and licensing status before Phase 2 planning)
- **Justification:** The database state machine + Temporal Phase 2 path satisfies the HITL requirements without the LangGraph ecosystem overhead. But the 3 CVEs and licensing concerns were documented against a pre-v1.0 release — if those are resolved in v1.0, the SKIP verdict should be revisited before Phase 2 architecture is finalized.
- **Keystone impact:** Flag for pre-Phase 2 review: reassess LangGraph v1.0 CVE status and licensing terms. If both are resolved, LangGraph becomes a legitimate alternative to building custom Temporal HITL infrastructure. Do not act on this now — it is a Phase 2 decision.
- **Contradicts:** Mild tension with existing settled decision. The CVE/licensing re-evaluation is the key action item, not an immediate architectural change.

---

### 8. Context Management Hierarchy: Isolation Primary, Compression Secondary

- **What:** The validated context management hierarchy from production systems is: (1) Isolation first — each subagent gets a fresh context window with only compressed prior-round outputs plus round-specific instructions; (2) Between-round compression — structured schemas preserving key facts, sources, confidence scores, discarding raw search results and intermediate reasoning; (3) Within-orchestrator memory — persistent scratchpad carrying research plan, key findings, gaps, active questions. The Manus principle: "Share memory by communicating, don't communicate by sharing memory." Applies directly to L1 parallel research context architecture.
- **Evidence basis:** Anthropic multi-agent research system (June 2025). Manus production platform (cited directly).
- **Evidence quality:** Verified (Anthropic first-party). Credible (Manus as production system).
- **Temporal check:** June 2025. Current.
- **Conflicts with existing project research?** Consistent with Settled Decision #5 (filesystem-based isolation) and the finding from Report 01 analysis (context resets with structured handoffs outperform compaction). This finding adds the between-round compression schema requirement and reinforces the orchestrator scratchpad requirement from Report 01.
- **Verdict:** ADOPT (reinforces and extends existing decisions)
- **Justification:** Converging evidence across multiple reports — this is the correct pattern.
- **Keystone impact:** Component #7 (Research Agent pipeline L1). Adds a concrete output budget: each research subagent returns 1,000-2,000 tokens of condensed findings (not the full research transcript). The orchestrator LeadResearcher maintains a persistent scratchpad. Between rounds, a compression step produces structured schemas, not raw concatenation.
- **Contradicts:** None.

---

## Architectural Decisions This Enables

**Decision: Database state machine HITL is the Phase 1 implementation for Jack's two non-negotiable gates**
The combination of Jack's Directive #7 (non-negotiable gates), Temporal deferral to Phase 2, and this report's 2-3 day database state machine specification makes the decision concrete. Phase 1 must ship functioning HITL gates using PostgreSQL state machine + PydanticAI `approval_required` flags. The gates are not optional, not deferred, and not dependent on Temporal. Temporal upgrade in Phase 2 requires no agent code changes — only the orchestration layer migrates.

**Decision: Error recovery Layers 1-2 (retry + fallback) are Phase 1 requirements**
The current plan treats error recovery as a general concern without specifying when it ships. Given Claude API's documented 62 incidents in 90 days, shipping research agents without retry/fallback is operationally incorrect. Layers 1-2 (tenacity + model fallback chain) are added to Phase 1 implementation scope. Layer 4 (PostgreSQL checkpointing) ships alongside the HITL gate infrastructure since they share the same database schema. Layer 3 (error classification and routing) ships with the pipeline controller.

**Decision: Agent SDK is removed from the primary orchestration stack and reclassified as a conditional future option**
CAPSTONE-PLAN-v2.md Section 12.0 lists "Claude Agent SDK for execution substrate" — this is incorrect framing. The Agent SDK is not the execution substrate for standard research agents. Remove this from the primary stack description. Add it as a conditional future node type for computer-use or code-execution workflows.

**Decision: L1 subagent output budget: 1,000-2,000 tokens of condensed findings per agent**
Empirically validated by Anthropic's own production system. This becomes a formal specification in the L1 → L1.5 handoff contract. Each research agent declares its output budget; the orchestrator enforces it. Agents should not return raw search transcripts or intermediate reasoning.

---

## Changes to Existing Plan

**CAPSTONE-PLAN-v2.md Section 12.0 — update two items:**
1. Remove "Claude Agent SDK for execution substrate" from the primary stack description. Replace with: "Agent SDK is reserved for specific future nodes requiring Claude Code's full runtime (computer use, code execution); standard research agents use PydanticAI calling Claude API directly."
2. Add "Error recovery: four-layer defense (retry → fallback → classification → checkpointing), Layers 1-2 ship with Phase 1 research agents, Layer 4 ships with HITL gate infrastructure."

**PHASE-1-IMPLEMENTATION-SPEC.md — add to Component #7 (Research Agents) scope:**
- Retry with exponential backoff via `tenacity` (1s base, 60s cap, full jitter, 5 attempts). Status codes: retry 429/500/529/timeout, never retry 400/401/413.
- Model fallback chain: Opus 4.6 → Sonnet 4.6 → Haiku 4.5 → cached/template. Retry primary 2-3 times before falling back.
- Structured success/failure status field on every agent output (not just content).
- Partial-result continuation: combine results from agents that succeeded; retry failed agents independently.
- Subagent output budget: 1,000-2,000 tokens of condensed findings (not raw transcripts).

**PHASE-1-IMPLEMENTATION-SPEC.md — add to Component #5 (Specification Engine) and Component #9 (Deliberation) scope:**
- Both must write artifacts to `review_gates` table and check status before proceeding.
- HITL implementation: PostgreSQL state machine with three tables (`pipeline_runs`, `review_gates`, `agent_results`), REST API, web UI with artifact + collapsible agent reasoning panel.
- Three review flows from Day 1: approve, modify (with schema validation), reject (with feedback as next-round context).
- Default timeouts: 1 hour (Gate 1, L0 spec approval), 24 hours (Gate 2, L1 research/deliberation output).

**Mandatory coding standards — add to ARCHITECTURE.md or a new CODING-STANDARDS.md:**
All pipeline layers must satisfy five pre-Temporal requirements:
1. Each layer is a pure function: `async def run_layer(input: LayerInput) -> LayerOutput`
2. All inter-layer data uses Pydantic models
3. Pipeline controller is separate from agent code
4. Correlation IDs logged per pipeline run from Day 1
5. All layers are idempotent

**LangGraph status — add to risk register / Phase 2 planning backlog:**
Reassess LangGraph v1.0 (October 2025) CVE status and licensing terms before Phase 2 architecture is finalized. The pre-v1.0 CVE and licensing concerns that drove the SKIP verdict may be resolved. Do not act in Phase 1; evaluate before Phase 2 HITL architecture is committed.

---

## Open Questions Remaining

**1. Who owns the pipeline controller and where does it live in the codebase?**
The report correctly distinguishes the DAG controller (system decides flow) from agent code (LLM reasons). The current architecture documents don't specify where the pipeline controller lives, what its interface looks like, or how it interacts with the HITL state machine. This needs a concrete spec before Phase 1 build begins. Likely a new `src/keystone/pipeline/` module with explicit controller classes.

**2. What is the concrete schema for between-round research compression?**
The report says compress raw research into structured schemas preserving facts, sources, and confidence scores. But the schema is not specified. This is the L1 → L1.5 handoff content format. It needs to be designed alongside the handoff contracts — the existing contracts define the envelope, but not the compression format within the research findings payload.

**3. Is PydanticAI's beta Graph API mature enough for Phase 2 use?**
The report notes the Graph API is in beta with potential API churn. The plan should track when it exits beta. If it achieves stability before Phase 2 begins, it simplifies the L1 parallel research fan-out implementation compared to building with `asyncio.gather()`. If it remains beta, the custom async path must be used.

**4. LangGraph v1.0 CVE and licensing status**
The settled decision to SKIP LangGraph was based on pre-v1.0 findings. v1.0 shipped October 2025. Before Phase 2 architecture is finalized, confirm: are the 3 CVEs patched in v1.0? What is the current licensing model (LangGraph was moved to MIT from LangChain's proprietary license)? This may reopen LangGraph as a Phase 2 HITL alternative if Temporal proves operationally complex.

**5. When does Temporal become mandatory — is the inflection point before or after MVP validation?**
The report frames the inflection point as "when you can't afford to re-run failed pipelines." With paying customers and SLA requirements, Temporal is mandatory. The question is whether MVP validation with real Keystone engagement data will produce that customer-facing SLA requirement before Phase 2 is started. If Keystone uses the MVP on real engagements before Phase 2 is complete, the custom PostgreSQL checkpointing (Layer 4 of error recovery) becomes load-bearing, not a bridge — plan its scope accordingly.
