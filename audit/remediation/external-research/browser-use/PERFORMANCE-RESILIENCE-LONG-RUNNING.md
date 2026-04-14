# Browser Use: Performance, Resilience, and Long-Running Agent Behavior

## Scope

This pass focused on Browser Use's runtime behavior for long workflows, especially:

- retries
- `fallback_llm`
- planning and replanning
- loop detection
- prompt/history compaction
- step/history/state persistence
- browser/session resilience
- timeouts
- replay/rerun behavior

Primary source inspected: Browser Use OSS repo at `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use`.

## Bottom Line

Browser Use has more real architectural value than "LLM + browser clicks."

The strongest reusable value is not its evidence model or citation system. It is the agent runtime around browser work:

- bounded step loop with explicit state
- resumable/persistable history
- prompt compaction with safeguards against false completion
- soft loop detection and replanning nudges
- browser-session auto-reconnect
- auth/storage/download persistence
- action-sequence guards against stale-page execution
- replay/rerun machinery with retry/backoff and redundant-retry skipping

For a Keystone or Perplexity-like deep research product, these are meaningful patterns. They suggest Browser Use is more than a site automation layer. But they still do **not** make it a governed retrieval runtime by themselves.

## Serious Architectural Value

### 1. Explicit long-running agent state machine

Browser Use keeps durable run state in a way that is actually useful for nontrivial workflows.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:59`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:251`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:2483`

Notable details:

- `AgentSettings` carries explicit limits for `max_failures`, `llm_timeout`, `step_timeout`, `max_actions_per_step`, planning, loop detection, and compaction.
- `AgentState` persists `n_steps`, `consecutive_failures`, plan state, pause/stop flags, message-manager state, filesystem state, and loop-detector state.
- `run()` is a bounded step loop, defaulting to `max_steps=500`, with pause/resume, interruption handling, finalization, and terminal stop conditions.

Why this matters:

- This is a real reusable orchestration shape for deep research systems.
- Keystone already has richer governed abstractions, but Browser Use shows a practical browser-task runtime with explicit pause/restart-friendly state.

### 2. Message/history compaction is one of the best reusable patterns here

The compaction path is more thoughtful than a naive "summarize chat history" trick.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:35`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/message_manager/service.py:213`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/message_manager/service.py:259`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tools/views.py:89`

What it does:

- Compaction triggers on both cadence and size: every `compact_every_n_steps` and only after history crosses a char threshold.
- It preserves prior compacted memory, current agent history, and optionally one-step read-state.
- The compaction prompt explicitly says to mark steps as complete only if success was explicitly confirmed, otherwise mark them `IN-PROGRESS`.
- After compaction it keeps the first history item plus the most recent `keep_last_items`.
- `done` schema also warns the model not to claim completion from `compacted_memory` unless re-verified.

Why this matters:

- This is one of the most directly reusable patterns for long-horizon research agents.
- It is especially relevant for products that need to keep working after 50-200 steps without silently hallucinating what was already done.

Limit:

- This is still LLM summarization, not deterministic checkpointing.
- It reduces context blow-up, but it does not create a canonical evidence ledger.

### 3. Action-loop detection is soft but well designed

Loop control is not just prompt advice; there is concrete runtime tracking.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:95`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:157`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1484`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/tests/ci/test_action_loop_detection.py:1`

What it does:

- Normalizes actions into stable hashes.
- Search queries are normalized by token set, so superficial keyword order changes do not bypass loop detection.
- Tracks repeated action hashes over a rolling window and separately tracks stagnant page fingerprints.
- Injects escalating nudges at repeated-action thresholds and stagnant-page thresholds.

Why this matters:

- For open-ended web research, loop-breaking is a first-class operational problem.
- The normalization strategy is smarter than raw string matching and could be reused elsewhere.

Limit:

- It only nudges; it does not hard-stop the loop.
- This is a guardrail for model behavior, not deterministic control.

### 4. Planning/replanning is lightweight but valuable

Planning is integrated into the output schema and state loop, not bolted on after the fact.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:388`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1405`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1452`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/system_prompts/system_prompt_no_thinking.md:99`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/tests/ci/test_agent_planning.py:1`

