# Architecture Preservation Audit

Date: 2026-05-24

## Bottom Line

Keep the DPVI architecture and the issue-tree/specification engine as the core product. Replace the Claude-first runtime and redesign the research acquisition surface around durable artifacts, subscription-backed provider adapters, and staged evaluation. Adapt the existing components where their contracts are sound but their execution shape burns context or assumes a business-only problem.

The current system failed because the runtime path asks too many large LLM calls to process too much raw material at once, depends on `claude -p` for both research and synthesis, and lacks stable artifact boundaries for browser Deep Research. The failure is architectural in the execution path, not a reason to discard the higher-level design.

## Preserve

| Component | Verdict | Why it survives |
| --- | --- | --- |
| DPVI pattern | KEEP | Decompose, parallelize, verify, iterate maps directly to consultant research workflows. It is still the right mental model for broad research. |
| L0 specification engine | ADAPT | Specification quality remains the highest-leverage control. The implementation needs dynamic lenses and richer task briefs, not removal. |
| Issue tree as operator artifact | KEEP | The issue tree is valuable by itself and matches the user's July 27 target. It should become a human-reviewable product surface. |
| Agent isolation | KEEP | Isolation prevents cross-contamination across branches and hypotheses. Aggregation should happen through structured evidence artifacts. |
| Citation Processor | KEEP | This is one of the strongest live pieces. It already validates URLs and produces a manifest on real data. |
| HITL gates | ADAPT | The design matches the owner vision. It needs an ergonomic operator workflow and pause/resume semantics. |
| Checkpoint/resume concept | ADAPT | Long-running subscription/browser work requires durable checkpoints. The concept is correct, but scripts and defaults need repair. |
| Observation library | ADAPT | The meta-layer is important for compounding quality. It needs concrete run outcomes and decision records, not only score optimization. |

## Replace

| Component | Verdict | Required replacement |
| --- | --- | --- |
| Claude-first provider doctrine | REPLACE | Make provider routing model-agnostic and subscription-first: Codex CLI for structured non-browser calls, ChatGPT/Claude web for research jobs, API only for fallback/control. |
| `claude -p` deep research transport | REPLACE | Use a research acquisition adapter that produces a standard `ResearchReportArtifact`, whether the report came from ChatGPT web, Claude web, manual upload, Codex, API, SEC retrieval, or a future tool. |
| Fixed financial/operational/market lenses | REPLACE | Build a dynamic lens selector that chooses decomposition lenses from problem characteristics and user context. |
| All-claims-to-all-analysts deliberation | REPLACE | Use claim clustering, selection, and staged analyst passes. Analysts should process issue bundles, contested claims, or synthesis briefs, not 155 flat claims at once. |
| Mocked shallow tool path | REPLACE | Wire real deterministic source acquisition for public company and industry workflows. SEC/EDGAR should be deterministic first. |

## Adapt

| Component | Current value | Needed adaptation |
| --- | --- | --- |
| Task generator | Produces structured tasks with acceptance criteria. | Generate 500-900 word research briefs for deep research branches, with required sources, disconfirming evidence, and expected artifact shape. |
| L1 research agents | Executes parallel branch research. | Separate branch planning from provider execution. L1 should manage research jobs and ingest artifacts, not force all research through one agent call. |
| L1.5 deliberation | Encodes useful methodologies. | Select analyst methodologies by domain and issue type; feed them synthesis briefs and evidence slices. |
| L2 sprint contracts | Good quality-control idea. | Generate sprint contracts only after evidence grouping. Avoid one expensive contract call for every low-value task. |
| Evaluator | Strong conceptual quality gate. | Stage it: deterministic checks first, cheap rubric pass second, frontier judges only for contested/high-impact outputs. |
| Server/HITL UI | Useful skeleton. | Make the operator approve issue tree, research plan, provider assignment, and rerun decisions. |
| Retrieval stack | Ambitious and partially built. | Treat as evidence-store infrastructure. First vertical slice should use deterministic SEC/Web artifacts before full hybrid retrieval. |

