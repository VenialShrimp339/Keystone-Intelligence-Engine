# 10x ideas for the Keystone Intelligence Engine

**The Keystone Intelligence Engine's six-layer DPVI architecture is architecturally sound, but ten specific findings from this research should change design decisions.** The most consequential: the CIA's ICD 203 analytical tradecraft standards map almost perfectly onto the Deliberation Layer as enforceable validation checks, not just conceptual guidance. Analysis of Competing Hypotheses (ACH) should be the data structure backbone of Layer 1.5. A five-layer citation enforcement architecture can make "cite-or-it-dies" a structural guarantee rather than a prompt instruction. And the autoresearch ratchet loop — Karpathy's 630-line revolution — provides the exact mechanism for the Meta-Layer's self-improvement, already proven to rediscover research milestones autonomously. What follows maps findings across all ten research areas to specific layers and provides concrete USE/LEARN/SKIP verdicts with evidence quality ratings.

---

## 1. The Deliberation Layer should run CIA tradecraft, not just debate

The intelligence community solved the multi-perspective analysis problem decades before LLMs existed. **ICD 203 defines nine analytic tradecraft standards** — source credibility assessment, uncertainty quantification using a calibrated seven-level probability scale, explicit assumption identification, alternative hypothesis evaluation, and five others — each of which maps directly to an agent role in Layer 1.5. This is not metaphor. The standards specify exactly what "good analysis" looks like, down to requiring probability language like "likely (55-80%)" and "almost certain (95-99%)." [Evidence: **Verified** — retrieved directly from intelligence.gov primary source]

Heuer and Pherson's third edition catalogs **66 structured analytic techniques across six families**: data organization, exploration, diagnostics, reframing, foresight, and decision support. The diagnostic family alone contains ACH, Key Assumptions Check, Deception Detection, and Argument Mapping — each decomposable into distinct agent roles. ACH is the highest priority: its matrix structure (hypotheses × evidence, scored for consistency/inconsistency) is the natural data structure for confidence maps. One agent per hypothesis advocates for it; a diagnosticity agent identifies which evidence actually distinguishes hypotheses; a sensitivity agent stress-tests conclusions by varying assumptions.

Existing software validates this decomposition. **PARC ACH 2.0** (funded by the Office of Naval Research), **Open Source ACH** on GitHub, and **Globalytica's TH!NK Suite** (built by Pherson himself) all implement ACH computationally. Open Source ACH's group matrix feature — which highlights cells where analysts disagree most — is precisely what the Deliberation Layer's confidence maps should produce. Stanford's **SocraSynth** goes further, demonstrating multi-LLM structured debate with adversarial linguistic calibration that modulates agent contentiousness from cooperative to combative. A 2024 ACM paper at IUI proved LLM-powered devil's advocates significantly improve group decision accuracy.

**Critical design warning**: Research from late 2025 shows LLM agents in debate settings exhibit **conformity bias and sycophancy** — agents agree too readily rather than maintaining adversarial positions. The architecture must enforce anonymization of agent outputs during debate rounds and penalize excessive agreement.

**Recommendations:**

