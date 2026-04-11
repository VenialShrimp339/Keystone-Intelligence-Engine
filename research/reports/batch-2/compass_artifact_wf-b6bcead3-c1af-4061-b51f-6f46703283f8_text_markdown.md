# Dynamic vs. fixed agent configuration in production multi-agent systems

**The emerging consensus is clear: production multi-agent systems dynamically generate agent configurations from flexible templates, not rigid type enums.** Anthropic's own multi-agent research system — the closest architectural analog to the Keystone Intelligence Engine — dynamically spawns subagents with per-task objectives, tools, and output formats rather than drawing from predefined types. This pattern, validated across CrewAI, Google ADK, and Microsoft AutoGen, consistently outperforms fixed typing. The recommended architecture for Keystone is a **hybrid template-inheritance model** where the Specification Engine maintains a registry of base agent templates (replacing rigid enums) and dynamically customizes or composes new configurations per engagement, constrained by structural validation and a "tighten-only" governance invariant.

The evidence is substantial. Microsoft's Azure SRE team started with 50+ specialized agents and collapsed to a handful of generalists after handoffs failed beyond 4 hops. Google DeepMind found coordination gains plateau beyond **4 agents** and error amplification reaches **17.2x** in poorly structured multi-agent networks. Meanwhile, Anthropic's dynamically-configured research system outperformed single-agent Claude Opus 4 by **90.2%** on research evaluations. The lesson: rigid typing creates brittleness, but unconstrained dynamic generation creates chaos. The sweet spot is parameterized templates with orchestrator-driven customization.

---

## How Anthropic actually configures subagents in their research system

Anthropic published their multi-agent research architecture in June 2025, and it directly answers the core question: **subagents are dynamically generated configurations, not predefined types**. The LeadResearcher (Claude Opus 4) analyzes each query, uses extended thinking to plan its approach, and generates custom subagent specifications on the fly. Each subagent receives four elements: a specific objective, an output format, guidance on tools and sources to use, and clear task boundaries.

The system embeds **complexity-scaled spawning rules** directly in the orchestrator's prompt: simple fact-finding gets 1 agent with 3–10 tool calls, direct comparisons get 2–4 subagents with 10–15 calls each, and complex research gets 10+ subagents (maximum 20) with clearly divided responsibilities. The default is 3 subagents. Critically, the lead agent doesn't select from an enum of agent types — it generates task descriptions that effectively define each subagent's role, behavioral constraints, and success criteria in natural language. The orchestrator prompt teaches delegation through examples and principles, not through type selection.

Token usage alone explains **80% of performance variance** in their evaluations. Multi-agent configurations use approximately **15× more tokens** than single chat interactions. This means the Specification Engine's spawning decisions directly determine both quality and cost — making dynamic scaling rules essential, not optional.

Claude Code's subagent system reveals Anthropic's other approach: a **hybrid of templates and dynamic generation**. Three built-in subagent types exist (Explore, Plan, General-purpose), each with preset model tiers and tool access. But custom agents can be defined as markdown files in `.claude/agents/` directories with YAML frontmatter specifying name, description, tools, model, and system prompt. The parent agent can also spawn the general-purpose subagent with any arbitrary prompt. The priority order is: managed settings > CLI flags > project-level agents > user-level agents > plugin agents. This layered approach allows organizations to define standard agent templates while preserving the ability to generate task-specific configurations at runtime.

---

## The "agent as prompt + tools" pattern has become the industry standard

Across every major framework, the dominant agent definition pattern has converged on a single abstraction: **Agent = (system_prompt, tools[], output_schema, constraints)**. This is not a code-level class hierarchy — it's a declarative configuration that can be generated, serialized, and composed at runtime.

The specific implementations vary by framework but share this core:

- **OpenAI Agents SDK**: `Agent(instructions, tools, handoffs)`
- **Google ADK**: `Agent(name, model, instruction, tools, sub_agents)` with YAML alternative
- **CrewAI**: YAML config with `role`, `goal`, `backstory` + programmatic `tools=[]`
- **PydanticAI**: `Agent(model, instructions, tools)` with typed dependency injection
- **Claude Code**: Markdown files with YAML frontmatter defining name, description, tools, model, system prompt

