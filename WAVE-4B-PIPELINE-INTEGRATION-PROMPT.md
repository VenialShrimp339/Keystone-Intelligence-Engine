# Wave 4b: First Real End-to-End Pipeline Run

*Generated: 2026-04-07 | Planning Session 16*

**Context:** All 10 components individually pressure-tested with real GPT-5.4 calls
(Wave 4a). 108 integration tests + 722 unit tests passing. 4 bugs found and fixed.
SimpleMCPClient provides real Exa/Brave search. LLM Client Factory connects to
OpenAI via Codex OAuth. Pipeline orchestrator wires all stages. This session runs
the full chain for the first time.

**This session produces the first real deliverable Jack will read.** Quality
judgment is Jack's job, not yours. Your job is: make it run, capture everything,
measure everything, and diagnose any mechanical failures.

---

## Session 13: Full Pipeline Integration -- Real LLM End-to-End

```
You are running the Keystone Intelligence Engine's full pipeline end-to-end for the
FIRST TIME with real GPT-5.4 calls and real search API calls. Every component has
been individually validated. Your job is to wire them together and run a complete
research engagement.

Read CLAUDE.md (auto-loaded), then read these files IN ORDER:

1. src/keystone/pipeline/orchestrator.py -- Read the ENTIRE file. Understand
   Pipeline.__init__, run_with_events, _build_assignments, _finding_to_text,
   _build_sprint_contract. This is the code you're exercising.
2. src/keystone/llm_client.py -- Read the ENTIRE file. Understand CodexTokenProvider,
   create_openai_client, _call_codex_oauth, get_llm_for_tier, create_llm_factory.
   This is how LLM calls actually work.
3. src/keystone/llm_settings.py -- reasoning_effort per tier.
4. src/keystone/gateway/simple_client.py -- Real Exa/Brave search adapter.
   This replaces MockMCPClient for real tool calls.
5. src/keystone/gateway/mcp_gateway.py -- Read MCPGateway.__init__ and the
   execute() method. Understand how to construct a gateway with SimpleMCPClient.
6. tests/e2e/test_mock_pipeline.py -- Read how the mock e2e test sets up the
   pipeline. Your setup is similar but with real LLM + real search.

Also skim (first 30 lines each):
7. src/keystone/specification/spec_engine.py -- SpecificationEngine.__init__
8. src/keystone/research/agent_pool.py -- AgentPool.__init__ + execute_all
9. src/keystone/citation/processor.py -- CitationProcessor (no LLM)
10. src/keystone/deliberation/deliberation.py -- Deliberation.__init__
11. src/keystone/evaluator/evaluator.py -- Evaluator.__init__

BEFORE WRITING ANY CODE, use a todo list to plan your work.

=== YOUR TASK ===

Create a single integration test script that runs the full pipeline and saves
all artifacts for Jack to review:

File: tests/integration/test_pipeline_real.py

SETUP:

The pipeline needs:
a) An LLMFactory that creates real LLM callables via Codex OAuth
b) An MCPGateway configured with SimpleMCPClient for real search
c) No db_session_factory (skip HITL gates -- Jack isn't at the terminal to approve)

```python
# Setup pattern (adapt as needed):
from dotenv import load_dotenv
load_dotenv()

from keystone.llm_client import create_llm_factory
from keystone.models.config import AppConfig
from keystone.gateway.mcp_gateway import MCPGateway
from keystone.gateway.simple_client import SimpleMCPClient
from keystone.gateway.tool_registry import ToolRegistry
from keystone.gateway.auth import ToolAuthorizer
from keystone.gateway.rate_limiter import InMemoryRateLimiter
from keystone.gateway.audit_log import AuditLogger

config = AppConfig()
llm_factory = create_llm_factory(config)

# Real search client
search_client = SimpleMCPClient()
registry = ToolRegistry()
registry.register_all_from_servers()  # or however servers.py populates it
authorizer = ToolAuthorizer(registry)
rate_limiter = InMemoryRateLimiter()
audit_logger = AuditLogger()

gateway = MCPGateway(
    client=search_client,
    registry=registry,
    authorizer=authorizer,
    rate_limiter=rate_limiter,
    audit_logger=audit_logger,
)

