# Artifact Contracts

Date: 2026-05-24

## Purpose

Keystone needs durable artifacts between every expensive or brittle step. The current pipeline carries too much raw context through long LLM calls. Artifact contracts let the system pause, resume, inspect, retry, re-ingest, evaluate, and switch providers without rerunning upstream work.

The contracts below are implementation targets. They should be represented as Pydantic models and persisted as JSON with schema versioning.

## Contract Principles

| Principle | Requirement |
| --- | --- |
| Provider-neutral | A ChatGPT report, Claude report, manual upload, SEC filing, or API output should normalize into the same downstream contract when semantically equivalent. |
| Citation-first | Every factual claim must either carry source references or be marked as unsourced and downgraded. |
| Durable | Every artifact has a stable ID, path, provider provenance, timestamps, status, and parent IDs. |
| Inspectable | Operator and agent can inspect the artifact without replaying provider sessions. |
| Retryable | Failed provider jobs store enough state to retry with same prompt, altered provider, or narrowed scope. |
| Scope-aware | Artifacts know the issue-tree node, research branch, and user-approved scope they belong to. |

## Core Artifact Types

### RunLedger

Tracks the full engagement:

| Field | Meaning |
| --- | --- |
| `run_id` | Stable engagement/run ID. |
| `user_request` | Original user prompt. |
| `public_data_only` | Boolean safety flag for current phase. |
| `profile` | Light, standard, deep, or custom. |
| `status` | Draft, awaiting_user, running, failed, complete. |
| `artifact_ids` | All child artifact references. |
| `provider_events` | Provider job IDs and usage. |

### SpecificationArtifact

Captures the L0 output:

| Field | Meaning |
| --- | --- |
| `decision_context` | What decision or output the research informs. |
| `clarifying_questions` | Questions required before launch. |
| `issue_tree` | MECE tree nodes and rationale. |
| `lens_set` | Dynamic lenses selected and why. |
| `research_plan` | Branches, priorities, provider assignments. |
| `approval_status` | Awaiting, approved, rejected, revised. |

### IssueTreeNodeArtifact

Each node should be addressable:

| Field | Meaning |
| --- | --- |
| `node_id` | Stable node ID. |
| `parent_id` | Parent tree node. |
| `question` | Research question for the node. |
| `hypothesis` | Day-1 hypothesis or branch hypothesis. |
| `acceptance_criteria` | What good research must answer. |
| `disconfirming_evidence` | What would weaken the hypothesis. |
| `provider_budget` | Suggested depth, providers, and concurrency. |

### ProviderJobArtifact

Tracks a submitted or planned provider job:

| Field | Meaning |
| --- | --- |
| `provider` | `codex_exec`, `chatgpt_web`, `claude_web`, `openai_api`, etc. |
| `surface` | CLI, Chrome, API, manual upload. |
| `prompt` | Exact submitted prompt. |
| `input_artifact_ids` | Parent spec/report/source artifacts. |
| `status` | Planned, submitted, running, needs_user, complete, failed. |
| `state_snapshots` | Screenshots, DOM snapshots, logs, JSONL events. |
| `usage` | Tokens, task counts, provider counters, or unavailable. |

### ResearchReportArtifact

Canonical report from Deep Research, Claude Research, manual upload, API, or equivalent:

| Field | Meaning |
| --- | --- |
| `report_id` | Stable report ID. |
| `provider_job_id` | Provider job that produced it. |
| `source_format` | Markdown, HTML, PDF, copied DOM, text, JSON. |
| `raw_path` | Raw saved report. |
| `normalized_markdown_path` | Normalized report text. |
| `title` | Report title. |
| `summary` | Short abstract. |
| `sections` | Structured section hierarchy. |
| `citations` | Extracted source refs and URLs. |
| `claims` | Extracted claims with section and source refs. |
| `quality_flags` | Missing citations, weak sources, extraction warnings. |

### SourceBundleArtifact

For deterministic sources:

| Field | Meaning |
| --- | --- |
| `source_id` | Stable source ID. |
| `source_type` | SEC filing, article, PDF, dataset, web page, transcript. |
| `url` | Source URL if public. |
| `retrieved_at` | Timestamp. |
| `raw_path` | Raw source bytes/text. |
| `parsed_path` | Parsed text/table representation. |
| `source_metadata` | Company, filing type, date, author, publisher, etc. |
| `lineage` | Fetch method and parser. |

### EvidenceBundleArtifact

Normalized evidence passed downstream:

| Field | Meaning |
| --- | --- |
| `evidence_id` | Stable evidence bundle ID. |
| `issue_node_ids` | Issue tree nodes covered. |
| `claim_records` | Claim list with evidence refs. |
| `source_records` | Deduped source list. |
| `absence_records` | Things searched for but not found. |
| `coverage_map` | Coverage by issue-tree branch and acceptance criteria. |
| `conflict_map` | Claims that disagree or have weak support. |

### SynthesisArtifact

The missing bridge between research and deliberation:

| Field | Meaning |
| --- | --- |
| `thesis` | Current best answer. |
| `supporting_arguments` | Hierarchical argument tree. |
| `contested_claims` | Claims needing adversarial review. |
| `gap_questions` | Follow-up research questions. |
| `branch_summaries` | Issue-tree node summaries. |
| `confidence_map` | Claim and branch confidence. |

### EvaluationArtifact

Staged evaluation result:

| Field | Meaning |
| --- | --- |
| `target_artifact_id` | Artifact being evaluated. |
| `deterministic_checks` | Citation/source/number checks. |
| `rubric_scores` | Dimension scores where run. |
| `judge_outputs` | LLM judge outputs where run. |
| `pass_fail` | Result by gate. |
| `required_rework` | Specific remediation instructions. |

### DeliverableArtifact

Final or intermediate output:

| Field | Meaning |
| --- | --- |
| `deliverable_type` | Brief, deck, workbook, issue-tree package, memo. |
| `source_artifact_ids` | Inputs used. |
| `file_paths` | Generated artifact paths. |
| `citation_manifest_id` | Citation manifest used. |
| `status` | Draft, reviewed, final. |

## Minimum First Slice Contract Set

The first working slice only needs:

1. `RunLedger`
2. `SpecificationArtifact`
3. `ProviderJobArtifact`
4. `ResearchReportArtifact`
5. `EvidenceBundleArtifact`
6. `SynthesisArtifact`
7. `EvaluationArtifact`
8. `DeliverableArtifact`

This slice supports manual upload, ChatGPT/Claude browser automation, citation verification, synthesis, and one deliverable without requiring the full retrieval stack or full evaluator ensemble.

