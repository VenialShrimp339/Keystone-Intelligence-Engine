# Candidate 5cc9585 File Manifest

- Candidate commit: `5cc9585`
- Parent commit: `4819527`
- Baseline commit: `4819527`
- Wave: `wave-3b`
- Purpose: record the exact committed Wave 3B candidate surface for review and controller checkpointing

## Allowed Write Set

### Code

- `src/keystone/contracts.py`
- `src/keystone/models/__init__.py`
- `src/keystone/models/structuring.py`
- `src/keystone/pipeline/orchestrator.py`
- `src/keystone/pipeline/markdown_renderer.py`
- `src/keystone/research/research_agent.py`
- `src/keystone/research/agent_pool.py`
- `src/keystone/research/round_state.py`
- `src/keystone/research/context_loader.py`
- `src/keystone/research/__init__.py`
- `src/keystone/structuring/__init__.py`
- `src/keystone/structuring/content_structuring.py`

### Tests

- `tests/unit/test_protocol_contracts.py`
- `tests/unit/structuring/test_content_structuring.py`
- `tests/unit/research/test_round_state.py`
- `tests/unit/research/test_context_loader.py`
- `tests/unit/pipeline/test_markdown_renderer.py`
- `tests/unit/pipeline/test_orchestrator.py`

### Generated Collateral Landed With Code

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

## Exact-Surface Boundary

Any file not listed in `Allowed Write Set` or `Committed Diff Classification` is outside the exact committed surface of `5cc9585`.

## Suspicious Dirty Files In Main Workspace

The controller workspace at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine` still contained unrelated pre-existing dirty and deleted files, but none of them were staged for `5cc9585`.

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
