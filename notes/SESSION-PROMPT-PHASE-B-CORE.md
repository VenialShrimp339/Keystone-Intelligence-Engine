# Session Prompt: Phase B-core — L0 Generalization (One-Size-Fits-All Fix)

## Orchestrator Disclosure

This prompt was written by an orchestrator session (Opus, 1M context) that read project tracking documents (`TODO.md`, `HANDOVER.md`, `SYNTHESIS-AND-PRIORITIES.md`, all four analysis files in `notes/analysis/`), key source files (`decomposer.py`, `task_generator.py`, `spec_engine.py`, `template_registry.py`, `orchestrator.py`, `evaluator.py`, `llm_client.py`, `config.py`), prompts (`task_generation.md`, `classification.md`, `actionability.md`), models (`research.py`, `tasks.py`), and the test scripts in `scripts/`. **The orchestrator did NOT read every file you will need to touch.** You will need to read the full implementation of files before modifying them — especially the prompt `.md` files, the evaluator rubric prompts, and the framework selector.

**If you discover information that changes the plan** — a dependency the orchestrator missed, a file that's structured differently than assumed, an adjacent fix that's necessary to make the planned change work, or a better approach — **you are authorized to diverge from this plan.** However, you MUST:

1. Document every divergence in your final output under a `## Plan Divergences` section
2. For each divergence, state: what the plan said, what you did instead, and why
3. If you discover work that's related but out of scope, note it under `## Discovered Work` rather than doing it

---

## Context

This is the Keystone Intelligence Engine — a multi-agent consulting research pipeline. The L0 Specification Engine takes a research question and decomposes it into typed, prioritized research tasks for L1 agents.

**The core problem:** L0 was built with consulting-engagement defaults hardcoded everywhere. When given a non-business question (e.g., "how should we architect an agentic research system"), it:
- Decomposes through financial/operational/market lenses (nonsensical for technical questions)
- Classifies into consulting engagement types (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC) — none fit technical/design questions
- Assigns task categories like MARKET_SIZING and FINANCIAL_ANALYSIS — no category exists for "prior art survey" or "architecture design"
- Routes to agent templates that include EDGAR (SEC filings) tools for non-financial research
- Applies Porter's Five Forces as mandatory framework for EVALUATIVE engagements
- Injects "news" and "industry reports" as default source requirements regardless of domain

**Evidence:** The first pipeline run (April 22, 2026) applied financial analysis lenses to a question about software architecture. The detailed audit is at `notes/analysis/one-size-fits-all-audit.md` (26 findings across 30+ files). The L0 quality analysis is at `notes/analysis/l0-specification-quality.md`.

**Branch:** `codex/owner-triage-normalization`
**Tests:** 1506 passing, 0 failing
**Parallel session:** A Phase A session is running concurrently on a worktree doing infrastructure work (chunking fixes, process visibility). It touches `task_generator.py` (chunking logic only), `layer1_deterministic.py`, and `orchestrator.py` (file writes). **Your work should NOT touch those files.** If you need orchestrator changes, document them under `## Discovered Work`.

## Your Tasks

### Task 1: Expand `EngagementType` enum

**File:** `src/keystone/models/research.py`

**Current state (lines 23-35):**
```python
class EngagementType(StrEnum):
    SIZING = "sizing"
    DIAGNOSTIC = "diagnostic"
    EVALUATIVE = "evaluative"
    EXPLORATORY = "exploratory"
    STRATEGIC = "strategic"
```

**Add these types:**
- `DESIGN = "design"` — How should X be built, structured, or organized. Example: "How should we architect this system?"
- `SYNTHESIS = "synthesis"` — Aggregate and integrate findings from multiple sources. Example: "What does the literature say about transformer scaling laws?"
- `TECHNICAL_EVALUATION = "technical_evaluation"` — Assess technical merits of a technology or approach. Example: "Evaluate whether GraphRAG is appropriate for our use case"
- `COMPARATIVE = "comparative"` — Head-to-head comparison of approaches, frameworks, or vendors. Example: "Compare LangGraph vs CrewAI for our pipeline"

**Cascade updates required** (read each file to understand the exact structure before modifying):

