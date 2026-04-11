# Report 12: C3 — Report/Deliverable Generation

**Source report:** `research/reports/batch-1/Deep_Research_Report_From_Prompt_12.md`
**Prompt:** Research AI-native consulting deliverable generation, McKinsey/BCG competitive benchmarks, multi-format output stacks, citation architecture, anti-slop enforcement, and visualization tooling.

---

## Top Findings

**Finding 1: Template-driven generation with system-level citation verification is the only pattern that produces consulting-usable output without 25-30% rework.**
- Pipeline layer: L3 (Generation)
- McKinsey's Lilli implements system-level citation: the system retrieves documents, AI generates, then a separate verification process maps claims back to sources with independent attribution scoring. Tow Center at Columbia found prompt-based self-citation fails in over 60% of tests across all major AI tools (Perplexity best at 37% failure rate, ChatGPT at 67%, Grok-3 at 94%). BCG's Deckster requires 25-30% rework rate; a system achieving <15% would be genuinely differentiated.
- Evidence quality: Verified for McKinsey architecture (security breach inadvertently revealed details March 2026); Verified for Tow Center citation failure rates
- Build implication: Keystone's citation architecture cannot rely on prompt-based self-citation ("please cite your sources"). The plan must implement the five-layer citation chain as described in the report: Source Layer (chunk-level metadata with stable IDs), Research Agent Layer (structured claim+source_chunk_id objects), Synthesis Layer (inherited citation chains), Generation Layer (cite-or-abstain prompts), Verification Layer (separate agent mapping claims back to sources). PROV-AGENT (IEEE e-Science 2025) provides the W3C PROV standard implementation for multi-agent citation propagation.

**Finding 2: No existing open-source system combines parallel deep research, citation-traced synthesis, multi-format rendering, and anti-slop enforcement into a single pipeline.**
- Pipeline layer: L3, L2
- McKinsey's Lilli is the closest analog but costs approximately £8,000/user/year and operates within McKinsey's walled garden. Every other system — GPT-Researcher, OpenAI Deep Research, Google Gemini Deep Research — outputs Markdown/text without PPTX or dashboards natively. The gap is verified by Manus's architecture (acquired by Meta for $2-3B) which still required separate content quality and visual quality optimization.
- Evidence quality: Verified (multiple production system benchmarks)
- Build implication: This is Keystone's competitive moat validation. The integration gap is real and documented. The plan is correct that this combination doesn't exist. The architectural prescription — Skills API for document rendering, PPTAgent/DeepPresenter for AI-native slides, Vizro for consulting-grade visualization, PROV-AGENT for citation propagation — is a build-first opportunity, not a buy-first one.

**Finding 3: McKinsey's Lilli architecture is now partially documented from the March 2026 security breach.**
- Pipeline layer: L3, L2
- CodeWall autonomous agent SQL injection revealed: 3.68 million RAG document chunks, 95 system prompts controlling 12 AI model types, 384,000 AI assistants, 266,000+ OpenAI vector stores. One-Click Deliverables: 3-4 prompt questions → draft deck in minutes. Every fact cross-checked against RAG knowledge base. Inline citations attached, unsupported claims flagged. Tone of Voice module rewrites to McKinsey syntax. Template governance locks color palettes and typography.
- Evidence quality: Verified (inadvertent architectural disclosure from security incident)
- Build implication: Three Lilli design patterns are directly adoptable: (1) Tone of Voice module that rewrites to client's syntax — implement as a Style module in Keystone's L3 that rewrites to Keystone's language conventions; (2) template governance that locks design parameters — implement via design token system; (3) One-Click Deliverables that pass through 3-4 clarifying questions — implement as L0 Specification Engine's intent clarification phase.

