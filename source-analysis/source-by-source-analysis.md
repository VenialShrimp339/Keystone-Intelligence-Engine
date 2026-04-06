# Source-by-Source Deep Analysis: HIGH-Value Bookmarks × Capstone Project

*Generated 2026-03-26 | Each source analyzed against Jack's multi-agent research pipeline proposal*

---

## How to Read This Document

Every HIGH-rated bookmark from the three analysis files is examined individually below. Sources are organized into tiers based on depth and relevance. For each source:

- **Source** — Who posted it, what they said, engagement
- **Core Content** — The specific technical details, patterns, or insights (not summaries)
- **Connection to Jack's Project** — How this informs the capstone architecture, including non-obvious connections
- **What It Changes About the Proposal** — Which layer(s) to modify, add, or restructure
- **Concrete Application** — What Jack would actually build differently

---

# TIER 1: ANTHROPIC ENGINEERING ARTICLES

*These are the highest-quality sources in the entire bookmark collection. Each was read in full (15,000-30,000 characters). They deserve disproportionate weight because they come from Anthropic's own engineering team building production systems with Claude — the same model Jack will use.*

---

## 1. Harness Design for Long-Running Application Development

**Source:** Prithvi Rajasekaran, Anthropic Labs team. Published March 2026. Referenced by multiple bookmarks (@AnthropicAI, @thismacapital). The single most-bookmarked Anthropic article in Jack's collection.

**Core Content — The Technical Details:**

This article documents the evolution of a three-agent architecture (planner → generator → evaluator) inspired by GANs. The specific technical innovations:

1. **GAN-Inspired Generator/Evaluator Separation:** The central insight is that LLMs systematically skew positive when evaluating their own work. Anthropic tried making generators self-critical — it doesn't work. What works is a *separate evaluator instance* that can be independently tuned toward skepticism. The evaluator uses Playwright MCP to actually interact with outputs (not just read them), takes screenshots, navigates pages, and grades against concrete rubric criteria. This is structurally analogous to a GAN's discriminator.

2. **Evaluator Calibration:** The evaluator uses four grading criteria (Design Quality, Originality, Craft, Functionality), weighted toward the dimensions where Claude naturally underperforms (design quality and originality are weighted higher than craft and functionality). Calibration uses few-shot examples with detailed score breakdowns. The evaluator ran 5-15 iterations per generation, with the generator making strategic decisions to either refine the current direction or pivot entirely based on evaluator feedback.

3. **Sprint Contracts:** Before each sprint, the generator and evaluator *negotiate* a sprint contract — agreeing on what "done" looks like before any code is written. This bridges the gap between high-level specs and testable implementation. Sprint 3 alone had 27 criteria. The evaluator then grades against these exact criteria.

4. **Planner Agent Design:** The planner takes a 1-4 sentence prompt and expands it into a full product spec. Crucially, the planner is instructed to stay at *product context* level and avoid granular technical details — because errors in an overly-detailed spec cascade downstream. This is a profound insight about abstraction boundaries.

5. **Context Resets vs. Compaction:** Anthropic discovered that context resets (clearing the window entirely, spawning a fresh agent with a structured handoff artifact) outperform compaction (summarizing earlier parts) for long tasks. Compaction preserves continuity but doesn't eliminate "context anxiety" — where agents start wrapping up prematurely as they approach perceived context limits. Sonnet 4.5 exhibited this so strongly that compaction alone wasn't sufficient. Opus 4.6 largely removed the behavior, allowing them to drop context resets and use compaction alone.

6. **Harness Simplification Principle:** "Every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing, both because they may be incorrect, and because they can quickly go stale as models improve." They simplified the harness iteratively — removing the sprint construct entirely for Opus 4.6 — and found the evaluator remained valuable only when tasks exceeded the generator's solo capability boundary.

7. **Cost Data:** A DAW (Digital Audio Workstation) built from a one-line prompt: 3 hours 50 minutes, $124.70. The planner took 4.7 minutes ($0.46), the build phases took ~3.3 hours ($113.85), and QA took ~25 minutes ($10.39). The QA agent caught real functional gaps that the generator missed even with Opus 4.6.

**Connection to Jack's Project:**

This is *the* architectural blueprint for Jack's capstone. The three-agent pattern maps almost perfectly to his proposed three-layer architecture, but with crucial refinements:

- Jack's **Layer 1 (Data Ingestion & Synthesis)** maps to the Planner's role — decomposing the research question into specific investigative threads.
- Jack's **Layer 2 (Content Structuring & Reasoning)** maps to the Generator — executing research, building arguments, creating analysis.
- Jack's **Layer 3 (Generation & QA)** maps to both the Generator's output phase AND the Evaluator.

But the critical insight is that Jack's original proposal has QA as a *phase* at the end. Anthropic's architecture shows QA should be a *separate agent* that runs after each sprint/section, not a monolithic final pass. The evaluator should interact with the output the way a Keystone partner would — actually reading through the presentation, checking data sources, verifying logical coherence, grading against a rubric.

**Non-obvious connection:** The sprint contract concept maps to something powerful for consulting research. Before generating each section of a research report, the generator and evaluator should negotiate what "done" looks like for that section. For a market sizing analysis, the contract might specify: "Must include top-down and bottom-up estimates. Must cite at least 3 data sources. Must quantify the margin of error. Must compare against at least one external estimate." This turns vague quality aspirations into concrete, testable criteria.

**What It Changes About the Proposal:**

1. **Layer 3 should be split into two distinct roles:** A Generation agent and a QA/Evaluator agent that are *never the same instance*. Self-evaluation doesn't work.
2. **Add Sprint Contracts between layers:** Before generating each deliverable component, the system should negotiate explicit acceptance criteria. This is new — the original proposal has no mechanism for pre-agreeing on what "good" looks like per component.
3. **The Planner should stay at product-context level:** Jack's Layer 1 should decompose research questions into investigative threads but should NOT specify how to execute each thread in detail. Over-specification cascades errors.
4. **Consider dropping context resets with Opus 4.6:** If Jack builds on Opus 4.6 (which he will), compaction may be sufficient for most tasks, simplifying the architecture.
5. **The evaluator must interact with outputs, not just read them:** For a PowerPoint, the evaluator should open the slides, view the charts, check that data visualizations actually render correctly — not just review the generation code.

**Concrete Application:**

Build a `research-evaluator` agent with a Keystone-calibrated rubric. The rubric would have criteria like:
- **Analytical Rigor:** Are conclusions supported by data? Are alternative explanations considered?
- **Source Quality:** Are sources authoritative? Is there appropriate skepticism toward secondary sources?
- **Insight Novelty:** Does this tell the partner something they didn't already know? Or is it surface-level synthesis?
- **Deliverable Standards:** Does this match Keystone's formatting, voice, and depth expectations?
- **Completeness:** Are there obvious gaps or questions a partner would immediately ask?

Calibrate using few-shot examples of actual Keystone deliverables rated by Jack. The evaluator grades each research section. If any criterion falls below threshold, the section gets regenerated with specific feedback.

---

## 2. Building a C Compiler with a Team of Parallel Claudes

**Source:** Nicholas Carlini, Anthropic Safeguards researcher. 16 agents, ~2,000 Claude Code sessions, $20K in API costs. Produced a 100,000-line Rust-based C compiler that compiles the Linux kernel.

**Core Content — The Technical Details:**

1. **Bare-Bones Parallelism via Git:** Each agent runs in a Docker container with a shared bare git repo. Agents claim tasks by writing lock files to `current_tasks/`. Git's merge mechanism prevents duplicate work — if two agents try to claim the same task, the second one's push fails and it picks a different task. No orchestration agent needed. Each agent decides what to work on next by looking at what's failing.

2. **The Ralph Loop:** A simple bash while-loop that restarts Claude in a fresh container with the agent prompt after each completion. Claude works until done, pushes, then a new instance starts. One agent even `pkill -9 bash`'d itself accidentally, killing its own loop.

3. **Test Quality as the Primary Lever:** "Claude will work autonomously to solve whatever problem I give it. So it's important that the task verifier is nearly perfect, otherwise Claude will solve the wrong problem." The test harness is more important than the agent prompt. Improving tests had more impact than improving prompts.

4. **Context Window Pollution Management:** "The test harness should not print thousands of useless bytes. At most, it should print a few lines of output and log all important information to a file so Claude can find it when needed." Error messages should have ERROR on the same line as the reason so `grep` finds it. Pre-compute aggregate summary statistics so agents don't have to recompute them.

5. **Time Blindness Workaround:** Claude can't tell time. Without intervention, it will happily spend hours running tests. The harness prints incremental progress infrequently and includes a `--fast` option that runs a 1-10% random sample. The sample is deterministic per-agent but random across VMs, so coverage is maintained across the team.

6. **The Parallelism Bottleneck:** When agents worked on the Linux kernel (one giant task vs. hundreds of independent tests), all 16 agents would hit the same bug, fix it, and overwrite each other. Solution: use GCC as an "oracle" to compare against — randomly compile most kernel files with GCC and only the remainder with Claude's compiler. If it works, the problem isn't in Claude's subset. This let each agent work on different bugs in different files.

7. **Agent Role Specialization:** One agent coalesces duplicate code. One optimizes compiler performance. One improves compiled output efficiency. One critiques design from a Rust developer perspective. One maintains documentation. Specialization within a parallel team.

**Connection to Jack's Project:**

The parallels to consulting research are striking once you reframe:
- **"Compiling the Linux kernel" = "Researching a complex company/market"** — one giant interconnected task that can't be trivially decomposed into independent subtasks.
- **"Independent test cases" = "Independent research questions"** — each can be assigned to a different agent.
- **"GCC as oracle" = "Existing Keystone research as oracle"** — using known-good prior work as a comparison baseline for evaluating new agent output.
- **"Lock files for task claiming" = "Research thread claiming"** — agents writing to a shared manifest to prevent duplicate investigation.