1. **`src/keystone/specification/prompts/classification.md`** — Add the new types with descriptions and examples to the Classification Taxonomy section. Add at least one non-consulting example per existing type too (e.g., for EXPLORATORY: "What approaches exist for LLM evaluation in production systems?"). Update the Five Classification Signals section to include non-consulting analytical frameworks alongside Porter's Five Forces and TAM/SAM/SOM (e.g., "Architecture Decision Records, systematic literature review, technology readiness levels").

2. **`src/keystone/specification/engagement_classifier.py`** — Read this file. It likely has a `_DEFAULT_PROFILES` mapping from EngagementType to PipelineProfile. Add entries for the new types:
   - DESIGN → DEEP (design questions are complex, need multiple research streams)
   - SYNTHESIS → STANDARD (literature synthesis is bounded)
   - TECHNICAL_EVALUATION → STANDARD (focused evaluation)
   - COMPARATIVE → STANDARD (bounded comparison)

3. **`src/keystone/evaluator/rubric_config.py`** — Read this file. It has `ENGAGEMENT_PROFILE_MAP` mapping EngagementType to EvaluationProfile. Add entries for the new types. DESIGN and TECHNICAL_EVALUATION should map to a profile that de-emphasizes QUANTITATIVE_RIGOR relative to ANALYTICAL_DEPTH. If no suitable profile exists, either reuse DEFAULT or note the need for a new QUALITATIVE profile under `## Discovered Work`.

4. **`src/keystone/specification/template_registry.py`** — The `_engagement_type_fit()` method (around line 307) has a hardcoded dict mapping each EngagementType to per-template fit scores. Add entries for the four new types. For DESIGN and TECHNICAL_EVALUATION: `academic_researcher` and `generalist_researcher` should score high (0.8-1.0), `quantitative_analyst` and `market_researcher` should score low (0.2-0.3). For SYNTHESIS: `academic_researcher` high. For COMPARATIVE: `generalist_researcher` and `academic_researcher` high.

### Task 2: Expand `TaskCategory` enum

**File:** `src/keystone/models/tasks.py`

**Current state (lines 16-24):**
```python
class TaskCategory(StrEnum):
    MARKET_SIZING = "market_sizing"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    FINANCIAL_ANALYSIS = "financial_analysis"
    TECHNOLOGY_ASSESSMENT = "technology_assessment"
    REGULATORY = "regulatory"
    STRATEGIC_POSITIONING = "strategic_positioning"
```

**Add these categories:**
- `PRIOR_ART_SURVEY = "prior_art_survey"` — Survey existing systems, papers, approaches
- `ARCHITECTURE_DESIGN = "architecture_design"` — System design, component selection, interface definition
- `EVALUATION_METHODOLOGY = "evaluation_methodology"` — Design or assess evaluation frameworks
- `QUALITY_STANDARDS = "quality_standards"` — Research quality bars, standards, best practices
- `LITERATURE_REVIEW = "literature_review"` — Academic/technical literature synthesis
- `PROCESS_ANALYSIS = "process_analysis"` — Workflow, methodology, process design

**Cascade updates required:**

1. **`src/keystone/specification/prompts/task_generation.md`** — The prompt currently hardcodes the category list on line 28: `"Category: One of: market_sizing, competitive_landscape, financial_analysis, technology_assessment, regulatory, strategic_positioning."` This MUST be updated to include the new categories. Better: change it to use the `{{available_categories}}` placeholder pattern, and have `task_generator.py` inject the full category list dynamically. Read `task_generator.py` to see how the prompt is built (the `load_prompt()` call in `generate()`).

2. **`src/keystone/specification/template_registry.py`** — Update `_CATEGORY_TEMPLATE_MAP` (around line 208) to map the new categories to appropriate templates:
   - `PRIOR_ART_SURVEY` → `academic_researcher` (or the new `technical_researcher` from Task 3)
   - `ARCHITECTURE_DESIGN` → new `technical_researcher` template
   - `EVALUATION_METHODOLOGY` → `academic_researcher`
   - `QUALITY_STANDARDS` → `generalist_researcher`
   - `LITERATURE_REVIEW` → `academic_researcher`
   - `PROCESS_ANALYSIS` → `generalist_researcher`

3. **`src/keystone/specification/template_registry.py`** — Update `_SOURCE_TEMPLATE_AFFINITY` (around line 218) to add source-type affinities for the new research domains:
   - `"technical_documentation"` → `technical_researcher`
   - `"github_repositories"` → `technical_researcher`
   - `"conference_proceedings"` → `academic_researcher`

