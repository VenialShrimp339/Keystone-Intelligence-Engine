# The Keystone Intelligence Engine
## A Multi-Agent Architecture for Automated Consulting Research & Analysis

*Capstone Project — Econ Consulting (Prof. Youle) | Jack Riddle | IU Kelley School of Business | Spring 2026*

---

## 1. Executive Vision

Management consulting runs on research. Before a partner walks into a boardroom with a recommendation, dozens of hours have been spent pulling SEC filings, mapping competitive landscapes, sizing markets, stress-testing assumptions, and synthesizing it all into a narrative that drives a $50M decision. That research work — thorough, rigorous, expensive — is both the foundation of every engagement and the bottleneck that constrains how many engagements a firm can run at peak quality.

This project builds an autonomous research engine: a multi-agent LLM system that takes a research question — "Evaluate the competitive position of Company X in the autonomous vehicle sensor market" — and produces a complete, Keystone-quality analytical brief. Not a summary of Google results. Not a template with blanks. A grounded, source-cited, multi-perspective analysis with the depth and rigor a Senior Engagement Manager would expect from a three-analyst team working a full week. The system decomposes the question into parallel research threads, dispatches specialized agents to investigate each thread against public and proprietary data sources, runs a structured deliberation that surfaces consensus and contested findings, constructs a narrative framework, and subjects every section to an independent evaluator calibrated to Keystone's own quality standards. Every number is traced to a source. Every claim is stress-tested. Every "so what?" is explicit.

What makes this more than an engineering project is the self-improvement loop. Drawing from Andrej Karpathy's autoresearch paradigm and its derivatives in financial markets, the system treats its own research methodology as the "editable asset" and research quality as the "scalar metric." After each completed project, it evaluates which agents, prompts, and analytical approaches produced the highest-scoring work — then evolves the worst performers while preserving what works. The tool doesn't just do research. It learns to do research better, compounding every engagement into institutional intelligence that makes the next one faster, cheaper, and sharper.

---

## 2. Architecture Overview

The original proposal described three layers: Data Ingestion, Content Structuring, and Generation/QA. After deep analysis of Anthropic's own engineering practices, production multi-agent systems, and the practitioner literature on agentic architectures, that design evolves into a six-layer architecture with a meta-optimization loop. Each layer exists because a specific source or engineering finding demanded it.

