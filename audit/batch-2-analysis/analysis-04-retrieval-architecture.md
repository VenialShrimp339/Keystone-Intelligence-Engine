# Analysis: Report 04 — Retrieval Architecture and Knowledge Accumulation
*Analyzed: 2026-04-05 | Priority: Tier 2 (HIGH) | Report quality: high*

---

## Executive Summary

The report confirms Jack's instinct: the Karpathy wiki pattern and embeddings solve fundamentally different problems — discovery vs. accumulation — and neither eliminates the other. Karpathy's pattern is a strong fit for Observation Library and within-engagement tracking but does not replace embedding-based source discovery. The critical gap in the default Karpathy pattern is citation provenance at the passage level; Keystone's existing claim-level IRs are already more rigorous and should drive the wiki compilation layer, not the other way around. The existing Component #3 spec (pgvector + hybrid search + Semantic Router + Docling + Bifrost caching) was correctly flagged as over-engineered: Semantic Router and complex caching layers can be dropped, but pgvector + BM25 hybrid + contextual retrieval + Docling are all validated and should stay. Voyage-finance-2 is the clear embedding model choice for financial documents with a 49% empirical advantage over OpenAI on financial QA tasks.

---

## Key Findings (ranked by implementation impact)

### 1. Karpathy wiki pattern solves accumulation, not discovery — both layers are required

