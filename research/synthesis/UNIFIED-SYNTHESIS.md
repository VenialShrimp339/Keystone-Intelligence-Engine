# Unified Synthesis: 16-Report Research Analysis
*Produced: 2026-04-04 | Synthesized from 16 per-report analyses across 4 threads*

---

## 1. Cross-Thread Convergent Findings

These findings appeared independently across 2+ threads. They represent the highest-confidence architectural guidance.

### 1.1 Evaluation Is the Highest-Leverage Investment (A1, A2, A3, B1, B3, B4, D1, D2)

**Convergence:** Every thread independently concluded that evaluation quality bounds output quality. A1 found no existing system has structural evaluation. A2 found SOS-Bench proves holistic judging is broken. B4 delivered a 28-failure-mode taxonomy. D2 quantified the 60-68% single-judge ceiling in expert domains. B3 found evaluation is partially decomposable (65% dimensional, 35% holistic).

**Architectural implication:** The Evaluator is not a single component. It is a five-layer stack:
1. **Deterministic verification** (FActScore atomic facts, citation URL liveness, numerical consistency) -- ungameable foundation
2. **Citation validation** (CrossRef/Semantic Scholar/OpenAlex existence checks) -- pre-rubric binary gate
3. **Multi-rubric scoring** (Prometheus 2 with custom consulting rubrics, 10 dimensions) -- decomposed evaluation
4. **Process trajectory evaluation** (Agent-as-a-Judge pattern) -- methodology quality, not just output quality
5. **Diverse judge ensemble** (PoLL pattern: 2-3 models from different families, SE-Jury dynamic selection) -- bias mitigation

**Confidence:** Verified. SOS-Bench (152K data points, ICLR 2025), DeepMind (180 configurations), CALM (12 bias types), multiple peer-reviewed sources.

---

### 1.2 Specification Quality Determines Output Quality (A1, A4, C1, D1, D2, D3)

**Convergence:** Six systems proved the specification layer dominates. Superpowers (120K stars) produces identical results across 8 LLM platforms -- the implementing model doesn't matter. ATLAS's Darwinian evolution downweighted its synthesis agent to minimum (0.3). MAST taxonomy: 36.9% of MAS failures stem from specification/system design. Google DeepMind: centralized coordination reduces error amplification from 17.2x to 4.4x.

**Architectural implication:** L0 (Specification Engine) is correctly positioned as the highest-value component. The plan should formalize: write RESEARCH.md task decompositions "as if for an enthusiastic junior engineer with poor taste, no judgment, no project context, and an aversion to testing" (Superpowers framing). Cache stability of specification files matters: 10x cost difference between cached and uncached tokens (Manus AI).

**Confidence:** Verified. Academic (arXiv:2602.00180 Spec-as-Source taxonomy), empirical (Superpowers cross-platform), production (MAST 1,642 traces).

---

### 1.3 Iterative Debate Is a Mathematical Martingale (C1, C2, D2, D3)

**Convergence:** The plan's "structured multi-perspective debate" design is empirically wrong. NeurIPS 2025 Spotlight proved debate forms a martingale (expected future value equals current value). Majority voting alone (0.7691) outperformed best debate variant (0.7377). More rounds consistently degraded performance. DeepMind found unstructured multi-agent networks amplify errors 17.2x. Wu et al. found majority pressure suppresses independent correction below 5%.

**Architectural implication:** Redesign L1.5 as two phases:
- **Phase 1: Independent Parallel Analysis** -- each agent analyzes the same findings using a different analytical methodology (ACH, quantitative modeling, adversarial critique, historical analogy) with no inter-agent communication
- **Phase 2: Structured Aggregation** -- strongest model aggregates all outputs via DAR-style diversity-aware filtering, one curmudgeon challenge round, then final synthesis

**Additionally:** Methodological diversity (DMAD, ICLR 2025) consistently outperforms persona diversity (bull/bear/consensus). Cross-provider model diversity (Claude + GPT + Gemini) is a functional requirement, not a preference.

**Confidence:** Verified. NeurIPS 2025 Spotlight (formal proof + empirical), ICLR 2025 (Self-MoA, DMAD), Google DeepMind (180 configurations).

---

### 1.4 Single LLM Judge Is Fundamentally Insufficient (A2, B4, D1, D2)

