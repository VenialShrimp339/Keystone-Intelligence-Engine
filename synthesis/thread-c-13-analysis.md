# Report 13: C4 — Data Retrieval Architecture

**Source report:** `research-reports/Deep_Research_Report_From_Prompt_13.md`
**Prompt:** Research RAG architectures, vector store selection, MCP integration layer, source quality scoring, query routing, embedding models, and caching strategies for the Keystone retrieval layer.

---

## Top Findings

**Finding 1: Plan-based multi-hop retrieval is the highest-impact engineering investment in the entire architecture.**
- Pipeline layer: L0 (Specification Engine), L1 (Research), L1.5 (Deliberation)
- FRAMES benchmark: naive RAG achieves ~40% accuracy on multi-hop tasks; Agentic RAG reaches ~60%; plan-based execution (decoupled plan generation from execution) reaches ~100%. This is the largest performance differential in the architecture.
- Evidence quality: Verified (FRAMES benchmark, empirical with reproducible methodology)
- Build implication: The Specification Engine's decomposition into research-tasks.json is not just an organizational convenience — it IS the plan-based multi-hop retrieval mechanism. The decomposition that happens before any agent spawns directly determines retrieval accuracy on complex consulting queries ("Compare Company A's debt profile to peers" requires independent retrieval per company, not a single query). The 40% vs. 100% gap means the plan's L0 design decision (decompose first, retrieve second) is empirically the highest-leverage architectural choice.

**Finding 2: pgvector + pgvectorscale handles Keystone's workload with 28x lower latency than Pinecone at 75% less cost.**
- Pipeline layer: L1 (Research), L0 (Specification, retrieval interface)
- Timescale benchmarks on 50M Cohere embeddings (768 dimensions): pgvector + pgvectorscale achieved 28x lower p95 latency and 16x higher throughput vs. Pinecone s1 at 99% recall, at 75% less cost. pgvector 0.8.x iterative index scans solve the "overfiltering" problem. Keystone operates in the low tens of millions of vectors — well within pgvector's capabilities. Against Qdrant at 50M vectors: Qdrant showed 39% lower p95 and 48% better p99, both achieving sub-100ms.
- Evidence quality: Verified (Timescale benchmarks, methodology-specified)
- Build implication: Build on pgvector as primary vector store. The operational benefits are decisive: ACID transactions spanning vector data and relational metadata (filing dates, company IDs, source types); SQL joins between embeddings and structured data; existing infrastructure (backup, monitoring, replication). Qdrant is the upgrade path at 50-100M+ vectors, but Keystone won't need it at launch. Do NOT use Milvus (requires Kubernetes, designed for billion-scale) or ChromaDB (missing multi-tenancy, hybrid search, compliance certifications).

**Finding 3: 66% of MCP servers have security findings — the integration layer requires a gateway architecture with defensive engineering.**
- Pipeline layer: L1 (Research), L0 (Integration)
- AgentSeal scan of 1,808 MCP servers: 66% had security findings (8,282 tool-level issues). 53% rely on static API keys. Three CVEs found in Anthropic's own Git MCP server. Counterfeit npm packages silently exfiltrating data. Tool poisoning attacks hide malicious instructions in tool descriptions invisible to users. Context window exhaustion risk: connecting 10+ MCP servers loads 75,000-100,000+ tokens of tool definitions.
- Evidence quality: Verified (empirical scan data, specific CVEs documented)
- Build implication: MCP is the right integration layer (de facto standard, Linux Foundation governance, 97M+ monthly downloads, 10,000+ public servers), but requires non-negotiable mitigations: OAuth authentication, container isolation per server, audit all tool descriptions for hidden instructions, never deploy unvetted community servers, Redis-backed rate limiter with per-provider configurations, circuit breakers per provider. Only the seven specifically recommended servers (EdgarTools, FMP, FRED, us-gov-open-data-mcp, Academix, Exa, Brave) should be deployed — all vetted.

**Finding 4: Hybrid search with RRF is non-negotiable for financial documents; under-reranking is the most common production failure.**
- Pipeline layer: L1 (Research)
- BEIR aggregate (13 datasets): hybrid search improved NDCG by 26-31%. OpenSearch real-world data: NDCG jumped from 0.69 to 0.82 (+19%). Weaviate's BRIGHT Biology benchmark: +24% recall. Financial documents — with their mix of precise identifiers (ticker symbols, CIK numbers) and conceptual analysis — represent the ideal hybrid search use case. Critical warning: poorly tuned hybrid search performs worse than dense-only (MRR dropped from 0.410 to 0.390 with untuned fusion, recovering to 0.486 only when optimized).
- Evidence quality: Verified (multiple independent benchmarks across different retrieval systems)
- Build implication: Implement hybrid search (dense + sparse BM25) with Reciprocal Rank Fusion as the default, then tune convex combination weights when labeled data is available. The cross-encoder reranking step (Cohere Rerank 4 Pro or Jina Reranker v2) is the single highest-ROI post-retrieval step and must not be skipped.

**Finding 5: Docling + structure-aware chunking achieves 87.7% context recall on SEC filings — fixed-size chunking is a quality antipattern.**
- Pipeline layer: L1 (Research), L0 (Data ingestion)
- Structure-aware chunking achieved 87.7% context recall on 10 real SEC filings vs. worse performance from fixed-size chunking. Docling (IBM, 42K+ GitHub stars, 1.5M monthly PyPI downloads) preserves table structure, headers, and reading order from PDFs. Enterprise RAG Challenge winner: markdown optimal for most tables, with 10-15% token savings vs. JSON/XML. Contextual retrieval (Anthropic approach, adding LLM-generated summaries to each chunk): 5-10% retrieval accuracy improvement on SEC filings. Small-to-large retrieval (index 256-512 token chunks, expand to 1024+ token parent sections at generation).
- Evidence quality: Verified for context recall benchmark; Verified for Docling (IBM, production scale)
- Build implication: Use Docling as the PDF parser for all financial documents. Never split tables across chunks. Prepend LLM-generated document-level context to each chunk (Anthropic contextual retrieval pattern). Use small-to-large retrieval via LlamaIndex's HierarchicalNodeParser. This setup directly addresses the financial document parsing requirement for SEC filings in the plan's data source stack.

---

## Tool/Framework Verdicts

**EdgarTools MCP**
- Version/maturity: MIT license, free, 13 tools, 30+ form types; rate-limit aware to SEC's 10 req/sec
- What it does: SEC EDGAR integration; 10-K, 10-Q, 8-K, Form 4, 13F; live filing monitoring; revenue/income/EPS trend analysis; insider trading tracking; executive compensation parsing
- Verdict: BUILD — highest-value MCP server for Keystone; covers the primary data source for consulting research; free, well-maintained, comprehensive; deploy first

**Financial Modeling Prep MCP**
- Version/maturity: Free tier 250 calls/day, paid ~$19/month; 70,000+ tickers; production
- What it does: Real-time quotes, 30+ years historical prices, financial statements, ratios, DCF models, analyst ratings, earnings transcripts, economic indicators
- Verdict: BUILD — deploy as primary financial data provider alongside EdgarTools; the $19/month paid tier is trivial for production research system

**FRED MCP Server**
- Version/maturity: Mature, well-tested; free API key; endorsed by financial professionals
- What it does: Access to 800,000+ FRED time series via 3 focused tools (browse catalog, search series, get observations)
- Verdict: BUILD — essential for macroeconomic context in consulting research; the focused 3-tool design prevents context window bloat

**us-gov-open-data-mcp**
- Version/maturity: Relatively new, single maintainer, Credible
- What it does: 36+ U.S. government APIs, 300+ tools; Treasury, BLS, BEA, EIA, Census, FEC, USAspending; selective module loading; WASM-sandboxed JavaScript (98-100% context window savings for large responses)
- Verdict: BUILD with caution — use selective module loading (`--modules fred,treasury,bls`) to control context window; the WASM sandboxing for large responses is critical; monitor for maintainer continuity risk

**Academix MCP**
- Version/maturity: Free; optional Semantic Scholar API key; multi-source aggregator; Credible
- What it does: Unified search across OpenAlex (250M+), DBLP, Semantic Scholar (200M+), arXiv, CrossRef (150M+); citation analysis; BibTeX export
- Verdict: BUILD — deploy for academic source retrieval; the multi-source aggregation at free tier is high value; Semantic Scholar API key should be obtained for higher rate limits

**Exa MCP**
- Version/maturity: $85M Series B, own search index; 81% on complex retrieval vs. 71% for Tavily; 2-3x faster; Verified
- What it does: Web search with specialized indexes (1B+ people, 50M+ companies, 100M+ papers); query-dependent highlights reducing token usage 50-75%; 10% higher RAG accuracy
- Verdict: BUILD — use as primary web search MCP server; the 10% higher RAG accuracy from highlights is meaningful at scale; 50-75% fewer tokens sent is significant for context management

