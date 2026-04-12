# Wave 4 Template / Routing Research

*Date: 2026-04-12 | Scope: C-6, C-8, C-10, C-14 | Purpose: freeze the routing and template-content contracts that can later land without silently widening the specification seams*

---

## Purpose

This memo covers the Wave 4 research tranche for:

- `C-6`: classification borderline tiebreaker
- `C-8`: task-generation tool-selection guidance
- `C-10`: dynamic lens selection for non-standard engagements
- `C-14`: template archetype redesign

The goal is not to patch the routing code yet.
The goal is to define the accepted routing rules, tool-selection heuristics, lens-registry concept, template-enrichment boundary, and explicit deferrals so Wave 4B does not mix prompt polish with new specification capability.

## Accepted Boundary

- Baseline runtime: cleared Wave 3B commit `5cc9585`
- Current live routing seams still show these constraints:
  - `EngagementClassifier` returns only `engagement_type`, `pipeline_profile`, `confidence`, and `reasoning`
  - `TaskGenerator` exposes a fixed registered tool list but no explicit selection heuristics
  - `Decomposer` hardcodes `_LENSES = ["financial", "operational", "market"]`
  - `TemplateRegistry` matches by task category, required sources, and single-axis engagement type
- The architectural direction is already settled:
  - analytical type and domain/workstream should not be collapsed into one label
  - framework metadata should inform retrieval and enrichment, not become a brittle routing table
- This memo does **not** authorize:
  - new taxonomy invention beyond the accepted dual-axis target
  - ad hoc engagement-type proliferation like `m_and_a` or `restructuring` as replacements for the analytical axis
  - a dynamic lens registry going live without an explicit controller checkpoint
  - auto-generated template expansion beyond the current parent-template tool and model envelope

Any recommendation that requires new persisted classifier fields, dynamic prompt-registry infrastructure, or a new custom-template generation layer must be labeled `new capability` and kept out of Wave 4B.

## Runtime Consumer Summary

| Item | Observed problem | Runtime consumer | Recommended classification | Dependency note |
|---|---|---|---|---|
| `C-6` | Borderline engagements have no explicit tiebreaker and the current classifier cannot represent domain plus runner-up analytical modes | `src/keystone/specification/prompts/classification.md`, `src/keystone/specification/engagement_classifier.py`, future dual-axis classifier fields | `new capability` until the accepted dual-axis classifier surface is real; then `existing-seam code` | Do not force dual-axis semantics into the current single-axis runtime by prompt wording alone |
| `C-8` | Task generation prompt names the registered tools but gives no selection heuristics | `src/keystone/specification/prompts/task_generation.md`, `src/keystone/specification/task_generator.py`, `src/keystone/tool_names.py` | `content-only` | Safe now because it can stay inside the existing prompt contract and registered tool set |
| `C-10` | Decomposition lens selection is hardcoded to three fixed lenses | `src/keystone/specification/decomposer.py`, future lens prompt registry | `new capability` | Requires a real registry / selector surface, not just revised wording |
| `C-14` | Template registry stays shallow, methodology prompts are underspecified, and low-fit tasks silently collapse toward generic fallback behavior | `src/keystone/specification/template_registry.py`, `src/keystone/specification/task_generator.py` | `existing-seam code` for template enrichment inside current archetypes; `new capability` for custom-template expansion below the current seam | Safe only if template enrichment stays inside the existing template/tool/model envelope |

## Routing Rules Aligned To The Accepted Dual-Axis Target

These routing rules are the global contract for this memo:

| Routing surface | Accepted rule |
|---|---|
| Classification | Separate analytical type from domain/workstream. Analytical type answers "what kind of reasoning is primary?"; domain answers "what business problem space is this?" |
| Borderline cases | Choose the primary analytical type by dominant end product, not by industry label or transaction label |
| Mixed engagements | Preserve runner-up analytical modes as secondary metadata once the classifier surface supports it; do not force them into ad hoc new primary types |
| Tool selection | Pick tools by task category, evidence burden, and data modality, not by a fixed default trio |
| Decomposition lenses | Choose 3 lenses by default and 4 only when a distinct additional risk surface exists; do not exceed 4 |
| Template matching | Keep methodology archetypes as the base, then enrich by problem characteristics and domain context; do not create one template per engagement label |

