# Wave 1: Parallel Session Prompts

*Generated: 2026-04-06 | Planning Session 16*

**Prerequisites before launching any session:**
1. Initialize git: `git init && git add -A && git commit -m "Pre-switchover baseline: 7 components, 486 tests passing"`
2. This gives us a rollback point and lets us merge parallel work safely.

**These three sessions touch zero overlapping files. They can run truly in parallel.**

---

## Session 1: Provider Config Swap

```
You are working on the Keystone Intelligence Engine. Read CLAUDE.md (auto-loaded),
then read these files in order before making any changes:

1. OPENAI-SWITCHOVER-PLAN.md -- Sections 1 (Architecture Decisions) and 3
   (Implementation Plan, Session A). This is your task spec.
2. src/keystone/models/tasks.py -- ModelTier enum you're renaming
3. src/keystone/models/config.py -- AnthropicConfig, ModelMixingConfig, AppConfig
4. src/keystone/models/agents.py -- AgentDefinition.model field
5. .env.example -- env vars to rewrite

YOUR TASK: Execute "Session A: Provider Config Swap" from OPENAI-SWITCHOVER-PLAN.md.
This is a pure rename/refactor with zero behavioral changes. All 486 existing tests
must pass after your changes.

SPECIFIC CHANGES:

1. src/keystone/models/tasks.py (ModelTier enum, lines 39-47):
   - OPUS = "opus" -> FLAGSHIP = "flagship"
   - SONNET = "sonnet" -> STANDARD = "standard"
   - HAIKU = "haiku" -> FAST = "fast"
   - Add: LIGHT = "light"
   - Update docstring to be provider-agnostic (remove "Opus for L0/L4" etc.)

2. src/keystone/models/config.py:
   - Rename class AnthropicConfig -> LLMProviderConfig
   - Change field names: opus_model -> flagship_model, sonnet_model -> standard_model,
     haiku_model -> fast_model
   - Change defaults: "claude-opus-4-6" -> "gpt-5.4",
     "claude-sonnet-4-6" -> "gpt-5.4", "claude-haiku-4-5-20251001" -> "gpt-5.4-mini"
   - Add field: reasoning_effort: str = Field(default="medium",
     description="Default reasoning effort: low/medium/high/xhigh")
   - In RateLimitConfig: anthropic_rpm -> provider_rpm
   - In ModelMixingConfig: change all defaults from "opus"/"sonnet"/"haiku" to
     "flagship"/"standard"/"fast". Update docstring.
   - In AppConfig: anthropic_api_key -> openai_api_key,
     anthropic_rpm_limit -> provider_rpm_limit,
     opus_model -> flagship_model (default "gpt-5.4"),
     sonnet_model -> standard_model (default "gpt-5.4"),
     haiku_model -> fast_model (default "gpt-5.4-mini")

3. src/keystone/models/agents.py:
   - default=ModelTier.SONNET -> default=ModelTier.STANDARD
   - Update description to remove Claude-specific tier names

4. .env.example -- Full rewrite:
   - ANTHROPIC_API_KEY -> OPENAI_API_KEY=sk-...
   - OPUS_MODEL -> FLAGSHIP_MODEL=gpt-5.4
   - SONNET_MODEL -> STANDARD_MODEL=gpt-5.4
   - HAIKU_MODEL -> FAST_MODEL=gpt-5.4-mini
   - ANTHROPIC_RPM_LIMIT -> PROVIDER_RPM_LIMIT=60
   - Keep all search API keys (EXA, BRAVE, CROSSREF, etc.) unchanged

5. src/keystone/evaluator/evaluator.py line 54:
   - Change "anthropic_client" -> "llm_client" in usage comment

6. src/keystone/specification/template_registry.py:
   - All 7 templates: model=ModelTier.SONNET -> model=ModelTier.STANDARD

7. src/keystone/specification/task_generator.py line 139:
   - ModelTier(t.get("assigned_model", "sonnet")) -> "standard"

8. src/keystone/specification/decomposer.py docstring (lines 3-6):
   - "Sonnet-tier" -> "standard-tier", "Opus-tier" -> "flagship-tier"

9. src/keystone/specification/validator.py docstring (lines 3, 44):
   - "Opus as judge" -> "flagship model as judge"

10. src/keystone/specification/prompts/task_generation.md line 59:
    - "assigned_model": "sonnet" -> "assigned_model": "standard"

11. pyproject.toml:
    - Uncomment and add: "openai>=1.60.0" and "pydantic-ai>=1.77.0" to dependencies
    - Remove the commented-out "anthropic" line
    - Add "pydantic-ai" to mypy overrides ignore_missing_imports list

TEST FILES TO UPDATE (same rename pattern):
- tests/unit/test_research_models.py: ModelTier.OPUS/SONNET/HAIKU -> FLAGSHIP/STANDARD/FAST
- tests/unit/specification/test_template_registry.py: ModelTier.SONNET -> STANDARD
- tests/unit/specification/test_task_generator.py: "sonnet" -> "standard"
- tests/unit/specification/test_spec_engine.py: "sonnet" -> "standard"
- tests/unit/evaluator/test_sprint_contract.py: ModelTier references
- tests/fixtures/evaluator/sample_research_task.json: "assigned_model": "sonnet" -> "standard"

AFTER ALL CHANGES: Run the full test suite (pytest). All 486 tests must pass.
If any test fails, fix it -- the failures will be because you missed a string
literal or enum reference somewhere. Grep for "opus", "sonnet", "haiku",
"anthropic" across src/ and tests/ to catch stragglers.

DO NOT:
- Touch any prompt files in evaluator/prompts/ or specification/prompts/
  EXCEPT task_generation.md line 59 (another session handles prompt migration)
- Create new files (this is a refactor of existing files only)
- Add OAuth/token management code (that's a later session)
- Change any logic, only names/strings/defaults
- Touch any files in citation/, gateway/, hitl/, knowledge/
- Update SESSION-LOG.md or CURRENT-STATE.md (the planning session handles handoff)

When complete, report: test count, pass/fail, and list every file you modified.
```

