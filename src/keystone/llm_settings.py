"""Per-layer model settings for the Keystone Intelligence Engine.

Maps model tiers to reasoning_effort values and model IDs.
Based on OPENAI-SWITCHOVER-PLAN.md Decision 1 reasoning_effort table.
"""

from __future__ import annotations

from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier

# Default reasoning_effort per model tier.
# Pipeline layers that need different effort can override at call time.
#
# Reference (OPENAI-SWITCHOVER-PLAN.md):
#   L0 Specification (FLAGSHIP)            -> xhigh
#   L1 Research (STANDARD)                 -> medium
#   L1.5 Deliberation analysts (STANDARD)  -> medium
#   L1.5 Deliberation aggregator (FLAGSHIP)-> xhigh
#   L4 Evaluator (FLAGSHIP)               -> high
#   Extraction/classification (FAST)       -> low
TIER_REASONING_EFFORT: dict[ModelTier, str] = {
    ModelTier.FLAGSHIP: "high",
    ModelTier.STANDARD: "medium",
    ModelTier.FAST: "low",
    ModelTier.LIGHT: "low",
}

# Layer-specific reasoning_effort for when a layer needs different
# effort than the tier default (e.g. L0 wants xhigh on FLAGSHIP).
LAYER_REASONING_EFFORT: dict[str, str] = {
    "l0_specification": "xhigh",
    "l1_research": "medium",
    "l1_5_analysts": "medium",
    "l1_5_aggregator": "xhigh",
    "l4_evaluator": "high",
    "extraction": "low",
}


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
