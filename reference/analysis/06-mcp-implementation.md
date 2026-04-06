# nano-claude-code: MCP Implementation Analysis

**Source:** `reference/nano-claude-code/mcp/`
**Scope:** MCP client architecture, transport layer, tool registration, and configuration -- reference for Keystone's MCP Gateway (Component #4)
**Date:** 2026-04-05

---

## Summary Verdict

nano-claude-code contains a complete, working MCP client implementation covering three transports (stdio, SSE, HTTP), lifecycle management, tool registration, and auto-reconnect. This is the most directly adoptable module in the codebase. The MCPManager singleton, qualified tool naming, and background initialization patterns are all ADOPT without modification. The gaps are production concerns (rate limiting, caching, cost tracking) that nano-claude-code never needed -- all must be built from scratch for Keystone. The reference implementation saves several weeks of protocol implementation work.

---

## Module Map

| File | Lines | Purpose |
|---|---|---|
| `mcp/types.py` | 125 | Transport enum, server config, connection state, tool schema |
| `mcp/client.py` | 547 | Transport implementations, MCPClient lifecycle, MCPManager singleton |
| `mcp/config.py` | 134 | Config loading from user + project .mcp.json files |
| `mcp/tools.py` | 132 | Tool registration, ToolDef wrapping, idempotent initialization |

---

## 1. Type System (`mcp/types.py`, lines 1-125)

### Transport Enum

```python
# mcp/types.py
class MCPTransport(Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WS = "ws"   # defined but not implemented
```

Three transports implemented; WebSocket is stubbed. For Keystone's 8 target services, all will use stdio (local Python MCP packages) or SSE (hosted services). HTTP is available as fallback. ✅ Verified from source.

### MCPServerConfig

```python
# mcp/types.py
@dataclass
class MCPServerConfig:
    name: str
    transport: MCPTransport
    # stdio fields:
    command: str | None         # e.g., "uvx" or "python"
    args: list[str]             # e.g., ["exa-mcp-server"]
    env: dict[str, str]         # e.g., {"EXA_API_KEY": "..."}
    # sse/http fields:
    url: str | None
    headers: dict[str, str]
    # shared:
    timeout: int                # default 30 seconds
    disabled: bool              # skip this server at startup
```

The `disabled` flag allows servers to be declared in config but not connected. Useful for staging environments or temporarily disabling a rate-limited provider. ✅ Verified from source.

### MCPServerState

```python
# mcp/types.py
class MCPServerState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
```

Four states. ERROR is a terminal state in this implementation -- the auto-reconnect logic in MCPClient resets to DISCONNECTED before retrying. ✅ Verified from source.

### MCPTool

```python
# mcp/types.py
@dataclass
class MCPTool:
    server_name: str
    tool_name: str
    qualified_name: str         # "mcp__server__tool"
    description: str
    input_schema: dict          # JSON Schema for tool inputs
    read_only: bool             # from server annotations
```

The `qualified_name` pattern (`mcp__exa__search`, `mcp__firecrawl__scrape`) prevents namespace collisions when multiple servers expose tools with identical names (e.g., three servers all exposing `search`). ✅ Verified from source.

### to_tool_schema()

```python
# mcp/types.py: MCPTool.to_tool_schema()
# Returns Claude API-compatible tool schema dict
# Prepends "[MCP:server_name] " to description
# The prefix makes MCP tools visually distinct in Claude's tool list
```

The `[MCP:server]` prefix in descriptions allows agents to distinguish native tools from MCP tools at a glance. 🟡 Inferred: primarily a debugging affordance, not a protocol requirement.

### JSON-RPC 2.0 Helpers

```python
# mcp/types.py
def make_request(method: str, params: dict, id: int) -> dict:
    return {"jsonrpc": "2.0", "method": method, "params": params, "id": id}

def make_notification(method: str, params: dict) -> dict:
    return {"jsonrpc": "2.0", "method": method, "params": params}
    # no id field -- notifications don't expect a response
```

Protocol version: `"2024-11-05"`. This is the stable MCP spec version. ✅ Verified from source.

---

## 2. Client and Transport Layer (`mcp/client.py`, lines 1-547)

### StdioTransport

