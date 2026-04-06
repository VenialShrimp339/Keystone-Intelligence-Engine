# Session Log

Chronological record of every agent session on the Keystone Intelligence Engine. New agents: read this to understand the project arc. Each entry captures what was done, what was produced, and what it set up for the next session.

---

## Session 1: Research Synthesis
- **Date:** 2026-04-03
- **Agent:** Claude Code (Opus 4.6)
- **Duration:** ~30 min
- **Task:** Analyze 16 deep research reports across 4 threads, synthesize findings, update CAPSTONE-PLAN-v2.md with research-backed changes.
- **Approach:** 4 parallel Opus subagents (one per thread A-D) for independent analysis, then a single synthesis agent that read all outputs before touching the plan. Hybrid approach avoids merge conflicts (full parallel) and context saturation (full sequential).
- **Key outputs:**
  - `synthesis/UNIFIED-SYNTHESIS.md` -- Cross-thread findings, ~80 tool verdicts, 6 contradiction resolutions, 8 gaps
  - `synthesis/PLAN-CHANGELOG.md` -- 17 changes documented with section/what/why/evidence/confidence
  - `CAPSTONE-PLAN-v2.md` updated from 1,051 to 1,294 lines with 31 [SYNTHESIS UPDATE] tags
  - Per-report analyses and 4 thread summaries in `synthesis/`
