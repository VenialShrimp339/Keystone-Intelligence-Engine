# Wave 3: Parallel Session Prompts

*Generated: 2026-04-06 | Planning Session 16*

**Prerequisite:** Waves 1+2 merged. 643 tests passing. 10 components built (all mock LLM).
Codex OAuth configured (`~/.codex/auth.json` exists with valid refresh token).

**These three sessions create files in completely separate directories. No overlaps.**

---

## Session 6: LLM Client Factory + Real API Smoke Test

```
You are building the LLM client factory for the Keystone Intelligence Engine --
the bridge between our mock-tested components and real OpenAI API calls via
Codex OAuth. Read CLAUDE.md (auto-loaded), then read these files IN ORDER:

1. OPENAI-SWITCHOVER-PLAN.md -- Section 1 (Decision 1: Model Tier Mapping,
   including the reasoning_effort table) and Section 3 (Session B).
2. src/keystone/models/tasks.py -- Read ModelTier enum (FLAGSHIP/STANDARD/FAST/LIGHT)
3. src/keystone/models/config.py -- Read LLMProviderConfig, AppConfig (env vars)
4. src/keystone/evaluator/retry.py -- Read LLMCallable type alias and retry_llm_call.
   This is the interface ALL components use for LLM calls.
5. research-reports/openai-switchover/03-pydanticai-openai-integration.md --
   Read the OAuth token management section and the Responses API integration.
   Pay attention to the callable api_key pattern and OpenAIResponsesModel.
6. research-reports/openai-switchover/01-codex-oauth-models-quotas.md --
   Read Section 5 about Responses API via OAuth. Critical: the Codex OAuth
   endpoint uses Responses API ONLY (not Chat Completions), and store:true
   is NOT supported.

CONTEXT ON AUTH: The Codex CLI is installed. ~/.codex/auth.json exists with a
valid ChatGPT Pro OAuth session (auth_mode: chatgpt, refresh_token present).
The Codex CLI manages token refresh automatically. Our .env has:
  OPENAI_AUTH_TYPE=codex_oauth
  CODEX_AUTH_FILE=~/.codex/auth.json
  FLAGSHIP_MODEL=gpt-5.4
  STANDARD_MODEL=gpt-5.4
  FAST_MODEL=gpt-5.4-mini

CONTEXT ON THE RESPONSES API: The Codex OAuth path routes to
chatgpt.com/backend-api/codex/responses. This is the Responses API, not
Chat Completions. PydanticAI supports this via OpenAIResponsesModel with
the 'openai-responses:' model prefix.

YOUR TASK: Create the LLM client factory in two new files, plus a smoke test.

=== PART 1: Build ===

FILES TO CREATE:

1. src/keystone/llm_client.py -- LLM client factory

   This module bridges our LLMCallable abstraction to real OpenAI calls.

   Key components:
   a) CodexTokenProvider class:
      - Reads ~/.codex/auth.json
      - Extracts the access_token
      - Implements __call__() -> str so it can be passed as a callable api_key
        to AsyncOpenAI (see Report 3: "api_key also accepts a callable")
      - On each call, re-reads auth.json to get the latest token
        (Codex CLI handles refresh externally -- we just read the file)
      - Thread/task safe (use asyncio.Lock if needed)

   b) create_openai_client(config: AppConfig) -> AsyncOpenAI:
      - If OPENAI_AUTH_TYPE == "codex_oauth": use CodexTokenProvider
      - If OPENAI_AUTH_TYPE == "api_key": use OPENAI_API_KEY directly
      - Set base_url to "https://chatgpt.com/backend-api/codex" for OAuth path
        (the Codex OAuth endpoint)
      - For api_key auth, use default base_url (api.openai.com)

   c) get_llm_for_tier(tier: ModelTier, config: AppConfig) -> LLMCallable:
      - This is THE function the pipeline calls
      - Creates an AsyncOpenAI client (cached/shared across tiers)
      - Returns an async callable that:
        * Takes a prompt string
        * Calls the Responses API via the OpenAI client
        * Returns the response text
      - Model ID comes from config (flagship_model, standard_model, fast_model)
      - Applies reasoning_effort from llm_settings

   d) LLMFactory type alias:
      LLMFactory = Callable[[ModelTier], LLMCallable]
      This is the interface Session 7's pipeline will use.

2. src/keystone/llm_settings.py -- Per-layer model settings

   Maps pipeline layers to reasoning_effort values:
   | Layer | reasoning_effort |
   | L0 Specification | xhigh |
   | L1 Research | medium |
   | L1.5 Deliberation (analysts) | medium |
   | L1.5 Deliberation (aggregator) | xhigh |
   | L4 Evaluator | high |
   | Extraction/classification | low |

   Provide:
   - get_reasoning_effort(tier: ModelTier) -> str
   - get_model_id(tier: ModelTier, config: AppConfig) -> str

3. tests/unit/test_llm_client.py -- Unit tests (mock the file I/O and API calls)
   - Test CodexTokenProvider reads auth.json correctly
   - Test CodexTokenProvider handles missing file gracefully
   - Test create_openai_client returns AsyncOpenAI for both auth types
   - Test get_llm_for_tier returns a callable
   - Test LLMFactory type works (lambda tier: mock_llm)
   - Test reasoning_effort mapping per tier

CRITICAL IMPLEMENTATION NOTES:

- The Codex OAuth endpoint is: https://chatgpt.com/backend-api/codex
  Use this as base_url for the AsyncOpenAI client when auth_type is codex_oauth.
  The Responses API path is /responses under this base.

- For the actual API call inside the LLMCallable wrapper, use the openai SDK's
  responses.create() method (NOT chat.completions.create):
  ```python
  response = await client.responses.create(
      model=model_id,
      input=prompt,
      # reasoning={"effort": reasoning_effort} if applicable
  )
  ```
  Check the openai SDK docs/source for the exact responses.create() signature.
  If responses.create() is not available in the SDK version, fall back to the
  raw HTTP endpoint.

- Import AppConfig from keystone.models.config for env var access.
  Import ModelTier from keystone.models.tasks for tier mapping.
  Import LLMCallable from keystone.evaluator.retry for the type alias.

- DO NOT install the codex-auth PyPI package. It's community-built and not
  for production. We read auth.json directly.

=== SELF-AUDIT (between Part 1 and Part 2) ===

Run your unit tests. All must pass. Also run the full test suite (pytest tests/)
to verify no regressions. Report the count.

=== PART 2: Real API Smoke Test ===

After unit tests pass, create a smoke test script:

4. tests/integration/test_llm_smoke.py
   - Actually call the OpenAI API via Codex OAuth
   - Test 1: Simple text completion with gpt-5.4 ("Respond with exactly: hello")
   - Test 2: Simple text completion with gpt-5.4-mini (same prompt)
   - Test 3: Structured JSON output (ask for {"answer": "..."} format)
   - Each test should have a 30-second timeout
   - Mark tests with @pytest.mark.integration so they don't run in CI
   - Print: model used, response length, latency, any errors

   Run the smoke tests and report results. If a model isn't accessible or the
   auth fails, diagnose and report the error (don't just fail silently).

   IMPORTANT: These tests make REAL API calls. They will consume quota.
   Keep them minimal (3 tests, short prompts, short responses).

DO NOT:
- Modify any existing source files
- Touch any files outside llm_client.py, llm_settings.py, and test files
- Install codex-auth or any third-party OAuth libraries
- Store tokens in code or logs (print only metadata: model, latency, length)
- Update SESSION-LOG.md or CURRENT-STATE.md

When complete, report: unit test count, smoke test results (which models worked,
latency, any errors), and the exact file paths created.
```

