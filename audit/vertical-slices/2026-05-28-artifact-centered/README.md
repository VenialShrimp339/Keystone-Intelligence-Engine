# Artifact-Centered Vertical Slice

Date: 2026-05-28

Prompt: public PE diligence on Permira's take-private of Squarespace.

## Run

Command:

```bash
PYTHONPATH=src .venv/bin/python audit/vertical-slices/2026-05-28-artifact-centered/run_artifact_centered_slice.py
```

## What It Exercises

- Messy user request.
- Problem frame and issue-tree package.
- Candidate axes and selected-axis rationale.
- Approved pruned leaves as branch-level research prompts.
- Provider jobs through `BrowserProviderAdapter` using a fixture controller.
- ChatGPT route with Markdown body plus DOCX source-link path.
- Claude route with artifact/report export path.
- Provider ledger and completion-only export control.
- Report ingestion, source extraction, combined evidence bundle, synthesis, evaluation, and cited deliverable.

## Key Outputs

- Result manifest: `run/result.json`
- Provider ledger: `run/provider-ledger.json`
- Issue-tree package JSON: `run/issue-tree-package.json`
- Research tasks: `run/artifact-store/sqsp-permira-artifact-slice/files/research-tasks.json`
- Cited deliverable: `run/artifact-store/sqsp-permira-artifact-slice/files/deliverables/synthesis-evidence-combined-sqsp-permi-ef1d530508.md`
- Adversarial review: `ADVERSARIAL-REVIEW.md`

## Limitation

This is a realistic artifact slice, not a live browser automation proof. Provider jobs used a fixture controller and completed local reports. The next step is to replace the fixture controller with a logged-in Chrome/plugin controller that can submit jobs and trigger exports without manual downloading.