The most rigorous expression of this pattern comes from **Snap Inc.'s Agent Format (.agf.yaml)**, open-sourced in 2026. Grounded in POMDP theory, it declares agents through five sections: metadata (identity/versioning), interface (input/output contract), action_space (tools, MCP servers, sub-agents), execution_policy (strategy, model, instructions), and constraints (budgets, governance). Every field must pass three tests: settable at authoring time, portable across runtimes, and declarative (WHAT not HOW).

The critical insight from GitHub Copilot's architecture reinforces this: **tool restriction is a hard constraint, while prompt instruction is soft guidance**. An instruction saying "don't edit files" is guidance the model might ignore under pressure. An agent that only has read-only tools literally cannot edit files. This means the tools[] assignment in an AgentDefinition isn't just configuration — it's the primary enforcement mechanism for agent behavior boundaries. For Keystone, this means the tool subset assigned to each research agent should be the primary mechanism for constraining behavior, not the system prompt alone.

---

## What the research literature reveals about fixed vs. dynamic configuration

The empirical evidence strongly favors dynamic configuration for research tasks, but with important caveats about coordination costs and failure rates.

**Dynamic configuration wins for parallel, read-heavy tasks.** The DyLAN paper (ICLR 2024) showed that dynamically selecting agent teams improved accuracy by **up to 25%** compared to fixed teams on MMLU benchmarks. The X-MAS system demonstrated **8.4% accuracy improvement on MATH and 47% boost on AIME** through role-wise LLM assignment. The MetaAgent system, which automatically designs multi-agent systems via finite state machines, achieved **97% of the performance of the best human-designed systems** on ML tasks and passed 50% more checkpoints on software development tasks.

**Fixed configuration wins for sequential, write-heavy tasks.** Google DeepMind's scaling study (December 2025) tested 180 configurations and found multi-agent coordination produced **+81% improvement on parallelizable tasks** but **up to 70% degradation on sequential tasks**. The saturation threshold was clear: coordination gains plateau beyond 4 agents. They also identified a tool-coordination tradeoff where tasks requiring many tools perform worse with multi-agent overhead.

**The most instructive production case study is Microsoft Azure's SRE Agent.** The team started with 100+ tools and 50+ specialized sub-agents with focused personas. They ended with **5 core tools and a handful of generalists**. The agent became more reliable, not less. Their key finding: problems requiring more than 4 handoffs almost always failed. Discovery problems, system prompt fragility, infinite loops, and "tunnel vision" plagued the specialized approach. They concluded: "We hadn't built an agent — we'd built a workflow with an LLM stapled on." Domain knowledge was moved from rigid system prompts into files agents could read on demand, inspired by Anthropic's "agent skills" pattern.

The MAST framework (ICLR 2025) analyzed **1,642 execution traces across 7 open-source frameworks** and found failure rates ranging from **41% to 86.7%**. "Disobeying role specification" — where agents fail to adhere to their defined responsibilities — was identified as a primary failure mode. But the study also found that coordination breakdowns accounted for **36.9% of all failures**, the largest category. The core tension: too-rigid roles create brittleness when tasks don't fit neatly; too-loose roles create coordination chaos. The solution is not choosing one extreme but engineering the boundary between them.

---

## A decision framework for template vs. custom agent configuration

The decision of when to use a predefined template versus generating a custom agent configuration should be driven by a classification step in the Specification Engine. Based on the research, five criteria determine the optimal approach:

- **Task familiarity**: If the engagement type (e.g., M&A due diligence, market sizing) has been handled before with known agent configurations that performed well, use the template. If it's a novel engagement type or combines domains in unusual ways, generate a custom configuration.
- **Input structure predictability**: Well-structured inputs with clear analytical frameworks (financial modeling, competitive benchmarking) favor templates. Ambiguous, exploratory queries (emerging market assessment, scenario planning for unprecedented events) favor dynamic configuration.
- **Tool requirements**: If the task requires the standard tool set for a known agent type, use the template. If it requires a novel combination of tools or tools not typically assigned to any existing type, generate a custom configuration.
- **Evaluation availability**: If pre-calibrated evaluation rubrics exist for the agent type, templates are safer. If no evaluation baseline exists, dynamic configuration with LLM-as-judge evaluation and structural validation is required.
- **Reliability requirements**: For high-stakes deliverables (board presentations, regulatory filings), prefer well-tested templates. For exploratory research where breadth matters more than precision, dynamic configuration is acceptable.

