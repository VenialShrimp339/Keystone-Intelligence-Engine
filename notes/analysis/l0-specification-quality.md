# L0 Specification Engine Quality Analysis

**Date:** 2026-04-21
**First real pipeline run:** 2026-04-22
**Question tested:** "How should a multi-agent LLM pipeline be architected and optimized — across prompt design, context engineering, agent coordination, evaluation, and agent-to-agent handoffs — to reliably produce high-quality company research and analysis for a boutique consulting firm, matching the depth and rigor of a team of McKinsey analysts spending a week on the same question?"
**Benchmark:** 16 manual research prompts in RESEARCH-PROMPTS-FINAL.md (categories A1-D3)

---

## Executive Summary

The first L0 run produced structurally valid output (16-leaf tree, MECE validation passed, classification completed) but the substance is systematically wrong for this question. The hardcoded consulting lenses decomposed a technical architecture question through financial and market lenses that have no coherent application to "how do I design a software system." The engagement type taxonomy forced an AI system design question into a consulting business-analysis category. The task category enum has no vocabulary for "prior art survey," "evaluation design," or "systems architecture." The intent clarifier said the question was clear when it should have flagged at least five ambiguities. The result is that L0 would have generated 16 research tasks about financial viability and market positioning of an agentic research system — when the question actually needed tasks about evaluation methodology, deliberation architecture, prompt design, and existing open-source systems.

This analysis documents each failure precisely, with code references and prompt text, and proposes specific fixes.

---

## 1. Lens Appropriateness: The Financial/Operational/Market Mismatch

### What the code does

`decomposer.py:56` hardcodes:

```python
_LENSES = ["financial", "operational", "market"]
```

These map to three prompt files loaded in `Decomposer._run_lens()` (line 160). Each prompt assigns a role and focus areas:

- **Financial lens** (`decompose_financial_lens.md`): "You are a financial analyst... Revenue model and growth drivers, Cost structure and margin dynamics, Capital requirements, Unit economics, Financial risk factors, Comparative financial positioning vs peers, Valuation implications"
- **Operational lens** (`decompose_operational_lens.md`): "You are an operations strategy consultant... Technology capabilities, Manufacturing/delivery capacity, Supply chain dependencies, Organizational structure, Process efficiency, Regulatory compliance"
- **Market lens** (`decompose_market_lens.md`): "You are a market strategy consultant... Market size and segmentation, Competitive landscape, Customer needs and switching costs, Porter's Five Forces, Market entry barriers, Macro trends"

### The mismatch in detail

The test question is: **how to architect and optimize a multi-agent LLM pipeline**. This is a software systems design and technical evaluation question. It has no natural financial, market, or competitive-positioning structure.

**Financial lens applied to this question:** The model would interpret "financial" as: What does it cost to build this system? What's the ROI of building it vs. buying it? What's the unit economics per research engagement? What's the LLM API cost per query? This produces branches like "cost of LLM inference," "build vs buy for vector databases," and "API cost per engagement" — none of which appear in the 16 benchmark research streams. The benchmark has zero interest in ROI or build-vs-buy economics; it is entirely focused on *how* to build the system well.

**Operational lens applied to this question:** The model would interpret "operational" through phrases like "Technology capabilities and maturity," "Organizational structure and talent," "Process efficiency and scalability," "Partnership and ecosystem dependencies." This is closer — it could produce branches on system architecture, agent coordination, or technical maturity. But the operational prompt's framing ("manufacturing/delivery capacity," "supply chain") is anchored in a business-entity context, not a software-design context. It would likely produce branches on "deployment infrastructure" and "team composition" rather than "evaluation methodology" and "prompt design patterns."

**Market lens applied to this question:** The model would produce competitive landscape analysis of existing deep research systems (GPT-Researcher, STORM, 199-Bio) — which actually overlaps with research streams A1 and A5 in the benchmark. But it would frame this through Porter's Five Forces ("market entry barriers," "substitutes and alternatives") rather than the architectural learning framing of A1 ("what's been tried and failed, where the genuine gaps are"). The "customer needs and switching costs" focus area is simply not applicable.

**What MECE checking validated:** The MECE validator checked that the three lens outputs, when synthesized, had non-overlapping and collectively exhaustive branches. Since all three lenses were applied to the same question, the validator confirmed that the financial/operational/market breakdown covers the full "analytical space" — but the analytical space it validated is the wrong space entirely. MECE correctness does not equal topical relevance.

### What lenses SHOULD have been selected

For a technical architecture and evaluation question about building an agentic research pipeline, the appropriate lenses are:

