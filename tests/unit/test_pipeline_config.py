"""Configuration-system coverage.

Exercises the :class:`PipelineConfig` wiring introduced alongside the
audit-driven model-tier normalization. Covers:

- AppConfig.pipeline defaults match legacy hardcoded constants.
- ``LayerAwareLLMFactory.for_layer`` resolves tier and effort from
  :class:`PipelineConfig`.
- Per-layer effort overrides are honored (L0 gets xhigh, L4 gets high).
- Env vars route through the nested-delimiter prefix (PIPELINE__...).
- The orchestrator threads :class:`PipelineConfig` into downstream
  components that used to read module-level constants (Deliberation's
  dispute-variance threshold, WWHTB confidence threshold, Evaluator
  pass threshold + layer3 blend weight, research rounds / quality
  threshold, L5 low-agreement threshold).
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from keystone.llm_client import (
    LayerAwareLLMFactory,
    _build_llm_callable,
    create_llm_factory,
    get_llm_for_tier,
)
from keystone.llm_settings import (
    LAYER_REASONING_EFFORT,
    get_layer_effort,
    get_layer_tier,
)
from keystone.models.config import (
    AppConfig,
    ModelMixingConfig,
    PipelineConfig,
)
from keystone.models.tasks import ModelTier


# ---- PipelineConfig defaults --------------------------------------------


class TestPipelineConfigDefaults:
    def test_default_instance_reproduces_hardcoded_constants(self):
        pc = PipelineConfig()
        # Research (research_agent.py historic defaults).
        assert pc.research_default_rounds == 3
        assert pc.research_max_rounds == 5
        assert pc.research_quality_threshold == 0.8
        # Deliberation (aggregator.py + wwhtb.py historic constants).
        assert pc.dispute_variance_threshold == 0.04
        assert pc.wwhtb_confidence_threshold == 0.6
        # Evaluator (evaluator.py historic constants).
        assert pc.evaluator_pass_threshold == 60.0
        assert pc.evaluator_layer3_weight == 0.8
        # L5 governance (policy.py historic constant).
        assert pc.l5_low_agreement_threshold == 0.30
        # Claude CLI concurrency (llm_client.py historic constants).
        assert pc.claude_cli_concurrency == 10
        assert pc.research_concurrency == 5
        # Deep research timeout (increased from 1200 to 2400 after first pipeline run).
        assert pc.deep_research_timeout_s == 2400

    def test_layer_effort_overrides_include_critical_layers(self):
        pc = PipelineConfig()
        # L0 is the most critical layer — xhigh reasoning effort.
        assert pc.layer_effort_overrides["l0_specification"] == "xhigh"
        # Spec-engine per-step: classifier is STANDARD/medium;
        # synthesis/validator/scorer are FLAGSHIP/xhigh.
        assert pc.layer_effort_overrides["l0_engagement_classifier"] == "medium"
        assert pc.layer_effort_overrides["l0_decomposer_synth"] == "xhigh"
        assert pc.layer_effort_overrides["l0_mece_validator"] == "xhigh"
        # L4 evaluator runs at high (not xhigh).
        assert pc.layer_effort_overrides["l4_evaluator"] == "high"
        # L1 evaluator extraction runs at medium (Sonnet).
        assert pc.layer_effort_overrides["l4_extraction"] == "medium"

    def test_model_mixing_defaults_map_fixes(self):
        mixing = ModelMixingConfig()
        # Phase 2B: Layer 1 evaluator extraction -> STANDARD.
        assert mixing.l4_extraction == "standard"
        # Phase 2C: Spec engine per-step tiers.
        assert mixing.l0_engagement_classifier == "standard"
        assert mixing.l0_task_generator == "standard"
        assert mixing.l0_intent_clarifier == "flagship"
        assert mixing.l0_mece_validator == "flagship"
        assert mixing.l0_priority_scorer == "flagship"
        # Phase 2D: Decomposer split — lens STANDARD, synth FLAGSHIP.
        assert mixing.l0_decomposer_lens == "standard"
        assert mixing.l0_decomposer_synth == "flagship"

    def test_app_config_nests_pipeline_config(self):
        c = AppConfig()
        assert isinstance(c.pipeline, PipelineConfig)
        # Confirm default layer-effort table is accessible through AppConfig.
        assert c.pipeline.layer_effort_overrides["l0_specification"] == "xhigh"


class TestLegacyLayerEffortExport:
    def test_llm_settings_exports_match_default(self):
        # Legacy import path must continue to resolve.
        pc = PipelineConfig()
        assert LAYER_REASONING_EFFORT == pc.layer_effort_overrides


# ---- get_layer_tier / get_layer_effort ----------------------------------


class TestLayerTierResolution:
    def test_layer_tier_reads_model_mixing(self):
        pc = PipelineConfig()
        assert get_layer_tier("l0_engagement_classifier", pc) == ModelTier.STANDARD
        assert get_layer_tier("l0_decomposer_synth", pc) == ModelTier.FLAGSHIP
        assert get_layer_tier("l4_extraction", pc) == ModelTier.STANDARD
        assert get_layer_tier("l4_evaluator", pc) == ModelTier.FLAGSHIP

    def test_unknown_layer_defaults_to_standard(self):
        pc = PipelineConfig()
        assert get_layer_tier("nonexistent_layer", pc) == ModelTier.STANDARD

    def test_layer_effort_override_wins_over_tier_default(self):
        pc = PipelineConfig()
        # L0 is FLAGSHIP, whose tier default is 'high', but the layer
        # override is 'xhigh'. Override must win.
        tier = get_layer_tier("l0_specification", pc)
        assert tier == ModelTier.FLAGSHIP
        assert get_layer_effort("l0_specification", tier, pc) == "xhigh"

    def test_layer_effort_falls_back_to_tier_default(self):
        pc = PipelineConfig(layer_effort_overrides={})
        # Without an override, effort comes from tier default (medium for STANDARD).
        assert get_layer_effort("anything", ModelTier.STANDARD, pc) == "medium"
        assert get_layer_effort("anything", ModelTier.FLAGSHIP, pc) == "high"
        assert get_layer_effort("anything", ModelTier.FAST, pc) == "low"


# ---- LayerAwareLLMFactory ------------------------------------------------


class TestLayerAwareLLMFactory:
    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    def test_callable_interface_returns_llmcallable(self):
        c = AppConfig(openai_api_key="test")
        f = create_llm_factory(c)
        # __call__(tier) returns an async callable.
        cb = f(ModelTier.FLAGSHIP)
        assert callable(cb)

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    def test_for_layer_uses_config_tier_and_effort(self):
        c = AppConfig(openai_api_key="test")
        f = create_llm_factory(c)
        # All three access patterns resolve.
        assert callable(f.for_layer("l0_specification"))
        assert callable(f.for_layer("l4_extraction"))
        assert callable(f.for_tier(ModelTier.STANDARD, effort="xhigh"))

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    async def test_for_layer_passes_correct_effort_to_api(self):
        """L0 must reach the API with reasoning.effort=xhigh."""
        from unittest.mock import MagicMock

        c = AppConfig(openai_api_key="test")
        f = create_llm_factory(c)

        seen_kwargs: list[dict] = []
        resp = MagicMock(output_text="ok")

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()

            async def capture(**kwargs):
                seen_kwargs.append(kwargs)
                return resp

            mock_client.responses.create = capture
            mock_get.return_value = mock_client

            llm = f.for_layer("l0_specification")
            await llm("probe")

        assert len(seen_kwargs) == 1
        assert seen_kwargs[0]["reasoning"] == {"effort": "xhigh"}

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    async def test_for_layer_l4_evaluator_runs_at_high(self):
        from unittest.mock import MagicMock

        c = AppConfig(openai_api_key="test")
        f = create_llm_factory(c)
        seen_kwargs: list[dict] = []

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()

            async def capture(**kwargs):
                seen_kwargs.append(kwargs)
                return MagicMock(output_text="ok")

            mock_client.responses.create = capture
            mock_get.return_value = mock_client

            llm = f.for_layer("l4_evaluator")
            await llm("probe")

        assert seen_kwargs[0]["reasoning"] == {"effort": "high"}

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    def test_factory_honors_explicit_pipeline_config(self):
        c = AppConfig(openai_api_key="test")
        custom = PipelineConfig(claude_cli_concurrency=3, research_concurrency=2)
        f = LayerAwareLLMFactory(c, pipeline_config=custom)
        assert f.pipeline_config is custom
        # The semaphores must reflect the custom limits.
        assert f._claude_semaphore._value == 3
        assert f._research_semaphore._value == 2


# ---- Claude CLI model resolution honors AppConfig -----------------------


class TestClaudeModelResolution:
    def test_default_matches_app_config(self):
        from keystone.llm_client import _resolve_claude_model

        c = AppConfig()
        assert _resolve_claude_model(ModelTier.FLAGSHIP, c) == c.flagship_model
        assert _resolve_claude_model(ModelTier.STANDARD, c) == c.standard_model
        assert _resolve_claude_model(ModelTier.FAST, c) == c.fast_model
        # LIGHT falls back to fast_model.
        assert _resolve_claude_model(ModelTier.LIGHT, c) == c.fast_model

    def test_overridden_model_ids_flow_through(self):
        from keystone.llm_client import _resolve_claude_model

        c = AppConfig(
            flagship_model="custom-opus",
            standard_model="custom-sonnet",
            fast_model="custom-haiku",
        )
        assert _resolve_claude_model(ModelTier.FLAGSHIP, c) == "custom-opus"
        assert _resolve_claude_model(ModelTier.STANDARD, c) == "custom-sonnet"
        assert _resolve_claude_model(ModelTier.FAST, c) == "custom-haiku"


# ---- get_llm_for_tier accepts optional effort -----------------------------


class TestGetLLMForTierEffort:
    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    async def test_effort_override_threaded_through(self):
        from unittest.mock import MagicMock

        c = AppConfig(openai_api_key="test")
        seen: list[dict] = []

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()

            async def capture(**kw):
                seen.append(kw)
                return MagicMock(output_text="ok")

            mock_client.responses.create = capture
            mock_get.return_value = mock_client

            # Explicit effort override must flow to the API call.
            llm = get_llm_for_tier(ModelTier.STANDARD, c, effort="xhigh")
            await llm("probe")

        assert seen[0]["reasoning"] == {"effort": "xhigh"}

    @patch.dict(os.environ, {"LLM_PROVIDER": "api_key"}, clear=False)
    async def test_no_effort_uses_tier_default(self):
        from unittest.mock import MagicMock

        c = AppConfig(openai_api_key="test")
        seen: list[dict] = []

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()

            async def capture(**kw):
                seen.append(kw)
                return MagicMock(output_text="ok")

            mock_client.responses.create = capture
            mock_get.return_value = mock_client

            llm = get_llm_for_tier(ModelTier.STANDARD, c)
            await llm("probe")

        # STANDARD default is 'medium'.
        assert seen[0]["reasoning"] == {"effort": "medium"}


# ---- Env-var driven overrides --------------------------------------------


class TestEnvVarOverrides:
    def test_research_quality_threshold_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PIPELINE__RESEARCH_QUALITY_THRESHOLD", "0.95")
        c = AppConfig()
        assert c.pipeline.research_quality_threshold == 0.95

    def test_claude_cli_concurrency_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PIPELINE__CLAUDE_CLI_CONCURRENCY", "20")
        c = AppConfig()
        assert c.pipeline.claude_cli_concurrency == 20

    def test_deep_research_timeout_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PIPELINE__DEEP_RESEARCH_TIMEOUT_S", "600")
        c = AppConfig()
        assert c.pipeline.deep_research_timeout_s == 600

    def test_evaluator_pass_threshold_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PIPELINE__EVALUATOR_PASS_THRESHOLD", "75.0")
        c = AppConfig()
        assert c.pipeline.evaluator_pass_threshold == 75.0

    def test_l5_low_agreement_threshold_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PIPELINE__L5_LOW_AGREEMENT_THRESHOLD", "0.5")
        c = AppConfig()
        assert c.pipeline.l5_low_agreement_threshold == 0.5
