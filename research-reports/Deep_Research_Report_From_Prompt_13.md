# Data retrieval architecture for the Keystone Intelligence Engine

**The optimal architecture combines Agentic RAG on a Modular RAG framework, pgvector as the primary vector store, MCP as the unified integration layer, and a multi-signal source quality scoring system.** This combination lets research agents autonomously decide what to search, when to search, and how much to trust what they find — the three capabilities that separate a production consulting research system from a demo. The evidence base for these recommendations draws from 40+ papers, production benchmarks, and real deployment data across financial, legal, and enterprise RAG systems through early 2026. Below, every tool and framework carries an explicit USE/LEARN/SKIP tag with a confidence rating.

---

## 1. Agentic RAG on a modular framework is the right architecture

The Keystone pipeline requires agents that dynamically choose data sources, evaluate retrieval quality mid-flight, and orchestrate multi-hop reasoning across SEC filings, news, and academic papers. Three RAG architectures compete for this role.

**Agentic RAG** embeds autonomous AI agents into the retrieval pipeline with four key capabilities: retrieval decisions, relevance evaluation, query rewriting, and multi-step reasoning. The taxonomy includes single-agent, multi-agent, hierarchical, corrective, adaptive, and graph-based variants. Multi-agent RAG — with specialized agents per data source — maps directly to Keystone's design. One vendor reports a **78% reduction in error rates** versus traditional RAG (Claimed — single vendor report). The critical tradeoff: every evaluation step is an LLM call, so production deployments cap retrieval cycles at 3 and use tiered evaluation, routing simple queries to standard RAG and reserving the full correction loop for complex ones. This cuts costs **40–60%**. [**USE** — Confidence: Verified]

**Modular RAG** (Gao et al., arXiv:2407.21059) decomposes RAG into six modules — Indexing, Pre-retrieval, Retrieval, Post-retrieval, Generation, and Orchestration — with LEGO-like composability across linear, conditional, branching, and looping flow patterns. This structural framework should underpin Keystone's pipeline design while Agentic RAG handles orchestration. An open-source implementation exists (Haystack + Hypster). [**LEARN** the structural principles — Confidence: Verified]

**Self-RAG** (Asai et al., ICLR 2024 Oral, top 1%) trains a single LM to adaptively retrieve on demand using reflection tokens. Self-RAG 7B/13B outperforms ChatGPT on open-domain QA. However, it requires fine-tuning a custom model with special tokens — not plug-and-play with commercial LLMs. [**LEARN** the reflection/critique concepts; **SKIP** as a standalone architecture — Confidence: Verified]

The recommended hybrid: use **Modular RAG as the structural framework**, layer **Agentic RAG for multi-agent orchestration** with specialized retrieval agents per data source, and incorporate **Self-RAG-style reflection** as a post-generation validation step within the Evaluator layer rather than fine-tuning custom models.

### Query rewriting decides retrieval quality more than any other component

Four techniques merit production integration, each for a different query type. An adaptive query router should classify incoming queries and apply the appropriate transformation.

**Multi-query generation with RAG-Fusion** generates 3+ query variations from different perspectives, retrieves for each, and applies reciprocal rank fusion (RRF) to merge results. MQRF-RAG benchmarks show P@5 improved ~9% over standard RAG Fusion on AmbigNQ, and FreshQA accuracy exceeded LLM Rewrite by **5.76%**. [**USE** — Confidence: Verified]

**HyDE (Hypothetical Document Embeddings)** generates a hypothetical answer, embeds it, and uses that embedding for retrieval. Effective in zero-shot settings but adds one LLM call of latency. [**USE** for ambiguous queries — Confidence: Verified]

**Query decomposition** breaks complex multi-faceted queries into sub-queries. Essential for consulting queries like "Compare Company A's debt profile to peers" where each company needs independent retrieval. Benchmarks show up to **37% improvement** in relevant retrieval. [**USE** — Confidence: Verified]

**Step-back prompting** generates abstract, higher-level conceptual queries from specific ones. Good for analytical consulting queries where the underlying question is broader than the surface query. [**USE** for analytical queries — Confidence: Credible]

### Hybrid search delivers 15–30% better recall and is non-negotiable for financial documents

Dense vector search alone misses exact identifiers — ticker symbols, CIK numbers, form types, specific financial terms. BM25 alone misses semantic relationships. Hybrid search combining both consistently outperforms either method alone across every benchmark tested.

