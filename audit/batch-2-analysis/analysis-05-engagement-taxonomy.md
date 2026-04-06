# Analysis: Report 05 — Consulting Engagement Taxonomy
*Analyzed: 2026-04-05 | Priority: Tier 3 (MEDIUM) | Report quality: medium-high*

---

## Executive Summary

This report is more taxonomy than architecture — it catalogs MBB engagement types, workstreams, frameworks, and knowledge management systems with reasonable depth and verified sourcing. Its highest-value sections are Section 5 (how consultants navigate ambiguity — directly informs the Specification Engine) and Section 6 (MBB knowledge infrastructure — directly informs the Observation Library). The taxonomy sections (1–4) confirm Jack's Engagement Scope directive and validate the "no predefined skill files" design intent: 70% of MBB engagements blend multiple categories simultaneously, which means category-matching is the wrong approach. Section 5 contains specific, actionable design recommendations for the Spec Engine that go beyond what the current plan specifies. The MBB knowledge management data (McKinsey Lilli, five-tier artifact hierarchy, faceted taxonomy) provides concrete structural patterns the Observation Library should adopt rather than invent.

---

## Key Findings (ranked by implementation impact)

### 1. Multi-category engagement blending is the norm, not the exception

- **What:** 70% of published MBB case studies involve multiple engagement types simultaneously. The auto shop expansion test case blends at minimum four categories: market sizing (Growth), competitive analysis (Strategy), location optimization (Operations), and logistics (Supply Chain Operations). The report provides 20 verified case studies where most combine strategy, digital, and implementation workstreams in one engagement.
- **Evidence basis:** BCG, McKinsey, Bain published case studies from 2025–2026 sourced and cited by URL.
- **Evidence quality:** Credible. Primary sources from firm websites, recent publications (2025–2026).
- **Temporal check:** Current. Cases cited range from August 2025 to January 2026.
- **Conflicts with existing project research?** No conflict. Confirms and strengthens Jack's Directive #4 (Engagement Scope) and Directive #1 (The Rigidity Problem). The existing plan's five fixed agent types were designed for market research and are structurally mismatched to this reality.
- **Verdict:** ADOPT — confirms the design direction already established by Jack's directives.
- **Justification:** This is not a subtle point. If most real engagements cross categories, a system that routes to category-specific agent configurations will fail the majority of the time. Dynamic configuration from the Spec Engine is not optional.
- **Keystone impact:** Component #5 (Specification Engine) must not route by engagement type. It must decompose by problem structure. This finding prohibits a "detect engagement type, load type-specific template" design.
- **Contradicts:** Nothing currently in the plan. The plan already says "dynamic config" — this evidence makes the case for why it cannot be compromised.

---

### 2. Seven-step hypothesis-driven problem decomposition with explicit Day One Hypothesis

