"""Per-layer model settings for the Keystone Intelligence Engine.

Bridges :class:`keystone.models.config.PipelineConfig` (the configuration
surface) to the LLM factory (the call-site). Every source for per-tier or
per-layer behavior flows through here so a single ``PipelineConfig`` can
drive tier selection, reasoning effort, and model ID resolution across
every provider path.
"""

from __future__ import annotations

from keystone.models.config import _DEFAULT_LAYER_EFFORTS, AppConfig, PipelineConfig
from keystone.models.tasks import ModelTier

# Default reasoning_effort per model tier. Used as the fallback when a
# layer does not declare its own override in PipelineConfig.
TIER_REASONING_EFFORT: dict[ModelTier, str] = {
    ModelTier.FLAGSHIP: "high",
    ModelTier.STANDARD: "medium",
    ModelTier.FAST: "low",
    ModelTier.LIGHT: "low",
}

# View of the default layer-effort table. The canonical source is
# :data:`keystone.models.config._DEFAULT_LAYER_EFFORTS`, which
# :class:`PipelineConfig.layer_effort_overrides` copies at construction.
# Kept here as a module-level constant so legacy imports continue to
# resolve and operators reading ``from keystone.llm_settings import
# LAYER_REASONING_EFFORT`` still get the current defaults.
LAYER_REASONING_EFFORT: dict[str, str] = dict(_DEFAULT_LAYER_EFFORTS)


def get_reasoning_effort(tier: ModelTier) -> str:
    """Return the default reasoning_effort for a model tier."""
    return TIER_REASONING_EFFORT.get(tier, "medium")


def get_model_id(tier: ModelTier, config: AppConfig) -> str:
    """Return the model ID for a tier from config."""
    mapping: dict[ModelTier, str] = {
        ModelTier.FLAGSHIP: config.flagship_model,
        ModelTier.STANDARD: config.standard_model,
        ModelTier.FAST: config.fast_model,
        ModelTier.LIGHT: config.fast_model,
    }
    return mapping.get(tier, config.standard_model)


def get_layer_tier(layer_name: str, pipeline_config: PipelineConfig) -> ModelTier:
    """Resolve the model tier assigned to a pipeline layer.

    Reads the ``model_mixing`` section of ``pipeline_config``; returns
    :class:`ModelTier.STANDARD` when the layer has no override. Unknown
    tier string values raise ``ValueError`` via the enum constructor so a
    typo in config produces a loud failure, not silent degradation.
    """
    mixing = pipeline_config.model_mixing
    # Introspect the ModelMixingConfig fields directly — the layer names
    # are declared as attributes so we keep one source of truth.
    raw = getattr(mixing, layer_name, None)
    if raw is None:
        return ModelTier.STANDARD
    return ModelTier(raw)


def get_layer_effort(
    layer_name: str,
    tier: ModelTier,
    pipeline_config: PipelineConfig,
) -> str:
    """Resolve the reasoning effort for a pipeline layer.

    Falls back to the tier's default effort when the layer name has no
    explicit override in ``pipeline_config.layer_effort_overrides``.
    """
    override = pipeline_config.layer_effort_overrides.get(layer_name)
    if override is not None:
        return override
    return get_reasoning_effort(tier)
