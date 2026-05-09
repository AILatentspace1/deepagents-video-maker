"""Build Scenes and Render Package milestone helpers for video-maker-v2."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from .models import (
    MilestoneStatus,
    RatifyCheck,
    RatifyResult,
    RunInfo,
    VideoMakerGoal,
    VideoMakerState,
    WorkflowStatus,
)
from .script_flow import _to_virtual_path
from .session import create_milestone_run
from .state_store import update_milestone_status


def remotion_project_dir(output_dir: str | Path) -> Path:
    return Path(output_dir) / "remotion-project"


def final_video_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / "final" / "video.mp4"


def final_thumbnail_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / "final" / "thumbnail.jpg"


def publish_readiness_markdown_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / "final" / "publish-readiness.md"


def publish_readiness_json_path(output_dir: str | Path) -> Path:
    return Path(output_dir) / "ratify" / "publish-readiness.json"


def start_build_scenes_milestone(
    state: VideoMakerState,
    *,
    script_approved: bool,
) -> RunInfo:
    script = state.milestone("script")
    if script.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot start build_scenes milestone: script status={script.status.value} "
            "(must be completed)"
        )
    if not script_approved:
        raise RuntimeError("cannot start build_scenes milestone without script_approved=True")
    return create_milestone_run(state, "build_scenes")


def build_remotion_builder_task_description(
    goal: VideoMakerGoal,
    state: VideoMakerState,
    run_info: RunInfo,
) -> str:
    output_dir = Path(state.output_dir)
    project_dir = remotion_project_dir(output_dir)
    script_run = state.milestone("script").current_run or 1
    return f"""You are the DeepAgents-native video-maker Remotion Builder subagent.

Dispatch contract:
- subagent_type='remotion-builder'
- build_run_dir: {_to_virtual_path(run_info.run_dir)}

Input files:
- goal_file: {_to_virtual_path(output_dir / "goal.yaml")}
- script_file: {_to_virtual_path(output_dir / "artifacts" / "script" / f"run-{script_run}" / "script.md")}
- source_manifest_file: {_to_virtual_path(output_dir / "artifacts" / "source" / "source-manifest.md")}
- output_project_dir: {_to_virtual_path(project_dir)}
- final_video: {_to_virtual_path(final_video_path(output_dir))}
- thumbnail: {_to_virtual_path(final_thumbnail_path(output_dir))}

Boundaries:
- no video-pipeline-cli
- no v1 template mutation
- write only output_project_dir/final
- preserve facts from script/source manifest
- subtitles required on narration/data_card/quote_card/diagram_walkthrough scenes

Look and feel:
- topic: {goal.topic}
- duration: {goal.duration}
- style: {goal.style}
- aspect_ratio: {goal.aspect_ratio}
- lut_style: {goal.lut_style}
- template: {goal.template}
- visual_strategy: {goal.visual_strategy}
- transition_style: {goal.transition_style}

Required output:
- {project_dir / "package.json"}
- {project_dir / "src" / "index.ts"}
- renderable Remotion project rooted at output_project_dir