The test-quality-as-primary-lever insight is transformative. For Jack's research tool, the *evaluation rubric* is more important than the *research prompt*. Investing heavily in what "good research" looks like (with concrete examples from Keystone) will drive more quality improvement than refining how agents are told to do research.

**Non-obvious connection:** The agent role specialization pattern maps to consulting research specialization. Instead of one agent doing everything, Jack could have:
- A **data agent** that gathers and validates quantitative data (financial filings, market data)
- A **narrative agent** that synthesizes qualitative sources (expert commentary, strategy documents, news)
- A **contrarian agent** that critiques and stress-tests the emerging thesis
- A **formatting agent** that ensures Keystone deliverable standards
- A **documentation agent** that maintains the research log and methodology notes

**What It Changes About the Proposal:**

1. **Layer 1 should use git-based task coordination for parallel research agents.** No orchestration agent needed — agents claim research threads via lock files. This is simpler and more robust than a central orchestrator assigning tasks.
2. **Add an evaluation/test layer that's MORE important than the research prompts.** Jack's original proposal focuses on prompt design and agent-to-agent handoffs. Carlini's experience says: invest in the *test harness* (the rubric, the acceptance criteria, the known-good examples) and the agents will figure out the rest.
3. **Agent specialization should be a first-class design choice.** The proposal currently treats all agents identically. Different research sub-tasks benefit from different agent "personalities" and toolsets.
4. **Context window pollution is a critical failure mode.** Research tools (web scrapers, PDF parsers, database queries) must return concise, pre-processed output — not raw data dumps.

**Concrete Application:**

Build a `research-coordinator` that uses a shared git repo (or shared directory) with a `claimed_threads/` folder. When a research agent starts investigating "market sizing for autonomous vehicles," it creates `claimed_threads/market_sizing_autonomous_vehicles.lock`. Other agents see this and pick different threads. Each agent pushes its findings to a shared `findings/` directory. A synthesis agent periodically pulls all findings and identifies gaps, contradictions, and opportunities for deeper investigation.

For the "oracle" pattern: feed past Keystone research reports as the gold standard. The evaluator agent compares new research output against the structure, depth, and rigor of these reports, identifying where the new output falls short.

---

## 3. Effective Context Engineering for AI Agents

**Source:** Anthropic Applied AI team (Prithvi Rajasekaran, Ethan Dixon, Carly Ryan, Jeremy Hadfield). Published alongside Sonnet 4.5 launch.

**Core Content — The Technical Details:**

1. **Context Rot:** As tokens increase in the context window, recall accuracy decreases across ALL models. This isn't a bug — it's architectural. Transformers compute n² pairwise relationships for n tokens. As n grows, the model's ability to capture these relationships gets stretched thin. Models develop attention patterns from training data where shorter sequences are more common, so they have fewer specialized parameters for long-range context dependencies.

2. **"Just in Time" Context:** Rather than pre-loading all relevant data, maintain lightweight identifiers (file paths, stored queries, web links) and dynamically load data at runtime using tools. Claude Code does this: CLAUDE.md files are naively loaded up front, but everything else uses `glob` and `grep` for just-in-time retrieval. This mirrors human cognition — we don't memorize entire corpuses, we build indexing systems (file systems, inboxes, bookmarks) for on-demand retrieval.

3. **Progressive Disclosure:** Agents can incrementally discover relevant context through exploration. Each interaction yields context that informs the next decision: file sizes suggest complexity, naming conventions hint at purpose, timestamps proxy for relevance. This self-managed context window keeps the agent focused on relevant subsets.

4. **Compaction:** Taking a conversation nearing the context window limit, summarizing its contents, and reinitializing with the summary. The art is in what to keep vs. discard. Anthropic recommends maximizing recall first, then iterating to improve precision. Lowest-hanging fruit: clearing tool call results deep in message history (launched as a platform feature).

5. **Structured Note-Taking / Agentic Memory:** Agents regularly write notes persisted outside the context window, pulled back in later. Like Claude Code creating a to-do list, or a custom agent maintaining a NOTES.md file. Claude playing Pokémon demonstrates this: tracking objectives across thousands of game steps, maintaining maps of explored regions, remembering combat strategies. After context resets, it reads its own notes and continues.

6. **Sub-Agent Architectures:** Specialized sub-agents handle focused tasks with clean context windows. The main agent coordinates with a high-level plan while sub-agents do deep work. Each sub-agent might use tens of thousands of tokens but returns only 1,000-2,000 tokens of condensed summary. This achieves separation of concerns — detailed search context stays isolated within sub-agents.

7. **The "Right Altitude" for Prompts:** Between brittle hardcoded if-else logic and vague high-level guidance lies the Goldilocks zone — specific enough to guide behavior, flexible enough to provide strong heuristics.

**Connection to Jack's Project:**

Context engineering IS Jack's capstone, reframed. His research question — "how should a multi-agent LLM pipeline be architected across prompt design, context engineering, and agent-to-agent handoffs?" — is literally the subject of this article. But the article reframes the problem in ways that should reshape the capstone:

The key reframe: **Context is not a container to fill. It is a scarce resource with diminishing marginal returns.** Every token of research data loaded into an agent's context reduces the agent's ability to reason about the rest of the context. This means:

- **Loading an entire 10-K filing into context is worse than loading a targeted excerpt.** The 10-K pollutes the context with thousands of tokens the agent doesn't need for the current question.
- **The research agent shouldn't have all research findings in context when writing a specific section.** It should have only the findings relevant to THAT section plus the overall narrative framework.
- **"Just in time" context is the right paradigm for research data.** Maintain an index of what's been found; load specific findings only when the agent needs them for the current task.

**Non-obvious connection:** The progressive disclosure pattern is how a senior consultant actually does research. You don't read every document cover-to-cover. You scan titles, read abstracts, drill into specific sections that seem relevant, cross-reference with other sources. An agent doing research should work the same way — scan a source, decide if it's relevant, extract specific data points, move on.

The sub-agent architecture insight has a specific implication for Jack's project: each research sub-agent (investigating one thread) should do extensive work — reading dozens of sources, synthesizing data, building arguments — but return only a 1-2 page condensed summary to the orchestrator. The orchestrator never sees the raw data. It works with pre-synthesized intelligence. This is exactly how a consulting engagement manager works — they never read every source document; they work with pre-synthesized analysis from their team.

**What It Changes About the Proposal:**

1. **Layer 1 (Data Ingestion) needs a "context budget" concept.** Don't ingest everything — ingest what's needed for the current research question. Maintain an index of available data; load on demand.
2. **Layer 2 (Content Structuring) should receive condensed intelligence, not raw data.** Sub-agents do the deep reading and return summaries. The structuring agent works with synthesized findings, not source documents.
3. **Add a "Research Index" component** — a lightweight manifest of all data sources, what's been investigated, what findings exist, organized for just-in-time retrieval. This is not a layer but infrastructure that all layers use.
4. **The system prompt for each agent should be at "the right altitude"** — not prescriptive step-by-step instructions, not vague "do good research." Specific enough to encode Keystone quality standards, flexible enough to let the agent figure out how.

**Concrete Application:**

Build a `research-index.json` that maintains lightweight references:
```json
{
  "sources_identified": [
    {"id": "src_001", "type": "10-K", "company": "Acme Corp", "year": 2025, "path": "/data/acme_10k_2025.pdf", "sections_extracted": ["revenue_breakdown", "risk_factors"]},
    {"id": "src_002", "type": "industry_report", "publisher": "McKinsey", "topic": "autonomous_vehicles", "path": "/data/mckinsey_av_2025.pdf", "sections_extracted": []}
  ],
  "findings": [
    {"id": "find_001", "source": "src_001", "claim": "Acme's revenue grew 23% YoY driven by enterprise segment", "confidence": "high", "path": "/findings/acme_revenue.md"},
    {"id": "find_002", "source": "src_002", "claim": null, "path": null, "status": "not_yet_investigated"}
  ],
  "research_threads": [
    {"id": "thread_001", "question": "What is Acme's competitive position?", "status": "in_progress", "findings_used": ["find_001"]},
    {"id": "thread_002", "question": "What is the TAM for autonomous vehicles?", "status": "not_started", "findings_used": []}
  ]
}
```

Research agents pull specific sources by ID when they need them, rather than having everything pre-loaded. The orchestrator works from the index, not from raw data.

---

## 4. Writing Effective Tools for Agents — with Agents

**Source:** Ken Aizawa, Anthropic, with contributions from Research, MCP, Product Engineering, Marketing, Design, and Applied AI teams. Referenced by multiple bookmarks (@kloss_xyz, @Shpigford).

**Core Content — The Technical Details:**

1. **Tools ≠ APIs:** Tools are contracts between deterministic systems and *non-deterministic* agents. When a user asks "should I bring an umbrella?", an agent might call a weather tool, answer from knowledge, or ask for location first. This means fundamentally rethinking tool design — not wrapping existing APIs, but designing for how agents *perceive and use* tools.

2. **Choosing the Right Tools (and NOT Building Others):**
   - Instead of `list_users`, `list_events`, `create_event` → implement `schedule_event` which handles the whole workflow.
   - Instead of `read_logs` → implement `search_logs` that returns relevant lines with context.
   - Instead of `get_customer_by_id`, `list_transactions`, `list_notes` → implement `get_customer_context` that compiles everything at once.
   - Consolidate multi-step chains into single tools. Reduce the agent's decision surface.

