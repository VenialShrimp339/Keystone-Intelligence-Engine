# Context management for long-running multi-agent research systems

**For a system dispatching 3–5 Sonnet subagents per round across 2–4 rounds, the evidence overwhelmingly favors context resets with structured handoffs over context accumulation, combined with a file-based external memory layer that persists findings between rounds.** Anthropic's own research system—architecturally similar to Keystone Intelligence Engine—uses this pattern and outperforms single-agent Opus by **90.2%** on research tasks. The critical insight from multiple production systems is that context is a finite resource with diminishing marginal returns: LLM performance degrades **13.9–85%** as context length increases, even when models can perfectly retrieve all relevant information. The optimal strategy treats the orchestrator's context window as a coordination surface (not a knowledge store), while pushing accumulated findings into external memory that agents read on demand.

---

## Anthropic's three posts define the state of the art

Anthropic published three engineering posts that together form a coherent context management philosophy for multi-agent systems. Understanding how they combine is essential for Keystone's architecture.

The **September 2025 "Context Engineering" post** (by Rajasekaran, Dixon, Ryan, and Hadfield) establishes the foundational principle: context must be treated as **"a finite resource with diminishing marginal returns."** Due to transformer attention mechanics, every token attends to every other token in n² pairwise relationships. As context grows, the model's ability to capture these relationships gets stretched thin. The post recommends three techniques for long-horizon tasks: compaction (summarizing conversation history), structured note-taking (agents writing persistent notes outside the context window), and sub-agent architectures where specialized agents handle focused tasks with clean context windows. The critical design directive is to **"find the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."**

The **November 2025 "Effective Harnesses" post** (by Justin Young) operationalizes this with the `claude-progress.txt` pattern. A two-agent system splits work: an Initializer Agent creates a progress file, feature list, and init script during the first session; a Coding Agent reads these artifacts at the start of every subsequent session to resume work. The key insight: **"finding a way for agents to quickly understand the state of work when starting with a fresh context window"** matters more than preserving full conversation history. This pattern—inspired by how effective software engineers hand off work—uses git history plus a structured progress file as the bridge between context windows.

The **March 2026 "Harness Design" post** (by Prithvi Rajasekaran) directly compares the two core strategies and delivers a clear verdict: **"Context resets—clearing the context window entirely and starting a fresh agent, combined with a structured handoff that carries the previous agent's state—differs from compaction, where earlier parts of the conversation are summarized in place. While compaction preserves continuity, it doesn't give the agent a clean slate, which means context anxiety can still persist."** The post introduces the concept of "context anxiety"—models losing coherence on lengthy tasks and prematurely wrapping up work as they approach perceived context limits. Notably, the post also reports that **Opus 4.6 largely eliminated context anxiety**, allowing the team to drop context resets entirely for that model. The implication for Keystone: with Opus 4.6 as orchestrator, compaction via the Claude Agent SDK may suffice for the lead agent, while Sonnet 4.6 subagents should still operate with clean, isolated context windows per task.

Anthropic's **June 2025 multi-agent research system post** provides the closest architectural parallel to Keystone. Their LeadResearcher (Opus) saves its research plan to an external Memory store because "if the context window exceeds 200,000 tokens it will be truncated and it is important to retain the plan." Subagents store their work in external systems and pass **lightweight references** back to the coordinator, explicitly to "minimize the 'game of telephone.'" A dedicated **CitationAgent** handles source attribution as a separate post-processing step. This system uses ~**15× more tokens** than chat interactions, but token usage explains **80% of performance variance**—spending more tokens on research quality pays off directly.

**How the three patterns combine for Keystone:** The orchestrator (Opus 4.6) should persist its research plan and round-by-round synthesis to external memory files at the start of each round. Subagents (Sonnet 4.6) receive clean context windows with only their specific task instructions plus relevant prior findings retrieved from external memory. Between rounds, the orchestrator reads subagent outputs and its own persisted state, performs synthesis, and writes updated findings back to external memory before dispatching the next round. This is context resets for subagents (they always start clean) plus structured note-taking for the orchestrator (external memory as the continuity mechanism).

