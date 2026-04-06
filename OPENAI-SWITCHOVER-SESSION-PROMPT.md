# Prompt for the Existing Claude Code Session

Paste the following into the Claude Code session that did the audit work:

---

New task, major strategic shift. The Cowork session has been researching a provider migration from Anthropic to OpenAI. The short version: Anthropic killed third-party harness OAuth on April 4, and Jack requires zero per-token API costs, so we're moving to OpenAI's Codex OAuth path (ChatGPT Pro subscription, $200/month, flat rate). This affects every component you audited.

Two files to read first:

1. `OPENAI-SWITCHOVER-HANDOFF.md` — Contains all the context from the Cowork session: why we're switching, the current GPT-5.4 model landscape, a new "Responses API" architectural consideration, every provider-sensitive file in the codebase mapped by tier, and the four architecture decisions you need to resolve. Read this completely before doing anything else.

2. `OPENAI-SWITCHOVER-RESEARCH-PROMPTS.md` — Contains the prompts that generated the research reports, plus an Implementation Scoping section at the bottom that maps every research question to specific codebase files. Read the Implementation Scoping section carefully.

Then: find the four most recent files in `~/Downloads/`. These are research reports Jack ran from those prompts — covering Codex OAuth model access/quotas, GPT-5.4 behavioral differences, PydanticAI+OpenAI integration, and Responses API architecture. Copy them into `research-reports/openai-switchover/` with clear names, then read and analyze all four.

Your deliverable: `OPENAI-SWITCHOVER-PLAN.md` as specified in the handoff doc (Steps 2-5). Synthesize the research findings against your existing codebase knowledge. Resolve the four architecture decisions with evidence. Produce an ordered implementation plan with specific files and changes. Validate against Jack's directives.

Take your time with this. Read everything before writing anything. This is bigger than any single component.

---
