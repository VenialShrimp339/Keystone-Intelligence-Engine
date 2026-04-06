# Analysis: Report 08 — MCP Tool Ecosystem
*Analyzed: 2026-04-05 | Priority: Tier 3 (LOWER) | Report quality: high*

---

## Executive Summary

This report is well-researched and directly actionable for Component #4. The MCP ecosystem is production-ready at the server level but still maturing at the gateway level. The report delivers on its brief: concrete server inventory, gateway architecture options, and reliability patterns.

Three findings materially affect the existing plan:

1. **Server selection is mostly confirmed, with one meaningful upgrade.** The plan's Academix server should be replaced or supplemented by `paper-search-mcp` (21+ academic sources vs. Academix's 5). This is an unambiguous improvement at no added cost.

2. **IBM ContextForge is the right starting point for the gateway.** Building the MCP gateway from scratch is now a worse option than adapting ContextForge, which already has circuit breakers, rate limiting, Redis federation, and an admin UI. The plan's custom build spec should be reconsidered.

3. **Tool Search deferred loading is critical for the 10K token budget.** With 6+ MCP servers active, the plan's 10,000-token acceptance criterion requires deferred loading. Without it, tool definitions alone exhaust the budget before any research context loads.

The report also confirms all existing tool verdicts (Exa, Brave, Firecrawl, Tavily, EdgarTools, FRED, doi-mcp) and adds two new candidates worth evaluating (Finnhub MCP for free market data, Jina AI MCP for URL-to-markdown fallback).

The one significant limitation: Tavily's February 2026 acquisition by Nebius introduces pricing uncertainty. The plan should confirm Tavily remains viable before integrating it deeply.

---

## Key Findings (ranked by implementation impact)

### 1. IBM ContextForge is a better starting point than building the gateway from scratch

**Finding:** IBM ContextForge (github.com/IBM/mcp-context-forge) provides circuit breakers with Closed/Open/Half-Open states, configurable thresholds, rate limiting, Redis-backed multi-cluster federation, 40+ plugins, and an admin UI. Microsoft's MCP Gateway adds Kubernetes-native routing, Azure Entra ID RBAC, and OpenTelemetry integration. Both are production-quality open-source.

**Evidence quality:** Credible. Active GitHub projects from enterprise-tier organizations. No production case studies cited for these specific tools, but implementations are well-documented and concrete.

**Verdict: ADAPT.** Start with IBM ContextForge as the gateway foundation rather than building `mcp_gateway.py` from scratch. The Component #4 spec calls for circuit breakers, rate limiting, Redis-backed rate limiting, per-provider circuit breakers, and an audit log — ContextForge already has all of these. The build effort shifts from implementing these primitives to configuring ContextForge with Keystone-specific tool authorization logic.

**Impact on Component #4:** The existing spec's custom `mcp_gateway.py`, `rate_limiter.py`, and `circuit_breaker.py` may be reducible to ContextForge configuration + a thin Keystone authorization wrapper (`auth.py`) that reads `assigned_tools[]` from research-tasks.json. This is a scope reduction, not a shortcut — the architecture remains correct, the implementation depth decreases. If ContextForge proves too heavyweight or its abstraction model conflicts with the Keystone authorization contract, fall back to the custom build. Decision point: evaluate ContextForge in the first week of Component #4 build; decide within 2 days.

**Caution:** ContextForge also federates A2A (Agent-to-Agent) and REST/gRPC APIs. Do not adopt those layers. Use only the MCP routing, circuit breaking, rate limiting, and observability plugins. The federation and admin UI complexity should be stripped to minimum.

---

### 2. Tool Search deferred loading is required to meet the 10K token acceptance criterion

**Finding:** Anthropic's Tool Search API (beta) marks tools with `defer_loading: true` so they are searched via regex/BM25 at call time rather than loaded upfront. This reduces tool token usage from ~77K tokens (50+ tools) to ~8.7K tokens — an 85% reduction. The acceptance criterion for Component #4 requires tool descriptions under 10,000 tokens with 8+ MCP servers connected.

**Evidence quality:** Credible. Anthropic beta documentation. The AIRIS MCP Gateway claims 97% token reduction with 60+ tools behind 7 meta-tools via progressive disclosure — corroborating the approach independently.

**Verdict: ADOPT.** The plan already includes progressive Tool Search loading in the Component #4 spec (`tool_loader.py`). This finding confirms it is not optional — it is required to hit the acceptance criterion. The implementation direction is correct.

