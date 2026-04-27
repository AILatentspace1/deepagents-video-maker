"""Prompt loading for DeepAgents-native Video-Maker."""

from __future__ import annotations

from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a UTF-8 prompt by relative prompt name.

    Examples:
        load_prompt("producer")
        load_prompt("subagents/researcher")
    """

    normalized = name.strip().removesuffix(".md")
    path = PROMPTS_DIR / f"{normalized}.md"
    try:
        path.relative_to(PROMPTS_DIR)
    except ValueError as exc:
        raise ValueError(f"prompt path escapes prompts dir: {name}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def load_subagent_prompt(name: str) -> str:
    return load_prompt(f"subagents/{name}")

