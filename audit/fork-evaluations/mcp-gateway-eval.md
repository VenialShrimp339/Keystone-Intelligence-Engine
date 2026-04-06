# Fork Evaluation: vurgunhajiyev/mcp-gateway

**Evaluated:** 2026-04-05
**Evaluator:** Claude Opus 4.6
**Target Component:** #4 -- MCP Gateway
**Verdict:** EXTRACT

---

## 1. Repository Overview

| Property | Value |
|----------|-------|
| Language | Python 3.10+ |
| Framework | FastAPI + uvicorn + httpx |
| Total code | ~2,584 lines (Python) |
| License | pyproject.toml declares MIT, but **no LICENSE file exists** |
| First commit | 2026-02-28 |
| Total commits | 4 (1 meaningful, 1 test file, 1 merge, 1 unrelated) |
| Contributors | 1 |
| Stars/forks | Negligible (solo project) |
| Tests | 3 files: protocol validation (15 tests), circuit breaker (5 tests), integration (11 tests) |
| CI | GitHub Actions (ruff + mypy + pytest + safety + bandit + Docker build) |
| Dependencies | 21 runtime deps (FastAPI, httpx, Pydantic v2, pydantic-settings, PyJWT, redis, OpenTelemetry, structlog, tenacity, prometheus-client, etc.) |

### Architecture

The repo implements a standard API gateway pattern: FastAPI middleware stack (logging -> rate limiting -> auth) feeding into an MCP-specific JSON-RPC 2.0 router that proxies requests to configurable HTTP upstream servers. Includes agent registration with JWT session tokens, per-upstream circuit breakers, token-bucket rate limiting, and structured JSON access logging.

---

## 2. Requirement Coverage Matrix

| # | Our Requirement | mcp-gateway Coverage | Gap Severity |
|---|----------------|---------------------|--------------|
| 1 | Central router for all MCP tool calls | YES -- single `/mcp` endpoint handles all MCP methods, routes by method type and upstream | None |
| 2 | Per-agent tool authorization (structural) | PARTIAL -- has per-upstream authorization via `can_access(upstream_name)`. Controls which MCP *servers* an agent can reach, NOT which individual *tools* within a server | **Critical** -- our spec needs `agent.assigned_tools = ["exa_search", "brave_search"]` enforcement at tool granularity, not server granularity |
| 3 | Redis-backed rate limiting per provider | PARTIAL -- token-bucket rate limiter exists per-identity (per user/agent). `redis_url` config field is a stub; implementation is in-memory only. Rate limiting is per-caller, not per-provider (per-provider = "don't exceed Exa's API quota") | **High** -- both the Redis backend and the per-provider dimension are missing |
| 4 | Circuit breakers (3 failures -> open, 30s retry) | YES -- full CLOSED/OPEN/HALF_OPEN state machine with async locks. Defaults are 5/60s but configurable, so we'd set 3/30s | None (config change) |
| 5 | Audit logging (agent_id, tool, I/O hash, latency) | PARTIAL -- structlog access logging captures agent_id, method, status, latency_ms. Missing: input hash, output hash, tool name (only captures HTTP path), engagement_id | **Medium** -- access log pattern is sound but needs expansion to full tool-call audit |
| 6 | Tool registry with health checks | PARTIAL -- upstreams have health_check_path, `/readyz` probes them. But no dynamic tool registry, no individual tool schema storage, no transport_type or security_approved fields | **High** -- our tool registry needs per-tool metadata, not just per-server |
| 7 | stdio + HTTP MCP transport | NO -- HTTP-only reverse proxy. Proxy engine (`proxy.py`) constructs HTTP requests via httpx. No stdio subprocess management | **Critical** -- we need stdio for EdgarTools, FRED, doi-mcp. Retrofitting stdio into an HTTP proxy architecture is a deep refactor |
| 8 | Citation extraction from tool outputs | NO -- proxy passes through responses untouched | **High** -- needs new module |
| 9 | Max retry + dead-letter on all loops | PARTIAL -- tenacity retry with exponential backoff (3 attempts). No dead-letter path; exhausted retries return 502 | **Medium** -- retry exists, dead-letter is missing |
| 10 | Python / FastMCP compatibility | PARTIAL -- Python + Pydantic v2 + FastAPI (all compatible). But doesn't use FastMCP; implements its own MCP types. FastMCP provides strictly more (both transports, tool definition API, better protocol compliance) | **High** -- we'd be maintaining parallel MCP implementations instead of using FastMCP |

