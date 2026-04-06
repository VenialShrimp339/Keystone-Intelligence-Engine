# Report 5: A5 — Deep Research Tooling & Capabilities

---

## Top Findings

**Finding 1: Consulting-scale research (15-50 parallel agents) is economically viable at 0.3-2.7% of engagement revenue**
Using Claude Sonnet 4.6 for research subagents and Opus 4.6 for orchestration, standard engagement cost is $40 (30 agents, 10 searches/agent). With prompt caching (90% savings on repeated system prompts), Batch API (50% off non-real-time steps), and model tiering (Haiku for extraction, Sonnet for research, Opus only for orchestration), optimized costs drop to $7-$85 per engagement. For a consulting firm charging $5K-$50K per engagement, this is 0.3-2.7% of revenue — essentially free relative to the value delivered. The economic case for full deployment is closed.
- Pipeline layer: L1 (Research Agents), all layers (infrastructure)
- Build implication: Optimize for quality and speed, not cost. At these margins, token-saving micro-optimizations are less valuable than architectural quality investments. Prompt caching is mandatory for throughput management (not cost reduction), and the Batch API is worth using for non-real-time evaluation passes.
- Evidence quality: Verified — pricing from Anthropic's published API rates, cost model is independently reproducible.

**Finding 2: Claude Research is the only multi-agent commercial platform — and its architecture is the direct blueprint**
Every other major platform (OpenAI Deep Research, Gemini Deep Research, Perplexity Sonar Pro, Grok DeepSearch) uses single-agent architectures with extended reasoning. Claude Research is the only true multi-agent system (lead Opus spawning 3-10+ parallel Sonnet subagents with independent context windows). The 90.2% improvement over single-agent Claude and the specific patterns (CitationAgent for post-processing, compressed findings return, model mixing) are directly applicable to Keystone's build because they come from Anthropic's own production experience with the same infrastructure.
- Pipeline layer: L0, L1 (whole research architecture)
- Build implication: The CitationAgent pattern (dedicated agent for post-processing source attribution across all research output) should be added to Keystone's pipeline as a discrete step between L1 (Research) and L1.5 (Deliberation). This is a new discrete pipeline stage not explicitly named in CAPSTONE-PLAN-v2.md.
- Evidence quality: Verified — Anthropic's own reported metrics, corroborated by A4's finding from the same source.

**Finding 3: The retrieval layer requires four complementary APIs — each handles query types the others cannot**
Exa (semantic/category search), Brave (broad web/news), Firecrawl (full-page extraction and autonomous browsing), and Tavily (RAG-optimized structured output) cover non-overlapping query types. No single API handles all consulting research needs. After Microsoft retired the Bing Search API in August 2025, Brave became the only independent Western index at scale — making it irreplaceable for news and general web coverage. Exa's category-based search (targeting SEC filings, company research, academic papers by type) is a capability with no substitute.
- Pipeline layer: L1 (Research Agents)
- Build implication: Build a query router that dispatches to the right provider based on query classification. Each research agent receives 3-5 domain-specific tools (not the full suite), following Anthropic's finding that "a model loaded with 50 different tools performs worse than specialized agents with 5 focused tools."
- Evidence quality: Verified — Brave's Bing displacement is documented; pricing and benchmarks from provider documentation.

**Finding 4: Specialized data MCP servers (EdgarTools, Semantic Scholar, Government Data) eliminate major integration build work**
EdgarTools (MIT, free, 2.3M+ downloads) provides typed Python objects for 30+ SEC form types and live filing alerts — the most comprehensive SEC EDGAR integration available at zero cost. The Government Data MCP exposes 40+ US federal APIs through 300+ tools with 18 requiring no API key and WASM-sandboxed code execution that reduces context window usage by 98-100% for large responses. Semantic Scholar (225M+ papers, AI-powered TLDR summaries, citation classification) pairs with OpenAlex (278M+ works, CC0, 100K+ daily calls free) for academic coverage. These cover the specialized data categories consulting research requires without custom integration work.
- Pipeline layer: L1 (Research Agents)
- Build implication: Use MCP servers for specialized data integration rather than building custom API wrappers. The MCP tool ecosystem is mature enough that building custom connectors for SEC, academic, or government data is unnecessary work.
- Evidence quality: Verified — EdgarTools download counts, API pricing documentation. Government Data MCP has only 6 stars (Credible for architecture, treat as early project requiring verification of critical data).

**Finding 5: Citation tracking requires a dedicated CitationAgent pipeline stage — not just agent-level source logging**
Cross-agent corroboration (facts found independently by 2+ agents from different sources) should receive elevated confidence scores. Each research agent should return structured metadata (source URL, retrieval timestamp, search query used, search API, confidence score, corroborating sources) alongside findings. A dedicated CitationAgent post-processes everything to verify every claim maps to a source. Without this discrete stage, citation accuracy degrades at scale because agents do not have visibility into each other's findings and cannot detect where the same source is being cited through different intermediaries.
- Pipeline layer: Between L1 and L1.5 (new discrete stage)
- Build implication: Add a CitationAgent stage (or CitationProcessor function) that runs after all research agents complete and before Deliberation begins. This stage: deduplicates sources, elevates confidence scores on cross-agent corroboration, verifies URL liveness, and produces the citation manifest that the Evaluator checks against.
- Evidence quality: Credible — Anthropic's own production architecture includes a CitationAgent; the specific benefit (cross-agent corroboration) is logically derived from the multi-agent architecture.