- **Key decisions:** Deliberation redesigned from debate to independent parallel analysis (Change #2). Evaluator overhauled to 5-layer stack (Change #4). CitationProcessor added as discrete pipeline stage (Change #1). Observation Library replaces Rejection Library (Change #9). Custom orchestration over framework adoption (Change #11).
- **Set up next:** Plan updated and tagged, ready for consistency audit.

---

## Session 2: Plan Audit + Implementation Spec
- **Date:** 2026-04-04
- **Agent:** Claude Code (Opus 4.6)
- **Duration:** ~20 min
- **Task:** Verify plan consistency after 17 changes, triage remaining gaps, produce implementation spec and session context briefing.
- **Key outputs:**
  - 3 stale references fixed in CAPSTONE-PLAN-v2.md
  - 6 evidence caveats documented (none change architecture)
  - `audit/GAP-TRIAGE.md` -- 8 gaps triaged. 0 block Phase 1. 2 resolved in-place (canary set, cost model).
  - `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- 11 components with schemas, acceptance criteria, build order, MVP definition
  - `audit/SESSION-CONTEXT.md` -- 66-line briefing doc (now superseded by CURRENT-STATE.md)
- **Key decisions:** Build order established: 4 parallel foundations (#1-#4), then sequential chain (#5-#11). MVP defined: 2-3 agents, 2 search APIs, Layers 1-2 eval, Markdown output.
- **Set up next:** Implementation spec ready for building. External dependency flagged: Jack provides 10+ deliverables for calibration.

---

## Session 3: Cowork Planning Session
- **Date:** 2026-04-04 through 2026-04-05
- **Agent:** Claude Cowork (Opus 4.6)
- **Duration:** Long session across two days (compacted multiple times)
- **Task:** End-to-end project orientation, CLAUDE.md restructuring, Claude Code leak analysis strategy, overnight analysis prompt design, deep research prompt design, scaffolding prompt design, handoff protocol design.
- **Key outputs:**
  - `CLAUDE.md` restructured from 146-line prose to ~90-line behavioral rules (audited twice, 7+3 issues fixed)
  - `.claude/settings.json`, `.claude/agents/research-analyst.md`, `.claude/agents/synthesis-lead.md`, `.claude/skills/research-synthesis/SKILL.md`, `.claude/skills/architecture/SKILL.md`
  - `reference/OVERNIGHT-ANALYSIS-PROMPT.md` -- 10-phase autonomous analysis prompt (audited, 14 issues fixed)
  - `reference/DEEP-RESEARCH-PROMPTS.md` -- 10 parallel deep research prompts with project file references
  - `reference/PROJECT-CUSTOM-INSTRUCTIONS.md` -- Custom instructions for deep research Claude project
  - `reference/SYNTHESIS-AND-SCAFFOLDING-PROMPT.md` -- Pre-build session prompt (audited, 17 issues fixed)
  - Handoff protocol designed (SESSION-LOG.md + CURRENT-STATE.md + CLAUDE.md working rule)
- **Key decisions:** Verdict taxonomy standardized to ADOPT/ADAPT/SKIP/INVESTIGATE. Deployment context (Claude Max, model mixing, cost target) added to CLAUDE.md. Deep research split into 10 parallel prompts covering agent teams, context management, tool system, harness, quality enforcement, MCP, self-improvement, cost, community, and Agent SDK. Synthesis prompt designed with explicit file creation ordering and JIT context loading. Architecture doc moved from src/ to docs/.
- **Set up next:** Overnight analysis prompt ready for Claude Code. Deep research prompts ready for parallel execution. Scaffolding prompt ready for post-analysis session. Handoff protocol designed but not yet implemented.

---

## Session 4: Overnight nano-claude-code Analysis
- **Date:** 2026-04-05 (overnight)
- **Agent:** Claude Code (Opus 4.6, dangerously-skip-permissions)
- **Duration:** ~13 min
- **Task:** Methodically analyze entire nano-claude-code Python reimplementation (56 files, 11,833 lines) against Keystone's architecture.
- **Key outputs (all in `reference/analysis/`):**
  - `00-master-index.md` (108 lines) -- Quick-reference tables, top 5 findings, component mapping
  - `01-core-architecture.md` (262 lines) -- Agent loop, compaction, config, DPVI mapping
  - `02-tool-system.md` (314 lines) -- ToolDef registry, per-agent subsetting, output truncation
  - `03-multi-agent.md` (529 lines) -- HIGHEST VALUE: isolation, spawning, coordination, security analysis
  - `04-task-management.md` (234 lines) -- Dependency graph, thread safety, research-tasks mapping
  - `05-memory-context.md` (455 lines) -- HIGHEST VALUE: Observation Library mapping, JIT loading, compaction
  - `06-mcp-implementation.md` (488 lines) -- Complete MCP client reference for Component #4
  - `07-skills-plugins.md` (192 lines) -- Consulting methodology skill definitions
  - `08-emergent-patterns.md` (213 lines) -- 10 cross-cutting patterns, anti-patterns
  - `09-implementation-recommendations.md` (269 lines) -- All 11 components mapped, architecture validated
- **Key decisions:** No architectural decisions changed. All existing decisions validated. 5 ADOPT patterns identified: ToolDef registry, generator-based agent loop, AgentDefinition from markdown, two-layer compaction, MCP client architecture.
- **Set up next:** Repo fully analyzed. Concrete implementation patterns ready for Components #4, #5, #7, #9, #11.

---

## Session 5: Deep Research Reports (10 parallel agents)
- **Date:** 2026-04-05
- **Agent:** Claude.ai Deep Research (10 parallel conversations in a Claude Project)
- **Duration:** ~30 min per report
- **Task:** Research community discoveries from the 512K-line Claude Code TypeScript leak, mapped to Keystone's pipeline.
- **Key outputs (in `reference/analysis/`, later renamed in Session 6):**
  - 10 reports (~1,485 lines total) covering: Agent Teams, context/compaction, tool system, harness architecture, quality enforcement/hooks, MCP architecture, self-improvement/KAIROS, cost optimization, community landscape, Agent SDK/hybrid orchestration
- **Key findings:** Fork-mode prompt caching makes 5 agents cost ~1x. MicroCompact at zero API cost. 50+ tools with isolated schemas validates 3-5 per agent. KAIROS/autoDream directly applicable to Observation Library. Extended thinking default (31,999 tokens) is a hidden cost multiplier.
- **Set up next:** Raw reports with opaque filenames. Need synthesis against repo analysis and plan changes.

---

## Session 6: Pre-Build Scaffolding (Synthesis + Code Architecture)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, dangerously-skip-permissions)
- **Duration:** ~45 min
- **Task:** Synthesize 10 deep research reports against repo analysis and plan changes. Design code architecture. Produce foundational Pydantic v2 models, event system, handoff contracts, and project scaffolding.
- **Key outputs:**
  - `reference/analysis/LEAK-SYNTHESIS.md` (45KB) -- Unified synthesis of all leak research, 7 sections + impl spec impact
  - `reference/analysis/deep-research-rename-map.md` -- Filename mapping
  - `reference/analysis/deep-research-01-agent-teams.md` through `deep-research-10-agent-sdk-hybrid.md` -- Renamed from opaque compass_artifact filenames
  - `src/keystone/models/citations.py` -- Citation, Claim, CitationManifest, CorroborationPair, SourceType, ConfidenceTier
  - `src/keystone/models/tasks.py` -- ResearchTask, TaskDecomposition, TaskCategory, TaskType, TaskStatus
  - `src/keystone/models/research.py` -- ResearchSpec, EngagementSpec, StructuredFinding, FindingClaim, ValidationReport
  - `src/keystone/models/evaluation.py` -- EvaluationResult, SprintContract, Layer1/2/3Result, DimensionScore, rubric weights
  - `src/keystone/models/observations.py` -- ObservationEntry, ObservationLibrary, 3-category taxonomy
  - `src/keystone/models/confidence.py` -- ConfidenceMap, 5 tier-specific claim models, DiscoUQFeatures, ACHMatrix
  - `src/keystone/models/agents.py` -- AgentDefinition, AgentInstance, AgentRole, agent type enums
  - `src/keystone/models/config.py` -- AppConfig (PydanticSettings), EngagementConfig, ModelMixingConfig, RateLimitConfig
  - `src/keystone/events.py` -- 29 typed pipeline events across all 6 layers + META
  - `src/keystone/contracts.py` -- 7 Protocol-based handoff contracts (one per pipeline boundary)
  - `docs/ARCHITECTURE.md` -- Full directory tree, module responsibilities, interface table, dependency rules, coherence check
  - `pyproject.toml`, `.env.example`, `Makefile`, test directory structure, `.venv/`
  - `audit/PHASE-1-IMPLEMENTATION-SPEC.md` modified with 4 [LEAK-SYNTHESIS UPDATE] tags
- **Key decisions:** ConfidenceTier enum placed in citations.py (not confidence.py) to avoid circular imports. Rubric weights as module-level dicts, not model fields. Contracts use Protocol (structural typing), not ABC inheritance. Events use type union, not inheritance dispatch. JSON Schema files NOT produced separately (Pydantic models are source of truth, can generate schemas via `.model_json_schema()`). Synthesis delegated to background agent while code architecture proceeded in parallel.
- **Deviations from prompt:** Full pip install fails on Python 3.14 (sandbox system Python). Core deps installed and validated. Production build should target Python 3.11-3.12. Ruff auto-fixed style issues including Optional -> X | None and str Enum -> StrEnum conversions.
- **Surprises:** All 5 Phase 1 MCP targets have existing community/official servers (biggest scope reduction). doi-mcp verifies citations across 9 databases in parallel (directly addresses Layer 2 gate). Extended thinking at 31,999 tokens is a hidden cost multiplier (capped to 10,000 for Sonnet agents).
- **Three minor model gaps noted:** retrieval/ needs SearchQuery/SearchResults, gateway/ needs ToolCall/ToolResult, structuring/ needs Outline/SectionDraft. None block build order.
- **Set up next:** Foundations complete. Ready to build Components #1-#4 in parallel.

---

## Session 7: Handoff Protocol Implementation
- **Date:** 2026-04-05
- **Agent:** Claude Cowork (Opus 4.6)
- **Task:** Implement the handoff protocol designed in Session 3. Create SESSION-LOG.md, CURRENT-STATE.md, update CLAUDE.md with handoff working rule.
- **Key outputs:** SESSION-LOG.md (this file), CURRENT-STATE.md, updated CLAUDE.md
- **Set up next:** Handoff protocol operational. Any new session reads CLAUDE.md (auto) then CURRENT-STATE.md (first manual read) and is fully oriented.

---

## Session 8A: Deep Research Gap Analysis
- **Date:** 2026-04-05
- **Agent:** Claude Opus 4.6 (Claude Code)
- **Task:** Analyze LEAK-SYNTHESIS.md against all 10 source deep research reports. Identify findings that were missed, underrepresented, or decision-changing.
- **Key outputs:**
  - `audit/pre-build/01-deep-research-gap-analysis.md` -- Report-by-report gap analysis with verdicts
  - `audit/pre-build/06-deep-research-analysis-prompt.md` -- Ready-to-paste prompt for full re-analysis session
- **Key findings:** LEAK-SYNTHESIS.md is ~60-65% complete. 5-6 decision-changing findings missed: compaction laundering (security), memory poisoning history (Observation Library design), system prompt baseline overhead (27-31K tokens, capacity planning), three-input-copy pattern (MCP gateway design), five-level MCP config hierarchy, auto-mode critic classifier pattern. Gaps concentrated in security/trust boundaries and quantitative baselines. Reports 05 (quality enforcement) and 07 (self-improvement) have highest gap density.
- **Set up next:** Full re-analysis should run in parallel with Components #1-#2 building. Results needed before Component #4.

---

## Session 8B: Pre-Build Code Audit
- **Date:** 2026-04-05
- **Agent:** Claude Opus 4.6 (Claude Code)
- **Task:** File-by-file audit of all scaffolding code from Session 6. Check plan fidelity, runtime correctness, cross-file consistency.
- **Key outputs:**
  - `audit/pre-build/02-code-audit.md` -- 16 files audited with ratings and specific issues
- **Key findings:** 8 SOLID, 7 NEEDS MINOR FIXES, 0 NEEDS REWORK. Estimated fix time: 1-2 hours. Top issues: (1) TYPE_CHECKING imports for Pydantic field types will cause runtime errors in 3 files (HIGH). (2) env_prefix mismatch between config.py and .env.example silently ignores all env vars (HIGH). (3) RUBRIC_WEIGHTS sum to 1.05 not 1.00 (MEDIUM, inherited from plan math error). Architecture is sound. Models faithfully implement the plan. Multi-tenancy (engagement_id/client_id) consistently applied.
- **Set up next:** 1-2 hour fix session resolves all issues before building.

---

## Session 8C: Folder Inventory + Reading List + Execution Readiness
- **Date:** 2026-04-05
- **Agent:** Claude Opus 4.6 (Claude Code)
- **Task:** Produce folder inventory, Jack's reading list, and execution readiness assessment. Update handoff docs for Sessions 8A/8B/8C.
- **Key outputs:**
  - `audit/pre-build/03-folder-inventory.md` -- Tagged inventory of all Claude-generated files with cleanup recommendations
  - `audit/pre-build/04-jack-reading-list.md` -- Prioritized 8-file reading list (~2-3 hours total)
  - `audit/pre-build/05-execution-readiness.md` -- Build/no-build decision with risk register and recommended sequence
  - `SESSION-LOG.md` updated with Sessions 8A, 8B, 8C entries
  - `CURRENT-STATE.md` rewritten to reflect post-audit state
- **Key findings:** Ready to build Components #1-#2 immediately. Components #3-#4 after 1-2 hour fix session. Component #3 retrieval architecture is over-engineered for a 6-week capstone (4 subsystems where 1-2 suffice). Top risk: Python dependency resolution on 3.11/3.12 (untested). Recommended: simplify Component #3 to basic pgvector search, cut Temporal/Redis/Docling/Semantic Router from MVP.
- **Set up next:** Day 0 fix session (1-2 hours), then build Components #1-#2 in Week 1.

---

## Session 9: Day 0 Fix Session
- **Date:** 2026-04-05
- **Agent:** Claude Opus 4.6 (Claude Code)
- **Task:** Fix all 7 issues rated NEEDS MINOR FIXES in the pre-build code audit (Session 8B). Update stale skill file. Delete redundant file. Verify everything passes.
- **Files modified:**
  - `src/keystone/models/research.py` -- Moved Citation, ConfidenceTier, TaskDecomposition from TYPE_CHECKING to runtime imports (with `# noqa: TC001` for ruff compatibility)
  - `src/keystone/models/observations.py` -- Moved RubricDimension from TYPE_CHECKING to runtime import
  - `src/keystone/models/confidence.py` -- Moved ACHDiagnosticity from TYPE_CHECKING to runtime import, removed unused TYPE_CHECKING import
  - `src/keystone/models/config.py` -- Removed `env_prefix: "KEYSTONE_"` from AppConfig.model_config
  - `src/keystone/models/evaluation.py` -- Fixed RUBRIC_WEIGHTS to sum to 1.00 (Narrative Coherence 0.10->0.05), added assert, adjusted ESTIMATIVE_WEIGHT_OVERRIDES (Narrative Coherence 0.07->0.03), added explanatory comments
  - `src/keystone/models/__init__.py` -- Added ResearchQuestion, MethodologyRequirement, SourceRequirement re-exports
  - `.claude/skills/architecture/SKILL.md` -- Updated 7 stale references: "8-dimension"->"10-dimension" (2 places), "Rejection Library"->"Observation Library" (5 places), Deliberation description (debate roles->methodology-based analysts), handoff table last row
- **Files deleted:**
  - `audit/SESSION-CONTEXT.md` -- Stale, predated Sessions 4-8, replaced by CURRENT-STATE.md
- **Key decisions:**
  - **Rubric weight fix:** Reduced Narrative Coherence from 10% to 5% (not Intent Alignment or other 15% dimensions). Rationale: the plan's own weighting philosophy says to de-emphasize dimensions where LLMs naturally excel. Narrative Coherence ("clear story", "so what?") is exactly that -- LLMs produce coherent prose by default. The three 15% dimensions (Quantitative Rigor, Actionability, Intent Alignment) all target LLM weak spots and the plan argues forcefully for each. ESTIMATIVE_WEIGHT_OVERRIDES.NARRATIVE_COHERENCE adjusted proportionally (0.07->0.03).
  - **TC001 noqa comments:** ruff's TCH rule set wants cross-module imports under TYPE_CHECKING. This is correct for non-Pydantic code but breaks Pydantic v2 model resolution with `from __future__ import annotations`. Added `# noqa: TC001` with explanation on the 4 affected import lines rather than disabling the rule globally (it's still useful for non-Pydantic imports).
