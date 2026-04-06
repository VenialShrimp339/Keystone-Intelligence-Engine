# Retrieval architecture for the Keystone Intelligence Engine

**The LLM Knowledge Base pattern Andrej Karpathy published three days ago changes the calculus for this system's retrieval stack.** Rather than building elaborate RAG infrastructure, the most promising architecture combines LLM-compiled markdown wikis for accumulated knowledge with lightweight embedding search for source discovery — an approach that aligns naturally with Keystone's existing claim-level intermediate representations and Claude Max economics. The original plan of pgvector + hybrid search + Semantic Router + Docling + caching was correctly flagged as over-engineered; the evidence now supports a simpler, more powerful design where the LLM itself is the primary knowledge organizer, embeddings play a supporting discovery role, and infrastructure stays minimal.

---

## Part A: Karpathy's LLM Knowledge Base pattern rewrites the playbook

### The pattern and its provenance

On April 2–3, 2026, Karpathy posted to X describing how "a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge." On April 4, he published a detailed GitHub gist (4,207 stars in 24 hours) laying out the full architecture. **Confidence: Verified** — primary sources confirmed.

The pattern has three layers and four operations:

**Three layers.** First, a `raw/` directory holds immutable source material — papers, articles, data. The LLM reads but never modifies these files. Second, a `wiki/` directory contains LLM-compiled structured markdown: summaries, entity pages, concept pages, comparisons, and synthesis articles, all interlinked. Two critical files maintain navigability: `index.md` (catalog with one-line summaries and links) and `log.md` (append-only chronological record of all changes). Third, a schema file (`CLAUDE.md` or `AGENTS.md`) provides natural-language instructions governing LLM behavior, replacing formal ontology.

**Four operations.** *Ingest*: drop a source into `raw/`, and the LLM reads it, writes a summary, updates the index, modifies 10–15 related wiki pages, and logs the change. *Query*: ask a question, the LLM reads the index, drills into pages, synthesizes an answer, then **files the answer back into the wiki** — creating a compounding knowledge effect. *Lint*: health checks for contradictions, stale claims, orphan pages, missing cross-references. *Output*: renders markdown, slides, charts, or dynamic visualizations.

Karpathy tested this at **~100 articles and ~400K words** (~533K tokens) on a single research topic, finding it worked better than "fancy RAG." The key insight: at this scale, the compiled index plus modern context windows (Gemini 2.0 Pro at 2M tokens, Claude at 200K+) eliminate the need for vector search entirely. He explicitly acknowledged this **does not scale to millions of documents** but argued that for focused research, "you probably don't need a million documents — you need the right 100."

### Rapid ecosystem emergence confirms the pattern's power

Within 48 hours, multiple implementations appeared. **CRATE** implements compile/ask/lint/ingest as a Python CLI. **llm-wiki-compiler** tested on 383 markdown files (13.1 MB) with incremental recompilation and bidirectional Obsidian-style wikilinks. **Farzapedia**, highlighted by Karpathy himself, compiled 2,500 raw entries (diary, Apple Notes, iMessages) into 400 interlinked articles. Its creator's comparison is telling: "I built a similar system to this a year ago with RAG but it was ass." Shopify CEO Tobi Lütke released **qmd**, a local hybrid search tool (BM25 + vector + LLM re-ranking) designed as a companion to the wiki pattern at larger scales.

A GitHub gist commenter reported working with 227 files and 2,230 indexed chunks, noting "the compounding effect is real." The Pebblous analysis places the sweet spot at **hundreds to tens of thousands of high-signal documents**. Beyond single-context capacity, wikis naturally decompose into domain-specific modules — a fundamentally different scaling model than RAG's approach of simply adding more vectors. **Confidence: Verified** for implementations; **Credible** for scale claims beyond Karpathy's tested range.

### Citation provenance is the critical gap for Keystone

Karpathy's default citation model maintains provenance at the **file level, not the passage level**. The `raw/` directory is immutable, and wiki articles can reference source files, but there is no automated mechanism to verify that a compiled wiki claim accurately represents its source. A GitHub gist commenter built a stronger system using content hashes: "Every proposition records which source files produced it and their hashes at compilation time. When you query, it checks whether files still match. Match = valid. Mismatch = stale." Another commenter warned: "The LLM can synthesize without citing, and you won't notice unless you look."

**For Keystone, this means the existing claim-level intermediate representation system is more rigorous than the Karpathy pattern's default.** The recommendation: use the Karpathy wiki pattern for knowledge synthesis and organization while maintaining the existing claim-level citation chain. Each wiki article should embed structured provenance metadata — source document ID, page/section reference, and content hash — that traces back to the original filing. The LLM compilation prompt should explicitly require inline citations in every factual claim.