---

## Tool/Framework Verdicts

**Exa ($7/1K standard, $15/1K deep-reasoning, $85M Series B at $700M valuation)**
- Neural search index, category-based search, "Find Similar," 1B+ people/70M+ companies; official MCP server
- Verdict: INTEGRATE
- Justification: Primary semantic search engine for L1 Research Agents — category search targeting SEC filings, company research, and academic papers by type is a capability no other provider offers; the official MCP server exposes 10+ specialized tools directly usable by research agents.

**Brave Search API ($5/1K queries)**
- Independent index (35B+ pages), highest AIMultiple benchmark score (14.89); snippets only (requires extraction layer)
- Verdict: INTEGRATE
- Justification: Primary news and general web coverage for L1 Research Agents — the only independent Western web index after Bing API shutdown (August 2025); pair with Firecrawl or Jina Reader for full-page extraction.

**Firecrawl (~99.5K stars, AGPL-3.0, $83/month for 100K pages)**
- Five endpoints including Agent (autonomous multi-page research), self-hostable, 12+ MCP tools
- Verdict: INTEGRATE
- Justification: Fills the full-page extraction gap that search APIs cannot cover for L1 Research Agents; the Agent endpoint enables autonomous browsing tasks that don't fit search-query patterns; self-hostable for cost control.

**Tavily (acquired by Nebius for ~$400M, February 2026)**
- RAG-optimized structured output, LangChain default, 1M+ monthly SDK downloads; pricing uncertainty post-acquisition
- Verdict: INTEGRATE (with monitoring for pricing changes)
- Justification: Returns clean structured JSON with summaries and content highlights already trimmed for context windows — reduces LLM post-processing work for RAG patterns in L1; monitor pricing following Nebius acquisition.

**Jina AI (acquired by Elastic, October 2025)**
- Reader API (URL → LLM-friendly markdown), reranker-v3 (listwise SOTA), Embeddings v5 (32K context); official MCP server
- Verdict: INTEGRATE
- Justification: The jina-reranker-v3 should be used to re-rank retrieved results before LLM processing in L1 — improves signal quality before agents synthesize; the Reader API is a useful companion to Firecrawl for URL-to-markdown conversion.

**SearXNG (27.4K stars, AGPL-3.0, aggregates 243 search engines)**
- Self-hosted, zero cost, 70+ search services
- Verdict: LEARN (zero-cost fallback)
- Justification: Valuable as a development-phase and privacy-sensitive deployment search layer for L1 agents; quality depends on configured engines; production reliance on SearXNG would sacrifice the benchmark quality of Brave/Exa.

**Stagehand v3 by Browserbase (21.1K stars, MIT)**
- act()/extract()/observe()/agent() primitives, action caching, 50M+ sessions, $20/month cloud
- Verdict: INTEGRATE
- Justification: Best-in-class browser automation for L1 Research Agents requiring full-page interaction, dynamic content, or data behind JavaScript rendering; action caching (~30% cost reduction on repeat patterns) is directly applicable to consulting research with recurring site patterns.

**Playwright MCP (Microsoft, Apache-2.0)**
- Accessibility snapshots, CLI mode (4x more token-efficient than vision), no cloud costs
- Verdict: INTEGRATE (as cost-optimized alternative)
- Justification: For L1 Research Agents with high-volume browser automation needs, Playwright MCP at 27K vs 114K tokens per session (CLI mode) can replace Stagehand for non-interactive extraction tasks while dramatically reducing costs.

**browser-use (83.5K stars, MIT)**
- Pure autonomy, ~50ms latency per command; March 2026 supply chain incident (backdoored litellm)
- Verdict: LEARN
- Justification: The pure-autonomy approach is less deterministic than Stagehand's structured primitives — less suitable for structured consulting research extraction; supply chain incident adds near-term security concern.

**Lightpanda (24.1K stars, AGPL-3.0)**
- 11x faster, 9x less memory than Chrome; ~140 concurrent instances per 8GB; ~5% error rate in beta
- Verdict: LEARN
- Justification: Game-changing for high-volume L1 research scenarios once stable, but ~5% beta error rate requires fallback logic that adds orchestration complexity; monitor for production maturity.

**EdgarTools MCP (MIT, free, 2.3M+ downloads)**
- 13 MCP tools, typed objects for 30+ form types, live filings monitor, edgar_monitor for alerts
- Verdict: INTEGRATE
- Justification: The most comprehensive SEC EDGAR integration available at zero cost — directly covers the SEC filing research category that consulting competitive analysis requires; use as the primary financial filing tool for L1 Research Agents.

**Financial Modeling Prep MCP ($22/month Starter)**
- 70,000+ securities, 60+ exchanges; free tier (250 calls/day) too restrictive for production
- Verdict: LEARN
- Justification: The $22/month Starter tier is the minimum viable for production use; evaluate against the specific securities coverage needed for Keystone's engagements before committing.

