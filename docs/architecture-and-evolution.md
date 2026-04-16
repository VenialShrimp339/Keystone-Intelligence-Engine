# The Keystone Intelligence Engine

> Status: derived historical/professor narrative. Not current-state truth. Read `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair first. Historical provider/runtime references below are provenance only.

**Architecture, Evolution, and Build Methodology**

*Jack Riddle | IU Kelley School of Business | Econ Consulting Capstone, Prof. Youle | Spring 2026*

---

## 1. What This Is

The Keystone Intelligence Engine is a multi-agent AI system that takes a consulting research question and produces a complete analytical brief. Not a summary of search results. A grounded, multi-perspective analysis with source citations, confidence mapping, and the kind of structured reasoning a senior engagement manager would expect from a three-analyst team working a full week.

The system does this through a six-layer pipeline: a Specification Engine translates vague questions into precise research specifications, parallel research agents fan out across real data sources, a citation processor deduplicates and verifies sources, an independent deliberation stage surfaces consensus and disagreement through structured analysis, an evaluator grades every output through a five-layer quality stack, and a self-improvement loop turns quality outcomes into permanent architectural constraints.

What makes this project worth examining is not the ambition of that description. It is what happened when the ambition met evidence. Every obvious design choice the project started with turned out to be wrong. Not marginally wrong, but structurally wrong, in ways that peer-reviewed research, formal mathematical proofs, and controlled benchmarks could demonstrate. The architecture that exists today was rebuilt from those findings. Its quality properties are guaranteed by structure rather than dependent on prompt compliance.

The system has been built and pressure-tested over six days of active development (April 3-9, 2026), using AI-assisted development methodology that is itself part of the contribution. Ten production components, 825 automated tests, approximately 11,000 lines of production code. Components were individually pressure-tested against real GPT-5.4 calls, then the pipeline was switched to Claude (Opus 4.6 and Sonnet 4.6) and completed its first full end-to-end run. The architecture proved model-agnostic: the provider swap required zero changes to pipeline components, contracts, or evaluation logic.

---

## 2. The Architecture

### 2.1 The Pipeline

The system implements DPVI: Decompose, Parallelize, Verify, Iterate. This is a workflow pattern that was independently discovered by four organizations building production AI systems. The convergent discovery validates the pattern's universality: the only way to get reliable output from language models is to break problems into independent pieces, execute them in isolation, verify every output against explicit criteria, and feed quality signals back into the system.

```mermaid
flowchart LR
    Q[Research Question]
    L0[L0: Specification Engine]
    G1[HITL Gate 1]
    L1[L1: Parallel Research Agents]
    CP[CitationProcessor]
    L15[L1.5: Deliberation]
    G2[HITL Gate 2]
    L4[L4: Evaluator]
    MR[Markdown Renderer]
    OUT[Analytical Brief]

    Q --> L0 --> G1 --> L1 --> CP --> L15 --> G2 --> L4 --> MR --> OUT

    classDef built fill:#d9f2d9,stroke:#2d6a2d,color:#111
    classDef gate fill:#fff0c2,stroke:#8a6d1d,color:#111

    class L0,L1,CP,L15,L4,MR built
    class G1,G2 gate
