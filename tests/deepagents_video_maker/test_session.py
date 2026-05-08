from pathlib import Path

from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import init_video_session


def test_init_video_session_creates_v2_layout(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder\nsource_folder=fixtures")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    output_dir = Path(state.output_dir)

    assert output_dir.name == "20260425-120000-video-介绍-video-maker-v2-skill"
    assert (output_dir / "goal.yaml").is_file()
    assert (output_dir / "state.yaml").is_file()
    assert (output_dir / "artifacts" / "source").is_dir()
    assert (output_dir / "artifacts" / "script").is_dir()
    assert not (output_dir / "artifacts" / "research").exists()
    assert (output_dir / "final").is_dir()
    assert (output_dir / "ratify").is_dir()
    assert [milestone.id for milestone in state.milestones] == [
        "source_intake",
        "script",
        "build_scenes",
        "render_package",
    ]


def test_goal_and_state_yaml_are_v2_utf8_readable(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder\nsource_folder=fixtures")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    output_dir = Path(state.output_dir)

    goal_text = (output_dir / "goal.yaml").read_text(encoding="utf-8")
    assert "topic: \"介绍 video-maker-v2 skill\"" in goal_text
    assert "source_folder: \"fixtures\"" in goal_text
    state_text = (output_dir / "state.yaml").read_text(encoding="utf-8")
    assert "workflow: video-maker-v2" in state_text
    assert "id: source_intake" in state_text
