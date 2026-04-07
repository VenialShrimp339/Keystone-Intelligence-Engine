"""Integration smoke tests -- real API calls via Codex OAuth.

Run with: pytest tests/integration/test_llm_smoke.py -v -m integration
Consumes API quota. Keep prompts minimal.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

from keystone.llm_client import _client_cache, get_llm_for_tier
from keystone.models.config import AppConfig
from keystone.models.tasks import ModelTier

# Load .env so OPENAI_AUTH_TYPE and CODEX_AUTH_FILE are in os.environ
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _fresh_client():
    _client_cache.clear()
    yield
    _client_cache.clear()


@pytest.fixture()
def live_config() -> AppConfig:
    return AppConfig()


async def test_flagship_text_completion(live_config):
    """Simple text completion with gpt-5.4."""
    llm = get_llm_for_tier(ModelTier.FLAGSHIP, live_config)

    start = time.monotonic()
    async with asyncio.timeout(30):
        result = await llm("Respond with exactly one word: hello")
    elapsed = time.monotonic() - start

    print(f"\n  Model: {live_config.flagship_model}")
    print(f"  Response length: {len(result)} chars")
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Response: {result[:100]}")

    assert len(result) > 0, "Empty response from flagship model"
    assert "hello" in result.lower(), f"Expected 'hello', got: {result[:100]}"


async def test_fast_text_completion(live_config):
    """Simple text completion with gpt-5.4-mini."""
    llm = get_llm_for_tier(ModelTier.FAST, live_config)

    start = time.monotonic()
    async with asyncio.timeout(30):
        result = await llm("Respond with exactly one word: hello")
    elapsed = time.monotonic() - start

    print(f"\n  Model: {live_config.fast_model}")
    print(f"  Response length: {len(result)} chars")
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Response: {result[:100]}")

    assert len(result) > 0, "Empty response from fast model"
    assert "hello" in result.lower(), f"Expected 'hello', got: {result[:100]}"


async def test_structured_json_output(live_config):
    """Structured JSON output from flagship model."""
    llm = get_llm_for_tier(ModelTier.FLAGSHIP, live_config)

    prompt = (
        "Return ONLY valid JSON, no markdown fences, no other text:\n"
        '{"answer": "hello", "model": "gpt-5.4"}'
    )

    start = time.monotonic()
    async with asyncio.timeout(30):
        result = await llm(prompt)
    elapsed = time.monotonic() - start

    print(f"\n  Model: {live_config.flagship_model}")
    print(f"  Response length: {len(result)} chars")
    print(f"  Latency: {elapsed:.2f}s")
    print(f"  Response: {result[:200]}")

    assert len(result) > 0, "Empty response"

    cleaned = result.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    parsed = json.loads(cleaned)
    assert "answer" in parsed, f"Missing 'answer' key: {parsed}"
    print(f"  Parsed JSON: {parsed}")
