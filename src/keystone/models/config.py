"""Configuration models for the Keystone Intelligence Engine.

Application configuration uses PydanticSettings for environment variables.
Engagement configuration is YAML-loadable for per-project overrides.
Model mixing settings define which model tier serves which pipeline layer.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMProviderConfig(BaseModel):
    """LLM provider API configuration."""

    api_key: str = Field(description="LLM provider API key")
    flagship_model: str = Field(
        default="gpt-5.4",
        description="Model ID for flagship tier (L0/L4 judgment tasks)",
    )
    standard_model: str = Field(
        default="gpt-5.4",
        description="Model ID for standard tier (L1 throughput tasks)",
    )
    fast_model: str = Field(
        default="gpt-5.4-mini",
        description="Model ID for fast tier (extraction/classification)",
    )
    reasoning_effort: str = Field(
        default="medium",
        description="Default reasoning effort: low/medium/high/xhigh",
    )


class SearchAPIConfig(BaseModel):
    """Configuration for external search APIs."""

    exa_api_key: str = Field(default="", description="Exa search API key")
    brave_api_key: str = Field(default="", description="Brave Search API key")
    crossref_mailto: str = Field(
        default="", description="Polite pool email for CrossRef API"
    )
    semantic_scholar_api_key: str = Field(
        default="", description="Semantic Scholar API key"
    )
    openalex_mailto: str = Field(
        default="", description="Polite pool email for OpenAlex API"
    )


class InfraConfig(BaseModel):
    """Infrastructure connection configuration."""

    postgres_url: str = Field(
        default="postgresql+asyncpg://keystone:keystone@localhost:5432/keystone",
        description="PostgreSQL connection string (with pgvector)",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string (caching + rate limiting)",
    )
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server address",
    )
    temporal_namespace: str = Field(
        default="keystone",
        description="Temporal namespace for workflows",
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration per provider."""

    max_parallel_agents: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent research agents. Start at 3-5, tier up organically.",
    )
    provider_rpm: int = Field(
        default=60, description="LLM provider API requests per minute"
    )
    exa_rpm: int = Field(default=100, description="Exa API requests per minute")
    brave_rpm: int = Field(
        default=100, description="Brave Search API requests per minute"
    )


class ModelMixingConfig(BaseModel):
    """Which model tier serves each pipeline layer.

    Default: Flagship for L0/L4 (judgment), Standard for L1 (throughput),
    Fast for extraction/classification. Validated configuration from
    multi-agent research system (90.2% improvement).
    """

    l0_specification: str = Field(
        default="flagship", description="Specification Engine model tier"
    )
    l1_research: str = Field(
        default="standard", description="Research Agent model tier"
    )
    l1_5_analysts: str = Field(
        default="standard", description="Deliberation analyst model tier"
    )
    l1_5_aggregator: str = Field(
        default="flagship", description="Deliberation aggregator model tier"
    )
    l2_structuring: str = Field(
        default="standard", description="Content structuring model tier"
    )
    l3_generation: str = Field(
        default="standard", description="Deliverable generation model tier"
    )
    l4_evaluator: str = Field(
        default="flagship", description="Evaluator model tier"
    )
    extraction: str = Field(
        default="fast", description="Extraction/classification model tier"
    )


class EvaluationConfig(BaseModel):
    """Evaluator-specific configuration."""

    prometheus_model_path: str | None = Field(
        default=None,
        description="Path to local Prometheus 2 model (7B variant for Layer 3)",
    )
    calibration_threshold: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Minimum Spearman correlation for production readiness",
    )
    kappa_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum Cohen's Kappa for production readiness",
    )
    canary_set_size: int = Field(
        default=30,
        ge=20,
        description="Number of pre-scored samples for drift detection",
    )
    recalibration_interval: int = Field(
        default=5,
        ge=1,
        description="Re-calibrate every N engagements",
    )


class AppConfig(BaseSettings):
    """Root application configuration loaded from environment variables.

    Environment variables are loaded from .env file. Each nested config
    section groups related settings.
    """

    model_config = {"env_nested_delimiter": "__"}

    # Provider configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    exa_api_key: str = Field(default="", description="Exa API key")
    brave_search_api_key: str = Field(default="", description="Brave Search API key")

    # Infrastructure
    postgres_url: str = Field(
        default="postgresql+asyncpg://keystone:keystone@localhost:5432/keystone"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    temporal_host: str = Field(default="localhost:7233")
    temporal_namespace: str = Field(default="keystone")

    # Rate limits
    max_parallel_agents: int = Field(default=5)
    provider_rpm_limit: int = Field(default=60)

    # Model IDs
    flagship_model: str = Field(default="gpt-5.4")
    standard_model: str = Field(default="gpt-5.4")
    fast_model: str = Field(default="gpt-5.4-mini")

    # Evaluation
    prometheus_model_path: str | None = Field(default=None)


class EngagementConfig(BaseModel):
    """Per-engagement configuration, loaded from YAML.

    This allows overriding default settings for specific engagements
    (e.g., more agents for complex projects, different model tiers).
    """

    engagement_id: str = Field(description="Unique engagement identifier")
    client_id: str = Field(description="Client identifier for data sandboxing")
    project_name: str = Field(description="Human-readable project name")
    model_mixing: ModelMixingConfig = Field(
        default_factory=ModelMixingConfig,
        description="Model tier assignments for this engagement",
    )
    max_agents: int = Field(
        default=5, ge=1, le=50, description="Max concurrent agents for this engagement"
    )
    max_tasks: int = Field(
        default=50, ge=5, le=100, description="Max tasks for decomposition"
    )
    evaluation_intensity: str = Field(
        default="standard",
        description="Default evaluation intensity: light_touch, standard, deep",
    )
    output_format: str = Field(
        default="markdown", description="Output format: markdown, slides, excel"
    )
    working_dir: Path = Field(
        default=Path("./engagements"),
        description="Base directory for engagement artifacts",
    )
