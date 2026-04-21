"""Prompt template loading for the Research layer."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter (---...---) from a prompt template if present."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template and substitute {{placeholders}}.

    Args:
        name: Template filename (without .md extension).
        **kwargs: Placeholder values. Keys map to {{key}} in the template.

    Returns:
        Rendered prompt string.
    """
    path = _PROMPTS_DIR / f"{name}.md"
    template = _strip_frontmatter(path.read_text())
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template


__all__ = ["load_prompt"]