4. **`src/keystone/specification/task_generator.py`** — The `_resolve_category()` method (line 195) defaults unknown categories to `STRATEGIC_POSITIONING`. Change the fallback to use `custom_category` if provided by the LLM, and only default to `STRATEGIC_POSITIONING` if neither the enum value nor `custom_category` is usable. Also ensure the LLM is told about `custom_category` as an option in the prompt.

### Task 3: Add `technical_researcher` template, clean up EDGAR

**File:** `src/keystone/specification/template_registry.py`

**Add a new template** (alongside the existing `_QUANTITATIVE_ANALYST`, `_MARKET_RESEARCHER`, etc.):

```python
_TECHNICAL_RESEARCHER = AgentDefinition(
    name="technical_researcher",
    description="Technical architecture evaluation, system design, prior art survey, and implementation assessment",
    role=AgentRole.RESEARCH,
    model=ModelTier.STANDARD,
    tools=[
        ToolName.PAPER_SEARCH,
        ToolName.DOI_VERIFY,
        ToolName.EXA_SEARCH,
        ToolName.BRAVE_SEARCH,
    ],
    system_prompt=(
        "You are a technical research analyst. Your methodology prioritizes "
        "primary technical sources: official documentation, peer-reviewed papers, "
        "reference implementations, and benchmark results. Evaluate architectural "
        "trade-offs rigorously — name what you gain and what you give up with each "
        "design choice. Distinguish between proven patterns and speculative claims. "
        "When assessing systems, check maintenance trajectory (recent commits, "
        "community health) alongside technical merit."
    ),
    source="builtin",
    research_type=ResearchAgentType.QUALITATIVE,
)
```

**Add to `_SEED_TEMPLATES` list.**

**Remove EDGAR from non-financial templates:**
- `_ACADEMIC_RESEARCHER` (line ~90): Remove `ToolName.EDGAR_FILINGS` from tools list
- `_GENERALIST` (line ~138): Remove `ToolName.EDGAR_FILINGS` and `ToolName.FINNHUB_MARKET` from tools list
- `_CONTRARIAN_ANALYST` (line ~156): Remove `ToolName.EDGAR_FILINGS` and `ToolName.FINNHUB_MARKET`
- `_HISTORICAL_ANALYST` (line ~178): Remove `ToolName.EDGAR_FILINGS` and `ToolName.FINNHUB_MARKET`
- Keep EDGAR in `_QUANTITATIVE_ANALYST`, `_MARKET_RESEARCHER`, and `_REGULATORY_ANALYST` — those are financial/market templates where EDGAR belongs

**Note:** Read the tool lists carefully before removing. The orchestrator read these files but line numbers may have shifted.

### Task 4: Fix `_DEFAULT_METHODOLOGY` and `_DEFAULT_SOURCES`

**File:** `src/keystone/specification/spec_engine.py`

**Problem 1:** `_DEFAULT_METHODOLOGY` (lines 60-101) maps every EngagementType to consulting frameworks. Porter's Five Forces is assigned to EVALUATIVE and STRATEGIC. For the new non-consulting types, this is wrong.

**Fix:** Add entries for the new EngagementTypes with domain-appropriate methodology:
- `DESIGN` → `MethodologyRequirement(framework="Trade-off Analysis", mandatory=True, rationale="Design engagements require systematic evaluation of alternatives")`
- `SYNTHESIS` → `MethodologyRequirement(framework="Systematic Review", mandatory=True, rationale="Literature synthesis requires structured evidence aggregation")`
- `TECHNICAL_EVALUATION` → `MethodologyRequirement(framework="Evaluation Framework", mandatory=True, rationale="Technical evaluation requires structured criteria assessment")`
- `COMPARATIVE` → `MethodologyRequirement(framework="Comparative Analysis", mandatory=True, rationale="Comparison requires consistent criteria across alternatives")`

**Problem 2:** `_DEFAULT_SOURCES` (lines 103-106) hardcodes `news` (min 5) and `industry_reports` (min 2) for ALL engagements. These are irrelevant for technical or academic research.

**Fix:** Make `_DEFAULT_SOURCES` engagement-type-aware. Create a `_SOURCES_BY_TYPE` dict:
- Existing business types (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC): keep current defaults
- DESIGN, TECHNICAL_EVALUATION, COMPARATIVE: `[SourceRequirement(source_type="technical_documentation", minimum_count=3, quality_threshold=0.7), SourceRequirement(source_type="academic", minimum_count=2, quality_threshold=0.7)]`
- SYNTHESIS, LITERATURE_REVIEW-related: `[SourceRequirement(source_type="academic", minimum_count=5, quality_threshold=0.7)]`

