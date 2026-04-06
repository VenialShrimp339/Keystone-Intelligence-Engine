# Keystone Intelligence Engine: what to build, what to steal, and what to skip

**Keystone's three architectural convictions — Evaluator-first design, structural quality enforcement, and specification-as-system — are validated by a landscape where no existing system implements all three.** Every open-source research agent system reviewed enforces quality through prompts, not architecture. The closest analog (Imbad0202's academic pipeline) proves the Evaluator conviction empirically: its integrity checks caught 15 fabricated references, yet a subsequent post-publication audit found 21 additional issues the prior checks missed, demonstrating that *more evaluation always produces more value*. The strategic implication is clear: Keystone should compose research infrastructure from proven components (GPT-Researcher's parallelism, Cranot's knowledge graphs, the Brave+Exa+Tavily search stack) while building its Evaluator, Rejection Library, and Specification Engine from scratch — these are the only layers where no adequate component exists.

---

## The research agent landscape validates Keystone's core bet

Eight research agent systems were evaluated across architecture, quality control, search infrastructure, and maintenance health. The findings form a consistent pattern.

**GPT-Researcher** (25.7K stars, v3.4.2, March 2026) is the benchmark leader and best-engineered system. Its planner-executor-publisher pipeline runs parallel research agents against **20+ sources** in 2-3 minutes at ~$0.005/query (standard) or ~$0.40 for deep research. It supports 10+ search providers and 20+ LLM providers through clean abstractions. Its three-tier LLM strategy (fast/smart/strategic models) is the most cost-efficient pattern observed. The AG2 integration (March 2026) adds an 8-agent pipeline with human-in-the-loop review. CMU's DeepResearchGym benchmark confirmed it **outperforms Perplexity, OpenAI, and HuggingFace** on citation quality, report quality, and information coverage across 1,000 complex queries.

However, GPT-Researcher's quality control is fundamentally prompt-based. Its hallucination strategy is "scrape 20+ sites and assume the most frequent information is correct" — a probabilistic heuristic, not structural enforcement. The ReviewerAgent scores quality 1-10 via LLM prompting, but **there is no architectural gate that can reject substandard output**. In standard mode (the most common usage path), no review step exists at all. There is no Rejection Library, no claim-level verification against cited sources, and no conflict resolution mechanism when sources disagree.

**STORM** (Stanford, ~14K stars, NAACL 2024) takes a genuinely novel approach: simulating multi-turn conversations between writers carrying different perspectives and a topic expert grounded in internet sources. This perspective-guided research produces **25% better article organization** and 10% broader coverage than baseline RAG. But the perspectives are *cooperative information-gathering heuristics* (event planner, cultural critic), not *adversarial analytical positions* (bull vs. bear). They generate breadth, not contested depth. STORM has no runtime evaluator, no conflict resolution, and development has **plateaued since January 2025** — a classic academic project trajectory.

**199-Biotechnologies' deep-research-skill** (58 stars, v2.3.1) is the most Keystone-aligned system architecturally. Its 8.5-phase pipeline (Scope → Plan → Retrieve → Triangulate → Outline Refinement → Synthesize → Critique → Refine → Package) maps closely to Keystone's six layers. The **Dynamic Outline Evolution** phase — restructuring report outlines after evidence gathering to prevent specification lock-in — is a pattern Keystone should steal. Its `validate_report.py` (9 structural checks) and `verify_citations.py` (DOI/URL verification) provide real structural enforcement, and the multi-persona red teaming (Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer) adds analytical challenge during the Critique phase. But the source credibility scoring (0-100) is **semi-cosmetic** — scores are LLM-generated heuristics, not backed by domain authority databases, and the personas are prompt-based role-playing within a single model, not genuinely diverse perspectives.

**Cranot/deep-research** (202 stars) offers the most architecturally sophisticated component: **typed knowledge graphs tracking epistemic state**. Research findings are stored as typed nodes (Question, Answer, Insight, BlindSpot) with explicit state transitions (Unknown → Explored → Validated → Synthesized). The DETECT operation identifies blind spots and contradictions structurally, not through prompts. Its multi-model ensemble approach — querying Claude, Gemini, and Kimi simultaneously, then merging via a dedicated synthesis model — produces genuinely diverse perspectives because different model families have different training biases. This is fundamentally more robust than 199-Bio's persona prompting within a single model.

---

