"""LangChain/DeepAgents tool wrappers for native video-maker functions.

The wrappers expose primitive JSON-compatible inputs/outputs so the Producer
can call them reliably. Importing this module does not require LangChain; if
`langchain_core` is absent, the decorator is a no-op for unit tests.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .params import parse_video_request
from .research_flow import (
    build_researcher_task_description,
    ratify_and_update_research,
    start_research_milestone,
)
from .serialization import to_jsonable
from .session import init_video_session
from .models import RunInfo
from .script_flow import (
    build_scriptwriter_task_description,
    ratify_and_update_script,
    start_script_milestone,
)
from .state_store import load_goal_yaml, load_state_yaml, save_state_yaml
from .models import EvalSample
from .training_data import append_eval_sample


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
    """Parse a user video-maker request into a derived VideoMakerGoal."""

    goal = parse_video_request(prompt)
    return to_jsonable(goal)


@_tool
def vm_init_video_session(
    topic: str | None = None,
    source: str | None = None,
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
    """Create a video-maker output session from structured inputs or a prompt."""

    goal = _goal_from_inputs(
        prompt=prompt,
        topic=topic,
        source=source,
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
def vm_start_research(output_dir: str) -> dict[str, Any]:
    """Start the research milestone and create the next research run."""

    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    run = start_research_milestone(state)
    save_state_yaml(state, state_path)
    return {"state": to_jsonable(state), "run": to_jsonable(run)}


@_tool
def vm_load_state(output_dir: str) -> dict[str, Any]:
    """Load state.yaml from an existing video-maker output directory."""

    state = load_state_yaml(Path(output_dir) / "state.yaml")
    return {"state": to_jsonable(state), "output_dir": output_dir}


@_tool
def vm_build_researcher_task(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
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
    """Build the strict task description for task(subagent_type='researcher')."""

    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
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
    run_dir = Path(output_dir) / "artifacts" / "research" / f"run-{run_number}"
    description = build_researcher_task_description(
        goal,
        state,
        run_info=RunInfo(milestone="research", run_number=run_number, run_dir=str(run_dir)),
    )
    return {"subagent_type": "researcher", "description": description, "run_dir": str(run_dir)}


@_tool
def vm_ratify_research(
    output_dir: str,
    run_number: int = 1,
    prompt: str | None = None,
    topic: str | None = None,
    source: str | None = None,
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
    """Ratify research.md and update research milestone state."""

    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
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
    result = ratify_and_update_research(state, goal)
    save_state_yaml(state, state_path)
    return {"result": to_jsonable(result), "state": to_jsonable(state)}


@_tool
def vm_start_script(output_dir: str) -> dict[str, Any]:
    """Start the script milestone and create the next run dir."""

    state_path = Path(output_dir) / "state.yaml"
    state = load_state_yaml(state_path)
    research = state.milestone("research")
    if research.status.value != "completed":
        # Return a structured error instead of raising — crashing the stream is not helpful.
        return {
            "error": (
                f"Cannot start script milestone: research status is '{research.status.value}' "
                "(must be 'completed'). "
                "Call vm_ratify_research first and ensure it passes before calling vm_start_script."
            ),
            "research_status": research.status.value,
            "retry_count": research.retry_count,
            "max_retries": research.max_retries,
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
    """Ratify script.md/manifest.json and update script milestone state."""

    goal = _goal_from_inputs_or_goal_file(
        output_dir=output_dir,
        prompt=prompt,
        topic=topic,
        source=source,
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
def vm_record_eval_sample(
    output_dir: str,
    session_id: str,
    topic: str,
    style: str,
    duration: str,
    eval_round: int,
    script_text: str,
    eval_score: float,
    eval_pass: bool,
    dimensions: list[dict] | None = None,
    iteration_fixes: list[dict] | None = None,
    contract_violations: list[dict] | None = None,
) -> dict[str, Any]:
    """Record a (script, score, suggestions) triplet as a training data sample.

    Call this after each GAN Evaluator round in the Script milestone to
    accumulate data for future Generator / Evaluator fine-tuning (Phase 2+).
    The sample is appended to ``{output_dir}/training/eval-samples.jsonl``.
    """
    sample = EvalSample(
        session_id=session_id,
        topic=topic,
        style=style,
        duration=duration,
        eval_round=eval_round,
        script_text=script_text,
        eval_score=float(eval_score),
        eval_pass=bool(eval_pass),
        dimensions=dimensions or [],
        iteration_fixes=iteration_fixes or [],
        contract_violations=contract_violations or [],
    )
    path = append_eval_sample(output_dir, sample)
    return {"recorded": True, "path": str(path)}


def build_langchain_tools() -> list[Any]:
    """Return LangChain-compatible native tools."""

    return [
        vm_parse_video_request,
        vm_init_video_session,
        vm_load_state,
        vm_start_research,
        vm_build_researcher_task,
        vm_ratify_research,
        vm_start_script,
        vm_build_scriptwriter_task,
        vm_ratify_script,
        vm_record_eval_sample,
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
            # Normalize underscore variant (local_file) → hyphen (local-file)
            goal.source = source.replace("_", "-")  # type: ignore[assignment]
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
