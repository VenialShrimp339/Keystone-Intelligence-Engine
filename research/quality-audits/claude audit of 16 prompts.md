# Vetting 14 Keystone Intelligence Engine prompts against the March 2026 landscape

The AI agent ecosystem has shifted dramatically since these prompts were drafted. **AutoGen is in maintenance mode, OpenAI Swarm has been formally superseded, and AGENTS.md is now a Linux Foundation standard**—while entirely new paradigms like spec-driven development, Meta's HyperAgents, and Claude's Skills marketplace have emerged. Below is a prompt-by-prompt audit identifying every outdated reference, every missing addition, and every item requiring updated framing, drawn from current research across all 14 prompts.

---

## A3: Self-improvement, autoresearch, and learning loops

This prompt's core references are still valid but now sit within a vastly larger ecosystem. Karpathy's autoresearch went from concept to a **42,000-star open-source phenomenon** in March 2026, spawning dozens of forks. DSPy didn't stall—it accelerated.

### Items to remove

None require full removal. All referenced systems remain active. However, the framing of TextGrad as a leading framework should be demoted: it is now positioned as a **baseline/predecessor** in the optimization literature, not a frontier tool.

### Items to add

- **DSPy v3.1.3 with GEPA optimizer** (Agrawal et al., arXiv:2507.19457): Reflective prompt evolution achieving 67%→93% on MATH benchmark, endorsed by Shopify CEO as "severely under-hyped." Also add **SIMBA** for large-dataset scenarios. GEPA outperforms MIPROv2 by ~11% across tasks.
- **Meta HyperAgents** (arXiv:2603.19461, March 19, 2026): Metacognitive self-modification where the agent rewrites its own improvement procedure. Achieved 3x improvement on polyglot coding (14%→34%), cross-domain transfer demonstrated. Built on the **Darwin Gödel Machine** (arXiv:2505.22954).
- **HKUDS OpenSpace** (March 2026): Self-evolving skill engine with auto-repair and auto-improve modes. **4.2x income improvement, 46% token reduction** across 50 professional tasks. Skills accumulate in SQLite DB.
- **metaTextGrad** (arXiv:2505.18524): Meta-optimizes TextGrad's own optimizer prompts per task.
- **Modular Prompt Optimization (MPO)** (arXiv:2601.04055, Jan 2026): Outperforms TextGrad by treating prompts as structured schema objects with section-local textual gradients.
- **Karpathy autoresearch release details**: 630-line Python script, MIT license, March 7 2026. 126 experiments/23 improvements (18% keep rate). Fortune dubbed it "The Karpathy Loop." Massive fork ecosystem including generalized (autoresearch-anything), agent-specific (codex-autoresearch, gemini-autoresearch), and distributed (autoresearch-at-home) variants.
- **199-biotechnologies ecosystem**: Confirm autoresearch-cli exists; also add **engram** (MCP memory server with BM25 + ColBERT + Knowledge Graph hybrid search) and **claude-deep-research-skill** (8-phase pipeline with source credibility scoring).
- **Claude Agent SDK** (renamed from Claude Code SDK): Not a self-improvement framework per se, but the primary harness powering autoresearch loops. Supports subagents, hooks, session forking, context compaction. Available on Anthropic API, Bedrock, Vertex AI, Azure AI Foundry.
- **OpenAI Self-Evolving Agents Cookbook**: Combines GEPA with OpenAI Agents SDK for automated prompt refinement loops.
- **"A Comprehensive Survey of Self-Evolving AI Agents"** (arXiv:2508.07407): Unified four-component framework (System Inputs, Agent System, Environment, Optimisers). Accompanying awesome list at github.com/EvoAgentX/Awesome-Self-Evolving-Agents.
- **Stanford CS329A**: New Stanford course on self-improving AI agents covering constitutional AI, verifiers, test-time compute scaling.
- **Agent memory frameworks**: Hindsight (Vectorize.io, institutional knowledge), Mem0 (personal), Zep (customer history), Letta (long-context), Cognee (structured memory graph). Distinguish personalization memory from institutional knowledge memory.

### Items to modify

