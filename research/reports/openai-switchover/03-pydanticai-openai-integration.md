# Migrating multi-agent AI from Anthropic to OpenAI with PydanticAI

**PydanticAI (v1.77.0, April 2026) fully abstracts the differences between Anthropic and OpenAI for tool definitions, structured output, and agent orchestration — making provider migration as simple as changing a model string.** The framework supports both OpenAI's Chat Completions and Responses APIs, OAuth bearer tokens via callable `api_key`, parallel tool calls, and cross-provider multi-agent delegation. The biggest migration friction comes from provider-specific model settings (caching, reasoning, built-in tools) that require manual translation. Below is the complete technical integration guide with working code.

---

## PydanticAI's OpenAI provider supports OAuth and both APIs

PydanticAI's `OpenAIProvider` accepts a custom `AsyncOpenAI` client, which is the entry point for all authentication customization. The provider exposes two model classes: **`OpenAIChatModel`** for Chat Completions and **`OpenAIResponsesModel`** for the Responses API.

### Passing an OAuth bearer token

The OpenAI Python SDK sends `Authorization: Bearer {api_key}` on every request. Since OAuth bearer tokens use the same header format, **set the OAuth token as `api_key`** — this is the cleanest approach. Since PR #2588 (merged September 2025), `api_key` also accepts a callable for automatic token refresh:

```python
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
import asyncio, time

class TokenManager:
    def __init__(self, refresh_fn, buffer_seconds=300):
        self._refresh_fn = refresh_fn
        self._buffer = buffer_seconds
        self._token = None
        self._expires_at = 0
        self._lock = asyncio.Lock()

    async def __call__(self) -> str:
        if time.time() < self._expires_at - self._buffer:
            return self._token
        async with self._lock:
            if time.time() < self._expires_at - self._buffer:
                return self._token  # Double-check after acquiring lock
            self._token, expires_in = await self._refresh_fn()
            self._expires_at = time.time() + expires_in
            return self._token

token_mgr = TokenManager(my_oauth_refresh_function, buffer_seconds=300)

# The callable is invoked before EVERY request — handles 30+ min sessions
client = AsyncOpenAI(api_key=token_mgr)
provider = OpenAIProvider(openai_client=client)
model = OpenAIResponsesModel('gpt-4.1', provider=provider)
agent = Agent(model, instructions='You are a helpful assistant.')
```

The `default_headers` parameter on `AsyncOpenAI` can technically override `Authorization`, but the SDK's internal `auth_headers` property may conflict — **using `api_key` directly (or as a callable) is the only reliable method**. For high-concurrency workloads, the `AsyncOpenAI` client is fully task-safe via its underlying `httpx.AsyncClient` connection pool (default 100 connections, configurable).

### Responses API vs Chat Completions

PydanticAI recommends `OpenAIResponsesModel` for new OpenAI integrations. The old `OpenAIModel` is a deprecated alias for `OpenAIChatModel`:

```python
# Responses API (recommended)
agent = Agent('openai-responses:gpt-4.1')

# Chat Completions API (legacy)
agent = Agent('openai:gpt-4.1')
```

The Responses API model exposes additional settings not available in Chat Completions: **`openai_builtin_tools`** (web search, file search, code interpreter), **`openai_previous_response_id`** for stateful multi-turn conversations, `openai_reasoning_summary`, and `openai_truncation`.

### Reasoning effort, structured output, and parallel tool calls

All three are fully supported. PydanticAI exposes `openai_reasoning_effort` for o-series and reasoning models, `NativeOutput` for JSON-schema structured output via `response_format`, and handles parallel tool calls with concurrent async execution by default:

```python
from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    categories: list[str]

agent = Agent(
    'openai-responses:o3',
    output_type=NativeOutput(AnalysisResult),  # Uses response_format JSON schema
    instructions='Analyze the input and return structured results.',
)

result = agent.run_sync(
    'Analyze recent trends in renewable energy adoption.',
    model_settings=OpenAIResponsesModelSettings(
        openai_reasoning_effort='high',
        openai_builtin_tools=[{'type': 'web_search'}],
        parallel_tool_calls=True,  # Default; set False to disable
    ),
)
print(result.output)  # AnalysisResult(summary='...', confidence=0.92, categories=[...])
```

For parallel tool calls, PydanticAI schedules all returned `tool_calls` concurrently using `asyncio.create_task`. You can force sequential execution per-tool with `sequential=True` on the decorator, or globally via `parallel_tool_calls=False` in model settings.

---

## The codex-auth package is community-built and not for production

