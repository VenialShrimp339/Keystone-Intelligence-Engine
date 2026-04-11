# Report 4: A4 — Orchestration Frameworks & Agent Coordination

---

## Top Findings

**Finding 1: 68.8% inter-agent data leakage rate in standard frameworks — strict isolation is a measured necessity, not a design preference**
The AgentLeak benchmark (February 2026, 4,979 traces) found that 68.8% of inter-agent message traces leak sensitive data in standard frameworks, with shared memory leaking in 46.7% of traces. No framework tested provides mechanisms to intercept inter-agent messages or monitor shared memory writes. Claude 3.5 Sonnet showed the best performance (28.1% leakage) but that is still unacceptable for strict isolation. This is the most important empirical finding in the orchestration space — it validates CAPSTONE-PLAN-v2.md's strict isolation requirement from a security perspective, not just an analytical correctness perspective.
- Pipeline layer: L1 (Research Agents)
- Build implication: Strict agent isolation (each agent writes to its own directory, only the orchestrator reads across directories) is not a design preference that could be traded off — it is a necessary defense against a documented, measured failure mode. The filesystem-as-state coordination approach directly prevents the shared-memory leakage that accounts for 46.7% of the documented problem.
- Evidence quality: Verified — peer-reviewed benchmark, February 2026, 4,979 traces.

**Finding 2: Anthropic's own multi-agent research system validates Keystone's core architectural patterns with 90.2% performance improvement**
Anthropic's engineering blog (June 2025) describes a production multi-agent research system: orchestrator-worker pattern (Lead Researcher spawns parallel subagents), separate context windows (strict isolation), file-system-as-state (explicitly recommended to minimize "game of telephone" information loss), LLM-as-judge evaluation with rubric scoring, and model mixing (Opus for lead, Sonnet for subagents at 40% cost reduction). The 90.2% performance improvement over single-agent Opus is the strongest available validation for the multi-agent research architecture. Token usage explains 80% of performance variance.
- Pipeline layer: L0, L1, L4 (whole pipeline)
- Build implication: The Keystone architecture is already well-aligned with the most validated production multi-agent research system. No fundamental redesign is needed. Priority: implement the model mixing strategy (Opus for Specification Engine and Evaluator, Sonnet for research agents) from the start to manage costs.
- Evidence quality: Verified — Anthropic Engineering blog with specific metrics.

**Finding 3: The Evaluator will dominate costs — verification consumes 72% of tokens in comparable systems**
ICLR 2025 workshop finding: verification phases consume 72% of tokens in multi-agent research pipelines. Reflexive (reject/regenerate) loops achieve the highest accuracy (F1=0.943) at 2.3x cost, but hybrid configurations recover 89% of reflexive accuracy at only 1.15x cost. The implication: applying reject/regenerate everywhere is not economically viable. Selective application on high-value stages dramatically changes the cost profile.
- Pipeline layer: L4 (Evaluator)
- Build implication: The multi-tiered evaluation intensity model in CAPSTONE-PLAN-v2.md Section 5.5 is validated and economically necessary. "Deep" evaluation (multi-pass with adversarial testing) should be reserved for strategic analyses and client-facing deliverables. "Light" evaluation for preliminary findings. This is not a quality compromise — it is the only economically sustainable way to run the pipeline at consulting scale.
- Evidence quality: Verified — ICLR 2025 workshop paper.

**Finding 4: No existing framework natively supports Keystone's combination of strict isolation, reject/regenerate loops, handoff contracts, and filesystem-as-state**
LangGraph requires careful subgraph architecture to achieve isolation (not the default). CrewAI's router loop-back is bugged (GitHub issue #1579). PydanticAI's graph API lacks built-in persistence. Google ADK is pre-1.0. Every framework assumes shared state as the coordination primitive — isolation must be bolted on, and the AgentLeak data shows that bolting it on fails 46-69% of the time. The build-custom case is unusually strong for Keystone.
- Pipeline layer: L0, L1 (Orchestration)
- Build implication: Build custom orchestration logic for the pipeline itself (Specification → isolated parallel Research → Deliberation → Evaluation), informed by LangGraph patterns and ADK composition primitives. Use PydanticAI for agent definition and type-safe handoff contracts. Use Temporal for durable execution. This is not a failure of existing tools — it is evidence that Keystone's requirements are genuinely novel.
- Evidence quality: Verified (LangGraph CVE reports, CrewAI GitHub issue verified, AgentLeak benchmark verified); Credible (ADK pre-1.0 status, PydanticAI graph API documented limitations).

