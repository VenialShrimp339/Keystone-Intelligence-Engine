# Reference Pattern Audit

Checked against public product/help materials on 2026-04-12.

## Comparison Table

| Product | Pattern worth borrowing | Why it helps Keystone | Do not copy blindly |
|---|---|---|---|
| ChatGPT | Familiar bottom composer, project/workspace continuity, editable research setup | Eases onboarding for free-ChatGPT users | Do not reuse unstable OpenAI labels or imply identical backend breadth |
| Claude | Clean chat-plus-artifact split, lightweight research mode, output pane | Strong model for keeping the answer separate from durable workpapers | Do not turn every intermediate into an "artifact" if it is not inspectable or reusable |
| Codex | Long-running task supervision, honest task lifecycle, resumable work | Best model for making background work visible without fake magic | Do not import developer-first jargon or terminal aesthetics |
| Gemini | Compact tool/source/file controls close to the composer | Good progressive disclosure pattern | Do not promise broad tool/source scope before Keystone truly supports it |
| Perplexity | Dense citations, source-first answer framing, source selection | Best model for truth-forward research UX | Do not mimic the search-engine skin or count discovery as evidence |
| NotebookLM | Bounded workspace mental model | Useful once file-bounded research becomes more real | Do not imply bounded-source rigor unless Keystone truly stays inside the bound |

## Highest-Value Patterns To Borrow

### 1. Source scope near the composer

Users should understand what kind of research Keystone is about to run before it starts. Source scope matters more than model branding.

### 2. A visible run, not a magic assistant message

Long-running work should become a run card with status, elapsed time, warnings, and resumability.

### 3. A right-side durable output pane

Chat should initiate and summarize. The brief, evidence, files, and artifacts should live in a secondary pane or drawer.

### 4. Uploads as first-class controls

Files should sit directly beside the composer, not behind settings. Uploaded files need honest usage labels such as `Attached`, `Used in run`, or `Not indexed`.

### 5. Dense citations and expandable source drawers

The answer should expose source references inline and let the user drill into files, web sources, and gaps without leaving the flow.

### 6. Simple visible controls, deeper optional controls

Normal users should choose only what they can understand: speed/depth, file input, maybe source scope. Advanced users can open a deeper panel for experimental or technical options.

## Patterns To Avoid

- Fake agent theater: pseudo-terminal streams, animated swarms, or "thinking" orbs with no inspectable truth behind them.
- Provider-badge theater: logo walls or source counts that make stub tools look real.
- One-click `Deep Research` if it still bypasses the governed path.
- Fancy confidence dials that outstate evaluator maturity.
- Export-grade report chrome that makes a partial or degraded run feel cleared.
- A dashboard that defaults to internal IDs, logs, and developer framing for nontechnical analysts.

## Keystone Implications

### Borrow

- ChatGPT familiarity.
- Claude's answer-vs-output separation.
- Codex's long-running work supervision.
- Perplexity's citation honesty.
- NotebookLM's bounded-workspace discipline once Keystone can back it up.

### Do Not Borrow

- Labels whose backend semantics do not match Keystone.
- Any progress pattern that outruns actual backend state.
- Any trust signal that collapses discovery, evidence, and validation into one green badge.

## Naming Guidance

Prefer:

- `Analysis`
- `Research Plan`
- `Review checkpoint`
- `Evidence`
- `Outputs`

Avoid:

- `Deep Research` as a default surface label
- `Canvas` unless it is truly editable/exportable
- `Artifact` as the primary user-facing noun
- `Verified` unless the exact verification boundary is stated

## Sources

- OpenAI Help: [Deep research in ChatGPT](https://help.openai.com/en/articles/10500283), [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt), [Apps in ChatGPT](https://help.openai.com/en/articles/11487775/), [Voice Mode FAQ](https://help.openai.com/en/articles/8400625-voice-mode), [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)
- OpenAI Product: [Introducing the Codex app](https://openai.com/index/introducing-the-codex-app/)
- Anthropic Help: [Using Research on Claude](https://support.claude.com/en/articles/11088861-using-research-on-claude), [What are artifacts and how do I use them?](https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them), [Create and edit files with Claude](https://support.claude.com/en/articles/12111783-create-and-edit-files-with-claude)
- Google Help: [Use Deep Research in Gemini Apps](https://support.google.com/gemini/answer/15719111?hl=en), [Upload and analyse files in Gemini Apps](https://support.google.com/gemini/answer/14903178?hl=en-SG), [Create docs, apps & more with Canvas](https://support.google.com/gemini/answer/16047321?co=GENIE.Platform%3DDesktop&hl=en), [Create a notebook in NotebookLM](https://support.google.com/notebooklm/answer/16206563)
- Perplexity Help: [What is Research mode?](https://www.perplexity.ai/help-center/en/articles/10738684-what-is-research-mode), [What is Pro Search?](https://www.perplexity.ai/help-center/en/articles/10352903-what-is-pro-search), [What are Spaces?](https://www.perplexity.ai/help-center/en/articles/10352961-what-are-spaces), [What is a Thread?](https://www.perplexity.ai/help-center/en/articles/10354769-what-is-a-thread), [Choose sources / Focus replacement](https://www.perplexity.ai/help-center/en/articles/10354759-why-can-t-i-see-focus-mode-on-my-search-bar)
