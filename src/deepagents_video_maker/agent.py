"""Agent factory for the DeepAgents-native Video-Maker implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from .prompts import load_prompt, load_subagent_prompt
from .langchain_tools import build_langchain_tools


SUBAGENT_NAMES = ["researcher", "scriptwriter"]

_SUBAGENT_SKILL_DIRS = {
    "researcher": ".deepagents/skills/video-researcher",
    "scriptwriter": ".deepagents/skills/video-scriptwriter",
}


def build_subagents(project_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Build DeepAgents subagent configs from native prompt files."""

    root = Path(project_root or Path.cwd()).resolve()
    return [
        {
            "name": name,
            "description": _subagent_description(name),
            "system_prompt": load_subagent_prompt(name),
            "skills": [str(root / _SUBAGENT_SKILL_DIRS[name])],
        }
        for name in SUBAGENT_NAMES
    ]


def build_native_tools() -> list[Callable[..., Any]]:
    """Return LangChain/DeepAgents-compatible native tools."""

    return build_langchain_tools()


def create_video_maker_agent(
    model: Any,
    *,
    project_root: str | Path | None = None,
    interrupt: bool = False,
    backend: Any | None = None,
    checkpointer: Any | None = None,
):
    """Create a DeepAgents-native video-maker agent.

    This factory intentionally keeps LangGraph as the DeepAgents runtime only;
    it does not split milestones into hand-written LangGraph nodes.
    """

    try:
        from deepagents import create_deep_agent
        from deepagents.backends import FilesystemBackend
    except ImportError as exc:  # pragma: no cover - depends on optional runtime
        raise RuntimeError(
            "DeepAgents runtime is required to create the native video-maker agent."
        ) from exc

    root = Path(project_root or Path.cwd()).resolve()
    os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(root))
    effective_backend = backend or FilesystemBackend(root_dir=root, virtual_mode=True)

    return create_deep_agent(
        model=model,
        tools=build_native_tools(),
        system_prompt=load_prompt("producer"),
        subagents=build_subagents(root),
        backend=effective_backend,
        checkpointer=checkpointer,
        interrupt_on=(
            {
                "write_file": True,
                "edit_file": True,
            }
            if interrupt
            else None
        ),
        name="video-maker-producer",
    )


def _subagent_description(name: str) -> str:
    descriptions = {
        "researcher": "Collects structured research and writes research.md.",
        "scriptwriter": "Writes script.md and manifest.json from research artifacts.",
        "evaluator": "Evaluates script/manifest artifacts and writes structured eval JSON.",
        "reviewer": "Performs Layer 2 quality review and writes review artifacts.",
        "editor": "Edits or patches scene-level visual/video artifacts.",
        "scene-batch-generator": "Generates batch scene files from script/manifest.",
        "scene-patch-generator": "Patches scene files from render/lint/HITL feedback.",
    }
    return descriptions[name]