```
┌─────────────────────────────────────────────────────────────────┐
│                    META-LAYER: SELF-IMPROVEMENT                 │
│  Autoresearch loop · Darwinian prompt evolution · Trajectory    │
│  storage · Skill library growth · Compounding research assets   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ optimizes all layers over time
┌──────────────────────────────┼──────────────────────────────────┐
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LAYER 0: ORCHESTRATION                     │    │
│  │  Research question → task decomposition → agent         │    │
│  │  lifecycle → progress tracking → human review gates     │    │
│  └────────────┬───────────────────────────────┬────────────┘    │
│               │                               │                 │
│  ┌────────────▼────────────┐    ┌─────────────▼─────────────┐  │
│  │  LAYER 1: DATA          │    │  LAYER 4: EVALUATION      │  │
│  │  INGESTION & RESEARCH   │◄──►│  Independent evaluator    │  │
│  │  Parallel agents ·      │    │  Keystone-calibrated      │  │
│  │  unified retrieval ·    │    │  rubric · structural      │  │
│  │  JIT context            │    │  enforcement · multi-     │  │
│  └────────────┬────────────┘    │  dimensional scoring      │  │
│               │                 └─────────────▲─────────────┘  │
│  ┌────────────▼────────────┐                  │                 │
│  │  LAYER 1.5:             │                  │                 │
│  │  DELIBERATION           │                  │                 │
│  │  Multi-perspective      │                  │                 │
│  │  debate · confidence    │                  │                 │
│  │  mapping · gap          │                  │                 │
│  │  detection              │                  │                 │
│  └────────────┬────────────┘                  │                 │
│               │                               │                 │
│  ┌────────────▼────────────┐                  │                 │
│  │  LAYER 2: CONTENT       │──────────────────┘                 │
│  │  STRUCTURING &          │                                    │
│  │  REASONING              │                                    │
│  │  Skill-driven analysis  │                                    │
│  │  · narrative framework  │                                    │
│  │  · sprint contracts     │                                    │
│  └────────────┬────────────┘                                    │
│               │                                                 │
│  ┌────────────▼────────────┐                                    │
│  │  LAYER 3: GENERATION    │                                    │
│  │  (Future: PowerPoint,   │                                    │
│  │   Excel, formatted      │                                    │
│  │   deliverables)         │                                    │
│  └─────────────────────────┘                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 0: Orchestration

**What it does:** Receives the research question, spawns an Initializer agent to decompose it into a structured JSON task list, manages the lifecycle of all downstream agents, tracks progress, and provides optional human review gates between layers.

**Why it's designed this way:** The orchestrator pattern — where the coordinating agent never does substantive work itself — emerged from @johann_sath's production experience and is reinforced by Khaliq Gant's six weeks of multi-agent orchestration work (*"Let Them Cook"*). Gant discovered that orchestrators that try to do real work alongside coordination lose coherence. The design also draws from Anthropic's *Effective Harnesses for Long-Running Agents* (Justin Young), which showed that an Initializer agent that decomposes the task into a structured JSON feature list — not Markdown, because models are less likely to corrupt JSON's rigid structure — dramatically improves downstream agent coordination. The orchestrator spawns agents via ACP (Agent Client Protocol), tracks their progress in a `research-status.json` manifest, and caps parallel workers at 2-5 per orchestrator — the empirical scaling sweet spot Gant discovered after watching systems with 10+ workers cause Lead agents to "die" from cognitive overload.

### Layer 1: Data Ingestion & Research

**What it does:** Parallel research agents fan out across public data (SEC filings, industry reports, news, video transcripts, academic papers), internal Keystone documents, and historical findings from prior projects. Each agent claims a research thread, investigates it deeply, and returns a condensed 1-2 page synthesis.

**Why it's designed this way:** Three Anthropic sources converge on this design. Nicholas Carlini's C Compiler project (16 agents, 2,000 sessions, $20K in API costs) demonstrated that agents coordinating through a shared repository — claiming tasks via lock files, pushing findings to shared directories — outperforms central task assignment. No orchestration bottleneck. Anthropic's *Context Engineering* article established that sub-agents should do extensive work but return only condensed summaries to the orchestrator, because context is a scarce resource with diminishing marginal returns as token count grows. And Anthropic's *Writing Effective Tools for Agents* (Ken Aizawa) showed that research tools must be designed for agent consumption — consolidating multi-step data retrieval into single workflow-level calls that return concise, pre-processed output rather than raw API responses. The "just in time" context paradigm means agents maintain a lightweight index of available data and load specific sources on demand, rather than pre-loading entire filings into context where they dilute reasoning quality.

### Layer 1.5: Deliberation

**What it does:** After research agents produce independent findings, a structured multi-perspective debate identifies consensus, contested claims, and gaps requiring further investigation. Multiple "analyst persona" agents — Bull Case, Bear Case, Consensus View, Contrarian — each construct a thesis from the shared findings and critique each other's positions.

**Why it's designed this way:** This layer didn't exist in the original proposal. It emerged from the MiroFish swarm intelligence engine (@k1rallik), which demonstrated that multi-agent debate and convergence produces higher-quality synthesis than single-agent aggregation. The deliberation phase mirrors the most valuable moment in a real consulting engagement: the team synthesis meeting where analysts present competing interpretations, challenge assumptions, and converge on a unified thesis. The output isn't just merged findings — it's a *confidence map* that tells the structuring agent which conclusions are high-confidence (all perspectives agreed) and which need nuanced treatment (legitimate disagreement). This prevents the common failure mode of AI-generated analysis: false confidence in contested claims.

### Layer 2: Content Structuring & Reasoning

**What it does:** Takes synthesized findings plus the confidence map, applies consulting analytical frameworks via a skills library, builds the narrative arc, and produces a structured outline with supporting evidence mapped to each section.

**Why it's designed this way:** Anthropic's *Harness Design* article (Prithvi Rajasekaran) introduced sprint contracts — before generating each section, the structuring agent and the evaluator *negotiate what "done" looks like*. For a market sizing section, the contract might specify: "Must include top-down and bottom-up estimates. Must cite at least 3 independent data sources. Must quantify uncertainty range. Must compare against at least one external estimate." This turns vague quality aspirations into concrete, testable criteria that the evaluator can grade against. The skills library concept draws from Boris Cherny (Claude Code creator), who emphasized encoding domain expertise into reusable skill files rather than embedding it in prompts, and from John Prendergast's analysis of Anthropic's Wealth Management Plugin, which structures professional services workflows as skills with defined inputs, outputs, and intermediate steps.

### Layer 4: Evaluation

**What it does:** An independent evaluator agent — never the same instance as the generator — grades each section of the analysis against a multi-dimensional rubric calibrated to Keystone's quality standards. Failed sections receive specific feedback and get regenerated.

**Why it's designed this way:** This is the single most important architectural decision in the system, and it's grounded in Anthropic's strongest empirical finding: LLMs systematically skew positive when evaluating their own work, and no amount of prompting for self-criticism overcomes this bias. The *Harness Design* article demonstrated that a separate evaluator instance — analogous to a GAN's discriminator — must be independently tuned toward skepticism. The evaluator in that system used Playwright MCP to actually interact with outputs (navigating pages, taking screenshots, checking functionality), not just read them. Carlini's C Compiler project reinforced the finding from a different angle: "Claude will work autonomously to solve whatever problem I give it. So it's important that the task verifier is nearly perfect, otherwise Claude will solve the wrong problem." The test harness — the evaluator — is more important than the agent prompt. Improving evaluation had more impact on output quality than improving generation instructions. Critical quality requirements (source citation, data accuracy, format compliance) are enforced structurally through tool design and pipeline architecture, not through prompt instructions — because @jordymaui's finding that language-based instructions drift approximately 40% of the time means prompt-only quality gates are unreliable at production scale.

### Meta-Layer: Self-Improvement

**What it does:** After each completed project, the system evaluates which research approaches, agent configurations, and analytical frameworks produced the highest-quality work — then evolves the worst performers. The pipeline's own research methodology is the "editable asset"; research quality scores are the "scalar metric."

**Why it's designed this way:** Three convergent sources established this design. Karpathy's autoresearch paradigm provides the foundational loop: define an editable asset, a scalar metric, and a time-boxed optimization cycle, then let the system iterate. Chris Worsey (@Chris_Worsey) applied this to financial markets with Darwinian agent selection — 25 agents producing daily recommendations, with the worst performer by rolling Sharpe ratio getting its prompt rewritten by the system — achieving +22% returns over 173 days. And @Hesamation documented a skill going from 56% to 92% accuracy in just 4 rounds of autoresearch iteration. The *everything-claude-code* repository's "instinct system" provides the mechanism: temporary patterns observed during research get logged as instincts, valuable instincts are evolved into permanent skills after validation, and instincts that don't generalize get pruned. This is more practical than ML-based self-improvement — it starts working immediately and compounds with every project.

---

## 3. The Research & Analysis Engine (Core Focus)

This section describes how the system takes a research question and produces a rigorous, Keystone-quality analytical brief. This is where the capstone's primary contribution lives.

### 3.1 Research Initiation: From Question to Task List

A research engagement begins when a user provides a question — anything from "Evaluate Company X's competitive position" to "Size the North American market for autonomous vehicle sensors by 2030." The Orchestrator (Layer 0) receives this and immediately spawns an **Initializer Agent**.

The Initializer does not research. Drawing from Anthropic's *Harness Design* finding that planners should stay at "product context" level and avoid granular technical details — because errors in an overly-detailed plan cascade downstream — the Initializer decomposes the question into 15-50 discrete research tasks, each scoped tightly enough for a single agent session. The output is a `research-tasks.json` file:

```json
{
  "project": "Acme Corp Competitive Position Analysis",
  "research_question": "Evaluate Acme Corp's competitive position in the autonomous vehicle sensor market",
  "tasks": [
    {
      "id": "task_001",
      "category": "market_sizing",
      "description": "Estimate TAM for L4+ AV sensor market in North America by 2030",
      "required_sources": ["industry_reports", "financial_data", "academic"],
      "acceptance_criteria": [
        "Top-down and bottom-up estimates with explicit assumptions",
        "At least 3 independent data sources cited",
        "Uncertainty range quantified",
        "Comparison against at least one external analyst estimate"
      ],
      "passes": false,
      "priority": 1
    },
    {
      "id": "task_002",
      "category": "competitive_landscape",
      "description": "Map key players by technology approach and market share",
      "required_sources": ["company_filings", "news", "patents"],
      "acceptance_criteria": [
        "Top 8-10 competitors identified with differentiation",
        "Categorized by approach (lidar vs. camera-only, full-stack vs. component)",
        "Competitive moats and vulnerabilities assessed per player",
        "Positioning matrix with 2+ meaningful dimensions"
      ],
      "passes": false,
      "priority": 1
    }
  ]
}
```

Three design decisions are critical here. First, tasks are structured as JSON, not Markdown — Anthropic's *Effective Harnesses* article found that models are significantly less likely to inappropriately modify or corrupt JSON compared to Markdown, making it safer for multi-agent state tracking. Second, each task carries explicit `acceptance_criteria` — these become the sprint contracts that the evaluator grades against. Third, the `passes` field can only be flipped by the Evaluator agent, never by the research agent itself — this is structural enforcement of quality gates, not prompt-based enforcement.

### 3.2 Parallel Research Execution

Once the task list exists, the Orchestrator fans out research agents. Each agent:

1. **Claims a task** by writing a lock file (e.g., `claimed_threads/task_001.lock`), following Carlini's git-based coordination pattern where the file system prevents duplicate work without requiring a central scheduler.

2. **Loads context just-in-time.** The agent doesn't start with all available data preloaded. It starts with the Research Index — a lightweight manifest of available sources, prior findings, and the project's analytical framework — then dynamically loads specific sources as needed. This follows Anthropic's *Context Engineering* principle that context has diminishing marginal returns: loading an entire 10-K filing into context is worse than loading the three relevant sections, because the irrelevant content dilutes the model's attention across thousands of tokens it doesn't need.

3. **Investigates using workflow-level tools.** Following Aizawa's guidance in *Writing Effective Tools for Agents*, the research tools are designed for agent consumption — not raw API wrappers. Instead of separate calls to `get_company_financials`, `get_company_news`, and `get_company_filings`, the agent calls `research_company(company="Acme Corp", focus_areas=["financials", "competitive"])`, which returns a pre-synthesized summary with key metrics, recent developments, and notable filings — all in one context-efficient response. Tool responses support concise/detailed modes: agents get the concise version by default and request details only when needed, reducing context consumption by roughly two-thirds per call (consistent with Aizawa's measurement of 206 tokens vs. 72 tokens for the same Slack query in different modes).

4. **Writes findings to the shared store.** Each agent produces a structured finding — claim, supporting evidence, source citations with access dates, confidence level, and caveats — and commits it to the `findings/` directory. The finding format enforces source citation structurally: the tool output format includes citations as a required field, so an uncited claim literally cannot be produced. This is the @jordymaui principle applied to research integrity: don't tell the agent to cite sources, make it impossible not to.

5. **Returns a condensed summary.** Following the sub-agent architecture pattern from Anthropic's *Context Engineering* work, each research agent may process tens of thousands of tokens during its investigation but returns only a 1-2 page condensed synthesis to the Orchestrator. The Orchestrator never sees raw data. It works with pre-synthesized intelligence — exactly how a consulting engagement manager operates, receiving digested analysis from their team rather than reading every source document.

### 3.3 Agent Specialization

Not all research is the same. Different threads benefit from different agent "personalities" and toolsets. Drawing from Carlini's C Compiler project — where agents were specialized into roles like code coalescing, performance optimization, design critique, and documentation — the research pipeline uses specialized agent types:

- **Quantitative Research Agent**: Optimized for financial data extraction, ratio analysis, trend decomposition, and numerical verification. Its tools prioritize structured data sources (SEC EDGAR, financial databases). Its soul prompt (following @tolibear_'s distinction between skills and identity) is calibrated toward precision, skepticism about rounded numbers, and explicit uncertainty quantification.

- **Qualitative Research Agent**: Optimized for narrative sources — news articles, expert commentary, conference presentations, video transcripts. Ingests content via Cloudflare /crawl for systematic website extraction and Defuddle for video transcript processing with timestamps and speaker diarization. Its soul prompt emphasizes synthesis, thematic pattern recognition, and identification of sentiment shifts over time.

- **Contrarian Agent**: Exists specifically to stress-test the emerging thesis. Looks for disconfirming evidence, identifies assumptions the other agents are making implicitly, and surfaces risks the consensus view might be underweighting. This agent is the institutional check against confirmation bias — a failure mode that @Chris_Worsey's Darwinian selection work identified as persistent in single-agent research.

- **Internal Document Agent**: Specializes in navigating and synthesizing Keystone's proprietary materials (covered in Section 4).

Each agent type has both a skill set (procedural knowledge — what tools to use, what data formats to expect) and a soul prompt (identity and judgment — how skeptical to be, what "good enough" looks like, when to push deeper versus move on). The Evaluator Agent's soul prompt, for example:

> *You are a Senior Engagement Manager at a top-3 management consulting firm. You have reviewed 500+ research deliverables. When you see surface-level analysis, you push for depth. When you see unsupported claims, you demand evidence. When you see generic frameworks applied without adaptation, you reject them. Your standard: would a Managing Director present this to a Fortune 500 CEO without edits?*

This soul-based approach to agent design emerged from @tolibear_'s insight that agents need identity and judgment alongside procedural knowledge — a "skilled agent without a soul produces correct but generic output."

### 3.4 The Deliberation Phase

After research threads complete, the system doesn't immediately hand findings to the structuring agent. First, it runs a Deliberation — an architectural innovation inspired by MiroFish's swarm intelligence work, where multi-agent debate and convergence outperforms single-agent aggregation.

The Deliberation spawns 3-4 analyst personas, each constructing a thesis from the shared findings:

- **Bull Case Analyst**: Constructs the most optimistic defensible interpretation. Where is the company strongest? What growth catalysts does the market underappreciate?
- **Bear Case Analyst**: Constructs the most pessimistic defensible interpretation. Where are the hidden risks? What competitive threats are being underestimated?
- **Consensus Analyst**: Synthesizes the modal view — what would a well-informed analyst conclude as the most likely scenario?
- **Contrarian Analyst**: Identifies what everyone is assuming that might be wrong. What second-order effects could invalidate the consensus?

Each persona produces a 1-page thesis, then a synthesis round runs where each critiques the others' positions. The output is a **confidence map**:

```json
{
  "high_confidence": [
    {"claim": "Acme holds 23% sensor market share, growing", "agreement": "4/4", "sources": 7}
  ],
  "moderate_confidence": [
    {"claim": "Lidar costs will drop below $500/unit by 2028", "agreement": "3/4", "dissent": "Bear case argues supply chain constraints delay to 2030", "sources": 4}
  ],
  "contested": [
    {"claim": "Camera-only approaches will converge with lidar on safety metrics", "agreement": "2/4", "key_disagreement": "Fundamental debate on sensor fusion necessity", "sources": 3}
  ],
  "gaps_identified": [
    "No data on Acme's patent portfolio defensibility",
    "Regulatory landscape in EU not yet investigated"
  ]
}
```

This confidence map tells the structuring agent exactly how to handle each claim. High-confidence findings become assertions. Moderate-confidence findings get presented with caveats. Contested findings are framed as "perspectives" with both sides represented. Gaps identified trigger additional research threads — the system is self-correcting, identifying its own deficiencies and spawning work to address them (the Mission Control pattern from @pbteja1998, where agents create work for other agents).

### 3.5 Content Structuring via Sprint Contracts

Layer 2 receives the synthesized findings and the confidence map, then constructs the analytical narrative. This is where the system applies consulting analytical frameworks — Porter's Five Forces, value chain mapping, profit pool analysis, TAM/SAM/SOM sizing — via a **skills library**.

The skills library follows the three-layer loading architecture discovered in John Prendergast's analysis of Anthropic's Wealth Management Plugin: at startup, the agent loads only lightweight skill names and descriptions (Layer 1 of the skill architecture). When the analytical task matches a skill, the full methodology file loads (Layer 2). Supporting documents — glossaries, example analyses, reference data — load on demand (Layer 3). This progressive loading minimizes context consumption while giving the agent deep methodological guidance exactly when needed.

Each skill is a directory:

```
skills/
├── market-sizing/
│   ├── SKILL.md          # Methodology: top-down + bottom-up + triangulation
│   ├── gotchas.md        # Common mistakes: confusing TAM with SAM, ignoring adoption curves
│   └── examples/         # Anonymized past Keystone market sizing analyses
├── competitive-analysis/
│   ├── SKILL.md          # Methodology: positioning matrix + moat assessment
│   ├── gotchas.md        # Common mistakes: confusing market share with mind share
│   └── examples/
└── financial-analysis/
    ├── SKILL.md          # Methodology: ratio analysis + trend decomposition + peer comparison
    ├── gotchas.md
    └── examples/