**Convergence:** A2 found same-family evaluation has a perplexity-based bias mechanism. B4 quantified CALM's 12 bias types (authority 33.8%, bandwagon 20.9-39%). D2 documented the 60-68% single-judge ceiling in expert domains. D1 established 0.80+ Spearman correlation from 100-200 expert-scored samples as the production calibration standard.

**Architectural implication:** The Evaluator must use cross-model ensembles. Never use Claude to evaluate Claude-generated output without a cross-model ensemble member. Calibrate against actual Keystone deliverables with a hard threshold: 0.80+ Spearman correlation before production deployment.

**Confidence:** Verified. "Play Favorites" (causal mechanism identified), CALM (ICLR 2025), SOS-Bench (ICLR 2025).

---

### 1.5 Citation Enforcement Requires Five Layers (A5, B1, C3, D3)

**Convergence:** Prompt-based self-citation fails >60% (Tow Center). Deloitte Australia (AU$440K, fabricated references) and Deloitte Canada (CA$1.6M, fabricated citations) are documented category failures. STORM achieves only 84.8% citation recall with a single mechanism.

**Five-layer architecture:**
1. Retrieval-constrained generation (model receives only retrieved passages)
2. Structured output with mandatory citation fields (schema enforcement)
3. Post-generation verification agent (CoVe decomposition into atomic claims)
4. Hard gate rejection (every uncited sentence stripped)
5. Provenance graph (DAG tracing every claim to primary source)

**Architectural implication:** Add CitationProcessor as a discrete pipeline stage between L1 (Research) and L1.5 (Deliberation). Implement PROV-AGENT (IEEE e-Science 2025) for multi-agent citation propagation. Source fabrication is a pre-rubric binary gate, not a scored dimension.

**Confidence:** Verified. Deloitte incidents (AP, Fortune, Guardian), Tow Center (Columbia), STORM (NAACL 2024), PROV-AGENT (IEEE).

---

### 1.6 Self-Improvement Saturates Without New Failure Signals (A3, D2)

**Convergence:** A3 found Goodhart's Law at 19.3% measured rate. D2 found saturation after 2-3 iterations (ICLR 2025 Oral). Combined: optimizing against a kappa-0.52 proxy at 19.3% gaming rate means self-improvement is more likely to game a bad metric than improve actual quality. Mode collapse documented: agents converge on single strategy while metrics plateau.

**Architectural implication:** Multi-metric Pareto selection (not single-metric optimization). Monitor trajectory entropy across Deliberation. Inject new failure signals through domain expansion, adversarial probing, and periodic human review of borderline cases. The plan's description of monotonic improvement needs an explicit saturation-breaking mechanism.

**Confidence:** Verified. ICLR 2024 (Goodhart), ICLR 2025 Oral (saturation), Microsoft Agent Lightning (mode collapse).

---

### 1.7 MCP Is the Integration Layer but Requires Defensive Engineering (A4, C4)

**Convergence:** A4 found 68.8% inter-agent data leakage in standard frameworks. C4 found 66% of MCP servers have security findings (8,282 tool-level issues). 53% rely on static API keys. Context window exhaustion: 10+ servers load 75K-100K+ tokens of tool definitions.

**Architectural implication:** Build an MCP gateway with: OAuth authentication, container isolation per server, audit all tool descriptions for hidden instructions, intelligent tool routing with lazy loading, Redis-backed rate limiter, circuit breakers per provider. Only deploy the seven vetted servers initially.

**Confidence:** Verified. AgentLeak (4,979 traces), AgentSeal (1,808 servers scanned), CVEs documented.

---

### 1.8 ICD 203 Intelligence Tradecraft Standards Map Directly to the Pipeline (B1, B2, D3)

**Convergence:** B1 found five IC structured analytic techniques translate directly into pipeline components without modification. B2 found ICD 203's estimative vs. current intelligence distinction requires evaluator mode-switching. D3 found ACH matrix is the natural data structure for the Confidence Map.

**Architectural implication:** Implement ICD 203 as nine L4 validation gates. Use ACH matrix as L1.5's structural backbone for the Confidence Map. Implement calibrated probability language (seven-term scale) as a pass/fail criterion for Intellectual Honesty.

**Confidence:** Verified. ICD 203 is official US government directive.

---

## 2. Unified Tool/Framework Verdict Matrix