3. **Namespacing:** Group related tools under common prefixes. `asana_search` vs. `jira_search`. `asana_projects_search` vs. `asana_users_search`. Prefix-based vs. suffix-based namespacing has non-trivial effects on evaluation performance. This varies by LLM — test both.

4. **Token-Efficient Responses:** Implement a `response_format` enum parameter (CONCISE vs. DETAILED). A Slack thread response went from 206 tokens (detailed) to 72 tokens (concise) — ~⅓ of the tokens. Include technical IDs (needed for subsequent tool calls) only in DETAILED mode.

5. **Response Structure Matters:** XML, JSON, or Markdown can each impact evaluation performance differently. There is no universal best format — it depends on the task and agent. Test against your evaluation.

6. **Truncation with Guidance:** Claude Code restricts tool responses to 25,000 tokens by default. When truncating, steer agents toward more efficient strategies: "Try making many small, targeted searches instead of a single broad search." Error messages should be specific and actionable, not opaque codes.

7. **Evaluation-Driven Tool Improvement:** Build eval tasks from real-world usage. Weak tasks: "Search the payment logs for customer_id=9182." Strong tasks: "Customer ID 9182 reported being charged three times for a single purchase. Find all relevant log entries and determine if any other customers were affected." Pair with verifiable outcomes. Run programmatically with simple agentic loops. Have Claude analyze transcripts and improve tools iteratively.

8. **Real Example — Web Search Tool Bug:** Claude was appending "2025" to every web search query, biasing results. They fixed it by improving the tool description. Small prompt changes to tool descriptions yield dramatic evaluation improvements (this is how Sonnet 3.5 achieved SOTA on SWE-bench Verified).

**Connection to Jack's Project:**