## C-6: Classification Borderline Tiebreaker

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-6`
- Governing overlay: `audit/remediation/round-3/PLANNING-ADDENDUM.md` `D-1`
- Live prompt surface: `src/keystone/specification/prompts/classification.md`
- Live code surface: `src/keystone/specification/engagement_classifier.py`

Current state:

- the classifier asks for exactly one `engagement_type`
- the prompt lists five signals but gives no precedence among them
- the response schema cannot represent:
  - domain/workstream category
  - secondary analytical modes
  - a borderline explanation that becomes load-bearing downstream

So borderline engagements either collapse to one label by undocumented intuition or they encourage future prompt drift toward ad hoc category invention.

### Accepted boundary

- The analytical axis stays the existing five-type set:
  - `sizing`
  - `diagnostic`
  - `evaluative`
  - `exploratory`
  - `strategic`
- Domain/workstream is a separate concern from analytical type.
- `M&A`, `restructuring`, `operations`, and similar labels belong on the domain side, not as replacements for the analytical axis.
- The 4B-ready docs contract may define the tiebreaker now, but it must **not** pretend the current single-axis classifier can already persist the full dual-axis result.

### Recommended contract

Borderline cases should be resolved by **dominant end product first**.

Primary analytical-type decision table:

| Dominant requested end product | Primary analytical type |
|---|---|
| Numeric estimate, range, forecast, or sensitivity-backed magnitude judgment | `sizing` |
| Root-cause explanation of an observed delta, failure, or outcome | `diagnostic` |
| Verdict on a named company, asset, strategy, option, or claim | `evaluative` |
| Structured landscape map without a governing thesis or explicit verdict | `exploratory` |
| Multi-variable go/no-go or scenario tradeoff where no narrower deliverable dominates | `strategic` |

Tiebreaker rules:

1. Use the narrowest analytical mode that fully explains the requested deliverable.
   `strategic` is the umbrella mode of last resort, not the default for every high-stakes question.
2. If a question is framed as "Should we...?" but the first-class work product is still a numeric estimate or root-cause diagnosis, keep the narrower mode primary and treat the broader decision frame as secondary metadata once the classifier surface supports it.
3. Domain/workstream should never override the analytical axis.
   An M&A diligence question may still be primarily `evaluative` or `strategic`; a restructuring question may still be `diagnostic`.
4. If two analytical modes remain genuinely tied after the end-product rule, prefer the mode with the more falsifiable success criterion:
   - `sizing` over `evaluative`
   - `diagnostic` over `strategic`
   - `evaluative` over `exploratory`

### Negative example

Bad implementation:

- labeling every acquisition, turnaround, or board decision as `strategic` regardless of the actual deliverable
- creating `m_and_a` or `restructuring` as new primary engagement types to dodge the dual-axis model
- using company or sector labels to choose analytical type
- baking a tie rule into the prompt while the runtime still lacks any place to store the runner-up analytical mode

### Regression test ideas

- `tests/unit/specification/test_engagement_classifier.py::test_borderline_should_we_question_prefers_narrower_end_product_type`
- `tests/unit/specification/test_engagement_classifier.py::test_named_company_assessment_stays_evaluative_not_exploratory`
- future dual-axis test: `tests/unit/specification/test_engagement_classifier.py::test_runner_up_mode_is_preserved_in_secondary_types`

## C-8: Task-Generation Tool-Selection Guidance

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-8`
- Live prompt surface: `src/keystone/specification/prompts/task_generation.md`
- Live code surface: `src/keystone/specification/task_generator.py`
- Registered tool surface: `src/keystone/tool_names.py`

Current state:

- the task-generation prompt lists the valid tools
- it does **not** explain when to use which tool
- `_resolve_tools()` accepts any registered 3-5 tools, then falls back to template tools if the set is invalid
- regulatory and technology-heavy tasks are especially vulnerable to filler assignments or invented tool names if the prompt is not explicit

### Accepted boundary

- Only the registered tool set is in scope:
  - `exa_search`
  - `brave_search`
  - `edgar_filings`
  - `fred_data`
  - `finnhub_market`
  - `paper_search`
  - `doi_verify`
- The 4B-ready slice should improve prompt guidance, not invent missing MCP servers.
- If the available tool set has a gap, the prompt should admit that limitation rather than hallucinating a nonexistent tool.

### Recommended contract

The task-generation prompt should include a tool-selection heuristic table like this:

| Task category | Preferred tools | Supporting tools | Notes |
|---|---|---|---|
| `market_sizing` | `fred_data`, `edgar_filings`, `finnhub_market` | `exa_search`, `brave_search` | Use search for corroboration and market-definition context; use `paper_search` only when the sizing method or adoption curve is research-heavy |
| `competitive_landscape` | `exa_search`, `brave_search`, `edgar_filings`, `finnhub_market` | `paper_search` | Use `paper_search` only for technical moats or scientific differentiation, not generic competitor scans |
| `financial_analysis` | `edgar_filings`, `finnhub_market`, `fred_data` | `exa_search`, `brave_search` | Prefer structured market or filings data over generic web search when public-company evidence exists |
| `technology_assessment` | `paper_search`, `doi_verify`, `exa_search` | `brave_search`, `edgar_filings` | `doi_verify` should accompany academic-source use, not appear as a standalone filler tool |
| `regulatory` | `exa_search`, `brave_search`, `edgar_filings` | `paper_search`, `fred_data` | No dedicated government/regulatory MCP exists now; say that in the reasoning rather than invent a fake tool |
| `strategic_positioning` | `exa_search`, `brave_search` plus the most relevant structured source tool for the branch | `paper_search`, `finnhub_market`, `edgar_filings`, `fred_data` | Choose tools by the branch's evidence burden, not by a static default trio |

Tool-specific rules:

- use `edgar_filings` when public-company filings, investor materials, or disclosed segment data are likely to matter
- use `finnhub_market` for public-market fundamentals, price behavior, and comparable-company context
- use `fred_data` for macro, industry-cycle, or time-series questions, not company-specific tasks
- use `paper_search` when the claim depends on scientific, technical, or academic evidence
- use `doi_verify` only alongside likely DOI-bearing academic sources
- use both `exa_search` and `brave_search` when broad web discovery plus corroboration is valuable

### Negative example

Bad implementation:

- assigning the same three default search tools to nearly every task
- using `doi_verify` on a pure competitor or pricing scan with no academic evidence burden
- inventing tools like `government_data_api` or `news_search`
- assigning `fred_data` to an entity-specific diligence task just to satisfy the 3-tool minimum

### Regression test ideas

- `tests/unit/specification/test_task_generator.py::test_task_generation_prompt_includes_tool_selection_heuristics`
- `tests/unit/specification/test_task_generator.py::test_regulatory_tasks_do_not_invent_unregistered_tools`
- `tests/unit/specification/test_task_generator.py::test_doi_verify_is_not_used_as_generic_filler`
- `tests/unit/specification/test_task_generator.py::test_macro_tasks_can_select_fred_data`

