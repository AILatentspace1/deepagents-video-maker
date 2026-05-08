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


def _state(tmp_path: Path, source_status=MilestoneStatus.COMPLETED) -> VideoMakerState:
    return VideoMakerState(
        output_dir=str(tmp_path),
        milestones=[
            MilestoneState(id="source_intake", status=source_status),
            MilestoneState(id="script"),
        ],
    )


def _goal() -> VideoMakerGoal:
    g = VideoMakerGoal(topic="quantum attention", source="folder", source_folder="fixtures")
    g.duration = "1-3min"
    g.style = "professional"
    return g


def test_start_script_milestone_requires_source_intake_completed(tmp_path):
    state = _state(tmp_path, source_status=MilestoneStatus.IN_PROGRESS)
    with pytest.raises(RuntimeError, match="source_intake status=in_progress"):
        start_script_milestone(state)


def test_start_script_milestone_creates_run_dir_and_contract(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    assert Path(run.run_dir).exists()
    assert run.milestone == "script"
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS
    assert (Path(run.run_dir) / "script-contract.json").exists()


def test_build_scriptwriter_task_description_includes_source_manifest_and_contract(tmp_path):
    state = _state(tmp_path)
    manifest = tmp_path / "artifacts/source/source-manifest.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("# Source Manifest\n\n## Items\n- path: brief.md\n", encoding="utf-8")
    run = start_script_milestone(state)
    desc = build_scriptwriter_task_description(_goal(), state, run)
    assert "source_manifest_file" in desc
    assert "script-contract.json" in desc
    assert "research_file" not in desc


def test_ratify_and_update_script_marks_completed_when_artifacts_valid(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    run_dir = Path(run.run_dir)
    (run_dir / "script.md").write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hi\n"
        "scene_intent: hook\n"
        "content_brief: x\n",
        encoding="utf-8",
    )
    result = ratify_and_update_script(state, _goal())
    assert result.passed
    assert state.milestone("script").status == MilestoneStatus.COMPLETED
    ratify_file = tmp_path / "ratify" / "script-run-1.json"
    assert ratify_file.exists()
    assert json.loads(ratify_file.read_text(encoding="utf-8"))["passed"] is True


def test_ratify_and_update_script_resets_retry_count_on_pass(tmp_path):
    state = _state(tmp_path)
    run = start_script_milestone(state)
    state.milestone("script").retry_count = 4
    state.milestone("script").blocking_reason = "previous ratify failure"
    run_dir = Path(run.run_dir)
    (run_dir / "script.md").write_text(
        "## Scene 1\n"
        "type: narration\n"
        "narration: hi\n"
        "scene_intent: hook\n"
        "content_brief: x\n",
        encoding="utf-8",
    )

    result = ratify_and_update_script(state, _goal())

    assert result.passed
    assert state.milestone("script").status == MilestoneStatus.COMPLETED
    assert state.milestone("script").retry_count == 0
    assert state.milestone("script").blocking_reason is None


def test_ratify_and_update_script_increments_retry_when_artifact_missing(tmp_path):
    state = _state(tmp_path)
    start_script_milestone(state)
    result = ratify_and_update_script(state, _goal())
    assert not result.passed
    assert state.milestone("script").retry_count == 1
    assert state.milestone("script").status == MilestoneStatus.IN_PROGRESS