| Lens | Coverage | Benchmark Streams |
|------|----------|-------------------|
| **Technical architecture** | Agent coordination patterns, orchestration frameworks, state management, component interfaces, failure modes | A4 (orchestration), C4 (retrieval), C1 (spec-driven) |
| **Existing systems landscape** | What's already built, what works, what fails, what can be composed vs built | A1 (multi-agent systems), A5 (deep research tooling) |
| **Quality and evaluation methodology** | Evaluation frameworks, rubric design, LLM-as-judge failure modes, anti-gaming, self-eval problem | A2 (evaluation), B4 (failure modes), B2 (decision-useful) |
| **Research methodology** | How to conduct research well, deliberation patterns, synthesis quality, structured analytic techniques | C2 (deliberation), B1 (consulting standards), B3 (taste/judgment) |
| **Self-improvement and learning** | Rejection libraries, prompt optimization, runtime improvement loops, trajectory storage | A3 (self-improvement) |

This set covers all 16 benchmark streams. The financial lens contributes nothing to any benchmark stream. The market lens contributes partial coverage of A1 and A5 but frames it incorrectly.

### The fix

The lens selection must be dynamic. The `Decomposer` should:

1. Add a pre-decomposition step: a lens selection LLM call that reads the question and engagement type and returns 2-4 appropriate lens names with descriptions.
2. The lens menu should include consulting-specific lenses (financial, market, operational) AND domain-appropriate alternatives: technical architecture, evaluation methodology, prior art landscape, organizational/process, regulatory, scientific/research, economic/behavioral.
3. The selected lenses should be passed to a generic lens prompt template that inserts the lens name, description, and focus areas. The three fixed `.md` files become one parameterized template.
4. `_LENSES` at `decomposer.py:56` becomes a runtime product of the lens selector, not a module-level constant.

The lens selector prompt should take the question text, the engagement type, and a menu of 10-15 possible lenses, and return a JSON array of 2-4 lens objects with `{"name": str, "description": str, "focus_areas": [str]}`. The synthesis prompt at `decompose_synthesis.md` already handles merging N lens trees — it references `financial_tree`, `operational_tree`, and `market_tree` by name, which would need to change to a generic numbered or named structure.

---

## 2. EngagementType Fitness: Forcing a Square Peg

### The five types

From `research.py:23`:

```python
class EngagementType(StrEnum):
    SIZING = "sizing"
    DIAGNOSTIC = "diagnostic"
    EVALUATIVE = "evaluative"
    EXPLORATORY = "exploratory"
    STRATEGIC = "strategic"
```

The classifier prompt (`classification.md`) defines these with consulting-business examples:
- sizing: "Estimate TAM for autonomous vehicle sensors"
- diagnostic: "What caused the Q3 revenue decline"
- evaluative: "Evaluate the competitive position of Company X"
- exploratory: "What's happening in the generative AI infrastructure market"
- strategic: "Should we acquire Company Y"

L0 classified the test question as `strategic / deep`.

### Assessment of fit

The test question — "how should a multi-agent LLM pipeline be architected" — does not cleanly fit any of the five types:

- **SIZING:** No. The question is not about quantifying anything.
- **DIAGNOSTIC:** No. There is no observed outcome to explain.
- **EVALUATIVE:** Partial. The question does require evaluating existing systems (A1, A2, A4, A5). But "evaluative" implies assessing a specific entity (Company X, Strategy Y). This question is generative — it's asking how to build something new.
- **EXPLORATORY:** Partial. The question is exploring a domain (agentic research systems). But "exploratory" in the prompt is defined as "mapping a landscape without a specific hypothesis," which undersells the design-decision focus of this question.
- **STRATEGIC:** The closest, because it involves "high-stakes decision with multiple interacting variables." But the classification prompt's example ("Should we acquire Company Y") is a binary decision, not a design question. The pipeline profile consequence of STRATEGIC is `DEEP` (5+ agents, 5 rounds, full eval stack), which is appropriate for the complexity — but for the wrong reasons.

### Missing engagement types

For a boutique consulting firm that might receive research questions on a wide range of topics, the enum needs expansion. Missing types include:

| Missing Type | Description | Example |
|---|---|---|
| **DESIGN** | How should X be built, structured, or organized | "How should we architect this system" |
| **SYNTHESIS** | Aggregate and integrate findings from multiple prior sources | "Synthesize the research on AI safety approaches" |
| **CAPABILITY_ASSESSMENT** | What can we do with X, and how well | "What is this team capable of building in 6 months" |
| **TECHNICAL_EVALUATION** | Assess the technical merits of a specific technology or approach | "Evaluate whether GraphRAG is appropriate for our use case" |
| **COMPARATIVE** | Head-to-head comparison of approaches, frameworks, or vendors | "Compare LangGraph vs CrewAI for our pipeline" |

