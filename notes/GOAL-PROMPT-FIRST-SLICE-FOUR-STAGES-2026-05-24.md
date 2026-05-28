# Slash Goal Prompt: First Slice Four-Stage Build

## Objective

Build the first artifact-centered Keystone vertical slice by completing these four stages:

1. Artifact foundation
2. Manual Deep Research report ingestion
3. Browser lifecycle probes for ChatGPT Deep Research and Claude Research
4. Dynamic L0 planning patch with issue-tree approval readiness

The goal is not to make the old full pipeline pass. The goal is to create the new working path that can replace the brittle Claude-first pipeline: messy request -> dynamic issue tree -> approved research plan -> research report artifact -> citation/evidence bundle -> synthesis brief -> light evaluation -> readable brief.

## Context To Read First

Read these before editing:

1. `AUTHORITY-INDEX.md`
2. `SESSION-STANDARD.md`
3. `audit/mega-goal/00-repo-baseline.md`
4. `audit/architecture-preservation/ARCHITECTURE-PRESERVATION-AUDIT.md`
5. `audit/architecture-preservation/component-matrix.yaml`
6. `audit/provider-feasibility/PROVIDER-FEASIBILITY-REPORT.md`
7. `audit/provider-feasibility/experiment-log.md`
8. `audit/contracts/ARTIFACT-CONTRACTS.md`
9. `audit/contracts/contracts.yaml`
10. `audit/roadmap/JULY-27-EXECUTION-PLAN.md`
11. `audit/roadmap/first-vertical-slice-spec.md`
12. `audit/roadmap/refactor-sequence.yaml`
13. `docs/deliverable/KNOWN-ISSUES.md`
14. `docs/deliverable/CURRENT-STATUS.md`
15. `notes/OWNER-VISION-2026-05-24.md`

Also inspect relevant implementation files before changing code. Likely areas:

- `src/keystone/models/`
- `src/keystone/citation/`
- `src/keystone/specification/`
- `src/keystone/pipeline/`
- `src/keystone/server/`
- existing tests under `tests/`

Do not assume the audit documents are perfectly right. Use them as a starting hypothesis, then verify against code.

## Hard Constraints

- Public-data workflows only.
- Do not process client-confidential files.
- Do not run the full Keystone pipeline.
- Do not default to paid API paths.
- Do not revive `claude -p` as a primary path.
- Do not broadly refactor unrelated modules.
- Do not overwrite or revert dirty user files.
- Do not commit unless explicitly instructed.
- Keep manual upload/report ingestion as a first-class fallback even after browser automation works.
- Treat provider feasibility as "how to make this work." For each limitation, define the route, fallback route, and next proof.

## Current Strategic Direction

Preserve:

- DPVI
- L0 specification and issue tree
- citation processor concepts
- HITL/approval gates
- checkpoint/resume concept
- evaluator doctrine

Replace or adapt:

- Claude-first runtime doctrine
- hardcoded financial/operational/market lenses
- `claude -p` deep research dependency
- all-claims-to-all-analysts downstream fanout
- non-durable in-memory handoffs

## Stage 1: Artifact Foundation

Implement production-ready artifact contracts, persistence, and a run ledger.

### Required Deliverables

- Pydantic models for:
  - `RunLedger`
  - `SpecificationArtifact`
  - `IssueTreeNodeArtifact`
  - `ProviderJobArtifact`
  - `ResearchReportArtifact`
  - `SourceBundleArtifact`
  - `EvidenceBundleArtifact`
  - `SynthesisArtifact`
  - `EvaluationArtifact`
  - `DeliverableArtifact`
- Simple local artifact store that can:
  - write artifact JSON
  - read artifact JSON
  - list artifacts by run ID
  - update artifact status
  - store file paths for raw/normalized report content
- IDs and paths must be stable and deterministic enough for resume.
- Schema versioning must be present.
- Public-data flag must be recorded at run level.

### Acceptance Criteria

- Unit tests prove artifact round-trip persistence.
- Unit tests prove status updates do not corrupt artifacts.
- Unit tests prove a run ledger can reference child artifacts.
- The implementation does not require a database for the first slice.
- File layout is documented in code or tests.

## Stage 2: Manual Deep Research Report Ingestion

Build the reliable ingestion path before depending on browser automation.

### Required Deliverables

- `ManualUploadAdapter` or equivalent ingestion entrypoint for local report files.
- Support at minimum:
  - Markdown
  - plain text
  - HTML saved/copied from browser
- Best-effort PDF support only if straightforward with existing dependencies. Do not block on PDF.
- Normalize report into `ResearchReportArtifact`.
- Extract:
  - title
  - sections
  - source URLs
  - citation references where present
  - candidate claims
  - quality flags for missing/ambiguous citations
- Convert report into an `EvidenceBundleArtifact`.
- Integrate existing citation processor where appropriate, but avoid forcing a huge refactor.

### Fixture Requirement

Use a small public synthetic fixture if no real Deep Research export is available. The fixture must include:

- at least 3 sections
- at least 5 claims
- at least 5 source URLs
- at least 1 claim with missing citation to test quality flags

Mark synthetic fixtures clearly as fixtures. Do not imply they prove provider export.

### Acceptance Criteria

