"""LangChain/DeepAgents tool wrappers for video-maker-v2."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .params import parse_video_request
from .serialization import to_jsonable
from .session import init_video_session
from .models import RunInfo
from .build_render_flow import (
    build_remotion_builder_task_description,
    build_publish_readiness_report,
    package_render_output,
    ratify_and_update_build_scenes,
    ratify_and_update_render_package,
    render_remotion_project,
    start_build_scenes_milestone,
    start_render_package_milestone,
)
from .source_flow import start_source_intake_milestone, ratify_and_update_source_intake
from .script_flow import build_scriptwriter_task_description, ratify_and_update_script, start_script_milestone
from .state_store import load_goal_yaml, load_state_yaml, save_state_yaml

try:  # pragma: no cover - depends on optional runtime package
    from langchain_core.tools import tool as _tool
except Exception:  # pragma: no cover
    def _tool(func=None, *args, **kwargs):
        def decorate(inner):
            inner.name = inner.__name__
            return inner
        return decorate(func) if func is not None else decorate


@_tool
def vm_parse_video_request(prompt: str) -> dict[str, Any]:
    """Parse a user video-maker-v2 request into a derived VideoMakerGoal."""
    goal = parse_video_request(prompt)
    return to_jsonable(goal)


@_tool
def vm_init_video_session(
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
    prompt: str | None = None,
    root_dir: str = ".",
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Create a video-maker-v2 output session from structured inputs or a prompt."""
    goal = _goal_from_inputs(
        prompt=prompt,
        topic=topic,
        source=source,
        source_folder=source_folder,
        local_file=local_file,
        notebook_url=notebook_url,
        excalidraw_file=excalidraw_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold,
        eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state = init_video_session(goal, _resolve_project_root(root_dir), timestamp=timestamp)
    return {"goal": to_jsonable(goal), "state": to_jsonable(state), "output_dir": state.output_dir}


@_tool
def vm_load_state(output_dir: str) -> dict[str, Any]:
    """Load state.yaml from an existing video-maker-v2 output directory."""
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    return {"state": to_jsonable(state), "output_dir": output_dir}


@_tool
def vm_start_source_intake(output_dir: str) -> dict[str, Any]:
    """Start the Source Intake milestone."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    run = start_source_intake_milestone(state)
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_ratify_source_intake(
    output_dir: str,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
) -> dict[str, Any]:
    """Write/ratify source-manifest.md and update Source Intake state."""
    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
        source_folder=source_folder,
        local_file=local_file,
        notebook_url=notebook_url,
        excalidraw_file=excalidraw_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold,
        eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    result = ratify_and_update_source_intake(state, goal)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}


@_tool
def vm_start_script(output_dir: str) -> dict[str, Any]:
    """Start the Script milestone after Source Intake passes."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    source_intake = state.milestone("source_intake")
    if source_intake.status.value != "completed":
        return {
            "error": f"Cannot start script milestone: source_intake status is '{source_intake.status.value}' (must be 'completed').",
            "source_intake_status": source_intake.status.value,
            "state": to_jsonable(state),
        }
    run = start_script_milestone(state)
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_build_scriptwriter_task(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
) -> dict[str, Any]:
    """Build strict task description for task(subagent_type='scriptwriter')."""
    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
        source_folder=source_folder,
        local_file=local_file,
        notebook_url=notebook_url,
        excalidraw_file=excalidraw_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold,
        eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    run_dir = Path(output_dir) / "artifacts" / "script" / f"run-{run_number}"
    description = build_scriptwriter_task_description(
        goal,
        state,
        run_info=RunInfo(milestone="script", run_number=run_number, run_dir=str(run_dir)),
    )
    return {"subagent_type": "scriptwriter", "description": description, "run_dir": str(run_dir)}


@_tool
def vm_ratify_script(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
) -> dict[str, Any]:
    """Ratify script.md/script-contract.json and update script milestone state."""
    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
        source_folder=source_folder,
        local_file=local_file,
        notebook_url=notebook_url,
        excalidraw_file=excalidraw_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold,
        eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    result = ratify_and_update_script(state, goal)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}


@_tool
def vm_start_build_scenes(output_dir: str, script_approved: bool = False) -> dict[str, Any]:
    """Start Build Scenes after Script passes and the user explicitly approves."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    try:
        run = start_build_scenes_milestone(state, script_approved=script_approved)
    except RuntimeError as exc:
        return {"error": str(exc), "state": to_jsonable(state)}
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_build_remotion_task(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
) -> dict[str, Any]:
    """Build strict task description for task(subagent_type='remotion-builder')."""
    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
        source_folder=source_folder,
        local_file=local_file,
        notebook_url=notebook_url,
        excalidraw_file=excalidraw_file,
        duration=duration,
        style=style,
        aspect_ratio=aspect_ratio,
        quality_threshold=quality_threshold,
        eval_mode=eval_mode,
        transition_style=transition_style,
    )
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    run_dir = Path(output_dir) / "artifacts" / "build_scenes" / f"run-{run_number}"
    description = build_remotion_builder_task_description(
        goal,
        state,
        run_info=RunInfo(milestone="build_scenes", run_number=run_number, run_dir=str(run_dir)),
    )
    return {"subagent_type": "remotion-builder", "description": description, "run_dir": str(run_dir)}


@_tool
def vm_ratify_build_scenes(output_dir: str) -> dict[str, Any]:
    """Ratify remotion-project minimal structure and update Build Scenes state."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    result = ratify_and_update_build_scenes(state)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}


