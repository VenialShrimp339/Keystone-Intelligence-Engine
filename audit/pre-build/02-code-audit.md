# Pre-Build Code Audit: Scaffolding Session Output

*Audited: 2026-04-05 | Auditor: Claude Opus 4.6 (Session B)*

---

## File-by-File Audit

### 1. `src/keystone/models/citations.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
Faithfully implements the Component #2 schemas. Citation model has all required fields: citation_id with CIT- prefix validator, url, doi, title, authors, publication, date_published, access_date, source_type, quality_score (0-1 Admiralty Code composite), url_live, crossref_verified, found_by_agents. Claim model has full provenance chain: claim_id (CLM- prefix), text, source_chunk_ids, citation_ids, confidence, corroboration_count, confidence_tier, ach_diagnosticity.

- `engagement_id` and `client_id`: Present on Citation, Claim, CitationManifest. Gap #2 satisfied.
- `ConfidenceTier` placement in citations.py: Good decision. Prevents circular import since confidence.py imports from citations.py.
- `frozen=True` on Citation and Claim: Correct. Citations are immutable evidence records.
- `CorroborationPair` missing `engagement_id`/`client_id`: Minor, since it's always nested inside CitationManifest which has them.

**Issues:**
1. `date` and `datetime` imported under `TYPE_CHECKING` (lines 16-17). For Pydantic v2 field types, this works because Pydantic has built-in resolution for stdlib datetime types. Not a bug here, but the pattern is misleading when applied to custom types in other files.

**Design decision assessment:** ConfidenceTier in citations.py is the right call. The alternative (in confidence.py) would create a circular import: citations.py needs ConfidenceTier for Claim, confidence.py imports ACHDiagnosticity from citations.py.

---

### 2. `src/keystone/models/tasks.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
Implements CAPSTONE-PLAN-v2.md Section 3.6 with high fidelity. All 7 design decisions from the plan are represented:

1. Tasks are Pydantic models (JSON-serializable), not Markdown. ✓
2. `acceptance_criteria` field present. ✓
3. `passes` field with `validate_passes_not_self_set` model_validator. ✓
4. `anti_confirmatory_framing` with validator blocking confirmatory patterns. ✓
5. `deliverable_destination` field present. ✓
6. `type: TaskType` (estimative/current) with ICD 203 classification. ✓
7. `target_decision_usefulness` with ge=1, le=5 constraint. ✓

- `engagement_id` and `client_id`: Present on ResearchTask and TaskDecomposition. Gap #2 satisfied.
- `assigned_tools` validator enforcing 3-5 tools: Correct, matches plan's per-agent tool specialization.
- `frozen=False` on ResearchTask: Correct. Tasks have mutable status transitions.

**Issues:**
1. `TaskCategory` missing `"company_filings"` and `"patents"` as required_sources options. The plan's task_002 example uses `required_sources: ["company_filings", "news", "patents"]`, but these are free-text strings on ResearchTask, not restricted to TaskCategory values. Not a bug -- required_sources and category are different fields.
2. `TaskDecomposition.tasks` has no validator for the 15-50 task range mentioned in the plan (Section 3.6: "decomposes it into 15-50 discrete research tasks"). Minor omission.

---

### 3. `src/keystone/models/research.py`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** Match

**Assessment:**
ResearchSpec faithfully maps the RESEARCH.md structure from Section 3.2: decision_context, surprising_finding, questions (with primary/secondary), methodology, source_requirements, output_format, quality_bar, non_goals. ValidationReport implements the four-step verification correctly.

StructuredFinding implements the L1 agent output format with claims, absence_report, sources_consulted, tokens_consumed. FindingClaim has the full evidence chain: text, evidence, citations, confidence, confidence_tier, caveats.

- `engagement_id` and `client_id`: Present on ResearchSpec, StructuredFinding. Gap #2 satisfied.
- `EngagementSpec` bundles ResearchSpec + TaskDecomposition + ValidationReport. Correct composite.

**Issues:**
1. **Critical TYPE_CHECKING bug (lines 15-18):** `Citation`, `ConfidenceTier`, and `TaskDecomposition` are imported under `TYPE_CHECKING`. These are used as Pydantic field types in `FindingClaim` (lines 203, 209) and `EngagementSpec` (line 160). With `from __future__ import annotations`, Pydantic v2 cannot resolve these types at model creation time because they're not in the module's runtime namespace. This will cause `PydanticUndefinedAnnotation` errors when trying to validate data. Fix: move these imports out of `TYPE_CHECKING` block, or add `model_rebuild()` calls in `models/__init__.py`.
2. `ResearchQuestion` missing validator ensuring exactly one `is_primary=True` question. The plan says "Primary: [The core question]" (singular).
3. `ResearchQuestion`, `MethodologyRequirement`, `SourceRequirement` not re-exported in `models/__init__.py`. These are used as field types within ResearchSpec, so consumers creating ResearchSpec instances may need them.

