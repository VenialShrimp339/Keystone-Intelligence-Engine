# Mega Goal Prompt - Architecture Preservation + Provider Feasibility

Use this prompt for an autonomous `/goal` run. It is designed to let Codex work deeply without refactoring prematurely.

## Objective

Produce the evidence base and execution plan needed to make Keystone Intelligence Engine operational by July 27, 2026, while preserving valuable existing architecture and moving the runtime away from Claude CLI toward subscription-first ChatGPT/Codex/browser-backed execution.

This is an audit, feasibility, and planning goal. Do not perform broad code refactors. Small probe scripts are allowed only when they directly support provider feasibility or artifact-contract validation.

## Required Operating Doctrine

Read and internalize `notes/OWNER-VISION-2026-05-24.md` first.

Key directives:

- The July 27 target is a full operational system, not a narrow demo.
- Preserve the issue-tree/specification engine as core product value.
- Evaluate conceptual architecture and current implementation separately.
- Default to subscription-powered execution through Codex CLI, ChatGPT web, and Claude web where feasible.
- Use paid API only when subscription paths are technically blocked, materially weaker for the job, or too costly to reconstruct.
- Public-data workflows come first. Do not process client-confidential files.
- Human approval gates should be configurable.
- When a workflow is slow, brittle, tedious, or expensive, assume a better architecture likely exists and investigate before accepting the limitation.

## Required Context Read

Read these first:

1. `AGENTS.md`
2. `AUTHORITY-INDEX.md`
3. `SESSION-STANDARD.md`
4. `audit/remediation/control-plane/CONTROL-PLANE-STATE.yaml`
5. `audit/remediation/control-plane/ACTIVE-HANDOFF.md`
6. `notes/OWNER-VISION-2026-05-24.md`

Then read the architecture/rationale corpus:

1. `CAPSTONE-PLAN-v2.md`
2. `JACK-ARCHITECTURAL-DIRECTIVES.md`
3. `docs/architecture-and-evolution.md`
4. `research/synthesis/UNIFIED-SYNTHESIS.md`
5. `research/synthesis/batch-2/MASTER-SYNTHESIS.md`
6. `research/synthesis/batch-2/analysis-05-engagement-taxonomy.md`
7. `reference/RESEARCH-PROMPTS-FINAL.md`
8. `docs/deliverable/CURRENT-STATUS.md`
9. `docs/deliverable/KNOWN-ISSUES.md`
10. `notes/FIRST-RUN-ANALYSIS.md`

Then inspect the implementation and evidence:

1. `src/keystone/models/config.py`
2. `src/keystone/llm_client.py`
3. `src/keystone/pipeline/orchestrator.py`
4. `src/keystone/specification/`
5. `src/keystone/research/`
6. `src/keystone/deliberation/`
7. `src/keystone/structuring/`
8. `src/keystone/evaluator/`
9. `src/keystone/retrieval/`
10. `scripts/full_pipeline_test.py`
11. `scripts/resume_from_l1.py`
12. `output/pipeline_run_20260427_214406.log`
13. `output/resume_run_20260428_014016.log`
14. `output/resume_run_20260428_014314.log`
15. `output/downstream_test_stdout.log`
16. `output/l1_deep_mode_test_stdout.log`

If graphify artifacts exist, read them before architecture conclusions:

- `graphify-out/wiki/index.md`
- `graphify-out/GRAPH_REPORT.md`

## Public Test Prompts

Use these as evaluation anchors. You may refine wording if needed, but preserve the task type.

### Prompt A: Broad Consulting Diligence

Evaluate the competitive landscape of the US auto body repair industry across the top 10 metropolitan areas by population. Identify the largest chains, their estimated market share, whether the market is consolidating or fragmenting, the role of insurers and OEM certification, and what a new entrant would need to know before entering or acquiring in the space.

### Prompt B: Meta-Research / System Design