---

## Session 7: Pipeline Orchestrator + Markdown Renderer

```
You are building the pipeline orchestrator and markdown output renderer for the
Keystone Intelligence Engine. This is the "main()" that wires all 10 existing
components into a single end-to-end research pipeline. Read CLAUDE.md (auto-loaded),
then read these files IN ORDER:

1. audit/PHASE-1-IMPLEMENTATION-SPEC.md -- Read the "Minimum Viable Pipeline" section
   (around line 35) and the "Done Criteria" section (around line 795).
2. src/keystone/contracts.py -- Read ALL 9 Protocol contracts. These define every
   pipeline boundary. Your orchestrator calls these interfaces.

Then read each component's constructor to understand how to instantiate them:

3. src/keystone/specification/spec_engine.py -- SpecificationEngine.__init__
   (line 113): takes llm, template_registry, db_session_factory
4. src/keystone/research/agent_pool.py -- AgentPool.__init__ (line 50):
   takes llm, gateway, finding_writer, context_loader, error_recovery, max_retries
5. src/keystone/research/research_agent.py -- ResearchAgent.__init__ (line 63):
   takes llm, gateway, finding_writer, context_loader, error_recovery, max_rounds
6. src/keystone/citation/processor.py -- CitationProcessor.__init__: takes nothing
7. src/keystone/deliberation/deliberation.py -- Deliberation.__init__ (line 54):
   takes analyst_llm, judge_llm, wwhtb_llm, analyst_types, db_session_factory
8. src/keystone/evaluator/evaluator.py -- Evaluator.__init__ (line 61):
   takes llm, profile, doi_verifier, intensity, pass_threshold
9. src/keystone/gateway/mcp_gateway.py -- MCPGateway (read how to construct it
   with MockMCPClient or a real client)
10. src/keystone/hitl/gate.py -- Read create_and_wait_for_gate() usage pattern

Also read:
11. src/keystone/models/tasks.py -- ModelTier enum (FLAGSHIP/STANDARD/FAST/LIGHT)
12. src/keystone/evaluator/retry.py -- LLMCallable type alias

YOUR TASK: Build the pipeline orchestrator and markdown renderer.

=== PART 1: Build ===

FILES TO CREATE:

1. src/keystone/pipeline/__init__.py -- Package exports

2. src/keystone/pipeline/orchestrator.py -- Main pipeline orchestrator

   class Pipeline:
       def __init__(
           self,
           llm_factory: Callable[[ModelTier], LLMCallable],
           gateway: MCPGateway,
           db_session_factory: Callable | None = None,
       ) -> None:
           # Instantiate all components using llm_factory for each tier:
           # L0 (Specification): llm_factory(ModelTier.FLAGSHIP)
           # L1 (Research): llm_factory(ModelTier.STANDARD)
           # L1.5 analysts: llm_factory(ModelTier.STANDARD)
           # L1.5 aggregator: llm_factory(ModelTier.FLAGSHIP)
           # L4 (Evaluator): llm_factory(ModelTier.FLAGSHIP)

       async def run(
           self,
           question: str,
           client_id: str,
           client_context: str | None = None,
       ) -> PipelineResult:
           """Run the full pipeline end-to-end.

           Flow:
           1. L0: SpecificationEngine.generate_spec(question, client_id, ...)
              -> collect events, get EngagementSpec
              -> HITL Gate 1 (if db_session_factory provided)
           2. L1: Create AgentInstances from spec's task_decomposition
              -> AgentPool.execute_all(assignments)
              -> collect StructuredFindings
           3. CitProc: CitationProcessor.process(findings, eid, cid)
              -> get CitationManifest
           4. L1.5: Deliberation.deliberate(manifest, findings, eid, cid)
              -> get ConfidenceMap
              -> HITL Gate 2 (if db_session_factory provided)
           5. L4: For each task, Evaluator.evaluate(output_text, contract, ...)
              -> get EvaluationResults
           6. Render: MarkdownRenderer.render(spec, findings, confidence_map, results)
              -> return PipelineResult

           Yields AnyPipelineEvent throughout for observability.
           """

   class PipelineResult(BaseModel):
       engagement_id: str
       client_id: str
       spec: EngagementSpec
       findings: list[StructuredFinding]
       manifest: CitationManifest
       confidence_map: ConfidenceMap
       evaluation_results: list[EvaluationResult]
       markdown_output: str
       total_tokens: int
       total_events: int

3. src/keystone/pipeline/markdown_renderer.py -- MVP L3 output

   class MarkdownRenderer:
       def render(
           self,
           spec: EngagementSpec,
           findings: list[StructuredFinding],
           confidence_map: ConfidenceMap,
           evaluation_results: list[EvaluationResult],
           manifest: CitationManifest,
       ) -> str:
           """Produce a formatted Markdown deliverable.

           Structure:
           # {spec.research_spec.title}

           ## Executive Summary
           (High-confidence claims from confidence_map)

           ## Key Findings
           (Per-task findings with confidence tiers)

           ## Areas of Uncertainty
           (Weak + Contested claims from confidence_map)

           ## Research Gaps
           (From confidence_map.gaps_identified + absence reports)

           ## Sources
           (All citations from manifest, formatted)

           ## Quality Assessment
           (Evaluation scores summary)
           """

4. tests/unit/pipeline/__init__.py

5. tests/unit/pipeline/test_orchestrator.py
   - Test Pipeline instantiation with mock llm_factory
   - Test each pipeline stage is called in correct order
   - Test events are collected throughout
   - Test PipelineResult has all required fields
   - Test HITL gates are skipped when db_session_factory is None
   - Test partial pipeline (what happens if L1 produces no findings?)

6. tests/unit/pipeline/test_markdown_renderer.py
   - Test basic rendering with mock data
   - Test all sections are present in output
   - Test citations are formatted
   - Test empty findings produce graceful output
   - Test confidence map tiers appear in correct sections

CRITICAL DESIGN NOTES:

- The llm_factory parameter is: Callable[[ModelTier], LLMCallable]
  In tests, use: lambda tier: mock_llm
  In production, Session 6's get_llm_for_tier will be passed here.

- For step 2 (L1), you need to create AgentInstance objects for each task.
  Read models/agents.py to understand AgentInstance fields. The template
  registry provides AgentDefinition; you wrap it in an AgentInstance with
  a unique agent_id and working directory.

- For step 5 (L4), the evaluator takes output_text: str. Convert each
  StructuredFinding to text (json serialization or a formatted string).
  It also needs a SprintContract -- build one from the task's acceptance_criteria.

- For the mock end-to-end test, each component's mock LLM should return
  realistic-looking JSON that the next stage can parse. This is the most
  important test -- it validates the data flow across all boundaries.

- The Pipeline.run() method should also work as an async generator yielding
  events, OR return a PipelineResult. Consider supporting both patterns:
  run() returns PipelineResult, run_with_events() yields events then returns.

=== SELF-AUDIT ===

Run your tests. All must pass. Run the full suite (pytest tests/) to verify
no regressions. Report the count.

=== PART 2: Full Mock End-to-End ===

After unit tests pass, write and run:

7. tests/e2e/test_mock_pipeline.py
   - Feed "Estimate TAM for L4+ AV sensor market" through the entire pipeline
   - Use mock LLMs that return realistic structured JSON at each stage
   - Configure MockMCPClient with canned search results
   - Verify:
     a) Pipeline completes without errors
     b) PipelineResult has all fields populated
     c) markdown_output is non-empty and contains expected sections
     d) Events were emitted from all stages (L0, L1, CitProc, L1.5, L4)
     e) Citations in the output trace back to the manifest
   - Print the generated markdown output to stdout for inspection

   Run this test and report the full output.

DO NOT:
- Modify any existing source files (except adding __init__.py for new packages)
- Touch any files outside src/keystone/pipeline/ and tests/
- Add dependencies to pyproject.toml
- Build real LLM integration (use mock LLMs for all tests)
- Update SESSION-LOG.md or CURRENT-STATE.md

When complete: report test counts, whether the mock end-to-end succeeded,
and paste the first 50 lines of the generated markdown output.
```

