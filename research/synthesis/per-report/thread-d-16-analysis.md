# Report 16: D3 — 10x Ideas — What Would Make Keystone Extraordinary

## Source
`research/reports/batch-1/Deep_Research_Report_From_Prompt_16.md`

---

## Top Findings

### Finding 1: ICD 203 tradecraft standards and the Analysis of Competing Hypotheses matrix are directly implementable as L1.5 structural backbone — not aspirational guidance
**Pipeline layer affected:** L1.5 (Deliberation)
**Evidence quality:** Verified (ICD 203 retrieved from intelligence.gov primary source; ACH software implementations confirmed)

The IC's ICD 203 defines nine analytical tradecraft standards with specific implementation guidance: source credibility assessment, calibrated seven-level probability language ("likely 55-80%", "almost certain 95-99%"), explicit assumption identification, and alternative hypothesis evaluation. These are not conceptual guidelines — they specify exactly what "good analysis" means at the output level. The Analysis of Competing Hypotheses (ACH) matrix (hypotheses x evidence, scored for consistency/inconsistency) is the natural data structure for Keystone's confidence maps. Three software implementations exist: PARC ACH 2.0 (ONR-funded), Open Source ACH (GitHub), and Globalytica TH!NK Suite (built by Heuer and Pherson). The ACH "group matrix" feature — which highlights cells where analysts disagree most — produces exactly the confidence map L1.5 should output.

**What it means for the build:** The CAPSTONE-PLAN-v2.md describes a "Confidence Map" as L1.5 output but does not specify its structure. This report provides the specification: an ACH matrix where rows are hypotheses, columns are evidence items, cells contain consistency scores (+, 0, -), and disagreements between agents are highlighted. ICD 203's nine standards should be implemented as Layer 4 validation gates applied to every deliverable, not just as rubric inspiration. The intelligence community spent decades developing this — implementing it costs weeks, not months.

---

### Finding 2: Five-layer citation enforcement makes "cite-or-it-dies" structurally enforceable, not aspirational
**Pipeline layer affected:** L1 (Research Agents), L2 (Content Structuring), L4 (Evaluator)
**Evidence quality:** Verified (multiple peer-reviewed sources: ACL 2024, SIGIR 2025, EMNLP 2023)

The report provides a complete five-layer architecture:
1. Retrieval-constrained generation: model receives only retrieved passages (prevents most hallucinations at source)
2. Structured output with mandatory citation fields: OpenAI structured output mode achieves 100% JSON schema compliance via logit masking; Outlines/XGrammar for self-hosted models
3. Post-generation verification agent (CoVe, ACL 2024): decompose into atomic claims, generate verification questions, answer independently, regenerate only from verified facts
4. Hard gate rejection: every sentence without a citation marker is automatically stripped (regex + NLI validation)
5. Provenance graph (DAG): every claim traces to primary source through agent boundaries

STORM achieves 84.8% citation recall / 85.2% citation precision using the reference-pool constraint: gather sources before writing, writing agent can only cite from pre-collected set. ALCE benchmark (Princeton, EMNLP 2023) provides NLI-based citation evaluation metrics for continuous monitoring.

**What it means for the build:** This converts one of the plan's most important design principles into a concrete engineering specification. No single mechanism is sufficient — all five layers are required. The plan currently describes the "cite-or-it-dies" policy as a structural enforcement goal but does not specify the enforcement mechanism. This report specifies it. The L1→L2 handoff should require a reference pool gathered before synthesis begins (STORM pattern).

---

### Finding 3: Causal inference is production-ready and transforms consulting research from correlation-reporting to mechanism-identification
**Pipeline layer affected:** L2 (Content Structuring), L3 (Generation)
**Evidence quality:** Verified (ACM IUI 2026 paper; ACL 2025 Findings peer-reviewed)