The practical implementation is a **two-tier classification**: the Specification Engine first attempts to match the task against the template registry using semantic similarity on the task description. If a template matches above a confidence threshold (e.g., 0.85), it uses the template with variable interpolation for task-specific details. Below that threshold, it generates a custom AgentDefinition using the orchestrator LLM, constrained by structural validation and the tighten-only invariant.

---

## Evaluating dynamically configured agents without pre-calibrated benchmarks

This is the hardest problem in the space, and no framework has fully solved it. But three complementary approaches emerge from the research.

**Structural validation catches configuration errors.** Every dynamically generated AgentDefinition should pass schema validation against a JSON schema (does it have required fields?), tool-access validation (are the assigned tools actually available and appropriate?), output-format validation (is the output schema well-formed?), and constraint validation (do constraints tighten rather than loosen relative to the parent?). Snap's Agent Format enforces this at parse-time, and it catches a surprisingly large fraction of configuration errors before any tokens are spent.

**LLM-as-judge evaluation handles semantic quality.** Anthropic's own evaluation guidance recommends grading dynamically generated outputs across isolated dimensions: factual accuracy, completeness, source quality, reasoning coherence, and tool efficiency. Each dimension gets its own LLM-as-judge prompt rather than a single aggregate grader, because isolated dimension scoring is more consistent with human judgments. The key innovation for dynamic agents is that the evaluation rubric itself can be generated from the agent's task description — if the Specification Engine creates an agent with the objective "analyze supplier concentration risk in the target's top 10 accounts," the evaluation rubric can be generated to assess whether the output actually addresses supplier concentration, covers the top accounts, quantifies risk, and cites sources.

**The generator-critic pattern provides runtime quality gates.** Google ADK implements this as a LoopAgent where one agent generates output and another validates against criteria, iterating until quality thresholds are met. For Keystone, this means each dynamically configured research agent's output should pass through a review step — either a dedicated critic agent or the orchestrator itself — before being incorporated into the final deliverable. The critic doesn't need to know the agent's type; it evaluates the output against the task objective and output schema.

A practical bootstrapping approach from Google Cloud: start with human evaluation on early outputs, convert feedback into binary Pass/Fail scores across key dimensions, use LLM-as-judge to automate scoring, and continuously build a golden dataset by curating real-world successes and failures. Over time, frequently-spawned dynamic configurations that perform well get promoted to the template registry.

---

## The recommended architecture: template registry with orchestrator-driven customization

Based on the full body of evidence, the recommended architecture for Keystone replaces the fixed Python enums with a **template registry pattern** that enables both template reuse and dynamic generation. Here is the specific design:

**Replace enums with a template registry.** Instead of `ResearchAgentType(Enum)` with 5 fixed values, maintain a registry of `AgentTemplate` objects — each containing a base system_prompt, default tool set, output schema, evaluation rubric, and constraint set. The current 5 research agent types and 5 deliberation analyst types become the **seed templates** in this registry. New templates can be added without code changes, validated against a schema, and versioned.

**The Specification Engine becomes a two-path dispatcher.** Given a task decomposition, the Specification Engine (running on Opus) follows this logic: (1) Analyze the subtask requirements — objective, domain, tools needed, output format. (2) Search the template registry for matching templates using semantic similarity on the task description against template descriptions. (3) If a strong match exists (similarity > threshold), instantiate the template with task-specific variable interpolation — customize the system prompt with engagement-specific context, adjust the tool set if needed, and specialize the output schema. (4) If no strong match exists, generate a custom AgentDefinition from scratch, constrained by structural validation, tool whitelisting, and the tighten-only invariant. (5) In both cases, attach an evaluation rubric — either the template's pre-calibrated rubric or a generated one.

**Use the "tighten-only" constraint invariant.** Borrowed from Snap's Agent Format, this principle states that when the orchestrator delegates to sub-agents, constraints can only become more restrictive, never less. If the orchestrator has access to 20 tools, a subagent can have access to at most 20 (and typically fewer). If the orchestrator has a token budget of 50,000, subagents inherit that ceiling. This prevents privilege escalation in dynamically generated agent hierarchies and provides a hard safety boundary regardless of how creative the orchestrator gets with agent generation.