---

## Session 8: Test Gaps + Cleanup + Session Log

```
You are filling test coverage gaps and cleaning up the Keystone Intelligence Engine
codebase. This is maintenance work, not new feature development. Read CLAUDE.md
(auto-loaded), then read these files:

1. audit/OVERNIGHT-AUDIT-RESULTS.md -- Read the "Consolidated Test Coverage Gaps"
   section. These are known untested behaviors.
2. src/keystone/research/context_loader.py -- Read it fully. You need to write tests.
3. src/keystone/deliberation/deliberation.py -- Read the HITL gate integration
   (the _trigger_hitl_gate method). You need to add a positive-path test.
4. src/keystone/contracts.py -- Read all 9 Protocol contracts. You'll write
   isinstance verification tests.

=== PART 1: Test Gaps ===

FILES TO CREATE:

1. tests/unit/research/test_context_loader.py
   Read src/keystone/research/context_loader.py carefully. Write tests for:
   - Loading context from a compiled/ wiki directory
   - INDEX.md navigation (finding relevant entries)
   - Empty wiki directory handling
   - Round 1 (no wiki context expected) vs Round 2+ (wiki context loaded)
   - File not found graceful handling

2. Update tests/unit/deliberation/test_deliberation.py
   Add a test for the HITL Gate 2 POSITIVE path:
   - Provide a real (in-memory SQLite) db_session_factory
   - Run deliberation
   - Verify create_and_wait_for_gate was called with gate_type="post_deliberation"
   - You'll need to mock the gate to auto-approve (look at how
     tests/unit/hitl/test_gate.py sets up the database)

3. tests/unit/test_protocol_contracts.py
   For each of the 9 Protocol contracts in contracts.py, verify isinstance:
   - SpecificationEngineContract -> SpecificationEngine
   - ResearchAgentContract -> ResearchAgent
   - CitationProcessorContract -> CitationProcessor
   - DeliberationContract -> Deliberation
   - EvaluatorContract -> Evaluator
   - HITLGateContract -> (check hitl/gate.py for the implementation)
   - ContentStructuringContract -> NOT IMPLEMENTED (skip)
   - GenerationContract -> NOT IMPLEMENTED (skip)
   - ObservationLibraryContract -> NOT IMPLEMENTED (skip)

   This test catches Protocol signature drift -- if a component's method
   signature doesn't match its contract, isinstance returns False.

=== SELF-AUDIT ===

Run ALL tests (pytest tests/ -v). Report the count. Fix any failures.

=== PART 2: Cleanup + Session Log ===

4. Remove empty scaffolding directories that have no Python files:
   - src/keystone/agents/ (contains only an empty definitions/ subdir)
   - src/keystone/generation/ (empty)
   - src/keystone/meta/ (empty)
   - src/keystone/retrieval/ (empty)
   - src/keystone/structuring/ (empty)
   - src/keystone/tools/ (empty)

   Verify each is truly empty before removing. If any contain .py files
   or non-empty subdirectories, DO NOT remove them.

5. Update .env.example -- Add these two new variables that are in the live
   .env but missing from .env.example:
   - OPENAI_AUTH_TYPE=codex_oauth   (add after the OPENAI_API_KEY line)
   - CODEX_AUTH_FILE=~/.codex/auth.json  (add after OPENAI_AUTH_TYPE)

6. Update SESSION-LOG.md -- Append entries for all sessions since Session 15.
   Read the existing format in SESSION-LOG.md to match the style. Add entries for:

   Session 16 (2026-04-06): Planning + orchestration session. OpenAI switchover
   plan produced. Wave 1-3 prompts written. Pre-Wave audit found StructuredFinding
   model gaps (fixed), 5 missing files in Session 1 prompt (fixed). Project root
   cleaned up (12 spent prompts deleted, 4 files moved). Git initialized.

   Wave 1 Sessions (2026-04-06):
   - Session 1A-7: Provider config swap (ModelTier rename, 18 files)
   - Session 1A-8: Prompt migration for GPT-5.4 (22 prompt files)
   - Session 1A-9: Component #8 CitationProcessor MVP (15 tests)

   Wave 2 Sessions (2026-04-06):
   - Session 1A-10: Component #7 Research Agent Pipeline (64 tests)
   - Session 1A-11: Component #9 Deliberation (78 tests)

   For each entry, include: date, agent type, task summary, key files
   created/modified, key decisions, what comes next. Keep entries concise.

DO NOT:
- Modify any source files in src/keystone/ except removing empty directories
  and updating .env.example
- Create new source files (only test files)
- Touch any files in pipeline/ (Session 7 is working there)
- Touch llm_client.py or llm_settings.py (Session 6 is creating those)
- Update CURRENT-STATE.md (the planning session handles this)

When complete: report total test count across the full suite, list of empty
directories removed, and confirm SESSION-LOG.md was updated.
```

---

## Post-Wave 3: Merge + Documentation (Planning Session)

After all three sessions complete, the planning session (this one) will:
1. Audit all three outputs
2. Merge and run full test suite
3. Rewrite CURRENT-STATE.md
4. Regenerate docs/ARCHITECTURE.md
5. Update CLAUDE.md
6. Determine readiness for Wave 4 (first real end-to-end run)
