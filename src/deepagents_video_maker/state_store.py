"""Minimal YAML writers for Phase 1 state files.

The generated YAML intentionally uses a small subset that is human-readable and
stable in tests. A full YAML parser can be introduced later if needed.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import VideoMakerGoal, VideoMakerState
from .models import MilestoneState, MilestoneStatus, WorkflowStatus


def _scalar(value: Any) -> str:
    if value is None:
        return "~"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def save_goal_yaml(goal: VideoMakerGoal, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    data = asdict(goal)
    for key, value in data.items():
        lines.append(f"{key}: {_scalar(value)}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def load_goal_yaml(path: str | Path) -> VideoMakerGoal:
    """Load the small YAML subset emitted by save_goal_yaml."""

    data: dict[str, str] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        data[key.strip()] = _unquote(raw_value.strip())
    if not data.get("topic"):
        raise ValueError(f"goal.yaml missing topic: {path}")
    goal = VideoMakerGoal(topic=data["topic"])
    for key, value in data.items():
        if key == "topic":
            continue
        if value == "~":
            continue
        if key in {"quality_threshold"}:
            setattr(goal, key, int(value))
        elif key in {"bgm_volume"}:
            setattr(goal, key, float(value))
        elif key in {"enable_video_qa", "sfx_enabled"}:
            setattr(goal, key, value.lower() == "true")
        elif hasattr(goal, key):
            setattr(goal, key, value)
    return goal


def save_state_yaml(state: VideoMakerState, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "workflow: video-maker-native",
        f"workflow_status: {state.workflow_status.value}",
        f"created_at: {_scalar(state.created_at)}",
        f"output_dir: {_scalar(state.output_dir)}",
        "milestones:",
    ]
    for milestone in state.milestones:
        lines.extend(
            [
                f"  - id: {milestone.id}",
                f"    status: {milestone.status.value}",
                f"    retry_count: {milestone.retry_count}",
                f"    max_retries: {milestone.max_retries}",
                f"    current_run: {_scalar(milestone.current_run)}",
                f"    started_at: {_scalar(milestone.started_at)}",
                f"    completed_at: {_scalar(milestone.completed_at)}",
                f"    blocking_reason: {_scalar(milestone.blocking_reason)}",
            ]
        )
    lines.append("todos:")
    for todo in state.todos:
        lines.append(f"  - content: {_scalar(todo.get('content', ''))}")
        lines.append(f"    status: {_scalar(todo.get('status', 'pending'))}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def load_state_yaml(path: str | Path) -> VideoMakerState:
    """Load the small YAML subset emitted by save_state_yaml."""

    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    output_dir = ""
    workflow_status = WorkflowStatus.IN_PROGRESS
    created_at = ""
    milestones: list[MilestoneState] = []
    current: MilestoneState | None = None
    in_milestones = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("workflow_status:"):
            workflow_status = WorkflowStatus(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("created_at:"):
            created_at = _unquote(stripped.split(":", 1)[1].strip())
        elif stripped.startswith("output_dir:"):
            output_dir = _unquote(stripped.split(":", 1)[1].strip())
        elif stripped == "milestones:":
            in_milestones = True
        elif stripped == "todos:":
            in_milestones = False
        elif in_milestones and stripped.startswith("- id:"):
            current = MilestoneState(id=stripped.split(":", 1)[1].strip())
            milestones.append(current)
        elif in_milestones and current is not None and ":" in stripped:
            key, raw_value = stripped.split(":", 1)
            value = _unquote(raw_value.strip())
            if key == "status":
                current.status = MilestoneStatus(value)
            elif key == "retry_count":
                current.retry_count = int(value)
            elif key == "max_retries":
                current.max_retries = int(value)
            elif key == "current_run":
                current.current_run = None if value == "~" else int(value)
            elif key == "started_at":
                current.started_at = None if value == "~" else value
            elif key == "completed_at":
                current.completed_at = None if value == "~" else value
            elif key == "blocking_reason":
                current.blocking_reason = None if value == "~" else value

    return VideoMakerState(
        output_dir=output_dir,
        workflow_status=workflow_status,
        created_at=created_at,
        milestones=milestones,
    )


def _unquote(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def update_milestone_status(
    state: VideoMakerState,
    milestone_id: str,
    status: MilestoneStatus | str,
    *,
    blocking_reason: str | None = None,
    ratify: dict[str, Any] | None = None,
) -> VideoMakerState:
    milestone = state.milestone(milestone_id)
    next_status = status if isinstance(status, MilestoneStatus) else MilestoneStatus(status)
    milestone.status = next_status
    if next_status == MilestoneStatus.COMPLETED:
        milestone.completed_at = datetime.now().isoformat(timespec="seconds")
        milestone.blocking_reason = None
    elif blocking_reason is not None:
        milestone.blocking_reason = blocking_reason
    if ratify is not None:
        milestone.ratify = ratify
    return state
