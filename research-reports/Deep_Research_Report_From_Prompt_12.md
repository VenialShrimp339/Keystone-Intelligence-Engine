# The generation layer: building consulting-grade AI deliverables

**No AI system today produces truly autonomous consulting-quality deliverables — but the tooling has reached a critical threshold.** McKinsey's Lilli generates one-click slide decks used by 72% of the firm's 45,000 employees, BCG's Deckster has logged 450,000+ uses across 800 templates, and Anthropic's Skills API now ships production-ready PPTX/DOCX/XLSX/PDF generation. The gap between "AI first draft" and "partner-ready output" has narrowed to roughly 10–20% of effort — a gap Keystone's Generation layer can close through template-driven architecture, citation enforcement, and multi-format rendering. The strategic opportunity is clear: no open-source system yet combines parallel research, citation-traced synthesis, and multi-format deliverable generation into a single pipeline. This report maps every tool, pattern, and production deployment relevant to building that system.

---

## Claude's document generation ecosystem is production-ready but not consulting-complete

Anthropic's **Skills API** (beta header `skills-2025-10-02`) is the canonical foundation for programmatic document generation. The official `anthropics/skills` repository holds **105,000 stars** and packages PPTX, DOCX, XLSX, and PDF skills that power Claude's native capabilities. The PPTX skill uses PptxGenJS and python-pptx internally, supporting HTML-to-PPTX conversion, template-based creation, OOXML manipulation, and visual validation via thumbnail grids. Skills follow a progressive-disclosure pattern — Claude loads only metadata initially, then full instructions, then scripts — keeping context windows efficient.

The **Claude for PowerPoint add-in** (research preview, February 2026) is the most template-aware AI presentation tool available. It reads slide masters, layouts, fonts, and color schemes before generating, and outputs native editable PowerPoint objects rather than static images. Available on Pro through Enterprise plans, it supports Sonnet 4.5 and Opus 4.6 model switching. However, independent testing by an ex-McKinsey/Deloitte consultant across 35+ presentations over 8 weeks concluded that **neither Claude nor ChatGPT produces consulting-ready output without significant formatting work**. Critical gaps include missing waterfall, Mekko, and Gantt charts, a 30MB file limit, no audit log integration, and the fact that Skills API calls are not covered by Zero Data Retention arrangements.

**Three community skill projects** extend Claude's capabilities in ways directly relevant to Keystone:

- **Gadoci Consulting's PPTX skill files** define a design system (color constants, typography, spacing, geometric shape generators) plus a layout library with **13 parameterized slide functions**. Available on Notion, these represent the most sophisticated publicly available custom PPTX skill architecture — though quality claims are self-reported.
- **promptadvisers/claude-code-polished-documents-skills** packages **10 premium brand themes** (McKinsey, Deloitte, KPMG, Stripe, Apple) as JSON configs with a Python styling pipeline and FireCrawl-based brand extraction from any website.
- **199-biotechnologies/claude-deep-research-skill** implements an 8.5-phase research pipeline with auto-continuation for unlimited report length (50K–100K+ words via recursive agent spawning), McKinsey-style HTML output, and quality gates enforcing per-section word counts, citation density, and ≥80% prose ratio.

| Tool | Stars | Classification | Production Ready | Evidence |
|---|---|---|---|---|
| Anthropic Skills API | N/A (Official) | **USE** | Beta, functional | Verified |
| Claude for PowerPoint | N/A (Product) | **USE** (polish) | Research preview | Verified |
| anthropics/skills repo | 105K | **USE** | Reference impl. | Verified |
| Gadoci PPTX Skills | N/A (Notion) | **LEARN** | Brand-specific | Claimed |
| promptadvisers/polished-docs | 50 | **LEARN** | 3 commits | Credible |
| 199-bio/deep-research-skill | 58 | **LEARN** | Usable | Credible |
| tfriedel/claude-office-skills | 333 | **LEARN** | 5 commits | Verified |