### Pipeline Layer: L0 (Specification Engine)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| .claude/ directory + CLAUDE.md | C1 | BUILD | Native deployment format; every agent role maps to .claude/agents/*.md |
| SKILL.md progressive disclosure | C1 | BUILD | Three-level lazy loading is the plan's Section 4.4 implemented natively |
| GitHub Spec Kit 4-phase pattern | C1 | LEARN | Adapt Specify-Plan-Tasks-Implement for consulting research lifecycle |
| Kiro EARS notation | C1 | LEARN | WHEN/SHALL pattern makes acceptance criteria testable by Evaluator |
| Semantic Router (Aurelio AI) | C4 | BUILD | <5ms query routing before LLM routing; critical for parallel retrieval |
| STORM perspective discovery | A1 | LEARN | Auto-mining analytical angles enriches specification, not runtime use |

### Pipeline Layer: L1 (Research Agents)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| Exa | A1, A5 | INTEGRATE | Primary semantic search; category search for SEC/companies/papers unique |
| Brave Search API | A1, A5 | INTEGRATE | Only independent Western index post-Bing shutdown; highest benchmark |
| Firecrawl | A5 | INTEGRATE | Full-page extraction; Agent endpoint for autonomous browsing |
| Tavily | A1, A5 | INTEGRATE | RAG-optimized structured output; news-focused tertiary search |
| EdgarTools MCP | A5, C4 | BUILD | Free, MIT, 13 tools, 30+ SEC form types; deploy first |
| Financial Modeling Prep MCP | C4 | BUILD | $19/month for 70K+ securities; essential financial data |
| FRED MCP | C4 | BUILD | 800K+ time series; focused 3-tool design prevents context bloat |
| Government Data MCP | A5, C4 | BUILD (caution) | 300+ tools, free; verify critical data (6-star project) |
| Academix MCP | C4 | BUILD | Unified search across OpenAlex/DBLP/Semantic Scholar/arXiv/CrossRef |
| Semantic Scholar | A5, C4 | INTEGRATE | 225M+ papers; TLDR summaries; citation classification |
| OpenAlex | A5 | INTEGRATE | 278M+ works, CC0, paired with Semantic Scholar |
| Stagehand v3 | A5 | INTEGRATE | Best browser automation; action caching for repeat patterns |
| Playwright MCP | A5 | INTEGRATE | 4x more token-efficient than vision mode; cost-optimized extraction |
| Docling (IBM) | C4 | BUILD | Only viable SEC filing PDF parser; 42K stars, 1.5M monthly downloads |
| 199-bio deep-research-skill | D1 | INTEGRATE (skeleton) | 8-phase pipeline with critique loop-back; closest to L1 agent design |
| GPT-Researcher (MCP only) | A1 | INTEGRATE | Use gptr-mcp as callable research backend; don't rely on its evaluation |
| SearXNG | A1, A5 | LEARN | Zero-cost development/fallback; not production primary |

### Pipeline Layer: L1.5 (Deliberation)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| Together AI MoA (propose-aggregate) | C2 | BUILD | Foundation pattern; aggregator quality > proposer quality |
| ReConcile (confidence-weighted voting) | C2 | BUILD | Confidence-weighted aggregation for Confidence Map |
| DiscoUQ | C2 | BUILD | Structured disagreement tracking; AUROC 0.802 |
| CIR3 Curmudgeon Agent | C2 | BUILD | Structurally enforced devil's advocate with diversity score |
| DAR (Diversity-Aware Retention) | C2 | BUILD | Preserves authentic dissent before aggregation |
| ICD 203 ACH matrix | B1, D3 | BUILD | Natural data structure for Confidence Map |
| DMAD methodological diversity | D2 | INTEGRATE | Different reasoning methods > different roles |

### Pipeline Layer: L2-L3 (Structuring & Generation)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| Anthropic Skills API (PPTX/DOCX) | C3 | BUILD | L3 document generation foundation; progressive disclosure |
| PPTAgent/DeepPresenter | C3 | BUILD | Environment-grounded slide generation; fine-tuned model |
| python-pptx | C3 | BUILD | Essential PPTX manipulation; note single-maintainer risk |
| Typst | C3 | BUILD | Data-driven PDF; built-in JSON ingestion for Confidence Map |
| Vizro (QuantumBlack Labs) | C3 | BUILD | McKinsey visual standards programmatic; Vizro-MCP |
| PROV-AGENT | C3 | BUILD | Citation provenance graph; W3C PROV standard |
| Streamlit | C3 | BUILD | Interactive deliverables; 21% more time, 41% higher completion |
| DoWhy (causal inference) | D3 | INTEGRATE (Phase 2) | 1M+ installs; refutation step prevents spurious claims |