Consolidated benchmark data tells a clear story. On BEIR aggregate (13 datasets), hybrid search improved NDCG by **26–31%** and MRR from 0.410 to **0.486** (+18.5%). On OpenSearch real-world data, NDCG jumped from 0.69 to **0.82** (+19%). On Weaviate's BRIGHT Biology benchmark, recall improved by **24%**. Financial documents — with their mix of precise identifiers and conceptual analysis — represent an ideal use case for hybrid retrieval.

**Reciprocal Rank Fusion (RRF)** should be the default fusion strategy. It's score-agnostic (uses rank positions, not raw scores), requires no normalization, and has been the industry standard since Cormack et al. (SIGIR 2009). [**USE** — Confidence: Verified]

**Convex combination** (`α × dense + (1-α) × sparse`) outperforms RRF when α is tuned with labeled data (Bruch et al., ACM TOIS 2023). Starting points: α≈0.3 for technical docs with exact identifiers, α≈0.7 for semantic queries. Fifty labeled query-relevance pairs suffice for tuning. [**USE** when labeled data is available — Confidence: Verified]

**Critical warning**: poorly tuned hybrid search can perform *worse* than dense-only. AIMultiple found MRR dropped from 0.410 to 0.390 with untuned fusion, recovering to 0.486 only when optimized. Start with RRF, then tune convex combination weights.

### Structure-aware chunking with contextual enrichment wins for financial documents

Fixed-size chunking splits revenue tables mid-number and separates conditions from conclusions. For SEC filings and consulting documents, **structure-aware chunking** achieved **87.7% context recall** on 10 real SEC filings — the highest of any strategy tested. The key principles:

- **Parse with layout-aware tools**: Docling (IBM, 42K+ GitHub stars, 1.5M monthly PyPI downloads) preserves table structure, headers, and reading order from PDFs. [**USE** — Confidence: Verified]
- **Treat tables as atomic units**: Never split a table across chunks. Convert to markdown for simple tables, HTML for complex tables with merged cells. The Enterprise RAG Challenge winner found markdown optimal for most cases, with **10–15% token savings** versus JSON/XML. [**USE** — Confidence: Verified]
- **Prepend document-level context**: Anthropic's contextual retrieval approach adds LLM-generated summaries to each chunk. Snowflake found this improves retrieval accuracy by **5–10%** on SEC filings. [**USE** — Confidence: Verified]
- **Small-to-large retrieval**: Index 256–512 token chunks for precise semantic matching, then expand to parent sections (1024+ tokens) at generation time. LlamaIndex's HierarchicalNodeParser implements this. [**USE** — Confidence: Verified]

A March 2026 paper on **adaptive chunking** (arXiv:2603.25333) selects the best chunking strategy per document using intrinsic quality metrics, raising RAG answer correctness to **72% from 62–64%** and increasing successfully answered questions by **30%+**. Worth monitoring. [**LEARN** — Confidence: Credible]

**Late chunking** (Jina AI) embeds entire documents first at token level, then segments. Elegant but "tends to sacrifice relevance and completeness" versus contextual retrieval in direct comparison. [**LEARN** — Confidence: Credible]

### Reranking is the single highest-ROI post-retrieval step

Cross-encoder reranking after initial retrieval produces the largest precision gains in the entire pipeline. The February 2026 Agentset benchmark provides the most current comparison:

**Cohere Rerank 4 Pro** holds the #2 ELO (1629) with 614ms latency. Consistently enhances all embedding models. LlamaIndex benchmarks show OpenAI + CohereRerank achieving **0.932 hit rate** and **0.874 MRR**. Enterprise SLAs and 100+ language support. [**USE** as primary API reranker — Confidence: Verified]

**Jina Reranker v2** is the best self-hosted option: 278M parameters (half the size of BGE-reranker-v2-m3), **15× more throughput** than BGE, Flash Attention 2 implementation. Elevates Hit Rate by **+7.9%** and MRR by **+33.7%** on average. Unique function-calling and text-to-SQL awareness for agentic RAG. [**USE** as self-hosted fallback — Confidence: Verified]

**BGE Reranker v2 M3** is fully open-source and frequently offers near-highest MRR. [**USE** as open-source alternative — Confidence: Verified]

