"""Unit tests for the LLM client factory and settings modules."""

from __future__ import annotations

import asyncio
import json
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI

from keystone.llm_client import (
    CODEX_BASE_URL,
    CodexTokenProvider,
    LLMFactory,
    _call_codex_oauth,
    _call_standard_api,
    _client_cache,
    create_llm_factory,
    create_openai_client,
    get_llm_for_tier,
)
from keystone.llm_settings import (
    LAYER_REASONING_EFFORT,
    TIER_REASONING_EFFORT,
    get_model_id,
    get_reasoning_effort,
)
from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier


# ---- Fixtures ----


@pytest.fixture()
def auth_json_data():
    return {
        "auth_mode": "chatgpt",
        "OPENAI_API_KEY": None,
        "tokens": {
            "id_token": "test-id-token",
            "access_token": "test-access-token-abc123",
            "refresh_token": "test-refresh-token",
            "account_id": "test-account-id",
        },
        "last_refresh": "2026-04-06T12:00:00.000000Z",
    }


@pytest.fixture()
def auth_file(tmp_path, auth_json_data):
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth_json_data))
    return path


@pytest.fixture()
def app_config():
    return AppConfig(
        openai_api_key="test-api-key-xyz",
        flagship_model="gpt-5.4",
        standard_model="gpt-5.4",
        fast_model="gpt-5.4-mini",
    )


@pytest.fixture(autouse=True)
def _clear_client_cache():
    _client_cache.clear()
    yield
    _client_cache.clear()


# ---- CodexTokenProvider ----


class TestCodexTokenProvider:
    async def test_reads_access_token(self, auth_file, auth_json_data):
        provider = CodexTokenProvider(auth_file)
        token = await provider()
        assert token == auth_json_data["tokens"]["access_token"]

    async def test_caches_token_by_mtime(self, auth_file):
        provider = CodexTokenProvider(auth_file)
        t1 = await provider()
        t2 = await provider()
        assert t1 == t2

    async def test_rereads_on_mtime_change(self, auth_file):
        provider = CodexTokenProvider(auth_file)
        t1 = await provider()

        time.sleep(0.05)
        new_data = {
            "auth_mode": "chatgpt",
            "tokens": {"access_token": "new-token-xyz"},
        }
        auth_file.write_text(json.dumps(new_data))

        t2 = await provider()
        assert t2 == "new-token-xyz"
        assert t1 != t2

    async def test_missing_file_raises(self, tmp_path):
        provider = CodexTokenProvider(tmp_path / "nonexistent.json")
        with pytest.raises(FileNotFoundError, match="Codex auth file not found"):
            await provider()

    async def test_missing_access_token_raises(self, tmp_path):
        bad = tmp_path / "auth.json"
        bad.write_text(json.dumps({"tokens": {}}))
        provider = CodexTokenProvider(bad)
        with pytest.raises(ValueError, match="No access_token"):
            await provider()

    async def test_empty_tokens_dict_raises(self, tmp_path):
        bad = tmp_path / "auth.json"
        bad.write_text(json.dumps({"tokens": {"access_token": ""}}))
        provider = CodexTokenProvider(bad)
        with pytest.raises(ValueError, match="No access_token"):
            await provider()

    async def test_concurrent_access(self, auth_file):
        provider = CodexTokenProvider(auth_file)
        results = await asyncio.gather(*(provider() for _ in range(10)))
        assert all(r == results[0] for r in results)


# ---- create_openai_client ----


class TestCreateOpenAIClient:
    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    def test_api_key_auth(self, app_config):
        client = create_openai_client(app_config)
        assert isinstance(client, AsyncOpenAI)

    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    def test_api_key_missing_raises(self):
        config = AppConfig(openai_api_key="")
        with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
            create_openai_client(config)

    def test_oauth_client_base_url(self, app_config, auth_file):
        env = {
            "OPENAI_AUTH_TYPE": "codex_oauth",
            "CODEX_AUTH_FILE": str(auth_file),
        }
        with patch.dict(os.environ, env, clear=False):
            client = create_openai_client(app_config)
            assert isinstance(client, AsyncOpenAI)
            assert str(client.base_url).rstrip("/") == CODEX_BASE_URL

    def test_oauth_default_auth_file(self, app_config):
        env = {"OPENAI_AUTH_TYPE": "codex_oauth"}
        with patch.dict(os.environ, env, clear=False):
            client = create_openai_client(app_config)
            assert isinstance(client, AsyncOpenAI)

    def test_llm_provider_codex_oauth_routes_to_oauth_client(self, app_config, auth_file):
        env = {
            "LLM_PROVIDER": "codex_oauth",
            "CODEX_AUTH_FILE": str(auth_file),
        }
        with patch.dict(os.environ, env, clear=True):
            client = create_openai_client(app_config)
            assert isinstance(client, AsyncOpenAI)
            assert str(client.base_url).rstrip("/") == CODEX_BASE_URL


