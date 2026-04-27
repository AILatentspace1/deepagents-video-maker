"""Artifact helpers and tool-call dropout detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import ArtifactRef


PSEUDO_TOOL_MARKERS = ("<sop_invocation", '<invoke name="task"', "DSML")


def artifact_ref(kind: str, path: str | Path) -> ArtifactRef:
    return ArtifactRef.from_path(kind, path)


def collect_artifacts(output_dir: str | Path) -> dict[str, ArtifactRef]:
    root = Path(output_dir)
    known = {
        "goal": root / "goal.yaml",
        "state": root / "state.yaml",
        "research": root / "artifacts" / "research" / "run-1" / "research.md",
        "script": root / "artifacts" / "script" / "run-1" / "script.md",
        "manifest": root / "artifacts" / "script" / "run-1" / "manifest.json",
        "final_video": root / "final" / "video.mp4",
    }
    return {kind: artifact_ref(kind, path) for kind, path in known.items()}


def research_artifact_path(output_dir: str | Path, run_number: int = 1) -> Path:
    return Path(output_dir) / "artifacts" / "research" / f"run-{run_number}" / "research.md"


def script_artifact_paths(output_dir: str | Path, run_number: int = 1) -> dict[str, Path]:
    run_dir = Path(output_dir) / "artifacts" / "script" / f"run-{run_number}"
    return {
        "script": run_dir / "script.md",
        "manifest": run_dir / "manifest.json",
    }


def detect_tool_call_dropout(
    last_message: dict[str, Any],
    *,
    milestone_status: str,
    expected_artifact: str | Path,
) -> bool:
    """Detect pseudo tool-call text with no real tool calls and missing artifact."""

    has_tool_calls = bool(last_message.get("tool_calls"))
    if has_tool_calls:
        return False
    if milestone_status != "in_progress":
        return False
    if Path(expected_artifact).exists():
        return False
    content = str(last_message.get("content", ""))
    return any(marker in content for marker in PSEUDO_TOOL_MARKERS)