**Brave Search MCP**
- Version/maturity: Independent index (not Google/Bing wrapper); 50M+ searches/day; highest AIMultiple agentic benchmark score (14.89); Verified
- What it does: Web search with independent indexing; $5/1K queries; handles 50M+ daily searches
- Verdict: BUILD — deploy as fallback/parallel web search; the independent index catches sources that Exa's specialized index misses; the AIMultiple benchmark leadership is the strongest available validation

**Tavily**
- Version/maturity: Acquired by Nebius Feb 2026; /research endpoint GA; Credible
- What it does: Managed multi-step research with citations; fast/ultra-fast search depths; news-focused
- Verdict: BUILD as tertiary — use specifically for news-focused searches where Exa/Brave are less specialized

**pgvector + pgvectorscale**
- Version/maturity: pgvector 0.8.x; pgvectorscale adds StreamingDiskANN; AWS benchmark-verified
- What it does: Vector search within PostgreSQL; ACID transactions; SQL joins; iterative index scans; 471 QPS at 99% recall on 50M vectors
- Verdict: BUILD — primary vector store; eliminates operational complexity of dedicated vector DB; the SQL join capability between embeddings and SEC filing metadata (dates, company IDs, form types) is architecturally irreplaceable

**Qdrant**
- Version/maturity: v1.17.x, Rust, monthly releases; SOC 2 Type II certified; server-side BM25 since v1.15.2; Verified
- What it does: Dedicated vector DB; best filtered vector search (payload-aware HNSW); 1.5-bit/2-bit quantization; million-tenant multi-tenancy; hybrid search via single Query API
- Verdict: LEARN as upgrade path — deploy when Keystone exceeds 50M vectors; Qdrant's server-side BM25 is the critical feature for eliminating the separate sparse search system

**Pinecone**
- Version/maturity: Fully managed; SOC 2 + ISO 27001 + HIPAA; 99.95% SLA; Verified
- What it does: Managed vector search; zero operational overhead
- Verdict: LEARN — best compliance story if regulated data handling becomes a hard requirement; total vendor lock-in and no SQL integration are dealbreakers for Keystone's primary vector store

**Weaviate**
- Version/maturity: v1.35.16; native generative search; BlockMax WAND BM25; Credible
- What it does: Hybrid search (+42% NDCG over pure vector on MS MARCO); multi-tenancy; native RAG
- Verdict: LEARN — study hybrid search implementation (BlockMax WAND is more sophisticated than RRF); could replace pgvector+Qdrant path if operational complexity is acceptable

**Milvus/Zilliz**
- Version/maturity: v2.6.11; GPU acceleration 50x faster than CPU HNSW; requires Kubernetes
- What it does: Billion-scale vector search with GPU acceleration
- Verdict: SKIP — operational complexity (etcd, MinIO, multiple node types, Kubernetes) is unjustifiable for Keystone's scale; GPU acceleration unnecessary at tens of millions of vectors

**ChromaDB**
- Version/maturity: v1.4.1; Rust rewrite
- What it does: Simple embedded vector store; developer-friendly
- Verdict: SKIP — missing multi-tenancy, advanced filtering, hybrid search, compliance certifications; appropriate for prototyping, not production

**Cohere Embed v4**
- Version/maturity: Production, 128K token context window, MTEB 65.2; enterprise SLAs; Verified
- What it does: Embedding model designed for "noisy real-world data"; multimodal (text+images for charts); VPC deployment; $0.12/M tokens
- Verdict: BUILD — primary embedding model for consulting documents; 128K context window enables entire SEC filings in one pass; multimodal capability for embedded chart understanding

**BGE-M3**
- Version/maturity: MIT license, 568M params, single GPU; multi-function (dense + sparse + multi-vector); Verified
- What it does: Self-hosted embedding producing hybrid search vectors in one model pass; supports 100+ languages; domain fine-tuning can close 10-30% gap vs. proprietary
- Verdict: BUILD as self-hosted option — zero API cost; produces hybrid search vectors without a separate sparse model; single-GPU deployment fits Mac Mini infrastructure constraint

**OpenAI text-embedding-3-large**
- Version/maturity: MTEB 64.6; $0.13/M tokens; Matryoshka 3072→256 dimensions; Verified
- What it does: Strong general-purpose embedding with excellent ecosystem integration
- Verdict: LEARN — strong runner-up to Cohere Embed v4; consider if Cohere pricing or compliance constraints become issues

**Jina Embeddings v3**
- Version/maturity: CC-BY-NC-4.0 (non-commercial for v4); task-specific LoRA adapters; Verified
- What it does: Task-specific embedding via LoRA; Matryoshka from 1024 to 32 dimensions
- Verdict: LEARN — license terms must be verified before any commercial use; the non-commercial license for v4 may be a hard disqualifier for Keystone's commercial application