# ---- get_llm_for_tier ----


class TestStandardAPIPath:
    """Tests for _call_standard_api (api_key auth via api.openai.com)."""

    async def test_uses_responses_create(self):
        """Standard path calls responses.create (non-streaming)."""
        mock_resp = MagicMock()
        mock_resp.output_text = "standard response"
        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(return_value=mock_resp)

        result = await _call_standard_api(mock_client, "gpt-5.4", "medium", "hello")

        assert result == "standard response"
        kw = mock_client.responses.create.call_args.kwargs
        assert kw["model"] == "gpt-5.4"
        assert kw["input"] == "hello"  # plain string, not list
        assert kw["reasoning"] == {"effort": "medium"}
        assert "store" not in kw  # no store constraint
        assert "instructions" not in kw  # instructions optional

    async def test_no_reasoning_when_empty(self):
        mock_resp = MagicMock()
        mock_resp.output_text = "ok"
        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(return_value=mock_resp)

        await _call_standard_api(mock_client, "gpt-5.4", "", "test")

        kw = mock_client.responses.create.call_args.kwargs
        assert "reasoning" not in kw


class TestCodexOAuthPath:
    """Tests for _call_codex_oauth (chatgpt.com backend)."""

    async def test_uses_streaming_with_deltas(self):
        """OAuth path streams and collects text deltas."""
        delta1 = MagicMock(type="response.output_text.delta", delta="he")
        delta2 = MagicMock(type="response.output_text.delta", delta="llo")
        other = MagicMock(type="response.created")

        async def _fake_iter(self):
            for e in (other, delta1, delta2):
                yield e

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        mock_stream.__aiter__ = _fake_iter

        mock_client = MagicMock()
        mock_client.responses.stream = MagicMock(return_value=mock_stream)

        result = await _call_codex_oauth(mock_client, "gpt-5.4", "high", "test")

        assert result == "hello"
        kw = mock_client.responses.stream.call_args.kwargs
        assert kw["input"] == [{"role": "user", "content": "test"}]
        assert kw["instructions"] == "You are a helpful assistant."
        assert kw["store"] is False
        assert kw["reasoning"] == {"effort": "high"}