**Coverage summary:** 2 of 10 requirements fully met, 5 partially met, 3 completely absent.

---

## 3. Code Quality Assessment

### Strengths

- **Clean separation of concerns.** Modules map well to responsibilities (core/, protocol/, routing/, security/, middleware/, observability/).
- **Pydantic v2 throughout.** Config, MCP types, agent sessions all use Pydantic models. Matches our stack.
- **Async-native.** httpx + FastAPI + asyncio locks. No blocking calls.
- **Well-structured tests.** Protocol validation tests are thorough. Circuit breaker tests cover all state transitions.
- **Good middleware pattern.** The app factory in `core/app.py` with lifespan management is clean.

### Weaknesses

- **HTTP-only transport assumption is architectural.** The entire proxy engine (`proxy.py`, 201 lines) assumes upstream communication is HTTP request/response. Adding stdio support means either (a) a parallel code path that duplicates half the gateway logic, or (b) a deep refactor to abstract the transport layer. Neither is cheap.
- **No LICENSE file.** pyproject.toml declares MIT but that's metadata, not a legal grant. Cannot legally fork without a proper LICENSE file.
- **4 commits, 1 contributor.** No community, no review process, no maintenance track record. Any bugs are our bugs.
- **Dependency weight.** 21 runtime deps include OpenTelemetry (4 packages), prometheus-client, circuitbreaker (unused -- they rolled their own), orjson (imported in health.py but main router uses stdlib json). Several are dead weight.
- **Agent auth is session-based, not task-based.** Agent registers once, gets a 24h JWT, uses it for all requests. Our model: agents are spawned per-task with a specific tool allowlist that changes per research assignment.
- **Rate limiting dimension mismatch.** Their rate limiter answers "is this caller sending too many requests?" Our rate limiter needs to answer "are we sending too many requests to this provider's API?"

### Test Coverage

- Protocol validation: good coverage of happy + error paths
- Circuit breaker: covers all state transitions
- Integration tests: basic gateway lifecycle (health, auth, MCP initialize/ping/tools_list, agent registration)
- Missing: rate limiter tests, proxy/retry tests, concurrent access tests, error injection tests

---

## 4. Module Classification

