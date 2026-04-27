"""Session creation for DeepAgents-native Video-Maker."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import MilestoneState, MilestoneStatus, RunInfo, VideoMakerGoal, VideoMakerState
from .state_store import save_goal_yaml, save_state_yaml


DEFAULT_MILESTONES = ("research", "script", "assets", "assembly")


def init_video_session(
    goal: VideoMakerGoal,
    root_dir: str | Path,
    *,
    timestamp: str | None = None,
) -> VideoMakerState:
    """Create a video-maker output session and write goal/state files."""

    root = Path(root_dir)
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "output" / f"{stamp}-video-{goal.slug()}"

    for relative in [
        "artifacts/research",
        "artifacts/script",
        "artifacts/assets/visual_director",
        "final",
        "ratify",
    ]:
        (output_dir / relative).mkdir(parents=True, exist_ok=True)

    state = VideoMakerState(
        output_dir=str(output_dir),
        milestones=[MilestoneState(id=name) for name in DEFAULT_MILESTONES],
        todos=[
            {"content": "Research milestone", "status": "pending"},
            {"content": "Script milestone", "status": "pending"},
            {"content": "Assets milestone", "status": "pending"},
            {"content": "Assembly milestone", "status": "pending"},
        ],
    )
    save_goal_yaml(goal, output_dir / "goal.yaml")
    save_state_yaml(state, output_dir / "state.yaml")
    return state


def create_milestone_run(state: VideoMakerState, milestone_id: str) -> RunInfo:
    milestone = state.milestone(milestone_id)
    existing = sorted(
        (Path(state.output_dir) / "artifacts" / milestone_id).glob("run-*"),
        key=lambda item: item.name,
    )
    run_number = len(existing) + 1
    milestone.current_run = run_number
    milestone.status = MilestoneStatus.IN_PROGRESS
    if not milestone.started_at:
        milestone.started_at = datetime.now().isoformat(timespec="seconds")
    run_dir = Path(state.output_dir) / "artifacts" / milestone_id / f"run-{run_number}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return RunInfo(milestone=milestone_id, run_number=run_number, run_dir=str(run_dir))