Update `_build_research_spec()` to look up sources by engagement type instead of using the flat `_DEFAULT_SOURCES`.

### Task 5: Fix hardcoded non-goals and quality bar

**File:** `src/keystone/specification/spec_engine.py` (lines 356-359)

**Problem:** `non_goals` always starts with `["Political positioning and recommendation framing", "Client relationship management"]`. These are meaningless for non-consulting questions.

**Fix:** Start with an empty list. Only add these two for business engagement types (SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC). For non-business types, start empty and let scope boundaries from the intent clarifier populate the list.

**File:** `src/keystone/models/research.py` (around line 140)

**Problem:** `quality_bar` defaults to `"Goldman-grade: would a domain expert call this solid on its own merits?"`

**Fix:** Change to `"Expert-grade: would a domain expert call this rigorous and well-sourced on its own merits?"`

### Task 6: Update the framework selector for new types

**File:** `src/keystone/structuring/framework_selector.py`

**Problem:** The `_FRAMEWORK_MAP` maps EngagementType to `FrameworkHint` lists. EVALUATIVE maps to Porter's Five Forces (mandatory). The new types have no entries, so they'd fall through to whatever default exists.

**Fix:** Read the file first. Add entries for the new EngagementTypes:
- DESIGN → framework appropriate for design work (not Porter's Five Forces). If `AnalyticalFramework` enum doesn't have a suitable value, add one (e.g., `TRADE_OFF_ANALYSIS = "trade_off_analysis"`) to `src/keystone/models/structuring.py`
- SYNTHESIS → `LANDSCAPE_MAPPING` (already exists, reasonable fit)
- TECHNICAL_EVALUATION → a new `EVALUATION_FRAMEWORK = "evaluation_framework"` or similar
- COMPARATIVE → `LANDSCAPE_MAPPING` or a new `COMPARATIVE_ANALYSIS`

Also: ensure that Porter's Five Forces is NOT mandatory for non-business engagement types. If the framework selector applies it broadly, constrain it.

### Task 7: Validate

1. Run `ruff format` on all changed files
2. Run `pytest tests/unit/ -x --tb=short` — all 1506+ tests must pass (likely more with new tests)
3. Run `ruff check src/ tests/`
4. Commit all changes with descriptive commit message(s)

**Tests to add:**
- Verify `EngagementType("design")` and the other new values work
- Verify `TaskCategory("prior_art_survey")` and the other new values work
- Verify `_CATEGORY_TEMPLATE_MAP` has entries for all `TaskCategory` members
- Verify `_engagement_type_fit()` has entries for all `EngagementType` members
- Verify `_DEFAULT_METHODOLOGY` has entries for all `EngagementType` members (or the lookup handles missing gracefully)
- Verify the `technical_researcher` template exists and has no EDGAR tools
- Verify that `academic_researcher` and `generalist_researcher` templates no longer include EDGAR
- Verify `_resolve_category()` falls back gracefully for unknown category strings

## What NOT to do

- Do NOT touch `decomposer.py` — dynamic lens selection is a separate, later session. The hardcoded `_LENSES` stays for now.
- Do NOT touch `orchestrator.py` — the Phase A session is modifying it concurrently for process visibility
- Do NOT touch `task_generator.py` beyond the `_resolve_category` fallback fix and prompt template changes — Phase A is adding chunking logic to it. If both the prompt template and chunking need changes, limit your changes to the prompt content and the `_resolve_category` method. Do NOT change the `generate()` method's control flow.
- Do NOT rewrite evaluator rubric prompts (`actionability.md`, `intent_alignment.md`, etc.) — that's a separate session for domain-adaptive evaluator prompts
- Do NOT rewrite the deliberation analyst type system — that's Phase C work
- Do NOT modify `intent_clarification.md` — interactive clarification is Phase C

## Expected Output

When you're done, provide:
1. Summary of what was implemented
2. Test results (count passing)
3. Files changed with a one-line description of each change
4. `## Plan Divergences` — any places you deviated from this plan and why
5. `## Discovered Work` — any related issues you found that should be addressed in future sessions