**Government Data MCP (lzinga, 6 stars)**
- 40+ US federal APIs, 300+ tools, 18 APIs requiring no key, WASM-sandboxed, disk-backed caching
- Verdict: INTEGRATE (with caution — early project, verify critical data)
- Justification: Covers FRED, BLS, BEA, EIA, Census, and other macro data essential for economic consulting research at zero cost; the architecture is sound but the 6-star community warrants verification of critical data points before relying on it for client deliverables.

**Semantic Scholar (225M+ papers, free API)**
- AI-powered TLDR summaries, citation classification, multiple community MCP servers
- Verdict: INTEGRATE
- Justification: Primary academic paper access for L1 Research Agents — TLDR summaries reduce context consumption while citation classification helps identify primary vs. secondary academic sources.

**OpenAlex (278M+ works, CC0, 100K+ API calls/day)**
- Open-source, many records lack abstracts/affiliations; complements Semantic Scholar
- Verdict: INTEGRATE (paired with Semantic Scholar)
- Justification: Broadest coverage for academic research in L1; pair with Semantic Scholar which has better metadata quality; use paper-search-mcp to unify access across both plus arXiv, PubMed, SSRN.

**paper-search-mcp (openags, 22+ sources)**
- Covers arXiv, PubMed, SSRN, CORE, Zenodo via three tools; BibTeX export
- Verdict: INTEGRATE
- Justification: Single MCP server for unified multi-source academic search across 22+ sources reduces L1 agent tool count for academic research tasks.

**GPT-Researcher open_deep_research (LangChain, 10.8K stars, MIT)**
- LangGraph supervisor-agent pattern, scored 0.4344 on Deep Research Bench (#6 overall), production-ready state management
- Verdict: INTEGRATE
- Justification: The most architecturally relevant open-source blueprint for Keystone's L0/L1 orchestration — the supervisor-agent pattern with LangGraph state management is directly applicable; not used as a dependency but as the primary architectural reference.

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Plan says (Section 4.1):** Research agents "load context just-in-time" and return "1-2 page condensed synthesis" to the pipeline.
**Evidence shows:** The CitationAgent pattern from Anthropic's production system suggests a dedicated post-processing stage for citation handling between L1 and L1.5. The current plan does not name this as a discrete pipeline stage — it implies citations are handled by each agent individually.
**Follow:** Add a CitationAgent (or CitationProcessor) as a discrete stage between Research and Deliberation. This is an improvement to the plan, not a contradiction.

**Plan says (Section 6.2):** A unified retrieval interface `research_search(query, scope=["public", "internal", "historical"])` fans out across all three source categories.
**Evidence shows:** Anthropic's own finding: "a model loaded with 50 different tools performs worse than specialized agents with 5 focused tools." A single unified retrieval interface that exposes all tools to all agents reduces agent performance. The correct pattern is per-agent tool specialization (3-5 domain-specific tools per agent based on assigned task), coordinated by the Specification Engine's agent dispatch.
**Follow:** The unified retrieval interface is a useful human-facing abstraction (the orchestrator routes queries to the right provider), but each research agent should receive only its relevant tools, not the unified interface. This is an architectural refinement, not a fundamental contradiction.

**Plan says (Section 2 architecture diagram):** The pipeline flows directly from L1 (Research) to L1.5 (Deliberation).
**Evidence shows:** A discrete CitationAgent post-processing stage belongs between L1 and L1.5 — this is Anthropic's production pattern and directly addresses the cross-agent corroboration gap.
**Follow:** The architecture should be updated to include CitationProcessor as a named stage (L1 → CitationProcessor → L1.5). This is a new component, not a contradiction.

---

## Cross-Report Flags

**Reinforces A1 on search stack:** A5's four-provider stack (Exa + Brave + Firecrawl + Tavily) directly confirms A1's Brave + Exa + Tavily recommendation with the addition of Firecrawl for extraction. The two reports converge on overlapping search configurations.

**Reinforces A4 on Anthropic architecture validation:** A5's citation of the same Anthropic Engineering blog (90.2% improvement, CitationAgent, model mixing) as A4 strengthens the validation. Both reports independently arrived at the same architectural blueprint from different angles (orchestration vs. tooling).

**New architectural implication for all threads:** The CitationAgent as a discrete pipeline stage between L1 and L1.5 is a new recommendation not in CAPSTONE-PLAN-v2.md. Synthesis agent should evaluate adding this to the plan.

**Cost model enables synthesis:** A5's $7-$85/engagement cost model (with optimization) is the benchmark for synthesis-level economic analysis. Combined with A4's finding that verification consumes 72% of tokens, the expected Evaluator cost per engagement is ~$5-$60, which is within acceptable bounds for consulting economics.

**Potential contradiction with A3 on memory:** A5 does not address memory architecture for the Rejection Library or trajectory storage. A3's Cognee recommendation needs to be evaluated against A5's finding that specialized MCP servers are the preferred integration pattern — is there a Cognee MCP server, or would the memory backend require custom integration outside the MCP ecosystem?
