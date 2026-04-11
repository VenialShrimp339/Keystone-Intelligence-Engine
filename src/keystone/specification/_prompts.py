"""Prompt template loading and rendering for the Specification Engine."""

from __future__ import annotations

from pathlib import Path

from keystone.llm.parsing import ParseError, safe_llm_json

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

    Delegates to safe_llm_json. Raises ParseError on failure.
    """
    return safe_llm_json(text)


__all__ = ["extract_json", "load_prompt", "ParseError"]
