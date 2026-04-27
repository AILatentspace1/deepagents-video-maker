"""Native Research milestone flow helpers.

These helpers keep the DeepAgents model as the Producer, but make the research
milestone protocol explicit and testable:

1. start research milestone
2. produce a strict `task(subagent_type="researcher")` description
3. ratify the resulting artifact
4. update state to completed / retry / blocked
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .artifacts import research_artifact_path
from .models import MilestoneStatus, RatifyResult, RunInfo, VideoMakerGoal, VideoMakerState
from .ratify import ratify_research
from .session import create_milestone_run
from .state_store import update_milestone_status


def start_research_milestone(state: VideoMakerState) -> RunInfo:
    """Start research milestone and create the next research run directory."""

    return create_milestone_run(state, "research")


def build_researcher_task_description(
    goal: VideoMakerGoal,
    state: VideoMakerState,
    run_info: RunInfo,
) -> str:
    """Build the strict task description for `task(subagent_type="researcher")`."""

    output_path = Path(run_info.run_dir) / "research.md"
    output_path_for_agent = _to_virtual_path(output_path)
    excalidraw_line = (
        f"- excalidraw_file: {goal.excalidraw_file}\n" if goal.excalidraw_file else ""
    )
    return f"""You are the DeepAgents-native video-maker Researcher subagent.

Input contract:
- topic: {goal.topic}
- source: {goal.source}
- local_file: {goal.local_file}
{excalidraw_line}- output_path: {output_path_for_agent}
- required_sections: 9
- min_chars: 800
- visual_strategy: {goal.visual_strategy}

Required behavior:
1. Read input paths yourself. Do not ask the Producer to inline large file contents.
2. Write UTF-8 Markdown to output_path.
3. Include at least 3 markdown headings beginning with "## ".
4. For source=local-file, URL references are optional, but local source attribution is required.
5. Return only the output contract summary, not the full research text.

Output contract:
research_path: {output_path_for_agent}
summary: <3-5 sentence summary>
section_count: <number>
source_count: <number>
visual_strategy: {goal.visual_strategy}
blocking_issues: <none or list>
"""


def _to_virtual_path(path: str | Path) -> str:
    item = Path(path).resolve()
    root_env = os.environ.get("ORCHESTRATOR_SKILLS_ROOT")
    if root_env:
        root = Path(root_env).resolve()
        try:
            return "/" + item.relative_to(root).as_posix()
        except ValueError:
            pass
    return str(path)


def ratify_and_update_research(
    state: VideoMakerState,
    goal: VideoMakerGoal,
    *,
    research_path: str | Path | None = None,
) -> RatifyResult:
    """Ratify research.md and update research milestone state."""

    milestone = state.milestone("research")
    path = Path(research_path) if research_path else research_artifact_path(
        state.output_dir, milestone.current_run or 1
    )
    result = ratify_research(path, source=goal.source)
    ratify_payload = {
        "passed": result.passed,
        "issues": result.issues,
        "checks": [
            {
                "id": check.id,
                "passed": check.passed,
                "message": check.message,
                "metadata": check.metadata,
            }
            for check in result.checks
        ],
    }
    if result.passed:
        update_milestone_status(
            state,
            "research",
            MilestoneStatus.COMPLETED,
            ratify=ratify_payload,
        )
    else:
        milestone.retry_count += 1
        if milestone.retry_count > milestone.max_retries:
            update_milestone_status(
                state,
                "research",
                MilestoneStatus.BLOCKED,
                blocking_reason="research ratify failed after max retries",
                ratify=ratify_payload,
            )
            result.next_action = "block_for_user"
        else:
            update_milestone_status(
                state,
                "research",
                MilestoneStatus.IN_PROGRESS,
                blocking_reason="research ratify failed; retry required",
                ratify=ratify_payload,
            )
            result.next_action = "retry_milestone"
    ratify_dir = Path(state.output_dir) / "ratify"
    ratify_dir.mkdir(parents=True, exist_ok=True)
    (ratify_dir / f"research-run-{milestone.current_run or 1}.json").write_text(
        json.dumps(ratify_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return result
