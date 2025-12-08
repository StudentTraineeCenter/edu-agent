"""Utility functions for loading and rendering prompt templates."""

from functools import lru_cache
from pathlib import Path

from jinja2 import Template


@lru_cache
def get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    return Path(__file__).parent / "prompts"


def get_prompt(prompt_name: str) -> str:
    """Load a prompt file.

    Args:
        prompt_name: The prompt file name (without .jinja2 extension)

    Returns:
        The prompt content as a string.

    Raises:
        FileNotFoundError: If the prompt file doesn't exist.
    """
    prompt_path = get_prompts_dir() / f"{prompt_name}.jinja2"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(prompt_name: str, **kwargs) -> str:
    """Load and render a prompt template.

    Args:
        prompt_name: The prompt file name (without .jinja2 extension)
        **kwargs: Variables to pass to the template

    Returns:
        The rendered prompt as a string.
    """
    template_content = get_prompt(prompt_name)
    template = Template(template_content)
    return template.render(**kwargs)