**ZeroEntropy zerank-2** holds the #1 ELO (1638) with the fastest latency (265ms), but benchmarks are vendor-run and the project is newer. [**LEARN** — Confidence: Claimed]

The production pipeline: retrieve 50–100 candidates via hybrid search → rerank to top 15–20 with cross-encoder → deduplicate → expand to parent context → reorder into [most relevant → least relevant → second most relevant] to mitigate the lost-in-the-middle problem → structure as JSON blocks with metadata.

---

## 2. pgvector is the right primary vector store; Qdrant is the upgrade path

For a system already on PostgreSQL handling millions (not billions) of documents, the analysis strongly favors keeping vector search in Postgres with a clear upgrade path to a dedicated vector DB if needed.

### pgvector + pgvectorscale handles the Keystone workload with room to grow

**pgvector 0.8.x** introduced iterative index scans — automatically re-scanning the index when filters cause insufficient results — solving the critical "overfiltering" problem that plagued earlier versions. AWS benchmarks show up to **5.7× improvement** in query performance versus v0.7.4. pgvectorscale adds StreamingDiskANN (disk-based ANN inspired by Microsoft's DiskANN), dramatically reducing RAM requirements versus HNSW, plus Statistical Binary Quantization and label-based filtered vector search.

The **471 QPS at 99% recall** benchmark originates from Timescale's methodology on 50M Cohere embeddings (768 dimensions). The authoritative finding: pgvector + pgvectorscale achieved **28× lower p95 latency** and **16× higher throughput** versus Pinecone s1 at 99% recall, at **75% less cost** on AWS EC2. Against Qdrant at 50M vectors, the comparison is tighter: Qdrant showed 1% better p50 latency, **39% lower p95**, and **48% better p99**. Both achieve sub-100ms across all percentiles. [**USE** — Confidence: Verified]

The operational benefits are decisive for Keystone: ACID transactions spanning vector data and relational metadata (filing dates, company IDs, source types); SQL joins between embeddings and structured data; existing backup, monitoring, replication, and security infrastructure; familiar development model with standard PostgreSQL clients and ORMs; row-level security for multi-tenant client isolation; no additional service fees.

**Limitations**: no native horizontal scaling (single-node PostgreSQL), no GPU acceleration, pgvectorscale is not available on AWS RDS (only Timescale Cloud or self-hosted), and heavy vector queries on a shared instance can cause contention — use a dedicated instance or read replicas.

### Qdrant is the strongest dedicated alternative if pgvector hits limits

Qdrant (v1.17.x, Rust, monthly releases) offers **server-side BM25/IDF calculation** (since v1.15.2), first-class hybrid search via the Query API combining dense + sparse + ColBERT late-interaction in a single collection, and the best filtered vector search in the market (payload-aware HNSW traversal, not post-filtering). The 1.5-bit and 2-bit quantization (16–24× compression), ACORN algorithm for filtered HNSW, and million-tenant multi-tenancy make it genuinely production-grade. SOC 2 Type II certified. [**USE** as secondary/upgrade path — Confidence: Verified]

### Other vector databases: where they stand

**Pinecone**: Fully managed, SOC 2 + ISO 27001 + HIPAA certified, zero operational overhead, 99.95% SLA. Excellent compliance story. However, vendor lock-in is total (no self-hosted option), costs escalate significantly above 10M vectors, and there's no SQL integration — requiring a sync pipeline with PostgreSQL. [**LEARN** — Confidence: Verified]

**Weaviate** (v1.35.16): Built-in hybrid search (BlockMax WAND for BM25 + dense, native RRF), native generative search (RAG in a single API call), and multi-tenancy scaling to millions of tenants. Hybrid search boosts NDCG@10 by **42% over pure vector** on MS MARCO. Resource-hungry at scale. [**LEARN** — Confidence: Credible]

**Milvus/Zilliz** (v2.6.11): Designed for billion-scale with GPU acceleration (**50× faster** than CPU HNSW, **21× faster** index builds). Operational complexity is massive (etcd, MinIO, multiple node types, Kubernetes required). [**SKIP** for this use case — Confidence: Verified]

**ChromaDB** (v1.4.1): Rust rewrite delivered 4× speed improvements. Still lacks multi-tenancy, advanced filtering, hybrid search, and compliance certifications. [**SKIP** — Confidence: Credible]

**LanceDB**: Innovative embedded/serverless architecture on the Lance columnar format with DuckDB integration. Cloud offering still in public beta. Used by Harvey AI for legal documents. [**LEARN** — Confidence: Credible]

### The scale threshold decision framework

Below **10M vectors**, pgvector with proper tuning handles everything. At **10–50M**, pgvectorscale's StreamingDiskANN keeps it competitive with dedicated vector DBs. At **50–100M+**, dedicated vector DB advantages in horizontal scaling and distributed indexing become meaningful. At **1B+**, Milvus or Qdrant is strongly recommended. Keystone will likely operate in the low tens of millions — well within pgvector's capabilities.

---

## 3. MCP is the right unified integration layer, but demands defensive engineering

MCP became the **de facto standard** for AI-to-tool integration in 2025–2026. Anthropic donated it to the **Agentic AI Foundation** under the Linux Foundation in December 2025, with platinum members including Amazon, Google, Microsoft, OpenAI, and Bloomberg. The ecosystem now has **10,000+ active public servers**, **97M+ monthly SDK downloads**, and first-class client support in Claude, ChatGPT, Cursor, Gemini, and VS Code.

### The recommended MCP server stack covers all Keystone data sources

**SEC Filings — EdgarTools MCP** [**USE** — Confidence: Verified]: 13 tools across Discover, Examine, and Analyze intents. Covers 10-K, 10-Q, 8-K, Form 4, 13F, DEF 14A, SC 13D/G, and 30+ other form types. Unique features include live filing monitoring, revenue/income/EPS trend analysis with growth rates, side-by-side company comparison, insider trading tracking, and executive compensation parsing. **Free** (MIT license, no API key — only EDGAR_IDENTITY required). Rate-limit aware to SEC's 10 req/sec. This is the single most valuable MCP server for Keystone.

**Financial Data — Financial Modeling Prep MCP** [**USE** — Confidence: Verified]: Real-time quotes across **70,000+ tickers**, 30+ years of historical prices, financial statements, ratios, DCF models, analyst ratings, earnings calendars and transcripts, and economic indicators. Covers stocks, ETFs, mutual funds, forex, crypto, and commodities. Requires API key; free tier provides 250 calls/day, paid starts at ~$19/month.

**Economic Data — FRED MCP Server** [**USE** — Confidence: Verified]: Access to all **800,000+ FRED time series** through 3 focused tools (browse catalog, search series, get observations). Requires free API key. Mature, well-tested, endorsed by financial professionals. More production-ready than the comprehensive government data server for core economic indicators.

**Government Data — us-gov-open-data-mcp** [**USE** — Confidence: Credible]: **36+ U.S. government APIs with 300+ tools** in a single server covering Treasury, FRED, BLS, BEA, EIA, Census, plus FEC, Congress, Federal Register, USAspending, and 25 more agencies. Supports selective module loading (`--modules fred,treasury,bls`) to manage tool definition bloat. Includes WASM-sandboxed JavaScript execution that saves **98–100%** of context window tokens for large responses. Risk: relatively new with a small community and single maintainer. Worth deploying for agencies not covered by the standalone FRED server.

**Academic Research — Academix MCP** [**USE** — Confidence: Credible]: Unified aggregator across OpenAlex (250M+ works), DBLP, Semantic Scholar (200M+ papers), arXiv, and CrossRef (150M+ works). Multi-source search with citation analysis, AI-powered related paper recommendations, and BibTeX export. Free; optional Semantic Scholar API key for higher rate limits.

**Web Search — Exa MCP** (primary) + **Brave Search MCP** (fallback) [Both **USE** — Confidence: Verified]: Exa scores **81% on complex retrieval** (vs 71% for Tavily), is **2–3× faster**, and provides query-dependent highlights that deliver **10% higher RAG accuracy** while sending 50–75% fewer tokens. Brave has an independent web index handling 50M+ searches/day with the highest score on the AIMultiple agentic search benchmark (**14.89**). Tavily as tertiary for news-specific searches. [Tavily: **USE** — Confidence: Credible; SearXNG: **LEARN** — Confidence: Credible]

### MCP failure modes demand a gateway architecture

The case for MCP as the unified layer is strong, but six failure modes require explicit mitigation.

**Context window exhaustion** is the most immediate threat. Connecting 10+ MCP servers means loading 75,000–100,000+ tokens of tool definitions. The fix: deploy an MCP gateway with intelligent tool routing and lazy loading. Load only the tools relevant to the current query (the us-gov-open-data-mcp's `--modules` pattern is a good model).

**Rate limit coordination** doesn't exist natively in MCP. Each upstream API has different limits (SEC: 10/sec, Semantic Scholar: 100/5min, FMP: 250/day free). Build a centralized Redis-backed rate limiter with per-provider configurations.

**Security is alarming**: AgentSeal scanned 1,808 MCP servers and found **66% had security findings** (8,282 tool-level issues). Astrix Security found 53% rely on static API keys. Three CVEs were found in Anthropic's own Git MCP server. Counterfeit npm packages have been published. Mitigation: OAuth authentication, container isolation for each server, tool description auditing, and vetting every server before deployment.

**Stateless scaling** conflicts with MCP's session model. Sessions can't be resumed if routed to different server instances behind a load balancer. The 2026 roadmap addresses this, but current workarounds include session-affinity routing or stateless server design.

**Connection management** matters: shared session pools deliver **10× performance** versus unique sessions per request. Parallel server connection at startup reduces cold-start latency.

---

## 4. Source quality scoring requires a multi-signal composite approach

No single quality metric works in production. Domain authority alone fails because high-authority domains host low-quality pages. Citation count alone is field-dependent and lags by years. Journal impact factor alone correlates with *higher* rates of inflated findings due to publication pressure (documented in Brembs et al., Frontiers in Human Neuroscience). Recency alone prioritizes trending but unverified content over established research.

### The four-tier financial data hierarchy

**Tier 1 (Primary)**: SEC filings (10-K, 10-Q, 8-K) and government statistics (BLS, BEA, Census, FRED). Audited, legally required, standardized XBRL. Highest provenance — "as-filed" without change. Every number should hyperlink to source documents.

**Tier 2 (Verified Secondary)**: Professional data platforms (Compustat, CRSP, Refinitiv, Bloomberg). Aggregated from primary sources with quality control.

**Tier 3 (Analytical)**: Analyst reports, S&P Industry Surveys. Expert interpretation but potential conflicts of interest.

**Tier 4 (Derivative)**: Financial news (Reuters, Bloomberg News, WSJ). Timely but may contain errors or spin.

### Production-ready scoring APIs exist for news and academic sources

**NewsGuard** covers 35,000+ online sources with 0–100 credibility scores assessed by journalists against 9 apolitical criteria. API access via cloud datastream and webhooks. It's the most comprehensive production-ready news credibility API. [**USE** — Confidence: Verified]

**Semantic Scholar API** provides citation counts, influential citations, citation velocity, author h-index, and SPECTER2 embeddings — all freely available at 1,000 req/sec. Already has an MCP server implementation. [**USE** — Confidence: Verified]

**OpenAlex** and **CrossRef** provide complementary bibliometric data with generous free tiers (100K+ calls/day). [**USE** — Confidence: Verified]

For journal-level quality, **SNIP (Source Normalized Impact per Paper)** is the best single metric because it normalizes across citation practices in different fields — critical for a system spanning finance, economics, and technology. [**USE** — Confidence: Verified]

### The recommended composite scoring formula

```
Source_Quality = w1 × Venue_Score + w2 × Author_Score + w3 × Recency_Score 
              + w4 × Citation_Score + w5 × Provenance_Score + w6 × Corroboration_Score
```

Weights should be tuned per source type. For academic sources, Citation_Score and Venue_Score dominate. For news, Corroboration_Score and Provenance_Score matter most (does the article cite primary sources? do multiple outlets confirm it?). For financial data, Provenance_Score dominates (is this the primary filing or a derivative?). The Perplexity-style approach of evaluating trustworthiness, authority, corroboration, and provenance provides the right framework. [**LEARN** the Perplexity pattern — Confidence: Credible]

---

## 5. Architecture patterns that tie everything together

### Query routing: Semantic Router first, LLM fallback for ambiguity

**Semantic Router** (Aurelio AI, MIT license, v0.1.12) uses embedding-based classification to route queries in **<5ms** — versus 200–2000ms for LLM-based routing. Define routes with sample utterances for each data source (SEC filings, news, academic, government statistics). The `retrieve_multiple_routes()` function returns ranked routes with similarity scores, enabling multi-source fan-out for queries that need several sources. [**USE** — Confidence: Verified]

For ambiguous or complex queries where the semantic router has low confidence, fall back to **LLM function-calling routing** (LlamaIndex RouterQueryEngine). This adds latency but handles edge cases correctly. [**USE** — Confidence: Verified]

### Embedding model: Cohere Embed v4 for production, BGE-M3 for self-hosting

**Cohere Embed v4** leads for consulting documents: designed for "noisy real-world data" (formatting issues, scanned docs), **128K token context window** (processes entire SEC filings in one pass), multimodal (text + images for charts), enterprise SLAs, and VPC deployment. MTEB score: **65.2**. Cost: $0.12/M tokens. [**USE** — Confidence: Verified]

**OpenAI text-embedding-3-large** is a strong runner-up with excellent ecosystem integration and configurable dimensions (3072 → 256 via Matryoshka). MTEB score: **64.6**. Cost: $0.13/M tokens. [**USE** — Confidence: Verified]

**BGE-M3** is the best self-hosted option (MIT license, zero API cost): unique multi-function capability producing dense + sparse + multi-vector representations in one model, enabling hybrid search without separate models. Supports 100+ languages and 8192 tokens. Runs on a single GPU (568M params). Slightly lower performance than proprietary models, but domain-specific fine-tuning can close the gap by **10–30%**. [**USE** for self-hosted — Confidence: Verified]

**Jina Embeddings v3**: task-specific LoRA adapters are elegant, and Matryoshka representation from 1024 down to 32 dimensions is useful. Check license terms carefully — v4 is CC-BY-NC-4.0 (non-commercial). [**LEARN** — Confidence: Verified]

**Nomic Embed**: lightweight but drops significantly at 4K+ tokens. Not suitable for long financial documents. [**SKIP** — Confidence: Credible]

### Structured + unstructured data in one pipeline: dual-path retrieval

The core challenge: financial tables need precise numerical retrieval while analyst commentary needs semantic understanding. The answer is a query router that dispatches to the right retrieval path.

**Quantitative queries** ("What was Q3 revenue?") → **Text2SQL** against a structured financial database. LlamaIndex's `SQLAutoVectorQueryEngine` handles this, routing to SQL or vector store or both based on query analysis. ICE/NYSE built this pattern on Databricks for production financial data. [**USE** — Confidence: Verified]

**Qualitative queries** ("Industry outlook?") → **Vector search** against embedded unstructured documents.

**Mixed queries** ("Revenue trends and competitive analysis") → **Both paths** in parallel, with LLM synthesis of combined results.

For **table serialization**: ingest PDFs with Docling, which preserves table structure as markdown. Store tables in two places: raw structured data in PostgreSQL for precise SQL queries, and markdown-serialized versions in the vector store for semantic retrieval. The Enterprise RAG Challenge winner found that additional serialization beyond Docling's native output "not only failed to improve the system but slightly decreased its effectiveness" — more text reduced signal-to-noise ratio. [**USE** Docling — Confidence: Verified]

### Caching: source-aware TTLs with dual-layer architecture

Different data sources have radically different freshness requirements. SEC filings update quarterly (TTL: 90 days, invalidate on new filing event via EDGAR RSS). News updates continuously (TTL: 1–4 hours). Academic papers update sporadically (TTL: 30–90 days). Government statistics follow known release schedules (TTL: matches publication cycle).

**Bifrost** (Maxim AI, open-source) provides gateway-level dual-layer caching — exact hash matching plus vector similarity search — with **per-request TTL and similarity threshold overrides** via HTTP headers. This lets you set different TTLs per data source type without application-level changes. [**USE** — Confidence: Credible]

**GPTCache** (Zilliz) is the most cited semantic caching library but is vulnerable to adversarial embedding-collision attacks (SAFE-CACHE paper, Nature 2026) that reduce reliability. Use with the dual-layer pattern (hash + semantic) rather than semantic similarity alone. [**LEARN** — Confidence: Verified]

Set semantic cache similarity thresholds at **0.85–0.90** for consulting use cases — higher precision than chatbots to avoid serving wrong financial data from semantically similar but factually different queries.

### Rate limiting: Redis-backed per-provider with circuit breakers

With 10+ simultaneous data providers, one flaky source can block the entire pipeline. The pattern: **token bucket rate limiters** per provider (Redis + Lua scripts for atomic operations, <2ms P95 latency at 50K+ req/sec) plus **circuit breakers** per provider (Closed → Open after N failures → Half-Open to probe recovery).

Graceful degradation cascade: provider rate-limited → serve cached results (even slightly stale) → provider circuit open → skip source, note in metadata, proceed with available sources → all providers degraded → return partial results with confidence indicators. Add random jitter (100–500ms) to all retries to prevent thundering herd effects. [**USE** Redis + circuit breaker pattern — Confidence: Verified]

---

## 6. Failure modes that should change architectural decisions

### Multi-hop reasoning is where naive RAG collapses

On the FRAMES benchmark, naive RAG achieves **~40% accuracy** for multi-hop tasks. Agentic RAG reaches ~60%. Plan-based execution (decoupling plan generation from execution) reaches ~100%. This is the single most important architectural insight for Keystone: the Deliberation layer must decompose complex consulting questions into retrieval plans before executing them, not just retrieve and hope. [Confidence: Verified]

### Negative interference from retrieval is real and measurable

Retrieved context can *harm* model performance. Semantically similar but irrelevant documents (distractors) cause false predictions — worse than no retrieval at all for some queries. The fix: aggressive reranking with high precision thresholds, and explicit "insufficient information" detection when no retrieved document meets the relevance bar. [Confidence: Verified]

### Embedding drift is an invisible quality killer

When embedding models are updated, query embeddings become misaligned with indexed document embeddings. Quality degrades gradually — invisible to request-level monitoring. The fix: version-tag every embedding model, maintain a model registry, and trigger automated reindexing when the model changes. Never mix embeddings from different model versions in the same index. [Confidence: Verified]

### MCP security cannot be assumed

**66% of MCP servers have security findings** across a scan of 1,808 servers. 53% rely on static API keys. Tool poisoning attacks hide malicious instructions in tool descriptions — invisible to users but processed by AI models. A counterfeit npm package (`postmark-mcp`) silently forwarded all emails to an attacker before removal. Mitigation is non-optional: OAuth authentication, container isolation per server, audit tool descriptions for hidden instructions, and never deploy unvetted community servers. [Confidence: Verified]

### The chunking-architecture anti-pattern matrix

Five patterns consistently fail in production: (1) fixed token windows that split tables and separate conditions from conclusions; (2) over-retrieval flooding context with irrelevant documents that dilute signal; (3) under-reranking — skipping the cross-encoder step loses the single highest precision gain; (4) single-hop retrieval when multi-hop is needed; and (5) the "index everything" approach that creates poor signal-to-noise ratios. The corrective is structure-aware chunking, two-stage retrieval with reranking, plan-based multi-hop execution, and curated ingestion with source-type-specific processing pipelines. [Confidence: Verified]

---

## Conclusion: the five decisions that matter most

The research yields five architectural decisions that dominate all others for the Keystone Intelligence Engine.

**First, Agentic RAG with Modular RAG structure** is the correct architecture — not because it's trendy, but because consulting research inherently requires agents that decide what to search, evaluate whether the results are sufficient, and iterate. The alternatives (naive RAG, pure Self-RAG) either lack autonomy or require impractical model fine-tuning.

**Second, pgvector + pgvectorscale as primary vector store** with Qdrant as the upgrade path eliminates an entire category of operational complexity. The benchmarks prove it handles tens of millions of vectors at competitive latency, and SQL joins between embeddings and filing metadata are architecturally irreplaceable.

**Third, MCP as the unified integration layer** is correct but requires a gateway architecture with lazy tool loading, per-provider rate limiting, container isolation, and circuit breakers. The seven recommended MCP servers (EdgarTools, FMP, FRED, us-gov-open-data-mcp, Academix, Exa, Brave) cover all required data sources at a total API cost under $100/month.

**Fourth, multi-signal source quality scoring** with separate weight profiles per source type (academic, news, financial, government) is the only approach that works. Single-metric scoring fails predictably. The composite model — leveraging NewsGuard, Semantic Scholar, SNIP, and provenance tracking — creates a defensible credibility layer.

**Fifth, plan-based multi-hop retrieval** in the Deliberation layer is what separates a useful system from one that hallucinates on complex questions. The gap between naive RAG (40%) and plan-based execution (~100%) on multi-hop tasks is the largest performance differential in the entire architecture. Building the Specification Engine to decompose complex queries into retrieval plans before any data is fetched is the single highest-impact engineering investment.