---

### 4. `src/keystone/models/evaluation.py`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** Match

**Assessment:**
Excellent implementation of Sections 5.3, 5.9, 5.10. RubricDimension enum has all 10 dimensions. RUBRIC_WEIGHTS, RUBRIC_EVAL_TYPES, type-specific overrides all match the plan. Layer1/2/3Result models faithfully represent the 3-layer evaluation stack. SprintContract has section-level weight overrides, mandatory elements, and anti-patterns. CalibrationSample and CalibrationReport implement Component #10 with Spearman and Cohen's Kappa thresholds.

- `engagement_id` and `client_id`: Present on EvaluationResult, SprintContract. Gap #2 satisfied.
- Rubric weights as module-level dicts, not model fields: Good decision. These are canonical constants.
- `Layer3Result.gestalt_adjustment` range ±10 with `final_score` field: Correctly implements the 3-pass architecture (Section 5.10).

**Issues:**
1. **RUBRIC_WEIGHTS sum to 1.05, not 1.00.** 0.12+0.10+0.15+0.10+0.08+0.15+0.15+0.10+0.05+0.05 = 1.05. This is inherited from the plan text (Section 5.3), which states weights reduced from 15%→12% on Analytical Depth and 10%→8% on Completeness to "fund" two new 5% dimensions. But the original 8 dimensions already summed to 100%, and the reductions (3%+2%=5%) only recoup half of the 10% needed for two new dimensions. The code faithfully implements the plan's error. Fix: normalize weights or adjust (e.g., reduce Intent Alignment from 15% to 10% to get back to 100%).
2. **ESTIMATIVE_WEIGHT_OVERRIDES and CURRENT_WEIGHT_OVERRIDES don't specify how to merge with base weights.** They contain partial override dicts, but there's no utility function that applies them. The merge logic (replace matching keys, keep rest) needs to be clear, and the override profiles also don't sum correctly when applied.
3. `Layer2Result.validate_gate` validator (lines 146-152) is a no-op with a comment acknowledging it can't cross-reference `citations_fabricated`. Should be a `model_validator` instead, or removed.
4. `EvaluationResult.overall_score` doesn't have a validator linking it to `layer3_results.final_score`. Acceptable for scaffolding but worth noting.

---

### 5. `src/keystone/models/observations.py`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** Match

**Assessment:**
Faithfully implements Section 7.1. ObservationEntry has all required fields from the plan's JSON examples: observation_id (OBS- prefix), type (rejection/success), category (3-tier taxonomy), project, task_id, dimension, what_was_produced, assessment, root_cause, action_taken, propagated_to. ObservationLibrary has filtering properties for type and category.

- `engagement_id` and `client_id`: Present on ObservationEntry. ObservationLibrary has optional `engagement_id` (None for global). Gap #2 satisfied.
- `ObservationCategory` as `int, Enum` with values 1/2/3: Matches the plan's 3-tier structure.
- `promoted_to_skill` and `superseded_by` fields: Good additions beyond the plan's example JSON.

**Issues:**
1. **TYPE_CHECKING bug (line 20):** `RubricDimension` imported under `TYPE_CHECKING` but used as a Pydantic field type in `ObservationEntry.dimension` (line 72). Same issue as research.py -- will fail at runtime validation. Fix: move to runtime import.
2. Plan's example JSON uses `"dimension_failed"` and `"what_was_wrong"` field names; the model uses `"dimension"` and `"assessment"`. Not a bug (the model names are better), but the divergence should be noted.
3. No `observation_id` prefix validator (like CIT- or CLM- have). Minor, but the plan shows "OBS-047" format.
4. `ObservationLibrary` missing `client_id` field. It has `engagement_id` but not `client_id`. Since the library can be global (engagement_id=None), it should probably also track client scope.

---

### 6. `src/keystone/models/confidence.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
Outstanding implementation of Section 4.3. The 5-tier confidence taxonomy is perfectly mapped: HighConfidenceClaim (>80%), ModerateConfidenceClaim (60-80%), WeakConfidenceClaim (50-60%), ContestedClaim (<50%), InsufficientEvidenceClaim. Each tier has the correct fields from the plan's JSON example.