| Module | Path | Lines | Classification | Rationale |
|--------|------|-------|---------------|-----------|
| MCP Types | `protocol/mcp_types.py` | 224 | SKIP | FastMCP provides better MCP type definitions with transport handling |
| Protocol Validator | `protocol/validator.py` | 121 | SKIP | FastMCP handles validation |
| MCP Router | `routing/mcp_router.py` | 273 | SKIP | Tightly coupled to HTTP proxy model; we need a different routing model |
| HTTP Proxy | `routing/proxy.py` | 201 | SKIP | HTTP-only; we need multi-transport |
| Circuit Breaker | `middleware/circuit_breaker.py` | 82 | **EXTRACT** | Clean state machine pattern. Port the async-lock-guarded CLOSED/OPEN/HALF_OPEN transitions. Adjust defaults to 3 failures / 30s |
| Rate Limiter | `middleware/rate_limiter.py` | 73 | **EXTRACT** | Token-bucket algorithm is solid. Port the bucket math, rewrite the middleware to be per-provider instead of per-identity, add Redis backend |
| Logging Middleware | `middleware/logging_mw.py` | 78 | **EXTRACT** | structlog JSON pattern + request context. Expand fields for tool-call audit |
| Auth Middleware | `security/auth.py` | 194 | SKIP | Session-based auth model doesn't match our task-based tool authorization |
| Agent Registry | `security/agent_registry.py` | 158 | SKIP | In-memory session store with JWT issuance. Our agents don't register externally |
| Config | `core/config.py` | 176 | **EXTRACT** | Pydantic Settings pattern with JSON file loading. Good template for our gateway config |
| State | `core/state.py` | 160 | **EXTRACT** | GatewayState singleton managing HTTP pool + CB states + rate buckets. Pattern is reusable |
| App Factory | `core/app.py` | 143 | GUT | Lifespan pattern is useful but routing/middleware will be completely different |
| Health | `observability/health.py` | 76 | SKIP | We'll use FastMCP's health endpoint pattern |
| Telemetry | `observability/telemetry.py` | 157 | SKIP | OpenTelemetry is overkill for Claude Max deployment. Structlog setup is extractable |
| Agent Routes | `agents/routes.py` | 85 | SKIP | Not applicable to our agent model |
| K8s / Docker / Monitoring | deploy/, monitoring/ | N/A | SKIP | We deploy on Claude Max, not K8s |

**Summary:** EXTRACT 5 modules (circuit breaker, rate limiter, logging middleware, config pattern, state pattern). SKIP everything else.

---

## 5. Three-Way Effort Comparison

### Option A: Fork mcp-gateway + Modify

| Task | Effort |
|------|--------|
| Strip unused features (K8s, OAuth, Grafana, product tiers, monitoring) | 1 day |
| Add stdio transport support (deep refactor of proxy engine) | 2-3 days |
| Rework auth from upstream-level to tool-level authorization | 1-2 days |
| Implement Redis rate limiting (currently stub) + change to per-provider | 1-1.5 days |
| Expand audit logging to full tool-call audit with I/O hashing | 1 day |
| Build tool registry with transport_type, security_approved, schemas | 1 day |
| Add citation extraction module | 1 day |
| Add dead-letter path to retry logic | 0.5 day |
| Integrate with Keystone events system (PipelineEvent) | 1 day |
| Resolve license issue (contact author or rewrite extracted code) | Unknown |
| **Total** | **~10-12 days** |

**Risk:** High. The stdio transport retrofit touches the core architectural assumption. We'd be fighting the codebase rather than building with it. The fork also inherits 21 deps, many of which we don't need.

### Option B: Build from scratch with FastMCP (Recommended)

| Task | Effort |
|------|--------|
| Gateway wrapper around FastMCP (tool routing, both transports) | 1-2 days |
| Per-agent tool authorization (assigned_tools enforcement) | 1 day |
| Redis-backed per-provider rate limiting | 1 day |
| Circuit breaker (port pattern from mcp-gateway) | 0.5-1 day |
| Audit logging (structlog, port pattern from mcp-gateway) | 0.5-1 day |
| Tool registry with health checks, transport_type, security_approved | 1 day |
| Citation extraction from tool outputs | 1 day |
| Dead-letter path on retry exhaustion | 0.5 day |
| Keystone events integration | 0.5-1 day |
| Tool Search / progressive schema loading | 0.5 day |
| **Total** | **~7-9 days** |

**Risk:** Low. FastMCP handles protocol compliance, both transports, and tool definition. We build only Keystone-specific features on top.

### Option C: Build from scratch without FastMCP

| Task | Effort |
|------|--------|
| MCP protocol types + JSON-RPC 2.0 validation | 2 days |
| Gateway router + method dispatch | 2 days |
| stdio transport (subprocess management) | 1.5 days |
| HTTP transport (httpx proxy) | 1 day |
| Auth + tool authorization | 1-1.5 days |
| Rate limiting (Redis) | 1 day |
| Circuit breakers | 1 day |
| Audit logging | 1 day |
| Tool registry | 1 day |
| Citation extraction | 1 day |
| Dead-letter path | 0.5 day |
| Keystone events | 0.5-1 day |
| **Total** | **~13-15 days** |

