# Keystone Intelligence Engine: tooling and architecture deep dive

The Keystone pipeline can be built today for **$11–$136 per engagement** using a stack of Exa + Brave + Firecrawl for retrieval, LangGraph for orchestration, and specialized MCP servers for financial, academic, and government data — all coordinated through the same orchestrator-worker pattern that powers Claude's own Research mode. The commercial deep research landscape has converged on a shared set of architectural patterns (iterative search refinement, extended reasoning, citation-as-first-class-output) while diverging sharply on parallelism strategy, where Claude's multi-agent approach is the only one that matches Keystone's fan-out design. The open-source ecosystem has matured enough that two projects (GPT-Researcher and LangChain's open_deep_research) are production-viable for direct integration, while several others contribute patterns worth stealing — particularly 199-bio's 8-phase pipeline methodology and Cranot's typed knowledge graph with epistemic states. The MCP protocol, now under Linux Foundation governance with support from OpenAI, Anthropic, Google, and Microsoft, provides the unifying integration layer across **20,000+ server implementations**, though security hardening remains essential.

---

## Commercial deep research platforms share a core loop but diverge on parallelism

Every major platform — Claude Research, OpenAI Deep Research, Gemini Deep Research, Perplexity Sonar, and Grok DeepSearch — implements some variant of the Plan → Act → Observe cycle with iterative search refinement. All use extended reasoning or chain-of-thought between tool calls, and all treat citations as first-class output. But the architectures differ in ways that matter for Keystone's design.

**Claude Research** is the only true multi-agent system. A lead agent (Opus 4.6) decomposes queries and spawns **3–10+ parallel subagents** (Sonnet 4.6), each with independent context windows. Subagents search independently, then return compressed findings. A dedicated CitationAgent post-processes everything for source attribution. Anthropic reports a **90.2% improvement** over single-agent Claude on internal research benchmarks, with token usage explaining 80% of performance variance. The key limitation: subagents currently execute synchronously (the lead waits for each batch), and the system uses **~15× more tokens** than single-agent chat.

**OpenAI Deep Research** takes the opposite approach — a single agent running a reinforcement-learning-trained o3 variant through hundreds of reasoning steps. It performs **30–60 web searches** and fetches **120–150 pages** per task, maintaining coherence through sheer model capability rather than architectural decomposition. The interactive clarification phase (using GPT-4o/4.1 for scoping) before research begins is a pattern Keystone should adopt for its Specification Engine.

**Gemini Deep Research** introduces a novel async task manager with shared state that enables graceful error recovery without restarting — critical for Keystone's 15–50 agent deployment. It scales from **80 to 160+ search queries** automatically and leverages a **1M token context window**. The plan-approval step shown in the consumer UI (though not yet available via API) maps directly to Keystone's Specification Engine concept.

**Perplexity Sonar Pro** is architecturally distinct — a pre-composed RAG pipeline optimized for speed (running on Cerebras at ~1,200 tokens/sec) rather than depth. Its **94.3% citation accuracy claim could not be independently verified**; the Tow Center study found ~37% error rate. Sonar Pro scores **0.858 on SimpleQA** and leads Search Arena rankings. Pricing ($3/M input, $15/M output for Sonar Pro) makes it viable as a fast-retrieval component within larger systems, not as a standalone research engine.

**Grok DeepSearch** offers unique access to X/Twitter's real-time data stream but suffers from heavy reliance on X sources of variable quality. DeeperSearch (March 2025) spends ~6.5 minutes per query but results are sometimes worse than standard DeepSearch, per independent testing.

The five patterns most relevant to Keystone: (1) orchestrator-worker with parallel subagents (Claude), (2) interactive clarification before research (OpenAI), (3) async task management with error recovery (Gemini), (4) dedicated citation post-processing (Claude), and (5) budget-driven hard stops with two-tier coverage/cost limits (OpenAI).

---

## Two open-source projects are production-ready; three others contribute essential patterns

The open-source deep research space has exploded since early 2025, with over a dozen significant projects. Two stand out for direct integration.

