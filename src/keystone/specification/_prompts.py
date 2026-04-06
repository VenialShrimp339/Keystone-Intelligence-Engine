"""Prompt template loading and rendering for the Specification Engine."""

from __future__ import annotations

import json
import re
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and substitute {{placeholders}}.

    Args:
        name: Template filename (without .md extension).
        **kwargs: Placeholder values. Keys map to {{key}} in the template.

    Returns:
        Rendered prompt string.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    template = path.read_text()
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


def extract_json(text: str) -> dict:
    """Extract JSON object from an LLM response.

    Handles responses wrapped in ```json ... ``` fences or raw JSON.
    """
    # Try to find fenced JSON block
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"No JSON found in LLM response: {text[:200]}...")