- **What:** Karpathy's compiled markdown wiki (raw/ + wiki/ + index.md + log.md) is a knowledge organization pattern, not a retrieval pattern. Tested at ~100 articles / 400K words on a single focused topic. It beats "fancy RAG" at this scale because modern context windows can hold the entire compiled index, eliminating the need for vector search over already-processed knowledge. It explicitly fails at finding sources the system has not yet ingested. Jack's cowork session analysis (embedded in directive #8) is confirmed exactly.
- **Evidence basis:** Karpathy GitHub gist (4,207 stars in 24 hours), Farzapedia implementation (2,500 entries -> 400 articles), llm-wiki-compiler (383 files / 13.1 MB), Pebblous analysis, multiple GitHub commenter reports.
- **Evidence quality:** Verified for the core pattern and tested implementations. Credible for scale claims beyond Karpathy's 400K words. The ecosystem is 72 hours old as of report publication — every implementation is alpha.
- **Temporal check:** April 2026. Highest credibility. The pattern is literally 3 days old; no production deployments exist yet.
- **Conflicts with existing project research?** No — reinforces the cowork session conclusion verbatim.
- **Verdict:** ADOPT for Observation Library and within-engagement knowledge tracking. SKIP as a replacement for initial source discovery.
- **Justification:** Confirmed by four independent implementations and Karpathy's own scoping. The compounding query->wiki-filing effect is real and maps directly to the Observation Library's 3-tier structure. The scale ceiling (~tens of thousands of high-signal documents) is above what any single engagement would generate.
- **Keystone impact:** Defines Component #3 scope split: embeddings handle discovery (L1 input), compiled wiki handles accumulation (L1 output -> Observation Library -> cross-engagement knowledge base). This is an additive layer, not a replacement.
- **Contradicts:** Nothing in existing decisions. Confirms directive #8.

---

### 2. Citation provenance is the pattern's critical failure mode — Keystone's existing design is already ahead

- **What:** Karpathy's default pattern tracks provenance at file level only. No automated verification that a compiled wiki claim accurately represents its source. A commenter's content-hash approach ("Every proposition records which source files produced it and their hashes at compilation time. Match = valid. Mismatch = stale.") is the structural fix. Keystone's claim-level IRs at L1->L2 handoff (source_chunk_ids, citation_ids, confidence, corroboration_count, provenance_chain) are more rigorous than what Karpathy ships by default.
- **Evidence basis:** GitHub gist comments. Report's own synthesis. Confirmed Keystone IR spec from settled decision #6.
- **Evidence quality:** Credible — conceptually sound, commenter-sourced. Risk of hallucination during compilation is Verified based on general LLM behavior.
- **Temporal check:** Timeless principle about LLM synthesis risk.
- **Conflicts with existing project research?** No — reinforces settled decision #6 and strengthens the case for claim-level IRs.
- **Verdict:** ADOPT the content-hash provenance approach. Wiki compilation prompts must require inline citations on every factual claim. Each wiki article must embed structured metadata: source document ID, page/section reference, content hash.
- **Justification:** Without passage-level provenance, the wiki becomes a citation integrity black hole. Keystone is building a Goldman-grade research system; a compiled wiki that can't trace claims to sources is a hallucination amplifier. This must be designed in at day one, not retrofitted.
- **Keystone impact:** Wiki compilation prompt spec becomes a required deliverable. The LLM is not just organizing content — it is maintaining a living citation manifest. This is Component #8 (CitationProcessor) territory, not just Component #3.
- **Contradicts:** Nothing. Deepens existing decision #6.

---

### 3. Voyage-finance-2 is the definitive embedding model for financial documents

- **What:** Voyage-finance-2 ($0.12/MTok) averages 0.831 NDCG@10 across 11 financial datasets vs. OpenAI text-embedding-3-large at 0.762 (+9%). On ConvFinQA (complex financial QA), the gap is 0.820 vs. 0.550 — a 49% improvement. On FinQA, 0.795 vs. 0.537 — 48% improvement. FinMTEB (EMNLP 2025, 64 datasets) proves no statistically significant correlation between general MTEB scores and financial domain performance. Domain specialization provides 4.5–15.6% uplift over general models. 1,024 dimensions, 32K-token context window, 90ms query latency.
- **Evidence basis:** Vendor benchmarks corroborated by TigerData independent testing on ~10,000 SEC filings (54% vs. 38.5% accuracy). FinMTEB peer-reviewed EMNLP 2025.
- **Evidence quality:** Verified — vendor data confirmed by independent third-party benchmark.
- **Temporal check:** 2025 benchmarks. Credible. No V4 financial variant as of April 2026; Voyage 4 series (January 2026) does not include a financial-domain model.
- **Conflicts with existing project research?** Current Component #3 spec does not specify an embedding model. This fills that gap directly.
- **Verdict:** ADOPT. Voyage-finance-2 is the primary embedding model for financial document indexing.
- **Justification:** 49% improvement on financial QA is not marginal — it's the difference between a retrieval system that works and one that doesn't on the tasks that matter most. The FinMTEB finding is critical: you cannot proxy financial embedding quality from general benchmarks, which means the current plan's silence on embedding model selection was a real risk.
- **Keystone impact:** Component #3 spec gains a concrete embedding model. Budget impact: $0.12/MTok. At 1,000 SEC filings (~200K tokens each), full re-indexing costs ~$24 — negligible. Ongoing per-engagement cost is near zero.
- **Contradicts:** Nothing. Fills a gap in current spec.

---

### 4. Hybrid BM25 + dense retrieval is non-negotiable for financial documents — pure semantic search fails

- **What:** Pure dense retrieval on FinanceBench achieved ~19% accuracy with a shared vector store. Hybrid BM25 + dense with page-level retrieval achieved ~76% accuracy — a 57-point improvement. Exact financial term queries ("EBITDA margin for Q2 2023", specific dollar amounts) fail with embeddings because semantically similar chunks are not factually correct chunks. Reciprocal Rank Fusion (k=60) is the recommended fusion method.
- **Evidence basis:** FinanceBench benchmark results. Feb 2026 paper "Decomposing Retrieval Failures in RAG for Long-Document Financial QA."
- **Evidence quality:** Verified — controlled benchmark with published methodology.
- **Temporal check:** 2025-2026. Highest credibility.
- **Conflicts with existing project research?** No — the existing Component #3 spec already includes BM25 + RRF fusion. This validates that choice with hard numbers.
- **Verdict:** ADOPT (already planned). The 19% vs. 76% finding quantifies the exact risk of going pure-semantic and should be cited in implementation documentation.
- **Justification:** Financial documents are full of exact-match queries (specific figures, named entities, period labels, regulatory terms). Embeddings cannot reliably surface these. BM25 is not optional complexity — it is the difference between a functional system and a broken one on the queries that matter most.
- **Keystone impact:** Confirms Component #3 core architecture. SPLADE-v3 (37.4 nDCG@10 on FiQA-2018, native keyword + semantic expansion) is worth evaluating as a BM25 alternative or supplement. ColBERT should be skipped — no financial-domain evaluation, high storage cost.
- **Contradicts:** Nothing.

---

### 5. Contextual retrieval (Anthropic, September 2024) is validated and essentially free on Claude Max

- **What:** Prepending a 50–100 token LLM-generated context preamble to each chunk before embedding and BM25 indexing reduces retrieval failure by 35% (contextual embeddings alone), 49% (contextual BM25 combined), and 67% (with reranking added). Cost: $1.02/MTok with prompt caching, ~$0.20 per 100-page 10-K. On Claude Max, this is zero. ECIR 2025 independent validation confirmed effectiveness. AWS Bedrock and Together AI have production implementations.
- **Evidence basis:** Anthropic self-reported numbers (Claimed for exact figures), but ECIR 2025 independent validation exists, and production deployments at AWS Bedrock are Verified.
- **Evidence quality:** Credible — self-reported numbers with independent conceptual validation and production deployment evidence.
- **Temporal check:** September 2024 technique, 2025 independent validation. Credible and current.
- **Conflicts with existing project research?** The existing Component #3 spec does not mention contextual retrieval. This is an additive improvement.
- **Verdict:** ADOPT. Add contextual retrieval to the ingest pipeline. Prompt must include company name, filing type, reporting period, section name.
- **Justification:** 67% retrieval failure reduction (combined with reranking) at zero incremental cost on Claude Max is the clearest ROI in the entire report. The technique is conceptually sound — it solves the chunk-decontextualization problem that is especially acute for financial documents where "revenue grew 3%" is meaningless without filing context.
- **Keystone impact:** Component #3 ingest pipeline gains a contextual enrichment step using Haiku (fast, cheap, appropriate model tier for extraction). This is aligned with settled decision #4 (Haiku for extraction/classification).
- **Contradicts:** Nothing. Additive to existing spec.

---

### 6. Reranking must be added to the retrieval pipeline

- **What:** Adding a reranker (Cohere Rerank v3.5 or cross-encoder) on top of hybrid retrieval pushed combined failure reduction from 49% to 67%. Multiple production guides confirm 12–18% improvement in retrieval precision. Recommended pipeline: retrieve top 100–150 candidates via hybrid search, rerank to top 20, pass to LLM.
- **Evidence basis:** Anthropic contextual retrieval study (Claimed for exact numbers). Multiple independent production guides (Credible).
- **Evidence quality:** Credible — directionally consistent across multiple sources even if exact numbers are self-reported.
- **Temporal check:** 2024-2025. Current.
- **Conflicts with existing project research?** Current Component #3 spec does not include a reranking step. This is a gap.
- **Verdict:** ADOPT. Cohere Rerank v3.5 as the default reranker. Budget: Cohere Rerank API is pay-per-use; at engagement scale this is negligible.
- **Justification:** 12–18% retrieval precision improvement compounds through the pipeline — better retrieval means better claims, better citations, better final output. At Keystone's per-engagement scale, the API cost is inconsequential. This should have been in the original spec.
- **Keystone impact:** Component #3 retrieval pipeline: hybrid search (top 150) -> Cohere Rerank v3.5 -> top 20 -> LLM. Semantic Router is now eliminated (see Finding #7) — reranking replaces query classification with result quality.
- **Contradicts:** Omission in current spec. Does not contradict any settled decision.

---

### 7. Semantic Router and complex caching layers should be dropped from Component #3

- **What:** The current spec includes Semantic Router for <5ms query classification and Bifrost dual-layer caching (Redis + disk, per-source TTLs). At hundreds to low thousands of documents per engagement, performance differences between retrieval approaches are negligible. pgvector + ParadeDB delivers sub-100ms queries under 10 million vectors. Semantic Router adds architectural complexity that the Karpathy pattern largely obsoletes — when the compiled wiki holds organized knowledge, the routing question changes from "which index do I search" to "is this in my wiki or do I need to go external."
- **Evidence basis:** pgvector install count (8M+, Q1 2026), performance benchmarks at scale. Report's own synthesis.
- **Evidence quality:** Verified for pgvector performance. Credible for Semantic Router elimination rationale.
- **Temporal check:** Current.
- **Conflicts with existing project research?** Yes — current spec explicitly includes both Semantic Router and Bifrost. This is a change recommendation.
- **Verdict:** SKIP Semantic Router and Bifrost caching. The LLM agent's decision about when to use local pgvector vs. compiled wiki vs. external search is more flexible and context-aware than a <5ms classifier.
- **Justification:** Semantic Router was designed for a pure-RAG architecture where routing between indexes is the primary decision. In the hybrid wiki + discovery architecture, the LLM orchestrator already has context to make this call. Adding a fast classifier creates a rigid classification layer that will be wrong on edge cases — exactly the Rigidity Problem from Jack's directive #1. Bifrost caching adds operational complexity (Redis + disk) that provides marginal benefit at engagement scale; per-source TTLs inside the compiled wiki's log.md-based change tracking is simpler and more coherent.
- **Keystone impact:** Component #3 scope shrinks. Estimated build time reduction: several days. Removes two external dependencies (Semantic Router library, Redis).
- **Contradicts:** Current Component #3 spec. Recommend removing both from spec.

---

### 8. pgvector + ParadeDB is the right vector database — no specialized alternatives needed

- **What:** Performance differences between vector databases are negligible at hundreds to low thousands of documents per engagement (all deliver sub-100ms queries under 10M vectors). pgvector with ParadeDB pg_search provides BM25 scoring, HNSW index, RRF fusion, and full SQL joins — vector embeddings alongside relational data (engagement metadata, permissions, document metadata) in one transaction, one backup, one ops story. 8M+ installs as of Q1 2026. Weaviate adds $45–280+/month and a separate service. Qdrant lacks SQL joins. Pinecone is managed-only and expensive.
- **Evidence basis:** Deployment data (8M installs), benchmark evidence (performance parity at this scale), infrastructure cost comparisons.
- **Evidence quality:** Verified.
- **Temporal check:** Q1 2026. Current.
- **Conflicts with existing project research?** Confirms existing spec choice. Adds pgvectorscale was already in spec — ParadeDB pg_search is the equivalent BM25 addition.
- **Verdict:** ADOPT (already planned). The existing spec's pgvector choice is correct. Validate that ParadeDB pg_search covers the BM25 capability pgvectorscale was intended for, or use both.
- **Justification:** The architectural simplicity argument is decisive. If the vector index's role shrinks to a lightweight discovery layer (with compiled wiki as primary knowledge store), the case for a purpose-built vector database weakens further. SQL joins for multi-tenant engagement queries (engagement_id, client_id, source metadata) are a real operational advantage.
- **Keystone impact:** Confirms Component #3 infrastructure choice. No change required.
- **Contradicts:** Nothing.

---

### 9. Docling is the right parser — structure-aware chunking still matters despite the wiki pattern

- **What:** Docling (IBM, MIT license) achieves 97.9% accuracy on complex table extraction vs. Unstructured.io's 75%. 23.5% mAP gain on multi-column layouts (Heron layout model). Native XBRL support for SEC filings. Runs locally (data sensitivity requirement). 8.5x faster than Unstructured.io. Vectara NAACL 2025: chunking configuration has as much or more influence on retrieval quality as embedding model choice. Critical rules: tables as complete HTML units (never split), text at 512 tokens / 50–100 token overlap, footnotes associated with parent sections via metadata, XBRL to structured storage bypassing chunking, semantic chunking minimum floor of 200–400 tokens.
- **Evidence basis:** Direct benchmarks vs. Unstructured.io (Verified). Vectara NAACL 2025 chunking study (Verified). FloTorch 2026 benchmark (Credible).
- **Evidence quality:** Verified for core parser comparison. Credible for chunking parameter recommendations.
- **Temporal check:** 2025. Current.
- **Conflicts with existing project research?** Confirms existing spec choice. Adds specific chunking rules not in current spec.
- **Verdict:** ADOPT (already planned). Add the chunking rules as concrete implementation requirements.
- **Justification:** Docling's advantage on tables (97.9% vs. 75%) matters enormously for financial documents where tables contain the primary quantitative evidence. The report notes that even with the wiki pattern, Docling's role does not shrink — the wiki organizes processed knowledge, but the quality of that knowledge depends on parsing accuracy at ingest time.
- **Keystone impact:** Component #3 ingest spec gains concrete chunking parameters. Tables as HTML (not Markdown) for complex structures is a concrete implementation decision. XBRL extraction path bypasses the entire chunking pipeline — this should be a distinct code path.
- **Contradicts:** Nothing. Extends current spec.

---

### 10. External search APIs: Brave Search primary, Exa for semantic queries — avoid Tavily and Google CSE

- **What:** Brave Search API scored highest in AIMultiple March 2026 benchmark (14.89 agent score), 669ms latency, $5/1,000 requests, independent 30B+ page index. Exa scores 94.9% on SimpleQA, dedicated company/financial search indexes, $7–15/1,000 requests — strongest for complex semantic queries. Tavily acquired by Nebius (February 2026) — roadmap uncertainty. Google Custom Search discontinued January 1, 2027 — avoid.
- **Evidence basis:** AIMultiple March 2026 benchmark (Credible — independent). Exa SimpleQA score (Credible). Acquisition/deprecation news (Verified).
- **Evidence quality:** Credible for API comparisons. Verified for vendor changes.
- **Temporal check:** February-March 2026. Current.
- **Conflicts with existing project research?** The existing spec does not specify external search APIs. This fills a gap and eliminates a dependency risk (Google CSE).
- **Verdict:** ADOPT Brave Search as primary external discovery API. ADOPT Exa as complement for financial/company semantic queries. SKIP Tavily (acquisition uncertainty), SKIP Google CSE (deprecating January 2027).
- **Justification:** Google CSE's 2027 deprecation is a hard constraint — building on it is building on a deadline. Tavily's acquisition creates vendor risk. Brave + Exa together cover volume (Brave) and quality semantic search (Exa) at reasonable cost.
- **Keystone impact:** Component #4 (MCP gateway) or Component #7 (Research Agents) need explicit Brave + Exa tool integrations. You.com is worth evaluating given their AI equity research team blog post — directly relevant to Keystone's use case.
- **Contradicts:** Nothing. Fills a spec gap.

---

### 11. Multimodal embeddings show promise for financial tables but are not production-ready

- **What:** Agentset benchmark (December 2025): multimodal embeddings achieved 88% Recall@1 vs. 76% for text embeddings on table retrieval (12-point advantage). Lumer et al. (November 2025) financial earnings benchmark: 32% relative improvement in mAP@5, 20% improvement in nDCG@5. However, multimodal embeddings don't natively support BM25/keyword search (critical for exact financial terms). RAGFlow 2025 year-end review: "production-grade multimodal RAG hasn't fully materialized." Primary candidates: Cohere Embed v4 ($0.12/MTok, 128K-token context, multimodal), Gemini Embedding 2 Preview (March 2026, natively multimodal, text/image/audio/video).
- **Evidence basis:** Agentset benchmark (Credible — controlled). Lumer et al. (Credible — academic). RAGFlow review (Credible).
- **Evidence quality:** Credible — evidence is strong but production validation is limited.
- **Temporal check:** November-December 2025 benchmarks, March 2026 Gemini release. Current.
- **Conflicts with existing project research?** No. Additive finding.
- **Verdict:** INVESTIGATE. Monitor Cohere Embed v4 and Gemini Embedding 2 as they mature. Use selectively for chart/table-heavy pages as a supplement to Voyage-finance-2 + BM25. Do not replace primary retrieval path.
- **Justification:** A 12-point Recall@1 improvement on table retrieval is meaningful for financial documents. But the BM25 incompatibility is a hard constraint for financial term matching, and production immaturity is a real risk for a system targeting Goldman-grade output quality. The right call is to track this and add it when the pipeline engineering matures.
- **Keystone impact:** Docling's table extraction to HTML format is forward-compatible with future multimodal embedding integration. No architecture changes needed now; this is a Phase 2 consideration.
- **Contradicts:** Nothing.

---

## Architectural Decisions This Enables

**Decision: Split Component #3 into two distinct sub-components.**

The current spec treats Component #3 as a single "retrieval system." The Karpathy pattern analysis justifies splitting it cleanly:

- **Component #3a — Source Discovery:** pgvector + ParadeDB (BM25), Voyage-finance-2 embeddings, contextual retrieval at ingest, Cohere Rerank v3.5 at query time, Docling parsing, Brave Search + Exa external APIs. Input: SearchQuery. Output: ranked source chunks with provenance metadata.
- **Component #3b — Knowledge Accumulation (new):** Compiled markdown wiki per engagement (raw/ + wiki/ + index.md + log.md), LLM compilation with mandatory inline citations, content-hash provenance tracking, lint operations. Input: processed claims from L1 agents. Output: organized wiki that feeds Observation Library and cross-engagement knowledge base.

Component #3b maps directly to the Observation Library's 3-tier structure (structural/analytical/judgment). It is also the mechanism by which cross-engagement knowledge builds over time — a McKinsey Knowledge Center analog.

**Decision: Confirm wiki pattern as Observation Library implementation mechanism.**

The Observation Library (captured from Rejection Library, expanded to include successes + failures) can be implemented as a compiled wiki. Each engagement's outcomes get ingested into raw/, compiled into wiki entries, and cross-linked with prior engagements. The log.md append-only record provides audit trail. The lint operation catches contradictions between observations from different engagements. This is architecturally cleaner than a bespoke structured database for the Observation Library.

**Decision: LLM orchestrator (not classifier) decides when to use each retrieval layer.**

Eliminating Semantic Router means the L1 research agent must decide: "Is this in the compiled wiki? Do I query the local pgvector index? Do I go external?" This is a richer decision than a <5ms classifier can make and benefits from agent context (what we're researching, what we've found, what gaps remain). This aligns with the generator-based agent loop (settled decision #7).

---

## Changes to Existing Plan

### Component #3 scope changes (PHASE-1-IMPLEMENTATION-SPEC.md)

| Element | Current Spec | Change |
|---|---|---|
| Semantic Router | Included | REMOVE — LLM orchestrator replaces query classification |
| Bifrost dual-layer caching | Included | REMOVE — operational complexity without proportional benefit at engagement scale |
| Embedding model | Unspecified | ADD Voyage-finance-2 as primary |
| Contextual retrieval | Absent | ADD — ingest-time LLM preamble generation (Haiku), domain-specific prompt |
| Reranking | Absent | ADD — Cohere Rerank v3.5, top 150 -> rerank -> top 20 |
| Chunking rules | Absent | ADD — 512 tokens / 50–100 overlap, tables as HTML units, XBRL to structured storage |
| External APIs | Unspecified | ADD Brave Search (primary) + Exa (semantic complement). Remove Google CSE dependency. |
| Wiki accumulation layer | Absent | ADD Component #3b — compiled wiki per engagement |

### Sizing impact

The original spec estimated Component #3 at "L" (1-2 weeks). After removing Semantic Router and Bifrost, core retrieval (pgvector + BM25 + contextual retrieval + reranking + Docling) is still an "L" estimate. The wiki accumulation layer (Component #3b) is a new "M" (3-5 days) item. Net impact: roughly the same total effort, better divided into two focused deliverables with cleaner scope.

### Build sequencing

Jack's directive #9 says Component #3 should WAIT for this report's findings. The findings now support proceeding. Recommended build order: Component #3a first (source discovery, needed for L1 agents), Component #3b second (knowledge accumulation, needed for cross-engagement Observation Library). Both can begin now.

---

## Open Questions Remaining

1. **Karpathy ecosystem maturity timeline.** Every wiki implementation is alpha as of April 2026. When is the ecosystem stable enough to commit to a specific library (CRATE, llm-wiki-compiler) versus building a minimal custom implementation? Recommendation: build custom minimal wiki management (it is not complex — file I/O + LLM prompts) rather than depending on 72-hour-old libraries. Revisit in 60 days.

2. **qmd viability as wiki search layer.** Tobi Lutke's qmd (BM25 + vector + LLM re-ranking, MCP server mode) is designed precisely for the "search over compiled wiki at scale beyond context window" use case. Worth evaluating if per-engagement wikis exceed 200K tokens. Currently alpha — monitor.

3. **SPLADE-v3 vs. BM25 for financial documents.** SPLADE-v3 achieves 37.4 nDCG@10 on FiQA-2018 and natively expands keyword queries ("10-K" -> "annual report"). This could improve exact financial term retrieval beyond standard BM25. Evaluation cost is low. Recommend testing SPLADE-v3 as a BM25 replacement before Component #3a launch.

4. **Cross-engagement wiki contamination.** When the compiled wiki accumulates across many engagements, circular reasoning becomes a risk — query outputs filed into the wiki can influence subsequent research on different clients. How do we scope the wiki per engagement vs. the cross-engagement Observation Library? The log.md structure provides auditability but not isolation. This needs an explicit scoping rule: engagement-scoped raw/ + wiki/ directories, with a separate promotion step for cross-engagement knowledge.

5. **Voyage-finance-2 vs. general models for non-financial engagements.** Jack's directive #4 says Keystone targets any consulting type, any industry. Voyage-finance-2 dominates financial benchmarks but is domain-specialized. For non-financial engagements (strategy, operations, technology), a general model (Voyage-4-large, Gemini Embedding 001) may be preferable. Component #3a should support configurable embedding model per engagement context, consistent with directive #1 (no rigid defaults).

6. **Content-hash provenance at wiki scale.** As the cross-engagement wiki grows to thousands of articles with source files being updated or re-ingested, the content-hash provenance system needs an efficient staleness-detection mechanism. This is a data engineering problem, not an LLM problem. pgvector's relational storage (SQL joins) is the right place to maintain the hash manifest — one more argument for pgvector over a purpose-built vector DB.

7. **Hallucination during wiki compilation.** The report identifies this as the highest-risk failure mode. The proposed "evaluation LLM as quality gate" maps directly to Keystone's L4 Evaluator. Define a specific eval criterion: does the compiled wiki article accurately represent its source claims? This should be a standard Evaluator dimension, not an ad-hoc check.
