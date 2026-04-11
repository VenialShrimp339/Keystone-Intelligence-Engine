# Deep Research Gap Analysis: LEAK-SYNTHESIS.md vs. Source Reports

*Produced: 2026-04-05 | Session A (read-only audit)*

---

## Executive Assessment

**Completeness estimate: ~60-65%.** LEAK-SYNTHESIS.md captures the six headline patterns well (KAIROS, autoDream, 5-strategy compaction, Tool Search, hooks, fork-mode), the community MCP server inventory is solid, and the cost model refinements are actionable. However, the synthesis was produced by a background agent reading ~60 lines per report for topic ID, then delegating. This shows. The gaps concentrate in four categories:

1. **Security and trust boundaries** (most implementation-impactful): compaction laundering, memory poisoning history, 50-subcommand vulnerability
2. **Quantitative baselines** needed for capacity planning: system prompt overhead (27-31K tokens), subagent startup overhead (20K tokens), team token multipliers
3. **Implementation-level mechanics** needed for building: 7-stage tool dispatch pipeline, three-input-copy separation, five-level MCP config hierarchy, output slot reservation
4. **Ecosystem options** beyond what was cataloged: three additional MCP gateway implementations, model routing tools, ECC instinct-to-skill pipeline

**Decision-changing findings:** 5-6 findings would actually change implementation decisions (flagged below with [DECISION-CHANGING]). The remainder are implementation-relevant detail or nice-to-know context.

---

## Report 1: deep-research-01-agent-teams.md

### Findings missing from or underrepresented in LEAK-SYNTHESIS.md

**1. JSON inbox message type taxonomy (7 types)**
LEAK-SYNTHESIS mentions the mailbox system in one sentence. The report catalogs seven message types: `task_assignment`, `message`, `broadcast`, `shutdown_request`/`shutdown_response`, `plan_approval_request`/`plan_approval_response`, and `idle_notification`. The `plan_approval_request/response` pair directly maps to L1.5 Deliberation quality gates and L4 Evaluator sprint contract enforcement.

- Captured in repo analysis? Partially -- 03-multi-agent.md covers SubAgentManager but not the mailbox message taxonomy.
- Verdict: **ADAPT** the message type taxonomy for Temporal Signals. Map `plan_approval_request/response` to Temporal Signal + query pattern for pipeline boundary gates.
- Components: #9 (Deliberation), #6 (Evaluator), #5 (Specification Engine)

**2. Shared task dependency graph mechanics (blocks/blockedBy/highwatermark)**
LEAK-SYNTHESIS mentions dependency tracking once in the pattern catalog. The report details: auto-incremented IDs via `.highwatermark` counter file, three task states (`pending`/`in_progress`/`completed`), automatic downstream unblocking when blockers complete, `flock()`-based mutual exclusion with 0-byte lock files, and lowest-ID-first claiming preference.

- Captured in repo analysis? Yes -- 04-task-management.md covers the dependency graph in detail (bidirectional graph, thread-safe JSON store). **Not a gap in coverage, just a gap in LEAK-SYNTHESIS.**
- Verdict: Already marked ADOPT in repo analysis. No change needed.
- Components: #5 (Specification Engine)

**3. Token overhead multipliers for multi-agent teams**
LEAK-SYNTHESIS does not quantify coordination costs. The report provides: 3-7x token overhead for teams, ~33% coordination overhead beyond the raw agent multiplier, 3-5 teammates with 5-6 tasks each as the empirical sweet spot, and Anthropic's C compiler benchmark (16 agents, ~2,000 sessions, ~2B input tokens, <$20K total).

- Captured in repo analysis? No.
- Verdict: **ADOPT** the 3-5 agents / 5-6 tasks ratio for Component #7 capacity planning. [DECISION-CHANGING] for cost model validation -- the 33% coordination overhead should be factored into the $12-$100 engagement estimate.
- Components: #7 (Research Agents), #5 (Specification Engine), cost model