**Implement progressive skill loading rather than monolithic system prompts.** Following Google ADK's three-tier pattern and Microsoft Azure's hard-won lesson about on-demand knowledge loading: don't pack all domain expertise into the system prompt. Instead, maintain a skill/knowledge library that agents can load on demand. For Keystone, this means M&A due diligence knowledge, market sizing methodologies, and industry-specific frameworks live as loadable skill files, not as hardcoded system prompt components for each agent type. A "quantitative research agent" template points to relevant skills; a dynamically generated "semiconductor supply chain analyst" agent points to different skills. The agent definition references skills by ID; the runtime loads them into context as needed.

**Template promotion loop closes the feedback cycle.** When a dynamically generated agent configuration performs well (measured by evaluation scores and human feedback), it should be promoted to the template registry as a new named template. This creates a flywheel: novel engagement types start with dynamic generation, successful configurations get crystallized into templates, and the template registry grows organically. Over time, the proportion of tasks handled by templates increases while the system retains the ability to handle truly novel requests.

---

## What this means concretely for the Keystone Intelligence Engine

The current architecture — 5 fixed `ResearchAgentType` enum values and 5 fixed `DeliberationAnalystType` enum values dispatched by the Specification Engine — should evolve in three phases.

**Phase 1: Template parameterization.** Keep the existing 10 agent types but convert them from enum-dispatched fixed configurations to parameterized templates stored as YAML or Pydantic models. The existing `AgentDefinition` model (with name, description, role, tools, system_prompt) already has the right fields — it just needs to become the unit of configuration rather than a downstream artifact of enum selection. The Specification Engine learns to interpolate task-specific context into these templates: the engagement type, industry, specific analytical questions, and relevant domain knowledge.

**Phase 2: Registry + dynamic generation.** Introduce a template registry that the Specification Engine queries. Add the ability for the Specification Engine (Opus) to generate custom `AgentDefinition` objects when no template matches well. Implement structural validation, tool whitelisting, and the tighten-only invariant. Add LLM-as-judge evaluation for dynamically generated agents. This is where the real flexibility gains come — an M&A due diligence engagement can spawn a "regulatory risk analyst" that didn't exist in the original enum, configured with the right tools (SEC filing search, regulatory database access) and evaluation criteria.

**Phase 3: Promotion loop + skill loading.** Implement the template promotion flywheel and progressive skill loading. Successful dynamic configurations get promoted to named templates. Domain knowledge gets externalized into loadable skill files. The system becomes self-improving: each novel engagement type it handles successfully expands its template library for future engagements.

The key constraint to respect throughout: **Anthropic's research system shows that 80% of performance variance comes from token usage, not architecture**. The most important thing the Specification Engine does is calibrate research effort to task complexity — ensuring simple subtasks get 1 lightweight agent while complex multi-source research gets 5–10 specialized agents with adequate token budgets. Getting this scaling right matters more than any architectural pattern for agent definition.

## Conclusion

The industry has converged on a clear answer: **agents should be defined as declarative configurations (prompt + tools + output schema + constraints), organized in extensible registries, and dynamically customized or generated by orchestrator LLMs**. Fixed enums are an anti-pattern that every production system has moved away from. The Keystone Intelligence Engine's existing `AgentDefinition` model already has the right shape — the gap is that the Specification Engine treats it as a downstream artifact of enum selection rather than as the primary unit of configuration.

Three insights are novel or underappreciated. First, **tool assignment is a harder constraint than system prompt instructions** — the tools[] field in an AgentDefinition is the primary behavioral enforcement mechanism, not the system prompt. Second, **the tighten-only invariant** from Snap's Agent Format provides a simple, enforceable governance rule for dynamic agent hierarchies that prevents the quality degradation teams fear from dynamic generation. Third, **the template promotion loop** — where successful dynamic configurations get crystallized into named templates — resolves the fixed-vs-dynamic tradeoff entirely by making it a spectrum rather than a binary choice, with the system naturally migrating toward the optimal balance over time.