---

## Session 2: Prompt Migration for GPT-5.4

```
You are working on the Keystone Intelligence Engine. Read CLAUDE.md (auto-loaded),
then read these files before making any changes:

1. OPENAI-SWITCHOVER-PLAN.md -- Section 4 (Prompt Migration Notes).
   This explains GPT-5.4's behavioral differences and mitigation strategies.
2. research-reports/openai-switchover/02-gpt54-behavioral-differences.md --
   The full research report on GPT-5.4 vs Claude. Read Pattern 5 (system prompt
   adherence) carefully.

YOUR TASK: Adapt all 22 prompt template files for GPT-5.4's documented behavioral
differences. GPT-5.4 has an 80% system prompt completion rate (it silently drops
~20% of constraints). The fix is structural: XML-tagged instruction blocks,
explicit completeness contracts, and scoped constraints.

THE PROBLEM (from research):
- GPT-5.4's "most common failure mode: delivering 80% of what you asked for
  and quietly dropping the rest"
- "Markdown instruction drift: adherence degrades over long conversations"
- OpenAI recommends explicit "completeness contracts" and XML-tagged blocks

YOUR APPROACH FOR EACH PROMPT FILE:
1. Wrap the core output format requirements in <structured_output_contract> tags
2. Add an explicit completeness checklist at the end listing every required field
3. Replace vague constraints ("provide specific feedback") with scoped ones
   ("provide 2-4 specific, actionable sentences per dimension")
4. Add "After the [JSON/output], output nothing further." as a termination signal
5. DO NOT change the analytical content or methodology -- only add structural
   reinforcement

EVALUATOR PROMPTS (14 files in src/keystone/evaluator/prompts/):
These score research output on 10 dimensions. Each needs:
- <evaluation_contract> wrapper specifying exact output format (score + feedback)
- Explicit scoring scale with examples at each tier (90-100, 70-89, 50-69, <50)
- "You MUST provide a specific quote from the text supporting your score"
- Termination: "Output only the JSON. After the closing brace, output nothing."

Files:
- intent_alignment.md
- intellectual_honesty.md
- completeness.md
- narrative_coherence.md
- analytical_depth.md
- source_quality.md
- quantitative_rigor.md
- actionability.md
- evaluative_surprise.md
- calibrated_confidence.md
- gestalt_overlay.md (this is different -- it's the overall adjustment, not a dimension)
- fact_decomposition.md
- numerical_consistency.md
- sprint_contract_generation.md (this generates contracts, not scores -- different format)

SPECIFICATION PROMPTS (8 files in src/keystone/specification/prompts/):
These drive L0 analytical decomposition. Each needs:
- <analytical_contract> wrapper for output structure
- Explicit field checklist
- Anti-drift reinforcement for multi-step reasoning

Files (DO NOT touch task_generation.md -- another session handles it):
- classification.md
- intent_clarification.md
- decompose_financial_lens.md
- decompose_operational_lens.md
- decompose_market_lens.md
- decompose_synthesis.md
- mece_validation.md
- priority_scoring.md

Read each file before modifying it. Understand what it currently does before
adding structural reinforcement. The analytical content is carefully designed --
your job is to add structural guardrails, not rewrite methodology.

EXAMPLE TRANSFORMATION:

Before (classification.md, hypothetical):
  "Classify this engagement into one of five types: sizing, diagnostic,
   evaluative, exploratory, strategic. Output JSON with type and confidence."

After:
  <analytical_contract>
  You MUST output exactly this JSON structure:
  {
    "engagement_type": "one of: sizing, diagnostic, evaluative, exploratory, strategic",
    "confidence": "number 0.0-1.0",
    "rationale": "1-2 sentences explaining the classification",
    "alternative_type": "second-most-likely type or null",
    "alternative_confidence": "number 0.0-1.0 or null"
  }
  All fields are required. Do not omit any field.
  After the closing brace, output nothing further.
  </analytical_contract>

  Classify this engagement into one of five types...

  <completeness_check>
  Before outputting, verify your response includes:
  [ ] engagement_type (one of the five types)
  [ ] confidence (0.0-1.0)
  [ ] rationale (1-2 sentences)
  [ ] alternative_type (or null)
  [ ] alternative_confidence (or null)
  </completeness_check>

DO NOT:
- Touch task_generation.md (Session 1 handles it)
- Change any Python source files
- Change the analytical methodology or scoring rubric within any prompt
- Add new prompt files
- Remove any existing content from prompts -- only ADD structural reinforcement
- Update SESSION-LOG.md or CURRENT-STATE.md

When complete, report: which files you modified, what pattern you applied to each,
and any prompts where the existing structure was already sufficient (no changes needed).
```

