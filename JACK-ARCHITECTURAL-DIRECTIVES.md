# Jack's Architectural Directives
*Captured from Cowork planning sessions, April 5-6 2026*
*These decisions and design directions were given by Jack Riddle during interactive planning and are NOT captured in CAPSTONE-PLAN-v2.md or any other existing project file. Treat these as authoritative.*

---

## 1. The Rigidity Problem

The current plan was designed around a prototypical market research engagement. It hardcodes:

- **5 fixed research agent types** (quantitative, qualitative, contrarian, historical analogy, internal document)
- **5 fixed deliberation analyst types** (ACH, quantitative, adversarial, historical analogy, scenario planning)
- **Fixed rubric weights** that only flex between two profiles (estimative vs. current intelligence)

**Jack's directive:** These fixed types work for broad market research but fail for specialized tasks like "deep-dive a specific public company for an M&A pitch" or "analyze optimal retail expansion locations for an auto shop chain." The system must dynamically configure agent roles, deliberation approaches, and evaluation criteria based on the engagement.

**Design intent:** Predefined types should be *templates* or *defaults*, not constraints. When they fit, use them. When they don't, the Specification Engine generates custom configurations on the fly. Think of it like McKinsey casing: you don't want memorized frameworks, you want someone who can take ambiguity, structure it, and prioritize.

---

## 2. MECE Issue Tree Decomposition

**Jack's directive:** Add a "casing phase" to the Specification Engine before task decomposition. The flow:

1. System receives engagement description + specific workstream
2. Multiple agents independently construct MECE issue trees for the problem
3. Deliberation selects or synthesizes the best decomposition
4. Task generation follows the issue tree branches, not predefined categories
5. Human reviews the issue tree before research begins

**Why:** This is how McKinsey consultants structure novel problems. The issue tree is the system's primary tool for handling ambiguity. It forces the system to think about what matters before doing research, rather than applying a generic template.

**The issue tree should be a living document** that updates as research reveals new branches or invalidates existing ones.

---

## 3. Iterative Multi-Round Research

**Jack's directive:** The system cannot be single-pass. Research findings must be able to spawn new research threads. The plan has concepts for this (scout/strike model, insufficient_evidence triggers) but no mechanical specification.

**What's missing:**
- Who decides when to spawn new research? (The LeadResearcher? A separate evaluator?)
- How many rounds maximum?
- What's the stopping condition?
- How does the system handle mid-research scope expansion (e.g., discovering a company is being acquired while researching its competitive position)?
- How do findings from round N inform the research plan for round N+1?

**This is the single biggest architectural gap in the current plan.**

---

## 4. Engagement Scope

**Jack's directive:** Keystone Group handles the full range of consulting engagements:
- **Operations** (process optimization, supply chain, logistics)
- **Growth** (market entry, expansion, product strategy)
- **M&A** (target screening, due diligence, integration planning)
- **Restructuring / Turnaround** (cost reduction, organizational redesign, crisis management)

Across diverse industries. The system must handle ANY consulting engagement type without relying on predefined skill files for every possible scenario.

**Test case:** "An auto shop chain hires Keystone to determine optimal expansion locations. This involves market sizing (auto body repair demand by geography), competitor analysis, location optimization (balancing demand, competition, existing store/warehouse locations, shipping costs), and hub-and-spoke logistics. You're assigned the research workstream: analyze the competitive landscape and market demand for auto body repair across the top 50 US metropolitan areas."

The system should handle this without an "auto body repair" skill file. The Specification Engine's issue tree decomposition + dynamic agent configuration should be sufficient.

---

## 5. Build Philosophy

**Jack's directive:** Build the architecture *correctly* (right interfaces, right abstractions, right data flow) but stage feature depth. This is NOT about building every feature at full depth in 6 weeks. It IS about ensuring the architectural foundations are right so features can be deepened later without rework.