Assess the best architecture for an AI system that automates consultant-grade research by decomposing ambiguous questions into issue trees, running parallel deep research, normalizing evidence, deliberating across claims, evaluating output quality, and producing source-backed deliverables. Identify existing systems and patterns worth adopting, where custom architecture is justified, and what failure modes must be structurally prevented.

### Prompt C: Public Financial Extraction / Modeling

Using only public sources, pull and analyze the most recent annual and quarterly filings for Driven Brands Holdings Inc. (`DRVN`). Extract income statement, balance sheet, cash flow, segment, store-count, debt, and key operating metrics into a clean workbook-ready structure. Produce a concise financial analysis focused on revenue growth, margins, cash conversion, leverage, capital intensity, and diligence questions a consultant should investigate next. Do not run broad web Deep Research unless the task planner determines it is necessary.

## Phase 0: Repo Truth And Baseline

Determine the true current repo state:

- Current branch and remote state.
- Whether local branch is behind remote.
- Dirty/untracked files and whether they predate this run.
- Worktree list and which worktree control-plane docs claim is canonical.
- Whether control-plane docs conflict with GitHub default branch.

Deliverable:

- `audit/mega-goal/00-repo-baseline.md`

Success criteria:

- State which branch/worktree the rest of the audit is based on.
- Do not overwrite user changes.
- Do not pull or merge unless the user explicitly instructed it.

## Phase 1: Architecture Preservation Audit

Produce a preservation audit that distinguishes strategic concept from current implementation.

Components to cover:

- Meta-layer / Observation Library / self-improvement loop.
- L0 Specification Engine.
- Issue-tree generation and dynamic lens selection.
- Clarification loop and human approval gate.
- L1 Research Agents.
- Research acquisition backends.
- Citation processor and source normalization.
- L1.5 Deliberation.
- L2 Content Structuring and sprint contracts.
- L3 generation/rendering/output layer.
- L4/L5 evaluator and cross-model ensemble.
- Checkpoint/resume.
- Retrieval stack.
- Provider/runtime layer.
- UI and operator workflow.
- Data confidentiality and public/private run boundary.

For each component, produce:

- Original rationale.
- Evidence/research basis.
- Current implementation status.
- Observed failure modes from code/logs/tests.
- Runtime/token/usage risk.
- July 27 importance.
- Recommendation: KEEP / ADAPT / REPLACE / DELETE / DEFER.
- Confidence level.
- Exact local file/log references.

Deliverables:

- `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`
- `audit/architecture-preservation/component-matrix.yaml`
- `audit/architecture-preservation/decision-log.md`

Success criteria:

- No component is rejected only because the current run failed.
- No component is preserved only because the plan said it was important.
- At least one strongest argument is written for preserving each major layer and one strongest argument for changing it.
- Final section gives a ranked architecture refactor roadmap.

## Phase 2: Subscription Provider Feasibility

Determine how much of the target system can be powered through subscription-backed execution.

Test matrix:

### Codex CLI

Evaluate:

- Non-interactive execution.
- JSONL event streams.
- Schema-constrained final output.
- Model selection.
- Web search availability.
- MCP/tool integration.
- Access token or persistent auth feasibility.
- Structured output fidelity.
- Failure mode and retry control.

### ChatGPT Web

Evaluate using public-data tasks:

- Can browser automation open ChatGPT and submit a prompt?
- Can it select or access Deep Research?
- Can it select or access Pro / web-only high-end models if available?
- Can it detect job completion?
- Can it copy, export, or download the report?
- Can it preserve citations/source links?
- Can it run multiple jobs in parallel?
- What rate/concurrency limit appears in practice?
- What artifacts can be saved durably?

### Claude Web

Evaluate the same points for Claude web, especially Deep Research parallel capacity and export/copy behavior.

### Fallback APIs

Use official docs and minimal probes only. Identify where Responses API or Deep Research API provides materially better control:

- background mode
- webhooks
- exact usage accounting
- tool-call caps
- source/tool traces
- structured outputs

Do not default to API. Treat API as fallback/control.

