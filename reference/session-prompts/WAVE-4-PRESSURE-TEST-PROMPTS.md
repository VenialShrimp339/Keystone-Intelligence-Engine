# Wave 4a: Component Pressure Tests (Parallel)

*Generated: 2026-04-07 | Planning Session 16*

**Context:** All plumbing is built (10 components, 725 tests, pipeline orchestrator, LLM client).
Smoke test confirmed Codex OAuth works (gpt-5.4 and gpt-5.4-mini both responding).
These sessions make REAL API calls. They are DIAGNOSTIC -- finding what breaks,
not proving things work.

**Quota note:** Combined ~100-130 LLM calls across all 4 sessions. Should fit in a
single 5-hour window. If you hit quota issues, prioritize Session 9 (Spec Engine)
as it's the first pipeline stage and blocks everything downstream.

**Each session's mandate:**
- Follow the testing plan below as your BASELINE
- You are explicitly authorized and encouraged to ADD tests beyond what's listed
- Think deeper about edge cases, adversarial inputs, and failure modes
- Use a todo list to track what you've tested
- When something fails: diagnose, fix within your component scope, re-test
- If a fix requires shared files (llm_client.py, contracts.py, events.py),
  document the needed change but DO NOT apply it
- Report: what worked, what broke, what was fixed, what needs fixing elsewhere,
  token consumption per operation

---

## Session 9: L0 Specification Engine -- Real LLM Pressure Test

```
You are pressure-testing the Specification Engine (L0) with REAL GPT-5.4 calls
for the Keystone Intelligence Engine. This is the first time this component runs
with a real LLM instead of mocks. Your goal is to find everything that breaks.

Read CLAUDE.md (auto-loaded), then read:
1. src/keystone/specification/spec_engine.py -- the 10-step pipeline you're testing
2. src/keystone/llm_client.py -- how LLM calls actually work (read the full file,
   especially _call_codex_oauth and the streaming delta collection)
3. src/keystone/llm_settings.py -- reasoning effort mapping
4. src/keystone/specification/prompts/ -- read ALL 9 prompt files. These are what
   GPT-5.4 will receive. Understand what JSON output each expects.
5. src/keystone/specification/_prompts.py -- read the prompt loading and JSON
   extraction logic. This is where parsing failures will surface.
6. src/keystone/models/research.py -- EngagementSpec, ResearchSpec (output types)
7. src/keystone/models/tasks.py -- ResearchTask, TaskDecomposition (output types)

YOUR TASK: Write and run a comprehensive integration test suite that calls the
REAL Specification Engine with REAL GPT-5.4 via Codex OAuth.

Create: tests/integration/test_spec_engine_live.py

BASELINE TESTS (do all of these, then add more):

1. BASIC FUNCTIONALITY: Feed "Estimate the total addressable market for Level 4+
   autonomous vehicle sensors in North America through 2030" to the Spec Engine.
   Verify:
   - EngagementSpec is produced (not None, no crash)
   - ResearchSpec has all required fields populated
   - TaskDecomposition has 15-50 tasks
   - DAG validation passes (no cycles, no dangling refs)
   - Every task has 3-5 assigned tools
   - Every task has anti-confirmatory framing
   - Every task has acceptance criteria
   - Issue tree is present and has 2+ levels
   - Events were emitted: SpecificationGenerated, TasksDecomposed

2. ENGAGEMENT TYPE COVERAGE: Test 3 more question types. For each, verify the
   engagement classifier routes to the correct type:
   - Sizing: "What is the market size for electric vehicle charging infrastructure
     in the US, segmented by Level 2 vs DC fast charging?"
   - Diagnostic: "Why has employee turnover at mid-size SaaS companies increased
     30% since 2024, and what interventions are most cost-effective?"
   - Strategic: "Should a regional auto body shop chain expand into the Dallas-Fort
     Worth metropolitan area given current competitive dynamics?"

3. JSON PARSING ROBUSTNESS: For each LLM call, capture the raw output and verify:
   - Valid JSON was produced (json.loads succeeds)
   - All expected keys are present
   - No truncated output (closing braces present)
   - Log any cases where the XML structural reinforcement tags appear in the
     output (they should be in the prompt only, not echoed back)

4. EDGE CASES:
   - Very short question: "Analyze Tesla"
   - Very long question: 500+ word question with detailed context
   - Ambiguous question: "What should we do about the market?"
   - Non-English terms: "Analyze the Mittelstand companies' approach to Industry 4.0"

5. CONSISTENCY: Run the basic AV sensor question TWICE. Compare:
   - Same engagement type classified?
   - Similar task count?
   - Same DAG structure? (exact match not expected, but similar depth/breadth)

6. TOKEN MEASUREMENT: For each test, measure and log:
   - Total tokens consumed
   - Time elapsed
   - Number of LLM calls made

7. PROMPT-MODEL FIT: For each of the 9 specification prompts, check:
   - Did the model produce the expected output format?
   - Did the XML tags (<analytical_contract>, <completeness_check>) appear to
     help or did the model ignore/echo them?
   - Were all fields in the completeness checklist actually produced?

AFTER running all baseline tests, STOP AND THINK: what additional tests would
expose weaknesses you haven't covered? Add at least 3 more tests based on your
observations. Common failure modes to probe:
- Models producing markdown-wrapped JSON (```json...```) that needs extraction
- Models adding commentary after the JSON
- Models splitting a single JSON object across multiple response chunks
- Task descriptions that are too generic ("research the market" without specifics)
- Duplicate tasks (same investigation phrased differently)

WHEN SOMETHING BREAKS:
- Capture the raw LLM output that caused the failure
- Diagnose whether it's a prompt issue, parsing issue, or model behavior issue
- If it's a prompt issue in specification/prompts/*.md: fix it and re-test
- If it's a parsing issue in _prompts.py: fix it and re-test
- If it's a model behavior issue (GPT-5.4 genuinely can't do X): document it

DO NOT modify files outside src/keystone/specification/ and tests/integration/.

Mark all tests @pytest.mark.integration. Use 60-second timeouts per LLM call.
Report total token consumption at the end.
```