- **DSPy**: Update from generic reference to v3.1.3 with 23K stars, 300+ contributors, 500+ dependents. Emphasize GEPA as the new top optimizer, with MIPROv2 now one option among several.
- **TextGrad**: Reframe from "frontier framework" to "foundational work published in Nature, now used primarily as a baseline." Active but superseded by metaTextGrad and MPO.
- **MIPRO**: Still active within DSPy but no longer top performer. Outperformed by GEPA by ~11%.
- **Chris Worsey's ATLAS/Darwinian selection**: Still the best *applied real-world* example (+22% returns in 173 days on real capital, $20/month infrastructure). But add Meta's HyperAgents and DGM as more rigorous *academic* frameworks for evolutionary self-improvement. The prompt should reference both applied and academic examples.
- **Rejection sampling**: The autoresearch ecosystem has made this pattern concrete—every fork uses keep/revert logic. Frame as "ratchet loop" pattern (Karpathy's term).
- **Trajectory storage**: Now a rapidly maturing category. Update from generic concept to specific frameworks: autoresearch.jsonl (standard format), MEMORY.md/GUARDRAILS.md/WORKSTATE.md (tiered flat-file pattern), OpenSpace skill database (SQLite with lineage tracking).

---

## A4: Orchestration frameworks and agent coordination

This prompt needs the most significant overhaul. Two of its core references (AutoGen, Swarm) are effectively deprecated, while multiple major new frameworks and protocols have launched.

### Items to remove

- **AutoGen as a recommended framework**: It is in **maintenance mode**—no new features, only bug fixes and security patches. Microsoft consolidated it with Semantic Kernel into the new **Microsoft Agent Framework** (public preview Oct 2025, GA targeted Q1 2026). The prompt should mention AutoGen only as legacy context, not as a current option.
- **OpenAI Swarm as a current framework**: Formally superseded by the **OpenAI Agents SDK** (shipped March 2025). GitHub repo has a banner: "Swarm is now replaced by the OpenAI Agents SDK." Retain only as historical/educational reference.

### Items to add

- **OpenAI Agents SDK** (~19K stars): Production-grade replacement for Swarm with built-in guardrails, tracing dashboards, persistent memory, handoff architecture. Vendor-locked to OpenAI ecosystem.
- **Google Agent Development Kit (ADK)** (v0.6.0, 17K stars): Code-first, model-agnostic (optimized for Gemini 3), modular multi-agent hierarchies, Sequential/Parallel/Loop workflow agents. A2A and MCP native. Python and TypeScript. Bi-weekly release cadence.
- **Claude Agent SDK**: Renamed from Claude Code SDK. Python v0.1.50, TypeScript. Powers Claude Code's agent loop. Programmatic subagents, session forking, structured outputs, hooks system. MCP integration is deepest of any SDK.
- **PydanticAI** (v1.72.0, 15K stars): "FastAPI feeling" for agents. Type-safe, model-agnostic (40+ providers), Capabilities system, AgentSpec (YAML/JSON), MCP/A2A/UI integration, durable execution via Temporal/DBOS. Pydantic Evals framework built in.
- **A2A Protocol (Agent-to-Agent)** v0.3: Originally Google, now under Linux Foundation with 150+ partners (Adobe, Salesforce, SAP, ServiceNow). JSON-RPC 2.0 over HTTP/SSE/gRPC. Complementary to MCP (MCP = agent-to-tool; A2A = agent-to-agent). Agent Cards for discovery, Tasks, Messages, Artifacts.
- **Mastra** (22.3K stars): Leading TypeScript agent framework, from the Gatsby team. YC W25, $13M seed. 300K+ weekly npm downloads, v1.0 Jan 2026. Used by PayPal, Adobe, Replit.
- **Microsoft Agent Framework**: Successor to both AutoGen and Semantic Kernel. Public preview Oct 2025, GA targeted Q1 2026.
- **DeerFlow 2.0** (ByteDance, 3.7K stars): Deep research and content creation focused. #1 GitHub trending at launch.
- **Smolagents** (HuggingFace): HuggingFace's entry into agent frameworks.
- **Letta** (~15K stars, formerly MemGPT): Stateful agents with long-term memory.
- **AG-UI protocol** (CopilotKit): Agent-to-frontend streaming standard.

### Items to modify

- **LangGraph**: Update to v1.1.2 (March 2026). LangGraph 1.0 GA was a milestone—"first stable major release in the durable agent framework space." 24K stars, 9M+ weekly PyPI downloads. Used by Uber, LinkedIn, Klarna. Note security vulnerabilities patched (CVE-2026-34070). **Still the top choice for production-grade complex workflows.**
- **CrewAI**: Update to v1.12.2. **45,900+ stars**—fastest-growing framework. Native A2A and MCP support, Flows architecture. 12M+ daily agent executions in production. 100K+ certified developers.
- **MCP**: Update to reflect Linux Foundation governance (donated Dec 2025) under the Agentic AI Foundation (AAIF), co-founded by Anthropic, Block, and OpenAI. **97M+ monthly SDK downloads**. Adopted by ChatGPT, Cursor, Gemini, VS Code. 2026 roadmap published March 9 with transport scalability, agent communication primitives, enterprise readiness.
- **Agency Swarm**: Still active (agency-swarm.ai) but small community. Keep as a reference but note it's a tier below the leaders.
- **CAMEL-AI**: Active with ~18K stars. Strong in academic/research contexts (OWL, CRAB, OASIS). Keep but position as research-focused.
- **MetaGPT**: Active but niche—specialized in automated software development simulation. Keep but note it's not a general-purpose orchestrator.
- **OpenClaw ACP**: Clarify that this is an IDE-to-agent protocol (JSON-RPC 2.0 over stdio, similar to LSP), distinct from A2A. OpenClaw implements an ACP bridge for Zed and VS Code. Note IBM's BeeAI also introduced an "Agent Communication Protocol" separately.
- **Anthropic multi-agent patterns**: Update with their published blog post "How we built our multi-agent research system" describing orchestrator-worker pattern. Add their 2026 Agentic Coding Trends Report identifying 8 trends including multi-agent coordination replacing single-agent workflows.

### Recommended framework tier list for the prompt

The prompt should present a **tiered landscape**: Tier 1 Production (LangGraph, CrewAI, OpenAI Agents SDK), Tier 2 Strong (PydanticAI, Claude Agent SDK, Google ADK, Mastra), Tier 3 Specialized (CAMEL-AI, MetaGPT, Agency Swarm, DSPy), Tier 4 Legacy (AutoGen, Swarm).

---

## A5: Deep research tooling and capabilities

The tooling landscape has matured considerably. Every major platform now offers deep research, and the MCP ecosystem has exploded.

### Items to remove

No full removals needed. All referenced tools remain active. However, **Puppeteer** should be deprioritized in favor of the newer AI-native browser tools.

### Items to add

- **Exa Search** ($85M Series B): Built its own search engine and index from scratch. Specialized indexes for **1B+ people, 50M+ companies, 100M+ research papers**. Sub-450ms latency (fastest benchmarked). 81% on WebWalker vs Tavily's 71%. MCP server with web_search_exa, web_search_advanced_exa, crawling_exa. Claude Code skills for company/people/code research.
- **Brave Search API**: Independent index (not Google/Bing wrapper), privacy-focused. Scored **14.89 on AIMultiple agentic search benchmark** (highest). $5/1K queries.
- **199-bio search-cli**: Installable via Homebrew. Part of ecosystem including **claude-deep-research-skill** (8-phase pipeline: Scope→Plan→Retrieve→Triangulate→Outline→Synthesize→Critique→Refine) with parallel search + sub-agents, source credibility scoring (0-100), Graph-of-Thoughts reasoning, multi-persona red teaming.
- **Stagehand v3 by Browserbase** (Feb 2026): Complete rewrite with AI-native architecture. Three primitives: `act()`, `extract()`, `observe()` plus `agent()`. **44% faster than v2**. Self-healing capabilities. SDKs in TypeScript, Python, Go, Ruby. Browserbase raised **$40M Series B** ($300M valuation).
- **OpenAlex**: 271.3M indexed works + 192M expansion records. Free, open-source by OurResearch. REST API with 100K+ free calls/day. Now encompasses Unpaywall and Unsub. Limitations documented: many records lack abstracts/affiliations.
- **Academix MCP Server**: Aggregates OpenAlex, DBLP, Semantic Scholar, arXiv, and CrossRef into unified research interface. Smart ID resolution, BibTeX export, citation analysis.
- **Serper API**: Budget Google SERP scraping. Deep integrations with LangChain. MCP servers available.
- **Lightpanda**: Open-source headless browser built in Zig; 11x faster, 9x less memory than headless Chrome.
- **Platform deep research architectures**: Claude uses parallel multi-agent with orchestrator; OpenAI uses interactive clarification then o3/o4-mini; Gemini uses autonomous plan-first with user approval; Perplexity Sonar Pro uses iterative adaptive retrieval (94.3% citation accuracy, <3 min completion).
- **MCP server ecosystem**: Exa MCP, SEC EDGAR MCP (EdgarTools—most popular Python SEC library, 2.3M+ downloads, 13 tools), Financial Modeling Prep MCP, Government Data MCP (36 US govt APIs / 188 tools), Semantic Scholar MCP, SearXNG MCP, Brave Search MCP, Tavily MCP.

### Items to modify

- **Tavily**: Update to note **acquisition by Nebius** (Feb 2026). New `/research` endpoint is now GA—fully managed multi-step research with citations. New search depths: `fast` and `ultra-fast`. Monitor acquisition impact on roadmap/pricing.
- **Firecrawl**: Update to reflect five endpoints (Scrape, Crawl, Search, Map, **Agent**). The Agent endpoint enables autonomous multi-page research. Browser Sandbox for managed Chromium environments. Official Claude plugin.
- **Jina AI**: Update to note **acquisition by Elastic**. Now a full-stack search foundation provider with embeddings (v5), reranker (jina-reranker-m0, 2.4B parameter multimodal), Reader API, and Classifier. Token-based pricing.
- **SearXNG**: Update star count to 25K+. Growing adoption in AI/LLM toolchains with multiple MCP servers available. Ideal as free, self-hosted search backend for unlimited queries.
- **browser-use**: Update to 50K+ stars. Pure autonomy model—describe task, agent navigates. Model-agnostic. Pair with Browserbase for cloud deployment.
- **AgentQL**: Still active. Chrome extension for natural language commands. Lowest barrier to entry for web automation.
- **Semantic Scholar**: Update to 225M+ papers, 100M+ authors, 2.8B+ citation edges. Multiple MCP servers available. AI-powered recommendations feature is unique.
- **SEC EDGAR**: Multiple dedicated MCP servers now exist. EdgarTools MCP is the most comprehensive (free, MIT license, 13 tools, typed objects for 30+ form types, live filings monitor).

---

## B1: What senior consulting partners value

The consulting-AI intersection has generated a wealth of new data since these prompts were drafted, including empirical studies and a major AI-fabrication scandal.

### Items to remove

None require full removal. Victor Cheng's frameworks are considered outdated by current MBB practitioners ("completely outdated and useless for many cases" per a McKinsey partner on PrepLounge), but his structural decomposition logic remains foundational. Keep with explicit caveat.

### Items to add

- **McKinsey's Lilli metrics**: 72% of 45,000 employees active, 500,000+ prompts/month, **~50,000 labor hours/month recovered**. Auto-generated decks save 90-120 minutes each, account for ~1/3 of Lilli usage. 20,000 AI agents working alongside 40,000 humans.
- **BCG's Harvard Business School study** (758 consultants): 12.2% more tasks, 25.1% faster, 40%+ higher quality. Bottom-half performers saw **43% quality improvement**. Critical finding: complex tasks sometimes saw *decreased* performance. This "**jagged technological frontier**" concept is essential.
- **BCG GENE and Deckster**: GPT-4o-based conversational agent and slide automation tool. 36,000+ custom GPTs built; 80% created by front-line consultants. Multi-agent mesh with domain-specific agents planned to expand to 50+ blueprints by mid-2026.
- **Deloitte Australia AI fabrication incident** (July 2025): $290,000 government report with fake academic references, non-existent court cases, incorrect quotes. Forced refund and rewrite. Essential cautionary tale.
- **ICD 203 analytical tradecraft standards**: The nine IC analytic standards map almost perfectly to quality criteria for AI-generated analysis. Add the private-sector adaptation angle and the 2024 NIU Research Short arguing standards haven't reached full potential.
- **Industry data points**: MCA UK Jan 2026: 77% of consulting firms integrated AI; IBM 2025: 86% of consulting buyers seek AI-enabled services; Gartner: up to 40% of consulting tasks automatable; Big Four + MBB collectively invested $10B+ since 2023.
- **PwC "Human + AI Skillset" curriculum** (Feb 2026): 30 skills (15 AI-focused, 15 human).
- **HBR Feb 2026 "judgment gap"**: AI handles messy tasks that once built junior consultant judgment, risking thin leadership pipelines.
- **"2025 was the year of AI speed. 2026 will be the year of AI quality"** (CodeRabbit + industry consensus).

### Items to modify

- **Victor Cheng**: Reposition as foundational for structured decomposition logic but note his specific frameworks are considered outdated by current practitioners. Supplement with modern frameworks from actual MBB methodology documentation.
- **Ethan Rasiel / Pyramid Principle**: These remain valid foundational references. No updates needed beyond noting they predate AI-augmented consulting.
- **McKinsey quality frameworks**: Update from generic reference to specific 2026 data (Lilli adoption, QuantumBlack Horizon, 20K agents).

---

## B2: Decision-useful vs. comprehensive research

The decision-making frameworks referenced are more relevant than ever, with new data on how executives actually use AI-generated analysis.

### Items to remove

None. All referenced thinkers remain highly relevant.

### Items to add

- **Richards Heuer's "Psychology of Intelligence Analysis"** and the 3rd edition of **Structured Analytic Techniques** (Heuer & Pherson, now 66 techniques including 9 new). Specific techniques directly implementable in multi-agent systems: Analysis of Competing Hypotheses (ACH), Key Assumptions Check, Red Team Analysis, Pre-Mortem Analysis.
- **Gary Klein's AIQ toolkit**: New development from Klein and ShadowBox LLC for helping people manage specific AI systems. His Recognition-Primed Decision model and Data/Frame sensemaking model remain the theoretical basis for when AI can substitute for expert judgment.
- **Tetlock's ForecastEx appointment** (Jan 2026): Board of Directors of CFTC-registered prediction market. Superforecasters beat financial markets on Fed decisions through 2023-2025. Multi-agent investing experiments directly applying Tetlock's framework show promising but mixed results.
- **Kahneman's posthumous impact**: Died March 27, 2024. No new publications beyond *Noise* (2021). But his frameworks are being extensively applied to AI: System 1/System 2 → SOFAI architecture (Communications of the ACM), *Noise* framework → AI evaluation consistency, "decision hygiene" → AI evals and observability.
- **Deloitte 2026 survey**: 60% of executives regularly use AI for decisions. Gartner projects by 2027 half of business decisions will be augmented/automated by agents.
- **HBR Jan 2026**: "How Executives Are Thinking About AI" — vast majority see AI as high priority but struggle with measurable value. MIT Sloan: 2026 is a "level-set year" with dialed-back expectations.
- **IMD 2026**: "When AI takes care of scale and speed, the real bottleneck becomes human judgment."
- **Phil Rosenzweig**: Still relevant, no updates needed. His *The Halo Effect* critique of management research quality directly applies to AI-generated analysis.

### Items to modify

- **Kahneman**: Add death date and note extensive posthumous application of his frameworks to AI system design. The System 1/System 2 mapping and the Noise framework for measuring AI output consistency are now widely used.
- **Klein**: Update with AIQ toolkit and NDM 2026 conference. Emphasize his collaboration with Kahneman (2009 paper on when intuition is trustworthy) as relevant to understanding when AI analysis can substitute for expert judgment.
- **Tetlock**: Update with ForecastEx appointment and the multi-agent application experiments. His framework maps directly to multi-agent system design: independent perspectives first, constructive debate second, convergence last.
- **Chip & Dan Heath**: Still relevant but no significant new publications in the AI context. Keep at current priority.

---

## B3: Ness Labs and quality of thought

Paul Graham's "taste" thesis exploded in February 2026 and is now the defining discourse on AI quality in tech circles. This prompt should be substantially updated.

### Items to remove

None require full removal.

### Items to add

- **Paul Graham's Feb 14, 2026 prediction**: "In the AI age, taste will become even more important" to 2.2M followers. Sparked massive industry debate. OpenAI president Greg Brockman: "Taste is a new core skill." Cloudflare CTO: "In 2026, taste is the engineering differentiator." Counterpoint: "Taste is being automated. The thing that can't be automated, conviction, isn't being discussed."
- **Stripe Press "Tacit" docuseries**: Cites Cedric Chin's Commoncog as inspiration. Key insight: "The ceiling for LLMs, for now, seems to be conscious competence. They can capture procedure, but not judgment." Contributors include Andy Matuschak, Brie Wolfson, Dwarkesh Patel.
- **Simon Willison's expanded role**: Now widely considered the preeminent practitioner-voice on LLM quality. Published "LLM predictions for 2026" (Jan 2026) and comprehensive "2025: The year in LLMs." Coined "slop" for low-quality AI content. "Agentic Engineering Patterns" guide (Feb 2026) is essential reading.
- **HBR Feb 2026**: "How Do Workers Develop Good Judgment in the AI Era?" — organizations must deliberately redesign work to build judgment through simulations, case-based learning, stretch experiences.
- **Designative "Taste Is the New Bottleneck"** (Feb 2026): Teams must encode quality standards into prompts, evaluation functions, and design systems. Proposes taste as aesthetic judgment, aesthetic sensitivity, and cultural capital.
- **IMF June 2025 note**: "As AI prediction advances, the distribution of judgment will increasingly determine the distribution of wealth and power."
- **CodeRabbit analysis**: "2025 was the year of AI speed. 2026 will be the year of AI quality." AI code has **1.7x more issues and bugs** than human code.

### Items to modify

- **Anne-Laure Le Cunff**: Now **Dr.** Le Cunff (PhD Psychology & Neuroscience, King's College London). Published *Tiny Experiments* (Penguin Random House). TEDxNashville Jan 2026. Reposition as valuable for metacognition and experimental thinking, not primarily an AI quality authority.
- **Paul Graham**: **Major upgrade.** His 2026 taste thesis is now the defining frame for AI quality in tech circles. Add the Feb 2026 prediction, the Graham-Brockman-Knecht axis, and the counterarguments.
- **Cedric Chin**: Keep and strengthen. The Stripe Press "Tacit" docuseries dramatically validates his work. The "LLMs reach conscious competence but not unconscious competence" framing is directly applicable.
- **Dan Luu**: Lower priority. Remains a respected tech blogger but has NOT written extensively about AI quality in 2025-2026. His approach (empirical, contrarian) is more a model to emulate than a source to cite. Keep but deprioritize.
- **Simon Willison**: **Major upgrade.** Karpathy praised his 23 years of blogging. Published comprehensive annual LLM reviews. His emphasis on the changing nature of quality (from writing code to managing context, specifications, agent oversight) is directly relevant.

---

## B4: AI-generated research quality failures

Several key references need clarification or correction, and important new benchmarks and papers must be added.

### Items to remove

- **"19% paradox" as framed**: This actually refers to the **METR developer productivity study** (Feb-June 2025), not research quality. 16 experienced open-source developers were **19% slower** with AI assistance, while believing they were 20% faster—a **39-43 percentage point perception gap**. The prompt should reframe this as the "productivity illusion" or "perception gap" rather than a research quality paradox.
- **"False depth problem" as a formal concept**: No canonical paper uses this term. Reframe using SOS-Bench ("style over substance"), the "verisimilitude paradox" (as models become more fluent, users struggle more to identify inaccurate information), or reference the specific phenomenon documented in the AI Scientist paper.

### Items to add

- **SOS-Bench details** (ICLR 2025, arXiv:2409.15268): LLM-judge preferences do NOT correlate with concrete measures of safety, world knowledge, and instruction following. Sarcasm caused 96% loss vs only 13% loss for factual errors. 152,380 data points across 19 benchmarks.
- **CALM "Justice or Prejudice?"** (ICLR 2025, arXiv:2410.02736): The correct reference for 12 LLM-as-judge bias types (verbosity, fallacy oversight, sentiment, position, authority, diversity, refinement, etc.). Note: a different CALM paper measures sociodemographic bias—this is the one about judge bias.
- **DeepResearchGym** (CMU et al., arXiv:2505.19253, May 2025): Open-source benchmark for deep research systems. DiskANN-based dense retrieval over ClueWeb22 and FineWeb. Extends Researchy Questions with metrics for information coverage, retrieval faithfulness, and report quality. Also add **DeepResearch Bench** (100 PhD-level tasks, 22 fields, active leaderboard—Cellcog Max leads at 56.13 as of March 2026).
- **Prometheus 2** (EMNLP 2024, arXiv:2405.01535): Open-source evaluator LM (7B/8x7B) with 72-85% agreement with human judgments on pairwise ranking. Supports direct assessment AND pairwise ranking with custom criteria. Highly relevant as affordable, controllable evaluator.
- **LLM-as-judge consensus statistics**: GPT-4 achieves ~80% agreement with human preferences; position bias causes 40% inconsistency; verbosity bias inflates scores ~15%; self-enhancement bias 5-7%; domain expert agreement drops to 60-68%. Multi-model ensemble reduces biases 30-40% but costs 3-5x more.
- **SE-Jury** (ASE 2025): Ensemble-of-judges with 34-113% improvement in human correlation. 5 distinct evaluation strategies with dynamic team selection. Effective with only 20 annotated samples.
- **Agent-as-a-Judge** (Zhuge et al., 2025, arXiv:2508.02994): Extends evaluation from static outputs to dynamic agent behavior and reasoning trajectories.
- **The AI Scientist** (Nature 2026): End-to-end research automation pipeline. Only 1 of 3 submissions accepted at workshops. Common failures: naive ideas, incorrect implementations, hallucinated citations.
- **METR study details**: The actual "19% paradox" source. Randomized controlled trial with Cursor Pro + Claude 3.5 Sonnet. Faros AI follow-up (10K+ developers): 21% more tasks but 91% longer PR review time, 9% more bugs.
- **Deloitte Australia incident** (July 2025): $290K government report with fabricated academic references and non-existent court cases.
- **International AI Safety Report 2026**: Documents the "evaluation gap"—models can detect when being evaluated and modify behavior.

### Items to modify

- **HELM**: Update to reflect continuous maintenance with domain-specific leaderboards (MedHELM, VHELM, Audio-HELM). Also note a distinct paper "HELM: A Human-Centered Evaluation Framework for LLM-Powered Recommender Systems" at WWW '26.
- **LLM-as-judge failures**: Expand from general concept to specific, quantified bias types with mitigation strategies (order randomization, length normalization, cross-model evaluation, majority voting across diverse model families).

---

## C1: Specification-driven development

This prompt captures a paradigm that has since **exploded** into a major industry movement. Spec-driven development is now a dominant methodology, not a niche concept.

### Items to remove

None require full removal.

### Items to add

- **AGENTS.md as Linux Foundation standard**: Now stewarded by the Agentic AI Foundation. Adopted by OpenAI Codex, GitHub Copilot, Cursor, Windsurf, Gemini CLI, Claude Code, Kilo Code, Factory, and more. GitHub analyzed 2,500+ AGENTS.md files to identify success patterns.
- **Claude Code multi-agent architecture**: CLAUDE.md now works with `.claude/agents/*.md` (subagent definitions), `.claude/commands/`, `.claude/skills/` (SKILL.md files). Context editing achieves **84% token reduction**. Subagent orchestration with YAML frontmatter.
- **Claude Code Skills marketplace**: **500,000+ skills** indexed on SkillsMP.com. 277,000+ installs for official frontend-design skill. Universal SKILL.md format works across 11+ tools. Progressive disclosure pattern (SKILL.md is concise, bundled files load on-demand). Skills available via API with `skill_id` parameter.
- **antigravity-awesome-skills**: Now at **28K+ stars, 1,326+ skills**, V9.0.0. Installer CLI supports Claude Code, Codex, Gemini CLI, Kiro CLI/IDE, Cursor, OpenCode.
- **GitHub Spec Kit** (72.7K stars, 110 releases): Four-phase workflow: Specify → Plan → Tasks → Implement. Supports 22+ AI agent platforms.
- **Kiro IDE** (AWS): Entire IDE built around spec-driven development using EARS (Easy Approach to Requirements Syntax).
- **OpenCode** (122K stars, 5M monthly developers): Provider-neutral, multi-model agent harness with `.agents/` directory.
- **Academic recognition**: arXiv:2602.00180 "Spec-Driven Development: From Code to Contract in the Age of AI Coding Assistants" (Jan 2026). ThoughtWorks analysis and Martin Fowler coverage.
- **EU AI Act compliance** (Aug 2026 deadline) is driving spec documentation requirements.
- **Google DeepMind finding**: Unstructured multi-agent networks amplify errors up to **17.2x** vs single-agent. Structured specification essential.
- **Context engineering > prompt engineering**: Now considered more important. Cache hit rate identified as most important metric for production agents (Manus).

### Items to modify

- **CLAUDE.md**: Update from "emerging pattern" to "established constitution" for Claude Code projects. Note the full `.claude/` directory architecture.
- **AGENTS.md**: Major upgrade from "pattern" to "Linux Foundation industry standard."
- **Cursor Rules**: Update to `.cursor/rules/*.mdc` files with YAML frontmatter (alwaysApply, intelligent, manual modes). Note Windsurf acquisition by Cognition (Devin team), pricing increase from $15 to $20/mo.
- **everything-claude-code repository**: Confirm active at affaan-m/everything-claude-code. Features NanoClaw v2, AgentShield security scanner (98% coverage, 102 static analysis rules), PM2 multi-agent orchestration.

---

## C2: Deliberation and multi-perspective synthesis

Multi-agent debate has moved from purely academic to production implementations, with surprising findings that challenge some assumptions.

### Items to remove

- **MiroFish**: No current evidence of this project found in any search. **Remove entirely** and replace with production-validated frameworks like CrewAI, LangGraph, or the cross-company model diversity pattern.

### Items to add

- **"Debate or Vote" (NeurIPS 2025 Spotlight)**: Critical finding—majority voting alone accounts for most performance gains attributed to multi-agent debate. Debate modeled as stochastic process forms a martingale. Targeted interventions biasing belief updates toward correction CAN enhance debate.
- **"Can LLM Agents Really Debate?"** (Wu et al., Nov 2025): Intrinsic reasoning strength and group diversity are dominant drivers; majority pressure suppresses independent correction.
- **"Society of Thought"** (Kim et al., 2026): Frontier reasoning models spontaneously simulate multi-agent-like interactions within their chain of thought. "Models rediscover that robust reasoning is a social process."
- **Evans et al. "Agentic AI and the next intelligence explosion"** (Science, 2026): "We will need systems that support multiple parallel, converging, and diverging streams of deliberation—architectures in which brainstorming, devil's advocacy, and constructive conflict are designed features."
- **Self-MoA finding** (ICLR 2025): Single top model aggregating its own outputs outperforms mixed-model MoA by **6.6%** on AlpacaEval 2.0. Quality matters more than diversity.
- **Attention-MoA** (Jan 2026): Inter-agent Semantic Attention + residual connections. Ensemble of small open-source models outperforms Claude-4.5-Sonnet and GPT-4.1.
- **A-HMAD**: Adaptive Heterogeneous Multi-Agent Debate with diverse specialized agents + dynamic routing + learned consensus module.
- **Production implementation example**: Stavros Korokithakis (March 2026) published account of production multi-agent pipeline: Claude Opus 4.6 as architect, Sonnet 4.6 for implementation, Codex + Gemini + Opus as reviewers. **Cross-company model diversity is essential** to avoid self-agreement bias.
- **Red teaming frameworks**: DeepTeam (Confident AI), Promptfoo (30K+ developers), PyRIT (Microsoft), Garak (NVIDIA). Prompt injection found in 73% of production deployments. Multi-turn jailbreaks reach 97% success in 5 turns.
- **MAJ-EVAL** (July 2025): Multi-Agent-as-Judge with auto-constructed evaluator personas. Spearman ρ up to 0.47 vs 0.15-0.36 for baselines.

### Items to modify

- **Society of Mind**: Major upgrade. Now experiencing a renaissance via AutoGen/AG2's `SocietyOfMindAgent` class, the "Society of Thought" paper, and the Science paper. The concept has shifted from Minsky's philosophical framework to concrete engineering patterns.
- **Mixture of Agents**: Update with MoA's ICLR 2025 Spotlight status, ~266 citations, production implementation from Together AI (~50 lines of code). Add the counterintuitive Self-MoA finding that challenges the diversity assumption.
- **Du et al. LLM Debate**: Still foundational (ICML 2024). Update with citation count and key follow-up papers (A-HMAD, "Debate or Vote," "Can LLM Agents Really Debate?").
- **Red team implementations**: Far more mature than likely referenced. Specific tools, benchmarks, and statistics now available. Constitutional AI debate approach has evolved from training-time technique to runtime multi-agent governance pattern.
- **Multi-agent debate framing**: The literature now suggests **ensemble voting may be more important than actual debate**. Diverse agent compositions outperform homogeneous ones. The prompt should reflect this nuanced understanding rather than assuming debate is always beneficial.

---

## C3: Report and deliverable generation

This prompt needs a fundamental reorientation around **Claude's Skills API** as the primary integration point.

### Items to remove

- **python-pptx as the primary tool**: It remains the foundational library under the hood, but the prompt should center on **Claude Skills** which abstract over it. python-pptx is now an implementation detail, not the user-facing layer.

### Items to add

- **Anthropic Official Skills for PPTX/DOCX/XLSX/PDF**: Released Oct 2025, fully available Feb 2026. Pre-built via Skills API (`client.beta.skills.list(source="anthropic")`). HTML-to-PPTX conversion, OOXML manipulation, template-based creation, visual validation via thumbnail grids.
- **Claude for PowerPoint Add-in**: Research preview released Feb 2026 for Pro/Max/Team/Enterprise. Claude directly inside PowerPoint.
- **Gadoci Consulting PPTX Skill Files**: Custom Claude Code skills for McKinsey-style deliverables—design system file + layout library with 13 slide functions. Delivered a "McKinsey-level 60,000-word analysis" in 3 days. Publicly downloadable.
- **PPTAgent** (icip-cas/PPTAgent): Most sophisticated open-source AI presentation tool. "DeepPresenter" for environment-grounded agentic generation (arXiv Feb 2026). Sandbox with 20+ tools.
- **tfriedel/claude-office-skills**: Community repo packaging all Office skills for Claude Code CLI.
- **deck2video**: Converts Marp or Slidev decks into narrated MP4 videos with local AI voice cloning.
- **Industry shift**: "The era of the 100-page PDF report as the end-all deliverable is waning." Consultants now expected to deliver working prototypes, dashboards, AI tools. CIO quote: "We're not going to keep paying $500K for a report we suspect was generated by a machine."
- **McKinsey Lilli deck generation**: ~1/3 of all Lilli usage is auto-generated decks, saving 90-120 minutes each. Cross-checks facts against RAG knowledge base, attaches inline citations, flags unsupported claims.

### Items to modify

- **Marp**: Still active and excellent with Claude Code. MCP servers exist for AI-powered Marp generation. Better for internal presentations than client deliverables.
- **Slidev**: Growing rapidly. Works well with Claude Code. Vue.js powered with PDF/PPTX export.
- **pandoc/weasyprint**: Remain solid infrastructure components but are not the primary path. Claude Skills + code execution are more direct.
- **Chart generation**: Update to include matplotlib/plotly via Claude Code's code execution, Powerdrill Bloom, Tableau Agent, and Manus (now Meta—deploys hundreds of parallel agents for research + visualization + report generation).

---

## C4: Data retrieval architecture

The vector database landscape has matured with clear positioning, and the MCP ecosystem has created turnkey data source integrations.

### Items to remove

None. All referenced databases remain active.

### Items to add

- **pgvectorscale** (Timescale): Game-changer. **471 QPS at 99% recall on 50M vectors—11.4x better than Qdrant** in benchmarks. Makes pgvector competitive with dedicated vector DBs for most use cases (<10M vectors).
- **LanceDB**: DuckDB integration, SQL-like hybrid search, composable retrieval. Growing fast.
- **RAG architecture evolution**: Naive RAG is dead in production. Modular RAG (query rewriting → hybrid search → reranking → context assembly) is baseline. Agentic RAG and Multi-Agent RAG patterns emerging for complex research. **Self-RAG** with self-correcting architecture and reflection tokens.
- **Hybrid search as production baseline**: Dense vectors (semantic) + sparse BM25 (keyword) consistently outperforms either alone. **+7.2% Recall@5, +18.5% MRR improvement** documented. Adaptive chunking (87% accuracy) vs fixed-size (13%) is a massive quality gap.
- **Jina reranker-m0**: 2.4B parameter multimodal reranker. Reranking is now considered essential post-retrieval.
- **RAGAS evaluation framework**: De facto standard for measuring retrieval and generation quality.
- **Exa MCP server** with category-based search: Specialized indexes for people (1B+), companies (50M+), research papers (100M+), plus code search. Token-efficient highlights feature reduces costs 50%+.
- **SEC EDGAR MCP servers**: EdgarTools MCP (free, MIT, 13 tools, 30+ form types, live filings monitor), stefanoamorelli/sec-edgar-mcp (Docker-ready), Apify SEC EDGAR MCP (13M+ filings).
- **Government Data MCP** (lzinga): **36 US government APIs / 188 tools** covering Treasury, FRED, BLS, BEA, EIA, Census, FEC, Congress, SEC, FBI, World Bank, CDC.
- **Financial Modeling Prep MCP**: Dedicated server covering equities, financials, earnings, SEC filings, ETFs, indices, macro indicators.
- **Academix MCP**: Unified academic search across OpenAlex, DBLP, Semantic Scholar, arXiv, CrossRef.

### Items to modify

- **Vector database landscape**: Present as a mature market with clear positioning. Qdrant (v1.15.2, server-side IDF, Rust-based), Pinecone (fully managed, SOC 2/HIPAA), Weaviate (built-in BM25, GraphQL), Milvus/Zilliz (billions scale, GPU), ChromaDB (v1.5.5, still not production-grade—no horizontal scaling or native hybrid search), pgvector (competitive with pgvectorscale for <10M vectors).
- **Hybrid search**: Upgrade from optional feature to **required production baseline**. Every major vector DB now supports it.
- **RAG**: Update from simple retrieve-augment-generate to the seven-tier architecture (Naive → Modular → Hybrid → Graph → Agentic → Multi-Agent → Self-RAG).
- **News APIs**: Add the MCP ecosystem (Tavily with real-time search, Government Data MCP for macro data, Financial Modeling Prep for market data).

---

## D1: Best AI agent systems by individuals and small teams

The landscape of impressive individual projects has shifted dramatically. OpenClaw is the breakout phenomenon, and several new star projects have emerged.

### Items to remove

- **"Dan Malone's OpenClaw mission control"**: No evidence of this project found. OpenClaw's creator is **Peter Steinberger** (Austrian developer, former PSPDFKit founder). Remove this reference.
- **"OpenClaw multi-agent kit by raulvidis"**: Not found. OpenClaw is by steipete (Peter Steinberger). Remove this specific attribution.
- **"Dark factory implementations"**: Too vague, no relevant results found. Remove or replace with specific examples.

### Items to add

- **Peter Steinberger's OpenClaw** (210,000+ stars): Fastest-growing open-source project in GitHub history. Autonomous always-on agent that browses web, fills forms, runs shell, writes code, controls smart home, writes its own skills. 5,700+ community skills. Started as "Clawdbot," renamed after Anthropic trademark complaint. Steinberger joined OpenAI Feb 2026; project moved to open-source foundation. Security concerns documented (Cisco found malicious data-exfiltrating skill).
- **obra/Superpowers** (113.5K stars, #1 trending March 2026): Agentic skills framework and software development methodology. Composable skills with SKILL.md files. Planning process creates precisely crafted context. Allows using cheaper models for implementation.
- **Karpathy's autoresearch details**: 42K+ stars. 630 lines of Python. 126 experiments, 23 improvements (18% keep rate). Also released MicroGPT (Feb 2026, GPT from scratch in 243 lines). Vision: "emulate a research community" of collaborating agents.
- **Willison's Agentic Engineering Patterns** (Feb 2026): Comprehensive documentation of coding practices for agent-era development including "preserve domain expertise," Red/Green TDD for agents, linear walkthroughs.
- **garrytan/gstack**: Y Combinator president's project, 23K stars in first week. Opinionated agent configurations.
- **Agency-Agents**: 48 AI agents in specialist roles working like a digital agency. 36 workflow skills.
- **affaan-m/everything-claude-code**: Claude Code optimization configurations, +36K monthly stars.
- **mvanhorn/last30days-skill** (8.4K stars): Researches topics across Reddit, X, YouTube, HN, Polymarket, then synthesizes grounded summaries.
- **GPT Researcher**: Framework for automated deep research with parallel agents and citation-backed reports.

### Items to modify

- **Karpathy**: Major update with autoresearch release details and its ecosystem of forks. He coined "vibe coding → agentic engineering → fully independent research" as the three phases.
- **Simon Willison**: Update with Agentic Engineering Patterns guide, LLM tool v0.29, and his role as the preeminent practitioner-voice on LLMs.
- **swyx**: Now at Cognition (Devin team), editing Latent.Space (80K+ AINews subscribers), running AI Engineer conferences globally. SmolAI research agents relevant as pattern for automated research workflows.
- **Harrison Chase**: Focus on LangGraph specifically (the production component) rather than just LangChain. Used by Klarna, Uber, LinkedIn. 34.5M monthly downloads.
- **199-biotechnologies**: Confirm the ecosystem exists (engram, claude-deep-research-skill, autoresearch-cli, agent-cli-framework by Boris Djordjevic). Reposition from "GitHub trending" to "specialized deep research tooling ecosystem."

---

## D2: Academic research on automated analysis

Several foundational papers need updating and important new publications must be added.

### Items to remove

None require full removal. All referenced topics remain active research areas.

### Items to add

- **"Debate or Vote" (NeurIPS 2025 Spotlight)**: Majority voting alone accounts for most multi-agent debate gains. Debate as stochastic process forms a martingale.
- **Self-MoA / "Rethinking Mixture-of-Agents" (ICLR 2025)**: Single best model outperforms mixed models by 6.6%.
- **Attention-MoA (2026)**: Small open-source model ensembles outperform Claude-4.5-Sonnet and GPT-4.1.
- **The AI Scientist (Nature 2026)**: End-to-end research automation. 1/3 workshop acceptance. Documented failure modes.
- **SE-Jury (ASE 2025)**: Ensemble judge with 34-113% improvement over single judges.
- **Agent-as-a-Judge (arXiv:2508.02994)**: Evaluation of dynamic agent behavior, not just static outputs.
- **"When AIs Judge AIs" survey**: Evolution from single-model judges to multi-agent debate to agent-as-a-judge.
- **DeepResearch Bench**: 100 PhD-level tasks across 22 fields with active leaderboard.
- **"Characterizing Deep Research"**: Proposes DR task as a DAG of information synthesis.
- **Meta HyperAgents (arXiv:2603.19461)**: Metacognitive self-modification, cross-domain transfer.
- **"Society of Thought" (Kim et al., 2026)**: Reasoning models spontaneously simulate multi-agent debate internally.
- **Evans et al. (Science 2026)**: "Agentic AI and the next intelligence explosion."
- **Comprehensive multi-agent surveys**: Li et al. (Vicinagearth/Springer 2024), Chen et al. (Dec 2024), Plaat et al. (March 2025), plus Awesome-Agent-Papers GitHub repo.
- **"ARTIST" (ICML 2025)**: Agentic Reasoning and Tool Integration in Self-improving Transformers.
- **ICLR 2025 papers**: ADAS (meta-agents inventing agent architectures), "Breaking Mental Set through Diverse Multi-Agent Debate."

### Items to modify

- **Multi-agent debate papers**: Frame the literature as showing a more nuanced picture than "debate always helps." Ensemble voting may matter more than the debate itself. Diversity of model families matters more than number of debaters.
- **Mixture of Agents**: Update to ICLR 2025 Spotlight, ~266 citations, with the critical Self-MoA counterpoint.
- **NeurIPS/ICML/ICLR**: Update to reflect 2025 proceedings (now published) and 2026 early papers. NeurIPS 2025 processed ~21.6K submissions.

---

## D3: What would make this 10x better

Blue-sky capabilities from adjacent fields are now increasingly production-ready.

### Items to remove

None. This prompt is about aspiration and inspiration—breadth is appropriate.

### Items to add

- **Intelligence analysis tools**: Maltego (graph-based OSINT, 120+ integrations), SpiderFoot (100+ sources), Fivecast (ONYX/LUNEX/MATRIX). OSINT market expected to reach $29.19B by 2026. ICD 203 analytical standards as quality framework.
- **CausalAgent** (Feb 2026, IUI Conference): Conversational multi-agent system for end-to-end causal inference using LangGraph, RAG, and MCP. Upload dataset + ask natural language questions → interactive analysis report. Also **MATMCD**: up to 66.7% reduction in causal inference errors. And **causaLens**: commercial "PhD-level Economist" agent.
- **Financial due diligence AI**: AlphaSense (90% of top asset management firms), Kira Systems (90%+ accuracy on contracts), Datasite (AI-powered VDR), Spellbook (2,300+ contract types). McKinsey's five-step gen AI integration for diligence.
- **Competitive intelligence**: AlphaSense "Smart Synonyms" technology, PitchBook/CB Insights AI-enhanced tracking, dynamic peer set construction scanning earnings transcripts and patent filings.
- **Multimodal analysis**: Qwen 3.5 (text, images, audio, video), GPT-5.4 capabilities (76K photos for $52), Google ADK native multimodal via Gemini. Document analysis of PDFs, scanned docs, charts, diagrams.
- **Code execution for quantitative analysis**: Claude Code, Cursor Agent Mode (8 parallel agents via git worktrees), ChatGPT Code Interpreter. The autoresearch pattern (write code → execute → evaluate → iterate) applies to quantitative analysis beyond ML.
- **Real-time monitoring**: Fivecast continuous monitoring, Improvado AI Agent for anomaly detection, Claude Cowork scheduled tasks (Feb 2026). Pattern shift from on-demand to always-on with alerts.
- **Manus (Meta)**: Autonomous agent deploying hundreds of parallel agents for research, data analysis, visualization, and complete structured report generation. "Wide Research" feature.
- **"Cite-or-it-dies" policy**: Emerging from StackAI and others as a requirement for any factual claim in AI-generated consulting output.

### Items to modify

- **Adjacent fields framing**: These are no longer hypothetical adjacencies—production tools exist in each domain. The prompt should reference specific tools and documented capabilities rather than abstract possibilities.
- **Causal inference**: Upgrade from theoretical aspiration to production-ready differentiation opportunity. CausalAgent and causaLens demonstrate feasibility.
- **Multimodal**: Upgrade from future capability to current reality across all major model providers.

---

## Cross-cutting themes the prompts should collectively address

Five overarching shifts affect all 14 prompts and should be woven throughout:

**The spec-driven paradigm** has won. AGENTS.md under the Linux Foundation, GitHub Spec Kit at 72.7K stars, and AWS building an entire IDE (Kiro) around specifications represent a fundamental shift. Every prompt touching on system architecture should reference this.

**MCP and A2A as the protocol layer** are now the shared infrastructure. MCP (97M+ monthly downloads, Linux Foundation governance) for agent-to-tool connectivity and A2A (150+ partners) for agent-to-agent communication are the universal integration standards. Every tool and framework reference should note MCP/A2A support.

**The "taste and judgment" discourse** is the quality framework for 2026. Graham's taste thesis, the Stripe Press "Tacit" series, the HBR "judgment gap" article, and the IMF note on judgment as wealth determinant collectively define how the field thinks about AI output quality. All quality-related prompts (B1-B4) should integrate this.

**Ensemble evaluation over single-model judgment** is the empirical consensus. SOS-Bench, CALM, SE-Jury, MAJ-EVAL, and the "Debate or Vote" paper collectively demonstrate that multi-model evaluation with majority voting across diverse families reduces biases 30-40%. The system's quality assurance architecture should be built on this finding.

**Self-improvement has gone mainstream.** Karpathy's autoresearch, Meta's HyperAgents, OpenSpace, and DSPy's GEPA optimizer have moved autonomous self-improvement from theory to practice. The consulting system should incorporate ratchet-loop optimization from day one, not treat it as a future enhancement.