- **What:** McKinsey's canonical decomposition process (from Staff Paper 66 and "Bulletproof Problem Solving"): (1) Define problem with constraints and success criteria, (2) Disaggregate via MECE logic tree, (3) Prioritize by impact × actionability, (4) Develop work plan with specific analytical "end products" per branch, (5) Conduct analyses starting with heuristics, (6) Synthesize, (7) Communicate. The process is explicitly iterative — teams are required to form a "Day One Hypothesis" within the first 24 hours and update it continuously. Precision should match stakes: "level one" (heuristic), "level two" (quick structured analysis), "level three" (full rigorous study).
- **Evidence basis:** McKinsey Staff Paper 66, "Bulletproof Problem Solving" (Conn & McLean), "The McKinsey Way" (Rasiel), Pyramid Principle (Minto). Multiple corroborating sources.
- **Evidence quality:** Verified. Canonical McKinsey methodology, well-documented in multiple independent sources across decades.
- **Temporal check:** Timeless. Problem-solving methodology — not technology-dependent.
- **Conflicts with existing project research?** No conflict. Extends and specifies Jack's Directive #2 (MECE Issue Tree). The current plan has issue trees conceptually; this gives the mechanical specification.
- **Verdict:** ADOPT with direct mapping to Spec Engine design.
- **Justification:** This is the exact process the Spec Engine should mechanize. The "Day One Hypothesis" maps directly to generating a governing hypothesis before task dispatch. The "impact × actionability" priority scoring maps to task prioritization in the work plan. The three precision levels map to the iterative research loop design (Jack's Directive #3).
- **Keystone impact:** Spec Engine should produce: (a) explicit problem definition with constraints and success criteria using SCQA format, (b) 2–3 MECE decompositions using different structural approaches, (c) a stated Day One Hypothesis, (d) a priority-scored work plan where each branch has a defined analytical "end product" (specific chart, table, or conclusion format), not just a topic. The "end product" specification is currently missing from the plan and is high-leverage for quality.
- **Contradicts:** Nothing. Adds specificity the plan currently lacks.

---

### 3. Five approaches to MECE decomposition of novel problems

- **What:** When confronting problems that don't fit standard frameworks, consultants generate MECE structures through five structural approaches: by process/stages (value chain decomposition), by segmentation (customer/product/geography), by algebraic decomposition (Revenue = Price × Volume), by conceptual framework (internal vs. external factors), by opposing forces (supply vs. demand). Teams try multiple cuts at the same problem — each decomposition reveals different analytical angles. Issue trees (open questions, insufficient knowledge) vs. hypothesis trees (if/then construction, sufficient directional knowledge) are used differently depending on information state.
- **Evidence basis:** McKinsey consulting methodology, "Bulletproof Problem Solving," case interview resources. Multiple corroborating sources.
- **Evidence quality:** Verified. Foundational consulting methodology.
- **Temporal check:** Timeless.
- **Conflicts with existing project research?** Directly extends Jack's Directive #2. The current plan says "multiple agents independently construct MECE issue trees" without specifying the structural approaches. This fills that gap.
- **Verdict:** ADOPT — this is the operational specification for what "generate MECE decompositions" means.
- **Justification:** Without specifying structural approaches, agents generating issue trees will default to one pattern (likely process-based or topic-based) and miss other cuts. The report's five approaches should be the explicit prompt repertoire for Spec Engine issue tree generation. Each approach should be attempted and the best or a synthesis selected.
- **Keystone impact:** The Spec Engine should explicitly prompt for at least 3 of the 5 approaches for each novel engagement. The deliberation over issue trees (Jack's Directive #2, step 3) should compare decompositions from different structural approaches, not just different agents using the same approach. This distinction is architecturally important and not currently in the plan.
- **Contradicts:** Nothing. Fills a specification gap.

---

### 4. McKinsey "flexons" as cross-domain pattern matching primitives

- **What:** McKinsey Quarterly's concept of "flexons" — four flexible mental models for shaping novel problems: (1) Network flexon (map entities and relationships), (2) Evolutionary flexon (view through adaptation and selection), (3) Decision-agent flexon (model stakeholders as agents with different incentives), (4) System-dynamics flexon (map feedback loops and delays). Cross-industry analogies are a primary tool: "How would a low-cost airline attack this problem? A cosmetics manufacturer?" The McKinsey salmon conservation case demonstrates the same disaggregation logic applied to a completely non-business problem.
- **Evidence basis:** McKinsey Quarterly, published methodology.
- **Evidence quality:** Credible. Published by the firm itself; no independent empirical validation cited.
- **Temporal check:** Timeless. Structural reasoning pattern.
- **Conflicts with existing project research?** Extends Jack's Directive #6 (FITFO Standard). The plan references "cross-domain pattern recognition" but has no mechanism specified.
- **Verdict:** ADAPT for the Observation Library's problem archetype library.
- **Justification:** The four flexons are a compact, useful classification of analytical lenses. They're better suited to the Observation Library (as problem archetype metadata) than to real-time Spec Engine prompting, where they'd add latency. The cross-industry analogy pattern is directly applicable to Spec Engine prompting: include a step that asks "what structurally similar problem has been solved in another domain?"
- **Keystone impact:** Observation Library problem archetypes should tag entries across the four flexon types. This enables retrieval by structural problem pattern rather than by industry. Example: "auto shop expansion" and "hospital network design" both retrieve under "network optimization under demand uncertainty" — the report explicitly names this as a target pattern. This is the mechanism for the FITFO Standard.
- **Contradicts:** Nothing. Adds mechanism to a stated but unspecified capability.

---

### 5. McKinsey Lilli as a concrete architectural model for the Observation Library

- **What:** McKinsey's Lilli (launched 2023) is a generative AI platform aggregating 40+ curated knowledge sources and 100,000+ documents/interview transcripts. Operates in two modes: internal knowledge search and external source chat. Achieved 72% firm-wide adoption. Processes 500,000+ monthly prompts. Delivers 5–7 relevant pieces per query. Produces up to 30% time savings in search and synthesis. Operates as an "orchestration layer" combining large and small language models with specialized agents, including a McKinsey Tone of Voice agent and slide-building capabilities. The firm maintains 50,000+ practice documents organized by practice area AND topic with multi-dimensional metadata.
- **Evidence basis:** McKinsey public disclosures, reported stats from McKinsey presentations. Single-source, from the firm itself.
- **Evidence quality:** Credible. Self-reported by McKinsey — no independent audit. Usage statistics plausible given firm scale.
- **Temporal check:** 2023 launch, stats current as of report date (early 2026). Highest relevance.
- **Conflicts with existing project research?** The Karpathy KB pattern discussed in Jack's Directive #8 and the Lilli architecture are complementary. Lilli is the codification end; Karpathy KBs are the accumulation mechanism. Not in conflict.
- **Verdict:** ADAPT — use Lilli's architecture as structural reference, not direct replication.
- **Justification:** The two-mode operation (internal knowledge search + external source chat) maps directly to Keystone's within-engagement knowledge (claim-level IR) vs. cross-engagement Observation Library. The orchestration layer with specialized sub-agents maps to the multi-agent pipeline architecture already designed. Lilli proves the concept works at scale with high adoption — useful evidence for the design direction. The 5–7 relevant pieces per query is a useful target precision for Observation Library retrieval.
- **Keystone impact:** Observation Library retrieval should target delivering 5–7 highly relevant observations per query rather than ranked lists of 20+. The two-mode distinction (within-engagement vs. cross-engagement) should be explicit in the API. The "McKinsey Tone of Voice agent" parallel suggests Keystone should have a consulting-voice quality agent at L3 (Generation), though this is already implied by the evaluation rubric.
- **Contradicts:** Nothing.

---

### 6. Five-tier knowledge artifact hierarchy from MBB knowledge management

- **What:** All three MBB firms converge on five tiers of knowledge artifacts: (1) Client deliverables — confidential, restricted; (2) Sanitized practice documents/case examples; (3) Reusable frameworks and methodologies; (4) Proprietary data tools and benchmarks; (5) Published thought leadership. Content is organized on a dual-axis matrix: industry vertical × functional capability, plus cross-cutting dimensions for topic/theme, geography, document type, and date. Client-identifying information is stripped before documents enter the knowledge base; specifics are abstracted into reusable patterns.
- **Evidence basis:** Synthesized from McKinsey, Bain, BCG knowledge management documentation, PPK job descriptions, BCG Vantage descriptions.
- **Evidence quality:** Credible. Triangulated across three firms from multiple source types.
- **Temporal check:** 2025–2026 sourcing. Patterns described as consistent across decades of evolution — timeless structural logic.
- **Conflicts with existing project research?** The current plan has an Observation Library with 3-tier categorization (from Jack's Directive #10 context). The MBB five-tier hierarchy is more specific and operationally validated. No conflict; adds precision.
- **Verdict:** ADOPT with adaptation to Keystone's scale.
- **Justification:** The five-tier hierarchy solves the sanitization and reusability problem that any consulting KM system must solve. Keystone doesn't have confidential client deliverables in the same sense (Tier 1), but the distinction between raw engagement outputs and abstracted reusable learnings is critical. Tiers 2–4 map directly: sanitized engagement summaries, reusable frameworks/analytical templates, and benchmark data.
- **Keystone impact:** Observation Library entries should be explicitly tiered. Tier 2 (sanitized engagement summaries) feeds from every engagement automatically. Tier 3 (reusable frameworks) is manually curated from Tier 2 entries that prove durable. Tier 4 (benchmark data) is industry/market data accumulated across engagements. This tiering should be in the data model. The dual-axis metadata (industry × functional capability) plus cross-cutting dimensions should be the tagging schema — not a flat tag list.
- **Contradicts:** Nothing in the plan. Adds operational precision to a stated but underspecified component.

---

### 7. GenAI-augmented consultants 15 percentage points more likely to correctly apply unfamiliar methods

- **What:** BCG Henderson Institute research finding: consultants augmented with GenAI were 15 percentage points more likely to correctly apply unfamiliar analytical methods. The report interprets this as shifting the historical 80/20 personalization-over-codification balance at MBB firms — codification becomes more valuable when AI can retrieve and apply it in context.
- **Evidence basis:** BCG Henderson Institute research. Single study, not independently replicated as cited.
- **Evidence quality:** Credible. BCG's internal research arm — credible though not peer-reviewed. Directionally consistent with the 78% vs. 42% empirical anchor already in the project (same model, different structure).
- **Temporal check:** Recent. Consistent with the project's empirical anchors.
- **Conflicts with existing project research?** Consistent with the project's core conviction: "Harness > model." The 15pp figure is new but directionally aligned.
- **Verdict:** ADOPT as additional evidence for the design thesis — does not require architectural changes.
- **Justification:** The finding is relevant primarily as validation. It confirms that Keystone's Observation Library feeding forward into future engagements is a high-value investment, not a secondary feature.
- **Keystone impact:** Supports prioritizing Observation Library development as a Phase 1 component, not a later-phase addition. The value of accumulated methodology knowledge is empirically confirmed.
- **Contradicts:** Nothing.

---

### 8. "What Would You Have to Believe?" and uncertainty labeling in consulting practice

- **What:** Three McKinsey tools for navigating incomplete/contradictory data: (1) Day One Hypothesis — always maintain a current best answer, updated continuously; (2) "Directionally Right, Same Order of Magnitude" — aim for roughly correct rather than precisely wrong; (3) "What Would You Have to Believe?" — when a key assumption is uncertain, map what must be true for the conclusion to hold, then assess plausibility. Pre-mortem analysis, constructive confrontation, and triangulation across multiple data sources (client interviews, industry reports, financials, customer surveys, expert calls) are standard practice.
- **Evidence basis:** McKinsey practice documentation, "The McKinsey Way," case interview methodology.
- **Evidence quality:** Verified. Well-documented McKinsey methodology, consistent across multiple sources.
- **Temporal check:** Timeless.
- **Conflicts with existing project research?** Consistent with the project's evaluator design (confidence scoring, uncertainty flagging). Provides concrete reasoning patterns that should be embedded in Spec Engine and deliberation prompts.
- **Verdict:** ADOPT "What Would You Have to Believe?" as an explicit reasoning step in deliberation and evaluation.
- **Justification:** The current plan has confidence scoring but not the structured reasoning pattern for generating confidence assessments. "WWHTB" is a well-specified tool for exactly this: forcing explicit assumption enumeration before confidence labeling. It belongs in the deliberation layer (L1.5) where analysts assess competing interpretations.
- **Keystone impact:** L1.5 (Deliberation) prompts should include an explicit "What Would You Have to Believe?" step for any finding rated below high confidence. The confidence map produced by deliberation should include enumerated key assumptions per conclusion, not just a confidence score. This is a concrete prompt engineering specification.
- **Contradicts:** Nothing. Adds precision to an existing design element.

---

### 9. Engagement duration and phase structure patterns

- **What:** Typical durations by type: Due Diligence (2–4 weeks), Strategy (8–12 weeks), Operations (3–6 months), Transformation/Implementation (6–24 months). Restructuring/turnaround follows a three-phase structure: Stabilization (0–3 months), Optimization (3–12 months), Growth Repositioning (12–36 months). Operations engagements begin with process mapping (gemba walks, time studies) before quantitative analysis. Strategy engagements follow a specific analytical arc: market landscape → competitive benchmarking → customer segmentation → trend analysis → scenario planning → capability assessment → strategic options evaluation.
- **Evidence basis:** MBB published case studies and practice area descriptions. Verified against 20 case studies.
- **Evidence quality:** Credible. Industry-wide norms, triangulated across firms.
- **Temporal check:** Timeless structural patterns.
- **Conflicts with existing project research?** No conflict. Fills in domain knowledge the plan assumes but doesn't specify.
- **Verdict:** ADOPT as Observation Library seed content and Spec Engine guidance.
- **Justification:** These patterns are the domain knowledge the Spec Engine needs to generate plausible work plans for novel engagements. They are not architectural decisions for Keystone — they are content the system needs to be initialized with.
- **Keystone impact:** The Observation Library should be initialized (pre-engagement) with: engagement type duration norms, standard phase structures, and workstream sequences for the six most common engagement types covered in this report. This is the "compiled wiki" pattern from Karpathy's KBs applied to consulting methodology knowledge. The Spec Engine can reference these patterns when generating work plans rather than reasoning from scratch.
- **Contradicts:** Nothing.

---

### 10. Framework-to-engagement mapping and contextual metadata

- **What:** The report maps 35 frameworks to engagement types and provides a framework-to-engagement pairing table. Key observation: frameworks should be stored with metadata indicating "when useful" (problem type, data availability, engagement phase) rather than just category. The auto shop case would invoke frameworks from at least four different categories: TAM/SAM/SOM (Growth), Porter's Five Forces (Strategy), gravity modeling (Operations — not named as a consulting framework but implied), and network optimization (Operations/Supply Chain).
- **Evidence basis:** Synthesized from MBB practice area methodology documents. Author-constructed mapping.
- **Evidence quality:** Credible. Reasonable synthesis; the framework pairings are standard consulting practice knowledge.
- **Temporal check:** Timeless. Framework utility doesn't change rapidly.
- **Conflicts with existing project research?** The current plan has a "Skills Library in L2 with 3-level progressive loading." This report's framework library is the content that populates that library. No structural conflict; provides content specification.
- **Verdict:** ADAPT — use the framework-to-engagement mapping as metadata structure, not as a routing table.
- **Justification:** The report's recommendation (frameworks stored with contextual metadata, not just category) directly supports the dynamic configuration design. The L2 Skills Library should index frameworks by problem type, data availability, and engagement phase — not by engagement category. This changes how the Spec Engine retrieves frameworks: semantic search by problem characteristics, not category lookup.
- **Keystone impact:** L2 Skills Library framework metadata schema should include: applicable problem types (list), data requirements (what must be available to use this), engagement phase (diagnostic/analysis/synthesis/recommendation), typical deliverable format, and MBB firm that originated/uses it. This schema enables framework retrieval to work correctly for hybrid and novel engagements.
- **Contradicts:** Nothing structural. Adds content specification to an existing component.

---

## Architectural Decisions This Enables

**1. Spec Engine issue tree generation must specify structural approach, not just content.**
The Spec Engine should explicitly generate decompositions using different structural approaches (process-based, segmentation-based, algebraic, conceptual, opposing forces). "Generate 2-3 MECE decompositions" in the current plan is underspecified. Each decomposition should use a named structural approach, and the deliberation step should compare decompositions that use different approaches, not just different agents using the same approach.

**2. Work plan branch outputs should specify "end product," not just "topic."**
McKinsey's work plan discipline requires each branch to define a specific analytical end product (a specific chart type, a specific table structure, a specific conclusion format). The Spec Engine output — which becomes the RESEARCH.md spec — should require this level of specificity per task. This prevents agents from producing unfocused outputs and gives the evaluator concrete quality criteria.

**3. Observation Library data model should implement five-tier artifact hierarchy with dual-axis metadata.**
Industry vertical × functional capability as primary axes, plus topic/theme, geography, document type, date, confidence level, and problem archetype (flexon type) as secondary dimensions. Tiered entry types: raw engagement outputs, sanitized learnings, reusable analytical templates, benchmark data, and published methodology. This should be in the Pydantic models before build.

**4. L1.5 Deliberation must include explicit "What Would You Have to Believe?" step for low-confidence findings.**
The confidence map produced by deliberation should output: conclusion, confidence score, and enumerated key assumptions per conclusion. This is currently underspecified in the deliberation design. "WWHTB" is the mechanism for generating the key assumptions list.

**5. L2 Skills Library framework metadata should enable retrieval by problem characteristics.**
Framework entries tagged by: problem types, data requirements, engagement phase, typical deliverable format. Retrieval via semantic search on problem characteristics, not category lookup. This is a schema decision that affects the Skills Library data model.

---

## Changes to Existing Plan

**Moderate change — Spec Engine output spec:**
The RESEARCH.md spec format should include a "Day One Hypothesis" field and "Analytical End Products" per task branch. Currently the plan specifies tasks, context, and constraints. Adding the Day One Hypothesis and per-branch end product specs meaningfully improves downstream quality without architectural rework. This is a content change to the RESEARCH.md template, not a structural change.

**Minor change — Observation Library data model:**
Add the five-tier artifact classification and the dual-axis metadata schema (industry × functional capability + secondary dimensions including flexon type). This extends the existing model rather than replacing it. Should be incorporated into the Pydantic models before the Observation Library component is built.

**Minor change — Deliberation prompts:**
Add "What Would You Have to Believe?" as an explicit step in the deliberation prompt for findings below high confidence. Add enumerated key assumptions to the confidence map output schema. Changes to prompts and output schema — no structural change to the pipeline.

**No change — Dynamic configuration:**
The report confirms the design direction already established. No changes needed beyond what Jack's directives already require.

**No change — Pipeline architecture:**
Nothing in this report suggests changes to the 7-layer pipeline, component boundaries, or handoff contracts.

---

## Open Questions Remaining

**1. Observation Library initialization content:**
The report provides the patterns (engagement types, workstreams, frameworks, durations, phase structures) that should initialize the Observation Library before the first real engagement. Who curates this initial content? Should it be a manual task (Jack + team) or a structured prompt-driven compilation process? The Karpathy KB pattern suggests a compilation session — an agent processes the source material (this report, the framework list, the workstream descriptions) and generates structured wiki entries. This is actionable in Phase 1 as a distinct build task.

**2. Problem archetype library scope:**
The report suggests maintaining "a library of problem archetypes" distinct from engagement types. The flexon framework gives a structural classification. But what level of granularity is right? "Network optimization under demand uncertainty" (report's example) is specific enough to be useful. "Strategy engagement" is too broad. Who defines and maintains the archetype library? This needs an owner and a maintenance process.

**3. Framework retrieval mechanism timing:**
The report's recommendation (contextual framework retrieval by problem characteristics) implies the Spec Engine retrieves relevant frameworks from L2 during work plan generation — but L2 (Content Structuring) is downstream of L1 (Research). Does the Spec Engine (L0) need direct access to the framework library, or does framework selection happen at L2 after research? This is a sequencing question with interface implications. Current architecture puts skills/frameworks in L2, but the Spec Engine operating at L0 needs to know which frameworks to instruct agents to apply. This sequencing tension is unresolved.

**4. Confidence-tiered precision (three analytical levels):**
McKinsey's three-level precision (heuristic/quick structured/full rigorous) maps to the iterative research loop design — but the stopping condition for each level is unclear. When does a "level one" answer satisfy the engagement, and when does the system escalate to level two? This connects to Jack's Directive #3 (iterative research stopping conditions) and is flagged there as the single biggest architectural gap. This report adds the vocabulary but not the stopping rule.

**5. Cross-engagement knowledge sanitization process:**
MBB firms employ dedicated knowledge professionals to sanitize client deliverables before they enter the knowledge base. Keystone is a small firm. Who or what performs this sanitization? Can it be automated (LLM-based sanitization and abstraction)? If the Observation Library is to accumulate cross-engagement knowledge, this process must be designed. Not addressed in the current plan.
