# Architecture Decision Log

Date: 2026-05-24

## Decision 1: Preserve DPVI And Issue Trees

Verdict: KEEP  
Confidence: High

Keystone should preserve the DPVI architecture and the issue-tree/specification engine. The owner explicitly values the issue tree as a standalone product, and the current system's best real-run output came from L0: Day-1 hypothesis, MECE issue tree, and 13 research tasks. The problem is execution reliability and cost shape, not the existence of a specification layer.

Evidence:

| Source | Signal |
| --- | --- |
| `docs/deliverable/CURRENT-STATUS.md` | L0 output is described as genuinely impressive. |
| `output/pipeline_run_20260427_214406.log:13` | Specification completed and validated. |
| Owner vision, 2026-05-24 | Full issue-tree system is part of July 27 target. |

## Decision 2: Replace Claude-First Runtime

Verdict: REPLACE  
Confidence: High

The repo's provider layer must stop treating Claude CLI as the default. Anthropic's current support docs state that beginning June 15, 2026, Claude Agent SDK and `claude -p` no longer count against Claude plan usage and instead use separate Agent SDK credit. This makes the old doctrine operationally stale for the owner's subscription-first objective.

Evidence:

| Source | Signal |
| --- | --- |
| `src/keystone/models/config.py:482` | Default provider is `claude_cli`. |
| `src/keystone/llm_client.py:463` | Deep research callable is Claude CLI. |
| Anthropic support | `claude -p` is now covered by separate Agent SDK credit, not normal plan usage. |

Implementation consequence: build provider adapters and route by capability. Codex CLI should power structured non-browser calls. ChatGPT and Claude web should power hosted Deep Research jobs. API remains fallback/control and benchmark, not the default plan.

## Decision 3: Browser Deep Research Becomes A Research Acquisition Backend

Verdict: BUILD  
Confidence: High

The system should automate ChatGPT and Claude web for Deep Research, but the automation should sit behind an acquisition backend that produces durable artifacts. Keystone should not bake ChatGPT DOM selectors into L1 research logic.

Evidence:

| Source | Signal |
| --- | --- |
| `audit/provider-feasibility/artifacts/chatgpt-tools-menu-dom.txt` | ChatGPT exposes `Deep research` as a menu option. |
| `audit/provider-feasibility/artifacts/chatgpt-deep-research-selected-dom.txt` | ChatGPT Deep Research can be programmatically selected. |
| `audit/provider-feasibility/artifacts/claude-tools-menu-dom.txt` | Claude exposes `Research` and `Web search`. |
| OpenAI Deep Research help docs | Deep Research starts from tools menu, creates plan, runs, and returns a report with citations. |
| Anthropic Research help docs | Research is available on paid Claude plans and uses web search plus citations. |

The path is to automate submission, monitor progress, export/copy/download reports, then feed them into ingestion. Browser brittleness gets contained at the adapter level.

## Decision 4: Dynamic Lens Selection Is Load-Bearing

Verdict: REPLACE hardcoded implementation, KEEP concept  
Confidence: High

The three-lens approach was useful as a business-query starter, but a universal research system needs lenses selected from the problem. The original research supports this: real consulting engagements blend categories, and problem decomposition should choose structure based on characteristics, not task labels.

Evidence:

| Source | Signal |
| --- | --- |
| `src/keystone/specification/decomposer.py:56` | Fixed financial, operational, market lenses. |
| `docs/deliverable/KNOWN-ISSUES.md: O-2` | Current lenses break for non-business questions. |
| `research/synthesis/batch-2/analysis-05-engagement-taxonomy.md` | MBB cases blend categories and should be decomposed by problem characteristics. |

## Decision 5: Add Narrative Synthesis Before Deliberation

Verdict: BUILD  
Confidence: High

The system currently pushes flat claims into deliberation. That causes both quality loss and runtime failure. The missing layer is a narrative synthesis step that turns claim lists into thesis, issue-bundle summaries, contested claims, and gap questions.

Evidence:

| Source | Signal |
| --- | --- |
| `docs/deliverable/KNOWN-ISSUES.md: O-4` | No narrative synthesis layer. |
| `notes/FIRST-RUN-ANALYSIS.md` | First run produced flat claims rather than analytical brief. |
| `output/resume_run_20260428_014314.log:17` | All analysts failed on real load and degraded to raw confidence map. |

## Decision 6: Stage Evaluation By Risk

Verdict: ADAPT  
Confidence: High

The evaluator architecture is valuable but too expensive to run indiscriminately at full depth. Layer 3 rubric scoring can call 4 Tier-1 dimensions, 6 Tier-2 dimensions, and a gestalt overlay per judge. With ensembles and multiple tasks, this explodes quickly.

Evidence:

| Source | Signal |
| --- | --- |
| `src/keystone/evaluator/layer3_rubric.py:124` | Rubric scorer performs multi-call dimension scoring. |
| `output/downstream_test_stdout.log:55` | Synthetic fact decomposition timed out twice at 300s. |
| `output/downstream_test_stdout.log:117` | Synthetic downstream works, but only on a tiny fixture. |

Implementation consequence: deterministic gates first, cheap rubrics second, high-effort/ensemble review only for final deliverables, contested claims, and high-risk outputs.

## Decision 7: Public-Data First, Confidentiality Later

Verdict: BUILD later governance boundary  
Confidence: Medium

The July target should focus on public-data workflows: public company diligence, industry landscapes, competitive landscapes, public financial filings, and public web research. Client-confidential support should wait for explicit firm approval and must include data classification and provider controls.

Evidence:

| Source | Signal |
| --- | --- |
| Owner vision, 2026-05-24 | Firm approval required before confidential client files. |
| Provider probe artifacts | Current web surfaces are external subscription services. |

## Decision 8: First Vertical Slice Should Be Research-Artifact-Centered

Verdict: BUILD  
Confidence: High

The fastest path to a working system is a vertical slice that creates an issue tree, approves a research plan, acquires one or more Deep Research artifacts, ingests those artifacts, verifies citations, synthesizes findings, and produces a brief. This uses the existing architecture while avoiding the failed all-in-one CLI research path.

Evidence:

| Source | Signal |
| --- | --- |
| Real run logs | Full pipeline melted on provider/timeouts before completion. |
| L1 deep mode test | Individual deep research can produce useful source-rich output. |
| Browser probes | ChatGPT/Claude hosted research controls are accessible. |