**Finding 5: The framework layer is thinning — durable value lies in context engineering, evaluation infrastructure, and observability**
AWS Strands team: "We realized we no longer needed such complex orchestration." Manus rebuilt their agent framework 4 times before getting context management right. Microsoft merged AutoGen and Semantic Kernel in 2026, requiring migration for all existing users. The wrong framework choice cost one startup "6 months of velocity" to rebuild. Better models commoditize orchestration logic — the durable investment is in the layers that do not improve automatically with model upgrades.
- Pipeline layer: All layers (build strategy)
- Build implication: Keystone's investment should concentrate on the Specification Engine, Evaluator, and Rejection Library — these are the layers that compound with engagement history and do not depreciate with model improvements. The orchestration layer should be built for replaceability, not for sophistication.
- Evidence quality: Credible — practitioner observations and industry examples, not controlled studies.

---

## Tool/Framework Verdicts

**LangGraph v1.1.0 (24K stars, Elastic-2.0 for API)**
- Graph-based state machine, Send API for dynamic fan-out, PostgresSaver checkpointing, NVIDIA production validation
- Verdict: LEARN (steal patterns, build on top)
- Justification: The typed state with reducers, conditional edges, and Send API for 15-50 parallel research agents are the best-documented orchestration patterns available and should directly inform L0/L1 custom pipeline design — but security posture (3 CVEs in March 2026, CVSS 9.3) and Elastic-2.0 licensing argue against direct dependency.

