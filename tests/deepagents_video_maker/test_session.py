from pathlib import Path

from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import init_video_session


def test_init_video_session_creates_expected_layout(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    output_dir = Path(state.output_dir)

    assert output_dir.name == "20260425-120000-video-介绍-video-maker-skill"
    assert (output_dir / "goal.yaml").is_file()
    assert (output_dir / "state.yaml").is_file()
    assert (output_dir / "artifacts" / "research").is_dir()
    assert (output_dir / "artifacts" / "script").is_dir()
    assert (output_dir / "artifacts" / "assets" / "visual_director").is_dir()
    assert (output_dir / "final").is_dir()
    assert (output_dir / "ratify").is_dir()
    assert [milestone.id for milestone in state.milestones] == [
        "research",
        "script",
        "assets",
        "assembly",
    ]


def test_goal_and_state_yaml_are_utf8_readable(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    output_dir = Path(state.output_dir)

    assert "topic: \"介绍 video-maker skill\"" in (output_dir / "goal.yaml").read_text(
        encoding="utf-8"
    )
    state_text = (output_dir / "state.yaml").read_text(encoding="utf-8")
    assert "workflow: video-maker-native" in state_text
    assert "id: research" in state_text