## Highest-Risk Execution Mismatches

| Risk | Evidence | Fix direction |
| --- | --- | --- |
| Provider fragility | `llm_client.py` defaults to `claude_cli`; deep research callable is hardwired to Claude. Anthropic now separates `claude -p` from subscription usage after June 15, 2026. | ProviderAdapter interface with Codex CLI, ChatGPT web, Claude web, API fallback, and manual upload adapters. |
| Context bloat | Trivial `codex exec` probe loaded 28.5K input tokens. L1.5 timed out on 155 claims. | Keep harness calls narrow. Use artifacts, manifests, and claim bundles rather than whole-repo and whole-run context. |
| Business-only decomposition | `_LENSES = ["financial", "operational", "market"]`. | Dynamic lens selector based on problem form: causal, market, technical, legal, scientific, financial, operational, regulatory, comparative, temporal, etc. |
| Research mode bypasses tool governance | Deep research bypasses MCPGateway and uses provider-native web tools directly. | Capture provider-native research output as an artifact, then run local citation/provenance validation after ingestion. |
| Retry paths duplicate cost | Deep research can time out then fall back to shallow mode; shallow mode may produce zero claims due stubs. | A failed deep job should checkpoint as failed provider job and requeue provider/branch, not start a doomed fallback. |
| Resume drift | `resume_from_l1.py` awaited an async generator. | Make checkpoint/resume use the same orchestrator contracts as live execution. Add contract tests. |

## How The Five-Stage Direction Should Be Interpreted

The earlier five-stage architecture direction should be treated as a refactor sequence, not as a replacement doctrine. The system should still look like Keystone's original DPVI design, but the execution boundaries need to move:

| Stage | Purpose | Relationship to current architecture |
| --- | --- | --- |
| Specification | Turn messy request into decision context, issue tree, research plan, and clarification questions. | Preserves L0 and makes it more dynamic. |
| Research acquisition | Execute branch research through provider adapters and deterministic source tools. | Replaces `claude -p` deep mode as the only serious research path. |
| Ingestion/provenance | Convert reports, filings, PDFs, browser exports, and source lists into normalized evidence. | Preserves and extends CitationProcessor/retrieval work. |
| Synthesis/deliberation | Build narrative thesis, contested claims, and gap plan from evidence bundles. | Adapts L1.5 and adds the missing narrative synthesis layer. |
| Evaluation/deliverable | Verify, score, and render briefs, decks, workbooks, and issue-tree outputs. | Preserves evaluator concepts but stages them to control cost. |

## Preserve-And-Rebuild Thesis

The valuable part of the project is the control system: issue trees, handoff contracts, citation invariants, HITL gates, evaluator doctrine, and observation feedback. The broken part is the assumption that a coding CLI can directly act as the research engine for every branch while also carrying the whole pipeline context through repeated long-running calls.

The next version should make research reports first-class artifacts. Once a ChatGPT or Claude Deep Research report exists, Keystone should ingest it, cite it, score it, gap-check it, and decide the next research wave. That matches the workflow that originally created the project while preserving the architecture that makes it more than a pile of ad hoc reports.

## Evidence References

- `src/keystone/models/config.py:482` defaults provider to `claude_cli`.
- `src/keystone/llm_client.py:463` builds deep research through Claude CLI.
- `src/keystone/specification/decomposer.py:56` hardcodes business lenses.
- `src/keystone/gateway/simple_client.py:66` returns stubs for non-Exa/Brave tools.
- `src/keystone/research/research_agent.py:266` describes deep mode as a single `claude -p` call.
- `src/keystone/research/research_agent.py:324` estimates tokens from prompt/response length, missing hidden provider work.
- `src/keystone/evaluator/layer3_rubric.py:124` defines up to 11 rubric calls per judge.
- `output/pipeline_run_20260427_214406.log:1470` shows the real run fatal failure.
- `docs/deliverable/KNOWN-ISSUES.md` already identifies the main open issues and aligns with this audit.