class TestGetLLMForTier:
    """Tests for get_llm_for_tier routing."""

    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    def test_returns_callable(self, app_config):
        llm = get_llm_for_tier(ModelTier.FLAGSHIP, app_config)
        assert callable(llm)

    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    def test_all_tiers_produce_callable(self, app_config):
        for tier in ModelTier:
            assert callable(get_llm_for_tier(tier, app_config))

    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    async def test_api_key_routes_to_standard(self, app_config):
        """api_key auth routes to _call_standard_api."""
        mock_resp = MagicMock()
        mock_resp.output_text = "std"

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.responses.create = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_client

            llm = get_llm_for_tier(ModelTier.STANDARD, app_config)
            result = await llm("hello")

            assert result == "std"
            mock_client.responses.create.assert_called_once()
            kw = mock_client.responses.create.call_args.kwargs
            assert kw["input"] == "hello"  # plain string
            assert "store" not in kw

    @patch.dict(
        os.environ,
        {"OPENAI_AUTH_TYPE": "codex_oauth", "CODEX_AUTH_FILE": "/tmp/x.json"},
        clear=False,
    )
    async def test_oauth_routes_to_codex_path(self, app_config):
        """codex_oauth auth routes to _call_codex_oauth."""
        delta = MagicMock(type="response.output_text.delta", delta="oauth")

        async def _fake_iter(self):
            yield delta

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        mock_stream.__aiter__ = _fake_iter

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = MagicMock()
            mock_client.responses.stream = MagicMock(return_value=mock_stream)
            mock_get.return_value = mock_client

            llm = get_llm_for_tier(ModelTier.FAST, app_config)
            result = await llm("test")

            assert result == "oauth"
            kw = mock_client.responses.stream.call_args.kwargs
            assert kw["store"] is False
            assert kw["model"] == "gpt-5.4-mini"

    @patch.dict(
        os.environ,
        {"LLM_PROVIDER": "codex_oauth", "CODEX_AUTH_FILE": "/tmp/x.json"},
        clear=True,
    )
    async def test_llm_provider_codex_oauth_uses_oauth_cache_key(self, app_config):
        with patch("keystone.llm_client.create_openai_client") as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client

            get_llm_for_tier(ModelTier.FAST, app_config)

            mock_create.assert_called_once_with(app_config)
            assert "codex_oauth" in _client_cache

    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    async def test_fast_tier_uses_mini_model(self, app_config):
        mock_resp = MagicMock()
        mock_resp.output_text = "ok"

        with patch("keystone.llm_client._get_cached_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.responses.create = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_client

            llm = get_llm_for_tier(ModelTier.FAST, app_config)
            await llm("test")

            kw = mock_client.responses.create.call_args.kwargs
            assert kw["model"] == "gpt-5.4-mini"
            assert kw["reasoning"] == {"effort": "low"}


# ---- LLMFactory ----


class TestLLMFactory:
    @patch.dict(os.environ, {"OPENAI_AUTH_TYPE": "api_key"}, clear=False)
    def test_factory_produces_callables(self, app_config):
        factory = create_llm_factory(app_config)
        for tier in ModelTier:
            assert callable(factory(tier))

    def test_lambda_factory_satisfies_type(self):
        mock_llm: AsyncMock = AsyncMock(return_value="ok")
        factory: LLMFactory = lambda _tier: mock_llm
        assert factory(ModelTier.FLAGSHIP) is mock_llm


# ---- Reasoning effort ----


class TestReasoningEffort:
    def test_flagship(self):
        assert get_reasoning_effort(ModelTier.FLAGSHIP) == "high"

    def test_standard(self):
        assert get_reasoning_effort(ModelTier.STANDARD) == "medium"

    def test_fast(self):
        assert get_reasoning_effort(ModelTier.FAST) == "low"

    def test_light(self):
        assert get_reasoning_effort(ModelTier.LIGHT) == "low"

    def test_all_tiers_mapped(self):
        for tier in ModelTier:
            assert get_reasoning_effort(tier) in ("low", "medium", "high", "xhigh")

    def test_layer_table_complete(self):
        # L0 runs at xhigh (most critical layer), L4 evaluator at high,
        # extraction at low. The spec-engine per-step split and extra
        # L0 substeps make this a superset of the original 6-key table.
        required_layers = {
            "l0_specification",
            "l0_engagement_classifier",
            "l0_intent_clarifier",
            "l0_decomposer_lens",
            "l0_decomposer_synth",
            "l0_mece_validator",
            "l0_priority_scorer",
            "l0_task_generator",
            "l1_research",
            "l1_5_analysts",
            "l1_5_aggregator",
            "l4_extraction",
            "l4_evaluator",
            "extraction",
        }
        assert required_layers.issubset(set(LAYER_REASONING_EFFORT.keys()))
        # L0 is the most critical layer and must run at xhigh.
        assert LAYER_REASONING_EFFORT["l0_specification"] == "xhigh"
        # L4 evaluator runs at high (not xhigh — we accept some cost savings).
        assert LAYER_REASONING_EFFORT["l4_evaluator"] == "high"

    def test_layer_values_valid(self):
        for effort in LAYER_REASONING_EFFORT.values():
            assert effort in ("low", "medium", "high", "xhigh")


# ---- Model ID ----


class TestModelId:
    def test_flagship(self, app_config):
        assert get_model_id(ModelTier.FLAGSHIP, app_config) == "gpt-5.4"

    def test_standard(self, app_config):
        assert get_model_id(ModelTier.STANDARD, app_config) == "gpt-5.4"

    def test_fast(self, app_config):
        assert get_model_id(ModelTier.FAST, app_config) == "gpt-5.4-mini"

    def test_light_uses_fast(self, app_config):
        assert get_model_id(ModelTier.LIGHT, app_config) == "gpt-5.4-mini"

    def test_custom_ids(self):
        cfg = AppConfig(
            openai_api_key="k",
            flagship_model="custom-flag",
            standard_model="custom-std",
            fast_model="custom-fast",
        )
        assert get_model_id(ModelTier.FLAGSHIP, cfg) == "custom-flag"
        assert get_model_id(ModelTier.STANDARD, cfg) == "custom-std"
        assert get_model_id(ModelTier.FAST, cfg) == "custom-fast"