```

**Layer 0: Specification Engine.** Receives a natural-language research question. Classifies the engagement type. Clarifies intent by identifying what decision the research will inform. Constructs a MECE issue tree using three independent analytical lenses (financial, operational, market). Validates the tree for mutual exclusivity and collective exhaustiveness. Prioritizes branches. Generates a task decomposition with explicit acceptance criteria, tool assignments, and anti-confirmatory framing for every task. Produces a formal RESEARCH.md specification that every downstream component reads and validates against.

**Layer 1: Research Agents.** Three to five agents execute research tasks in strict isolation. No agent can see another agent's intermediate findings. Each agent has 3-5 assigned tools (Exa search, Brave search, EdgarTools, etc.) enforced by the MCP Gateway. Each produces structured findings with source citations as required fields, not optional annotations. The system supports iterative multi-round research with a three-criterion stopping condition.

**CitationProcessor.** A dedicated pipeline stage between research and deliberation. Deduplicates citations across agents using union-find on URLs and DOIs. Scores cross-agent corroboration. Verifies URL liveness. Produces a citation manifest for downstream reasoning.

**Layer 1.5: Deliberation.** Three to five analyst agents independently analyze the research findings using fundamentally different analytical methodologies: Analysis of Competing Hypotheses, quantitative modeling, adversarial critique, and historical analogy. They have zero inter-agent communication. A single aggregator then reads all independent analyses, identifies convergent findings and genuine disagreements, and produces a five-tier confidence map. Low-confidence claims receive a "What Would Have To Be True" challenge. High-confidence claims receive a curmudgeon challenge.

**Layer 4: Evaluator.** A three-layer evaluation stack. Layer 1 runs deterministic checks (fact decomposition, numerical consistency, URL liveness). Layer 2 is a binary citation gate: a fabricated citation means immediate rejection. Layer 3 scores output across ten dimensions using independent prompts, aggregated via geometric mean so that a failure on any dimension cannot be masked by excellence on others. A holistic gestalt overlay adjusts the composite score by up to ten points.

**HITL Gates.** Two mandatory human review points. Gate 1 pauses after the Specification Engine produces the research plan. Gate 2 pauses after Deliberation produces the confidence map. The system runs autonomously between gates.

### 2.2 Key Architectural Principles

**The specification layer is the system.** The model improves automatically. The tools improve automatically. The specification layer improves only through deliberate investment. The .md files that define research methodology, quality criteria, and analytical frameworks are the only irreplaceable component. The same model scores 78% or 42% depending solely on the quality of the specification and harness surrounding it.

**Evaluation is more important than generation.** The Evaluator is the most carefully engineered component, not an afterthought. The generation problem is largely solved by frontier models. The verification problem is what determines whether output can be trusted. Approximately 72% of the system's total token consumption goes to verification, not generation.

**Structure over intent.** Quality enforced through architecture, not through prompt instructions. Instructions drift approximately 40% of the time. The system's critical quality properties are guaranteed structurally: uncited claims literally cannot be produced (citations are required model fields), agents literally cannot access unauthorized tools (the gateway enforces it), and a zero on any evaluation dimension produces a near-zero composite score (geometric mean makes this mathematically inevitable).

**Handoff contracts.** Every pipeline boundary has an explicit contract defining input format, output format, quality threshold, and completion signal. When output quality is low, these contracts allow precise diagnosis: trace backward through the pipeline to identify exactly which handoff degraded the signal.

### 2.3 Implementation Status

| Component | Status | Tests | Pressure Tested |
|-----------|--------|-------|-----------------|
| Specification Engine (L0) | Built | 99 | Yes (real GPT-5.4) |
| Research Agents (L1) | Built | 92 | Yes (real search APIs) |
| CitationProcessor | Built | 28 | Yes |
| Deliberation (L1.5) | Built | 93 | Yes (real GPT-5.4) |
| Evaluator (L4) | Built | 93 | Yes (real GPT-5.4) |
| MCP Gateway | Built | 145 | Yes (real Exa/Brave) |
| HITL Infrastructure | Built | 42 | Unit only |
| Knowledge Accumulation | Built | 45 | Unit only |
| Pipeline Orchestrator | Built | 13 | E2E mock |
| Markdown Renderer | Built | 15 | Unit only |
| LLM Client Factory | Built | 36 | Yes (real API) |

**Total: ~10,850 lines of production code. 825 tests. Zero architectural bugs found during pressure testing.**

---

## 3. How the Design Changed and Why

This is the most important section of this document. The architecture described above is not what the project started with. It is what emerged after systematic research proved that every major assumption in the original design was wrong.

### 3.1 The Original Design

Before any research, the system looked like this:

- **Five fixed research agent types** (Quantitative, Qualitative, Contrarian, Historical Analogy, Internal Document). These were hardcoded roles, not configurable templates.
- **Debate-based deliberation.** Structured multi-perspective debate with bull, bear, contrarian, and consensus personas debating through multiple rounds, concluding with a synthesis round. This is how humans refine ideas, so it seemed obvious.
- **Single LLM judge** evaluating output with an eight-dimension rubric in a single prompt. Standard practice.
- **Shared agent context.** Research agents could access each other's intermediate findings. The assumption was that sharing reduces redundancy and improves quality.
- **No CitationProcessor.** Citations were handled within agent outputs, not as a discrete pipeline stage.
- **No claim-level handoffs.** Raw agent outputs passed between layers as prose, not structured data.
- **Four-tier confidence map.** High, Moderate, Contested, Gaps.
- **No validated cost model.** No formal stopping condition for iterative research.

The plan at this stage was 1,051 lines.

### 3.2 The Theoretical Foundation

The first input to the architecture was a synthesis of 91 articles from Nate Jones's Substack on AI system design, spanning December 2025 through March 2026. This corpus analysis established the project's intellectual foundation.

Five emphasis shifts emerged that would shape every subsequent decision:

1. The Orchestrator was reframed from a coordination layer to a **Specification Engine**. The bottleneck in AI systems is not capability but specification quality. The same model produces dramatically different results depending on how precisely the task is defined. "Precision machinery executing imprecise blueprints produces precisely wrong outputs."

2. The Evaluator was elevated to **the most important component**, more important than any generator. "The generation problem is solved; the verification problem is crushing us."

3. Quality enforcement was reconceived around **structure over intent**. Language-based instructions to AI agents drift approximately 40% of the time. Quality gates must be architectural, not behavioral.

4. The harness thesis was quantified: the same model scores 78% versus 42% depending on the quality of the harness surrounding it. A separate datapoint showed improvement from 17% to 92% with harness engineering alone.

5. A Rejection Library concept was introduced, later expanded to the Observation Library: every quality outcome, whether success or failure, becomes a structured entry that feeds forward into future engagements.

These were not minor refinements. They changed what the system was *for*. The project went from "build a multi-agent research tool" to "build the specification and evaluation infrastructure that makes multi-agent research trustworthy."

### 3.3 The Five Reversals

The theoretical foundation established *what to prioritize* (specification quality, evaluation rigor, structural enforcement) but did not yet reveal *what was wrong* with the specific design choices. That came from sixteen deep research reports commissioned across four thematic threads: the technical landscape, the consulting quality lens, the pipeline stages, and the research frontier. These reports, analyzed by parallel Opus-tier agents and synthesized into a unified set of findings, produced seventeen specific changes to the architecture plan. Five of those changes were outright reversals of the original design. Each reversal was driven by specific, peer-reviewed evidence.

#### Reversal 1: Deliberation

**The assumption:** Debate is how groups arrive at truth. If individual agents are imperfect, having them debate should surface errors and converge toward better answers.

**What killed it:** A NeurIPS 2025 Spotlight paper proved, via formal mathematical analysis using a Dirichlet-Compound-Multinomial model, that multi-agent debate forms a *martingale*. The expected value of the group's belief after round N+1 equals its expected value after round N. Additional rounds of debate do not improve the answer in expectation. They converge toward consensus, which is not the same thing as convergence toward truth.

The numbers were stark. Simple majority voting (0.7691 accuracy) outperformed the best debate variant (0.7377). Wu et al. found that majority pressure suppresses independent correction below 5%. Google DeepMind tested 180 configurations and found that unstructured multi-agent networks amplify errors 17.2 times. A separate study at ICLR 2025 showed that methodological diversity consistently outperforms persona diversity: giving agents different analytical *methods* produces better results than giving them different *personalities*.

**What replaced it:** Two-phase deliberation. Phase 1: three to five analyst agents independently apply fundamentally different analytical methodologies (ACH, quantitative modeling, adversarial analysis, historical analogy) with zero inter-agent communication. Agent identifiers are stripped from findings to prevent anchoring bias. Phase 2: a single aggregator reads all independent analyses simultaneously, identifies convergent findings, genuine disagreements, and methodological blind spots. One curmudgeon challenge per high-confidence finding. No iterative debate rounds.

**Why this matters beyond the project:** The mathematical proof that debate is a martingale is counter-intuitive. Debate *feels* like it should converge on truth. What it actually converges on is consensus, and consensus is easily achieved by agents herding toward the majority view rather than by agents independently verifying claims. The insight is that *independent observations* are more valuable than *coordinated ones* precisely because they provide genuine signal about convergence versus divergence.

#### Reversal 2: Agent Communication

**The assumption:** Research agents should share their intermediate findings. Sharing reduces redundant work and lets agents build on each other's discoveries.

**What killed it:** The AgentLeak benchmark, published in February 2026 from an analysis of 4,979 traces, measured 68.8% inter-agent data leakage in standard multi-agent frameworks. Of that leakage, 46.7% originated from shared memory. No framework provided mechanisms to intercept inter-agent messages. Separate findings from the Nate Jones corpus analysis documented that cross-contamination between research agents causes confirmation bias: agents seeing each other's work herd toward consensus rather than independently verifying claims.

**What replaced it:** Strict process-level isolation. Each research agent operates in its own working directory with advisory file locks. Research agents cannot access each other's intermediate findings under any circumstances. All convergence is deferred to the Deliberation stage (L1.5), where it happens under controlled, transparent conditions. Agent identifiers are stripped before deliberation to prevent anchoring. Each agent receives 3-5 domain-specific tools, not the full suite.

**Why this matters:** Isolation is not a limitation. It is a feature. When agents work independently, convergence in their findings is *evidence* that the claim is well-supported. When agents share findings, convergence is *expected* and proves nothing.

#### Reversal 3: The Evaluator

**The assumption:** A single LLM judge with a well-designed rubric can score output quality reliably.

**What killed it:** SOS-Bench, an ICLR 2025 study with 152,000 data points, proved that holistic LLM judging systematically rewards style over substance. Sarcasm causes a 96% scoring loss. Factual errors cause only a 13% scoring loss. The implication is that a single LLM judge penalizes *tone* seven times more harshly than *factual accuracy*. A separate study identified the causal mechanism: models score their own outputs higher due to lower perplexity, a phenomenon called "Play Favorites." Single LLM judge agreement with domain experts plateaus at 60-68%.

**What replaced it:** A five-layer evaluation stack. Layer 1: deterministic verification (FActScore fact decomposition, numerical consistency checks, URL liveness). Layer 2: citation binary gate, where a fabricated citation means immediate rejection, full stop. Layer 3: ten independent dimension-specific prompts scored individually and aggregated via geometric mean. Layer 4 (Phase 2): process trajectory evaluation. Layer 5 (Phase 2): cross-model ensemble with minority veto. The generating model is prohibited from being the primary evaluating model.

**Why the geometric mean matters:** Under a weighted sum, a high Narrative Coherence score can mask a failing Intellectual Honesty score. Under geometric mean, a score of 1/100 on any dimension drags the composite near zero. This changes the evaluation incentive from "maximize your strengths" to "eliminate your weaknesses." Three independent evaluation frameworks (Stanford HELM, MQM, AdaRubric) converged on geometric mean for exactly this reason.

#### Reversal 4: How Findings Are Aggregated

**The assumption:** After deliberation, findings from multiple analysts should be synthesized into a unified narrative. Synthesis is sophisticated and produces a coherent output.

**What killed it:** Research in Batch 2 found that judge-based claim selection achieves an 81% win rate. Synthesis-based blending scores 51.2%, near chance. Synthesis "introduces incoherence, conflicting perspectives, and diluted arguments."

**What replaced it:** Claim-level selection. The aggregator evaluates competing claims and selects the best-supported one rather than blending them. Each claim carries source references, confidence score, corroboration count, and a provenance chain. Selection preserves the strongest arguments intact rather than averaging them into mush.

#### Reversal 5: Rubric Aggregation

**The assumption:** Weighted sum of dimension scores. Standard practice across evaluation frameworks.

**What killed it:** Three independent frameworks (Stanford HELM, MQM, AdaRubric) use geometric mean specifically because weighted sum allows dimension compensation. As described above, under weighted sum, excellence in easy dimensions can mask failure in hard ones.

**What replaced it:** Geometric mean with weight normalization, so that a zero on any dimension produces an overall zero. The rubric was also expanded from eight to ten dimensions by adding Evaluative Surprise (rewarding non-obvious insights) and Calibrated Confidence (rewarding honest uncertainty), and weights were rebalanced away from dimensions where LLMs naturally excel (coherent prose, coverage) toward dimensions where they underperform (analytical novelty, quantitative rigor, actionable insight).

### 3.4 Jack's Directives: The Consulting Lens

The five reversals came from research. But research alone could not have produced the full architecture. Fourteen directives from the project owner, Jack Riddle, injected consulting domain expertise that no amount of literature review could provide. These directives shaped the system's relationship to the real world of consulting practice.

**The Rigidity Problem (Directive 1).** The original five fixed agent types work for broad market research but fail for specialized tasks like "deep-dive a specific public company for an M&A pitch." Predefined types should be templates or defaults, not constraints. When they fit, use them. When they do not, the Specification Engine generates custom configurations on the fly. Think of it like McKinsey casing: you do not want memorized frameworks, you want someone who can take ambiguity, structure it, and prioritize.

**MECE Issue Tree Decomposition (Directive 2).** Before task decomposition, the Specification Engine constructs a MECE (Mutually Exclusive, Collectively Exhaustive) issue tree. Multiple agents independently build trees using different consulting lenses, then a synthesis step selects or merges the best decomposition. This is how top-tier consultants structure novel problems. The issue tree is the system's primary tool for handling ambiguity.

**The FITFO Standard (Directive 6).** "The system should be as competent as a senior McKinsey consultant. When it encounters something it has never seen before, it should be able to figure it out without predefined skills or templates." This became the design litmus test for the Specification Engine: can the system handle a novel engagement type without a pre-existing skill file?

**Configurable Pipeline Depth (Directive 11).** A simple factual question should not spin up MECE decomposition, five research agents, and five rounds of iterative research. Three profiles (Light, Standard, Deep) allow the system to scale its effort to the complexity of the question. The engagement classifier recommends a profile; the user can override. This resolves the concern that the system's maximum capability is also its minimum cost.

**Build Philosophy (Directive 5).** Build the architecture correctly, with the right interfaces, right abstractions, and right data flow, but stage feature depth. The pipeline should have all layers wired up with correct handoff contracts, but individual layers can start simple and get more sophisticated over time. This is not building a "mini MVP" that shortcuts the architecture. It is building the real architecture at reduced feature depth.

### 3.5 Batch 2: Resolving the Open Questions

After the initial seventeen changes, eight open questions remained, ranging from the mechanical specification of the iterative research loop to the retrieval architecture to the rubric aggregation method. A second round of ten targeted deep research reports was commissioned, each addressing a specific open question.

The results were consistent with Batch 1: no contradictions between the two rounds of research. Batch 2 sharpened and extended Batch 1 findings in every case. Key resolutions:

- **The iterative research loop** was fully specified with a three-criterion stopping condition (hard round cap, quality gate, novelty exhaustion), a scope-change detection protocol, and between-round context continuity via a structured scratchpad.
- **The retrieval architecture** was split into two components: source discovery (vector search for finding new sources) and knowledge accumulation (compiled markdown wikis for organizing what has been found). This was informed by Andrej Karpathy's pattern of using LLMs to compile raw data into structured wikis, and validated by research showing file-based memory (74% accuracy) outperforms vector-based memory systems (68.5%) for agent knowledge.
- **Six apparent contradictions** between the two research batches were resolved through structured analysis, including filesystem vs. PostgreSQL storage for the Observation Library (filesystem for Phase 1, database for Phase 2), and the role of the Agent SDK (removed from primary stack due to vendor lock-in concerns).

After all 48 changes from Batch 2 were applied and independently verified, the architecture plan grew from 1,051 to 1,294 lines. Every change was tagged with its source, evidence, and confidence level.

### 3.6 Contact with Reality

The architecture survived two stress tests, one planned and one unplanned.

**Provider switchover (Claude to GPT-5.4 and back).** The system was built around Claude, then switched to OpenAI GPT-5.4 to test with a different provider. The swap required zero architectural changes: only configuration-level modifications to model names and API keys. No contracts changed. No handoff formats changed. No evaluation criteria changed. Later, the pipeline was switched back to Claude (Opus 4.6 for judgment, Sonnet 4.6 for throughput) for production use via Claude Code's headless mode (`claude -p`), running on the Max subscription at zero API cost. Both switches validated model-agnosticism in practice, not just theory.

**Component pressure testing.** Four parallel sessions tested each major component with real LLM calls and real Exa/Brave search APIs. Eight bugs were found. All eight were implementation-level: parser robustness when the LLM wraps JSON in markdown fences, a missing HTTP User-Agent header that caused Wikipedia and SEC.gov to reject URL verification requests, and tool name validation where the model hallucinated tool names not in the registry.

**Full pipeline end-to-end.** The complete pipeline (L0 through Markdown Renderer) ran successfully. The Specification Engine generated an issue tree and research tasks. Research agents executed across real search APIs. The CitationProcessor deduplicated and verified sources. Deliberation produced a five-tier confidence map. The Evaluator scored output across all dimensions.

Zero architectural bugs across all three stress tests. The abstractions held. The contracts worked. The structural enforcement correctly rejected unsubstantiated claims when search APIs returned empty results. The system works not because the prompts are perfect, but because the architecture makes failure visible and recoverable.

### 3.7 The Narrative Arc

To summarize the story so far: the project started with obvious design choices, and every one was wrong.

The architecture was rebuilt around counter-intuitive findings: isolation over collaboration, independent analysis over debate, structural enforcement over prompt compliance, claim-level selection over synthesis, geometric mean over weighted sum. Fourteen directives from the project owner injected the consulting domain expertise that research alone could not provide. A second round of targeted research resolved the remaining open questions. A model provider replacement validated model-agnosticism. Pressure testing validated the abstractions.

The result is a system whose quality properties are architecturally guaranteed rather than hoped for. Every major design decision traces to a specific research report, a formal proof, a benchmark, a production incident, or a consulting practitioner's domain expertise. The architecture emerged from systematic engagement with evidence rather than from first principles alone. And the entire evolution, from initial concept through 65 specific plan changes to a pressure-tested MVP, took six days of active development.

---

## 4. Inside Each Component

### 4.1 The Specification Engine (Layer 0)

The Specification Engine is where all the value lives. Before "what should we research?" comes "what decision does the client need to make?" and "what evidence would change their mind?" No agents spawn until the specification meets a quality threshold.

**The pipeline.** The engine implements an eight-step process (of a designed ten-step pipeline, with two deferred to Phase 2):

1. **Engagement Classification.** Five-signal analysis classifies the question into one of five types (sizing, diagnostic, evaluative, exploratory, strategic) and recommends a pipeline profile (Light, Standard, or Deep).

2. **Intent Clarification.** Decision-First Chain of Thought: what decision will this research inform? What constraints are unstated? What would a surprising finding look like? Produces a Day-1 Hypothesis, a specific testable claim that the research will confirm, refute, or qualify. This prevents the infinite-loop failure mode where research continues without a clear target.

3. **Issue Tree Decomposition.** Three Sonnet-tier agents independently construct MECE issue trees using different consulting lenses: financial, operational, and market/competitive. Each agent sees only the research question and intent clarification, not the other agents' trees. An Opus-tier meta-agent synthesizes the three trees into a single coherent decomposition.

4. **MECE Validation.** Five binary dimensions: mutual exclusivity, collective exhaustiveness, depth appropriateness, actionable specificity, and no false precision. If validation fails, the engine retries decomposition up to twice.

5. **Priority Scoring.** Heuristic scoring in Phase 1 (decision relevance times uncertainty). Full VOI-inspired scoring deferred to Phase 2.

6. **Agent Configuration.** Seven seed templates (quantitative analyst, market researcher, academic researcher, regulatory analyst, generalist, contrarian analyst, historical analyst) in a template registry. Three-tier matching: exact match above 0.85 similarity, interpolated match between 0.5 and 0.85, custom generation below 0.5.

7. **Task Generation.** Research tasks with explicit acceptance criteria, dependencies as a directed acyclic graph validated by Kahn's algorithm, anti-confirmatory framing, and 3-5 assigned tools per task from the MCP Gateway registry.

8. **Human Review Gate.** The pipeline pauses. A human reviewer sees the issue tree, task decomposition, and agent assignments, and can approve, modify, or reject before research begins.

**Why this design:** Most AI systems tell the model what to do (prompt engineering) or what to know (context engineering). The Specification Engine goes further: it encodes what the client actually *needs*, including unstated constraints, the decision the research informs, and what evidence would change their mind. This is the difference between "research the autonomous vehicle sensor market" and "the client is considering a $200M position in Luminar Technologies and needs to know whether LiDAR will be displaced by camera-only systems within five years." The latter produces fundamentally different research because the specification captures intent, not just topic.

**What changed over time:** The original design was a seven-step "coordinator" that decomposed questions and dispatched agents. It became a ten-step Specification Engine after the research synthesis established that specification quality, not model capability, determines output quality. Jack's Directive 2 added the MECE issue tree as the primary analytical tool. Batch 2 research added the Day-1 Hypothesis, the heterogeneous consulting lenses, the five-dimension MECE validation, and the template registry pattern.

**Planned depth enhancement: casing-informed decomposition.** The MECE decomposition currently operates with generic consulting prompts. It works -- the three-lens structure, synthesis, and five-dimension validation produce sound issue trees -- but the prompts themselves do not yet encode the structured problem decomposition methodology that top-tier consulting firms use. Jack's Directive 12 envisioned analyzing McKinsey casing methodology from reference materials (to be placed in `reference/casing-books/`) via an Opus session that would distill the principles into a skill file. That skill file would then inform the decomposition prompts, upgrading them from "generic MECE" to "trained on how senior consultants actually decompose novel problems." The casing materials have not yet been uploaded, so this enhancement remains pending. The architecture supports it without structural changes -- it requires only richer prompt content informed by the casing analysis.

### 4.2 Research Agents (Layer 1)

Research agents are intentionally simple. Their value comes not from individual sophistication but from strict isolation, structural enforcement of citation quality, and the ability to iterate.

**How they work.** Each agent receives a single research task from the Specification Engine. It operates in an isolated working directory. It has access to 3-5 assigned tools (enforced by the MCP Gateway, not by prompt instructions). It queries search APIs, processes results, and produces structured findings where every claim must have at least one citation. If the agent produces a claim without a citation, the finding writer rejects it structurally.

**Multi-round research.** Agents can iterate up to five rounds (three by default). Round 2+ receives a compiled wiki of prior round findings via the Knowledge Accumulation component. The three-criterion stopping condition checks: (1) hard round cap, (2) minimum confidence threshold across all claims (0.8), and (3) semantic novelty exhaustion (new findings no longer differ meaningfully from prior rounds).

**Error recovery.** A two-level recovery system. The inner loop retries transient failures (API timeouts, rate limits) up to three times with exponential backoff. The outer loop falls back through model tiers (Flagship to Standard to Fast) when the model itself produces unparseable output. After all retries are exhausted, the failure is dead-lettered and the agent continues with remaining tasks.

**The isolation principle in practice.** During pressure testing, two parallel research agents investigating the same competitive landscape produced 22 and 21 claims respectively. There was no cross-contamination, no race conditions, and convergence between their findings provided genuine evidence of claim support. When Exa search failed with a ConnectionError, the gateway retried three times, dead-lettered the call, and the agent continued with Brave search. Findings were still produced.

### 4.3 The CitationProcessor

The CitationProcessor exists because citation handling is too important to be an afterthought. It is the system's traceability guarantee.

**What it does.** Takes raw findings from all research agents. Deduplicates citations using union-find on URLs and DOIs (if agent A and agent B cite the same URL, the citations are merged). Detects cross-agent corroboration (if two agents independently found the same source, that is evidence of the source's importance). Verifies URL liveness with concurrent HEAD requests. Produces a citation manifest that downstream components use for reasoning and evaluation.

**Why it exists as a discrete stage.** The original design had no CitationProcessor. It was added based on three independent research findings: Anthropic's own production multi-agent system uses a dedicated CitationAgent (90.2% improvement over a single-agent baseline), IEEE research specified the PROV-AGENT standard for multi-agent citation propagation, and the Deloitte fabricated-citation incidents (AU$440,000 and CA$1.6M in damages) demonstrated that citation quality is not a nice-to-have but a liability issue.

### 4.4 Deliberation (Layer 1.5)

Deliberation is where independent observations become structured knowledge. It is designed around the principle that *disagreement between independent analysts is signal, not noise*.

**Phase 1: Independent Analysis.** Three to five analyst agents each apply a different analytical methodology:

- **ACH (Analysis of Competing Hypotheses):** Evaluates each claim against all hypotheses, looking for diagnostic evidence that differentiates between alternatives.
- **Quantitative:** Focuses on numerical evidence, statistical significance, market sizing, and financial modeling.
- **Adversarial:** Challenges every claim. Identifies the strongest counterargument. Rates confidence conservatively.
- **Historical Analogy:** Finds relevant precedents. Evaluates whether historical patterns apply to the current situation.

These agents have zero inter-agent communication. They cannot see each other's analyses. This is not a limitation but the core design feature: their independence is what makes convergence meaningful.

**Phase 2: Structured Aggregation.** A single aggregator reads all independent analyses simultaneously. For each claim, it identifies which analysts agree and disagree, selects the best-supported position (claim-level selection, not synthesis), and runs consistency checks across selected claims. The output is a five-tier confidence map:

- **High Confidence (>80%):** Convergent findings with a curmudgeon challenge attached.
- **Moderate (60-80%):** Generally supported with sensitivity notes.
- **Weak (50-60%):** Recommended for WWHTB analysis.
- **Contested (<50%):** Genuine disagreement, with steelmanned opposing views.
- **Insufficient Evidence:** Flagged as gaps.

**What changed over time:** The original design used iterative multi-round debate with bull, bear, contrarian, and consensus personas. The NeurIPS martingale proof eliminated debate. DMAD research at ICLR 2025 replaced persona diversity with methodological diversity. Batch 2 research replaced synthesis with claim-level selection.

### 4.5 The Evaluator (Layer 4)

The Evaluator is the most carefully engineered component in the system. It is designed around the conviction that generation quality matters less than evaluation quality, because evaluation is what prevents bad output from reaching the client.

**Layer 1: Deterministic Checks.** Fact decomposition using the FActScore methodology (breaking output into atomic, verifiable claims), numerical consistency verification (catching contradictions like "15% market share" in the text and "12.3%" in a table), and URL liveness checking. These are not LLM-dependent. They catch categories of error that LLMs systematically miss.

**Layer 2: Citation Binary Gate.** Every DOI is verified against doi.org. A fabricated DOI triggers immediate rejection with a score of zero. There is no partial credit for fabricated citations. This layer exists because of the Deloitte incidents: AI-generated fabricated citations that referenced non-existent books, misspelled judge names, and cited incorrect court decisions. The binary gate makes fabrication structurally impossible to hide.

**Layer 3: Ten-Dimension Rubric.** Each dimension is scored independently with its own dedicated prompt. The dimensions, with their weights:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Intent Alignment | 15% | Does the output answer what was actually asked? |
| Intellectual Honesty | 15% | Are limitations, uncertainties, and counterarguments acknowledged? |
| Analytical Depth | 12% | Does the analysis go beyond surface-level observation? |
| Actionability | 10% | Could a consultant act on this Monday morning? |
| Quantitative Rigor | 10% | Are numbers sourced, consistent, and meaningful? |
| Completeness | 8% | Does any missing element change the conclusion? |
| Calibrated Confidence | 6% | Does the language match the evidence strength? |
| Source Quality | 6% | Are sources authoritative, diverse, and current? |
| Narrative Coherence | 5% | Does the analysis tell a coherent story? |
| Evaluative Surprise | 5% | Does the output contain non-obvious insights? |

Two dimensions were added beyond the original eight: Evaluative Surprise (rewarding genuine insight) and Calibrated Confidence (rewarding honest uncertainty expressed in ICD 203 probability language). Weights were deliberately shifted away from dimensions where LLMs naturally excel (Narrative Coherence, Completeness) toward dimensions where they underperform (Quantitative Rigor, Actionability, Analytical Depth). The rubric is designed to catch the specific failure mode where AI produces beautifully written output that contains no original thought.

**Tier gating.** Four dimensions (Intent Alignment, Intellectual Honesty, Completeness, Narrative Coherence) are Tier 1 universal gates. If any Tier 1 dimension falls below its floor threshold, the remaining six dimensions are not scored. This saves seven LLM calls per evaluation for output that fails basic quality criteria.

**Gestalt overlay.** After dimensional scoring, a holistic assessment adjusts the composite score by up to ten points, capturing the 35% of quality judgment that is holistic "taste" rather than dimensional analysis.

**What changed over time:** The original design used a single LLM judge with an eight-dimension rubric. The SOS-Bench findings on style-over-substance bias, the "Play Favorites" finding on perplexity-based self-preference, and the 60-68% expert agreement ceiling all drove the five-layer stack design. The geometric mean replaced weighted sum after three independent frameworks converged on it. The ten-dimension rubric was shaped by four independent research reports across two batches.

### 4.6 The MCP Gateway

The MCP Gateway is the central router for all tool calls. Every search query, every API request, and every external data access goes through it.

It enforces per-agent tool authorization (agents cannot call tools they were not assigned), rate limiting (token-bucket algorithm per provider), circuit breaking (three failures trigger a 30-second cooldown), retry with exponential backoff (three retries before dead-lettering), and structured audit logging with SHA-256 I/O hashing.

Seven MCP server configurations are registered: Exa (neural search), Brave Search (web search), EdgarTools (SEC filings), FRED (economic data), paper-search-mcp (academic papers), doi-mcp (DOI verification), and Finnhub (financial data). Both HTTP and stdio transports are supported.

### 4.7 Supporting Components

**Knowledge Accumulation (Component #3b).** Implements the Karpathy wiki pattern. Raw research artifacts are stored verbatim. A compilation step produces structured markdown entries with content-hash provenance linking each compiled fact back to its raw source. An auto-maintained INDEX.md provides navigable access. The filesystem-based implementation is backed by a storage-agnostic Protocol interface, ready for PostgreSQL in Phase 2.

**HITL Infrastructure.** A database state machine implementing the two mandatory human review gates. REST API with five endpoints for creating gates, listing pending reviews, and submitting decisions (approve, modify, reject). A rejected gate raises a typed exception that halts the pipeline. The implementation maps cleanly to Temporal Signals in Phase 2 without changing the integration interface.

**Pipeline Orchestrator.** Wires the full Phase 1 flow: L0 to L1 to CitationProcessor to L1.5 to L4 to Markdown Renderer. Emits typed pipeline events at every stage transition. Layers 2 (Content Structuring) and 3 (Generation) are Phase 2 capabilities; the markdown renderer serves as the MVP output path.

---

## 5. The Research That Drove the Design

### 5.1 Why Research Before Building

The project committed to a research-first methodology. Twenty-six deep research reports were produced before a single line of production code was written. The rationale was straightforward: the cost of architectural rework is orders of magnitude higher than the cost of research. Getting the interfaces right means components can be built in parallel. Getting them wrong means every component built on a bad interface needs rework.

This bet paid off. Zero architectural rework was required during the build phase. Every design choice had a documented evidence trail. When pressure testing found eight bugs, all were implementation-level (parsing, headers, validation) rather than architectural (wrong abstractions, broken contracts, incompatible interfaces).

### 5.2 Batch 1: Exploring the Landscape

Sixteen deep research reports were organized into four thematic threads:

- **Thread A (Reports 1-5):** The technical landscape. Open-source research agent systems, evaluation frameworks, self-improvement mechanisms, orchestration patterns, and deep research tooling.
- **Thread B (Reports 6-9):** The consulting lens. What senior consulting partners value, what makes research decision-useful, what constitutes quality of thought, and how AI systems fail.
- **Thread C (Reports 10-13):** The pipeline stages. Specification-driven development, multi-perspective deliberation, report generation, and data retrieval architecture.
- **Thread D (Reports 14-16):** The frontier. The best individual and small-team AI systems, relevant academic papers, and high-leverage ideas.

These reports were produced by Claude.ai's deep research capability, running as parallel conversations within a shared project context. Each conversation received the same architectural context files but a topic-specific research prompt.

The reports were substantive. Report 6 (what senior partners value) identified six failure modes from practitioner testimony, mapped each to evaluation dimensions with pass/fail criteria, integrated intelligence tradecraft standards from ICD 203, and documented the BCG/Harvard field experiment with 758 consultants. Report 11 (deliberation) opened with the NeurIPS martingale proof and systematically evaluated seven production deliberation architectures. Report 14 (best AI systems) profiled six projects in detail, including a failure analysis section documenting what went wrong and why.

The reports were analyzed by four parallel Opus-tier subagents, one per thread, each producing structured per-report analyses and a thread summary. A single synthesis agent then read all four thread outputs and produced a unified synthesis with approximately 80 tool verdicts, 6 contradiction resolutions, and 17 specific plan changes. This hybrid approach balanced parallelism (independent analysis prevents confirmation bias) with coherence (a single synthesis agent sees all patterns before modifying the plan).

### 5.3 Batch 2: Targeted Questions

After Batch 1, eight open questions remained. A second round of ten research reports targeted these questions specifically:

1. How should the iterative research loop's stopping condition work?
2. What patterns exist for dynamic agent configuration?
3. What are best practices for MECE issue tree construction?
4. What should the retrieval architecture look like?
5. How should engagement types be classified?
6. How should context be managed across research rounds?
7. How should the evaluator adapt to different engagement types?
8. What MCP servers exist for our target data sources?
9. Which orchestration patterns should we use?
10. What should the Specification Engine pipeline look like?

Batch 2 differed from Batch 1 in both scope and analysis method. Where Batch 1 explored landscapes, Batch 2 answered specific questions. Where Batch 1 used four thread-level analysts, Batch 2 used ten individual analysts (one per report) because the reports were narrowly scoped and cross-report patterns were less important than per-report depth.

The Batch 2 synthesis produced 16 new decisions, resolved 6 contradictions, and recommended 48 specific plan changes. All 48 were applied and independently verified in a separate audit session.

### 5.4 The nano-claude-code Analysis

An unexpected opportunity arose when Anthropic accidentally shipped a 59.8 MB source map in an npm package, exposing 512,000+ lines of the Claude Code TypeScript source. A community Python reimplementation (nano-claude-code, 56 files, 11,833 lines) was analyzed overnight in a single autonomous Claude Code session.

The analysis validated every existing architectural decision without requiring any changes. Five patterns were adopted: generator-based agent loops, process-level isolation, a tractable MCP client architecture, two-layer compaction for long sessions, and agent definitions from markdown with YAML frontmatter. The most valuable finding was that thread-level isolation is insufficient and process-level isolation is required, independently validating the AgentLeak findings.

### 5.5 Evidence Quality Controls

The research process included several quality controls:

**Prompt auditing.** Every research prompt was audited before execution. The system prompt for the sixteen research agents was analyzed and nine critical flaws were found, resulting in a 40% shorter prompt with higher signal density. Individual prompts were vetted against the March 2026 landscape, identifying outdated references, missing tools and papers, and items to modify.

**Evidence tier classification.** Every finding was tagged as Verified (empirical, reproduced), Credible (active project, reputable source), Claimed (blog post, no evidence), or Stale (6+ months old, superseded). This prevented treating a single blog post with the same confidence as a peer-reviewed paper.

**Cross-reference requirements.** Every analysis was required to cross-reference findings against the existing plan changelog and implementation spec, preventing the rediscovery of settled decisions and ensuring findings mapped to specific build components.

---

## 6. How AI Built This System

### 6.1 Three Tools for Three Cognitive Modes

The project used three distinct AI tools, each for a different kind of thinking:

**Claude.ai Deep Research** for landscape exploration. Its autonomous multi-hop web research capability handled tasks like "what has the community discovered about multi-agent deliberation patterns?" that require following citations across sources and synthesizing across papers. Twenty-six reports were produced this way.

**Cowork (Claude's interactive chat)** for planning and design. The back-and-forth dialogue was essential for tasks requiring iterative refinement: restructuring CLAUDE.md, designing research prompts, auditing those prompts for internal consistency, debating architectural tradeoffs, and making judgment calls. The longest planning session spanned two days and produced the project's operational infrastructure.

**Claude Code (the CLI tool)** for execution. Direct file system access, parallel subagent spawning, and shell command execution made it the right tool for autonomous code generation, research synthesis, and overnight analysis. Sixteen build sessions, each producing a specific pipeline component with tests, were orchestrated through Claude Code.

The tools formed a pipeline: Deep Research explored the landscape, Cowork designed the approach, Claude Code built the thing. Information flow was unidirectional and file-mediated. No tool had direct access to another tool's context. All coordination happened through the filesystem, matching the project's own "Structure over intent" principle.

### 6.2 CLAUDE.md as Behavioral Contract

Every Claude Code session auto-loads the project's CLAUDE.md file. Its design was a deliberate architectural decision.

The original CLAUDE.md was 146 lines of project prose: thesis statements, evidence tables, a biographical section. This violated published best practices from the Claude Code creator, Boris Cherny, whose core principle is error-driven iteration: start minimal, run tasks, add corrections from actual failures.

The file was restructured to approximately 90 lines of behavioral rules. Project description content was removed. What remained was: a one-line project description, a directory map, deployment context (target platform, model mixing, cost target), five architectural convictions stated as behavioral constraints, a compact pipeline reference, an orientation section telling new sessions which files to read first, the session handoff protocol, working rules for communication and evidence standards, domain-specific key terms with precise definitions, and an empirical anchors table with five statistics and what each proves.

The principle: every line of CLAUDE.md competes with the agent's working context. A rule like "Make verdicts, not inventories" changes behavior more than three paragraphs describing the project's analytical philosophy. An empirical anchors table with five statistics (e.g., "17% to 92% | Claude Code + LangSmith | Harness > model") forces agents to ground their reasoning in evidence rather than making unsupported capability claims. The file grew from approximately 90 to 110 lines over the project as real errors revealed missing constraints. For example, when early analysis sessions used inconsistent verdict taxonomies, a standardized ADOPT/ADAPT/SKIP/INVESTIGATE taxonomy was added. When an audit session gave blanket "SOLID" verdicts without examining specific acceptance criteria, a rule about evidence-backed assessment was added. Each rule traces to a specific failure.

### 6.3 The Handoff Problem and Solution

Claude Code sessions are stateless. When a session ends, its context is lost. This creates three failure modes: repeated work (the new session reinvestigates settled decisions), contradictory decisions (the new session makes choices that conflict with previous sessions), and stale understanding (the new session reads the plan but does not know what has changed since it was written).

The solution was a three-document handoff system:

- **CLAUDE.md** (permanent, auto-loaded): What the project IS. Updated rarely.
- **SESSION-LOG.md** (append-only, chronological): What was DONE. Each entry contains date, agent type, task summary, files created and modified, key decisions, and what comes next. New sessions read this to understand the project arc.
- **CURRENT-STATE.md** (living snapshot, rewritten each session): What IS RIGHT NOW. Current phase, completed work, in-progress work, blockers.

A mandatory handoff rule in CLAUDE.md required every session to append to SESSION-LOG.md and rewrite CURRENT-STATE.md before finishing. In practice, sessions frequently forgot or ran out of context before completing the handoff. The planning session verified and fixed handoff documents after each wave, another instance of the project's layered quality control.

A fourth document, JACK-ARCHITECTURAL-DIRECTIVES.md, captured fourteen design decisions marked as authoritative and not overrideable by any Claude session. Without it, sessions would "improve" architectural decisions based on their own judgment, creating drift from the owner's intent.

### 6.4 Parallel Agent Orchestration

The project used several distinct parallelization patterns, each matched to the task's coordination requirements:

**Thread-based analysis (Batch 1 synthesis).** Four Opus-tier agents, one per thread of four to five reports. Each analyzed independently against the immutable plan. A single synthesis agent read all four outputs before touching the plan. Rationale: fully parallel analysis of all sixteen reports would prevent cross-report pattern detection, while fully sequential analysis would saturate context by report twelve. The hybrid of four-report threads balanced these constraints.

**Individual analysis (Batch 2 synthesis).** Ten Opus-tier agents, one per report. Different from Batch 1 because Batch 2 reports were narrowly scoped and cross-report patterns were less important than per-report depth. The orchestrator handled cross-referencing in the synthesis phase.

**Parallel specification (Track 1 architecture finalization).** Three parallel agents producing change specifications for different sections of the architecture plan (Sections 3-4, Sections 5-6, Sections 7-12), followed by orchestrator review for cross-section consistency. This enabled applying 48 changes without conflicts.

**Wave-based building.** Build sessions organized into waves by dependency. Wave 1 (provider swap, prompt migration, CitationProcessor) had no inter-session dependencies. Wave 2 (Research Agents, Deliberation) depended on Wave 1 outputs. Wave 3 (LLM client, pipeline orchestrator, test gaps) depended on Wave 2. Within each wave, sessions were assigned exclusive file ownership to prevent merge conflicts.

**Parallel pressure testing.** Four simultaneous test sessions, each targeting a different component (Specification Engine, Research Agents, Evaluator, Deliberation + CitationProcessor) with real LLM and search API calls.

### 6.5 Quality Assurance: Four Layers

Quality verification happened at four levels, each catching a different category of issue:

**Layer 1: Session Self-Audit.** Every build session prompt included a self-audit step between implementation and validation. The session ran its own tests, checked for regressions, and reported results. This caught approximately 60% of issues: syntax errors, import failures, and basic logic bugs.

**Layer 2: Post-Session Audit.** The planning session launched audit agents that read each build session's output, verified it against the original task specification, and ran the full test suite. This caught approximately 30% of remaining issues: specification compliance gaps, stale references, and missing files.

**Layer 3: Integration Review.** The planning session verified cross-session compatibility. Do outputs from Session A work with Session B's expectations? Are shared interfaces consistent? Does the full test suite pass after merging?

**Layer 4: Pre-Wave Structural Audit.** Before launching each wave, the entire codebase was audited for systemic issues. This is where the most critical bug was found: 9 of 11 tool name strings in the Specification Engine did not match the MCP Gateway's registrations. Two sessions had independently chosen different string identifiers for the same tools. Neither session's tests caught this because each tested in isolation with mocks. The fix was a shared ToolName enum that both modules import from, preventing future drift.

The pre-build audit pattern was also valuable. Before any code was written, three parallel audit sessions examined the scaffolding from different angles: a gap analysis found the research synthesis was only 60-65% complete, a code audit found seven files needing minor fixes (including a rubric weights sum of 1.05 instead of 1.00), and an execution readiness assessment identified that the retrieval architecture was over-engineered for the capstone timeline.

### 6.6 Lessons and Principles

Ten principles emerged from this development process:

1. **The prompt is the specification.** Session prompt quality is the ceiling for session output quality. A 148-line prompt for a 200-line module is proportional to the coordination cost of getting the module right without iterative feedback.

2. **Statelessness demands structure.** The only way to maintain coherence across sixteen autonomous sessions is persistent, structured documentation that every session reads.

3. **File ownership prevents conflicts.** The simplest way to enable parallel sessions is to ensure they touch zero overlapping files.

4. **Audit depth determines audit value.** The initial audit pass gave blanket quality verdicts. Only after the project owner pushed back and demanded deeper examination did the audit map each acceptance criterion to specific code paths and find real bugs.

5. **The owner's role is judgment, not code.** The most impactful interventions were "I do not trust this, dig deeper" (forced thorough audit), direct edits to design reasoning (business judgment no AI could replicate), and the fourteen architectural directives that prevented autonomous sessions from overriding consulting domain expertise.

6. **Error-driven iteration beats speculative planning.** CLAUDE.md grew from real errors. Session prompts improved from real failures. Rules were added when needed, not preemptively.

7. **Parallel analysis with atomic synthesis.** Give N agents the same immutable input. Have each produce structured output. Have a single agent read all N outputs and produce a consistent synthesis. This avoids merge conflicts while enabling parallel speedup.

8. **Detection over hope at every layer.** Four layers of quality verification catch different failure modes. No single layer is sufficient.

9. **The mock boundary is a quality boundary.** Mock testing validates plumbing (data flow, type safety, error handling). Real API testing validates behavior (JSON parsing, prompt-model fit, citation quality). These are fundamentally different quality dimensions.

10. **Configuration is architecture.** The choices in settings.json, agent frontmatter, and skill files shaped every session's behavior. These are not administrative settings. They are architectural decisions that determine the quality ceiling of every output.

---

## 7. Where It Stands and What Comes Next

### 7.1 What Has Been Demonstrated

The Phase 1 MVP is built and running. Ten production components implement the core pipeline from research question to analytical brief. Every major component has been individually pressure-tested with real LLM calls and real search APIs. The full pipeline has completed end-to-end. The system runs on Claude Opus 4.6 and Sonnet 4.6 via the Max subscription at zero API cost, with the provider swap validated against GPT-5.4 as well.

825 automated tests provide a regression safety net. The architecture survived a complete model provider replacement with zero contract or component changes. Eight implementation-level bugs were found and fixed during pressure testing; zero architectural bugs.

### 7.2 Active Development

**Research depth upgrade (in progress).** The initial research agents used shallow search-and-synthesize: API snippet queries producing 50-150 sources per engagement. This is being replaced by deep research agents that leverage Claude Code's multi-turn web search capability (`claude -p` with `--allowedTools "WebSearch,WebFetch"`). Empirical testing showed a single deep research agent producing 28 sourced claims with real URLs, current information, and multiple-source verification in 6 minutes. The target: each research agent produces deep-research-level output, with 5-10 agents running in parallel per engagement.

**Casing-informed MECE decomposition (pending).** The Specification Engine's MECE decomposition works with generic consulting prompts. Directive 12 envisions a principles-based skill file distilled from McKinsey casing methodology, which will upgrade the decomposition from generic MECE to trained-consultant-level problem structuring.

**Evaluator calibration.** After the deep research agents are integrated and produce higher-quality output, the evaluator's rubric will be calibrated against human scores. The target is 0.80+ Spearman rank correlation, Anthropic's own production standard.

### 7.3 The Roadmap

The MVP demonstrates the pipeline architecture: specification, research, citation processing, deliberation, evaluation. The full product vision extends this across five dimensions.

**User interface.** The system currently runs from the terminal. The production version needs a web interface where a consultant types a research question, adjusts pipeline depth, reviews the issue tree and confidence map at interactive HITL gates, and receives output with inline citations and confidence indicators. The architectural foundation is in place: typed pipeline events enable real-time progress streaming, the FastAPI HITL endpoints provide the review gate backend, and the Mermaid diagrams demonstrate the visualization concepts. The UI transforms adoption: consultants live in browsers and PowerPoint, not terminals.

**Production retrieval stack.** The current pipeline searches via Exa and Brave APIs. The researched and spec'd retrieval architecture (CAPSTONE-PLAN-v2.md Section 6.2) adds: pgvector with Voyage-finance-2 embeddings (49% improvement on financial QA), hybrid search with BM25 and Reciprocal Rank Fusion (26-31% NDCG improvement), Cohere Rerank, Docling for structure-aware PDF parsing (87.7% accuracy on tables and SEC filings), and three-source federation across public, internal, and historical data. This becomes critical when the system needs to search internal documents, analyze full 10-K filings, or maintain a knowledge base across engagements.

**Self-improvement system.** The Observation Library, trajectory storage, and client calibration profiles turn the system from a tool into a tool that learns. After each engagement, the system extracts patterns (heuristic observations, structural constraints, client-specific calibrations) and feeds them forward into future engagements via Case-Based Reasoning. Darwinian prompt evolution (GEPA/DSPy) systematically optimizes prompts after enough engagement data accumulates.

**Rich output generation.** Content Structuring (L2) applies consulting analytical frameworks to claim-level input. Deliverable Generation (L3) produces PowerPoint, Excel, and formatted PDF using tools like Vizro or PPTAgent. Anti-slop enforcement (8,000+ pattern detection with Redraft Specialist subagent) ensures output quality at the language level.

**Production infrastructure.** Temporal for durable workflow execution with crash recovery. PostgreSQL for persistent state and multi-user access. Authentication and multi-tenancy for client-scoped data isolation. Redis for caching at scale.

Longer-horizon roadmap detail is intentionally not routed from this tracked narrative until it exists as a tracked canonical artifact.

### 7.4 What This Means

The architecture is evidence-driven. Twenty-six research reports, analyzed by parallel agents, produced sixty-five specific changes to the plan. Every major design decision traces to a named source. Five original design assumptions were reversed when evidence proved them wrong.

The code is real. Ten thousand lines of production Python, organized into ten components with typed contracts and event systems. Working code tested against real models and real data sources.

The methodology is rigorous. Four layers of quality verification. Prompt auditing before execution. Evidence tier classification. Cross-reference requirements. Handoff protocols that persist context across sixteen autonomous sessions.

The build process itself is a contribution. Using three AI tools across different cognitive modes, orchestrating parallel autonomous agents with file-based coordination, and maintaining architectural coherence through structured handoffs represents a replicable methodology for AI-assisted system development.

The project has reached the point where the engine works and the next phase is making it deep, fast, and accessible. The remaining work is not conceptual scaffolding. It is the work of turning a validated architecture into a product a consulting firm would adopt.

---

## Appendix A: Decision Provenance Summary

| # | Decision | Origin | Evidence | Confidence |
|---|----------|--------|----------|------------|
| 1 | Deliberation: independent analysis, not debate | Batch 1 Reports C2, D2, C1 | NeurIPS martingale proof, DMAD ICLR 2025, DeepMind 180 configs | HIGH |
| 2 | Evaluator: 5-layer stack | Batch 1 Reports A2, B4, D2, D1, B1 | SOS-Bench 152K, Play Favorites, 60-68% ceiling, Deloitte incidents | HIGH |
| 3 | CitationProcessor as discrete stage | Batch 1 Reports A5, C3, D3 | Anthropic 90.2% improvement, PROV-AGENT W3C, five-layer chain | HIGH |
| 4 | Agent isolation (no shared findings) | Batch 1 Reports A4, A5 + Jones corpus | AgentLeak 68.8%, tool specialization finding | HIGH |
| 5 | Observation Library (successes + failures) | Directive 10 + Batch 1 Reports D1, B3, D2, A3 | ECC instinct pipeline, saturation after 2-3 iterations | HIGH |
| 6 | MECE issue tree decomposition | Directives 2, 12 + Batch 2 Reports 03, 10 | A-HMAD 4-6% gain, Self-MoA pattern | HIGH |
| 7 | Claim-level handoffs | Batch 1 Report D2 | Microsoft Research ICLR 2026, STORM NAACL 2024 | HIGH |
| 8 | Dynamic agent configuration | Directives 1, 6 + 5 Batch 2 reports | Convergent production evidence across 5 independent reports | HIGH |
| 9 | Three-criterion stopping condition | Directive 3 + Batch 2 Reports 01, 06, 10 | Anthropic/OpenAI/Google/DBAutoDoc convergence | HIGH |
| 10 | Configurable pipeline depth | Directive 11 + Batch 2 Reports 10, 05 | 5-type taxonomy, domain/analytical orthogonality | HIGH |
| 11 | Custom orchestration (PydanticAI + custom) | Directive 10 + Batch 1 Report A4 | AgentLeak, LangGraph CVEs, Agent SDK ToS | HIGH |
| 12 | Day-1 Hypothesis | Directive 3 + Batch 2 Report 10 | VOI framework, exploration-exploitation lifecycle | MEDIUM |
| 13 | Karpathy wiki pattern | Directive 8 + Batch 2 Report 04 | File-based memory 74% vs. Mem0 68.5% | MEDIUM |
| 14 | 10-dimension rubric | Batch 1 Reports B3, B1, B2, B4 + Batch 2 Report 07 | Taste 65/35 split, trendslop, ICD 203, geometric mean | HIGH |
| 15 | Component #3 split (#3a/#3b) | Directives 8, 9 + Batch 2 Report 04 | Karpathy pattern validated, Voyage-finance-2 49% improvement | HIGH |

## Appendix B: Session Chronology

| Date | Sessions | Key Events |
|------|----------|------------|
| Mar 27 | Pre-project | Nate Jones 91-article corpus analysis |
| Apr 3 | 1 | Batch 1 synthesis: 16 reports, 17 plan changes |
| Apr 4 | 2, 3 | Plan audit, implementation spec. Cowork planning begins. |
| Apr 5 | 3-12, 1A-1, 1A-2, 14, T2-4, 2A-1, T2-5, 8 | nano-claude-code analysis, 10 leak research reports, scaffolding, handoff protocol, 3 pre-build audits, Batch 2 analysis (48 changes), architecture finalization, Components #1, #2, HITL, Evaluator, 3 fork evaluations |
| Apr 6 | 1A-4 through 1A-11, 15, 16 | Components #4, #3b, #5, #7, #8, #9. Provider swap. Overnight audit. Wave planning. |
| Apr 7 | 4a-9 through 4a-12, 13 | Wave 4a pressure tests. 8 bugs found/fixed. Full pipeline run started, interrupted. |
| Apr 9 | 17 (parallel) | Comprehensive 5-agent audit. Architecture document written. Claude -p switchover (Codex OAuth -> Claude CLI on Max plan). First full pipeline run completed. Deep research agent architecture designed and implementation started. Directory cleanup, README rewrite, setup/demo scripts. |

## Appendix C: Key Empirical Anchors

| Statistic | Source | What It Proves |
|-----------|--------|----------------|
| 17% to 92% | Claude Code + LangSmith | Harness engineering, not model capability, determines quality |
| 96.5% SpreadsheetBench | AutoAgent | Self-optimizing harness outperforms hand-engineering |
| 29-30% false claims | Claude agentic benchmarks | Structural evaluation catches approximately one-third of output errors |
| 78% vs. 42% | Same model, different harness | Specification quality explains 2x variance in output quality |
| 68.8% leakage | AgentLeak benchmark | Agent isolation must be architectural, not framework-level |
