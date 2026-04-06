does claude code have a native deep research functionality like the web ui? am i able to use claude deep research as an api call?

Mar 27  
Clarified feature availability across platforms and API limitations  
Clarified feature availability across platforms and API limitations

No on both counts.

**Claude Code**: No native deep research. Research is available for users with [Claude](https://support.claude.com/en/articles/11088861-using-research-on-claude) paid Claude plans (Pro, Max, Team, or Enterprise) using Claude on the web, Claude Desktop, or Claude Mobile. It's a product-level feature, not something exposed through Claude Code's toolset.

**API**: There's no deep research API endpoint. You can't call it programmatically the way you'd hit `/v1/messages`.

**What people actually do instead**: The community has converged on building deep research as a Claude Code workflow rather than waiting for a native feature. Three main patterns:

1. **Multi-agent spawning** (simplest): The simplest approach uses about 20 lines of shell with zero dependencies, using the flag `--allowedTools "Bash(claude:*)"` to let Claude spawn more Claude instances that run searches in parallel. [Emergent Minds](https://paddo.dev/blog/three-ways-deep-research-claude/)  
2. **MCP server approach**: Projects like `claude-deep-research` integrate search providers (DuckDuckGo, Semantic Scholar, Brave, etc.) as MCP tools that Claude Code can call during a research session.  
3. **Custom skill packages**: There's an enterprise-grade deep research skill for Claude Code with an 8-phase pipeline, source credibility scoring, and automated validation that you install into your `~/.claude/skills/` directory. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill) That one (199-biotechnologies) is probably the most production-ready option and would slot right into your existing OpenClaw/Claude Code setup.

Given your Mac Mini setup with Claude Max via proxy, option 3 is the most relevant. You'd clone the skill into your Claude Code skills directory and invoke it with natural language like "deep research on \[topic\]." It handles parallel search, source triangulation, citation verification, and outputs structured reports. The multi-agent spawning approach (option 1\) is also worth knowing about since it's dead simple and you're already comfortable with Claude Code's architecture.

do more detailed research on claude code skills or other systems that people have set up in their claude code and openclaw to give it access to deep research which is on par with or ideally even rivals the native deep research functionality embedded in the claude.ai site/app

Mar 27  
Synthesized comprehensive findings for detailed response  
Synthesized comprehensive findings for detailed response

Here's the landscape, organized by approach from simplest to most production-ready.

---

**Tier 1: Minimal recursive spawning (Cranot's approach)**

Cranot's `:antCitation[]{citations="d3626f65-60d2-470a-a85f-6e04380fbf4a"}deep-research` repo has evolved well beyond the original 20-line shell script. It now supports 7 LLM providers (Claude, Gemini, OpenAI/Azure, OpenRouter/Grok, Kimi), 4 research strategies (Recursive, Socratic, Perspective-based, Grounded/web-verified), multi-model ensembles where multiple models answer then merge perspectives, parallel execution with configurable limits, persistent checkpoints for resuming interrupted research, and typed knowledge graphs tracking the epistemic state of every finding.

The core architecture is still elegant: an orchestrator decomposes questions into sub-questions, spawns sub-agents to answer them in parallel, detects blind spots and tensions, grounds claims with web search verification, and synthesizes everything back up. The key flag is `--allowedTools "Bash(claude:*)"` which lets Claude spawn more Claude instances, and results flow back up into synthesis. [Emergent Minds](https://paddo.dev/blog/three-ways-deep-research-claude/)

For your setup: this works natively with your Claude Max subscription since it can use the Claude CLI (subscription-based provider). You'd clone it, `pip install -e .`, set your `ANTHROPIC_API_KEY`, and run queries from terminal or have OpenClaw invoke it. Cost warning: recursive spawning burns tokens fast, and a deep research query can easily hit $1-5 in API costs. Research takes 30-90+ seconds minimum. [Emergent Minds](https://paddo.dev/blog/three-ways-deep-research-claude/)

**Strengths**: Highest ceiling, multi-model verification, no framework lock-in. **Weakness**: Token-expensive, requires API keys (not just Max subscription) for multi-model mode.

---

**Tier 2: 199-Biotechnologies deep-research skill (most turnkey for Claude Code)**

This is the one most directly comparable to native Claude.ai Research. It explicitly claims to match and exceed Claude Desktop's Advanced Research feature, with an 8-phase pipeline, source credibility scoring (0-100 per source), graph-of-thoughts non-linear exploration, automatic citation management, a built-in critique/red-team phase, and a refine phase that addresses gaps before finalizing. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill/blob/main/QUICK_START.md)

The 8 phases: Scope, Plan, Retrieve (parallel search \+ agents), Triangulate, Outline Refinement, Synthesize, Critique (with loop-back), Refine, Package. It runs 5-10 concurrent searches plus 2-3 focused sub-agents returning structured evidence objects. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill)

Four research modes with different depth/speed tradeoffs: Quick (3 phases, 2-5 minutes), Standard (6 phases, 5-10 minutes), Deep (8 phases, 10-20 minutes), and UltraDeep (8+ phases, 20-45 minutes). [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill/blob/main/QUICK_START.md)

The architecture review shows it outperforms competitors on validation (automated 8-check system vs. undocumented), failure handling (explicit stop rules \+ error gates), and credibility scoring (quantitative 0-100 system vs. basic triangulation). It ties on graph-of-thoughts/subagent spawning. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill/blob/main/ARCHITECTURE_REVIEW.md?plain=1)

It's designed for fully autonomous operation. It proceeds without user input by default, makes reasonable assumptions based on query context, and only asks if the query is genuinely incomprehensible or contradictory. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill/blob/main/AUTONOMY_VERIFICATION.md) Reports over 18K words auto-continue via recursive agent spawning with context preservation, and there's an automated validation loop (validate, fix, retry, max 3 cycles) with DOI/URL/hallucination detection. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill)

Installation is one command:

bash  
git clone https://github.com/199-biotechnologies/claude-deep-research-skill.git \~/.claude/skills/deep-research

For enhanced search (beyond Claude Code's built-in WebSearch/WebFetch): Install their `search-cli` for aggregated search across Brave, Serper, Exa, Jina, and Firecrawl: `brew tap 199-biotechnologies/tap && brew install search-cli`, then configure at least one provider key. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill)

It uses only Python standard library for basic usage, so no pip install is needed. [GitHub](https://github.com/199-biotechnologies/claude-deep-research-skill/blob/main/QUICK_START.md)

**For your OpenClaw setup**: Since OpenClaw runs Claude Code under the hood, this skill would be available to your Telegram agent if it's in the agent's workspace skills directory (e.g., `~/.openclaw/workspace/skills/deep-research/` or `~/.claude/skills/deep-research/`). You'd trigger it with natural language: "deep research on \[topic\]" or "deep research in ultradeep mode: \[topic\]".

**Strengths**: Zero-config, autonomous, built-in validation, directly comparable to native Research feature. **Weakness**: Single-model (Claude only), relies on Claude Code's built-in web search unless you add `search-cli`.

---

**Tier 3: Weizhena's Deep-Research-skills (human-in-the-loop variant)**

This is a structured two-phase research workflow: outline generation (extensible) followed by deep investigation, with human-in-the-loop design for control at every stage. It supports Claude Code, OpenCode, and Codex. [GitHub](https://github.com/Weizhena/Deep-Research-skills)

It requires installing a web-search-agent alongside the skill files, plus `pyyaml` as a dependency. [GitHub](https://github.com/Weizhena/Deep-Research-skills) The key difference from 199-bio is the human-in-the-loop philosophy: it generates an outline first, lets you modify/extend it, then investigates each item deeply. Better for situations where you want to steer the research direction rather than fire-and-forget.

Use cases: academic paper surveys, benchmark reviews, technology comparisons, framework evaluations, market/competitor analysis, due diligence, and investment analysis. [GitHub](https://github.com/Weizhena/Deep-Research-skills)

**Strengths**: You control the research scope before it burns tokens. Good for focused investigations where you know what you're looking for. **Weakness**: Not autonomous. Requires your interaction between phases.

---

**Tier 4: Academic-focused (Imbad0202's academic-research-skills)**

This is a full 10-stage academic pipeline: Research, Write, Integrity Check, Review (5-person panel), Socratic Coaching, Revise, Re-Review, Re-Revise, Final Integrity Check, Finalize, with a process summary and collaboration quality evaluation. [GitHub](https://github.com/Imbad0202/academic-research-skills) It includes a Socratic Mentor Agent with a State-Challenge-Reflect protocol that detects high-confidence language and introduces counterpoints.

Recommended model is Opus 4.6 with Max plan. A single end-to-end run can exceed 200K input \+ 100K output tokens. [GitHub](https://github.com/Imbad0202/academic-research-skills) Outputs APA 7.0 formatted papers in LaTeX/DOCX/PDF.

Relevant for your G400 capstone-style work or the performative negotiation paper, but overkill for general research queries.

---

**Search backend layer (the foundation all of these need)**

The quality ceiling of any deep research system is bounded by its search quality. Claude Code has built-in WebSearch and WebFetch tools [Apiyi.com Blog](https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html), but the MCP search ecosystem provides much richer options:

* **Brave Search MCP**: General web search, free tier available. `claude mcp add brave-search npx -y @anthropic/mcp-brave-search --api-key YOUR_KEY` [Apiyi.com Blog](https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html)  
* **Exa MCP**: Excels at semantic search and code search, great for research-type queries. [Apiyi.com Blog](https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html) Has ready-to-use Claude Code skills for company research, people research, and code context search, each running in forked context to avoid polluting your main conversation. [GitHub](https://github.com/exa-labs/exa-mcp-server)  
* **Tavily MCP**: Free tier provides 1,000 queries per month, suited for technical documentation search. [Apiyi.com Blog](https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html)  
* **SearXNG MCP**: Privacy-respecting metasearch engine, requires your own SearXNG instance with JSON mode enabled. [LobeHub](https://lobehub.com/mcp/deedoi-brave-search-with-claude-mcp-on-macos) You were already looking at self-hosting SearXNG, so this slots right in.

For your Mac Mini setup, the strongest search configuration would be: Brave (broad web) \+ Exa (semantic/academic) \+ your self-hosted SearXNG (privacy-first fallback), all configured as MCP servers. The 199-bio `search-cli` aggregates across multiple providers if you want a single interface instead.

---

**My recommendation for your specific setup**

Given your OpenClaw on Mac Mini with Claude Max via proxy and Telegram interface:

1. **Install the 199-bio skill** as your primary deep research capability. It's the most autonomous, requires zero interaction, and its output quality is competitive with native Research. Clone it into your OpenClaw workspace's skills directory.  
2. **Add Brave \+ Exa MCP servers** to your OpenClaw agent's MCP config for richer search than Claude Code's built-in WebSearch provides.  
3. **Keep Cranot's `deep-research`** in your back pocket for queries where multi-model verification matters (e.g., checking whether multiple LLMs agree on a factual claim). This is the only option that does true cross-model triangulation.  
4. **Set up a dedicated research agent in OpenClaw** using the multi-agent routing you already know. Create a second agent with its own Telegram bot, fully isolated workspace, and route it to Opus 4.6 for research queries while keeping your everyday agent on Sonnet for speed. [GitHub](https://gist.github.com/bdennis-dev/b876ab61047df62561cf163c4a4d5bca) The research agent's workspace gets the deep-research skill, heavier search MCP config, and a SOUL.md tuned for thorough investigation.

The gap between this setup and native Claude.ai Research is mostly in the search layer (Anthropic's native Research has direct integrations with Google Workspace, Gmail, etc. that MCP servers approximate but don't fully replicate) and in UX polish (progress streaming, inline citations). The actual research depth and verification quality from the 199-bio skill is arguably stronger than native Research for most queries because it has explicit validation, critique, and credibility scoring phases that native Research doesn't expose.

i was about to give you the following prompt below, but instead i had another claude instance create it for a separate chat (not this chat). what i need you to do is to remove outdated infomration from the following prompt based on your research.  i dont want it looking into architectures which are outdated/which have better current alternatives. analyze the prompt below and do some research to figure out which items should be added, modified, or removed:

"

I'm building a multi-agent AI system for automated consulting research and analysis called the Keystone Intelligence Engine. Before building, I need to map what already exists.

Find and deeply evaluate every open-source project, framework, or system that does multi-agent research, analysis, or report generation. I'm looking for systems that:  
\- Take a research question and produce structured analytical output  
\- Use multiple agents in a pipeline (decomposition → research → synthesis → evaluation)  
\- Include quality evaluation or verification steps  
\- Generate research reports, market analyses, competitive landscapes, or similar

Specifically investigate:  
\- GPT-Researcher (assafelovic/gpt-researcher) — how does its architecture compare?  
\- STORM (stanford-oval/storm) — Stanford's research paper generation system  
\- AutoGPT, BabyAGI, and their current state (many are abandoned)  
\- CrewAI, AutoGen, LangGraph — as orchestration frameworks  
\- Any consulting-specific or business-analysis-specific AI tools  
\- Tavily's research API and how production systems use it  
\- Perplexity's architecture (to the extent it's public)  
\- Any papers or projects on "automated consulting" or "AI-assisted strategy analysis"

For each system found, analyze:  
1\. Architecture (how agents coordinate, what the pipeline looks like)  
2\. Quality control (how they handle evaluation, verification, hallucination)  
3\. Strengths we should learn from  
4\. Weaknesses or gaps our system addresses  
5\. Components we could directly use or integrate rather than building from scratch  
6\. How actively maintained it is (stars, commits, community)

I want to know: what already works, what's been tried and failed, and where the genuine gaps are that our system fills."

"

again dont execute that prompt^ just help me optimize it

Show more  
Mar 27  
Assessing research landscape and identifying optimization opportunities  
Assessing research landscape and identifying optimization opportunities

Let me check the current state of the specific projects and frameworks mentioned.

Assembled framework analysis to optimize research prompt  
Assembled framework analysis to optimize research prompt

Here's my analysis of the prompt, item by item, with recommended changes:

---

**REMOVE: BabyAGI**

BabyAGI is a 2023 reference architecture, not a production system. It's a minimal agent loop that was more of a conceptual proof than a product, and its architecture turned out to be overkill for what it actually did. [Medium](https://medium.com/@roseserene/agentic-ai-autogpt-babyagi-and-autonomous-llm-agents-substance-or-hype-8fa5a14ee265) Its educational value is its biggest strength [Fast](https://fast.io/resources/top-10-open-source-ai-agents/), and at under 500 lines of Python, it's a teaching tool. There's nothing architecturally relevant to learn from it that isn't better demonstrated by the systems you'd actually use. It belongs in a footnote at most, not a research target.

**REMOVE: AutoGPT**

Same era, same problem. AutoGPT launched the autonomous agent category in 2023 and remains actively maintained [Fast](https://fast.io/resources/top-10-open-source-ai-agents/), but it's a general-purpose autonomous agent, not a research system. Its contribution was proving that LLM agent loops could work at all. That question is settled. Every system you'd actually build on has moved past its architecture. Listing it alongside GPT-Researcher or STORM conflates "historically significant" with "architecturally useful."

**KEEP: GPT-Researcher (update framing)**

GPT Researcher is the OG open-source deep research agent, with 25.7k stars, Apache-2.0 license, active since May 2023\. It's the longest-running and most battle-tested deep research agent in the ecosystem. [Rywalker](https://rywalker.com/research/gpt-researcher) It's actively maintained with recent releases, now includes a comprehensive Claude Code skill directory [GitHub](https://github.com/assafelovic/gpt-researcher/releases), has an MCP server for integration, and includes Deep Research mode with tree-like exploration of configurable depth and breadth. [GitHub](https://github.com/assafelovic/gpt-researcher) The planner/execution architecture is directly relevant to what you're building. The prompt should frame it as a primary reference implementation, not just one of many.

**KEEP: STORM (update framing)**

STORM is actively maintained with a live research preview that over 70,000 people have tried. [GitHub](https://github.com/stanford-oval/storm) It now has Co-STORM for human-AI collaborative research, supports multiple retrieval modules including Brave, SearXNG, DuckDuckGo, Tavily, and Google Search [GitHub](https://github.com/stanford-oval/storm), and has published papers at NAACL and EMNLP. Its multi-perspective question-asking architecture is genuinely novel and directly applicable to consulting research where you need to explore a topic from multiple stakeholder angles. Keep it, but position it as the academic gold standard for the pre-writing/research stage.

**KEEP: CrewAI, LangGraph (update to reflect current differentiation)**

Both are actively maintained and widely adopted. They solve different engineering problems: LangGraph is built for explicit state and control flow, CrewAI is built for quickly assembling role-based workflows. [Medium](https://medium.com/data-science-collective/langgraph-vs-crewai-vs-autogen-which-agent-framework-should-you-actually-use-in-2026-b8b2c84f1229) For production multi-agent pipelines with cycles and complex state, LangGraph is the standard; for rapid prototyping with role-based agents, CrewAI has the lowest barrier to entry. [DEV Community](https://dev.to/synsun/autogen-vs-langgraph-vs-crewai-which-agent-framework-actually-holds-up-in-2026-3fl8) The prompt should distinguish between them as orchestration frameworks rather than lumping them together.

**MODIFY: AutoGen (downgrade)**

Microsoft has shifted AutoGen to maintenance mode in favor of the broader Microsoft Agent Framework. Major new feature development has slowed. [Openagents](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) The v0.4 rewrite (AG2) exists but is still maturing. It receives bug fixes and security patches but strategic focus has moved. [GuruSup](https://gurusup.com/blog/best-multi-agent-frameworks-2026) It's worth mentioning as context (conversational multi-agent pattern) but not worth deep investigation. Replace the deep-dive with a single line acknowledging it's in maintenance mode.

**ADD: Claude Agent SDK / Claude Code skills ecosystem**

This is the most directly relevant thing the prompt is missing. Claude Code natively supports skills with frontmatter, forked subagent contexts, and multi-agent orchestration. [Claude](https://code.claude.com/docs/en/skills) The 199-bio deep-research skill, Cranot's recursive spawning approach, and the Weizhena structured research skill are all production systems built on this pattern. Since you're building on Claude infrastructure via OpenClaw, this is your actual deployment surface.

**ADD: OpenAgents**

OpenAgents is the only framework with native support for both MCP and A2A (Agent-to-Agent) protocols as of 2026\. [Openagents](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared) If you're building a system that needs to interoperate with external agent networks or use MCP servers (which you already do via OpenClaw), this is architecturally relevant.

**ADD: Google ADK**

Released April 2025, Google's ADK provides hierarchical agent trees where a root agent delegates to sub-agents, with native A2A protocol support enabling cross-framework agent communication. [GuruSup](https://gurusup.com/blog/best-multi-agent-frameworks-2026) Worth evaluating for the hierarchical delegation pattern.

**MODIFY: Tavily (expand scope)**

Tavily is just one search provider. The prompt should broaden to "search infrastructure layer" covering Tavily, Brave Search API, Exa (semantic search), SearXNG (self-hosted metasearch), Jina, and Firecrawl. The search backend is the quality ceiling for any research system, and the landscape has matured significantly. Exa excels at semantic search and code search, great for research-type queries [Apiyi.com Blog](https://help.apiyi.com/en/claude-code-web-search-websearch-mcp-guide-en.html), and Brave has an official MCP server.

**MODIFY: Perplexity reference**

Perplexity's architecture is still not meaningfully public. Keep as a competitive benchmark but don't spend research effort trying to reverse-engineer it. Instead, note that Carnegie Mellon's DeepResearchGym evaluated leading deep research systems on 1,000 complex queries, and GPT Researcher outperformed Perplexity, OpenAI, and others in citation quality, report quality, and information coverage. [GPT Researcher](https://gptr.dev/) That benchmark is more useful than speculating about Perplexity's internals.

**ADD: Consulting-specific framing**

The prompt asks for "automated consulting" tools but doesn't reference the most relevant architectural patterns: the McKinsey-style report template in the 199-bio skill, the multi-persona red teaming (Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer), or the critic-loop architectures that are becoming standard. These are the patterns closest to what a consulting research engine actually needs.

---

Here's the revised prompt:

markdown  
I'm building a multi-agent AI system for automated consulting research   
and analysis called the Keystone Intelligence Engine. Before building,   
I need to map what already exists.

Find and deeply evaluate every open-source project, framework, or system   
that does multi-agent research, analysis, or report generation. I'm   
looking for systems that:  
\- Take a research question and produce structured analytical output  
\- Use multiple agents in a pipeline (decomposition → research →   
  synthesis → evaluation)  
\- Include quality evaluation, verification, or red-teaming steps  
\- Generate research reports, market analyses, competitive landscapes,   
  or consulting deliverables

**\#\# Primary Systems to Investigate**

\*\*Research Agents (evaluate deeply):\*\*  
\- GPT-Researcher (assafelovic/gpt-researcher) — the longest-running   
  open-source deep research agent. Planner/execution architecture,   
  Deep Research mode with tree-like exploration, MCP server, Claude   
  Code skill integration. How does its pipeline compare to what we   
  need?  
\- STORM / Co-STORM (stanford-oval/storm) — Stanford's multi-perspective   
  research system. Unique approach of simulating expert conversations   
  from different perspectives. Co-STORM adds human-in-the-loop.   
  Evaluate the perspective-guided question-asking pattern for   
  consulting use cases.  
\- 199-Biotechnologies deep-research-skill — 8-phase pipeline   
  (Scope→Plan→Retrieve→Triangulate→Outline→Synthesize→Critique→Refine)   
  built as a Claude Code skill. Source credibility scoring, multi-persona   
  red teaming, auto-continuation for long reports. Most directly   
  comparable to what we're building.  
\- Cranot/deep-research — Multi-model recursive agent spawning with   
  knowledge graphs and epistemic state tracking. Supports 7 LLM   
  providers and 4 research strategies.  
\- Weizhena/Deep-Research-skills — Structured two-phase research with   
  human-in-the-loop control. Worth evaluating for the outline-first   
  approach.

\*\*Orchestration Frameworks (evaluate as infrastructure options):\*\*  
\- LangGraph — Graph-based state machines, best production readiness   
  (LangSmith observability, checkpointing, streaming). The standard   
  for complex pipelines with cycles.  
\- CrewAI — Role-based agent teams, fastest prototyping, growing A2A   
  support. Best for linear multi-agent workflows.  
\- Claude Agent SDK — Anthropic's agent harness (renamed from Claude   
  Code SDK). Native tool use, MCP integration, subagent spawning.   
  Our most likely deployment surface given the OpenClaw/Claude Code   
  stack.  
\- OpenAgents — Only framework with native MCP \+ A2A protocol support.   
  Evaluate for cross-framework agent interoperability.  
\- AutoGen/AG2 — Note: Microsoft shifted to maintenance mode.   
  Conversational multi-agent pattern is architecturally interesting   
  but not actively developed. Don't deep-dive.

\*\*Search Infrastructure Layer:\*\*  
\- Tavily Search API (GPT-Researcher's default)  
\- Brave Search API \+ MCP server  
\- Exa (semantic search, strong for research queries)  
\- SearXNG (self-hosted metasearch, privacy-first)  
\- Jina, Firecrawl (content extraction/crawling)  
\- How do production research systems compose multiple search providers?

\*\*Benchmarks and Competitive Context:\*\*  
\- CMU DeepResearchGym benchmark results (GPT Researcher vs Perplexity   
  vs OpenAI on 1,000 complex queries)  
\- Claude.ai native Research feature (the UX/quality bar we're   
  competing with)  
\- ChatGPT Deep Research (the other commercial benchmark)  
\- Any papers on "automated consulting," "AI-assisted strategy analysis,"   
  or multi-agent research verification

**\#\# For Each System Found, Analyze:**  
1\. Architecture (how agents coordinate, what the pipeline looks like,   
   how state flows between phases)  
2\. Quality control (evaluation, verification, hallucination detection,   
   source credibility scoring, red-teaming)  
3\. Search infrastructure (which providers, how they handle multi-source   
   triangulation)  
4\. Strengths we should learn from  
5\. Weaknesses or gaps our system addresses  
6\. Components we could directly use or integrate (MCP servers, skills,   
   search providers) rather than building from scratch  
7\. Maintenance status (recent commits, community size, trajectory)

I want to know: what already works, what's been tried and superseded,   
where the genuine architectural gaps are, and which existing components   
we should compose rather than rebuild.

Key changes in summary: dropped BabyAGI and AutoGPT (historical, not architecturally useful), downgraded AutoGen to a footnote, added the Claude Code skills ecosystem and three specific deep-research skills that are the most relevant prior art, added OpenAgents for protocol interoperability, expanded search infrastructure to cover the full provider landscape, added CMU's DeepResearchGym as a concrete benchmark reference, and restructured the analysis criteria to include search infrastructure and composability as explicit evaluation dimensions.

great. do the same with the following:

"

I'm building a multi-agent research system where the Evaluator is the most important component. I need to find every existing framework, tool, or methodology for evaluating AI-generated research and analytical output.

Search for:  
\- Open-source evaluation frameworks for LLM output quality (not just accuracy — analytical depth, decision-usefulness, intellectual honesty)  
\- Academic papers on automated evaluation of research quality  
\- "LLM-as-judge" implementations and their known failure modes  
\- Rubric-based evaluation systems (not just pass/fail but multi-dimensional scoring)  
\- RAGAS, DeepEval, LangSmith evaluations, Braintrust, and similar tools  
\- Any consulting-specific quality frameworks (McKinsey, BCG, Bain quality standards — to the extent they're public)  
\- Anthropic's published work on model evaluation and the "evaluator problem"  
\- Papers on "calibrating AI evaluators against human judgment"  
\- Anti-gaming strategies — how to prevent models from optimizing for evaluation metrics rather than genuine quality  
\- Factorial evaluation methods — systematically varying inputs to test robustness

For each, I want:  
1\. What it evaluates and how  
2\. Known limitations and failure modes  
3\. Whether it could serve as our Evaluator's backbone or if we need to build custom  
4\. How it handles the "same model evaluating same model" problem  
5\. Whether it supports custom rubrics calibrated to domain-specific standards

"

Show more  
Mar 27  
Synthesized research findings to analyze comprehensive evaluation framework requirements  
Synthesized research findings to analyze comprehensive evaluation framework requirements

Here's my analysis, item by item:

---

**KEEP but REFRAME: RAGAS**

RAGAS is still relevant but its scope is narrower than the prompt implies. RAGAS focuses on research-backed retrieval and generation scoring for RAG pipelines [Braintrust](https://www.braintrust.dev/articles/deepeval-alternatives-2026), with over 400K monthly downloads. But as a pure evaluation framework, RAGAS lacks production observability, experiment tracking, artifact storage, and simulation capabilities. Many platforms, including Maxim AI, now offer RAGAS metrics as built-in features. [Maxim Articles](https://www.getmaxim.ai/articles/top-5-rag-evaluation-platforms-in-2026-2/) It's a metrics library, not an evaluation backbone. The prompt should position it as a component you'd compose into a larger evaluator, not a standalone candidate for "our Evaluator's backbone."

**KEEP but REFRAME: DeepEval**

DeepEval is the strongest open-source option and has matured significantly. It now includes DAG (graph-based deterministic LLM-as-a-judge metric builder) [GitHub](https://github.com/confident-ai/deepeval), G-Eval custom metrics where you define criteria in natural language, support for agentic workflows beyond just RAG [Deepeval](https://deepeval.com/blog/deepeval-vs-ragas), and red teaming via DeepTeam. It's the most complete open-source eval framework available, with 50+ research-backed metrics and pytest integration. [Awesome Agents](https://awesomeagents.ai/tools/best-llm-eval-tools-2026/) For your use case, the G-Eval custom metrics and DAG metric builder are the most relevant features because they let you define consulting-specific rubrics. The prompt should elevate DeepEval from "one of several tools" to "primary open-source candidate."

**KEEP: LangSmith**

Still relevant but only if you're in the LangChain/LangGraph ecosystem. LangSmith is best suited if your stack is centered on LangChain or LangGraph, and framework-native tracing and evaluation are the priority. [Braintrust](https://www.braintrust.dev/articles/deepeval-alternatives-2026) Since LangGraph is one of your orchestration candidates, LangSmith stays. But if you go Claude Agent SDK, it becomes less relevant.

**KEEP: Braintrust**

The prompt mentions it but doesn't emphasize it enough. Braintrust raised $80M in February 2026 at an $800M valuation [Awesome Agents](https://awesomeagents.ai/tools/best-llm-eval-tools-2026/) and connects evaluation scoring with production tracing, dataset management, cross-functional review, and CI-based release enforcement inside a single system. [Braintrust](https://www.braintrust.dev/articles/deepeval-alternatives-2026) It's the only platform that handles the full evaluation lifecycle from dataset to release gate. For a consulting research system where quality is the differentiator, the CI-based release enforcement pattern (output doesn't ship unless it passes eval thresholds) is directly applicable.

**ADD: Inspect AI (UK AISI)**

This is a significant omission from the original prompt. Inspect AI is an open-source Python framework from the UK AI Safety Institute for building and running reproducible LLM evaluations, with 100+ pre-built evaluations. It's adopted by METR, Apollo Research, other government AISIs, and major safety labs. [Substack](https://neurlcreators.substack.com/p/inspect-ai-evaluation-framework-review) Its architecture (Dataset \-\> Task \-\> Solver \-\> Scorer) is the most principled evaluation framework design. It supports model-graded QA, multi-turn/agent workflows with tools, sandboxed execution, and custom metrics. [Substack](https://neurlcreators.substack.com/p/inspect-ai-evaluation-framework-review) For your Evaluator, its composable Scorer system is the right abstraction layer because you can define domain-specific scorers for consulting quality dimensions.

**ADD: Langfuse**

Missing from the prompt entirely. Langfuse offers self-hosted observability [Awesome Agents](https://awesomeagents.ai/tools/best-llm-eval-tools-2026/) under MIT license, which means you can run it on your Mac Mini alongside OpenClaw. It's the open-source alternative to LangSmith for tracing and eval dashboards. Given your self-hosted infrastructure preference, this is more relevant than LangSmith.

**ADD: Arize Phoenix**

Also missing. Open-source, OpenTelemetry-based tracing with pre-built evaluation templates for hallucination detection, relevance, and correctness. Blazing fast performance with built-in concurrency achieving up to 20x speedup in evaluation execution. [Maxim Articles](https://www.getmaxim.ai/articles/the-5-best-rag-evaluation-tools-you-should-know-in-2026/) Self-hostable, framework-agnostic.

**MODIFY: "LLM-as-judge" section (significantly expand with specific papers)**

The prompt's treatment is too vague. The research landscape is now well-characterized. Specific items to investigate:

The CALM framework (from "Justice or Prejudice?" by Ye et al.) identifies 12 distinct bias types and provides an automated bias quantification framework. [OpenReview](https://openreview.net/forum?id=3GTtZFiajM) This is the most comprehensive taxonomy of LLM judge failure modes.

SOS-Bench ("Style Outweighs Substance") found that LLM-judge preferences do not correlate with concrete measures of safety, world knowledge, and instruction following, and that LLM judges have powerful implicit biases prioritizing style over factuality and safety. [OpenReview](https://openreview.net/forum?id=MzHNftnAM1) This is the most important finding for a consulting evaluator because it means a naive LLM judge will rate well-formatted nonsense higher than poorly-formatted insight.

The known bias taxonomy includes position bias (preferring responses based on ordering), verbosity bias (mistaking longer outputs for higher quality), and self-enhancement bias (models rate their own outputs higher than those from other systems). [Weights & Biases](https://wandb.ai/site/articles/exploring-llm-as-a-judge/) The self-enhancement bias directly addresses the prompt's "same model evaluating same model" concern.

The prompt should also reference Prometheus (Kim et al., ICLR 2024), a purpose-built judge model trained specifically for fine-grained evaluation with custom rubrics.

**MODIFY: Anthropic evaluation section (narrow the scope)**

The prompt asks for "Anthropic's published work on model evaluation and the 'evaluator problem'" which is vague. Anthropic's most relevant published work is Constitutional AI (the self-critique and revision loop), Constitutional Classifiers (automated safety evaluation), and AISI's finding that automated grader models can be optimized to increase agreement with human expert graders but show lower inter-rater agreement than humans themselves (Cohen's Kappa 0.52 for AI-human vs 0.8 for human-human). [Aisi](https://www.aisi.gov.uk/blog/advanced-ai-evaluations-may-update) The prompt should cite these specifically rather than hoping the research agent finds them.

**MODIFY: "Consulting-specific quality frameworks"**

The prompt asks for McKinsey/BCG/Bain quality standards "to the extent they're public." They're not public in any useful way. Drop the specific firm names and instead focus on what's actually available: the multi-persona red-teaming patterns from the 199-bio deep-research skill (Skeptical Practitioner, Adversarial Reviewer, Implementation Engineer), the MECE framework as an evaluable property, and academic literature on structured analytical techniques (ACH, SWOT quality criteria, Porter's Five Forces completeness checks). These are things you can actually encode as evaluation rubrics.

**ADD: Anti-gaming and calibration research**

The prompt mentions these but without specific references. Add:

* EvalGen (Shankar et al.) which addresses "criteria drift" where evaluation criteria evolve as reviewers assess more outputs  
* The "evaluator ensemble" pattern where you use multiple judge models and flag disagreements  
* Constitutional AI's self-critique loop as an anti-gaming mechanism (the model critiques its own output against principles before scoring)

**REMOVE: Nothing outright**, but several items need repositioning from "investigate deeply" to "note as context."

---

Here's the revised prompt:

markdown  
I'm building a multi-agent research system where the Evaluator is   
the most critical component. I need to map every existing framework,   
tool, methodology, and research finding relevant to evaluating   
AI-generated research and analytical output.

**\#\# Evaluation Frameworks & Tools**

\*\*Open-source frameworks (evaluate as Evaluator backbone candidates):\*\*  
\- DeepEval — Most complete open-source eval framework. 50+ metrics,   
  G-Eval custom metrics (define criteria in natural language), DAG   
  graph-based deterministic judge builder, pytest integration, CI/CD   
  native. Primary candidate for custom rubric implementation.  
\- Inspect AI (UK AISI) — Government-backed framework for reproducible   
  LLM evaluations. Composable Task→Solver→Scorer architecture. 100+   
  pre-built evals, adopted by METR and Apollo Research. Most principled   
  eval framework design; evaluate its Scorer abstraction for   
  consulting-quality dimensions.  
\- Braintrust — Managed platform connecting dataset management, eval   
  scoring, experiment tracking, and CI-based release enforcement.   
  The release-gate pattern (output doesn't ship unless eval passes)   
  is directly relevant. $80M raise Feb 2026\.

\*\*Metrics libraries (components, not backbones):\*\*  
\- RAGAS — Reference-free RAG evaluation metrics (context precision,   
  recall, faithfulness, answer relevance). 400K+ monthly downloads.   
  Narrow scope: RAG pipelines only, no observability or tracking.   
  Use as a metrics component inside a larger system.  
\- LangSmith — Only relevant if LangGraph is our orchestration layer.   
  Best-in-class tracing and time-travel debugging for LangChain stack.  
\- Langfuse — MIT-licensed, self-hostable observability \+ eval   
  dashboards. More relevant than LangSmith given our self-hosted   
  infrastructure (Mac Mini / OpenClaw).  
\- Arize Phoenix — Open-source, OpenTelemetry-based tracing with   
  pre-built eval templates. Self-hostable, framework-agnostic.

\*\*Specialized eval tools (note for specific capabilities):\*\*  
\- Promptfoo — Red teaming and security validation. Node.js ecosystem.  
\- DeepTeam (from DeepEval) — LLM safety and security testing   
  (bias, toxicity, prompt injection, jailbreaking).  
\- MLflow — Modular eval runner, good for simple QA/RAG evaluation   
  within existing ML pipelines.

**\#\# LLM-as-Judge: Research & Failure Modes**

\*\*Core papers to investigate (these define the field):\*\*  
\- CALM framework / "Justice or Prejudice?" (Ye et al., ICLR 2025\) —   
  Identifies 12 distinct bias types in LLM judges with automated   
  quantification. The most comprehensive bias taxonomy.  
\- SOS-Bench / "Style Outweighs Substance" (ICLR 2025\) — Found LLM   
  judge preferences do NOT correlate with concrete measures of safety,   
  world knowledge, or instruction following. Judges prioritize style   
  over factuality. This is the biggest threat to our Evaluator: a   
  naive judge will rate well-formatted nonsense higher than   
  poorly-formatted insight.  
\- "A Survey on LLM-as-a-Judge" (Gu et al., 2024, arXiv:2411.15594) —   
  Comprehensive survey on building reliable judge systems.  
\- "Evaluating Scoring Bias in LLM-as-a-Judge" (arXiv:2506.22316) —   
  Systematic investigation of bias in scoring-based (not just   
  pairwise) evaluation.  
\- Prometheus (Kim et al., ICLR 2024\) — Purpose-built judge model   
  trained for fine-grained evaluation with custom rubrics. Evaluate   
  whether a specialized judge model outperforms general-purpose   
  models for our domain.

\*\*Known failure modes to design against:\*\*  
\- Position bias: judges prefer responses based on ordering  
\- Verbosity bias: longer outputs scored higher regardless of quality  
\- Self-enhancement bias: models rate own outputs higher (directly   
  relevant to "same model evaluating same model" problem)  
\- Style-over-substance: formatting and tone dominate factual accuracy  
\- Criteria drift: evaluation standards shift as the judge processes   
  more examples (EvalGen, Shankar et al.)  
\- Sycophancy in evaluation: judge agrees with confident-sounding   
  claims regardless of accuracy

**\#\# The "Same Model Evaluating Same Model" Problem**

This is the central technical challenge. Investigate:  
\- Cross-model evaluation (use a different model family as judge)  
\- Evaluator ensembles (multiple judges, flag disagreements)  
\- Constitutional AI self-critique loop (model critiques own output   
  against explicit principles) as partial mitigation  
\- Decomposed evaluation (break quality into orthogonal dimensions   
  scored independently rather than holistic judgment)  
\- AISI's finding that automated graders show Cohen's Kappa of 0.52   
  vs human agreement of 0.8 — what does this mean for our confidence   
  thresholds?  
\- Deterministic checks layered under LLM judgment (citation   
  verification, source existence, structural completeness) as   
  anti-gaming anchors

**\#\# Rubric Design for Consulting Quality**

The prompt's original ask for McKinsey/BCG/Bain quality standards   
is a dead end — these aren't public. Instead investigate:  
\- Multi-persona red-teaming patterns (199-bio deep-research skill   
  uses Skeptical Practitioner, Adversarial Reviewer, Implementation   
  Engineer personas in Deep/UltraDeep modes)  
\- MECE as an evaluable property (can an LLM judge reliably detect   
  whether analysis is mutually exclusive and collectively exhaustive?)  
\- Structured analytical technique completeness checks (Porter's Five   
  Forces coverage, SWOT balance, scenario planning rigor)  
\- Academic literature on structured analytic techniques from   
  intelligence analysis (Richards Heuer's "Psychology of Intelligence   
  Analysis" and the IC's Analytic Standards)  
\- The distinction between accuracy evaluation (is this factually   
  correct?) and analytical quality evaluation (is this decision-useful,   
  appropriately caveated, and intellectually honest?) — the latter is   
  far harder and less studied

**\#\# Anti-Gaming Strategies**

\- Factorial evaluation: systematically vary inputs to test whether   
  the system produces genuinely different analysis vs template-filling  
\- Adversarial probes: deliberately introduce errors or weak arguments   
  to test whether the evaluator catches them  
\- Constitutional self-critique: require the system to critique its   
  own output against explicit quality principles before final scoring  
\- Deterministic anchors: non-LLM checks (citation URLs resolve,   
  sources actually contain claimed information, numerical claims   
  are internally consistent) that can't be gamed by optimizing prose  
\- Human-in-the-loop calibration: periodic comparison of evaluator   
  scores against human expert judgment to detect drift

**\#\# For Each System/Paper Found, Analyze:**  
1\. What it evaluates and how (metrics, scoring method, rubric design)  
2\. Known limitations and failure modes  
3\. Whether it could serve as our Evaluator's backbone, a component   
   within it, or only as a reference for custom design  
4\. How it handles (or doesn't handle) the self-evaluation problem  
5\. Whether it supports custom rubrics calibrated to domain-specific   
   standards  
6\. Whether it can run self-hosted (given our infrastructure)

Key changes in summary: elevated DeepEval and Inspect AI as primary backbone candidates, repositioned RAGAS as a component library rather than a backbone, added Langfuse and Arize Phoenix for self-hosted observability, replaced vague LLM-as-judge investigation with six specific papers and a characterized taxonomy of failure modes, replaced the unobtainable McKinsey/BCG/Bain standards with actually-implementable consulting quality rubrics (MECE evaluability, structured analytic technique completeness, multi-persona red-teaming), broke out the "same model evaluating same model" problem as its own section with concrete mitigation strategies, and added self-hosted viability as an evaluation criterion given your infrastructure.

### **ACTION-ITEMS.md**

md

### **OPENCLAW-IMPLICATIONS.md**

md

### **FRAMEWORKS.md**

md

### **CAPSTONE-IMPLICATIONS.md**

md

### **SYNTHESIS.md**

md

### **CAPSTONE-PLAN-v2.md**

md

\#\#\#\# A3: Self-Improvement, AutoResearch, and Learning Loops \*\*Prompt:\*\* \`\`\` I'm building a research system with a self-improvement loop. The core mechanism is a "Rejection Library" — every time the Evaluator rejects output, the rejection is structured (what failed, why, constraint to prevent recurr

pasted

great. attached are the rest of the prompts which i need you to review. i turned on deep research mode so that you can spawn an individual research agent to vet and improve each individual prompt and provide the updated and optimized prompts. make sure that each prompt is thoroughly evaluated, and that you don't mistakenly execute the prompts which i pasted. again, you are doing what you just did with researching and thinking through the specifics of each prompt, and optmizing them for a full deep research session. proceed\! it was written by merlin, my openclaw agent (also opus 4.6 thinking, but it didn't utilize search and put nearly enough thought and effort into each prompt.). also attached are the project files which are referenced in the document. read through them to fully understand my project before proceeding. the pasted prompts are what you're optimizing. the rest are context files, some, or a few of which, may not be relevant to your research here. just wanted to make sure everything was included which the deep research agents will have access to who will be executing the prompts you create/modify

Show more  
Mar 27  
Researching landscape to optimize remaining prompts systematically  
Researching landscape to optimize remaining prompts systematically

Let me read through the project context files first to fully understand the system before I start optimizing.

Orchestrated comprehensive research strategy for fourteen prompt evaluations  
Orchestrated comprehensive research strategy for fourteen prompt evaluations

I've read through all the context files. This is a substantial project with clear intellectual architecture. Let me now launch comprehensive research to vet and optimize all 14 remaining prompts.

Given the scope (14 prompts spanning self-improvement loops, orchestration frameworks, deep research tooling, consulting quality standards, deliberation patterns, spec-driven development, report generation, data retrieval, and frontier ideas), I'll launch the research task with full context so it can investigate the current state of every referenced tool, framework, paper, and concept across all prompts.

Keystone Intelligence Engine prompt vetting

Research complete•  
960 sources  
•  
23m 22s

Your research report vetting the 14 Keystone Intelligence Engine prompts against the March 2026 landscape is ready. It covers a prompt-by-prompt audit across all categories—self-improvement frameworks (A3), orchestration and agent coordination (A4), deep research tooling (A5), consulting quality standards (B1-B4), specification-driven development (C1), multi-perspective synthesis (C2), deliverable generation (C3), data retrieval architecture (C4), notable individual/small-team projects (D1), academic research updates (D2), and blue-sky capabilities (D3). Key findings include the deprecation of AutoGen and OpenAI Swarm, the rise of AGENTS.md as a Linux Foundation standard, the explosion of the MCP/A2A protocol ecosystem, major new frameworks like Claude Agent SDK and Google ADK, and five cross-cutting themes—spec-driven development, protocol standardization, the taste/judgment quality discourse, ensemble evaluation, and mainstream self-improvement loops—that should be woven throughout all prompts.