CausalAgent (IUI '26, March 2026) demonstrates end-to-end causal inference using LangGraph, RAG, and MCP — the exact technology stack Keystone already uses. MATMCD (ACL 2025, NEC Labs America) validates multi-agent causal inference: up to 66.7% reduction in causal inference errors and 83.3% improvement in root cause accuracy. Microsoft's DoWhy library (1M+ installs) provides four-step pipeline: Model → Identify → Estimate → Refute. The refutation step (placebo treatments, random common cause tests, data subset validation) is the critical structural check that prevents spurious causal claims. Nobel laureate Guido Imbens has endorsed the approach as "on the verge of becoming useful collaborators."

The consulting application: every market sizing and competitive analysis currently reports correlations ("this company grew 40% when market grew 15%"). With DoWhy integration, the system can identify whether the relationship is causal, identify confounders, and produce intervention recommendations (not just "X happened when Y happened" but "increasing X causes Y to increase by Z, holding confounders constant").

**What it means for the build:** This is a genuine capability expansion that makes Keystone's output substantively different from all existing consulting research tools. None of the major platforms (AlphaSense, Hebbia, even McKinsey's Lilli) perform causal inference. This is a direct implementation of the CAPSTONE-PLAN-v2.md Expansion Thesis: "What research would you do if cost dropped 10x?" Causal analysis at scale is something that was previously prohibitively expensive to include in consulting deliverables.

---

### Finding 4: Satellite imagery and earnings call audio analysis are production-ready multimodal sources for competitive intelligence
**Pipeline layer affected:** L1 (Research Agents)
**Evidence quality:** Verified (SpaceKnow commercial API, UC Berkeley academic research, FinVoc2Vec academic validation)

Satellite imagery competitive intelligence scores 4/5 for production readiness: SpaceKnow API at $15-30K/year, Bloomberg Terminal integration, documented use cases including retail revenue prediction from parking lot counts and China manufacturing index reconstruction from infrared imagery. Academic research confirms trading strategies based on satellite-derived parking lot data generate significant returns. Earnings call audio analysis scores 3/5: Markets EQ (formerly Helios Life Enterprises) claims 20-25% gains in Sharpe ratios, domain-adapted models (FinVoc2Vec) provide text-tone discrepancy detection. The highest-alpha signal: vocal delivery quality deteriorates measurably when executives deliver negative news, and stock markets react in real time. Text-tone discrepancy (positive words, negative vocal affect) is detectable and currently underutilized.

For documents (PPTX, XLSX, DOCX), a critical finding: extracting XML structure directly and feeding to text LLMs outperforms VLM-based visual analysis for editable documents.

**What it means for the build:** These are concrete L1 data sources not currently specified in CAPSTONE-PLAN-v2.md's retrieval layer. Adding satellite imagery as an L1 source for physical asset analysis and earnings call audio analysis for executive sentiment adds analytical dimensions that text-only research cannot produce. The XML extraction finding has immediate practical implications: the system should never screenshot a PPTX to analyze it; it should extract the XML and process it as text.

---

### Finding 5: GEPA + the autoresearch ratchet make the META-layer immediately implementable, not aspirational
**Pipeline layer affected:** META (Self-Improvement Loop)
**Evidence quality:** Verified (GEPA is ICLR 2026 Oral; autoresearch reproduced by multiple parties including Shopify CEO)

GEPA (ICLR 2026 Oral) is already integrated into MLflow's `mlflow.genai.optimize_prompts()` API with adapters for DSPy programs, RAG systems, and MCP tools. It outperforms MIPROv2 by 10%+ while using 35x fewer rollouts. AgentHER (Hindsight Experience Replay) converts failed agent trajectories into high-quality training data through failure classification, LLM-guided prompt relabeling, and multi-judge verification; this reduces label noise from 5.9% to 2.3%. The autoresearch ratchet loop (Karpathy, 42K+ stars, reproduced): generate → evaluate → keep if improvement → revert if not → iterate. Applied to consulting research: build composite quality score (data coverage + model coherence + sensitivity completeness + source diversity + computational reproducibility) → run ratchet → keep improvements → revert regressions.

**What it means for the build:** The plan describes the META-layer self-improvement loop as a Phase 2-3 deliverable. This report establishes that the core mechanism (GEPA + autoresearch ratchet) is available immediately and production-tested. GEPA through DSPy/MLflow means every agent's prompt can be automatically optimized against Layer 4 quality scores from the first project. The Rejection Library (Phase 2 in the plan) should be bootstrapped immediately with AgentHER-style trajectory logging from Phase 1 work.

