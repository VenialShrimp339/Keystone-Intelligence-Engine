# Keystone Intelligence Engine: Code Architecture

*Regenerated: 2026-04-06 (Audit Session 15) | Source of truth for code structure*

## Directory Tree (Actual)

```
src/keystone/
    __init__.py                         # Package root, version
    tool_names.py                       # Single source of truth for MCP tool name constants (ToolName enum)
    events.py                           # 34 typed pipeline events across all layers + HITL
    contracts.py                        # 9 Protocol-based handoff contracts (one per pipeline boundary)

    models/
        __init__.py                     # Re-exports all model classes (50+ classes)
        citations.py                    # Citation, Claim, CitationManifest, CorroborationPair, WikiCompilationRecord
        tasks.py                        # ResearchTask, TaskDecomposition (w/ DAG validation), TaskCategory/Type/Status
        research.py                     # ResearchSpec, EngagementSpec, StructuredFinding, ValidationReport
        evaluation.py                   # EvaluationResult, SprintContract, 10-dimension rubric, calibration models
        observations.py                 # ObservationEntry, ObservationLibrary, 3-category taxonomy
        confidence.py                   # ConfidenceMap, DiscoUQ features, ACH matrix, 5-tier claims
        agents.py                       # AgentDefinition, AgentInstance, role/type enums
        config.py                       # AppConfig (env vars), EngagementConfig, ModelMixingConfig

    citation/                           # Component #2: Citation utilities
        __init__.py                     # Package exports
        hash.py                         # SHA-256 content hashing + proposition hashing
        dedup.py                        # Union-find deduplication by URL/DOI + corroboration detection
        url_check.py                    # Async URL liveness checking (HEAD+GET with batch concurrency)

    specification/                      # Component #5: L0 Specification Engine
        __init__.py                     # Package exports
        _prompts.py                     # Prompt template loading and JSON extraction
        spec_engine.py                  # Main orchestrator: 10-step pipeline, SpecificationEngineContract
        engagement_classifier.py        # Step 1: 5-type taxonomy + Light/Standard/Deep profiles
        intent_clarifier.py             # Step 2: Decision-First CoT + Day-1 Hypothesis
        decomposer.py                   # Step 3: 3 heterogeneous lens agents + Opus synthesis
        validator.py                    # Step 4: MECE verification (5 binary dimensions)
        priority_scorer.py              # Step 5: Heuristic scoring (VOI deferred to Phase 2)
        template_registry.py            # Step 6: 7 seed AgentDefinition templates
        task_generator.py               # Step 7: research-tasks.json with DAG

    evaluator/                          # Component #6: L4 Evaluator Stack
        __init__.py                     # Package exports
        evaluator.py                    # Main orchestrator: 3-layer stack, EvaluatorContract
        layer1_deterministic.py         # FActScore decomposition, numerical consistency, URL liveness
        layer2_citation_gate.py         # DOI verification (pluggable Protocol), fabrication detection
        layer3_rubric.py                # 10-dimension scorer, weighted geometric mean, Tier 1/2 gating
        three_pass.py                   # Pass 1 (dimensional) + Pass 2 (gestalt). Pass 3 stub (Phase 2)
        rubric_config.py                # 4 evaluation profiles, weight functions, floor thresholds
        sprint_contract.py              # Unilateral contract generation (negotiation in Phase 2)
        retry.py                        # LLMCallable type, retry_llm_call with exponential backoff + dead-letter

    gateway/                            # Component #4: MCP Gateway
        __init__.py                     # Package exports (21 symbols)
        mcp_gateway.py                  # Central router: auth -> rate limit -> circuit break -> execute -> cite -> audit
        tool_registry.py                # ToolEntry, TransportType, HealthStatus + ToolRegistry class
        servers.py                      # 7 MCP server configs (Exa, Brave, EdgarTools, FRED, paper-search, doi, Finnhub)
        auth.py                         # Per-agent tool authorization (structural enforcement)
        rate_limiter.py                 # Token-bucket rate limiter with RateLimiterBackend Protocol
        circuit_breaker.py              # CLOSED/OPEN/HALF_OPEN state machine with async lock
        audit_log.py                    # Structured audit logging with SHA-256 I/O hashing

    hitl/                               # Component #HITL: Human-in-the-Loop
        __init__.py                     # Module docstring
        models.py                       # SQLAlchemy 2.0 ORM: ReviewGate, ReviewItem, ReviewDecision
        schemas.py                      # Pydantic API schemas: GateType, GateStatus, DecisionType
        db.py                           # Async database engine/session factory
        service.py                      # HITLService: state machine logic (create, decide, wait)
        api.py                          # FastAPI router: 5 REST endpoints
        gate.py                         # Pipeline integration: create_and_wait_for_gate(), builders

    knowledge/                          # Component #3b: Knowledge Accumulation (Karpathy wiki)
        __init__.py                     # Module docstring
        wiki_schema.py                  # WikiEntry model, WikiStore Protocol
        wiki_builder.py                 # Compiles StructuredFindings -> WikiEntries + WikiCompilationRecords
        index_maintainer.py             # Auto-rebuilds INDEX.md per engagement
        content_hasher.py               # Delegates to citation/hash.py for wiki provenance
        engagement_store.py             # FilesystemWikiStore: async filesystem backend (Phase 1)

tests/
    unit/
        models/                         # Model validation tests
        specification/                  # Spec Engine tests (8 files, 58 tests)
        evaluator/                      # Evaluator tests (6 files, 77 tests)
        gateway/                        # Aliased: test files at tests/unit/test_*.py (6 files, 75 tests)
        hitl/                           # HITL tests (3 files, 42 tests)
        knowledge/                      # Knowledge tests (5 files, 45 tests)

prompts/
    # Evaluator prompt templates (14 files)
    intent_alignment.md, intellectual_honesty.md, completeness.md,
    narrative_coherence.md, analytical_depth.md, source_quality.md,
    quantitative_rigor.md, actionability.md, evaluative_surprise.md,
    calibrated_confidence.md, gestalt_overlay.md, fact_decomposition.md,
    numerical_consistency.md, sprint_contract_generation.md
    # Specification Engine prompt templates (9 files)
    classification.md, intent_clarification.md, decompose_financial_lens.md,
    decompose_operational_lens.md, decompose_market_lens.md,
    decompose_synthesis.md, mece_validation.md, priority_scoring.md,
    task_generation.md

schemas/                                # JSON Schema files for validation
    research_md.schema.json, research_tasks.schema.json,
    citation.schema.json, claim.schema.json, citation_manifest.schema.json

templates/                              # Canonical templates
    RESEARCH.md.template, research-tasks.json.template

samples/                                # Test engagement samples
    luminar_lidar/, auto_body_chain/, specialty_chemicals_ma/
```

