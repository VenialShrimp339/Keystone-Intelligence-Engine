# July 27 Execution Plan

Date: 2026-05-24  
Target date: 2026-07-27

## Target Outcome

By July 27, Keystone should run a public-data consulting research workflow end to end:

1. Take a messy research request.
2. Ask clarifying questions when scope is underspecified.
3. Generate a dynamic issue tree and research plan.
4. Pause for human approval.
5. Launch or ingest hosted Deep Research reports by branch.
6. Normalize citations and evidence.
7. Synthesize a thesis, branch summaries, gaps, and contested claims.
8. Run staged evaluation.
9. Produce a research brief and reusable issue-tree/evidence package.

Financial extraction and workbook generation should run as a deterministic public-company workflow in parallel, but it should not block the first research vertical slice.

## Strategic Direction

The system should become artifact-centered. The current code tries to run the whole research workflow through long LLM calls inside the same pipeline context. The revised design should move expensive work behind durable artifacts:

```text
User Request
  -> Clarification
  -> Dynamic Issue Tree
  -> Approved Research Plan
  -> Provider Jobs
  -> Research Reports / Source Bundles
  -> Evidence Bundles
  -> Narrative Synthesis
  -> Staged Evaluation
  -> Deliverable
```

## Milestones

| Window | Milestone | Exit criteria |
| --- | --- | --- |
| May 24 - May 31 | Provider and artifact foundation | Provider adapter interface sketched, report artifact model implemented, manual upload ingestion works on saved ChatGPT/Claude report. |
| June 1 - June 7 | First research vertical slice | One public prompt runs through issue tree, manual/automated report ingestion, citation normalization, synthesis brief, and light evaluation. |
| June 8 - June 14 | Browser lifecycle automation | ChatGPT Deep Research and Claude Research can submit a public branch prompt, detect completion, and save report artifacts. |
| June 15 - June 21 | Dynamic specification | Hardcoded lenses replaced with dynamic lens selector; clarification gate pauses before research when scope is ambiguous. |
| June 22 - June 30 | Synthesis and deliberation repair | Narrative synthesis layer added; L1.5 runs on claim clusters or synthesis briefs rather than all raw claims. |
| July 1 - July 7 | Deterministic public-company workflow | SEC/EDGAR public filings flow into source bundles, extracted statements, and a basic workbook. |
| July 8 - July 14 | Staged evaluator and operator workflow | Cheap gates run by default; high-effort evaluator only escalates on final/contested outputs. HITL review loop is usable. |
| July 15 - July 21 | Real public-data rehearsals | At least 3 public prompts complete from request to deliverable without manual code intervention. |
| July 22 - July 26 | Hardening | Resume, retries, provider fallback, artifact inspection, and runbooks are documented and tested on public prompts. |
| July 27 | Operational target | System is useful for analyst workflow on public-data research and issue-tree planning. |

## Workstream A: Architecture Preservation And Refactor

Goal: preserve the valid architecture while changing execution boundaries.

Priority tasks:

| Task | Outcome |
| --- | --- |
| Add artifact contracts | Durable schema for provider jobs, reports, evidence bundles, synthesis, evaluation, and deliverables. |
| Build provider adapter interface | One orchestration surface for Codex CLI, ChatGPT web, Claude web, API fallback, deterministic sources, and manual upload. |
| Replace provider defaults | Move from `claude_cli` default to subscription-first provider routing. |
| Repair checkpoints | Persist every provider job and artifact; resume from artifacts, not only pipeline stage memory. |

## Workstream B: Research Acquisition

Goal: make hosted Deep Research a first-class input source.

Priority tasks:

| Task | Outcome |
| --- | --- |
| Manual report ingestion | Accept copied/exported ChatGPT/Claude report and normalize into `ResearchReportArtifact`. |
| ChatGPT lifecycle probe | Submit small public Deep Research prompt and capture selectors for running/completion/export. |
| Claude lifecycle probe | Same for Claude Research. |
| Provider ledger | Record provider, prompt, status, snapshots, artifacts, and usage when available. |
| Branch prompt generator | Convert issue-tree node into 500-900 word research brief. |

## Workstream C: Dynamic Specification

Goal: make the system flexible across public company diligence, industry landscapes, technical research, legal research, scientific review, and custom consulting tasks.

Priority tasks:

| Task | Outcome |
| --- | --- |
| Dynamic lens selector | Select 2-5 lenses from problem characteristics. |
| Clarification gate | Ask user when ambiguity changes issue tree or provider budget. |
| Research plan review | Human approves or edits tree and provider allocation before launch. |
| Depth/config profile | Light, standard, deep, and custom operator toggles. |

## Workstream D: Synthesis And Evaluation

Goal: produce useful output without melting usage.

Priority tasks:

| Task | Outcome |
| --- | --- |
| Narrative synthesis layer | Convert reports/evidence into thesis, branch summaries, contested claims, and gaps. |
| Claim clustering | Reduce all-claims fanout into issue bundles. |
| Staged evaluator | Deterministic checks first, cheap rubric second, frontier judges only for high-risk outputs. |
| Gap-driven next wave | Recommend next research jobs only when coverage gaps matter. |

## Workstream E: Deterministic Financials

Goal: support public company financial workflows without unnecessary Deep Research.

Priority tasks:

| Task | Outcome |
| --- | --- |
| SEC source bundle | Pull filings and company facts into durable source artifacts. |
| Statement extraction | Parse income statement, balance sheet, cash flow, and segment data. |
| Workbook generator | Create editable workbook with formulas, source links, and audit tab. |
| Narrative analysis | Generate brief that cites workbook cells and filings. |

## Operating Rules

| Rule | Reason |
| --- | --- |
| Public data only until firm approval. | Avoid client confidentiality exposure. |
| Subscription-first provider routing. | Matches owner cost constraint. |
| No full pipeline retries for debugging. | Use artifacts and vertical slices to avoid melting usage. |
| Every expensive provider action writes an artifact. | Enables resume, audit, and provider switching. |
| Human approves issue tree and research plan in early versions. | Prevents expensive research on wrong scope. |
| Manual upload remains supported. | It is the reliability fallback for browser automation and the fastest first slice. |

## Success Criteria

| Criterion | Required proof |
| --- | --- |
| Issue tree works | Dynamic issue tree for 3 different prompt types passes human review. |
| Research acquisition works | At least one ChatGPT and one Claude public research report are ingested through the same contract. |
| Citation integrity works | Every final factual claim has source refs or explicit unsourced flag. |
| Synthesis works | Output contains thesis, branch summaries, contested claims, gaps, and next-wave recommendation. |
| Cost is controlled | Run ledger shows provider calls, elapsed time, and usage where available. |
| Resume works | A run can stop after research acquisition and resume from artifacts. |
| Deliverable is useful | Produces a brief that a consultant can read without inspecting raw JSON claims. |

