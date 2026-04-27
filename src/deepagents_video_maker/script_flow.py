"""Native Script milestone flow helpers, mirroring research_flow.py."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .artifacts import script_artifact_paths
from .models import MilestoneStatus, RatifyResult, RunInfo, VideoMakerGoal, VideoMakerState
from .ratify import ratify_script
from .session import create_milestone_run
from .state_store import update_milestone_status


def start_script_milestone(state: VideoMakerState) -> RunInfo:
    research = state.milestone("research")
    if research.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot start script milestone: research status={research.status.value} "
            "(must be completed)"
        )
    return create_milestone_run(state, "script")


def build_scriptwriter_task_description(
    goal: VideoMakerGoal,
    state: VideoMakerState,
    run_info: RunInfo,
) -> str:
    research_run = state.milestone("research").current_run or 1
    research_file = (
        Path(state.output_dir) / "artifacts" / "research" / f"run-{research_run}" / "research.md"
    )
    paths = script_artifact_paths(state.output_dir, run_info.run_number)
    return f"""You are the DeepAgents-native video-maker Scriptwriter subagent.

Input contract:
- topic: {goal.topic}
- duration: {goal.duration}
- style: {goal.style}
- aspect_ratio: {goal.aspect_ratio}
- bgm_file: {goal.bgm_file}
- sfx_enabled: {goal.sfx_enabled}
- research_file: {_to_virtual_path(research_file)}
- script_path: {_to_virtual_path(paths["script"])}
- manifest_path: {_to_virtual_path(paths["manifest"])}
- eval_mode: {goal.eval_mode}

Required behavior:
1. Read research_file with read_file. Do not ask Producer to inline content.
2. Write script.md (Markdown, scenes as `## Scene N`) and manifest.json (JSON with scenes[]).
3. Each manifest scene must include: id, narration, duration.
4. script.md scene count must equal manifest.scenes length.
5. Return only the output contract summary, not full script text.

Output contract:
script_path: {_to_virtual_path(paths["script"])}
manifest_path: {_to_virtual_path(paths["manifest"])}
scene_count: <number>
estimated_duration: <seconds>
blocking_issues: <none or list>
"""


def _to_virtual_path(path: str | Path) -> str:
    item = Path(path).resolve()
    root_env = os.environ.get("ORCHESTRATOR_SKILLS_ROOT")
    if root_env:
        try:
            return "/" + item.relative_to(Path(root_env).resolve()).as_posix()
        except ValueError:
            pass
    return str(path)


def ratify_and_update_script(state: VideoMakerState, goal: VideoMakerGoal) -> RatifyResult:
    milestone = state.milestone("script")
    run_number = milestone.current_run or 1
    paths = script_artifact_paths(state.output_dir, run_number)
    result = ratify_script(paths["script"], paths["manifest"])
    ratify_payload = {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {"id": c.id, "passed": c.passed, "message": c.message, "metadata": c.metadata}
            for c in result.checks
        ],
    }
    if result.passed:
        update_milestone_status(state, "script", MilestoneStatus.COMPLETED, ratify=ratify_payload)
    else:
        milestone.retry_count += 1
        if milestone.retry_count > milestone.max_retries:
            update_milestone_status(
                state,
                "script",
                MilestoneStatus.BLOCKED,
                blocking_reason="script ratify failed after max retries",
                ratify=ratify_payload,
            )
            result.next_action = "block_for_user"
        else:
            update_milestone_status(
                state,
                "script",
                MilestoneStatus.IN_PROGRESS,
                blocking_reason="script ratify failed; retry required",
                ratify=ratify_payload,
            )
            result.next_action = "retry_milestone"
    ratify_dir = Path(state.output_dir) / "ratify"
    ratify_dir.mkdir(parents=True, exist_ok=True)
    (ratify_dir / f"script-run-{run_number}.json").write_text(
        json.dumps(ratify_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result