---

## Context windows degrade well before they fill up

Multiple independent studies confirm that LLM performance degrades significantly as context utilization increases, establishing hard constraints on how much information should flow through any single agent's context window.

The landmark **"Lost in the Middle" paper** (Liu et al., Stanford/Meta) demonstrates a U-shaped performance curve: accuracy is highest when relevant information sits at the beginning or end of context, degrading by **over 30%** when critical information is in the middle. This finding holds across all tested models and persists even with extended-context architectures.

More alarming is **"Context Length Alone Hurts LLM Performance Despite Perfect Retrieval"** (Du et al., October 2025), which shows **13.9–85% performance degradation** from context length alone—even when models can perfectly retrieve all relevant information, even when irrelevant tokens are replaced with whitespace, and even when irrelevant tokens are completely masked. At **30,000 masked tokens**, performance still drops at least **7.9%**. This means context length imposes a "cognitive tax" independent of content quality.

The **Chroma Research "Context Rot" study** (July 2025) evaluated 18 frontier LLMs and found that model performance grows "increasingly unreliable" as input length grows, even on simple tasks. Distractors have non-uniform impact that compounds with input length, and haystack structure (logical flow vs. random ordering) consistently affects performance.

NVIDIA's **RULER benchmark** reveals that effective context is typically **50–65% of advertised context window size**. Only half of models claiming 32K+ context maintained satisfactory performance at 32K tokens. Even GPT-4 showed a **15.4-point accuracy drop** from 4K to 128K tokens. Production recommendations converge on **70–80% maximum utilization** as the operational ceiling, with compression triggered at **85% capacity** to leave buffer for the compression pipeline itself.

For Keystone specifically: with Opus 4.6's 200K context window, target keeping orchestrator context under **140–160K tokens** (70–80%). For Sonnet 4.6 subagents running focused tasks, keeping context under **100K tokens** is safer for maintaining high accuracy. Place the research plan and critical instructions at the beginning of context, and the most recent findings at the end—never bury critical information in the middle.

---

## Four external memory approaches, ranked for research pipelines

The choice of external memory architecture is perhaps the most consequential design decision for Keystone. Four approaches exist, each with distinct tradeoffs, and one hybrid pattern is emerging as the clear winner.

**File-based markdown memory** (as used by Claude Code) is the simplest and—surprisingly—often the most effective approach. Letta's benchmark found that a filesystem-based agent scored **74.0% on the LoCoMo benchmark** by simply storing conversation histories in files, beating Mem0's specialized graph variant at 68.5%. The reason: LLMs are extensively trained on filesystem operations (ls, grep, cat), making file manipulation a near-native capability. Claude Code uses hierarchical CLAUDE.md files loaded at session start, filesystem-persisted tasks for cross-session coordination, and shared files as the primary inter-agent communication mechanism. The ETH Zurich AGENTbench study found that human-written memory files improve agent performance by ~4%, though LLM-generated files actually hurt by ~2%—suggesting that file-based memory works best when the structure is human-designed and agents fill in content.

**Vector-based RAG** works well for document search over large, diverse corpora but fails for agent memory. Research from King's College London ("Beyond RAG for Agent Memory," February 2026) identifies three failure modes: redundant top-k retrieval (the same facts appear in many phrasings), pruning that breaks evidence chains, and similarity-based retrieval that misses logical structure. **Structure-driven retrieval consistently outperforms similarity-driven retrieval** for agent memory tasks. RAG is appropriate when Keystone needs to search across 200+ previously processed sources, but not for maintaining the working state of an ongoing research engagement.

