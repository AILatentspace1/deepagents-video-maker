"""UI-facing state projection for the video-maker LangGraph thread state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import VideoMakerState
from .state_store import load_state_yaml


MILESTONE_LABELS = {
    "source_intake": "Source Intake",
    "script": "Script Review",
    "build_scenes": "Build Scenes",
    "render_package": "Render Package",
    "publish_readiness": "Publish Readiness",
}


def build_video_maker_ui_state(output_dir: str | Path) -> dict[str, Any]:
    """Build the `stream.values.video_maker` object consumed by `web-ui`.

    The projection intentionally reads only `state.yaml` plus a fixed list of
    canonical artifacts so it stays cheap and deterministic for every tool call.
    """

    root = Path(output_dir)
    state = load_state_yaml(root / "state.yaml")
    return build_video_maker_ui_state_from_state(state)


def build_video_maker_ui_state_from_state(state: VideoMakerState) -> dict[str, Any]:
    root = Path(state.output_dir)
    milestones = []
    current_blocker: str | None = None
    script_run = _current_run(state, "script")
    for milestone in state.milestones:
        artifact_paths = _milestone_artifacts(milestone.id, script_run=script_run)
        if current_blocker is None and milestone.blocking_reason:
            current_blocker = milestone.blocking_reason
        milestones.append(
            {
                "id": milestone.id,
                "label": MILESTONE_LABELS.get(milestone.id, milestone.id),
                "status": milestone.status.value,
                "blockingReason": milestone.blocking_reason,
                "artifactPaths": [str(root / relative) for relative in artifact_paths],
            }
        )

    artifacts = [
        {
            "kind": kind,
            "path": str(root / relative),
            "exists": (root / relative).exists(),
        }
        for kind, relative in _known_artifacts(script_run=script_run).items()
    ]

    publish = _read_publish_readiness(root)
    return {
        "outputDir": state.output_dir,
        "workflowStatus": state.workflow_status.value,
        "milestones": milestones,
        "artifacts": artifacts,
        "currentBlocker": current_blocker,
        "nextActions": _next_actions(state),
        "publishReadiness": publish,
    }


def _current_run(state: VideoMakerState, milestone_id: str) -> int:
    try:
        return state.milestone(milestone_id).current_run or 1
    except (ValueError, KeyError):
        return 1


def _milestone_artifacts(milestone_id: str, *, script_run: int) -> list[str]:
    script_prefix = f"artifacts/script/run-{script_run}"
    artifacts = {
        "source_intake": ["artifacts/source/source-manifest.md"],
        "script": [f"{script_prefix}/script.md", f"{script_prefix}/script-contract.json"],
        "build_scenes": ["remotion-project/package.json", "remotion-project/src/index.ts"],
        "render_package": ["final/video.mp4", "final/thumbnail.jpg", "ratify/render-package.json"],
        "publish_readiness": ["final/publish-readiness.md", "ratify/publish-readiness.json"],
    }
    return artifacts.get(milestone_id, [])


def _known_artifacts(*, script_run: int) -> dict[str, str]:
    script_prefix = f"artifacts/script/run-{script_run}"
    return {
        "source_manifest": "artifacts/source/source-manifest.md",
        "script": f"{script_prefix}/script.md",
        "script_contract": f"{script_prefix}/script-contract.json",
        "remotion_project": "remotion-project/package.json",
        "render_command": "ratify/render-command.json",
        "final_video": "final/video.mp4",
        "thumbnail": "final/thumbnail.jpg",
        "render_ratify": "ratify/render-package.json",
        "publish_readiness": "final/publish-readiness.md",
        "publish_readiness_ratify": "ratify/publish-readiness.json",
    }


def _read_publish_readiness(root: Path) -> dict[str, Any]:
    report_path = root / "final" / "publish-readiness.md"
    ratify_path = root / "ratify" / "publish-readiness.json"
    if not ratify_path.is_file():
        return {"status": "not_reviewed", "reportPath": str(report_path)}

    try:
        payload = json.loads(ratify_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "status": "needs_revision",
            "reportPath": str(report_path),
            "notes": f"invalid publish readiness JSON: {ratify_path}",
        }
    return {
        "status": payload.get("status", "not_reviewed"),
        "reportPath": payload.get("report", str(report_path)),
        "notes": payload.get("notes", ""),
    }


def _next_actions(state: VideoMakerState) -> list[str]:
    for milestone in state.milestones:
        if milestone.status.value == "blocked":
            return [f"Resolve blocker for {MILESTONE_LABELS.get(milestone.id, milestone.id)}"]
        if milestone.status.value == "in_progress":
            return [f"Complete {MILESTONE_LABELS.get(milestone.id, milestone.id)}"]
        if milestone.status.value == "pending":
            return [f"Start {MILESTONE_LABELS.get(milestone.id, milestone.id)}"]
    if state.workflow_status.value == "completed":
        return ["Review publish readiness and final package"]
    return []