The consequence of misclassification is not just semantic. The `_DEFAULT_PROFILES` in `engagement_classifier.py:27` maps engagement types to pipeline profiles, and the type drives evaluation weight profiles and framework selection. A STRATEGIC classification causes the pipeline to apply a strategic engagement rubric to what is fundamentally a technical design question — a rubric optimized for "scenario analysis, risk assessment, and decision frameworks" rather than for "technical correctness, implementation feasibility, and prior art coverage."

### The fix

Two options:

**Option A (expand the enum):** Add DESIGN, SYNTHESIS, TECHNICAL_EVALUATION, COMPARATIVE to `EngagementType`. Each needs a `_DEFAULT_PROFILES` entry, a description and example in `classification.md`, and default evaluation/framework mappings. This is straightforward but the enum will keep growing.

**Option B (two-level taxonomy):** Add a `domain` field alongside `engagement_type`. The domain would be `consulting`, `technical`, `scientific`, `policy`, etc. The engagement_type within the `technical` domain could be `design`, `evaluation`, `survey`. This is more structured but requires more schema changes.

The classification prompt would need corresponding updates. Currently `classification.md` instructs the LLM to pick "exactly ONE of these engagement types" from the five — a constraint that forces incorrect mappings.

---

## 3. TaskCategory Coverage: Six Buckets for Sixteen Topics

### The six categories

From `tasks.py:16`:

```python
class TaskCategory(StrEnum):
    MARKET_SIZING = "market_sizing"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    FINANCIAL_ANALYSIS = "financial_analysis"
    TECHNOLOGY_ASSESSMENT = "technology_assessment"
    REGULATORY = "regulatory"
    STRATEGIC_POSITIONING = "strategic_positioning"
```

### Mapping the 16 benchmark topics to these categories

| Benchmark Stream | Best-Fit Category | Quality of Fit |
|---|---|---|
| A1: Multi-Agent Research Systems | TECHNOLOGY_ASSESSMENT | Partial — A1 is really "prior art landscape" not "technology readiness level assessment" |
| A2: Evaluation & Verification Frameworks | TECHNOLOGY_ASSESSMENT | Partial — evaluation methodology is distinct from technology assessment |
| A3: Self-Improvement and Learning Loops | TECHNOLOGY_ASSESSMENT | Poor — this is about system design patterns, not a technology being assessed |
| A4: Orchestration Frameworks & Coordination | TECHNOLOGY_ASSESSMENT | Poor — architecture design, not technology assessment |
| A5: Deep Research Tooling & Capabilities | TECHNOLOGY_ASSESSMENT | Partial — tooling survey |
| B1: What Senior Consulting Partners Value | STRATEGIC_POSITIONING | Partial — quality standards ≠ strategic positioning |
| B2: Decision-Useful vs Comprehensive Research | STRATEGIC_POSITIONING | Poor — this is about research methodology design |
| B3: Taste, Judgment, Quality of Thought | STRATEGIC_POSITIONING | Poor — evaluation rubric design |
| B4: AI-Generated Research Quality Failures | TECHNOLOGY_ASSESSMENT | Partial — failure mode analysis |
| C1: Specification-Driven Development | TECHNOLOGY_ASSESSMENT | Poor — this is about software development methodology |
| C2: Deliberation & Multi-Perspective Synthesis | TECHNOLOGY_ASSESSMENT | Poor — agent coordination patterns |
| C3: Report/Deliverable Generation | TECHNOLOGY_ASSESSMENT | Partial — tooling |
| C4: Data Retrieval Architecture | TECHNOLOGY_ASSESSMENT | Partial — infrastructure |
| D1: Best AI Agent Systems by Individuals/Teams | COMPETITIVE_LANDSCAPE | Reasonable fit |
| D2: Academic Papers on Automated Analysis | TECHNOLOGY_ASSESSMENT | Partial |
| D3: 10x Ideas — What Would Make Keystone Extraordinary | STRATEGIC_POSITIONING | Reasonable fit |

**Result: 4 of 16 topics have reasonable category fits. 12 of 16 are forced into TECHNOLOGY_ASSESSMENT or STRATEGIC_POSITIONING with poor fit.** The entire Category B (quality standards) has no corresponding task category. The entire field of "evaluation methodology" has no category. "Prior art survey" has no category. "Architecture design" has no category.

The `custom_category` field on `ResearchTask` (line 156) exists as an escape hatch, but the `task_generator.py:163` logic shows it only gets used when the LLM explicitly provides it. The LLM would need to know to use `custom_category` and would be working against the constraint of the provided category enum. The `_resolve_category` method (line 195) defaults to `STRATEGIC_POSITIONING` on any unknown value — meaning misclassified categories silently get a strategic framing rather than the correct one.

### The fix

The category enum needs expansion for technical and design engagements. Minimum additions:

```python
PRIOR_ART_SURVEY = "prior_art_survey"          # A1, A2, A3, A4, A5
EVALUATION_METHODOLOGY = "evaluation_methodology" # A2, B1, B2, B3, B4
ARCHITECTURE_DESIGN = "architecture_design"     # A4, C1, C2, C4
QUALITY_STANDARDS = "quality_standards"         # B1, B2, B3
IMPLEMENTATION_ASSESSMENT = "implementation_assessment"  # C3, C4, D1
SYNTHESIS_AND_IDEATION = "synthesis_and_ideation"  # D2, D3
```

The `_CATEGORY_TEMPLATE_MAP` in `template_registry.py:208` would need corresponding entries mapping these new categories to appropriate agent templates (or new templates for "literature reviewer," "architecture analyst," "quality standards researcher").

---

## 4. Intent Clarification Gap: False Confidence

### What the clarifier did

The `IntentClarifier` at `intent_clarifier.py:52` called the `intent_clarification.md` prompt, which defines "intent clear" (line 48) as: the decision context is identifiable, scope is bounded enough to complete within 3 research rounds, deliverable expectations are clear, and the question is about a task not a job.

The clarifier returned `intent_clear=True`. This is wrong.

### What it should have flagged

The test question contains five unresolved ambiguities that any consulting analyst would surface before beginning research:

1. **Scope of "optimized":** Does "optimized" mean cost-optimized (minimize API spend), latency-optimized (fastest time to brief), quality-optimized (maximum analytical depth), or balanced? These lead to very different research priorities. A cost-optimization framing leads to research on model tier selection and caching strategies. A quality-optimization framing leads to research on evaluation design and deliberation architecture.

2. **"Company research and analysis" vs. architectural design questions:** The test question is primarily about *building* the pipeline, but the framing says the output should handle "company research and analysis." Is the question (a) how to design a general-purpose research pipeline, or (b) specifically how to handle company-specific research (competitive intelligence, due diligence, market entry)? These need different tool sets, different source types, and different evaluation rubrics.

3. **Team and infrastructure constraints:** The question says "boutique consulting firm" but doesn't specify team size, infrastructure (Mac Mini vs. cloud), API budget, or whether the firm has existing data assets. The 16 benchmark streams assume a specific context (Mac Mini infrastructure, multiple API keys, no existing RAG corpus) that the question doesn't state. A clarifier should ask: "What infrastructure will this run on, and what API budget is available per engagement?"

4. **"Matching McKinsey analysts" — which dimensions?** McKinsey quality could mean: (a) factual accuracy and citation density, (b) strategic insight and synthesis quality, (c) presentation format and narrative structure, (d) breadth of coverage and absence of blind spots, or (e) all of the above. The evaluation rubric depends on which dimensions are prioritized. The clarifier should ask: "What aspects of McKinsey-quality output are most important: citation rigor, analytical depth, narrative structure, or strategic insight?"

5. **Build vs. compose vs. integrate:** The question asks how to "architect and optimize" a pipeline but doesn't say whether the goal is (a) building it from scratch, (b) composing existing open-source tools (LangGraph, GPT-Researcher, DeepEval), or (c) wrapping existing commercial APIs (Claude Research, OpenAI Deep Research). These lead to entirely different research programs. The benchmark's A1 and A4 prompts explicitly address this ("which existing components should we compose rather than rebuild"), but the question as stated doesn't surface it.

### The threshold issue in the prompt

The `intent_clarification.md` defines `intent_clear: true` as a binary boolean with these four conditions (lines 48-51): decision context identifiable, scope bounded, deliverable clear, question is a task not a job. The problem is that ALL FOUR conditions read as true for this question at a surface level — there is a decision context (build a pipeline), the scope sounds bounded (a pipeline question), the deliverable sounds clear (an architecture recommendation), and it's a task not a job. The conditions are not sensitive enough.

The question that should determine `intent_clear` is not "can I describe a decision context" but "would a senior analyst be confident proceeding without a clarifying conversation." For complex, multi-dimensional questions, that bar is higher. The prompt needs a fifth condition: "Are the criteria for success specific enough that two analysts would agree on whether the research succeeded?"

The structural problem is that the clarifier runs immediately after classification, before the user has any feedback loop. There is no mechanism in the current design for the system to surface clarifying questions to the user and wait for answers. The `IntentClarificationResult` has `intent_clear: bool` but the upstream caller (the spec engine orchestrator) does not branch on it to enter a clarification dialogue. Even if `intent_clear=False`, the pipeline proceeds.

### The fix

Two changes are needed:

1. **Stricter threshold:** Add a fifth condition to `intent_clarification.md`: "The success criteria for this research are specific enough that two senior analysts would agree whether the research succeeded or failed." This catches multi-dimensional design questions where "success" is genuinely ambiguous.

