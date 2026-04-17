# Keystone Intelligence Engine: Full Product Vision & Roadmap

> Status: roadmap / intent draft. Not current-state truth or a delivery commitment.
> Read `AUTHORITY-INDEX.md`, `SESSION-STANDARD.md`, and the control-plane pair first.
> `Current State` sections below are planning snapshots used to frame future gaps; for what is built, cleared, or authorized now, use the control-plane pair and code/tests.

*Captured: 2026-04-09 | From planning session with orchestrator agent*
*Status: Draft for future development planning. Not yet synthesized into architecture-and-evolution.md.*

---

## What the MVP Has vs. What the Final Product Needs

The MVP is the **analytical engine**: the pipeline that takes a question and produces a researched answer. The architecture is evidence-driven, the evaluation is structural, the agent isolation is real. This is the part most AI companies get wrong because they focus on UI and skimp on the reasoning layer.

What's missing is everything around the engine: the user interface, the production retrieval stack, the self-improvement system, rich output generation, and production infrastructure.

---

## Gap 1: User Interface

### Current State
CLI only. Everything runs from terminal/tests. No web interface for HITL review gates. No dashboard for monitoring pipeline progress. No way for non-technical users to interact.

### Vision: Cowork Meets Perplexity Meets Linear

**Input experience:** Clean web interface. Consultant types a research question, selects engagement type from a dropdown, adjusts pipeline depth with a slider (Light / Standard / Deep), optionally adds client context, hits "Start Research."

**Pipeline transparency (the Cowork model):** Real-time visualization of what's happening:
- Which stage is active (Specification -> Research -> Citation Processing -> Deliberation -> Evaluation)
- Within each stage, what the agents are doing ("Agent 2: Searching Exa for 'automotive sensor market LiDAR vs camera'")
- Streaming intermediate output
- Token consumption and estimated time remaining

**HITL gates as first-class UI elements:**
- Issue tree rendered as interactive, expandable/collapsible diagram
- Task list with drag-and-drop prioritization
- Agent assignments with rationale
- Approve / Modify / Reject with inline editing
- Confidence map as visual: green/yellow/orange/red with expandable rationale

**Results as a document:**
- Citation footnotes linking to actual sources
- Confidence indicators on each claim (color-coded)
- Expandable "Why we believe this" evidence chains
- WWHTB challenges as callout boxes
- Evaluation radar chart (10 dimensions)
- One-click export to PDF, DOCX, slides

**Settings panel:**
- Toggle MECE decomposition on/off
- Set agent count (1-7), research rounds (1-5)
- Choose evaluation intensity
- API key management
- Observation Library browser
- Past engagement history

### Technology Stack
- **Frontend:** Next.js + Tailwind + shadcn/ui
- **Real-time:** WebSocket streaming pipeline events (typed events already exist in events.py)
- **Backend:** FastAPI (already have it for HITL; extend for full pipeline)
- **Visualization:** D3.js for issue tree, radar charts for evaluation
- **Estimate:** 3-4 weeks for someone comfortable with React/Next.js

### OpenCode/Claude Code Patterns to Borrow
- Streaming architecture (real-time agent output to UI)
- Multi-panel layout (main content + sidebar context + status bar)
- Agent progress tracking
- File management patterns

### Patterns NOT to borrow (different user base)
- Terminal aesthetic
- Keyboard-shortcut-heavy interaction
- Developer-centric framing

---

## Gap 2: Production Retrieval Stack (Component #3a)

### Current State
Exa and Brave search APIs via SimpleMCPClient. Effective for web research but limited to what these services index. No vector database, no embeddings, no hybrid search, no reranking.

### What Was Researched and Spec'd (CAPSTONE-PLAN-v2.md Section 6.2)

**pgvector + Voyage-finance-2 embeddings.** 49% improvement over general-purpose embeddings on financial QA (FinMTEB benchmark, EMNLP 2025). Domain-specific embeddings are non-negotiable for financial documents.

**Hybrid search (dense + BM25 + RRF).** 26-31% NDCG improvement over dense-only retrieval (BEIR aggregate benchmarks). Financial documents with exact figures need keyword matching, not just semantic similarity.