**Concretely:** The pipeline should have all layers wired up with correct handoff contracts, but individual layers can start simple and get more sophisticated over time. A Specification Engine that produces a basic issue tree is fine for MVP as long as the interface supports a sophisticated one later.

**Not building a "mini MVP" that shortcuts the architecture.** Building the real architecture at reduced feature depth.

---

## 6. The "FITFO" Standard

**Jack's direct quote (paraphrased):** "The system should be as competent as a senior McKinsey consultant. When it encounters something it's never seen before, it should be able to FITFO (figure it the f*** out) without predefined skills or templates."

This means:
- The Specification Engine is the highest-leverage component
- Dynamic agent configuration is essential (not optional)
- The issue tree is the primary analytical tool
- The Observation Library feeds forward (past engagements inform future ones)
- The system should degrade gracefully on novel problems, not fail

---

## 7. Human-in-the-Loop Gates

**Confirmed gates:**
1. **After the Specification Engine produces the issue tree / task list** — human reviews and approves or modifies before research begins
2. **After Deliberation produces the confidence map** — human reviews synthesis before content generation

These are non-negotiable. The system runs autonomously between gates.

---

## 8. Karpathy's LLM Knowledge Bases

**Context:** Andrej Karpathy described a pattern of using LLMs to compile raw data into structured markdown wikis with auto-maintained index files, instead of traditional RAG with embeddings. Jack is attracted to this because: (1) it could reduce/remove the embedding dependency, and (2) it makes findings easy to track, visualize, and maintain continuity.

**Analysis from Cowork session:** The Karpathy pattern and embeddings solve different problems:
- Embeddings: "Find relevant documents I haven't processed yet" (discovery)
- LLM Knowledge Bases: "Organize and navigate knowledge I've already processed" (accumulation)

**High-value applications in Keystone:**
1. **Observation Library** — compiled markdown wikis organized by industry/engagement-type/pattern, with LLM-maintained indexes. Better fit than vector search for accumulated learnings.
2. **Within-engagement knowledge** — tracking what agents have already found across research rounds. The claim-level IR already does a version of this.
3. **Cross-engagement knowledge base** — industry-specific knowledge wikis built up over many engagements. New concept not in the current plan.