## Module Responsibilities

### `tool_names.py` -- Shared Tool Name Constants
Single source of truth for MCP tool identifiers. `ToolName` StrEnum prevents drift between Gateway registrations and Spec Engine templates. Both `gateway/servers.py` and `specification/template_registry.py` import from here.

### `models/` -- Shared Data Types
All Pydantic v2 models. The only module every other module imports from. Frozen where appropriate (citations, specs), mutable where needed (tasks with status transitions). Every top-level entity carries `engagement_id` and `client_id` for multi-tenancy.

### `events.py` -- Pipeline Observability
34 typed events covering all 6 pipeline layers + META + HITL. Every pipeline stage is an async generator yielding typed events. `AnyPipelineEvent` union type enables dispatch/routing.

### `contracts.py` -- Pipeline Boundaries
9 Protocol-based handoff contracts. Each defines typed inputs, outputs, quality gates. Uses `@runtime_checkable` for structural verification. Includes contracts for L2/L3 (Phase 2 implementations).

### `citation/` -- Citation Utilities (Component #2)
SHA-256 content hashing, union-find deduplication, async URL liveness checking. Used by Component #3b (knowledge) and will be used by Component #8 (CitationProcessor).

### `specification/` -- L0 Specification Engine (Component #5)
10-step pipeline: classify -> clarify -> decompose -> validate -> score -> template match -> generate tasks -> HITL gate -> (stubs for research + feedback). Outputs EngagementSpec.

### `evaluator/` -- L4 Evaluator Stack (Component #6)
3-layer stack: deterministic verification, citation gate, 10-dimension rubric scoring. Geometric mean aggregation. Tier 1/Tier 2 gating. 4 evaluation profiles. Layers 4-5 deferred to Phase 2.

### `gateway/` -- MCP Gateway (Component #4)
Central router for all tool calls. Structural authorization (agents only call assigned tools). Token-bucket rate limiting. Circuit breakers. Retry with dead-letter. Audit logging. Phase 1 uses MockMCPClient.

### `hitl/` -- Human-in-the-Loop (Component #HITL)
Database state machine with REST API. Two gates (post-specification, post-deliberation). Polling-based wait (Phase 1), Temporal Signal-ready interface (Phase 2).

### `knowledge/` -- Knowledge Accumulation (Component #3b)
Karpathy wiki pattern. Raw artifacts -> compiled entries with content-hash provenance. WikiStore Protocol is storage-agnostic. FilesystemWikiStore for Phase 1.

## Interface Contracts

| Protocol (contracts.py) | Implemented By | Status |
|---|---|---|
| SpecificationEngineContract | specification/spec_engine.py | Built (Component #5) |
| ResearchAgentContract | -- | Not built (Component #7) |
| CitationProcessorContract | -- | Not built (Component #8) |
| DeliberationContract | -- | Not built (Component #9) |
| ContentStructuringContract | -- | Not built (Phase 2) |
| GenerationContract | -- | Not built (Phase 2) |
| EvaluatorContract | evaluator/evaluator.py | Built (Component #6) |
| ObservationLibraryContract | -- | Not built (Phase 2) |
| HITLGateContract | hitl/gate.py | Built (Component #HITL) |

## Dependency Rules

1. `models/` imports from: nothing (base layer)
2. `tool_names.py` imports from: nothing (constants)
3. `events.py` imports from: `models/`
4. `contracts.py` imports from: `models/`, `events.py`, `hitl/schemas.py`
5. Pipeline modules import from: `models/`, `events.py`, `contracts.py`, `tool_names.py`
6. Pipeline modules do NOT import from each other, except:
   - `specification/` imports `evaluator/retry.py` (shared LLMCallable pattern)
   - `evaluator/layer1_deterministic.py` imports `citation/url_check.py`
   - `knowledge/content_hasher.py` delegates to `citation/hash.py`
7. `gateway/` is imported by pipeline modules needing tool access
8. `hitl/` is imported by pipeline modules at gate boundaries
9. `meta/` imports from `models/` only (Phase 2)

```
models/ <- tool_names.py
     \         |
      \        v
       events.py <- contracts.py <- pipeline modules
                                 <- gateway/
                                 <- hitl/
                                 <- citation/
                                 <- knowledge/
```