**GPT-Researcher** (assafelovic/gpt-researcher, **25,600 stars**, Apache 2.0, last commit March 2026) is the most battle-tested option. Its plan-and-solve architecture decomposes research into sub-queries executed in parallel, with a Deep Research mode using tree-like recursive exploration with configurable depth/breadth. The **MCP server (gptr-mcp, 331 stars)** enables any MCP-compatible client to use it as a research tool, and a comprehensive 1,500-line Claude Code skill provides integration patterns. Limitations include context window stuffing issues and lack of built-in source credibility scoring. **Verdict: USE** — integrate via MCP server or pip package.

**LangChain's open_deep_research** (langchain-ai/open_deep_research, **10,800 stars**, MIT) provides the most architecturally relevant blueprint. Its supervisor-agent pattern — where a supervisor splits queries into subtopics, spawns parallel sub-agents, and iteratively checks completeness — maps directly to Keystone's pipeline. It scored 0.4344 on the Deep Research Bench, ranking #6 overall, and offers production-ready state management, persistence, and observability via LangGraph Platform. **Verdict: USE** — as the architectural foundation for Keystone's orchestration layer.

Three projects contribute patterns worth stealing rather than code worth integrating:

**199-bio/claude-deep-research-skill** (65 stars) delivers the most sophisticated methodology design in this space, despite its small community. Its **8-phase pipeline** (Scope → Plan → Retrieve → Triangulate → Outline → Synthesize → Critique → Refine) with loop-back from Phase 6 to Phase 3, **source credibility scoring (0–100)** evaluating domain authority/recency/expertise/bias, **disk-persisted citations** surviving context window resets, and **multi-persona red teaming** (Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer) in the critique phase are all directly applicable to Keystone's Evaluator and Self-Improvement layers. **Verdict: LEARN** — steal the pipeline methodology and credibility rubric.

**Cranot/deep-research** (163 stars) introduces the most intellectually interesting architecture: a typed knowledge graph where research questions become graph nodes with **epistemic states** (CONFIRMED, CONTESTED, SPECULATIVE). Operations like DECOMPOSE, ANSWER, SYNTHESIZE, DETECT, and GROUND transform nodes through declarative strategy compositions. The DETECT operation for identifying blind spots and tensions, and the GROUND operation for web-verified claim checking, map directly to Keystone's Multi-Perspective Deliberation layer. **Verdict: LEARN** — steal the epistemic state tracking and declarative strategy pattern.

**Alibaba-NLP/DeepResearch** (18,600 stars) contributes the **IterResearch paradigm** — reconstructing a streamlined workspace between research rounds to avoid context pollution — which solves one of Keystone's core challenges at scale. **Verdict: LEARN** — study the context management approach.

| Project | Stars | Architecture | Verdict | Key pattern to steal |
|---------|-------|-------------|---------|---------------------|
| GPT-Researcher | 25.6K | Plan-and-solve + tree exploration | **USE** | MCP server, tree exploration |
| LangChain open_deep_research | 10.8K | LangGraph supervisor/sub-agents | **USE** | Orchestration blueprint |
| 199-bio skill | 65 | 8-phase pipeline skill | **LEARN** | Credibility scoring, critique loops |
| Cranot | 163 | Typed knowledge graph | **LEARN** | Epistemic state tracking |
| Tongyi DeepResearch | 18.6K | RL-trained model | **LEARN** | IterResearch context management |

---

## The retrieval layer needs four complementary search APIs, not one

No single search API covers the breadth consulting research demands. The optimal stack combines semantic search, broad web coverage, full-page extraction, and RAG-optimized retrieval.

**Exa ($7/1K searches, $85M Series B at $700M valuation)** should be the **primary search engine**. Its neural embedding approach processes the web into dense vectors on 80 A100s + 144 H200s, enabling semantic queries that return conceptually relevant results rather than keyword matches. Category-based search (`financial report`, `company research`, `personal site`) is a killer feature for consulting — agents can target SEC filings, LinkedIn profiles, or expert blogs with a single parameter. Deep Search ($12/1K) and Deep-Reasoning Search ($15/1K) add multi-hop capabilities. The official MCP server at `mcp.exa.ai` exposes 10+ specialized tools including `company_research_exa`, `research_paper_search`, `competitor_finder`, and `linkedin_search`. Free tier: 1,000 requests/month. **Verdict: USE** as primary search. Confidence: Verified.