The `codex-auth` package (v0.1.1, released March 3, 2026) exists on PyPI but is a **third-party community package by Yousef-Madboly, not an official OpenAI library**. It patches the OpenAI SDK to route requests through ChatGPT's consumer backend (`chatgpt.com/backend-api/codex/responses`), enabling ChatGPT Plus/Pro subscribers to use Codex models without an API key. The author explicitly states it is "for personal usage users, not for production."

The package works via a custom httpx transport that intercepts and rewrites requests:

```python
import codex_auth  # Monkey-patches the SDK on import
from openai import OpenAI

client = OpenAI()  # No API key needed — uses browser PKCE auth
response = client.responses.create(
    model="gpt-5.1-codex-mini",
    input="Write a Python function to sort a list.",
)
```

**For production OAuth integration, skip `codex-auth` entirely** and use the callable `api_key` pattern shown above. The official `openai-codex-sdk` (v0.1.11, by OpenAI) wraps the Codex CLI binary and supports `login_with_device_code()`, but it is designed for embedding the Codex agent, not for general API authentication. Related community packages include `oauth-codex` (v4.0.0) and `codex-open-client` (v0.2.2), both focused on consumer-tier access.

Token refresh during long sessions is best handled with a preemptive refresh strategy. The SDK calls `_refresh_api_key()` before each request (not on 401 failure), so the callable must return a valid token at call time. **401 errors are not automatically retried** by the SDK's retry logic. For streaming responses that may span minutes, refresh tokens proactively with a buffer (e.g., 5 minutes before expiry).

---

## OpenAI function calling: two formats, one strict mode engine

The critical format difference between the two APIs is structural. Chat Completions nests tool definitions inside a `function` key; the Responses API flattens them:

```python
# Chat Completions API format
chat_tool = {
    "type": "function",
    "function": {                          # <-- nested wrapper
        "name": "get_weather",
        "description": "Get weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": ["string", "null"], "enum": ["F", "C"]},
            },
            "required": ["location", "unit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}

# Responses API format
responses_tool = {
    "type": "function",
    "name": "get_weather",                  # <-- flat, no wrapper
    "description": "Get weather for a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string"},
            "unit": {"type": ["string", "null"], "enum": ["F", "C"]},
        },
        "required": ["location", "unit"],
        "additionalProperties": False,
    },
    "strict": True,
}
```

**Strict mode** (`"strict": true`) uses a Context-Free Grammar engine to guarantee schema adherence. It imposes specific constraints:

- **`additionalProperties`** must be `false` on every object
- **All properties must be in `required`** — optional fields are modeled as `"type": ["string", "null"]`
- **Supported**: `anyOf`, `$ref` (including recursive), `enum` (max 500 values), `const`, nested objects (max **5 levels**)
- **Not supported**: `allOf`, `oneOf`, `minimum`/`maximum`, `minLength`/`maxLength`, `pattern`, `format`, `default`
- **Limits**: max **100 total properties**, combined property/enum/const character count ≤ **15,000**

The `tool_choice` parameter controls invocation: `"auto"` (default), `"none"`, `"required"` (must call at least one tool), or `{"type": "function", "function": {"name": "specific_fn"}}`. There is **no hard upper limit** on tool count, though practical performance degrades with many tools.

Parallel tool calls return multiple entries in `tool_calls` (Chat Completions) or multiple `function_call` items in `output` (Responses API), each with a unique ID. Results must reference the matching `tool_call_id`/`call_id`. **Important caveat**: parallel function calling is disabled when built-in Responses API tools (web_search, etc.) are also configured.

---

## Responses API built-in tools and stateful conversations

The Responses API provides **10+ built-in tools** that execute server-side without custom code: `web_search`, `file_search`, `code_interpreter`, `computer_use`, `image_generation`, `mcp` (remote MCP servers), `apply_patch`, `shell`, `skills`, `local_shell`, and `tool_search`. These can be mixed with custom function tools in the same request:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModelSettings

agent = Agent(
    'openai-responses:gpt-4.1',
    instructions='Research topics using web search, then call analyze_data with findings.',
)

@agent.tool_plain
def analyze_data(findings: str, source_count: int) -> str:
    """Process research findings into structured analysis."""
    return f"Analyzed {source_count} sources: {findings[:200]}..."