```python
# mcp/client.py: StdioTransport
# Spawns subprocess via subprocess.Popen
# Communication: subprocess.stdin (write) / subprocess.stdout (read)
# Protocol: newline-delimited JSON-RPC messages
# Background threads:
#   _read_loop: reads stdout, matches responses to pending requests by ID
#   _stderr_loop: captures and logs stderr (server errors, debug output)
# Request synchronization: threading.Event per pending request
```

The `_read_loop` is a background thread that continuously reads server stdout and routes responses to waiting callers via threading.Event. A caller blocks on `event.wait(timeout=self.timeout)` after sending a request. The background thread sets the event when the matching response ID arrives. ✅ Verified pattern -- this is standard IO multiplexing for subprocess communication.

**Error handling:** If the subprocess dies, `_read_loop` exits and pending events will timeout. The MCPClient auto-reconnect catches this via the connection state machine.

### HttpTransport (SSE mode)

```python
# mcp/client.py: HttpTransport (SSE mode)
# Step 1: GET /sse -- opens SSE stream, waits for 'endpoint' event
# Step 2: Extract session URL from 'endpoint' event data
# Step 3: POST messages to session URL
# Step 4: Read responses from SSE stream (server-sent events)
```

SSE mode is a two-channel protocol: requests go out via POST, responses come back via the SSE stream. The session URL from the 'endpoint' event ties the two channels together. ✅ Verified from source.

**HTTP mode** (non-SSE): direct POST to the server URL, synchronous request-response. Simpler but does not support streaming responses from the MCP server. 🟡 Inferred: HTTP mode is for simple MCP servers that don't need streaming.

### MCPClient Lifecycle

```python
# mcp/client.py: MCPClient
def connect(self):
    self.state = CONNECTING
    self._transport = self._make_transport()
    self._transport.start()
    self._handshake()
    self.state = CONNECTED

def _handshake(self):
    # Send: initialize request with INIT_PARAMS
    # Receive: serverInfo, capabilities
    # Send: notifications/initialized (no response expected)
```

The handshake is a three-message sequence: initialize request → server capabilities response → initialized notification. This is the standard MCP protocol handshake. ✅ Verified from source.

### list_tools() and call_tool()

```python
# mcp/client.py: MCPClient
def list_tools(self) -> list[MCPTool]:
    # Sends tools/list request
    # Caches result as MCPTool objects
    # Sanitizes qualified names (replaces non-alphanumeric with _)

def call_tool(self, tool_name: str, inputs: dict) -> list[ContentBlock]:
    # Sends tools/call request
    # Collects text/image/resource content blocks
    # Returns structured content, not raw JSON
```

Tool discovery is cached after the first `list_tools()` call. Subsequent calls use the cache without a network round-trip. Cache invalidation is not implemented -- if a server adds tools after connection, the cache is stale. ⚠️ Not a concern for Keystone's static tool set; would matter if servers hot-reload their tool lists.

### Auto-Reconnect

```python
# mcp/client.py: MCPClient
# On call_tool() or list_tools():
#   if state != CONNECTED:
#     attempt reconnect (up to N retries with backoff)
#     if reconnect fails: raise MCPConnectionError
```

Auto-reconnect is triggered at the call site, not proactively. A server that drops between tool calls will be reconnected on the next call. For research sessions that run 30-60 minutes, connections will drop. The auto-reconnect handles this transparently. ✅ Critical for Keystone's long research sessions.

### MCPManager Singleton

```python
# mcp/client.py: MCPManager
class MCPManager:
    _instance: MCPManager | None = None  # singleton

    def connect_all(self, configs: list[MCPServerConfig]):
        # Connects each server sequentially
        # Logs success/failure per server
        # Continues on failure (partial connectivity is acceptable)

    def all_tools(self) -> list[MCPTool]:
        # Aggregates tools from all connected servers
        # Deduplicates by qualified_name

    def call_tool(self, qualified_name: str, inputs: dict):
        # Parses "mcp__server__tool" into server + tool
        # Dispatches to correct MCPClient instance
```

The singleton pattern means there is one shared MCPManager for the entire process. All agents in the same process share the same pool of MCP connections. For Keystone's parallel L1 research agents running in a single process, this is the correct architecture -- we want 5 connections to Exa, not 25. ✅ Verified pattern.

**Thread safety:** MCPClient instances are accessed concurrently by multiple agent threads. The threading.Event synchronization per request handles concurrent calls to the same server. 🟡 Inferred thread safety -- concurrent calls are supported by the response-ID matching in _read_loop.

