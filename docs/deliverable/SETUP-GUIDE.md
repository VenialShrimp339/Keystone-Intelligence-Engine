# Setup Guide

Instructions for running the Keystone Intelligence Engine locally.

---

## Prerequisites

- **Python 3.11+**
- **Claude Max subscription** — the pipeline uses `claude -p` (Claude CLI) for LLM calls. The test scripts explicitly verify that `ANTHROPIC_API_KEY` is NOT set, because the pipeline is designed to run against the Claude Max subscription, not the pay-per-call API.

  ```bash
  # IMPORTANT: if you have an API key set, UNSET it — otherwise the
  # pipeline will bill to the API instead of Max
  unset ANTHROPIC_API_KEY
  ```

- **Git**

Optional (for the full retrieval stack, not required for the core pipeline):
- PostgreSQL 17 with pgvector 0.8.2 extension
- Voyage AI API key (`VOYAGE_API_KEY`)
- Cohere API key (`COHERE_API_KEY`)

## Installation

```bash
# Clone the repository
git clone https://github.com/VenialShrimp339/Keystone-Intelligence-Engine.git
cd Keystone-Intelligence-Engine

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running the Test Suite

```bash
# Run all 1,584 unit tests (~57 seconds)
pytest tests/unit/ -x --tb=short

# Run with verbose output
pytest tests/unit/ -v --tb=short

# Run a specific component's tests
pytest tests/unit/specification/ -v     # L0 Spec Engine
pytest tests/unit/evaluator/ -v         # L4 Evaluator (all 5 layers)
pytest tests/unit/deliberation/ -v      # L1.5 Deliberation
pytest tests/unit/research/ -v          # L1 Research Agents
pytest tests/unit/structuring/ -v       # L2 Content Structuring
pytest tests/unit/retrieval/ -v         # Retrieval stack (pgvector, BM25, etc.)
pytest tests/unit/gateway/ -v           # MCP Gateway (auth, rate limiting, etc.)
```

All unit tests mock LLM calls — they require no API keys, no network access, and no database connections. Three tests are expected failures (`xfail`), all others pass.

## Running the Pipeline

### Full pipeline (requires Claude Max)

```bash
source .venv/bin/activate

# Run the full pipeline with the default test question
# (auto body repair competitive landscape)
python scripts/full_pipeline_test.py
```

**What to expect:** L0 specification takes 5-10 minutes. L1 deep research takes 20-40 minutes per agent (13 agents run in parallel, but each one is expensive). A full run consumes significant Claude Max usage — the first run hit the daily limit after 6 of 13 agents completed.

**Current limitation:** The pipeline will likely complete L0 and L1, but may time out or hit usage limits in L1.5 deliberation. The most recent timeout fix (1200s for regular calls) has not yet been validated on a real run.

### Resume from existing findings

If the pipeline crashes or hits a usage limit, you can resume from the last checkpoint without repeating expensive L1 research:

```bash
python scripts/resume_from_l1.py
```

This loads saved L1 findings from `output/eng_74e67db162c7/l1_findings/` and re-runs CitationProcessor → Deliberation → Evaluator → Renderer.

### View existing output

The auto body repair run's output is saved in `output/eng_74e67db162c7/`:

```
output/eng_74e67db162c7/
├── l0_classification.json          # Engagement type + domain classification
├── l0_intent_clarification.json    # Day-1 Hypothesis, scoping, non-goals
├── l0_issue_tree.json              # MECE decomposition (6 branches, 13 leaves)
├── l0_tasks.json                   # 13 research task specifications
├── l1_findings/                    # Per-agent research output
│   ├── task_004.json               # Entry capital requirements (27 claims)
│   ├── task_005.json               # OEM certification analysis (25 claims)
│   ├── task_006.json               # Unit economics (26 claims)
│   ├── task_008.json               # Claim frequency & complexity (24 claims)
│   ├── task_012.json               # Workforce & training (28 claims)
│   └── task_013.json               # ADAS/EV disruption (25 claims)
├── citation_manifest.json          # Cross-agent citation dedup (first run)
└── citation_manifest_resumed.json  # Updated manifest from resume run
```

## Exploring with an AI Agent

If you're using Claude Code, Codex, or another AI agent to explore the repo:

1. **Read `CLAUDE.md` first** — it's the project map with directory structure, key commands, conventions, and known gotchas.

2. **Key source directories:**
   - `src/keystone/pipeline/orchestrator.py` — main pipeline entry point (`Pipeline.run_with_events()`)
   - `src/keystone/specification/` — L0 Specification Engine (decomposer, intent clarifier, task generator)
   - `src/keystone/research/` — L1 Research Agents (agent pool, research agent, deep mode, evidence context)
   - `src/keystone/deliberation/` — L1.5 multi-methodology deliberation
   - `src/keystone/structuring/` — L2 content structuring (framework selector, section text, sprint contracts)
   - `src/keystone/evaluator/` — L4 five-layer evaluation stack
   - `src/keystone/models/` — shared Pydantic models (the type system is the pipeline's nervous system)
   - `src/keystone/contracts.py` — explicit handoff contracts between pipeline layers
   - `src/keystone/gateway/` — MCP Gateway (auth, rate limiting, circuit breaker, tool registry)
   - `src/keystone/retrieval/` — pgvector + Voyage + BM25 + Cohere rerank

3. **The code is well-structured** with clear module boundaries. Each pipeline layer is self-contained. The Pydantic models in `src/keystone/models/` define the contracts between layers — start there to understand data flow.

4. **Prompt files** live in `*/prompts/*.md` within each layer's package. There are 38 of them. The evaluator has 15 prompt files (one per rubric dimension plus fact decomposition, gestalt overlay, process trajectory, and sprint contract generation).

## Linting and Type Checking

```bash
# Lint
ruff check src/ tests/

# Auto-format
ruff format src/ tests/

# Type check (strict mode, 129 files)
mypy src/
```
