"""Native Script milestone flow helpers, mirroring research_flow.py."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .artifacts import script_artifact_paths
from .models import MilestoneStatus, RatifyResult, RunInfo, VideoMakerGoal, VideoMakerState
from .ratify import ratify_script
from .session import create_milestone_run
from .state_store import load_goal_yaml, update_milestone_status


def start_script_milestone(
    state: VideoMakerState,
    goal: VideoMakerGoal | None = None,
) -> RunInfo:
    source_intake = state.milestone("source_intake")
    if source_intake.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot start script milestone: source_intake status={source_intake.status.value} "
            "(must be completed)"
        )
    if goal is None:
        goal_path = Path(state.output_dir) / "goal.yaml"
        if goal_path.exists():
            goal = load_goal_yaml(goal_path)
    run = create_milestone_run(state, "script")
    # Only write the contract when the file is absent.  Each new run receives
    # its own path (run-N/script-contract.json) from create_milestone_run(), so
    # this path is always fresh on the first pass; the guard prevents a
    # double-write if start_script_milestone() is somehow called twice for the
    # same run.
    paths = script_artifact_paths(state.output_dir, run.run_number)
    if not paths["contract"].exists():
        _write_script_contract(goal=goal, state=state, run_info=run)
    return run


def build_scriptwriter_task_description(
    goal: VideoMakerGoal,
    state: VideoMakerState,
    run_info: RunInfo,
) -> str:
    paths = script_artifact_paths(state.output_dir, run_info.run_number)
    # Only write the contract if it doesn't already exist on disk.  The first
    # run's contract is written—with the correct goal data—by
    # start_script_milestone(), so we avoid clobbering it here.  Retry runs
    # (run_number > 1) will have a new, absent path and will be written below.
    if not paths["contract"].exists():
        _write_script_contract(goal=goal, state=state, run_info=run_info)
    contract = paths["contract"]
    source_manifest = Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md"
    return f"""You are the DeepAgents-native video-maker Scriptwriter subagent.

Input contract:
- topic: {goal.topic}
- duration: {goal.duration}
- style: {goal.style}
- aspect_ratio: {goal.aspect_ratio}
- source_manifest_file: {_to_virtual_path(source_manifest)}
- contract_file: {_to_virtual_path(contract)}
- output_format_reference: /skills/video-maker-v2/references/scriptwriter-output-contract.md
- bgm_file: {goal.bgm_file}
- sfx_enabled: {goal.sfx_enabled}
- script_path: {_to_virtual_path(paths["script"])}
- eval_mode: {goal.eval_mode}

Required behavior:
1. Read source_manifest_file first with read_file. Do not ask Producer to inline folder contents.
2. Read contract_file and follow the target scene count/duration constraints. Do not modify contract_file.
3. Read output_format_reference and follow its exact scene schema.
4. Write only script.md (Markdown, scenes as `## Scene N`) to script_path.
   Scene fields must be canonical bare keys, for example `type: narration`,
   `scene_intent:`, and `content_brief:`. Do not write markdown bullet/bold
   keys such as `- **type**:`.
5. Stop at the script review checkpoint; do not build Remotion scenes.
6. Return only the output summary, not full script text.

Output contract:
script_path: {_to_virtual_path(paths["script"])}
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


def ratify_and_update_script(
    state: VideoMakerState,
    goal: VideoMakerGoal,
    *,
    run_number: int | None = None,
) -> RatifyResult:
    milestone = state.milestone("script")
    selected_run_number = run_number or milestone.current_run or 1
    paths = script_artifact_paths(state.output_dir, selected_run_number)
    result = ratify_script(paths["script"], paths["contract"])
    ratify_payload = {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {"id": c.id, "passed": c.passed, "message": c.message, "metadata": c.metadata}
            for c in result.checks
        ],
    }
    if result.passed:
        milestone.current_run = selected_run_number
        milestone.retry_count = 0
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
    (ratify_dir / f"script-run-{selected_run_number}.json").write_text(
        json.dumps(ratify_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result


def _write_script_contract(
    *,
    goal: VideoMakerGoal | None,
    state: VideoMakerState,
    run_info: RunInfo,
) -> Path:
    paths = script_artifact_paths(state.output_dir, run_info.run_number)
    contract = paths["contract"]
    contract.parent.mkdir(parents=True, exist_ok=True)
    duration = goal.duration if goal else "1-3min"
    scene_ranges = {
        "1-3min": {"min": 1, "max": 16},
        "3-5min": {"min": 1, "max": 24},
        "5-10min": {"min": 1, "max": 40},
    }
    seconds_ranges = {
        "1-3min": {"min": 60, "max": 180},
        "3-5min": {"min": 180, "max": 300},
        "5-10min": {"min": 300, "max": 600},
    }
    payload = {
        "version": 2,
        "topic": goal.topic if goal else "",
        "duration": duration,
        "target_scene_count": scene_ranges.get(duration, {"min": 1, "max": 16}),
        "target_duration_seconds": seconds_ranges.get(duration, {"min": 60, "max": 180}),
        "narrative_structure": {
            "opening_type": "hook",
            "closing_type": "cta",
            "required_roles": ["hook", "setup", "development", "climax", "cta"],
        },
        "constraints": {
            "max_consecutive_same_type": 3,
            "min_visual_break_scenes": 1,
            "audio_scene_types": ["narration", "data_card", "quote_card", "diagram_walkthrough"],
        },
    }
    contract.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return contract
