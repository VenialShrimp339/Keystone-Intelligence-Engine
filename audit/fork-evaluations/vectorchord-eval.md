# VectorChord + VectorChord-BM25 Infrastructure Evaluation

*Track 2C | Evaluator: Claude Opus 4.6 | Date: 2026-04-05*
*Target: Component #3a (Source Discovery) -- replacing pgvector + ParadeDB*

---

## Verdict: KEEP CURRENT STACK (pgvector + ParadeDB)

## Confidence: HIGH

---

## 1. Architecture Discovery (Critical Finding)

**VectorChord is NOT a replacement for pgvector. It is a layer on top of pgvector.**

The VectorChord extension control file (`vchord.control`) declares:
```
requires = 'vector'
```

VectorChord depends on pgvector for data types (`vector(N)`, `halfvec`), distance operators (`<->`, `<#>`, `<=>`), and base functionality. `CREATE EXTENSION vchord CASCADE` installs pgvector first. VectorChord adds two new index types that work with pgvector's existing data:

- `vchordrq` -- IVF-style index with RaBitQ quantization (optimized for disk-based search at scale)
- `vchordg` -- Graph index (VectorChord's alternative to HNSW, ~2,868 lines of Rust)

**Implication:** The question is not "pgvector vs. VectorChord" but "pgvector alone vs. pgvector + VectorChord." This fundamentally changes the evaluation.

**VectorChord-BM25 is independent.** It has no dependency on pgvector or VectorChord. It requires `pg_tokenizer.rs` for tokenization. Its `bm25vector` type and `<&>` operator are entirely separate from pgvector's types.

---

## 2. Vector Search Evaluation (VectorChord Enhancement to pgvector)

| Requirement | pgvector (baseline) | pgvector + VectorChord | Winner |
|---|---|---|---|
| 1024-dim vectors (Voyage-finance-2) | Yes (`vector(1024)`) | Yes (same pgvector types) | Tie |
| HNSW index | Yes (native HNSW) | No HNSW; has `vchordrq` (IVF+RaBitQ) and `vchordg` (graph) | pgvector at our scale |
| Approximate + exact search | Yes | Yes (plus autonomous reranking) | VectorChord |
| PostgreSQL 15/16/17 compatibility | Yes (verified PG17) | Yes (PG14-18; PG13 dropped in v1.1.0) | Tie |
| Maturity / production usage | Very high (PostgreSQL ecosystem core) | Moderate (v1.1.1, 1.6k stars, Feb 2026; successor to pgvecto.rs) | pgvector |
| Performance at 100K-1M vectors | Adequate (sub-100ms, high recall) | Overkill (designed for 100M-1B+) | Tie (pgvector sufficient) |
| Performance at 10M+ vectors | Degrades without pgvectorscale | Claims 5x faster queries, 16x insert throughput vs. HNSW | VectorChord |
| Storage cost | Full vectors in memory/disk | RaBitQ: 400K vectors/$1 (6x cheaper than Pinecone, 26x cheaper than pgvector) | VectorChord |
| Index build time | Moderate | 100M vectors in 20 minutes (hierarchical K-means) | VectorChord |
| Docker deployment | Yes (standard postgres images) | Yes (`ghcr.io/tensorchord/vchord-postgres:pg17-v1.1.1`) | Tie |
| Drop-in compatibility | N/A | Full: same data types, same operators, only index creation syntax differs | VectorChord |
| License | PostgreSQL License (permissive) | AGPLv3 + ELv2 (dual, restrictive) | pgvector |

### Assessment

VectorChord's advantages -- storage compression, faster index builds, graph index -- are designed for 10M-1B+ vector scale. At our Phase 1 scale (100K-1M vectors), pgvector's native HNSW provides adequate performance with sub-100ms latency and high recall. The switching cost (learning new index types, testing quantization parameters) is not justified by the performance gains at our scale.

**VectorChord becomes relevant when we exceed ~10M vectors**, which would happen if we index the full corpus of SEC filings, academic papers, and cross-engagement knowledge. At that point, `vchordrq` with RaBitQ quantization would provide meaningful storage and query speed benefits over HNSW.

### Additional Technical Notes (from docs research)

- **pgvector version constraint:** VectorChord requires pgvector >= 0.7, < 0.9. Our current pgvector installation should be verified against this range before any future adoption.
- **Graph index (`vchordg`) is experimental.** VectorChord's own docs recommend `vchordrq` for 95%+ of use cases. `vchordg` (DiskANN + RaBitQ) targets static corpora with NVMe hardware. Not relevant for our dynamic engagement-based workflow.
- **EDB (EnterpriseDB) partnership.** As of Q1 2026, EDB officially supports VectorChord with GPU-accelerated index builds. This is a meaningful maturity signal beyond the 1.6k GitHub stars.
- **VectorChord Cloud exists** (AWS us-east-1, free tier: 1CPU/2GB). However, Neon and Supabase do NOT support VectorChord -- only pgvector.
- **Compatibility caveat:** `halfvec`, `sparsevec`, and `bit` types are NOT supported in pgvector compatibility mode. Not relevant for us (we use `vector(1024)` only).

---

## 3. BM25 Search Evaluation (VectorChord-BM25 vs. ParadeDB pg_search)

| Requirement | ParadeDB pg_search | VectorChord-BM25 | Winner |
|---|---|---|---|
| True BM25 scoring in PostgreSQL | Yes (Tantivy-based) | Yes (Block-WeakAnd algorithm) | Tie |
| Full-text search features | Rich (faceted, JSON, fuzzy, range, highlight) | BM25 only (no facets, no fuzzy, no highlighting) | ParadeDB |
| Index maintenance overhead | Medium (Tantivy index files) | Medium (growing/sealed segment architecture) | Tie |
| Financial document handling | Mature (custom tokenizers, analyzers) | Limited ("only tested against English") | ParadeDB |
| Custom tokenization | PostgreSQL-native text search config | Requires separate `pg_tokenizer.rs` extension | ParadeDB (simpler) |
| Query syntax | PostgreSQL-native (familiar) | Custom operators (`<&>`, `to_bm25query()`) | ParadeDB |
| Hybrid search (BM25+dense+RRF) | Documented SQL-level hybrid search | No native hybrid; requires app-layer fusion | ParadeDB |
| Maturity | Established ($12M Series A July 2025, 7K+ stars, Alibaba/Modern Treasury customers) | Early (v0.3.0, ~360 stars, no named customers) | ParadeDB |
| PostgreSQL compatibility | PG14-17 | PG13-18 | VectorChord-BM25 |
| Result limit cap | No hard cap | `bm25_limit` GUC (default 100, max 65535) | ParadeDB |
| License | AGPL (pg_search) | AGPLv3 + ELv2 | Comparable |

### Assessment

VectorChord-BM25 is fundamentally a lighter, more focused alternative to ParadeDB. It does one thing (BM25 ranking) and does it natively in PostgreSQL with a clean operator API. However:

1. **Too early.** v0.3.0 with ~360 GitHub stars vs ParadeDB's 7,000+ and $12M Series A. No named production customers. ParadeDB has Alibaba Cloud, Modern Treasury, Bilt Rewards.
2. **Financial tokenization is the weak point.** No out-of-box financial tokenizer. `bert-base-uncased` lowercases everything (destroying ticker case signal), strips dots from `BRK.B`, and fragments company names like `3M` and `AT&T`. Custom corpus training is available but undocumented for financial text. ParadeDB's Tantivy pipeline has more tuning surface area and community knowledge for this.
3. **Missing features.** No faceted search, no fuzzy matching, no highlighting, no cross-encoder reranking. ParadeDB provides a complete full-text search solution.
4. **Extra dependency.** Requires `pg_tokenizer.rs` as a separate extension for tokenization (functionally coupled). ParadeDB is self-contained.
5. **`bm25_limit` cap is operationally significant.** Default cap on BM25 candidates returned before post-index filtering. Must be tuned higher for hybrid search with date ranges and source type filters (common in consulting research queries).
6. **No hybrid search advantage.** Both stacks require you to write RRF fusion yourself (SQL CTE or Python). Neither provides a built-in `hybrid_search()` function.

---

## 4. Hybrid Search (The Key Question)

**Q: Can VectorChord + VectorChord-BM25 do dense + BM25 + RRF fusion NATIVELY within PostgreSQL?**

**A: No.**

Grep of both entire codebases for "hybrid", "rrf", "reciprocal", "fusion" returns zero results in source code (excluding license text). The two extensions:
- Use different data types (`vector` vs. `bm25vector`)
- Use different operators (`<->` vs. `<&>`)
- Return different score semantics (distance vs. negative BM25 score)
- Have no shared query planner integration or built-in RRF function

VectorChord's official hybrid search docs show Python-level RRF fusion (two separate queries, merge in application code). However, since both operators are standard PostgreSQL index scans, a single-SQL CTE pattern is valid:

```sql
WITH vector_results AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <-> $query_vector) AS rank
  FROM documents ORDER BY embedding <-> $query_vector LIMIT 100
),
bm25_results AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY bm25_col <&> to_bm25query(...)) AS rank
  FROM documents ORDER BY bm25_col <&> to_bm25query(...) LIMIT 100
)
SELECT COALESCE(v.id, b.id) AS id,
       COALESCE(1.0/(60+v.rank), 0) + COALESCE(1.0/(60+b.rank), 0) AS score
FROM vector_results v FULL OUTER JOIN bm25_results b ON v.id = b.id
ORDER BY score DESC LIMIT 10;
```

This same CTE pattern works with pgvector + ParadeDB. **No advantage either way.** Both stacks require you to write the RRF fusion yourself, whether in SQL or Python.

---

## 5. Deployment and Operations

### Docker Images
- **VectorChord only:** `ghcr.io/tensorchord/vchord-postgres:pg17-v1.1.1` (Docker Hub + GHCR)
- **All-in-one suite:** `tensorchord/vchord-suite:pg17-latest` (VectorChord + VectorChord-BM25 + pg_tokenizer.rs)
- Images are official and actively maintained.

### Managed Hosting

| Platform | VectorChord | pgvector |
|---|---|---|
| VectorChord Cloud (first-party) | Yes (AWS us-east-1, free tier) | N/A |
| EDB (EnterpriseDB) | Yes (Q1 2026, GPU-accelerated builds) | Yes |
| Neon | No | Yes |
| Supabase | No | Yes |
| AWS RDS | No | Yes |
| Google Cloud SQL | No | Yes |

pgvector is available everywhere. VectorChord is limited to VectorChord Cloud and EDB.

### Backup/Restore
- VectorChord uses pgvector's data types, so `pg_dump`/`pg_restore` works normally for data.
- VectorChord indexes would need to be rebuilt after restore (same as HNSW indexes).

### Bus Factor
- **pgvector:** PostgreSQL ecosystem core. Maintained by Andrew Kane, widely contributed to, supported by every major cloud provider. Would survive any single maintainer leaving.
- **VectorChord:** Maintained by TensorChord (company). Successor to pgvecto.rs (which TensorChord also built). 1.6k stars, 57 forks. If TensorChord stops development, the extension would go unmaintained. However, since VectorChord sits on pgvector, reverting to pgvector-only is trivial (drop VectorChord indexes, create HNSW indexes).
- **ParadeDB:** Backed by a funded company ($7.6M+). Active development. Larger community than VectorChord-BM25.
- **VectorChord-BM25:** Same TensorChord company. Smaller community. v0.3.0 maturity. Higher bus factor risk.

---

## 6. Migration Path (pgvector -> pgvector + VectorChord)

**This is the key risk mitigator: migration is trivially easy.**

Since VectorChord reuses pgvector's data types and operators:

1. **Data migration:** None required. `vector(1024)` columns stay exactly the same.
2. **Query migration:** None required. `ORDER BY embedding <-> $query LIMIT K` works identically.
3. **Index migration:** Drop HNSW index, create vchordrq or vchordg index:
   ```sql
   -- Before (pgvector HNSW)
   CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops);
   
   -- After (VectorChord vchordrq)
   CREATE INDEX ON items USING vchordrq (embedding vector_cosine_ops);
   
   -- Or (VectorChord graph index)
   CREATE INDEX ON items USING vchordg (embedding vector_cosine_ops);
   ```
4. **Application code changes:** Zero (same operators, same query patterns).

**This means the decision to stay with pgvector now has near-zero lock-in cost.** We can add VectorChord at any time -- when our vector count exceeds 10M, when storage costs become material, or when index build times become a bottleneck.

---

## 7. License Analysis

| Component | License | Implications |
|---|---|---|
| pgvector | PostgreSQL License | Maximally permissive. No restrictions. |
| VectorChord | AGPLv3 + ELv2 (choose one) | AGPLv3: must share modifications if running as network service. ELv2: cannot offer as managed database service. |
| ParadeDB pg_search | AGPL | Must share modifications if running as network service. |
| VectorChord-BM25 | AGPLv3 + ELv2 | Same as VectorChord. |

For Keystone's use case (internal consulting tool, not a managed database service), both AGPLv3 and ELv2 are acceptable. However, pgvector's PostgreSQL License is simpler and carries zero licensing risk.

---

## 8. Performance Benchmarks (Published, Not Self-Tested)

### VectorChord vs. pgvector (from TensorChord publications and EDB docs)

**GIST dataset (1M vectors, 960 dimensions):**

| Metric | pgvector HNSW | VectorChord vchordrq | Ratio |
|---|---|---|---|
| QPS at equivalent recall | Baseline | ~2x baseline | 2x |
| Index build time | ~2,976 sec (implied) | 186 sec | 16x faster |
| Insert throughput | 246 inserts/sec | 1,565 inserts/sec | 6.4x |

**LAION 100M dataset (AWS i4i.xlarge: 4 vCPU, 32GB RAM, NVMe):**

| Metric | Value |
|---|---|
| Top-10 QPS @ 0.95 recall (1 thread) | 16.2 |
| Top-100 QPS @ 0.95 recall (1 thread) | 4.3 |
| Top-10 QPS @ 0.95 recall (8 threads) | 131 |
| P50 latency (100M x 768-dim, per EDB docs) | 35ms |

**Storage cost:** $1 per 400K vectors (6x cheaper than Pinecone, 26x cheaper than pgvector).

**Caveat:** These benchmarks are from TensorChord's publications (corroborated by EDB docs), not independently verified at our target dimensions (1024-dim) or scale (100K-1M). Benchmarks at 960-dim on 1M vectors may not translate linearly to 1024-dim on 100K vectors. At smaller scales, pgvector HNSW is already fast enough that a 2x improvement is the difference between 20ms and 10ms -- both imperceptible behind our 200ms Cohere Rerank API call.

### VectorChord-BM25 vs. ParadeDB (from README, commented out)

The VectorChord-BM25 README contains commented-out benchmark data:

| Dataset | VectorChord-BM25 QPS | ElasticSearch QPS |
|---|---|---|
| trec-covid | 28.38 | 27.31 |
| webis-touche2020 | 38.57 | 32.05 |

| Dataset | VectorChord-BM25 NDCG@10 | ElasticSearch NDCG@10 | Lucene NDCG@10 |
|---|---|---|---|
| trec-covid | 67.67 | 68.80 | 61.0 |
| webis-touche2020 | 31.0 | 34.70 | 33.2 |

**Caveat:** Benchmarks are commented out in the README (not published as official), compare against ElasticSearch (not ParadeDB), and show VectorChord-BM25 slightly behind ElasticSearch on NDCG@10 while slightly ahead on QPS. No head-to-head comparison with ParadeDB pg_search exists.

### Performance Testing (Not Conducted)

Docker-based performance testing was scoped but not executed for this evaluation. Rationale:
1. At our scale (100K-1M vectors), both pgvector and VectorChord would be fast enough.
2. The bottleneck in our pipeline is the Cohere Rerank API call (~200ms), not the PostgreSQL vector search (~20ms).
3. Published benchmarks, while vendor-sourced, are directionally reliable and show the advantage is at 10M+ scale.

---

## 9. Summary Tables

### Advantages of VectorChord Suite Over Current Stack

| Advantage | Magnitude | Relevance at Our Scale |
|---|---|---|
| Storage compression (RaBitQ) | 6-26x cheaper storage | Low (100K-1M vectors = <$10/mo either way) |
| Faster index builds | 16x at 100M vectors | Low (index builds at 100K take seconds either way) |
| Faster queries at scale | 5x at 100M vectors | Low (both sub-100ms at our scale, behind 200ms rerank API) |
| Graph index (vchordg) | Alternative to HNSW | Neutral (untested at our dimensions, no clear advantage at 1M) |
| Quantized types (RaBitQ4/8) | Novel native 4/8-bit types | Future interest (useful when scale justifies storage optimization) |

### Risks of Switching

| Risk | Severity | Mitigation |
|---|---|---|
| VectorChord-BM25 immaturity (v0.3.0) | HIGH | Don't switch BM25; keep ParadeDB |
| AGPLv3/ELv2 licensing complexity | LOW | Acceptable for internal tool; no managed service offering |
| Bus factor (TensorChord company) | MEDIUM | Revert to pgvector-only is trivial (same data types) |
| Financial document tokenization gaps | HIGH | VectorChord-BM25 "only tested against English," no financial domain tokenizers |
| No native hybrid search | N/A | Same situation as current stack; not a switching cost, but not an advantage either |
| Three extensions to manage (vchord + vchord_bm25 + pg_tokenizer) vs. two (pgvector + ParadeDB) | LOW | Suite Docker image bundles all three |

---

## 10. Recommendation

### Decision Framework Applied

- **If VectorChord is clearly better AND mature: REPLACE now.** -- VectorChord vector search is better at scale but our scale doesn't warrant it. VectorChord-BM25 is NOT mature enough.
- **If comparable performance but riskier: KEEP pgvector, revisit in 60 days.** -- This is the correct bucket.
- **If immature/unmaintained: SKIP, pgvector is the safe default.** -- VectorChord itself is not immature (v1.1.1), but VectorChord-BM25 is (v0.3.0).

### Final Recommendation

**KEEP pgvector + ParadeDB as the Component #3a stack. Add VectorChord as a future optimization when vector count exceeds 10M.**

Specifically:

1. **Phase 1 (now):** Build with pgvector (HNSW) + ParadeDB (BM25) + application-layer RRF fusion + Cohere Rerank. This is the spec as written.

2. **Phase 2 trigger (10M+ vectors):** When the knowledge base grows past 10M vectors (cross-engagement accumulation, full SEC filing corpus), evaluate adding VectorChord on top of pgvector for `vchordrq` or `vchordg` indexes. Zero data migration required. Only index type changes.

3. **VectorChord-BM25: SKIP for now.** Revisit when it reaches v1.0 and has published benchmarks against ParadeDB on financial/English corpora. Its v0.3.0 maturity, English-only testing, and lack of full-text search features beyond BM25 make it unsuitable for production financial document search.

4. **Remove "Fork candidate: VectorChord as conditional replacement for pgvectorscale" from the implementation spec** and replace with: "Future enhancement: VectorChord (vchordrq/vchordg indexes) as pgvector index upgrade when vector count exceeds 10M. Zero-migration-cost addition since VectorChord sits on pgvector. Evaluated 2026-04-05, verdict: KEEP pgvector for Phase 1."

---

## Appendix: Source Evidence

| Claim | Source | Verification Level |
|---|---|---|
| VectorChord requires pgvector | `vchord.control`: `requires = 'vector'` | Verified (source code) |
| Same operators as pgvector | `vchord--0.4.2.sql`: `CREATE OPERATOR <->`, `<#>`, `<=>` | Verified (source code) |
| PG14-18 support | `Cargo.toml`: feature flags `pg14` through `pg18` | Verified (source code) |
| VectorChord-BM25 v0.3.0 | `Cargo.toml`: `version = "0.2.1"`, SQL install files up to `0.3.0` | Verified (source code) |
| "Only tested against English" | VectorChord-BM25 README, Limitation section | Verified (README) |
| No hybrid/RRF fusion | Grep of both codebases: zero matches for hybrid/rrf/fusion/reciprocal | Verified (source code) |
| 1.6k GitHub stars (VectorChord) | GitHub web page fetch (Feb 2026 data point) | Credible (web fetch) |
| ~360 GitHub stars (VectorChord-BM25) | GitHub web page fetch | Credible (web fetch) |
| 5x/16x performance claims | TensorChord blog posts, corroborated by EDB docs | Credible (vendor + independent confirmation) |
| GIST 1M: 2x QPS, 16x index, 6.4x inserts | VectorChord docs benchmark page | Credible (vendor-published with methodology) |
| BM25 3-5x QPS vs Elasticsearch | VectorChord-BM25 blog (MS-MARCO, BEIR datasets) | Claimed (vendor-sourced) |
| BM25 benchmarks in README (commented out) | VectorChord-BM25 README (HTML comments) | Stale (commented out, not officially published) |
| ParadeDB funding ($12M Series A, July 2025) | ParadeDB blog, public reporting | Verified |
| ParadeDB customers (Alibaba, Modern Treasury) | ParadeDB website | Credible |
| Financial tokenization gaps (tickers, BRK.B) | pg_tokenizer.rs docs + analysis of BERT tokenizer behavior | Verified (architectural analysis) |
| `bm25_limit` cap behavior | VectorChord-BM25 README, Limitation section | Verified (README) |
| Hybrid search CTE pattern validity | VectorChord docs hybrid search page + operator analysis | Verified (both operators confirmed as PostgreSQL index scans) |