**Where it does NOT replace embeddings:** Initial source discovery during active research (finding SEC filings, news articles, etc. that haven't been processed yet).

**Architectural implication:** Component #3 (retrieval) may be simpler than planned if compiled wikis handle accumulated knowledge and embeddings are only needed for initial source discovery. Deep Research Report #4 is tasked with evaluating this tradeoff.

---

## 9. Component #3 Over-Engineering Concern

**Jack's directive:** Component #3 is flagged as over-engineered not because of time pressure, but because the best technical approach is uncertain. New embedding models have come out since the original research (including multimodal Gemini embeddings). The Karpathy knowledge base pattern adds another alternative. Jack wants to make a well-informed decision before building, not commit to an architecture that may be wrong.

**Action:** Deep Research Report #4 evaluates all options. Component #3 build should wait for that report's findings.

---

## 10. Confirmed Settled Decisions

Jack confirmed all 11 settled decisions listed in CURRENT-STATE.md. Additionally:

- **Claude Max deployment** confirmed as the target platform
- **Cost target:** $12-$100 per engagement if not on Claude Max
- **Model mixing:** Opus 4.6 for L0/L4 (judgment), Sonnet 4.6 for L1 (throughput), Haiku 4.5 for extraction
- **PydanticAI** confirmed as agent framework (with Temporal deferred to Phase 2)
- **MCP** confirmed as tool integration standard
- **Observation Library** (renamed from Rejection Library) captures both successes and failures with 3-tier categorization

---

## 11. Configurable Pipeline Depth (No Gold-Plated Bullets)

**Jack's directive:** The system must NOT default to the full pipeline for every query. A simple factual question shouldn't spin up MECE decomposition, 5 research agents, and 5 rounds of iterative research. The pipeline depth should be configurable, both automatically (via the engagement classifier) and manually (via a user-facing control panel).

**Pipeline profiles:**
- **Light:** No issue tree, 1-2 agents, 1 round, Layers 1-2 eval only. For scoped factual queries.
- **Standard:** Simplified issue tree (single agent), 3 agents, 2-3 rounds, Layers 1-3 eval. For typical research.
- **Deep:** Full MECE decomposition (multi-agent), 5+ agents, up to 5 rounds, full eval stack. For complex strategic engagements.

The engagement classifier in Step 1 of the Specification Engine recommends a profile. The user can override up or down via a control panel. This resolves the 15x token multiplier concern: 15x is the Deep profile ceiling, not the default.

**Design principle:** Maximum flexibility for the operator. The system should be powerful enough for the hardest engagements but efficient enough for simple ones. Users select which layers they want. Think of it as a mixing console, not a fixed pipeline.

---

## 12. Casing Principles Over Example Libraries

**Jack's directive:** The Specification Engine's issue tree capability should be taught via PRINCIPLES of structured problem decomposition, not by copying example trees. This mirrors how McKinsey trains consultants: you learn the methodology (MECE, hypothesis-driven, prioritize by impact/feasibility), not memorize specific frameworks.

**Implementation approach:** Jack has casing books that will be analyzed by an Opus 1M context agent. The output: a skill file that teaches the agent HOW to decompose problems, not WHAT decompositions to produce. A few example trees can appear as demonstrations of the principles in action (like a professor using case studies), but the agent's skill comes from understanding the methodology.

This means the "exemplar library bootstrap" flagged in the Batch 2 analysis is NOT a months-long curation effort. It's a single Opus session producing a skill file from existing casing materials.

---

## 13. Phase 1 Depth Staging

**Jack's directive (confirmed from Batch 2 analysis review):** The Batch 2 analysis proposed a 10-step Specification Engine (XL scope, 2-3 weeks) with features like TiCoder divergence detection, VOI-inspired scoring, CBR Observation Library query, and 8-10 evaluation profiles. Jack's position: build the architecture correctly (right interfaces, right data flow) but defer sophistications that can be added later without forcing rework.

**Ship in Phase 1:**
- Issue tree decomposition (multi-agent with heterogeneous lenses, shallow start)
- MECE verification step
- Engagement classifier (routes to pipeline profile)
- Human review gate (database state machine)
- Template registry for agent configs (seed templates, not just enums)
- Iterative research loop (3-round default, 5 max, three-criterion stopping)
- Claim-level selection for deliberation
- Component #3 split (#3a discovery + #3b accumulation)
- Error recovery Layers 1-2
- Geometric mean rubric aggregation
- Tier 1/Tier 2 rubric split

**Defer to Phase 2 (add later without rework):**
- TiCoder divergence detection in intent clarification
- VOI-inspired priority scoring (use simpler heuristic scoring in Phase 1)
- CBR Observation Library query at Spec Engine entry (Observation Library doesn't exist in Phase 1)
- 8-10 engagement-type evaluation profiles (start with 3-4, expand)
- Sprint contract negotiation between Evaluator and Generator
- Cross-engagement knowledge base / wiki promotion rules
- Flexon-based problem archetype tagging
- Dimension-specific verification strategies (programmatic QR, position-switching AD)

**The test:** Can this feature be added later by extending an interface or adding a module, WITHOUT changing the data flow or rewriting existing components? If yes, defer. If no, build now.

---

## 14. Quality Standard

Jack emphasized repeatedly: this is a *real product* for a *real consulting firm*, not a class project. The research and architecture decisions must be at the level of quality that would satisfy a senior consultant at McKinsey, Bain, or BCG. Speed is secondary to getting the architecture right.

**Jack's exact framing:** "I'd rather take the time to get this right than rush and build the wrong thing. This is the most critical stage of the project."