**Brave Search API ($5/1K queries)** provides the only independent Western web index remaining after Microsoft retired the Bing Search API in August 2025. Its **30+ billion page index** with 100M+ daily updates excels at news queries and general web coverage. Brave leads the AIMultiple agentic search benchmark with a **14.89 score**. The official MCP server exposes web, news, image, and video search. The free tier was eliminated in February 2026; $5 monthly credits (~1,000 queries) now require a credit card. Brave returns snippets, not full content — pair with Firecrawl or Jina Reader for extraction. **Verdict: USE** as general/news search. Confidence: Verified.

**Firecrawl (~99.5K GitHub stars, AGPL-3.0)** handles what search APIs can't: full-page content extraction, website crawling, and autonomous multi-page research. Five endpoints — Scrape, Crawl, Search, Map, and the unique **Agent endpoint** — cover the full extraction pipeline. The Agent endpoint, powered by Spark 1 models, accepts a research prompt and autonomously plans its own browsing strategy across multiple pages. The official MCP server exposes 12+ tools including `firecrawl_agent` and `firecrawl_deep_research`. Self-hostable via Docker. Standard plan: $83/month for 100K pages ($0.00083/page). **Verdict: USE** for extraction and autonomous browsing. Confidence: Verified.

**Tavily (acquired by Nebius for up to $400M, February 2026)** serves as the RAG-optimized search layer, returning clean structured JSON with summaries, citations, and content highlights already trimmed for context windows. It's LangChain's default search tool with 1M+ monthly SDK downloads. Basic search costs 1 credit (~$0.003); advanced search with content extraction costs 2 credits. The acquisition introduces pricing uncertainty — monitor closely. **Verdict: USE** for RAG pipelines. Confidence: Verified.

**Jina AI (acquired by Elastic, October 2025)** provides the post-retrieval quality layer. The Reader API (`r.jina.ai`) converts any URL to LLM-friendly markdown. Embeddings v5 models (February 2026) are SOTA for their size class with 32K token context and task-specific LoRA adapters. The jina-reranker-v3 (listwise SOTA) should be used to re-rank retrieved results before LLM processing. The official MCP server at `mcp.jina.ai/v1` includes `parallel_search_web`, `parallel_read_url`, and `sort_by_relevance`. Free tier: 10M tokens. **Verdict: USE** for embeddings, reranking, and URL-to-markdown conversion. Confidence: Verified.

**SearXNG (27.4K stars, AGPL-3.0)** aggregates 243 search engines at zero cost when self-hosted. Multiple community MCP servers exist, including one claiming 3× faster performance than Claude Code's native search. Quality depends entirely on configured engines. **Verdict: LEARN** — valuable as a zero-cost fallback for privacy-sensitive or air-gapped deployments. Confidence: Verified.

---

## Browser automation has matured, with Stagehand v3 leading

When search APIs return snippets but the research agent needs full page content, interactive navigation, or data behind JavaScript rendering, browser automation fills the gap.

**Stagehand v3 by Browserbase (21.1K stars, MIT)** is the clear leader. Rewritten from scratch on Chrome DevTools Protocol, it provides four primitives — `act()` for AI-driven interactions, `extract()` for structured data extraction, `observe()` for element discovery, and `agent()` for autonomous multi-page workflows. Action caching eliminates redundant LLM calls (~2× faster, ~30% cost reduction on repeat patterns). Browserbase's cloud infrastructure (**$40M Series B**, $67.5M total) runs **50M+ sessions** for 1,000+ companies including Perplexity and Vercel. Pricing: framework is free; Browserbase cloud starts at $20/month for 100 browser hours. Python, TypeScript, Go, Java, Ruby, Rust, and PHP SDKs available. MCP server launched March 2026. **Verdict: USE.** Confidence: Verified.