---

## 3. Configuration (`mcp/config.py`, lines 1-134)

### Two Config Sources

```python
# mcp/config.py
# User config: ~/.nano_claude/mcp.json
# Project config: .mcp.json (walks up 10 directories from cwd)
# Project overrides user by server name (same name = project wins)
```

### Config Format

```json
{
  "mcpServers": {
    "exa": {
      "type": "stdio",
      "command": "uvx",
      "args": ["exa-mcp-server"],
      "env": {"EXA_API_KEY": "${EXA_API_KEY}"}
    },
    "firecrawl": {
      "type": "stdio",
      "command": "uvx",
      "args": ["firecrawl-mcp"],
      "env": {"FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}"}
    }
  }
}
```

Environment variable substitution in `env` values is handled at connection time. API keys stay in environment variables, not hardcoded in config files. ✅ Verified pattern.

### Runtime Management

```python
# mcp/config.py
add_server_to_user_config(name, config_dict)   # writes to ~/.nano_claude/mcp.json
remove_server_from_user_config(name)           # removes by name
```

Runtime additions persist across sessions via the user config file. No project-level runtime management -- project config is file-based only. 🟡 Inferred: the distinction is intentional -- user-level tools are permanent installs, project-level tools are engagement-specific.

---

## 4. Tool Registration (`mcp/tools.py`, lines 1-132)

### _make_mcp_func() Closure

```python
# mcp/tools.py: _make_mcp_func(qualified_name)
def _make_mcp_func(qualified_name: str):
    def mcp_func(**inputs) -> str:
        result = MCPManager.instance().call_tool(qualified_name, inputs)
        return format_content_blocks(result)
    return mcp_func
```

Each MCP tool gets a dedicated closure that captures its qualified name. The closure is the callable registered as a ToolDef. When the agent invokes the tool, it calls the closure, which dispatches through MCPManager. ✅ This is the correct factory pattern for dynamic tool registration.

### _register_tool()

```python
# mcp/tools.py: _register_tool(mcp_tool: MCPTool)
# Creates ToolDef from MCPTool schema
# Wraps _make_mcp_func closure as the callable
# Registers in central tool registry
```

MCP tools and native tools share the same registry after registration. The agent loop sees no distinction. ✅ Verified -- tool dispatch is unified regardless of tool origin.

### initialize_mcp() -- Idempotent Startup

```python
# mcp/tools.py: initialize_mcp()
# Loads configs from both sources
# Adds servers to MCPManager
# Calls connect_all()
# Registers tools from connected servers
# IDEMPOTENT: safe to call multiple times; skips already-connected servers
```

Idempotency means `initialize_mcp()` can be called at any point without causing duplicate connections. ✅ Verified from source.

### Background Auto-Initialization

```python
# mcp/tools.py: module-level
_init_thread = threading.Thread(target=_background_init, daemon=True)
_init_thread.start()
```

MCP connection starts at module import time in a background thread. By the time the user sends the first message, MCP servers are usually already connected. If they aren't, the agent loop waits on the first tool call. ✅ Verified pattern -- this is the correct non-blocking startup approach for services with meaningful connection latency.

---

## Keystone Layer Connections

### MCP Gateway (Component #4, no dependencies)

The MCP Gateway is one of Keystone's four parallel first builds. nano-claude-code provides a complete reference implementation. Keystone's 8 target services and their transport types:

| Service | Transport | MCP Package |
|---|---|---|
| Exa | stdio | `exa-mcp-server` (uvx) |
| Brave Search | stdio | `brave-search-mcp` |
| Firecrawl | stdio | `firecrawl-mcp` |
| Tavily | stdio | `tavily-mcp` |
| EdgarTools | stdio | Custom build |
| CrossRef | stdio or HTTP | Custom build |
| Semantic Scholar | HTTP | Direct API (no MCP package) |
| OpenAlex | HTTP | Direct API (no MCP package) |

For services without existing MCP packages, nano-claude-code's HttpTransport handles direct API calls wrapped in the MCP protocol. Alternatively, we build thin MCP servers for Semantic Scholar and OpenAlex using the `mcp` Python SDK.

**Deployment configuration** (`.mcp.json` in engagement root):

