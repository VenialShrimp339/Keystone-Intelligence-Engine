# Execution Readiness Assessment

*Produced: 2026-04-05 | Session C (pre-build audit)*
*Based on: Session A (gap analysis), Session B (code audit), folder inventory, implementation spec review*

---

## Verdict: Ready to build Components #1-#2 tomorrow. Components #3-#4 after a 1-2 hour fix session.

---

## 1. Ready to Build Now

### Component #1: RESEARCH.md Specification Format (Size: S, 2-3 days)

**Evidence:**
- `ResearchSpec` model exists in `src/keystone/models/research.py` with all required fields: decision_context, questions, methodology, source_requirements, quality_bar, non_goals.
- `EngagementSpec` composite model bundles ResearchSpec + TaskDecomposition + ValidationReport.
- Acceptance criteria in implementation spec are clear and testable.
- `templates/` directory exists (empty, ready for template file).
- No external dependencies (no API keys, no infrastructure).

**Can start today:** Yes. Write the template, create 3-5 sample RESEARCH.md files, validate against the Pydantic model.

**One caveat:** The implementation spec references JSON Schema files (`schemas/research_md.schema.json`), but Session 6 decided to use Pydantic models as source of truth and generate schemas via `.model_json_schema()`. The builder should generate the JSON schemas from the models, not write them from scratch.

### Component #2: Citation Data Model Validation (Size: S, 1-2 days)