- Unit tests parse the fixture into a `ResearchReportArtifact`.
- Unit tests create an `EvidenceBundleArtifact`.
- Unit tests show missing citation flags are produced.
- The ingestion path can be called without launching the full pipeline.
- A developer can rerun only ingestion and synthesis from saved artifacts.

## Stage 3: Browser Lifecycle Probes

Prove the implementation path for ChatGPT Deep Research and Claude Research with tiny public prompts.

### Required Deliverables

- Probe scripts or documented probe procedure under a suitable repo path, preferably `scripts/provider_probe/` or `audit/provider-feasibility/probes/`.
- Saved artifacts under `audit/provider-feasibility/artifacts/` or `output/provider-probes/`.
- For ChatGPT:
  - selected model/mode
  - selected Deep Research tool
  - submitted public prompt
  - plan/preflight state, if shown
  - running state
  - completion state
  - export/copy/download route
  - saved report content
- For Claude:
  - selected model/mode
  - selected Research and Web Search controls
  - submitted public prompt
  - running state
  - completion state
  - export/copy/download route
  - saved report content

### Probe Prompt

Use a tiny public prompt designed to complete quickly:

```text
Using only public web sources, produce a concise research report on the current state of the U.S. auto body repair industry consolidation trend. Include 5 cited factual claims, source links, and a short note on evidence gaps. Keep the report compact.
```

If Deep Research forces a broader or longer workflow, accept that. Save the lifecycle state and continue or resume later rather than treating elapsed time as failure.

### Browser Automation Rules

- Use the logged-in Chrome profile via the Chrome automation path.
- Do not inspect cookies, local storage, passwords, or account internals.
- Do not upload confidential files.
- Do not submit anything except public test prompts.
- If the provider asks for a plan confirmation, choose the public-web/default option when safe and record the state.
- If a CAPTCHA, security barrier, payment prompt, or account-sensitive prompt appears, stop and record a handoff.

### Acceptance Criteria

- At least one provider completes a public research report and the content is saved durably.
- If one provider fails or requires handoff, the failure is documented with screenshot/DOM evidence and a next route.
- Saved report content can be fed into the manual ingestion path from Stage 2.
- The report is not trapped in a browser tab as the only durable artifact.

## Stage 4: Dynamic L0 Planning Patch

Patch L0 toward dynamic issue-tree planning without rebuilding the entire pipeline.

### Required Deliverables

- Replace or bypass hardcoded `_LENSES = ["financial", "operational", "market"]` with a dynamic lens selector.
- Lens selector should choose 2-5 lenses based on the request, domain, decision context, and output target.
- Include general lens families such as:
  - market/competitive
  - financial
  - operational
  - regulatory/legal
  - technical/architecture
  - scientific/evidence-review
  - customer/user
  - risk/security
  - temporal/trend
  - stakeholder/incentive
  - causal/driver tree
  - comparative/benchmark
- Preserve the existing parallel heterogeneous decomposition concept.
- Emit a human-reviewable research plan artifact or structure that can support approval before research launch.
- Add a clarification event or structured output when the request is materially underspecified.

### Acceptance Criteria

- Unit tests prove a business diligence prompt does not always use the same lenses as a technical architecture prompt.
- Unit tests prove a scientific/literature prompt receives a different lens set.
- Unit tests prove ambiguous prompt handling produces clarifying questions or an approval-needed state.
- Existing L0 behavior for business prompts remains coherent.
- The old fixed lens list is no longer the load-bearing source of truth.

## Integration Target

After the four stages, demonstrate a narrow vertical slice without running the old full pipeline:

1. Create a run ledger for a public prompt.
2. Generate or load a specification/issue-tree artifact.
3. Ingest a saved research report into a report artifact.
4. Convert it into an evidence bundle.
5. Produce a minimal synthesis artifact or brief.
6. Record evaluation/quality flags.
7. Write all artifacts to disk.

This can be a test or a small script. It must be repeatable without launching a full multi-hour pipeline.

## Verification Requirements

Run focused tests only. Do not run the full pipeline.

Minimum:

- artifact model/store tests
- manual ingestion tests
- dynamic lens selector tests
- integration smoke test for the narrow vertical slice
- syntax/type checks if already standard in the repo

If graphify is available after code changes, run:

```bash
python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"
```

If graphify is unavailable, record the exact failure in `SESSION-LOG.md`.

## Documentation Requirements

Update or create concise docs:

- implementation notes for artifact store and ingestion
- provider probe results
- next-step notes for browser adapters
- `SESSION-LOG.md`

The final response must include:

- files changed
- tests run and results
- provider probe status
- what works now
- what remains manual
- next recommended goal

## Stopping Conditions

Stop and report clearly if:

- a provider page requires CAPTCHA, payment, password re-entry, or sensitive account action
- the repo has conflicting dirty changes in files you must edit and the conflict cannot be worked around
- a necessary dependency is unavailable and cannot be installed safely
- after three distinct attempts, browser automation cannot communicate with Chrome

Do not stop merely because a task is large or a provider run takes time. Persist state and continue.

## Preferred Work Order

1. Artifact foundation
2. Manual ingestion
3. Dynamic L0 planning
4. Browser lifecycle probes
5. Narrow vertical slice integration
6. Focused tests
7. Documentation and session log

Browser probes can run in parallel with local code work if the automation environment supports it safely.

