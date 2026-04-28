# Architecture Overview

The Keystone Intelligence Engine implements **DPVI** — Decompose, Parallelize, Verify, Iterate — a workflow pattern independently discovered by four organizations building production AI systems. The convergent discovery validates the pattern's universality: the only way to get reliable output from language models is to break problems into independent pieces, execute them in isolation, verify every output against explicit criteria, and feed quality signals back.

## Pipeline Flow

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │                       RESEARCH QUESTION                             │
 │  "Evaluate the competitive landscape of US auto body repair         │
 │   across the top 10 metropolitan areas..."                          │
 └──────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  LAYER 0: SPECIFICATION ENGINE                                       │
 │                                                                      │
 │  1. Classify engagement on two axes:                                 │
 │     - Analytical mode (evaluative, strategic, exploratory, etc.)     │
 │     - Subject domain (business, technical, scientific, etc.)         │
 │  2. Clarify intent → generate falsifiable Day-1 Hypothesis           │
 │  3. Run 3 analytical lenses in parallel (currently: financial,       │
 │     operational, market) — each produces an independent tree          │
 │  4. Synthesize lens trees into unified MECE issue tree               │
 │  5. Validate mutual exclusivity and collective exhaustiveness         │
 │  6. Generate research tasks with acceptance criteria from tree leaves │
 │                                                                      │
 │  IN:  natural language question                                      │
 │  OUT: classification JSON, intent clarification JSON,                │
 │       issue tree JSON, tasks JSON                                    │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │  HITL GATE 1  │  Human reviews issue tree
                        │  (mandatory)  │  and task list before
                        └───────┬───────┘  research begins
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  LAYER 1: PARALLEL RESEARCH AGENTS                                   │
 │                                                                      │
 │  One agent per task, all running concurrently in strict isolation     │
 │  (no agent sees another's intermediate findings).                     │
 │                                                                      │
 │  Deep mode (DEEP_RESEARCH=1): each agent runs a single claude -p     │
 │  session with WebSearch/WebFetch. Takes 5-20 minutes per agent.       │
 │  Produces 20-30 claims with real source URLs.                         │
 │                                                                      │
 │  Shallow mode (default): iterative tool-call loop up to 5 rounds.    │
 │  Tools dispatched through MCPGateway with auth, rate limiting, and    │
 │  circuit breaker. Currently uses MockMCPClient — real MCP servers     │
 │  not yet connected.                                                   │
 │                                                                      │
 │  Both modes: structured claims with citations as required fields      │
 │  (not optional), confidence scores, explicit caveats, and absence     │
 │  reports listing what evidence was sought but not found.              │
 │                                                                      │
 │  IN:  task description + acceptance criteria + tool assignments       │
 │  OUT: StructuredFinding per agent (claims, citations, absence report) │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  CITATION PROCESSOR                                                  │
 │                                                                      │
 │  Cross-agent deduplication via union-find on URLs and DOIs.           │
 │  Replaces per-agent CIT-* IDs with canonical CAN-* IDs.              │
 │  URL liveness verification. Corroboration scoring.                    │
 │  Produces citation manifest for downstream reasoning.                 │
 │                                                                      │
 │  IN:  per-agent findings with raw citations                          │
 │  OUT: deduplicated citation manifest + corroboration scores          │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  LAYER 1.5: DELIBERATION                                             │
 │                                                                      │
 │  4 analyst agents independently analyze findings using different      │
 │  methodologies: Analysis of Competing Hypotheses, quantitative        │
 │  modeling, adversarial critique, historical analogy. Zero inter-agent │
 │  communication. A FLAGSHIP-tier aggregator reads all independent      │
 │  analyses, identifies convergent findings and genuine disagreements,  │
 │  produces a five-tier confidence map. Low-confidence claims get a     │
 │  "What Would Have To Be True" challenge.                              │
 │                                                                      │
 │  IN:  citation manifest + corroborated findings                      │
 │  OUT: confidence map (consensus / contested / gaps)                  │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │  HITL GATE 2  │  Human reviews confidence
                        │  (mandatory)  │  map before generation
                        └───────┬───────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  LAYER 2: CONTENT STRUCTURING                                        │
 │                                                                      │
 │  Builds StructuredOutline: executive summary → analytical framework   │
 │  → per-branch findings → uncertainty areas → evidence gaps → absence. │
 │  Selects analytical frameworks based on engagement type (e.g.,        │
 │  Porter's Five Forces for evaluative, scenario planning for           │
 │  strategic). Generates per-task sprint contracts defining quality      │
 │  criteria the evaluator will score against. Drafts per-task section   │
 │  text with lede, evidence chain, and analytical significance.         │
 │                                                                      │
 │  IN:  confidence map + findings + spec + tasks                       │
 │  OUT: StructuredOutline + section text + sprint contracts             │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  LAYER 4: EVALUATION (5-layer internal stack)                        │
 │                                                                      │
 │  Runs per-task, fresh evaluator instance each time.                   │
 │                                                                      │
 │  L1: Deterministic checks — FActScore fact extraction, numerical      │
 │      consistency, URL liveness. STANDARD-tier LLM for extraction.     │
 │  L2: Citation gate — any fabricated citation = immediate rejection.   │
 │      Purely deterministic, no LLM call.                               │
 │  L3: 10-dimension rubric scoring — each dimension scored in a         │
 │      separate prompt to prevent cross-contamination. Scores           │
 │      aggregated via weighted geometric mean (a zero on any dimension  │
 │      produces a near-zero composite). FLAGSHIP-tier LLM.             │
 │  L4: Process trajectory — scores how the agent worked (tool           │
 │      utilization, source diversity, issue tree coverage). Optional,   │
 │      runs only when process context is available. Blended with L3     │
 │      at 80/20 weighted geometric mean.                                │
 │  L5: Cross-model ensemble — 2-3 independent judges re-score via L3.  │
 │      Scores aggregated by median. Minority dissenter veto: if any     │
 │      judge scores a Tier 1 dimension below floor, composite forced    │
 │      to 0.0 regardless of other judges. Optional, skipped for         │
 │      LIGHT_TOUCH intensity.                                           │
 │                                                                      │
 │  IN:  structured output + sprint contract + process context          │
 │  OUT: composite score + per-dimension feedback + pass/fail           │
 └──────────────────────────────┬───────────────────────────────────────┘
 │                                                                      │
 │  Governance gates: l0_mece_failed, l1_tool_dead_letter,              │
 │  l1_cost_ceiling, l1_degraded_dispatch, l5_ensemble_dissenter_veto,  │
 │  l5_ensemble_degraded_panel, l5_low_agreement — any ESCALATE-level   │
 │  gate halts the pipeline.                                             │
 └──────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  MARKDOWN RENDERER                                                   │
 │                                                                      │
 │  Outline-driven: executive summary, analytical framework, key         │
 │  findings per branch with evidence tiers, areas of uncertainty        │
 │  (moderate / weak / contested), evidence gaps, absence report,        │
 │  evaluation summary with per-dimension averages, numbered sources     │
 │  aligned with inline [N] citation refs.                               │
 │                                                                      │
 │  Only renders findings that PASSED evaluation. Governance-halted      │
 │  or failed findings are excluded.                                     │
 │                                                                      │
 │  IN:  evaluated findings + filtered outline + filtered confidence map │
 │  OUT: final_brief.md                                                 │
 └──────────────────────────────────────────────────────────────────────┘
```

## The 10-Dimension Evaluation Rubric

Scores are aggregated via **weighted geometric mean** — a zero on any dimension produces a near-zero composite score. This is by design: excellence on nine dimensions cannot mask failure on one.

Weights are calibrated away from where LLMs naturally perform well (coherent prose, comprehensive coverage) and toward where they underperform (analytical novelty, quantitative rigor, actionable insight).

| # | Dimension | Weight | Tier | What It Measures |
|---|-----------|--------|------|-----------------|
| 1 | Intent Alignment | 15% | 1 | Does the output answer the question that was asked? |
| 2 | Quantitative Rigor | 15% | 1 | Are numerical claims specific, sourced, and internally consistent? |
| 3 | Actionability | 15% | 1 | Could a decision-maker act on these findings Monday morning? |
| 4 | Analytical Depth | 12% | 1 | Multi-layer reasoning, not just surface-level claims? |
| 5 | Intellectual Honesty | 10% | 1 | Are limitations acknowledged, counter-evidence surfaced? |
| 6 | Source Quality | 10% | 1 | Authoritative, diverse, current sources? |
| 7 | Narrative Coherence | 8% | 2 | Clear analytical narrative with a "so what?" |
| 8 | Completeness | 8% | 2 | Coverage of the research specification's scope? |
| 9 | Calibrated Confidence | 5% | 2 | Do confidence levels match the strength of evidence? |
| 10 | Evaluative Surprise | 2% | 2 | Non-obvious insights that a domain expert would find valuable? |

**Tier 1** dimensions (Intent Alignment, Quantitative Rigor, Actionability, Analytical Depth, Intellectual Honesty, Source Quality) carry 77% of total weight and trigger the cross-model ensemble's dissenter veto: if any single judge scores a Tier 1 dimension below floor, the entire evaluation is rejected regardless of other scores.

**Tier 2** dimensions (Narrative Coherence, Completeness, Calibrated Confidence, Evaluative Surprise) carry 23% and cannot trigger a veto. These are dimensions where LLMs naturally perform well — they contribute to the score but don't gate the output.

The rubric also has **type-specific weight overrides** for different intelligence products. Estimative intelligence (ICD 203-style) increases Calibrated Confidence and Quantitative Rigor while decreasing Completeness and Narrative Coherence. Current intelligence increases Source Quality and Completeness while decreasing Quantitative Rigor and Evaluative Surprise.

## Key Architectural Principles

**Structure over intent.** Quality is enforced architecturally, not through prompt instructions that drift ~40% of the time. Citations are required Pydantic model fields — uncited claims cannot be produced. Tools are enforced by the MCP Gateway — agents cannot access unauthorized tools. Geometric mean scoring makes quality failures mathematically unforgeable.

**The specification layer is the system.** The same model scores 78% or 42% depending solely on the quality of the specification surrounding it. The Specification Engine — which translates vague questions into precise research plans — is the highest-leverage component in the system.

**Evaluation is more important than generation.** The five-layer evaluation stack is the most carefully engineered component. By design, the evaluation stack is the most token-intensive part of the pipeline — verification matters more than generation for determining whether output can be trusted.

**Dual-axis domain classification.** A recent architectural addition: L0 now classifies questions on two axes — analytical mode (evaluative, strategic, exploratory, diagnostic, sizing) and subject domain (business, technical, scientific). Downstream components (methodology selection, source requirements, non-goals, analytical frameworks) adapt based on both axes. This was added after the first run exposed that consulting-domain defaults broke on non-business questions.
