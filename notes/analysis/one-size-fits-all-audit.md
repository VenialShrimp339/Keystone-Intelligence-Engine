# One-Size-Fits-All Audit: Hardcoded Consulting Defaults

**Date:** 2026-04-21
**Context:** Post-mortem on 2026-04-23 first pipeline run. Question was a technical architecture question ("design an agentic research system") and the pipeline applied consulting-engagement defaults throughout, producing nonsensical outputs.
**Scope:** Every file in `src/keystone/specification/`, `src/keystone/research/`, `src/keystone/deliberation/`, `src/keystone/evaluator/`, `src/keystone/models/`, `src/keystone/structuring/`, `src/keystone/gateway/`, and `src/keystone/tool_names.py`.

---

## Summary of Findings

| Priority | Count | Description |
|---|---|---|
| CRITICAL | 9 | Blocks non-consulting use; produces nonsensical output |
| HIGH | 11 | Degrades quality significantly; wrong framing applied |
| MEDIUM | 8 | Suboptimal but pipeline still runs |

The system was built for one archetype: a consulting firm doing company/market/industry research for a client. Every structural assumption encodes that archetype. A molecular biology literature review, a build-vs-buy technology evaluation, or a process design question for an internal team all hit these defaults and get systematically wrong behavior.

---

## L0 Specification Layer

### Finding 1 — Hardcoded decomposition lenses: financial / operational / market

**File:** `src/keystone/specification/decomposer.py`, line 56

```python
_LENSES = ["financial", "operational", "market"]
```

**What's hardcoded:** The decomposer always spawns exactly three lens agents — a financial analyst, an operations strategist, and a market consultant — regardless of what was asked. Three prompt files are named `decompose_financial_lens.md`, `decompose_operational_lens.md`, and `decompose_market_lens.md`. The synthesis prompt at line 184–189 hardcodes these same three labels in positional arguments:

```python
financial_tree=json.dumps(lens_trees[0], indent=2),
operational_tree=json.dumps(lens_trees[1], indent=2),
market_tree=json.dumps(lens_trees[2], indent=2),
```

The synthesis prompt (`decompose_synthesis.md`, line 42) also hardcodes these lenses in the "Synthesis Strategy" section: "Start with the tree that best matches the engagement type (financial for sizing, market for evaluative, operational for diagnostic)."

**Why it breaks:** Asked "how should we design an agentic research system?", the decomposer runs:
- A financial analyst who produces branches about revenue models, capital requirements, and unit economics — completely irrelevant.
- An operations strategist who produces branches about manufacturing capacity and supply chain — completely irrelevant.
- A market/competitive analyst who produces branches about Porter's Five Forces and market sizing — completely irrelevant.

The synthesis agent then merges three irrelevant trees into one slightly-less-irrelevant unified tree. For a molecular biology research question, a legal brief analysis question, or any internal capability-building question, all three lenses are wrong.

**Proposed fix:** Classify lenses dynamically from the `engagement_type` and question domain before running decomposition. Add a `lens_selector.py` step that maps engagement type and detected domain (technical, scientific, business, policy, operational, organizational) to an appropriate lens set. Example: `(EVALUATIVE, technical_domain)` → lenses `["technical_feasibility", "implementation_risk", "adoption_dynamics"]`. The `_LENSES` list becomes a fallback for business/market questions only. The synthesis prompt should receive dynamic labels, not hardcoded `financial_tree`/`operational_tree`/`market_tree` kwargs.

**Priority: CRITICAL** — this is the first major decomposition step; wrong lenses corrupt every downstream task.

---

### Finding 2 — EngagementType enum is consulting-scoped

**File:** `src/keystone/models/research.py`, lines 23–35

```python
class EngagementType(StrEnum):
    SIZING = "sizing"
    DIAGNOSTIC = "diagnostic"
    EVALUATIVE = "evaluative"
    EXPLORATORY = "exploratory"
    STRATEGIC = "strategic"
```

**What's hardcoded:** Five types designed around client-facing consulting work. The classification prompt (`specification/prompts/classification.md`, lines 16–22) gives examples that are exclusively market/company-focused: "Estimate TAM for autonomous vehicle sensors," "What caused the Q3 revenue decline," "Evaluate the competitive position of Company X in the EV market," "What's happening in the generative AI infrastructure market?"

There is no type for: technology architecture evaluation, internal process design, build-vs-buy analysis, scientific literature synthesis, legal/policy analysis, or organizational design. When the system is given a technical architecture question, it must force-fit it into one of five consulting types. The classifier then applies defaults (methodology requirements, framework selector, rubric weights) that are wrong for the forced category.

**Why it breaks:** A question like "Design the architecture for an agentic research pipeline" gets classified as `EVALUATIVE` or `EXPLORATORY`. `EVALUATIVE` triggers Porter's Five Forces as the primary framework. `EXPLORATORY` triggers landscape mapping. Neither is appropriate for a design question. The `_DEFAULT_METHODOLOGY` and `_FRAMEWORK_MAP` then apply consulting frameworks to technical questions.

**Proposed fix:** Add additional `EngagementType` values that cover the non-consulting cases the owner explicitly describes: `DESIGN` (architecture, system, process), `SYNTHESIS` (literature, evidence), `BUILD_EVALUATE` (build-vs-buy), `ORGANIZATIONAL` (org design, team structure), `POLICY_ANALYSIS`. Alternatively, treat the current five as subtypes of a broader taxonomy and add an `OTHER` enum value with a `custom_type` free-text field on `ResearchSpec`. The classifier must be updated to recognize and route these new types.

**Priority: CRITICAL** — wrong engagement type cascades into wrong methodology, wrong frameworks, wrong rubric weights, and wrong template selection throughout the pipeline.

---

### Finding 3 — _DEFAULT_METHODOLOGY maps engagement types to consulting frameworks

**File:** `src/keystone/specification/spec_engine.py`, lines 60–101