---

## Tool/Framework Verdicts

### DoWhy (Microsoft, 1M+ installs)
- Four-step causal inference pipeline: Model → Identify → Estimate → Refute; placebo testing and common cause tests in refutation step
- **Verdict: INTEGRATE (Phase 2)**
- Use as the causal inference computation engine inside a Layer 2 Causal Analysis Agent; the refutation step is the structural quality gate that prevents spurious causal claims.

### CausalAgent (DMIRLAB-Group, GitHub: DMIRLAB-Group/CausalAgent)
- LangGraph + RAG + MCP architecture for end-to-end causal inference; PC/FCI/LiNGAM algorithm selection via MCP
- **Verdict: LEARN**
- The MCP pattern for decoupling LLM reasoning from causal algorithm execution is the correct integration architecture; study and replicate rather than adopting the full system.

### MATMCD (NEC Labs America, ACL 2025)
- Multi-agent causal coordination: Data Augmentation Agent + Causal Constraint Agent; 66.7% reduction in causal errors
- **Verdict: LEARN**
- The multi-agent causal debate pattern (opposing causal hypotheses + judge agent) is the correct design for integrating causal reasoning into L1.5 Deliberation.

### GEPA + DSPy (ICLR 2026 Oral; integrated into DSPy v3.1.3 and MLflow)
- Prompt evolution via natural language reflection; 93% accuracy on MATH; 35x fewer rollouts than GRPO; MLflow integration
- **Verdict: INTEGRATE (immediate)**
- Integrate GEPA through MLflow to optimize all soul prompts against Layer 4 quality scores from the first project; this is the META-layer's prompt evolution mechanism.

### AgentHER (Hindsight Experience Replay)
- Converts failed trajectories to training data; failure classification + LLM-guided relabeling + multi-judge verification; reduces label noise to 2.3%
- **Verdict: INTEGRATE (Phase 2)**
- Use as the mechanism for converting Rejection Library entries into prompt evolution training data; builds directly on the Phase 1 Rejection Library infrastructure.

### E2B sandboxing (Firecracker microVM)
- 80ms startup, full Linux environment, internet access; ~$0.05/hour; 50% of Fortune 500 use; Manus runs 27 tools inside E2B
- **Verdict: INTEGRATE**
- Use for all code execution agents (market sizing models, Monte Carlo simulations, causal inference scripts); cost negligible, isolation complete.

### SpaceKnow satellite imagery API
- $15-30K/year, Bloomberg Terminal integration, parking lot counts, factory activity monitoring, manufacturing indices
- **Verdict: INTEGRATE (Phase 2)**
- Production-ready, priced for enterprise, enables competitive intelligence dimensions no text-based research can provide; design L1 data source architecture to accommodate in Phase 1.

### PARC ACH 2.0 / Open Source ACH (GitHub)
- Analysis of Competing Hypotheses matrix implementation with group disagreement highlighting; ONR-funded (PARC), open-source (GitHub version)
- **Verdict: LEARN (Open Source ACH) / SKIP (Globalytica TH!NK Suite)**
- Build custom ACH matrix implementation borrowing Open Source ACH's disagreement detection; Globalytica is commercial and patterns are extractable from published methodology.

### ICD 203 analytical standards (intelligence.gov)
- Nine analytical tradecraft standards with specific probability language requirements (seven-level calibrated scale)
- **Verdict: INTEGRATE**
- Implement as nine Layer 4 validation gates applied to every deliverable; this is a free, primary-source methodology that encodes decades of analytical best practices.

### Temporal knowledge graph (Graphiti / Neo4j / SurrealDB)
- Every fact has validity window + provenance tracing; enables living competitive landscapes that update when facts change
- **Verdict: LEARN (Phase 3)**
- Design the persistence layer to support temporal knowledge graphs from Phase 1; implement in Phase 3 when the core pipeline is stable.