---

## Session 10: L1 Research Agents + MCP Gateway -- Real LLM + Real Search

```
You are pressure-testing the Research Agent pipeline (L1) and MCP Gateway with
REAL GPT-5.4 calls AND REAL search tool calls (Exa, Brave) for the Keystone
Intelligence Engine. This is the first time agents do actual research.

Read CLAUDE.md (auto-loaded), then read:
1. src/keystone/research/research_agent.py -- the agent executor
2. src/keystone/research/agent_pool.py -- parallel agent manager
3. src/keystone/research/isolation.py -- filesystem isolation
4. src/keystone/research/finding_writer.py -- StructuredFinding builder
5. src/keystone/research/error_recovery.py -- retry + fallback
6. src/keystone/gateway/mcp_gateway.py -- gateway with MockMCPClient
7. src/keystone/gateway/servers.py -- 7 MCP server configs (Exa, Brave, etc.)
8. src/keystone/llm_client.py -- how LLM calls work
9. src/keystone/tool_names.py -- tool name constants
10. .env -- check that EXA_API_KEY and BRAVE_SEARCH_API_KEY are set

IMPORTANT CONTEXT: The MCP Gateway currently uses MockMCPClient. For this test,
you need to either:
a) Create a SimpleMCPClient that makes REAL HTTP calls to Exa/Brave APIs
   (not full MCP protocol, just direct REST calls), OR
b) Use PydanticAI's built-in web_search tool as a quick alternative

Option (a) is preferred. Exa's API is a simple POST to api.exa.ai/search with
the API key in the header. Brave Search is a GET to api.search.brave.com/res/v1/web/search.
Create a minimal client that implements the MCPClient Protocol from mcp_gateway.py.

Create: tests/integration/test_research_agent_live.py
Create: src/keystone/gateway/simple_client.py (if using option a)

BASELINE TESTS:

1. SINGLE AGENT, SINGLE ROUND: Create one Quantitative research agent.
   Assign it: "Estimate the total addressable market for L4+ AV sensors."
   With tools: exa_search, brave_search, edgar_filings (mock edgar, real search)
   Verify:
   - Agent calls at least one search tool
   - Tool results contain actual web content (not empty)
   - Agent synthesizes findings via LLM
   - StructuredFinding is produced with:
     * Claims with non-empty citations
     * Citation URLs that actually resolve (HTTP HEAD check)
     * Per-claim confidence scores in 0-1 range
     * Non-empty absence report
   - Events emitted: ResearchStarted, SourceFound, FindingSynthesized, ResearchComplete

2. TOOL CALL VERIFICATION:
   - Exa search returns results for "autonomous vehicle sensor market size"
   - Brave search returns results for same query
   - Verify gateway auth check passes (agent is authorized for these tools)
   - Verify audit log captures the tool calls

3. FILESYSTEM ISOLATION:
   - Spawn 2 agents in parallel with different working directories
   - Verify agent A cannot read agent B's files (use isolation.verify_isolation)
   - Verify each agent's working directory contains its artifacts

4. ITERATIVE LOOP (if quota allows):
   - Run a single agent for 2 rounds
   - Verify round 2 context differs from round 1
   - Verify stopping criteria are checked after each round

5. ERROR RECOVERY:
   - Configure one tool to return an error (invalid API key or wrong endpoint)
   - Verify retry logic fires
   - Verify the agent continues with other tools after the failed one

6. CITATION REALITY CHECK: For every citation in the output:
   - HTTP HEAD the URL. Is it live?
   - Does the title roughly match the URL content?
   - Log: total citations, live URLs, dead URLs, fabricated-looking titles

AFTER baseline tests, ADD YOUR OWN TESTS. Probe:
- What happens when search returns zero results?
- What happens when the LLM hallucinates a tool name not in its assigned set?
- Are the search queries the agent generates actually relevant?
- Does the agent's synthesis accurately reflect the search results?

WHEN SOMETHING BREAKS: fix within src/keystone/research/ or src/keystone/gateway/.
If search APIs are down or rate-limited, document it and test what you can.

DO NOT modify files outside research/, gateway/, and tests/integration/.

Mark all tests @pytest.mark.integration. Report token consumption and search API calls.
```