No artificial subscription usage cap is required, but experiments should be information-gain driven. Run enough probes to answer the capability questions, then stop. Do not spam providers merely because usage is available.

Deliverables:

- `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`
- `audit/provider-feasibility/provider-capability-matrix.yaml`
- `audit/provider-feasibility/experiment-log.md`
- `audit/provider-feasibility/artifacts/` for screenshots, exports, copied reports, or probe outputs
- `scripts/provider_probe/` only if small scripts are useful

Success criteria:

- Every capability claim is labeled PROVEN / LIKELY / BLOCKED / UNTESTED.
- Every PROVEN claim has a command, screenshot, exported artifact, local log, or official-doc citation.
- Report says which backend should power each Keystone layer for July 27.
- Report identifies what must be manually tested by the owner if authentication or UI access blocks automation.

## Phase 3: Artifact Contracts

Define the durable contracts needed to connect the preserved architecture to subscription/browser acquisition.

Draft contracts for:

- `ResearchPlan`
- `IssueTree`
- `ApprovalGate`
- `ResearchWave`
- `ResearchJob`
- `ResearchReportArtifact`
- `EvidenceBundle`
- `ClaimRecord`
- `CitationManifest`
- `DeliberationMap`
- `SynthesisBrief`
- `WorkbookArtifact`
- `DeckArtifact`
- `RunLedger`

For each:

- Purpose.
- Required fields.
- Producer.
- Consumer.
- Validation rules.
- Persistence path.
- Failure/retry behavior.

Deliverables:

- `audit/contracts/ARTIFACT-CONTRACTS.md`
- `audit/contracts/contracts.yaml`
- Optional Pydantic model sketch in `audit/contracts/model-sketch.py`

Success criteria:

- Contracts support all three public test prompts.
- Contracts support manual report upload and browser-exported Deep Research.
- Contracts support deterministic SEC/financial extraction without forcing Deep Research.
- Contracts preserve source/citation provenance.

## Phase 4: Synthesis Roadmap

Combine the architecture audit and provider feasibility findings into an execution plan.

Deliverables:

- `audit/roadmap/JULY-27-EXECUTION-PLAN.md`
- `audit/roadmap/first-vertical-slice-spec.md`
- `audit/roadmap/refactor-sequence.yaml`

The roadmap must include:

- First vertical slice.
- Tests/acceptance criteria before implementation.
- Parallelizable workstreams.
- What to build first, second, third.
- What to defer beyond July 27.
- Which existing components are preserved.
- Which components are replaced.
- How Claude CLI dependency is removed.
- How subscription-first execution is achieved.

Success criteria:

- Plan is specific enough that a new Codex agent could start implementation without redoing the audit.
- Plan preserves valuable original architecture where justified.
- Plan prevents full pipeline quota melt during testing.
- Plan defines a clear stopping point for the next implementation goal.

## Quality Bar

Every material claim must be traceable to one of:

- Local file reference.
- Local log/output artifact.
- Generated experiment artifact.
- Screenshot.
- Official provider documentation.
- Clearly labeled owner directive.

Use confidence labels:

- HIGH: directly verified in code/logs/artifacts or official docs.
- MEDIUM: supported by multiple credible local docs or a successful small probe.
- LOW: plausible but not yet tested.

Do not hide uncertainty. Put unresolved questions in a dedicated section.

## Constraints

- Do not run full Keystone pipeline tests.
- Do not process confidential client files.
- Do not commit unless explicitly instructed.
- Do not perform broad code refactors.
- Do not overwrite dirty user files.
- Do not use paid API calls as the default route.
- Do not treat old Claude-first doctrine as binding when it conflicts with the 2026-05-24 owner vision.

## Completion Conditions

The goal is complete when all required deliverables exist, each success criterion is addressed, and the final roadmap identifies the next implementation goal with acceptance tests.

If blocked, try at least three alternate approaches before declaring the block. Document the block, attempts, and the exact user input needed to proceed.
