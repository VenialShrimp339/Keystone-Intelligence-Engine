# Candidate 5cc9585 File Manifest

- Candidate commit: `5cc9585`
- Parent commit: `4819527`
- Baseline commit: `4819527`
- Wave: `wave-3b`
- Purpose: record the exact committed Wave 3B candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/events.py`
- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/round_state.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/__init__.py`
- `src/keystone/knowledge/wiki_builder.py`
- `src/keystone/knowledge/index_maintainer.py`
- `src/keystone/knowledge/engagement_store.py`

### Tests

- `tests/unit/test_protocol_contracts.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/research/test_research_agent.py`
- `tests/unit/knowledge/test_wiki_builder.py`
- `tests/unit/knowledge/test_index_maintainer.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/e2e/test_mock_pipeline.py`
- `tests/canary/test_architectural_guarantees.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Explicit Denylist

Do not treat these as part of the Wave 3B candidate unless a later controller action explicitly widens scope:

- `src/keystone/evaluator/prompts/**`
- `src/keystone/specification/prompts/**`
- `src/keystone/specification/engagement_classifier.py`
- `src/keystone/specification/template_registry.py`
- `src/keystone/evaluator/rubric_config.py`
- `src/keystone/pipeline/provenance_sidecar.py`
- `src/keystone/pipeline/post_synthesis_verifier.py`
- Wave 4, Wave 4B, or Wave 5 setup docs
- immutable historical review packets
- unrelated main-workspace dirty files

## Suspicious Dirty Files In Main Workspace

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contains numerous unrelated pre-existing dirty and deleted files. Representative excluded entries:

- `.claude/settings.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `OPENAI-SWITCHOVER-HANDOFF.md`
- `audit/GAP-TRIAGE.md`
- `docs/PARALLEL-EXECUTION-PLAN.md`
- `reference/analysis/00-master-index.md`
- `research-reports/Deep_Research_Report_From_Prompt_1.md`
- `reference/nano-claude-code`

None of those controller-workspace dirty files were staged for `5cc9585`.

## Committed Diff Classification

### Expected

- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/research/__init__.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/round_state.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/test_protocol_contracts.py`

### Legitimate Collateral

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

### Scope Creep

- None

### Quarantined Unrelated

- all unrelated dirty and deleted files already present in `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine`

## Classification Rule

Every touched file in the candidate is classified as one of:

- `expected`
- `legitimate collateral`
- `scope creep`
- `quarantined unrelated`

No unresolved `scope creep` remains in `5cc9585`.