### Failure modes to design against

**Hallucination during compilation** is the highest-risk failure mode. When an LLM synthesizes across sources, it can introduce subtle errors that compound as other agents treat compiled content as ground truth. One proposed "Swarm Knowledge Base" design addresses this with a dedicated evaluation LLM as a quality gate. **Stale compiled knowledge** is the second major risk — when source documents change, the wiki may silently lag. Content-hash provenance tracking is the structural fix. **Update propagation failures** can leave the wiki inconsistent: a single ingest touching 10–15 pages has no transactional guarantees. **Wiki contamination** from query outputs filed back into the wiki can create circular reasoning. **Confidence: Verified** for hallucination and staleness; **Credible** for propagation and contamination risks.

### How the pattern maps to Keystone's four use cases

For **within-engagement knowledge accumulation** — tracking what research agents have found during a single session — the pattern is an excellent fit. The compounding query→wiki filing cycle naturally builds session context. Each agent finding gets filed into the wiki, creating a persistent, organized record that subsequent agents can navigate. This is precisely what Keystone's claim-level IRs already do in a more structured way; the wiki pattern adds organizational synthesis on top.

For **cross-engagement knowledge** — building industry expertise over many engagements, like McKinsey's Knowledge Center — the pattern is strong. The wiki compounds over sessions, with `log.md` tracking evolution. The key concern is citation provenance across sessions, which requires the content-hash approach.

For **initial source discovery** — finding relevant documents the system hasn't read yet — the pattern is weak. It assumes sources are already curated into `raw/`. This is where embeddings and external search APIs remain essential.

For **self-improvement** — capturing engagement outcomes and lessons learned — the pattern excels. The lint operation plus query filing naturally creates a lessons-learned loop. Outputs filed back into the wiki mean future agents start with accumulated wisdom.

### The hybrid architecture Keystone should adopt

The strongest path combines four layers:

**Layer 1 — Discovery (embeddings + external search).** Embedding-based search over document pools and web search APIs for finding sources the system hasn't read. This solves the pattern's one weakness.

**Layer 2 — Compilation (Karpathy pattern).** Discovered sources go into `raw/`. The LLM compiles structured wiki with claim-level citations, maintaining Keystone's existing provenance chain. On Claude Max, compilation cost is essentially zero — each ingest touching 10–15 pages uses ~10–30K tokens.

**Layer 3 — Retrieval over compiled knowledge (qmd or pgvector).** At scale beyond context window limits, hybrid BM25 + vector search over the compiled wiki. qmd has MCP server mode for agent integration.

**Layer 4 — Quality gates.** Evaluation LLM validates compiled content before promotion. Content-hash provenance tracking for staleness detection. Periodic lint operations for contradiction detection.

---

## Part B: Embedding models and retrieval for financial documents

### Voyage-finance-2 dominates financial retrieval benchmarks

For financial document embedding specifically, **Voyage-finance-2 ($0.12/MTok) leads by a substantial margin**. Across 11 financial datasets, it averages **0.831 NDCG@10** versus OpenAI text-embedding-3-large at 0.762 (+9%) and Cohere Embed v3 at 0.713 (+17%). The gains are especially dramatic on complex financial QA: on ConvFinQA, Voyage-finance-2 scores 0.820 versus OpenAI's 0.550 — a **49% improvement**. On FinQA, it scores 0.795 versus 0.537 — a **48% improvement**. Independent validation from TigerData on ~10,000 SEC filings confirmed the advantage: 54% overall accuracy versus 38.5% for OpenAI text-embedding-3-small, with direct financial queries showing 63.75% versus 40%. **Confidence: Verified** — vendor benchmarks corroborated by independent testing.

The FinMTEB benchmark (EMNLP 2025, 64 datasets across 7 tasks) revealed a critical insight: **there is no statistically significant correlation between general MTEB scores and financial domain performance**. A model ranking highly on general benchmarks may underperform on financial text. Domain specialization boosts financial embedding performance by **4.5–15.6%** over general-purpose counterparts. The open-source Fin-E5 model tops FinMTEB at 0.6767, while FinBERT — despite being trained on financial text — underperforms general models on retrieval tasks. **Confidence: Verified** — peer-reviewed academic benchmark.

