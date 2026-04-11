# Wave 2: Parallel Session Prompts

*Generated: 2026-04-06 | Planning Session 16*

**Prerequisite:** Wave 1 merged and committed. 501 tests passing. 8 of 12 components built.

**These two sessions create files in completely separate directories. No overlaps. Fully parallel.**

---

## Session 4: Component #7 -- Research Agent Pipeline

```
You are building Component #7 (Research Agent Pipeline) for the Keystone Intelligence
Engine. This is the first component where agents actually DO research -- taking tasks,
calling tools, and producing structured findings. Read CLAUDE.md (auto-loaded), then
read these files IN ORDER before writing any code:

1. audit/PHASE-1-IMPLEMENTATION-SPEC.md -- Search for "#7: Research Agent Pipeline"
   (around line 551). Read the full spec including acceptance criteria and first test.
2. src/keystone/contracts.py -- Read ResearchAgentContract (around line 66).
   This is the Protocol interface you must satisfy.
3. src/keystone/events.py -- Find the L1 events you must emit: ResearchStarted,
   SourceFound, CitationExtracted, FindingSynthesized, ResearchComplete.
4. src/keystone/models/research.py -- Read StructuredFinding and FindingClaim.
   This is the output your agents must produce. Note the fields: status (FindingStatus),
   gaps, artifact_path were recently added (they have defaults).
5. src/keystone/models/tasks.py -- Read ResearchTask. This is the input.
6. src/keystone/models/agents.py -- Read AgentDefinition and AgentInstance.
7. src/keystone/specification/template_registry.py -- Read the 7 seed templates.
   Your agents load configs FROM these templates.
8. src/keystone/gateway/mcp_gateway.py -- Read MCPGateway and MockMCPClient.
   Your agents call tools THROUGH the gateway. In tests, use MockMCPClient.
9. src/keystone/evaluator/retry.py -- Read LLMCallable and retry_llm_call.
   This is the pattern for all LLM calls. Your agents use LLMCallable, not a
   provider-specific client.
10. src/keystone/knowledge/wiki_builder.py -- Skim the compile_round() method.
    Your context_loader.py reads FROM the wiki's compiled/ directory.

YOUR TASK: Build the research agent pipeline in src/keystone/research/.

MODULE STRUCTURE:

src/keystone/research/
    __init__.py           -- Package exports
    research_agent.py     -- Single agent executor. Takes a ResearchTask + EngagementSpec
                             + AgentInstance. Runs an iterative loop: call tools via
                             gateway -> process results -> synthesize -> repeat.
                             Produces StructuredFinding. Uses LLMCallable for all LLM calls.
    agent_pool.py         -- Parallel agent manager. Spawns N agents concurrently.
                             Collects results. Handles partial-result continuation:
                             if 3 of 5 agents succeed, combine results + retry failures.
    isolation.py          -- Per-agent filesystem isolation. Creates isolated working
                             directories. Agents cannot read each other's files.
                             Advisory file locks. Async-safe.
    finding_writer.py     -- Builds StructuredFinding from agent output. Enforces:
                             every claim has citations (structurally, not via prompt),
                             per-claim confidence scores, non-empty absence report,
                             1000-2000 token condensed output. Writes full artifact to raw/.
    task_claimer.py       -- Lock-file-based task claiming for concurrent agents.
    context_loader.py     -- JIT context loading from compiled/ wiki. Reads INDEX.md
                             to navigate, loads relevant entries for round N+1.
    error_recovery.py     -- Retry with exponential backoff (use tenacity or the
                             existing retry_llm_call pattern). Model fallback chain:
                             flagship -> standard -> fast. Error classification.

tests/unit/research/
    __init__.py
    test_research_agent.py  -- Test single-agent execution with mock LLM + MockMCPClient
    test_agent_pool.py      -- Test parallel execution, partial-result continuation
    test_isolation.py       -- Test filesystem isolation (agents can't see each other)
    test_finding_writer.py  -- Test StructuredFinding validation (citations required,
                               confidence scores present, absence report non-empty)
    test_task_claimer.py    -- Test concurrent claiming
    test_error_recovery.py  -- Test retry, fallback chain, partial results

CRITICAL PATTERNS TO FOLLOW:

1. LLMCallable for ALL LLM calls:
   ```python
   from keystone.evaluator.retry import LLMCallable, retry_llm_call

   class ResearchAgent:
       def __init__(self, llm: LLMCallable, gateway: MCPGateway): ...
   ```
   Tests pass a mock: `async def mock_llm(prompt: str) -> str: return '...'`

2. Async generator for event emission (same as evaluator and spec engine):
   ```python
   async def execute(self, task, spec, agent) -> AsyncIterator[AnyPipelineEvent]:
       yield ResearchStarted(...)
       # ... do work ...
       yield ResearchComplete(...)
   ```

3. Tool calls through the gateway:
   ```python
   result = await self._gateway.execute(ToolCall(
       agent_id=agent.agent_id,
       tool_name="exa_search",
       parameters={"query": "..."},
   ))
   ```
   In tests, configure MockMCPClient with canned responses.

4. Template-based agent configuration (NOT hardcoded types):
   Load AgentDefinition from template_registry. The template determines tools,
   system prompt, and research methodology. Do not hardcode agent types.

5. Iterative research loop:
   - Default 3 rounds, max 5
   - Three stopping criteria (any one terminates): hard round cap, quality
     threshold met, semantic novelty exhaustion (no new claims in last round)
   - Round N+1 uses context from compiled/ wiki (loaded by context_loader.py)

SCOPE -- BUILD NOW:
- All 7 files listed above
- All 6 test files listed above
- The iterative loop STRUCTURE (rounds, stopping criteria) but with mock LLM
  producing canned findings per round
- Error recovery with retry and model fallback chain

SCOPE -- DO NOT BUILD (Phase 2 or post-OAuth):
- fork_manager.py, micro_compact.py, auto_compact.py (Claude-specific optimizations)
- Real LLM integration (OAuth not configured yet)
- MAX_THINKING_TOKENS config (provider-specific)
- Agent definition .md files in .claude/agents/ (those are for Claude Code itself)
- Soul prompts (defer until real LLM testing)

NOTE ON THE IMPLEMENTATION SPEC: The spec says the output has a `condensed_summary`
nesting with claims inside it. The ACTUAL Pydantic model (StructuredFinding in
models/research.py) has claims FLAT at the top level, with status, gaps, and
artifact_path as separate fields. FOLLOW THE PYDANTIC MODEL, not the spec's
JSON example. The model is the source of truth.

NOTE ON MODEL TIERS: The codebase was just migrated from Anthropic to OpenAI.
ModelTier values are now FLAGSHIP/STANDARD/FAST/LIGHT (not opus/sonnet/haiku).
The default for research agents is ModelTier.STANDARD.

DO NOT:
- Modify any existing files except adding exports to a new __init__.py
- Touch any files in evaluator/, specification/, citation/, gateway/, hitl/, knowledge/
- Add dependencies to pyproject.toml (openai and pydantic-ai are already added)
- Update SESSION-LOG.md or CURRENT-STATE.md
- Build real LLM integration or OAuth code

When complete: run pytest on your new tests AND the full suite. Report counts.
```

