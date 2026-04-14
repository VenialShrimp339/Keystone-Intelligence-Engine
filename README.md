# The Keystone Intelligence Engine

A multi-agent AI system for automated consulting research.

Jack Riddle | IU Kelley School of Business | Econ Consulting Capstone, Prof. Youle | Spring 2026

## Status

The audited project is materially real, but it is not yet an honest play-ready MVP with the full governed retrieval layer.

Current high-level truth:

- historical implementation is cleared through Wave 4B at `65a612d`
- the retrospective audit program is complete
- the live forward workstream is `Lane H - Retrieval Tool-Surface Authority Expansion`
- governed full-document retrieval, deterministic parse/evidence normalization, and L1 retrieval integration are still in active buildout

Use these docs first for current truth before relying on any older readiness language:

- [CURRENT-STATE.md](CURRENT-STATE.md)
- [audit/remediation/WORKSTREAM-STATUS.md](audit/remediation/WORKSTREAM-STATUS.md)
- [audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md](audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md)

Full architecture/evolution context remains in [docs/architecture-and-evolution.md](docs/architecture-and-evolution.md).

## Quick Start

These commands are still useful for local setup and legacy demos, but they are not by themselves proof that the current project state is MVP-complete. Read the status/buildout docs above first if you need the truthful current build picture.

**Prerequisites:** Python 3.11+, API keys (OpenAI, Exa, Brave Search)

```bash
./scripts/setup.sh          # Creates venv, installs deps, configures API keys
./scripts/run_demo.sh       # Runs the pipeline on a sample research question
pytest tests/unit/ -q       # Runs the test suite (no API keys needed)
```

## For Prof. Youle

The comprehensive project report is at [docs/architecture-and-evolution.md](docs/architecture-and-evolution.md). It covers the architecture, how the design evolved through 26 deep research reports, key design decisions with empirical evidence, and the AI-assisted build methodology.

## Directory Guide

| Path | What's Here |
|------|-------------|
| `docs/architecture-and-evolution.md` | Comprehensive architecture, evolution, and methodology report |
| `src/keystone/` | Production Python code (10 components, ~11K lines) |
| `tests/` | 830 automated tests (unit, integration, e2e) |
| `samples/` | Example engagement specifications (Luminar, auto body chain, specialty chemicals M&A) |
| `CAPSTONE-PLAN-v2.md` | Architecture source of truth (1,294 lines) |
| `JACK-ARCHITECTURAL-DIRECTIVES.md` | 14 authoritative design directives from project owner |
| `SESSION-LOG.md` | Chronological record of every development session |
| `CURRENT-STATE.md` | Living project status snapshot |
| `audit/remediation/project-state-reconcile/MVP-REQUIRED-BUILDOUT.md` | Honest gap map from current state -> MVP -> fuller product vision |
| `research/` | All research artifacts: 30 reports, synthesis, codebase analysis, external sources |
| `audit/` | Active remediation (`remediation/`) + archived audit phases (`archive/`) |
| `reference/` | External references: nano-claude-code submodule, session prompts, switchover docs |
| `output/` | Pipeline execution outputs from test runs |

## The Pipeline

The system implements DPVI (Decompose, Parallelize, Verify, Iterate):

```
Research Question
  -> L0: Specification Engine (question -> MECE issue tree -> task decomposition)
  -> L1: Parallel Research Agents (isolated execution, real search APIs)
  -> CitationProcessor (dedup, corroboration scoring, URL verification)
  -> L1.5: Deliberation (independent multi-perspective analysis + aggregation)
  -> L4: Evaluator (10-dimension rubric, geometric mean, citation gate)
  -> Markdown Renderer -> Analytical Brief
```

## Running Tests

```bash
# Unit tests (no API keys needed)
pytest tests/unit/ -q

# Integration tests (requires API keys in .env)
pytest tests/integration/ -v -m integration

# Full pipeline end-to-end (real API calls, ~15-30 min)
pytest tests/integration/test_pipeline_real.py -v -m integration -s
```

## License

Proprietary. Built for Keystone Group.