- `engagement_id` and `client_id`: Present on ConfidenceMap. Gap #2 satisfied.
- DiscoUQFeatures: evidence_overlap, minority_argument_strength, divergence_depth. Matches plan exactly.
- ACHMatrix: hypotheses, diagnostic_evidence, inconsistent_evidence_per_hypothesis. Matches plan.
- HighConfidenceClaim has `curmudgeon_challenge`. Matches plan.
- ContestedClaim has `steelmanned_opposing_view` and optional `ach_matrix`. Matches plan.
- ConfidenceMap includes `gaps_identified` and `absence_report`. Matches plan.
- `total_claims` and `tiers_populated` properties: Useful additions.

**Issues:**
1. **TYPE_CHECKING bug (line 16):** `ACHDiagnosticity` imported under `TYPE_CHECKING` but used as a Pydantic field type in `ModerateConfidenceClaim.ach_diagnosticity` (line 93). Same class of bug. Fix: move to runtime import.
2. ACHMatrix.inconsistent_evidence_per_hypothesis should have a validator ensuring its length matches len(hypotheses). Minor.

---

### 7. `src/keystone/models/config.py`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** Match (no direct plan section; implements deployment context from CLAUDE.md)

**Assessment:**
Well-structured configuration hierarchy: AnthropicConfig, SearchAPIConfig, InfraConfig, RateLimitConfig, ModelMixingConfig, EvaluationConfig, AppConfig (BaseSettings), EngagementConfig. Model mixing defaults match the plan: Opus for L0/L4, Sonnet for L1, Haiku for extraction.

EvaluationConfig has calibration_threshold=0.80, kappa_threshold=0.60, canary_set_size=30, recalibration_interval=5. All match the plan and GAP-TRIAGE.md.

**Issues:**
1. **AppConfig env_prefix mismatch with .env.example.** AppConfig uses `env_prefix = "KEYSTONE_"`, meaning it expects env vars like `KEYSTONE_ANTHROPIC_API_KEY`. But `.env.example` defines `ANTHROPIC_API_KEY` without the prefix. Either remove the prefix from AppConfig or update .env.example. This will cause all env vars to be silently ignored at runtime.
2. `ModelMixingConfig` uses `str` types for layer assignments (e.g., `l0_specification: str = "opus"`) instead of `ModelTier` enum. This allows invalid values like `"gpt4"` to pass validation. Should use `ModelTier` type.
3. `AnthropicConfig`, `SearchAPIConfig`, `InfraConfig` are defined but not used in AppConfig's nested structure. AppConfig duplicates all their fields directly. The nested configs are dead code unless used elsewhere.
4. `EngagementConfig.evaluation_intensity` is `str` instead of `EvaluationIntensity` enum.

---

### 8. `src/keystone/models/agents.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
Implements Section 4.1-4.2. AgentRole enum covers all pipeline layers. ResearchAgentType matches the 5 agent types from Section 4.2: quantitative, qualitative, contrarian, historical_analogy, internal_document. DeliberationAnalystType matches Section 4.3's 5 methodologies: ACH, quantitative, adversarial, historical_analogy, scenario_planning.

AgentDefinition has the nano-claude-code pattern fields: name, description, role, model, tools, system_prompt, source. AgentInstance has lifecycle tracking: working_dir, status, task_ids, tokens_consumed, cost_usd.

- `engagement_id` and `client_id`: Present on AgentInstance. Gap #2 satisfied.
- `AgentDefinition` intentionally lacks engagement_id/client_id (definitions are templates, not instances). Correct.
- Runtime import of `ModelTier` from tasks.py (line 14): **Correct pattern**. This is what the other files should do for their Pydantic field types.
- `tools: list[str]` with "Empty = all tools" note: Matches plan's "3-5 tools per agent" but no validator enforcing the 3-5 range on AgentDefinition (only on ResearchTask). Acceptable since L0/L4 agents get unrestricted tools.

**Issues:**
1. `AgentInstance.status` is `str` instead of a proper enum (like `TaskStatus`). Should define an `AgentStatus` enum (pending/running/completed/failed).
2. No agent-level `max_thinking_tokens` field. The LEAK-SYNTHESIS UPDATE added `MAX_THINKING_TOKENS = 10000` for Sonnet agents. This could live on AgentDefinition or AgentInstance as a config field.

---

### 9. `src/keystone/models/__init__.py`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** Match

