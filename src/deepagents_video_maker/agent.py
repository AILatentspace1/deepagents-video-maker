"""Agent factory for the DeepAgents-native Video-Maker implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .prompts import load_prompt, load_subagent_prompt
from .langchain_tools import build_langchain_tools
from .middleware import VideoMakerUiStateMiddleware


SUBAGENT_NAMES = ["scriptwriter", "remotion-builder"]

_SUBAGENT_SKILL_DIRS = {
    "scriptwriter": ".deepagents/skills/video-maker-v2-scriptwriter",
    "remotion-builder": ".deepagents/skills/video-maker-v2-remotion-builder",
}


def build_subagents(project_root: str | Path | None = None) -> list[dict[str, Any]]:
    """Build DeepAgents subagent configs from native prompt files."""

    root = Path(project_root or Path.cwd()).resolve()
    subagents: list[dict[str, Any]] = []
    for name in SUBAGENT_NAMES:
        spec: dict[str, Any] = {
            "name": name,
            "description": _subagent_description(name),
            "system_prompt": load_subagent_prompt(name),
            "skills": [str(root / _SUBAGENT_SKILL_DIRS[name])],
        }
        subagents.append(spec)
    return subagents


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
    import os

    os.environ.setdefault("ORCHESTRATOR_SKILLS_ROOT", str(root))
    effective_backend = backend or FilesystemBackend(root_dir=root, virtual_mode=True)

    return create_deep_agent(
        model=model,
        tools=build_native_tools(),
        system_prompt=load_prompt("producer"),
        subagents=build_subagents(root),
        middleware=[VideoMakerUiStateMiddleware()],
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
        "scriptwriter": "Writes video-maker-v2 script.md from source-manifest.md and script-contract.json.",
        "remotion-builder": "Builds a standalone Remotion project from approved video-maker-v2 script artifacts.",
        "evaluator": "Evaluates script/manifest artifacts and writes structured eval JSON.",
        "reviewer": "Performs Layer 2 quality review and writes review artifacts.",
        "editor": "Edits or patches scene-level visual/video artifacts.",
        "scene-batch-generator": "Generates batch scene files from script/manifest.",
        "scene-patch-generator": "Patches scene files from render/lint/HITL feedback.",
    }
    return descriptions[name]