**Risk:** Medium. More work but full control. Only justified if FastMCP has show-stopping limitations.

---

## 6. Verdict: EXTRACT

**Do not fork. Build from scratch with FastMCP, extracting specific patterns from mcp-gateway.**

### Rationale

1. **Transport mismatch is load-bearing.** The mcp-gateway is an HTTP reverse proxy. Our gateway needs to manage both HTTP and stdio MCP servers. This isn't a feature gap that can be patched in; it's an architectural mismatch baked into the proxy engine, the routing layer, and the health check system.

2. **FastMCP already does what mcp-gateway does, plus more.** FastMCP provides MCP protocol types, both transports, tool definition with schemas, and is a maintained first-party MCP SDK. Forking mcp-gateway would mean maintaining a parallel MCP implementation.

3. **Authorization model mismatch.** mcp-gateway controls which *servers* an agent can reach. We need to control which *tools* an agent can call. This is a fundamental data model difference that would require rewriting auth, routing, and agent registry.

4. **Fork overhead exceeds build cost.** Option A (fork) is estimated at 10-12 days. Option B (build with FastMCP) is 7-9 days. The fork is both slower and riskier.

5. **License risk.** No LICENSE file. Cannot legally fork.

6. **No maintenance community.** 1 contributor, 4 commits. We'd inherit all maintenance burden.

### What to Extract

These patterns are worth studying and porting (reimplemented in our codebase, not copied):

| Pattern | Source | Value |
|---------|--------|-------|
| Circuit breaker state machine | `middleware/circuit_breaker.py` | Async-lock-guarded CLOSED/OPEN/HALF_OPEN transitions. Clean 82-line implementation |
| Token-bucket algorithm | `core/state.py` (RateLimitBucket) | Monotonic clock + async lock. Port the math, add Redis backend |
| GatewayState singleton | `core/state.py` | Centralized management of HTTP pool, CB states, rate buckets. Good pattern for our gateway state |
| Pydantic Settings with JSON loading | `core/config.py` | Env + .env + JSON file layered config. Good template for gateway config |
| Structured access logging | `middleware/logging_mw.py` | structlog + request context propagation. Extend for tool-call audit |

### What to Skip

- MCP protocol implementation (FastMCP handles this)
- HTTP proxy engine (FastMCP handles transports)
- Agent registration / JWT session management (our agents don't work this way)
- K8s, Docker, Grafana, Prometheus (we deploy on Claude Max)
- OAuth JWKS integration (not in our auth model)
- Product strategy / monetization tier code

---

## 7. Implementation Plan (Build with FastMCP)

If proceeding with Option B, the recommended build order for Component #4:

1. **Core gateway module** -- FastMCP-based tool router with both transports. Wire up 3 MCP servers (Exa HTTP, Brave HTTP, EdgarTools stdio) to validate the architecture.
2. **Per-agent tool authorization** -- `assigned_tools` enforcement. Reject calls to unauthorized tools before they reach the MCP server.
3. **Tool registry** -- Dynamic registration with transport_type, security_approved, health checks. Progressive schema loading for context efficiency.
4. **Rate limiting** -- Redis-backed per-provider token bucket. Configurable per provider (Exa: 100/min, Brave: 60/min, etc.).
5. **Circuit breaker** -- Per-provider, port pattern from mcp-gateway (3 failures / 30s).
6. **Audit logging** -- structlog JSON with agent_id, tool_name, input_hash, output_hash, latency_ms, engagement_id.
7. **Citation extraction** -- Parse tool outputs for URLs, titles, dates. Hand off CitationExtracted events.
8. **Dead-letter path** -- On retry exhaustion, emit a structured dead-letter event and continue pipeline.
9. **Wire remaining MCP servers** -- FRED, paper-search-mcp, Finnhub, doi-mcp.
