from pathlib import Path

from deepagents_video_maker.controller import block_if_tool_call_dropout, can_enter_milestone
from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import create_milestone_run, init_video_session
from deepagents_video_maker.state_store import update_milestone_status


def test_block_if_tool_call_dropout_marks_source_intake_blocked(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    create_milestone_run(state, "source_intake")
    message = {
        "content": '<sop_invocation><invoke name="task">scriptwriter</invoke> DSML',
        "tool_calls": [],
    }

    expected = Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md"
    assert block_if_tool_call_dropout(
        state,
        milestone_id="source_intake",
        last_message=message,
        expected_artifact=expected,
    )
    assert state.milestone("source_intake").status == MilestoneStatus.BLOCKED


def test_can_enter_script_requires_completed_source_manifest(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    create_milestone_run(state, "source_intake")
    assert not can_enter_milestone(state, "script")

    manifest = Path(state.output_dir) / "artifacts" / "source" / "source-manifest.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("# Source Manifest\n\n## Items\n- path: brief.md\n", encoding="utf-8")
    update_milestone_status(state, "source_intake", MilestoneStatus.COMPLETED)

    assert can_enter_milestone(state, "script")