### Pipeline Layer: L4 (Evaluator)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| DeepEval (G-Eval + DAG) | A2 | INTEGRATE | Custom criteria engine for 10-dimension rubric |
| Prometheus 2 | A2, B4, D2 | INTEGRATE | Open-source judge model; 72-85% human agreement; local deployment |
| FActScore | B4 | INTEGRATE | Atomic fact verification; <2% error vs. human; Layer 1 of eval stack |
| ARES | B4 | INTEGRATE | RAG evaluation; outperforms RAGAS by 59.3pp |
| Promptfoo | A2, C2 | INTEGRATE | Evaluator testing; adversarial red-teaming; canary sets |
| CALM framework | A2 | INTEGRATE | Monthly diagnostic audit; 12 bias types quantified |
| Agent-as-a-Judge | B4, D2 | BUILD | Process trajectory evaluation; 90% human agreement |
| SE-Jury dynamic selection | B4, D2 | INTEGRATE | 29.6-140.8% improvement; 50% cost reduction |
| PoLL diverse panel | B4, D2 | INTEGRATE | 3 smaller diverse models > single GPT-4; 7x cheaper |
| Arize Phoenix | A2 | INTEGRATE | Observability + eval storage; lightest Mac Mini footprint |
| Google Check Grounding API | C3 | BUILD | Sub-500ms claim-to-source verification |
| DeepResearchGym | B4, D2 | INTEGRATE | External benchmark for calibration |
| Antislop Sampler | C3 | LEARN | 8K+ pattern suppression; 90% slop reduction |
| Kahneman Noise audit | B2 | INTEGRATE | Parallel evaluation + conservative scoring |
| ICD 203 tradecraft standards | B1, B2, D3 | INTEGRATE | Nine L4 validation gates |

### Pipeline Layer: META (Self-Improvement)

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| GEPA / DSPy v3.1.3 | A3, D2, D3 | INTEGRATE | Best prompt optimizer; 35x fewer rollouts; MLflow integration |
| Cognee | A3 | INTEGRATE | Knowledge graph backbone for Observation Library |
| codex-autoresearch lessons pattern | A3 | INTEGRATE | Cross-run persistent lessons; graduated escalation |
| HKUDS OpenSpace skill evolution | A3 | INTEGRATE | FIX/DERIVED/CAPTURED modes map to Observation Library |
| ECC instinct-to-skill pipeline | C1, D1 | INTEGRATE | Hook-based capture; confidence-scored pattern learning |
| Engram MCP (199-bio) | D1 | INTEGRATE | Temporal memory decay; 80% LOCOMO benchmark |
| AgentHER | D3 | INTEGRATE (Phase 2) | Failed trajectories to training data; 2.3% label noise |

### Pipeline Layer: Infrastructure