---

## Session 11: L4 Evaluator -- Real LLM Scoring Pressure Test

```
You are pressure-testing the Evaluator (L4) with REAL GPT-5.4 calls for the
Keystone Intelligence Engine. The Evaluator is the most important component --
it determines output quality. You need to verify it produces structurally valid
scores and catches known failure types.

Read CLAUDE.md (auto-loaded), then read:
1. src/keystone/evaluator/evaluator.py -- the 3-layer orchestrator
2. src/keystone/evaluator/layer1_deterministic.py -- FActScore, numerical checks
3. src/keystone/evaluator/layer2_citation_gate.py -- DOI verification, fabrication
4. src/keystone/evaluator/layer3_rubric.py -- 10-dimension scoring, _parse_score_json
5. src/keystone/evaluator/three_pass.py -- three-pass evaluation flow
6. src/keystone/evaluator/rubric_config.py -- weights, profiles, tier 1/2 split
7. src/keystone/evaluator/prompts/ -- read ALL 14 prompt files
8. src/keystone/llm_client.py -- how LLM calls work
9. src/keystone/models/evaluation.py -- EvaluationResult, SprintContract, DimensionScore

YOUR TASK: Write and run comprehensive integration tests that call the REAL
Evaluator with REAL GPT-5.4.

Create: tests/integration/test_evaluator_live.py

You need to craft test inputs at different quality levels. The evaluator scores
text against a SprintContract. Create:

GOOD INPUT: A well-structured research finding with real citations, specific data,
balanced evidence, and clear conclusions. Should score 65-85 on most dimensions.

BAD INPUT: A finding with vague claims, no citations, generic statements,
internally contradictory numbers. Should score below 40 on most dimensions.

FABRICATED INPUT: A finding with invented citations (fake DOIs, non-existent URLs),
made-up statistics, and confident but unsupported claims. Layer 2 should REJECT this.

BASELINE TESTS:

1. GOOD INPUT SCORING:
   - Feed well-crafted input through all 3 layers
   - Verify Layer 1 passes (no numerical inconsistencies in your good input)
   - Verify Layer 2 passes (real citations in your good input)
   - Verify Layer 3 produces scores for all 10 dimensions
   - Verify geometric mean is calculated correctly (recompute it yourself)
   - Verify gestalt overlay is within [-10, +10]
   - Verify final score is in a reasonable range (50-90)

2. BAD INPUT SCORING:
   - Feed bad input through
   - Verify scores are meaningfully LOWER than the good input
   - Verify Tier 1 dimensions (intent_alignment, intellectual_honesty,
     completeness, narrative_coherence) have floor gates that trigger
   - Verify feedback is specific (not generic "needs improvement")

3. FABRICATED CITATION REJECTION:
   - Feed input with fake DOIs (doi.org/10.fake/xxx)
   - Verify Layer 2 citation gate returns gate_passed=False
   - Verify the pipeline short-circuits (no Layer 3 scoring after rejection)

4. JSON PARSING ROBUSTNESS: For each of the 10 dimension prompts:
   - Capture raw LLM output
   - Verify _parse_score_json successfully extracts the JSON
   - Check that "score", "feedback", "sub_criteria_notes" are present
   - Log any cases where parsing falls back to default values

5. SCORE CONSISTENCY: Run the GOOD input through the evaluator TWICE.
   - Compare dimension scores: are they within +/- 15 points of each other?
   - Compare final scores: within +/- 10?
   - If variance is high, log which dimensions are most inconsistent

6. TIER 1 / TIER 2 GATING:
   - Craft input that should FAIL Tier 1 (e.g., completely off-topic)
   - Verify Layer 3 returns early without scoring Tier 2 dimensions
   - Verify the EvaluationResult reflects the early termination

7. EVALUATION PROFILE VARIATION:
   - Test with EvaluationProfile.ESTIMATIVE on estimative content
   - Verify weights shift (calibrated_confidence should be weighted higher)
   - Compare scores to DEFAULT profile on same input

AFTER baseline tests, ADD YOUR OWN. Key areas to probe:
- Does the anti-slop detection in prompts actually affect scores?
  (Feed it trendslop: "leveraging synergies to drive holistic value creation")
- How does the evaluator handle very short output (100 words)?
- How does it handle very long output (5000 words)?
- Does the gestalt overlay consistently adjust in the right direction?
- Are the feedback strings actually actionable or just generic?

WHEN SOMETHING BREAKS: fix within src/keystone/evaluator/ and tests/integration/.
The most likely failure is _parse_score_json failing on unexpected LLM output format.
If this happens, improve the parser's robustness and the prompt's output format section.

DO NOT modify files outside evaluator/ and tests/integration/.

Mark all tests @pytest.mark.integration. Report token consumption. Report score
distributions (mean, min, max per dimension across all test inputs).
```

