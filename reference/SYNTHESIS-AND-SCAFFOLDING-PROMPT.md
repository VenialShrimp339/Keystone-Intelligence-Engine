# Pre-Build Session: Research Synthesis + Code Architecture + Project Scaffolding

## Your Mission

You are the final step between research and building. The Keystone Intelligence Engine has completed extensive research (16 original reports, 10 nano-claude-code analysis files, 10 deep research reports on the Claude Code leak). All architectural decisions have been validated. No changes are needed to the plan.

Your job is to:
1. Synthesize the unprocessed deep research reports against the existing analysis
2. Design the actual code architecture for the Keystone Intelligence Engine
3. Produce the foundational code files that every Phase 1 component depends on

**Work autonomously. Do not stop to ask questions. Every piece of context you need is in this project folder.**

## Context Loading Strategy

**Read immediately (orienting):**
- `CLAUDE.md` -- Project conventions, pipeline summary, key terms, deployment context
- `audit/SESSION-CONTEXT.md` -- What exists, what's settled, what to build
- `audit/GAP-TRIAGE.md` -- 8 remaining gaps. Gap #2 requires client_id on all data schemas from Day 1. This affects every model you write.

**Read for synthesis (Phase 1 of your work):**
- All 10 files in `reference/analysis/` matching `compass_artifact*.md` -- These are the deep research reports on the Claude Code leak. Read every one completely.
- `reference/analysis/09-implementation-recommendations.md` -- The repo analysis synthesis. Cross-reference against the deep research.
- `reference/analysis/00-master-index.md` -- Quick reference for all repo analysis findings.
- `synthesis/PLAN-CHANGELOG.md` -- The 17 research-backed changes. Cross-reference deep research against these too, not just the repo analysis.

