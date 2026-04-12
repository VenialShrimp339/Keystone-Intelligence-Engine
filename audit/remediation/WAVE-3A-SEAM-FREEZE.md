# Wave 3A Seam Freeze

*Date: 2026-04-12 | Status: binding seam-freeze checkpoint before any Wave 3 code*

---

## Purpose

Wave 3A exists to freeze the highest-risk ownership seams before Wave 3 implementation opens.

This document is authoritative for:

1. verifier-module ownership
2. provenance-sidecar emission point
3. round-state persistence location
4. deep vs shallow template/prompt wiring
5. inner-loop vs outer-loop authority

It is not permission to start coding from the main workspace.  
It is the boundary contract the next clean Wave 3 worktree must honor.

## Inputs

This seam freeze was derived from:

1. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
2. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
3. `audit/remediation/AUTONOMOUS-REMEDIATION-PLAN-v4.md`
4. `audit/remediation/WAVE-3-3B-PREWORK.md`
5. `audit/remediation/decisions/FINAL-DECISIONS-v2.1.md`
6. `graphify-out/GRAPH_REPORT.md`
7. current-code inspection of `src/keystone/pipeline/orchestrator.py`, `src/keystone/research/research_agent.py`, `src/keystone/specification/template_registry.py`, `src/keystone/research/context_loader.py`, `src/keystone/knowledge/wiki_builder.py`, `src/keystone/knowledge/engagement_store.py`, and `src/keystone/contracts.py`

## Global Rules

1. The main workspace stays controller/docs only.
2. Any Wave 3 code lane must open from cleared commit `2cdbfec`.
3. Wave 3 scope remains `Decision C + E2 + F1 + DAG + concrete verifier + provenance sidecar`.
4. Wave 3B scope remains `Thin Pipeline-L2 + live iterative loop`; Wave 3 must not silently pull Wave 3B control-flow into the runtime.
5. `src/keystone/pipeline/orchestrator.py` remains the integration hotspot with a single owner in the implementation lane.
6. `W2B-R01` remains visible as a carried non-blocking follow-up and must not disappear from later planning.

## Seam 1: Verifier Module

### In Scope

- Wave 3 owns a concrete verifier module at `src/keystone/pipeline/post_synthesis_verifier.py`.
- That module owns the current post-evaluation provenance gate now implemented as `_filter_confidence_map_by_passed_tasks()` in `src/keystone/pipeline/orchestrator.py`.
- The verifier is responsible for:
  - filtering tier claims by `passed_task_ids`
  - rebuilding claim provenance for surviving claims
  - rebuilding gap provenance for surviving gaps
  - providing a narrow handoff back to the orchestrator for render-safe data

### Out Of Scope

- evaluator Layer-2 citation validation
- renderer formatting policy
- provenance-sidecar formatting or file writing
- any broader rendered-text semantic verification contract beyond the passed-task provenance gate

### Owner

- Primary implementation owner: `src/keystone/pipeline/post_synthesis_verifier.py`
- Integration owner: `src/keystone/pipeline/orchestrator.py`

### Handoff Contract

- Inputs: `ConfidenceMap`, `passed_task_ids`
- Output: filtered `ConfidenceMap` suitable for render-time and sidecar-time use
- Orchestrator may call the verifier, but it may not keep a second competing implementation of the filtering logic after the module lands

### Reopen Trigger

- Reopen this seam only if Wave 3 needs a verifier interface that changes the data contract beyond `ConfidenceMap -> filtered ConfidenceMap`, or if later evidence requires claim-level rendered-text verification rather than provenance gating alone

## Seam 2: Provenance Sidecar Emission Point

### In Scope

- Wave 3 owns a dedicated sidecar builder in the pipeline layer, expected at `src/keystone/pipeline/provenance_sidecar.py`.
- The sidecar emission point is frozen at the post-evaluation, post-verifier, pre-output boundary of the pipeline.
- The sidecar must be derived from the same filtered render surfaces used for the deliverable:
  - passed findings
  - filtered confidence map
  - filtered manifest
  - evaluation results

### Out Of Scope

- citation dedup internals
- wiki compilation internals
- markdown renderer layout decisions
- persistence of raw research-round memory artifacts

### Owner

- Primary implementation owner: `src/keystone/pipeline/provenance_sidecar.py`
- Emission owner: `src/keystone/pipeline/orchestrator.py`

### Handoff Contract

- CitationProcessor remains the source of canonical citation truth.
- Deliberation remains the source of claim/gap provenance.
- The verifier decides what survives to the final deliverable surface.
- The sidecar builder serializes that surviving surface into `<engagement_id>.provenance.md` and must not invent new provenance semantics upstream.

### Reopen Trigger

- Reopen this seam only if a later deliverable-writer abstraction becomes the canonical output boundary and the sidecar must move there without losing access to filtered render-state inputs

## Seam 3: Round-State Persistence Location

### In Scope