**Cohere Rerank 4 Pro**
- Version/maturity: #2 ELO (1629); 614ms latency; 100+ languages; enterprise SLAs; Verified
- What it does: Cross-encoder reranking after initial retrieval; LlamaIndex benchmark: 0.932 hit rate, 0.874 MRR with OpenAI + CohereRerank
- Verdict: BUILD — use as primary reranker; the 0.932 hit rate is the production target; enterprise SLAs justify API dependency

**Jina Reranker v2**
- Version/maturity: 278M params; 15x more throughput than BGE; Flash Attention 2; +7.9% Hit Rate, +33.7% MRR average; Verified
- What it does: Self-hosted cross-encoder reranker with function-calling and text-to-SQL awareness
- Verdict: BUILD as self-hosted fallback — use when Cohere is unavailable or for cost-sensitive tiers; function-calling awareness is particularly valuable for agentic RAG

**Semantic Router (Aurelio AI)**
- Version/maturity: MIT license, v0.1.12; embedding-based; <5ms routing; Verified
- What it does: Query routing to correct data source in <5ms; retrieve_multiple_routes() for multi-source fan-out
- Verdict: BUILD — deploy as primary query router before any LLM-based routing; the <5ms vs. 200-2000ms for LLM routing is a critical latency difference for a system processing parallel queries

**Docling (IBM)**
- Version/maturity: 42K+ GitHub stars, 1.5M monthly PyPI downloads; IBM-backed; Verified
- What it does: Layout-aware PDF parsing preserving table structure, headers, reading order; markdown output for tables
- Verdict: BUILD — only viable option for SEC filing ingestion that preserves table structure; the Enterprise RAG Challenge winner confirms markdown output as optimal

**Bifrost (Maxim AI)**
- Version/maturity: Open-source; dual-layer caching (hash + semantic); per-request TTL via HTTP headers; Credible
- What it does: Gateway-level caching with exact hash + vector similarity search; configurable TTL and similarity thresholds per source type
- Verdict: BUILD — deploy as the caching layer with source-aware TTLs: SEC filings 90 days, news 1-4 hours, academic 30-90 days; the per-request TTL override is critical for Keystone's multi-source architecture

**NewsGuard**
- Version/maturity: API production; 35,000+ sources; 0-100 credibility scores; journalist-assessed; Verified
- What it does: News source credibility scoring against 9 apolitical criteria; cloud datastream and webhooks
- Verdict: BUILD — deploy for Tier 4 source (news) quality scoring; the journalist-assessed scoring against explicit criteria is the only production-ready news credibility API

**Semantic Scholar API**
- Version/maturity: 1,000 req/sec free; SPECTER2 embeddings; citation velocity; already has MCP server; Verified
- What it does: Citation counts, influential citations, author h-index, citation velocity for academic quality scoring
- Verdict: BUILD — integrate for academic source quality scoring in the composite scoring formula; the 1,000 req/sec free tier enables real-time scoring during research

**SearXNG**
- Version/maturity: 25K+ stars, self-hosted, multiple MCP servers; Credible
- What it does: Self-hosted metasearch aggregating multiple search engines; free, unlimited queries
- Verdict: LEARN — valuable for unlimited-query use cases and cost-sensitive tiers; deploy as a secondary search option when Exa/Brave API limits are reached; privacy advantage for sensitive research

**LanceDB**
- Version/maturity: Cloud offering in public beta; DuckDB integration; used by Harvey AI for legal documents; Credible
- What it does: Embedded/serverless vector store on Lance columnar format
- Verdict: LEARN — monitor for GA; the embedded architecture and DuckDB integration are interesting for Keystone's analytical layer; Harvey AI's legal document use case is directly analogous to consulting research

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Contradiction 1: The plan's unified retrieval interface doesn't specify hybrid search.**
- Plan says: Section 6.2 describes `research_search(query, scope=["public", "internal", "historical"])` as a unified retrieval interface
- Evidence shows: Dense-only search on financial documents misses exact identifiers (ticker symbols, CIK numbers, form types). Hybrid search with BM25 is non-negotiable for SEC filings. The plan's unified interface must implement hybrid search internally.
- Resolution: Follow the evidence. The `research_search()` function signature is correct, but its implementation must dispatch to hybrid search (dense + sparse BM25 + RRF) for financial documents and pure semantic search for qualitative documents. The query router (Semantic Router) should determine the dispatch path before the unified interface is called.