```python
_DEFAULT_METHODOLOGY: dict[EngagementType, list[MethodologyRequirement]] = {
    EngagementType.SIZING: [
        MethodologyRequirement(framework="Top-Down / Bottom-Up Estimation", ...),
    ],
    EngagementType.EVALUATIVE: [
        MethodologyRequirement(framework="Porter's Five Forces", ...),
    ],
    EngagementType.STRATEGIC: [
        MethodologyRequirement(framework="Scenario Planning", ...),
        MethodologyRequirement(framework="Porter's Five Forces", ...),
    ],
    ...
}
```

**What's hardcoded:** Every engagement type gets a consulting-specific analytical framework injected as a methodology requirement. These are stamped onto `ResearchSpec.methodology` at line 354, which then propagates into every agent's context.

**Why it breaks:** A technical architecture question classified as `EVALUATIVE` gets Porter's Five Forces injected as a mandatory methodology. Research agents reading the spec will orient their analysis around competitive forces (supplier power, buyer power, threat of substitutes) when they should be evaluating technical trade-offs (scalability, latency, fault tolerance, maintainability). A scientific synthesis question gets "Scenario Planning" or "Landscape Mapping" when it needs a systematic review protocol.

**Proposed fix:** The methodology should be LLM-selected at specification time, not hardcoded by engagement type. The intent clarifier (Step 2) already asks the question "what decision does this research inform?" — that context should feed a methodology selection step that recommends domain-appropriate frameworks. The `_DEFAULT_METHODOLOGY` dict should become a fallback for business engagements only, not a universal assignment.

**Priority: CRITICAL**

---

### Finding 4 — _DEFAULT_SOURCES assumes news and industry reports universally

**File:** `src/keystone/specification/spec_engine.py`, lines 103–106

```python
_DEFAULT_SOURCES: list[SourceRequirement] = [
    SourceRequirement(source_type="news", minimum_count=5, quality_threshold=0.5),
    SourceRequirement(source_type="industry_reports", minimum_count=2, quality_threshold=0.7),
]
```

**What's hardcoded:** Every engagement gets a requirement for at minimum 5 news sources and 2 industry reports, regardless of the question domain. This list is injected at line 374 into every `ResearchSpec`.

**Why it breaks:** A technical architecture question needs academic papers, technical documentation, and GitHub repositories — not news and industry reports. A molecular biology question needs peer-reviewed journals and clinical studies. A legal analysis needs case law and statutes. Requiring news sources for a question where news is irrelevant means agents waste tool calls fetching useless content and the Evaluator's Source Quality dimension may penalize the output for not having enough "news" sources.

**Proposed fix:** Source requirements should be inferred from the question domain and engagement type, not hardcoded as universal defaults. The intent clarifier step could output a `recommended_sources` list, or a dedicated source-planner step could run after classification. Fallback to `["web_search"]` only when domain is unclassifiable.

**Priority: CRITICAL**

---

### Finding 5 — TaskCategory enum is consulting-scoped

**File:** `src/keystone/models/tasks.py`, lines 16–24

```python
class TaskCategory(StrEnum):
    MARKET_SIZING = "market_sizing"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    FINANCIAL_ANALYSIS = "financial_analysis"
    TECHNOLOGY_ASSESSMENT = "technology_assessment"
    REGULATORY = "regulatory"
    STRATEGIC_POSITIONING = "strategic_positioning"
```

**What's hardcoded:** Six categories. Five are explicitly consulting/business: market sizing, competitive landscape, financial analysis, regulatory analysis, strategic positioning. Only `TECHNOLOGY_ASSESSMENT` could generalize. There is no category for: literature synthesis, process design, system architecture, organizational analysis, build-vs-buy evaluation, experimental design, or policy analysis.

The task_generation prompt (line 28 in `task_generation.md`) instructs the LLM: "Category: One of: market_sizing, competitive_landscape, financial_analysis, technology_assessment, regulatory, strategic_positioning." The LLM is forced to assign one of these six even when none fits.

**Why it breaks:** For a technical architecture question, every task gets assigned `STRATEGIC_POSITIONING` (the generalist fallback at `task_generator.py` line 163) or misassigned to `TECHNOLOGY_ASSESSMENT`. The `_CATEGORY_TEMPLATE_MAP` in `template_registry.py` then routes `STRATEGIC_POSITIONING` to the `generalist_researcher` template, which has EDGAR filings in its tool set.

**Proposed fix:** Add categories appropriate for non-consulting work: `LITERATURE_SYNTHESIS`, `SYSTEM_DESIGN`, `PROCESS_ANALYSIS`, `ORGANIZATIONAL_ANALYSIS`, `EXPERIMENTAL_DESIGN`. The `custom_category` field on `ResearchTask` (already exists at line 154) is designed for this escape hatch but it requires the LLM to know to use it. Make the task generator prompt aware of `custom_category` as the preferred path for novel categories. Update `_CATEGORY_TEMPLATE_MAP` to include new categories.

**Priority: CRITICAL**

---

### Finding 6 — Task generation prompt hardcodes consulting-specific task categories

**File:** `src/keystone/specification/prompts/task_generation.md`, line 28

```
Category: One of: market_sizing, competitive_landscape, financial_analysis, technology_assessment, regulatory, strategic_positioning.
```

**What's hardcoded:** The LLM instruction bakes the consulting-scoped category list directly into the prompt text. Even if `TaskCategory` enum were extended, this prompt would still constrain the LLM to the old six.

**Why it breaks:** The LLM cannot assign a `literature_synthesis` or `system_design` category even if such values existed in the enum — it has been explicitly told to choose from six consulting options. For any non-consulting question, the LLM is forced to either misassign or hallucinate a value.

**Proposed fix:** The task generation prompt should receive the category list dynamically from `available_categories` (a new template placeholder), not have it hardcoded. The task generator should build this list from `TaskCategory` enum members plus any domain-specific categories inferred at classification time.

**Priority: HIGH** — doubles the impact of Finding 5.

---

### Finding 7 — Classification prompt gives only consulting examples

**File:** `src/keystone/specification/prompts/classification.md`, lines 16–22