**Recommendation for Keystone:** Use the Skills API as the PPTX/DOCX generation foundation. Adopt Gadoci's design-system-plus-layout-library architecture pattern. Steal the brand theme JSON system from promptadvisers. Integrate the 199-bio auto-continuation and quality-gate patterns for long-form output.

---

## McKinsey, BCG, and Deloitte set the competitive benchmark

**McKinsey's Lilli** is the gold standard. Built by QuantumBlack's 150+ developers, it orchestrates "a combination of large and small models" across **40+ curated knowledge sources and 100,000+ documents**. The March 2026 security breach (SQL injection by CodeWall autonomous agent) inadvertently revealed precise architecture details: **3.68 million RAG document chunks**, 95 system prompts controlling 12 AI model types, 384,000 AI assistants, and 266,000+ OpenAI vector stores. Lilli's "One-Click Deliverables" feature, launched early 2025, lets consultants answer 3–4 prompt questions and receive a draft deck in minutes. Every fact is cross-checked against the RAG knowledge base, **inline citations are attached, and unsupported claims are flagged**. A "Tone of Voice" module rewrites text to match McKinsey's syntax and visual density rules. Template governance locks color palettes and typography. Roughly one-third of all Lilli usage — **500,000+ prompts per month** — goes to auto-generated decks, saving 90–120 minutes each and recovering an estimated **50,000 consultant hours monthly** (worth ~$12M in labor).