- Wave 3A freezes persistent round-state under the engagement memory tree, not inside in-memory orchestrator fields and not inside the research-agent instance.
- The planned owner is a dedicated module under `src/keystone/research/round_state.py`.
- The persistence location is `engagements/{engagement_id}/memory/rounds/` with per-round machine-readable state artifacts.
- This round-state layer may reference wiki artifacts, but it is distinct from:
  - `memory/raw/`
  - `memory/compiled/`
  - `memory/INDEX.md`

### Out Of Scope

- storing round state inside `ResearchAgent`
- storing round state inside `TemplateRegistry` or `SpecificationEngine`
- collapsing round-state into compiled wiki pages or their metadata sidecars

### Owner

- Primary implementation owner: `src/keystone/research/round_state.py`
- Storage-adjacent collaborators: `src/keystone/knowledge/engagement_store.py`, `src/keystone/research/context_loader.py`, `src/keystone/knowledge/wiki_builder.py`

### Handoff Contract

- The round-state module owns persistence and reload of round intent, findings summary, gaps, branch coverage, and stop-condition status.
- `ContextLoader` consumes persisted memory plus compiled wiki artifacts; it does not become the source of truth for round control.
- `WikiBuilder` compiles content artifacts; it does not own controller state.

### Reopen Trigger

- Reopen this seam only if the project replaces the filesystem memory backend entirely and can preserve the same conceptual ownership boundary in a new store

## Seam 4: Deep vs Shallow Template/Prompt Wiring

### In Scope

- Template selection remains upstream in `TemplateRegistry` and assignment creation.
- Prompt consumption is frozen inside `ResearchAgent`, because the assigned `AgentInstance.definition` already carries the chosen template and its `system_prompt`.
- Wave 3 wiring belongs in:
  - `_build_deep_research_prompt()` for deep mode
  - `_build_synthesis_prompt()` for shallow mode synthesis
- Shallow tool-call query construction is not the prompt-wiring owner; the accepted Wave 3 requirement is prompt use in synthesis, not a second template system inside tool parameter assembly.

### Out Of Scope

- moving prompt assembly into `TemplateRegistry`
- duplicating template prompt logic in `SpecificationEngine` or `TaskGenerator`
- introducing separate deep and shallow template registries

### Owner

- Prompt-definition owner: `src/keystone/specification/template_registry.py`
- Prompt-consumption owner: `src/keystone/research/research_agent.py`
- Governance visibility owner for deep-mode bypass state: `src/keystone/pipeline/orchestrator.py`

### Handoff Contract

- `TemplateRegistry` chooses and supplies the template.
- `_build_assignments()` passes the chosen template through `AgentInstance.definition`.
- `ResearchAgent` is the only component allowed to translate that template into deep or shallow prompt text.
- The orchestrator may record that deep mode bypassed the gateway, but it does not assemble research prompts.

### Reopen Trigger

- Reopen this seam only if the system introduces a gateway-owned prompt broker or a provider-agnostic research prompt abstraction that replaces direct prompt assembly inside `ResearchAgent`

## Seam 5: Inner-Loop vs Outer-Loop Authority

### In Scope

- Until Wave 3B lands, the live runtime still has only one production round controller: the inner loop in `src/keystone/research/research_agent.py`.
- Wave 3 may add audit visibility and completeness fixes around that loop, but it may not add a second live engagement-level round controller in the orchestrator.
- Wave 3B is the only wave allowed to introduce outer-loop authority in `src/keystone/pipeline/orchestrator.py`.
- When Wave 3B starts, engagement-level stopping, branch coverage, sufficiency, novelty exhaustion, and round `N+1` task generation belong to the orchestrator.

### Out Of Scope

- nested independent round controllers in both `ResearchAgent` and `Pipeline`
- branch-coverage authority inside `ResearchAgent`
- using `ContextLoader` or `WikiBuilder` as de facto round controllers

### Owner

- Current inner-loop owner before Wave 3B: `src/keystone/research/research_agent.py`
- Future outer-loop owner in Wave 3B: `src/keystone/pipeline/orchestrator.py`

### Handoff Contract

- Wave 3 work may preserve the current inner loop for per-task execution.
- Wave 3B must either collapse the agent loop to a per-round execution primitive or otherwise make the orchestrator the sole authority for cross-task round advancement.
- There must be one authoritative round controller at runtime, never two peers.

### Reopen Trigger

- Reopen this seam immediately if any Wave 3 change requires orchestrator-driven multi-round task replay before `WAVE-3B-SETUP.md` exists

## Implementation Guardrails

1. Keep new Wave 3 modules additive where possible before the orchestrator integration pass.
2. Do not let the verifier, sidecar, or round-state seams widen into Wave 3B control-flow by accident.
3. Do not move wiki-content compilation ownership out of `knowledge/`.
4. Do not move research-prompt assembly out of `ResearchAgent` during Wave 3.
5. Do not leave duplicate implementations of the same seam live after integration.

## Ready-To-Open Result

After this checkpoint lands:

1. a clean Wave 3 setup doc may be written
2. a clean Wave 3 worktree may be opened from `2cdbfec`
3. implementation may proceed only within the seam ownership frozen above