**Andrej Karpathy's "LLM Knowledge Bases" pattern** (published April 2026) offers a compelling middle ground. Raw materials (papers, articles, datasets) go into a `raw/` directory. An LLM then *compiles* these into a structured markdown wiki: generating summaries, categorizing concepts, writing encyclopedia-style articles, creating backlinks, and maintaining auto-generated index files. At ~100 articles / ~400K words, Karpathy found that complex questions could be answered by the LLM navigating via summaries and index files **without "fancy RAG"**—the auto-maintained indices were sufficient. The community has extended this with a "Compound Loop" where agents dump raw outputs, a compiler organizes them, a validator checks quality, and verified briefings feed back to all agents. This pattern maps naturally to Keystone's multi-round architecture: each round's findings feed into a compiled knowledge base that subsequent rounds can navigate.

**The emerging best practice is a hybrid: filesystem interface backed by database substrate.** As Oracle's 2026 analysis puts it: "Don't conflate interface with substrate. Filesystems win as an interface (LLMs already know how to use them); databases win as a substrate (concurrency, auditability, semantic search)." For Keystone's needs—multiple Sonnet subagents potentially writing findings concurrently—a database-backed store exposed through a file-like interface provides both LLM familiarity and data integrity. AgentFS (by Turso) implements exactly this pattern using SQLite as a POSIX-like filesystem abstraction.

**Recommendation for Keystone:** Start with Karpathy's pattern adapted for research. Create a structured findings directory with auto-maintained index files. Each round's subagent outputs get "compiled" by the orchestrator into organized findings files. Use simple markdown files for the first version—the Letta benchmark proves this outperforms specialized tools. Add a database substrate only when concurrent write conflicts become a real problem.

---

## Subagent compression demands structured contracts, not free text

The compression ratio between what a subagent processes and what it returns to the orchestrator is a critical parameter. Get it wrong and information is either lost (too aggressive) or the orchestrator drowns in tokens (too conservative).

Anthropic's context engineering post states that each subagent "may use tens of thousands of tokens but returns only **1,000–2,000 token condensed summary.**" Their June 2025 multi-agent post emphasizes that "the essence of search is compression: distilling insights from a vast corpus." This implies a practical compression ratio of roughly **95–98%**: a subagent processing 50K tokens of search results and source content returns 1–2K tokens of findings.

However, Factory.ai's evaluation reveals a critical warning: **multi-session information retention with LLM summarization is only 37%**—nearly two-thirds of information is lost or corrupted during summarization. Academic research corroborates this: compression causes a **30–50 point drop in groundedness scores** on QA benchmarks. The more aggressive the compression, the less faithful the output to the original sources.

Three compression modalities exist, each with different information-fidelity tradeoffs:

- **Consolidation** (70–90% info retention, 30–50% compression): Reorganizes and removes redundancy while preserving details. Best when specific facts matter.
- **Summarization** (50–80% info retention, 60–90% compression): Preserves key points, sacrifices peripheral details. The default mode for most agent systems.
- **Distillation** (30–60% raw info retention, 80–95% compression): Captures principles and concepts, not specific details. Best for high-level synthesis.

JetBrains' December 2025 research offers a pragmatic alternative: **observation masking** (replacing stale tool outputs with placeholders while keeping tool calls visible) matched the quality of full LLM summarization on SWE-bench while being **52% cheaper**. The agent remembers what it did but large outputs are removed. Morph's **verbatim compaction** takes a similar approach: delete tokens rather than rewrite them, achieving **50–70% compression with 98% accuracy** and zero hallucination risk.

The practical contract for subagent responses, synthesized from Anthropic's system and Pasi Huuhka's analysis, should include a structured format with findings (3–7 key claims with confidence ratings and source references), status (complete/partial/blocked), and identified gaps. Critically, subagents should **store full research artifacts externally** (in the findings directory) and pass only lightweight references plus condensed insights back to the orchestrator. This "artifact bypass" pattern—where the orchestrator can read the full subagent output from a file if needed—prevents the information loss inherent in pure summarization while keeping the orchestrator's context lean.