```json
{
  "mcpServers": {
    "exa": {"type": "stdio", "command": "uvx", "args": ["exa-mcp-server"]},
    "firecrawl": {"type": "stdio", "command": "uvx", "args": ["firecrawl-mcp"]},
    "brave": {"type": "stdio", "command": "uvx", "args": ["brave-search-mcp"]},
    "edgar": {"type": "stdio", "command": "python", "args": ["-m", "keystone_edgar_mcp"]},
    "crossref": {"type": "http", "url": "https://api.crossref.org/works"},
    "semantic_scholar": {"type": "http", "url": "https://api.semanticscholar.org/graph/v1"}
  }
}
```

### L1 -- Research Agent Tool Access

L1 research agents access all MCP tools through the unified registry. The `read_only` flag on MCPTool maps to Keystone's tool safety model:

- Read-only tools (search, fetch, retrieve): available to all L1 agents, auto-approved
- Write tools (if any): not exposed to L1 agents, require L2/L3 agent context

The agent permission gate from `agent.py` handles this automatically when L1 agents run with `permission_mode="read_only"`. ✅ Direct integration with pattern from `01-core-architecture.md`.

### L1 -- CitationProcessor

The CitationProcessor needs to call Firecrawl (URL verification) and CrossRef (DOI resolution) after L1 agents complete their research. These are the same MCP tools L1 agents use, accessed through the same MCPManager. The CitationProcessor runs as a distinct agent with access to the subset of tools it needs -- URL verification, not broad web search.

Tool access is scoped at agent initialization, not at the registry level. The CitationProcessor's config specifies `allowed_tools: ["mcp__firecrawl__scrape", "mcp__crossref__lookup"]`. ⚠️ nano-claude-code has no per-agent tool allowlist -- all registered tools are available to all agents. We must add tool scoping at the agent config level.

### L0 -- Specification Engine Tool Discovery

L0 needs to know what research tools are available before generating a RESEARCH.md spec. `MCPManager.all_tools()` returns the full tool manifest. L0 can use this to select appropriate tools per research subtask:

```python
# L0 tool selection for RESEARCH.md generation
available_tools = MCPManager.instance().all_tools()
academic_tools = [t for t in available_tools if "scholar" in t.server_name or "crossref" in t.server_name]
web_tools = [t for t in available_tools if t.server_name in ("exa", "brave", "firecrawl")]
financial_tools = [t for t in available_tools if t.server_name in ("edgar", "tavily")]
```

The RESEARCH.md spec assigns specific tool subsets to each research subtask based on the question type. This prevents all agents from hammering Exa when some subtasks need academic sources. 🟡 Inferred as the correct L0 behavior; not explicitly in CAPSTONE-PLAN-v2.md at this level of detail.

### META -- Trajectory Storage for Tool Calls

nano-claude-code logs MCP calls to stderr only (no structured logging). For Keystone's META layer self-improvement, every MCP tool call must be logged with:

- Tool qualified name
- Input parameters (truncated for PII)
- Latency (ms)
- Response size (bytes)
- Success or error
- Agent ID and task ID

This is not in nano-claude-code's MCPManager. We wrap `call_tool()` with a logging decorator:

```python
# Keystone extension to MCPManager.call_tool()
def call_tool(self, qualified_name: str, inputs: dict) -> list[ContentBlock]:
    start = time.monotonic()
    try:
        result = self._dispatch(qualified_name, inputs)
        self._log_call(qualified_name, inputs, result, latency=time.monotonic()-start)
        return result
    except Exception as e:
        self._log_error(qualified_name, inputs, e, latency=time.monotonic()-start)
        raise
```

Logs are written to the engagement's trajectory store (`.nano_claude/trajectories/{engagement}/mcp_calls.jsonl`). ✅ Required for DPVI iterate phase -- we cannot improve tool selection without knowing which tools are called and what they return.

---

## What We Need Beyond nano-claude-code

| Capability | Status in nano-claude-code | Keystone Build |
|---|---|---|
| Rate limiting per provider | Not implemented | Redis-based token bucket, per-server limits configurable in mcp.json |
| Request caching | Not implemented | Redis cache (TTL configurable per tool), pgvector for semantic dedup |
| Cost tracking per tool call | Not implemented | Per-call logging with provider cost tables, aggregated per engagement |
| Tool call trajectory logging | Not implemented | JSONL append to engagement trajectory store |
| Per-agent tool allowlists | Not implemented | Tool scoping at AgentConfig level, enforced at call time |
| Health check / monitoring | Basic alive check only | Prometheus metrics per server: latency p50/p95, error rate, call count |
| Concurrent connection limits | No limit | Per-server max_concurrent configurable, semaphore at MCPManager |
| Retry with exponential backoff | Auto-reconnect only | Configurable retry policy per server (max_retries, base_delay, max_delay) |