result = agent.run_sync(
    'What are the latest advances in quantum error correction?',
    model_settings=OpenAIResponsesModelSettings(
        openai_builtin_tools=[{'type': 'web_search'}],  # Mixed with custom tools
    ),
)
```

For multi-turn stateful conversations, the Responses API offers two mechanisms. The `previous_response_id` approach chains responses with **30-day server-side storage**, and PydanticAI supports this via `openai_previous_response_id` (including `'auto'` mode). The newer Conversations API provides durable long-lived conversation objects without the 30-day TTL. **For reasoning models (o3, o4-mini, GPT-5+), using `previous_response_id` persists raw chain-of-thought tokens between turns** — improving intelligence and increasing cache hit rates. This capability has no Chat Completions equivalent.

Automatic prompt caching activates for prompts ≥ **1,024 tokens**, reducing time-to-first-token by up to 80% and offering significant token cost discounts. Static content (instructions, tool definitions) should be placed at the beginning of prompts for maximum cache hits. The `prompt_cache_retention` parameter can extend cache TTL to 24 hours.

---

## Migration checklist: what PydanticAI abstracts and what it doesn't

PydanticAI's core abstraction is robust. **Tool definitions, structured output, message history, streaming, and multi-agent delegation all work identically across providers.** You define tools as decorated Python functions, and PydanticAI generates the provider-specific JSON schema, handles argument parsing, and normalizes responses into provider-agnostic `ToolCallPart` / `ToolReturnPart` messages:

```python
import os
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, UsageLimits

MODEL = os.getenv('AI_MODEL', 'openai-responses:gpt-4.1')

class SearchResult(BaseModel):
    answer: str
    sources: list[str]

# Parent agent — works with ANY provider
research_agent = Agent(MODEL, output_type=SearchResult, instructions='Research topics thoroughly.')

# Child agent — can use a DIFFERENT provider
summarizer = Agent('anthropic:claude-sonnet-4-6', output_type=str)

@research_agent.tool
async def deep_summarize(ctx: RunContext, text: str) -> str:
    """Summarize complex text using a specialized model."""
    r = await summarizer.run(f'Summarize concisely: {text}', usage=ctx.usage)
    return r.output

result = research_agent.run_sync(
    'Explain CRISPR gene editing advances in 2025-2026',
    usage_limits=UsageLimits(request_limit=15, total_tokens_limit=50_000),
)
```

### What leaks through the abstraction

Despite strong provider-agnosticism, these differences require attention during migration:

- **Model settings are provider-specific.** Replace `AnthropicModelSettings` fields (`anthropic_cache_instructions`, `anthropic_thinking`, `anthropic_effort`) with OpenAI equivalents (`openai_reasoning_effort`, `openai_store`, `openai_builtin_tools`). The unified `thinking` parameter in base `ModelSettings` normalizes reasoning control across providers.
- **Built-in tools are not portable.** Anthropic's `MemoryTool` and container execution have no OpenAI equivalent. OpenAI's `FileSearchTool` and `ImageGenerationTool` have no Anthropic equivalent. Custom function tools (`@agent.tool`) work everywhere.
- **Caching strategies differ fundamentally.** Anthropic offers explicit `CachePoint` markers with fine-grained control (instructions, tools, messages). OpenAI uses automatic server-side caching with no explicit control beyond `prompt_cache_key` and `prompt_cache_retention`.
- **Usage details vary.** `result.usage().details` includes `cache_read_tokens`/`cache_write_tokens` for Anthropic versus `reasoning_tokens`/`cached_tokens` for OpenAI.
- **`provider_details` on responses** surface provider-specific metadata like `finish_reason: "tool_calls"` (OpenAI) vs `finish_reason: "tool_use"` (Anthropic).

### Quick-switch migration pattern

For the simplest migration path, use environment-driven model selection with a `FallbackModel` for resilience:

```python
from pydantic_ai import Agent
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.models.anthropic import AnthropicModel

# Production: OpenAI primary, Anthropic fallback
model = FallbackModel(
    OpenAIResponsesModel('gpt-4.1'),
    AnthropicModel('claude-sonnet-4-6'),
)
agent = Agent(model, instructions='...')

# Or override per-run:
result = agent.run_sync('Hello', model='openai-responses:gpt-4.1')
```

Message history from `result.all_messages()` uses PydanticAI's provider-agnostic format, so conversations started with Anthropic can theoretically continue with OpenAI — though `instructions` from prior agents are not replayed, and provider-specific thinking tokens are not transferable.

---

## Conclusion

The migration surface area is smaller than it appears. PydanticAI eliminates **100% of the tool definition and message format translation work** — the Chat Completions nested `function` wrapper vs Responses API flat format vs Anthropic's `input_schema` format is handled transparently. The real migration work concentrates in three areas: replacing provider-specific `ModelSettings` (especially caching and reasoning parameters), auditing built-in tool usage for portability, and implementing OAuth token management via the callable `api_key` pattern rather than any third-party auth library. For production systems, ignore `codex-auth` and use a `TokenManager` class with preemptive refresh and async locking. The Responses API's `previous_response_id` provides a meaningful intelligence and cost advantage for multi-turn agent workflows that has no Anthropic parallel — making it the strongest technical reason to migrate.