The `## Classification Taxonomy` section gives exactly five examples, all business/market consulting scenarios:
- "Estimate TAM for autonomous vehicle sensors in North America."
- "What caused the Q3 revenue decline despite increased marketing spend?"
- "Evaluate the competitive position of Company X in the EV market."
- "What's happening in the generative AI infrastructure market?"
- "Should we acquire Company Y given current market conditions?"

**What's hardcoded:** The few-shot examples in the classification prompt exclusively model consulting scenarios. The classifier LLM is being told, implicitly through examples, that "this is what research questions look like."

**Why it breaks:** A question about "how do we design an agentic research pipeline?" doesn't pattern-match to any of these examples. The classifier will force-fit it into the nearest consulting type. A question about "what does the literature say about transformer scaling laws?" has no exemplar at all.

**Proposed fix:** Add diverse examples covering technical, scientific, organizational, and policy questions. At minimum, one example per engagement type should be non-consulting: `EXPLORATORY` example should include a literature survey; `EVALUATIVE` example should include a build-vs-buy technical evaluation; `STRATEGIC` example should include an internal capability-building decision. The signal descriptions (lines 33–39) — especially "Known analytical framework: Does the question map to established frameworks (Porter's Five Forces, TAM/SAM/SOM, root cause analysis)?" — should also list non-consulting frameworks.

**Priority: HIGH**

---

### Finding 8 — Intent clarification prompt is consulting-persona only

**File:** `src/keystone/specification/prompts/intent_clarification.md`

The prompt opens: "You are a senior strategy consultant performing Decision-First analysis on a research engagement." Every step is framed around a client relationship: "Step 1: What decision does this research inform?" references a "decision-maker" and "constraints." Step 5 notes that "Political positioning, client relationship management, and implementation planning are always out of scope."

**What's hardcoded:** The consultant persona, "client" framing, and "decision-maker" terminology throughout. The hardcoded non-goals at `spec_engine.py` lines 357–359 are:
```python
non_goals = [
    "Political positioning and recommendation framing",
    "Client relationship management",
]
```

**Why it breaks:** For an internal capability-building question, there is no "client." The "decision-maker" is the organization's own team. "Client relationship management" being a hardcoded non-goal is meaningless for an internal technical question. More importantly, the consulting framing shapes what `decision_context` and `surprising_finding` will look like, which then appear on the `ResearchSpec` and propagate into every agent's prompt context.

**Proposed fix:** The persona in the prompt should adapt to the engagement type. For technical/internal questions, the prompt should frame around "What problem does this solve?" rather than "What decision does this inform?". The hardcoded non-goals in `spec_engine.py` should be empty by default, populated dynamically from the clarification step.

**Priority: HIGH**

---

### Finding 9 — Decompose synthesis prompt instructs consulting-biased starting lens

**File:** `src/keystone/specification/prompts/decompose_synthesis.md`, lines 41–44

```
## Synthesis Strategy
- Start with the tree that best matches the engagement type (financial for sizing, market for evaluative, operational for diagnostic)
```

**What's hardcoded:** The synthesis guidance explicitly maps engagement types to consulting lenses: financial for sizing, market for evaluative, operational for diagnostic. This is a design rule baked into a prompt file.

**Why it breaks:** Even if the classification and lens selection were fixed, this guidance would still anchor synthesis toward consulting-framing. For a technical question classified as EVALUATIVE, the synthesis would try to "start with the market tree" — which for a technical question is the least relevant starting point.

**Proposed fix:** Remove the prescriptive mapping and replace with: "Start with the lens tree that most directly addresses the core question. Use the day_1_hypothesis to identify which branches are most central and anchor from those." Let the synthesis LLM decide the starting point based on the content, not a hardcoded engagement_type mapping.

**Priority: MEDIUM** — depends on Finding 1 being fixed; once lenses are dynamic this guidance becomes less harmful.

---

## L1 Research Layer

### Finding 10 — EDGAR filings appear in every default agent template

**File:** `src/keystone/specification/template_registry.py`, lines 33–195

Four of the seven seed agent templates include `ToolName.EDGAR_FILINGS` in their tool lists:
- `_QUANTITATIVE_ANALYST` (line 39): includes `EDGAR_FILINGS`, `EDGAR_FINANCIALS`, `EDGAR_COMPANY_FACTS`
- `_MARKET_RESEARCHER` (line 67): includes `EDGAR_FILINGS`
- `_ACADEMIC_RESEARCHER` (line 90): includes `EDGAR_FILINGS`
- `_REGULATORY_ANALYST` (line 114): includes `EDGAR_FILINGS`
- `_GENERALIST` (line 138): includes `EDGAR_FILINGS`

**What's hardcoded:** EDGAR is a US-only SEC financial filing database. It has zero value for technical architecture questions, scientific literature questions, legal analysis (non-US), organizational design, or most non-financial research. Yet it appears in five of seven templates including `generalist_researcher` (the catch-all default for unrecognized categories).

**Why it breaks:** Every task not matched to a specific template falls back to `generalist_researcher`, which includes EDGAR in its tool set. The task generator then assigns EDGAR to technical research tasks. Agents get confused or waste tool calls attempting EDGAR lookups for companies that don't exist or for questions where financial filings are irrelevant.

**Proposed fix:** Remove EDGAR from `generalist_researcher` and `academic_researcher` templates. EDGAR should appear only in `quantitative_analyst`, `regulatory_analyst`, and `market_researcher`. Add a `technical_researcher` template for system design and architecture questions with tools: `paper_search`, `exa_search`, `brave_search`. Update `_CATEGORY_TEMPLATE_MAP` to route new `SYSTEM_DESIGN` and `LITERATURE_SYNTHESIS` categories to this template.

**Priority: CRITICAL** — this is the specific tool-assignment bug exposed in the first pipeline run.

---

### Finding 11 — BASELINE_AGENT_TOOLS padding pulls in EDGAR filings

**File:** `src/keystone/tool_names.py`, lines 78–82
**File:** `src/keystone/specification/task_generator.py`, lines 55–63