```

Skills are interconnected, not flat — drawing from @rohit4verse's Ars Contexta skill graph architecture. Market sizing links to industry analysis (market sizing requires industry understanding). Competitive analysis links to company valuation (competitive position affects valuation). Research agents navigating this graph discover that their current task requires complementary analysis from a related skill, enabling the system to surface analytical connections that a rigid task list might miss.

Before generating each section, the structuring agent and the Evaluator negotiate a **sprint contract** — Anthropic's *Harness Design* innovation that bridges the gap between high-level specifications and testable criteria. For a competitive landscape section, the contract might read:

> **Sprint Contract: Competitive Landscape**
> - Must identify 8+ competitors with defensible differentiation criteria
> - Positioning matrix uses 2+ dimensions that reveal strategic insight (not just "price vs. quality")
> - Each competitor assessment includes at least one non-obvious vulnerability
> - Competitive moat analysis distinguishes between structural moats and temporary advantages
> - Section must explicitly address: "What would have to change for the current leader to lose their position?"

The evaluator then grades the generated section against these exact criteria. A section that maps competitors on a generic 2x2 without strategic insight fails, regardless of how well-written it is. This is what makes the quality enforcement specific rather than aspirational.

### 3.6 The Evaluation Loop

Every section passes through the independent Evaluator Agent before it can be considered complete. The evaluator never sees the generator's reasoning process — it receives only the output and the sprint contract, then grades against a multi-dimensional rubric:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Analytical Depth | 20% | Are conclusions non-obvious? Is the analysis layered, not surface-level? |
| Source Quality | 15% | Are sources authoritative and diverse? Is there appropriate skepticism? |
| Quantitative Rigor | 15% | Are claims supported by data? Are uncertainties explicitly quantified? |
| Narrative Coherence | 15% | Does the analysis tell a clear story? Is the "so what?" evident? |
| Completeness | 15% | Are obvious follow-up questions addressed? Are there gaps a partner would notice? |
| Actionability | 20% | Could a consultant advise a client based on this? Does it drive a decision? |

These weights are deliberately calibrated away from where LLMs naturally perform well (coherent prose, comprehensive coverage) and toward where they naturally underperform (analytical novelty, quantitative rigor, actionable insight) — following Anthropic's *Harness Design* finding that evaluator dimensions should be weighted toward the generator's weakest areas to maximize the evaluator's corrective impact.

Calibration uses few-shot examples: 10+ past Keystone deliverables, each scored by Jack on this rubric, serve as the calibration set. The evaluator is tuned until its scores match Jack's scores within ±1 point per dimension. This is how the system's quality standard becomes *Keystone's* quality standard, not a generic AI quality standard.

When a section scores below threshold on any dimension, the evaluator provides specific feedback — "The competitive moat analysis conflates temporary cost advantages with structural network effects. Distinguish between moats that compound over time and advantages that can be replicated in 18 months." — and the generator regenerates with this feedback. Drawing from Anthropic's experience with iterative refinement, the generator makes a strategic decision on each rejection: refine the current direction, or pivot to an entirely different analytical approach. This mirrors the consulting reality where sometimes the right response to "this analysis isn't deep enough" is to dig deeper, but sometimes it's to reframe the question entirely.

Mitchell's 20-agent content pipeline (@MitcheIl) independently validated this pattern with a dual-axis quality gate: every line was scored for both *Invention Novelty* (does this feel like a breakthrough insight?) and *Copy Intensity* (does the reader feel something, not just understand?). Both had to hit maximum scores. Flat analysis with a novel insight fails. Sharp writing about a generic observation fails. The consulting analog is clear: every insight on a slide should be scored for both *analytical rigor* (is it defensible?) and *executive impact* (would it change a decision?). An insight that is rigorous but boring, or provocative but unsubstantiated, gets cut.

---

## 4. Internal Document Integration

The ability to synthesize proprietary firm documents alongside public data is what separates this system from any publicly available AI research tool. This is the capability that makes it specifically valuable to Keystone, not just generically useful.

### 4.1 The Scaffold vs. System Distinction

John Prendergast's analysis of Anthropic's Wealth Management Plugin exposed the critical distinction between **scaffolds** (well-structured templates without data access) and **systems** (templates connected to real data with automated verification). The plugin produces beautiful report structures — cover pages, executive summaries, allocation analyses — but cannot pull a single number from any account. Prendergast's verdict: "AI drafts a variance analysis in 30 seconds. The analyst spends 2.5 hours verifying every number. Net time saved: maybe 30 minutes." He called this the **Hallucination Tax** — the hidden cost of verifying AI output that has no data grounding.

The Keystone Intelligence Engine must be a system, not a scaffold. This means:

- Research agents pull data from actual sources (SEC EDGAR, industry databases, news APIs, Keystone's document store) — not from parametric memory
- Every factual claim in the output is traced to a specific source with URL and access timestamp
- The verification agent spot-checks cited claims against their sources before any section is marked as passing
- Internal documents are retrieved, not hallucinated

### 4.2 Unified Retrieval Architecture

The Internal Document Agent operates against a dedicated retrieval layer built on Keystone's proprietary corpus — strategy documents, prior client deliverables (anonymized where necessary), engagement debriefs, template libraries, and methodology guides. Drawing from the Supermemory ASMR architecture (@VadimStrizheus), which demonstrated that hybrid search combining RAG with conversational memory in a single query outperforms sequential search, the system implements a **unified retrieval interface**:

```
research_search(query, scope=["public", "internal", "historical"])
```

One query fans out across three source categories:
1. **Public sources**: Web search, SEC filings, industry reports, news, academic papers
2. **Internal sources**: Keystone's document store — past deliverables, methodology guides, partner preferences
3. **Historical sources**: Findings from prior research projects completed by this system

Results return merged, ranked, and annotated with source provenance. The research agent sees a single, coherent result set — it doesn't need to know or care which sources are proprietary vs. public. The retrieval layer handles the routing.

### 4.3 Security and Data Isolation

Internal documents require a security model. Research agents can READ internal documents but cannot WRITE to them or exfiltrate content outside the project scope. Client-confidential information is sandboxed — findings from Client A's engagement never appear in Client B's research, even if the topics are related. An audit log records every internal document access for compliance purposes. This follows @JordanLyall's principle of minimum-viable permissions: start with read-only access to internal documents, expand capabilities only with explicit authorization.

### 4.4 Why Internal Integration Matters

The value is compounding. Every Keystone engagement the system has access to becomes part of its institutional memory. When a new project involves analyzing a market Keystone has studied before, the system doesn't start from scratch — it queries prior findings, identifies what's changed, and builds incrementally. This mirrors how experienced consultants actually work: a partner who's done five healthcare engagements brings a mental model to the sixth that a first-year analyst doesn't have. The system builds that institutional memory programmatically, making it available to every engagement regardless of which human consultants are staffed.

Amy Tam's thesis (@amytam01) — "When code is free, research is all that matters... the differentiator is knowing what's worth building and whether it's buildable at all" — applies here. When every consulting firm has access to the same LLMs, the competitive advantage shifts to proprietary data and accumulated expertise. The system that learns from Keystone's own engagement history produces analysis that no competitor's AI tool can replicate, because no competitor has access to Keystone's institutional knowledge.

---

## 5. Self-Improvement Loop

The system doesn't just do research. It learns to do research better. This is the architectural feature that transforms a static tool into a compounding asset.

### 5.1 The Autoresearch Ratchet

Karpathy's autoresearch paradigm defines the template: take any system with an editable asset and a scalar metric, and the system can optimize itself through iterative cycles of generation, evaluation, and modification. For the Keystone Intelligence Engine:

- **Editable asset**: Agent prompts, skill methodology files, evaluator rubric weights, tool configurations
- **Scalar metric**: Research quality scores from the evaluator (the six-dimension rubric described in Section 3.6)
- **Time-boxed cycle**: One complete research project = one cycle

After each project completes, the meta-optimization system:

1. **Collects evaluator scores** broken down by research thread, agent type, and analytical framework used
2. **Identifies what worked** — which skill methodologies produced above-threshold sections? Which agent configurations consistently scored highest?
3. **Identifies what failed** — which threads required the most regeneration cycles? Where did the evaluator most frequently flag deficiencies?
4. **Generates improvement hypotheses** — specific proposed modifications to prompts, skills, or tool configurations
5. **Validates in the next project** — the modification is tested against the next research question, and retained only if scores improve

The @Hesamation finding — a skill going from 56% to 92% accuracy in four rounds of autoresearch iteration — suggests that this loop can produce dramatic improvement quickly. The key constraint: each round must produce a measurable score on the same rubric, creating an apples-to-apples comparison that prevents the system from gaming the metric.

### 5.2 Darwinian Prompt Evolution

Chris Worsey's financial market application provides the more aggressive variant. Rather than manually analyzing failures, the system maintains a population of agent prompt variants and applies selection pressure:

1. Multiple research agent configurations (varying in analytical approach, skepticism level, source preferences) run in parallel
2. After each project, agents are ranked by average evaluator score across their research threads
3. The worst-performing configuration gets its prompt rewritten — either inspired by the best performer or generated as a novel variant
4. The rewritten prompt runs on the next project; keep if improved, revert if degraded

This is literal Darwinian evolution applied to research methodology. The system discovers optimal research approaches through competition and selection rather than through human curation. Over 10-20 projects, the agent population converges on research approaches that consistently produce Keystone-quality output — approaches that may be non-obvious to a human designer.

### 5.3 Trajectory Storage: Institutional Memory

Every completed project generates a **trajectory record** — the full decision log of what was researched, which sources were most valuable, what analytical frameworks were applied, what the evaluator flagged, and how the final deliverable was received. Following Khaliq Gant's trajectory storage pattern, these records persist in a structured directory:

```
trajectory-store/
├── project_001_acme_competitive/
│   ├── trajectory.json       # Full decision log: tasks, agents, timing, costs
│   ├── sources_rated.json    # Which sources proved most valuable (ranked by evaluator impact)
│   ├── frameworks_used.md    # Which analytical frameworks worked, which were abandoned
│   ├── evaluator_feedback.md # All evaluator critiques and how they were resolved
│   └── quality_scores.json   # Final per-section and overall quality scores
├── project_002_market_sizing_ev/
│   └── ...
```

When a new project begins, the Initializer queries the trajectory store for similar past projects. If Keystone has previously analyzed a company in the same industry, the Initializer retrieves that project's trajectory — what research questions were most productive, which sources proved most valuable, which analytical frameworks generated the highest-scoring output — and incorporates those lessons into the new project's task decomposition.

This is the everything-claude-code repository's "instinct system" applied to consulting research: temporary patterns observed during research (instincts) get logged, patterns that prove valuable across multiple projects are evolved into permanent skills, and patterns that don't generalize get pruned. Every engagement makes the system smarter. The trajectory store is the mechanism through which institutional knowledge compounds.

### 5.4 The Quality Metric as Academic Contribution

Defining what "research quality" means in a computable, evaluable way is arguably the capstone's most novel contribution. As the autoresearch community roundup (@zhengyaojiang) noted: "Anything with a measurable metric can be autoresearched." Karpathy had loss functions. Worsey had Sharpe ratios. Jack's system needs a research quality metric that:

- **Is computable**: An evaluator agent can produce it reliably and consistently
- **Correlates with human judgment**: A Keystone partner would broadly agree with the system's quality rankings
- **Is granular enough to drive improvement**: Not just "good/bad" but specific dimensional feedback
- **Is resistant to gaming**: The system can't achieve high scores through surface-level tricks

The six-dimension rubric (Analytical Depth, Source Quality, Quantitative Rigor, Narrative Coherence, Completeness, Actionability) is the starting design. Calibrating it against actual Keystone deliverables scored by experienced consultants — then measuring how well the automated evaluator's scores correlate with human scores — is the quantitative backbone of the capstone research. The improvement curve (quality scores over successive projects as the self-improvement loop runs) is the empirical evidence that the system works.

---

## 6. Future Layers: Deliverable Generation

The research and analysis engine is the core — but the path to full consulting deliverable automation is clear, and the architecture is designed to extend.

### 6.1 PowerPoint Generation (Layer 3a)

The structured outline from Layer 2, with its section-by-section findings and evidence mapping, is designed as the input format for a PowerPoint generation agent. Using Keystone's slide templates, the generation agent would:

- Map outline sections to slide types (title slides, framework slides, data slides, insight/takeaway slides)
- Generate data visualizations from quantitative findings (charts, tables, positioning matrices)
- Apply Keystone's visual identity (fonts, colors, layout rules) via template-driven generation
- Subject each slide to the Evaluator, which would check: Does the chart accurately represent the underlying data? Is the takeaway non-obvious? Would a partner present this without edits?

The Wealth Management Plugin provides the structural template: each deliverable type becomes a skill with defined sections, data requirements, and output formatting. The critical lesson from Prendergast's analysis: the system must be connected to the actual data used in the analysis, not regenerating data at the presentation layer — otherwise the Hallucination Tax applies to every number on every slide.

### 6.2 Excel Model Generation (Layer 3b)

Financial models follow predictable structures within consulting: revenue build-ups, market sizing models, unit economic analyses, scenario analyses. The generation agent would:

- Translate quantitative findings into structured workbook tabs
- Build formulas that reference source data (not hardcoded numbers)
- Generate scenario toggles (base/bull/bear cases informed by the Deliberation phase)
- Apply Keystone's Excel formatting standards

The evaluator for Excel output would verify that formulas resolve correctly, that sensitivities produce reasonable ranges, and that the model's assumptions are explicitly documented — catching the common failure mode where AI-generated spreadsheets look correct but contain circular references or logical errors.

### 6.3 Executive Summary Tailoring

Different audiences need different framings of the same analysis. A PE partner evaluating an acquisition target cares about different dimensions than a corporate strategy officer evaluating organic growth opportunities. The generation layer would support audience-specific tailoring — same underlying research, different narrative emphasis — guided by audience profiles encoded as skills.

---

## 7. What Makes This Extraordinary

This section is for Prof. Youle and for any Keystone partner who's skeptical that an AI tool can produce work worth reviewing. Here's what specific design decisions, grounded in the best available engineering evidence, elevate this beyond what anyone else is building.

### 7.1 Evaluation Quality Bounds Output Quality

Most AI research tools optimize the generation step — better prompts, more data, longer context windows. This system invests disproportionately in the evaluation step, because that's what the evidence says matters most. Carlini spent $20K building a C compiler with 16 agents and concluded that "the test harness is more important than the agent prompt." Anthropic's harness team found that improving evaluation had more impact than improving generation. The Keystone Intelligence Engine is designed around this finding: the evaluator is the most carefully engineered component in the system. Its rubric is calibrated against actual Keystone deliverables. Its quality gates are enforced structurally, not through prompt instructions that drift 40% of the time. A system where evaluation is mediocre produces mediocre output regardless of how good the generator is. A system where evaluation is excellent pulls the generator upward.

### 7.2 It Thinks in Multiple Perspectives Before Concluding

The Deliberation phase is not standard in any AI research tool currently available. Generic tools aggregate findings into a single narrative. This system runs a structured, multi-perspective debate that surfaces where the evidence is strong, where it's contested, and where it's absent — before any conclusions are drawn. This mirrors how the best consulting teams actually work: not by having one person write the answer, but by having the team argue about the answer until the strongest interpretation survives. The confidence map that emerges gives the reader (the partner, the client) exactly what they need: clear conviction on well-supported claims and transparent uncertainty on contested ones. Consultants who present false confidence on uncertain findings destroy credibility. This system is architecturally incapable of that failure mode.

### 7.3 It Gets Better, Measurably, and the Improvement Compounds

The self-improvement loop isn't aspirational — it's designed to produce a quantitative improvement curve that the capstone can report. Round 1: the system scores X on the quality rubric. Round 4: it scores Y. The trajectory is the evidence. What's more, the improvement compounds: every completed project adds to the trajectory store, grows the skills library, refines agent prompts through Darwinian selection, and expands the internal knowledge corpus. The 20th project the system completes will be meaningfully better than the 5th — not because someone manually tuned it, but because the system learned what works. At Keystone scale (potentially hundreds of research projects over years), this compounding transforms a tool into an institutional asset that no competitor can replicate without running the same number of engagements through their own system.

### 7.4 It's a System, Not a Scaffold

Drawing from Prendergast's analysis: most AI tools for professional services are scaffolds — well-structured templates that look impressive but can't pull a single number from an actual data source. The Hallucination Tax (2.5 hours of human verification for 30 seconds of AI generation) makes them net-negative on productivity for any analysis that requires factual accuracy. This system is designed from the ground up as a *system*: connected to real data sources, with structural enforcement of source citation, automated verification of factual claims, and an evaluator that rejects unsourced assertions. Every number in the output is traceable to a source. The human reviewer's job is to evaluate the analysis, not to fact-check the data.

### 7.5 The Research Question IS the Differentiator

Amy Tam's insight — "When anyone can build for free, the differentiator is knowing what's worth building" — reframes the entire capstone. The system's most valuable layer isn't the one that generates slides or formats charts. It's the one that decides *which research questions to ask.* The Initializer's task decomposition, informed by trajectory storage from past projects, encodes Keystone's accumulated judgment about what research directions yield decision-useful insights. Over time, as the trajectory store grows, the system doesn't just research better — it *asks* better. It learns which questions partners actually found valuable, which analyses changed client decisions, which frameworks produced the most actionable output. This is the true competitive moat: not faster research, but *smarter questions.*

### 7.6 The Architecture Is Honest About What's Proven

This project doesn't claim to have solved automated consulting. The research and analysis engine — the core focus — draws on architectural patterns validated by Anthropic's own engineering team in production systems. The evaluator calibration against Keystone deliverables is a proven methodology (few-shot calibration is a standard technique with known performance characteristics). The parallel research fan-out is proven at scale (Carlini ran 16 agents; this system uses 3-5).

What's experimental is clearly marked: the Deliberation phase draws from MiroFish's swarm approach but hasn't been validated specifically for consulting research. The Darwinian prompt evolution produced +22% returns in financial markets but may behave differently in a research quality domain. The self-improvement loop's rate of convergence depends on the quality metric's correlation with human judgment, which will only be established during the capstone's evaluation phase.

This honesty is intentional. A capstone that claims everything works is a capstone that hasn't tested anything. A capstone that identifies exactly what's proven, what's promising, and what needs validation is a capstone that understands the difference between engineering and research — and demonstrates both.

---

## Appendix: Source Attribution

Key design decisions and the specific sources that informed them:

| Decision | Primary Source(s) |
|----------|-------------------|
| Generator/Evaluator separation as core architectural principle | Anthropic *Harness Design* (Rajasekaran); Anthropic *C Compiler* (Carlini) |
| Sprint contracts between structuring and evaluation | Anthropic *Harness Design* (Rajasekaran) |
| JSON-based task tracking over Markdown | Anthropic *Effective Harnesses* (Young) |
| 2-5 agents per coordinator cap | @Khaliqgant, *Let Them Cook* (6 weeks empirical) |
| Just-in-time context loading via Research Index | Anthropic *Context Engineering* (Rajasekaran, Dixon, Ryan, Hadfield) |
| Workflow-level tools over raw API wrappers | Anthropic *Writing Effective Tools* (Aizawa) |
| Structural enforcement over prompt-based quality gates | @jordymaui (*"Your OpenClaw is Ignoring Half Your Instructions"*) |
| Multi-perspective deliberation phase | @k1rallik (MiroFish swarm intelligence) |
| Skills library with three-layer progressive loading | Prendergast analysis of Anthropic Wealth Management Plugin; @mrjain |
| Skill graph with interconnections | @rohit4verse (Ars Contexta) |
| Agent identity (souls) alongside procedural skills | @tolibear_ (*"I Gave My Agents Skills. I Should Have Given Them Souls"*) |
| Darwinian prompt evolution via rolling quality scores | @Chris_Worsey (25-agent financial market system) |
| Autoresearch ratchet as self-improvement paradigm | Karpathy (autoresearch); @Hesamation (56→92% improvement); @zhengyaojiang (community roundup) |
| Instinct→Skill evolution for methodology development | @dunik_7 / affaan-m (everything-claude-code repository instinct system) |
| Trajectory storage as institutional memory | @Khaliqgant (*Let Them Cook*); @christinetyip (autoresearch@home, 34 agents, shared memory) |
| Compound research assets (every project increases system value) | @elvissun (fan-out deep research); @amytam01 (*"When code is free"*) |
| Scaffold vs. System distinction | Prendergast (Wealth Management Plugin analysis); @mrjain |
| File-system-as-state for agent collaboration | @trq212 / Thariq Shihipar (*"Your Agent should use a File System"*; Deep Research Demo) |
| Unified retrieval across public/internal/historical sources | @VadimStrizheus (Supermemory ASMR architecture) |
| Plan-first, verify-after agent loop | @trq212 (*"Gather context → Take action → Verify work"*); @arvidkahl |
| Orchestrator never does substantive work | @johann_sath (CEO pattern); @Khaliqgant (Lead agent role) |
| Encode mistakes into institutional knowledge | Boris Cherny via @startupideaspod (CLAUDE.md as compound engineering) |
| Dual-axis quality scoring (rigor × impact) | @MitcheIl (20-agent pipeline: Invention Novelty × Copy Intensity) |
| Read agent transcripts as primary improvement method | @trq212 (*"The #1 metalearning"*) |
| Multimodal retrieval for diverse source types | @VibeMarketer_ (Gemini Embedding 2 multimodal embeddings) |
| Security by design for quality enforcement | @elvissun (gog CLI architectural security); @JordanLyall |

---

*This plan synthesizes insights from 5 Anthropic engineering articles, 19 high-value X bookmarks, Google's 64-page AI Agents Technical Guide, the everything-claude-code repository (28 agents, 116 skills, 1,421 tests), and John Prendergast's Wealth Management Plugin analysis — representing approximately 180,000 characters of analyzed source material. Every architectural decision traces to a specific, cited source.*