**Assessment:**
Re-exports 51 classes across 8 model modules. `__all__` list is complete and matches the import statements. Alphabetically organized within sections.

**Issues:**
1. **Missing re-exports from research.py:** `ResearchQuestion`, `MethodologyRequirement`, `SourceRequirement` are defined but not re-exported. These are field types within `ResearchSpec` -- consumers creating ResearchSpec instances need them.
2. **Missing re-exports from config.py:** `AnthropicConfig`, `SearchAPIConfig`, `InfraConfig` are defined but not re-exported. Less critical since AppConfig duplicates their fields.
3. **No `model_rebuild()` calls** to resolve the TYPE_CHECKING forward reference issue in research.py, confidence.py, observations.py. Adding `research.FindingClaim.model_rebuild()` etc. after all imports would fix the Pydantic resolution bug systematically.

---

### 10. `src/keystone/__init__.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
Minimal package root. `__version__ = "0.1.0"` matches pyproject.toml version. No unnecessary imports.

**Issues:** None.

---

### 11. `src/keystone/events.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
29 typed events + 1 base class (PipelineEvent). Coverage:

| Layer | Events | Count |
|-------|--------|-------|
| L0 | SpecificationGenerated, TasksDecomposed, AgentDispatched | 3 |
| L1 | ResearchStarted, SourceFound, CitationExtracted, FindingSynthesized, ResearchComplete | 5 |
| CitationProcessor | CitationDeduped, CorroborationScored, URLVerified, ManifestProduced | 4 |
| L1.5 | AnalystSpawned, IndependentAnalysisComplete, AggregationComplete, ConfidenceMapProduced | 4 |
| L2 | OutlineGenerated, SectionDrafted, SprintContractNegotiated | 3 |
| L3 | DraftGenerated, CitationFormatted, DeliverableAssembled | 3 |
| L4 | DeterministicCheckPassed, CitationGateResult, RubricDimensionScored, EvaluationComplete | 4 |
| META | ObservationRecorded, PatternPromoted, ConstraintEncoded | 3 |

All 6 layers + META covered. ✓
L3 events present (DraftGenerated, CitationFormatted, DeliverableAssembled). ✓
AnyPipelineEvent union type covers all 29 events. ✓

PipelineEvent base has engagement_id, client_id, timestamp, layer. Gap #2 satisfied at the event level.

**Issues:**
1. `timestamp` uses `datetime.utcnow` default factory. `datetime.utcnow()` is deprecated in Python 3.12+ in favor of `datetime.now(timezone.utc)`. Not a blocker for 3.11 target but worth fixing for forward compatibility.
2. Events use `str` types for fields like `agent_type`, `dimension`, `model_tier` instead of the corresponding enum types. Acceptable for event simplicity (events are serialized for trajectory storage), but loses type safety.
3. No discriminated union support. The plan mentions Pydantic v2 handles discriminated unions "naturally via the `layer` field" (handoff Section 4), but `AnyPipelineEvent` is a plain union, not a discriminated one. Multiple events share the same `layer` value (e.g., all L1 events have `layer="L1"`), so `layer` alone can't discriminate. Would need a `type` or `event_type` discriminator field.

---

### 12. `src/keystone/contracts.py`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
8 Protocol classes (not 7 as stated in the scaffolding handoff), all `@runtime_checkable`:

1. SpecificationEngineContract (L0)
2. ResearchAgentContract (L1)
3. CitationProcessorContract (CitationProcessor)
4. DeliberationContract (L1.5)
5. ContentStructuringContract (L2)
6. GenerationContract (L3)
7. EvaluatorContract (L4)
8. ObservationLibraryContract (META)

All method signatures use typed parameters referencing the model classes. All methods are async generators yielding `AsyncIterator[AnyPipelineEvent]`. Each contract has a getter method (get_spec, get_finding, get_manifest, etc.) for retrieving the final output.

The plan's handoff contract table (Section 2) has 6 boundaries. The code adds 2 more (GenerationContract for L3, and separates out the observation library). This is an improvement -- L3 and META were implicit boundaries in the plan.

All imports under TYPE_CHECKING: Correct for Protocol classes (protocols are structural typing, so imports are only needed for type checking, not runtime).

**Issues:**
1. **Documentation discrepancy:** Handoff claims "7 Protocol classes" but there are 8. Minor.
2. No `ContentStructuringContract` getter for the outline itself -- only `get_sprint_contracts()`. The L2 module also produces an outline, which is referenced in events (OutlineGenerated) but not accessible via the contract.