- **ACH matrix as Layer 1.5 backbone** → LEARN (build custom implementation borrowing from Open Source ACH's disagreement detection)
- **ICD 203 tradecraft standards as validation checks** → USE (implement the nine standards as post-analysis compliance gates)
- **SocraSynth adversarial debate protocol** → LEARN (steal the three-phase structure: opening positions → cross-examination → synthesis)
- **Devil's Advocacy agent** → USE (proven effective with LLMs; implement as permanent adversarial role)
- **Key Assumptions Check agent** → USE (LLMs excel at assumption identification; implement as mandatory pre-output step)
- **Globalytica TH!NK Suite** → SKIP (commercial, not open; the patterns are learnable from the published methodology)

---

## 2. Causal inference transforms correlation-heavy consulting research

CausalAgent, presented at IUI '26 in March 2026, demonstrates an end-to-end causal inference pipeline built on exactly the technology stack Keystone already uses. **Its architecture — LangGraph for routing, RAG grounded in causal inference textbooks, and MCP to interface with causal algorithms — is directly replicable.** Three agents handle data profiling, causal structure learning (selecting between PC, FCI, and LiNGAM algorithms via MCP), and RAG-grounded reporting. The key innovation is using MCP to decouple LLM reasoning from algorithm execution, making causal tools swappable without changing the agent logic. [Evidence: **Verified** — ACM published, GitHub repo at github.com/DMIRLAB-Group/CausalAgent]

MATMCD (ACL 2025 Findings, NEC Labs America) validates the multi-agent approach with hard numbers: **up to 66.7% reduction in causal inference errors** measured by Normalized Hamming Distance, and **83.3% improvement in root cause accuracy**. Its architecture pairs a Data Augmentation Agent (which retrieves multi-modal context via web search) with a Causal Constraint Agent that ranks causal hypotheses with confidence levels. The critical finding is that hybrid approaches — combining statistical causal discovery with LLM-based refinement — consistently outperform either method alone. [Evidence: **Verified** — peer-reviewed ACL publication]

Microsoft's **DoWhy** library (1M+ installs) provides the production-grade implementation backbone. Its four-step pipeline — Model (encode assumptions as causal graph) → Identify (determine if effect is estimable) → Estimate (statistical estimation) → Refute (robustness testing) — maps cleanly to a causal analysis agent within Layer 2. The refutation step is architecturally critical: it runs placebo treatments, random common cause tests, and data subset validation before any causal claim passes through.

causaLens operates commercially with enterprise clients including Cisco (10,000+ products, 3,000+ models) and Johnson & Johnson. Their approach — agents that build structural causal models, run counterfactual what-if analyses, and translate findings into business language — validates that causal AI is production-ready for consulting-grade work. Nobel laureate Guido Imbens has endorsed the approach as "on the verge of becoming useful collaborators." [Evidence: **Credible** — commercial marketing claims, but backed by named enterprise clients]

**The integration pattern for Keystone**: After Layer 1 research agents gather market data and financial metrics, a Causal Analysis Agent in Layer 2 should run DoWhy's pipeline on the quantitative data, use MATMCD's multi-modal augmentation pattern for context enrichment, and produce outputs that explicitly distinguish **verified causal relationships** from **correlational associations**, with confounders identified and intervention recommendations attached.

**Recommendations:**

- **CausalAgent's MCP-based architecture** → LEARN (replicate the MCP pattern for causal algorithm encapsulation)
- **DoWhy library** → USE (integrate directly as the causal inference computation engine)
- **MATMCD's multi-agent causal debate** → LEARN (implement opposing causal debaters with a judge agent)
- **causaLens platform** → SKIP (enterprise-priced, patterns are learnable from open-source alternatives)
- **Causal claims as Layer 3 output requirement** → USE (every recommendation should distinguish causal from correlational)

---

## 3. Hebbia's Matrix is the closest architectural precedent

Among financial due diligence tools, **Hebbia stands out as the most architecturally relevant model for Keystone**. Its Matrix platform orchestrates multiple AI agents (o3-mini, o1, GPT-4o simultaneously) in a swarm architecture with Iterative Source Decomposition (ISD) that preserves document context across overlapping chunks — achieving **92% accuracy** on financial benchmarks versus 68% with standard RAG. Investment bankers report saving **30-40 hours per deal**. Hebbia's $700M valuation and backing by a16z, Peter Thiel, and OpenAI itself signals market validation. Its 2025 acquisition of FlashDocs adds automated slide deck generation — expanding from retrieval to full artifact production, exactly the Layer 3 generation capability Keystone needs. [Evidence: **Verified** — OpenAI case study, published benchmarks]

AlphaSense's **Smart Synonyms** technology deserves special attention for Layer 1. It builds domain-specific semantic expansion graphs by analyzing speech patterns across tens of millions of documents — so searching "electric vehicles" automatically surfaces "autonomous cars," "self-driving vehicles," and related terms. This is replicable with embedding-based synonym detection trained on domain corpora. AlphaSense also pioneered **Sentiment Smart Synonyms**, where searching "positive" or "negative" returns documents discussing topics in that emotional context. At **$500M+ ARR** serving 88% of S&P 100 companies, the commercial model is validated but the patterns are stealable. [Evidence: **Verified** — company blog technical descriptions, Forbes Cloud 100]

McKinsey's five-step gen AI due diligence framework, published September 2025, reads like a direct blueprint for Keystone:

- **Step 1**: Customize models using proprietary data (train on institutional knowledge and deal outcomes)
- **Step 2**: Optimize peer set and benchmark selection with AI (scan databases, filings, and local-language press to construct dynamic peer sets)
- **Step 3**: Construct prompts like a product manager, not a search bar (structured prompt libraries with role definitions and priority hypotheses)
- **Step 4**: Build specialized agents for specialized tasks (map each agent's data sources, users, and outputs)
- **Step 5**: Implement a robust governance layer (risk-based oversight before any agent goes live)

McKinsey practices what it preaches: its internal **Lilli platform** runs RAG on 100K+ documents across 40+ curated knowledge sources, serving 500K+ prompts monthly to 72% of its 45,000 employees. Each session eliminates roughly six minutes of manual document hunting. [Evidence: **Verified** — McKinsey published article with specific methodology]

**Brightwave** introduces two patterns worth stealing. Its **Blueprints** concept — 100+ pre-populated analytical frameworks that encode a firm's analytical process once and run them continuously — maps directly to Layer 0's RESEARCH.md specification files. Its **entailment models** cross-verify every finding against source content, going beyond RAG retrieval to structural verification. [Evidence: **Credible** — early-stage company, TIME Best Inventions mention]

**Recommendations:**

- **Hebbia's ISD (Iterative Source Decomposition)** → LEARN (build custom implementation to overcome RAG context loss)
- **Hebbia's grid view extraction** → LEARN (structured tabular output from unstructured documents is critical for Layer 3)
- **AlphaSense Smart Synonyms** → LEARN (build domain-specific semantic expansion for Layer 1 search)
- **McKinsey's 5-step framework** → USE (adopt as the design methodology for Keystone's agent system)
- **Brightwave Blueprints** → LEARN (encode analytical frameworks as reusable .md specification templates)
- **Kira Systems' hybrid architecture** → LEARN (domain-trained extraction models plus GenAI overlay, not GenAI alone)

---

## 4. Multimodal analysis is production-ready for three of five modalities

The multimodal landscape for business research is unevenly mature. **Satellite imagery competitive intelligence scores 4/5 for production readiness**, with SpaceKnow offering API access at $15-30K/year and data available through Bloomberg Terminals. Orbital Insight pioneered parking lot car counts for retail revenue prediction; SpaceKnow rebuilt China's Guangdong manufacturing index from infrared imagery when the government stopped publishing it. UC Berkeley research confirmed that trading strategies based on satellite-derived parking lot data generate significant returns. [Evidence: **Verified** — academic research, commercial APIs available]

**Earnings call audio analysis scores 3/5** and represents the highest-alpha opportunity. Markets EQ (formerly Helios Life Enterprises) measures arousal, valence, and dominance in executive vocal patterns, claiming **20-25% gains in Sharpe ratios** when voice analysis supplements text-based sentiment models. Academic research validates the signal: FinVoc2Vec provides domain-adapted deep learning for executive vocal tone, and studies show that vocal delivery quality deteriorates measurably when executives deliver negative news, with stock markets reacting in real time. The key signal is **text-tone discrepancy** — when positive words don't match negative vocal affect. [Evidence: **Credible** — commercial claims plus academic validation]

**Document and slide analysis scores 3.5/5**. Amazon Bedrock Data Automation processes PowerPoint files by converting slides to images for VLM analysis. Vision-language models achieve roughly **90% accuracy on ChartQA** and are approaching human-level on MMMU (o4 Mini at 79.2%, human expert range 76-89%). However, a critical finding: for editable documents (PPTX, XLSX, DOCX), **extracting XML structure directly and feeding it to text LLMs outperforms VLM-based visual analysis**. Patent diagram analysis remains academic-stage (PatentLMM, PatentVision), scoring 2/5.

**Video analysis for business intelligence scores 2/5**. Gemini 3 Pro leads with 60 FPS processing and a 1M token context window (87.6% on Video-MMMU), but no turnkey business intelligence video platform exists. Analyzing factory tour videos or product demos for competitive intelligence requires custom implementation.

The current model landscape as of March 2026: **Gemini 2.5/3 Pro** leads for multimodal breadth (video, audio, 1M context); **GPT-5/5.2** leads for reasoning accuracy (84.2% MMMU, 400K context); **Claude** leads for document-heavy analysis (200K context, lowest hallucination rates); **Qwen3-VL** leads for document and diagram understanding (256K context, strong on DocVQA and ChartQA). Note: "GPT-5.4" and "Qwen 3.5" mentioned in the original prompt do not exist as released models — the current versions are GPT-5.2 and Qwen3-VL/Qwen3-Omni.

**Google ADK** (Agent Development Kit) provides production-ready multimodal agent orchestration with native bidirectional streaming for text, audio, and video. It supports sequential, parallel, and loop agent patterns and is the same framework powering Google Agentspace.

**Recommendations:**

- **Satellite imagery (SpaceKnow API)** → USE for Layer 1 research agents (production-ready, $15-30K/year)
- **Earnings call audio analysis** → LEARN (build custom using open-source audio models + FinVoc2Vec patterns)
- **Document XML extraction over VLM** → USE (for PPTX/XLSX/DOCX, extract structure directly rather than screenshot-and-analyze)
- **Google ADK for multimodal orchestration** → LEARN (evaluate as orchestration layer alongside LangGraph)
- **Video analysis** → SKIP for now (no turnkey solution; revisit when Gemini's video API matures)

---

## 5. The autoresearch ratchet makes every market sizing computable

Karpathy's autoresearch (released March 7, 2026, **42,000+ GitHub stars** in three weeks) demonstrates a paradigm shift directly applicable to Keystone's quantitative analysis. The core loop: human writes direction in markdown → agent reads instructions → modifies code → runs experiment (fixed 5-minute budget) → evaluates against metric → keeps improvement or reverts → repeats. In 700 experiments, the system discovered 20 genuine improvements and an **11% efficiency gain** on code Karpathy considered already well-optimized. The agent independently **rediscovered ML milestones** (RMSNorm, tied embeddings) in 17 hours that took human researchers eight years. [Evidence: **Verified** — public GitHub repo, reproduced by multiple parties including Shopify CEO]

Applied to consulting quantitative analysis, this transforms market sizing from estimation to computation. Instead of an LLM stating "the market is approximately $50B," the system would: build a bottom-up Python model, pull real data from Census Bureau/BLS/SEC EDGAR APIs (all free), run **Monte Carlo simulations** on assumptions (each parameter has a distribution, not a point estimate), generate sensitivity tables showing which assumptions matter most, and validate against top-down analyst estimates. If bottom-up and top-down diverge by more than 20%, the system iterates.

**E2B provides the sandboxing infrastructure** at negligible cost. Each agent runs in a secure Firecracker microVM with 80ms startup time, full Linux environment, and internet access. Pricing: ~$0.05/hour for 1 vCPU. Roughly **50% of Fortune 500** companies already use E2B. Manus runs 27 different tools inside E2B sandboxes. The total marginal cost for a complete market sizing analysis (50 LLM API calls + 4 E2B sandboxes running 10 minutes each): **approximately $3-10**. [Evidence: **Verified** — E2B documentation, published pricing]

**Claude Code with financial MCP connectors** is the most production-ready LLM for this pattern. Anthropic has built direct connectors to Daloopa (3,500+ companies), Morningstar, S&P Global, FactSet, Moody's, LSEG (live yield curves, FX rates), and PitchBook. Claude Opus 4 passed **5 of 7 levels** of the Financial Modeling World Cup. The system can build DCF models, run comparable company analyses, and generate sensitivity tables with live data. [Evidence: **Verified** — Anthropic documentation, FundamentalLabs benchmarks]

The key adaptation from Karpathy's original: replace the single scalar metric (val_bpb) with a **composite quality score** measuring data coverage (% of claims backed by cited sources), model coherence (bottom-up vs. top-down variance <20%), sensitivity completeness (top 5 drivers identified with ranges), source diversity (≥3 independent sources per claim), and computational reproducibility (every number traces to executable code).

**Recommendations:**

- **E2B sandboxing** → USE (integrate directly for all code execution agents)
- **Autoresearch ratchet loop** → USE (implement as the iteration mechanism in Layer 4's evaluator)
- **Claude Code + financial MCP connectors** → USE (for financial modeling agents in Layer 2)
- **Monte Carlo market sizing pattern** → USE (every market sizing should produce distributions, not point estimates)
- **ChatGPT Code Interpreter** → SKIP (sandbox limitations, no API connectivity, session-based)
- **Cursor Agent Mode** → SKIP (optimized for code editing, not data analysis workflows)

---

## 6. Always-on intelligence requires threat intelligence architecture, not CI platforms

The most mature implementations of continuous monitoring exist in **threat intelligence** (Dataminr, Recorded Future, Fivecast), not competitive intelligence. Dataminr processes **1M+ public data sources** across 150 languages with **50+ proprietary LLMs** trained on 12+ years of data, detecting ~500,000 daily events while filtering noise. Its ReGenAI distills multi-dimensional events into dynamically updating briefs. Valued at **$4.1B**, it serves two-thirds of the Fortune 50. Recorded Future's Intelligence Graph indexes and organizes data from 1M+ sources, reducing manual research by 80%. [Evidence: **Verified** — public valuations, documented capabilities]

Traditional CI platforms (Crayon at $20-40K/year, Klue with unlimited competitor tracking, Kompyte starting at $300/month) focus on aggregation and distribution rather than deep autonomous analysis. Contify's Athena AI engine is the most sophisticated, covering 1M+ vetted sources across 117+ languages with AI-based tagging, deduplication, and source credibility checking. But none maintain a **temporal knowledge graph** — the critical missing piece for a "living competitive landscape."

The technical architecture for a living competitive landscape requires five components:

A **temporal knowledge graph** where every fact has a validity window (when it became true, when superseded) and full provenance tracing to source episodes. Technology options include Neo4j, SurrealDB, or the Graphiti pattern from Zep's open-source framework. Second, a **multi-source data ingestion layer** monitoring news APIs in real time, competitor websites hourly, review sites daily, and financial reports weekly. Third, a **multi-modal event detection engine** with NER extraction, event classification into taxonomies (product launches, pricing changes, executive hires, M&A), relevance scoring, and deduplication. Fourth, a **graduated alert system** with dynamic baselining (learn what "normal" looks like per competitor, surface only anomalies), tiered notifications (critical → daily digest → weekly summary), and role-based delivery. Research shows AI-driven detection reduces alert volumes by **54%+ while maintaining 95%+ detection rates**. Fifth, an **intelligence synthesis layer** that auto-generates competitive profiles, dynamic battlecards, trend detection, and natural language Q&A grounded in the knowledge graph.

Alert fatigue is the paramount design challenge. SOC teams average **4,484 alerts per day** with 67% ignored and 40-70% being false positives. The solution is not fewer sources but smarter filtering: dynamic baselining, intelligent correlation and consolidation, risk-based prioritization, and automated triage.

**Recommendations:**

- **Temporal knowledge graph architecture** → LEARN (build as the persistence layer underlying Keystone's competitive intelligence)
- **Dataminr's multi-modal fusion pattern** → LEARN (adapt event detection architecture from security to CI)
- **Contify** → USE as a data source (1M+ vetted sources, 5-7 day setup, reasonable pricing)
- **Kompyte** → USE for MVP (most affordable at $300/month, Semrush data integration)
- **Dynamic baselining for alerts** → USE (implement anomaly-first alerting rather than threshold-based)
- **Fivecast MATRIX continuous evaluation** → LEARN (adapt the security vetting model for competitor vetting)

---

## 7. Scaling past four agents requires centralized orchestration or independence

The most rigorous scaling research comes from a Google/MIT paper (January 2026) evaluating **180 agent configurations** across 5 architectures and 3 LLM families. Three findings should directly shape Keystone's scaling decisions.

First, **centralized coordination limits error amplification to 4.4×** while independent agents amplify errors **17.2×** when mistakes propagate unchecked. This validates Keystone's orchestrator-based DPVI architecture over flat peer-to-peer designs. Second, **adding agents yields diminishing or negative returns when single-agent baseline exceeds ~45%**. If the base model already performs well on a task, more agents add noise. Third, for parallelizable tasks like financial reasoning, centralized coordination improved performance by **+80.9%** — but for sequential reasoning tasks, every multi-agent variant degraded performance by **39-70%**. The implication: Keystone should use multi-agent parallelism for research gathering (Layer 1) but single-agent depth for synthesis and judgment (Layer 2). [Evidence: **Verified** — peer-reviewed, 180 configurations tested]

Manus's Meta acquisition (**$2B+, confirmed December 2025** by WSJ, CNBC, Reuters) validates the commercial viability of autonomous research agents. Its Wide Research feature deploys hundreds of parallel agents, each a **full-featured Manus instance** in its own VM with fresh context. The critical architectural insight: agents **do not communicate with each other**, preventing context pollution and hallucination propagation. This solves the "fabrication threshold" problem where sequential processing degrades after 8-10 items — each agent gets a clean slate, so item #250 receives the same analysis depth as item #1. [Evidence: **Verified** — multiple major news outlets confirmed acquisition]

The **MAST taxonomy** (NeurIPS 2025) analyzed 1,642 execution traces across 7 open-source multi-agent frameworks, identifying **14 failure modes**: specification and system design issues account for 37% of failures (agents disobeying constraints, getting stuck in loops), inter-agent misalignment accounts for 31% (communication failures, ignoring peer input, role confusion), and task verification failures account for 31% (incomplete or incorrect verification). The critical finding: **failures stem from system design, not model limitations**. Tactical fixes like prompt refinement yield only 9-15% improvement; structural redesigns are required. State-of-the-art multi-agent system correctness rates range from **25% to 86.7%** across frameworks. [Evidence: **Verified** — NeurIPS accepted paper]

Anthropic's own research found that multi-agent systems (Opus 4 lead + Sonnet 4 subagents) outperform single-agent Opus 4 by **90.2%** on internal research evaluations. But **token usage explains 80% of performance variance** — multi-agent is fundamentally a way to scale token consumption across parallel context windows. Agents use 4× more tokens than chat; multi-agent systems use **15× more tokens** than single-agent chats. Cost control requires matching model to task: use expensive models for planning/synthesis, cheap models for execution.

**Recommendations:**

- **Centralized orchestrator** → USE (Keystone's DPVI architecture is validated; never use flat peer-to-peer)
- **Context isolation per agent** → USE (Manus's clean-slate pattern prevents error propagation)
- **Parallel for research, serial for synthesis** → USE (Layer 1 parallel, Layer 2 serial based on Google/MIT findings)
- **Performance saturation at ~4 agents per task** → USE (cap agent count per sub-task; scale by decomposing into more sub-tasks, not more agents per sub-task)
- **Model tiering** → USE (Opus/o3 for planning and evaluation, Sonnet/4o-mini for execution)
- **MAST failure taxonomy** → USE (design specification contracts and verification checks against all 14 failure modes)

---

## 8. Five layers make "cite-or-it-dies" architecturally enforceable

No single mechanism enforces citation integrity — the research reveals that **layered defense is required**. Here is the five-layer architecture that makes unsourced claims structurally impossible to produce or propagate.

**Layer 1 — Retrieval-constrained generation (prevention):** The generation model receives ONLY retrieved passages as context. Perplexity's core principle: "You're not supposed to say anything that you didn't retrieve." This constrains the generation space by design, not by instruction. However, Perplexity's own documentation acknowledges that links in structured outputs "may not always work reliably and can result in hallucinations." Retrieval constraint is necessary but insufficient alone. [Evidence: **Verified** — Perplexity technical documentation]

**Layer 2 — Structured output with mandatory citation fields (structural):** OpenAI's structured output mode achieves **100% JSON schema compliance** in strict mode by masking logits at the token level so only schema-valid tokens can be sampled. A schema requiring `source_url`, `source_passage`, and `confidence` for every `claim` object makes it literally impossible to generate a claim without an associated source field. For self-hosted models, **Outlines** (dottxt-ai) and **XGrammar** provide equivalent constrained decoding. Critical nuance: schema enforcement guarantees format but **not content quality** — a citation field will always exist, but may contain a hallucinated URL. [Evidence: **Verified** — OpenAI API documentation, Outlines GitHub]

**Layer 3 — Post-generation verification agent (detection):** Chain-of-Verification (CoVe, ACL 2024) decomposes output into atomic claims, generates verification questions for each, answers them independently (crucial — to avoid bias), and regenerates only from verified facts. RARR (CMU/Google, ACL 2023) provides a model-agnostic post-generation attribution system that preserves 90%+ of original content while significantly improving attribution. RAGentA (SIGIR 2025) implements this as a four-agent pipeline with specialized query, filter, predictor, and reviser agents. [Evidence: **Verified** — peer-reviewed at ACL, SIGIR]

**Layer 4 — Hard gate rejection (enforcement):** Every sentence without a citation marker is automatically stripped. Simple regex detection plus NLI validation. Only cited content reaches the user. This is the "die" in "cite-or-it-dies."

**Layer 5 — Provenance graph (auditability):** A directed acyclic graph where leaf nodes are primary source documents, intermediate nodes are agent-produced summaries with source references, and root nodes are final output claims. Each edge carries source_id, relevant_passage, and an NLI score. At output time, traverse the graph to verify every claim has a complete path to a primary source. This solves the unsolved problem of **multi-agent citation propagation** — when Agent B summarizes Agent A's output, how do citations transfer?

Stanford's **STORM** achieves **84.8% citation recall and 85.2% citation precision** using a reference-pool constraint: references are gathered before writing begins, and the writing agent can only cite from the pre-collected set. This is directly implementable in Layer 1→Layer 2 handoffs. The **ALCE benchmark** (Princeton, EMNLP 2023) provides evaluation metrics using NLI-based automatic citation assessment. [Evidence: **Verified** — Stanford NAACL 2024, Princeton EMNLP 2023]

**Recommendations:**

- **Five-layer citation defense** → USE (implement all five layers; no single mechanism suffices)
- **Structured output schemas** → USE (OpenAI structured outputs for API models, Outlines for self-hosted)
- **STORM's reference-pool constraint** → USE (gather sources first, write second)
- **CoVe verification pattern** → USE (implement as dedicated Verification Agent in Layer 4)
- **ALCE benchmark** → USE (for continuous monitoring of citation quality)
- **Provenance DAG** → LEARN (build custom; no existing implementation handles multi-agent citation propagation)

---

## 9. Self-improvement is no longer theoretical — HyperAgents and GEPA prove it

The Meta-Layer's self-improvement capabilities are the most technically ambitious component of Keystone, but recent developments make them implementable rather than aspirational.

**GEPA** (Genetic-Pareto, ICLR 2026 Oral) represents the state of the art in prompt optimization. It uses natural language reflection instead of scalar rewards — diagnosing problems, proposing fixes — and **outperforms MIPROv2 by 10%+** (up to 12% on AIME-2025) while using **35× fewer rollouts** than GRPO. It achieves **93% accuracy on MATH** versus 67% with basic Chain-of-Thought, all through DSPy's Full Program Adapter. GEPA is already integrated into MLflow's `mlflow.genai.optimize_prompts()` API with adapters for DSPy programs, RAG systems, and MCP tools. For Keystone, this means every agent's soul prompt can be automatically optimized against the Layer 4 evaluator's quality scores. [Evidence: **Verified** — ICLR 2026 oral presentation, MLflow integration documented]

**HyperAgents** (Meta AI, March 2026) pushes further into genuine self-modification. It merges task agent and meta agent into a single self-referential program that can rewrite **both its task-solving code and its self-improvement mechanism**. Without being instructed to, HyperAgents spontaneously developed performance tracking classes, persistent memory with timestamped storage for causal hypotheses, and compute-aware planning logic. On paper review tasks, accuracy jumped from 0.0 to **0.71**, beating AI-Scientist-v2 (0.63). These are genuine methodological innovations the system discovered autonomously. [Evidence: **Credible** — Meta AI paper, March 2026, not yet peer-reviewed at conference]

For the Rejection Library, **AgentHER** (Hindsight Experience Replay) provides the exact mechanism: a trajectory that fails goal A is often a correct demonstration for some alternative goal B. It converts failed agent trajectories into high-quality training data through failure classification, outcome extraction, LLM-guided prompt relabeling, and data packaging. Multi-judge verification reduces label noise from 5.9% to **2.3%**. The **AgentDebug** framework achieves **24% higher accuracy** and 17% higher step accuracy by isolating root-cause failures and providing corrective feedback. [Evidence: **Credible** — arXiv preprints, reproducible frameworks]

Google DeepMind's **AlphaEvolve** (May 2025) demonstrates the ceiling of evolutionary self-improvement: it improved a 50-year-old matrix multiplication record, recovered **0.7% of Google's worldwide compute** through an evolved Borg scheduling heuristic, and achieved 23% speedup on a critical Gemini training kernel. Its meta-level evolution — evolving not just solutions but the strategies used to find them — mirrors what the Meta-Layer should aspire to.

**Implementation roadmap for the Meta-Layer:**

- **Immediate**: Implement the autoresearch ratchet loop for all measurable quality dimensions. Build a trajectory database logging complete agent traces with structured metadata. Deploy GEPA through DSPy to optimize all agent prompts against the Layer 4 evaluator.
- **Medium-term**: Define research quality as constitutional principles and train evaluators via RLAIF. Implement AgentHER-style hindsight relabeling to convert failed research trajectories into training data. Use MAP-Elites-style archives to maintain diverse high-performing agent configurations.
- **Long-term**: Allow the system to modify not just prompts but orchestration logic (HyperAgent pattern). Build cross-domain methodology transfer. Automated methodology experimentation — the equivalent of AlphaEvolve applied to research workflow discovery.

**Recommendations:**

- **GEPA + DSPy** → USE (immediate; optimize all soul prompts against quality scores)
- **Autoresearch ratchet loop** → USE (immediate; keep improvements, revert failures)
- **AgentHER trajectory relabeling** → LEARN (build custom failure-to-training-data pipeline)
- **AgentDebug error taxonomy** → USE (classify all Layer 4 rejections for systematic improvement)
- **HyperAgent self-modification** → LEARN (medium-term; requires robust rollback mechanisms and human oversight gates)
- **AlphaEvolve** → SKIP (requires Google-scale compute; learn the meta-evolution concept only)

---

## 10. Five human capabilities remain beyond AI's reach — and three of them matter for Keystone

The gap between elite human analysts and AI research is **wide but narrowing unevenly**. Five capabilities remain fundamentally or near-fundamentally human. Three of them have direct implications for Keystone's design.

**Trust-based relationship intelligence is irreducible.** BCG conducts 15,000+ expert consultations annually. GLG's network spans 1.2 million professionals. Expert networks exist because humans share privileged insights with humans they trust — implementation reality, organizational dysfunction, competitive dynamics known only to insiders. No AI system can attend dinners, earn confidences through demonstrated discretion, or dynamically pivot an interview when sensing a source is holding back. This does not mean Keystone should ignore primary research — it means **Keystone should be designed to augment expert interviews**, not replace them. Layer 0 should generate interview guides from intelligence frameworks; Layer 3 should produce interview transcription analysis; the system should integrate expert network APIs (GLG, AlphaSights) as data sources.

**Cross-industry analogical reasoning remains AI's weakest analytical skill.** Research rooted in Gentner's Structure-Mapping Theory (1983) shows that true analogy requires systematic mapping of relationships between domains — not surface-level pattern matching. LLMs perform analogical reasoning as "an emergent phenomenon of pattern recognition rather than deliberate mapping," lacking "a formal mechanism for ensuring correspondence between domains is consistent and logically valid." Melanie Mitchell's assessment: "No current AI system is anywhere close to forming humanlike abstractions or analogies." For Keystone, this means the Structured Analogies SAT should be implemented as a **human-in-the-loop** component where the system identifies candidate analogies but a human validates structural mapping. [Evidence: **Verified** — peer-reviewed cognitive science]

**Time-soaked experiential judgment differentiates 5-year from 20-year analysts.** As IE Business School's analysis states: "AI does not understand time. It can recall a prompt from 15 seconds ago, but it cannot appreciate what unfolds over five years of a messy product rollout." The California Management Review (March 2026) found that "the real differentiator is not the data or even the models, but the tacit knowledge embedded in the judgment of their people." For Keystone, the architectural implication is the **"Danger Zone"** warning: novices using AI for judgment-based tasks produce "polished work but lack the foundational judgment to distinguish good insights from compelling-sounding nonsense." Layer 4's evaluator must flag confidence levels and explicitly mark where human judgment is required.

Two areas are **narrowing faster than expected**. Linguistic analysis of corporate communications — "reading between the lines" of earnings calls — is increasingly AI-capable. Research shows deceptive executives display more extreme positive emotion, fewer anxiety words, and more references to general knowledge. Business Intelligence Advisors hires ex-CIA officers to detect these patterns; AI models now achieve 6-16% better than random on deception detection, and multimodal approaches fusing verbal and vocal cues are improving rapidly. Regulatory monitoring is similarly advancing: NLP systems process thousands of sources simultaneously, with financial institutions reporting 40% reduction in legal advisory hours. But predicting **what will change** (versus detecting what has changed) remains firmly human.

**Recommendations:**

- **Expert interview augmentation** → USE (Layer 0 generates interview guides; Layer 3 analyzes transcripts)
- **Structured Analogies as human-in-the-loop** → USE (system identifies candidates; human validates structural mapping)
- **Earnings call linguistic analysis** → LEARN (implement FinBERT-based sentiment + vocal analysis as Layer 1 agents)
- **"Danger Zone" warnings in Layer 3 output** → USE (flag where human judgment is required vs. where AI confidence is high)
- **Expert network API integration** → USE (GLG, AlphaSights as Layer 1 data sources alongside web research)
- **Regulatory monitoring agents** → LEARN (NLP-powered scanning of government portals, but prediction requires human layer)

---

## Conclusion: the evaluator is the system, and the system improves itself

Three findings from this research should reshape Keystone's development priorities. First, **ICD 203's nine tradecraft standards should be implemented as hard validation gates in Layer 4**, not aspirational guidelines. Each standard maps to a specific, implementable check: source credibility rating, calibrated probability language, explicit assumption identification, alternative hypothesis evaluation. The intelligence community spent decades codifying what "good analysis" means. Use it.

Second, **the five-layer citation architecture converts "cite-or-it-dies" from philosophy to engineering**. Retrieval-constrained generation prevents most unsourced claims. Structured output schemas make citation fields mandatory at the token level. Post-generation verification catches hallucinated citations. Hard gates strip anything uncited. Provenance graphs enable end-to-end auditability across agent boundaries. No single layer is sufficient; all five together approach structural guarantee.

Third, **GEPA + the autoresearch ratchet make the Meta-Layer immediately implementable**. Every soul prompt can be automatically optimized against quality scores. Every failed output becomes training data through AgentHER-style hindsight relabeling. The ratchet ensures the system only moves forward. And the emerging evidence from HyperAgents and AlphaEvolve suggests that systems with robust evaluation infrastructure genuinely discover methodological improvements humans haven't articulated — the most ambitious promise of the Meta-Layer is grounded in 2026 evidence, not speculation.

The research confirms Keystone's core bet: **the evaluator matters more than the generators**. Google/MIT's finding that performance saturates beyond ~4 agents but improves dramatically with better evaluation; MAST's finding that failures stem from system design not model limitations; Anthropic's finding that token budget allocation explains 80% of performance variance — all point to the same conclusion. Build the evaluator first. Make it rigorous. Let everything else evolve around it.