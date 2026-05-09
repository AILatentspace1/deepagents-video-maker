from pathlib import Path

from deepagents_video_maker.artifacts import collect_artifacts, source_manifest_path
from deepagents_video_maker.params import parse_video_request
from deepagents_video_maker.session import init_video_session


def test_collect_artifacts_reports_v2_known_paths(tmp_path: Path):
    goal = parse_video_request(
        "topic=介绍 video-maker-v2 skill\nsource=folder\nsource_folder=fixtures"
    )
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")
    manifest_path = source_manifest_path(state.output_dir)
    manifest_path.write_text(
        "# Source Manifest\n\n## Items\n- path: fixtures/brief.md\n", encoding="utf-8"
    )

    artifacts = collect_artifacts(state.output_dir)

    assert artifacts["goal"].exists is True
    assert artifacts["state"].exists is True
    assert artifacts["source_manifest"].exists is True
    assert artifacts["source_manifest"].size > 0
    assert artifacts["final_video"].exists is False


def test_source_manifest_path_is_stable(tmp_path: Path):
    goal = parse_video_request("topic=介绍 video-maker-v2 skill\nsource=folder")
    state = init_video_session(goal, tmp_path, timestamp="20260425-120000")

    assert str(source_manifest_path(state.output_dir)).endswith(
        "artifacts\\source\\source-manifest.md"
    ) or str(source_manifest_path(state.output_dir)).endswith(
        "artifacts/source/source-manifest.md"
    )