---

## Session 5: Component #9 -- Deliberation (L1.5)

```
You are building Component #9 (Deliberation) for the Keystone Intelligence Engine.
Deliberation is the stage between CitationProcessor and the Evaluator. It takes
corroborated findings and produces a confidence map through independent parallel
analysis + structured aggregation. Read CLAUDE.md (auto-loaded), then read these
files IN ORDER before writing any code:

1. audit/PHASE-1-IMPLEMENTATION-SPEC.md -- Search for "#9: Deliberation"
   (around line 661). Read the full spec including acceptance criteria.
2. src/keystone/contracts.py -- Read DeliberationContract (around line 129).
   This is the Protocol interface you must satisfy.
3. src/keystone/events.py -- Find the L1.5 events you must emit: AnalystSpawned,
   IndependentAnalysisComplete, AggregationComplete, ConfidenceMapProduced.
4. src/keystone/models/confidence.py -- Read the ENTIRE file. This defines
   ConfidenceMap with its five tier-specific claim models (HighConfidenceClaim,
   ModerateConfidenceClaim, WeakConfidenceClaim, ContestedClaim,
   InsufficientEvidenceClaim). This is your primary output.
5. src/keystone/models/citations.py -- Read CitationManifest (your input),
   Claim (your output), CorroborationPair, ConfidenceTier.
6. src/keystone/models/research.py -- Read StructuredFinding and FindingClaim
   (your input from L1 agents via CitationProcessor).
7. src/keystone/evaluator/retry.py -- LLMCallable pattern for all LLM calls.
8. src/keystone/hitl/gate.py -- Read create_and_wait_for_gate(). This is how
   you trigger HITL Gate 2 after the confidence map is produced.
9. src/keystone/hitl/schemas.py -- Read GateType (you need "post_deliberation").
10. src/keystone/citation/processor.py -- Read the CitationProcessor to understand
    what you receive as input (CitationManifest + findings).

YOUR TASK: Build the deliberation module in src/keystone/deliberation/.

MODULE STRUCTURE:

src/keystone/deliberation/
    __init__.py              -- Package exports
    deliberation.py          -- Main orchestrator. Satisfies DeliberationContract.
                                Two-phase flow:
                                Phase 1: Spawn 3-5 independent analyst agents (parallel,
                                no inter-agent communication). Each produces per-claim
                                confidence scores.
                                Phase 2: Aggregator selects best-supported claims
                                (claim-level SELECTION, NOT synthesis/blending).
                                Then: WWHTB for low-confidence, gap detection,
                                confidence map building, HITL Gate 2.
    analyst.py               -- Independent analyst agent. Each analyst applies a
                                different methodology (ACH, Quantitative, Adversarial,
                                Historical Analogy). Uses LLMCallable. Produces
                                per-claim confidence scores and source counts.
    aggregator.py            -- Claim-level SELECTION aggregator. For each disputed
                                finding, a judge LLM selects the best-supported claim
                                (not blend/synthesize). Post-selection consistency check.
                                Uses LLMCallable (flagship tier).
    wwhtb.py                 -- "What Would You Have to Believe?" step. For claims
                                with confidence < 0.6, elicit structured assumptions.
                                Uses LLMCallable.
    confidence_builder.py    -- Builds ConfidenceMap from aggregated claims. Maps each
                                claim to the appropriate tier based on methodological
                                agreement percentage. Populates all five tiers.
    gap_detector.py          -- Identifies research gaps from absence reports and
                                low-confidence claims. Produces gap_report.

tests/unit/deliberation/
    __init__.py
    test_deliberation.py     -- End-to-end orchestrator test with mock LLM
    test_analyst.py          -- Test individual analyst producing scored claims
    test_aggregator.py       -- Test selection (not blending): given 2 competing claims
                                on the same finding, verify the judge picks one
    test_wwhtb.py            -- Test WWHTB fires for claims below 0.6 confidence
    test_confidence_builder.py -- Test claim routing to correct tiers
    test_gap_detector.py     -- Test gap identification from absence reports

CRITICAL PATTERNS:

1. LLMCallable for ALL LLM calls (same pattern as evaluator):
   ```python
   from keystone.evaluator.retry import LLMCallable, retry_llm_call
   class Analyst:
       def __init__(self, llm: LLMCallable, analyst_type: str): ...
   ```

2. Async generator for events:
   ```python
   async def deliberate(self, manifest, findings, engagement_id, client_id):
       yield AnalystSpawned(...)
       # ... run analysts in parallel ...
       yield IndependentAnalysisComplete(...)
       # ... aggregate ...
       yield AggregationComplete(...)
       # ... build confidence map ...
       yield ConfidenceMapProduced(...)
   ```

3. HITL Gate 2 integration:
   ```python
   from keystone.hitl.gate import create_and_wait_for_gate
   # After confidence map is built:
   gate_response = await create_and_wait_for_gate(
       db_session_factory=self._db_session_factory,
       engagement_id=engagement_id,
       client_id=client_id,
       gate_type="post_deliberation",
       artifacts=[confidence_map.model_dump()],
   )
   ```
   In tests, pass db_session_factory=None and the gate should be skipped
   (check how spec_engine.py handles this -- it conditionally skips the gate
   when db_session_factory is None).

4. Claim-level SELECTION, not synthesis:
   The aggregator does NOT blend competing claims into a new claim. It SELECTS
   the best-supported original claim for each disputed finding. The judge LLM
   evaluates which claim has stronger evidence and picks it. This is a critical
   design choice (81% win rate vs 51.2% for synthesis per the spec).

5. Confidence map construction:
   Use the ConfidenceMap model from models/confidence.py directly. Route claims
   based on methodological agreement percentage:
   - >80% agreement -> HighConfidenceClaim (with curmudgeon_challenge)
   - 60-80% -> ModerateConfidenceClaim (with sensitivity analysis)
   - 50-60% -> WeakConfidenceClaim (with DiscoUQ features if available)
   - <50% -> ContestedClaim (with steelmanned opposing view)
   - Insufficient evidence -> InsufficientEvidenceClaim

SCOPE -- BUILD NOW:
- All 7 module files listed above
- All 6 test files listed above
- HITL Gate 2 integration (conditional on db_session_factory)
- Mock LLM throughout (analysts, aggregator, WWHTB all use mock)

SCOPE -- DO NOT BUILD:
- Cross-provider diversity ("at least one analyst on different model family") --
  single provider for Phase 1
- Real LLM integration
- Curmudgeon challenge quality verification (the challenge text is LLM-generated
  in mock; quality verification needs real LLM)

NOTE ON ANALYST TYPES: The spec defines ACH, Quantitative, Adversarial, Historical
Analogy as analyst types. These map to DeliberationAnalystType in models/agents.py.
Also add SCENARIO_PLANNING from that enum. But like research agents, these should
be methodology templates, not hardcoded behavior.

NOTE ON MODEL TIERS: ModelTier values are FLAGSHIP/STANDARD/FAST/LIGHT.
Analysts use STANDARD. Aggregator uses FLAGSHIP.

DO NOT:
- Modify any existing files except what's needed for __init__.py exports
- Touch any files in evaluator/, specification/, citation/, gateway/, research/
- Add dependencies to pyproject.toml
- Update SESSION-LOG.md or CURRENT-STATE.md
- Build real LLM integration

When complete: run pytest on your new tests AND the full suite. Report counts.
```

---

## Post-Wave 2 Merge

After both sessions complete, a merge session should:
1. Run the full test suite (501 + new Component #7 + new Component #9 tests)
2. Verify no file conflicts
3. Verify both components satisfy their Protocol contracts (isinstance checks)
4. Update SESSION-LOG.md, CURRENT-STATE.md, docs/ARCHITECTURE.md
5. Determine: are we ready for Component #11 (end-to-end pipeline test)?

---

## Wave 3 Preview (after OAuth configured)

**Session 6: LLM Client Factory + Integration Testing**
- Create src/keystone/llm_client.py (OAuth TokenManager, OpenAI client factory)
- Create src/keystone/llm_settings.py (per-layer reasoning_effort from OPENAI-SWITCHOVER-PLAN.md)
- Wire real LLM calls into Components #5, #7, #9, #6
- First real engagement: "Estimate TAM for L4+ AV sensor market"
- Validate against acceptance criteria with live model output

**Session 7: Component #11 -- End-to-End Pipeline Test**
- Wire L0 -> L1 -> CitProc -> L1.5 -> L4 -> Markdown
- Minimal: 3 tasks, 2 agents, 1 round, Layers 1-2 eval only
- Verify data flows correctly across all handoff boundaries