## C-10: Dynamic Lens Selection For Non-Standard Engagements

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-10`
- Research anchors:
  - `research/synthesis/batch-2/analysis-03-mece-issue-trees.md`
  - `research/synthesis/batch-2/analysis-05-engagement-taxonomy.md`
- Live code surface: `src/keystone/specification/decomposer.py`

Current state:

- `_LENSES` is hardcoded to `["financial", "operational", "market"]`
- the live prompt set assumes those three lenses always apply
- non-standard engagements have no path to request a regulatory, technology, organization, customer, or risk lens even when those are clearly first-class problem structures

### Accepted boundary

- Preserve the current decomposition architecture:
  - independent parallel lens runs
  - synthesis after the parallel runs
- Default to 3 lenses and allow a 4th only when the engagement exposes a distinct additional risk surface.
- Do **not** exceed 4 lenses.
- Do **not** reopen C-4.
  C-4 improves how the current fixed lenses use engagement context; C-10 is about selecting different lenses in the first place.

### Recommended contract

Freeze the future lens registry concept as:

| Lens | When it is primary | Typical question shape |
|---|---|---|
| `financial` | unit economics, valuation, margin, cost, capital, or sizing burden dominates | "What is the size, cost, return, or financial tradeoff?" |
| `operational` | throughput, process, bottleneck, sequencing, or implementation burden dominates | "Where does execution break or scale?" |
| `market` | competitive structure, substitutes, share, or external industry forces dominate | "How is the external arena structured?" |
| `customer` | demand, segment behavior, willingness to pay, adoption, or channel dynamics dominate | "Who chooses, why do they buy, and how does that behavior segment?" |
| `technology` | product feasibility, technical differentiation, roadmap, IP, or readiness dominate | "Does the technology work, scale, or differentiate?" |
| `regulatory` | jurisdictional rules, approvals, compliance burdens, or policy timelines dominate | "What rules constrain or enable the decision?" |
| `organization` | capability, talent, incentives, or operating-model fit dominates | "Can this organization actually execute?" |
| `risk` | downside cases, fragility, scenario spread, or dependency chains dominate | "What breaks this conclusion or decision?" |

Selection rules:

1. Choose 3 lenses by default.
2. Choose a 4th only when it surfaces a materially distinct question class:
   - regulatory burden
   - technology feasibility
   - organizational capability
   - scenario/risk spread
3. Avoid redundant pairs unless the question explicitly needs both.
   Example: `market` plus `customer` is justified for adoption or segmentation work, but not for every standard competitive landscape.
4. Select lenses by problem structure, not by engagement label alone.

Illustrative mappings:

| Problem pattern | Recommended lenses |
|---|---|
| Market entry with regulatory friction | `market`, `customer`, `operational`, `regulatory` |
| Technology diligence for an acquisition | `technology`, `financial`, `market`, `regulatory` |
| Restructuring / turnaround | `financial`, `operational`, `organization`, `risk` |
| Network expansion / site selection | `financial`, `market`, `operational`, `customer` |

### Negative example

Bad implementation:

- using the same 4-lens set for every "complex" question
- selecting 5 or more lenses because more feels safer
- swapping in a new lens based only on sector words instead of the branch structure of the problem
- treating the existing three-lens prompt files as if they already constitute a dynamic registry

### Regression test ideas

- future capability test: `tests/unit/specification/test_decomposer.py::test_nonstandard_engagement_can_request_regulatory_lens`
- future capability test: `tests/unit/specification/test_decomposer.py::test_dynamic_lens_selection_caps_at_four`
- future capability test: `tests/unit/specification/test_decomposer.py::test_dynamic_selector_avoids_redundant_lenses`

## C-14: Template Archetype Redesign

### Observed problem

- Source artifact: `audit/remediation/round-3/CONTENT-SYNTHESIS-v2.md` `C-14`
- Related runtime failure: `CX-3` custom-category collapse
- Live surfaces:
  - `src/keystone/specification/template_registry.py`
  - `src/keystone/specification/task_generator.py`

Current state:

- templates are methodology archetypes with short 3-4 sentence system prompts
- `TemplateRegistry.match()` keys off enum category, required sources, and single-axis engagement type
- `TaskGenerator._resolve_category()` silently maps unknown categories to `strategic_positioning`
- `custom_category` survives on `ResearchTask` but does not participate in template matching
- the tighten-only invariant is documented, but there is no bounded content-enrichment escape hatch for low-fit cases

### Accepted boundary

- Keep methodology archetypes as the base templates.
- Do **not** reorganize the system around one template per engagement label.
- Framework-to-engagement mappings should remain metadata for enrichment and retrieval, not become a brittle direct routing table.
- Any low-fit handling that expands tools or model tier beyond the parent template is `new capability` and out of scope for Wave 4B.

### Recommended contract

The 4B-ready slice is **template enrichment**, not template replacement.

Required enrichment blueprint:

| Template | Add this content | Require these outputs | Guard against these failure modes |
|---|---|---|---|
| `quantitative_analyst` | denominator discipline, sensitivity thinking, assumption transparency, range-first framing | assumptions table, scenario or sensitivity band, explicit data-quality caveat | false precision, denominator drift, unqualified extrapolation |
| `market_researcher` | segmentation logic, competitor-map discipline, substitute awareness, share-estimate triangulation | segment cuts, competitor comparison, market-structure summary | generic trend summary, no segment logic, no competitor implications |
| `regulatory_analyst` | enacted vs. proposed distinction, jurisdiction splits, timeline discipline, compliance trigger points | jurisdiction matrix, timeline, decision-trigger summary | law-vs-rumor conflation, missing jurisdiction qualifier |
| `generalist_researcher` | cross-domain synthesis rules, when to escalate to a specialized template, hypothesis-framing discipline | scoped synthesis with explicit gaps, escalation note when specialization is missing | shallow breadth with no decision relevance |

Controlled low-fit rule:

1. If a task-template match is strong, keep the tighten-only invariant.
2. If similarity is weak, the current runtime should prefer an explicit `custom` / bounded fallback path over a silent collapse to generic strategic-positioning behavior.
3. Until a real custom-template generation seam exists, "escape hatch" means:
   - keep the parent template's tool/model envelope
   - enrich prompt content or task requirements only
   - surface the low-fit condition explicitly in metadata or reasoning

### Negative example

Bad implementation:

- creating separate templates for every domain label instead of enriching the methodology archetypes
- silently routing unknown categories through `strategic_positioning` with no trace of the mismatch
- relaxing tighten-only by adding more tools or a stronger model tier below the controller's boundary
- copying framework names into prompts without turning them into output expectations or failure-mode checks

### Regression test ideas

- `tests/unit/specification/test_template_registry.py::test_low_fit_task_returns_explicit_custom_match_instead_of_silent_collapse`
- `tests/unit/specification/test_template_registry.py::test_enriched_market_template_mentions_segmentation_and_competitor_outputs`
- `tests/unit/specification/test_task_generator.py::test_unknown_category_does_not_silently_erase_custom_context`

## 4B-Ready Scope Vs Deferred Scope

### 4B-ready scope

- `C-8`: add tool-selection heuristics to the task-generation prompt while staying inside the registered tool set
- `C-14`: enrich existing methodology archetypes with frameworks, output expectations, and failure-mode language without expanding tool/model envelopes

### Deferred as `new capability`

- `C-6`: load-bearing dual-axis classification with persisted domain and secondary analytical modes
- `C-10`: dynamic lens registry and selector
- `C-14`: automatic low-fit custom-template generation that expands beyond the current parent-template content seam

## Recommended Future Write Surfaces

### 4B-ready surfaces

- `src/keystone/specification/prompts/task_generation.md`
- `src/keystone/specification/template_registry.py`
- `tests/unit/specification/test_task_generator.py`
- `tests/unit/specification/test_template_registry.py`

### Deferred capability surfaces

- `src/keystone/specification/prompts/classification.md`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/decomposer.py`
- future lens prompt files if a real registry is introduced

## Final Classification

- `C-8` is `content-only`.
- `C-14` is split:
  - `existing-seam code` for archetype enrichment inside the current template envelope
  - `new capability` for true low-fit custom-template expansion
- `C-6` is `new capability` until the accepted dual-axis classifier surface is real.
- `C-10` is `new capability`.

Wave 4B should carry only the `C-8` prompt guidance and the `C-14` archetype-enrichment slice.
Dual-axis tiebreaking and dynamic lens selection must wait for a later capability checkpoint.