What it does:

- `AgentOutput` can emit `plan_update` and `current_plan_item`.
- Runtime stores plan items and status markers.
- The agent injects replanning nudges after consecutive failures and exploration nudges after too many planless steps.
- Plan rendering is fed back into agent context with `[x]`, `[>]`, `[ ]`, `[-]` markers.

Why this matters:

- This is a useful pattern for deep research products that need to preserve progress through uncertain site exploration.
- It gives a middle ground between no plan and a heavyweight planner.

Limit:

- This is model-authored plan text, not a robust task graph or dependency engine.
- Flash mode disables planning entirely.

### 5. Multi-action stale-page protection is genuinely useful

Browser Use explicitly protects against continuing an action queue after the page has changed.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:2696`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tools/service.py:413`

What it does:

- Some actions are tagged `terminates_sequence=True`, such as navigation/search/go-back/switch.
- Even without static tags, runtime compares pre-action and post-action URL/focus target and aborts the remaining queued actions if the page changed.

Why this matters:

- This is a good anti-footgun pattern for browser agents.
- It reduces stale-element and stale-context cascades in multi-action steps.

### 6. Browser session recovery is more substantial than I expected

There is real browser/session resilience here, especially around reconnects.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py:537`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py:2032`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py:2120`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1256`

What it does:

- Tracks reconnect state and exposes `RECONNECT_WAIT_TIMEOUT`.
- Detects dropped CDP WebSocket handler tasks and launches auto-reconnect.
- Reconnect sequence recreates the CDP client, session manager, auto-attach, target discovery, focus restoration, and proxy auth hooks.
- Agent step error handling is reconnect-aware and waits for reconnect before declaring failure.

Why this matters:

- For long-lived browser tasks, CDP disconnects are common enough to matter.
- This is meaningful infrastructure value beyond "single page automation."

Limit:

- This is still session-level recovery, not durable cross-process distributed recovery.

### 7. Storage, auth, captcha wait, and downloads are operationally important

Several watchdogs materially help long workflows.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py:1561`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/storage_state_watchdog.py:25`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/captcha_watchdog.py:44`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/downloads_watchdog.py:1177`

What matters:

- `StorageStateWatchdog` loads/saves cookies and origin storage, merges state, and writes atomically.
- `CaptchaWatchdog` blocks the agent loop while a proxy-backed captcha solve is in progress, then injects outcome into memory.
- Downloads/PDF flows are tracked, deduplicated, and surfaced into agent-available files.

Why this matters:

- For authenticated or dynamic sites, this is a meaningful practical acquisition layer.
- This is exactly the sort of runtime hygiene a research product needs when it moves beyond simple public pages.

Important caveat:

- The captcha piece in OSS is mainly a wait/listener around externally solved captcha events, not a standalone local anti-bot breakthrough.

### 8. Rerun/replay is surprisingly strong and probably the most overlooked value

The replay subsystem is one of the most interesting parts for auditability and debugging.

Key refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:3073`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:3156`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:3173`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:3294`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/tests/ci/test_rerun_ai_summary.py:579`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/tests/ci/test_rerun_ai_summary.py:1057`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/tests/ci/test_rerun_ai_summary.py:1181`

What it does:

- Replays prior action histories with preserved step timing.
- Skips originally failed steps when asked.
- Detects redundant retry steps and skips them if a previous attempt already succeeded.
- Uses exponential backoff in rerun retries.
- Can wait for a minimum number of elements before matching on SPA-like pages.
- Produces an AI summary of rerun completion.

Why this matters:

- This is closer to "trace harness" value than raw automation value.
- For a research product, replay plus summarized audit traces can be very useful for regression analysis, demo reproducibility, and operational debugging.

Limit:

- It is not a governed evidence replay system.
- It replays browser behavior, not canonical source extraction semantics.

## Performance and Stability Patterns Worth Borrowing

### Good patterns

1. Separate short-lived read state from long-lived memory.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/message_manager/views.py:86`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/message_manager/service.py:301`

Why useful:

- One-step extracted content and images do not need to poison all future context.

2. Keep structured step history with screenshots and timing.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1725`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/views.py:595`

Why useful:

- This creates a strong debugging substrate even when the main agent loop remains non-deterministic.

3. Use budget warnings before hard exhaustion.

Ref:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1530`

