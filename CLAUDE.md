# Keystone Intelligence Engine

Multi-agent consulting research pipeline. Takes a question, decomposes via MECE issue trees, dispatches parallel research agents, deliberates with confidence mapping, evaluates against a 10-dimension rubric, renders a source-cited analytical brief.

## Stack

Python 3.11+ · Pydantic v2 · async throughout · pytest + pytest-asyncio
ruff (lint/format) · mypy (strict) · SQLAlchemy + aiosqlite (HITL gates)

## Key Directories

```
src/keystone/
  pipeline/        orchestrator.py (main entry), markdown_renderer.py
  specification/   L0: spec_engine, task_generator, engagement_classifier
  research/        L1: agent_pool, research_agent, context_loader
  citation/        CitationProcessor: cross-agent dedup, corroboration
  deliberation/    L1.5: analyst, aggregator, confidence mapping
  evaluator/       L4: 3-layer eval stack, rubric, sprint contracts
  governance/      execution policy, halt/flag logic
  gateway/         MCP gateway, tool registry, auth, circuit breaker
  models/          Pydantic models shared across layers
tests/
  unit/            mirrors src/ structure
  integration/     full pipeline tests (require API keys)
  canary/          architectural guarantee tests
```

## Commands

```bash
source .venv/bin/activate
pytest tests/unit/ -x --tb=short       # unit tests (fast, no API keys)
ruff check src/ tests/                  # lint
ruff format src/ tests/                 # auto-format
mypy src/                               # type check (strict)
```

## After Every Code Change

1. `ruff format` on changed files
2. `pytest tests/unit/ -x --tb=short`
3. `ruff check src/ tests/`

## Pipeline Flow

L0 (SpecEngine) → L1 (AgentPool) → CitationProcessor → L1.5 (Deliberation) → L4 (Evaluator) → Renderer

Each stage yields typed `AnyPipelineEvent`. Governance can halt at any stage.
HITL gates fire in SpecEngine and Deliberation when `db_session_factory` is provided.

## Conventions

- Pipeline components: async generate/process → `get_result()` pattern
- Models: Pydantic v2 `BaseModel` with strict validation
- Tests mock LLM calls — never hit real APIs in unit tests
- New components MUST yield `AnyPipelineEvent` for observability
- Use `from keystone.models.X import Y`, not star imports

## What's Built vs Not

- Core pipeline (L0 → L4 → Render): **BUILT**, 800 unit tests pass
- Lane H (governed document fetch): **BUILT**, at commit `93a5ca8`
- Lane E (article/PDF parse + evidence normalization): **NOT BUILT** — next feature
- No `src/keystone/retrieval/` directory exists yet

## Gotchas

- `openai` SDK is the LLM client (historical). Anthropic SDK migration is separate work.
- `DEEP_RESEARCH=1` env var switches L1 agents to multi-turn web research mode
- 22 git worktrees exist from prior sessions. This worktree is the active primary.
- `audit/` and `research/` directories are historical reference only — do not read them for building context. Their findings are already incorporated in the codebase.

## Session Continuity

- Update `HANDOVER.md` at end of each session
- Append failure patterns to `notes/LESSONS.md`
- Active work tracked in `TODO.md`

## Architecture Reference

Use `/architecture` skill for deep DPVI pipeline details, component contracts, and design rationale. Use `CAPSTONE-PLAN-v2.md` for the full specification.
