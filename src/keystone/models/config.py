"""Configuration models for the Keystone Intelligence Engine.

Application configuration uses PydanticSettings for environment variables.
Engagement configuration is YAML-loadable for per-project overrides.
Model mixing settings define which model tier serves which pipeline layer.

The :class:`PipelineConfig` is the single source of truth for pipeline
behavior knobs — per-layer model tiers, per-layer reasoning effort
overrides, research concurrency, evaluator thresholds, deliberation
thresholds, and L5 ensemble thresholds. Changing any of those should be
an environment-variable or constructor-parameter change, not a source
edit. Env vars use the ``PIPELINE__`` prefix with ``__`` nested delimiter,
e.g. ``PIPELINE__RESEARCH_QUALITY_THRESHOLD=0.9``.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
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
    crossref_mailto: str = Field(default="", description="Polite pool email for CrossRef API")
    semantic_scholar_api_key: str = Field(default="", description="Semantic Scholar API key")
    openalex_mailto: str = Field(default="", description="Polite pool email for OpenAlex API")


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


class RetrievalConfig(BaseModel):
    """Retrieval service configuration.

    Holds connection parameters for the pgvector-backed document store
    and the minimum viable knobs for the hybrid-search pipeline. The
    default ``database_url`` targets a locally installed PostgreSQL 17
    without credentials; production deployments override via the
    ``KEYSTONE_DATABASE_URL`` env var on :class:`AppConfig`.
    """

    database_url: str = Field(
        default="postgresql://localhost/keystone",
        description=(
            "asyncpg DSN for the pgvector-backed retrieval store. Must use "
            "the plain postgresql:// scheme (asyncpg does not accept the "
            "+asyncpg suffix used by SQLAlchemy)."
        ),
    )
    embedding_dimension: int = Field(
        default=1024,
        ge=64,
        le=4096,
        description="Dimensionality of the embedding vectors stored in pgvector.",
    )
    voyage_model: str = Field(
        default="voyage-finance-2",
        description="Voyage embedding model. Finance-tuned by default.",
    )
    cohere_rerank_model: str = Field(
        default="rerank-v3.5",
        description="Cohere reranker model (cross-encoder).",
    )
    chunk_size_tokens: int = Field(
        default=384,
        ge=64,
        le=2048,
        description="Target chunk size in tokens (word-count proxy).",
    )
    chunk_overlap_tokens: int = Field(
        default=64,
        ge=0,
        le=512,
        description="Token overlap between adjacent chunks when a passage is split.",
    )
    hybrid_top_k_candidates: int = Field(
        default=150,
        ge=10,
        le=1000,
        description="Per-branch candidate pool size before RRF fusion.",
    )
    rerank_top_k: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Final top-k returned after reranking.",
    )
    rrf_k: int = Field(
        default=60,
        ge=1,
        description="Reciprocal Rank Fusion damping constant (standard value is 60).",
    )


class RateLimitConfig(BaseModel):
    """Rate limiting configuration per provider."""

    max_parallel_agents: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent research agents. Start at 3-5, tier up organically.",
    )
    provider_rpm: int = Field(default=60, description="LLM provider API requests per minute")
    exa_rpm: int = Field(default=100, description="Exa API requests per minute")
    brave_rpm: int = Field(default=100, description="Brave Search API requests per minute")


class ModelMixingConfig(BaseModel):
    """Which model tier serves each pipeline layer.

    Default: Flagship for judgment-heavy layers, Standard for throughput
    and extraction work that still requires Sonnet-class reasoning, Fast
    for pure extraction/classification. The spec-engine per-step split
    (classifier/task-generator at STANDARD, decomposer lenses at STANDARD
    with FLAGSHIP synthesis, clarifier/validator/scorer at FLAGSHIP) is
    expressed as individual fields so operators can retune each step
    without patching source.
    """

    l0_specification: str = Field(default="flagship", description="Specification Engine model tier")
    # Per-step overrides for the specification engine. Each step is named
    # so operators can retune without patching source.
    l0_engagement_classifier: str = Field(
        default="standard",
        description="Step 1 (engagement classifier) model tier — classification task",
    )
    l0_intent_clarifier: str = Field(
        default="flagship",
        description="Step 2 (intent clarifier) model tier — judgment task",
    )
    l0_decomposer_lens: str = Field(
        default="standard",
        description="Step 3 (decomposer per-lens) model tier — parallel lens analyses",
    )
    l0_decomposer_synth: str = Field(
        default="flagship",
        description="Step 3 (decomposer synthesis) model tier — meta synthesis",
    )
    l0_mece_validator: str = Field(
        default="flagship",
        description="Step 4 (MECE validator) model tier — judgment task",
    )
    l0_priority_scorer: str = Field(
        default="flagship",
        description="Step 5 (priority scorer) model tier — judgment task",
    )
    l0_task_generator: str = Field(
        default="standard",
        description="Step 7 (task generator) model tier — schema emission",
    )
    l1_research: str = Field(default="standard", description="Research Agent model tier")
    l1_5_analysts: str = Field(default="standard", description="Deliberation analyst model tier")
    l1_5_aggregator: str = Field(
        default="flagship", description="Deliberation aggregator model tier"
    )
    l2_structuring: str = Field(default="standard", description="Content structuring model tier")
    l3_generation: str = Field(default="standard", description="Deliverable generation model tier")
    # Layer 1 (Evaluator) fact decomposition and numerical extraction. Sonnet
    # reasoning is enough for extraction work; Opus is unnecessary here.
    l4_extraction: str = Field(
        default="standard",
        description="Layer 1 evaluator (fact decomposition + numerics) tier",
    )
    # Layer 3 rubric scoring keeps flagship. This is the judgment step.
    l4_evaluator: str = Field(default="flagship", description="Evaluator Layer 3 rubric tier")
    extraction: str = Field(default="fast", description="Extraction/classification model tier")


# Layer-name keys used by :class:`PipelineConfig.layer_effort_overrides`.
# The LLM factory reads this mapping to resolve per-layer reasoning effort.
# L0 runs at xhigh (maximum reasoning depth — most critical layer).
# L4 evaluator at high. Extraction at low.
_DEFAULT_LAYER_EFFORTS: dict[str, str] = {
    "l0_specification": "xhigh",
    "l0_engagement_classifier": "medium",
    "l0_intent_clarifier": "xhigh",
    "l0_decomposer_lens": "medium",
    "l0_decomposer_synth": "xhigh",
    "l0_mece_validator": "xhigh",
    "l0_priority_scorer": "xhigh",
    "l0_task_generator": "medium",
    "l1_research": "medium",
    "l1_5_analysts": "medium",
    "l1_5_aggregator": "xhigh",
    "l2_structuring": "medium",
    "l3_generation": "medium",
    "l4_extraction": "medium",
    "l4_evaluator": "high",
    "extraction": "low",
}


class PipelineConfig(BaseModel):
    """Pipeline-wide behavior knobs.

    Holds every tunable that was previously a module-level constant or a
    hardcoded literal: per-layer model tier assignments, per-layer
    reasoning effort, research concurrency and quality thresholds,
    evaluator pass threshold, evaluator L3/L4 blend weight, deliberation
    dispute variance and WWHTB confidence thresholds, and the L5 low-
    agreement threshold. Default instance reproduces prior hardcoded
    behavior so unchanged call sites see no behavior change.

    Operators override via env vars (``PIPELINE__<field>=...``) or by
    passing a constructed instance to :class:`AppConfig` / the LLM
    factory / :class:`Pipeline`.
    """

    model_config = ConfigDict(frozen=False)

    # Model selection
    model_mixing: ModelMixingConfig = Field(
        default_factory=ModelMixingConfig,
        description="Per-layer model tier assignments",
    )
    layer_effort_overrides: dict[str, str] = Field(
        default_factory=lambda: dict(_DEFAULT_LAYER_EFFORTS),
        description=(
            "Per-layer reasoning-effort overrides. Keys match pipeline layer "
            "names (e.g. 'l0_specification'); values are 'low'/'medium'/'high'/'xhigh'."
        ),
    )

    # Research (L1) knobs
    research_default_rounds: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Default iterative research rounds per agent.",
    )
    research_max_rounds: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Hard cap on research rounds regardless of constructor input.",
    )
    research_quality_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum claim confidence that short-circuits further rounds.",
    )
    claude_cli_concurrency: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Global ceiling on simultaneous ``claude -p`` processes.",
    )
    research_concurrency: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Global ceiling on simultaneous deep-research ``claude -p`` sessions.",
    )
    deep_research_timeout_s: int = Field(
        default=1200,
        ge=60,
        description="Timeout (seconds) for a deep-research ``claude -p`` call.",
    )

    # Evaluator knobs
    evaluator_pass_threshold: float = Field(
        default=60.0,
        ge=0.0,
        le=100.0,
        description="Composite score threshold above which evaluation passes.",
    )
    evaluator_layer3_weight: float = Field(
        default=0.8,
        gt=0.0,
        le=1.0,
        description="Weight applied to L3 content score when blending with L4 process score.",
    )

    # Deliberation knobs
    dispute_variance_threshold: float = Field(
        default=0.04,
        ge=0.0,
        le=1.0,
        description=(
            "Variance of analyst confidences above which a claim is routed to the "
            "judge LLM for selection. 0.04 ≈ stddev 0.2 (a 20-point spread)."
        ),
    )
    wwhtb_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Confidence below which 'What Would You Have to Believe?' fires.",
    )

    # L5 ensemble knobs
    l5_low_agreement_threshold: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description=(
            "Agreement-level below which the l5_low_agreement governance gate fires "
            "(judges disagreed on > (1 - threshold) of dimensions)."
        ),
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

    # LLM provider
    llm_provider: str = Field(
        default="claude_cli",
        description="LLM provider: claude_cli, api_key, or codex_oauth",
    )

    # Model IDs
    flagship_model: str = Field(default="claude-opus-4-6")
    standard_model: str = Field(default="claude-sonnet-4-6")
    fast_model: str = Field(default="claude-haiku-4-5")

    # Evaluation
    prometheus_model_path: str | None = Field(default=None)

    # Retrieval stack
    keystone_database_url: str = Field(
        default="postgresql://localhost/keystone",
        description="asyncpg DSN for the pgvector-backed retrieval store.",
    )
    voyage_api_key: str = Field(default="", description="Voyage AI API key")
    cohere_api_key: str = Field(default="", description="Cohere API key")

    # Pipeline behavior — see :class:`PipelineConfig` for the full field list.
    # Env vars route through the nested-delimiter prefix, e.g.
    # ``PIPELINE__RESEARCH_QUALITY_THRESHOLD=0.9`` or
    # ``PIPELINE__LAYER_EFFORT_OVERRIDES='{"l0_specification": "xhigh"}'``.
    pipeline: PipelineConfig = Field(
        default_factory=PipelineConfig,
        description="Pipeline behavior knobs (model tiers, efforts, thresholds)",
    )


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
    max_tasks: int = Field(default=50, ge=5, le=100, description="Max tasks for decomposition")
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