### Rate Limiting Design (Redis-based)

```python
# Keystone rate limiter wrapping MCPManager.call_tool()
class RateLimitedMCPManager:
    _rate_limits = {
        "exa": TokenBucket(rate=10, burst=20),          # 10 req/sec, burst 20
        "firecrawl": TokenBucket(rate=5, burst=10),
        "semantic_scholar": TokenBucket(rate=1, burst=3),
        "crossref": TokenBucket(rate=50, burst=100),
    }

    def call_tool(self, qualified_name: str, inputs: dict):
        server_name = qualified_name.split("__")[1]
        bucket = self._rate_limits.get(server_name)
        if bucket:
            bucket.acquire(timeout=30)  # blocks up to 30s, then raises
        return super().call_tool(qualified_name, inputs)
```

Rate limits are per-server because providers have different API quotas. The token bucket algorithm handles burst capacity correctly -- L1 agents starting simultaneously won't immediately exhaust Exa's quota. ⚠️ Rate limits must be tuned against actual provider SLAs before production deployment.

---

## Gap Analysis

| Gap | Severity | Fix |
|---|---|---|
| No rate limiting | HIGH -- parallel L1 agents will exhaust provider quotas | Redis token bucket per server |
| No request caching | HIGH -- same search query from multiple agents wastes money | Redis cache with configurable TTL |
| No cost tracking | HIGH -- no visibility into per-engagement research costs | Per-call logging with cost tables |
| No per-agent tool allowlists | MEDIUM -- all agents can call all tools | Tool scoping at AgentConfig level |
| No trajectory logging for tool calls | HIGH -- META layer cannot optimize without data | JSONL logging in call_tool() wrapper |
| WebSocket transport stubbed | LOW -- none of our target services require WS | Not needed for initial build |
| Tool cache not invalidated on server update | LOW -- our tool set is static | Not needed for initial build |
| No concurrent connection limits | MEDIUM -- runaway parallelism can saturate local resources | Semaphore per server in MCPManager |

---

## Verdict Summary

| Component | Source | Verdict | Keystone Layer |
|---|---|---|---|
| MCPClient with stdio/SSE/HTTP transports | `mcp/client.py` | ADOPT as reference -- do not rewrite | MCP Gateway |
| MCPManager singleton | `mcp/client.py` | ADOPT -- correct pattern for shared connection pool | MCP Gateway, L1 |
| Qualified tool naming (mcp__server__tool) | `mcp/types.py` | ADOPT -- prevents namespace collisions across 8 providers | All agents |
| Background initialization | `mcp/tools.py` | ADOPT -- non-blocking startup | MCP Gateway |
| Auto-reconnect on dropped connections | `mcp/client.py` | ADOPT -- critical for long research sessions | L1 |
| Config format (.mcp.json, two-source) | `mcp/config.py` | ADOPT -- clean separation of user vs. engagement config | MCP Gateway |
| _make_mcp_func closure pattern | `mcp/tools.py` | ADOPT -- correct factory for dynamic tool registration | MCP Gateway |
| Idempotent initialize_mcp() | `mcp/tools.py` | ADOPT | MCP Gateway |
| [MCP:server] prefix in descriptions | `mcp/types.py` | ADOPT for debugging clarity | All agents |
| read_only flag from server annotations | `mcp/types.py` | ADOPT -- maps to tool safety model | L1 isolation |
| Rate limiting | Not present | BUILD from scratch -- Redis token bucket | MCP Gateway |
| Request caching | Not present | BUILD from scratch -- Redis + pgvector | MCP Gateway |
| Cost tracking | Not present | BUILD from scratch -- per-call logging | META |
| Trajectory logging for tool calls | Not present | BUILD from scratch -- JSONL append | META |
| Per-agent tool allowlists | Not present | BUILD -- enforcement at AgentConfig | L1, L4 |
| Concurrent connection limits | Not present | BUILD -- semaphore at MCPManager | MCP Gateway |