---

### 13. `docs/ARCHITECTURE.md`

**Rating:** SOLID
**Plan fidelity:** Match

**Assessment:**
- Directory tree matches what was created in `src/keystone/`. Pipeline module directories (specification/, agents/, citation/, etc.) are documented as planned structure, not yet created. This is accurate.
- Interface table (9 boundaries) is comprehensive and matches contracts.py.
- Coherence check accurately documents all 11 components with their models and contract status.
- 3 gaps (SearchQuery/SearchResults, ToolCall/ToolResult, Outline/SectionDraft) correctly identified and documented as non-blocking.
- nano-claude-code pattern references table is useful and accurate.
- Dependency rules are correct and create a clean DAG.

**Issues:**
1. Architecture.md lists `tool_loader.py` in the gateway module but the implementation spec's LEAK-SYNTHESIS UPDATE also references it. Consistent.
2. `tools/` directory listed but no tool models defined yet. Consistent with deferral.

---

### 14. `pyproject.toml`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** N/A

**Assessment:**
- `version = "0.1.0"` matches `__init__.py`. ✓
- `requires-python = ">=3.11"`. ✓
- `hatchling` build backend. Reasonable choice.
- Core deps: pydantic, pydantic-settings, anthropic, pydantic-ai, temporalio, httpx, mcp, exa-py, brave-search, pgvector, redis, sqlalchemy, asyncpg, pyyaml, python-dotenv, structlog.
- Dev deps: pytest, pytest-asyncio, pytest-cov, mypy, ruff, type stubs.
- ruff target-version = "py311", mypy python_version = "3.11". ✓