- **Verification results:**
  - `python -c "from keystone.models import FindingClaim, ObservationEntry, ModerateConfidenceClaim"` -- PASS
  - `RUBRIC_WEIGHTS sum` -- 1.00 (PASS)
  - `ruff check src/` -- All checks passed
  - `mypy src/keystone/` -- Success: no issues found in 12 source files
  - `pytest tests/unit/` -- 0 tests collected, 0 failures (no tests exist yet)
  - `ruff format --check` -- Fails on 10 files (pre-existing formatting differences, not introduced by this session)
- **Environment notes:** Only Python 3.14 available on system. Full `pip install -e ".[dev]"` fails due to dependency conflicts (brave-search requires httpx<0.26, our pyproject.toml requires httpx>=0.27). Pydantic + pydantic-settings install fine. Production build must target Python 3.11-3.12.
- **Issues discovered but not fixed:**
  - `ruff format` style differences across all 10 model files (pre-existing from Session 6). Running `ruff format src/` would fix but changes are cosmetic and outside this session's scope.
  - `agents.py` line 14 has same runtime import pattern for ModelTier but no `# noqa: TC001`. ruff doesn't flag it currently (possibly because agents.py isn't in the import-sorted group), but should get the noqa for consistency.
  - `pyproject.toml` dependency conflicts (brave-search httpx pin, pydantic-ai version) need resolution on Python 3.11/3.12.
- **Set up next:** All audit findings fixed. Ready to build Components #1 (RESEARCH.md spec format) and #2 (Citation model validation) in Week 1.

---

## Session 11: Batch 2 Deep Research Analysis (Parallel Architecture)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6) -- orchestrator + 10 parallel Opus subagents
- **Duration:** ~45 min
- **Task:** Analyze 10 deep research reports (Batch 2) addressing open architectural questions. Each report analyzed by an independent Opus subagent with full project context. Orchestrator wrote master synthesis cross-referencing all 10.
- **Approach:** Three-phase execution. Phase 1: orchestrator loads shared context (CURRENT-STATE.md, JACK-ARCHITECTURAL-DIRECTIVES.md, CAPSTONE-PLAN-v2.md Sections 2-5, PHASE-1-IMPLEMENTATION-SPEC.md, UNIFIED-SYNTHESIS.md Section 6), identifies and maps all 10 reports. Phase 2: 10 Opus subagents spawned simultaneously, each with identical shared context plus unique report assignment and focus instructions. Phase 3: orchestrator reads all 10 analyses and writes master synthesis.
- **Key outputs:**
  - `audit/batch-2-analysis/analysis-01-iterative-research.md` -- Iterative research loop fully specified
  - `audit/batch-2-analysis/analysis-02-dynamic-agents.md` -- Template registry pattern, tighten-only invariant
  - `audit/batch-2-analysis/analysis-03-mece-issue-trees.md` -- Heterogeneous lenses, shallow-then-adaptive
  - `audit/batch-2-analysis/analysis-04-retrieval-architecture.md` -- Component #3 split, Voyage-finance-2
  - `audit/batch-2-analysis/analysis-05-engagement-taxonomy.md` -- 70% blend, Day-1 Hypothesis, WWHTB
  - `audit/batch-2-analysis/analysis-06-context-management.md` -- Opus compaction, artifact bypass, selection > synthesis
  - `audit/batch-2-analysis/analysis-07-adaptive-evaluation.md` -- Geometric mean, tier split, 8-10 profiles
  - `audit/batch-2-analysis/analysis-08-mcp-ecosystem.md` -- ContextForge, paper-search-mcp, Finnhub
  - `audit/batch-2-analysis/analysis-09-orchestration-patterns.md` -- PydanticAI confirmed, error recovery Phase 1, DB state machine HITL
  - `audit/batch-2-analysis/analysis-10-specification-engine.md` -- 10-step pipeline, 5-type taxonomy, CBR library
  - `audit/batch-2-analysis/MASTER-SYNTHESIS.md` -- Master synthesis: 16 decisions, 6 contradictions resolved, 48 plan changes
  - `CURRENT-STATE.md` -- Updated with Batch 2 analysis results