**Read for code architecture (Phase 2 of your work):**
- `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- The 11 build components with schemas, acceptance criteria, and build order. This is the spec you're producing code for.
- `reference/analysis/03-multi-agent.md` -- Highest-value repo analysis. Contains AgentDefinition pattern.
- `reference/analysis/05-memory-context.md` -- Second-highest-value. Contains Observation Library mapping.
- `reference/analysis/06-mcp-implementation.md` -- MCP client reference for Component #4.
- `reference/analysis/02-tool-system.md` -- ToolDef registry pattern.
- `CAPSTONE-PLAN-v2.md` Section 2 -- Handoff contract table. Read BEFORE writing contracts.py.
- `CAPSTONE-PLAN-v2.md` Section 3.6 -- Task schema detail.
- `CAPSTONE-PLAN-v2.md` Section 4.3 -- Deliberation and confidence map. Read BEFORE writing confidence.py.
- `CAPSTONE-PLAN-v2.md` Section 5.3 -- Rubric dimensions. Read BEFORE writing evaluation.py.
- `CAPSTONE-PLAN-v2.md` Section 7.1 -- Observation Library. Read BEFORE writing observations.py.

## Phase 1: Deep Research Synthesis

### 1a. Rename the deep research files

The 10 deep research reports have opaque filenames (compass_artifact_wf-*). Rename each to a descriptive name based on its content. Write a rename mapping file to `reference/analysis/deep-research-rename-map.md` and then rename the actual files. Use the pattern `deep-research-NN-topic.md` (e.g., `deep-research-01-agent-teams.md`).

**Fallback:** If `mv` commands fail due to filesystem permissions, create new files with the correct names, copy the content, and note the old filenames in the mapping file. Do not stall on permission errors.

### 1b. Cross-reference deep research against repo analysis AND plan changes

Read all 10 deep research reports. For each, extract:
- Findings that are **new** (not in the repo analysis OR the 17 plan changes)
- Findings that **validate** repo analysis conclusions or plan changes
- Findings that **contradict** or **complicate** repo analysis conclusions or plan changes
- Specific implementation details (line numbers, function names, configuration values) useful for the build

### 1c. Write LEAK-SYNTHESIS.md

Write `reference/analysis/LEAK-SYNTHESIS.md` that synthesizes ALL Claude Code leak research (both repo analysis and deep research). Structure:

1. **Executive summary**: What did we learn? What changes? What's validated?
2. **Agent SDK assessment**: Should we build on the Claude Agent SDK, use patterns from the leak, or combine both? This is the key strategic question from deep research Prompt 10.
3. **Community MCP servers inventory**: Phase 1 targets 5 APIs: Exa, Brave Search, EdgarTools, FRED, Academix (per PHASE-1-IMPLEMENTATION-SPEC.md Component #4). Eventual target is 8+ APIs including CrossRef, Semantic Scholar, OpenAlex. For each: does a community MCP server exist? Build-vs-integrate decision.
4. **Cost model refinement**: What did the cost research reveal about prompt caching, fork-mode savings, and model mixing economics? Deployment target is Claude Max plan with minimal external API spend.
5. **New patterns not in repo analysis**: Anything from the full 512K TypeScript leak that the 11.8K Python reimplementation missed.
6. **Consolidated pattern catalog**: Every ADOPT/ADAPT/SKIP/INVESTIGATE verdict from both the repo analysis and deep research, unified and deduplicated.
7. **Build-order implications**: Does anything from the deep research change the Phase 1 build order or approach for any component?

### 1d. Update PHASE-1-IMPLEMENTATION-SPEC.md if needed

If the synthesis reveals anything that changes the build approach for a specific component (e.g., an existing MCP server for Exa means Component #4 is smaller than expected, or the Agent SDK means Component #5 should be structured differently), update the implementation spec. If nothing changes, document that explicitly.

## Phase 2: Code Architecture Design

**File creation order matters.** Write files in this order to avoid import errors:
1. Project scaffolding (pyproject.toml, directories, __init__.py files)
2. Base models with no cross-model dependencies (citations.py, tasks.py)
3. Models that reference base models (research.py, evaluation.py, observations.py, confidence.py, agents.py, config.py)
4. Event system (events.py -- references model types)
5. Handoff contracts (contracts.py -- references events and models)
6. Architecture document (docs/ARCHITECTURE.md -- references everything above)

### 2a. Design the project structure

Design the directory structure for the Keystone Intelligence Engine codebase. This is a Python project. Consider:
- Module boundaries that map to pipeline layers (L0, L1, L1.5, L2, L3, L4, META)
- Shared types/models used across modules (citations, claims, tasks, events, observations)
- Configuration management (PydanticSettings for env vars, YAML for engagement configs)
- Test structure mirroring source structure
- Scripts for running the pipeline, calibration, etc.

Write the architecture to `docs/ARCHITECTURE.md`. Include:
- The full directory tree
- One-paragraph description of each module's responsibility
- Interface contracts between modules (what data crosses each boundary)
- Dependency rules (which modules can import from which)

Reference the nano-claude-code patterns where applicable (e.g., "tool_registry pattern from nano-claude-code for src/keystone/tools/").

### 2b. Produce foundational data models

Write these as actual Python files using Pydantic v2. **Include `engagement_id: str` and `client_id: str` fields on all top-level entities** (per Gap #2: multi-tenancy from Day 1).

Write in this order:

**`src/keystone/models/citations.py`** -- Citation entity, Claim entity, CitationManifest. Based on Component #2 schemas in PHASE-1-IMPLEMENTATION-SPEC.md.

**`src/keystone/models/tasks.py`** -- ResearchTask with all fields (type, decision_usefulness, anti_confirmatory_framing, assigned_tools, passes, etc.). Based on Component #1 task schema.

**`src/keystone/models/research.py`** -- RESEARCH.md spec model and research-tasks model. Based on Component #1 schemas. Imports from tasks.py and citations.py.

**`src/keystone/models/evaluation.py`** -- The 10-dimension rubric model, evaluation result model, sprint contract model. Read CAPSTONE-PLAN-v2.md Section 5.3 BEFORE writing this file.

**`src/keystone/models/observations.py`** -- Observation Library entry model with three-category taxonomy (structural/analytical/judgment). Read CAPSTONE-PLAN-v2.md Section 7.1 BEFORE writing this file.

**`src/keystone/models/confidence.py`** -- The 5-tier confidence map structure with DiscoUQ features. Read CAPSTONE-PLAN-v2.md Section 4.3 BEFORE writing this file.

**`src/keystone/models/agents.py`** -- AgentDefinition model (adopted from nano-claude-code). Agent specialization types for L1, L1.5 analysts.

**`src/keystone/models/config.py`** -- Application configuration (PydanticSettings for API keys, provider settings, rate limits), engagement-level configuration (YAML-loadable), and model mixing settings (which model for which pipeline layer).

### 2c. Design the event system

The repo analysis's #1 finding was: "Generator-based agent loop is the right orchestration primitive. Adopt for ALL pipeline stages." Every pipeline transition should yield typed events for observability and trajectory storage.

Design the event type hierarchy. Write it as actual Python code in `src/keystone/events.py`. This file imports from the model files above. Include event types for:
- L0 events (SpecificationGenerated, TasksDecomposed, AgentDispatched)
- L1 events (ResearchStarted, SourceFound, CitationExtracted, FindingSynthesized, ResearchComplete)
- CitationProcessor events (CitationDeduped, CorroborationScored, URLVerified, ManifestProduced)
- L1.5 events (AnalystSpawned, IndependentAnalysisComplete, AggregationComplete, ConfidenceMapProduced)
- L2 events (OutlineGenerated, SectionDrafted, SprintContractNegotiated)
- L3 events (DraftGenerated, CitationFormatted, DeliverableAssembled)
- L4 events (DeterministicCheckPassed, CitationGateResult, RubricDimensionScored, EvaluationComplete)
- META events (ObservationRecorded, PatternPromoted, ConstraintEncoded)

### 2d. Write the handoff contract interfaces

Read CAPSTONE-PLAN-v2.md Section 2 (the handoff contract table) FIRST. Then write Python Protocol classes or ABCs in `src/keystone/contracts.py`. Each pipeline stage should have a typed input and output contract. The contracts reference both model types and event types.

### 2e. Produce project scaffolding

Create:
- `pyproject.toml` with dependencies:
  - Core: pydantic (>=2.0), anthropic, pydantic-ai, temporalio, httpx, mcp
  - Search: exa-py, brave-search
  - Storage: pgvector, redis[hiredis], sqlalchemy[asyncio], asyncpg
  - Evaluation: (verify factscore package name before adding -- may need git install)
  - Dev: pytest, pytest-asyncio, mypy, ruff
- `src/keystone/__init__.py`
- `src/keystone/models/__init__.py` (re-exports all model classes)
- `tests/` directory structure mirroring `src/`
- `.env.example` with all required API keys and infrastructure connection strings (Postgres, Redis, Temporal server)
- `Makefile` with common commands (test, lint, typecheck, run)

### 2f. Write docs/ARCHITECTURE.md

After all code files are written, produce the architecture document. Include:
- Full directory tree with file descriptions
- Module responsibility descriptions
- Interface contracts between modules
- Dependency rules
- Nano-claude-code pattern references where applicable
- A "Coherence Check" section (see Phase 3b)

## Phase 3: Validation

### 3a. Schema validation

Run the Pydantic models through Python to verify they parse correctly:
```bash
cd src && python -c "
from keystone.models import *
from keystone.events import *
from keystone.contracts import *
# Test instantiation of at least one model per file
print('All imports valid')
"
```

If imports fail, fix the errors and re-run.

### 3b. Type checking

Run mypy on the src/ directory:
```bash
cd src && python -m mypy keystone/ --ignore-missing-imports
```

Fix any type errors. If mypy is not installed, add it to pyproject.toml dev dependencies and install it.

### 3c. Architecture coherence check

Re-read PHASE-1-IMPLEMENTATION-SPEC.md one more time. For each of the 11 components, verify that:
- The code architecture has a clear home for it
- The data models it needs exist
- Its interfaces with adjacent components are defined
- Nothing was missed

Write findings to the "Coherence Check" section of docs/ARCHITECTURE.md.

## Output Standards

- All Python code must be valid, importable, and properly typed
- Use Pydantic v2 syntax (model_validator, field_validator, ConfigDict)
- Every model field should have a docstring or Field(description=...) explaining its purpose
- Include examples as class-level docstrings where helpful
- Follow the project's communication rules: no em dashes, lead with the answer, be specific
- All top-level data entities include engagement_id and client_id fields

## Execution Rules

1. **Do not stop.** Work through all three phases.
2. **Do not ask questions.** Make your best judgment and document reasoning.
3. **Write as you go.** Save each file before moving to the next.
4. **Validate as you go.** Run Python imports after creating model files.
5. **Respect the file creation order in Phase 2.** Scaffolding -> base models -> derived models -> events -> contracts -> architecture doc.
6. **Context limit resilience.** If approaching limits, save current work. After compaction, re-read in this priority order: (1) docs/ARCHITECTURE.md, (2) src/keystone/models/__init__.py, (3) your most recently written file. Then continue.
7. **Prioritize correctly.** Phase 1 (synthesis) is important but Phase 2 (code architecture + models) is the highest-value output. If you must rush, rush the synthesis and take your time on the code.
8. **Read CAPSTONE-PLAN sections JIT.** Don't read the entire 1294-line plan upfront. Read the specific sections listed in the context loading strategy, at the time you need them.