**Risk:** Tool Search is currently Claude-exclusive. If the Evaluator's cross-model ensemble (settled decision: cross-provider diversity required) uses non-Claude models, those models cannot use Tool Search and will require direct tool schema injection. Design the gateway's tool loading as an abstraction: Claude agents use deferred loading, non-Claude agents receive pre-selected tool subsets. The 3-5 tools-per-agent constraint already limits context for non-Claude agents.

---

### 3. Replace Academix with paper-search-mcp as primary academic aggregator

**Finding:** The plan specifies Academix (`xingyulu23/Academix`) with 5 sources (OpenAlex, DBLP, Semantic Scholar, arXiv, CrossRef). `paper-search-mcp` (openags) aggregates 21+ sources including PubMed, SSRN, Zenodo, HAL, Unpaywall, and a free-first fallback chain for full-text downloads. `academic-mcp` (LinXueyuanStdio) adds Springer, IEEE, and Scopus support.

**Evidence quality:** Credible. GitHub projects with documented source lists. Both are in beta, not production-rated.

**Verdict: ADAPT.** Replace Academix with `paper-search-mcp` as the primary academic search MCP. Academix's 5-source coverage is a strict subset. `paper-search-mcp`'s free-first fallback chain for full-text is particularly valuable for consulting research where PDFs are needed. Retain `doi-mcp` alongside it for citation verification (already in the plan). Add the Semantic Scholar MCP specifically for citation graph navigation if deep citation network traversal becomes a research task requirement (not needed for MVP).

**Impact on Component #4:** Update the configured servers list: replace `xingyulu23/Academix` with `openags/paper-search-mcp`. The stdio transport and free tier are unchanged from a gateway configuration perspective.

---

### 4. Finnhub MCP should replace the undefined market data slot

**Finding:** The current plan's financial data stack covers EdgarTools (SEC filings) and FRED (macro data) but leaves market data unspecified. Finnhub MCP offers 60 requests/minute on its free tier — the most generous free rate limit among market data providers. It covers real-time US stock quotes, fundamentals, and ESG data. Financial Modeling Prep (FMP) offers 250 API calls/day with financial statements and ratios. Alpha Vantage dropped to 25 requests/day on its free tier, making it insufficient.

**Evidence quality:** Credible. Free tier limits are current as of the report (2026). Alpha Vantage's drop from 500 to 25 requests/day is documented.

**Verdict: ADOPT Finnhub as the market data MCP.** 60 requests/minute is workable for a 3-5 agent system running consulting research (not high-frequency trading). FMP at 250/day is a reasonable supplement for financial statement queries. Do not integrate Alpha Vantage (25/day is effectively unusable for multi-agent parallelism).

**Impact on Component #4:** Add `mcp-finnhub` (cfdude) to the configured servers list. For engagements requiring more detailed financial statements, add FMP MCP as a secondary. Both are stdio transport, free tier.

---

### 5. Security scanning is mandatory before gateway registration

**Finding:** A security scan of 8,000+ MCP servers found 36.7% with SSRF vulnerabilities and 43% with unsafe command execution paths. Pinterest's production deployment (the best-documented MCP-at-scale case) uses allowlists (not blocklists), two-layer authentication (end-user JWTs + service mesh identities validated by Envoy), and mandatory Security/Legal/Privacy/GenAI reviews before any server reaches production.

**Evidence quality:** Credible. Pinterest case study is concrete (66,000 invocations/month, 844 users). The 36.7% SSRF figure references an unspecified scan corpus — treat as directional, not precise.

**Verdict: ADOPT the allowlist approach.** The plan already specifies per-agent tool authorization via assigned_tools[]. Extend this to the gateway registration layer: only servers that have been explicitly reviewed and registered may be added to the tool registry. No dynamic server addition at runtime. For Keystone's MVP (6 pre-selected servers, all well-known), this is a configuration policy, not a major implementation change.

**Practical implication for the build:** Add a `security_approved: boolean` field to the tool registry schema. Gate `tool_registry.py`'s registration function to reject servers without this flag. For MVP, hand-approve all 6 planned servers. This creates the right architectural pattern without requiring a full automated scanning pipeline in Phase 1.

---

### 6. The MCP Reliability Playbook specifies the circuit breaker parameters to use

**Finding:** The MCP Reliability Playbook (github.com/alexey-tyurin/reliable-mcp, Google Cloud community, March 2026) documents concrete parameters: exponential backoff with jitter using `min(200ms × 2^attempt, 5000ms) ± 30%`, per-operation timeout budgets (MCP tool call: 10s, cache: 500ms, overall: 15s), and rolling error-rate windows for circuit breaker triggers. The existing Component #4 spec requires circuit breakers that open after 3 consecutive failures and retry after 30s.