Voyage-finance-2 offers 1,024 dimensions, a 32,000-token context window (sufficient for long SEC filing sections without aggressive chunking), and 90ms query latency. It is a V3-era model; there is no V4 financial variant as of April 2026. The Voyage 4 series (January 2026) introduced shared embedding spaces and Matryoshka support, but Voyage-finance-2 does not participate in this space.

### The broader embedding landscape as of April 2026

For general-purpose use, **Gemini Embedding 001** leads the MTEB leaderboard at 68.32 average score with 3,072 dimensions and $0.15/MTok. **Gemini Embedding 2 Preview** (March 2026) is the first natively multimodal embedding model, supporting text, images, audio, and video in a single vector space at 8,192-token context. Among commercial APIs, **Voyage-4-large** ($0.12/MTok, January 2026) and **Cohere Embed v4** ($0.12/MTok, 128,000-token context, multimodal) are the strongest contenders. OpenAI's text-embedding-3-large sits at 64.60 MTEB average — competitive but behind the frontier. In open-source, **NV-Embed-v2** (72.31 legacy MTEB), **Qwen3-Embedding-8B** (70.58 MMTEB), and **BGE-en-ICL** (71.24 legacy MTEB) offer top-tier quality at zero API cost.

For Keystone specifically, **Voyage-finance-2 should be the primary embedding model** for financial document indexing given its clear domain advantage. If multimodal capability is needed for tables and charts, Cohere Embed v4 or Gemini Embedding 2 can supplement.

### Multimodal embeddings show strong promise for financial tables

The evidence for multimodal embeddings on financial tables is compelling. An Agentset benchmark (December 2025) found that for table retrieval, **multimodal embeddings achieved 88% Recall@1 versus 76% for text embeddings — a 12-point advantage** — because "linearizing tables into text removes structural information that queries depend on: row-column relationships, alignment, grouping, and relative position." Lumer et al. (November 2025) tested directly on a financial earnings benchmark and found multimodal embedding retrieval achieved **32% relative improvement in mAP@5** and 20% improvement in nDCG@5 over text-based approaches, with an LLM-as-judge win rate of 0.612 versus 0.388. **Confidence: Verified** — controlled academic benchmarks.

However, multimodal embeddings don't natively support keyword/BM25 search, which is critical for exact financial term matching. They also represent a relatively immature pipeline — RAGFlow's 2025 year-end review noted that "production-grade multimodal RAG hasn't fully materialized" due to engineering challenges around recall unit determination and cross-modal index management. The practical recommendation: **use multimodal embeddings selectively for chart/table-heavy pages while maintaining text-based hybrid search as the primary retrieval path**. This partially reduces but does not eliminate the need for structure-aware parsing like Docling. **Confidence: Credible** — evidence is strong but production validation is limited.

### Hybrid BM25 + dense search is non-negotiable for financial documents

Pure semantic search critically fails on exact financial terms. When a user queries "EBITDA margin for Q2 2023" or specific dollar amounts like "$5.2M," embedding models may retrieve semantically similar but factually wrong chunks. On FinanceBench, pure dense retrieval achieved only ~19% accuracy with a shared vector store, while **hybrid BM25 + dense with page-level retrieval reached ~76% accuracy** — a dramatic improvement. The Feb 2026 paper "Decomposing Retrieval Failures in RAG for Long-Document Financial QA" systematically confirmed that hybrid methods with reranking and query reformulation consistently outperform single-method approaches.

**Reciprocal Rank Fusion (RRF)** is the recommended fusion method: `score(d) = Σ 1/(k + rank_r(d))` with k=60. It requires no score normalization and is robust — documents ranking well across multiple independent methods are almost certainly relevant. Native hybrid search is supported by Weaviate (best-in-class), Elasticsearch, Qdrant, and pgvector + ParadeDB.

Among advanced retrieval methods, **SPLADE-v3** deserves consideration. It achieves 37.4 nDCG@10 on FiQA-2018 (financial QA within BEIR) and natively combines keyword precision with semantic expansion — learning, for instance, that "10-K" relates to "annual report." Its sparse vectors are compatible with inverted indexes, adding minimal overhead. **ColBERT** (late interaction) offers theoretical advantages for financial text through token-level matching but **lacks financial-domain-specific evaluation** and carries significant storage costs. For Keystone's moderate scale, the added complexity of ColBERT is unlikely to justify itself over hybrid BM25 + dense.

**Reranking is no longer optional.** Anthropic's contextual retrieval study showed that adding a reranker (Cohere Rerank v3.5 or a cross-encoder) on top of hybrid retrieval pushed failure reduction from 49% to **67%**. Multiple production guides confirm **12–18% improvement** in retrieval precision from reranking. The recommended pipeline: retrieve top 100–150 candidates via hybrid search, rerank to top 20, pass to LLM.