### Hebbia Matrix + ISD
- Iterative Source Decomposition achieving 92% accuracy vs. 68% standard RAG; 30-40 hours saved per deal; $700M valuation
- **Verdict: LEARN**
- ISD's method for preserving document context across overlapping chunks is directly applicable to Keystone's L1 retrieval design; study and replicate rather than licensing.

### AlphaSense Smart Synonyms
- Domain-specific semantic expansion graphs from speech pattern analysis across millions of documents; $500M+ ARR, 88% of S&P 100
- **Verdict: LEARN**
- Build domain-specific semantic expansion for consulting research using embedding-based synonym detection trained on industry corpora; the commercial product is out of budget range, the pattern is replicable.

### Contify intelligence platform
- 1M+ vetted sources, 5-7 day setup, AI tagging, deduplication, source credibility checking, 117+ languages
- **Verdict: INTEGRATE as data source (Phase 2)**
- Use as a curated intelligence feed for competitive monitoring; do not build the underlying monitoring infrastructure in Phase 1.

### HyperAgents (Meta AI, arXiv:2603.19461)
- Agent rewrites both task-solving code and self-improvement mechanism; paper review 0.0 to 0.710; spontaneously develops persistent memory
- **Verdict: LEARN (Phase 3)**
- The most ambitious direction for META-layer evolution; requires robust rollback mechanisms and human oversight gates before implementation; design the META layer's architecture to support this extensibility.

### SocraSynth adversarial debate protocol (Stanford)
- Multi-LLM structured debate with adversarial linguistic calibration; three phases: opening positions → cross-examination → synthesis
- **Verdict: LEARN**
- Steal the three-phase structure for L1.5 Deliberation design; the adversarial calibration mechanism addresses the conformity bias problem documented in 2025 research.

### Brightwave Blueprints
- Pre-populated analytical frameworks that encode firm's analytical process as reusable templates running continuously
- **Verdict: LEARN**
- This is the vision for Keystone's skill modules (Section 10 of CAPSTONE-PLAN-v2.md); Brightwave demonstrates the product concept, but the implementation should be custom.

### ChatGPT Code Interpreter
- Session-based code execution
- **Verdict: SKIP**
- Sandbox limitations, no API connectivity, session-based; E2B is superior in every dimension.

### AlphaEvolve (Google DeepMind)
- Evolutionary improvement of 50-year-old algorithms; recovered 0.7% of Google's worldwide compute
- **Verdict: SKIP (direct use) / LEARN (meta-evolution concept)**
- Requires Google-scale compute; the concept of evolving not just solutions but strategies for finding solutions is the correct long-term direction for META-layer design.

### GLG / AlphaSights expert network APIs
- 1.2M+ professional networks; trust-based privileged insights unavailable through data sources
- **Verdict: INTEGRATE as data source (design for Phase 1, implement Phase 2)**
- Expert interview augmentation is one of the human capabilities that Keystone cannot replace; integrate as an input source where Layer 0 generates interview guides and Layer 3 analyzes transcripts.

---

## Contradictions with CAPSTONE-PLAN-v2.md

### Contradiction 1: The plan's "cite-or-it-dies" policy is a prompt instruction; this report shows it requires five layers of structural enforcement

**What the plan says:** Section 8.2 lists "Source citation on every claim" as Structural enforcement with "Tool output format requires citations as mandatory field; uncited claims literally cannot be produced." This implies structural enforcement is achievable through tool design alone.

**What the evidence shows:** No single mechanism suffices. STORM achieves 84.8% citation recall (not 100%) with the reference-pool constraint alone. The report documents a five-layer defense: retrieval-constraint, structured output, post-generation verification, hard gate rejection, and provenance graph. OpenAI's structured output mode achieves 100% schema compliance but cannot prevent hallucinated URLs — it guarantees the field exists, not that the content is valid.

**Which to follow:** The five-layer architecture. The plan's single-mechanism claim is overstated. Structured output enforces the presence of citation fields; it cannot enforce citation validity. Add the post-generation verification agent (Layer 3 of the five-layer stack) and provenance DAG as architectural requirements, not optional improvements.

---

### Contradiction 2: The plan does not include causal inference as a research capability; this report shows it is production-ready and transformatively valuable