**BCG's Deckster** (launched March 2024, GPT-4o based) takes a different approach: it sits in every consultant's PowerPoint ribbon with **800–900 firm-approved templates**. Its "One-Click Draft" ingests outlines and returns formatted slides, while a "Review This" button grades each slide against BCG's design rubric — checking MECE structure, headline clarity, and chart hygiene. With 450,000+ uses, it is one of BCG's fastest-scaling internal apps. BCG has also built 36,000+ custom GPTs (claiming world's largest enterprise GPT library) through its "Agent Factory" platform, which includes RAG over a vectorized knowledge lake with toxicity filtering and PII redaction.

**Deloitte's Sidekick** platform serves **170,000+ users with 110 million+ uses**, featuring PowerPoint generation with source-linked synthesis. Users have created 3,000+ reusable skills. Deloitte explicitly notes that "all outputs require appropriate human review and validation" — a pattern universal across all consulting firms.

A critical finding for Keystone: **the industry rework rate is approximately 25–30%**. Third-party analysis suggests roughly 1 in 4 McKinsey AI-drafted deliverables requires substantial rewriting, and BCG reports similar figures. A system achieving **less than 15% rework** would be genuinely differentiated. Every leading system treats citation as infrastructure rather than decoration — inline citations with source verification are table stakes.

---

## Open-source tools for the generation stack

The open-source landscape provides every component needed for Keystone's multi-format rendering pipeline, though no single tool covers the full stack.

**PPTAgent/DeepPresenter** (icip-cas/PPTAgent, 3,300 stars) represents the state of the art for AI-native presentation generation. Its V2 "DeepPresenter" mode (arXiv February 2026) uses a dual-agent architecture: a Research Agent handles content gathering, web search, and PDF parsing, while a Design Agent creates HTML slides with visual design. The key innovation is **environment-grounded reflection** — rather than self-reflecting over reasoning traces, it conditions generation on rendered slide perceptions, enabling identification and correction of visual issues during execution. It runs 30+ tools in a secure Docker sandbox with MCP integration, supports template-based and freeform modes, and has been benchmarked against GPT-5, Gemini 3 Pro, and Claude Sonnet 4.5. A fine-tuned **DeepPresenter-9B** model achieves scores competitive with GPT-5 at lower cost.

**python-pptx** (3,200 stars) remains the essential foundation for programmatic PowerPoint manipulation — creating native editable slides with shapes, charts, tables, and placeholders. Version 1.0.2 is stable and production-proven, though it has a single maintainer, no animation support, and slow feature velocity. For PDF generation, the **Pandoc + WeasyPrint** pipeline (42,300 and 8,700 stars respectively) is production-ready with full CSS design control, while **Typst** (45,000 stars) emerges as a compelling alternative with millisecond compilation, built-in data loading from JSON/CSV/XML, and a single 40MB binary — adopted by UBS, 3,500+ universities, and explicitly positioned for automated PDF generation.

**Marp** (10,700 stars) provides a clean Markdown-to-slide pipeline with MCP server integration (`@masaki39/marp-mcp`), but its PPTX export renders slides as images rather than editable objects. **deck2video** converts Marp or Slidev decks into narrated MP4 videos with local AI voice cloning — a novel delivery format for asynchronous executive briefings.

| Tool | Stars | Classification | Key Strength | Key Limitation |
|---|---|---|---|---|
| PPTAgent/DeepPresenter | 3.3K | **USE** | SOTA AI slide generation | Requires customization for brand templates |
| python-pptx | 3.2K | **USE** | Native editable PPTX | Single maintainer, no animations |
| Pandoc + WeasyPrint | 42.3K + 8.7K | **USE** | Production PDF pipeline | No JS (pre-render charts) |
| Typst | 45K | **USE** | Fast data-driven PDFs | Newer ecosystem |
| Marp + MCP | 10.7K | **USE** | Markdown→slides, MCP | PPTX exports as images |
| deck2video | New | **USE** | Slides→narrated video | Early stage |
| Slidev | 44.4K | **LEARN** | Design patterns | PPTX as images only |
| Presenton | 3.8K | **LEARN** | Self-hosted AI slides | Less sophisticated |

---

## McKinsey's Vizro solves the visualization quality gap

The gap between AI-generated charts and consulting-grade visualizations is primarily about **design consistency, insight-driven titling, and annotation quality** — not chart generation capability. A critical discovery in this research is **Vizro**, an open-source framework from QuantumBlack Labs (McKinsey's AI arm) with **2,500+ stars and 15,000+ monthly downloads**. Built on Plotly and Dash, Vizro encodes McKinsey's visual design best practices into a programmatic framework with curated chart templates inspired by the Financial Times' visual vocabulary. Its **Vizro-MCP** extension enables AI agents to generate consulting-styled dashboards via natural language.

Claude Code's Python sandbox provides the underlying charting engine with full matplotlib, seaborn, and Plotly access — **40+ chart types** including scatter, waterfall, funnel, choropleth, and 3D surfaces. MCP integrations and dedicated Claude Code skills exist for both libraries. The Plotly-based `plotly-mcp-cursor` provides 49+ trace types. For interactive deliverables, **Streamlit** excels at rapid dashboard prototyping (massive ecosystem, Snowflake backing), while **Hex** ($172M total funding) offers a notebook-to-app pipeline that turns analysis into shareable data applications.

The consulting-grade visualization standard requires action titles stating insights ("Asia Sales Lag 15% Behind Target" not "Sales by Region"), highlight-what-matters color discipline, extensive annotation and sourcing footnotes, and brand-consistent styling. **LLM-powered design systems** solve the consistency problem: a documented approach by Hardik Pandya uses three-tier CSS token layers with CI-ready audit scripts, reducing 418 hardcoded values across 28 files to zero. This pattern — structured spec files read at session start, closed token vocabularies, and automated drift detection — should be adopted as Keystone's visual consistency layer atop Vizro.

For Keystone's visualization stack: **Plotly for chart generation → Vizro for consulting styling → custom design token layer for brand consistency → Streamlit for interactive deliverables**. This combination produces output that matches consulting standards programmatically.

---

## Citation chains require infrastructure, not just prompts

End-to-end citation traceability across a multi-agent pipeline demands architectural commitment at every layer. The most directly applicable academic work is **PROV-AGENT** (IEEE e-Science 2025), which extends the W3C PROV standard specifically for multi-agent AI workflows. Each AI agent becomes a first-class provenance node with tool executions, model invocations, prompts, and responses tracked as entities in a provenance graph. It uses MCP for tool access, MongoDB for filtering, LMDB for high-frequency inserts, and Neo4j for graph traversal — enabling queries like "What input data led this agent to this claim?" and "How did Agent A's output become Agent B's input?"

For practical "cite-or-it-dies" enforcement, three production-grade approaches emerged. **Google's Vertex AI Check Grounding API** provides a support score (0–1) measuring what fraction of claims are grounded in provided facts, with configurable citation thresholds and sub-500ms latency for real-time checking. A **citation-enforced RAG framework** (arXiv 2603.14170) demonstrates source-first ingestion with explicit citation enforcement and an abstention mechanism — the system declines to answer rather than generate unsupported claims. The **FINOS AI Governance Framework** (AIR-DET-013) provides an ISO 42001-aligned control framework specifically for citation traceability in financial AI systems, covering design for citability, presentation, quality assessment, and citation integrity over time.

McKinsey's Lilli implements **system-level citation** (the gold standard): the system retrieves documents, the AI generates, and then a separate verification process maps claims back to sources with independent attribution scoring. Erik Roth confirmed: "We go full attribution — every answer carries citations and page numbers." This is fundamentally different from prompt-based citation where the LLM self-reports its sources, which the Tow Center at Columbia found **fails in over 60% of tests** across all major AI tools (Perplexity best at 37% failure rate, ChatGPT at 67%, Grok-3 at 94%).

**Keystone's citation architecture should follow five layers:**

1. **Source Layer**: Chunk-level metadata (document ID, page, section, URL, date) with stable unique IDs per chunk
2. **Research Agent Layer**: Outputs structured `{claim, source_chunk_id, confidence_score, cited_text}` objects using PROV-AGENT model
3. **Synthesis Layer**: Maintains source chains — every analytical claim inherits citations from supporting findings
4. **Generation Layer**: Template-driven output with inline `[source_id]` notation, using cite-or-abstain prompts
5. **Verification Layer**: Separate agent (different model, different prompt) maps output claims back to sources, applying Google Check Grounding API pattern

---

## Anti-slop enforcement demands a multi-agent quality pipeline

Template-driven generation **decisively outperforms** free-form generation for consulting deliverables. Evidence is consistent across multiple independent evaluations: Beautiful.ai's constrained "Smart Slides" reduce creation time by 75% while preventing broken formatting; Templafy cuts enterprise proposal creation from 4 hours to 20 minutes through approved templates; and an ex-McKinsey consultant testing AI tools found that Microsoft Copilot output required **30–45 minutes of reformatting per deck** to meet consulting standards because "Copilot creates generic business slides, not MBB-style structured arguments."

The **Antislop Sampler** (arXiv 2510.15061) provides the most rigorous technical approach: backtracking-based suppression of 8,000+ unwanted patterns at inference time, with a companion fine-tuning method (FTPO) that achieves **90% slop reduction** while maintaining performance on GSM8K and MMLU benchmarks. Research shows some LLM patterns appear 1,000× more frequently in AI output versus human text.

For pipeline-level enforcement, the **Anti-Slop System (ASS) v3.0** on GitHub implements a four-agent architecture directly applicable to Keystone: a naive Drafter produces baseline content, a brutal Slop Detector rates slop 1–10 identifying generic openings, listicle structures, excessive hedging, and corporate buzzwords, a Redraft Specialist rewrites using original prompt context plus slop feedback, and a Quality Arbiter provides final approval or triggers another iteration. The key design principle: the drafter stays intentionally naive while the detector is maximally critical.

**TraycerAI's anti-drift patterns** add practical production guardrails: separate verification agents with "fresh eyes" (different model, no investment in defending original output), threshold-based loop prevention, persistent state for failure recovery, and explicit scope constraints keeping agents focused.

For Keystone, anti-slop enforcement should operate at three stages. **Pre-generation**: template constraints defining required sections, content density minimums, and banned phrase lists. **During generation**: cite-or-abstain prompts, no general knowledge allowed, specific terminology requirements. **Post-generation**: the four-agent quality pipeline (Drafter → Slop Detector → Redraft Specialist → Quality Arbiter) plus style guide enforcement via NLP model and automated design token auditing.

---

## Multi-agent systems and the right output mix

**Manus** (acquired by Meta for $2–3B in December 2025) demonstrated the viability of large-scale parallel research agents, processing **14.7 trillion tokens** and reaching $125M ARR within 8 months. Its architecture — Planner Agent, Execution Agent, Verification Agent with "Wide Research" deploying parallel sub-agents across sources — directly informs Keystone's design. However, a16z benchmarks found Manus produced stronger analysis than ChatGPT Agent but **Gamma beat it on visual design** for presentations, confirming that content quality and visual quality require separate optimization.

For orchestration, **CrewAI** (15,200 stars, 1.3M+ monthly PyPI installs, 60%+ Fortune 500 adoption) is the strongest open-source framework. Its role-based agent model — Researcher, Writer, Analyst, Designer — maps directly to Keystone's pipeline stages. **LangGraph** provides an alternative with graph-based state machines and durable execution, and its Open Deep Research implementation scored #6 on the Deep Research Bench.

The Deep Research landscape confirms the research engine options for Keystone's upstream pipeline. **Google Gemini Deep Research** leads on benchmarks (46.4% on Humanity's Last Exam) and offers the broadest output format support — structured reports, Google Docs export, Audio Overview, and interactive Canvas. Its API is available via the Interactions API. **OpenAI Deep Research** provides API access via Responses API (o3-deep-research, o4-mini-deep-research) with MCP tool integration and structured output prompting. Neither produces PPTX or dashboards natively — both output Markdown/text, confirming that Keystone's multi-format rendering layer fills a real gap.

The proposed output mix of **Markdown research brief + PPTX executive deck + interactive dashboard** is validated by the evidence, with refinements. Storydoc data from 100,000+ sessions shows interactive reports receive **21% more time spent, 41% higher completion, and 2.3× more internal sharing** versus static documents. Yet PowerPoint remains "the primary currency of value delivery" in consulting. The recommended five-format stack:

1. **Structured Markdown + JSON**: Internal knowledge base and source of truth
2. **Branded PPTX** (10–15 slides): C-suite presentation via python-pptx + template system
3. **Branded PDF**: Analyst-level depth with citations via Typst or Pandoc + WeasyPrint
4. **Interactive web report**: Stakeholder engagement with tracking via Streamlit or custom HTML
5. **Audio brief**: Executive consumption via NotebookLM-pattern narration or deck2video

---

## Conclusion: the generation layer architecture

The research reveals a clear architectural prescription for Keystone's Layer 3. **Template-driven generation with citation-enforced content injection** is the only pattern that produces consulting-usable output — free-form AI generation universally requires 25–30% rework at leading firms. The tooling stack is mature enough to build on: Anthropic's Skills API for document rendering, PPTAgent/DeepPresenter for AI-native slide creation, Vizro for consulting-grade visualization styling, and PROV-AGENT for multi-agent citation propagation.

Three novel insights emerge from synthesizing across all eight research areas. First, the **visual consistency problem is solved** by LLM-readable design token systems with automated audit scripts — not by better prompting, but by architectural constraints that remove formatting decisions from the model entirely. Second, **system-level citation verification** (where a separate agent independently maps claims to sources) is non-negotiable — prompt-based self-citation fails in 60%+ of cases per Columbia's Tow Center research. Third, the **competitive moat** for Keystone lies not in any single capability but in the integration: no existing system combines parallel deep research, citation-traced synthesis, multi-format rendering, and anti-slop enforcement into a single pipeline. McKinsey's Lilli comes closest but operates only within McKinsey's walled garden and costs ~£8,000 per user per year. An open system achieving comparable quality at lower cost and broader accessibility would be genuinely category-defining.