**Evidence quality:** Credible. Google Cloud community publication, March 2026.

**Verdict: ADOPT these parameters directly.** The plan's "3 failures, retry after 30s" spec is reasonable but incomplete. Supplement with:
- Exponential backoff: `min(200ms × 2^attempt, 5000ms) ± 30%` jitter (prevents thundering herd)
- Tool call timeout: 10s (not infinite)
- Overall budget: 15s per tool call cycle including retries
- Cache operation timeout: 500ms

These are not architectural changes — they are configuration values for the circuit_breaker.py and rate_limiter.py modules. Add them to the Component #4 spec directly.

---

### 7. The Exa + Firecrawl core is confirmed; Jina AI MCP is a free fallback for extraction

**Finding:** The report confirms the Exa → Tavily → Brave search layer and Firecrawl → Jina → Fetch extraction layer as the recommended architecture. Anthropic's Fetch MCP server has ~26 million installs and is the #2 most-used MCP server. Jina AI's `read_url` tool converts URLs to markdown without requiring an API key.

**Evidence quality:** Verified for Exa, Brave, Firecrawl (confirmed by existing verdicts + report corroboration). Credible for Jina AI (official vendor MCP, free tier documented).

**Verdict:** All existing tool verdicts (Exa: INTEGRATE, Brave: INTEGRATE, Firecrawl: INTEGRATE, Tavily: INTEGRATE) are confirmed. Add **Jina AI MCP: INTEGRATE** as a free fallback for URL-to-markdown conversion when Firecrawl's rate limits are hit or for low-priority extraction tasks. Add **Fetch MCP (Anthropic): INTEGRATE** as the baseline free fallback.

**Tavily caution:** The February 2026 Nebius acquisition is a real risk. Tavily's RAG-optimized output is genuinely useful for the pipeline (LLM-ready structured content), but do not make it architecturally required. Treat it as an enhancement over Exa, not a dependency. If pricing becomes prohibitive, Exa + Firecrawl covers the same function.

---

### 8. Bing retirement and Google sunsetting make Brave structurally non-optional

**Finding:** Bing Search API was retired in August 2025. Google Custom Search is sunsetting in January 2027. Brave Search is now the only independent Western search index at scale. Its free tier was eliminated; the minimum is now $5/month.

**Evidence quality:** Verified. Bing retirement and Google sunsetting are documented facts.

**Verdict:** This changes Brave's status from "independent alternative" to "the only remaining non-proprietary index." Exa uses neural embeddings over a crawled index (not the open web in real time). Brave provides the traditional keyword-match view of the live web that no other affordable option offers. The $5/month cost is trivial relative to the $12-$100 per-engagement cost target. This is a must-have, not a nice-to-have.

**No plan change required** — Brave is already an INTEGRATE verdict. This finding elevates the justification and removes the option of skipping it.

---

### 9. Streamable HTTP is the production transport; stdio works only for local servers

**Finding:** The MCP spec v2025-11-25 uses Streamable HTTP (single endpoint, POST + GET, optional SSE) as the production remote transport, replacing the deprecated HTTP+SSE transport. stdio (subprocess communication) works for locally-hosted servers only. Session management uses `Mcp-Session-Id` headers with stream resumability.

**Evidence quality:** Verified. Official MCP spec v2025-11-25.

**Verdict: ADOPT Streamable HTTP for all remote-hosted servers (Exa, Brave, Firecrawl, Tavily); use stdio for local servers (FRED, EdgarTools, paper-search-mcp).** This is already partially reflected in the plan. Ensure the gateway's transport abstraction handles both cleanly — the tool registry should record `transport_type: enum["stdio", "streamable_http"]` per server and route accordingly.

---

### 10. The official MCP registry and governance model are stable enough to rely on

**Finding:** The MCP spec governance moved to the Linux Foundation's Agentic AI Foundation (December 2025), co-founded by Anthropic, Block, and OpenAI. The official registry (registry.modelcontextprotocol.io) reached v1.0.0 with namespace authentication. 9 core maintainers, 58 supporting maintainers, 2,900+ contributors. 97 million cumulative SDK downloads.

**Evidence quality:** Verified. Linux Foundation announcement is a public event.