**What the plan says:** The research and analysis engine is described as gathering data, synthesizing findings, and producing multi-perspective analysis. Nowhere does the plan include causal analysis — identifying whether relationships are causal or correlational, identifying confounders, or producing intervention recommendations.

**What the evidence shows:** Causal inference is now production-ready through DoWhy (1M+ installs) and CausalAgent (ACM IUI 2026). MATMCD shows 66.7% reduction in causal errors through multi-agent coordination. No existing consulting AI tool (including Lilli, Hebbia, AlphaSense) currently provides causal analysis. This is a white-space capability.

**Which to follow:** Add causal inference as a Phase 2 capability. In Phase 1, design the L2 Content Structuring layer to accept causal analysis outputs as a first-class input type (even if the causal agent doesn't exist yet). This prevents the need for pipeline redesign when causal analysis is added.

---

### Contradiction 3: The plan positions Deliberation as multi-perspective role-based debate; this report and D2 academic evidence show the effective design is multi-method, not multi-role

**What the plan says:** L1.5 uses "multi-perspective debate" with different stakeholder perspectives (bull, bear, consensus). The value comes from different viewpoints representing different interests.

**What the evidence shows (confirmed by both D3 and D2):** Methodological diversity (different analytical methods: ACH matrix analysis, causal inference, quantitative modeling, adversarial critique) outperforms persona diversity (different roles with the same reasoning method). ICD 203's tradecraft standards provide the specific analytical methods that should be assigned to different agents.

**Which to follow:** The evidence. Redesign L1.5 to assign agents specific analytical methodologies from ICD 203's 66 structured analytic techniques (diagnostics family: ACH, Key Assumptions Check, Deception Detection; reframing family: Devil's Advocacy, Red Team Analysis). The bull/bear framing is a poor substitute for structured analytical methods.

---

### Contradiction 4: The plan treats satellite imagery and earnings call audio as future possibilities; this report shows they are production-ready today

**What the plan says:** Section 9 (Future Layers) discusses "multimodal analysis" as something to design for but not build in Phase 1.

**What the evidence shows:** SpaceKnow API is production-ready at $15-30K/year with Bloomberg integration. Satellite-based competitive intelligence (parking lot analysis, factory activity monitoring) is documented in academic research with validated returns. Earnings call audio analysis has commercial products (Markets EQ) and academic validation (FinVoc2Vec).

**Which to follow:** The report is right that video analysis should be deferred (no turnkey solution), but satellite imagery and earnings call audio should be elevated to Phase 2 deliverables rather than future speculation. Add them to the L1 data source architecture in Phase 1 design so the retrieval layer can accommodate them.

---

## Cross-Report Flags

**Strongly validates D1 and D2 on specification quality:** D3's concrete finding that MAST failure taxonomy shows 37% of failures from specification and system design issues reinforces D1's practitioner evidence. All three thread reports independently arrive at the same conclusion.

**Extends D2 on deliberation design:** D3's specific recommendation to implement ACH matrix + ICD 203 standards as the L1.5 backbone provides the concrete specification that D2's "methodological diversity" finding implies. Together, D2 + D3 fully specify the Deliberation Layer redesign.

**Flags model version discrepancy for synthesis agent:** The D3 report explicitly notes that "GPT-5.4" and "Qwen 3.5" referenced in the original prompt do not exist as released models — the current versions are GPT-5.2 and Qwen3-VL/Qwen3-Omni. Any other reports citing these model names may contain inaccurate capability assessments that should be verified.

**New capability not in any other report:** Causal inference via DoWhy + CausalAgent is specific to D3. No other thread report reviewed here discusses causal inference as an architectural capability. This is a 10x idea that deserves explicit inclusion in the synthesis agent's plan update recommendations.

**Temporal knowledge graphs as cross-thread capability:** D3's recommendation for temporal knowledge graphs (Graphiti/Neo4j/SurrealDB) as the persistence layer for living competitive landscapes is architectural infrastructure that would benefit multiple pipeline layers: L1 (research retrieval), META (trajectory storage), and the future scheduled research pipelines. The synthesis agent should flag this as a cross-cutting infrastructure requirement.