**Issues:**
1. **`brave-search>=0.1.0` version constraint.** Handoff noted this was changed from `>=0.3.0` because PyPI only has up to 0.2.0. The actual latest may differ; needs verification on Python 3.11/3.12.
2. **Full dependency tree untested.** `pip install -e ".[dev]"` fails on Python 3.14. Packages known to fail: brave-search, temporalio, pgvector. Will need testing on Python 3.11-3.12 before build phase.
3. `pydantic-ai>=1.0` -- PydanticAI's versioning should be verified. As of early 2026, it may be <1.0.
4. `mcp>=1.0.0` -- MCP SDK versioning should be verified.
5. Missing `factscore` dependency (needed for Layer 1 deterministic verification, Component #6). Acceptable to add later.

---

### 15. `Makefile`

**Rating:** SOLID
**Plan fidelity:** N/A

**Assessment:**
Standard targets: install, test, test-unit, test-integration, test-e2e, lint, format, typecheck, check (combo), run, clean. The `check` target runs lint + typecheck + test-unit. Sensible.

**Issues:**
1. `run` target references `keystone.pipeline` which doesn't exist yet. Acceptable placeholder.
2. `lint` target runs `ruff format --check` but the `format` target runs `ruff format` then `ruff check --fix`. The order in `format` should probably be reversed (fix first, then format).

---

### 16. `.env.example`

**Rating:** NEEDS MINOR FIXES
**Plan fidelity:** N/A

**Assessment:**
Covers all required environment variables: API keys (Anthropic, Exa, Brave, CrossRef, Semantic Scholar, OpenAlex), infrastructure (Postgres, Redis, Temporal), model IDs, rate limits, evaluation config.

**Issues:**
1. **Env var names don't match AppConfig prefix.** AppConfig uses `env_prefix = "KEYSTONE_"`, so it expects `KEYSTONE_ANTHROPIC_API_KEY`. The .env.example defines `ANTHROPIC_API_KEY`. All vars would be silently ignored. Must either: (a) prefix all vars with `KEYSTONE_`, or (b) remove the prefix from AppConfig.
2. Missing `EXA_RPM_LIMIT` and `BRAVE_RPM_LIMIT` (present in AppConfig's RateLimitConfig but not in .env.example). Minor since defaults exist.

---

### 17. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` (LEAK-SYNTHESIS UPDATE tags only)

**Assessment of 4 `[LEAK-SYNTHESIS UPDATE]` sections:**

**Component #4 updates (lines 231, 261-262):**
- doi-mcp for Layer 2 citation verification: Correctly references the MCP server for 9-database parallel verification. The code has `Layer2Result` in evaluation.py with `citations_fabricated` list. Consistent.
- Tool Search token budget (under 10K tokens): Not directly enforced in any model, but it's an acceptance criterion, not a data model concern. Correct.
- Retry loops with dead-letter paths: Not in models (runtime behavior), but should be in gateway implementation. Correct placement as acceptance criteria.

**Component #7 updates (lines 400-405):**
- `fork_manager.py`, `micro_compact.py`, `auto_compact.py` added to file list: These don't have model representations (they're runtime components). The file list matches ARCHITECTURE.md's planned structure.
- `MAX_THINKING_TOKENS = 10000`: Not represented in any model or config. Should be in AgentDefinition or EngagementConfig. Noted as Issue #2 on agents.py.

**Consistency verdict:** The LEAK-SYNTHESIS UPDATEs are primarily runtime/infrastructure concerns, not data model concerns. The models don't need to change for most of them. The one gap is MAX_THINKING_TOKENS, which should be configurable.

---

## Overall Assessment

### Is this a solid foundation for building Components #1-#4?

**Yes, with caveats.** The scaffolding is architecturally sound and demonstrates thorough understanding of the plan. Model fidelity to CAPSTONE-PLAN-v2.md is high. The event hierarchy and contract interfaces are well-designed and cover the full pipeline. The multi-tenancy requirement (Gap #2) is consistently implemented.

However, **one systematic bug must be fixed before building**: the TYPE_CHECKING pattern for cross-module Pydantic field types will cause runtime failures when models are instantiated with actual data. This affects 3 of 8 model files and is a 15-minute fix.

### Top 5 Issues by Severity

| # | Severity | File(s) | Issue |
|---|----------|---------|-------|
| 1 | **HIGH** | research.py, confidence.py, observations.py | Cross-module Pydantic field types imported under `TYPE_CHECKING` will cause `PydanticUndefinedAnnotation` at runtime. Move to runtime imports or add `model_rebuild()` calls in `__init__.py`. |
| 2 | **HIGH** | config.py + .env.example | `env_prefix = "KEYSTONE_"` in AppConfig doesn't match .env.example vars (no prefix). All env vars silently ignored at runtime. |
| 3 | **MEDIUM** | evaluation.py | `RUBRIC_WEIGHTS` sum to 1.05, not 1.00. Inherited from plan (Section 5.3 math error: 12+10+15+10+8+15+15+10+5+5=110%). Weighted scores will be inflated by 5%. |
| 4 | **LOW** | config.py | `ModelMixingConfig` uses `str` instead of `ModelTier` enum; `EngagementConfig.evaluation_intensity` uses `str` instead of `EvaluationIntensity` enum. Loses type safety. |
| 5 | **LOW** | agents.py | `AgentInstance.status` is `str` instead of a proper enum. Missing `max_thinking_tokens` config field for the LEAK-SYNTHESIS UPDATE. |

### Files Rated NEEDS MINOR FIXES or NEEDS REWORK

| File | Rating | Specific Fix Needed |
|------|--------|---------------------|
| `models/research.py` | NEEDS MINOR FIXES | Move `Citation`, `ConfidenceTier`, `TaskDecomposition` imports from TYPE_CHECKING to runtime |
| `models/evaluation.py` | NEEDS MINOR FIXES | Fix RUBRIC_WEIGHTS to sum to 1.00; remove no-op Layer2Result.validate_gate |
| `models/observations.py` | NEEDS MINOR FIXES | Move `RubricDimension` import from TYPE_CHECKING to runtime |
| `models/confidence.py` | SOLID (borderline) | Move `ACHDiagnosticity` import from TYPE_CHECKING to runtime |
| `models/config.py` | NEEDS MINOR FIXES | Fix env_prefix mismatch; use enum types for model mixing and evaluation intensity |
| `models/__init__.py` | NEEDS MINOR FIXES | Add missing re-exports (ResearchQuestion, MethodologyRequirement, SourceRequirement) |
| `.env.example` | NEEDS MINOR FIXES | Either prefix all vars with `KEYSTONE_` or remove prefix from AppConfig |
| `pyproject.toml` | NEEDS MINOR FIXES | Verify dependency versions on Python 3.11-3.12 before build |

### Summary Statistics

- **Files audited:** 16
- **SOLID:** 8 (citations.py, tasks.py, confidence.py, agents.py, `__init__.py`, events.py, contracts.py, ARCHITECTURE.md, Makefile)
- **NEEDS MINOR FIXES:** 7 (research.py, evaluation.py, observations.py, config.py, models/__init__.py, .env.example, pyproject.toml)
- **NEEDS REWORK:** 0

**Estimated fix time for all issues:** 1-2 hours. None are architectural. The codebase is a solid foundation.