Why useful:

- Deep research systems often fail badly at the very end. Warning before exhaustion is a simple, good pattern.

4. Retry small local failures where verification is cheap.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/service.py:1657`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/default_action_watchdog.py:1996`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/default_action_watchdog.py:3511`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tools/service.py:425`

Why useful:

- Empty action retry, form-input auto-correction, lazy-dropdown retry, and empty-DOM reload are all sensible "small retries" that avoid large orchestration complexity.

### Less mature or weaker than they first appear

1. Failure recovery is not deeply hierarchical.

There is:

- one empty-action retry
- one fallback-LLM switch
- step-level timeout handling
- reconnect handling
- some local action auto-retries

But there is **not** a sophisticated policy engine for:

- retry classes by failure type
- provider cascades beyond one fallback
- dynamic timeout adaptation
- adaptive browser strategy switching
- deterministic checkpoint rollback

2. Some resilience is mostly prompt policy.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/system_prompts/system_prompt_no_thinking.md:84`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/system_prompts/system_prompt_no_thinking.md:99`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/system_prompts/system_prompt_no_thinking.md:123`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/agent/system_prompts/system_prompt_no_thinking.md:221`

The prompts are thoughtful and operationally useful, but many guarantees remain behavioral rather than enforced.

3. Crash monitoring exists, but is not fully wired into the default session attachment path.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/watchdogs/crash_watchdog.py:38`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/browser/session.py:1584`

The `CrashWatchdog` is implemented, but its default attachment lines are commented out in `attach_all_watchdogs()`. Auto-reconnect is real; crash watchdog attachment appears less central in the default path than the raw implementation suggests.

4. Token/cost tracking is observability, not control.

Refs:

- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tokens/service.py:48`
- `/Users/jackriddle/Desktop/Keystone-Intelligence-Engine-browser-use-eval/browser-use/browser_use/tokens/service.py:388`

They track usage and pricing well enough for reporting, but they do not use this to adapt execution policy in any meaningful way.

## What Matters Most to Keystone or a Perplexity-Like Product

### Reusable patterns with real value

1. Prompt compaction with "confirmed success only" rules.
2. Soft loop detection using normalized action hashes and page fingerprints.
3. Browser session reconnect and focus restoration.
4. Separation of:
   - long-term memory
   - one-step read state
   - persistent files
   - step history
5. Sequence termination guards after navigation/page change.
6. Replay/rerun harness with backoff and redundant-retry skipping.
7. Storage/auth/download persistence around browser sessions.

### Likely value to Keystone specifically

Highest-value borrowable ideas:

- long-horizon browser task state model
- compaction discipline
- replay/regression harness ideas
- browser session resilience patterns
- operational file/download/auth/session persistence

Lower-value areas for Keystone:

- judge-on-trace as currently implemented
- prompt-only success verification rules
- generic browser-agent planning format
- token/cost reporting

## Does this change the Browser Use recommendation?

No. This deepens the case that Browser Use has **serious supplement value**, but it still does not make it a canonical governed retrieval engine.

Updated interpretation:

- Browser Use is more valuable than a mere automation library.
- The value is concentrated in fallback acquisition and agent runtime patterns.
- It still does not replace Keystone's governed evidence extraction, anchored citation contract, or deterministic retrieval path.

So the recommendation remains:

- Browser Use OSS/Cloud family: `FALLBACK_ONLY`
- additionally worth studying as a `BENCHMARK_OR_CONTROL_ARM_ONLY` style reference for browser-task runtime behavior

## Verification Note

I attempted to run focused Browser Use test suites for:

- fallback LLM behavior
- loop detection
- planning

The sandbox machine only exposes `/usr/bin/python3` at Python `3.9.6`, while Browser Use requires Python `>=3.11` per `pyproject.toml`. I installed some missing pytest dependencies in the sandbox, but package/test execution remained blocked by the Python-version mismatch, so the conclusions in this memo are based on source inspection plus test-file inspection rather than successful local test execution.