For Keystone: define a Pydantic schema for subagent outputs. Each subagent returns structured findings (~1,500 tokens) plus writes its full research to an external file. The orchestrator reads the structured summary for synthesis decisions and can selectively read full artifacts when deeper detail is needed for the Deliberation phase.

---

## Source management requires external indexing and a dedicated citation pass

For systems processing 50–200 sources, no single agent's context window can hold the full source corpus. Production systems converge on a common architecture: decentralized discovery with centralized indexing and post-hoc citation validation.

**Anthropic's production pattern** uses subagents as "intelligent filters" that independently search, evaluate, and return condensed findings with source references. Sources are not centrally indexed during research—instead, a dedicated **CitationAgent** runs as a final post-processing step, receiving all documents and the research report to identify and validate specific citation locations. This separation ensures citation quality without burdening research agents with attribution tracking during discovery.

**Perplexity AI** processes sources through a 6-stage pipeline: query parsing → real-time retrieval (BM25 + dense embeddings) → multi-layer ranking → structured prompt assembly with pre-embedded citations → LLM synthesis constrained by retrieved evidence → citation attachment. They typically cite **3–5 sources per answer** and use authority scoring, freshness signals, and cross-source validation. **Elicit** scales to **1,000 papers and 20,000 data points**, using a process-based architecture that decomposes research into subtasks (searching, summarizing, classifying, extracting) and provides sentence-level citations with supporting quotes.

The metadata that should be tracked per source includes: unique source ID, URL, title, author, publication date, source type, quality/confidence rating, key claims extracted, retrieval context (which subagent found it, for what task), relevance score, and supporting quotes. The **PROV-AGENT framework** (August 2025) extends the W3C PROV standard for agentic workflows, modeling agents, tool executions, and responses as first-class provenance entities linked by relationships like `wasAttributedTo` and `wasGeneratedBy`.

**Recommendation for Keystone:** Implement an external source registry (a JSON file or lightweight database) where subagents register every source they consult with structured metadata. Assign unique source IDs at discovery time and propagate these IDs (not full content) through the agent chain. Add a dedicated Citation/Verification agent as the final pipeline step—this is proven by Anthropic and mirrors Keystone's existing isolation architecture. The Deliberation phase should have access to the full source registry for grounding its synthesis.

---

## The framework landscape validates Keystone's architectural choices

Surveying the major multi-agent frameworks reveals that Keystone's core design decisions—strict agent isolation, external state management, and PydanticAI with MCP—align with emerging industry consensus while avoiding common pitfalls.

**OpenAI's Agents SDK** uses typed `RunContextWrapper` objects for dependency injection (not sent to the LLM) and manages conversation state separately through sessions. Their compaction implementation triggers after 10+ non-user items accumulate. The key production insight from Manus (now part of Meta): **KV-cache hit rate is the single most important production metric**, with cached input tokens costing **10× less** than uncached. This means keeping prompt prefixes stable and context append-only directly impacts cost.

**Google's Agent Development Kit** articulates three principles that map to Keystone's architecture: separate storage from presentation (durable state vs. per-call views), make context transformations explicit and observable, and scope each model call to minimum required context. Their A2A protocol codifies Keystone's agent isolation principle at the protocol level—agents collaborate **"without sharing internal memory, tools, or context."**

**Microsoft's Azure SRE Agent** provides the most sobering production lessons. They started with 100+ tools and 50+ specialized sub-agents, then collapsed to **5 core tools and a handful of generalists**. Multi-agent handoffs had bimodal failure: **more than 4 handoffs almost always failed** due to discovery problems, system prompt fragility, and infinite loops. Their advice: "Invest context budget in capabilities, not constraints"—move domain knowledge from system prompts into files agents read on demand. This validates Keystone's approach of using external memory rather than bloated system prompts.