**Evidence:**
- `Citation`, `Claim`, `CitationManifest`, `CorroborationPair` models exist in `src/keystone/models/citations.py`. Code audit: SOLID.
- `ConfidenceTier`, `ACHDiagnosticity` enums exist and are correctly placed.
- `ConfidenceMap` with 5 tier-specific claim models exists in `confidence.py`. Code audit: SOLID.
- All models have `engagement_id` and `client_id` (Gap #2 satisfied).
- No external dependencies.

**Can start today:** Yes. Create mock citation manifests, validate provenance chains, write unit tests in `tests/unit/models/`.

**Caveat:** The TYPE_CHECKING bug in `research.py` and `confidence.py` will cause runtime failures when tests try to instantiate models with cross-module references. Fix the imports first (15 minutes), then proceed.

---

## 2. Needs Work First

### Fix the TYPE_CHECKING Bug (15 minutes, blocks Components #2-#4)

**What:** Three model files import cross-module Pydantic field types under `TYPE_CHECKING`, which means they're not available at runtime. `research.py` imports `Citation`, `ConfidenceTier`, `TaskDecomposition`; `observations.py` imports `RubricDimension`; `confidence.py` imports `ACHDiagnosticity`.

**Fix:** Either move these imports to runtime (outside `TYPE_CHECKING` block), or add `model_rebuild()` calls in `models/__init__.py` after all imports. The second approach is cleaner for maintaining the import structure.

**Impact if not fixed:** Any test that creates a `FindingClaim`, `ObservationEntry`, or `ModerateConfidenceClaim` with actual data will raise `PydanticUndefinedAnnotation`.

### Fix the env_prefix Mismatch (5 minutes, blocks Component #4)

**What:** `AppConfig` in `config.py` uses `env_prefix = "KEYSTONE_"`, expecting `KEYSTONE_ANTHROPIC_API_KEY`. `.env.example` defines `ANTHROPIC_API_KEY` without the prefix.

**Fix:** Remove `env_prefix = "KEYSTONE_"` from AppConfig. The plain variable names in `.env.example` are more standard and match what the MCP servers expect.

### Fix Rubric Weight Sum (5 minutes, blocks Component #6)

**What:** `RUBRIC_WEIGHTS` in `evaluation.py` sum to 1.05, not 1.00. The plan's math is wrong: reducing Analytical Depth from 15% to 12% and Completeness from 10% to 8% recovers 5%, but two new 5% dimensions cost 10%.

**Fix:** Reduce one dimension by 5% (recommend Intent Alignment from 15% to 10%, since it's partially redundant with Analytical Depth) or redistribute. Jack should decide which dimension to adjust.

**Impact if not fixed:** Weighted scores will be inflated by 5%. Not catastrophic but wrong.

### Deep Research Re-Analysis: Run in Parallel, Not Before Building

**What:** Session A found LEAK-SYNTHESIS.md is ~60-65% complete with 5-6 decision-changing findings. Session A produced a ready-to-paste prompt (`06-deep-research-analysis-prompt.md`).

**Recommendation:** Run the re-analysis in parallel with Components #1-#2. The decision-changing findings primarily affect Components #4 (MCP gateway config hierarchy, 3-input-copy pattern) and #7 (compaction laundering, memory poisoning, output slot reservation). Components #1-#2 are unaffected. The re-analysis results should be available before Component #4 building starts.

---

## 3. Over-Engineered for a 6-Week Capstone

### 3a. Component #3 Retrieval Architecture: 4 sub-systems where 1-2 would suffice

The implementation spec calls for:
- pgvector + hybrid search (dense + BM25 + RRF fusion)
- Semantic Router for query classification
- Docling for structure-aware PDF parsing
- Bifrost-pattern dual-layer caching (Redis hot + disk cold)

**Simplify to:** pgvector + basic embedding search. Add BM25 later if embedding-only search misses exact financial terms. Skip Semantic Router entirely (just run hybrid search for all queries). Skip Docling for MVP (use plain text extraction; add structure-aware parsing in Phase 2). Skip Redis caching (use in-memory LRU cache; engagement-level caching is premature before you know the access patterns).

**What you lose:** Sub-5ms query classification (unnecessary -- the query volume is low), table structure preservation from PDFs (nice-to-have but not MVP), cross-session cache hits (meaningless before you have multiple sessions).

**What you gain:** Component #3 drops from L (1-2 weeks) to M (3-5 days).

### 3b. Five-Tier Confidence Taxonomy: 5 tiers where 3 would suffice

The plan specifies 5 confidence tiers, each with a distinct Pydantic model class (`HighConfidenceClaim`, `ModerateConfidenceClaim`, `WeakConfidenceClaim`, `ContestedClaim`, `InsufficientEvidenceClaim`), each with tier-specific fields (`curmudgeon_challenge`, `steelmanned_opposing_view`, `ach_matrix`).

**Simplify to:** 3 tiers (High/Moderate/Low) with a single `ConfidenceClaim` model that has optional fields for contested claims. The 5-tier system comes from intelligence analysis (IC ICD 203), which is appropriate for the methodology but over-specifies the data model. You can always add tiers later; removing them is harder.

**Risk:** The models already exist and work. Simplifying now means rewriting working code. Recommendation: keep the 5 tiers in the model, but in the MVP pipeline, only use High/Moderate/Low and let the other two tiers be populated organically as the system matures.

### 3c. 10-Dimension Rubric with Type-Specific Weight Overrides

The evaluation model has 10 rubric dimensions, base weights, and two sets of type-specific overrides (estimative vs. current). The weight merge logic is undefined (Session B flagged this).

**Simplify for MVP:** Use 5 core dimensions (Analytical Depth, Source Quality, Citation Integrity, Actionability, Reasoning Rigor) with equal weights for Phase 1. Add the remaining 5 (Intent Alignment, Completeness, Intellectual Honesty, Consistency, Recency) after you've seen real pipeline output and can calibrate meaningfully.

### 3d. 29 Event Types

The event hierarchy has 29 typed events across all layers. For Phase 1 (Components #1-#4), most of these are unused. The events are well-designed and don't add runtime cost, so this is low-priority. But the builder should not feel obligated to emit all 29 events from day one.

---

## 4. Under-Specified

### 4a. How the MCP Gateway Routes to stdio vs. HTTP Servers

The implementation spec lists 6 MCP servers with their transport types (HTTP vs. stdio). The gateway needs to manage both transport types, including stdio process lifecycle (spawn, monitor, restart on crash). The spec says what servers to connect to but not how to handle the dual-transport architecture. The `tool_loader.py` spec is thin.

**Risk:** Ad-hoc stdio process management is a common source of reliability bugs.
**Mitigation:** Use the MCP SDK's built-in `StdioServerParameters` and `StreamableHTTPServerParameters` client classes. Don't write custom process management.

### 4b. How Research Agents Report Partial Findings on Failure

The plan specifies "graceful degradation" and Session A found the "diminishing returns detection" pattern (3 consecutive low-yield calls = stop). But there's no spec for what a partial finding looks like. `StructuredFinding` has all the fields for a complete finding. What does the L1 -> CitationProcessor handoff look like when an agent timed out or hit its context ceiling?

**Mitigation:** Add an optional `completion_status` field to `StructuredFinding` (enum: complete/partial/failed) with an optional `failure_reason` string.

### 4c. Sprint Contract Negotiation Between Generator and Evaluator

The plan describes sprint contracts extensively (Section 5.9), and the `SprintContract` model exists with section-level weight overrides and mandatory elements. But the negotiation protocol -- how L2 proposes contracts, how L4 approves/modifies them, what happens on disagreement -- is unspecified.

**Risk:** Low for Phase 1. Sprint contracts can be static for MVP (hardcoded per engagement type). Dynamic negotiation is Phase 2.

### 4d. Agent Working Directory Layout

The plan says agents have per-agent working directories with advisory locks. But the directory structure (what files go where, how the agent discovers its workspace, how results are collected) is unspecified.

**Mitigation:** Follow the nano-claude-code pattern from `reference/analysis/03-multi-agent.md`: each agent gets a temp directory, writes findings as JSON files, orchestrator collects on completion.

---

## 5. Risk Register

| # | Risk | Likelihood | Impact | L x I | Trigger | Blast Radius | Mitigation |
|---|------|-----------|--------|-------|---------|-------------|------------|
| 1 | **Python 3.11/3.12 dependency resolution fails** | High | High | **Critical** | First `pip install -e ".[dev]"` on the target Python version. Several packages (brave-search, temporalio, pgvector) failed on 3.14; untested on 3.11/3.12. | Blocks all components. No tests can run. | Resolve this in the first 30 minutes of building. Pin exact versions once working. Have a fallback: if temporalio doesn't install, defer Temporal and use simple async orchestration for MVP. |
| 2 | **Component #3 scope creep eats the timeline** | High | High | **Critical** | Attempting to build the full retrieval architecture (4 subsystems) in Week 1. | Consumes 2+ weeks of a 6-week project. Other components starved. | Build MVP retrieval first: pgvector + basic embedding search. No Semantic Router, no Docling, no Redis caching. Test with 5 documents. Add sophistication only after pipeline runs end-to-end. |
| 3 | **MCP server availability/compatibility issues** | Medium | Medium | **High** | Connecting to community MCP servers that may have version mismatches, undocumented requirements, or downtime. | Component #4 delayed. Downstream Components #5-#7 delayed. | Start with Exa (well-documented, HTTP) as the single test server. Add others incrementally. Have a "mock MCP server" fallback for testing pipeline flow without real API calls. |
| 4 | **API key acquisition delays** | Medium | Medium | **High** | Jack doesn't have Exa, Brave, FRED API keys ready. Some require signup, approval, or payment. | Components #3-#4 can only be tested with mocks. Real integration testing blocked. | Jack should sign up for Exa and Brave Search APIs today. Both have free tiers. FRED and EdgarTools can wait (lower priority for MVP). |
| 5 | **Evaluation calibration blocked by missing deliverables** | Low (Phase 1) | High (Phase 2) | **Medium** | Component #10 needs 10+ past Keystone deliverables with quality scores from Jack. If these aren't collected during Phase 1, calibration becomes the bottleneck. | Evaluator can't be calibrated. Final quality assessment impossible. | Jack should start collecting deliverables and assigning quality scores now, even while Phase 1 building proceeds. This is a background task, not a blocking one. |

---

## 6. Recommended Build Sequence

### Day 0 (Today/Tomorrow Morning): Fix Session

**Duration:** 1-2 hours. No new features.

1. Set up Python 3.11 or 3.12 environment. Run `pip install -e ".[dev]"`. Fix any dependency issues. Pin working versions.
2. Fix TYPE_CHECKING imports (3 files, 15 min).
3. Fix env_prefix mismatch (config.py + .env.example, 5 min).
4. Fix RUBRIC_WEIGHTS sum (evaluation.py, 5 min -- Jack decides which dimension to adjust).
5. Update `.claude/skills/architecture/SKILL.md` stale terminology (5 min).
6. Delete `audit/SESSION-CONTEXT.md` (redundant).
7. Run `make check` -- all linting, type checking, and tests should pass on a clean codebase.

### Week 1: Components #1 + #2 (in parallel)

These have zero external dependencies and can start immediately after Day 0 fixes.

- **#1 RESEARCH.md spec format (2-3 days):** Template, 3-5 samples, JSON schema generation from Pydantic models.
- **#2 Citation model validation (1-2 days):** Mock manifests, provenance chain tests, unit tests.
- **In parallel:** Run the deep research re-analysis (Session A's prompt in `06-deep-research-analysis-prompt.md`). Results needed before Component #4.
- **In parallel:** Jack signs up for API keys (Exa, Brave at minimum).

### Week 2: Components #3 (MVP) + #4 (starter)

Start these once API keys are available and the re-analysis results are in.

- **#3 Retrieval MVP (3-5 days):** pgvector setup, basic embedding search, test with 5 documents. Skip Semantic Router, Docling, Redis caching for now.
- **#4 MCP Gateway starter (1 week):** Gateway core, auth, rate limiter, circuit breaker, audit log. Connect Exa (HTTP) and one stdio server. Skip Tool Search progressive loading for now.

### Week 3-4: Components #5 + #6

- **#5 Specification Engine (L0):** Depends on #1 (RESEARCH.md format) and #4 (MCP gateway for tool dispatch).
- **#6 Evaluator Layers 1-3:** Depends on #2 (citation model) for Layer 2 gate. Build Layers 1-2 first, add Prometheus 2 rubric scoring (Layer 3) if time permits.

### Week 5: Components #7 + #8

- **#7 Research Agents (L1):** The core pipeline. Depends on #3 (retrieval), #4 (gateway), #5 (spec engine).
- **#8 CitationProcessor:** Depends on #2 (citation model), #7 (research agent output).

### Week 6: Integration + Polish

- **#9 Basic Deliberation (L1.5):** Single aggregation pass for MVP.
- **#11 End-to-end pipeline test:** Full pipeline run. Fix integration issues.
- **Skip for now:** #10 (Evaluator Calibration) -- requires Jack's deliverables and a working evaluator.

### What's cut from 6 weeks:
- Prometheus 2 local model deployment (Layer 3 can use Haiku instead)
- Temporal durable execution (use simple async orchestration for MVP)
- Redis caching layer
- Semantic Router query classification
- Docling PDF parsing
- Tool Search progressive loading
- Sprint contract dynamic negotiation
- Components #10 (calibration) deferred to post-capstone

This sequence prioritizes getting a working end-to-end pipeline by Week 5, leaving Week 6 for integration testing and the capstone demo preparation.
