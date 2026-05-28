# Mega-Goal Repo Baseline

Date: 2026-05-24  
Workspace: `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization`  
Goal source: `notes/MEGA-GOAL-PROMPT-2026-05-24.md`

## Current Position

The repo contains a serious implementation of the original DPVI architecture, but the executable path is still anchored to stale Claude-first assumptions. The strongest parts are the conceptual pipeline, handoff contracts, citation processor, HITL infrastructure, checkpoint design, and evaluator architecture. The weak parts are the provider surface, dynamic task/specification adaptation, research acquisition transport, and downstream large-context fanout.

The current evidence supports this conclusion with high confidence:

| Area | Finding | Confidence |
| --- | --- | --- |
| End-to-end status | No real full end-to-end run has completed. The documented real run reached L1.5 after 5,724.6s and failed on `claude -p` errors. | Verified from `output/pipeline_run_20260427_214406.log` |
| Provider default | `AppConfig.llm_provider` defaults to `claude_cli`; model defaults are Claude IDs. | Verified from `src/keystone/models/config.py:482` |
| Deep research path | `LayerAwareLLMFactory.deep_research_callable()` is hardwired to Claude CLI deep research. | Verified from `src/keystone/llm_client.py:463` |
| Generality | Decomposition uses `_LENSES = ["financial", "operational", "market"]`. | Verified from `src/keystone/specification/decomposer.py:56` |
| Shallow research | `SimpleMCPClient` only makes real Exa and Brave calls; other tools return stubs. | Verified from `src/keystone/gateway/simple_client.py:66` |
| Token burn | A trivial local `codex exec --json --output-schema` call succeeded but loaded 28,492 input tokens. | Verified from `audit/provider-feasibility/artifacts/codex-exec-structured-events.jsonl` |
| Browser feasibility | ChatGPT and Claude web are logged in and controllable through Chrome automation. | Verified from artifacts in `audit/provider-feasibility/artifacts/` |

## Git And Workspace State

Current branch: `codex/owner-triage-normalization`  
Remote: `https://github.com/VenialShrimp339/Keystone-Intelligence-Engine.git`  
Local HEAD: `31189a5 docs: add professor deliverable, pipeline output, and proper README`  
Remote branch state: local branch is behind `origin/codex/owner-triage-normalization` by 3 commits. The remote-only diff is README-only: 19 changed lines, 2 insertions and 17 deletions.

Known worktrees:

| Path | Branch | HEAD |
| --- | --- | --- |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` | `codex/remediation-program` | `bfb7497` |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-owner-triage-normalization` | `codex/owner-triage-normalization` | `31189a5` |
| `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-retrieval-tool-surface` | `codex/retrieval-tool-surface` | `45e3e79` |

Dirty or untracked files present before and during this audit include `TODO.md`, `.agents/`, presentation files, prior notes, and this audit output. I did not revert or normalize unrelated changes.

## Authority Stack Status

The formal authority stack still points at the older retrieval remediation program:

| File | Current claim | Relevance |
| --- | --- | --- |
| `AUTHORITY-INDEX.md` | Control-plane state and active handoff are current truth anchors. | Process authority, but stale for the user-specified May 24 objective. |
| `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml` | Lane E retrieval-tool-surface is current runtime truth. | Conflicts with the user-requested mega-goal. |
| `audit/remediation/control-plane/ACTIVE-HANDOFF.md` | Next step is retrieval parse worktree. | Superseded for this goal by `notes/MEGA-GOAL-PROMPT-2026-05-24.md`. |
| `FOUNDER-INTENT-DOCTRINE.md` | Describes the system as Claude-first and `claude -p` powered. | Stale because Anthropic changed `claude -p` billing and the owner gave a subscription-first OpenAI directive. |
| `JACK-ARCHITECTURAL-DIRECTIVES.md` | Captures dynamic issue tree, HITL, iterative research, and no mini-MVP doctrine. | Still authoritative for product intent. |

Audit stance: preserve the founder/product intent, document stale Claude-provider doctrine, and avoid mutating the older remediation control plane in this pass.

## Graphify

`graphify-out/GRAPH_REPORT.md` and `graphify-out/wiki/index.md` are absent in this worktree. The graphify instruction could not be applied from current-worktree artifacts. Because this audit changes documentation and probe artifacts only, I did not rebuild the code graph.

