"""Layer 1: Deterministic verification (FActScore, numerical consistency, URL liveness).

No LLM judgment in the verification step itself. LLM is used only for
decomposition (FActScore) and extraction (numerical claims). Verification
is rule-based or network-based.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from keystone.citation.url_check import batch_check_urls
from keystone.evaluator.retry import LLMCallable, retry_llm_call
from keystone.models.citations import CitationManifest
from keystone.models.evaluation import Layer1Result

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


class Layer1Evaluator:
    """Deterministic verification layer.

    Three sub-checks:
    1. FActScore decomposition: atomic fact verification against citations
    2. Numerical consistency: cross-referencing numbers within the document
    3. URL liveness: batch check citation URLs via httpx
    """

    def __init__(self, llm: LLMCallable) -> None:
        self._llm = llm

    async def evaluate(
        self,
        output_text: str,
        manifest: CitationManifest,
    ) -> Layer1Result:
        if not output_text.strip():
            return Layer1Result(
                facts_verified=0,
                facts_failed=0,
                numerical_inconsistencies=[],
                dead_urls=[],
            )

        facts_verified, facts_failed = await self._fact_check(output_text, manifest)
        inconsistencies = await self._numerical_consistency(output_text)
        dead_urls = await self._url_liveness(manifest)

        return Layer1Result(
            facts_verified=facts_verified,
            facts_failed=facts_failed,
            numerical_inconsistencies=inconsistencies,
            dead_urls=dead_urls,
        )

    async def _fact_check(
        self, output_text: str, manifest: CitationManifest
    ) -> tuple[int, int]:
        """FActScore decomposition and verification."""
        template = _load_prompt("fact_decomposition.md")
        citation_texts = "\n".join(
            f"[{c.citation_id}] {c.title} - {c.publication}"
            for c in manifest.citations
        )
        prompt = (
            template
            .replace("{{output_text}}", output_text)
            .replace("{{citation_texts}}", citation_texts)
        )

        raw = await retry_llm_call(
            self._llm, prompt, description="fact_decomposition"
        )
        claims = _parse_json_array(raw)

        verified = sum(1 for c in claims if c.get("status") == "SUPPORTED")
        failed = sum(
            1 for c in claims
            if c.get("status") in ("NOT_SUPPORTED", "CONTRADICTED")
        )
        return verified, failed

    async def _numerical_consistency(self, output_text: str) -> list[str]:
        """Cross-reference numbers within the document."""
        template = _load_prompt("numerical_consistency.md")
        prompt = template.replace("{{output_text}}", output_text)

        raw = await retry_llm_call(
            self._llm, prompt, description="numerical_consistency"
        )
        parsed = _parse_json_object(raw)
        inconsistencies = parsed.get("inconsistencies", [])
        return [
            f"{inc.get('metric', 'unknown')}: {inc.get('value_a')} vs {inc.get('value_b')} "
            f"({inc.get('explanation', '')})"
            for inc in inconsistencies
        ]

    async def _url_liveness(self, manifest: CitationManifest) -> list[str]:
        """Check citation URLs via batch_check_urls."""
        if not manifest.citations:
            return []
        results = await batch_check_urls(manifest.citations)
        return [cid for cid, is_live in results.items() if not is_live]


def _parse_json_array(raw: str) -> list[dict]:
    """Extract a JSON array from LLM output, tolerating markdown fences and trailing text."""
    text = raw.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    logger.warning("Failed to parse JSON array from LLM output: %.100s...", text)
    return []


def _parse_json_object(raw: str) -> dict:
    """Extract a JSON object from LLM output, tolerating markdown fences and trailing text."""
    text = raw.strip()
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start : end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
    logger.warning("Failed to parse JSON object from LLM output: %.100s...", text)
    return {}