```python
BASELINE_AGENT_TOOLS: list[str] = [
    ToolName.EXA_SEARCH,
    ToolName.BRAVE_SEARCH,
    ToolName.PAPER_SEARCH,
]
```

The `_ensure_minimum_distinct_tools` function in `task_generator.py` pads any tool list that has fewer than 3 entries by appending from `BASELINE_AGENT_TOOLS`. This is reasonable — but the templates that get padded include EDGAR (from the template's own list), so the final tool set for many tasks ends up: `[exa_search, brave_search, edgar_filings]` — EDGAR again appearing for non-financial tasks via the template's first-listed tools.

**What's hardcoded:** `BASELINE_AGENT_TOOLS` contains only general web search tools, which is fine, but the padding logic appends to whatever the template already provides. If the template includes EDGAR and only provides 2 tools, the padded result has EDGAR plus two baseline tools.

**Proposed fix:** The padding logic should filter out domain-specific tools (EDGAR, FRED, FINNHUB) from templates when the engagement domain is non-financial. Add a `domain_filter: set[str]` parameter to `_ensure_minimum_distinct_tools` that excludes tools inappropriate to the domain. Pass domain inferred from engagement type.

**Priority: HIGH**

---

### Finding 12 — Research agent synthesis prompt uses "consulting engagement" framing

**File:** `src/keystone/research/prompts/synthesis.md` (reviewed indirectly through `research_agent.py` line 874)

The synthesis prompts are loaded from `research/prompts/synthesis.md`. The research agent prompt chain (shallow mode, `_build_synthesis_prompt` at line 840) passes `task_description` and `anti_confirmatory_framing` as the core agent-instruction anchors. These are task-specific, so the prompt itself is more flexible than the decomposition prompts. However, the `AgentDefinition.system_prompt` fields (in `template_registry.py`) are hardcoded consulting system prompts for every agent:

- `_QUANTITATIVE_ANALYST` system prompt: "You are a quantitative research analyst. Your methodology is data-driven: start with financial filings and economic data..."
- `_MARKET_RESEARCHER` system prompt: "You are a market research analyst. Your methodology focuses on competitive dynamics, market structure, and strategic positioning."
- `_GENERALIST` system prompt: "You are a generalist research analyst. Your methodology is breadth-first: survey the landscape before going deep. Identify cross-cutting themes..."

**What's hardcoded:** All system prompts for research agents are pre-written consulting personas. Even the `generalist_researcher` prompt mentions "identify cross-cutting themes and unexpected connections between domains" — reasonable — but the context in which it appears is a template matched to consulting-style tasks.

**Why it breaks:** For a technical architecture question, an agent assigned the `market_researcher` template will have a system prompt telling it to "focus on competitive dynamics, market structure, and strategic positioning" for a question about software architecture trade-offs.

**Proposed fix:** System prompts should be generated (or at minimum selected) based on the actual task domain. Add a `domain` field to `AgentDefinition` and a mapping from domain to system prompt variant. The template registry's `match` method should use domain as a primary signal when selecting templates, and templates should have domain-appropriate system prompts. For the immediate fix: add a `technical_researcher` template with an appropriate system prompt.

**Priority: HIGH**

---

### Finding 13 — L1 sub-agent orchestration hardcodes consulting categories

**File:** `src/keystone/models/config.py`, lines 399–405

```python
l1_orchestrator_categories: list[str] = Field(
    default_factory=lambda: ["competitive_landscape", "market_sizing"],
    description=(
        "Task categories eligible for sub-agent dispatch. "
        "Values must match TaskCategory enum members."
    ),
)
```

**What's hardcoded:** The sub-agent orchestration feature is enabled by default only for `competitive_landscape` and `market_sizing` — the two most consulting-specific categories. Other categories (including `technology_assessment`, which is the most likely match for non-consulting questions) are not eligible.

**Why it breaks:** A technical architecture question with tasks assigned `technology_assessment` category won't benefit from sub-agent orchestration even when the task is complex enough to warrant it. The feature is effectively locked to consulting use cases.

**Proposed fix:** The default list should include `technology_assessment` and be configurable per question domain. The eligibility criterion should be "task complexity" (estimated token depth, number of issue tree branches) rather than a hardcoded category list.

**Priority: MEDIUM** — sub-agent dispatch is behind a feature flag (`l1_orchestrator_enabled: bool = False`), so this won't fire in default operation.

---

## L1.5 Deliberation Layer

### Finding 14 — Deliberation analyst types are fixed and consulting-biased

**File:** `src/keystone/models/agents.py`, lines 44–55

```python
class DeliberationAnalystType(StrEnum):
    ACH = "ach"
    QUANTITATIVE = "quantitative"
    ADVERSARIAL = "adversarial"
    HISTORICAL_ANALOGY = "historical_analogy"
    SCENARIO_PLANNING = "scenario_planning"
```

**File:** `src/keystone/deliberation/analyst.py`, lines 62–88

```python
METHODOLOGY_PROMPTS: dict[str, str] = {
    DeliberationAnalystType.ACH: "...intelligence analyst using Analysis of Competing Hypotheses...",
    DeliberationAnalystType.QUANTITATIVE: "...quantitative analyst. For each claim, evaluate numerical evidence...",
    DeliberationAnalystType.ADVERSARIAL: "...adversarial analyst tasked with finding weaknesses...",
    DeliberationAnalystType.HISTORICAL_ANALOGY: "...historical analogy analyst. For each claim, identify relevant historical precedents...",
    DeliberationAnalystType.SCENARIO_PLANNING: "...scenario planning analyst. For each claim, consider multiple future scenarios...",
}
```

**What's hardcoded:** Five fixed deliberation analyst methodologies. They are generally robust (ACH and adversarial are domain-agnostic, quantitative and historical analogy are partially applicable), but `SCENARIO_PLANNING` is business-futures-oriented and `HISTORICAL_ANALOGY` focuses on "markets," "regulatory cycles," and "growth rates" in the prompt text (`deliberation/prompts/historical_analogy.md`, lines 8–17).

The `historical_analogy.md` prompt explicitly mentions "A claim about 'AI startup valuations' belongs to a different reference class than 'technology startup valuations'" — which is business-framed. It also references "regulatory shifts" and "growth rate[s]" as the canonical claim types worth analyzing, which assumes financial/market research.

**Why it breaks:** For a technical architecture question, "historical analogy" applied to a claim like "microservices are better than monoliths for this system" would look for historical base rates in "markets" and "regulatory cycles" rather than in software engineering case studies. The prompt doesn't know to reason about software architecture precedents.

**Proposed fix:** The `historical_analogy.md` and `scenario_planning.md` prompts should use domain-neutral language — replace market/regulatory examples with generic examples. `historical_analogy.md` should instruct the analyst to find reference classes appropriate to the claim's domain, not assume it is financial. Additionally, consider adding a `TECHNICAL_FEASIBILITY` analyst type for technical questions, and a `META_ANALYSIS` type for scientific synthesis questions.

**Priority: MEDIUM** — the methodologies work reasonably for non-consulting questions despite business-domain examples. The framing is imperfect but not completely broken.

---

### Finding 15 — WWHTB and gap detector prompts assume business context

**File:** `src/keystone/deliberation/prompts/wwhtb.md` and `src/keystone/deliberation/prompts/judge.md` (reviewed indirectly)

The "What Would You Have to Believe?" (WWHTB) mechanism fires when `wwhtb_confidence_threshold` is below 0.6 and generates belief statements. Though the WWHTB prompt file itself is reasonably domain-agnostic, the `deliberation/prompts/judge.md` prompt (not read, but referenced in `aggregator.py`) likely uses consulting-domain language since the entire deliberation layer was designed around consulting research outputs.

**What's hardcoded:** The specific confidence threshold (0.6) and how WWHTB beliefs are framed are fixed. The aggregator and judge components are not easily domain-parameterized.

**Proposed fix:** Mark as low priority relative to the structural issues, but audit `judge.md` and `wwhtb.md` prompt files for consulting-specific language and replace with domain-neutral framing.

**Priority: MEDIUM**

---

## L4 Evaluator Layer

### Finding 16 — Actionability rubric dimension assumes client/consulting context

**File:** `src/keystone/evaluator/prompts/actionability.md`

The dimension definition (line 12): "Actionability measures whether a consultant could advise a client based on this output."

The scoring rubric throughout uses "client" language: "A decision-maker reading this..." (lines 21, 28, 35, 42), "recommendations segmented by role (CEO, VP Marketing, Operations)" (line 43), "Recommendations are genuinely specific to this client — they would not apply to competitors" (line 44).

The trendslop detection sub-check (line 35): "replace the client's name with a competitor's name. If the recommendation still holds, it is trendslop."

**What's hardcoded:** The actionability dimension is defined entirely around a consulting client-deliverable archetype. The sub-criteria notes require exactly: "monday-morning test," "trendslop detection," "role segmentation," and "tradeoff analysis" — all consulting-specific framings.

**Why it breaks:** For a technical architecture research output, "role segmentation" into "CEO, VP Marketing, Operations" is irrelevant. "Trendslop detection" using competitor name substitution doesn't apply to an internal architecture decision. "Monday-morning actionability" could apply (can an engineer act on this?) but the framing is wrong. A technical output scoring well on actionability should be evaluated on: "could an engineer implement this decision?" not "could a consultant advise a client?"

**Proposed fix:** The `actionability.md` prompt should receive an `engagement_context` placeholder (e.g., `consulting_client` vs `internal_technical` vs `scientific`) that adapts the dimension definition and scoring rubric accordingly. The sub-criteria for consulting context remain as-is; for technical context they become: "implementability test" (can an engineer act on this?), "specificity check" (are trade-offs named specifically enough to make the decision?), "risk identification" (are implementation risks called out?), "decision completeness" (does this resolve the architectural decision without another research round?).

**Priority: HIGH**

---

### Finding 17 — Intent Alignment rubric assumes client/consulting context

**File:** `src/keystone/evaluator/prompts/intent_alignment.md`

Lines 10–13: "Intent Alignment measures whether the research output serves the client's stated decision context." The "Klarna pattern" archetype failure is described as: "technically correct, strategically wrong." Every scoring tier uses "client" language.

Sub-criteria include "decision context mapping: Does the output explicitly reference the decision the client faces?" and "strategic framing: Are findings framed as inputs to the client's decision, or as standalone observations?"

**What's hardcoded:** "Client" appears 12+ times. "Strategic framing" assumes a client-strategy deliverable. The entire framing is wrong for internal/technical questions where there is no client.

**Why it breaks:** For a technical architecture output, the "decision context" is internal ("we need to pick a data store"). There is no "client." Scoring on "does this serve the client's stated decision context?" for an internal technical question results in confused evaluation. The rubric would potentially penalize a technically excellent output for not being "strategically framed."

**Proposed fix:** Same mechanism as Actionability — add an `engagement_context` placeholder to the evaluator prompts. For internal/technical context, replace "client" with "decision-maker," "strategic framing" with "solution framing," and adapt examples accordingly.

**Priority: HIGH**

---

### Finding 18 — Quantitative Rigor rubric is calibrated for financial data specifically

**File:** `src/keystone/evaluator/prompts/quantitative_rigor.md`

The examples throughout assume financial/market data: "A market size derived from analyst estimates should be '$12-15B' not '$13.7B'" (line 37), "CAGR projections presented as forecasts without stating the assumption set" (line 40), "A claim backed by a well-documented SEC filing" (line 8).

**What's hardcoded:** The concrete examples of quantitative rigor failure are financial. The `precision calibration` sub-criterion gives a financial example. The `adversarial robustness` check (line 30) describes "if a 20% change in an input assumption reverses the conclusion" — which is an appropriate check for market sizing but unusual framing for experimental science.

**Why it breaks:** For a molecular biology paper synthesis, the quantitative claims would be about sample sizes, p-values, effect sizes, and confidence intervals — not market sizes. The rubric evaluator would apply financial-precision intuitions to statistical concepts, potentially scoring incorrectly.

**Proposed fix:** The concrete examples in the prompt should be domain-agnostic or domain-switchable. Replace the "$12-15B" example with: "A quantitative claim should be reported at precision appropriate to its source. A market size derived from analyst estimates should be '$12-15B' not '$13.7B'; a statistical effect size derived from a sample of 40 should be '0.3-0.5' not '0.412'." This preserves the principle while broadening the example.

**Priority: MEDIUM** — the core principle (precision must match data quality) is domain-agnostic; only the examples are consulting-specific.

---

### Finding 19 — Source Quality rubric is calibrated for consulting source types

**File:** `src/keystone/evaluator/prompts/source_quality.md`

The prompt describes source tiers: "Tier 1 (primary data, filings, academic peer-reviewed), Tier 2 (industry reports, analyst coverage, government statistics), Tier 3 (news articles, trade press), Tier 4 (blogs, press releases, social media)."

The recurring example is "A claim backed by a well-documented SEC filing" (line 8). The signal-depth sub-criterion mentions "financial filings" as an exemplar of Tier 1 (line 29).

**What's hardcoded:** "Industry reports" and "analyst coverage" as Tier 2, which are consulting-specific source categories. For academic research, "analyst coverage" means nothing — preprints (arXiv), conference proceedings, and datasets would be Tier 1 alongside peer-reviewed journals.

**Why it breaks:** For a technical/scientific question, the rubric evaluator might underweight strong technical sources (authoritative GitHub repositories, RFC documents, whitepapers from major research labs) that don't fit the consulting tier hierarchy. It might also overweight "industry reports" (e.g., Gartner market research reports) relative to primary technical documentation.

**Proposed fix:** The source tier examples should be domain-switchable. For technical questions: Tier 1 includes RFCs, primary technical documentation, peer-reviewed computer science papers, official benchmarks; Tier 2 includes authoritative technical blogs (ACM, IEEE), reputable conference proceedings, widely-cited whitepapers; Tier 3 includes tech news (TechCrunch, The Verge); Tier 4 includes personal blogs, vendor marketing.

**Priority: MEDIUM**

---

### Finding 20 — QUANTITATIVE_RIGOR receives a high weight regardless of question type

**File:** `src/keystone/models/evaluation.py`, line 68

```python
RUBRIC_WEIGHTS: dict[RubricDimension, float] = {
    RubricDimension.QUANTITATIVE_RIGOR: 0.15,
    RubricDimension.ACTIONABILITY: 0.15,
    ...
}
```

**What's hardcoded:** Quantitative Rigor and Actionability both receive 15% weight in the default rubric. For questions where quantitative claims are not central — literature synthesis, system design, organizational analysis — this weight overemphasizes a dimension that may simply not apply.

The `ESTIMATIVE` weight override increases QUANTITATIVE_RIGOR to 18% and CALIBRATED_CONFIDENCE to 10%, doubling down on the financial-estimation assumption.

**Why it breaks:** A qualitative research synthesis on a technical topic (e.g., "what architectural patterns work best for multi-agent systems?") where the answer involves qualitative trade-offs rather than numerical claims would get penalized on Quantitative Rigor relative to its actual quality. A score of 40 on this dimension (adequate, but few numerical claims) drags the weighted total down by 0.15 × (40-60) = -3 points compared to a consulting market-sizing output where quantitative rigor is genuinely central.

**Proposed fix:** Add a `QUALITATIVE` evaluation profile (joining DEFAULT, ESTIMATIVE, CURRENT, STRATEGIC) with QUANTITATIVE_RIGOR reduced to 0.06 and ANALYTICAL_DEPTH/INTELLECTUAL_HONESTY increased. The engagement classifier should emit `QUALITATIVE` for non-quantitative research types.

**Priority: HIGH** — affects scores for every non-quantitative research question.

---

## Structuring Layer

### Finding 21 — AnalyticalFramework enum is consulting-scoped

**File:** `src/keystone/models/structuring.py`, lines 20–34

```python
class AnalyticalFramework(StrEnum):
    ESTIMATION = "estimation"
    ROOT_CAUSE = "root_cause"
    PORTERS_FIVE_FORCES = "porters_five_forces"
    VALUE_CHAIN = "value_chain"
    LANDSCAPE_MAPPING = "landscape_mapping"
    SCENARIO_PLANNING = "scenario_planning"
    SWOT = "swot"
```

**What's hardcoded:** Seven analytical frameworks, all consulting/business. Porter's Five Forces, Value Chain, SWOT, and Scenario Planning are classic MBA consulting tools. Estimation, Root Cause, and Landscape Mapping are broader but still encoded with consulting context. There is no: Systems Thinking, Design Thinking, MECE-neutral structuring, Literature Review taxonomy, Architecture Decision Record (ADR) framework, or Evidence Grading (e.g., GRADE framework for medical literature).

**Why it breaks:** The `framework_selector.py` maps every `EngagementType` to frameworks from this enum (e.g., EVALUATIVE → Porter's Five Forces mandatory). For a technical architecture evaluation classified as EVALUATIVE, Porter's Five Forces is selected as the primary mandatory framework. The structured outline that L2 produces then has a `FRAMEWORK_ANALYSIS` section stamped with `porters_five_forces` — which is then passed to the Evaluator's rubric scoring as context, rewarding "on-framework reasoning" for Porter's when the question was about software architecture.

**Proposed fix:** Extend the `AnalyticalFramework` enum with: `TECHNICAL_EVALUATION` (for system/architecture questions), `EVIDENCE_SYNTHESIS` (for literature review questions), `DESIGN_PATTERN` (for design questions), `PROCESS_ANALYSIS` (for operational/process design), `ORGANIZATIONAL_ANALYSIS`. Update `_FRAMEWORK_MAP` in `framework_selector.py` to use these for new engagement types. Or — better — make framework selection LLM-driven for non-consulting engagement types, with the `AnalyticalFramework` enum becoming a "registered framework" registry rather than an exhaustive list.

**Priority: CRITICAL** — framework stamping affects both structuring output and Evaluator scoring context.

---

### Finding 22 — Framework selector hardcodes Porter's Five Forces for EVALUATIVE

**File:** `src/keystone/structuring/framework_selector.py`, lines 39–55

```python
EngagementType.EVALUATIVE: [
    FrameworkHint(
        framework=AnalyticalFramework.PORTERS_FIVE_FORCES,
        rationale="Evaluative engagements assess attractiveness and positioning...",
        mandatory=True,
    ),
    FrameworkHint(
        framework=AnalyticalFramework.VALUE_CHAIN,
        rationale="Value chain analysis augments five-forces...",
        mandatory=False,
    ),
],
```

**What's hardcoded:** Porter's Five Forces is mandatory for every EVALUATIVE engagement. An evaluative question about a software architecture, a medical treatment, a hiring decision, or a technology vendor is all routed through Porter's Five Forces as the primary analysis frame.

**Why it breaks:** For the first pipeline run's question ("design an agentic research system"), if classified as EVALUATIVE, the content structurer produces a Five Forces analysis section (Supplier Power of LLM providers, Buyer Power, Threat of Substitutes from alternative approaches, etc.). This is technically possible to construct but analytically wrong — the right frame is a trade-off analysis or an ADR, not competitive positioning.

**Proposed fix:** The `_FRAMEWORK_MAP` should not apply to non-consulting engagement types. The `override` parameter already exists (`framework_selector.py` line 91) as an escape hatch. This override should be exercised whenever the engagement domain is non-business. Longer term, remove mandatory frameworks from hardcoded mappings and move them to LLM-selected recommendations validated against the question.

**Priority: CRITICAL**

---

## Gateway / Tool Registry

### Finding 23 — Tool registry is 100% financial/market sourcing tools

**File:** `src/keystone/gateway/servers.py`, `src/keystone/tool_names.py`

Registered tools:
- `exa_search`, `brave_search` — general web search (domain-agnostic)
- `edgar_filings`, `edgar_financials`, `edgar_company_facts` — SEC financial filings (US companies only)
- `fred_data` — Federal Reserve economic data (macroeconomics only)
- `paper_search` — academic papers (potentially useful broadly)
- `doi_verify` — DOI citation verification (academic)
- `finnhub_market` — real-time stock market data (financial markets only)

**What's hardcoded:** Five of nine tool categories are exclusively financial/market. There is no tool for: technical documentation search (GitHub, StackOverflow, official docs), code repository search, clinical trial databases (ClinicalTrials.gov), legal databases (court filings, statutes), patent search (despite being listed as removed from `academic_researcher` but never replaced), regulatory databases outside SEC, government data beyond FRED.

**Why it breaks:** For a technical question, `paper_search` and the two web search tools are the only useful instruments. EDGAR, FRED, and FINNHUB are completely irrelevant. The system has no specialized tool for technical documentation or code examples.

**Proposed fix:** Add tool categories for common non-consulting research domains: `github_search` (code repositories, technical discussions), `docs_search` (official documentation sites), `patent_search` (Google Patents or equivalent), `clinical_trials_search`, `legal_search`. Mark each tool with a `domain_tags: list[str]` field in `ToolEntry` so the template registry can filter tools by domain relevance before assignment. This does not require implementing all tools immediately — the ToolName enum and ToolEntry registration can be added with `health_status=UNHEALTHY` until servers are implemented.

**Priority: HIGH** — the tool gap means non-financial research always falls back to web search only.

---

### Finding 24 — RetrievalConfig defaults to finance-tuned embedding model

**File:** `src/keystone/models/config.py`, line 101

```python
voyage_model: str = Field(
    default="voyage-finance-2",
    description="Voyage embedding model. Finance-tuned by default.",
)
```

**What's hardcoded:** The retrieval/embedding model defaults to `voyage-finance-2`, which is explicitly tuned for financial content. A finance-tuned embedding model will produce worse semantic similarity scores for technical or scientific documents than a general-purpose model.

**Why it breaks:** Documents retrieved from the internal store for a technical architecture question will be ranked by embeddings trained on financial language. Technical terms and concepts may have incorrect semantic neighbors, leading to retrieval noise. For the first pipeline run, any documents in the knowledge store about technical architecture would be retrieved less accurately.

**Proposed fix:** The default should be a general-purpose embedding model (e.g., `voyage-3` or `voyage-large-2`). `voyage-finance-2` should be selectable per engagement or per document type when the content is financial. Add `voyage_model_technical: str = "voyage-3"` and a domain-to-model mapping in `RetrievalConfig`.

**Priority: MEDIUM** — affects document retrieval quality but not core pipeline logic.

---

## Cross-Cutting: Non-Goals and ResearchSpec Defaults

### Finding 25 — ResearchSpec.non_goals always includes "Political positioning" and "Client relationship management"

**File:** `src/keystone/specification/spec_engine.py`, lines 357–359

```python
non_goals = [
    "Political positioning and recommendation framing",
    "Client relationship management",
]
```

**What's hardcoded:** These two non-goals are hardcoded as the starting list for every engagement, before the intent clarifier's scope boundaries are appended. "Client relationship management" is meaningless for an internal technical question. "Political positioning and recommendation framing" is vague and consulting-specific.

**Why it breaks:** These non-goals appear in the `ResearchSpec`, which is the most important data structure in the system and is read by every agent. Agents reading a non-goal of "Client relationship management" for a technical question get a signal that the engagement has a client — which shapes their framing.

**Proposed fix:** Start with an empty `non_goals` list. Populate non-goals entirely from the intent clarifier's output. The intent clarification prompt should produce domain-appropriate scope boundaries rather than having them hardcoded at the spec_engine level.

**Priority: MEDIUM**

---

### Finding 26 — ResearchSpec.quality_bar is Goldman Sachs-branded

**File:** `src/keystone/models/research.py`, line 140

```python
quality_bar: str = Field(
    default="Goldman-grade: would a domain expert call this solid on its own merits?",
    description="Quality standard for this engagement",
)
```

**What's hardcoded:** The quality bar default uses "Goldman-grade" as a shorthand — a financial industry reference. For a technical architecture question, this is odd phrasing. While "domain expert" is generic, "Goldman-grade" specifically evokes financial industry standards.

**Proposed fix:** Change to `"Expert-grade: would a domain expert call this rigorous and solid on its own merits?"` or make the quality bar LLM-generated at intent clarification time based on the question domain.

**Priority: MEDIUM** — cosmetic but shapes evaluator context.

---

## Summary Table: File-by-File

| File | Findings | Highest Priority |
|---|---|---|
| `specification/decomposer.py:56` | `_LENSES = ["financial", "operational", "market"]` | CRITICAL |
| `specification/prompts/decompose_financial_lens.md` | Full financial-analyst persona | CRITICAL |
| `specification/prompts/decompose_operational_lens.md` | Full operations-consultant persona | CRITICAL |
| `specification/prompts/decompose_market_lens.md` | Full market-consultant persona | CRITICAL |
| `specification/prompts/decompose_synthesis.md` | Hardcoded lens labels and engagement-type mapping | CRITICAL |
| `specification/prompts/classification.md:16–22` | Only consulting examples in taxonomy | HIGH |
| `specification/prompts/intent_clarification.md` | "Senior strategy consultant" persona, "client" framing | HIGH |
| `specification/prompts/task_generation.md:28` | Hardcoded consulting category list | HIGH |
| `specification/spec_engine.py:60–106` | `_DEFAULT_METHODOLOGY`, `_DEFAULT_SOURCES` | CRITICAL |
| `specification/spec_engine.py:357–359` | Hardcoded non-goals | MEDIUM |
| `models/research.py:23–35` | `EngagementType` consulting-scoped enum | CRITICAL |
| `models/research.py:140` | "Goldman-grade" quality bar | MEDIUM |
| `models/tasks.py:16–24` | `TaskCategory` consulting-scoped enum | CRITICAL |
| `models/structuring.py:20–34` | `AnalyticalFramework` consulting-scoped enum | CRITICAL |
| `specification/template_registry.py:33–195` | EDGAR in 5/7 templates, no technical_researcher | CRITICAL |
| `specification/template_registry.py:208–229` | `_CATEGORY_TEMPLATE_MAP` maps only consulting categories | HIGH |
| `tool_names.py:78–82` | `BASELINE_AGENT_TOOLS` interacts badly with EDGAR templates | HIGH |
| `research/research_agent.py` | Financial domain bias in `_SOURCE_TYPE_PATTERNS` | MEDIUM |
| `deliberation/analyst.py:62–88` | `METHODOLOGY_PROMPTS` uses market/regulatory examples | MEDIUM |
| `deliberation/prompts/historical_analogy.md` | Market/regulatory framing in historical analogy prompt | MEDIUM |
| `deliberation/prompts/scenario_planning.md` | Business-futures framing (minor) | MEDIUM |
| `evaluator/prompts/actionability.md` | "Client" / consulting framing throughout | HIGH |
| `evaluator/prompts/intent_alignment.md` | "Client" / "strategic framing" throughout | HIGH |
| `evaluator/prompts/quantitative_rigor.md` | Financial examples ($12-15B, CAGR, SEC filings) | MEDIUM |
| `evaluator/prompts/source_quality.md` | Industry reports tier, "analyst coverage" framing | MEDIUM |
| `evaluator/rubric_config.py:64–70` | `ENGAGEMENT_PROFILE_MAP` routes to 4 profiles, no qualitative | HIGH |
| `models/evaluation.py:66–110` | Default weights: QUANTITATIVE_RIGOR 15%, no QUALITATIVE profile | HIGH |
| `structuring/framework_selector.py:18–85` | Porter's Five Forces mandatory for EVALUATIVE | CRITICAL |
| `gateway/servers.py` | 5/9 tools are financial-only | HIGH |
| `models/config.py:101` | `voyage-finance-2` embedding model default | MEDIUM |
| `models/config.py:399–405` | `l1_orchestrator_categories` defaults to consulting categories | MEDIUM |

---

## Recommended Fix Order

### Immediate (block non-consulting use)

1. **Extend `EngagementType`** with non-consulting types (DESIGN, SYNTHESIS, BUILD_EVALUATE, ORGANIZATIONAL, POLICY_ANALYSIS). Update classifier prompt with diverse examples.
2. **Extend `TaskCategory`** with non-consulting categories (LITERATURE_SYNTHESIS, SYSTEM_DESIGN, PROCESS_ANALYSIS, ORGANIZATIONAL_ANALYSIS). Update task_generation.md prompt.
3. **Make decomposition lenses dynamic** — replace `_LENSES` constant with a lens-selection step driven by engagement type and question domain.
4. **Remove EDGAR from `generalist_researcher` and `academic_researcher` templates.** Add `technical_researcher` template.
5. **Extend `AnalyticalFramework` enum** and fix `_FRAMEWORK_MAP` to not apply Porter's Five Forces to non-business engagement types.

### Near-term (quality-degrading)

6. **Replace `_DEFAULT_METHODOLOGY` and `_DEFAULT_SOURCES`** with LLM-selected values based on question domain.
7. **Add `engagement_context` placeholder to evaluator prompts** (actionability.md, intent_alignment.md) to parameterize "client" vs "internal/technical" framing.
8. **Add `QUALITATIVE` evaluation profile** with reduced QUANTITATIVE_RIGOR weight for non-quantitative research types.
9. **Update intent clarification prompt** to drop consulting-persona framing.

### Cleanup (suboptimal but low urgency)

10. Update `voyage_model` default to general-purpose model.
11. Fix hardcoded non-goals in spec_engine.py.
12. Update historical_analogy.md and scenario_planning.md to use domain-neutral examples.
13. Change "Goldman-grade" quality bar default.
14. Update `l1_orchestrator_categories` defaults.

---

*End of audit. 26 findings across 30+ files.*