- **Key decisions (16 new, pending Jack's review):**
  - Spec Engine upgraded to 10-step pipeline (from 7)
  - Iterative research loop fully mechanized: 3-criterion stopping, 3-5 round cap, scope-change protocol
  - Issue trees: heterogeneous consulting lenses, shallow start, adaptive deepening
  - Component #3 split into #3a (source discovery) + #3b (knowledge accumulation / Karpathy wiki)
  - Voyage-finance-2 as primary embedding model (49% improvement on financial QA)
  - Deliberation: claim-level selection replaces synthesis (81% vs 51.2%)
  - Evaluator: geometric mean, 4 universal gates + 6 adaptive dims, 8-10 engagement profiles
  - Error recovery Layers 1-2 in Phase 1 (Claude API: 62 incidents in 90 days)
  - Database state machine HITL for Phase 1 (maps to Temporal Phase 2)
  - Agent SDK removed from primary stack
  - paper-search-mcp replaces Academix
  - All 11 settled decisions validated. All Jack's directives validated or fully resolved.
- **Contradictions resolved (6):** Observation Library storage (filesystem Phase 1, PostgreSQL Phase 2), Self-MoA vs cross-provider (different pipeline stages), engagement taxonomy reconciliation (domain vs analytical mode), sprint contract directionality, rubric aggregation method, Agent SDK role.
- **Open questions (8):** Quality gate thresholds, orchestrator model for mid-round synthesis, template similarity calibration, exemplar library bootstrap, framework retrieval sequencing, cross-engagement wiki contamination, 15x token cost validation, RESEARCH.md versioning across rounds.
- **Set up next:** Jack reviews MASTER-SYNTHESIS.md Section 6 (16 decisions). After settlement: update CAPSTONE-PLAN-v2.md with 48 changes, update PHASE-1-IMPLEMENTATION-SPEC.md component scopes. Then build begins with the parallel block (#1, #2, #3a, #3b, #4, HITL).

---

## Session 12: Track 1 Architecture Finalization
**Date:** 2026-04-05
**Session type:** Claude Code with 3 parallel Opus subagents + 2 background agents
**Duration:** ~45 minutes

### Task
Apply all 48 recommended changes from MASTER-SYNTHESIS Section 9 to CAPSTONE-PLAN-v2.md, filtered through Directive 13 (Phase 1/Phase 2 staging). Update PHASE-1-IMPLEMENTATION-SPEC.md, CURRENT-STATE.md, and CLAUDE.md to match.

### Architecture
- Phase 0: Read all 11 context files (~5,000 lines of source material)
- Phase 1: 3 parallel Opus subagents produced change specifications for their assigned sections
  - Subagent A: §3 + §4 (22 changes, spec-A.md)
  - Subagent B: §5 + §6 (16 changes, spec-B.md)
  - Subagent C: §7 + §12 (10 changes, spec-C.md)
- Phase 2: Orchestrator reviewed all 3 specs for completeness and cross-section consistency
- Phase 3: Applied all 48 changes to CAPSTONE-PLAN-v2.md
- Phase 4: Updated PHASE-1-IMPLEMENTATION-SPEC.md (background agent)
- Phase 5: Updated CURRENT-STATE.md and CLAUDE.md
- Phase 6: Created change-audit.md and DIFF-SUMMARY.md (background agent)

### Files created
- `audit/track-1-session/context-verification.md` -- Pre-edit context verification
- `audit/track-1-session/change-spec-A.md` -- 22 change specifications for §3, §4
- `audit/track-1-session/change-spec-B.md` -- 16 change specifications for §5, §6
- `audit/track-1-session/change-spec-C.md` -- 10 change specifications for §7, §12
- `audit/track-1-session/change-audit.md` -- 48-change verification audit
- `audit/track-1-session/DIFF-SUMMARY.md` -- Human-readable change summary

### Files modified
- `CAPSTONE-PLAN-v2.md` -- 48 changes applied across §3, §4, §5, §6, §7, §12
- `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- Component specs updated for all Batch 2 changes
- `CURRENT-STATE.md` -- Updated to reflect architecture finalization completion
- `CLAUDE.md` -- Added audit/track-1-session/ to project structure

### Key decisions
- Sprint contract directionality (Change #27): Classified as Phase 2 per Directive 13, overriding PARALLEL-EXECUTION-PLAN which classified it as Phase 1
- Dimension-specific verification (Change #28): ALL dimension-specific verification classified as Phase 2 per Directive 13, including programmatic QR which PARALLEL-EXECUTION-PLAN classified as Phase 1
- §6.2 rewrite strategy: Complete subsection replacement rather than incremental patches, based on Subagent B's recommendation that the retrieval changes are too interconnected for surgical edits
- Day-1 Hypothesis: Classified as Phase 1 despite not being in Directive 13's explicit Phase 1 list, because it anchors the iterative research loop's stopping condition and cannot be deferred without changing data flow
- ADaPT reactive decomposition (Change #22): Classified as Phase 2, Phase 1 uses static tree depth from Step 3

### What comes next
1. Track 2: Fork evaluation sessions (SemanticCite, mcp-gateway, VectorChord)
2. Track 3: Casing book analysis (Jack + Opus 1M context)
3. Prerequisites: Python 3.11/3.12, PostgreSQL, Exa API key, Brave API key
4. Phase 1A builder sessions: Components #1, #2, HITL (parallel)

---

## Session 1A-2: Component #2 -- Citation Data Model Build
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, 1M context)
- **Task:** Build Component #2: citation data model, content-hash provenance, JSON schemas, citation pipeline utilities

### Files created
- `src/keystone/citation/__init__.py` -- Package init, re-exports all citation utilities
- `src/keystone/citation/hash.py` -- SHA-256 content hashing: compute_content_hash, compute_proposition_hash, verify_content_hash
- `src/keystone/citation/dedup.py` -- Citation deduplication (union-find by URL/DOI) + corroboration pair detection across agents
- `src/keystone/citation/url_check.py` -- Async URL liveness checking (HEAD with GET fallback, batch concurrency via semaphore)
- `schemas/citation.schema.json` -- JSON Schema for Citation entity (CIT- prefix, 0-1 quality_score, hex content_hash)
- `schemas/claim.schema.json` -- JSON Schema for Claim entity (CLM- prefix, confidence tiers, proposition_hashes)
- `schemas/citation_manifest.schema.json` -- JSON Schema for CitationManifest ($ref to citation.schema.json)
- `tests/unit/test_citation_models.py` -- 26 tests: Citation, Claim, CorroborationPair, CitationManifest, WikiCompilationRecord
- `tests/unit/test_citation_hash.py` -- 12 tests: content hashing, proposition hashing, verification
- `tests/unit/test_citation_dedup.py` -- 14 tests: URL/DOI dedup, agent merging, corroboration pairs
- `tests/unit/test_url_check.py` -- 9 tests: HEAD/GET fallback, timeouts, batch concurrency (pytest-httpx mocks)

### Files modified
- `src/keystone/models/citations.py` -- Added content_hash (validated 64-char hex) to Citation, proposition_hashes to Claim, WikiCompilationRecord class. Fixed TYPE_CHECKING bug: moved date/datetime to runtime imports (Pydantic v2 needs runtime access).
- `src/keystone/models/__init__.py` -- Added WikiCompilationRecord to exports

### Key decisions
- Union-find deduplication: Citations grouped by URL OR DOI transitively (A shares URL with B, B shares DOI with C -> all merge). Simpler DOI-first keying broke when one record had a DOI and the other didn't.
- Corroboration at URL level: find_corroboration_pairs matches citations by URL across agents. Same-agent citations don't count. overlap_score=1.0 for exact URL match (semantic similarity deferred to when embeddings exist).
- content_hash validator: 64-char lowercase hex enforced via regex. None allowed for not-yet-verified citations.
- Fixed pre-existing bug: date/datetime under TYPE_CHECKING made Citation uninstantiable. Moved to runtime import with noqa:TC003.

### Test results
- 61/61 tests passing
- Pre-existing failures in test_research_models.py (same TYPE_CHECKING bug in research.py -- not in scope, owned by Session 1A-1)

### What comes next
1. Component #8 (CitationProcessor) will use these models and utilities to implement the full citation processing pipeline
2. The TYPE_CHECKING bug in research.py should be fixed (same pattern as the citations.py fix)

---

## Session 14: HITL Infrastructure Build (Phase 1A-3)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6)
- **Task:** Build the Human-in-the-Loop review gate infrastructure (Component #HITL). Implements Jack's Directive 7: two mandatory human review gates (post-specification and post-deliberation).

### What was built
Complete HITL infrastructure: database state machine, REST API, pipeline integration, events, and contract.

### Files created
- `src/keystone/hitl/__init__.py` -- Module docstring
- `src/keystone/hitl/models.py` -- SQLAlchemy 2.0 ORM: ReviewGate, ReviewItem, ReviewDecision (3 tables)
- `src/keystone/hitl/schemas.py` -- Pydantic API schemas: enums (GateType, GateStatus, DecisionType, ReviewItemType), request/response models
- `src/keystone/hitl/db.py` -- Async database engine/session factory with FastAPI dependency injection
- `src/keystone/hitl/service.py` -- HITLService: create_gate, get_gate, get_pending_gates, list_gates, submit_decision, wait_for_decision
- `src/keystone/hitl/api.py` -- FastAPI router: 5 endpoints (list pending, list by engagement, create gate, get detail, submit decision)
- `src/keystone/hitl/gate.py` -- Pipeline integration: create_and_wait_for_gate(), build_spec_gate_items(), build_deliberation_gate_items(), GateRejectedError, GateTimeoutError
- `src/keystone/hitl/migrations/001_create_hitl_tables.sql` -- PostgreSQL migration with CHECK constraints and indexes
- `tests/unit/hitl/__init__.py`
- `tests/unit/hitl/test_service.py` -- 18 tests: creation, retrieval, filtering, state transitions, timeout
- `tests/unit/hitl/test_api.py` -- 14 tests: all REST endpoints, error cases, validation
- `tests/unit/hitl/test_gate.py` -- 10 tests: convenience builders, async approve/reject/modify/timeout flows

### Files modified
- `src/keystone/events.py` -- Added 5 HITL events (ReviewGateCreated, ReviewDecisionSubmitted, ReviewGateApproved, ReviewGateModified, ReviewGateRejected). Updated AnyPipelineEvent union.
- `src/keystone/contracts.py` -- Added HITLGateContract protocol

### Key decisions
- Session injection: HITLService methods take AsyncSession as parameter (not internally managed). Follows Day-1 coding standard #1 (pure function layers). Enables easy Temporal migration.
- State machine is simple status column: pending -> approved/modified/rejected. Terminal states are final. Maps to Temporal Signal-driven state in Phase 2 with no interface changes.
- wait_for_decision uses DB polling (Phase 1). Phase 2 replaces with Temporal Signal wait. The create_and_wait_for_gate interface in gate.py stays identical.
- GateRejectedError and GateTimeoutError: pipeline stages get clear exceptions to handle halt/timeout cases. No silent failures.
- Separate schemas.py from models.py: API request/response schemas are decoupled from ORM models. Service layer maps between them.
- aiosqlite for tests: all 42 tests run in-memory, no PostgreSQL required for CI.

### Test results
- 42/42 HITL tests passing
- Pre-existing failures in test_research_models.py and test_task_models.py unaffected (TYPE_CHECKING bug, not HITL-related)

### Acceptance criteria status
- Gate 1 blocks pipeline after EngagementSpec: YES (create_and_wait_for_gate blocks)
- Gate 2 blocks after DeliberationResult: YES (same function, different gate_type)
- Approve flow resumes with no changes: YES (tested)
- Modify flow resumes with modifications: YES (tested, modifications_json preserved)
- Reject flow halts pipeline: YES (GateRejectedError raised, tested)
- REST API < 100ms overhead: YES (in-process FastAPI, no network hop)
- Maps to Temporal Signals without agent code changes: YES (only wait mechanism changes)

### What comes next
1. Component #5 (Specification Engine) will call build_spec_gate_items() + create_and_wait_for_gate() at Step 8
2. Component #9 (Deliberation) will call build_deliberation_gate_items() + create_and_wait_for_gate() after confidence map
3. Web UI for human reviewers (deferred -- REST API is sufficient for CLI/programmatic review in Phase 1)
3. Component #3b (Knowledge Accumulation) will use WikiCompilationRecord and content hashing

---

## Session 1A-1: Component #1 Build (RESEARCH.md Specification Format)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, max effort)
- **Task:** Build Component #1 -- schemas, templates, samples, and tests that define the RESEARCH.md engagement specification format and research task structure.

### Files created
- `tests/unit/test_research_models.py` -- 38 unit tests for all model changes (DAG validation, anti-confirmatory framing, tool count, passes/status invariant, custom_category, engagement_type, day_1_hypothesis, issue_tree)
- `tests/unit/test_schemas.py` -- 20 JSON Schema validation tests (sample validation, rejection tests for invalid data)
- `templates/RESEARCH.md.template` -- Canonical engagement specification template with all CAPSTONE-PLAN 3.2 sections + Batch 2 fields
- `templates/research-tasks.json.template` -- JSON template showing DAG structure, dependencies, end_products
- `schemas/research_md.schema.json` -- JSON Schema enforcing decision_context non-empty, questions non-empty, non_goals non-empty, engagement_type enum
- `schemas/research_tasks.schema.json` -- JSON Schema enforcing anti_confirmatory_framing required, assigned_tools 3-5, passes default false, dependencies required, end_product required
- `samples/luminar_lidar/RESEARCH.md.json` -- Strategic engagement, 10 tasks with complex DAG, canonical test case
- `samples/luminar_lidar/research-tasks.json` -- 10 tasks, varied categories, multi-level dependencies
- `samples/auto_body_chain/RESEARCH.md.json` -- Sizing engagement, tests custom_category (Directive 1)
- `samples/auto_body_chain/research-tasks.json` -- 6 tasks, all use custom_category for non-standard categories
- `samples/specialty_chemicals_ma/RESEARCH.md.json` -- Evaluative engagement, M&A use case
- `samples/specialty_chemicals_ma/research-tasks.json` -- 8 tasks, screening->financial->synergy DAG

### Files modified
- `src/keystone/models/tasks.py` -- Added: dependencies (list[str]), end_product (str), issue_tree_branch_id (str|None), custom_category (str|None), effective_category property. Added DAG validation (Kahn's algorithm topological sort) to TaskDecomposition as model_validator.
- `src/keystone/models/research.py` -- Added: EngagementType StrEnum (5 types), engagement_type field on ResearchSpec, day_1_hypothesis field on ResearchSpec, issue_tree field on EngagementSpec. Fixed datetime import from TYPE_CHECKING to runtime (same bug Session 1A-2 fixed in citations.py).
- `src/keystone/models/__init__.py` -- Added EngagementType to exports.

### Key decisions
1. **DAG validation uses Kahn's algorithm** (topological sort via in-degree tracking). Catches cycles, self-references, and invalid dependency references. O(V+E) complexity.
2. **custom_category is additive, not replacing the enum.** The standard TaskCategory enum stays as the structural type. custom_category is a separate field that takes precedence via the effective_category property. This preserves backwards compatibility while enabling Directive 1's "templates, not constraints" principle.
3. **EngagementType is a StrEnum** matching CAPSTONE-PLAN Section 3.8's 5-type taxonomy. Values are lowercase to match JSON schema conventions.
4. **issue_tree on EngagementSpec is dict[str, Any] | None.** Intentionally untyped -- the issue tree structure will be refined when Component #5 (Specification Engine) is built. Using dict keeps the interface flexible without premature structure.
5. **Fixed datetime TYPE_CHECKING bug** in research.py (same issue Session 1A-2 found in citations.py). Pydantic v2 with `from __future__ import annotations` needs runtime type access.

### Test results
- 58 Component #1 tests: all passing
- 161 total tests (including pre-existing): all passing, zero regressions
- Integration check: SpecificationEngineContract.get_spec() return type (EngagementSpec) compatible with all new fields

### What comes next
1. Components #3a, #3b, #4 can proceed in parallel (no dependencies on Component #1)
2. Component #5 (Specification Engine) depends on Component #1 -- ready to build
3. Sample files serve as test fixtures AND few-shot examples for the Spec Engine agent

---

## Session T2-4: Fork Evaluation -- mcp-gateway (Component #4)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, 1M context, max effort)
- **Task:** Clone and evaluate vurgunhajiyev/mcp-gateway as a fork candidate for Component #4 (MCP Gateway). Full 5-phase evaluation: context loading, repo mapping, spec comparison, code quality, integration effort, verdict.

### Files created
- `audit/fork-evaluations/mcp-gateway-eval.md` -- Complete evaluation with requirement matrix, module classification, three-way effort comparison, implementation plan

### Key findings
- **Language:** Python 3.10+ (FastAPI, Pydantic v2, httpx). Full stack match.
- **Size:** ~2,584 lines, 4 commits, 1 contributor, 5 weeks old.
- **Coverage:** 2/10 requirements fully met, 5 partially met, 3 completely absent.
- **Critical gaps:** (1) HTTP-only transport -- no stdio support, which we need for EdgarTools, FRED, doi-mcp. The HTTP proxy assumption is architectural, not patchable. (2) Per-upstream authorization only, not per-tool -- our spec needs agent.assigned_tools enforcement at tool granularity. (3) No citation extraction. (4) No dead-letter path.
- **No LICENSE file** (pyproject.toml says MIT but that's metadata, not a legal grant).
- **FastMCP provides strictly more** than what mcp-gateway provides, plus both transports.

### Verdict: EXTRACT
Do not fork. Build from scratch with FastMCP, extracting 5 specific patterns:
1. Circuit breaker state machine (82 lines, async-lock-guarded CLOSED/OPEN/HALF_OPEN)
2. Token-bucket rate limiter algorithm
3. GatewayState singleton (HTTP pool + CB states + rate buckets)
4. Pydantic Settings with JSON file loading
5. structlog access logging middleware

### Effort estimates
- Fork + modify: ~10-12 days (higher risk from stdio retrofit)
- Build with FastMCP: ~7-9 days (recommended)
- Build from scratch: ~13-15 days

### Set up next
1. Remaining fork evaluations (SemanticCite, VectorChord) if scheduled
2. When Component #4 build begins: start with FastMCP gateway wrapper + 3 MCP servers (Exa HTTP, Brave HTTP, EdgarTools stdio)

---

## Session 2A-1: SemanticCite Fork Evaluation (Component #8)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6)
- **Task:** Evaluate sebhaan/SemanticCite as fork candidate for Component #8 (CitationProcessor).

### Files created
- `audit/fork-evaluations/semanticcite-eval.md` -- Full evaluation report

### Key findings
- **Original URL (`SciPhi-AI/SemanticCite`) does not exist.** SciPhi-AI has no such repo. Evaluated `sebhaan/SemanticCite` instead -- the only Python citation-related repo by that name.
- **Language:** Python. Dependencies: LangChain, ChromaDB, PyTorch, SentenceTransformers, FlashRank, LiteLLM, aiohttp, Streamlit.
- **Size:** ~2,000 lines of source (1,116 in citecheck.py), 14 commits, 1 contributor (Seb Haan), last commit 2025-11-21 (4.5 months stale).
- **Coverage: 0 of 11 Component #8 requirements have any coverage.**
- **Root cause:** SemanticCite is a single-citation verification tool ("Does claim X match document Y?"). Our CitationProcessor is a multi-agent output aggregator (merge, deduplicate, verify, manifest). Completely different problem domains sharing only the word "citation."
- **Dependency conflicts:** LangChain (we use PydanticAI), ChromaDB (not needed), PyTorch (~2GB, not needed), aiohttp (we use httpx).
- **No LICENSE file** (README claims MIT but no legal grant exists).
- **Existing code advantage:** Our `citation/dedup.py`, `citation/hash.py`, `citation/url_check.py`, and `models/citations.py` already provide ~60% of Component #8's functionality.

### Verdict: SKIP
Build from scratch using our existing citation/ utilities. Nothing in SemanticCite maps to our requirements. Fork would cost 7-8 days vs 3-5 days from scratch -- net negative savings.

**Side note:** SemanticCite's hybrid retrieval pipeline (BM25 + dense + FlashRank reranking) could be relevant to Component #3a (Source Discovery) or the Evaluator's Layer 2 citation gate, but not Component #8.

### Set up next
1. VectorChord + VectorChord-BM25 fork evaluation (Component #3a) if scheduled
2. Component #8 build (from scratch) when sequencing reaches it

---

## Session T2-5: VectorChord + VectorChord-BM25 Fork Evaluation (Component #3a)
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, 1M context) + 2 background Sonnet research agents
- **Task:** Evaluate VectorChord + VectorChord-BM25 as potential replacements for pgvector + ParadeDB in Component #3a (Source Discovery).

### Files created
- `audit/fork-evaluations/vectorchord-eval.md` -- Full evaluation report with filled comparison tables, license analysis, migration path, and verdict

### Files modified
- `audit/PHASE-1-IMPLEMENTATION-SPEC.md` -- Updated Component #3a: replaced "Fork candidate: VectorChord as conditional replacement for pgvectorscale pending Track 2 evaluation" with evaluation result and future-enhancement note
- `CURRENT-STATE.md` -- Marked Track 2 Session C complete with verdict summary
- `SESSION-LOG.md` -- This entry

### Approach
- Cloned both repos (`tensorchord/VectorChord`, `tensorchord/VectorChord-bm25`)
- Read source code directly: Cargo.toml (PG version features), vchord.control (`requires = 'vector'`), SQL install files (operator definitions), crate structure
- Grepped both codebases for hybrid/RRF/fusion: zero results
- 2 background Sonnet agents researched web docs, benchmarks, managed hosting, maturity (GitHub stars, funding)
- Cross-referenced against CAPSTONE-PLAN-v2.md Section 6.2 and PHASE-1-IMPLEMENTATION-SPEC.md Component #3a requirements

### Key findings
1. **VectorChord is NOT a replacement for pgvector.** Its control file declares `requires = 'vector'` (pgvector). It reuses pgvector's data types (`vector(N)`) and operators (`<->`, `<#>`, `<=>`). It adds two alternative index types: `vchordrq` (IVF + RaBitQ quantization) and `vchordg` (graph index).
2. **No native hybrid search / RRF fusion.** Neither extension provides built-in dense+BM25+RRF fusion. Both are independent PostgreSQL extensions with separate data types. Application-layer fusion still required, same as pgvector + ParadeDB.
3. **VectorChord-BM25 is immature.** v0.3.0, "only tested against English," requires separate pg_tokenizer.rs extension. ParadeDB is backed by a funded company with richer full-text search features.
4. **VectorChord's advantages are at scale we don't need yet.** Claims 5x query speed, 16x insert throughput, 16x index build speed vs pgvector HNSW -- but at 100M vector scale. At 100K-1M, both are sub-100ms (behind our 200ms Cohere Rerank API call).
5. **Migration path is trivially easy.** Since VectorChord sits on pgvector, adding it later = install extension + change index type from `hnsw` to `vchordrq`. Zero data migration, zero query changes.
6. **License complexity.** Dual AGPLv3 + ELv2 vs pgvector's permissive PostgreSQL License. Acceptable for internal tool but adds unnecessary complexity.

### Verdict: KEEP CURRENT STACK (pgvector + ParadeDB)
- **Confidence:** HIGH
- pgvector HNSW is sufficient for Phase 1 (100K-1M vectors)
- ParadeDB is more mature and feature-rich than VectorChord-BM25
- VectorChord can be added as a zero-cost upgrade when vector count exceeds 10M
- The switching cost is not justified by any concrete advantage at our scale

### Set up next
1. All Track 2 fork evaluations complete (SemanticCite: SKIP, mcp-gateway: EXTRACT, VectorChord: KEEP)
2. Continue Phase 1A parallel block: Components #3a, #3b, #4
3. Component #5 (Specification Engine) is now unblocked by Component #1 completion

---

## Session 8: Component #6 -- Evaluator Stack (L4) Full Build
- **Date:** 2026-04-05
- **Agent:** Claude Code (Opus 4.6, 1M context)
- **Task:** Build the complete L4 Evaluator -- the most important component in the system. 3-layer evaluation stack with 10-dimension rubric, geometric mean aggregation, Tier 1/Tier 2 gating, and 14 prompt templates.

### Files created

**Source modules (9 files, 1,264 lines):**
- `src/keystone/evaluator/__init__.py` (48 lines) -- Package exports
- `src/keystone/evaluator/rubric_config.py` (182 lines) -- 4 evaluation profiles, Tier 1/2 split, weight functions, STRATEGIC_WEIGHT_OVERRIDES
- `src/keystone/evaluator/retry.py` (74 lines) -- LLMCallable type, retry_llm_call with exponential backoff + dead-letter
- `src/keystone/evaluator/layer1_deterministic.py` (146 lines) -- FActScore decomposition, numerical consistency, URL liveness
- `src/keystone/evaluator/layer2_citation_gate.py` (142 lines) -- DOIVerifier Protocol, HTTPDOIVerifier, fabrication classification
- `src/keystone/evaluator/layer3_rubric.py` (200 lines) -- 10-dimension scorer, weighted geometric mean, Tier 1 gate, gestalt overlay
- `src/keystone/evaluator/sprint_contract.py` (88 lines) -- SprintContractGenerator (unilateral Phase 1, ready for Phase 2 negotiation)
- `src/keystone/evaluator/evaluator.py` (331 lines) -- Main orchestrator satisfying EvaluatorContract Protocol
- `src/keystone/evaluator/three_pass.py` (53 lines) -- Three-pass architecture (Pass 3 Observation Library stub for Phase 2)

**Prompt templates (14 files, 7,404 words):**
- `prompts/intent_alignment.md` (621 words)
- `prompts/intellectual_honesty.md` (564 words)
- `prompts/completeness.md` (575 words)
- `prompts/narrative_coherence.md` (589 words)
- `prompts/analytical_depth.md` (650 words)
- `prompts/source_quality.md` (603 words)
- `prompts/quantitative_rigor.md` (563 words)
- `prompts/actionability.md` (613 words)
- `prompts/evaluative_surprise.md` (692 words)
- `prompts/calibrated_confidence.md` (664 words)
- `prompts/gestalt_overlay.md` (525 words)
- `prompts/fact_decomposition.md` (207 words)
- `prompts/numerical_consistency.md` (266 words)
- `prompts/sprint_contract_generation.md` (272 words)

**Test files (6 files):**
- `tests/unit/evaluator/test_rubric_config.py` -- 31 tests (weights, tiers, gate logic)
- `tests/unit/evaluator/test_layer1.py` -- 6 tests (fact decomposition, numerical consistency, URL liveness)
- `tests/unit/evaluator/test_layer2.py` -- 8 tests (DOI verification, URL-only, protocol compliance)
- `tests/unit/evaluator/test_layer3.py` -- 17 tests (geometric mean math, tier gating, prompts)
- `tests/unit/evaluator/test_sprint_contract.py` -- 4 tests (generation, enums, IDs)
- `tests/unit/evaluator/test_evaluator.py` -- 11 tests (full pipeline, intensity, contract, feedback, profiles)

**Test fixtures (7 files):**
- `tests/fixtures/evaluator/clean_output.txt` -- Well-written telematics competitive analysis
- `tests/fixtures/evaluator/numerical_inconsistency.txt` -- "15%" in text vs "12.3%" in table
- `tests/fixtures/evaluator/trendslop_output.txt` -- Generic recommendations, zero insight
- `tests/fixtures/evaluator/mixed_quality.txt` -- One brilliant paragraph + two paragraphs of trendslop
- `tests/fixtures/evaluator/fabricated_citations.json` -- 5 citations, CIT-003 has fabricated DOI
- `tests/fixtures/evaluator/sample_sprint_contract.json` -- Competitive analysis contract
- `tests/fixtures/evaluator/sample_research_task.json` -- Telematics competitive landscape task

### Test results
**77 tests passing, 0 failing.** All fixtures validate against Pydantic models.

### Key design decisions

1. **STRATEGIC_WEIGHT_OVERRIDES:** Analytical Depth 15% (+3%), Actionability 18% (+3%), Evaluative Surprise 8% (+3%), Quantitative Rigor 10% (-5%), Completeness 5% (-3%), Calibrated Confidence 6% (+1%). Non-overridden dimensions scaled proportionally. Rationale: strategic engagements emphasize forward-looking insight and actionability over exhaustiveness.

2. **LLMCallable pattern:** `Callable[[str], Awaitable[str]]` type alias. Every LLM call flows through `retry_llm_call` with exponential backoff (1s, 2s, 4s) and dead-letter after 3 retries (Directive 9). Tests inject mock LLMs.

3. **DOIVerifier Protocol:** `runtime_checkable` Protocol with `async def verify(doi) -> DOIVerificationResult`. Phase 1 uses `HTTPDOIVerifier` (HEAD to doi.org). Phase 1B+ swaps to MCP gateway without code change.

4. **Geometric mean implementation:** `exp(sum(w_i * ln(max(score_i, 1.0))))` with weight normalization for subsets. Hand-verified: [80,80,80] = 80.0, [100,1,100] ~ 21.5, [100,...] = 100.0.

5. **EvaluationResult model_rebuild():** The `evaluation.py` model uses `TYPE_CHECKING` for `datetime`, requiring `model_rebuild()` at import time in evaluator.py.

### Directive compliance
- **Directive 7:** Geometric mean aggregation (not arithmetic mean)
- **Directive 8:** Tier 1/Tier 2 split enforced (Tier 1 failure = skip Tier 2)
- **Directive 9:** retry_llm_call wraps every LLM call, max retries + dead-letter
- **Directive 11:** Light/Standard/Deep intensity operational
- **Directive 13:** Phase 2 features deferred (Layers 4-5, Pass 3, sprint negotiation, dimension-specific verification, 8-10 profiles)

### Phase 2 deferred items
- Layers 4-5 (process trajectory evaluation, diverse judge ensemble)
- Pass 3 (Observation Library negative-space scan) -- stub in three_pass.py
- Sprint contract negotiation (Phase 1 is unilateral; data structure ready)
- Dimension-specific verification strategies (programmatic QR, position-switching AD)
- 8-10 evaluation profiles (Phase 1 has 4: DEFAULT, ESTIMATIVE, CURRENT, STRATEGIC)
- Redraft Specialist subagent for anti-slop remediation

### Handoff to Component #10 (Calibration)
Evaluator is ready for calibration. Needs 10+ Jack-scored deliverables. Target: 0.80+ Spearman correlation between automated and human scores. The calibration runner (Component #10) should use the `EvaluationResult` model and the `CalibrationSample`/`CalibrationReport` models already defined in `models/evaluation.py`.

---

## Session 1A-4: Component #4 -- MCP Gateway Full Build
- **Date:** 2026-04-06
- **Agent:** Claude Code (Opus 4.6, 1M context)
- **Task:** Build the MCP Gateway (Component #4) -- central router for all tool calls. Per-agent authorization, rate limiting, circuit breaking, retry + dead-letter, audit logging.

### Files created

**Source modules (7 files):**
- `src/keystone/gateway/__init__.py` (updated) -- Package exports (21 symbols)
- `src/keystone/gateway/tool_registry.py` -- ToolEntry, TransportType, HealthStatus models + ToolRegistry class
- `src/keystone/gateway/auth.py` -- AuthorizationError, ToolAuthorizer (structural enforcement)
- `src/keystone/gateway/rate_limiter.py` -- Token-bucket rate limiter with RateLimiterBackend Protocol (Redis-ready)
- `src/keystone/gateway/circuit_breaker.py` -- CLOSED/OPEN/HALF_OPEN state machine with async lock
- `src/keystone/gateway/audit_log.py` -- Structured audit logging with SHA-256 I/O hashing (structlog)
- `src/keystone/gateway/mcp_gateway.py` -- Central router: auth -> rate limit -> circuit break -> execute -> cite -> audit
- `src/keystone/gateway/servers.py` -- 7 MCP server configs (Exa, Brave, EdgarTools, FRED, paper-search-mcp, doi-mcp, Finnhub)

**Test files (6 files, 75 tests):**
- `tests/unit/test_tool_registry.py` -- 18 tests (register, get, health, budget, server configs)
- `tests/unit/test_auth.py` -- 8 tests (authorized, unauthorized, empty, unregistered, error fields, get_agent_tools)
- `tests/unit/test_rate_limiter.py` -- 11 tests (capacity, exhaustion, refill, isolation, remaining, retry_after, protocol)
- `tests/unit/test_circuit_breaker.py` -- 10 tests (all state transitions, failure counting, reset)
- `tests/unit/test_audit_log.py` -- 11 tests (success/failure logging, hashing, querying, dead letters, debug mode)
- `tests/unit/test_gateway.py` -- 17 tests (full flow, auth failure, rate limit, circuit break, retry, dead-letter, citation extraction)

### Test results
**75 tests passing in 0.64s, 0 failing.**

### Patterns extracted from mcp-gateway (reimplemented, not copied)
1. **Circuit breaker state machine** (middleware/circuit_breaker.py) -- async-lock-guarded CLOSED/OPEN/HALF_OPEN transitions
2. **Token-bucket algorithm** (core/state.py RateLimitBucket) -- monotonic clock timing, async lock
3. **GatewayState singleton** (core/state.py) -- centralized registry pattern
4. **Pydantic Settings config** (core/config.py) -- env-based configuration pattern
5. **Structured access logging** (middleware/logging_mw.py) -- structlog JSON output

### Directive compliance
- **Directive 9:** Max 3 retries with exponential backoff (0.5s, 1s, 2s). Dead-letter logging after exhaustion. Tested.
- **Directive 11:** Gateway is transport-agnostic (HTTP, stdio, Docker). Pipeline depth configured at Spec Engine level.
- **Directive 14:** Structural enforcement -- agents cannot call unauthorized tools, no prompt-based honor system.

### Phase 2 upgrade paths
- **Redis rate limiter:** RateLimiterBackend Protocol is defined. InMemoryRateLimiter is a drop-in. Redis implementation needs only `try_acquire()` and `get_remaining()`.
- **Real MCP client:** MCPClient Protocol defined. MockMCPClient used in Phase 1. RealMCPClient (FastMCP-based) is a drop-in for Phase 1B.
- **Health checks:** ToolRegistry.health_check_all() returns stored statuses in Phase 1. Phase 1B adds actual server probing.

### Handoff
Specification Engine (#5) can now import ToolRegistry for tool assignment:
```python
from keystone.gateway import ToolRegistry, register_all_tools
registry = ToolRegistry()
register_all_tools(registry)
# Query available tools when building ResearchTask.assigned_tools
```

---

## Session 1A-5: Component #3b Knowledge Accumulation Build
- **Date:** 2026-04-06
- **Agent:** Claude Code (Opus 4.6)
- **Task:** Build Component #3b (Knowledge Accumulation) -- the Karpathy wiki pattern for raw subagent artifact compilation into structured markdown wikis with auto-maintained indexes and content-hash provenance tracking.

### Files created
- `src/keystone/knowledge/__init__.py` -- Module docstring
- `src/keystone/knowledge/wiki_schema.py` -- WikiEntry (Pydantic model), WikiStore (Protocol interface)
- `src/keystone/knowledge/wiki_builder.py` -- WikiBuilder: compiles StructuredFindings into WikiEntries + WikiCompilationRecords
- `src/keystone/knowledge/index_maintainer.py` -- IndexMaintainer: auto-rebuilds INDEX.md after each round
- `src/keystone/knowledge/content_hasher.py` -- ContentHasher: wraps citation/hash.py with wiki provenance verification
- `src/keystone/knowledge/engagement_store.py` -- FilesystemWikiStore: async filesystem backend (Phase 1)
- `tests/unit/knowledge/__init__.py`
- `tests/unit/knowledge/test_wiki_schema.py` -- 11 tests (validation, hash format, frozen model)
- `tests/unit/knowledge/test_content_hasher.py` -- 8 tests (hash correctness, provenance valid/broken)
- `tests/unit/knowledge/test_index_maintainer.py` -- 6 tests (format, alphabetical, coverage stats)
- `tests/unit/knowledge/test_wiki_builder.py` -- 9 tests (compilation, hashes, records, empty handling)
- `tests/unit/knowledge/test_engagement_store.py` -- 11 tests (filesystem CRUD, full round integration, multi-round accumulation, provenance chain)

### Test results
**45 new tests passing, 428 total suite passing, 0 failures.**

### Key design decisions
1. **WikiStore is a Protocol, not a pipeline contract.** It does not appear in contracts.py, does not yield PipelineEvents. Wiki operations are event-silent. Observability is at the calling layer.
2. **Storage-agnostic from Day 1.** WikiStore Protocol has async methods. FilesystemWikiStore uses asyncio.to_thread. PostgresWikiStore is a drop-in replacement for Phase 2.
3. **No direct filesystem calls in wiki_builder.py.** All I/O goes through WikiStore. No hashlib imports in knowledge/ -- all hashing delegates to citation/hash.py.
4. **WikiCompilationRecords produced alongside WikiEntries** to maintain the citation provenance chain (citation_id -> raw_path -> compiled_path -> content_hash).
5. **INDEX.md auto-maintained** after every compile_round call via IndexMaintainer.
6. **Flat raw/ naming** per CAPSTONE-PLAN-v2.md: `{round}_{agent_id}_{task_id}.md`.
7. **JSON metadata sidecar** (.meta.json) stored alongside compiled .md files to enable full WikiEntry reconstruction from filesystem.
8. **compile_round returns tuple** of (list[WikiEntry], list[WikiCompilationRecord]) -- entries for downstream pipeline, records for citation provenance tracking.

### Handoff
Component #7 (Research Agents) writes to raw/ via WikiStore:
```python
from keystone.knowledge.engagement_store import FilesystemWikiStore
from keystone.knowledge.wiki_builder import WikiBuilder
from keystone.knowledge.content_hasher import ContentHasher

store = FilesystemWikiStore(base_path="engagements")
builder = WikiBuilder(store, ContentHasher())
entries, records = await builder.compile_round(
    engagement_id="ENG-001",
    client_id="CLIENT-001",
    round_number=1,
    findings=agent_findings,  # list[StructuredFinding]
)
```
Component #9 (Deliberation) reads from compiled/ via WikiStore:
```python
entries = await store.list_compiled("ENG-001")
index = await store.read_index("ENG-001")
```

---

## Session 1A-6: Component #5 -- Specification Engine (L0) Full Build
- **Date:** 2026-04-06
- **Agent:** Claude Code (Opus 4.6, max effort)
- **Task:** Build Component #5 (Specification Engine) -- the L0 pipeline that takes a natural language question and produces a complete EngagementSpec (RESEARCH.md + research-tasks.json + issue tree + validation report + agent configurations).

### Files created (10 source modules, 1524 lines)
- `src/keystone/specification/__init__.py` (70 lines) -- Module exports
- `src/keystone/specification/_prompts.py` (44 lines) -- Prompt template loading and JSON extraction
- `src/keystone/specification/engagement_classifier.py` (94 lines) -- Step 1: 5-type taxonomy + pipeline profiles
- `src/keystone/specification/intent_clarifier.py` (79 lines) -- Step 2: Decision-First CoT + Day-1 Hypothesis
- `src/keystone/specification/decomposer.py` (192 lines) -- Step 3: 3 heterogeneous lens agents + Opus synthesis
- `src/keystone/specification/validator.py` (89 lines) -- Step 4: MECE verification, 5 binary dimensions
- `src/keystone/specification/priority_scorer.py` (93 lines) -- Step 5: Heuristic scoring (Phase 1)
- `src/keystone/specification/template_registry.py` (311 lines) -- Step 6: 7 seed AgentDefinition templates
- `src/keystone/specification/task_generator.py` (186 lines) -- Step 7: research-tasks.json with DAG
- `src/keystone/specification/spec_engine.py` (366 lines) -- Main orchestrator, implements SpecificationEngineContract

### Prompt templates (9 files, 3015 total words)
- `prompts/classification.md` (388 words) -- 5-signal engagement classification
- `prompts/intent_clarification.md` (480 words) -- Decision-First CoT (5-step)
- `prompts/decompose_financial_lens.md` (280 words) -- Financial perspective tree
- `prompts/decompose_operational_lens.md` (256 words) -- Operational perspective tree
- `prompts/decompose_market_lens.md` (268 words) -- Market/competitive perspective tree
- `prompts/decompose_synthesis.md` (357 words) -- Opus synthesis of 3 lens trees
- `prompts/mece_validation.md` (450 words) -- 5-dimension MECE check
- `prompts/priority_scoring.md` (216 words) -- Heuristic priority scoring
- `prompts/task_generation.md` (320 words) -- research-tasks.json from prioritized tree

### Test files (8 files, 1333 lines, 58 tests)
- `tests/unit/specification/test_engagement_classifier.py` (99 lines, 8 tests)
- `tests/unit/specification/test_intent_clarifier.py` (119 lines, 6 tests)
- `tests/unit/specification/test_decomposer.py` (227 lines, 10 tests)
- `tests/unit/specification/test_validator.py` (126 lines, 6 tests)
- `tests/unit/specification/test_priority_scorer.py` (99 lines, 4 tests)
- `tests/unit/specification/test_template_registry.py` (115 lines, 9 tests)
- `tests/unit/specification/test_task_generator.py` (193 lines, 6 tests)
- `tests/unit/specification/test_spec_engine.py` (355 lines, 9 tests)

### Seed agent templates (7)
1. **Quantitative Analyst** -- SEC filings, FRED, financial data, quantitative modeling
2. **Market Researcher** -- competitive analysis, market sizing, industry reports
3. **Academic Researcher** -- paper search, patent analysis, technology assessment
4. **Regulatory Analyst** -- government sources, compliance, regulatory landscape
5. **Generalist** -- broad research, trend analysis, cross-cutting themes
6. **Contrarian Analyst** -- devil's advocate, assumption challenging, risk identification
7. **Historical Analyst** -- historical analogies, pattern matching across time

### Test results
- 58/58 tests passing
- All 3 audit checkpoints passed
- Full Luminar test case integration test passing

### Key decisions
1. **LLMCallable reused from evaluator.retry** -- same `Callable[[str], Awaitable[str]]` pattern, same retry_llm_call wrapper. No new abstractions.
2. **IssueTree models live in specification module** -- IssueTreeNode, IssueTree, IssueTreeMetadata are internal to specification, serialized to dict for EngagementSpec.issue_tree.
3. **Template registry uses heuristic matching** -- 3-signal scoring (category 0.4, source affinity 0.3, engagement type fit 0.3) instead of LLM-based matching. Fast, deterministic, debuggable.
4. **Decompose retry loop in orchestrator** -- validator.py is pure (returns result), spec_engine.py owns the retry (max 2 retries, returns last tree if all fail).
5. **HITL gate deferred to db_session_factory availability** -- Gate 1 only triggers if db_session_factory is provided. Tests run without DB.
6. **7 templates, not 5** -- Added contrarian and historical analyst templates beyond the minimum 5, matching the existing ResearchAgentType enum values.

### Verification checklist (all passed)
1. Contract compliance: `isinstance(engine, SpecificationEngineContract)` = True
2. Event compliance: SpecificationGenerated, TasksDecomposed, AgentDispatched all yielded with correct fields
3. Model compliance: EngagementSpec, ResearchSpec, TaskDecomposition, ValidationReport all validate
4. Schema compliance: Output matches research_md.schema.json and research_tasks.schema.json structure
5. HITL compliance: Gate 1 triggered with build_spec_gate_items (tested via mock)
6. Directive compliance: custom_category (D1), MECE issue tree with heterogeneous lenses (D2), Light/Standard/Deep profiles (D11), principles-based decomposition (D12), no Phase 2 features (D13)
7. DAG validation: Generated tasks pass Kahn's algorithm cycle detection
8. Anti-confirmatory: All task framings pass the validator in tasks.py
9. No ownership violations: All files in src/keystone/specification/ and tests/unit/specification/
10. Prompt completeness: 9 templates, 216-480 words each

### Phase 2 deferred items
- TiCoder divergence detection in intent clarification
- VOI-inspired priority scoring (full formula: / estimated_cost)
- CBR Observation Library query at Spec Engine entry
- ADaPT reactive decomposition
- Template promotion loop (successful custom configs -> new seed templates)
- Sprint contract negotiation between Evaluator and Generator
- 8-10 engagement-type evaluation profiles (currently defers to evaluator)

### Handoff
Component #7 (Research Agents) can now receive EngagementSpec:
```python
from keystone.specification import SpecificationEngine, TemplateRegistry

engine = SpecificationEngine(llm=my_llm_callable)
async for event in engine.generate_spec(
    question="Evaluate the competitive position of Luminar Technologies...",
    client_id="client_keystone",
    client_context="Growth equity fund considering $200M position",
):
    handle(event)

spec = await engine.get_spec()
# spec.research_spec -> ResearchSpec (RESEARCH.md)
# spec.task_decomposition -> TaskDecomposition (research-tasks.json)
# spec.issue_tree -> dict (MECE issue tree)
# spec.validation_report -> ValidationReport (4 checks)
```
Component #4 (MCP Gateway) provides the ToolRegistry for tool assignment validation.

---

## Session 15: Overnight Audit + Cleanup
- **Date:** 2026-04-06
- **Agent:** Claude Code (Opus 4.6, 1M context, max effort)
- **Task:** Full audit of all 7 overnight build sessions, followed by cleanup fixes. Transition from Cowork orchestration to direct Claude Code orchestration.

### Approach
Two passes. Pass 1 (orientation): read all core project files (CLAUDE.md, CURRENT-STATE.md, JACK-ARCHITECTURAL-DIRECTIVES.md, SESSION-LOG.md, PHASE-1-IMPLEMENTATION-SPEC.md, contracts.py, events.py, all component source code). Pass 2 (deepening): per-component acceptance criteria audit against implementation spec, cross-session tool name verification, L2/L3 pipeline layer resolution.

### Critical finding
**Tool name mismatch between Spec Engine and Gateway.** 9 of 11 tool name strings in `specification/template_registry.py` did not match `gateway/servers.py` registrations. Sessions 1A-4 and 1A-6 independently chose different string identifiers for the same tools.

### Files created
- `src/keystone/tool_names.py` -- ToolName StrEnum, semantic groupings (SEARCH_TOOLS, FINANCIAL_TOOLS, etc.)
- `audit/OVERNIGHT-AUDIT-RESULTS.md` -- Full per-component acceptance criteria audit, tool name finding, L2/L3 resolution

### Files modified
- `src/keystone/gateway/servers.py` -- Imports ToolName from tool_names.py
- `src/keystone/specification/template_registry.py` -- Imports ToolName, all 7 seed templates updated to use registered tool names, 4 missing tools removed
- `src/keystone/specification/task_generator.py` -- _resolve_tools() fallback uses DEFAULT_TOOLS from tool_names.py
- `src/keystone/events.py` -- datetime.utcnow() -> datetime.now(UTC)
- `src/keystone/evaluator/evaluator.py` -- datetime.utcnow() -> datetime.now(UTC) (3 locations)
- `tests/unit/evaluator/test_layer1.py` -- datetime fix
- `tests/unit/evaluator/test_layer2.py` -- datetime fix
- `tests/unit/evaluator/test_sprint_contract.py` -- datetime fix
- `tests/unit/evaluator/test_evaluator.py` -- datetime fix
- `tests/unit/test_research_models.py` -- tool name update
- `tests/unit/specification/test_task_generator.py` -- tool name update
- `tests/unit/specification/test_spec_engine.py` -- tool name update
- `tests/unit/specification/test_template_registry.py` -- tool name update
- `pyproject.toml` -- 11 unused dependencies removed, documented as comments
- `docs/ARCHITECTURE.md` -- Regenerated from actual codebase state
- `CURRENT-STATE.md` -- Updated with audit results and next steps
- `SESSION-LOG.md` -- This entry

### Key decisions
1. **Shared ToolName StrEnum over ad-hoc renaming.** Prevents future drift when new MCP servers are added.
2. **4 unregistered tools removed from templates.** `news_search`, `industry_reports`, `patent_search`, `government_search` have no MCP server configs. Better to have working defaults than aspirational ones that crash at runtime.
3. **L2/L3 confirmed as Phase 2.** MVP pipeline: L0 -> L1 -> CitProc -> L1.5 -> L4 -> Markdown. Contracts exist as hooks.
4. **Dependencies trimmed to actually-imported packages.** Prevents install failures on clean environments. Unused packages documented for when their components are built.

### Test results
486/486 passing. 0 warnings (down from 207).

### What comes next
1. Component #7 (Research Agent Pipeline) -- first real LLM integration
2. Exa and Brave Search API keys needed
3. Start with single-agent, single-round, then expand
