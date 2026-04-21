"""Prompt template loading for the Research layer."""

from __future__ import annotations

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


__all__ = ["load_prompt"]