| Tool/Framework | Thread | Verdict | Justification |
|---|---|---|---|
| PydanticAI | A4 | INTEGRATE | Type-safe handoff contracts; auto-re-prompting |
| Claude Agent SDK | A4 | INTEGRATE | Execution substrate; session forking; hooks |
| Temporal | A4 | INTEGRATE | Durable execution; crash recovery; human-in-the-loop gates |
| MCP (Linux Foundation) | A4 | INTEGRATE | De facto tool standard; requires gateway architecture |
| AG-UI (CopilotKit) | A4 | INTEGRATE | Token-by-token streaming for output delivery |
| pgvector + pgvectorscale | C4 | BUILD | 28x lower latency than Pinecone; ACID; SQL joins |
| Cohere Embed v4 | C4 | BUILD | 128K context; multimodal; $0.12/M tokens |
| BGE-M3 | C4 | BUILD | Self-hosted hybrid vectors; zero API cost; Mac Mini |
| Cohere Rerank 4 Pro | C4 | BUILD | 0.932 hit rate; enterprise SLAs |
| Jina Reranker v2 | C4 | BUILD | Self-hosted fallback; function-calling aware |
| Bifrost caching | C4 | BUILD | Dual-layer cache with per-source TTLs |
| NewsGuard | C4 | BUILD | 35K+ sources; journalist-assessed credibility scores |
| E2B sandboxing | D3 | INTEGRATE | 80ms startup; $0.05/hr; code execution isolation |
| markdownlint-cli2 | C1 | BUILD | Cheapest structural quality gate for spec files |
| AgentShield | C1 | BUILD | Security scanning for .claude/ specs; 98% coverage |
| LangGraph | A1, A4, C2, D1 | LEARN patterns | Best-documented orchestration patterns; security/licensing concerns prevent direct dependency |
| CrewAI | A4 | SKIP | Router bug (#1579); no checkpointing; prototype only |
| Milvus | C4 | SKIP | Kubernetes required; overkill for Keystone scale |
| ChromaDB | C4 | SKIP | Not production-grade; no hybrid search |
| TextGrad | A3 | SKIP | Superseded by GEPA |
| Mem0 | A3 | SKIP | Wrong abstraction; graph features paywalled |
| Letta/MemGPT | A3 | SKIP | Adopting whole framework conflicts with custom architecture |

---

## 3. Contradiction Resolutions

### 3.1 LangGraph: INTEGRATE vs. LEARN

**A1 says:** INTEGRATE as orchestration backbone (DeerFlow 39K stars validates it).
**A4 says:** LEARN patterns only (3 CVEs in March 2026, CVSS 9.3, Elastic-2.0 licensing).

**Resolution: LEARN.** A4's analysis is more thorough and identifies specific, documented risks. No existing framework natively supports Keystone's combination of strict isolation + reject/regenerate + handoff contracts + filesystem-as-state. Build custom orchestration using LangGraph's patterns (typed state, conditional edges, Send API), PydanticAI for agent definition, Temporal for durable execution, MCP for tools. The orchestration layer should be built for replaceability, not sophistication.

---

### 3.2 Deliberation Design: Debate vs. Aggregation

**Plan says:** "Structured multi-perspective debate" with synthesis round where personas critique each other.
**C2/D2 say:** Iterative debate is a mathematical martingale. Methodological diversity > persona diversity.
**C1 says:** DeepMind finds 17.2x error amplification in unstructured multi-agent networks.

**Resolution: Redesign L1.5.** Replace iterative debate with:
1. Independent parallel analysis (no inter-agent communication)
2. Each agent uses a different analytical methodology (ACH, quantitative modeling, adversarial critique, first-principles reasoning, historical analogy)
3. Cross-provider model diversity (Claude + GPT + Gemini)
4. Structured aggregation using DAR-style diversity-aware filtering
5. One curmudgeon challenge round
6. Final synthesis by strongest model as aggregator

The plan's core intuition (multiple perspectives + structured synthesis) is correct. The mechanism (iterative debate with critique rounds) is empirically wrong.

---

### 3.3 Rubric Dimensions: 8 vs. 10

**Plan says:** Eight dimensions totaling 100%.
**B3 says:** Add Evaluative Surprise (5%) and Calibrated Confidence (5%), reduce Analytical Depth (15%->12%) and Completeness (10%->8%).
**B1 says:** Reduce Completeness weight; add trendslop detection to Actionability.
**B2 says:** Add deletion test to Completeness; add task-type-specific weight profiles.

**Resolution: Adopt 10 dimensions.** The two new dimensions address the most significant blind spots identified across all Thread B reports. Additionally:
- Add pre-rubric binary gate for citation fabrication (B1)
- Add trendslop detection as Actionability sub-criterion (B1, B2)
- Add deletion test as Completeness sub-criterion (B2)
- Add ICD 203 calibrated probability language to Calibrated Confidence (B2)
- Add task-type field for estimative vs. current intelligence weight profiles (B2)

---

### 3.4 Rejection Library: Rejections-Only vs. Full Observation

**Plan says:** "Every evaluator rejection becomes a structured entry."
**D1 says:** ECC captures every tool call and outcome at 100% reliability, not just failures.

**Resolution: Expand to Observation Library.** Capture successes and failures. Positive patterns (what worked) are as valuable as negative patterns (what failed). The `/evolve` mechanism clusters both. The existing plan's Rejection Library becomes the negative-space component of a broader Observation Library that also captures positive patterns for reinforcement.

---

### 3.5 Self-Improvement Trajectory: Monotonic vs. Saturating

**Plan says:** "The 20th engagement should be meaningfully better than the 5th." Implies monotonic improvement.
**D2 says:** "Mind the Gap" (ICLR 2025 Oral): saturation after 2-3 iterations without new information.
**A3 says:** Goodhart's Law at 19.3%. Mode collapse documented.

**Resolution: Both true at different timescales.** Early stages see rapid improvement as new failure types are frequently encountered. After initial improvement curve, the META layer needs explicit saturation-breaking mechanisms: expansion to new research domains, adversarial probing, deliberate hard cases, periodic human review of borderline outputs. Add multi-metric Pareto selection to prevent Goodhart's Law. Monitor trajectory entropy to detect mode collapse.

---

### 3.6 Completeness: Valued vs. Harmful

**B2 says:** Comprehensiveness past decision-readiness actively degrades quality (Federal Reserve research, Heuer).
**B3 says:** Retain Completeness at reduced weight (10%->8%).
**B1 says:** "Completeness in consulting means covering the decision-relevant territory, not covering everything."

**Resolution: Compatible.** These are measuring different things. Completeness scores coverage of decision-relevant territory (absence detection: what's missing that matters). B2's deletion test scores information overload (presence detection: what's present that doesn't matter). Both become sub-criteria of the Completeness dimension at 8% weight.

---

## 4. Remaining Gaps

### Unanswered by any report:
1. **Keystone-specific rubric calibration methodology** -- requires actual Keystone deliverables scored by experienced consultants; cannot be researched in advance
2. **Multi-tenancy architecture for client isolation at scale** -- client data sandboxing is described at the principle level but not engineered
3. **EU AI Act compliance (August 2026 deadline)** -- specification documentation requirements are mentioned but not designed for
4. **Expert network integration design** -- GLG/AlphaSights are recommended as data sources but no integration architecture is specified
5. **Temporal knowledge graph implementation** -- recommended for living competitive landscapes but no production architecture evaluated
6. **Evaluator calibration drift detection** -- how to detect when the Evaluator's agreement with human judgment deteriorates over time
7. **Cost model for the full 5-layer evaluation stack** -- A5 estimates $7-$85/engagement but this predates the 5-layer evaluation recommendation
8. **Rate limit management at 15-50 parallel agents** -- Tier 4+ API access or custom invoicing required but not negotiated

---

## 5. Implementation Priority

### Phase 1: Core Pipeline (Build First)

| # | Component | Tools | Complexity | Dependencies | Rationale |
|---|---|---|---|---|---|
| 1 | RESEARCH.md specification format | .claude/skills/, EARS notation | S | None | Foundation everything validates against |
| 2 | Specification Engine (L0) | Claude Agent SDK, PydanticAI, Semantic Router | L | #1 | Quality ceiling of entire system; plan-based retrieval = 40%->100% accuracy |
| 3 | 5-layer Evaluator stack (L4) | FActScore, Prometheus 2, DeepEval, PoLL ensemble, Arize Phoenix | XL | #1 | Most important component; build deterministic gates first |
| 4 | Research Agent pipeline (L1) | Exa, Brave, Firecrawl, EdgarTools, MCP gateway | L | #1, #2 | Strict isolation + per-agent tool specialization (3-5 tools each) |
| 5 | CitationProcessor | PROV-AGENT pattern, CrossRef/Semantic Scholar APIs | M | #4 | New discrete stage between L1 and L1.5; cross-agent corroboration |
| 6 | Basic Deliberation (L1.5) | MoA propose-aggregate, DiscoUQ, ACH matrix | L | #4, #5 | Independent parallel analysis + structured aggregation (not debate) |
| 7 | pgvector + hybrid search retrieval | pgvector + pgvectorscale, Cohere Embed v4, BGE-M3, Docling | L | None (parallel with #2-#6) | Non-negotiable for financial documents; 26-31% NDCG improvement |
| 8 | MCP gateway with defensive engineering | OAuth, container isolation, Redis rate limiter, circuit breakers | M | None (parallel) | 66% of servers have security findings; gateway is prerequisite |
| 9 | Evaluator calibration against Keystone deliverables | Promptfoo, CALM diagnostic | M | #3 | 0.80+ Spearman from 100-200 expert-scored samples; binary gate |
| 10 | End-to-end pipeline test | All above | M | #1-#9 | Existence proof; measure quality on 10-dim rubric |
| 11 | Citation data model | PROV-AGENT entity model, chunk metadata schema | S | None (design in parallel) | Must be designed Phase 1 even if only rendered as Markdown |

### Phase 2: Quality Compounding (Build Next)

| # | Component | Tools | Complexity | Dependencies | Rationale |
|---|---|---|---|---|---|
| 12 | Observation Library (expanded Rejection Library) | Cognee, OpenSpace skill evolution, ECC instinct pipeline | L | Phase 1 complete | Captures successes and failures; instinct-to-skill promotion |
| 13 | GEPA/DSPy prompt optimization | GEPA via DSPy/MLflow, MCPAdapter | M | #3, #12 | Automate prompt evolution against L4 quality scores |
| 14 | Trajectory storage | Engram MCP, trajectory-store/ structure | M | #12 | Institutional memory across engagements |
| 15 | Client/Industry calibration profiles | Cognee per-client nodes, 4-lever profiles | M | #12, #14 | Comprehension flywheel; engagement-specific quality |
| 16 | Causal inference agent | DoWhy, CausalAgent patterns | L | Phase 1 L2 designed for causal inputs | White-space capability; no competitor offers this |
| 17 | Design token system for deliverables | Vizro, 3-tier CSS tokens, CI audit | M | None | Visual consistency without model discretion |
| 18 | Saturation-breaking mechanisms | Adversarial probing, domain expansion, human review pipeline | M | #12 | Prevents self-improvement plateau after 2-3 rounds |
| 19 | Anti-slop enforcement | Antislop Sampler patterns, slop detection rubric dimension | S | #3 | Structural enforcement via Evaluator + redraft subagent |

### Phase 3: Extend and Evolve (Defer But Design For)

| # | Component | Tools | Complexity | Dependencies | Rationale |
|---|---|---|---|---|---|
| 20 | Darwinian prompt evolution | ATLAS patterns, population-based variants | L | #12, #13 | Requires 5-10 completed projects for meaningful data |
| 21 | PPTX generation | Skills API, PPTAgent/DeepPresenter, python-pptx | L | #17 | Full consulting deliverable generation |
| 22 | Excel model generation | Skills API, Typst for PDF | M | #17 | Financial models, scenario analyses |
| 23 | Interactive dashboards | Streamlit, Vizro-MCP | M | #17 | 21% more engagement, 41% higher completion |
| 24 | Satellite imagery + earnings call audio | SpaceKnow API, FinVoc2Vec | L | L1 architecture accommodates | Design retrieval layer to accept in Phase 1 |
| 25 | Temporal knowledge graphs | Graphiti/Neo4j patterns | L | #14 | Living competitive landscapes |
| 26 | HyperAgents metacognitive evolution | Meta patterns | XL | #12, #13, #20 | The improvement process itself improves |
| 27 | Scheduled research pipelines | Cron + pipeline templates | M | Phase 1-2 stable | Ongoing market intelligence as a service |

---

## 6. Updated 10-Dimension Rubric (Recommended)

| Dimension | Weight | Type | What It Measures |
|---|---|---|---|
| Analytical Depth | 12% | Expert-checkable | Non-obvious conclusions; judgment ratio (analysis vs. aggregation) |
| Source Quality | 10% | Machine-checkable | Admiralty Code two-axis scoring; signal depth; triangulation |
| Quantitative Rigor | 15% | Machine-checkable | Data support; uncertainty quantification; false precision penalty |
| Narrative Coherence | 10% | Expert-checkable | Clear story; cross-finding synthesis; Pyramid Principle compliance |
| Completeness | 8% | Machine-checkable | Absence detection + deletion test (overload penalty) |
| Actionability | 15% | Expert-checkable | Monday-morning specificity; trendslop detection; role segmentation |
| Intent Alignment | 15% | Judgment-dependent | Decision context served; 5-level decision-usefulness rubric (B2) |
| Intellectual Honesty | 8% | Judgment-dependent | Limitations named; contested claims framed; ICD 203 uncertainty |
| **Evaluative Surprise** | **5%** | **Judgment-dependent** | **At least one insight a competent analyst wouldn't produce** |
| **Calibrated Confidence** | **5%** | **Judgment-dependent** | **ICD 203 7-term probability language; appropriate certainty levels** |

Pre-rubric gates (not scored, binary pass/fail):
- Citation existence verification (any fabrication = full rejection)
- Format compliance (anti-slop: directly presentable without cleanup)

Post-rubric overlay:
- Holistic gestalt adjustment (+-5-10% for emergent quality signals)
- Observation Library negative-space scan (anti-pattern check)

---

*This synthesis represents the combined findings of 16 deep research reports analyzed across 4 parallel threads. Every recommendation traces to specific report findings with documented evidence quality. The plan update and changelog follow.*