2. **Clarification questions list:** Add a `clarifying_questions` field to `IntentClarificationResult` (next to `unstated_constraints`). The prompt should produce 3-5 specific questions when `intent_clear=False`. The orchestrator should check `intent_clear` and, when false, surface the questions to the user before proceeding. This is the interactive scoping conversation the system currently lacks.

---

## 5. MECE Quality: What the Lenses Would Actually Produce

### Reasoning through the actual output

The tree had 16 leaves at depth 2 with MECE validation passing. Based on the lens prompts and question text, here is a plausible reconstruction of what each lens produced:

**Financial lens (3-5 leaves):** The model, asked to apply a financial lens to "how to architect an agentic research pipeline for a boutique consulting firm," would likely produce:
- "LLM API cost structure per research engagement" (fin_1.1)
- "Infrastructure cost vs. quality tradeoff analysis" (fin_1.2)
- "Build vs. buy economics for core components" (fin_2.1)
- "Revenue model and pricing for the consulting firm's AI-enhanced services" (fin_2.2)
- "ROI measurement and payback period estimation" (fin_3.1)

None of these appear in any of the 16 benchmark streams. The benchmark has zero interest in the financial economics of building the system. The financial lens is categorically wrong for this question.

**Operational lens (3-5 leaves):**
- "Agent coordination patterns and communication protocols" (ops_1.1)
- "Pipeline execution infrastructure and latency" (ops_1.2)
- "Data quality and source reliability management" (ops_2.1)
- "Integration with existing consulting workflows" (ops_2.2)
- "Team training and adoption requirements" (ops_3.1)

The first three are partially relevant (touching on C4, A4, C2), but the framing is operational ("execution infrastructure," "data quality management") rather than design-oriented ("what architecture decisions produce best outcomes"). Items ops_2.2 and ops_3.1 are about organizational adoption, not covered by any benchmark stream.

**Market lens (4-6 leaves):**
- "Competitive landscape of existing deep research AI systems" (mkt_1.1)
- "Market positioning: where Keystone differentiates" (mkt_1.2)
- "Customer demand for AI-enhanced consulting services" (mkt_2.1)
- "Substitute solutions and competitive threats" (mkt_2.2)
- "Barriers to entry and adoption for competing systems" (mkt_3.1)

Items mkt_1.1 and mkt_1.2 partially cover A1 and D1, but through a competitive positioning lens rather than an architectural learning lens. The other three items are irrelevant to the benchmark.

**Synthesis (16 leaves):** The synthesis would merge these three trees, preserving unique branches and merging overlapping ones. The result would be a tree covering: cost economics, infrastructure, coordination patterns, workflow integration, competitive landscape, and market positioning. The benchmark's coverage of evaluation methodology (A2), self-improvement (A3), quality standards (B1-B4), specification-driven development (C1), deliberation design (C2), and academic literature synthesis (D2) would be absent entirely.

**Benchmark streams that would be missed:**
- A2: Evaluation & Verification Frameworks — completely absent
- A3: Self-Improvement and Learning Loops — completely absent
- B1: What Senior Consulting Partners Value — completely absent
- B2: Decision-Useful vs Comprehensive Research — completely absent
- B3: Taste, Judgment, Quality of Thought — completely absent
- B4: AI-Generated Research Quality Failures — completely absent
- C1: Specification-Driven Development — completely absent
- C2: Deliberation & Multi-Perspective Synthesis — partially present (in operational lens)

That's 7-8 of 16 benchmark streams completely missed.

---

## 6. Decomposition Comparison: Coverage Map

### Stream-by-stream assessment

| Benchmark Stream | Priority | L0 Coverage | L0 Framing |
|---|---|---|---|
| A1: Multi-Agent Systems | CRITICAL | Partial | Via market competitive landscape lens |
| A2: Evaluation Frameworks | CRITICAL | None | No evaluation lens exists |
| A3: Self-Improvement | HIGH | None | Not a consulting concept |
| A4: Orchestration Frameworks | HIGH | Partial | Via operational "technology capabilities" |
| A5: Deep Research Tooling | HIGH | Partial | Via market competitive landscape |
| B1: Senior Partner Quality Bar | CRITICAL | None | No quality standards lens |
| B2: Decision-Useful Research | CRITICAL | None | No methodology lens |
| B3: Taste and Judgment | HIGH | None | No methodology lens |
| B4: AI Research Failure Modes | CRITICAL | None | No failure analysis lens |
| C1: Specification-Driven Development | HIGH | None | No software design lens |
| C2: Deliberation & Synthesis | HIGH | Partial | Via operational "process efficiency" |
| C3: Report/Deliverable Generation | MEDIUM | None | Not in any lens |
| C4: Data Retrieval Architecture | HIGH | Partial | Via operational "technology capabilities" |
| D1: Individual AI Agent Systems | MEDIUM | Partial | Via market competitive landscape |
| D2: Academic Papers on Analysis | MEDIUM | None | No literature review lens |
| D3: 10x Ideas / Blue Sky | HIGH | Partial | Via market "macro trends" |