This article is the design manual for every tool Jack builds for the research pipeline. The consulting research tool will need tools for:
- Web searching / crawling
- PDF/document parsing
- Financial data retrieval (SEC filings, financial databases)
- Internal document access (Keystone's proprietary files)
- Data analysis / chart generation
- Slide creation

Every one of these tools needs to be designed for *agent consumption*, not human consumption. The most common mistake would be wrapping existing APIs (e.g., an SEC EDGAR API) directly — the raw API responses will be full of metadata, IDs, and formatting that waste context tokens.

**Non-obvious connection:** The `get_customer_context` consolidation pattern maps directly to consulting research. Instead of separate tools for `get_company_financials`, `get_company_news`, `get_company_filings`, build a `get_company_research_context` tool that returns a pre-synthesized summary: key financial metrics, recent news highlights, notable filings — all in one call. This reduces tool calls, reduces decision complexity, and gives the agent a coherent starting point.

The evaluation-driven tool improvement cycle is also critical. Jack shouldn't guess at what makes a good research tool — he should build evals that test whether research agents using his tools produce Keystone-quality output, then iterate on the tools based on where agents fail.

**What It Changes About the Proposal:**

1. **Add a "Tool Design" section to the capstone.** The proposal focuses on prompt design and agent architecture but underweights tool design. Anthropic's experience shows that tool design is as impactful as prompt design on agent performance.
2. **Layer 1 tools should consolidate multi-step data retrieval.** Don't build separate tools for each data source — build workflow-level tools that handle common research patterns end-to-end.
3. **All tool responses should have concise/detailed modes.** Research agents should get concise summaries by default, with the ability to request detailed data when needed.
4. **Build an evaluation suite for the research tools.** Define what "good research tool usage" looks like with concrete test cases from Keystone research questions.

**Concrete Application:**

Design research tools like:
```
research_company(company_name, focus_areas=["financials", "competitive", "market"])
→ Returns: Concise company overview with requested focus areas pre-synthesized

search_industry(query, industry, source_types=["academic", "industry_report", "news"])
→ Returns: Top 5 relevant sources with 2-3 sentence summaries each

analyze_financial_data(company, metrics=["revenue_growth", "margins", "market_share"], years=3)
→ Returns: Pre-computed metrics with trends, formatted for agent consumption

get_internal_context(client_name, document_types=["strategy", "prior_research"])
→ Returns: Summary of relevant internal documents with key findings
```

Each returns concise, pre-processed output. No raw API responses. No thousands of bytes of metadata.

---

## 5. Effective Harnesses for Long-Running Agents

**Source:** Justin Young, Anthropic. Published alongside Claude Agent SDK. The foundational article that the "Harness Design" article builds upon.

**Core Content — The Technical Details:**

1. **The Core Problem:** Even frontier models (Opus 4.5) running in a loop with compaction fail to build production-quality apps from high-level prompts. Two failure modes: (a) trying to one-shot everything, running out of context mid-implementation, leaving the next session to guess what happened; (b) later agent instances see progress and prematurely declare the job done.

2. **Two-Part Solution:**
   - **Initializer Agent:** First session uses a specialized prompt to set up the environment: init.sh script, `claude-progress.txt` file for logging, initial git commit. Decomposes the prompt into 200+ feature requirements, all initially marked as "failing."
   - **Coding Agent:** Every subsequent session makes incremental progress on ONE feature, then leaves structured updates. Commits to git with descriptive messages. Updates the progress file.

3. **Feature List as JSON, Not Markdown:** Models are less likely to inappropriately change or overwrite JSON files compared to Markdown. Features use a structured format with `category`, `description`, `steps`, and `passes: false`. Agents are told "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."

4. **Incremental Progress:** Agents work on ONE feature at a time. This is "critical to addressing the agent's tendency to do too much at once." The agent commits progress to git and writes summaries to a progress file, enabling clean recovery if things go wrong.

5. **Testing as Verification:** Claude's tendency to mark features as complete without proper testing was a major failure mode. Adding Playwright MCP for end-to-end browser testing (testing as a human user would) dramatically improved performance. Some issues remain: Claude can't see browser-native alert modals through Playwright, so features relying on those modals tend to be buggier.

6. **Session Boot Sequence:** Every coding agent starts by: running `pwd`, reading git logs and progress files, reading the features list, choosing the highest-priority undone feature, running `init.sh` to start the dev server, and doing a basic end-to-end test before implementing anything new. This ensures the agent catches if the app was left in a broken state.

**Connection to Jack's Project:**

The initializer/coding agent pattern maps directly to how a consulting research project should be structured:

- **Initializer Agent = Research Scoping Agent:** Takes a research question ("What is the competitive landscape for autonomous vehicles?") and decomposes it into 50-200 specific research tasks, all initially marked as incomplete. Creates the research plan, the evaluation rubric, the folder structure, the data source index.

- **Coding Agent = Research Execution Agent:** Each session picks up ONE research thread, executes it fully, commits findings to the shared knowledge base, updates the progress file, then exits. The next session reads the progress file, picks the next highest-priority incomplete thread, and continues.

**The JSON-not-Markdown insight is critical.** Jack's research tracker should use structured JSON, not Markdown. Models will "helpfully" edit Markdown in ways that lose information — changing status labels, rewriting descriptions, removing items they think are done. JSON's rigid structure makes this less likely.

The session boot sequence is also directly transferable: every research agent session should start by reading the progress file, checking what's been done, verifying that existing findings are still valid (data sources haven't changed, links aren't broken), then picking the next task.

**What It Changes About the Proposal:**

1. **Add an "Initializer" phase before Layer 1.** Before any data ingestion happens, a scoping agent should decompose the research question into a structured feature list (in JSON) of specific research tasks. This doesn't exist in the original proposal.
2. **All research progress should be tracked in structured JSON.** Not markdown logs. Not free-text notes. Structured JSON with status fields that agents can reliably read and update.
3. **Each agent session should work on ONE research thread.** The proposal implies agents will handle entire layers. Instead, agents should be scoped to single research tasks within a layer.
4. **Every session should start with a verification step.** Before doing new work, verify that existing work is intact. In research: spot-check that data sources are still accessible, key claims are still supported, the overall narrative still holds.

**Concrete Application:**

Build a `research-tasks.json` structured like:
```json
{
  "project": "Autonomous Vehicle Market Analysis",
  "created": "2026-03-26",
  "tasks": [
    {
      "id": "task_001",
      "category": "market_sizing",
      "description": "Estimate total addressable market for L4+ autonomous vehicles in North America by 2030",
      "steps": [
        "Identify top-down sizing sources (industry reports, analyst estimates)",
        "Build bottom-up estimate from unit economics and adoption curves",
        "Triangulate top-down and bottom-up estimates",
        "Document assumptions and confidence intervals"
      ],
      "passes": false,
      "priority": 1,
      "assigned_agent": null
    },
    {
      "id": "task_002",
      "category": "competitive_landscape",
      "description": "Map key players in autonomous vehicle technology and their differentiation",
      "steps": [
        "Identify top 10 players by funding/revenue/market share",
        "Categorize by approach (lidar vs. camera-only, full-stack vs. component)",
        "Assess competitive moats and vulnerabilities",
        "Create positioning matrix"
      ],
      "passes": false,
      "priority": 2,
      "assigned_agent": null
    }
  ]
}
```

Each research agent reads this file, picks the highest-priority `passes: false` task, executes it, writes findings, and sets `passes: true`. The next agent continues from where the last left off.

---

# TIER 2: HIGH-VALUE BOOKMARKS — Architecture & Agent Patterns

---

## 6. Orchestrator Pattern for AGENTS.md

**Source:** @johann_sath on X. Quote: "Add this to your AGENTS.md: 'you are the orchestrator. subagents execute. never build, verify, or code inline. your job is to plan, prioritize & coordinate.' Went from 1 slow agent doing everything to a CEO managing an army."

**Core Content:**

The principle is deceptively simple: the main agent should NEVER do substantive work inline. It should only plan, prioritize, and coordinate. All execution happens in sub-agents. This is the "CEO pattern" — the CEO doesn't write code, doesn't do research, doesn't format slides. They decide what needs to happen and who should do it.

**Connection to Jack's Project:**

Jack's research pipeline needs a clear orchestration layer that sits ABOVE the three-layer architecture. The orchestrator receives the research question, decomposes it (by delegating to a Planner sub-agent), coordinates execution across research agents (Layer 1), routes findings to structuring agents (Layer 2), and manages the generation/QA loop (Layer 3). The orchestrator itself never touches raw data.

This changes the architecture from a linear pipeline (Layer 1 → Layer 2 → Layer 3) to a hub-and-spoke model where the orchestrator is the hub and each layer's agents are spokes.

**What It Changes About the Proposal:**

Add a **Layer 0: Orchestration** that sits above all three layers. The orchestrator manages the research project lifecycle, spawns and coordinates agents across layers, tracks overall progress, and is the interface to the user (Jack or a Keystone consultant). The three layers become execution layers, not autonomous stages.

**Concrete Application:**

The orchestrator agent's prompt would include:
```
You are the Research Orchestrator. You NEVER do research, write analysis, or format deliverables yourself.
Your job:
1. Receive the research question
2. Spawn a Planner to decompose it into tasks
3. Assign tasks to Research Agents (Layer 1)
4. Route completed findings to Structuring Agents (Layer 2)
5. Coordinate Generation and QA (Layer 3)
6. Track progress in research-tasks.json
7. Report status and flag blockers to the user
```

---

## 7. "Let Them Cook" — Lessons from 6 Weeks of Multi-Agent Orchestration

**Source:** @Khaliqgant (Khaliq Gant). "Let Them Cook: Lessons from 6 Weeks of Multi-Agent Orchestration." Agent Relay project.

**Core Content:**

This is the most practically battle-tested multi-agent guide in the bookmark collection. Key technical details:

1. **2-5 workers per Lead agent is the sweet spot.** 10+ workers causes the Lead to "die" (lose coherence trying to track too many threads). This is an empirically discovered limit, not theoretical.

2. **Role-model matching:** Claude for Lead/Reviewer roles (communicates well, interruptible). Codex for deep implementation work (heads-down, doesn't communicate back). Use `teams.json` to codify team structures.

3. **Trajectory Storage:** Store a "train of thought" for completed tasks as structured JSON — decisions made, reasoning, significance ratings, retrospectives. Future agents can query these trajectories to gain instant context when revisiting topics. This is "institutional memory."

4. **Shadow Agents:** Dedicated monitors that catch lazy work. A Reviewer agent that grades output. Cross-review as a quality lever — have one agent review another's work, not its own.

5. **The Lead's Job:** The Lead agent maintains a high-level plan, assigns work to workers, reviews outputs, and decides when to iterate vs. move on. The Lead NEVER does the work itself.

**Connection to Jack's Project:**

The 2-5 workers per Lead limit is critical for Jack's architecture. If Jack's research pipeline spawns 10 parallel research agents, they need at least 2-3 Lead agents coordinating subsets of the work. A single orchestrator cannot effectively manage 10+ deep research threads.

Trajectory storage is the "institutional memory" that Jack's system needs to improve over time. Every completed research project should log: what research questions were asked, what sources were most valuable, what analytical frameworks worked, what the evaluator flagged, how the final deliverable was received. Future research projects query this trajectory store for relevant prior work.

The Claude-for-Lead, Codex-for-deep-work pattern might map to: Claude-for-orchestration-and-synthesis, a different agent configuration for data-heavy quantitative research.

**What It Changes About the Proposal:**

1. **Cap Layer 1 research agents at 5 per orchestrator.** If more threads are needed, add sub-orchestrators.
2. **Add trajectory storage as a persistent component.** Every completed research project logs its trajectory (decisions, sources, findings, evaluator feedback) for future reference.
3. **Consider role-model matching** — different model configurations for different roles (orchestrator vs. researcher vs. evaluator).

**Concrete Application:**

Build a `trajectory-store/` directory:
```
trajectory-store/
├── project_001_acme_competitive_analysis/
│   ├── trajectory.json    # Full decision log
│   ├── sources_rated.json  # Which sources were most valuable
│   ├── frameworks_used.md  # What analytical frameworks worked
│   └── evaluator_feedback.md  # What the QA agent flagged
├── project_002_market_sizing_ev/
│   └── ...
```

When starting a new project, the Planner queries trajectory-store/ for similar past projects to inform its approach.

---

## 8. Agent Souls — Skills vs. Identity

**Source:** @tolibear_ — "I Gave My Agents Skills. I Should Have Given Them Souls." souls.zip ecosystem.

**Core Content:**

The distinction between **skills** (what to do — procedural knowledge) and **souls** (who to be — identity, judgment, communication style) is critical. A skilled agent without a soul produces correct but generic output. A "souled" agent produces output with judgment, perspective, and style.

The souls.zip ecosystem creates pre-packaged identity layers for agents — think of it as "persona templates" that shape how an agent approaches work, communicates findings, and exercises judgment.

**Connection to Jack's Project:**

Jack's research agents need different "souls" for different roles:
- The **Research Agent** soul should be curious, thorough, source-critical, and skeptical of easy answers.
- The **Evaluator Agent** soul should be demanding, detail-oriented, and calibrated to Keystone partner standards.
- The **Synthesis Agent** soul should be narrative-minded, able to find the through-line in disparate findings, and focused on "so what?" implications.
- The **Presentation Agent** soul should think like a consultant — structured, precise, visually aware, and focused on executive communication.

This is different from skills (how to use a web scraper) — it's about the *judgment* each agent brings to its work.

**What It Changes About the Proposal:**

Each agent in the pipeline should have both a **skill set** (tools and procedures) AND a **soul prompt** (identity, judgment standards, communication style). The soul prompt is calibrated to the role's requirements. This is a new design dimension not in the original proposal.

**Concrete Application:**

The Evaluator Agent's soul prompt:
```
You are a Senior Engagement Manager at a top-3 management consulting firm. You have reviewed 500+ research deliverables. You are demanding but fair. When you see surface-level analysis, you push for depth. When you see unsupported claims, you demand evidence. When you see generic frameworks applied without adaptation, you reject them. Your standard: would a Managing Director present this to a Fortune 500 CEO without edits? If not, it fails.
```

---

## 9. Complete Guide to Building Mission Control / "Mission Control" Setup

**Source:** @pbteja1998 — "Complete Guide to Building Mission Control: How We Built an AI Agent Squad." (32K bookmarks). Also @AlexFinn — "Mission Control" setup for OpenClaw (14.7K bookmarks).

**Core Content:**

A "Mission Control" pattern — a structured dashboard/workspace for monitoring and managing multiple AI agents. The core idea: don't just run agents — build visibility into what they're doing, their progress, their errors, and their outputs. This is the control plane for multi-agent systems.

**Connection to Jack's Project:**

When Jack's research pipeline runs — with potentially 5-10 agents working in parallel across different research threads — he needs visibility into what's happening. Which threads are complete? Which are stuck? Where has the evaluator flagged issues? What's the overall progress toward a deliverable?

This is especially important for the capstone demonstration. Being able to show a "Mission Control" view of the research pipeline in action would be a compelling visual for the capstone presentation — showing the multi-agent system at work on a real research question.

**What It Changes About the Proposal:**

Add a **monitoring/observability component** to the architecture. This isn't a new layer — it's infrastructure. A status dashboard that shows:
- Active research agents and their current tasks
- Completed vs. outstanding research threads
- Evaluator scores for completed sections
- Cost/token usage across the pipeline
- Estimated time to completion

**Concrete Application:**

A `research-status.json` file (updated by the orchestrator) that could be rendered as a simple dashboard:
```json
{
  "project": "Acme Corp Competitive Analysis",
  "status": "in_progress",
  "progress": "37/52 tasks complete",
  "agents_active": 4,
  "evaluator_scores": {
    "market_sizing": 8.5,
    "competitive_landscape": 7.2,
    "financial_analysis": null
  },
  "blockers": ["SEC filing for Q4 2025 not yet available"],
  "estimated_completion": "45 minutes",
  "cost_so_far": "$12.40"
}
```

---

## 10. MiroFish — Swarm Intelligence Engine

**Source:** @k1rallik (MiroFish project, Beitroot). Open source swarm intelligence engine. Simulates thousands of AI agents for predictions. Uses multi-agent social simulation.

**Core Content:**

Instead of asking one model "what's the answer?", MiroFish simulates a crowd of specialized agents debating and converging. Combines GraphRAG, long-term agent memory, and multi-round simulation. Each agent has its own perspective; they argue, update their positions, and the system tracks convergence.

**Connection to Jack's Project:**

The "debate and converge" pattern maps to the most valuable phase of consulting analysis: the synthesis meeting. In a consulting engagement, individual analysts present their findings, the team debates interpretations, challenges assumptions, and converges on a unified thesis. Jack's pipeline could simulate this:

- Research agents each produce independent analyses
- A "debate" phase runs where agents with different findings argue for their interpretations
- The system identifies where agents converge (high-confidence findings) and where they diverge (areas needing more investigation or nuanced presentation)
- The synthesis reflects the debate — presenting consensus views with high confidence and contested views with appropriate caveats

This is more sophisticated than just having one synthesis agent merge findings. It introduces *dialectic* into the pipeline.

**What It Changes About the Proposal:**

Add a **Deliberation Phase** between Layer 1 (Data Ingestion) and Layer 2 (Content Structuring). After research agents produce independent findings, a multi-agent debate identifies consensus, disagreements, and gaps. The structuring agent receives not just findings but the *confidence map* from the deliberation.

**Concrete Application:**

After all research threads complete, spawn 3-5 "analyst personas" (Bull Case, Bear Case, Consensus, Contrarian) and have them each produce a one-page thesis from the shared findings. Then run a "synthesis debate" where each persona critiques the others' theses. The final synthesis weights arguments by how well they survived cross-examination.

---

## 11. Supermemory — ASMR (Agentic Search and Memory Retrieval)

**Source:** @VadimStrizheus. Open-source memory engine claiming ~99% on LongMemEval_s benchmark. Combines memory extraction, user profiles, hybrid search (RAG + memory in one query), connectors for Google Drive/Gmail/Notion/GitHub.

**Core Content:**

ASMR combines traditional RAG (retrieval-augmented generation) with conversational memory in a single query. Instead of separate "search for documents" and "remember past conversations" steps, one query simultaneously searches the knowledge base AND recalls relevant prior interactions. It also builds user profiles from interaction history.

**Connection to Jack's Project:**

The hybrid search concept is critical for Layer 1. When a research agent is investigating a topic, it should simultaneously:
- Search external sources (web, databases, filings)
- Search internal Keystone documents (strategy docs, prior research)
- Recall findings from prior research projects on related topics

Currently, these are separate operations requiring different tools. A unified retrieval layer that handles all three in one query would dramatically reduce the agent's cognitive load and tool-calling overhead.

**What It Changes About the Proposal:**

Layer 1 should have a **unified retrieval interface** that searches across public data, internal documents, and historical research simultaneously. The agent issues one query; the retrieval layer fans out across all sources and returns a merged, ranked result set.

**Concrete Application:**

A `research_search(query, scope=["public", "internal", "historical"])` tool that:
1. Searches web sources for the query
2. Searches Keystone's internal document store
3. Searches past research project findings
4. Returns a unified, ranked list with source provenance

---

## 12. "How To Be A World-Class Agentic Engineer"

**Source:** @systematicls. 26K bookmarks — one of the most-bookmarked posts in the collection. Best practices compilation.

**Core Content:**

Core principle: "Delegate most design and implementation to agents, take responsibility for final results." The agentic engineer's job is to:
- Define the problem precisely
- Design the evaluation criteria
- Build the harness/tools
- Review and calibrate outputs
- Own the quality of the final result

The engineer does NOT do the work themselves. They architect the system that does the work.

**Connection to Jack's Project:**

This validates the capstone's entire premise. Jack isn't building a tool that does research. He's building a *system* that does research, and his role is to:
- Define what "good research" looks like (evaluation criteria)
- Build the tools and harness (the pipeline)
- Calibrate the evaluator (using Keystone examples)
- Own the final quality

This reframe could sharpen the capstone's framing. The research question isn't "how to build an AI research tool" — it's "how to be a world-class architect of AI research systems."

**What It Changes About the Proposal:**

Sharpen the framing. The capstone should position Jack as the "agentic engineer" whose job is system design, evaluation calibration, and quality ownership — not prompt engineering or tool building per se. The contribution is the *architecture* and the *evaluation framework*, not the code.

---

# TIER 2: HIGH-VALUE BOOKMARKS — Autoresearch & Self-Improvement

---

## 13. Darwinian Agent Selection (Chris Worsey)

**Source:** @Chris_Worsey. Autoresearch applied to financial markets. 25 agents producing daily market recommendations across macro, rates, commodities, sectors, and single stocks. +22% returns over 173 days.

**Core Content:**

The key innovation: **the worst-performing agent by rolling Sharpe ratio gets its prompt rewritten by the system. Keep or revert.** Prompts are the "weights." Sharpe ratio is the "loss function." The system evolves its own agents over time by selecting for the ones that produce the best outputs.

This is literal Darwinian evolution applied to agent prompts. No human curation of prompts — the system discovers what works through competition and selection.

**Connection to Jack's Project:**

Apply this to research methodology agents. Run multiple "research personality" agents:
- One conservative/skeptical (demands hard data, dismisses qualitative evidence)
- One creative/contrarian (challenges conventional wisdom, looks for non-obvious angles)
- One data-heavy (focuses on quantitative analysis, builds models)
- One qualitative (focuses on expert interviews, industry commentary, narrative)

Track which personality produces research that scores highest on the evaluator rubric over multiple projects. Evolve the worst performer by rewriting its prompt. Over time, the system discovers the optimal "research personality" for Keystone's needs.

**What It Changes About the Proposal:**

Add a **meta-optimization loop** that sits ABOVE the entire pipeline. After each completed research project:
1. Score the final output on the evaluator rubric
2. Identify which research agent prompts produced the highest-scoring contributions
3. Rewrite the worst-performing agent's prompt using the best-performing agent as a template
4. Track performance over multiple projects

This makes the system self-improving — Jack's stated goal for the capstone.

**Concrete Application:**

```
meta_optimization_loop:
  for each completed project:
    1. Collect evaluator scores per research thread
    2. Rank research agent prompts by average thread score
    3. If worst performer < threshold:
       - Generate new prompt variant inspired by top performer
       - A/B test new prompt on next project
       - Keep if improved, revert if degraded
    4. Log prompt evolution history
```

---

## 14. Self-Improving Skills via Autoresearch Pattern

**Source:** @Hesamation citing @itsolelehmann. Someone built a skill that went from **56% → 92%** accuracy in 4 rounds of iterative improvement using the autoresearch loop.

**Core Content:**

The method:
1. Define a set of tests for the skill (what to improve, what to measure)
2. Run the skill against tests
3. Analyze failures
4. Modify the skill
5. Re-test
6. Loop until performance plateaus

This is Harrison Chase's autoresearch-agents pattern applied to Claude Code skills. The "editable asset" is the skill's SKILL.md file. The "scalar metric" is the accuracy on the test set. The "time-boxed cycle" is one round of changes.

**Connection to Jack's Project:**

The research pipeline itself is a "skill" that can be iteratively improved. Define a test suite of research questions with known-good outputs (from past Keystone work). Run the pipeline against these test cases. Measure quality on the evaluator rubric. Analyze where the pipeline fails. Modify the pipeline (prompts, tools, architecture). Re-test. Loop.

56% → 92% in 4 rounds is a massive improvement. If Jack's research pipeline starts at 60% quality (compared to a senior consultant's work), iterating 4-8 rounds could potentially reach 85-95%.

**What It Changes About the Proposal:**

Add an **iterative calibration protocol** to the capstone methodology:
1. Build v1 of the pipeline
2. Run it against 5-10 test cases (research questions with known-good outputs from Keystone)
3. Score outputs on the evaluator rubric
4. Identify failure patterns
5. Modify the pipeline
6. Re-run against the same test cases
7. Measure improvement
8. Report the improvement curve in the capstone paper

This gives Jack quantitative evidence of system improvement — exactly what an academic capstone needs.

**Concrete Application:**

Create a `research-evals/` directory:
```
research-evals/
├── test_cases/
│   ├── case_001_acme_competitive.json   # Research question + known-good output
│   ├── case_002_market_sizing_ev.json
│   └── case_003_industry_disruption.json
├── results/
│   ├── round_1_scores.json  # Pipeline v1 scores
│   ├── round_2_scores.json  # Pipeline v2 scores
│   └── ...
└── improvements.md  # What changed between rounds and why
```

---

## 15. Autoquant — 135 Distributed Agents

**Source:** @varun_mathur. Autoquant: 135 autonomous agents in a distributed quant research lab. P2P gossip protocol for sharing strategies. Version 2.6.9 suggests serious iteration.

**Core Content:**

The most ambitious autoresearch derivative. 135 agents collaborating via peer-to-peer gossip protocol — agents share strategies with their neighbors, and successful strategies propagate through the network. No central coordinator. Emergent collaboration through local information sharing.

**Connection to Jack's Project:**

The gossip protocol concept is interesting for a future evolution of the research pipeline. Instead of a central orchestrator routing information, research agents could share findings laterally — Agent A investigating company financials discovers a supply chain risk, and "gossips" this to Agent B investigating competitive landscape, who then checks whether competitors face the same risk.

For the capstone, this is likely too complex to implement. But it's worth mentioning in the "future work" section as a scaling pattern.

**What It Changes About the Proposal:**

Mention in "future work" as a potential scaling architecture. For the capstone scope, the centralized orchestrator is sufficient. For a production system handling dozens of simultaneous research projects, a gossip-based coordination protocol could be more efficient.

---

## 16. autoresearch@home — 34 Distributed Agents with Shared Memory

**Source:** @christinetyip (Christine Yip / Ensue AI). 34 agents across distributed machines collaborating via shared memory. 803 experiments without human intervention.

**Core Content:**

Agents can see what others have tried, build on each other's results, and avoid redundant work. The coordination layer IS the shared memory — not a separate orchestrator. Agents read the shared memory before starting work, identify what's been tried, and choose novel approaches.

**Connection to Jack's Project:**

The shared memory pattern is directly applicable. All research agents should read from and write to a shared `findings.json` before and after each research thread. Before starting a new thread, the agent checks: "Has anyone already investigated this? What did they find? How can I build on it rather than duplicate it?"

This is especially critical for Keystone's use case. If two research projects on related topics run sequentially, the second should leverage the first's findings automatically, not start from scratch.

**What It Changes About the Proposal:**

Layer 1 should have a **shared findings store** that persists across research sessions and projects. Every agent reads it before starting work and writes to it upon completion. This is the "institutional memory" of the research practice.

**Concrete Application:**

The shared memory is the `research-index.json` + `findings/` directory described under the Context Engineering article. The critical addition: it persists across projects, building a growing corpus of research findings that future projects can query.

---

## 17. Community Roundup of Autoresearch Applications

**Source:** @zhengyaojiang. Community roundup of autoresearch applications after 2 weeks. The principle: "anything with a measurable metric can be autoresearched."

**Core Content:**

Meta-survey of what works across domains: ML training, interpretability research, financial markets, reinforcement learning, game design. The common thread: define an editable asset, define a scalar metric, run the loop.

**Connection to Jack's Project:**

The question for Jack: **what is the "scalar metric" for consulting research quality?** This is the hardest part. Karpathy had loss functions. Worsey had Sharpe ratios. Jack needs a research quality score that:
- Is computable (an evaluator agent can produce it)
- Correlates with actual quality (a Keystone partner would agree with the score)
- Is granular enough to drive improvement (not just "good/bad" but "strong analysis, weak sourcing, generic narrative")

Defining this metric IS the capstone contribution. The pipeline architecture is important, but the evaluation framework is what makes the self-improvement loop possible.

**What It Changes About the Proposal:**

The capstone should explicitly address: **how do you define and measure "research quality" in a way that enables automated self-improvement?** This is the novel academic contribution. The multi-agent architecture is engineering. The quality metric is research.

**Concrete Application:**

Design a multi-dimensional research quality score:
```
Research Quality Score = weighted average of:
  - Analytical Depth (0-10): Are conclusions non-obvious? Is the analysis layered?
  - Source Quality (0-10): Are sources authoritative and diverse?
  - Quantitative Rigor (0-10): Are claims supported by data? Are uncertainties quantified?
  - Narrative Coherence (0-10): Does the analysis tell a clear story? Is the "so what?" evident?
  - Completeness (0-10): Are obvious questions addressed? Are there gaps?
  - Actionability (0-10): Could a consultant use this to advise a client?
```

Calibrate by scoring 10+ past Keystone deliverables on this rubric, then tuning the evaluator until its scores match Jack's scores within ±1 point.

---

# TIER 2: HIGH-VALUE BOOKMARKS — Claude Code & Tools

---

## 18. Prompt Caching — The Foundation of Everything

**Source:** @trq212 (Thariq Shihipar, Claude Code engineer at Anthropic). "Long running agentic products like Claude Code are made feasible by prompt caching which allows us to reuse computation from previous roundtrips and significantly decrease latency and cost. At Claude Code, we build our entire harness around prompt caching."

**Core Content:**

Stable prefixes (system prompts, tools, context files) get cached, dramatically reducing cost and latency on subsequent turns. The key design principle: keep stable content at the TOP of the context, dynamic content at the BOTTOM. Anything that changes invalidates the cache from that point forward. Claude Code "declares SEVs if prompt cache hit rates are too low."

**Connection to Jack's Project:**

The research pipeline will make many API calls per project. If the system prompt, tool definitions, and evaluation rubric are stable across calls (they should be), prompt caching means each subsequent call is dramatically cheaper and faster. But this requires *architectural discipline*:
- System prompt must not change during a research project
- Tool definitions must be stable
- Dynamic content (research findings, progress updates) must go at the END of the context

This is a cost/performance concern, not an architecture concern — but at Keystone scale (potentially dozens of research projects per month), the cost implications are significant.

**What It Changes About the Proposal:**

Add **prompt caching awareness** to the architecture design. The system prompt, tool definitions, and evaluation rubric should be designed as stable prefixes that never change within a project. Research data goes at the end.

---

## 19. Thariq's Pinned Technical Writing Thread

**Source:** @trq212. Full index of all technical articles on agent design, prompt caching, tool architecture. Blog at thariq.io with pieces on LLM sorting with TrueSkill, interpretability, and computer use. Referenced by multiple bookmarks (@Shpigford, @kloss_xyz).

**Core Content:**

This is a meta-source — an index of Thariq's technical writing. The individual articles (tool design, prompt caching) are covered separately. The value of the index itself is as a curated reading list from someone with direct Claude Code engineering experience.

**Connection to Jack's Project:**

Jack should read Thariq's entire article index as background research for the capstone's literature review. Thariq's perspectives come from building production agentic systems, not from academic research. This practitioner-grounded perspective would strengthen the capstone's credibility.

**Concrete Application:**

Add Thariq's articles to the capstone bibliography. Cite his practitioner experience alongside academic sources.

---

## 20. CLAUDE.md Best Practices from Boris Cherny

**Source:** @NieceOfAnton (Srishti). Aggregation of best practices from the Claude Code product lead. The image likely contains the actual CLAUDE.md template.

**Core Content:**

Boris Cherny's recommended practices for configuring Claude Code. The specific patterns: encoding workflows into skills, using the smartest model available (counterintuitively cheaper due to fewer retries), running many agents in parallel.

**Connection to Jack's Project:**

The "smartest model available is actually cheaper" insight validates Jack's Opus 4.6 for everything approach. For the research pipeline, this means: don't try to save costs by using Haiku for research agents and Opus only for synthesis. Use Opus everywhere — the reduction in retries, hallucinations, and evaluator rejections more than compensates for the per-token cost increase.

**What It Changes About the Proposal:**

Validate the model selection strategy: **Opus 4.6 for all agents in the pipeline.** Don't split models by layer. The quality-cost tradeoff favors the best model everywhere.

---

## 21. Boris Cherny's Setup: 5-10 Claudes in Parallel

**Source:** @startupideaspod. Direct from the Claude Code product lead. Key formula: (1) Use smartest model available, (2) Run many agents in parallel, (3) Encode everything into skills.

**Core Content:**

Cherny runs 5-10 Claude instances in parallel from his phone, each working on different tasks. The key to scaling isn't better prompts — it's parallelism + skills encoding. Skills capture domain expertise in a reusable format that any agent can execute.

**Connection to Jack's Project:**

The "encode everything into skills" principle is critical. Every research workflow that Jack develops for the capstone should be encoded as a reusable skill:
- `industry-analysis.skill` — how to analyze an industry structure
- `company-valuation.skill` — how to build a quick valuation model
- `competitive-positioning.skill` — how to map competitive dynamics
- `market-sizing.skill` — how to estimate addressable market

Each skill encodes Keystone's specific methodology, not generic best practices.

**What It Changes About the Proposal:**

Add a **Skills Library** as a first-class component. Research methodologies should be encoded as reusable skills, not embedded in prompts. This enables: (a) consistent methodology across projects, (b) iterative improvement of individual skills, (c) easy addition of new research capabilities.

**Concrete Application:**

Build a `skills/` directory within the research pipeline:
```
skills/
├── market-sizing/
│   ├── SKILL.md  # Methodology: top-down + bottom-up + triangulation
│   └── examples/  # Past market sizing analyses as references
├── competitive-analysis/
│   ├── SKILL.md  # Methodology: Porter's Five Forces + positioning matrix
│   └── examples/
├── financial-analysis/
│   ├── SKILL.md  # Methodology: ratio analysis + trend decomposition
│   └── examples/
└── industry-structure/
    ├── SKILL.md  # Methodology: value chain mapping + profit pool analysis
    └── examples/
```

---

## 22. Claude Code Productivity Tips from SaaS Trenches

**Source:** @arvidkahl. Practical advice from building SaaS products with Claude Code.

**Core Content:**

Key tip: "For any non-trivial feature, shift-tab into planning mode and tell it to 'do deep research on best practices and known issues, using web search.' READ the plan before accepting."

The principle: don't let the agent jump straight to execution. Force a research-then-plan-then-execute cycle. Review the plan before allowing execution.

**Connection to Jack's Project:**

The research-then-plan-then-execute cycle IS the pipeline. Layer 1 is research. Layer 2 is planning/structuring. Layer 3 is execution/generation. The insight here is that each layer should produce a reviewable intermediate artifact before the next layer begins. The Planner's output should be reviewed (by the evaluator or by Jack) before research agents start working. The research findings should be reviewed before structuring begins.

**What It Changes About the Proposal:**

Add **human review gates** between layers. After Layer 1 produces findings and before Layer 2 begins structuring, there should be an option for Jack (or a Keystone consultant) to review the findings and redirect if needed. Similarly after Layer 2 and before Layer 3. The system should support both fully autonomous and human-in-the-loop modes.

---

## 23. Fan-Out Deep Research

**Source:** @elvissun. "Use unused weekly compute limits by running parallel deep research tasks. The outputs are 'context-dense files you reuse forever' with zero review cycles needed."

**Core Content:**

Practical tip: spawn 5-10 parallel research agents, each investigating a different sub-topic. Each produces a dense research file. These files become permanent assets — reusable across future projects. The key insight: research outputs compound. Every research file produced is an asset that makes future research faster and cheaper.

**Connection to Jack's Project:**

This is the operational model for Layer 1. Don't do research linearly — fan out 5-10 agents simultaneously. Each produces a `findings/topic_X.md` file that becomes a permanent asset in the research corpus. Future projects on related topics can query these files instead of re-researching from scratch.

At Keystone, this means: every research project Jack's system completes makes the system more valuable. The findings compound. A research file on "autonomous vehicle market dynamics" produced for Client A is reusable (minus confidential details) for Client B's adjacent project.

**What It Changes About the Proposal:**

Frame the research pipeline as **an asset-accumulation system**, not just a task-completion system. Every project produces durable research assets that compound. This changes the ROI calculation — the system's value grows with every project completed.

---

## 24. Anthropic Open-Sourced Skills Library

**Source:** @ihtesham2005. Anthropic's own internal skills library is open source.

**Core Content:**

Production-tested, plug-and-play skill components from Anthropic. These are the skills Anthropic uses internally — frontend design, code review, documentation, testing.

**Connection to Jack's Project:**

Study the *structure* of Anthropic's skills — how they're organized, how they encode methodology, how they reference examples. Use this as a template for Jack's research skills. The specific content (frontend design) isn't relevant, but the *format and architecture* of production-quality skills is.

**Concrete Application:**

Read the Anthropic skills library, extract the structural patterns, and apply them to research skill design.

---

## 25. Hidden Claude Code Setting for Faster Code Search

**Source:** @om_patel5. Claims there's a flag enabling semantic code indexing instead of text grep.

**Core Content:**

A specific configuration flag that improves code navigation by using semantic indexing. If true, this changes how agents find relevant code.

**Connection to Jack's Project:**

Minor connection. When building the research pipeline's codebase, semantic code search would help research agents navigate the pipeline's own code more efficiently. But this is a developer tool improvement, not an architecture change.

---

# TIER 2: HIGH-VALUE BOOKMARKS — Research Tools & Data

---

## 26. Cloudflare /crawl Endpoint

**Source:** @CloudflareDev. 25.6K bookmarks. One API call crawls an entire site, returns HTML/Markdown/JSON.

**Core Content:**

`POST /crawl` with a starting URL, configurable depth and page limit. Returns structured content from an entire website. Free tier available. Handles JavaScript rendering, respects robots.txt, and returns clean Markdown.

**Connection to Jack's Project:**

This is infrastructure for Layer 1. When a research agent needs to understand a company's website (products, pricing, team, press releases), Cloudflare /crawl can systematically extract all relevant content in one API call. This replaces the manual pattern of fetching individual pages.

For consulting research, company websites are primary sources. Being able to ingest an entire company website — all product pages, About Us, press releases, careers page — and have it available for analysis is a significant capability.

**What It Changes About the Proposal:**

Add **Cloudflare /crawl** as a Layer 1 data ingestion tool. It complements existing web search (for finding sources) with systematic site crawling (for deeply understanding a specific source).

**Concrete Application:**

A `crawl_company_website(url, depth=2)` tool that:
1. Crawls the company's website to specified depth
2. Extracts product descriptions, team info, press releases
3. Returns structured Markdown organized by page type
4. Caches results for future queries about the same company

---

## 27. Defuddle.md — YouTube Transcripts with Timestamps

**Source:** @kepano (Steph Ango, Obsidian CEO). 3.2K bookmarks.

**Core Content:**

Paste a YouTube link, get a Markdown transcript with timestamps, chapters, and speaker diarization. Also powers Obsidian Web Clipper's Reader mode.

**Connection to Jack's Project:**

YouTube is a significant research source. Earnings call recordings, conference presentations, expert interviews, industry keynotes — all on YouTube. Being able to ingest these as structured transcripts with timestamps and speaker labels makes them usable as research inputs.

For the capstone, this enables a novel data source category: **video content as structured research input.** A CEO's conference keynote becomes a searchable, quotable document.

**What It Changes About the Proposal:**

Expand Layer 1's data source types to include **video/audio transcripts**. The original proposal focuses on text sources (web, filings, documents). Adding video transcript ingestion significantly expands the research surface area.

**Concrete Application:**

A `transcribe_video(youtube_url)` tool in Layer 1 that:
1. Fetches the transcript via Defuddle
2. Structures it with timestamps, speakers, and chapters
3. Stores in the research index as a citable source
4. Enables the research agent to quote specific moments with timestamps

---

## 28. AlphaXiv Claude Skill — Structured Paper Summaries

**Source:** @oliviscusAI. 4.3K bookmarks.

**Core Content:**

Instead of uploading raw PDFs to Claude (token-wasteful), this skill extracts arXiv IDs and fetches pre-built, machine-readable structured overviews: problem, approach, results, limitations.

**Connection to Jack's Project:**

Academic papers are relevant for some consulting research (industry analysis, technology assessment, market sizing methodologies). Raw PDFs waste enormous context. Pre-structured overviews are exactly what a research agent needs: "What problem does this paper address? What did they find? How robust are the results?"

**What It Changes About the Proposal:**

For academic sources in Layer 1, use structured summaries instead of raw PDFs. This applies the context engineering principle (minimize tokens, maximize signal) specifically to academic literature.

---

## 29. Claude Wealth Management Plugin

**Source:** @mrjain. 22.8K bookmarks. Anthropic's official financial modeling plugin with six skills: Client Report, Client Review Prep, Financial Plan, Investment Proposal, Portfolio Rebalance, Tax-Loss Harvesting.

**Core Content:**

A production-grade example of how Anthropic structures domain-specific skills for professional services. Each skill has defined inputs, outputs, and intermediate steps. The architecture: domain expertise encoded as skills, with structured workflows for specific deliverable types.

**Connection to Jack's Project:**

This is the closest existing analog to what Jack is building. The wealth management plugin produces professional financial deliverables from data + expertise. Jack's research pipeline produces professional research deliverables from data + expertise. The skill structure (Client Report = Research Report, Financial Plan = Strategic Analysis, Investment Proposal = Recommendation Deck) maps almost 1:1.

Study this plugin's architecture as a direct template. How does it structure inputs? How does it encode domain expertise? How does it format outputs? How does it handle quality assurance?

**What It Changes About the Proposal:**

Use the Wealth Management Plugin as an **architectural template** for the research pipeline's skill structure. Each consulting deliverable type (industry analysis, competitive landscape, market sizing, strategic recommendation) should be a skill with the same structure as the wealth management skills.

**Concrete Application:**

Model the research pipeline's skill architecture after the wealth management plugin:
```
skills/
├── industry-analysis/  # Analogous to "Client Report"
│   ├── inputs.json     # Required: industry, scope, depth, client_context
│   ├── SKILL.md        # Methodology: value chain, profit pools, trends
│   └── output_template.md  # Structure of the final deliverable
├── competitive-landscape/  # Analogous to "Investment Proposal"
│   ├── inputs.json
│   ├── SKILL.md
│   └── output_template.md
└── strategic-recommendation/  # Analogous to "Financial Plan"
    ├── inputs.json
    ├── SKILL.md
    └── output_template.md
```

---

## 30. Gemini Embedding 2 — Multimodal Embeddings

**Source:** @VibeMarketer_. 11.6K bookmarks. Google's new embedding model that natively handles text, images, PDFs, audio, and video.

**Core Content:**

First truly unified multimodal embedding model. A single query searches across all modalities — text documents, images, PDFs, audio transcripts, video. No separate embedding pipelines for each modality.

**Connection to Jack's Project:**

For the research pipeline's retrieval layer, multimodal embeddings mean:
- A query about "autonomous vehicle sensor costs" simultaneously searches text reports, investor presentation slides (images), earnings call transcripts (audio), and product demo videos
- No need for separate search pipelines per modality
- The research agent issues one query and gets results from all source types

This is especially powerful for consulting, where research spans many media types: PDFs, presentations, videos, web pages, spreadsheets.

**What It Changes About the Proposal:**

The retrieval layer in Layer 1 should use **multimodal embeddings** to enable unified search across all source types. This simplifies the architecture (one search pipeline instead of many) and improves recall (findings aren't missed because they're in the "wrong" modality).

---

## 31. Skill Graph / Wikilink Architecture — Ars Contexta

**Source:** @rohit4verse. 4.9K bookmarks. Open-source Claude Code plugin that structures agent knowledge as a traversable graph connected by wikilinks.

**Core Content:**

Skills reference each other via wikilinks, creating a navigable knowledge topology. Instead of flat, independent skills, they form a connected graph where the agent can traverse from one skill to related skills. The agent discovers relevant skills by following links, not by searching a flat list.

**Connection to Jack's Project:**

Research methodologies aren't independent — they connect. An industry analysis links to competitive landscape (same industry). Market sizing links to financial analysis (TAM informs revenue projections). The research pipeline's skills should reflect these connections:

- `market-sizing.skill` links to `industry-analysis.skill` (market sizing requires industry understanding)
- `competitive-analysis.skill` links to `company-valuation.skill` (competitive position affects valuation)
- `financial-analysis.skill` links to `market-sizing.skill` (financials contextualize within market)

This means research agents can *discover* that they need additional analysis by following skill links — not because someone told them, but because the knowledge graph surfaces the connection.

**What It Changes About the Proposal:**

Skills should be **interconnected, not flat.** Use wikilinks or explicit references to create a skill graph. Research agents navigating this graph can discover that their current task requires complementary analysis from a related skill.

---

# TIER 2: HIGH-VALUE BOOKMARKS — OpenClaw & Infrastructure

---

## 32. "Your OpenClaw is Ignoring Half Your Instructions"

**Source:** @jordymaui. Key insight: language instructions drift — telling an agent "always validate the output" gets skipped 40% of the time. The fix: encode critical instructions into code/hooks/structural enforcement, not just prompt text.

**Core Content:**

Prompt-based rules have a compliance ceiling. No matter how emphatically you say "always check your sources," the agent will sometimes skip it. The solution: structural enforcement. If source verification is critical, build it into the tool — the tool itself verifies sources before returning results. If quality gates are critical, build them into the harness — the harness automatically routes output to the evaluator before delivering.

**Connection to Jack's Project:**

This is critical for the research pipeline's reliability. If the system prompt says "always cite your sources," research agents will sometimes produce uncited claims. If the system prompt says "always verify data accuracy," agents will sometimes skip verification. The fix: structural enforcement.

- Source citation: build it into the tool. The `research_search` tool returns results WITH citations pre-attached. The agent can't produce an uncited finding because the tool's output format includes the citation.
- Data verification: build it into the harness. Before any finding is committed to the findings store, the harness automatically runs a verification check (is this data current? is the source accessible? does the claim match the source?).
- Quality gates: build them into the pipeline. The evaluator runs automatically after each section, not because the system prompt says to, but because the harness code routes output to the evaluator.

**What It Changes About the Proposal:**

**Critical rules should be enforced structurally, not via prompts.** This is a new design principle for the capstone. Identify the top 5 quality requirements (source citation, data accuracy, analytical depth, Keystone formatting, completeness) and enforce each one through code, not instructions.

**Concrete Application:**

Build structural enforcement for the top quality requirements:
1. **Source citation:** Tools return `{finding: "...", sources: [{url, title, accessed_date}]}`. The finding is never stored without attached sources.
2. **Data accuracy:** Before committing to findings store, a verification agent spot-checks claims against sources. This is automatic, not optional.
3. **Completeness:** The task tracker requires all sub-tasks to pass before the thread is marked complete. No "skip to the next thing."
4. **Format compliance:** Output templates enforce Keystone's structure. Agents fill in templates, not free-form text.

---

## 33. Gmail Security via Architecture (gog CLI)

**Source:** @elvissun. Solved Gmail security for OpenClaw using `gog` CLI — drafting only, security enforced by architecture not by prompt.

**Core Content:**

Instead of telling agents "don't send emails without approval," make it structurally impossible. The gog CLI is configured to ONLY create drafts, never send. Approval happens outside the agent's control. Security by design, not by instruction.

**Connection to Jack's Project:**

The "security by design" principle applies to research quality. Instead of telling agents "produce high-quality research," make it structurally impossible to produce low-quality research. How?

- Agents can't mark tasks as complete — only the evaluator can change `passes` from false to true
- Agents can't write to the final deliverable directly — they write to a staging area, and the evaluator promotes accepted sections
- Agents can't skip research sources — the tool requires minimum source diversity before returning results

**What It Changes About the Proposal:**

Apply the **security-by-design principle to quality**. Quality gates should be architecturally enforced, not prompt-enforced.

---

## 34. Security-Focused OpenClaw Setup Guide

**Source:** @JordanLyall. "How I Set Up OpenClaw Without Giving It the Keys to My Life."

**Core Content:**

A locked-down, minimum-risk approach to agent setup that then extends carefully. Start with minimal permissions, add capabilities only as needed, with explicit security boundaries.

**Connection to Jack's Project:**

The research pipeline will access sensitive data — Keystone's internal documents, client information, financial data. The pipeline needs a security model:
- Research agents can READ internal documents but can't WRITE to them
- Agents can access public data freely but internal data only with explicit authorization
- Client-confidential information should be sandboxed — never mixed between client projects
- The pipeline should maintain an audit log of what data was accessed for each project

**What It Changes About the Proposal:**

Add a **security model** to the architecture, especially for handling internal/confidential data. This is important for the capstone because Keystone will need assurance that the tool respects data boundaries.

---

## 35. ACP (Agent Client Protocol) for Claude Code Integration

**Source:** @onusoz, @bilbeny, @steipete. OpenClaw can spawn Claude Code and Codex sessions via ACP. Running CLI via ACP is officially allowed.

**Core Content:**

ACP enables spawning and coordinating multiple coding agents through OpenClaw. Each runs in its own session. The orchestrator can manage multiple concurrent agents.

**Connection to Jack's Project:**

ACP is the *implementation mechanism* for the research pipeline's multi-agent architecture. When the orchestrator needs to spawn 5 parallel research agents, it uses ACP to create 5 concurrent sessions. When the evaluator needs to run, it's another ACP session. This is the plumbing that makes the architecture possible.

**What It Changes About the Proposal:**

Specify **ACP as the implementation protocol** for agent-to-agent communication and spawning. This grounds the abstract architecture in a concrete implementation mechanism.

---

## 36. LCM (Lossless Context Management) Plugin

**Source:** @steipete (Peter Steinberger, OpenClaw creator). Recommended config for memory management.

**Core Content:**

LCM handles context compression and memory management. Recommended settings: `freshTailCount: 32`, `contextThreshold: 0.75`, `summaryModel: "claude-3-5-haiku"` (for cost efficiency).

**Connection to Jack's Project:**

For long-running research projects, context management is critical. LCM ensures that research agents maintain coherence across long sessions without losing critical findings. The recommendation to use Haiku for compaction summaries (while using Opus for actual work) is a smart cost optimization.

---

# TIER 2: HIGH-VALUE BOOKMARKS — Other Notable Sources

---

## 37. Ray Dalio's "Great Disorder" Essay

**Source:** @MINHxDYNASTY referencing @RayDalio. 12.7K bookmarks.

**Core Content:**

Dalio argues the US has entered Stage 6 of his Big Cycle framework — the final stage before a new world order. Deep analysis of debt crises, geopolitical power shifts, and structural economic risks.

**Connection to Jack's Project:**

Not directly relevant to the pipeline architecture, but highly relevant to Jack's *content knowledge as a consultant*. Understanding macro frameworks like Dalio's Big Cycle gives Jack intellectual credibility in strategy discussions. A research pipeline that can synthesize Dalio-level macro analysis with company-specific data would produce genuinely differentiated deliverables.

More practically: this is the kind of content that a research pipeline should be able to ingest, synthesize, and apply. If a client asks "what macro risks affect our industry?", the pipeline should be able to pull frameworks like Dalio's and apply them to the specific context. This tests the pipeline's ability to handle complex, nuanced, framework-heavy analysis — not just data aggregation.

---

## 38. CodexBar — Usage Tracking

**Source:** @tom_doerr. 2.9K bookmarks. macOS menu bar app tracking AI usage limits.

**Core Content:**

Tracks session and weekly usage across Claude, Codex, Gemini. Shows reset countdowns.

**Connection to Jack's Project:**

Operational tool. When running many agents in parallel (which the research pipeline does), tracking usage limits prevents unexpected rate-limiting or cost overruns. Install for pipeline development.

---

## 39. twitter-cli — Terminal CLI for X

**Source:** @jedisct1. 1.9K bookmarks. No API key needed. Structured YAML/JSON output.

**Core Content:**

Terminal-first access to X/Twitter with structured output suitable for agent integration.

**Connection to Jack's Project:**

Minor connection. Could be a Layer 1 data source for research that involves social media analysis or expert commentary tracking. Some consulting research requires monitoring industry expert opinions on X — a CLI with structured output would make this automatable.

---

# SYNTHESIS: How This Changes the Capstone Architecture

Based on the deep analysis of all HIGH-value sources above, here's how the original three-layer proposal should evolve:

## Original Proposal
```
Layer 1: Data Ingestion & Synthesis
Layer 2: Content Structuring & Reasoning  
Layer 3: Generation & QA
```

## Revised Architecture
```
Layer 0: ORCHESTRATION
├── Receives research question from user
├── Spawns Initializer to decompose into task list (JSON)
├── Manages agent lifecycle via ACP
├── Tracks progress in research-status.json
├── Provides human review gates between layers
└── Never does substantive work itself

Layer 1: DATA INGESTION & RESEARCH
├── Parallel fan-out: 3-5 research agents per orchestrator
├── Git-based task claiming (lock files prevent duplicates)
├── Shared findings store (persists across projects)
├── Just-in-time context loading (index-based, not pre-loaded)
├── Unified retrieval: public + internal + historical
├── Tools designed for agent consumption (concise, pre-processed)
├── Data sources: web, filings, internal docs, video transcripts, academic papers
└── Each agent returns 1-2 page condensed findings

Layer 1.5: DELIBERATION (NEW)
├── Multi-perspective debate (Bull/Bear/Consensus/Contrarian)
├── Identifies consensus vs. contested findings
├── Produces confidence map for structuring agent
└── Catches contradictions and gaps

Layer 2: CONTENT STRUCTURING & REASONING
├── Receives synthesized findings + confidence map
├── Applies consulting frameworks via skill library
├── Builds narrative arc ("so what?" → implications → recommendations)
├── Sprint contracts with evaluator before each section
└── Produces structured outline with supporting evidence

Layer 3: GENERATION
├── PowerPoint creation from structured outline
├── Chart/model generation from quantitative findings
├── Executive summary tailored to audience
└── Formatting per Keystone standards (via templates)

Layer 4: EVALUATION (SEPARATE FROM GENERATION)
├── Independent evaluator agent (never the generator)
├── Calibrated to Keystone partner standards via few-shot examples
├── Multi-dimensional rubric (depth, sources, rigor, narrative, completeness, actionability)
├── Grades each section independently
├── Failed sections → specific feedback → regeneration loop
└── Structural enforcement (not prompt-based)

Meta-Layer: SELF-IMPROVEMENT
├── Autoresearch loop: run pipeline against test cases, measure quality, iterate
├── Darwinian prompt evolution: worst-performing agent prompts get rewritten
├── Trajectory storage: every project logs decisions, sources, feedback
├── Skill library grows with each project
├── Improvement curve tracked quantitatively for capstone reporting
└── Research findings compound as reusable assets
```

## New Design Principles (from the sources):

1. **Evaluator is king** — Quality is bounded by evaluation quality, not generation quality (Anthropic Harness)
2. **Context is scarce** — Every token has an opportunity cost; minimize context, maximize signal (Context Engineering)
3. **Tools > Prompts for reliability** — Critical rules enforced structurally, not via instructions (jordymaui)
4. **JSON > Markdown for state** — Models corrupt Markdown; JSON's rigidity protects state (Effective Harnesses)
5. **Compound research assets** — Every project makes the system more valuable (Fan-Out Research)
6. **Sprint contracts before generation** — Negotiate "done" criteria before work begins (Harness Design)
7. **Separate generation from evaluation, always** — Self-evaluation is systematically biased (Harness Design, C Compiler)
8. **2-5 agents per coordinator** — Empirical scaling limit (Let Them Cook)
9. **Skills + Souls, not just prompts** — Agents need identity/judgment AND procedural knowledge (tolibear_)
10. **The metric IS the contribution** — Defining "research quality" computably is the novel academic work (Autoresearch Community)

---

*This analysis drew from 39 HIGH-value bookmarks across three analysis files and 5 Anthropic engineering articles read in full (~136,000 characters of source material). Each source was analyzed individually for specific connections to Jack's multi-agent research pipeline capstone project.*