---

## Session 12: L1.5 Deliberation + CitationProcessor -- Real LLM Pressure Test

```
You are pressure-testing the Deliberation module (L1.5) and CitationProcessor with
REAL GPT-5.4 calls for the Keystone Intelligence Engine. Deliberation is where
independent analysts assess findings and an aggregator selects the best-supported
claims. CitationProcessor is deterministic but needs testing with realistic data.

Read CLAUDE.md (auto-loaded), then read:
1. src/keystone/deliberation/deliberation.py -- two-phase orchestrator
2. src/keystone/deliberation/analyst.py -- independent analyst agents
3. src/keystone/deliberation/aggregator.py -- claim-level selection
4. src/keystone/deliberation/wwhtb.py -- "What Would You Have to Believe?"
5. src/keystone/deliberation/confidence_builder.py -- five-tier routing
6. src/keystone/deliberation/gap_detector.py -- gap identification
7. src/keystone/citation/processor.py -- CitationProcessor
8. src/keystone/models/confidence.py -- ConfidenceMap and tier models
9. src/keystone/models/citations.py -- Citation, CitationManifest, Claim
10. src/keystone/models/research.py -- StructuredFinding, FindingClaim
11. src/keystone/llm_client.py -- how LLM calls work

YOUR TASK: Write and run comprehensive integration tests.

Create: tests/integration/test_deliberation_live.py
Create: tests/integration/test_citation_processor_live.py

First, you need to craft REALISTIC test data. Build 3 StructuredFindings that
simulate what 3 research agents would produce:
- Agent 1 (Quantitative): Market size claims with specific numbers and citations
- Agent 2 (Qualitative): Industry trend claims with news/report citations
- Agent 3 (Contrarian): Counter-arguments and risk factors with citations
Make some claims overlap (corroboration), some conflict (disagreement), and
some appear only in one agent's output (unique findings). Use REAL URLs for
citations (actual SEC filings, news articles, etc. -- things that exist on the web).

CITATION PROCESSOR TESTS:

1. DEDUP WITH REAL DATA:
   - Give Agents 1 and 2 a citation to the same real URL (e.g., a SEC filing)
   - Verify dedup merges them and found_by_agents has both agent IDs

2. URL LIVENESS WITH REAL URLS:
   - Include 5+ real URLs and 2 deliberately dead URLs
   - Verify batch_check_urls correctly identifies live vs dead
   - Measure latency for URL checks

3. CORROBORATION DETECTION:
   - Two agents independently cite the same market size figure
   - Verify corroboration pair is detected

4. CONTENT HASH INTEGRITY:
   - Verify every citation in the manifest has a content_hash
   - Verify hashes are deterministic (same input -> same hash)

DELIBERATION TESTS:

5. FULL DELIBERATION WITH REAL LLM:
   - Feed the 3 crafted findings + CitationManifest to Deliberation
   - Verify all 4 analyst types run (AnalystSpawned events for each)
   - Verify each analyst produces per-claim confidence scores
   - Verify aggregator runs (AggregationComplete event)
   - Verify ConfidenceMap is produced with claims in 2+ tiers

6. CLAIM-LEVEL SELECTION VERIFICATION:
   - Create a deliberate conflict: Agent 1 says "market is $50B by 2030",
     Agent 3 says "market is $20B by 2030 (accounting for regulatory delay)"
   - Verify the aggregator SELECTS one (not averages to $35B)
   - Log which claim was selected and the reasoning

7. WWHTB THRESHOLD:
   - Ensure at least one claim has confidence below 0.6
   - Verify WWHTB fires and produces structured assumptions
   - Verify the assumptions are specific (not generic "more research needed")

8. CONFIDENCE MAP STRUCTURE:
   - Verify all 5 tiers exist in the output (even if some are empty)
   - Verify high-confidence claims have curmudgeon_challenge
   - Verify moderate claims have sensitivity analysis
   - Verify contested claims have steelmanned opposing views
   - Check that the tier routing thresholds match (>80% high, etc.)

9. JSON PARSING: Capture raw LLM output from analysts and aggregator.
   - Verify JSON extraction works
   - Log any parsing failures or fallbacks

10. GAP DETECTION:
    - Verify gaps_identified is populated based on absence reports
    - Verify the gaps are specific, not generic

AFTER baseline tests, ADD YOUR OWN. Areas to probe:
- What happens with unanimous agreement? (All analysts agree on everything)
- What happens with total disagreement? (No two analysts agree)
- Does the consistency check catch contradictory selected claims?
- How does the confidence builder handle edge case ratios (exactly 0.8, exactly 0.5)?
- Token consumption: how expensive is deliberation vs research?

WHEN SOMETHING BREAKS: fix within src/keystone/deliberation/, src/keystone/citation/,
and tests/integration/. The most likely failures are JSON parsing of analyst output
and confidence score extraction.

DO NOT modify files outside deliberation/, citation/, and tests/integration/.

Mark all tests @pytest.mark.integration. Report token consumption for each phase
(analysts, aggregator, WWHTB). Report the final ConfidenceMap tier distribution.
```

---

## Wave 4b: Full Pipeline Integration (after Wave 4a merges)

```
TODO: Written after Wave 4a results are assessed. This session wires the real
LLM client into the pipeline orchestrator and runs the first complete end-to-end
engagement. Its scope depends on what Wave 4a finds and fixes.
```