**Score: 4 full misses from CRITICAL priority, 5 full misses from HIGH priority, 1 from MEDIUM. Only 7 of 16 streams get even partial coverage, and none are covered with appropriate framing.**

### Over-coverage areas

The L0 output would over-cover:
- Cost economics and ROI (financial lens dominates several branches)
- Competitive market positioning (market lens produces Porter's Five Forces analysis that no benchmark stream requested)
- Organizational adoption (operational lens produces team/training branches)

---

## 7. Task Specification Depth: The 50-Word vs 800-Word Problem

### What a generated ResearchTask would look like

Based on `tasks.py:72` and `task_generator.py:_parse_tasks()`, a generated task has:
- `description`: "What this task should investigate" — in practice, ~50-100 words
- `acceptance_criteria`: list of 2-4 criteria
- `anti_confirmatory_framing`: single sentence
- `end_product`: "Specific output format" — one sentence

A plausible L0-generated task for the A1 benchmark stream would be:

```json
{
  "description": "Survey existing multi-agent research systems including GPT-Researcher, STORM, and similar frameworks. Assess their architectures, quality control approaches, and weaknesses relative to the proposed pipeline.",
  "acceptance_criteria": [
    "At least 5 distinct systems analyzed",
    "Architecture and quality control assessed for each",
    "Gaps identified relative to consulting-grade output"
  ],
  "anti_confirmatory_framing": "Evaluate whether existing systems address consulting-grade quality requirements, including evidence both for and against their adequacy"
}
```

### What the benchmark A1 prompt provides

The A1 prompt runs approximately 800 words. Key content the 50-word description cannot convey:

1. **Specific systems to research, named and contextualized:** "GPT-Researcher (assafelovic/gpt-researcher) is the longest-running open-source deep research agent at 25.7K+ stars... It recently added a Deep Research mode with tree-like exploration, an MCP server for integration with Claude and other agents." The generated task says "evaluate multi-agent systems" — the agent must discover the landscape from scratch.

2. **Specific sub-questions for each system:** "For each system, analyze: (1) Architecture: how agents coordinate, what the pipeline looks like, how state flows between phases, how it handles failures mid-pipeline; (2) Quality control: evaluation, verification, hallucination detection, source credibility, red-teaming. Is quality enforced structurally or through prompt instructions?" The generated task has no per-system sub-questions.

3. **The key decision framing:** "The key question: Given our six-layer pipeline architecture with an independent Evaluator and Rejection Library, which existing components should we compose rather than rebuild, and where do we need to build something genuinely new?" The generated task has no such focal question that guides the synthesis.

4. **Specific metrics and quantitative benchmarks to find:** "CMU's DeepResearchGym evaluated leading deep research systems on 1,000 complex queries." The generated task has no guidance on what quantitative evidence to seek.

5. **Anti-confirmatory calibration:** "Strengths we should learn from" alongside "weaknesses and gaps that Keystone's architecture addresses." The generated task's anti-confirmatory framing is generic ("evaluate whether... including evidence both for and against") rather than domain-specific.

**Information lost:** Approximately 700 words of targeted guidance. The research agent with the 50-word description must independently reconstruct the right research scope, the specific systems to examine, the evaluation criteria to apply, and the decision-relevant framing. It will produce broader, shallower research. This is the root cause of the "28 claims at 2-4 sentences each" vs. "8 systems at 1-2 paragraphs each" depth gap documented in FIRST-RUN-ANALYSIS.md.

### The fix

The task generator prompt (`task_generation.md`) must be redesigned to produce richer task descriptions. Specifically, for each leaf node in the issue tree, the generator should produce:

- **Specific entities to investigate** (not "existing systems" but named ones, if known from the day-1 hypothesis and engagement context)
- **Per-entity sub-questions** (3-7 questions the agent must answer for each entity)
- **Quantitative benchmarks or metrics to seek** (specific numbers, studies, or comparisons)
- **The key focal question** that the agent's synthesis must answer
- **Anti-confirmatory calibration** specific to this topic (not generic)

This cannot be achieved with a single-sentence description. Task descriptions should target 200-400 words — still shorter than the 800-word benchmark prompts, but sufficient to provide meaningful guidance.

---

## 8. Tool Assignment Appropriateness

### Current baseline tools

`tool_names.py:78`:
```python
BASELINE_AGENT_TOOLS: list[str] = [
    ToolName.EXA_SEARCH,
    ToolName.BRAVE_SEARCH,
    ToolName.PAPER_SEARCH,
]
```

`_ensure_minimum_distinct_tools()` in `task_generator.py:37` pads any under-3-tool list with these three.

### Template tool assignments for this question

The `_CATEGORY_TEMPLATE_MAP` at `template_registry.py:208` maps categories to templates:
- `TECHNOLOGY_ASSESSMENT` → `academic_researcher` → tools: `[paper_search, doi_verify, exa_search, brave_search, edgar_filings]`

The `academic_researcher` template includes `edgar_filings` (line 90 of template_registry.py). For research into multi-agent LLM systems, `edgar_filings` is useless. No SEC filing contains information about the architecture of GPT-Researcher or the evaluation methodology of DeepEval. The `edgar_filings` tool exists in the academic researcher template because it was added as a generic fallback for the academic researcher type — a vestige of the financial/market bias in the overall system design.

### What tools this question actually needs

For the 16 research streams in the benchmark:

| Stream Category | Appropriate Tools |
|---|---|
| A1-A5 (systems landscape) | `exa_search`, `brave_search`, `paper_search` — correct |
| A2 (evaluation frameworks) | `paper_search`, `exa_search`, `doi_verify` — correct subset |
| B1 (consulting quality standards) | `exa_search`, `brave_search` — no `paper_search` needed (practitioner knowledge) |
| C4 (data retrieval architecture) | `exa_search`, `brave_search`, `paper_search` — correct |
| D2 (academic papers) | `paper_search`, `doi_verify` — correct |

None of the 16 research streams require `edgar_filings`, `edgar_financials`, `edgar_company_facts`, `fred_data`, or `finnhub_market`. These are financial data tools appropriate for company due diligence and market sizing — not for technical architecture research.

The `_CATEGORY_TEMPLATE_MAP` entry for `TECHNOLOGY_ASSESSMENT` → `academic_researcher` with `edgar_filings` is the specific misalignment. The academic researcher template was designed for "technology readiness level assessment" of a company's technology — an evaluative engagement. For a design-and-survey engagement, the right template is closer to the `_GENERALIST` template, which also unfortunately includes `edgar_filings` and `finnhub_market` (line 138-139 of template_registry.py).

The only template that avoids financial tool contamination for this question type would be a new "technical literature researcher" template with `[paper_search, doi_verify, exa_search, brave_search]` and a system prompt oriented toward evaluating technical architectures rather than assessing company technology.

### The fix

Two changes:

1. **Remove `edgar_filings` from non-financial templates.** The `academic_researcher` template at line 90 of `template_registry.py` and the `generalist_researcher` at line 138 include `edgar_filings` as a default tool. This is inappropriate for non-financial research tasks. Remove it from these templates and only include it in the `quantitative_analyst` and `regulatory_analyst` templates.

2. **Add domain-appropriate templates.** Add a `technical_architecture_researcher` template with tools `[paper_search, doi_verify, exa_search, brave_search]` and a system prompt oriented toward "evaluate architectural choices, assess implementation complexity, identify prior art, and compare approaches." Map `ARCHITECTURE_DESIGN` and `PRIOR_ART_SURVEY` categories to this template.

---

## 9. Concrete Recommendations by Issue

### Issue L0-1: Hardcoded lenses (CRITICAL)

**What the dynamic system looks like:** A new `LensSelector` component runs before `Decomposer.decompose()`. It makes one LLM call with a prompt that: (a) presents the question and engagement type, (b) provides a menu of 12 possible lenses each with a 1-sentence description and 3-4 focus areas, (c) instructs the model to select 2-4 lenses that together would produce a collectively exhaustive decomposition. The output is a list of lens objects with `{"name": str, "description": str, "focus_areas": [str]}`.

The `Decomposer` receives these lens objects instead of the hardcoded `_LENSES` list. The lens prompt templates (`decompose_financial_lens.md` etc.) are replaced by a single `decompose_generic_lens.md` that accepts `{{lens_name}}`, `{{lens_description}}`, and `{{lens_focus_areas}}` as template variables.

The `decompose_synthesis.md` must be refactored: instead of named `financial_tree`, `operational_tree`, `market_tree` variables, it receives a `lens_trees` JSON array where each element includes the lens name and its tree.

**Decision criteria for the lens selector:** The selector should prioritize lenses that: (a) each cover a distinct analytical dimension (non-overlapping), (b) together cover the full question space (collectively exhaustive), and (c) match the question's domain (technical, organizational, financial, etc.).

### Issue L0-2: Intent clarifier false confidence (HIGH)

**What the fix looks like:** Add `clarifying_questions: list[str]` to `IntentClarificationResult`. Update the `intent_clarification.md` prompt to require that `clarifying_questions` be populated whenever `intent_clear=False`. Add a fifth clarity condition to the prompt: "The success criteria are specific enough that two senior analysts would agree whether the research succeeded." Update the orchestrator (or the CLI interface) to detect `intent_clear=False`, surface the clarifying questions to the user, and accept answers before proceeding. The answers feed back into the spec as additional `client_context`.

### Issue L0-3: Task generation timeout (FIXED, but root cause remains)

The timeout fix (300s → 600s) addresses the symptom. The root cause is generating all 15 tasks in one LLM call. The fix is to chunk task generation: split the issue tree leaves into batches of 4-5 and make one LLM call per batch. The `TaskDecomposition.validate_dag()` runs on the combined output. This reduces per-call token count from ~15K to ~5K, decreasing timeout risk and improving output quality (LLMs produce better output on smaller, focused prompts).

### Issue L0-4: EngagementType taxonomy (HIGH)

**Minimum addition:** Add `DESIGN = "design"` and `TECHNICAL_EVALUATION = "technical_evaluation"` to the enum. Update `classification.md` with descriptions and examples for these types. Add entries to `_DEFAULT_PROFILES`. Add evaluation weight profiles for these types. The `_DEFAULT_METHODOLOGY` in the spec engine (if it exists) must map these types to appropriate frameworks — not Porter's Five Forces, but perhaps "technology readiness levels" or "architecture evaluation methodology (ATAM)."

### Issue L0-5: TaskCategory enum (HIGH)

**Minimum additions:** Add `PRIOR_ART_SURVEY`, `EVALUATION_METHODOLOGY`, `ARCHITECTURE_DESIGN`, `QUALITY_STANDARDS`. Update `_CATEGORY_TEMPLATE_MAP` in `template_registry.py` to map these to appropriate agent templates (create `technical_architecture_researcher` template if needed). Update `_SOURCE_TEMPLATE_AFFINITY` with relevant source type → template mappings (e.g., `"github_repos": "technical_architecture_researcher"`).

### Issue L0-6: No intermediate visibility (MEDIUM)

Write each L0 step's output to `output/{engagement_id}/l0/`:
- `l0_classification.json`: the `ClassificationResult`
- `l0_intent_clarification.json`: the `IntentClarificationResult`
- `l0_lens_selection.json`: the selected lenses (once dynamic)
- `l0_financial_lens.json`, `l0_operational_lens.json`, `l0_market_lens.json`: raw lens tree JSONs (renaming once dynamic)
- `l0_issue_tree.json`: the synthesized tree
- `l0_priority_scores.json`: the priority scorer output
- `l0_tasks.json`: the final `TaskDecomposition`

This enables debugging, quality review, and the kind of comparative analysis done in FIRST-RUN-ANALYSIS.md without requiring code instrumentation.

### Issue L0-7: Task description depth (CRITICAL)

**What richer task descriptions require:** The `task_generation.md` prompt must instruct the LLM to produce, for each leaf node:

1. `description`: 150-300 words covering what to investigate, why it matters, and what a complete answer would contain
2. `specific_entities`: named systems, papers, frameworks, or organizations to examine
3. `sub_questions`: 3-5 questions the agent must answer
4. `focal_question`: the synthesis question the agent's findings must address
5. `anti_confirmatory_framing`: specific to this topic (not generic)

This increases token usage per task generation call but dramatically improves research quality. The `ResearchTask` model already has `description`, `acceptance_criteria`, `anti_confirmatory_framing`, and `end_product` — the fields exist, they just need richer content.

---

## Summary Scorecard

| Dimension | Current State | Severity |
|---|---|---|
| Lens selection | Hardcoded financial/operational/market for all questions | CRITICAL |
| Lens fitness for test question | 0% financial, 30% operational, 25% market overlap with benchmark | CRITICAL |
| Engagement type fitness | STRATEGIC is closest but incorrectly scoped | HIGH |
| TaskCategory coverage | 4 of 16 benchmark topics have reasonable fit | HIGH |
| Intent clarifier sensitivity | `intent_clear=True` on a 5-ambiguity question | HIGH |
| MECE validity | Structurally correct, topically wrong | HIGH |
| Benchmark stream coverage | 7-9 of 16 streams partially covered, 7-9 fully missed | CRITICAL |
| Task description depth | 50-word descriptions vs 800-word benchmark prompts | CRITICAL |
| Tool assignment for technical questions | edgar_filings appears in non-financial templates | MEDIUM |
| Intermediate artifact visibility | No file output from any L0 step | MEDIUM |

**Net assessment:** L0 is a structurally sound specification engine built with consulting-engagement defaults. It produces correct, MECE-validated output for the use cases it was designed for. The first real run exposed that the design envelope is narrower than intended — specifically, it handles company/market/financial research questions well, but breaks on technical architecture, evaluation methodology, and system design questions. All identified issues are fixable within the existing architecture. No fundamental redesign is needed, but the four CRITICAL issues must be addressed before L0 produces research-grade task specifications for non-standard questions.
