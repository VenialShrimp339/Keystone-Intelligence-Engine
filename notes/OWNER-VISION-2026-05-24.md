# Owner Vision Notes - 2026-05-24

## July 27 Target

The target is a full operational Keystone system by July 27, 2026, the owner's start date at the firm. The issue-tree/specification engine is core product value and should be preserved. A research ingestion path can be built first as the fastest reliable spine, but it is not a replacement for the full autonomous issue-tree pipeline.

The system should not be optimized around a single demo query, market-sizing workflow, or business-only taxonomy. The intended product is a flexible research operating system that can handle consulting-style diligence, industry analysis, public-company financial work, engineering research, legal research, and the kind of meta-research that originally produced the Keystone Intelligence Engine architecture itself.

The issue tree must be dynamic and domain-adaptive. Hardcoded financial / operational / market lenses are considered a core brittleness source, because they fail when the task is not a classic business problem and can still fail inside business work when the right decomposition is subtler.

## Provider Direction

Claude should be removed as the primary runtime dependency for this system. OpenAI/ChatGPT should become the preferred provider path.

The owner strongly prefers using ChatGPT subscription capacity over paid OpenAI API calls where feasible, because the subscription limits are high and rarely reached. Paid OpenAI API usage is acceptable if needed for orchestration, parsing, evaluation, or other non-research calls, but it is not the preferred default.

Subscription-powered execution should be treated as the default design constraint, not as a fallback. When subscription-backed CLI or browser paths appear to lack API-like control, first investigate whether equivalent functionality can be recovered through Codex non-interactive mode, JSONL event streams, output schemas, access tokens, MCP, browser automation, local wrappers, or other integration surfaces. Escalate to paid API calls only when the subscription path is technically blocked, materially less reliable for the use case, or would take disproportionate engineering time.

The project should assume the desired subscription-first architecture is possible until proven otherwise by direct testing or authoritative documentation. Roadblocks should be treated as routing problems first.

For autonomous feasibility work, there is no artificial cap on subscription-backed ChatGPT or Claude usage. Experiments should still be information-gain driven: run enough probes to prove capabilities, rate limits, artifact extraction, and failure behavior, then stop.

## Research Acquisition Direction

Manual upload of Deep Research reports is acceptable for a first working version. Browser automation for ChatGPT or Claude web research remains strategically attractive and should be evaluated seriously, because it can access web-only subscription capabilities and high-usage models that may not be selectable through CLI paths.

Browser automation should be treated as a research acquisition backend that produces durable report artifacts for ingestion, not as a brittle replacement for Keystone's internal pipeline contracts.

The acquisition layer should support multiple task shapes. A broad diligence question may need issue-tree decomposition, multiple Deep Research branches, iterative follow-up, and synthesis. A financial extraction task may only need SEC filings, deterministic parsing, Excel modeling, and targeted analysis, with no broad web search. The system should infer the amount of research, tooling, compute, and human review appropriate to the task.

The system may automate both ChatGPT web and Claude web using the owner's logged-in browser sessions. ChatGPT and Claude should both remain available as research acquisition providers while the owner is paying for both plans, especially for parallel Deep Research capacity and rate-limit pooling. The constraint is likely provider-specific parallelism/rate limits rather than total monthly usage.

## Human-in-the-Loop Direction

The system should ask clarifying questions before launching expensive research when the task is ambiguous. It should also present the proposed research plan / issue tree for consultant approval before burning substantial compute or subscription usage. Human review of the issue tree is intentional product design, especially for complex consulting-style work where a wrong decomposition can waste the entire run.

Human checkpointing should be configurable. Some runs should operate in a guided mode that asks for approval after the issue tree and after major proposed research waves. Other runs should operate in a higher-autonomy mode once the user trusts the task framing. The long-term UI/settings surface should expose controls for research depth, number of deliberation rounds, number and type of judges, follow-up wave approval, provider/backends, output type, and compute budget.

## Output Direction

The eventual system should support multiple output forms: source-backed research brief, partner-ready PDF or memo, slide-ready outline, actual PowerPoint deck, and financial workbook / Excel model when the task requires quantitative extraction or modeling.

Financial outputs should eventually cover both lightweight analysis workbooks and more structured finance models. In this context, the useful distinction is not "consultant versus banker" but "how much modeling structure is required": clean extracted statements, KPI/cash-flow analysis, and formatted sensitivity views for many consulting workflows; full integrated DCF / three-statement / transaction-model style outputs only when the task actually requires that level of structure.

For the firm, adaptability is the core selling point. The first internal user is the owner / analyst workflow, but the system should eventually be understandable and valuable to nontechnical consultants.

## Runtime Expectations

There is no fixed wall-clock target. Quality and appropriate effort matter more than speed. An overnight run is acceptable for a genuinely complex week-of-consulting-work research task, while narrower tasks such as SEC financial extraction and modeling should complete much faster.

The system should route tasks by complexity and required evidence source rather than applying the full deep research pipeline to every request.

The operating instinct for this project should be: when a workflow is slow, expensive, brittle, or tedious, assume there is a faster and higher-quality architecture available and search for it before accepting the limitation. Do not treat visible roadblocks as definitive until alternative integration paths, automation strategies, or decomposition approaches have been tested.

## Naming

Keystone is the name of the consulting firm. "Keystone Intelligence Engine" is the current project name but is provisional and may be discarded later.

## Confidentiality Boundary

The current build should focus on public information workflows first: public-company diligence, SEC filings, industry research, competitor research, and other non-confidential sources. Client-confidential files should not be uploaded or processed through external systems until the owner has firm approval.

The architecture should still preserve a future path to confidential use by tracking data boundaries, training-data exposure risk, local-only storage options, provider/data-control assumptions, and clear separation between public-source runs and client-confidential runs.

## Collaboration Preference

When implementation work exposes uncertainty about product vision, consulting use cases, user workflow, acceptable automation tradeoffs, or what the firm would value, ask the owner directly rather than silently encoding assumptions.