## Three systems worth studying for specific patterns

**DeerFlow 2.0** (ByteDance, **39.1K stars**, February 2026) demonstrates production-grade LangGraph orchestration with 9 specialized nodes, Docker-sandboxed execution, persistent memory across sessions, and progressive skill loading. It is the most mature orchestration framework reviewed. But it has **no evaluator, no deliberation layer, and no specification engine** — the pipeline goes directly from research to report with no quality gate. ByteDance provenance creates jurisdictional risk for regulated enterprises.

**Imbad0202/academic-research-skills** (5 stars, solo developer) punches far above its adoption weight. Its 10-stage pipeline includes the most sophisticated quality control observed: a pre-review integrity verification phase that validates **100% of references, data, and claims** (catching 15 fabricated references in its showcase), a 5-person peer review panel (Editor-in-Chief + 3 dynamic reviewers + Devil's Advocate) scoring on 0-100 rubrics, and a Socratic Coaching protocol (SCR) that detects high-confidence language ("obviously," "clearly") and introduces counterpoints. The post-publication audit finding 21/68 additional issues after three rounds of integrity checks is the strongest empirical evidence that **evaluation quality scales with evaluation investment** — directly validating Keystone's Conviction #1.

**Weizhena/Deep-Research-skills** (4 stars) contributes one elegant concept: the **Items × Fields matrix** for specification. The user defines entities to research (items) and data points per entity (fields), creating an explicit, extensible research scope. Commands like `/research-add-items` and `/research-add-fields` allow incremental refinement. This is a simple but powerful model for Keystone's Specification Engine.

---

## The search infrastructure stack for consulting-grade research

The search API landscape has consolidated around three complementary providers, each optimized for different query types. The optimal configuration for Keystone is a quality-tiered router that dispatches queries to the right provider based on query classification.

**Brave Search API** should be the primary discovery layer. It operates the only independent Western search index at scale (**35B+ pages**, 100M daily updates) after Bing API's shutdown in August 2025. It achieved the **highest AIMultiple benchmark score at 14.89** and **94.1% F1 on SimpleQA** — state-of-the-art for AI grounding. Pricing is flat and predictable at **$5/1,000 requests**. SOC 2 Type II certified with zero-data-retention options. The limitation: it returns snippets, not full page content, requiring a separate extraction step.

**Exa** should handle semantic and specialized queries. Built on a proprietary neural search index trained via link prediction (predicting which URL follows given text), it offers capabilities no other provider matches: **"Find Similar" search** (feed a URL, get conceptually similar pages), category-specific search (research papers, companies, people), and structured data extraction. The index covers **1B+ people profiles and 70M+ companies**. Pricing ranges from **$7/1K requests** (standard) to **$15/1K** (deep reasoning). The $85M Series B at $700M valuation (September 2025, led by Benchmark) signals sustained investment. Limitation: smaller index than Brave for general web queries.

**Tavily** fills the extraction gap and offers a managed research endpoint. Acquired by **Nebius for $275M** in February 2026, it returns clean, parsed page content (not just URLs) and serves as LangChain's default search tool. The new **/research endpoint** (GA January 2026) performs multi-step research autonomously for **15-250 credits per request** (~$0.08-$2.00). This endpoint is a direct competitor to building custom research orchestration — Keystone should evaluate it as a potential shortcut for simpler research tasks while building its own pipeline for consulting-grade depth. The Nebius acquisition introduces ownership uncertainty worth monitoring.

**SearXNG** (27.4K stars, AGPL-3.0) serves as the free fallback: a self-hosted metasearch engine aggregating **70+ search services** for unlimited queries at ~$5/month hosting cost. Production systems like Local Deep Research and N8N workflows use it as a cost-zero development and backup layer.

**Estimated cost per Keystone consulting research task:** $0.05-$0.50 using the tri-provider stack (Brave + Exa + Tavily), scaling to **$200-600/month** at moderate usage (2,000 tasks). The 199-bio search-cli (1 GitHub star) is not worth using directly — build a custom search orchestration layer instead.

---

## Benchmarks reveal where the real quality gaps are

Two benchmarks define the competitive landscape. CMU's **DeepResearchGym** evaluated systems on 1,000 complex queries and found that **information coverage (Key Point Recall) is universally the hardest dimension** — "linguistic fluency has outpaced comprehensive content synthesis." Even top systems score significantly higher on Clarity and Insight than on KPR, meaning they write well but miss important information.

The **DeepResearch Bench** (100 PhD-level tasks, 22 fields) provides the most granular competitive picture. The current leaderboard as of March 2026:

| System | RACE Score | Type |
|--------|-----------|------|
| CellCog Max | **56.13** | Proprietary |
| nvidia-aiq (Nemotron 3 + GPT-5.2) | **55.95** | Open-source (Apache-2.0) |
| CMCC-DeepInsight | 55.24 | Proprietary |
| Tavily Research | 52.44 | Commercial |
| LangChain + GPT-5 | 50.60 | Open-source |
| Gemini Deep Research | 49.71 | Commercial |
| OpenAI Deep Research | 46.45 | Commercial |
| Claude Research | 45.00 | Commercial |

Three insights matter for Keystone. First, **specialized multi-agent systems now beat all major commercial platforms by 8-10 RACE points** — dedicated architecture outperforms general-purpose chatbot features. Second, the open-source nvidia-aiq stack achieves competitive parity with top proprietary systems on an Apache-2.0 license, proving that **open infrastructure is viable for building competitive research systems**. Third, citation accuracy and depth are separable qualities: Perplexity leads on citation accuracy (**90.24%**), Claude on citation precision (**93.68%**), but Gemini leads on effective citation count (**111 per report** vs. OpenAI's 41) and overall depth.

For consulting-grade quality, Keystone should target **>50 RACE with >90% citation accuracy** — a combination no current system achieves. The Evaluator and Rejection Library are the architectural mechanisms to get there.

---

## The strategic USE / LEARN / SKIP decision matrix

Every component evaluated falls into one of three categories. These recommendations are prioritized by impact on Keystone's production timeline.

**USE directly (integrate, don't rebuild):**

- **GPT-Researcher's MCP server** (gptr-mcp) as a research backend callable from any MCP-compatible agent — it handles parallel search, scraping, and initial synthesis at proven quality levels.
- **Brave Search API** as the primary search provider — broadest index, best benchmarks, predictable pricing, production-mature.
- **Exa API** for semantic search, company/people research, and "Find Similar" exploration — capabilities no other provider offers.
- **Tavily API** for content extraction and quick research — collapses search+scraping into one call, reducing pipeline complexity.
- **SearXNG** as the free development and fallback search layer — eliminates API costs during iteration.
- **LangGraph** for pipeline orchestration — DeerFlow 2.0 proves it handles production-grade state management, checkpointing, and agent coordination at 39K-star maturity.

**LEARN from (steal the pattern, build your own):**

- **GPT-Researcher's three-tier LLM strategy** (fast/smart/strategic) — use cheap models for routine sub-query generation and expensive models only for synthesis and evaluation.
- **Cranot's typed knowledge graph with epistemic state tracking** — model research state as a graph (Unknown → Explored → Validated → Synthesized), not a flat pipeline, giving the Evaluator richer signal.
- **Cranot's multi-model ensemble pattern** — query genuinely different model families for the Deliberation phase rather than prompting personas within a single model.
- **199-Bio's Dynamic Outline Evolution** (Phase 4.5) — restructure the report outline after evidence gathering to prevent specification lock-in.
- **199-Bio's validate_report.py + verify_citations.py** — structural validation scripts for the Evaluator layer, including DOI/URL verification and citation hallucination detection.
- **199-Bio's auto-continuation with anti-fatigue enforcement** — progressive file assembly with per-section quality gates (prose ratio, citation density, theme alignment) for long reports.
- **Imbad0202's integrity verification** (100% reference/data/claim validation as a discrete pipeline stage) — the empirical proof that it catches 15+ fabricated references makes this non-optional.
- **Imbad0202's Devil's Advocate pattern** — add an explicitly adversarial perspective to the Deliberation phase with CRITICAL finding authority.
- **Imbad0202's SCR Protocol** (Certainty-Triggered Contradiction) — detect high-confidence language and introduce counterpoints as an Evaluator heuristic.
- **Weizhena's Items × Fields matrix** — a clean specification model for the Specification Engine that makes research scope explicit and incrementally extensible.
- **STORM's perspective discovery mechanism** — auto-mine analytical angles from related knowledge before deliberation begins, enriching the specification layer.
- **STORM's multi-LM role specialization** with DSPy-style modularity — clean component separation with defined interfaces.
- **DeerFlow's progressive skill loading** — only load domain-relevant tools per task to keep agent context lean.
- **DeerFlow's persistent memory architecture** — user profiles and accumulated knowledge reduce cold-start for recurring consulting research.

**SKIP (exists but not relevant or not production-ready):**

- **199-bio search-cli** — 1 GitHub star, Rust-only, no community; build custom search orchestration instead.
- **STORM as a runtime component** — development plateaued 14+ months ago, Wikipedia-centric design requires heavy rework for consulting output, and cooperative (not adversarial) perspectives don't match Keystone's deliberation model.
- **Co-STORM's human-in-the-loop model** — the steering mechanism is lightweight and exploratory, not suitable for structured consulting research with defined quality criteria.
- **Weizhena/Deep-Research-skills as a dependency** — 4 stars, zero community, solo developer; useful only as a reference for the Items × Fields concept.
- **Imbad0202 as a dependency** — Claude-locked, solo developer, no tests; invaluable as a design reference for quality control patterns but not production-viable.
- **Tavily /research endpoint as a pipeline replacement** — it's a direct competitor to Keystone's own research orchestration and removes control over quality enforcement; use Tavily for search/extraction only.
- **GPT-Researcher's quality control approach** — "scrape 20+ sites, most frequent info wins" is inadequate for consulting-grade accuracy.

---

## Where Keystone must build something genuinely new

No existing system implements the three components that define Keystone's differentiation. These must be built from scratch.

**The Evaluator with structural veto power.** Every system reviewed treats evaluation as optional, post-hoc, or prompt-based. GPT-Researcher's ReviewerAgent scores 1-10 via prompting with no enforcement. STORM has no runtime evaluator at all. 199-Bio has validation scripts that check structure, not substance. Even Imbad0202's sophisticated review panel is implemented through prompt engineering within Claude. Keystone's 8-dimension rubric Evaluator must be an independent pipeline stage with **architectural authority to reject output** — a hard gate, not a suggestion. The DeepResearch Bench RACE framework (Comprehensiveness, Depth, Instruction-Following, Readability) plus the FACT framework (Citation Accuracy, Effective Citations) should inform rubric design. Target: **>50 RACE equivalent with >90% citation accuracy** as the minimum passing threshold.

**The Rejection Library as a learning mechanism.** No system reviewed maintains persistent memory of failure patterns. Every run starts from zero quality context. GPT-Researcher, STORM, 199-Bio, and Cranot all lack cross-run learning. DeerFlow has persistent memory but only for user preferences, not quality patterns. The Rejection Library — a catalog of known failure patterns, anti-patterns, and past evaluation failures that informs future runs — is Keystone's most novel architectural contribution. It transforms the Evaluator from a static gate into an improving system.

**The Specification Engine as a structured constraint system.** Every system reviewed accepts a natural language query and begins researching immediately. Only Weizhena's Items × Fields matrix and 199-Bio's Scope+Plan phases approximate structured specification, and neither enforces specification completeness. Keystone's .md-based specification layer — defining methodology, quality criteria, analytical frameworks, and output requirements as declarative specifications that constrain every downstream layer — has no precedent in the reviewed systems. This is consistent with the conviction that the specification layer is the irreplaceable component.

---

## Conclusion: compose the commodity, build the moat

The research agent landscape in March 2026 is rich in research *generation* infrastructure and poor in research *evaluation* infrastructure. This asymmetry is Keystone's strategic opportunity. The generation pipeline — parallel search, multi-source retrieval, LLM synthesis — is a solved problem with multiple production-ready implementations. The evaluation pipeline — structural quality gates, claim-level verification, adversarial testing, cross-run learning — is where every existing system falls short.

The practical path: **use LangGraph for orchestration, GPT-Researcher's MCP server for research execution, and the Brave+Exa+Tavily stack for search**. Steal Cranot's epistemic knowledge graph, 199-Bio's dynamic outline evolution and citation verification, and Imbad0202's integrity verification and Devil's Advocate patterns. Build the Evaluator, Rejection Library, and Specification Engine as the three layers no one else has. The nvidia-aiq result (55.95 RACE on an Apache-2.0 stack) proves that open infrastructure can compete with — and beat — every major commercial platform's deep research feature. Keystone doesn't need to outperform GPT-5.2 at generation. It needs to outperform everyone at *knowing when generation isn't good enough*.