pipeline = Pipeline(llm_factory=llm_factory, gateway=gateway)
```

Read the MCPGateway constructor and ToolRegistry to understand the exact wiring.
You may need to adjust the setup based on what the constructor actually requires.
Read simple_client.py to understand how it handles tools that don't have real backends
(edgar, fred, etc. return stubs).

THE TEST ENGAGEMENT:

Question: "Estimate the total addressable market for Level 4+ autonomous vehicle
sensors in North America through 2030, including LiDAR, radar, and camera modules.
Segment by sensor type and identify the top 5 competitive players."

Client ID: "keystone_test"
Client context: "Investment committee evaluating sensor startup acquisition targets.
Need defensible market size estimates with source-level citations. Particular interest
in whether LiDAR costs are declining fast enough to enable mass-market L4 deployment."

WHAT TO CAPTURE:

1. **Timing**: wall-clock time for each pipeline stage (L0, L1, CitProc, L1.5, L4, Render)
2. **Token count**: total tokens consumed (from PipelineResult.total_tokens + any you can measure)
3. **LLM call count**: how many GPT-5.4 calls were made total
4. **Search call count**: how many Exa/Brave calls were made
5. **Event count**: by layer (how many L0 events, L1 events, etc.)
6. **Agent count**: how many research agents ran, how many succeeded
7. **Citation count**: total in manifest, live URLs, dead URLs
8. **Confidence map distribution**: claims per tier
9. **Evaluation scores**: per-task scores and overall
10. **Any errors, retries, or fallbacks that occurred**

WHAT TO SAVE (all to output/first_real_run/):

Create the output directory and save:
a) output/first_real_run/deliverable.md -- the full markdown output
b) output/first_real_run/engagement_spec.json -- the EngagementSpec
c) output/first_real_run/findings.json -- all StructuredFindings
d) output/first_real_run/citation_manifest.json -- the CitationManifest
e) output/first_real_run/confidence_map.json -- the ConfidenceMap
f) output/first_real_run/evaluation_results.json -- all EvaluationResults
g) output/first_real_run/run_metrics.json -- timing, tokens, counts, errors
h) output/first_real_run/event_log.json -- all pipeline events (serialized)

Use Pydantic's .model_dump_json(indent=2) for all model serialization.

THE TEST FUNCTION:

```python
@pytest.mark.integration
@pytest.mark.timeout(600)  # 10 minute timeout for full pipeline
async def test_full_pipeline_real():
    """Run the complete pipeline with real LLM and real search.

    This is a DIAGNOSTIC run. We capture everything and save artifacts
    for human review. We do NOT judge output quality.
    """
    # Setup (as above)
    # ...

    # Run
    start = time.time()
    result = await pipeline.run(question, client_id, client_context)
    elapsed = time.time() - start

    # Save all artifacts
    # ...

    # Structural assertions ONLY (not quality):
    assert result.engagement_id  # non-empty
    assert result.findings  # at least one finding
    assert result.manifest.citations  # at least one citation
    assert result.confidence_map.total_claims > 0
    assert result.markdown_output  # non-empty
    assert "## Executive Summary" in result.markdown_output
    assert "## Sources" in result.markdown_output

    # Print summary for the session log
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE in {elapsed:.1f}s")
    print(f"Tasks: {len(result.spec.task_decomposition.tasks)}")
    print(f"Findings: {len(result.findings)}")
    print(f"Citations: {len(result.manifest.citations)}")
    print(f"Confidence map: {result.confidence_map.total_claims} claims "
          f"across {result.confidence_map.tiers_populated} tiers")
    print(f"Evaluations: {len(result.evaluation_results)}")
    print(f"Markdown: {len(result.markdown_output)} chars")
    print(f"Tokens: {result.total_tokens}")
    print(f"Events: {result.total_events}")
    print(f"{'='*60}\n")

    # Print the first 100 lines of the markdown for immediate inspection
    lines = result.markdown_output.split('\n')
    print("=== DELIVERABLE PREVIEW (first 100 lines) ===")
    print('\n'.join(lines[:100]))
    if len(lines) > 100:
        print(f"\n... [{len(lines) - 100} more lines in output/first_real_run/deliverable.md]")
```

HANDLING FAILURES:

This is a real pipeline with real API calls. Things WILL go wrong. When they do:

1. **LLM call fails (timeout, 429, 500)**: The retry logic in evaluator/retry.py
   should handle this. If it dead-letters after 3 retries, log it and continue.
   Don't crash the whole pipeline for one failed call.

2. **JSON parsing fails**: Research agents now have _extract_json_text with fence
   stripping. If parsing still fails, log the raw output and the error.

3. **Search returns no results**: SimpleMCPClient handles this. The agent should
   continue with what it has.

4. **Quota exhaustion**: If you hit the Codex OAuth quota limit mid-run, the
   pipeline will get 429 errors. Log it clearly and document where it stopped.

5. **Pipeline stage produces no output**: If L0 produces no tasks, or L1
   produces no findings, the pipeline should handle this gracefully (empty
   results, not crash).

For any failure that requires a CODE FIX to proceed:
- Fix it within the appropriate component's scope
- Re-run
- Document what you fixed in your session report

THE CRITICAL CONSTRAINT:

You are authorized to fix bugs that prevent the pipeline from running. You are
NOT authorized to "improve" the output quality. If the markdown deliverable is
mediocre, that's expected -- quality tuning comes from Jack's human review, not
from this session.

Fixes you CAN make:
- JSON parsing errors
- Type mismatches between components
- Missing error handling that causes crashes
- Constructor wiring issues (wrong args to a component)

Fixes you CANNOT make:
- Prompt content changes to improve output quality
- Evaluation rubric adjustments
- Markdown renderer formatting improvements
- Adding features that don't exist yet

AFTER THE RUN:

1. Verify all 8 artifact files were saved to output/first_real_run/
2. Run the full non-integration test suite (pytest tests/ --ignore=tests/integration/)
   to verify you didn't break anything
3. Write a brief summary at the end of your session:
   - Did the pipeline complete? If not, where did it fail?
   - How many LLM calls, search calls, tokens consumed?
   - How long did the full run take?
   - What bugs did you fix (if any)?
   - What are the biggest mechanical issues for the next run?

DO NOT:
- Modify prompt files (evaluator/prompts/, specification/prompts/)
- Change evaluation rubric weights or thresholds
- Add new components or pipeline stages
- Judge output quality
- Update SESSION-LOG.md or CURRENT-STATE.md (planning session handles this)

Mark the test @pytest.mark.integration. Use a 10-minute timeout.
When complete, report the full summary and confirm artifact files exist.
```