**Playwright MCP (Microsoft, Apache-2.0)** provides a free, production-ready foundation using accessibility snapshots rather than vision models for token-efficient page understanding. The new CLI mode is **4× more token-efficient** (27K vs 114K tokens per session). No cloud costs — runs locally. Pair with Browserbase or self-hosted infrastructure for scale. **Verdict: USE** as a cost-optimized component. Confidence: Verified.

**browser-use (83.5K stars, MIT)** dominates GitHub popularity with a pure-autonomy approach — give it a task and an LLM, and it navigates autonomously. The CLI tool achieves ~50ms latency per command. However, a March 2026 supply chain incident (backdoored litellm dependency) raises security concerns, and the pure-autonomy approach is less deterministic than Stagehand's structured primitives. **Verdict: LEARN.** Confidence: Verified.

**Lightpanda (24.1K stars, AGPL-3.0)** is a headless browser built from scratch in Zig — **11× faster, 9× less memory** than Chrome in benchmarks. It runs ~140 concurrent instances per 8GB server versus ~15 for Chrome. MCP protocol support and native markdown output make it excellent for high-volume scenarios. But it's still in beta with incomplete Web API support; expect ~5% error rate requiring fallback logic. **Verdict: LEARN** — monitor for maturity; game-changing at scale once stable. Confidence: Credible.

---

## Academic, financial, and government data have strong free MCP coverage

The specialized data layers for consulting research are surprisingly well-served by free or low-cost APIs with mature MCP integrations.

**Academic access** should combine Semantic Scholar (225M+ papers, AI-powered TLDR summaries, citation classification, free API with multiple community MCP servers) and OpenAlex (278M–470M works, CC0 licensed, 100K+ API calls/day free). For unified multi-source access, **paper-search-mcp** (openags) covers **22+ sources** including arXiv, PubMed, SSRN, CORE, and Zenodo through three tools: `paper_search`, `paper_download`, and `paper_read`. All three are **USE** recommendations with Verified confidence.

**SEC and financial data** centers on **EdgarTools** (MIT, completely free, 2.3M+ PyPI downloads), which provides 13 MCP tools with typed Python objects for 30+ form types. It covers 10-K, 10-Q, 8-K, Form 4, 13F, and DEF 14A filings with standardized XBRL enabling cross-company comparisons and a unique `edgar_monitor` for live filing alerts. For broader market data, Financial Modeling Prep covers 70,000+ securities across 60+ exchanges but its free tier (250 calls/day) is too restrictive for production — the $22/month Starter tier is the minimum viable option. Polygon.io's official MCP server (277 stars) provides composable financial tools with SQL queries on in-memory DataFrames, including built-in Black-Scholes and SMA functions. **EdgarTools verdict: USE. FMP and Polygon: LEARN** until budget justifies paid tiers.

**Government data** is remarkably well-covered by the **lzinga Government Data MCP** — a single server exposing **40+ U.S. federal APIs** through **300+ tools**, covering Treasury, FRED, BLS, BEA, EIA, Census, FEC, Congress, SEC, FBI, World Bank, and CDC data. **18 of these APIs require no API key at all.** The server features selective module loading (`--modules fred,treasury,congress`), disk-backed caching, and WASM-sandboxed code execution that reduces context window usage by 98–100% for large responses. With only 6 GitHub stars, it's an early project requiring verification of critical data, but the architecture is sound. **Verdict: USE with caution.** Confidence: Credible.

---

## Architecture, costs, and the MCP protocol tie everything together

**Retrieval architecture should use specialized MCP servers, not a unified tool.** Anthropic's own research system validates this: "A model loaded with 50 different tools gets confused and performs worse than specialized agents with 5 focused tools." Keystone's Specification Engine should assign each research subagent **3–5 domain-specific tools** based on its task. The MCP protocol provides the unifying integration layer — each search API wrapped in a thin MCP server, each agent connecting only to its assigned servers.

**The real cost of 15–50 parallel agents is viable for consulting economics.** Using Claude Sonnet 4.6 ($3/M input, $15/M output) for research subagents and Opus 4.6 for orchestration:

| Scenario | Agents | Searches/agent | LLM cost | Search API cost | Total |
|----------|--------|---------------|----------|----------------|-------|
| Light | 15 | 5 | ~$7 | ~$0.60 | **~$11** |
| Standard | 30 | 10 | ~$37 | ~$2.40 | **~$40** |
| Deep | 50 | 20 | ~$128 | ~$8.00 | **~$136** |

With **prompt caching** (90% savings on repeated system prompts), **batch API** (50% off non-real-time steps), and **model tiering** (Haiku 4.5 for extraction, Sonnet 4.6 for research, Opus 4.6 only for orchestration), optimized costs drop to **~$7–$85 per engagement**. For a consulting firm charging $5K–$50K per engagement, this represents **0.3–2.7% of revenue**.

**MCP ecosystem maturity is production-ready for core use cases.** The protocol is now under Linux Foundation governance (donated December 2025) with native support from OpenAI, Anthropic, Google, and Microsoft. Approximately **20,000 server implementations** exist, with 2,000+ in the official registry. The TypeScript SDK is at v1.27.x and production-stable; Python SDK is mature. However, a 2025 Invariant Labs audit found **43% of early servers had command injection vulnerabilities** and only 8.5% use OAuth properly — security hardening is non-negotiable for production deployment.

**LangGraph is the recommended orchestration framework.** Its `Send` primitive enables dynamic fan-out/fan-in essential for 15–50 agents, with built-in checkpointing, conditional edges for routing, and the largest production adoption among agent frameworks. For Keystone's scale, a hierarchical pattern prevents orchestrator bottlenecks: the lead agent delegates to 3–5 supervisors, each managing clusters of 5–10 research agents.

**Citation tracking requires a dedicated pipeline stage.** Every research agent should return structured metadata (source URL, retrieval timestamp, search query used, search API, confidence score, corroborating sources) alongside findings. A dedicated CitationAgent — Anthropic's production pattern — post-processes all research to verify every claim maps to a source. Cross-agent corroboration (facts found independently by 2+ agents from different sources) should receive elevated confidence scores.

---

## Mapping every tool to Keystone's six-layer pipeline

| Pipeline Layer | USE (integrate) | LEARN (steal pattern) |
|---------------|-----------------|----------------------|
| **Specification Engine** | LangGraph (orchestration) | OpenAI clarification phase, Gemini plan-approval |
| **Parallel Research Agents** | Exa, Brave, Tavily, Firecrawl, Stagehand v3, EdgarTools, Semantic Scholar, OpenAlex, paper-search-mcp, Gov Data MCP | GPT-Researcher tree exploration, SearXNG fallback |
| **Multi-Perspective Deliberation** | Jina Reranker v3 | Cranot epistemic states, 199-bio multi-persona red teaming |
| **Content Structuring** | GPT-Researcher (output formats), LangChain open_deep_research | 199-bio 8-phase pipeline methodology |
| **Evaluator** | Playwright MCP (verification browsing) | 199-bio credibility scoring (0–100), ContextCite |
| **Self-Improvement Loop** | LangGraph checkpointing | Tongyi IterResearch context reconstruction |

## Conclusion

Keystone's six-layer pipeline aligns remarkably well with the architectural patterns that have emerged across both commercial and open-source deep research systems in 2025–2026. The **most consequential design decision** is the retrieval layer: a stack of Exa (semantic), Brave (broad), Firecrawl (extraction), and domain-specific MCP servers (EdgarTools, Semantic Scholar, Government Data) — with each research agent receiving only 3–5 tools relevant to its assigned task, not the full suite. The **second-most consequential decision** is LangGraph as the orchestration backbone, providing the fan-out/fan-in primitives and checkpointing that 15–50 parallel agents demand.

The cost structure makes this viable at scale: **$7–$85 per optimized engagement** is economically trivial for consulting. The MCP protocol eliminates custom integration work for most tools. The biggest remaining risks are citation accuracy at scale (solved by a dedicated CitationAgent) and MCP server security (solved by input validation, OAuth, and code review of every server used in production). The ecosystem is ready. The question is execution speed.