**Contradiction 2: The plan relies on MCP integration without addressing the gateway architecture requirement.**
- Plan says: Section 6.2 mentions external data sources; Appendix references MCP servers as integration layer
- Evidence shows: 66% of MCP servers have security findings; connecting 10+ servers exhausts context windows with 75,000-100,000+ tokens of tool definitions; rate limit coordination doesn't exist natively in MCP; stateless scaling conflicts with MCP's session model
- Resolution: Follow the evidence. Build an MCP gateway with: (1) intelligent tool routing and lazy loading (load only tools relevant to current query), (2) Redis-backed rate limiter with per-provider configurations, (3) circuit breakers per provider, (4) container isolation per server, (5) OAuth authentication. The plan's MCP integration is correct at the design level but requires defensive engineering that isn't currently specified.

**Contradiction 3: The plan describes a "Research Index — a lightweight manifest of available sources" but doesn't specify the retrieval architecture.**
- Plan says: Section 4.1 describes "a Research Index — a lightweight manifest of available sources" that agents consult to load context just-in-time
- Evidence shows: The Research Index is a query routing layer — it must implement Semantic Router (<5ms embedding-based routing) with LLM fallback for ambiguous queries; the manifest must include source type metadata for TTL-aware caching and hybrid vs. semantic search dispatch
- Resolution: The plan's concept is correct. Formalize the Research Index as a query router (Semantic Router) plus a source registry (metadata per source type: retrieval method, TTL, hybrid/semantic dispatch, rate limits). This is an architectural detail the plan left unspecified.

**Contradiction 4: The plan uses an undifferentiated retrieval approach for tables vs. text.**
- Plan says: Agents "dynamically load specific sources as needed" (Section 4.1) without distinguishing table retrieval from text retrieval
- Evidence shows: Tables require precise SQL retrieval ("What was Q3 revenue?") while analysis requires semantic retrieval ("Industry outlook?"). The dual-path architecture (Text2SQL for quantitative + vector for qualitative + LLM synthesis for mixed) is essential for financial documents; Docling + structure-aware chunking is required to preserve table structure.
- Resolution: Follow the evidence. Add dual-path retrieval to the Research Agent's tool design: quantitative queries → LlamaIndex SQLAutoVectorQueryEngine → SQL against structured financial database; qualitative queries → vector search against embedded unstructured documents. Mixed queries dispatch to both paths with LLM synthesis.

---

## Cross-Report Flags

**Flag 1 (reinforces C1/Report 10):** The KV-cache economics finding (Report 10: 10x cost difference between cached and uncached tokens) connects to the retrieval layer's caching strategy. Bifrost's dual-layer caching (exact hash + semantic similarity at 0.85-0.90 threshold) is the retrieval-layer implementation of cache stability. The specification layer (Report 10) and retrieval layer (this report) must coordinate: stable RESEARCH.md specs enable stable retrieval cache keys.

**Flag 2 (reinforces C2/Report 11):** The plan-based multi-hop retrieval finding (40% naive RAG vs. 100% plan-based) directly validates the L1.5 Deliberation Layer's role. Complex analytical queries must be decomposed into retrieval plans before any data is fetched. The Specification Engine's decomposition (L0) is the retrieval planning step. Deliberation (L1.5) should not receive raw retrieved documents — it should receive synthesized research agent outputs from agents that each executed their own retrieval plans.

**Flag 3 (reinforces C3/Report 12):** The PROV-AGENT citation chain (Report 12) requires the retrieval layer to assign stable unique IDs to every source chunk at ingestion. This must be implemented in the vector store (pgvector) alongside the embedding, not added later. Design the chunk metadata schema in Phase 1 to include: document_id, chunk_id, page, section, URL, access_date, source_tier (1-4 in the financial data hierarchy).

**Flag 4 (reinforces Thread B on evaluation):** The source quality scoring framework (four-tier financial hierarchy, composite scoring formula) should feed into the L4 Evaluator's "Source Quality" dimension (10% weight in the eight-dimension rubric). The composite score — venue_score, author_score, recency_score, citation_score, provenance_score, corroboration_score — should be a computed metadata field attached to every retrieved chunk, not computed at evaluation time.

**Flag 5 (potential conflict with Thread A on orchestration):** The MCP gateway architecture requirement creates an orchestration dependency. The orchestration framework (Thread A: LangGraph vs. CrewAI vs. Claude Agent SDK) must be compatible with a centralized MCP gateway that implements lazy tool loading and rate limiting. LangGraph's explicit state management is better suited for this than CrewAI's linear model — the circuit breaker logic and graceful degradation cascade require state tracking.
