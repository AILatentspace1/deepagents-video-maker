from pathlib import Path

from deepagents_video_maker.artifacts import collect_artifacts, research_artifact_path
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import create_milestone_run, init_video_session


def test_collect_artifacts_reports_known_paths(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    create_milestone_run(state, "research")
    research_path = research_artifact_path(state.output_dir)
    research_path.write_text("research", encoding="utf-8")

    artifacts = collect_artifacts(state.output_dir)

    assert artifacts["goal"].exists is True
    assert artifacts["state"].exists is True
    assert artifacts["research"].exists is True
    assert artifacts["research"].size == len("research")
    assert artifacts["final_video"].exists is False


def test_research_artifact_path_is_stable(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker skill\nsource=local-file")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")

    assert str(research_artifact_path(state.output_dir, 2)).endswith(
        "artifacts\\research\\run-2\\research.md"
    ) or str(research_artifact_path(state.output_dir, 2)).endswith(
        "artifacts/research/run-2/research.md"
    )

