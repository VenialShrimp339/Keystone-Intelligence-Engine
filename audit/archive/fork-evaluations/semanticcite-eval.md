# SemanticCite Fork Evaluation for Component #8 (CitationProcessor)

**Evaluated:** 2026-04-05
**Repository:** `sebhaan/SemanticCite` (github.com/sebhaan/SemanticCite)
**Note:** The PHASE-1-IMPLEMENTATION-SPEC referenced `SciPhi-AI/SemanticCite` which does not exist. SciPhi-AI has no such repo. Evaluated `sebhaan/SemanticCite` instead -- the only Python citation-related repo by that name on GitHub.

---

## Verdict: SKIP
## Overlap Percentage: 0%
## Confidence: HIGH

---

## What SemanticCite Actually Does

SemanticCite is a **single-citation verification tool**. It answers: "Does this one claim match this one reference document?" It works by:

1. Chunking a reference document (RecursiveCharacterTextSplitter, 512-token chunks)
2. Hybrid retrieval (BM25 + ChromaDB dense vector search)
3. Neural reranking (FlashRank, sigmoid threshold 0.95)
4. LLM-based classification into 4 categories: Supported / Partially Supported / Unsupported / Uncertain
5. Returning a flat dict with classification, reasoning, evidence snippets, and a float confidence score

**This is a fundamentally different tool solving a fundamentally different problem than our CitationProcessor.**

Our CitationProcessor is a **multi-agent output aggregator** that merges, deduplicates, verifies, and manifests citations from 3-5+ independent research agents. It does not verify whether claims match source documents -- that's closer to what our Evaluator's Layer 2 citation gate does.

---

## Requirement Coverage Matrix

| Requirement | Our Spec | SemanticCite Coverage | Gap |
|---|---|---|---|
| Citation extraction from agent outputs | Required: process `StructuredFinding[]` from L1 agents | None. Takes single citation string + single reference document | TOTAL -- no multi-agent concept |
| Cross-agent deduplication (URL/DOI match -> merge) | Required. **Already built** in `citation/dedup.py` (union-find) | None. No URL/DOI dedup. No concept of duplicate citations | TOTAL |
| Corroboration scoring (2+ agents find same source independently) | Required. **Already built** in `citation/dedup.py` | None. Single-user tool, no agent-awareness | TOTAL |
| URL liveness verification (async, HEAD+GET fallback) | Required. **Already built** in `citation/url_check.py` | None. Has PDF download but no URL liveness checking | TOTAL |
| Fabrication detection (non-existent DOIs via doi-mcp) | Required | None. No DOI verification at all | TOTAL |
| Content-hash provenance (SHA-256 for Karpathy wiki pattern) | Required. **Already built** in `citation/hash.py` | None. No content hashing | TOTAL |
| Output conforming to `citation_manifest.schema.json` | Required. Schema and Pydantic model exist | None. Outputs flat dict: `{classification, reasoning, evidence, metadata}` | TOTAL |
| Pydantic v2 model compatibility | Required. Models in `models/citations.py` | None. Uses plain dicts. LangChain Document model for chunks | TOTAL |
| Integration with our existing `citation/` utilities | Required. Must use `hash.py`, `dedup.py`, `url_check.py` | None. Completely different architecture (LangChain + ChromaDB) | TOTAL |
| ACH diagnosticity classification on claims | Required. `ACHDiagnosticity` enum exists | None. Classifies as Supported/Partial/Unsupported/Uncertain | TOTAL |
| Five-tier confidence mapping on claims | Required. `ConfidenceTier` enum with 5 tiers | None. Single float `confidence_score` | TOTAL |

**0 of 11 requirements have any coverage.**

---

## Code Quality Assessment

| Dimension | Rating | Notes |
|---|---|---|
| Structure | 2/5 | Monolithic: 1116-line single file (`citecheck.py`), one class (`ReferenceChecker`). No separation of concerns |
| Test coverage | 2/5 | Tests require live API keys (OpenAI/Ollama). No mocking. Most tests commented out. No pytest, uses manual assertions |
| Dependency footprint | **CONFLICT** | LangChain, ChromaDB, PyTorch, SentenceTransformers, FlashRank, LiteLLM. We use PydanticAI, httpx, no embedding stack. PyTorch alone adds ~2GB |
| Maintenance pulse | 1/5 | Single contributor (Seb Haan). 14 commits total. Last commit: 2025-11-21 (4.5 months stale). No releases. No CI/CD |
| License | **PROBLEM** | README claims MIT. **No LICENSE file exists in the repository.** Legally ambiguous |

### Dependency Conflicts with Our Stack

| SemanticCite Uses | We Use | Conflict? |
|---|---|---|
| LangChain 0.1+ | PydanticAI | Yes -- different agent framework, different abstractions |
| ChromaDB 0.4+ | No vector DB in CitationProcessor | Unnecessary heavyweight dependency |
| PyTorch 2.0+ | Not in our stack | ~2GB dependency for no benefit |
| SentenceTransformers | Not in our stack | Adds transformers + torch |
| FlashRank | Not in our stack | Neural reranking not needed for citation dedup |
| LiteLLM | Anthropic SDK direct | Different LLM interface |
| aiohttp | httpx | Different HTTP client |

---

## Module Classification

