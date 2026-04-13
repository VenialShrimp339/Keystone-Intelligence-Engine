# Design Principles

## 1. Truth Before Premium

The interface must never imply a cleaner runtime, stronger retrieval path, or more complete evaluator than the system actually has.

## 2. Chat Is The Launcher, Not The Truth Surface

The conversation starts the work and summarizes it. The durable truth lives in the run record, sources, gates, artifacts, and output bundle.

## 3. Familiar By Interaction, Not By Copying Labels

Borrow the calm composer, sidebar history, artifact pane, and citation habits of modern AI apps. Do not cargo-cult labels like `Deep Research`, `Canvas`, or `Artifacts` unless Keystone truly supports those behaviors.

## 4. Progressive Disclosure Is Mandatory

Default analyst mode should feel simple. Advanced analyst controls should reveal more choice and more visibility. Dev mode should expose raw internals. These are different layers, not one cluttered surface.

## 5. Scope Before Model

Users should choose the depth and scope of work in plain English before they ever see model or backend choices.

## 6. No Fake Progress

Every progress state must map to a real backend state. Show `Planning`, `Researching`, `Source check`, `Confidence review`, `Quality review`, or `Waiting for review`. Do not invent deterministic percent-complete signals.

## 7. Sources Are First-Class

Uploads, citations, evidence summaries, and source limitations should sit close to the main answer. Provenance cannot be hidden behind a polished final brief.

## 8. Review Checkpoints Must Feel Real

If the system pauses for human review, the UI should show the pause clearly and present the actual review materials. If the runtime skipped gates, the UI should say so plainly.

## 9. Confidence Must Stay Humble

Confidence labels should read like analyst judgment, not platform bravado. Separate confidence from coverage, and separate citation existence from claim support.

## 10. Failures, Gaps, And Exclusions Stay Visible

Dropped claims, unevaluated tasks, render exclusions, dead URLs, bypass flags, and review blockers are core parts of the run record. They are not edge cases to hide.

## 11. Analyst Language On Top, System Language Underneath

Prefer `Analysis`, `Research Plan`, `Review checkpoint`, `Evidence strength`, and `Outputs` on the main surface. Keep `task_id`, `CIT-*`, `CAN-*`, model tiers, and audit terms in advanced or dev layers.

## 12. Design From Real Artifacts First

The UI should wrap the artifacts and seams that already exist: event stream, HITL API, markdown brief, JSON bundle, and wiki storage. Do not design around future-only capabilities as if they are already stable.

## 13. Experimental Must Look Experimental

Any bypass, preview, or benchmark-only path needs explicit labeling at entry, during the run, and in history.

## 14. Calm Default, Deep Optionality

The top-level experience should feel composed and premium, but the deeper layers should allow serious inspection for analysts, reviewers, and developers.