Update after artifact creation: `audit/contracts/model-sketch.py` is an optional code sketch, so I ran the required graphify rebuild command. It failed with `ModuleNotFoundError: No module named 'graphify'`. No graphify artifacts were rebuilt.

## Current Runtime Shape

The implemented pipeline has these major layers:

| Layer | Implemented role | Current evidence |
| --- | --- | --- |
| Meta / observation | Observation library and self-improvement direction exist conceptually. | Strong in docs, weaker in live runtime evidence. |
| L0 specification | Intent, classification, issue tree, task generation, HITL gate hook. | Built and real-run successful for business query, but too rigid for general research. |
| L1 research | Parallel agents, shallow iterative mode, deep mode. | Deep mode can produce real findings, but relies on Claude CLI and large opaque sessions. Shallow mode is incomplete because tools are stubbed. |
| Citation Processor | Citation normalization, URL validation, manifest. | Strongest live subsystem. It ran on real data and on synthetic smoke tests. |
| L1.5 deliberation | Independent analyst methodologies and aggregation. | Works on synthetic 6-claim fixture, fails or degrades on real 155-claim load. |
| L2 structuring | Sprint contracts, framework selection, outline generation. | Built, but not proven on real data and likely too call-heavy. |
| L3 generation | Markdown render path. | Built, but final deliverable flexibility is still shallow. |
| L4 / L5 evaluation | Five-layer evaluator and ensemble concepts. | Built and unit-tested, but expensive. Synthetic downstream run spent 948.4s evaluating one synthetic task. |
| HITL / server | Gate state machine and server runner exist. | Built but not proven as the primary operator workflow. |
| Checkpoint/resume | SQLite checkpoint store and resume path exist. | Concept is strong; scripts have had drift, including an async generator bug in `resume_from_l1.py`. |

## Run Evidence

| Artifact | What it proves |
| --- | --- |
| `output/pipeline_run_20260427_214406.log` | L0 completed in 1,911.3s and dispatched 13 tasks. Several deep research agents timed out after 1,200s or exited. The run reached CitationProcessor at 5,724.6s and failed in L1.5 consistency check. |
| `output/resume_run_20260428_014016.log` | Resume script drifted from the processor contract: `TypeError: 'async_generator' object can't be awaited`. |
| `output/resume_run_20260428_014314.log` | All four L1.5 analysts timed out after 600s and the system degraded to a raw-claim confidence map. |
| `output/downstream_test_stdout.log` | Synthetic downstream chain works on tiny fixture, but L4 fact decomposition timed out twice at 300s before success. |
| `output/l1_deep_mode_test_stdout.log` | Single L1 deep mode can produce real research: 28 claims, 46 sources, 9 absence items, 648.8s elapsed. |

## Provider Probe Evidence

| Artifact | Meaning |
| --- | --- |
| `codex-exec-structured-events.jsonl` | Local Codex CLI supports non-interactive execution, JSONL events, structured final output, and usage accounting. |
| `chatgpt-model-menu.png` and `chatgpt-model-menu-dom.txt` | ChatGPT web is logged in with Pro plan and exposes `Thinking` / `Heavy` plus `Pro` / `Extended` menu choices. |
| `chatgpt-tools-menu.png` and `chatgpt-tools-menu-dom.txt` | ChatGPT web exposes `Deep research` and `Web search` as tool menu radio options. |
| `chatgpt-deep-research-selected.png` and `chatgpt-deep-research-selected-dom.txt` | ChatGPT Deep Research can be selected programmatically before submission. |
| `claude-home.png` and `claude-home-dom.txt` | Claude web is logged in with Max plan and exposes a prompt box with `Opus 4.7 Adaptive`. |
| `claude-tools-menu.png` and `claude-tools-menu-dom.txt` | Claude web exposes `Research` and `Web search` as menu controls. |

## Constraints Applied

I did not run the full Keystone pipeline.  
I did not process confidential client files.  
I did not commit.  
I did not perform broad code refactors.  
I treated subscription-first OpenAI/Codex/ChatGPT and browser automation as the target path, with API as a fallback/control surface.