---

## Session 3: Component #8 CitationProcessor MVP

```
You are working on the Keystone Intelligence Engine. Read CLAUDE.md (auto-loaded),
then read these files in order before writing any code:

1. audit/PHASE-1-IMPLEMENTATION-SPEC.md -- Search for "#8: CitationProcessor"
   (around line 623). Read the full component spec including acceptance criteria.
2. CURRENT-STATE.md -- Section "What's next" for context.
3. src/keystone/contracts.py -- Read CitationProcessorContract (around line 98).
   This is the Protocol interface you must satisfy.
4. src/keystone/events.py -- Find the CitationProcessor events you must emit
   (CitationDeduped, CorroborationScored, URLVerified, ManifestProduced).
5. src/keystone/citation/__init__.py -- Existing utilities you'll wire together.
6. src/keystone/citation/dedup.py -- Union-find deduplication + corroboration pairs.
7. src/keystone/citation/hash.py -- Content hashing for provenance.
8. src/keystone/citation/url_check.py -- Async URL liveness checking.
9. src/keystone/models/citations.py -- Citation, CitationManifest, CorroborationPair.
10. src/keystone/models/research.py -- StructuredFinding (the input from L1 agents).

YOUR TASK: Build the CitationProcessor MVP. This is the stage between L1 (Research
Agents) and L1.5 (Deliberation). It receives StructuredFindings from multiple agents
and produces a deduplicated, verified CitationManifest.

The MVP spec (from PHASE-1-IMPLEMENTATION-SPEC.md line 43):
"CitationProcessor (dedup + URL check only, skip corroboration scoring)"

But we ARE implementing corroboration scoring because the utility already exists
in citation/dedup.py (find_corroboration_pairs). The "skip" was about the MVP
being viable without it, not about omitting it when the code is already written.

FILES TO CREATE:

1. src/keystone/citation/processor.py -- Main CitationProcessor class
   - Must satisfy CitationProcessorContract from contracts.py
   - Constructor takes no LLM dependency (this is deterministic processing)
   - process() method: async generator yielding typed events
     a. Collect all citations from all StructuredFindings
     b. Deduplicate via deduplicate_citations() from dedup.py
     c. Find corroboration pairs via find_corroboration_pairs() from dedup.py
     d. Run URL liveness checks via batch_check_urls() from url_check.py
     e. Compute content hashes via compute_content_hash() from hash.py
     f. Build and return CitationManifest
     g. Yield events at each step: CitationDeduped, CorroborationScored,
        URLVerified, ManifestProduced
   - get_manifest() method: returns the produced CitationManifest

2. tests/unit/citation/test_processor.py -- Comprehensive tests
   - Test dedup: feed findings from 3 agents where 2 cite the same source
     (same URL). Verify merge.
   - Test dedup by DOI: two citations with different URLs but same DOI. Verify merge.
   - Test corroboration: two agents independently find the same market figure.
     Verify pair is detected.
   - Test URL check: include a dead URL (mock httpx to return 404). Verify flagged.
   - Test content hash: verify every citation in manifest has a content_hash.
   - Test event emission: verify all 4 event types are yielded in correct order.
   - Test empty input: no findings -> empty manifest, no errors.
   - Test single agent: one finding -> no dedup needed, manifest produced.
   - Test manifest schema: output conforms to CitationManifest model.

ALSO UPDATE:
- src/keystone/citation/__init__.py -- Add processor exports

ARCHITECTURE NOTES:
- The existing dedup.py and url_check.py do the heavy lifting. Your processor.py
  is primarily an orchestrator that wires them together and emits events.
- URL checking is async (uses httpx). Mock it in tests using pytest-httpx or
  by patching batch_check_urls.
- The processor does NOT need LLM calls. All operations are deterministic.
- Follow the same async generator pattern used by every other component
  (see evaluator/evaluator.py or specification/spec_engine.py for the pattern).
- Use the exact event types from events.py. Read them to understand their fields.

CRITICAL: Read dedup.py carefully. Understand what deduplicate_citations() returns
and what find_corroboration_pairs() expects. Don't reinvent what's already built.
Similarly, read url_check.py to understand batch_check_urls() signature and return type.

DO NOT:
- Modify any existing source files except citation/__init__.py (add exports)
- Create files outside of src/keystone/citation/ and tests/unit/citation/
- Add any dependencies to pyproject.toml
- Use any LLM calls -- this component is purely deterministic
- Update SESSION-LOG.md or CURRENT-STATE.md
- Touch any prompt files, config files, or model files

When complete: run pytest on your new tests AND the existing citation tests
(tests/unit/test_citation_dedup.py, test_citation_hash.py, test_url_check.py)
to verify you haven't broken anything. Report test count and pass/fail.
```

---

## Post-Wave 1 Merge

After all three sessions complete, a single merge session should:
1. Verify all changes are compatible (no file conflicts expected)
2. Run the full test suite (486 original + new Component #8 tests)
3. Update SESSION-LOG.md with all three sessions
4. Update CURRENT-STATE.md to reflect new state
5. Regenerate docs/ARCHITECTURE.md to include CitationProcessor

---

## Wave 2 Preview (after Wave 1 merges + OAuth credentials configured)

**Session 4: LLM Client Factory + Component #7 Research Agent Skeleton**
- Create src/keystone/llm_client.py (OAuth TokenManager, model factory)
- Create src/keystone/llm_settings.py (per-layer reasoning_effort mapping)
- Build research agent orchestrator with mock LLM (same pattern as other components)
- This is the biggest session -- combines Session B from the switchover plan
  with the Component #7 build from PHASE-1-IMPLEMENTATION-SPEC.md

**Session 5: Component #9 Deliberation Skeleton**
- Build deliberation orchestrator with mock LLM
- Independent analyst spawning + claim-level selection aggregator
- HITL Gate 2 integration (hitl/ module is already built)
- Depends on Component #8 output types (from Wave 1 Session 3)