### Anthropic's contextual retrieval is validated and cost-effective

Anthropic's technique (September 2024) uses an LLM to generate a 50–100 token context preamble for each chunk — transforming "The company's revenue grew by 3%" into "This chunk is from an SEC filing on ACME corp's Q2 2023 performance; previous quarter revenue was $314 million. The company's revenue grew by 3%." This context is prepended before both embedding and BM25 indexing.

Anthropic claims **35% reduction** in retrieval failure from contextual embeddings alone, **49%** combined with contextual BM25, and **67%** with reranking added. Independent validation from an ECIR 2025 workshop paper confirmed contextual retrieval "preserves semantic coherence more effectively" than alternatives, though with higher computational cost. AWS Bedrock and Together AI have production implementations. **Confidence: Claimed** for exact numbers (self-reported), but **Credible** for the technique's effectiveness given independent adoption and conceptual soundness.

The cost — $1.02 per million document tokens with prompt caching — is negligible. A 100-page 10-K (~200K tokens) costs ~$0.20 to contextualize; 1,000 filings would cost ~$200 one-time. **On Claude Max, this is essentially free.** For financial documents specifically, contextual retrieval is especially valuable because chunks like "revenue grew 3%" are meaningless without knowing which company and quarter. A domain-specific prompt should include company name, filing type, reporting period, and section name.

---

## Part C: Infrastructure should be minimal and PostgreSQL-centric

### pgvector is the right choice at this scale

At hundreds to low thousands of documents per engagement, **performance differences between vector databases are negligible** — all options deliver sub-100ms queries under 10 million vectors. The differentiator is architectural simplicity. **pgvector with ParadeDB pg_search** provides competitive hybrid search with a decisive advantage: **full SQL joins**. Vector embeddings live alongside relational data (engagement metadata, user data, document metadata, permissions) in one transaction, one backup, one ops story.

ParadeDB pg_search adds production-ready BM25 scoring to PostgreSQL. Combined with pgvector's HNSW index and Reciprocal Rank Fusion, this delivers true hybrid search within a single PostgreSQL instance with ACID guarantees. The pgvector extension has over **8 million installs** as of Q1 2026, runs on every managed PostgreSQL service (AWS RDS, Supabase, Neon, Google Cloud SQL), and requires only `CREATE EXTENSION vector;` to set up. **Confidence: Verified** — well-documented, widely deployed.

Purpose-built vector databases justify their complexity only at much larger scale. Weaviate offers the best built-in hybrid search but adds a separate service, GraphQL learning curve, and $45–280+/month. Qdrant delivers the fastest raw performance (30–40ms p99, Rust-based) but lacks SQL joins. Pinecone is the easiest to set up but is managed-only, premium-priced, and lacks native BM25. Chroma is ideal for prototyping but production-immature. LanceDB is innovative (disk-based, Lance columnar format) but young. **None of these advantages matter at Keystone's scale, where pgvector's SQL integration and architectural simplicity dominate.**

If Keystone's vector DB role is limited to indexing source documents for initial discovery (with compiled wikis as the primary knowledge store), pgvector is even more clearly the right choice. The vector index becomes a lightweight discovery layer, not a mission-critical knowledge store, making simplicity the paramount concern.

### External search APIs fill the discovery gap

For initial source discovery beyond the ingested corpus, **Brave Search API** offers the best combination of quality, speed, and cost. It scored highest in the AIMultiple March 2026 benchmark (14.89 agent score), delivers the lowest latency (669ms), costs $5/1,000 requests, and runs on its own independent index of 30B+ pages. **Exa** is the strongest complement for complex semantic queries, scoring 94.9% on SimpleQA and offering dedicated company/financial search indexes ($7–15/1,000 requests). **Confidence: Verified** — independent benchmark.

Key notes on other options: **Tavily** was acquired by Nebius in February 2026, introducing roadmap uncertainty. **Google Custom Search is being discontinued January 1, 2027** — avoid. **Perplexity Sonar** synthesizes answers with citations but is too slow (11+ seconds) and expensive for high-volume search. **You.com** at $5/1,000 calls with citation-backed results is worth evaluating, particularly given their blog post on building AI equity research teams.

The optimal division of labor: **local retrieval (pgvector) handles all source documents already ingested** into the system with sub-10ms latency and zero per-query cost. **External search APIs handle discovery of new sources**, real-time information, and cross-referencing. The compiled markdown wiki holds accumulated knowledge. An LLM agent orchestrates across all three, deciding when local knowledge suffices versus when external search is needed.

