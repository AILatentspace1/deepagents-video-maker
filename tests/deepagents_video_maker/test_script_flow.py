from pathlib import Path
import json
import pytest

from deepagents_video_maker.models import (
    MilestoneState,
    MilestoneStatus,
    VideoMakerGoal,
    VideoMakerState,
)
from deepagents_video_maker.script_flow import (
    build_scriptwriter_task_description,
    ratify_and_update_script,
    start_script_milestone,
)


def _state(tmp_path: Path, research_status=MilestoneStatus.COMPLETED) -> VideoMakerState:
    return VideoMakerState(
        output_dir=str(tmp_path),
        milestones=[
            MilestoneState(id="research", status=research_status, current_run=1),
            MilestoneState(id="script"),
        ],
    )


def _goal(local_file: str = "ref.md") -> VideoMakerGoal:
    g = VideoMakerGoal(topic="quantum attention", source="local-file", local_file=local_file)
    g.duration = "1-3min"
    g.style = "professional"
    return g


def test_start_script_milestone_requires_research_completed(tmp_path):
    state = _state(tmp_path, research_status=MilestoneStatus.IN_PROGRESS)
    with pytest.raises(RuntimeError, match="research status=in_progress"):
        start_script_milestone(state)


def test_start_script_milestone_creates_run_dir(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    assert Path(run.run_dir).exists()
    assert run.milestone == "script"
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS


def test_build_scriptwriter_task_description_includes_research_path(tmp_path):
    state = _state(tmp_path)
    research_file = tmp_path / "artifacts/research/run-1/research.md"
    research_file.parent.mkdir(parents=True, exist_ok=True)
    research_file.write_text("# Research\n", encoding="utf-8")
    run = start_script_milestone(state)
    desc = build_scriptwriter_task_description(_goal(), state, run)
    assert "research_file" in desc
    assert "script.md" in desc
    assert "manifest.json" in desc


def test_ratify_and_update_script_marks_completed_when_artifacts_valid(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)
    (run_dir / "script.md").write_text(
        "## Scene 1\ntype: narration\nnarration: hi\nscene_intent: hook\ncontent_brief: x\n",
        encoding="utf-8",
    )
    (run_dir / "manifest.json").write_text(
        json.dumps({"scenes": [{"id": "s1", "narration": "hi", "duration": 5}]}),
        encoding="utf-8",
    )
    result = ratify_and_update_script(state, _goal())
    assert result.passed
    assert state.milestone("script").status == MilestoneStatus.COMPLETED
    ratify_file = tmp_path / "ratify" / "script-run-1.json"
    assert ratify_file.exists()
    assert json.loads(ratify_file.read_text(encoding="utf-8"))["passed"] is True


def test_ratify_and_update_script_increments_retry_when_artifact_missing(tmp_path):
    state = _state(tmp_path)
    start_script_milestone(state)
    result = ratify_and_update_script(state, _goal())
    assert not result.passed
    assert state.milestone("script").retry_count == 1
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS
