# The Keystone Intelligence Engine

**Jack Riddle | IU Kelley School of Business | Econ Consulting Capstone | Prof. Youle | Spring 2026**

A multi-agent AI system that takes a research question and autonomously produces a source-cited analytical brief. Built for The Keystone Group, a boutique consulting firm. The target: match the depth and rigor of a McKinsey team spending a week on the same question.

## How It Works

```
Question → L0 Specification → L1 Research → Citation Processing → L1.5 Deliberation → L2 Structuring → L4 Evaluation → Brief
```

**L0 Specification Engine** classifies the question on two axes (analytical mode + subject domain), generates a falsifiable Day-1 Hypothesis, decomposes it via three independent analytical lenses into a MECE issue tree, validates the tree, and generates research tasks with explicit acceptance criteria and anti-confirmatory framing.

**L1 Research Agents** execute tasks in parallel with strict isolation (no agent sees another's work). Deep mode: each agent runs a multi-turn web research session searching the live web, reading full pages, following citations. Produces structured claims with required citation fields — uncited claims cannot exist.

**Citation Processor** deduplicates citations across agents via union-find on URLs/DOIs, checks URL liveness, and builds a canonical citation manifest.

**L1.5 Deliberation** spawns 4 independent analyst agents using different methodologies (Analysis of Competing Hypotheses, quantitative modeling, adversarial critique, historical analogy). Zero inter-agent communication. A FLAGSHIP-tier aggregator produces a five-tier confidence map. Low-confidence claims receive a "What Would Have To Be True" challenge.

**L2 Content Structuring** builds the analytical outline, selects domain-appropriate frameworks, generates per-task sprint contracts, and drafts section text.

**L4 Evaluation** is a five-layer stack: deterministic fact-checking → binary citation gate (fabricated citation = instant rejection) → 10-dimension rubric scoring via weighted geometric mean → process trajectory assessment → cross-model ensemble with minority dissenter veto.

**Markdown Renderer** produces the final brief from evaluated, filtered findings.


## Current Status of testing on the **updated** components:

| Layer | Real Data Status |
|-------|-----------------|
| L0 Specification | Completed — MECE issue tree, hypothesis, 13 tasks |
| L1 Research | 6 of 13 agents completed (155 claims, real web sources) |
| Citation Processor | Completed — 155 live URLs, 18 dead, 0 fabricated |
| L1.5 Deliberation | Not yet completed (timeout issue, fix committed) |
| L2 Structuring | Not yet tested on real data |
| L4 Evaluation | Not yet tested on real data |
| Renderer | Not yet tested on real data |

The current version of the system has not completed a full end-to-end run. L0 and L1 decent outputs. The downstream layers are built and unit-tested (1,584 tests pass) but have not yet processed real research data due to timeout issues that are actively being fixed. See [`docs/deliverable/KNOWN-ISSUES.md`](docs/deliverable/KNOWN-ISSUES.md) for every issue with root cause analysis and lessons learned.

## The 10-Dimension Evaluation Rubric

Scores aggregate via weighted geometric mean — a zero on any dimension produces a near-zero composite.

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Intent Alignment | 15% | Does the output answer the question that was asked? |
| Quantitative Rigor | 15% | Are numerical claims specific, sourced, and consistent? |
| Actionability | 15% | Could a decision-maker act on these findings? |
| Analytical Depth | 12% | Multi-layer reasoning, not just surface-level claims? |
| Intellectual Honesty | 10% | Are limitations acknowledged, counter-evidence surfaced? |
| Source Quality | 10% | Authoritative, diverse, current sources? |
| Narrative Coherence | 8% | Clear analytical narrative with a "so what?" |
| Completeness | 8% | Coverage of the research specification's scope? |
| Calibrated Confidence | 5% | Do confidence levels match the evidence strength? |
| Evaluative Surprise | 2% | Non-obvious insights a domain expert would value? |

## Running It

```bash
git clone https://github.com/VenialShrimp339/Keystone-Intelligence-Engine.git
cd Keystone-Intelligence-Engine
git checkout codex/owner-triage-normalization
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run all 1,584 unit tests (~57 seconds, no API keys needed)
pytest tests/unit/ -x --tb=short

# Run the pipeline (requires Claude Max subscription)
unset ANTHROPIC_API_KEY
DEEP_RESEARCH=1 python scripts/full_pipeline_test.py
```

See [`docs/deliverable/SETUP-GUIDE.md`](docs/deliverable/SETUP-GUIDE.md) for full instructions including how to resume from existing findings.

## Exploring with an AI Agent

If you're using Claude Code, Codex, or another AI coding agent:

1. Read `CLAUDE.md` first — it's the project map
2. Key entry points:
   - `src/keystone/pipeline/orchestrator.py` — main pipeline (`Pipeline.run_with_events()`)
   - `src/keystone/specification/` — L0 (decomposer, classifier, task generator)
   - `src/keystone/evaluator/` — L4 five-layer evaluation stack
   - `src/keystone/models/` — Pydantic models (the type system IS the pipeline's nervous system)
   - `src/keystone/contracts.py` — explicit handoff contracts between layers

## Project Scale

| Metric | Value |
|--------|-------|
| Production source files | 129 Python files |
| Unit tests | 1,584 passing |
| Pipeline prompts | 38 `.md` files + 8 inline |
| Evaluation dimensions | 10 (geometric mean) |
| Evaluation stack depth | 5 layers |
| Research domains | Dual-axis classification (analytical mode + subject domain) |

## Documentation

| Document | What It Contains |
|----------|-----------------|
| [`CAPSTONE-PLAN-v2.md`](CAPSTONE-PLAN-v2.md) | Full architectural vision (~1,500 lines) |
| [`JACK-ARCHITECTURAL-DIRECTIVES.md`](JACK-ARCHITECTURAL-DIRECTIVES.md) | 14 design decisions from the owner |
| [`docs/architecture-and-evolution.md`](docs/architecture-and-evolution.md) | How the architecture evolved (sent to Prof. Youle April 9) |
| [`docs/deliverable/`](docs/deliverable/) | Detailed status report, known issues, architecture diagrams |
| [`output/eng_74e67db162c7/`](output/eng_74e67db162c7/) | Actual pipeline output from the first run |