### Docling is the right parser, and structure-aware chunking still matters

**Docling** (IBM, MIT license) is the recommended parser for financial documents. Its TableFormer model achieves **97.9% accuracy on complex table extraction** — far ahead of Unstructured.io's 75%. The Heron layout model provides a **23.5% mAP gain** over its predecessor on multi-column layouts, critical for SEC filings. Native XBRL support means structured financial statements (balance sheets, income statements, cash flows) can be extracted directly without chunking. Docling runs locally (important for financial data sensitivity), integrates with LlamaIndex and LangChain, and processes documents ~8.5× faster than Unstructured.io. **Confidence: Verified** — benchmarked against alternatives.

Structure-aware chunking remains essential even with advanced embeddings. The Vectara NAACL 2025 study found that **chunking configuration has as much or more influence on retrieval quality as embedding model choice**. For financial documents specifically:

- **Tables must be extracted as complete, intact units** — never split across chunk boundaries. Use HTML or structured JSON representation, not Markdown, for complex tables with merged cells and nested headers.
- **Text sections** should use recursive character splitting at **512 tokens with 50–100 token overlap** (69% accuracy in the FloTorch 2026 benchmark), respecting section boundaries (MD&A, Risk Factors, etc.).
- **Footnotes** must remain associated with their parent sections via metadata — they carry critical legal and financial context.
- **XBRL data** from SEC filings should bypass chunking entirely and go directly to structured storage.
- Semantic chunking (LlamaIndex's `SemanticSplitterNodeParser`) achieves high retrieval recall (91.9%) but produces dangerously small fragments (average 43 tokens) that hurt answer quality. It requires a minimum chunk size floor of 200–400 tokens to be useful.

**Late chunking** (Jina AI, 2024) — embedding first, chunking after — improves context retention but is **limited by the embedding model's context window** (typically 8K tokens ≈ 10–15 pages). Since SEC 10-K filings run 100+ pages, late chunking cannot process them in a single pass. Contextual retrieval is more practical for long financial documents.

---

## Concrete implementation recommendations for Keystone

The recommended architecture simplifies the original plan significantly while increasing capability:

**For MVP, build three components.** First, **pgvector + ParadeDB** as the discovery layer — index all source documents with Voyage-finance-2 embeddings and BM25, using Anthropic's contextual retrieval at ingest time. This handles initial source discovery within the corpus. Second, **Docling** for document parsing with structure-aware chunking, XBRL extraction for structured financials, and tables preserved as complete HTML units. Third, **Brave Search + Exa** for external discovery beyond the corpus.

**Layer the Karpathy wiki pattern on top for knowledge accumulation.** Each engagement gets a compiled markdown wiki that builds as research agents process documents. The wiki maintains Keystone's existing claim-level citation chain with source document IDs, page references, and content hashes embedded in every factual claim. The LLM compilation prompt should require inline citations. On Claude Max, compilation cost is zero — aggressive linting and recompilation are economically viable.

**What to defer.** Semantic Router, complex caching layers, and purpose-built vector databases are unnecessary at this scale. ColBERT and SPLADE add complexity without proven financial-domain advantages over hybrid BM25 + dense. Multimodal embeddings are promising for tables but immature for production — monitor Cohere Embed v4 and Gemini Embedding 2 as they mature.

**What to watch.** The Karpathy pattern ecosystem is 72 hours old. Every implementation is alpha-quality. The core concept is sound and maps well to Keystone's architecture, but treat scale claims beyond ~400K words as unverified. The hybrid architecture (embeddings for discovery + wiki for knowledge) hedges against the pattern's limitations while capturing its strengths. As the ecosystem matures, the wiki component can grow while the embedding component potentially shrinks.

## Conclusion

The convergence of three trends — LLM-compiled knowledge bases replacing retrieval-heavy RAG, domain-specialized embedding models outperforming general-purpose ones by 9–17% on financial text, and contextual retrieval reducing failures by up to 67% — points toward a simpler, LLM-centric architecture for Keystone. The most important architectural insight is that **the LLM should be the primary knowledge organizer, not just a generator sitting downstream of a retrieval pipeline**. Embeddings and vector search play a supporting role in discovery, not a central role in knowledge management. This inverts the traditional RAG assumption and aligns perfectly with Keystone's Claude Max economics, where LLM computation is essentially unlimited but architectural complexity carries ongoing engineering cost. The original plan was correctly flagged as over-engineered; the evidence supports doing less infrastructure and more LLM.