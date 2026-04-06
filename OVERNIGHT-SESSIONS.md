# Overnight Parallel Sessions (April 6-7, 2026)

## Overview

Four parallel Claude Code sessions launching overnight. All have zero hard blockers.
Component #6 prompt is in NEXT-WAVE-PROMPTS.md. Components #4, #3b, #5 are below.

**Dependency awareness:** #5 depends on #4 for tool registry, but #4 is being built
in parallel. #5 uses a stub tool registry interface. After both finish, wire the
real #4 tool registry into #5.

**Execution:**
```
Session A: Component #6 (Evaluator)         ~4-6 hrs  [prompt in NEXT-WAVE-PROMPTS.md]
Session B: Component #4 (MCP Gateway)       ~3-5 hrs  [prompt below]
Session C: Component #3b (Knowledge Accum)  ~2-4 hrs  [prompt below]
Session D: Component #5 (Spec Engine)       ~5-8 hrs  [prompt below]
```

**After overnight:**
- Wire #4 tool registry into #5
- Run cross-component integration tests
- Launch #3a (Source Discovery) once PostgreSQL + API keys are set up
- Component #7 (Research Agents) is unblocked by #5

---

## Session B: Component #4 — MCP Gateway

### Prompt:

````markdown
# Component #4: MCP Gateway — Full Build

## Identity

