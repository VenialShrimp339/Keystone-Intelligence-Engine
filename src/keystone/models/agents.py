"""Agent definition models for the Keystone Intelligence Engine.

Adopted from nano-claude-code's AgentDefinition pattern (multi_agent/subagent.py).
Agent types are defined as .md files with YAML frontmatter specifying tools,
model, and system prompt. This enables rapid specialization without code changes.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from keystone.models.tasks import ModelTier


class AgentRole(StrEnum):
    """Pipeline layer roles for agents."""

    SPECIFICATION = "specification"
    RESEARCH = "research"
    CITATION_PROCESSOR = "citation_processor"
    DELIBERATION_ANALYST = "deliberation_analyst"
    AGGREGATOR = "aggregator"
    STRUCTURING = "structuring"
    GENERATOR = "generator"
    EVALUATOR = "evaluator"


class ResearchAgentType(StrEnum):
    """Specialization types for L1 research agents.

    Each type uses a different analytical methodology on the same
    evidence, producing genuinely independent assessments.
    """

    QUANTITATIVE = "quantitative"
    QUALITATIVE = "qualitative"
    CONTRARIAN = "contrarian"
    HISTORICAL_ANALOGY = "historical_analogy"
    INTERNAL_DOCUMENT = "internal_document"


class DeliberationAnalystType(StrEnum):
    """Specialization types for L1.5 deliberation analysts.

    Methodological diversity replaces persona diversity (DMAD, ICLR 2025).
    """

    ACH = "ach"
    QUANTITATIVE = "quantitative"
    ADVERSARIAL = "adversarial"
    HISTORICAL_ANALOGY = "historical_analogy"
    SCENARIO_PLANNING = "scenario_planning"


class AgentDefinition(BaseModel):
    """Definition of an agent's identity, capabilities, and constraints.

    Adopted from nano-claude-code pattern: agents defined as .md files with
    YAML frontmatter. This model represents the parsed definition.

    Key properties:
    - tools: 3-5 tools per agent (structurally enforced by MCP gateway)
    - model: inherit from parent or override per agent
    - system_prompt: base methodology + agent specialization + engagement context
    """

    name: str = Field(description="Unique agent name within the engagement")
    description: str = Field(description="What this agent does (one line)")
    role: AgentRole = Field(description="Which pipeline layer this agent serves")
    model: ModelTier = Field(
        default=ModelTier.SONNET,
        description="Model tier. Opus for L0/L4 (judgment), Sonnet for L1 (throughput), "
        "Haiku for extraction.",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Allowed tool names. Empty = all tools (only for L0/L4). "
        "L1 agents get 3-5 tools.",
    )
    system_prompt: str = Field(
        default="",
        description="Additional instructions prepended to the agent's system prompt",
    )
    source: str = Field(
        default="project",
        description="Where this definition came from: 'builtin', 'user', or 'project'",
    )

    # Specialization metadata
    research_type: ResearchAgentType | None = Field(
        default=None, description="For L1 agents: their research specialization"
    )
    analyst_type: DeliberationAnalystType | None = Field(
        default=None, description="For L1.5 agents: their analytical methodology"
    )


class AgentInstance(BaseModel):
    """A running instance of an agent within an engagement.

    Tracks the agent's lifecycle, resource usage, and isolation state.
    """

    agent_id: str = Field(description="Unique instance ID")
    engagement_id: str = Field(description="Parent engagement for multi-tenancy isolation")
    client_id: str = Field(description="Client identifier for data sandboxing")
    definition: AgentDefinition = Field(description="The agent's definition")
    working_dir: str = Field(
        description="Isolated per-agent working directory (filesystem-based isolation)"
    )
    status: str = Field(
        default="pending",
        description="Agent lifecycle state: pending, running, completed, failed",
    )
    task_ids: list[str] = Field(
        default_factory=list, description="Tasks claimed by this agent"
    )
    tokens_consumed: int = Field(
        default=0, ge=0, description="Total tokens used by this agent"
    )
    cost_usd: float = Field(
        default=0.0, ge=0.0, description="Estimated cost in USD"
    )
