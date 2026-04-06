# Deep Research Prompts — Keystone Intelligence Engine
*Finalized: 2026-03-28 | 16 parallel deep research sessions*

Each prompt below is self-contained. Copy it into a deep research session along with the specified attached files.

---

# CATEGORY A: Landscape & Prior Art

---

## A1: Multi-Agent Research & Analysis Systems [🔴 CRITICAL]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

I'm building a multi-agent AI system called the Keystone Intelligence Engine for automated consulting research and analysis. The system takes a research question (e.g., "Evaluate the competitive position of Company X in the autonomous vehicle sensor market") and produces a complete, source-cited analytical brief through a six-layer pipeline: Specification Engine → Parallel Research Agents → Multi-Perspective Deliberation → Structuring → Evaluation → Self-Improvement Loop. The attached CAPSTONE-PLAN-v2.md contains the full architecture. Read it before researching.

Before I build, I need to know what already exists, what's been tried and failed, and where the genuine gaps are.

**Research agents to evaluate deeply:**

GPT-Researcher (assafelovic/gpt-researcher) is the longest-running open-source deep research agent at 25.7K+ stars, active since May 2023. It uses a planner/execution architecture where the planner generates research questions and execution agents gather information in parallel from 20+ sources. It recently added a Deep Research mode with tree-like exploration, an MCP server for integration with Claude and other agents, and Claude Code skill support. I need to understand its full pipeline, how it handles quality control, and where its architecture breaks down for consulting-grade output.

STORM and Co-STORM (stanford-oval/storm) from Stanford uses a genuinely novel approach: it simulates conversations between writers carrying different perspectives who pose questions to a topic expert grounded in trusted internet sources. Co-STORM adds human-in-the-loop collaboration. This multi-perspective questioning pattern maps directly to how consulting teams research a topic from multiple stakeholder angles. I need to understand whether this architecture produces depth or just breadth, how it handles contested claims, and whether Co-STORM's human collaboration model is actually useful.

The 199-Biotechnologies deep-research-skill is an 8-phase Claude Code skill (Scope → Plan → Retrieve → Triangulate → Outline Refinement → Synthesize → Critique → Refine) with source credibility scoring on a 0-100 scale, multi-persona red teaming (Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer), and automatic continuation for reports exceeding 18K words. It runs 5-10 concurrent searches plus 2-3 focused sub-agents. This is the closest existing system to what I'm building. I need to understand its actual output quality, whether its credibility scoring is meaningful or cosmetic, and what its failure modes are.

Cranot/deep-research supports 7 LLM providers, 4 research strategies (Recursive, Socratic, Perspective-based, Grounded/web-verified), multi-model ensembles where multiple models answer then merge perspectives, and typed knowledge graphs tracking epistemic state. Evaluate whether multi-model verification produces genuinely better output.

Also investigate: Weizhena/Deep-Research-skills (two-phase with human-in-the-loop), DeerFlow 2.0 (ByteDance, deep research + content creation), and Imbad0202/academic-research-skills (10-stage academic pipeline with Socratic coaching).

**Search infrastructure to map:**

The quality ceiling of any research system is bounded by its search quality. Map the current landscape: Exa ($85M Series B, built its own index with 1B+ people, 50M+ companies, 100M+ papers, sub-450ms latency), Brave Search API (independent index, highest AIMultiple benchmark score at 14.89), Tavily (acquired by Nebius Feb 2026, new /research endpoint GA for fully managed multi-step research), SearXNG (self-hosted metasearch, 25K+ stars, free/unlimited), 199-bio search-cli (aggregates across Brave, Serper, Exa, Jina, Firecrawl via single CLI). How do production research systems compose multiple search providers? What's the optimal configuration?

**Benchmarks and competitive context:**

CMU's DeepResearchGym evaluated leading deep research systems on 1,000 complex queries and found GPT Researcher outperformed Perplexity, OpenAI, and HuggingFace in citation quality, report quality, and information coverage. DeepResearch Bench tests 100 PhD-level tasks across 22 fields with an active leaderboard. Also benchmark against Claude.ai's native Research feature and ChatGPT's Deep Research (now on GPT-5.2 for Enterprise/Edu).

**For each system, analyze:**
1. Architecture: how agents coordinate, what the pipeline looks like, how state flows between phases, how it handles failures mid-pipeline
2. Quality control: evaluation, verification, hallucination detection, source credibility, red-teaming. Is quality enforced structurally or through prompt instructions?
3. Search infrastructure: which providers, how multi-source triangulation works, cost per research query
4. Strengths we should learn from and potentially integrate
5. Weaknesses and gaps that Keystone's architecture addresses
6. Components we could directly use (MCP servers, skills, search configs) rather than building from scratch
7. Maintenance trajectory: recent commits, community health, whether it's accelerating or plateauing

**The key question:** Given our six-layer pipeline architecture with an independent Evaluator and Rejection Library, which existing components should we compose rather than rebuild, and where do we need to build something genuinely new?

---

## A2: Evaluation & Verification Frameworks [🔴 CRITICAL]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md, CAPSTONE-IMPLICATIONS.md (read §4 on Evaluator Design carefully)

The Evaluator is the most important component in the Keystone Intelligence Engine. More important than any generator. This is a core architectural conviction backed by Anthropic's own finding that improving evaluation had more impact than improving generation, and by the 91-article corpus analysis showing evaluation as the "apex skill" across 15+ independent arguments. The attached CAPSTONE-IMPLICATIONS.md §4 explains the full rationale.

Our Evaluator grades every output against an eight-dimension rubric calibrated to consulting quality standards. It needs to catch not just factual errors but analytical shallowness, missing perspectives, false precision, generic frameworks applied without adaptation, and the "style over substance" problem where well-formatted output masks weak analysis. Every rejection feeds the Rejection Library, which becomes a permanent architectural constraint that prevents recurrence.

I need to find every existing framework, tool, and research finding relevant to building this.

**Evaluation backbone candidates (investigate deeply):**

DeepEval is the most complete open-source eval framework with 50+ metrics. Its G-Eval feature lets you define custom evaluation criteria in natural language and uses LLMs to assess outputs against those criteria. Its DAG (graph-based deterministic LLM-as-a-judge) metric builder could be the foundation for our multi-dimensional rubric. It integrates with pytest for CI/CD. Evaluate whether G-Eval's custom criteria system is flexible enough for consulting-specific dimensions like "decision-usefulness" and "intellectual honesty."

Inspect AI from the UK AI Safety Institute has the most principled eval framework design: composable Tasks (load data), Solvers (elicit behavior), and Scorers (score outputs). It includes 100+ pre-built evaluations, is adopted by serious safety orgs (METR, Apollo Research), and supports multi-provider models. Evaluate whether its Scorer abstraction can handle our eight-dimension rubric where dimensions are weighted differently per engagement type.