You are building the MCP Gateway (Component #4) for the Keystone Intelligence Engine.
The gateway is the central router ALL tool calls flow through. Every research agent
calls tools exclusively via this gateway. It enforces per-agent authorization,
rate limits, circuit breaking, and audit logging.

Track 2B evaluated the vurgunhajiyev/mcp-gateway repository and recommended EXTRACT:
build from scratch with FastMCP, but extract 5 patterns (circuit breaker state machine,
token-bucket rate limiter, gateway state singleton, Pydantic Settings config, structured
access logging). Do NOT fork the repo. Study the patterns and reimplement them.

## MANDATORY: CREATE A TODO LIST

Before writing any code, create a comprehensive todo list using TodoWrite:
```
1. PHASE 0: Context loading (read all required files)
2. PHASE 1: Build tool_registry.py + config
3. PHASE 2: Build auth.py (per-agent tool authorization)
4. PHASE 3: Build rate_limiter.py (token bucket, Redis-ready interface)
5. PHASE 4: Build circuit_breaker.py (CLOSED/OPEN/HALF_OPEN state machine)
6. AUDIT CHECKPOINT 1: Run tests for Phases 1-4
7. PHASE 5: Build mcp_gateway.py (central router)
8. PHASE 6: Build audit_log.py (structured logging)
9. PHASE 7: Build MCP server configs (Exa, Brave, EdgarTools stubs)
10. AUDIT CHECKPOINT 2: Run all tests, verify authorization enforcement
11. PHASE 8: Integration test with mock MCP servers
12. FINAL AUDIT: Full verification checklist
13. SESSION COMPLETION: Update SESSION-LOG.md
```

## PHASE 0: CONTEXT LOADING

Read these files before writing code:

1. `CLAUDE.md` — Project overview, coding standards
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Directives 9 (retry + dead-letter), 11
   (configurable pipeline depth), 14 (quality standard)
3. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Component #4 section. Read fully.
4. `audit/fork-evaluations/mcp-gateway-eval.md` — Track 2B results. Read the 5
   extraction patterns in the recommendation section.
5. `src/keystone/contracts.py` — There is no explicit MCP Gateway contract. The gateway
   is implicit infrastructure supporting ResearchAgentContract. When a research agent
   calls a tool, it uses `gateway.execute(ToolCall)` internally. Read how
   ResearchAgentContract references tool calls to understand the dependency.
6. `src/keystone/events.py` — The gateway does NOT emit PipelineEvents. Tool execution
   is lower-level than pipeline stage transitions. Research agents emit ResearchStarted/
   ResearchComplete; the gateway just executes their tool calls. Audit logging (Phase 6)
   is the gateway's observability mechanism, not events.
7. `src/keystone/models/agents.py` — Read AgentDefinition (tools field) and AgentInstance.
   The gateway checks agent.tools for authorization.
8. `src/keystone/models/tasks.py` — Read ResearchTask.assigned_tools. This is the
   source of truth for what tools an agent may use.
9. `src/keystone/models/config.py` — Read AppConfig and RateLimitConfig. The gateway
   config should follow the same pattern.

**DO NOT modify:** Any file outside `src/keystone/gateway/` and `tests/`.

## PHASE 1: BUILD tool_registry.py

The registry of all available MCP servers. This is what the Specification Engine
queries when assigning tools to agents.

```python
class ToolEntry(BaseModel):
    """A registered MCP tool."""
    name: str                          # e.g., "exa_search"
    server_name: str                   # e.g., "exa-mcp-server"
    description: str                   # Short description for context-window budget
    transport_type: TransportType      # "http" | "stdio" | "docker"
    security_approved: bool = True
    health_status: HealthStatus = HealthStatus.UNKNOWN
    config: dict[str, Any] = {}        # Server-specific config (API keys, URLs)

class TransportType(StrEnum):
    HTTP = "http"
    STDIO = "stdio"
    DOCKER = "docker"

class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ToolRegistry:
    """Registry of available MCP servers with health checks."""

    def register(self, entry: ToolEntry) -> None: ...
    def get(self, tool_name: str) -> ToolEntry | None: ...
    def list_tools(self) -> list[ToolEntry]: ...
    def get_description_budget(self) -> int:
        """Total tokens for all tool descriptions. Target: < 10,000 tokens."""
    async def health_check_all(self) -> dict[str, HealthStatus]: ...
```

Seed the registry with entries for: Exa, Brave Search, EdgarTools, FRED,
paper-search-mcp, doi-mcp, Finnhub. Use placeholder configs (API keys from
environment variables, not hardcoded).

## PHASE 2: BUILD auth.py

Per-agent tool authorization. Structural enforcement, not honor system.

```python
class AuthorizationError(Exception):
    """Agent attempted to call a tool not in its assigned_tools."""

class ToolAuthorizer:
    def __init__(self, registry: ToolRegistry): ...

    def check(self, agent_id: str, assigned_tools: list[str], tool_name: str) -> None:
        """Raise AuthorizationError if tool_name not in assigned_tools."""

    def get_agent_tools(self, assigned_tools: list[str]) -> list[ToolEntry]:
        """Return ToolEntry objects for the agent's assigned tools."""
```

## PHASE 3: BUILD rate_limiter.py

Token-bucket rate limiter. Phase 1 uses in-memory buckets. Phase 2 adds Redis backend.
Design the interface so Redis is a drop-in replacement.

```python
class RateLimiterBackend(Protocol):
    """Backend for rate limit state. In-memory for Phase 1, Redis for Phase 2."""
    async def try_acquire(self, key: str, tokens: int = 1) -> bool: ...
    async def get_remaining(self, key: str) -> int: ...

class InMemoryRateLimiter:
    """Token-bucket rate limiter with configurable per-provider limits."""

    def __init__(self, limits: dict[str, RateLimit]): ...
    async def try_acquire(self, provider: str, tokens: int = 1) -> bool: ...

class RateLimit(BaseModel):
    max_tokens: int          # Bucket capacity
    refill_rate: float       # Tokens per second
    refill_interval: float   # Seconds between refills
```

Extract the token-bucket math from mcp-gateway's RateLimitBucket (use monotonic clock).

## PHASE 4: BUILD circuit_breaker.py

Per-provider circuit breaker. 3 failures → OPEN. 30s retry window → HALF_OPEN.

```python
class CircuitState(StrEnum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject calls
    HALF_OPEN = "half_open" # Testing recovery

class CircuitBreaker:
    """Per-provider circuit breaker (extract pattern from mcp-gateway)."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0): ...

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute func through circuit breaker.
        Raises CircuitOpenError if circuit is OPEN.
        On success in HALF_OPEN: transition to CLOSED.
        On failure: increment counter, transition if threshold reached.
        """

    @property
    def state(self) -> CircuitState: ...
```

Use async lock to protect state transitions (extract from mcp-gateway's pattern).

## PHASE 5: BUILD mcp_gateway.py

The central router. This is the main entry point for all tool calls.

```python
@dataclass
class ToolCall:
    agent_id: str
    tool_name: str
    parameters: dict[str, Any]
    engagement_id: str
    client_id: str

@dataclass
class ToolResult:
    result: Any
    citations: list[dict]    # Extracted from tool output
    tokens_used: int
    latency_ms: float
    cache_hit: bool

class MCPGateway:
    """Central router for all MCP tool calls.

    Orchestrates: authorization → rate limiting → circuit breaking → execution → audit.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        authorizer: ToolAuthorizer,
        rate_limiter: InMemoryRateLimiter,
        audit_logger: AuditLogger,
    ): ...

    async def execute(self, call: ToolCall) -> ToolResult:
        """Execute a tool call through the full pipeline.

        Flow:
        1. Authorize: agent_id has tool_name in assigned_tools?
        2. Rate limit: provider has capacity?
        3. Circuit break: provider healthy?
        4. Execute: call MCP server
        5. Extract citations from result (basic extraction, Phase 1: URLs and
           direct attribute references only. Full deduplication and verification
           happens in CitationProcessor, not here.)
        6. Audit log: record full call context
        7. Return ToolResult
        """
```

**MCP execution:** For Phase 1, the actual MCP server calls are STUBBED. The gateway
architecture is real, but the MCP client that talks to servers will be a mock.
Create an MCPClient Protocol:

```python
class MCPClient(Protocol):
    async def call_tool(self, server: str, tool: str, params: dict) -> Any: ...

class MockMCPClient:
    """Returns canned responses. Used for testing and Phase 1 development."""

class RealMCPClient:
    """Phase 1B: uses FastMCP client to talk to real MCP servers."""
```

**Retry + dead-letter (Directive 9):** Every tool execution must have:
- Max 3 retries with exponential backoff
- Dead-letter logging after exhaustion (tool call recorded as failed, not silently dropped)

## PHASE 6: BUILD audit_log.py

Structured logging for every tool call. Use structlog.

```python
class AuditLogger:
    """Logs every tool call with full context for debugging and compliance."""

    def log_call(self, call: ToolCall, result: ToolResult | None, error: Exception | None) -> None:
        """Log: agent_id, tool_name, input_hash, output_hash, latency, timestamp, success."""
```

Input/output hashed (SHA-256) rather than logged in full (data volume concern).
Full I/O available in debug mode.

## PHASE 7: MCP SERVER CONFIGURATIONS

Create configuration entries for all 7 MCP servers. These are registry entries +
connection configs, NOT the servers themselves.

```python
# src/keystone/gateway/servers/
# One config file per server group

TOOL_CONFIGS = {
    "exa_search": ToolEntry(
        name="exa_search",
        server_name="exa-mcp-server",
        transport_type=TransportType.HTTP,
        config={"api_key_env": "EXA_API_KEY"},
    ),
    "brave_search": ToolEntry(...),
    "edgar_tools": ToolEntry(transport_type=TransportType.STDIO, ...),
    "fred_data": ToolEntry(transport_type=TransportType.STDIO, ...),
    "paper_search": ToolEntry(transport_type=TransportType.HTTP, ...),
    "doi_verify": ToolEntry(transport_type=TransportType.STDIO, ...),
    "finnhub_market": ToolEntry(transport_type=TransportType.HTTP, ...),
}
```

## TESTS

**test_tool_registry.py:**
- Register and retrieve tools
- Health check with mock responses
- Description budget < 10,000 tokens with all 7 servers
- Unknown tool returns None

**test_auth.py:**
- Agent with assigned tools can access them
- Agent without assigned tool gets AuthorizationError
- Empty assigned_tools list blocks all tools

**test_rate_limiter.py:**
- Token bucket allows calls within capacity
- Token bucket rejects when exhausted
- Tokens refill over time (mock time)
- Per-provider isolation

**test_circuit_breaker.py:**
- CLOSED → stays CLOSED on success
- CLOSED → OPEN after 3 failures
- OPEN → rejects calls with CircuitOpenError
- OPEN → HALF_OPEN after recovery_timeout
- HALF_OPEN → CLOSED on success
- HALF_OPEN → OPEN on failure

**test_gateway.py (integration):**
- Full flow: auth → rate limit → circuit break → execute → audit
- Authorization failure: tool not in assigned list
- Rate limit exhaustion: returns error after bucket depleted
- Circuit open: returns error
- Retry behavior: retries on transient failure, dead-letters after max
- Mock MCP client returns canned response, ToolResult populated correctly
- Audit log records all calls including failures

## FINAL AUDIT

1. All tests pass
2. `from keystone.gateway import MCPGateway, ToolRegistry, ToolAuthorizer` works
3. MockMCPClient pattern allows Phase 1B swap to RealMCPClient
4. RateLimiterBackend Protocol allows Phase 2 Redis swap
5. Directive 9: max retries + dead-letter on all tool calls
6. All 7 server configs registered with correct transport types
7. No files modified outside `src/keystone/gateway/` and `tests/`

## SESSION COMPLETION
Write entry to `SESSION-LOG.md`. Note: files created, test results, patterns extracted
from mcp-gateway, Phase 2 upgrade paths (Redis rate limiter, real MCP client).
Handoff: "Specification Engine (#5) can now import ToolRegistry for tool assignment."
````

---

## Session C: Component #3b — Knowledge Accumulation

### Prompt:

````markdown
# Component #3b: Knowledge Accumulation — Full Build

## Identity

You are building the Knowledge Accumulation module (Component #3b) for the Keystone
Intelligence Engine. This implements the Karpathy wiki pattern: raw subagent artifacts
are compiled into structured markdown wikis with auto-maintained indexes and
content-hash provenance tracking.

## MANDATORY: CREATE A TODO LIST

```
1. PHASE 0: Context loading
2. PHASE 1: Build wiki_schema.py (storage-agnostic interface)
3. PHASE 2: Build wiki_builder.py (compilation from raw → compiled)
4. PHASE 3: Build index_maintainer.py (INDEX.md auto-maintenance)
5. PHASE 4: Build content_hasher.py (proposition-level provenance)
6. AUDIT CHECKPOINT 1: Run tests, verify hash provenance chain
7. PHASE 5: Build engagement_store.py (filesystem backend, Phase 1)
8. PHASE 6: Integration test with mock research round
9. FINAL AUDIT: Full verification
10. SESSION COMPLETION: Update SESSION-LOG.md
```

## PHASE 0: CONTEXT LOADING

Read these files:
1. `CLAUDE.md` — Project overview, coding standards
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — Directive 8 (Karpathy knowledge bases),
   Directive 13 (Phase 1 staging), Directive 14 (quality standard)
3. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Component #3b section. Read fully.
4. `src/keystone/models/citations.py` — WikiCompilationRecord, Citation, Claim,
   content_hash. You will USE these types. **Pay special attention to
   WikiCompilationRecord** (citation_id, engagement_id, raw_path, compiled_path,
   content_hash, compiled_at). Your wiki builder must produce WikiCompilationRecords
   alongside WikiEntries so the citation provenance chain is maintained.
5. `src/keystone/citation/hash.py` — compute_content_hash, compute_proposition_hash.
   Import and use these. DO NOT reimplement.
6. `src/keystone/models/research.py` — StructuredFinding, FindingClaim. These are
   the raw inputs your wiki builder processes.
7. `CAPSTONE-PLAN-v2.md` — Read Section 6.3 only (knowledge accumulation architecture).
   **Critical:** The canonical file naming convention for raw/ is
   `{round}_{agent_id}_{task_id}.md` (flat, underscore-separated). Do NOT use
   nested subdirectories in raw/.

**DO NOT modify:** Any file outside `src/keystone/knowledge/` and `tests/`.

## PHASE 1: BUILD wiki_schema.py

Storage-agnostic interface. Phase 1 = filesystem. Phase 2 = PostgreSQL. The interface
must not change.

```python
class WikiEntry(BaseModel):
    """A compiled wiki entry."""
    path: str                          # compiled/{topic}.md
    engagement_id: str
    client_id: str
    content: str                       # Compiled markdown content
    content_hash: str                  # SHA-256 of content
    proposition_hashes: list[str]      # Per-proposition hashes
    source_artifacts: list[str]        # Paths to raw/ artifacts this was compiled from
    round_added: int                   # Research round number
    indexed: bool = False              # Appears in INDEX.md

class WikiStore(Protocol):
    """Storage-agnostic wiki interface.

    NOTE: WikiStore is a storage abstraction, NOT a pipeline contract.
    It does NOT appear in contracts.py and does NOT yield PipelineEvents.
    Wiki operations are event-silent. Observability is at the calling layer
    (the research orchestrator yields ResearchComplete events after wiki writes).
    """
    async def write_raw(self, engagement_id: str, round: int, agent_id: str,
                        task_id: str, artifact: str) -> str: ...  # Returns path ({round}_{agent_id}_{task_id}.md)
    async def write_compiled(self, entry: WikiEntry) -> None: ...
    async def read_compiled(self, engagement_id: str, path: str) -> WikiEntry | None: ...
    async def list_compiled(self, engagement_id: str) -> list[WikiEntry]: ...
    async def read_index(self, engagement_id: str) -> str: ...
    async def write_index(self, engagement_id: str, content: str) -> None: ...
```

## PHASE 2: BUILD wiki_builder.py

Compiles raw subagent artifacts into structured wiki entries.

```python
class WikiBuilder:
    """Compiles raw research artifacts into structured wiki entries.

    Also produces WikiCompilationRecords (from models/citations.py) to maintain
    the citation provenance chain: each record links citation_id → raw_path → compiled_path.
    """

    def __init__(self, store: WikiStore, hasher: ContentHasher): ...

    async def compile_round(
        self,
        engagement_id: str,
        client_id: str,
        round_number: int,
        findings: list[StructuredFinding],
    ) -> list[WikiEntry]:
        """Process one research round's findings into compiled wiki entries.

        For each finding:
        1. Write raw artifact to raw/{round}_{agent_id}_{task_id}.md (flat naming)
        2. Extract propositions from finding claims
        3. Hash each proposition (compute_proposition_hash)
        4. Compile into structured markdown (topic heading, claims, sources)
        5. Hash the compiled content (compute_content_hash)
        6. Write compiled entry to compiled/{topic}.md
        7. Create WikiCompilationRecord for each citation (raw_path → compiled_path)
        8. Return WikiEntry with full provenance chain
        """
```

**Compilation format:** Each compiled/{topic}.md should be structured:
```markdown
# {Topic Title}

## Key Findings
- {Finding 1} [Source: {citation_id}]
- {Finding 2} [Source: {citation_id}]

## Evidence
{Detailed evidence with attribution}

## Confidence Assessment
{Tier and rationale}

---
*Compiled from round {N} by agent {agent_id}*
*Content hash: {hash}*
```

## PHASE 3: BUILD index_maintainer.py

Auto-maintains INDEX.md for navigation.

```python
class IndexMaintainer:
    """Maintains INDEX.md as the navigation layer for the wiki."""

    async def update(self, store: WikiStore, engagement_id: str) -> None:
        """Rebuild INDEX.md from all compiled entries.

        INDEX.md format:
        # {Engagement Title} — Research Wiki

        ## Topics
        - [{Topic 1}](compiled/topic_1.md) — {one-line summary} (Round {N})
        - [{Topic 2}](compiled/topic_2.md) — {one-line summary} (Round {N})

        ## Coverage
        - Total topics: {N}
        - Rounds completed: {N}
        - Last updated: {timestamp}
        """
```

## PHASE 4: BUILD content_hasher.py

Wraps citation/hash.py utilities with wiki-specific logic.

```python
class ContentHasher:
    """Proposition-level provenance tracking using content hashing."""

    def hash_proposition(self, proposition: str, source_hash: str) -> str:
        """Hash a proposition linked to its source. Uses citation/hash.py."""
        return compute_proposition_hash(proposition, source_hash)

    def hash_content(self, content: str) -> str:
        """Hash compiled content. Uses citation/hash.py."""
        return compute_content_hash(content)

    def verify_provenance(self, entry: WikiEntry, raw_artifacts: list[str]) -> bool:
        """Verify that all proposition_hashes trace back to raw artifacts."""
```

## PHASE 5: BUILD engagement_store.py

Filesystem backend for WikiStore Protocol.

```python
class FilesystemWikiStore:
    """Filesystem implementation of WikiStore. Phase 1 backend.

    Directory structure:
    {base_path}/{engagement_id}/
        memory/
            raw/{round}_{agent_id}_{task_id}.md    # Flat naming, immutable after write
            compiled/{topic}.md
            INDEX.md
    """

    def __init__(self, base_path: str = "engagements"): ...
```

Use async file I/O (aiofiles or asyncio.to_thread wrapping sync IO).

## TESTS

**test_wiki_schema.py:**
- WikiEntry validates with all required fields
- Content hash is 64-char hex
- Proposition hashes list validated

**test_wiki_builder.py:**
- Single finding compiles into wiki entry with correct format
- Multiple findings from same round grouped correctly
- Proposition hashes generated for each claim
- Content hash matches recomputed hash
- Raw artifacts written to correct flat paths ({round}_{agent_id}_{task_id}.md)
- WikiCompilationRecords produced for each citation (raw_path populated, compiled_path populated)
- Empty findings handled gracefully

**test_index_maintainer.py:**
- INDEX.md generated with correct format
- Multiple topics listed alphabetically
- Round numbers tracked per topic
- Coverage stats accurate

**test_content_hasher.py:**
- Proposition hash matches citation/hash.py output
- Content hash matches citation/hash.py output
- Provenance verification: valid chain passes
- Provenance verification: broken chain fails

**test_engagement_store.py (integration):**
- Full round: write raw → compile → write compiled → update index → read back
- Multiple rounds accumulate correctly
- Index reflects all compiled entries
- Content hashes traceable through provenance chain

## FINAL AUDIT

1. All tests pass
2. WikiStore Protocol allows Phase 2 PostgreSQL swap
3. No direct filesystem calls in wiki_builder.py (uses WikiStore interface)
4. Content hashes use citation/hash.py (not reimplemented)
5. INDEX.md auto-maintained after each compile_round call
6. No files modified outside `src/keystone/knowledge/` and `tests/`

## SESSION COMPLETION
Write entry to `SESSION-LOG.md`. Note: files created, test results, storage-agnostic
design, provenance chain verification.
Handoff: "Component #7 (Research Agents) writes to raw/ via WikiStore.
Component #9 (Deliberation) reads from compiled/ via WikiStore."
````

---

## Session D: Component #5 — Specification Engine

### Prompt:

````markdown
# Component #5: Specification Engine (L0) — Full Build

## Identity

You are building the Specification Engine (Component #5, L0) for the Keystone
Intelligence Engine. This is the highest-leverage component in the system. It takes
a natural language question and produces a complete engagement specification:
RESEARCH.md, research-tasks.json (DAG structure), issue tree, agent configurations,
and Day-1 Hypothesis. Everything downstream depends on the quality of this output.

This is a long-running session. You will build 12+ modules, prompt templates, seed
agent templates, and a comprehensive test suite.

## MANDATORY: CREATE A TODO LIST

```
1. PHASE 0: Context loading (read all required files — this is the most important phase)
2. PHASE 1: Build engagement_classifier.py (5-type taxonomy + pipeline profiles)
3. PHASE 2: Build intent_clarifier.py (Decision-First CoT, Day-1 Hypothesis)
4. PHASE 3: Build decomposer.py (heterogeneous lens issue tree construction)
5. AUDIT CHECKPOINT 1: Run tests for classifier + clarifier + decomposer
6. PHASE 4: Build validator.py (MECE verification, 5 binary dimensions)
7. PHASE 5: Build priority_scorer.py (heuristic scoring, Phase 1)
8. PHASE 6: Build template_registry.py (5-10 seed AgentDefinition templates)
9. AUDIT CHECKPOINT 2: Run tests for validator + scorer + registry
10. PHASE 7: Build task_generator.py (research-tasks.json with DAG)
11. PHASE 8: Build spec_engine.py (main orchestrator, 10-step pipeline)
12. PHASE 9: Build hitl_integration.py (Gate 1 triggering)
13. AUDIT CHECKPOINT 3: Run all tests, verify contract compliance
14. PHASE 10: Build prompt templates for each pipeline step
15. PHASE 11: Integration test with Luminar test case
16. FINAL AUDIT: Full verification checklist
17. SESSION COMPLETION: Update SESSION-LOG.md
```

## PHASE 0: CONTEXT LOADING

This is the most context-heavy component. Read ALL of these files carefully.

**Architecture and directives:**
1. `CLAUDE.md` — Project overview, coding standards
2. `JACK-ARCHITECTURAL-DIRECTIVES.md` — ALL directives are relevant, but especially:
   - Directive 1: The Rigidity Problem (templates not constraints)
   - Directive 2: MECE Issue Tree Decomposition
   - Directive 4: Engagement Scope (auto body chain test case)
   - Directive 5: Build Philosophy (right interfaces, staged depth)
   - Directive 6: FITFO Standard
   - Directive 11: Configurable Pipeline Depth (Light/Standard/Deep)
   - Directive 12: Casing Principles Over Example Libraries
   - Directive 13: Phase 1 Depth Staging
   - Directive 14: Quality Standard

**Models you MUST import and use (DO NOT recreate):**
3. `src/keystone/models/research.py` — READ THOROUGHLY:
   - EngagementType (5 values: SIZING, DIAGNOSTIC, EVALUATIVE, EXPLORATORY, STRATEGIC)
   - ResearchSpec (the RESEARCH.md Pydantic model — all fields)
   - EngagementSpec (your FINAL output type — research_spec + task_decomposition +
     validation_report + issue_tree)
   - ValidationReport (4 boolean checks + all_passed property)
   - ResearchQuestion, MethodologyRequirement, SourceRequirement
4. `src/keystone/models/tasks.py` — READ THOROUGHLY:
   - ResearchTask (all fields including dependencies, end_product, custom_category,
     anti_confirmatory_framing validator, assigned_tools validator)
   - TaskDecomposition (with DAG validation via Kahn's algorithm)
   - TaskCategory (6 categories), TaskType, TaskStatus, ModelTier
5. `src/keystone/models/agents.py` — READ THOROUGHLY:
   - AgentDefinition (name, role, model, tools, system_prompt, research_type)
   - AgentInstance, AgentRole, ResearchAgentType, DeliberationAnalystType
6. `src/keystone/contracts.py` — Read SpecificationEngineContract Protocol:
   ```python
   async def generate_spec(self, question: str, client_id: str,
       client_context: str | None = None, constraints: list[str] | None = None
   ) -> AsyncIterator[AnyPipelineEvent]
   async def get_spec(self) -> EngagementSpec
   ```
7. `src/keystone/events.py` — Read ALL L0 events:
   - SpecificationGenerated (spec_version, question_count, validation_passed)
   - TasksDecomposed (task_count, categories, rationale)
   - AgentDispatched (agent_id, agent_type, task_id, model_tier, tools)

**HITL integration (you MUST use, DO NOT reimplement):**
8. `src/keystone/hitl/gate.py` — Read create_and_wait_for_gate signature and
   build_spec_gate_items helper. You call these at Step 8.
9. `src/keystone/hitl/schemas.py` — GateType.POST_SPECIFICATION, ReviewItemCreate

**Existing schemas and samples (your output must validate against these):**
10. `schemas/research_md.schema.json` — Your RESEARCH.md output must validate
11. `schemas/research_tasks.schema.json` — Your tasks output must validate
12. `templates/RESEARCH.md.template` — Reference for RESEARCH.md structure
13. `samples/luminar_lidar/` — Read both files. This is your test case.

**Specification (read relevant sections):**
14. `audit/PHASE-1-IMPLEMENTATION-SPEC.md` — Component #5 section (full 10-step
    pipeline, acceptance criteria, first test case)
15. `CAPSTONE-PLAN-v2.md` — Read Sections 3.1-3.8 only (Specification Engine pipeline)

After reading, confirm: What Protocol do I implement? What types do I produce?
What events do I yield? What HITL functions do I call?

## PHASE 1: BUILD engagement_classifier.py

Step 1 of the 10-step pipeline. Classifies the engagement and selects pipeline profile.

```python
class PipelineProfile(StrEnum):
    LIGHT = "light"        # 1-2 agents, 1 round, Layers 1-2 eval
    STANDARD = "standard"  # 3 agents, 2-3 rounds, Layers 1-3 eval
    DEEP = "deep"          # 5+ agents, up to 5 rounds, full eval stack

class ClassificationResult(BaseModel):
    engagement_type: EngagementType
    pipeline_profile: PipelineProfile
    confidence: float  # 0-1
    reasoning: str

class EngagementClassifier:
    def __init__(self, llm: LLMCallable): ...

    async def classify(
        self, question: str, client_context: str | None = None
    ) -> ClassificationResult:
        """Classify engagement by examining 5 signals:
        1. Specificity of deliverable
        2. Presence of testable hypothesis
        3. Known analytical framework
        4. Scope boundedness
        5. Decision type
        """
```

Create a prompt template at `src/keystone/specification/prompts/classification.md`.
The prompt must output structured JSON with engagement_type, pipeline_profile,
and reasoning.

**LLM interface:** Use the same `LLMCallable = Callable[[str], Awaitable[str]]`
pattern established in the Evaluator.

## PHASE 2: BUILD intent_clarifier.py

Step 2. Decision-First Chain-of-Thought + Day-1 Hypothesis formation.

```python
class IntentClarificationResult(BaseModel):
    day_1_hypothesis: str         # Testable claim anchoring the engagement
    intent_clear: bool            # Whether the question is sufficiently specified
    unstated_constraints: list[str]
    scope_boundaries: list[str]
    decision_context: str         # What decision this research informs
    surprising_finding: str       # What a surprising finding would look like

class IntentClarifier:
    def __init__(self, llm: LLMCallable): ...

    async def clarify(
        self,
        question: str,
        engagement_type: EngagementType,
        client_context: str | None = None,
        constraints: list[str] | None = None,
    ) -> IntentClarificationResult:
        """Run Decision-First CoT (5-step structured prompt):
        1. What decision does this research inform?
        2. What would a surprising finding look like?
        3. What constraints aren't stated?
        4. What evidence would change the client's mind?
        5. What is explicitly out of scope?
        """
```

Create prompt template at `prompts/intent_clarification.md`. This is an Opus-level
prompt — it must elicit genuine analytical thinking, not templated responses.

## PHASE 3: BUILD decomposer.py

Step 3. The core intellectual engine. 3-4 Sonnet agents with heterogeneous
consulting lenses independently construct issue trees, then an Opus meta-agent
synthesizes them.

```python
class IssueTreeNode(BaseModel):
    id: str
    name: str
    description: str
    children: list[IssueTreeNode] = []
    lens_annotations: dict[str, str] = {}  # Which lens contributed what

class IssueTree(BaseModel):
    root: IssueTreeNode
    metadata: IssueTreeMetadata

class IssueTreeMetadata(BaseModel):
    depth: int                    # Should be 2-3
    leaf_count: int               # Target: 8-20
    lenses_used: list[str]        # e.g., ["financial", "operational", "market"]
    synthesis_rationale: str

class Decomposer:
    def __init__(self, llm: LLMCallable): ...

    async def decompose(
        self,
        question: str,
        engagement_type: EngagementType,
        day_1_hypothesis: str,
        client_context: str | None = None,
    ) -> IssueTree:
        """Three-phase decomposition:
        1. Spawn 3 parallel agents (financial, operational, market/competitive lens)
        2. Each produces an independent shallow tree (2-3 levels)
        3. Opus meta-agent synthesizes into unified tree
        """
```

Create 4 prompt templates:
- `prompts/decompose_financial_lens.md`
- `prompts/decompose_operational_lens.md`
- `prompts/decompose_market_lens.md`
- `prompts/decompose_synthesis.md`

Each lens prompt must:
- Define the lens perspective clearly
- Instruct for 2-3 levels, 8-20 leaf nodes
- Require MECE at each level
- Output structured JSON matching IssueTreeNode
- Include the Day-1 Hypothesis as an anchor

The synthesis prompt takes all 3 trees and produces one unified tree.

## PHASE 4: BUILD validator.py

Step 4. MECE verification with 5 binary dimensions.

```python
class ValidationDimension(StrEnum):
    MUTUAL_EXCLUSIVITY = "mutual_exclusivity"
    COLLECTIVE_EXHAUSTIVENESS = "collective_exhaustiveness"
    TAILORING = "tailoring"
    ACTIONABILITY = "actionability"
    DEPTH_APPROPRIATENESS = "depth_appropriateness"

class MECEValidationResult(BaseModel):
    dimensions: dict[ValidationDimension, bool]
    feedback: dict[ValidationDimension, str]
    all_passed: bool
    regeneration_needed: bool

class MECEValidator:
    def __init__(self, llm: LLMCallable): ...

    async def validate(
        self,
        tree: IssueTree,
        question: str,
        engagement_type: EngagementType,
    ) -> MECEValidationResult:
        """Validate issue tree on 5 dimensions. Uses Opus as judge."""
```

Create prompt template at `prompts/mece_validation.md`.

If validation fails, the decomposer should be called again (max 2 retries).
Implement the retry loop in the orchestrator (spec_engine.py), not here.

## PHASE 5: BUILD priority_scorer.py

Step 5. Phase 1 uses simplified heuristic scoring.

```python
class PriorityScore(BaseModel):
    branch_id: str
    decision_relevance: float     # 0-1
    uncertainty_reduction: float  # 0-1
    priority_score: float         # decision_relevance * uncertainty_reduction
    reasoning: str

class PriorityScorer:
    def __init__(self, llm: LLMCallable): ...

    async def score(
        self,
        tree: IssueTree,
        day_1_hypothesis: str,
        engagement_type: EngagementType,
    ) -> list[PriorityScore]:
        """Score each leaf node. Phase 1 formula:
        priority_score = decision_relevance × uncertainty_reduction
        Phase 2 adds: / estimated_cost (VOI formula)
        """
```

## PHASE 6: BUILD template_registry.py

Step 6. 5-10 seed AgentDefinition templates.

```python
class TemplateMatch(BaseModel):
    template: AgentDefinition
    similarity: float              # 0-1
    match_type: str                # "exact" | "interpolated" | "custom"

class TemplateRegistry:
    """Registry of seed AgentDefinition templates."""

    def __init__(self): ...

    def match(
        self,
        task: ResearchTask,
        engagement_type: EngagementType,
    ) -> TemplateMatch:
        """Find best-matching template for a task.
        > 0.85 similarity: use template with task-specific interpolation
        < 0.85 similarity: flag for custom generation
        """

    def get_seed_templates(self) -> list[AgentDefinition]: ...
```

Create at least 5 seed templates:
1. **Quantitative Analyst** — financial data, EdgarTools, FRED, Finnhub
2. **Market Researcher** — competitive analysis, Exa, Brave, industry reports
3. **Academic Researcher** — paper-search-mcp, academic sources
4. **Regulatory Analyst** — EdgarTools, FRED, government sources
5. **Generalist** — Exa, Brave, mixed sources

Each template is an AgentDefinition with pre-configured tools, model tier, and
system prompt. Store as Python data (not markdown files) for Phase 1.

**Tighten-only invariant:** Custom configs generated from templates can only RESTRICT
capabilities, never expand beyond the parent template.

## PHASE 7: BUILD task_generator.py

Step 7. Generates research-tasks.json with DAG structure.

```python
class TaskGenerator:
    def __init__(self, llm: LLMCallable, registry: TemplateRegistry): ...

    async def generate(
        self,
        tree: IssueTree,
        priorities: list[PriorityScore],
        engagement_type: EngagementType,
        spec: ResearchSpec,
    ) -> TaskDecomposition:
        """Generate research-tasks.json from prioritized issue tree.

        For each leaf node:
        1. Create ResearchTask with DAG dependencies
        2. Assign anti-confirmatory framing
        3. Specify end_product per branch
        4. Match to agent template (via TemplateRegistry)
        5. Assign 3-5 tools from matched template

        Output must validate against TaskDecomposition (which runs DAG validation).
        """
```

Create prompt template at `prompts/task_generation.md`.

**Critical:** The generated TaskDecomposition MUST pass Pydantic validation, which
includes DAG cycle detection (Kahn's algorithm). If the LLM produces cyclic
dependencies, catch the ValidationError and regenerate (max 2 retries).

## PHASE 8: BUILD spec_engine.py

The main orchestrator. Implements SpecificationEngineContract.

```python
class SpecificationEngine:
    """L0 Specification Engine: 10-step pipeline.

    Implements SpecificationEngineContract Protocol.
    """

    def __init__(
        self,
        llm: LLMCallable,
        template_registry: TemplateRegistry,
        db_session_factory: Callable | None = None,  # For HITL gate
    ): ...

    async def generate_spec(
        self,
        question: str,
        client_id: str,
        client_context: str | None = None,
        constraints: list[str] | None = None,
    ) -> AsyncIterator[AnyPipelineEvent]:
        """Run the 10-step specification pipeline.

        Steps 1-7: Generate specification
        Step 8: HITL Gate 1 (blocks until human decision)
        Steps 9-10: Research execution + feedback (STUBS for Phase 1)

        Yields: SpecificationGenerated, TasksDecomposed, AgentDispatched events.
        """
        # Step 1: Classify
        classification = await self.classifier.classify(question, client_context)

        # Step 2: Clarify intent + Day-1 Hypothesis
        intent = await self.clarifier.clarify(
            question, classification.engagement_type, client_context, constraints
        )

        # Step 3: Decompose (with retry on MECE failure)
        tree = await self._decompose_with_validation(
            question, classification.engagement_type, intent.day_1_hypothesis
        )

        # Step 4: MECE validation (inside _decompose_with_validation)

        # Step 5: Priority scoring
        priorities = await self.scorer.score(
            tree, intent.day_1_hypothesis, classification.engagement_type
        )

        # Step 6-7: Task generation (includes template matching + tool assignment)
        research_spec = self._build_research_spec(question, intent, classification, ...)
        task_decomposition = await self.task_generator.generate(
            tree, priorities, classification.engagement_type, research_spec
        )

        yield SpecificationGenerated(
            spec_version=1,
            question_count=len(research_spec.questions),
            validation_passed=True,
            ...
        )
        yield TasksDecomposed(
            task_count=len(task_decomposition.tasks),
            categories=[...],
            rationale=task_decomposition.decomposition_rationale,
            ...
        )

        # Build EngagementSpec
        validation_report = ValidationReport(
            intent_clear=intent.intent_clear,
            scope_valid=True,
            within_frontier=True,
            quality_threshold_met=True,
        )
        self._spec = EngagementSpec(
            research_spec=research_spec,
            task_decomposition=task_decomposition,
            validation_report=validation_report,
            issue_tree=tree.model_dump(),
        )

        # Step 8: HITL Gate 1 (only if db_session_factory provided)
        if self.db_session_factory:
            await self._trigger_hitl_gate(tree, task_decomposition)

        # Steps 9-10: Research execution + feedback loop — STUB
        # These are implemented by Components #7 and the orchestrator.
        # The Spec Engine's job ends after HITL approval.

    async def get_spec(self) -> EngagementSpec:
        if self._spec is None:
            raise RuntimeError("generate_spec() must be called first")
        return self._spec
```

**HITL integration:**
```python
async def _trigger_hitl_gate(self, tree, tasks):
    from keystone.hitl.gate import create_and_wait_for_gate, build_spec_gate_items
    from keystone.hitl.schemas import GateType

    items = build_spec_gate_items(
        issue_tree=tree.model_dump(),
        agent_configs=[t.model_dump() for t in self._agent_configs],
    )
    # This blocks until human approves/rejects
    gate_result = await create_and_wait_for_gate(
        session=...,
        engagement_id=self._spec.research_spec.engagement_id,
        client_id=self._spec.research_spec.client_id,
        gate_type=GateType.POST_SPECIFICATION,
        items=items,
    )
    # If rejected, GateRejectedError propagates up
```

## PHASE 9: PROMPT TEMPLATES

Create prompt templates in `src/keystone/specification/prompts/`:

1. `classification.md` — 5-signal engagement classification
2. `intent_clarification.md` — Decision-First CoT (5-step)
3. `decompose_financial_lens.md` — Financial perspective tree
4. `decompose_operational_lens.md` — Operational perspective tree
5. `decompose_market_lens.md` — Market/competitive perspective tree
6. `decompose_synthesis.md` — Opus synthesis of 3 lens trees
7. `mece_validation.md` — 5-dimension MECE check
8. `task_generation.md` — research-tasks.json from prioritized tree
9. `priority_scoring.md` — Heuristic priority scoring

Each prompt must:
- Output structured JSON (specify exact format)
- Include placeholders for dynamic content ({{question}}, {{day_1_hypothesis}}, etc.)
- Be specific enough to produce calibrated output (not generic)
- Be 200-600 words

## TESTS

**test_engagement_classifier.py:**
- "Evaluate competitive position of Company X" → EVALUATIVE
- "Estimate TAM for autonomous vehicle sensors" → SIZING
- "What's happening in the EV market?" → EXPLORATORY
- "Should we acquire Company Y?" → STRATEGIC
- "What caused the Q3 revenue decline?" → DIAGNOSTIC
- Pipeline profile matches engagement type (SIZING → Standard, STRATEGIC → Deep)

**test_intent_clarifier.py:**
- Well-specified question → intent_clear=True, non-empty day_1_hypothesis
- Vague question ("Tell me about AI") → intent_clear=False
- Day-1 Hypothesis is testable (contains a claim, not just a question)
- Decision context extracted from client_context

**test_decomposer.py:**
- Produces tree with 2-3 levels (mock LLM)
- Leaf count between 8-20
- 3 lens trees merged into 1
- Tree is valid JSON (IssueTree validates)

**test_validator.py:**
- Valid tree passes all 5 dimensions (mock LLM)
- Overdecomposed tree (40+ leaves) fails depth_appropriateness
- Overlapping branches fail mutual_exclusivity
- Empty tree fails collective_exhaustiveness

**test_priority_scorer.py:**
- Returns scores for all leaf nodes
- Scores between 0-1
- priority_score = decision_relevance × uncertainty_reduction

**test_template_registry.py:**
- Financial task matches Quantitative Analyst template
- Academic task matches Academic Researcher template
- Novel task below 0.85 threshold flagged for custom generation
- At least 5 seed templates loaded

**test_task_generator.py:**
- Generates 10+ tasks (mock LLM)
- Tasks form valid DAG (TaskDecomposition validates)
- Each task has anti_confirmatory_framing
- Each task has end_product
- Each task has 3-5 assigned_tools
- Dependencies reference valid task IDs

**test_spec_engine.py (integration):**
- Full pipeline with Luminar test case (mock all LLM calls)
- Yields SpecificationGenerated then TasksDecomposed events
- EngagementSpec validates against all Pydantic models
- RESEARCH.md validates against research_md.schema.json
- research-tasks.json validates against research_tasks.schema.json
- HITL gate triggered (mock gate approval)
- Rejected gate raises GateRejectedError
- get_spec() raises before generate_spec() called
- isinstance(engine, SpecificationEngineContract) passes

## FINAL AUDIT

1. **Contract compliance:** SpecificationEngine satisfies SpecificationEngineContract
2. **Event compliance:** All 3 L0 events yielded with correct fields
3. **Model compliance:** EngagementSpec, ResearchSpec, TaskDecomposition all validate
4. **Schema compliance:** Output validates against JSON schemas in schemas/
5. **HITL compliance:** Gate 1 triggered with build_spec_gate_items
6. **Directive compliance:**
   - Directive 1: custom_category enables non-standard tasks
   - Directive 2: MECE issue tree with heterogeneous lenses
   - Directive 11: Light/Standard/Deep profiles operational
   - Directive 12: Principles-based decomposition (not example-library-dependent)
   - Directive 13: No Phase 2 features (TiCoder, VOI full formula, CBR query,
     ADaPT reactive decomposition)
7. **DAG validation:** Generated tasks pass Kahn's algorithm cycle detection
8. **Anti-confirmatory:** All task framings pass the validator in tasks.py
9. **No ownership violations:** Only created files in `src/keystone/specification/`
   and `tests/`
10. **Prompt completeness:** All 9 templates exist, 200-600 words each

## SESSION COMPLETION

Write entry to `SESSION-LOG.md`. Note:
- All files created with line counts
- Test results
- Seed template descriptions
- Prompt template word counts
- Luminar test case results
- Phase 2 deferred items: TiCoder, VOI, CBR, ADaPT, template promotion
- Handoff: "Component #7 (Research Agents) can now receive EngagementSpec.
  Component #4 (MCP Gateway) provides the ToolRegistry for tool assignment."
````

---

## Post-Overnight Integration Tasks

After all 4 sessions complete:

1. **Wire #4 → #5:** Replace stub tool registry in Spec Engine with real ToolRegistry
   from MCP Gateway. This should be a config change (import swap), not a rewrite.

2. **Wire #3b → #7:** When Component #7 (Research Agents) is built, it writes raw
   artifacts to WikiStore.

3. **Cross-component test:** Create a mini integration test that:
   - Runs Spec Engine → produces EngagementSpec
   - Checks ToolRegistry has the assigned tools
   - Verifies WikiStore can accept raw artifacts

4. **Update CURRENT-STATE.md** with all session results.