**CrewAI v1.12.2 (45.9K stars)**
- Role-based agent teams, @router() decorator, Flows architecture
- Verdict: SKIP
- Justification: The @router() loop-back bug (GitHub issue #1579) breaks exactly the pattern Keystone needs for the Evaluator's reject/regenerate loop; 12M+ execution claims are unverified marketing materials; "prototype in CrewAI, ship in LangGraph" is the practitioner consensus.

**PydanticAI v1.72.0 (15K stars, MIT)**
- Type-safe handoff contracts, auto-re-prompting on schema mismatch, Pydantic Evals, Temporal integration
- Verdict: INTEGRATE (for agent definition and handoff contracts)
- Justification: The strongest "structure over intent" enforcement for L0/L1 handoff contracts — Agent[DepsType, OutputType] generic typing catches schema mismatches at write-time, and auto-re-prompting provides a built-in reject/regenerate primitive at the individual agent level.

**Claude Agent SDK (Python v0.1.51, TypeScript v0.2.86)**
- Session forking, subagent isolation, hooks system, deep MCP integration, rate limits are per-org
- Verdict: INTEGRATE (as execution substrate)
- Justification: The natural execution layer for Claude-native Keystone — session forking enables parallel research agents, hooks system enables quality gates at every execution boundary; critical: plan for Tier 4+ API rate limits or custom invoicing before deploying 15-50 parallel agents.

**Google ADK v0.6.0 (17K stars)**
- SequentialAgent, ParallelAgent, LoopAgent primitives; closest 1:1 mapping to Keystone's pipeline
- Verdict: LEARN (composition pattern only)
- Justification: The SequentialAgent → ParallelAgent → LoopAgent composition is the clearest architectural blueprint for Keystone's pipeline and should be replicated in custom code, but ADK is pre-1.0 (API-breaking changes expected) and optimized for Google/Vertex AI ecosystem.

**OpenAI Agents SDK v0.13.2**
- Handoff architecture with input_filter; guardrails run in parallel; no ParallelAgent primitive
- Verdict: LEARN (handoff pattern and parallel guardrails)
- Justification: The input_filter for context control at handoffs and parallel guardrail execution are patterns worth replicating in custom orchestration; but the framework is vendor-locked to OpenAI with poor Claude support.

**Mastra (22.3K stars, $13M seed, YC W25, TypeScript-only)**
- Processor/tripwire pattern for reject/regenerate
- Verdict: LEARN (tripwire pattern only)
- Justification: The tripwire pattern (intercepts agent I/O at every step, triggers retry with LLM feedback) is the cleanest reject/regenerate implementation found — steal the pattern for the custom orchestration layer; language mismatch (TypeScript) prevents direct adoption.

**OpenAgents**
- Agent networking and discovery between independent services
- Verdict: SKIP
- Justification: Solves the wrong problem (discovery between independent services, not controlled pipeline orchestration); documentation warns it is under active revision with no visible production adoption.

**MCP (Model Context Protocol, Linux Foundation)**
- Under Linux Foundation governance, 97M+ monthly SDK downloads, 20,000+ active servers; 53% use insecure static secrets
- Verdict: INTEGRATE
- Justification: De facto standard for agent-to-tool communication for L1 Research Agents — standardizes access to web search, document analysis, financial data without custom connectors; use MCP gateway with auth overlay to address the 53% insecure-secrets finding.

**A2A Protocol v0.3 (Google-originated, Linux Foundation)**
- 150+ partner organizations; JSON-RPC 2.0; Agent Cards; Tasks lifecycle management
- Verdict: LEARN (adopt later)
- Justification: For Keystone's internal pipeline with known topology, custom handoff contracts are simpler; A2A adds value when agents need to communicate with external systems or when the pipeline topology becomes dynamic.

**AG-UI (CopilotKit)**
- Event-based protocol, SSE/WebSockets, adopted by AWS Bedrock AgentCore and Microsoft Agent Framework
- Verdict: INTEGRATE (for output delivery)
- Justification: Enables token-by-token streaming of final outputs and real-time pipeline progress dashboards for L3 Generation; lightweight and transport-agnostic.

**Temporal (durable execution)**
- Deterministic workflow replay, crash recovery, pause-until-approval
- Verdict: INTEGRATE
- Justification: The key production enabler for long-running research pipelines — offloads I/O to Temporal activities, providing crash recovery and human-in-the-loop approval gates that custom checkpointing cannot reliably replicate.

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Plan says (Section 12):** Implementation roadmap implies using an orchestration framework as the pipeline backbone.
**Evidence shows:** No existing framework natively supports all of Keystone's requirements (strict isolation + reject/regenerate loops + handoff contracts + filesystem-as-state). The correct architecture is PydanticAI for agent definition + Temporal for durable execution + custom pipeline orchestration + MCP for tools + AG-UI for output delivery. This is more specific and different from the plan's implicit "pick a framework" approach.
**Follow:** Follow the evidence. Build custom orchestration for the pipeline itself, using frameworks only where they provide unambiguous value (PydanticAI for type safety, Temporal for durability, MCP for tools).

**Plan says (Section 4.1):** "15-50 parallel research agents" are explicitly described as the target scale.
**Evidence shows:** Anthropic's own system runs 3-5 subagents in parallel, with "more than 10" for complex tasks. Scaling to 50 is beyond their tested range. Rate limits are per-organization (not per key), requiring Tier 4+ or custom invoicing. The coordination tax is exponential — 50 agents create up to 1,225 potential interaction paths without strict isolation.
**Follow:** The 15-50 agent target is valid for ambitious engagements, but start with 5-10 agents and scale up as rate limit and coordination patterns are validated. The strict isolation design (each agent writes to its own directory) is the specific mechanism that keeps coordination complexity linear rather than exponential.

**Plan says (Section 3.1):** File-based task tracking using JSON (research-tasks.json) as the state mechanism.
**Evidence shows:** File-system-as-state is validated by Anthropic's own production recommendation and works well for sequential writes. But Oracle's benchmark confirms that without a central coordinator, parallel agents hit race conditions. The plan should add: advisory file locks for orchestrator read operations and write-ahead logging for crash recovery.
**Follow:** The JSON-based task tracking is correct; add explicit concurrency controls (advisory locks, write-ahead log) to prevent race conditions under parallel execution.

---

## Cross-Report Flags

**Critical finding for all threads:** The 90.2% performance improvement from multi-agent over single-agent Claude (Anthropic's own production data) is the strongest empirical validation of the multi-agent research architecture. This finding should be cited as the anchor for the entire Keystone architecture across all threads.

**Reconcile with A1 on LangGraph verdict:** A1 recommends LangGraph as USE/INTEGRATE for orchestration. A4 recommends LEARN (steal patterns, don't adopt wholesale) due to security concerns and licensing. Both cannot be right. Synthesis agent should resolve: A4's concerns are more thoroughly documented (3 specific CVEs, Elastic-2.0 analysis, security benchmark citations) and should take precedence.

**Reinforces A2 on evaluation cost dominance:** A4's finding that verification consumes 72% of tokens validates A2's tiered evaluation architecture. The cost structure of the Evaluator is the dominant design constraint for the pipeline's economics.

**Potential flag for Thread B and C:** The "framework layer is thinning" finding is relevant for any thread evaluating the long-term moat of the Keystone architecture. The specific claim that "orchestration logic is commoditizing" should inform how Thread C (production/deployment) and Thread D (business model) think about competitive defensibility.

**Informs A5 (Deep Research Tooling):** Rate limit management for 15-50 parallel agents (Tier 4+, prompt caching, Batch API) needs to be costed against A5's per-engagement cost model. The orchestration overhead (rate limit governance, retry management, checkpointing) is a significant infrastructure cost not captured in A5's tool-level pricing.