**4. Context loss after compaction destroys team awareness (bug #23620)**
LEAK-SYNTHESIS does not mention this. After compaction, the team lead completely loses awareness of its team -- cannot message teammates or coordinate tasks. Team state is not re-injected after summarization.

- Captured in repo analysis? No.
- Verdict: **SKIP** the problem for Keystone (our claim-level IR architecture avoids long-running team sessions), but **ADOPT** the lesson: any compaction in Keystone must preserve pipeline state metadata, not just conversation content. Compaction summaries must include structured fields for active agents, pending handoffs, and pipeline position.
- Components: #7 (Research Agents), META layer

**5. Delegate mode prevents orchestrator scope creep**
LEAK-SYNTHESIS mentions delegate mode briefly in the pattern catalog. The report details: Shift+Tab activates it, restricts the coordinator to coordination-only tools, prevents the lead from grabbing implementation work. Community users reported this as a common failure mode without the restriction.

- Captured in repo analysis? No.
- Verdict: **ADAPT** for Component #5. Implement via PydanticAI tool allow-lists: the L0 orchestrator should be restricted to dispatch tools (task creation, agent spawning, result review) and explicitly blocked from research tools.
- Components: #5 (Specification Engine)

---

## Report 2: deep-research-02-context-management.md

### Findings missing from or underrepresented in LEAK-SYNTHESIS.md

**1. System prompt baseline overhead: 27K-31K tokens before any conversation** [DECISION-CHANGING]
LEAK-SYNTHESIS mentions the system prompt boundary split but never quantifies the baseline cost. Tool definitions alone consume 14K-17.6K tokens (the single largest component). Heavy MCP server usage pushes baseline past 40K tokens. The system is assembled from 110+ separate prompt strings.

- Captured in repo analysis? Partially -- 05-memory-context.md mentions the two-layer compaction but not baseline overhead numbers.
- Verdict: **ADOPT** these numbers for capacity planning. With 200K context windows, a 30K+ baseline means only ~170K for actual work. For L1 research agents using Sonnet (which may have smaller effective windows with thinking tokens), this constraint is tighter. Factor into Component #7 agent design.
- Components: #7 (Research Agents), #4 (MCP Gateway), #5 (Specification Engine)

**2. Compaction laundering: instructions survive compression and become trusted directives** [DECISION-CHANGING]
LEAK-SYNTHESIS does not mention this security finding. Multiple analysts flagged that instruction-like content in repository files (e.g., poisoned CLAUDE.md) can survive compaction, get laundered through the summarization step, and emerge in compressed context as what the model treats as genuine user directives. Straiker AI warned attackers can "craft payloads designed to survive compaction, effectively persisting a backdoor across an arbitrarily long session."

- Captured in repo analysis? No.
- Verdict: **ADOPT** as a design constraint for Component #7. Research agents processing untrusted web content must have compaction summaries filtered for instruction-like patterns before re-injection. Add to acceptance criteria for #7: "Compaction summaries are treated as untrusted input and validated before re-injection."
- Components: #7 (Research Agents), #6 (Evaluator), #4 (MCP Gateway)

**3. Re-injection is deterministic (recency-based via seenIds), not relevance-scored**
LEAK-SYNTHESIS mentions seenIds once but doesn't surface the deliberate architectural choice to use recency over relevance. The report explains: there is no learned relevance scoring model deciding what survives -- recency serves as the heuristic proxy. This trades sophistication for reliability.

- Captured in repo analysis? Partially -- 05-memory-context.md mentions two-layer compaction but not the recency-over-relevance choice.
- Verdict: **ADOPT** for Component #7 compaction design. Recency-based re-injection is simpler and more deterministic than relevance scoring. For Keystone research agents, supplement with claim-level persistence: claims extracted during research should survive compaction regardless of recency.
- Components: #7 (Research Agents)

**4. Memory poisoning vulnerability led to architectural change in v2.1.50**
LEAK-SYNTHESIS does not mention this. In early Claude Code versions, the first 200 lines of MEMORY.md were loaded directly into the system prompt (high authority). After a memory poisoning vulnerability was discovered, Anthropic moved user memories out of the system prompt. Cisco security research confirmed this.

- Captured in repo analysis? No.
- Verdict: **ADOPT** the lesson for META layer / Observation Library design. Observation Library content must never be placed in system prompts with high-authority positioning. Load as tool-accessible context, not system instructions. [DECISION-CHANGING] for Component #7 and META layer: agent context injection of Observation Library findings should use `<user-context>` or equivalent low-authority positioning, not system prompt injection.
- Components: META layer, #7 (Research Agents), #6 (Evaluator)

**5. EXTRACT_MEMORIES: fire-and-forget forked agent at session end**
Not in LEAK-SYNTHESIS. At session end, a fire-and-forget forked agent pulls durable insights from the conversation and writes them to persistent memory, with a manifest of existing memories pre-injected to avoid rediscovery.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for META layer Observation Library. After each L1 agent completes, spawn a lightweight extraction agent to pull structured observations before the agent's context is discarded. This is the "capture" phase that feeds autoDream's consolidation.
- Components: META layer, #7 (Research Agents)

---

## Report 3: deep-research-03-tool-system.md

### Findings missing from or underrepresented in LEAK-SYNTHESIS.md

**1. Seven-stage tool dispatch pipeline**
LEAK-SYNTHESIS catalogs individual patterns (permission gates, hooks, concurrency classification) but never describes the complete 7-stage pipeline: (1) routing via findToolByName, (2) Zod schema validation, (3) semantic validation, (4) input cloning into three copies, (5) PreToolUse hooks, (6) permission gate, (7) execution + PostToolUse hooks. The pipeline is the enforcement architecture, not the individual gates.

- Captured in repo analysis? 02-tool-system.md covers ToolDef and registry but not the dispatch pipeline stages.
- Verdict: **ADOPT** the 7-stage pattern for Component #4 MCP gateway tool dispatch. Implement: (1) tool name routing, (2) Pydantic schema validation, (3) custom validators, (4) input snapshot for audit, (5) pre-execution hooks (sprint contract checks), (6) authorization gate, (7) execution with post-hooks.
- Components: #4 (MCP Gateway), #6 (Evaluator)

**2. Three distinct input copies during tool dispatch** [DECISION-CHANGING]
LEAK-SYNTHESIS does not mention this. The system maintains: (a) the API-bound original (preserved for cache integrity), (b) a backfilled clone for hooks and permission checks, (c) a hook-updated copy for actual execution. This separation prevents hooks from contaminating cached data.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for Component #4. When the MCP gateway processes tool calls through its middleware pipeline (auth, rate limit, circuit breaker, audit), maintain separate copies: one for the audit log (immutable), one for middleware modification (mutable), one for execution (post-middleware). Prevents audit log tampering and cache contamination.
- Components: #4 (MCP Gateway)

**3. Bash error cascading via siblingAbortController while other tool failures are independent**
Not in LEAK-SYNTHESIS. Only Bash tool errors cascade to sibling tools via a shared abort controller. All other tool failures are independent -- one failing web fetch doesn't abort a parallel file read.

- Captured in repo analysis? No.
- Verdict: **ADAPT** for Component #7. In the research agent pipeline, implement selective error cascading: if a critical tool (e.g., the primary data source) fails, cancel parallel calls to dependent tools. But let independent source queries continue even if one source fails.
- Components: #7 (Research Agents), #4 (MCP Gateway)

**4. `tools: []` strips all built-ins, leaving only MCP tools**
Not in LEAK-SYNTHESIS. Setting `tools: []` in the agent definition removes all built-in tools entirely, enabling agents that operate exclusively through a curated MCP tool surface.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for Component #7 agent isolation. L1 research agents should operate exclusively through the MCP gateway, with zero direct built-in tools. All capability comes through the gateway's rate-limited, circuit-broken, audit-logged MCP interface.
- Components: #7 (Research Agents), #4 (MCP Gateway)

**5. Output slot reservation: 8K default auto-escalating to 64K**
Not in LEAK-SYNTHESIS. This saves context in 99% of requests while allowing long-form output when needed. Directly relevant to managing output token costs.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for Component #7. Set initial output budgets conservatively (8K tokens) for L1 research agents, auto-escalate only when the agent produces near-cap output. Prevents the default 32K thinking token waste.
- Components: #7 (Research Agents), cost model

---

## Report 4: deep-research-06-mcp-architecture.md

### Findings missing from or underrepresented in LEAK-SYNTHESIS.md

**1. Five-level MCP configuration hierarchy** [DECISION-CHANGING]
LEAK-SYNTHESIS describes the MCP server inventory but not the configuration architecture. The report details five levels: (1) project .mcp.json (version-controlled), (2) user ~/.claude.json, (3) project-local .claude/settings.local.json, (4) user-local ~/.claude/settings.local.json, (5) enterprise managed-mcp.json. This includes env var expansion syntax (`${VAR}` and `${VAR:-default}`).

- Captured in repo analysis? 06-mcp-implementation.md covers the MCP client but not the configuration hierarchy.
- Verdict: **ADOPT** the multi-level config pattern for Component #4. Implement: project-level MCP config (checked into repo), user-level (personal API keys), and environment-level (deployment overrides). Use env var expansion for secrets.
- Components: #4 (MCP Gateway)

**2. Three additional production MCP gateway implementations**
LEAK-SYNTHESIS covers FastMCP proxy and CHUK Tool Processor. The report adds: (a) **Microsoft MCP Gateway** -- Kubernetes-native with session-aware routing and Azure Entra ID RBAC (`mcp.admin`, `mcp.engineer` roles); (b) **MetaMCP** -- namespace-based grouping with per-agent MCP endpoint subsetting; (c) **Nexus Router** -- Rust-based with tool-level RBAC, OpenTelemetry tracing, and Redis rate limiting via TOML config.

- Captured in repo analysis? No.
- Verdict: **INVESTIGATE** MetaMCP for per-agent tool subsetting (directly relevant to 3-5 tools per agent requirement). **SKIP** Microsoft MCP Gateway (Kubernetes dependency is premature for Phase 1). **INVESTIGATE** Nexus Router's tool-level RBAC pattern (Rust performance + OTel tracing is attractive for production).
- Components: #4 (MCP Gateway)

**3. OAuth 2.1 with Dynamic Client Registration and headersHelper for custom auth**
Not in LEAK-SYNTHESIS. Claude Code stores OAuth client secrets in the system keychain (not config files). The `headersHelper` option runs a shell command and merges output into request headers, enabling custom auth schemes like Kerberos or SSO.

- Captured in repo analysis? No.
- Verdict: **ADOPT** the keychain-based secret storage pattern for Component #4. API keys for Exa, Brave, etc. should never be in config files. **SKIP** headersHelper for Phase 1 (no SSO requirement).
- Components: #4 (MCP Gateway)

**4. list_changed notification support for dynamic tool refresh**
Not in LEAK-SYNTHESIS. When MCP servers declare `{ "capabilities": { "tools": { "listChanged": true } } }`, they emit notifications triggering automatic client re-fetches without reconnection.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for Component #4. Support list_changed notifications so new tools from MCP servers are available to agents without restarting the gateway.
- Components: #4 (MCP Gateway)

**5. Firecrawl and Tavily as additional official hosted MCP servers**
LEAK-SYNTHESIS's MCP inventory covers Exa, Brave, EdgarTools, FRED, Academix, CrossRef, Semantic Scholar, OpenAlex, and doi-mcp. The report adds Firecrawl (official, hosted HTTP, structured web content extraction) and Tavily (official, hosted HTTP, AI-optimized search).

- Captured in repo analysis? No.
- Verdict: **INVESTIGATE** Firecrawl for structured web content extraction (relevant to L1 agents processing company websites, annual reports). **SKIP** Tavily for Phase 1 (overlaps with Exa and Brave). Add Firecrawl to the Phase 2 MCP server expansion list.
- Components: #4 (MCP Gateway), #7 (Research Agents)

---

## Report 5: deep-research-08-cost-architecture.md

### Findings missing from or underrepresented in LEAK-SYNTHESIS.md

**1. 20K tokens of context overhead per subagent before actual work begins**
LEAK-SYNTHESIS quantifies cache economics but not startup overhead. Each subagent carries ~20K tokens (system prompt, tool definitions, CLAUDE.md) before doing anything. For 10 parallel agents, that's 200K tokens of pure overhead.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for capacity planning. With 20K overhead per agent and a 200K context window, an L1 research agent has ~180K tokens of working space. After the 50% compaction threshold, that's ~90K before compaction fires. Factor into Component #7 design: keep system prompts minimal, use Tool Search to defer tool definitions.
- Components: #7 (Research Agents), cost model

**2. Third-party model routing tools (Claude Code Router, Morph Router, claude-router plugin)**
Not in LEAK-SYNTHESIS. Claude Code Router (26.4K GitHub stars) intercepts requests and routes to different models by task type. Morph Router classifies prompts in ~430ms at $0.001/request, claiming 40-60% savings. Claude-router plugin claims 50-70% savings.

- Captured in repo analysis? No.
- Verdict: **INVESTIGATE** Claude Code Router's routing categories (default, background, reasoning, long-context) as a pattern for Keystone's model mixing. **SKIP** using the actual tools (our model routing is architecture-level, not request-level). Extract the classification heuristics for the L0 Specification Engine's agent assignment logic.
- Components: #5 (Specification Engine), cost model

**3. Diminishing returns detection (DIMINISHING_THRESHOLD = 500, 3+ consecutive continuations)**
Not in LEAK-SYNTHESIS. If 3+ consecutive continuations each produce <500 additional tokens, the engine infers the model is stuck and stops. A practical circuit breaker for research agents that spin without progress.

- Captured in repo analysis? No.
- Verdict: **ADOPT** for Component #7. Implement diminishing returns detection in L1 research agents: if 3 consecutive tool calls yield minimal new information (measured by novel claim extraction, not raw token count), terminate the agent and report partial findings.
- Components: #7 (Research Agents), #6 (Evaluator)

**4. Context Collapse as a distinct compaction stage (90% capacity trigger, 95% spawn block)**
LEAK-SYNTHESIS describes 5 compaction strategies but lists Session Memory Compact where the source describes Context Collapse. The report clarifies: Context Collapse projects a collapsed view over a "commit log" of conversation segments, fires at 90% capacity, and blocks new agent spawning at 95%.

- Captured in repo analysis? No.
- Verdict: **ADAPT** the 95% spawn block for Component #7. When an L1 agent's context hits 95% utilization, block new tool calls and force output generation. Prevents the agent from consuming its entire context window without producing extractable findings.
- Components: #7 (Research Agents)

**5. CLAUDE_AUTOCOMPACT_PCT_OVERRIDE for customizable compaction threshold**
Not in LEAK-SYNTHESIS (the synthesis recommends 50% threshold but doesn't mention the override mechanism). The env variable accepts values 1-100 and overrides the default ~83.5% trigger.

- Captured in repo analysis? No.
- Verdict: **ADOPT** the configurability pattern for Component #7. Make the compaction threshold configurable per agent type: 50% for research agents that front-load document reading, 80% for synthesis agents that need more working memory.
- Components: #7 (Research Agents)

---

## Skimmed Reports: Significant Findings Worth Full Analysis

### deep-research-04-harness-architecture.md (PRIORITY: MEDIUM)
- **QueryEngine/query.ts architecture details** (46K + 69K lines): The complete flow from user query to response, including the `while(true)` loop, stop conditions, and state consolidation. Implementation-relevant for Component #5.
- **Explicit word count A/B test** (~1.2% output token reduction from explicit word counts vs. "be concise"): Minor cost optimization but empirically validated.
- **Settings cascade priority order**: Different subsystems resolve priority differently (skills: managed > user > project; MCP: local > project > user; hooks: merge all sources). Relevant for Component #4 configuration design.

### deep-research-05-quality-enforcement.md (PRIORITY: HIGH)
- **Three-tier quality enforcement taxonomy**: Hard structural gates (code), soft prompt-based enforcement (model compliance), hybrid hooks (externalized structural enforcement). This taxonomy directly maps to Keystone's evaluation stack layers. **Warrants full analysis.**
- **Auto-mode Sonnet 4.6 classifier as a critic pattern**: A cheaper, faster model evaluates whether proposed actions match stated intent. Adds latency and cost but provides adaptive, context-aware security. **Directly applicable to L4 Evaluator design** -- use Haiku as a cheap first-pass quality gate before expensive Opus evaluation.
- **Five permission modes in detail**: The `auto` mode's separate classifier call pattern is the most architecturally interesting finding for Keystone's sprint contract enforcement.
- **`{ retry: true }` on PermissionDenied**: Hook can signal a denied action should be retried -- enables transient-condition handling in pipeline gates.

### deep-research-07-self-improvement.md (PRIORITY: HIGH)
- **ECC instinct-to-skill pipeline with confidence scoring (0.3-0.9)**: LEAK-SYNTHESIS mentions ECC in one line. The report details: 100% observation reliability via hooks (vs. 50-80% via skills), Haiku-based pattern detection, confidence decay rate of 0.05, auto-promotion from project to global scope when same instinct appears in 2+ projects with average confidence >= 0.8. **Directly applicable to Observation Library design.** Warrants full analysis.
- **EXTRACT_MEMORIES fire-and-forget agent**: Session-end memory extraction with dedup manifest. Not in LEAK-SYNTHESIS.
- **Decision logging is distributed, not centralized**: No single trajectory storage system. The append-only message array IS the primary state. Relevant to META layer trajectory storage design.

### deep-research-09-community-analysis.md (PRIORITY: LOW)
- **50-subcommand security bypass**: Commands with >50 subcommands skip all security checks (performance cap in bashPermissions.ts). Relevant as a cautionary example for Keystone's tool execution sandboxing. 
- **ULTRAPLAN remote planning**: Offloads L0 spec generation to Opus in a cloud container for up to 30 minutes. Already flagged as INVESTIGATE in LEAK-SYNTHESIS.
- **UDS_INBOX**: Already flagged as INVESTIGATE in LEAK-SYNTHESIS.
- **Community rewrites provide additional reference implementations**: claw-code (Rust + Python), nano-claude-code (Python). Already covered in repo analysis.

### deep-research-10-agent-sdk-hybrid.md (PRIORITY: MEDIUM)
- **Anthropic's 14 engineering posts distilled into 5 principles**: The "How we built our multi-agent research system" post reveals 90.2% improvement with multi-agent Opus+Sonnet, token usage explains 80% of performance variance, 15x more tokens than chat. Partially captured in LEAK-SYNTHESIS's Agent SDK section but the blog post findings are not.
- **PydanticAI v1.74 with native MCP client and TemporalAgent integration**: Confirms the stack choice. Not in LEAK-SYNTHESIS.
- **"Self-evaluation is fundamentally unreliable"**: From Anthropic's March 2026 harness design post. Validates the separate Evaluator architecture. Not in LEAK-SYNTHESIS.
- **Scaling rules from official Anthropic guidance**: 1 agent for simple queries, 2-4 for comparisons, 10+ for complex research. Not in LEAK-SYNTHESIS.

---

## Overall Assessment of LEAK-SYNTHESIS.md Quality

### Completeness: ~60-65%

**What it got right (high confidence, no changes needed):**
- Six headline patterns (KAIROS, autoDream, 5-strategy compaction, Tool Search, hooks, fork-mode): well-captured
- Community MCP server inventory: comprehensive and accurate
- Cost model refinements: fork-mode economics, thinking budget caps, Batch API
- Pattern catalog verdicts: defensible, well-justified
- Build-order impact assessment: correctly identifies no changes to sequence

**What it missed that would change implementation decisions (5-6 items):**
1. Compaction laundering security concern -> adds acceptance criteria to Components #7 and #6
2. Memory poisoning history -> changes Observation Library context injection approach  
3. System prompt baseline overhead (27-31K tokens) -> changes L1 agent context budget calculations
4. Three-input-copy pattern in tool dispatch -> changes MCP gateway middleware design
5. Five-level MCP configuration hierarchy -> changes Component #4 config architecture
6. Auto-mode critic classifier pattern (from report 05, not fully analyzed) -> potentially changes L4 Evaluator first-pass design

**Where gaps are concentrated:**
- **Security/trust boundaries**: 3 of the 5 decision-changing gaps are security-related. The synthesis was optimized for pattern extraction, not threat modeling.
- **Quantitative baselines**: System prompt overhead, subagent overhead, team multipliers, diminishing returns thresholds -- none quantified in synthesis.
- **Implementation-level pipeline mechanics**: The 7-stage tool dispatch, 3-input-copy separation, and output slot reservation are build-relevant details omitted at the "read 60 lines" depth.
- **Ecosystem breadth**: Three gateway implementations, two model routing tools, and two additional MCP servers not captured.

**What it missed that is nice-to-know but wouldn't change decisions:**
- Internal model codenames (Capybara, Fennec)
- Anti-distillation mechanism details
- Undercover mode specifics
- Community rewrite comparisons (already covered in repo analysis)
- Frustration detection regex

### Recommendation

A thorough re-analysis of all 10 reports is warranted. Reports 05 (Quality Enforcement) and 07 (Self-Improvement) have the highest gap density relative to their LEAK-SYNTHESIS coverage. Reports 01, 02, and 03 have significant implementation-relevant detail not captured. Report 08 is reasonably well-covered. Reports 04, 09, and 10 can be analyzed at reduced depth. Report 06 has important MCP gateway details but the headline MCP findings are captured.

Priority ordering for full re-analysis:
1. deep-research-05 (quality enforcement taxonomy maps to evaluation stack)
2. deep-research-07 (ECC instinct-to-skill maps to Observation Library)
3. deep-research-01 (agent teams coordination details)
4. deep-research-02 (context management security findings)
5. deep-research-03 (tool system dispatch pipeline)
6. deep-research-06 (MCP gateway options)
7. deep-research-08 (cost details -- mostly captured)
8. deep-research-10 (SDK hybrid -- confirms stack choice)
9. deep-research-04 (harness internals)
10. deep-research-09 (community analysis -- lowest unique value)