**Verdict: No action required.** This is directional signal that MCP is not a fad. The multi-org governance reduces single-vendor lock-in risk (though Anthropic's Tool Search beta is still Claude-exclusive — a separate risk tracked in Finding #2). Proceed with MCP as the confirmed tool integration standard per Jack's directive.

---

## Architectural Decisions This Enables

**Gateway build strategy:** The report resolves the "build vs. adapt" question for Component #4. IBM ContextForge provides the missing primitives (circuit breakers, rate limiting, Redis federation) that would otherwise require significant custom implementation. The recommended approach: evaluate ContextForge in the first 2 days of the Component #4 build sprint. If it fits, strip to the required features and wrap with Keystone's authorization logic. If it conflicts with the authorization contract, fall back to the custom build.

**Final MVP server set (6 servers):**
1. Exa MCP (primary semantic search, remote Streamable HTTP)
2. Brave Search MCP (independent keyword index, remote HTTP)
3. EdgarTools MCP (SEC filings, local stdio)
4. FRED MCP (macroeconomic data, local stdio)
5. paper-search-mcp (academic search, 21+ sources, local stdio) — replaces Academix
6. doi-mcp (citation verification, local stdio)

**Supplementary servers for engagements requiring them (not in MVP gateway config by default):**
- Finnhub MCP (market data, free 60/min)
- Firecrawl MCP (full-page extraction, self-hostable)
- Jina AI MCP (URL-to-markdown fallback, free)
- Fetch MCP / Anthropic (basic URL fetch, free, unlimited)

**Tool Search architecture:** All agents use deferred loading. Non-Claude agents in the evaluator ensemble receive pre-selected subsets of 3-5 tool schemas directly. The abstraction must be built at the `tool_loader.py` layer, not at the agent layer.

---

## Changes to Existing Plan

| Area | Current Plan | Change | Priority |
|------|-------------|--------|----------|
| Component #4: Configured servers | Academix (`xingyulu23/Academix`) | Replace with `paper-search-mcp` (openags) — 21+ sources vs. 5 | HIGH |
| Component #4: Gateway implementation | Build mcp_gateway.py, circuit_breaker.py, rate_limiter.py from scratch | Evaluate IBM ContextForge first; adapt if viable, build if not | MEDIUM |
| Component #4: Circuit breaker parameters | "3 failures, retry after 30s" | Add: 10s tool call timeout, 15s overall budget, exponential backoff with jitter formula from MCP Reliability Playbook | MEDIUM |
| Component #4: Configured servers (new) | No market data server specified | Add Finnhub MCP (free, 60/min) as the market data server | MEDIUM |
| Component #4: Tool registry schema | Not specified | Add `transport_type` and `security_approved` fields per server record | LOW |
| Existing verdict: Academix | BUILD | Downgrade to SKIP (superseded by paper-search-mcp) | HIGH |
| New verdict: paper-search-mcp | Not in plan | INTEGRATE (replace Academix) | HIGH |
| New verdict: Finnhub MCP | Not in plan | INTEGRATE (market data, free tier) | MEDIUM |
| New verdict: Jina AI MCP | Not in plan | INTEGRATE as extraction fallback (free, no key required) | LOW |
| New verdict: Fetch MCP (Anthropic) | Not in plan | INTEGRATE as baseline fallback (free, unlimited, ~26M installs) | LOW |

---

## Open Questions Remaining

**1. IBM ContextForge authorization compatibility.** ContextForge's authorization model uses RBAC roles, not per-agent tool lists read from research-tasks.json. Does ContextForge support a plugin or hook that lets Keystone inject its own authorization check (agent_id → assigned_tools[])? This determines whether ContextForge is adaptable or must be bypassed.

**2. Tavily post-acquisition pricing.** The Nebius acquisition (February 2026) is recent. Tavily's pricing and API terms may have changed or be in flux. Before integrating Tavily, confirm current pricing and API stability. If Tavily raises prices or restricts access, the fallback is Exa + Firecrawl (coverage slightly reduced for RAG-formatted output, but viable).

**3. paper-search-mcp maturity.** Rated "Beta" in the report. The report gives it the strongest endorsement of the academic aggregators, but does not document production usage at scale. Before relying on it as the sole academic server, verify it handles concurrent requests from 3-5 agents without rate-limiting or stability issues. Test against Academix in a load test scenario.

**4. Tool Search beta status.** Anthropic's Tool Search API is currently beta and Claude-exclusive. The plan's 10K token acceptance criterion depends on it. What is the production timeline? Is there a fallback if it remains beta during the Phase 1 build window? The fallback (AIRIS-style meta-tool pattern: 7 meta-tools wrapping 60+ tools) should be documented as a contingency in Component #4.

**5. US Gov Open Data MCP scope.** The report flags this server as covering 300+ tools across 40+ APIs. The existing plan flags it with "caution" for the same reason. The MCP Security Standard at Pinterest only allows registry-listed servers. This server is described as Beta. Decision needed: include in the registry for specific engagements (e.g., public sector work) under a separate authorization policy, or exclude until it reaches production maturity.