**Cohere Rerank v3.5.** Cross-encoder reranking. Top 150 from hybrid search -> top 20 delivered to agent.

**Contextual retrieval at ingest.** Anthropic's pattern: Haiku-generated contextual preamble on each chunk before embedding. 67% reduction in retrieval failures. Free on Claude Max.

**Docling for PDF parsing.** 87.7% accuracy on structure-aware PDF parsing. Tables preserved as structured data.

**Query classification routing.** Quantitative -> Text2SQL. Qualitative -> vector search. Hybrid -> both paths merged via RRF. Classification via cheap Haiku call (<200ms).

**Three-source federation.** Public (Exa, Brave, EdgarTools, FRED, academic papers), internal (Keystone's past deliverables), historical (past engagement findings). Single coherent result set per agent.

### Assessment
All technologies still validated by research. The spec is detailed enough to build from. Main dependency: PostgreSQL infrastructure. Estimate: 2-3 weeks.

---

## Gap 3: Self-Improvement System (META Layer)

### Current State
Empty Observation Library. Filesystem wiki exists (Component #3b) but nothing learns yet.

### Vision

**Observation Library as CBR (Case-Based Reasoning):**
- After every engagement: extract heuristic observations, structural constraints, client calibrations
- R4 cycle: Retrieve similar past cases at engagement start, Reuse patterns, Revise based on new findings, Retain updated knowledge
- Five-tier knowledge artifact hierarchy: raw observations -> filtered heuristics -> validated patterns -> promoted principles -> skill file integration

**Trajectory storage.** Decision logs, source quality ratings, framework effectiveness. Specification Engine queries this for new engagements.

**Darwinian prompt evolution.** After 5-10 engagements, systematically optimize prompts using GEPA/DSPy. Best-performing prompts survive.

**Client calibration profiles.** Per-client preferences, terminology, formats, risk tolerance. Every interaction improves the next.

---

## Gap 4: Rich Output Generation (Layers 2 and 3)

### Current State
Markdown renderer only. No consulting frameworks applied. No formatted deliverables.

### Vision

**Layer 2: Content Structuring.** Claim-level inputs from Deliberation. Consulting analytical frameworks applied. Sprint contracts negotiated with Evaluator before generation.

**Layer 3: Deliverable Generation.** PowerPoint (Vizro/PPTAgent), Excel models, formatted PDF. Anti-slop enforcement (Antislop Sampler, 8K+ patterns, 90% reduction). Redraft Specialist subagent.

---

## Gap 5: Evaluator Completion

### Current State
Layers 1-3 built. 4 evaluation profiles. Not calibrated against human scores.

### Vision

**Calibration.** 0.80+ Spearman rank correlation against Jack's scores on 10+ outputs. Anthropic's production standard.

**Layer 4:** Process trajectory evaluation (Agent-as-a-Judge on the research process, not just output).

**Layer 5:** Diverse judge ensemble (PoLL pattern, 2-3 model families, minority veto).

**8-10 evaluation profiles.** Operations, M&A, restructuring, growth, competitive intelligence, regulatory, technology assessment.

---

## Gap 6: Infrastructure

**Temporal** for durable execution. Crash recovery, long-running workflows, visibility.

**PostgreSQL** for persistent state. Multi-user, proper HITL, Observation Library, pgvector.

**Authentication and multi-tenancy.** User auth, client-scoped data isolation, role-based access, audit logging.

---

## Everything Deferred: Priority Assessment

| Item | Impact | Priority | Effort | Notes |
|------|--------|----------|--------|-------|
| **User Interface (web)** | Transforms adoption | P0 | XL (3-4 wk) | The single biggest product gap |
| **Casing book skill file** | Professional-grade MECE | P1 | M | Opus 1M session on uploaded books |
| **TiCoder divergence detection** | 40%->84% intent alignment | P1 | S | Add to intent_clarifier.py |
| **ADaPT reactive decomposition** | +28.3% over static planning | P1 | M | Extends feedback loop |
| **Anti-slop enforcement** | Eliminates biggest quality complaint | P1 | M | Antislop Sampler + Redraft subagent |
| **Component #3a full retrieval** | Non-negotiable for financial docs | P1 | XL (2-3 wk) | pgvector + Voyage + hybrid search |
| **CBR Observation Library** | The learning flywheel | P1 | L | Needs populated library |
| **PowerPoint generation** | Transforms consultant adoption | P1 | L | Vizro/PPTAgent evaluation needed |
| **Evaluator calibration** | Makes scores meaningful | P1 | M | Needs 10+ Jack-scored outputs |
| **VOI priority scoring** | Better task prioritization | P2 | S | Replace heuristic scorer |
| **8-10 evaluation profiles** | Diverse engagement support | P2 | M | Needs calibration data |
| **Sprint contract negotiation** | Better generator output | P2 | M | Bidirectional Evaluator-Generator |
| **Cross-engagement wiki** | Institutional memory | P2 | M | Anonymized pattern promotion |
| **Dimension-specific verification** | Strongest eval dimensions | P2 | M | Programmatic QR, position-switching |
| **Evaluator Layers 4-5** | 60-68% ceiling breakthrough | P2 | L | Process trajectory + ensemble |
| **Client calibration profiles** | Comprehension flywheel | P2 | M | Per-client preferences |
| **Trajectory storage** | Feeds self-improvement | P2 | M | Decision logs, effectiveness tracking |
| **Reusable analytical modules** | Immediate product value | P2 | L | 10 consulting framework skill files |
| **Temporal workflow engine** | Production reliability | P2 | L | Crash recovery, long-running |
| **PostgreSQL migration** | Multi-user, persistence | P2 | M | Replace aiosqlite |
| **Flexon problem archetypes** | Better retrieval matching | P3 | S | Part of casing skill file |
| **Causal inference agent** | White-space capability | P3 | L | CausalAgent + DoWhy |
| **Darwinian prompt evolution** | Systematic optimization | P3 | L | Needs 5-10 engagements of data |
| **Scheduled research pipelines** | Recurring intelligence service | P3 | M | Future service model |
| **Excel model generation** | Extends output types | P3 | L | Lower priority than PPT |

---

## Phased Build Roadmap

### Phase 2A: Quality Depth (2-3 weeks)
- Casing book skill file (Directive 12)
- TiCoder divergence detection
- ADaPT reactive decomposition
- Anti-slop enforcement
- Full citation metadata enrichment
- Evaluator calibration (concurrent with Jack scoring outputs)

### Phase 2B: Retrieval + Infrastructure (2-3 weeks, parallel with 2A)
- PostgreSQL setup
- pgvector + Voyage-finance-2 + hybrid search
- Docling PDF ingestion
- Cohere Rerank integration
- Temporal workflow engine

### Phase 2C: UI (3-4 weeks, parallel)
- FastAPI backend extension
- Next.js frontend: input, pipeline progress, HITL review, results
- WebSocket bridge for real-time events
- Issue tree interactive visualization
- Export to PDF/DOCX

### Phase 3: Self-Improvement + Polish (4-6 weeks)
- Observation Library CBR
- Trajectory storage
- Client calibration profiles
- Evaluator Layers 4-5 + 8-10 profiles
- Sprint contract negotiation
- PowerPoint generation (Layer 3a)
- Cross-engagement knowledge base

### Phase 4: Evolution (ongoing)
- Darwinian prompt evolution
- Causal inference agent
- Scheduled research pipelines
- Reusable analytical modules
- Internal document integration

---

## The Product in One Paragraph

The best version of the Keystone Intelligence Engine is not an AI tool. It is an AI analyst that a consultant works with the way they'd work with a junior analyst, except it never sleeps, never forgets, and gets better with every engagement. A consultant types a research question into a clean web interface. Watches agents fan out across data sources in real time. Reviews and adjusts the research plan at structured checkpoints. Receives a consulting-quality brief with traced citations, calibrated confidence, and honest uncertainty. Exports to PowerPoint with one click. And after the engagement closes, the system extracts what it learned and applies it to the next engagement. The engine for all of this is built. Now it needs a body, a face, and a memory.