@_tool
def vm_start_render_package(output_dir: str) -> dict[str, Any]:
    """Start Render Package after Build Scenes passes."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    try:
        run = start_render_package_milestone(state)
    except RuntimeError as exc:
        return {"error": str(exc), "state": to_jsonable(state)}
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_render_remotion_project(
    output_dir: str,
    composition_id: str,
    install: bool = False,
) -> dict[str, Any]:
    """Run pnpm TypeScript, Remotion render, and Remotion still inside remotion-project."""
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    try:
        return render_remotion_project(
            state,
            composition_id=composition_id,
            install=install,
        )
    except RuntimeError as exc:
        return {"error": str(exc), "state": to_jsonable(state)}


@_tool
def vm_package_render_output(
    output_dir: str,
    rendered_video: str | None = None,
    rendered_thumbnail: str | None = None,
) -> dict[str, Any]:
    """Copy Remotion out/video.mp4 and optional thumbnail into final/."""
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    try:
        return package_render_output(
            state,
            rendered_video=rendered_video,
            rendered_thumbnail=rendered_thumbnail,
        )
    except RuntimeError as exc:
        return {"error": str(exc), "state": to_jsonable(state)}


@_tool
def vm_ratify_render_package(output_dir: str) -> dict[str, Any]:
    """Ratify final/video.mp4 and update Render Package state."""
    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    goal = load_goal_yaml(Path(output_dir) / "goal.yaml")
    result = ratify_and_update_render_package(state, duration=goal.duration)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}


@_tool
def vm_build_publish_readiness_report(
    output_dir: str,
    decision: str = "not_reviewed",
    notes: str = "",
) -> dict[str, Any]:
    """Write an advisory post-render publish-readiness checklist artifact."""
    state = load_state_yaml(Path(output_dir) / "state.yaml")
    try:
        return build_publish_readiness_report(state, decision=decision, notes=notes)
    except RuntimeError as exc:
        return {"error": str(exc), "state": to_jsonable(state)}


def build_langchain_tools() -> list[Any]:
    """Return LangChain-compatible video-maker-v2 native tools."""
    return [
        vm_parse_video_request,
        vm_init_video_session,
        vm_load_state,
        vm_start_source_intake,
        vm_ratify_source_intake,
        vm_start_script,
        vm_build_scriptwriter_task,
        vm_ratify_script,
        vm_start_build_scenes,
        vm_build_remotion_task,
        vm_ratify_build_scenes,
        vm_start_render_package,
        vm_render_remotion_project,
        vm_package_render_output,
        vm_ratify_render_package,
        vm_build_publish_readiness_report,
    ]


def _resolve_project_root(root_dir: str) -> Path:
    if root_dir and root_dir != ".":
        return Path(root_dir).resolve()
    env_root = os.environ.get("ORCHESTRATOR_SKILLS_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _goal_from_inputs(
    *,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
    source_folder: str | None = None,
    local_file: str | None = None,
    notebook_url: str | None = None,
    excalidraw_file: str | None = None,
    duration: str | None = None,
    style: str | None = None,
    aspect_ratio: str | None = None,
    quality_threshold: int | None = None,
    eval_mode: str | None = None,
    transition_style: str | None = None,
):
    if any(
        value is not None
        for value in [
            topic,
            source,
            source_folder,
            local_file,
            notebook_url,
            excalidraw_file,
            duration,
            style,
            aspect_ratio,
            quality_threshold,
            eval_mode,
            transition_style,
        ]
    ):
        if not topic:
            raise ValueError("topic is required when structured inputs are provided")
        goal = parse_video_request(f"topic={topic}")
        if source is not None:
            goal.source = source.replace("_", "-")  # type: ignore[assignment]
        if source_folder is not None:
            goal.source_folder = source_folder
        if local_file is not None:
            goal.local_file = local_file
        if notebook_url is not None:
            goal.notebook_url = notebook_url
        if excalidraw_file is not None:
            goal.excalidraw_file = excalidraw_file
        if duration is not None:
            goal.duration = duration  # type: ignore[assignment]
        if style is not None:
            goal.style = style  # type: ignore[assignment]
        if aspect_ratio is not None:
            goal.aspect_ratio = aspect_ratio  # type: ignore[assignment]
        if quality_threshold is not None:
            goal.quality_threshold = int(quality_threshold)
        if eval_mode is not None:
            goal.eval_mode = eval_mode  # type: ignore[assignment]
        if transition_style is not None:
            goal.transition_style = transition_style
        from .params import derive_video_params
        return derive_video_params(goal)

    if not prompt:
        raise ValueError("prompt or structured inputs are required")
    return parse_video_request(prompt)


def _goal_from_inputs_or_goal_file(*, output_dir: str, **kwargs):
    has_inputs = kwargs.get("prompt") or any(
        kwargs.get(key) is not None
        for key in [
            "topic",
            "source",
            "source_folder",
            "local_file",
            "notebook_url",
            "excalidraw_file",
            "duration",
            "style",
            "aspect_ratio",
            "quality_threshold",
            "eval_mode",
            "transition_style",
        ]
    )
    if has_inputs:
        return _goal_from_inputs(**kwargs)
    return load_goal_yaml(Path(output_dir) / "goal.yaml")
