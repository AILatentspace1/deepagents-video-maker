"""DeepAgents-native controller helpers.

This module does not implement a LangGraph node DAG. It provides small,
deterministic helpers that the DeepAgents Producer can call through typed tools
or use in tests to enforce the controller protocol.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import detect_tool_call_dropout, research_artifact_path
from .models import MilestoneStatus, VideoMakerState
from .state_store import update_milestone_status


def block_if_tool_call_dropout(
    state: VideoMakerState,
    *,
    milestone_id: str,
    last_message: dict[str, Any],
    expected_artifact: str | Path | None = None,
) -> bool:
    """Mark a milestone blocked if a pseudo tool call ended without artifact."""

    milestone = state.milestone(milestone_id)
    artifact = expected_artifact
    if artifact is None and milestone_id == "research":
        artifact = research_artifact_path(state.output_dir, milestone.current_run or 1)
    if artifact is None:
        return False

    is_dropout = detect_tool_call_dropout(
        last_message,
        milestone_status=milestone.status.value,
        expected_artifact=artifact,
    )
    if is_dropout:
        update_milestone_status(
            state,
            milestone_id,
            MilestoneStatus.BLOCKED,
            blocking_reason=(
                "tool-call dropout: model emitted pseudo task invocation text "
                "but no real task tool_call and expected artifact is missing"
            ),
        )
    return is_dropout


def can_enter_milestone(state: VideoMakerState, milestone_id: str) -> bool:
    """Minimal artifact gate for milestone transition checks."""

    if milestone_id == "script":
        research = state.milestone("research")
        if research.status != MilestoneStatus.COMPLETED:
            return False
        research_path = research_artifact_path(state.output_dir, research.current_run or 1)
        return research_path.exists()
    return True