Stop after creating the project and report composition_id plus validation notes.
Do not run final package copying; Producer will use native render/package tools.
"""


def ratify_and_update_build_scenes(state: VideoMakerState) -> RatifyResult:
    result = ratify_build_scenes(remotion_project_dir(state.output_dir))
    payload = _payload(result)
    if result.passed:
        update_milestone_status(state, "build_scenes", MilestoneStatus.COMPLETED, ratify=payload)
    else:
        milestone = state.milestone("build_scenes")
        milestone.retry_count += 1
        update_milestone_status(
            state,
            "build_scenes",
            MilestoneStatus.IN_PROGRESS
            if milestone.retry_count <= milestone.max_retries
            else MilestoneStatus.BLOCKED,
            blocking_reason="build_scenes ratify failed",
            ratify=payload,
        )
        result.next_action = (
            "retry_milestone"
            if milestone.retry_count <= milestone.max_retries
            else "block_for_user"
        )
    _write_ratify(state.output_dir, "build-scenes.json", payload)
    return result


def ratify_build_scenes(project_dir: str | Path) -> RatifyResult:
    project = Path(project_dir)
    checks = [
        RatifyCheck("project_dir_exists", project.is_dir(), f"{project} is dir"),
        RatifyCheck(
            "package_json_exists",
            (project / "package.json").is_file(),
            f"{project / 'package.json'} exists",
        ),
        RatifyCheck(
            "src_index_exists",
            (project / "src" / "index.ts").is_file(),
            f"{project / 'src' / 'index.ts'} exists",
        ),
    ]
    return _result(checks)


def start_render_package_milestone(state: VideoMakerState) -> RunInfo:
    build = state.milestone("build_scenes")
    if build.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot start render_package milestone: build_scenes status={build.status.value} "
            "(must be completed)"
        )
    return create_milestone_run(state, "render_package")


CommandRunner = Callable[[list[str], Path], tuple[int, str, str]]
ProbeRunner = Callable[[Path], tuple[int, str, str]]


def render_remotion_project(
    state: VideoMakerState,
    *,
    composition_id: str,
    install: bool = False,
    command_runner: CommandRunner | None = None,
) -> dict[str, object]:
    _ensure_render_package_ready(state)
    project = remotion_project_dir(state.output_dir)
    runner = command_runner or _run_command
    commands: list[list[str]] = []
    if install:
        commands.append(["pnpm", "install", "--ignore-workspace"])
    commands.extend(
        [
            ["pnpm", "--ignore-workspace", "exec", "tsc", "--noEmit"],
            [
                "pnpm",
                "--ignore-workspace",
                "exec",
                "remotion",
                "render",
                "src/index.ts",
                composition_id,
                "--output=out/video.mp4",
                "--gl=angle",
            ],
            [
                "pnpm",
                "--ignore-workspace",
                "exec",
                "remotion",
                "still",
                "src/index.ts",
                composition_id,
                "--output=out/thumbnail.jpg",
                "--gl=angle",
            ],
        ]
    )
    results = []
    passed = True
    for command in commands:
        exit_code, stdout, stderr = runner(command, project)
        results.append(
            {
                "command": command,
                "cwd": str(project),
                "exit_code": exit_code,
                "stdout": stdout[-4000:],
                "stderr": stderr[-4000:],
            }
        )
        if exit_code != 0:
            passed = False
            break
    payload = {
        "passed": passed,
        "composition_id": composition_id,
        "project_dir": str(project),
        "commands": results,
        "rendered_video": str(project / "out" / "video.mp4"),
        "rendered_thumbnail": str(project / "out" / "thumbnail.jpg"),
    }
    _write_ratify(state.output_dir, "render-command.json", payload)
    return payload


def package_render_output(
    state: VideoMakerState,
    *,
    rendered_video: str | Path | None = None,
    rendered_thumbnail: str | Path | None = None,
) -> dict[str, object]:
    _ensure_render_package_ready(state)
    output_dir = Path(state.output_dir)
    video_source = Path(rendered_video) if rendered_video else remotion_project_dir(output_dir) / "out" / "video.mp4"
    thumb_source = (
        Path(rendered_thumbnail)
        if rendered_thumbnail
        else remotion_project_dir(output_dir) / "out" / "thumbnail.jpg"
    )
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    copied_video = False
    copied_thumbnail = False
    if video_source.is_file():
        shutil.copy2(video_source, final_video_path(output_dir))
        copied_video = True
    if thumb_source.is_file():
        shutil.copy2(thumb_source, final_thumbnail_path(output_dir))
        copied_thumbnail = True
    return {
        "video_source": str(video_source),
        "thumbnail_source": str(thumb_source),
        "final_video": str(final_video_path(output_dir)),
        "thumbnail": str(final_thumbnail_path(output_dir)),
        "final_video_exists": final_video_path(output_dir).is_file(),
        "thumbnail_exists": final_thumbnail_path(output_dir).is_file(),
        "copied_video": copied_video,
        "copied_thumbnail": copied_thumbnail,
    }


def _run_command(command: list[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=1800,
    )
    return completed.returncode, completed.stdout, completed.stderr


def ratify_and_update_render_package(
    state: VideoMakerState,
    *,
    duration: str | None = None,
    probe_runner: ProbeRunner | None = None,
) -> RatifyResult:
    result = ratify_render_package(state.output_dir, duration=duration, probe_runner=probe_runner)
    payload = _payload(result)
    if result.passed:
        update_milestone_status(state, "render_package", MilestoneStatus.COMPLETED, ratify=payload)
        state.workflow_status = WorkflowStatus.COMPLETED
    else:
        milestone = state.milestone("render_package")
        milestone.retry_count += 1
        update_milestone_status(
            state,
            "render_package",
            MilestoneStatus.IN_PROGRESS
            if milestone.retry_count <= milestone.max_retries
            else MilestoneStatus.BLOCKED,
            blocking_reason="render_package ratify failed",
            ratify=payload,
        )
        result.next_action = (
            "retry_milestone"
            if milestone.retry_count <= milestone.max_retries
            else "block_for_user"
        )
    _write_ratify(state.output_dir, "render-package.json", payload)
    return result


PUBLISH_READINESS_DIMENSIONS = (
    "source_faithfulness",
    "visual_hierarchy",
    "pacing",
    "subtitle_readability",
    "thumbnail_usefulness",
)


def build_publish_readiness_report(
    state: VideoMakerState,
    *,
    decision: str = "not_reviewed",
    checklist: dict[str, str | bool] | None = None,
    notes: str = "",
) -> dict[str, object]:
    """Write an advisory post-render publish-readiness report.

    This intentionally does not mutate render_package technical completion.
    The first productization step is to separate "render succeeded" from
    "a human would publish this".
    """

    video = final_video_path(state.output_dir)
    if not video.is_file() or video.stat().st_size <= 0:
        raise RuntimeError(f"cannot build publish-readiness report: missing final video {video}")

    allowed = {"publish_ready", "needs_revision", "not_reviewed"}
    normalized_decision = decision if decision in allowed else "not_reviewed"
    supplied = checklist or {}
    normalized_checklist = {
        key: supplied.get(key, "not_reviewed") for key in PUBLISH_READINESS_DIMENSIONS
    }
    payload: dict[str, object] = {
        "status": normalized_decision,
        "final_video": str(video),
        "thumbnail": str(final_thumbnail_path(state.output_dir)),
        "checklist": normalized_checklist,
        "notes": notes,
    }
    report = publish_readiness_markdown_path(state.output_dir)
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Publish Readiness",
        "",
        f"- status: {normalized_decision}",
        f"- final_video: {video}",
        f"- thumbnail: {final_thumbnail_path(state.output_dir)}",
        "",
        "## Checklist",
    ]
    for key, value in normalized_checklist.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Notes", notes or "not reviewed yet"])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_ratify(state.output_dir, "publish-readiness.json", payload)
    payload["report"] = str(report)
    return payload


def ratify_render_package(
    output_dir: str | Path,
    *,
    duration: str | None = None,
    probe_runner: ProbeRunner | None = None,
) -> RatifyResult:
    video = final_video_path(output_dir)
    thumbnail = final_thumbnail_path(output_dir)
    checks = [
        RatifyCheck("final_video_exists", video.is_file(), f"{video} exists"),
        RatifyCheck(
            "final_video_non_empty",
            video.is_file() and video.stat().st_size > 0,
            f"{video} non-empty",
        ),
        RatifyCheck(
            "thumbnail_exists_or_warning",
            True,
            f"{thumbnail} exists={thumbnail.is_file()}",
            {"warning": None if thumbnail.is_file() else "thumbnail missing"},
        ),
    ]
    if duration and video.is_file() and video.stat().st_size > 0:
        runner = probe_runner or _probe_duration
        exit_code, stdout, stderr = runner(video)
        checks.append(
            RatifyCheck(
                "ffprobe_duration_exit_zero",
                exit_code == 0,
                stderr[-500:] if exit_code != 0 else "ffprobe duration OK",
                {"stdout": stdout.strip(), "stderr": stderr[-1000:]},
            )
        )
        if exit_code == 0:
            try:
                seconds = float(stdout.strip())
            except ValueError:
                checks.append(
                    RatifyCheck(
                        "final_video_duration_parseable",
                        False,
                        f"ffprobe duration is not numeric: {stdout.strip()}",
                    )
                )
            else:
                min_seconds, max_seconds = _duration_bounds(duration)
                checks.append(
                    RatifyCheck(
                        "final_video_duration_in_range",
                        min_seconds <= seconds <= max_seconds,
                        f"duration_seconds={seconds}, expected={min_seconds}..{max_seconds}",
                        {"duration_seconds": seconds, "min": min_seconds, "max": max_seconds},
                    )
                )
    return _result(checks)


def _probe_duration(video: Path) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(video),
            ],
            text=True,
            capture_output=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "ffprobe timed out"
    return completed.returncode, completed.stdout, completed.stderr


def _duration_bounds(duration: str) -> tuple[int, int]:
    ranges = {
        "1-3min": (60, 180),
        "3-5min": (180, 300),
        "5-10min": (300, 600),
    }
    return ranges.get(duration, (60, 180))


def _ensure_render_package_ready(state: VideoMakerState) -> None:
    build = state.milestone("build_scenes")
    if build.status != MilestoneStatus.COMPLETED:
        raise RuntimeError(
            f"cannot render/package: build_scenes status={build.status.value} (must be completed)"
        )
    render = state.milestone("render_package")
    if render.status != MilestoneStatus.IN_PROGRESS:
        raise RuntimeError(
            f"cannot render/package: render_package status={render.status.value} "
            "(must be in_progress)"
        )


def _payload(result: RatifyResult) -> dict[str, object]:
    return {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {"id": c.id, "passed": c.passed, "message": c.message, "metadata": c.metadata}
            for c in result.checks
        ],
    }


def _write_ratify(output_dir: str | Path, filename: str, payload: dict[str, object]) -> None:
    ratify_dir = Path(output_dir) / "ratify"
    ratify_dir.mkdir(parents=True, exist_ok=True)
    (ratify_dir / filename).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _result(checks: list[RatifyCheck]) -> RatifyResult:
    issues = [check.message for check in checks if not check.passed]
    return RatifyResult(
        passed=not issues,
        checks=checks,
        issues=issues,
        next_action="complete_milestone" if not issues else "retry_milestone",
    )
