# First Vertical Slice Spec

Date: 2026-05-24

## Objective

Build the smallest useful public-data Keystone workflow that proves the revised architecture:

```text
messy request
  -> dynamic issue tree draft
  -> human approval
  -> one or more research report artifacts
  -> citation/evidence ingestion
  -> synthesis brief
  -> light evaluation
  -> final research brief
```

This slice should use manual report upload first, then add ChatGPT/Claude browser automation once ingestion is stable.

## Public Test Prompt

Use a public consulting-style prompt that resembles the owner's summer workflow without using client information:

```text
I need to prepare a partner for an introductory meeting with the CFO of a publicly traded company that was recently acquired or is being acquired by a private equity sponsor. Build a public-data research plan and brief that covers the company, acquirer, financial profile, competitive landscape, industry trends, and likely consulting engagement opportunities. Start by proposing an issue tree and clarifying questions before launching research.
```

The system should let the operator pick the company before research launch. Good public candidates are companies with rich SEC filings and news coverage.

## Slice Requirements

| Requirement | Acceptance criteria |
| --- | --- |
| Clarification | System asks for target company if omitted and asks any scope questions that affect research branches. |
| Issue tree | Produces dynamic MECE tree with rationale and branch priorities. |
| Human approval | Operator can approve, reject, or revise issue tree before research jobs. |
| Research plan | Generates branch prompts suitable for ChatGPT/Claude Deep Research. |
| Report ingestion | Accepts manual Markdown/HTML/text/PDF report and normalizes it into `ResearchReportArtifact`. |
| Citation extraction | Extracts URLs/source refs and runs existing citation processor where possible. |
| Evidence bundle | Creates claim/source/absence records mapped to issue-tree branches. |
| Synthesis | Produces thesis, branch summaries, contested claims, coverage gaps, and next-wave recommendation. |
| Evaluation | Runs deterministic citation checks and a light rubric. |
| Deliverable | Produces a readable research brief with citations and a run ledger. |

## Out Of Scope For First Slice

| Deferred item | Reason |
| --- | --- |
| Full autonomous multi-wave research | Needs provider lifecycle automation and gap policy first. |
| Full L4/L5 evaluator ensemble | Too expensive for first slice. |
| Full slide deck generation | Brief proves evidence and synthesis first. |
| Full Excel DCF workflow | Parallel deterministic-financials track. |
| Confidential client files | Requires firm approval and governance. |

## Implementation Shape

| Step | Component |
| --- | --- |
| 1 | `RunLedger` created with public-data flag. |
| 2 | L0 produces `SpecificationArtifact`. |
| 3 | HITL gate records approval. |
| 4 | Branch prompt generator writes provider-ready prompts. |
| 5 | ManualUploadAdapter ingests report into `ResearchReportArtifact`. |
| 6 | Report parser extracts sections, claims, citations. |
| 7 | Citation processor normalizes and validates source refs. |
| 8 | Evidence bundle maps claims to issue nodes and acceptance criteria. |
| 9 | Narrative synthesizer produces `SynthesisArtifact`. |
| 10 | Light evaluator produces `EvaluationArtifact`. |
| 11 | Brief renderer writes `DeliverableArtifact`. |

## Quality Bar

| Dimension | Minimum acceptable result |
| --- | --- |
| Traceability | Every claim in the final brief links to report/source citation or is explicitly flagged. |
| Usefulness | Brief has a thesis and decision-relevant implications, not a list of facts. |
| Coverage | Each approved issue-tree branch has coverage status: covered, partial, missing, or out of scope. |
| Gap discipline | Next-wave recommendations are tied to specific gaps and expected value. |
| Operator control | User can see and approve issue tree before research spend. |
| Resume | Ingested reports remain reusable without rerunning provider jobs. |

## Test Plan

| Test | Purpose |
| --- | --- |
| Contract validation test | Ensure artifact JSON matches schema. |
| Manual ingestion fixture | Parse one saved ChatGPT or Claude public report. |
| Citation extraction fixture | Confirm source refs and URLs are captured. |
| Synthesis fixture | Feed small evidence bundle and verify thesis/gap output shape. |
| Resume fixture | Stop after report ingestion, resume from artifact, produce synthesis. |
| Public smoke run | One public prompt from request to brief. |

## Provider Automation Extension

After the manual slice passes:

1. Add ChatGPTWebResearchAdapter lifecycle probe.
2. Add ClaudeWebResearchAdapter lifecycle probe.
3. Store DOM snapshots/screenshots for selected tool, submitted prompt, running state, completion state, and export/copy route.
4. Route exported/copied content into the same ingestion adapter.
5. Preserve manual upload as fallback.