| Module | Classification | Rationale |
|---|---|---|
| `citecheck.py` (ReferenceChecker) | **SKIP** | Solves a different problem (verification, not aggregation). Hybrid retrieval pipeline could theoretically apply to Evaluator Layer 2 citation gate or Component #3a, but not CitationProcessor |
| `retrieval_utils.py` | **SKIP** | Debug file-saving utility for retrieval chunks. No reuse value |
| `security_utils.py` | **SKIP** | API key redaction in error messages. We have our own error handling patterns |
| `app.py` | **SKIP** | Streamlit UI for interactive citation checking. Completely irrelevant to a pipeline component |

### Modules Missing (must build regardless):

All core CitationProcessor functionality is missing from SemanticCite:

1. **Citation extraction from `StructuredFinding[]`** -- parse agent outputs into `Citation` objects
2. **Cross-agent deduplication** -- already built (`citation/dedup.py`, union-find on URL+DOI)
3. **Corroboration scoring** -- already built (`citation/dedup.py`, `find_corroboration_pairs`)
4. **URL liveness verification** -- already built (`citation/url_check.py`, async HEAD+GET)
5. **Fabrication detection** -- DOI verification via doi-mcp (new build)
6. **Content-hash provenance** -- already built (`citation/hash.py`, SHA-256)
7. **Manifest builder** -- assemble `CitationManifest` from processed citations (new build)
8. **Main orchestrator** -- `citation_processor.py` implementing `CitationProcessorContract` (new build)
9. **ACH diagnosticity classification** -- on claims at handoff (new build)
10. **Five-tier confidence mapping** -- `ConfidenceTier` assignment (new build)

Items 2, 3, 4, 6 are already implemented and tested. Items 1, 5, 7, 8, 9, 10 must be built new.

---

## Integration Risks

1. **Data model mismatch:** SemanticCite uses flat dicts. We use frozen Pydantic v2 models with validators (`Citation`, `Claim`, `CitationManifest`). Adapting would mean rewriting all data flow.
2. **Dependency bloat:** Forking would import LangChain + ChromaDB + PyTorch + SentenceTransformers (~3GB installed). Our CitationProcessor needs none of these.
3. **Wrong abstraction level:** SemanticCite operates on single citation + single document pairs. Our CitationProcessor operates on batches of findings from multiple agents. The core loop is fundamentally different.
4. **License uncertainty:** No LICENSE file despite MIT claim. Legally risky to fork.
5. **Stale codebase:** Single contributor, 14 commits, 4.5 months without activity. Unlikely to receive updates or accept contributions.

---

## Effort Comparison

### Fork + Modify: ~7-8 person-days
- 2 days: Strip out LangChain/ChromaDB/PyTorch/SentenceTransformers/FlashRank dependencies
- 1 day: Rewrite data models from flat dicts to our Pydantic v2 Citation/Claim/CitationManifest
- 1 day: Rewrite input interface from single-citation to multi-agent StructuredFinding[]
- 0.5 day: Rewrite output to conform to citation_manifest.schema.json
- 2-3 days: Build all the missing functionality (fabrication detection, manifest builder, orchestrator, ACH diagnosticity, confidence tier mapping) -- same as from-scratch since none exists
- 0.5 day: Integration testing

### Build from Scratch: 3-5 person-days
- 0 days: Citation dedup -- already built (dedup.py)
- 0 days: Corroboration scoring -- already built (dedup.py)
- 0 days: URL liveness checking -- already built (url_check.py)
- 0 days: Content-hash provenance -- already built (hash.py)
- 0 days: Data models -- already built (citations.py)
- 0 days: Contract interface -- already built (contracts.py)
- 1 day: Main orchestrator (`citation_processor.py`) implementing `CitationProcessorContract`
- 1 day: Fabrication detection via doi-mcp
- 0.5 day: Manifest builder
- 0.5 day: ACH diagnosticity + confidence tier mapping
- 1-2 days: Integration testing + event emission

### Net Savings: -3 to -4 days (NEGATIVE)

Forking costs MORE because:
- We'd spend 2+ days stripping dependencies we don't need
- We'd spend 1+ day adapting a foreign data model to our Pydantic schemas
- We'd still need to build every piece of CitationProcessor functionality from scratch
- Our existing `citation/` utilities already provide ~60% of what Component #8 needs

---

## Recommendation

**SKIP. Build from scratch. The name overlap is a false cognate.**

SemanticCite and our CitationProcessor share the word "citation" but solve completely different problems:
- SemanticCite = "Does claim X match document Y?" (single-pair verification)
- CitationProcessor = "Merge, deduplicate, verify, and manifest citations from N agents" (multi-agent aggregation)

Our existing code (`citation/dedup.py`, `citation/hash.py`, `citation/url_check.py`, `models/citations.py`, `contracts.py`) already provides a stronger foundation than SemanticCite could. The remaining work is the orchestrator, fabrication detection, manifest assembly, and claim-level metadata (ACH diagnosticity, confidence tiers) -- none of which exists in SemanticCite.

**Possible future relevance:** SemanticCite's hybrid retrieval + reranking pipeline (BM25 + dense + FlashRank) could be interesting for Component #3a (discovery retrieval) or the Evaluator's Layer 2 citation gate, where we DO need to check whether claims match source documents. But that's a different component evaluation, not Component #8.
