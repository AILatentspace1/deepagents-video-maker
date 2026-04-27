from pathlib import Path

from deepagents_video_maker.controller import block_if_tool_call_dropout, can_enter_milestone
from deepagents_video_maker.models import MilestoneStatus
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import create_milestone_run, init_video_session
from deepagents_video_maker.state_store import update_milestone_status


def test_block_if_tool_call_dropout_marks_research_blocked(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    create_milestone_run(state, "research")
    message = {
        "content": '<sop_invocation><invoke name="task">researcher</invoke> DSML',
        "tool_calls": [],
    }

    assert block_if_tool_call_dropout(state, milestone_id="research", last_message=message)
    research = state.milestone("research")
    assert research.status == MilestoneStatus.BLOCKED
    assert research.blocking_reason is not None
    assert "tool-call dropout" in research.blocking_reason


def test_can_enter_script_requires_completed_research_artifact(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    run = create_milestone_run(state, "research")

    assert can_enter_milestone(state, "script") is False

    research_path = Path(run.run_dir) / "research.md"
    research_path.write_text("ok", encoding="utf-8")
    update_milestone_status(state, "research", MilestoneStatus.COMPLETED)

    assert can_enter_milestone(state, "script") is True