**Finding 4: The Antislop Sampler and the four-agent Anti-Slop System (ASS v3.0) pipeline provide production-ready enforcement mechanisms.**
- Pipeline layer: L3, L4
- Antislop Sampler (arXiv 2510.15061): backtracking-based suppression of 8,000+ unwanted patterns at inference time; companion FTPO fine-tuning achieves 90% slop reduction while maintaining GSM8K/MMLU performance. Some LLM patterns appear 1,000x more frequently in AI output than human text.
- ASS v3.0 (GitHub): four-agent pipeline: naive Drafter → brutal Slop Detector (rates slop 1-10, identifies generic openings/listicle structures/excessive hedging/buzzwords) → Redraft Specialist (rewrites using original prompt + slop feedback) → Quality Arbiter (final approval or re-iteration). Key: drafter stays intentionally naive while detector is maximally critical.
- Evidence quality: Verified for Antislop Sampler (arXiv, benchmarked); Credible for ASS v3.0 (GitHub implementation)
- Build implication: The four-agent anti-slop pipeline maps directly onto the plan's L3/L4 interaction: the existing Evaluator (L4) should implement the Slop Detector role as a dedicated dimension in its rubric, with a separate Redraft Specialist subagent triggered on slop detection. This adds structure to the existing "anti-slop standard" in CAPSTONE-PLAN-v2.md Section 5.8 without requiring a separate pipeline.