**PydanticAI** (Keystone's framework) supports agent delegation, programmatic hand-offs, and graph-based control flow via Pydantic Graph. Agents are stateless by design—state is managed externally and passed in via `RunContext`. It has first-class MCP integration and supports durable execution through Temporal, DBOS, and Prefect. The framework's stateless agent design perfectly supports Keystone's isolation architecture.

**LangChain's four-strategy taxonomy** provides a useful mental model: **Write** (persist information outside context), **Select** (retrieve only what's relevant), **Compress** (reduce tokens while preserving meaning), and **Isolate** (separate agent contexts). Keystone already implements Isolate by design; the primary optimization opportunity lies in Write (external memory) and Select (just-in-time context retrieval for the orchestrator).

---

## Handling contradictions when later rounds revise earlier findings

The "When Agents Disagree" paper (2025) establishes that **selection dramatically outperforms synthesis** for aggregating contradictory agent outputs. A diverse team with judge-based selection achieved an **81% win rate** against single-model baselines, while homogeneous teams using synthesis-based aggregation (blending candidates) scored only 51.2%—near chance. Synthesis introduces "incoherence, conflicting perspectives, and diluted arguments."

This has direct implications for Keystone's Deliberation phase. Rather than attempting to merge contradictory findings from different rounds into a single narrative, the orchestrator should act as a judge: evaluate competing claims against source evidence and select the better-supported position. The KARMA multi-agent system uses a dedicated **Conflict Resolution Agent** that specifically handles contradictions—disabling it lowered correctness by **4.9%**.

Research on multi-agent resilience shows that **hierarchical structures** (one coordinator overseeing peer agents) are the most robust, suffering only **~5% accuracy loss** with faulty agents, compared to 24% for chain structures. Two safeguards recover up to **96% of lost performance**: a "Challenger" pattern (agents questioning each other's outputs) and an "Inspector" pattern (independent reviewer). Keystone's Deliberation phase naturally implements the Inspector pattern; adding explicit claim-level confidence scores from subagents would enable more effective selection during deliberation.

---

## Concrete architecture recommendations for Keystone Intelligence Engine

Based on the full body of evidence, these are the highest-impact design decisions for Keystone's context management:

**Orchestrator context strategy:** With Opus 4.6, context anxiety is largely eliminated, so the orchestrator can accumulate within a single round using compaction. Between rounds, persist the research plan and synthesized findings to an external `research-state.md` file. At the start of each new round, the orchestrator reads this file plus the previous round's compiled findings rather than carrying forward full conversation history. Target **70–80% maximum context utilization** (~140–160K tokens).

**Subagent context strategy:** Each Sonnet 4.6 subagent starts with a clean context window containing only its task instructions, relevant prior findings (selected by the orchestrator), and tool definitions. Subagents return structured outputs (~1,500 tokens) via a Pydantic schema and write full research artifacts to external files. This achieves ~95% compression while preserving full detail in accessible artifacts.

**External memory architecture:** Implement a Karpathy-inspired findings directory with three layers: `raw/` (full subagent outputs per round), `compiled/` (orchestrator-synthesized findings organized by topic), and an auto-maintained `INDEX.md` that the orchestrator updates after each round's synthesis. This structure lets any agent navigate the accumulated knowledge base through index files rather than requiring everything in context.

**Source registry:** A `sources.json` file (or SQLite database if concurrent writes are needed) where subagents register every source with structured metadata. Source IDs propagate through the pipeline. A dedicated Citation agent validates attribution as the final pipeline step.

**Deliberation phase:** Use selection over synthesis. The orchestrator evaluates competing claims from different rounds against source evidence and selects the best-supported positions. Add explicit confidence scores and source counts to subagent outputs to enable evidence-weighted selection.

**What to monitor:** Track three metrics obsessively—context utilization percentage per agent per round, KV-cache hit rate (for cost optimization), and information retention rate (sample-check whether key findings from subagents survive into the final report). The 37% multi-session retention figure from Factory.ai's benchmark is the failure mode to guard against. Artifact-based bypass (writing to files, not just passing summaries) is the primary mitigation.