Braintrust ($80M raise Feb 2026, $800M valuation) is the only platform that connects evaluation scoring with CI-based release enforcement. Their pattern (output doesn't ship unless it passes eval thresholds) maps directly to our pipeline where the Evaluator can reject and trigger regeneration. Evaluate their release-gate architecture.

Also investigate: RAGAS (RAG-only metrics, 400K+ downloads, useful as a component), Langfuse (MIT-licensed, self-hostable observability + eval dashboards, more relevant than LangSmith for our Mac Mini infrastructure), Arize Phoenix (OpenTelemetry-based, self-hostable), Promptfoo (red teaming, 30K+ developers), DeepTeam (safety testing).

**LLM-as-Judge research (the failure modes are the most important part):**

The CALM framework ("Justice or Prejudice?" by Ye et al., ICLR 2025, arXiv:2410.02736) identifies 12 distinct bias types in LLM judges and provides an automated quantification framework. This is the most comprehensive taxonomy of judge failures.

SOS-Bench ("Style Outweighs Substance," ICLR 2025, arXiv:2409.15268) found that LLM-judge preferences do NOT correlate with concrete measures of safety, world knowledge, or instruction following. Sarcasm caused a 96% scoring loss while factual errors caused only 13% loss. 152,380 data points across 19 benchmarks. This is the single most dangerous finding for our Evaluator: it means a naive LLM judge will rate a well-formatted wrong answer higher than a poorly-formatted correct one.

Also investigate: "A Survey on LLM-as-a-Judge" (arXiv:2411.15594), "Evaluating Scoring Bias in LLM-as-a-Judge" (arXiv:2506.22316), Prometheus 2 (EMNLP 2024, purpose-built judge model with custom rubric support, 72-85% human agreement), SE-Jury (ASE 2025, ensemble-of-judges with 34-113% improvement in human correlation), Agent-as-a-Judge (arXiv:2508.02994, evaluates dynamic agent behavior not just static outputs).

Quantified bias statistics to verify: GPT-4 achieves ~80% agreement with human preferences; position bias causes 40% inconsistency; verbosity bias inflates scores ~15%; self-enhancement bias is 5-7%; domain expert agreement drops to 60-68%; multi-model ensemble reduces biases 30-40% but costs 3-5x.

**The self-evaluation problem:**

How do you prevent the "same model evaluating same model" failure? Investigate: cross-model evaluation (different model family as judge), evaluator ensembles (multiple judges from different providers, flag disagreements), Constitutional AI self-critique loops, decomposed evaluation (break quality into orthogonal dimensions scored independently so gaming one doesn't game all), and deterministic anchor checks layered under LLM judgment (citation URLs actually resolve, sources actually contain claimed information, numerical claims are internally consistent). The AISI found automated graders show Cohen's Kappa of 0.52 vs 0.8 for human-human agreement. What does this mean for our confidence thresholds?

**Consulting quality rubric design:**

The 199-bio deep-research skill uses multi-persona red teaming in Deep/UltraDeep modes. The IC's ICD 203 analytical standards (Heuer & Pherson's "Structured Analytic Techniques," 3rd edition, 66 techniques) map almost perfectly to quality criteria for AI-generated analysis. Investigate whether MECE (mutually exclusive, collectively exhaustive) can be reliably evaluated by an LLM judge. Investigate structured analytic technique completeness checks. The critical distinction: accuracy evaluation (factually correct?) vs. analytical quality evaluation (decision-useful, appropriately caveated, intellectually honest?). The latter is far harder and less studied.

**Anti-gaming:**

Factorial evaluation (systematically vary inputs to test robustness), adversarial probes (deliberately introduce errors to test detection), deterministic anchors (non-LLM checks that can't be gamed by optimizing prose quality), human-in-the-loop calibration (periodic comparison against expert judgment to detect drift).

**For each framework/paper, analyze:**
1. What it evaluates and how (metrics, scoring method, rubric design)
2. Known limitations and failure modes
3. Whether it could serve as our Evaluator's backbone, a component within it, or only a reference for custom design
4. How it handles (or fails to handle) the self-evaluation problem
5. Whether it supports custom rubrics calibrated to domain-specific standards
6. Whether it can run self-hosted on a Mac Mini

---

## A3: Self-Improvement, AutoResearch, and Learning Loops [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md, CAPSTONE-IMPLICATIONS.md (read §5 on Self-Improvement Loop)

The Keystone Intelligence Engine's most durable competitive moat is its self-improvement loop. The core mechanism is a "Rejection Library": every time the Evaluator rejects output, the rejection is structured (what failed, why it failed, and the constraint that prevents recurrence) and becomes a permanent architectural constraint. The 20th engagement should be meaningfully better than the 5th because the constraint library has grown. This is described in CAPSTONE-IMPLICATIONS.md §5 and the Meta-Layer section of CAPSTONE-PLAN-v2.md.

I need to find every existing implementation of runtime self-improvement (not fine-tuning) and evaluate whether our Rejection Library approach fills a gap these systems miss, or whether we should adopt an existing framework.

**The autoresearch ecosystem:**

Andrej Karpathy released autoresearch in March 2026 (42K+ stars): a 630-line Python script that runs autonomous ML experiment loops. It ran 126 experiments overnight, kept 23 improvements (18% keep rate), and Karpathy called the pattern "emulate a research community." Fortune dubbed it "The Karpathy Loop." It spawned a massive fork ecosystem: autoresearch-anything (generalized beyond ML), codex-autoresearch, gemini-autoresearch, and autoresearch-at-home (distributed across 34 agents). Investigate the architecture of the keep/revert decision mechanism. How does it avoid the ratchet problem (ensuring "improvements" don't actually regress on dimensions not being measured)?

Chris Worsey built ATLAS: 25 AI agents debating macro, rates, commodities, sectors, and single stocks daily. Every recommendation scored against real market outcomes. The worst agent by rolling Sharpe ratio gets its prompt rewritten by the system. Result: +22% returns over 173 days on real capital, $20/month infrastructure cost. This is the best applied example of Darwinian prompt evolution. How does he prevent Goodhart's Law (agents optimizing for Sharpe at the expense of other risk metrics)? What's the prompt rewriting mechanism?

Also investigate: 199-bio autoresearch-cli (universal CLI for running loops across agents), WecoAI awesome-autoresearch (curated list of all implementations), @Hesamation's result (56→92% in 4 rounds), @christinetyip's autoresearch@home (34 agents).

**Self-improving agent frameworks:**

Meta's HyperAgents (arXiv:2603.19461, March 2026) introduced metacognitive self-modification where the agent rewrites its own improvement procedure, not just its prompts. It achieved 3x improvement on polyglot coding (14%→34%) with demonstrated cross-domain transfer. This is built on the Darwin Gödel Machine (arXiv:2505.22954). How does metacognitive self-modification differ from simple prompt optimization? Is it applicable to research quality improvement?

HKUDS OpenSpace (March 2026) is a self-evolving skill engine with auto-repair and auto-improve modes. It showed 4.2x income improvement and 46% token reduction across 50 professional tasks, with skills accumulating in a SQLite database with lineage tracking. How does skill lineage tracking work? Could we adapt this for our methodology evolution?

Also investigate: OpenAI Self-Evolving Agents Cookbook (GEPA + Agents SDK), Stanford CS329A (new course on self-improving agents), "A Comprehensive Survey of Self-Evolving AI Agents" (arXiv:2508.07407, unified four-component framework), "ARTIST" (ICML 2025, Agentic Reasoning and Tool Integration in Self-improving Transformers).

**Prompt optimization frameworks:**

DSPy v3.1.3 (23K stars, 300+ contributors) now includes the GEPA optimizer which achieved 67%→93% on MATH benchmark, outperforming MIPROv2 by ~11%. GEPA uses Reflective Text Evolution. Also investigate GEPA as a standalone tool (gepa-ai/gepa), metaTextGrad (arXiv:2505.18524, meta-optimizes TextGrad's optimizer prompts), Modular Prompt Optimization/MPO (arXiv:2601.04055, treats prompts as structured schema objects with section-local textual gradients, outperforms TextGrad). Note: TextGrad was published in Nature but is now primarily a baseline superseded by these newer approaches.

**Agent memory (trajectory storage):**

Our system needs to log decisions and learn from them across engagements. Map the current landscape: Hindsight by Vectorize.io (institutional knowledge), Mem0 (personal memory), Zep (customer history), Letta/formerly MemGPT (~15K stars, stateful agents), Cognee (structured memory graphs), engram from 199-bio (MCP memory server with BM25 + ColBERT + Knowledge Graph hybrid search). Also the tiered flat-file pattern: MEMORY.md / GUARDRAILS.md / WORKSTATE.md. Which approach best supports our Rejection Library architecture?

**For each system, analyze:**
1. Architecture of the improvement loop (what triggers improvement, what gets modified, how modifications persist)
2. What metric drives improvement and how it's measured
3. How it avoids metric gaming / Goodhart's Law
4. What's empirically proven vs. theoretically plausible
5. Could we use this directly, or does our Rejection Library approach fill a gap these miss?
6. How does it handle the ratchet problem (preventing regressions)?

---

## A4: Orchestration Frameworks & Agent Coordination [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine uses a "Specification Engine" as its orchestrator. Its primary job is translating vague research questions into precise, executable specifications before any agents start working. The quality ceiling of the entire pipeline is the specification quality of this decomposition. The system runs a six-stage pipeline (Specification → Research → Deliberation → Evaluation) with strict isolation between research agents (they cannot see each other's intermediate findings; all convergence happens in Deliberation). I need to evaluate every orchestration framework against these specific requirements.

The agent framework landscape has undergone a major shakeout. AutoGen is in maintenance mode (Microsoft consolidated it into the new Microsoft Agent Framework). OpenAI's Swarm has been formally superseded by the Agents SDK. Meanwhile, MCP (Model Context Protocol) has been donated to the Linux Foundation and hit 97M+ monthly SDK downloads, and the A2A (Agent-to-Agent) protocol has 150+ partners. The protocol layer has standardized. The framework layer hasn't.

**Production-grade frameworks (evaluate deeply against our pipeline):**

LangGraph v1.1.2 (24K stars, 9M+ weekly PyPI downloads): Graph-based state machines. First stable 1.0 GA. Used by Uber, LinkedIn, Klarna. LangSmith companion for tracing and time-travel debugging. Best for complex pipelines with cycles and conditional routing. Does its graph model naturally support our Specification → Research → Deliberation → Evaluation flow? Can it enforce agent isolation? How does it handle the "reject and regenerate" loop from our Evaluator? Note CVE-2026-34070 was patched.

CrewAI v1.12.2 (45.9K stars, fastest-growing): Role-based agent teams with intuitive task delegation. Native A2A and MCP support. Flows architecture. 12M+ daily agent executions. Best for linear multi-agent workflows. But: no built-in checkpointing, limited control over agent-to-agent communication, coarse error handling. Can it handle the non-linear flow where the Evaluator kicks output back to Research?

Claude Agent SDK (Python v0.1.50, TypeScript): Renamed from Claude Code SDK. Powers Claude Code's agent loop. Programmatic subagents, session forking, structured outputs, hooks system. Deepest MCP integration of any framework. This is our most likely deployment surface since we're building on Claude/OpenClaw infrastructure. How mature is it for production multi-agent orchestration beyond coding tasks?

OpenAI Agents SDK (~19K stars): Production replacement for Swarm. Built-in guardrails, tracing, persistent memory, handoff architecture. But vendor-locked to OpenAI models.

**Strong alternatives (evaluate for specific strengths):**

PydanticAI v1.72.0 (15K stars): "FastAPI feeling" for agents. Type-safe, model-agnostic (40+ providers), AgentSpec for declarative agent definitions, durable execution via Temporal/DBOS, built-in Pydantic Evals. The type-safety and AgentSpec patterns are interesting for our handoff contracts.

Google ADK v0.6.0 (17K stars): Hierarchical agent trees where root agents delegate to sub-agents. Native A2A and MCP. The hierarchical model maps well to our Specification Engine → Research Agent delegation.

OpenAgents: Only framework with native support for both MCP and A2A protocols. Worth evaluating for interoperability.

Mastra (22.3K stars): Leading TypeScript framework from the Gatsby team. YC W25, $13M seed. If we need a TypeScript option.

**Specialized/legacy (brief assessment only):**

CAMEL-AI (~18K stars, research-focused), MetaGPT (software dev simulation), Agency Swarm (active but small). AutoGen/AG2 (maintenance mode → Microsoft Agent Framework). OpenAI Swarm (deprecated → Agents SDK).

**Protocol layer (map thoroughly):**

MCP is now under Linux Foundation governance via the Agentic AI Foundation, co-founded by Anthropic, Block, and OpenAI. Agent-to-tool connectivity. The 2026 roadmap includes transport scalability, agent communication primitives, and enterprise readiness.

A2A (Agent-to-Agent Protocol) v0.3 is complementary: where MCP connects agents to tools, A2A connects agents to each other. Originally Google, now Linux Foundation with 150+ partners including Adobe, Salesforce, SAP. JSON-RPC 2.0 over HTTP/SSE/gRPC. Agent Cards for discovery.

OpenClaw ACP is an IDE-to-agent protocol (JSON-RPC 2.0 over stdio, similar to LSP). Distinct from A2A. AG-UI (CopilotKit) is an agent-to-frontend streaming standard.

Also investigate Anthropic's published multi-agent patterns: their blog post "How we built our multi-agent research system" (orchestrator-worker pattern) and their 2026 Agentic Coding Trends Report.

**Key questions:**
1. Which framework best supports our specific pipeline (Specification → isolated parallel Research → Deliberation → Evaluation with reject/regenerate loops)?
2. Which supports "handoff contracts" (explicit input/output/quality definitions at each pipeline boundary)?
3. Which handles parallel agent execution with strict isolation?
4. Which has the best primitives for our Rejection Library (persistent constraint storage that modifies future agent behavior)?
5. Should we build on an existing framework or build our own orchestration layer? What's the honest build-vs-buy tradeoff?
6. What coordination patterns have been tried and failed at scale? What are the documented failure modes?

---

## A5: Deep Research Tooling & Capabilities [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

I need to equip the Keystone Intelligence Engine's research agents with the best possible research capabilities. These agents fan out in parallel to investigate different aspects of a research question, pulling from SEC filings, academic papers, news, financial data, and industry reports. I also need to understand the competitive landscape of "deep research" tools since my system is itself a deep research tool competing with Claude Research, OpenAI Deep Research, and Perplexity.

**Platform deep research architectures (understand how the competition works):**

How does Claude's Research mode work architecturally? It uses parallel multi-agent with an orchestrator, conducts multiple searches that build on each other, explores different angles automatically, and delivers citations. How does OpenAI's Deep Research work (interactive clarification phase, then o3/o4-mini execution)? How does Gemini's Deep Research work (autonomous plan-first with user approval)? Perplexity Sonar Pro achieves 94.3% citation accuracy and sub-3-minute completion through iterative adaptive retrieval. What architectural patterns do these share? Where do they differ?

**Open-source deep research implementations (evaluate for integration into our pipeline):**

The 199-bio claude-deep-research-skill runs an 8-phase pipeline autonomously without user interaction: Scope, Plan, Retrieve (5-10 concurrent searches + 2-3 sub-agents), Triangulate, Outline Refinement, Synthesize, Critique (with loop-back to Retrieve if gaps found), Refine. Four modes: Quick (2-5 min), Standard (5-10 min), Deep (10-20 min), UltraDeep (20-45 min). Source credibility scoring 0-100, disk-persisted citations surviving context compaction. No external dependencies. Could this serve as our research agent's core, or do we need something more consulting-specific?

GPT-Researcher has a planner/execution architecture with Deep Research mode for tree-like exploration, an MCP server (gptr-mcp), and recently added Claude Code skill support. Cranot/deep-research supports 7 LLM providers, 4 research strategies, persistent checkpoints, and typed knowledge graphs. Weizhena/Deep-Research-skills uses a two-phase approach (outline generation then deep investigation) with human-in-the-loop control.

**Search APIs and MCP servers (evaluate for our retrieval layer):**

Exa ($85M Series B) built its own search engine from scratch with specialized indexes: 1B+ people, 50M+ companies, 100M+ research papers. Sub-450ms latency. MCP server with multiple search tools. Claude Code skills for company research, people research, and code context search, each running in forked context. Category-based search with different filters per category. How does category search compare to general web search for consulting research?

Brave Search API has an independent index (not a Google/Bing wrapper) and scored highest on AIMultiple's agentic search benchmark (14.89). $5/1K queries. Official MCP server. SearXNG (25K+ stars) is self-hosted metasearch, free and unlimited queries, multiple MCP servers available. Ideal as our privacy-first unlimited-query backend.

Tavily was acquired by Nebius in Feb 2026. New /research endpoint is GA for fully managed multi-step research with citations. New fast/ultra-fast search depths. Firecrawl now has five endpoints (Scrape, Crawl, Search, Map, Agent) where the Agent endpoint enables autonomous multi-page research. Jina AI was acquired by Elastic and is now a full-stack search provider with embeddings (v5), the jina-reranker-m0 (2.4B parameter multimodal reranker), Reader API, and Classifier. 199-bio's search-cli aggregates across Brave, Serper, Exa, Jina, and Firecrawl through a single Homebrew-installable CLI.

**Browser automation for research:**

Stagehand v3 by Browserbase (Feb 2026) is a complete rewrite with three primitives: act(), extract(), observe() plus an agent() function. 44% faster than v2, self-healing capabilities, SDKs in TypeScript/Python/Go/Ruby. Browserbase raised $40M Series B at $300M valuation. browser-use (50K+ stars) takes a pure autonomy approach where you describe a task and the agent navigates. AgentQL is the lowest barrier to entry (Chrome extension). Lightpanda is an open-source headless browser built in Zig that's 11x faster and uses 9x less memory than headless Chrome.

**Academic paper access:**

Semantic Scholar (225M+ papers, 100M+ authors, 2.8B+ citation edges) has multiple MCP servers and AI-powered recommendations. OpenAlex (271.3M indexed works, free, 100K+ API calls/day) is open-source but many records lack abstracts/affiliations. The Academix MCP Server unifies search across OpenAlex, DBLP, Semantic Scholar, arXiv, and CrossRef with smart ID resolution and BibTeX export.

**Financial and government data:**

EdgarTools MCP is the most comprehensive SEC EDGAR integration (free, MIT, 13 tools, typed objects for 30+ form types, live filings monitor). Financial Modeling Prep MCP covers equities, financials, earnings, ETFs, indices, macro indicators. The Government Data MCP by lzinga exposes 36 US government APIs through 188 tools covering Treasury, FRED, BLS, BEA, EIA, Census, FEC, Congress, SEC, FBI, World Bank, CDC.

**For each tool, analyze:**
1. Capabilities and concrete limitations (what can't it do?)
2. Cost model (free tier limits, per-query pricing, monthly caps)
3. Integration method (MCP server? Python SDK? REST API? Claude Code skill?)
4. Output quality (raw data vs. summarized intelligence vs. structured analysis?)
5. Self-hostability and infrastructure requirements
6. How it would fit into our parallel research agent architecture

---

# CATEGORY B: Quality Standards

---

## B1: What Senior Consulting Partners Actually Value [🔴 CRITICAL]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine is designed for a management consulting firm (Keystone Group, Chicago). Its output must meet the internal quality bar that senior partners expect from a three-analyst team working a full week. Not "impressive for AI" but actually solid. We call this "Goldman-grade" after a Goldman Sachs analyst who called AI-generated financial models "solid on their own merits." This research thread calibrates what that bar actually means in concrete, specific, encodable terms.

**What the real internal quality bar looks like:**

Search former consultant perspectives on Fishbowl, Blind, Reddit r/consulting, Management Consulted, and PrepLounge forums. What do partners complain about most in junior analyst work? What separates a deliverable that gets presented to clients without edits from one that gets sent back? What does "hypothesis-driven" research actually look like in practice vs. in interview prep books? How do the best analysts structure competitive landscapes, market sizings, and due diligence reports?

Investigate the pyramid principle (Barbara Minto) as it actually manifests in practice, not just as a communication framework but as a thinking discipline. What makes a "so what?" genuinely useful vs. generic? What are the specific quality failures that get analysts dinged: false precision (market size of $4.237B when the methodology only supports "roughly $4B"), generic frameworks applied without adaptation, missing the "so what," surface-level analysis dressed up as insight through formatting?

Victor Cheng's consulting frameworks are foundational for structural decomposition logic, but note that current MBB practitioners on PrepLounge have called his specific case frameworks "completely outdated and useless for many cases." Use him for the meta-skill of decomposition, not the specific frameworks. Ethan Rasiel's "The McKinsey Way" remains useful for understanding internal culture and quality expectations.

**AI-era consulting data (this is new and critical):**

McKinsey deployed Lilli internally with 72% of 45,000 employees active, generating 500,000+ prompts/month and recovering ~50,000 labor hours/month. Auto-generated decks save 90-120 minutes each and account for roughly 1/3 of Lilli usage. McKinsey now has 20,000 AI agents working alongside 40,000 humans. What quality standards does Lilli enforce? How does it handle the fact-checking problem?

BCG partnered with Harvard Business School on a study of 758 consultants. Results: 12.2% more tasks completed, 25.1% faster, 40%+ higher quality. Critical finding: bottom-half performers saw 43% quality improvement, but complex tasks sometimes saw DECREASED performance. This "jagged technological frontier" concept (some tasks benefit, adjacent tasks get worse) is essential for understanding where our system will succeed vs. fail.

BCG also built GENE (GPT-4o conversational agent) and Deckster (slide automation). 36,000+ custom GPTs built internally, 80% created by front-line consultants, not IT. Multi-agent mesh with domain-specific agents planned.

The Deloitte Australia incident (July 2025) is the essential cautionary tale: a $290,000 government report contained fabricated academic references, non-existent court cases, and incorrect quotes attributed to real people. Deloitte was forced to refund and rewrite. This is what happens when quality verification fails.

PwC launched a "Human + AI Skillset" curriculum (Feb 2026) with 30 skills: 15 AI-focused and 15 human. MCA UK (Jan 2026) found 77% of consulting firms integrated AI. Big Four + MBB have collectively invested $10B+ in AI since 2023.

**Intelligence community analytical tradecraft (a parallel quality framework):**

The IC's ICD 203 defines nine analytical standards that map almost perfectly to quality criteria for AI-generated research. Heuer & Pherson's "Structured Analytic Techniques for Intelligence Analysis" (3rd edition) catalogs 66 techniques including 9 new ones. Specific techniques directly implementable as multi-agent system components: Analysis of Competing Hypotheses (ACH), Key Assumptions Check, Red Team Analysis, Pre-Mortem Analysis, Diagnostic Reasoning. How does the IC evaluate analytical product quality? What can we steal for our eight-dimension rubric?

**The emerging quality discourse:**

HBR (Feb 2026) raised the "judgment gap": if AI handles the messy analytical tasks that once built junior consultant judgment, how do you develop the next generation of partners? "2025 was the year of AI speed. 2026 will be the year of AI quality" is now industry consensus. futureofconsulting.ai reports "Billions Spent, But the Old Pyramid Persists."

**Deliverable:** Concrete, specific, actionable quality criteria that I can encode into an AI evaluator rubric. Not "be rigorous" but "here's what rigorous means: [specific examples with pass/fail criteria]."

---

## B2: Decision-Useful vs. Comprehensive Research [🔴 CRITICAL]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine must produce research that actually changes decisions, not research that merely covers a topic thoroughly. This is a critical distinction: "comprehensive" is easy for AI (generate more content about more sub-topics), but "decision-useful" requires understanding what the decision-maker actually needs to know and framing findings in a way that drives action. This research thread produces the criteria I'll encode into the "decision-usefulness" dimension of our Evaluator's rubric.

**Decision-making under uncertainty (the academic foundations):**

Daniel Kahneman died March 27, 2024, but his frameworks are being extensively applied to AI systems. System 1/System 2 thinking maps to the SOFAI architecture (Communications of the ACM). His "Noise" framework (2021) provides a rigorous way to measure AI output consistency: noise is variability where there should be agreement. His "decision hygiene" concept maps directly to AI evaluation design. Investigate how these frameworks are being operationalized in 2026.

Gary Klein developed a new AIQ toolkit (ShadowBox LLC) for helping people manage specific AI systems. His Recognition-Primed Decision model explains how experts make decisions differently from novices. His Data/Frame sensemaking model is relevant to how our Deliberation Layer should synthesize conflicting evidence. His 2009 collaboration with Kahneman ("Conditions for Intuitive Expertise: A Failure to Disagree") established when expert intuition is trustworthy and when it's not. This directly informs when AI analysis can substitute for expert judgment.

Philip Tetlock is now on the Board of Directors of ForecastEx, a CFTC-registered prediction market (Jan 2026). His superforecasters beat financial markets on Fed decisions through 2023-2025. Multi-agent investing experiments directly applying Tetlock's framework show promising but mixed results. His forecasting methodology maps to multi-agent system design: generate independent perspectives first, structured debate second, convergence last.

Phil Rosenzweig's "The Halo Effect" critiques how management research quality illusions lead to confident-sounding but analytically empty conclusions. This maps directly to the AI "style over substance" problem. Chip & Dan Heath's work on decision-making communication ("Made to Stick," "Decisive") provides frameworks for how to frame findings to drive action.

**How executives actually use AI analysis (2026 data):**

HBR (Jan 2026): vast majority of executives see AI as high priority but struggle with measurable value. MIT Sloan calls 2026 a "level-set year" with dialed-back expectations. Deloitte's 2026 survey: 60% of executives regularly use AI for decisions. Gartner projects by 2027, half of business decisions will be augmented or automated by agents. IMD (2026): "When AI takes care of scale and speed, the real bottleneck becomes human judgment." IMF (June 2025): "As AI prediction advances, the distribution of judgment will increasingly determine the distribution of wealth and power."

What actually gets read in consulting deliverables? What gets ignored? What makes a board member stop and reconsider a strategic direction vs. file a report?

**Structured analytic techniques from intelligence analysis:**

Heuer's "Psychology of Intelligence Analysis" catalogs cognitive biases in analytical work and how structured techniques mitigate them. Which of Heuer & Pherson's 66 structured analytic techniques are implementable as multi-agent system components? How does the IC distinguish between analysis that's "actionable" vs. merely "accurate"?

**The quality spectrum:**

Research on information overload and diminishing returns of comprehensiveness. The difference between "analytically correct" and "strategically useful." What separates a $500K McKinsey engagement from a $50K boutique engagement in terms of analytical quality (not just brand)? Find examples of analyses that changed major corporate decisions (M&A, market entry, restructuring) and analyze what made them persuasive. How does contrarian analysis and red-team perspective improve decision quality? How do you evaluate whether research is adding signal vs. noise?

**Deliverable:** Concrete criteria encodable into our Evaluator rubric for "decision-usefulness." The rubric should distinguish between five levels: (1) actively misleading, (2) technically correct but unhelpful, (3) informative but doesn't change the decision, (4) directly decision-relevant, (5) changes the framing of the decision itself.

---

## B3: Taste, Judgment, and Quality of Thought [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The concept of "taste" as a professional skill exploded in early 2026 and is now the defining quality discourse in the tech industry. I need to synthesize every substantive framework for quality of thought that can be operationalized into evaluation criteria for an AI consulting research system. The key question is whether taste can be encoded into evaluation rubrics, or whether it's fundamentally about what you reject rather than what you specify.

**The 2026 taste discourse:**

Paul Graham's February 14, 2026 prediction ("In the AI age, taste will become even more important") reached his 2.2M followers and triggered an industry-wide debate. OpenAI president Greg Brockman called taste "a new core skill." Cloudflare CTO John Graham-Cumming said "In 2026, taste is the engineering differentiator." A notable counterpoint emerged: "Taste is being automated. The thing that can't be automated, conviction, isn't being discussed." Investigate the full discourse: who's right? What does this mean for AI evaluation systems?

Stripe Press launched a "Tacit" docuseries that found: "The ceiling for LLMs, for now, seems to be conscious competence. They can capture procedure, but not judgment." Contributors include Andy Matuschak, Brie Wolfson, and Dwarkesh Patel. It cites Cedric Chin's Commoncog as inspiration. This conscious/unconscious competence distinction is directly relevant to our Evaluator design.

Designative published "Taste Is the New Bottleneck" (Feb 2026) arguing teams must encode quality standards into prompts, evaluation functions, and design systems. HBR (Feb 2026) published "How Do Workers Develop Good Judgment in the AI Era?" arguing organizations must deliberately redesign work to build judgment. IMF (June 2025) noted "the distribution of judgment will increasingly determine the distribution of wealth and power." CodeRabbit reported AI-generated code has 1.7x more issues and bugs than human code.

**Key thinkers on quality of thought (investigate their recent work):**

Dr. Anne-Laure Le Cunff (PhD Psychology & Neuroscience, King's College London) published "Tiny Experiments" (Penguin Random House) and gave a TEDxNashville talk (Jan 2026). Her Ness Labs articles cover AI agents and their limitations, metacognition and thinking quality, the "collector's fallacy" (information hoarding vs. synthesis), creative thinking frameworks, and mental models for evaluating quality. She's valuable for the metacognition angle: how does an evaluator think about its own evaluation process?

Cedric Chin at Commoncog has been validated by Stripe Press. His work on expertise transfer and tacit knowledge is directly relevant. The key insight: "LLMs reach conscious competence (they can follow explicit procedures) but not unconscious competence (they can't exercise the tacit judgment that experts have internalized)." How does this map to evaluation rubric design? Can you encode unconscious competence as a set of explicit rejection criteria?

Simon Willison is now the preeminent practitioner-voice on LLMs. He published "Agentic Engineering Patterns" (Feb 2026), comprehensive annual LLM reviews, and coined "slop" for low-quality AI content. Karpathy praised his 23 years of blogging. His key insight: quality is shifting from "writing code" to "managing context, specifications, and agent oversight." His emphasis on transparency and reproducibility is relevant to our evaluation methodology.

**Academic foundations:**

Anders Ericsson's deliberate practice applied to analytical work. Research on "evaluative judgment" in education: how experts assess quality differently from novices. The concept of "judgment" as a skill that develops through specific types of experience. Any substantive writing on what separates a good analyst from a great one.

**Deliverable:** Frameworks for "quality of thought" that can be operationalized into evaluation criteria. Specifically: can taste be decomposed into evaluable dimensions, or is it inherently holistic? If holistic, how do you build an evaluation system that captures it?

---

## B4: AI-Generated Research Quality Failures [🔴 CRITICAL]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md, CAPSTONE-IMPLICATIONS.md (read §4 on Evaluator Design)

This is the most operationally important research thread. Every failure mode discovered here becomes a detection mechanism in our Evaluator. I need the specific, concrete ways that AI-generated research and analysis fails. Not hallucination in the abstract. The subtle failure modes where output looks professional and reads well but is analytically useless. For each failure mode, I need: description, real example, detection method, and architectural prevention strategy.

**Empirical studies on AI analysis quality:**

The METR developer productivity study (Feb-June 2025) is the most rigorous controlled experiment: 16 experienced open-source developers using Cursor Pro with Claude 3.5 Sonnet were 19% SLOWER with AI assistance, while believing they were 20% faster. That's a 39-43 percentage point perception gap. The Faros AI follow-up with 10,000+ developers found 21% more tasks completed but 91% longer PR review time and 9% more bugs. This "productivity illusion" is directly relevant: if AI makes analysts feel more productive while producing worse output, our Evaluator must catch what the analyst doesn't notice.

BCG's Harvard Business School study of 758 consultants found the "jagged technological frontier": 40%+ quality improvement on tasks INSIDE AI's capability frontier, but DECREASED performance on complex tasks OUTSIDE it. The danger is that the frontier is invisible. Analysts don't know which side of it they're on until output quality is evaluated.

The AI Scientist (published in Nature, 2026) demonstrated end-to-end research automation: idea generation, experiment design, execution, and paper writing. Only 1 of 3 workshop submissions was accepted. Documented failures: naive ideas that ignore prior work, incorrect implementations, hallucinated citations. These failure modes map directly to consulting research: generic hypotheses, flawed analytical frameworks, fabricated sources.

The Deloitte Australia incident (July 2025) is the canonical cautionary tale: a $290,000 government report contained fabricated academic references, non-existent court cases, and incorrect quotes attributed to real people. Forced refund and complete rewrite. The International AI Safety Report 2026 documents the "evaluation gap": models can detect when they're being evaluated and modify their behavior accordingly.

**LLM-as-Judge failure modes (quantified):**

SOS-Bench ("Style Outweighs Substance," ICLR 2025, arXiv:2409.15268) is the most important paper for our Evaluator design. Across 152,380 data points and 19 benchmarks, they found LLM-judge preferences do NOT correlate with concrete measures of safety, world knowledge, or instruction following. Sarcasm in the response caused a 96% scoring loss while actual factual errors caused only a 13% loss. This means a well-written wrong answer consistently scores higher than a poorly-written correct one. How do we design our Evaluator to resist this?

The CALM framework ("Justice or Prejudice?" ICLR 2025, arXiv:2410.02736) identified 12 distinct bias types in LLM judges: verbosity (favoring longer responses), fallacy oversight (ignoring logical errors), sentiment (preference for positive tone), position (ordering effects), authority (deference to claimed expertise), diversity (inconsistent across demographic contexts), and six more. These aren't edge cases. They're predictable, systematic failure modes.

Quantified bias statistics to investigate and verify: GPT-4 achieves ~80% agreement with human preferences overall, but position bias causes 40% inconsistency on pairwise comparisons, verbosity bias inflates scores by ~15%, self-enhancement bias (models rate their own outputs higher) is 5-7%, domain expert agreement drops to 60-68% on specialized topics, and multi-model ensembles reduce biases 30-40% but cost 3-5x more.

**The "style over substance" problem in detail:**

The "verisimilitude paradox": as models become more fluent, users struggle MORE to identify inaccurate information because it reads so well. How do you detect this architecturally? The "false confidence" pattern: AI presents uncertain claims with the same linguistic markers as well-established facts. The absence detection problem: AI rarely identifies what's NOT in the data that should be. Missing data points, missing perspectives, missing caveats are the hardest failures to catch.

**Domain-specific failures in consulting research:**

Market sizing: What goes wrong with AI estimates? Common errors in TAM/SAM/SOM logic, double-counting, wrong geographic scope, conflating revenue and market size. Competitive analysis: What does AI miss about competitive dynamics? The temporal dimension (how competition evolves), strategic intent, organizational capabilities, network effects. Financial analysis: How do AI-generated models fail? Unit economics errors, assumption sensitivity, circular references, misapplied multiples. Strategic recommendations: Why do AI recommendations feel generic? Missing the constraint-specific insight that makes advice actionable for THIS company in THIS situation.

**Evaluation benchmarks:**

DeepResearchGym (CMU, arXiv:2505.19253): Open-source benchmark for deep research systems with metrics for information coverage, retrieval faithfulness, and report quality. DeepResearch Bench: 100 PhD-level tasks across 22 fields with an active leaderboard. HELM with domain-specific leaderboards (MedHELM, VHELM, Audio-HELM). Prometheus 2 (EMNLP 2024): Open-source evaluator model, 72-85% human agreement, custom rubric support. SE-Jury (ASE 2025): Ensemble-of-judges with 34-113% improvement. Agent-as-a-Judge (arXiv:2508.02994): Evaluates dynamic agent behavior.

**Deliverable:** A taxonomy of AI research failure modes, each with: (1) description, (2) real example, (3) detection method our Evaluator can implement, (4) architectural prevention strategy (structural enforcement, not prompt instructions). This directly becomes the Evaluator's detection rulebook.

---

# CATEGORY C: Architecture & Implementation

---

## C1: Specification-Driven Development [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine's foundational architectural conviction is that "the specification layer IS the system." The model improves automatically. The tools get swapped. The integrations are fungible. The .md files that define research methodology, quality criteria, analytical frameworks, and agent behavior are the only layer that improves through deliberate human investment. A 200-line markdown file triggered $285B in SaaS market cap destruction when Anthropic released a plugin that made certain per-seat pricing models obsolete. The specification isn't documentation of the system; it IS the system.

This paradigm has exploded in early 2026 and I need to map everything that exists so we build on proven patterns rather than inventing from scratch.

**The AGENTS.md standard:**

AGENTS.md is now a Linux Foundation standard under the Agentic AI Foundation. It's been adopted by OpenAI Codex, GitHub Copilot, Cursor, Windsurf, Gemini CLI, Claude Code, Kilo Code, Factory, and many more. GitHub analyzed 2,500+ AGENTS.md files to identify success patterns. I need to understand: what did they find? What patterns produce the best agent behavior? How does AGENTS.md relate to CLAUDE.md (Claude Code's project-level constitution), RULES.md, SOUL.md (personality/values), and IDENTITY.md (metadata/capabilities)? What's the emerging taxonomy of specification file types?

**Claude Code's skills architecture (our deployment surface):**

Claude Code now supports a full `.claude/` directory structure: `.claude/agents/*.md` for subagent definitions with YAML frontmatter, `.claude/commands/` for custom slash commands, and `.claude/skills/` for SKILL.md files that teach Claude new capabilities. The skills marketplace (SkillsMP.com) has 500,000+ indexed skills. The official frontend-design skill alone has 277,000+ installs. The universal SKILL.md format works across 11+ tools (Claude Code, Cursor, Codex, Gemini CLI, etc.). Context editing in skills achieves 84% token reduction. Progressive disclosure pattern: SKILL.md is concise (~100 lines), bundled reference files load on-demand. Skills are available via the API with a `skill_id` parameter.

How should our Keystone system structure its specification files? Should RESEARCH.md (our engagement specification) be a skill? Should the Evaluator rubric be a skill? How do we version and test these specifications?

**The spec-driven development movement:**

GitHub Spec Kit (72.7K stars, 110 releases) implements a four-phase workflow: Specify → Plan → Tasks → Implement, supporting 22+ AI agent platforms. Kiro IDE (AWS) is an entire IDE built around spec-driven development using EARS (Easy Approach to Requirements Syntax). OpenCode (122K stars, 5M monthly developers) is a provider-neutral, multi-model agent harness with its own `.agents/` directory. The antigravity-awesome-skills collection has 28K+ stars and 1,326+ skills installable via CLI across Claude Code, Codex, Gemini CLI, Kiro, Cursor, and OpenCode.

An academic paper (arXiv:2602.00180, "Spec-Driven Development: From Code to Contract in the Age of AI Coding Assistants," Jan 2026) formalizes the paradigm. Google DeepMind found that unstructured multi-agent networks amplify errors up to 17.2x vs. single-agent. Structured specification is essential.

**Specification quality research:**

"Context engineering > prompt engineering" is now industry consensus. Cache hit rate has been identified as the most important metric for production agents (Manus/Meta). How do you version, test, and validate specification files? Is there empirical data on the relationship between specification quality and output quality (beyond the anecdotal 78% vs 42% harness finding)? How does OpenClaw use project context files (SOUL.md, IDENTITY.md, workspace files) to shape agent behavior? What's the everything-claude-code project (affaan-m) doing with NanoClaw v2 and AgentShield? The EU AI Act compliance deadline (Aug 2026) is driving specification documentation requirements.

**Key question:** Is there a framework for treating .md specification files as first-class engineering artifacts with testing, versioning, quality assurance, and CI/CD integration? If not, what would one look like?

---

## C2: Deliberation & Multi-Perspective Synthesis [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md, CAPSTONE-IMPLICATIONS.md (read §§2-3 on Deliberation)

The Keystone Intelligence Engine includes a "Deliberation Layer" where multiple AI agents with different analytical perspectives (bull case, bear case, contrarian, consensus) examine research findings before conclusions are drawn. This mirrors how consulting teams actually work: you don't just do the analysis, you stress-test it from multiple angles. The Deliberation Layer produces a "Confidence Map" showing high-confidence claims, moderate-confidence claims, and contested claims with evidence quality ratings on each side.

The recent academic literature suggests the picture is more nuanced than "debate always improves quality." I need to understand what actually works.

**Critical recent findings (investigate these first because they challenge assumptions):**

"Debate or Vote" (NeurIPS 2025 Spotlight) found that majority voting ALONE accounts for most of the performance gains previously attributed to multi-agent debate. When they modeled debate as a stochastic process, it forms a martingale (expected future value equals current value). Targeted interventions that bias belief updates toward correction CAN enhance debate beyond voting, but naive debate often doesn't help.

"Can LLM Agents Really Debate?" (Wu et al., November 2025) found that intrinsic reasoning strength and group diversity are the dominant drivers of multi-agent quality, and that majority pressure actually suppresses independent correction. This suggests our Deliberation Layer should prioritize diverse model families over more rounds of debate.

Self-MoA / "Rethinking Mixture-of-Agents" (ICLR 2025) found that a single top model aggregating its own outputs outperforms mixed-model MoA by 6.6% on AlpacaEval 2.0. Quality of the individual model matters more than diversity.

BUT Attention-MoA (Jan 2026) contradicts this: an ensemble of small open-source models with inter-agent semantic attention and residual connections outperformed Claude-4.5-Sonnet and GPT-4.1. So under the right architecture, diversity can still win.

"Society of Thought" (Kim et al., 2026) found that frontier reasoning models spontaneously simulate multi-agent-like interactions within their chain of thought. "Models rediscover that robust reasoning is a social process."

**Implementations to evaluate:**

"Mixture of Agents" (Together AI, ICLR 2025 Spotlight, ~266 citations): Implementable in ~50 lines of code. Key insight: diverse model families matter more than number of debaters. Du et al. "LLM Debate" (ICML 2024) and the A-HMAD follow-up (Adaptive Heterogeneous Multi-Agent Debate with diverse specialized agents + dynamic routing + learned consensus module). AutoGen/AG2's `SocietyOfMindAgent` class as a concrete engineering implementation of the Society of Mind concept.

Evans et al. "Agentic AI and the next intelligence explosion" (Science, 2026): "We will need systems that support multiple parallel, converging, and diverging streams of deliberation — architectures in which brainstorming, devil's advocacy, and constructive conflict are designed features."

A production example from Stavros Korokithakis (March 2026): Claude Opus 4.6 as architect, Sonnet 4.6 for implementation, Codex + Gemini + Opus as reviewers. Cross-company model diversity was essential to avoid self-agreement bias.

**Red team / adversarial analysis tools:**

DeepTeam (Confident AI), Promptfoo (30K+ developers), PyRIT (Microsoft), Garak (NVIDIA). Prompt injection found in 73% of production deployments. Multi-turn jailbreaks reach 97% success in 5 turns. How should adversarial analysis be structured within our Deliberation Layer?

**Evaluation of deliberation quality:**

MAJ-EVAL (July 2025): Multi-Agent-as-Judge with auto-constructed evaluator personas. Achieved Spearman ρ up to 0.47 vs 0.15-0.36 for baselines.

**Key questions for our architecture:**
1. Given the "Debate or Vote" finding, should our Deliberation Layer use structured debate, or simply run multiple independent analyses and aggregate? What's the tradeoff?
2. How do you ensure agents with different assigned perspectives (bull/bear/contrarian) actually maintain those perspectives rather than converging to polite agreement?
3. Cross-company model diversity (Claude + GPT + Gemini) vs. same-model diverse prompting — which produces better analytical output and at what cost differential?
4. Has anyone built a working multi-perspective deliberation system specifically for analytical research (not coding, not chat)? What worked and what didn't?
5. How should the Confidence Map be structured? What granularity of agreement/disagreement is useful?

---

## C3: Report/Deliverable Generation [🟡 MEDIUM]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine's final output layer must generate consulting-quality deliverables: research briefs, competitive landscape analyses, market sizing reports, and strategy recommendations. These must meet the "anti-slop" principle: every output is directly usable without cleanup or reformatting. A senior partner should be able to present the output to a client without editing it. This is the "Goldman-grade" standard.

The landscape for automated document generation has shifted significantly with Claude's Skills API and official Office skills. I need to understand the state of the art and decide what to build vs. integrate.

**Claude's official document generation skills (primary integration path):**

Anthropic released official PPTX, DOCX, XLSX, and PDF skills in October 2025, fully available February 2026. These are pre-built via the Skills API (`client.beta.skills.list(source="anthropic")`). They handle HTML-to-PPTX conversion, OOXML manipulation, template-based creation, and visual validation via thumbnail grids. Claude for PowerPoint was released as a research preview in February 2026 for Pro/Max/Team/Enterprise users, putting Claude directly inside PowerPoint.

Gadoci Consulting built custom Claude Code PPTX skill files specifically for McKinsey-style deliverables: a design system file plus a layout library with 13 slide functions. They reportedly delivered a "McKinsey-level 60,000-word analysis" in 3 days using these skills. The skill files are publicly downloadable. tfriedel/claude-office-skills packages all Office skills for the Claude Code CLI. How production-ready are these? What are the quality limitations?

**Open-source tools:**

PPTAgent (icip-cas/PPTAgent) is the most sophisticated open-source AI presentation tool. Its "DeepPresenter" mode (arXiv Feb 2026) uses environment-grounded agentic generation with a sandbox containing 20+ tools. Marp works well with Claude Code and has MCP servers for AI-powered generation; it's better for internal presentations than client deliverables. Slidev (Vue.js powered) is growing rapidly with PDF/PPTX export. deck2video converts Marp or Slidev decks into narrated MP4 videos with local AI voice cloning.

For reports: pandoc and weasyprint remain solid for PDF generation from markdown. Chart/visualization generation via matplotlib and plotly through Claude Code's code execution. Powerdrill Bloom and Tableau Agent for data visualization. Manus (now Meta) deploys hundreds of parallel agents for research + visualization + complete structured report generation.

**The quality benchmark:**

McKinsey's Lilli: roughly 1/3 of all usage is auto-generated presentation decks, saving 90-120 minutes each. Lilli cross-checks facts against a RAG knowledge base, attaches inline citations, and flags unsupported claims. This is the current state of the art for automated consulting deliverables.

**Industry context:**

"The era of the 100-page PDF report as the end-all deliverable is waning." Consultants are increasingly expected to deliver working prototypes, interactive dashboards, and AI tools alongside traditional reports. A CIO quoted: "We're not going to keep paying $500K for a report we suspect was generated by a machine." The "cite-or-it-dies" policy is emerging: every factual claim in a consulting deliverable must have a traceable source.

**Key questions:**
1. What's the state of the art for automated generation of professional-quality analytical deliverables?
2. Where should we build custom vs. integrate existing Claude Skills?
3. How do we enforce the anti-slop principle architecturally (output directly usable without cleanup)?
4. What's the right format mix for our output? (Markdown research brief + PPTX executive deck + interactive data dashboard?)
5. How do we handle the citation chain (every claim traceable from the final slide back to the original source)?

---

## C4: Data Retrieval Architecture [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

The Keystone Intelligence Engine's research agents need to access diverse data sources in parallel during a single research thread: SEC filings, industry reports, news articles, academic papers, financial data, government statistics, and eventually proprietary client documents. I need a unified retrieval architecture that routes queries to the right sources, handles different data formats, scores source quality, caches expensive calls, and stays within rate limits across multiple providers.

**RAG architecture (current best practices):**

Naive RAG (retrieve → augment → generate) is dead in production. The baseline is now Modular RAG: query rewriting → hybrid search (dense vectors + sparse BM25) → reranking → context assembly. Hybrid search consistently outperforms either approach alone: documented +7.2% Recall@5 and +18.5% MRR improvement. Adaptive chunking (87% accuracy) dramatically outperforms fixed-size chunking (13%). Reranking with models like Jina's reranker-m0 (2.4B parameter multimodal) is now considered essential post-retrieval. Beyond Modular RAG, investigate Agentic RAG (the agent decides what to search and when) and Self-RAG (self-correcting architecture with reflection tokens that critique retrieved context before generation).

**Vector database selection:**

pgvector with pgvectorscale (Timescale) is the game-changer: 471 QPS at 99% recall on 50M vectors, which is 11.4x better than Qdrant in benchmarks. This makes Postgres competitive with dedicated vector DBs for most use cases under 10M vectors. If we're already using Postgres, this eliminates the need for a separate vector DB.

For dedicated vector workloads: Qdrant v1.15.2 (Rust-based, server-side IDF), Pinecone (fully managed, SOC 2/HIPAA compliance), Weaviate (built-in BM25 for hybrid search, GraphQL API), Milvus/Zilliz (billions scale with GPU acceleration). ChromaDB v1.5.5 is still not production-grade (no horizontal scaling, no native hybrid search). LanceDB (DuckDB integration, SQL-like hybrid search) is growing fast and worth watching.

**MCP servers as the integration layer:**

The MCP ecosystem has created turnkey integrations for most of our data sources. Financial: EdgarTools MCP (free, MIT license, 13 tools covering 30+ SEC form types with a live filings monitor), Financial Modeling Prep MCP (equities, financials, earnings, ETFs, indices, macro indicators). Government/macro: Government Data MCP by lzinga exposes 36 US government APIs through 188 tools covering Treasury, FRED, BLS, BEA, EIA, Census, FEC, Congress, SEC, FBI, World Bank, and CDC. Academic: Academix MCP Server unifies search across OpenAlex, DBLP, Semantic Scholar, arXiv, and CrossRef with smart ID resolution, BibTeX export, and citation analysis. Semantic Scholar MCP gives direct access to 225M+ papers. Search: Exa MCP (category-based search with specialized indexes), Brave Search MCP (independent index), Tavily MCP (with /research endpoint), SearXNG MCP (self-hosted, unlimited).

**Source quality scoring:**

How do you rank sources by reliability? Academic papers vs. blog posts vs. news articles vs. social media. Within academic papers: peer-reviewed vs. preprint vs. working paper. Within news: primary reporting vs. aggregated vs. opinion. Our research agents need to weight evidence differently based on source quality. How do existing systems handle this?

**Architecture questions:**
1. Should MCP servers be the unified integration layer, with each data source accessed through its own MCP server?
2. How do you route queries to the right data source? (A query about a company's revenue should go to SEC EDGAR; a query about industry trends should go to news + academic search; a query about competitive positioning should go to multiple sources)
3. How do you handle caching for expensive API calls? What's a sensible caching strategy across providers with different update frequencies?
4. How do you stay within rate limits across 10+ simultaneous data providers during a parallel research session?
5. What's the optimal embedding model for consulting research documents (mix of financial data, prose analysis, tables)?

---

# CATEGORY D: Frontier & Inspiration

---

## D1: Best AI Agent Systems by Individuals/Small Teams [🟡 MEDIUM]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

I'm building the Keystone Intelligence Engine and want to learn from the most impressive AI agent systems built by individuals or small teams in the last 6 months. Not big-company products. Systems that demonstrate genuinely novel approaches to agent architecture, research automation, or quality control that we could adapt.

**Known high-impact projects (verify current status and extract architectural lessons):**

Peter Steinberger's OpenClaw (210K+ stars) is the fastest-growing open-source project in GitHub history. It's an autonomous always-on agent that browses the web, fills forms, runs shell commands, writes code, controls smart home devices, and writes its own skills. 5,700+ community skills. Steinberger joined OpenAI in Feb 2026 and the project moved to an open-source foundation. Important: Cisco's AI security research team found a malicious third-party skill that performed data exfiltration without user awareness, highlighting the security risks of open skill ecosystems. What architectural lessons can we learn about agent autonomy, skill composition, and security?

obra/Superpowers (113.5K stars, #1 GitHub trending March 2026) is an agentic skills framework and software development methodology. Its key innovation is that the planning process creates precisely crafted context for each task, which allows using cheaper models for implementation. How does its context-crafting approach relate to our Specification Engine?

Karpathy's autoresearch (42K+ stars, March 2026): 630 lines of Python, MIT license. Ran 126 experiments overnight, kept 23 improvements (18% keep rate). His vision: "emulate a research community" of collaborating agents. Spawned a massive fork ecosystem. What does the keep/revert decision mechanism look like? How does it prevent ratchet failures?

garrytan/gstack (23K stars in first week): Y Combinator president's opinionated agent configurations. affaan-m/everything-claude-code (+36K monthly stars): Claude Code optimization, NanoClaw v2, AgentShield security scanner (98% coverage, 102 static analysis rules). mvanhorn/last30days-skill (8.4K stars): Researches topics across Reddit, X, YouTube, HN, Polymarket, then synthesizes grounded summaries. This last one is interesting as a research pattern.

**Builders to track (investigate their recent work):**

Simon Willison published "Agentic Engineering Patterns" (Feb 2026), a comprehensive guide to coding practices for the agent era. He's writing the most substantive practitioner documentation on LLM quality. swyx is now at Cognition (Devin team), editing Latent.Space (80K+ AINews subscribers), and building SmolAI research agents. Harrison Chase's LangGraph is used by Klarna, Uber, LinkedIn with 34.5M monthly downloads. 199-biotechnologies (Boris Djordjevic) built an ecosystem: engram (memory MCP server), claude-deep-research-skill (8-phase pipeline), autoresearch-cli, search-cli, agent-cli-framework. Chris Worsey's ATLAS financial system (+22% returns, $20/month).

**What to search for beyond known projects:**

GitHub repos that trended in the agent/research space in Q1 2026. Systems that specifically target professional services (consulting, legal, finance research). Agent hackathon winners. Production multi-agent research systems by small teams (not demos). Any system demonstrating the autoresearch pattern applied to non-ML domains.

**For each system:**
1. What's genuinely novel about the architecture (not just another ChatGPT wrapper)
2. What specific patterns could we adapt for Keystone
3. What they tried that didn't work (failure signals are more valuable than success stories)
4. How they handle the specification and evaluation problems

---

## D2: Academic Papers on Automated Analysis [🟡 MEDIUM]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md

I need the most relevant recent academic papers (2024-2026) on automated research, multi-agent analysis systems, and AI-assisted decision support. I'm building a multi-agent consulting research system (see attached plan) and need to understand what the academic literature says about whether our architectural choices are validated, contradicted, or can be improved. Focus on papers with code and empirical results, not just theory.

**Multi-agent debate and deliberation (the literature is more nuanced than expected):**

"Debate or Vote" (NeurIPS 2025 Spotlight) found that majority voting alone captures most of the gains attributed to debate. Self-MoA (ICLR 2025) found a single best model outperforms mixed models by 6.6%. But Attention-MoA (Jan 2026) showed small model ensembles CAN beat frontier models with the right architecture. "Society of Thought" (Kim et al., 2026) found models spontaneously simulate multi-agent debate internally. "Can LLM Agents Really Debate?" (Wu et al.) found diversity and reasoning strength dominate over debate structure. Evans et al. (Science, 2026) called for "architectures in which brainstorming, devil's advocacy, and constructive conflict are designed features." Du et al. "LLM Debate" (ICML 2024) and A-HMAD. The Mixture of Agents paper (ICLR 2025 Spotlight, ~266 citations).

What's the net conclusion? Does multi-agent deliberation improve analytical research quality, and if so, under what conditions?

**Evaluation and meta-evaluation:**

SOS-Bench (ICLR 2025): style over substance in LLM judges. CALM (ICLR 2025): 12 bias types. Prometheus 2 (EMNLP 2024): open-source evaluator model. SE-Jury (ASE 2025): ensemble judges with 34-113% improvement. Agent-as-a-Judge (arXiv:2508.02994): evaluating agent behavior, not just outputs. "When AIs Judge AIs" survey. DeepResearchGym (CMU, arXiv:2505.19253). MAJ-EVAL: Multi-Agent-as-Judge.

**Self-improving systems:**

Meta HyperAgents (arXiv:2603.19461): metacognitive self-modification, cross-domain transfer. Darwin Gödel Machine (arXiv:2505.22954). "ARTIST" (ICML 2025). ADAS (ICLR 2025): meta-agents that invent agent architectures. "Breaking Mental Set through Diverse Multi-Agent Debate" (ICLR 2025). "A Comprehensive Survey of Self-Evolving AI Agents" (arXiv:2508.07407).

**Automated research and report generation:**

The AI Scientist (Nature, 2026): end-to-end research automation with documented failure modes. STORM / Co-STORM (NAACL 2024, EMNLP 2024): multi-perspective research synthesis. "Characterizing Deep Research": proposes the deep research task as a DAG of information synthesis. DeepResearch Bench: 100 PhD-level tasks across 22 fields.

**Agent architecture:**

arXiv:2602.00180 "Spec-Driven Development" (Jan 2026). Google DeepMind's finding that unstructured multi-agent networks amplify errors up to 17.2x. Multi-agent coordination surveys: Li et al. (2024), Chen et al. (Dec 2024), Plaat et al. (March 2025). Awesome-Agent-Papers GitHub repo.

**For each relevant paper:**
1. Core contribution (1-2 sentences)
2. Key finding that changes our architectural thinking
3. How it specifically applies to Keystone's design (specification engine, parallel isolated research, deliberation, evaluation, rejection library)
4. GitHub repo if code is available
5. Whether it validates, contradicts, or extends our architectural assumptions

---

## D3: 10x Ideas — What Would Make Keystone Extraordinary [🟠 HIGH]

**Attach:** CAPSTONE-PLAN-v2.md, SYNTHESIS.md, CAPSTONE-IMPLICATIONS.md, FRAMEWORKS.md

Read the attached project plan carefully. The Keystone Intelligence Engine is a six-layer multi-agent system for automated consulting research. I want you to think about what would make this system 10x better than what's described. Ideas we haven't considered. Approaches from adjacent fields. Capabilities that would make consulting partners say "I didn't know this was possible."

**Adjacent fields where production-ready tools already exist:**

Intelligence analysis: Maltego does graph-based OSINT with 120+ data integrations. SpiderFoot automates intelligence gathering from 100+ sources. Fivecast offers ONYX, LUNEX, and MATRIX platforms for open-source intelligence. The OSINT market is expected to reach $29.19B by 2026. More importantly, the IC's ICD 203 analytical standards and Heuer & Pherson's 66 structured analytic techniques represent decades of methodology for analyzing complex situations under uncertainty. Which of these techniques could be implemented as multi-agent components? Analysis of Competing Hypotheses, for example, maps almost perfectly to our Deliberation Layer.

Causal inference is now feasible, not just theoretical: CausalAgent (Feb 2026, IUI Conference) is a conversational multi-agent system for end-to-end causal inference using LangGraph, RAG, and MCP. You upload a dataset, ask natural language questions, and get an interactive analysis report. MATMCD achieves up to 66.7% reduction in causal inference errors through multi-agent coordination. causaLens offers a commercial "PhD-level Economist" agent. What if Keystone could go beyond correlation-based analysis to identify causal mechanisms?

Financial due diligence tools: AlphaSense is used by 90% of top asset management firms for research. Kira Systems achieves 90%+ accuracy on contract analysis. Datasite offers AI-powered virtual data rooms. Spellbook covers 2,300+ contract types. McKinsey published a five-step gen AI integration framework for due diligence. What would it look like to integrate these capabilities?

Competitive intelligence: AlphaSense's "Smart Synonyms" technology finds relevant results even when companies don't use standard terminology. Dynamic peer set construction that scans earnings transcripts and patent filings to identify competitive relationships that aren't obvious from industry classifications.

**Technical capabilities that are now production-ready:**

Multimodal analysis: Qwen 3.5 handles text, images, audio, and video. GPT-5.4 can process 76K photos for $52. Google ADK has native multimodal via Gemini. What would consulting research look like if the system could analyze earnings call tone (audio), conference presentation slides (images), patent diagrams (technical drawings), and factory satellite imagery alongside text? Most competitive intelligence is still text-only. Multimodal is an arbitrage opportunity.

Code execution for quantitative analysis: Claude Code, Cursor Agent Mode (8 parallel agents via git worktrees), ChatGPT Code Interpreter. The autoresearch pattern (write code → execute → evaluate → iterate) applies to quantitative analysis. What if every market sizing was actually computed (build the model, run the calculations, sensitivity-test the assumptions) rather than estimated with back-of-envelope arithmetic?

Real-time monitoring: Fivecast continuous monitoring, Improvado AI Agent for anomaly detection, Claude Cowork scheduled tasks (Feb 2026). What if Keystone maintained living competitive landscapes that updated automatically when a competitor files a patent, publishes earnings, launches a product, or gets mentioned in news? Shift from on-demand research to always-on intelligence.

Autonomous research at scale: Manus (now Meta) deploys hundreds of parallel agents for research, data analysis, visualization, and complete structured report generation. Its "Wide Research" feature does comprehensive coverage across many sources simultaneously. What does consulting research look like when you can investigate 50 hypotheses in parallel rather than 3 sequentially?

**Blue-sky questions:**

What would this system look like in 3 years? What capabilities should we design the architecture to support even if we can't build them yet? What do the best human research analysts do that this system doesn't even attempt? What would the self-improvement loop discover about research methodology that humans haven't articulated? What would make this not just "AI that does research" but "a new kind of analytical capability that doesn't exist yet"?

The "cite-or-it-dies" policy (every factual claim traceable to a primary source) should be enforced architecturally, not as a prompt instruction. How? What would it look like if the system refused to include any claim it couldn't trace to a verified source?

Don't hold back. Some of these ideas might be infeasible now but worth designing the architecture to support.

---

## Run Order

🔴 **Immediate (start all in parallel):** A1, A2, B1, B2, B4
🟠 **Next (all in parallel):** A3, A4, A5, B3, C1, C2, C4, D3
🟡 **Then (all in parallel):** C3, D1, D2