**Finding 5: Vizro (McKinsey/QuantumBlack Labs) solves the consulting-grade visualization problem through programmatic constraint, not better prompting.**
- Pipeline layer: L3
- Vizro (2,500+ stars, 15,000+ monthly downloads): McKinsey's visual design best practices in a programmatic framework; curated chart templates inspired by FT visual vocabulary; built on Plotly and Dash; Vizro-MCP extension enables AI-native dashboard generation via natural language. The LLM-powered design token system (3-tier CSS tokens, CI audit scripts) reduces 418 hardcoded values across 28 files to zero.
- Evidence quality: Credible (active project, QuantumBlack Labs = McKinsey's AI arm; production-grade but community validation limited)
- Build implication: Use Vizro as the visualization layer, not just Plotly directly. The design token architecture (Plotly → Vizro → custom design tokens → automated drift detection) is the correct solution to visual consistency — removing formatting decisions from the model entirely, which aligns with the plan's "structure over intent" principle.

---

## Tool/Framework Verdicts

**Anthropic Skills API (PPTX/DOCX/XLSX/PDF skills)**
- Version/maturity: Beta (skills-2025-10-02), official Anthropic; anthropics/skills repo 105K stars
- What it does: Programmatic document generation via skill_id; progressive disclosure loading; PptxGenJS + python-pptx internals; OOXML manipulation
- Verdict: BUILD — this is the L3 document generation foundation; integrate as the primary PPTX/DOCX skill backend; note that Skills API calls are not covered by Zero Data Retention arrangements (flag for compliance)

**PPTAgent/DeepPresenter (icip-cas)**
- Version/maturity: 3,300 stars; V2 "DeepPresenter" mode from arXiv February 2026
- What it does: Dual-agent architecture (Research Agent + Design Agent); environment-grounded reflection (conditions generation on rendered slide perceptions); 30+ tools in Docker sandbox; MCP integration; fine-tuned DeepPresenter-9B competitive with GPT-5 at lower cost
- Verdict: BUILD — state of the art for AI-native slide generation; environment-grounded reflection is the key differentiator (identifies visual issues during execution, not just content issues); integrate as L3's slide generation engine

**python-pptx**
- Version/maturity: v1.0.2 stable, 3,200 stars; single maintainer, slow feature velocity
- What it does: Native editable PPTX creation; shapes, charts, tables, placeholders
- Verdict: BUILD — essential foundation for programmatic PowerPoint; use as the underlying PPTX manipulation layer; note single-maintainer risk but no viable alternative for native editable output

**Typst**
- Version/maturity: 45,000 stars; millisecond compilation; adopted by UBS + 3,500+ universities
- What it does: Data-driven PDF generation; built-in JSON/CSV/XML loading; single 40MB binary
- Verdict: BUILD — use for Layer 3 PDF deliverables; the data-loading capability (built-in JSON ingestion) is critical for connecting the Deliberation phase's JSON Confidence Map directly to the deliverable, eliminating manual translation

**Vizro (QuantumBlack Labs)**
- Version/maturity: 2,500+ stars, 15,000+ monthly downloads; Vizro-MCP available
- What it does: McKinsey visual design standards programmatically; FT visual vocabulary templates; Plotly/Dash base; AI-native dashboard generation via Vizro-MCP
- Verdict: BUILD — use as the visualization styling layer on top of Plotly; the Vizro-MCP extension enables AI agents to generate consulting-styled dashboards via natural language, which is exactly what L3 needs

**PROV-AGENT (W3C PROV for multi-agent workflows)**
- Version/maturity: IEEE e-Science 2025; MongoDB + LMDB + Neo4j backend
- What it does: Tracks each AI agent as a first-class provenance node; tool executions, model invocations, prompts, and responses tracked as PROV entities; Neo4j queries enable "What input data led this agent to this claim?"
- Verdict: BUILD — implement as L3's citation infrastructure; the "claim → source_chunk_id → cited_text" structured output for each research agent directly implements PROV-AGENT's entity model

**Google Vertex AI Check Grounding API**
- Version/maturity: Production Vertex AI; sub-500ms latency; 0-1 support score
- What it does: Measures what fraction of claims are grounded in provided facts; configurable citation thresholds
- Verdict: BUILD — use as the Verification Layer (Layer 5 in the five-layer citation chain); this is the architectural equivalent of Lilli's independent claim-to-source verification process

**Pandoc + WeasyPrint**
- Version/maturity: 42,300 + 8,700 stars; production-proven
- What it does: Markdown → PDF pipeline; full CSS design control
- Verdict: LEARN — secondary to Typst for new PDF generation; consider for converting existing Markdown outputs; Typst is preferable for new builds given its data loading capabilities

**Marp + MCP (masaki39/marp-mcp)**
- Version/maturity: 10,700 stars; @masaki39/marp-mcp available
- What it does: Markdown → slides pipeline; MCP server integration; PPTX export renders slides as images (not editable objects)
- Verdict: LEARN — useful for rapid prototyping of slide structures; image-only PPTX export is a dealbreaker for consulting deliverables that need to be editable

**deck2video**
- Version/maturity: Early stage; novel delivery format
- What it does: Converts Marp/Slidev decks into narrated MP4 videos with local AI voice cloning
- Verdict: LEARN — the "audio brief" format (finding: 21% more time spent, 41% higher completion, 2.3x more internal sharing for interactive reports) has real engagement value; design for it in Phase 3 but don't build now

**Streamlit**
- Version/maturity: Massive ecosystem, Snowflake-backed, production
- What it does: Rapid dashboard prototyping; notebook-to-shareable-app pipeline
- Verdict: BUILD — use for interactive deliverable format (#4 in recommended five-format stack); Storydoc data (21% more time, 41% higher completion) validates the interactive format

**Hex**
- Version/maturity: $172M total funding, production SaaS
- What it does: Notebook-to-app pipeline; collaborative data analysis; turns analysis into shareable data applications
- Verdict: LEARN — interesting for analyst-facing internal deliverables; more expensive and complex than Streamlit; evaluate when client needs collaborative analytical workbooks

**Slidev**
- Version/maturity: 44,400 stars; presentation dev tool
- What it does: Developer-focused slide creation; design patterns strong; PPTX as images only
- Verdict: LEARN — study design patterns and layout approaches; image-only PPTX export disqualifies for consulting deliverables

**Presenton**
- Version/maturity: 3,800 stars; self-hosted AI slide generator
- What it does: Self-hosted alternative to AI presentation tools
- Verdict: LEARN — less sophisticated than PPTAgent/DeepPresenter; evaluate if self-hosting becomes a hard requirement

**Beautiful.ai / Templafy**
- Version/maturity: Commercial SaaS products, production
- What it does: Template-constrained presentation tools; Beautiful.ai reduces creation time 75%; Templafy cuts proposal creation from 4 hours to 20 minutes
- Verdict: SKIP for core build — commercial SaaS adds vendor dependency; but adopt the design principle (constraint-first template governance) and implement it natively via python-pptx template system

---

## Contradictions with CAPSTONE-PLAN-v2.md

**Contradiction 1: The plan treats Layer 3 (Generation) as future/deferred work; the evidence suggests anti-slop enforcement should be built in Phase 1.**
- Plan says: Section 12.2 defers PowerPoint generation to Phase 3 ("Defer implementation"); Section 9 marks generation as "future layers"
- Evidence shows: The anti-slop principle (plan Section 5.8) requires outputs that are "directly usable without human cleanup" — but if L3 isn't built, there's no output layer to enforce this on. More importantly, the five-layer citation chain must be implemented in L1 (Research Agent output format) to flow through to L3 correctly; it can't be retrofitted later.
- Resolution: Partial follow-the-evidence. The full PPTX/dashboard generation can remain Phase 3. But the citation data model (PROV-AGENT pattern, structured claim+source_chunk_id output from research agents) must be designed in Phase 1, even if only rendered as Markdown initially. The plan already says "tag findings with deliverable destinations from Day 1" — extend this to include citation metadata from Day 1 as well.

**Contradiction 2: The plan doesn't specify a visual design governance layer.**
- Plan says: Section 9.2 mentions "apply Keystone's visual identity (fonts, colors, layout rules) via template-driven generation"
- Evidence shows: The design token architecture (three-tier CSS tokens + CI audit scripts) is the only scalable solution to visual consistency. Without it, models will hardcode formatting decisions inconsistently. The Lilli pattern (template governance locks color palettes and typography) shows this is how the best-in-class system does it.
- Resolution: Follow the evidence. Add a design token layer to L3's architecture: Plotly → Vizro → custom Keystone design tokens → automated drift detection. This is an addition to the plan, not a contradiction.

**Contradiction 3: The plan's five-format output stack needs explicit prioritization.**
- Plan says: Section 9.4 lists Executive briefs, Deep reports, Dashboard-style outputs, Scenario models — without explicit prioritization or dependency ordering
- Evidence shows: The recommended five-format stack (Structured Markdown + JSON → Branded PPTX → Branded PDF → Interactive web report → Audio brief) has a clear dependency hierarchy. Structured Markdown+JSON is the source of truth that all other formats render from. Build in this order.
- Resolution: Follow the evidence. Structured Markdown+JSON (already closest to the plan's RESEARCH.md/confidence map JSON approach) should be the authoritative internal format from which all other deliverables are rendered. This enforces the "lossless pipeline" principle from Section 3.2.

---

## Cross-Report Flags

**Flag 1 (reinforces C1/Report 10):** The Skills API (progressive disclosure, SKILL.md format, skill_id) directly implements the generation layer. The PPTX/DOCX/XLSX/PDF pre-built skills in the official anthropics/skills repo are immediately usable as L3 components. Report 10's verification of the .claude/skills/ architecture means these pre-built skills integrate natively.

**Flag 2 (reinforces C4/Report 13):** The five-layer citation chain's Verification Layer (separate agent mapping claims to sources) is the same architectural pattern as Report 13's recommendation to use Google Check Grounding API for post-retrieval grounding verification. These are the same verification step from two different angles (citation chain integrity vs. RAG grounding accuracy). Implement as a single shared verification service.

**Flag 3 (potential conflict with Thread B on evaluation):** The ASS v3.0 four-agent pipeline (Drafter → Slop Detector → Redraft Specialist → Quality Arbiter) partially duplicates the L4 Evaluator's role. Thread B's evaluation research will need to clarify whether slop detection is a separate pipeline step or a dimension within the eight-dimension rubric. This analysis recommends integrating it into the Evaluator rubric (as a dedicated "Anti-Slop" dimension with the Redraft Specialist as a triggered subagent) rather than running a parallel pipeline.

**Flag 4 (validates Thread A on orchestration):** McKinsey's Lilli architecture (12 AI model types, 95 system prompts, structured citation verification pipeline) confirms that production consulting AI systems require sophisticated orchestration. The 500,000+ prompts/month at Lilli validates the scale this type of system can reach. Thread A's orchestration framework analysis should evaluate frameworks against Lilli-scale production requirements.

**Flag 5 (industry rework rate is the quality benchmark):** McKinsey/BCG 25-30% rework rate establishes the baseline. A system achieving <15% rework would be "genuinely differentiated" per the report. This should be a formal metric target for the Keystone system — the Evaluator's calibration against Keystone deliverables should be validated against this benchmark.
